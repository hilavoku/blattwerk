using Microsoft.Web.WebView2.WinForms;
using System.Diagnostics;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace PdfWerkstatt;

internal static class Program
{
    private static int port;
    private static bool dirty;

    [STAThread]
    private static void Main(string[] args)
    {
        // Doppelklick auf eine PDF-Datei: Pfad liegt in args[0]
        string? pdfPath = args.Length > 0 ? Path.GetFullPath(args[0]) : null;
        if (pdfPath != null && !File.Exists(pdfPath)) pdfPath = null;

        port = GetFreePort();
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string serverExe = Path.Combine(baseDir, "server", "PdfWerkstattServer.exe");
        if (!File.Exists(serverExe))
        {
            MessageBox.Show(
                "PdfWerkstattServer.exe wurde nicht gefunden:\n" + serverExe,
                "Blattwerk", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        var psi = new ProcessStartInfo
        {
            FileName = serverExe,
            Arguments = $"--port {port}" + (pdfPath != null ? $" --file \"{pdfPath}\"" : ""),
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = Path.GetDirectoryName(serverExe)!
        };
        Process? server = Process.Start(psi);

        ApplicationConfiguration.Initialize();

        var form = new HauptForm
        {
            Text = pdfPath != null
                ? "Blattwerk - " + Path.GetFileName(pdfPath)
                : "Blattwerk",
            Width = 1450,
            Height = 940,
            StartPosition = FormStartPosition.CenterScreen,
            Font = new Font("Segoe UI", 9f),
            FormBorderStyle = FormBorderStyle.None,
            BackColor = System.Drawing.Color.FromArgb(23, 25, 29),
            Padding = new Padding(6, 0, 6, 6)
        };

        // Fenstergroesse/-position wiederherstellen (fenster.json neben der EXE)
        string winFile = Path.Combine(baseDir, "fenster.json");
        try
        {
            if (File.Exists(winFile))
            {
                using var winDoc = JsonDocument.Parse(File.ReadAllText(winFile));
                var r = winDoc.RootElement;
                int wx = r.TryGetProperty("x", out var px) && px.ValueKind == JsonValueKind.Number ? px.GetInt32() : 100;
                int wy = r.TryGetProperty("y", out var py) && py.ValueKind == JsonValueKind.Number ? py.GetInt32() : 60;
                int ww = r.TryGetProperty("w", out var pw) && pw.ValueKind == JsonValueKind.Number ? Math.Max(400, pw.GetInt32()) : 1450;
                int wh = r.TryGetProperty("h", out var ph) && ph.ValueKind == JsonValueKind.Number ? Math.Max(300, ph.GetInt32()) : 940;
                bool wasMax = r.TryGetProperty("max", out var pm) && pm.ValueKind == JsonValueKind.True;
                var bounds = new Rectangle(wx, wy, ww, wh);
                if (Screen.AllScreens.Any(s => s.WorkingArea.IntersectsWith(bounds)))
                {
                    form.StartPosition = FormStartPosition.Manual;
                    form.Bounds = bounds;
                }
                if (wasMax) form.WindowState = FormWindowState.Maximized;
            }
        }
        catch { /* kaputte Datei: Standardgroesse und zentriert starten */ }
        var webView = new WebView2 { Dock = DockStyle.Fill, DefaultBackgroundColor = System.Drawing.Color.FromArgb(23, 25, 29) };
        form.Controls.Add(webView);
        try { form.Icon = System.Drawing.Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

        form.Resize += (_, _) =>
        {
            // Maximiert: randlos ueber den ganzen Bildschirm; sonst 6px-Groesse-Rand unten/links/rechts
            form.Padding = form.WindowState == FormWindowState.Maximized
                ? Padding.Empty
                : new Padding(6, 0, 6, 6);
        };

        form.Load += async (_, _) =>
        {
            try
            {
                await webView.EnsureCoreWebView2Async();
                webView.CoreWebView2.Settings.AreDefaultContextMenusEnabled = true;
                webView.CoreWebView2.Settings.AreHostObjectsAllowed = false;
                webView.CoreWebView2.WebMessageReceived += async (_, e) =>
                {
                    var msg = e.TryGetWebMessageAsString();
                    if (msg == "dirty:1") dirty = true;
                    else if (msg == "dirty:0") dirty = false;
                    else if (msg != null && msg.StartsWith("fenster|"))
                    {
                        // Eigene Titelleiste: Minimieren/Maximieren/Schliessen/Ziehen aus der Kopfzeile
                        var befehl = msg.Substring(8);
                        if (befehl == "min") form.WindowState = FormWindowState.Minimized;
                        else if (befehl == "max") form.MaximierenWechseln();
                        else if (befehl == "zu") form.Close();
                        else if (befehl == "drag") form.Titelziehen();
                        try
                        {
                            var maxed = form.WindowState == FormWindowState.Maximized;
                            _ = webView.CoreWebView2.ExecuteScriptAsync(
                                $"window.pwMaximiert && window.pwMaximiert({(maxed ? "true" : "false")});");
                        }
                        catch { /* UI evtl. nicht bereit */ }
                    }
                    else if (msg != null && msg.StartsWith("saveas|"))
                    {
                        // "saveas|<docid>|<dateiname>|<flatten>" -> Systemdialog, dann speichern
                        var teile = msg.Split('|', 4);
                        if (teile.Length >= 3)
                        {
                            int flatten = teile.Length == 4 && teile[3] == "1" ? 1 : 0;
                            using var dlg = new SaveFileDialog
                            {
                                Filter = "PDF-Datei (*.pdf)|*.pdf|Alle Dateien (*.*)|*.*",
                                FileName = teile[2].EndsWith(".pdf", StringComparison.OrdinalIgnoreCase)
                                    ? teile[2] : teile[2] + ".pdf"
                            };
                            if (dlg.ShowDialog() == DialogResult.OK)
                            {
                                bool ok = false;
                                try
                                {
                                    using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(60) };
                                    var resp = await http.GetAsync(
                                        $"http://127.0.0.1:{port}/api/saveas/{teile[1]}?path={Uri.EscapeDataString(dlg.FileName)}&flatten={flatten}");
                                    ok = resp.IsSuccessStatusCode;
                                }
                                catch { ok = false; }
                                try
                                {
                                    var script = $"window.pwSaveasDone && window.pwSaveasDone({(ok ? "true" : "false")}, {System.Text.Json.JsonSerializer.Serialize(dlg.FileName)});";
                                    await webView.CoreWebView2.ExecuteScriptAsync(script);
                                }
                                catch { /* UI ist evtl. schon zu */ }
                            }
                        }
                    }
                };

                // Erst den Startbildschirm zeigen - NIE die Edge-Fehlerseite
                webView.CoreWebView2.NavigateToString(SplashHtml());

                // Warten, bis der Server antwortet (max. ~60 s, Abbruch wenn er stirbt)
                bool ready = false;
                using (var http = new HttpClient { Timeout = TimeSpan.FromSeconds(2) })
                {
                    for (int i = 0; i < 120 && server is { HasExited: false }; i++)
                    {
                        try
                        {
                            var resp = await http.GetAsync($"http://127.0.0.1:{port}/api/health");
                            if (resp.IsSuccessStatusCode) { ready = true; break; }
                        }
                        catch { /* Server noch nicht bereit */ }
                        await Task.Delay(500);
                    }
                }

                if (ready)
                {
                    webView.CoreWebView2.Navigate($"http://127.0.0.1:{port}/");
                }
                else
                {
                    webView.CoreWebView2.NavigateToString(ErrorHtml());
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "WebView2 konnte nicht geladen werden:\n" + ex.Message +
                    "\n\nBitte das \"WebView2 Runtime\"-Paket installieren.",
                    "Blattwerk", MessageBoxButtons.OK, MessageBoxIcon.Error);
                form.Close();
            }
        };

        form.FormClosing += (_, e) =>
        {
            if (!dirty) return;
            var choice = MessageBox.Show(
                "Es gibt nicht gespeicherte \u00c4nderungen.\n\n" +
                "Ja = Speichern und schließen\n" +
                "Nein = Ohne Speichern schließen\n" +
                "Abbrechen = Zurück zum Dokument",
                "Ungespeicherte \u00c4nderungen",
                MessageBoxButtons.YesNoCancel, MessageBoxIcon.Warning,
                MessageBoxDefaultButton.Button1);
            if (choice == DialogResult.Cancel)
            {
                e.Cancel = true;
                return;
            }
            if (choice == DialogResult.Yes)
            {
                if (!SaveCurrent())
                {
                    var again = MessageBox.Show(
                        "Speichern fehlgeschlagen. Trotzdem schließen?",
                        "Blattwerk", MessageBoxButtons.YesNo, MessageBoxIcon.Error);
                    if (again == DialogResult.No) e.Cancel = true;
                }
            }
        };

        form.FormClosed += (_, _) =>
        {
            // Fenstergroesse/-position fuer den naechsten Start merken
            try
            {
                var state = form.WindowState;
                var b = state == FormWindowState.Normal
                    ? new Rectangle(form.Left, form.Top, form.Width, form.Height)
                    : form.RestoreBounds;
                if (b.Width >= 400 && b.Height >= 300)
                    File.WriteAllText(winFile, System.Text.Json.JsonSerializer.Serialize(
                        new { x = b.X, y = b.Y, w = b.Width, h = b.Height, max = state == FormWindowState.Maximized }));
            }
            catch { /* nicht speicherbar: naechster Start mit Standardgroesse */ }
            try { if (server is { HasExited: false }) server.Kill(entireProcessTree: true); }
            catch { /* Server war schon weg */ }
        };

        Application.Run(form);
    }

    private static string? _logoCache;

    private static string? LogoDataUrl()
    {
        if (_logoCache == null)
        {
            try
            {
                string basis = AppDomain.CurrentDomain.BaseDirectory;
                string[] kandidaten =
                {
                    Path.Combine(basis, "server", "_internal", "static", "logo.png"),  // Deployment
                    Path.Combine(basis, "..", "app", "static", "logo.png"),            // Entwicklung / paket
                };
                var pfad = kandidaten.FirstOrDefault(File.Exists);
                _logoCache = pfad != null
                    ? "data:image/png;base64," + Convert.ToBase64String(File.ReadAllBytes(pfad))
                    : "";
            }
            catch { _logoCache = ""; }
        }
        return _logoCache.Length > 0 ? _logoCache : null;
    }

    private static string LogoHtml(int groesse)
    {
        var url = LogoDataUrl();
        return url != null
            ? $"<img class=\"logo\" style=\"width:{groesse}px;height:{groesse}px\" src=\"{url}\" alt=\"\">"
            : $"<div class=\"logo emoji\" style=\"font-size:{Math.Max(24, groesse - 10)}px\">&#128196;</div>";
    }

    private static string SplashHtml() => """
        <!DOCTYPE html><html><head><meta charset="utf-8"><style>
        html,body{height:100%;margin:0}
        body{background:#17191d;color:#e6e9ee;font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center}
        .c{text-align:center}
        .logo{display:block;margin:0 auto 16px;border-radius:18px;box-shadow:0 8px 28px rgba(0,0,0,.5)}
        .logo.emoji{line-height:1}
        h1{font-weight:600;margin:0 0 8px}
        p{color:#97a0af;margin:0}
        .bar{width:140px;height:3px;background:#2c313a;border-radius:2px;margin:18px auto 0;overflow:hidden}
        .bar i{display:block;width:40%;height:100%;background:#4cc2ff;border-radius:2px;animation:sl 1.1s infinite linear}
        @keyframes sl{from{transform:translateX(-100%)}to{transform:translateX(350%)}}
        </style></head><body><div class="c">__LOGO__<h1>Blattwerk</h1><p>wird gestartet &hellip;</p><div class="bar"><i></i></div></div></body></html>
        """.Replace("__LOGO__", LogoHtml(84));

    private static string ErrorHtml() => """
        <!DOCTYPE html><html><head><meta charset="utf-8"><style>
        html,body{height:100%;margin:0}
        body{background:#17191d;color:#e6e9ee;font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center}
        .c{text-align:center;max-width:420px}
        .logo{display:block;margin:0 auto 18px;border-radius:18px;box-shadow:0 8px 28px rgba(0,0,0,.5)}
        .logo.emoji{line-height:1}
        h1{font-weight:600;margin:0 0 10px}
        p{color:#97a0af;line-height:1.6;margin:0}
        </style></head><body><div class="c">__LOGO__<h1>&#9888;&#65039; Server nicht erreichbar</h1>
        <p>Der Blattwerk-Server konnte nicht gestartet werden.<br>Bitte das Programm schlie\u00dfen und neu starten.<br>Besteht das Problem, den Ordner <b>server</b> im Programmverzeichnis <b>pr\u00fcfen</b>.</p></div></body></html>
        """.Replace("__LOGO__", LogoHtml(64));

    private static bool SaveCurrent()
    {
        try
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
            var cur = http.GetStringAsync($"http://127.0.0.1:{port}/api/current").Result;
            using var doc = JsonDocument.Parse(cur);
            var id = doc.RootElement.GetProperty("id").GetString();
            if (string.IsNullOrEmpty(id)) return true; // nichts offen -> nichts zu speichern
            var resp = http.PostAsync($"http://127.0.0.1:{port}/api/save/{id}", null!).Result;
            dirty = false;
            return resp.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private static int GetFreePort()
    {
        var listener = System.Net.Sockets.TcpListener.Create(0);
        listener.Start();
        int port = ((System.Net.IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        return port;
    }
}

/// <summary>Rahmenloses Hauptfenster: die App-Kopfzeile ist die Titelleiste,
/// die 6px-Raender links/rechts/unten sind Groesse-Anfasspunkte.</summary>
internal sealed class HauptForm : Form
{
    private const int WM_NCHITTEST = 0x84;
    private const int HTLEFT = 10, HTRIGHT = 11, HTBOTTOM = 15, HTBOTTOMLEFT = 16, HTBOTTOMRIGHT = 17;
    private const int WM_NCLBUTTONDOWN = 0xA1;
    private const int HTCAPTION = 2;

    [DllImport("user32.dll")]
    private static extern bool ReleaseCapture();

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessage(IntPtr hWnd, int msg, int wParam, int lParam);

    /// <summary>Ziehen der Kopfzeile an das System uebergeben (inkl. Snap an Bildschirmraender).</summary>
    public void Titelziehen()
    {
        ReleaseCapture();
        _ = SendMessage(Handle, WM_NCLBUTTONDOWN, HTCAPTION, 0);
    }

    /// <summary>Maximieren/Wiederherstellen mit taskbar-sicherer Flaeche.</summary>
    public void MaximierenWechseln()
    {
        MaximizedBounds = Screen.FromControl(this).WorkingArea;
        WindowState = WindowState == FormWindowState.Maximized
            ? FormWindowState.Normal
            : FormWindowState.Maximized;
    }

    protected override void OnLoad(EventArgs e)
    {
        MaximizedBounds = Screen.FromControl(this).WorkingArea;   // taskbar-sicher
        base.OnLoad(e);
    }

    protected override void WndProc(ref Message m)
    {
        // Groesse-Raender nur im Normalzustand und nur wo das WebView2 nicht ueberdeckt
        if (m.Msg == WM_NCHITTEST && WindowState == FormWindowState.Normal && Padding.Left > 0)
        {
            int x = (short)(m.LParam.ToInt32() & 0xFFFF);
            int y = (short)((m.LParam.ToInt32() >> 16) & 0xFFFF);
            var p = PointToClient(new Point(x, y));
            bool links = p.X <= Padding.Left;
            bool rechts = p.X >= ClientSize.Width - Padding.Right;
            bool unten = p.Y >= ClientSize.Height - Padding.Bottom;
            if (links && unten) { m.Result = (IntPtr)HTBOTTOMLEFT; return; }
            if (rechts && unten) { m.Result = (IntPtr)HTBOTTOMRIGHT; return; }
            if (links) { m.Result = (IntPtr)HTLEFT; return; }
            if (rechts) { m.Result = (IntPtr)HTRIGHT; return; }
            if (unten) { m.Result = (IntPtr)HTBOTTOM; return; }
        }
        base.WndProc(ref m);
    }
}
