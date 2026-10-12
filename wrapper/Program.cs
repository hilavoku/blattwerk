using Microsoft.Web.WebView2.WinForms;
using System.Diagnostics;
using System.Drawing.Drawing2D;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace FederPDF;

internal static class Program
{
    private static int port;
    private static bool dirty;
    // UI-Sprache ("de"/"en"): Startwert aus einstellungen.json, laufend per
    // Webmessage "sprache|en" aus der UI nachgezogen (Splash/Dialoge)
    private static string uiSprache = "de";

    [STAThread]
    private static void Main(string[] args)
    {
        // Doppelklick auf eine PDF-Datei: Pfad liegt in args[0]
        string? pdfPath = args.Length > 0 ? Path.GetFullPath(args[0]) : null;
        if (pdfPath != null && !File.Exists(pdfPath)) pdfPath = null;

        port = GetFreePort();
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string serverExe = Path.Combine(baseDir, "server", "FederPDFServer.exe");
        if (!File.Exists(serverExe))
        {
            MessageBox.Show(
                "FederPDFServer.exe wurde nicht gefunden:\n" + serverExe,
                "FederPDF", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        // Gespeicherte UI-Sprache uebernehmen (steuert Splash/Fehlerseite/
        // Schliessdialog, bis die UI per "sprache|xx" nachzieht) + Start-Design
        // fuer den inneren Ziehzonen-Ring
        bool startLicht = false;
        try
        {
            string einst = Path.Combine(baseDir, "einstellungen.json");
            if (File.Exists(einst))
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(einst));
                if (doc.RootElement.TryGetProperty("sprache", out var sp)
                    && sp.ValueKind == JsonValueKind.String && sp.GetString() == "en")
                    uiSprache = "en";
                if (doc.RootElement.TryGetProperty("theme", out var th)
                    && th.ValueKind == JsonValueKind.String && th.GetString() == "light")
                    startLicht = true;
            }
        }
        catch { /* kaputte/kompatible Datei: Deutsch/Dunkel bleibt */ }

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

        // Fensterrand: SICHTBAR bleibt der duenne Trikolore-Streifen (4 px, Nutzer-
        // Wunsch v0.18.11); die ZIEHZONE ist breiter (nativen Rahmen nachempfunden,
        // Nutzer-Wunsch v0.21.4: Ecken besser greifbar) und wird in HauptForm
        // (RandAnwenden/OnPaint) DPI-abhaengig gesetzt und mit UI-Farben gefuellt.

        var form = new HauptForm
        {
            Text = pdfPath != null
                ? "FederPDF - " + Path.GetFileName(pdfPath)
                : "FederPDF",
            Width = 1450,
            Height = 940,
            StartPosition = FormStartPosition.CenterScreen,
            Font = new Font("Segoe UI", 9f),
            FormBorderStyle = FormBorderStyle.None,
            BackColor = System.Drawing.Color.FromArgb(23, 25, 29)
        };
        form.ThemeSetzen(startLicht);   // innerer Ziehzonen-Ring im gespeicherten Design

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
            // Padding (Ziehzone) pflegt HauptForm.RandAnwenden selbst (vor dem
            // Layout, im OnResize) - hier nur die WebView-Flaeche nachziehen
            WebViewAufInnenflaecheSetzen(form, webView);
        };

        form.Shown += (_, _) =>
        {
            // Nach dem ersten Anzeigen einmal explizit setzen: Beim Wiederherstellen
            // der Groesse aus fenster.json skaliert das automatische Dock das
            // WebView2 mit falscher DPI-Basis (Control dann nur CSS- statt
            // physischer Groesse) - Klicks landen daneben (DPI-De-Sync).
            WebViewAufInnenflaecheSetzen(form, webView);
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
                    else if (msg != null && msg.StartsWith("sprache|")) uiSprache = msg.Substring(8) == "en" ? "en" : "de";
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
                    else if (msg == "theme|light" || msg == "theme|dark")
                    {
                        // Fensterrand ist seit v0.16.9 in beiden Designs der
                        // Schwarz-Rot-Gold-Verlauf; der INNERE Ziehzone-Ring
                        // faerbt sich seit v0.21.4 passend zum Design
                        form.ThemeSetzen(msg == "theme|light");
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
                    "FederPDF", MessageBoxButtons.OK, MessageBoxIcon.Error);
                form.Close();
            }
        };

        form.FormClosing += (_, e) =>
        {
            if (!dirty) return;
            bool en = uiSprache == "en";
            var choice = MessageBox.Show(
                en ? "There are unsaved changes.\n\n" +
                     "Yes = Save and close\n" +
                     "No = Close without saving\n" +
                     "Cancel = Back to the document"
                   : "Es gibt nicht gespeicherte \u00c4nderungen.\n\n" +
                     "Ja = Speichern und schließen\n" +
                     "Nein = Ohne Speichern schließen\n" +
                     "Abbrechen = Zurück zum Dokument",
                en ? "Unsaved changes" : "Ungespeicherte \u00c4nderungen",
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
                        en ? "Saving failed. Close anyway?" : "Speichern fehlgeschlagen. Trotzdem schließen?",
                        "FederPDF", MessageBoxButtons.YesNo, MessageBoxIcon.Error);
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
        .logo{display:block;margin:0 auto 16px}
        .logo.emoji{line-height:1}
        h1{font-weight:600;margin:0 0 8px}
        p{color:#97a0af;margin:0}
        .bar{width:140px;height:3px;background:#2c313a;border-radius:2px;margin:18px auto 0;overflow:hidden}
        .bar i{display:block;width:40%;height:100%;background:#4cc2ff;border-radius:2px;animation:sl 1.1s infinite linear}
        @keyframes sl{from{transform:translateX(-100%)}to{transform:translateX(350%)}}
        </style></head><body><div class="c">__LOGO__<h1>FederPDF</h1><p>__START__</p><div class="bar"><i></i></div></body></html>
        """.Replace("__LOGO__", LogoHtml(84))
           .Replace("__START__", uiSprache == "en" ? "starting &hellip;" : "wird gestartet &hellip;");

    private static string ErrorHtml() => """
        <!DOCTYPE html><html><head><meta charset="utf-8"><style>
        html,body{height:100%;margin:0}
        body{background:#17191d;color:#e6e9ee;font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center}
        .c{text-align:center;max-width:420px}
        .logo{display:block;margin:0 auto 18px}
        .logo.emoji{line-height:1}
        h1{font-weight:600;margin:0 0 10px}
        p{color:#97a0af;line-height:1.6;margin:0}
        </style></head><body><div class="c">__LOGO__<h1>&#9888;&#65039; __ERRTITEL__</h1>
        <p>__ERRTEXT__</p></div></body></html>
        """.Replace("__LOGO__", LogoHtml(64))
           .Replace("__ERRTITEL__", uiSprache == "en" ? "Server not reachable" : "Server nicht erreichbar")
           .Replace("__ERRTEXT__", uiSprache == "en"
               ? "The FederPDF server could not be started.<br>Please close the program and start it again.<br>If the problem persists, check the <b>server</b> folder in the program directory."
               : "Der FederPDF-Server konnte nicht gestartet werden.<br>Bitte das Programm schlie\u00dfen und neu starten.<br>Besteht das Problem, den Ordner <b>server</b> im Programmverzeichnis <b>pr\u00fcfen</b>.");

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

    /// <summary>WebView2 manuell auf die Clientflaeche abzueglich Rahmen setzen.
    /// Umgeht den DPI-Skalier-Bug beim Wiederherstellen aus fenster.json, bei dem
    /// das Dock-Fill-Control in CSS- statt physischer Groesse landet (Klick-De-Sync).</summary>
    private static void WebViewAufInnenflaecheSetzen(Form form, WebView2 webView)
    {
        var p = form.Padding;
        webView.Bounds = new Rectangle(p.Left, p.Top,
            form.ClientSize.Width - p.Horizontal,
            form.ClientSize.Height - p.Vertical);
    }
}

/// <summary>Rahmenloses Hauptfenster: die App-Kopfzeile ist die Titelleiste,
/// die 6px-Raender links/rechts/unten sind Groesse-Anfasspunkte.</summary>
internal sealed class HauptForm : Form
{
    private const int WM_NCHITTEST = 0x84;
    private const int HTLEFT = 10, HTRIGHT = 11, HTTOP = 12, HTTOPLEFT = 13, HTTOPRIGHT = 14,
                      HTBOTTOM = 15, HTBOTTOMLEFT = 16, HTBOTTOMRIGHT = 17;
    private const int WM_NCLBUTTONDOWN = 0xA1;
    private const int HTCAPTION = 2;
    private const int WM_DPICHANGED = 0x02E0;
    private const int WM_GETDPISCALEDSIZE = 0x02E4;

    [StructLayout(LayoutKind.Sequential)]
    private struct VorschlagsRect
    {
        public int Links, Oben, Rechts, Unten;
    }

    // lParam von WM_GETDPISCALEDSIZE ist eine SIZE-Struktur (Breite/Hoehe),
    // KEIN Rect - ein Rect-Zugriff liefert Muell und das System faellt dann
    // auf unskaliert zurueck (Diagnose 11.10.2026)
    [StructLayout(LayoutKind.Sequential)]
    private struct SkalierteGroesse
    {
        public int Breite, Hoehe;
    }

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

    // Markenfarben wie das Band ueber der Kopfzeile (index.html header::before)
    private static readonly Color RandSchwarz = Color.FromArgb(26, 26, 26);
    private static readonly Color RandRot = Color.FromArgb(221, 0, 0);
    private static readonly Color RandGold = Color.FromArgb(255, 204, 0);

    // Innerer Ziehzone-Ring in den Farben der ANGRENZENDEN UI (v0.21.4): oben
    // Kopfzeilen-Ton, sonst Viewer-Hintergrund - dunkel wie hell nahezu unsichtbar
    private static readonly Color InnenDunkel = Color.FromArgb(23, 25, 29);      // #17191d
    private static readonly Color InnenObenDunkel = Color.FromArgb(31, 32, 36);  // #1f2024
    private static readonly Color InnenHell = Color.FromArgb(238, 241, 245);     // #eef1f5
    private static readonly Color InnenObenHell = Color.White;

    private static bool licht;

    public void ThemeSetzen(bool hell)
    {
        licht = hell;
        if (greifRing != null)
        {
            greifRing.BackColor = hell ? InnenObenHell : InnenObenDunkel;
            greifRing.Invalidate();
        }
        if (IsHandleCreated) Invalidate();
    }

    // Ziehzone in PHYSISCHEN Pixeln, an native Rahmen angelehnt (8 px bei
    // 100 %, 12 px bei 150 %) - die v0.18.11er 4 px waren halb so breit wie
    // bei jedem anderen Programm (Nutzer: "Ecke schwer zu treffen")
    private int ZiehzonePx() => Math.Max(8, (int)Math.Round(8.0 * DeviceDpi / 96.0));

    /// <summary>Ziehzone (Padding) je Fensterzustand setzen: maximiert randlos,
    /// sonst der breite unsichtbare Greifring. Steuert WebView-Flaeche UND
    /// WM_NCHITTEST.</summary>
    public void RandAnwenden()
    {
        Padding = WindowState == FormWindowState.Maximized ? Padding.Empty : new Padding(ZiehzonePx());
    }

    // Sichtbarer Greifring unten rechts (Nutzer-Wunsch v0.21.4, "kleines
    // Rechteck"): klassische Diagonalrillen, Klick+Ziehen loest den NATIVEN
    // Groesse-Zug an der Ecke aus (gleiches Muster wie Titelziehen/HTCAPTION)
    private Control greifRing;

    private int GreifringPx() => Math.Max(16, (int)Math.Round(16.0 * DeviceDpi / 96.0));

    private void GreifringAnlegen()
    {
        greifRing = new Control
        {
            Size = new Size(GreifringPx(), GreifringPx()),
            Cursor = Cursors.SizeNWSE,
            BackColor = licht ? InnenObenHell : InnenObenDunkel   // Fussleisten-Ton
        };
        greifRing.Paint += (s, e) =>
        {
            int g = greifRing.Width;
            using var stift = new Pen(licht ? Color.FromArgb(98, 108, 122) : Color.FromArgb(156, 151, 140), 2);
            int r = g - 3;
            for (int i = 1; i <= 3; i++)
            {
                int abstand = i * g / 4;
                e.Graphics.DrawLine(stift, r - abstand, r, r, r - abstand);
            }
        };
        greifRing.MouseDown += (s, e) =>
        {
            if (e.Button == MouseButtons.Left)
            {
                ReleaseCapture();
                _ = SendMessage(Handle, WM_NCLBUTTONDOWN, HTBOTTOMRIGHT, 0);
            }
        };
        Controls.Add(greifRing);
        greifRing.BringToFront();   // ueber dem WebView2: nur 16 px Ecke, dahinter liegt die leere Fussleiste
    }

    private void GreifringPlatzieren()
    {
        if (greifRing == null) return;
        bool normal = WindowState == FormWindowState.Normal;
        greifRing.Visible = normal;   // maximiert: kein Größengriff
        if (normal)
        {
            greifRing.Size = new Size(GreifringPx(), GreifringPx());
            greifRing.Location = new Point(ClientSize.Width - greifRing.Width, ClientSize.Height - greifRing.Height);
        }
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        int zone = Padding.Left;
        if (zone == 0) return;   // maximiert: kein Rand
        // Sichtbar bleibt der duenne Trikolore-Streifen (4 px, Nutzer-Wunsch
        // v0.18.11). Die breitere Ziehzone (v0.21.4) wird mit den Farben der
        // ANGRENZENDEN UI gefuellt - oben Kopfzeilen-Ton, sonst Viewer-
        // Hintergrund - und ist darum nahezu unsichtbar.
        int sichtbar = Math.Min(4, zone);
        using (var bo = new SolidBrush(licht ? InnenObenHell : InnenObenDunkel))
            g.FillRectangle(bo, 0, 0, Width, zone);
        using (var bi = new SolidBrush(licht ? InnenHell : InnenDunkel))
        {
            g.FillRectangle(bi, 0, zone, zone, Height - zone);             // links
            g.FillRectangle(bi, Width - zone, zone, zone, Height - zone);  // rechts
            g.FillRectangle(bi, 0, Height - zone, Width, zone);            // unten
        }
        // Verlaufskamm schwarz - rot - gold wie das CSS-Band (50% Rot). Der Rand
        // laeuft als NAHTLOSER Umlauf ums Fenster (an jeder Ecke treffen gleiche
        // Farben aufeinander): oben schwarz->gold, rechts gold->schwarz,
        // unten gold->schwarz (in Leserichtung), links schwarz->gold.
        var kamm = new ColorBlend
        {
            Positions = new float[] { 0f, 0.5f, 1f },
            Colors = new[] { RandSchwarz, RandRot, RandGold }
        };
        var kammUmgekehrt = new ColorBlend
        {
            Positions = new float[] { 0f, 0.5f, 1f },
            Colors = new[] { RandGold, RandRot, RandSchwarz }
        };
        using (var po = new LinearGradientBrush(new Rectangle(0, 0, Width, sichtbar), RandSchwarz, RandGold, LinearGradientMode.Horizontal))
        { po.InterpolationColors = kamm; g.FillRectangle(po, 0, 0, Width, sichtbar); }
        using (var pr = new LinearGradientBrush(new Rectangle(Width - sichtbar, 0, sichtbar, Height), RandGold, RandSchwarz, LinearGradientMode.Vertical))
        { pr.InterpolationColors = kammUmgekehrt; g.FillRectangle(pr, Width - sichtbar, 0, sichtbar, Height); }
        using (var pu = new LinearGradientBrush(new Rectangle(0, Height - sichtbar, Width, sichtbar), RandGold, RandSchwarz, LinearGradientMode.Horizontal))
        { pu.InterpolationColors = kammUmgekehrt; g.FillRectangle(pu, 0, Height - sichtbar, Width, sichtbar); }
        using (var pl = new LinearGradientBrush(new Rectangle(0, 0, sichtbar, Height), RandSchwarz, RandGold, LinearGradientMode.Vertical))
        { pl.InterpolationColors = kamm; g.FillRectangle(pl, 0, 0, sichtbar, Height); }
    }

    protected override void OnResize(EventArgs e)
    {
        RandAnwenden();   // Ziehzone VOR dem Layout (DPI-abhaengig; maximiert randlos)
        base.OnResize(e);
        GreifringPlatzieren();   // Position/Groesse nach dem Layout (nach base, ClientSize frisch)
        // Groessenaenderung: Verlaufsrand STRECKENWEISE komplett neu zeichnen -
        // Windows malt sonst nur die freigelegten Streifen, an den Grenzflaechen
        // zum WebView2 bleiben weisse Reststriche stehen. Zweites Invalidate
        // NACH dem Layout (falls das WebView2 den Rand zwischenzeitlich
        // uebermalt hat) - nur mit fertigen Fensterhandle, sonst wuerfe
        // BeginInvoke beim Start (fenster.json-Restore) die App wegwerfen.
        Invalidate();
        if (IsHandleCreated)
        {
            try { BeginInvoke((Action)(() => Invalidate())); } catch { }
        }
    }

    protected override void OnLoad(EventArgs e)
    {
        DoubleBuffered = true;   // randloses Fenster: Verlaufsrand ohne Flackern
        MaximizedBounds = Screen.FromControl(this).WorkingArea;   // taskbar-sicher
        GreifringAnlegen();
        RandAnwenden();   // erste Ziehzone (Padding steuert WebView-Flaeche + WM_NCHITTEST)
        GreifringPlatzieren();
        base.OnLoad(e);
    }

    protected override void WndProc(ref Message m)
    {
        // Monitorwechsel auf andere Skalierung, Teil 1: WinForms beantwortet
        // WM_GETDPISCALEDSIZE mit der UNVERAENDERTEN Fensterflaeche - Windows
        // schlaegt dann in WM_DPICHANGED genau dieses Rechteck vor, das Fenster
        // behaelt also seine Pixelmasse (auf dem Zielfenster zu gross bzw.
        // zu klein) und das WebView2 bleibt auf dem Rueckweg im alten
        // Rastermassstab haengen ("alles sehr klein", Nutzer-Fall 11.10.2026).
        // Wir antworten deshalb SELBST mit linear skaliertem Rechteck
        // (neue DPI / alte DPI) - nur im Normalzustand, maximiert regelt das
        // System selbst.
        if (m.Msg == WM_GETDPISCALEDSIZE && WindowState == FormWindowState.Normal
            && Marshal.PtrToStructure(m.LParam, typeof(SkalierteGroesse)) is SkalierteGroesse anfrage)
        {
            double faktor = (double)(m.WParam.ToInt32() & 0xFFFF) / DeviceDpi;
            anfrage.Breite = (int)Math.Round(anfrage.Breite * faktor);
            anfrage.Hoehe = (int)Math.Round(anfrage.Hoehe * faktor);
            Marshal.StructureToPtr(anfrage, m.LParam, false);
            m.Result = (IntPtr)1;
            return;
        }
        // Teil 2: den (jetzt sinnvollen) Vorschlag tatsaechlich uebernehmen.
        // Erst base lassen (interne Font-/Skalierungspflege), dann anwenden.
        if (m.Msg == WM_DPICHANGED)
        {
            base.WndProc(ref m);
            if (WindowState == FormWindowState.Normal
                && Marshal.PtrToStructure(m.LParam, typeof(VorschlagsRect)) is VorschlagsRect v)
            {
                Bounds = new Rectangle(v.Links, v.Oben, v.Rechts - v.Links, v.Unten - v.Oben);
                Invalidate();
            }
            return;
        }
        // Groesse-Raender nur im Normalzustand und nur wo das WebView2 nicht ueberdeckt
        if (m.Msg == WM_NCHITTEST && WindowState == FormWindowState.Normal && Padding.Left > 0)
        {
            int x = (short)(m.LParam.ToInt32() & 0xFFFF);
            int y = (short)((m.LParam.ToInt32() >> 16) & 0xFFFF);
            var p = PointToClient(new Point(x, y));
            bool links = p.X <= Padding.Left;
            bool rechts = p.X >= ClientSize.Width - Padding.Right;
            bool oben = p.Y <= Padding.Top;
            bool unten = p.Y >= ClientSize.Height - Padding.Bottom;
            if (links && oben) { m.Result = (IntPtr)HTTOPLEFT; return; }
            if (rechts && oben) { m.Result = (IntPtr)HTTOPRIGHT; return; }
            if (links && unten) { m.Result = (IntPtr)HTBOTTOMLEFT; return; }
            if (rechts && unten) { m.Result = (IntPtr)HTBOTTOMRIGHT; return; }
            if (oben) { m.Result = (IntPtr)HTTOP; return; }
            if (links) { m.Result = (IntPtr)HTLEFT; return; }
            if (rechts) { m.Result = (IntPtr)HTRIGHT; return; }
            if (unten) { m.Result = (IntPtr)HTBOTTOM; return; }
        }
        base.WndProc(ref m);
    }
}
