# FederPDF-Testsuite: startet den gebauten Server und prueft die API
# end-to-end (89 Checks: Signaturen, Text, Formen, Markieren, OCR, KI,
# Bilder, Undo, Speichern). Sie erzeugt eigene Wegwerf-Signaturen und
# Fixtures — Nutzerdaten werden nie angefasst.
#
# Ausfuehrung:   py -3.14 tests/pdfwerkstatt_test.py
#   (erwartet die installierte App unter dem Standardpfad; abweichend:
#    PW_EXE=C:\Pfad\zu\PdfWerkstattServer.exe py -3.14 tests/pdfwerkstatt_test.py)
# Benoetigt: requests, pymupdf, pillow  (pip install requests pymupdf pillow)
import os
import shutil
import subprocess
import tempfile
import time
import sys

import requests

EXE = os.environ.get("PW_EXE", r"C:\Anwendungen\PDF-Werkstatt\server\PdfWerkstattServer.exe")
DEMO = os.path.join(os.path.dirname(EXE), "demo", "demo.pdf")
PORT = 8515
BASE = f"http://127.0.0.1:{PORT}"
TMPD = tempfile.gettempdir()
FIXDIR = os.path.join(TMPD, "pw_test_fixtures")

failures = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL") + f": {name}" + (f" [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


# Isolation: frisches Demo-Dokument erzwingen (alte User-Reste weg)
if os.path.isfile(DEMO):
    os.remove(DEMO)

srv = subprocess.Popen([EXE, "--port", str(PORT)], creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(60):
        time.sleep(0.5)
        try:
            if requests.get(BASE + "/api/health", timeout=2).json().get("ok"):
                break
        except Exception:
            pass
    else:
        print("FAIL: Server startet nicht")
        sys.exit(1)
    check("Server hochgefahren", True)

    # Über-Dialog (Klick auf Logo/FederPDF): Versions-Endpunkt + Logo-Route
    v = requests.get(BASE + "/api/version", timeout=5).json()
    check("Versions-Endpunkt", v.get("name") == "FederPDF" and len(v.get("version", "")) >= 5 and bool(v.get("pymupdf")), str(v))
    r = requests.get(BASE + "/logo.png", timeout=5)
    check("Logo fuer Über-Dialog", r.status_code == 200 and r.headers.get("content-type") == "image/png")

    d = requests.get(BASE + "/api/demo", timeout=15).json()
    did = d["id"]
    check("Demo offen", d["pages"] == 3 and len(d["toc"]) == 4)

    # Eigene Wegwerf-Signatur anlegen (Nutzer-Signaturen werden NIE angefasst)
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGBA", (300, 100), (20, 60, 160, 255)).save(buf, "PNG")
    r = requests.post(f"{BASE}/api/signature/upload",
                      files={"file": ("TestSig.png", buf.getvalue(), "image/png")},
                      data={"remove_bg": "0"}, timeout=10).json()
    check("Test-Signatur hochgeladen", r.get("ok"), str(r))
    ts1 = r["file"]

    sigs = requests.get(BASE + "/api/signatures", timeout=5).json()
    check("Signatur gelistet", any(s["file"] == ts1 for s in sigs), str(len(sigs)))

    # Signatur als Annotation (beweglich)
    r = requests.post(f"{BASE}/api/stamp/{did}", data={
        "page": "0", "x": "100", "y": "100", "width": "140", "fname": ts1}, timeout=10).json()
    check("Stempel-Annot angelegt", r.get("ok") and r.get("xref", 0) > 0, str(r))
    sig_xref = r.get("xref")
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    sig = next((a for a in annots if a["xref"] == sig_xref), None)
    check("Stempel gelistet als sign", sig is not None and sig["type"] == "sign", str(annots))
    r = requests.post(f"{BASE}/api/annot/move/{did}", data={
        "page": "0", "xref": str(sig_xref), "rect": "[300,200,440,260]"}, timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    sig2 = next((a for a in annots if a["xref"] == sig_xref), None)
    check("Stempel verschoben", r.get("ok") and sig2 and abs(sig2["rect"][0] - 300) < 1, str(sig2))

    # Signatur umbenennen -> Verweis in gesetzter Annotation muss mitziehen
    r = requests.post(f"{BASE}/api/signature/rename", data={
        "old": ts1, "new": "TestSig Umbenannt"}, timeout=10).json()
    check("Signatur umbenannt", r.get("ok") and r.get("file") == "TestSig Umbenannt.png", str(r))
    ts2 = r["file"]
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    sig3 = next((a for a in annots if a["xref"] == sig_xref), None)
    check("Stempel-Verweis mitumbenannt", sig3 and sig3.get("file") == ts2, str(sig3))

    # Signatur loeschen -> Verweis geleert (Platzhalter), Datei weg
    r = requests.post(f"{BASE}/api/signature/delete", data={"fname": ts2}, timeout=10).json()
    sigs_after = requests.get(f"{BASE}/api/signatures", timeout=5).json()
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    sig4 = next((a for a in annots if a["xref"] == sig_xref), None)
    check("Signatur geloescht + Verweis geleert",
          r.get("ok") and not any(s["file"] == ts2 for s in sigs_after)
          and sig4 and sig4.get("file") == "", str(sig4))

    # Freitext-Annotation mit Font/Stil/Groesse
    r = requests.post(f"{BASE}/api/annot/text/{did}", data={
        "page": "0", "rect": "[100,300,300,330]", "text": "Bemerkung in Fett",
        "size": "14", "font": "hebo", "color": "0.1,0.1,0.6"}, timeout=10).json()
    check("Freitext angelegt", r.get("ok") and r.get("xref", 0) > 0, str(r))
    txt_xref = r.get("xref")
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    txt = next((a for a in annots if a["xref"] == txt_xref), None)
    check("Freitext-Eigenschaften", txt and txt["font"] == "hebo" and txt["size"] == 14 and "Bemerkung" in txt["text"], str(txt))
    # Text aendern (re-create mit xref)
    r = requests.post(f"{BASE}/api/annot/text/{did}", data={
        "page": "0", "rect": "[100,300,300,330]", "text": "Geaendert kursiv",
        "size": "12", "font": "tiit", "color": "1,0,0", "xref": str(txt_xref)}, timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    txt2 = next((a for a in annots if a["xref"] == r.get("xref")), None)
    check("Freitext geaendert (neu erzeugt)", txt2 and "Geaendert" in txt2["text"] and txt2["font"] == "tiit", str(txt2))

    # Freitext verschieben - Position muss BLEIBEN (Regressionsbug: sprang zurueck)
    ft_xref = txt2["xref"]
    r = requests.post(f"{BASE}/api/annot/move/{did}", data={
        "page": "0", "xref": str(ft_xref), "rect": "[400,500,600,535]"}, timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    txt3 = next((a for a in annots if a["xref"] == ft_xref), None)
    check("Freitext verschoben und geblieben", r.get("ok") and txt3 and abs(txt3["rect"][0] - 400) < 1, str(txt3))

    # Formularfeld mit Rect (fuer Eingabe direkt aufs Papier)
    fields = requests.get(f"{BASE}/api/fields/{did}", timeout=10).json()
    vor = next((f for f in fields if f["name"] == "Vorname"), None)
    check("Feld mit Position", vor is not None and len(vor.get("rect", [])) == 4, str(vor))
    requests.post(f"{BASE}/api/field/{did}", data={"page": "2", "name": "Vorname", "value": "Guido"}, timeout=10)
    fields = requests.get(f"{BASE}/api/fields/{did}", timeout=10).json()
    check("Feld gesetzt", next((f for f in fields if f["name"] == "Vorname"), {}).get("value") == "Guido")

    # ---------- Rueckgaengig (vor dem Seitenloeschen: Formularfelder liegen auf Seite 3) ----------
    r = requests.post(f"{BASE}/api/annot/text/{did}", data={
        "page": "0", "rect": "[80,80,240,110]", "text": "UndoProbe", "size": "12",
        "font": "helv", "color": "0,0,0"}, timeout=10).json()
    ux = r["xref"]
    u = requests.post(f"{BASE}/api/undo/{did}", timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    check("Undo: Text entfernt", u.get("undone") and not any(a["xref"] == ux for a in annots), str(u))

    # Eigene Wegwerf-Signatur fuer Undo-Stempel
    buf = io.BytesIO()
    Image.new("RGBA", (300, 100), (160, 20, 60, 255)).save(buf, "PNG")
    r = requests.post(f"{BASE}/api/signature/upload",
                      files={"file": ("UndoSig.png", buf.getvalue(), "image/png")},
                      data={"remove_bg": "0"}, timeout=10).json()
    usig = r["file"]
    r = requests.post(f"{BASE}/api/stamp/{did}", data={
        "page": "0", "x": "500", "y": "600", "width": "120", "fname": usig}, timeout=10).json()
    s3 = r["xref"]
    orig = r["rect"]
    requests.post(f"{BASE}/api/annot/move/{did}", data={
        "page": "0", "xref": str(s3), "rect": "[50,50,190,110]"}, timeout=10)
    u = requests.post(f"{BASE}/api/undo/{did}", timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{did}/0", timeout=10).json()
    s3b = next((a for a in annots if a["xref"] == s3), None)
    check("Undo: Verschieben zurueck", u.get("undone") and s3b and abs(s3b["rect"][0] - orig[0]) < 1, str(s3b))

    requests.post(f"{BASE}/api/field/{did}", data={"page": "2", "name": "Nachname", "value": "Temp"}, timeout=10)
    u = requests.post(f"{BASE}/api/undo/{did}", timeout=10).json()
    fields = requests.get(f"{BASE}/api/fields/{did}", timeout=10).json()
    nach = next((f for f in fields if f["name"] == "Nachname"), {})
    check("Undo: Feld zurueck", nach.get("value") == "", str(nach))

    # --- Speichern unter ---
    ziel = os.path.join(TMPD, "pw_test_saveas.pdf")
    if os.path.isfile(ziel):
        os.remove(ziel)
    r = requests.get(f"{BASE}/api/saveas/{did}", params={"path": ziel}, timeout=15)
    check("Speichern unter: Kopie erzeugt", r.ok and os.path.isfile(ziel) and os.path.getsize(ziel) > 1000,
          f"status={r.status_code}")
    curj = requests.get(f"{BASE}/api/current", timeout=5).json()
    check("Speichern unter: neue Datei ist Arbeitsdokument", curj.get("name") == "pw_test_saveas.pdf", str(curj.get("name")))
    ann_sofort = requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json()
    check("Speichern unter: Annotationen bleiben greifbar", any(a["type"] == "sign" for a in ann_sofort),
          str(len(ann_sofort)))

    # --- Passwortgeschtzte Signatur: verschluesselt gespeichert, stampbar ---
    buf2 = io.BytesIO()
    Image.new("RGBA", (200, 80), (160, 30, 30, 255)).save(buf2, "PNG")
    r = requests.post(f"{BASE}/api/signature/upload",
                      files={"file": ("PwSig.png", buf2.getvalue(), "image/png")},
                      data={"remove_bg": "0", "password": "geheim"}, timeout=10).json()
    pwfile = r.get("file", "")
    check("Geschuetzte Signatur als .pwdsig", r.get("ok") and pwfile.endswith(".pwdsig"), str(r))
    sigdir = os.path.join(os.path.dirname(EXE), "signatures")
    inhalt = open(os.path.join(sigdir, pwfile), "rb").read()
    check("Datei verschluesselt (kein Klartext-PNG)", b"\x89PNG" not in inhalt and b"token" in inhalt)
    r = requests.post(f"{BASE}/api/stamp/{did}", data={"page": "0", "x": "100", "y": "400",
                      "width": "120", "fname": pwfile}, timeout=10)
    check("Stempeln mit (frisch entsperrter) Pw-Sig", r.ok and r.json().get("xref", 0) > 0, str(r.status_code))
    pwx = r.json().get("xref")

    # --- Drehen 90 Grad + Undo ---
    an0 = next(a for a in requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json() if a["xref"] == pwx)
    r = requests.post(f"{BASE}/api/annot/rotate/{did}", data={"page": "0", "xref": str(pwx), "delta": "90"}, timeout=10)
    an1 = next((a for a in requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json() if a["xref"] == pwx), None)
    check("Signatur gedreht (Breite/Hoehe getauscht, rot=90)",
          r.ok and an1 and an1.get("rot") == 90 and abs((an1["rect"][3]-an1["rect"][1]) - (an0["rect"][2]-an0["rect"][0])) < 1,
          str(an1))
    u = requests.post(f"{BASE}/api/undo/{did}", timeout=10).json()
    an2 = next((a for a in requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json() if a["xref"] == pwx), None)
    check("Undo: Drehung zurueck", u.get("undone") and an2 and an2.get("rot") == 0, str(an2))

    # --- Freier Winkel (Zielwert) + gedrehtes Vorschaubild ---
    import math as _m
    r = requests.post(f"{BASE}/api/annot/rotate/{did}", data={"page": "0", "xref": str(pwx), "to": "37.5"}, timeout=10)
    an3 = next((a for a in requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json() if a["xref"] == pwx), None)
    # erwartete Huelle: Bild 200x80 um 37.5 Grad -> (200*c+80*s, 200*s+80*c)
    c, s = _m.cos(_m.radians(37.5)), _m.sin(_m.radians(37.5))
    erw = (200 * c + 80 * s) / (200 * s + 80 * c)      # Breite/Hoehe-Verhaeltnis
    ist = (an3["rect"][2] - an3["rect"][0]) / (an3["rect"][3] - an3["rect"][1]) if an3 else 0
    check("Freier Winkel 37.5 (rot + Huellen-Verhaeltnis)",
          r.ok and an3 and abs(an3["rot"] - 37.5) < 0.01 and abs(ist - erw) < 0.05, f"rot={an3 and an3['rot']} vh={ist:.2f}/{erw:.2f}")
    r = requests.get(f"{BASE}/api/signature/file/PwSig.pwdsig?rot=37.5", timeout=10)
    check("Gedrehtes Vorschaubild lieferbar", r.ok and r.content[:4] == b"\x89PNG", str(r.status_code))
    u = requests.post(f"{BASE}/api/undo/{did}", timeout=10).json()
    an4 = next((a for a in requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json() if a["xref"] == pwx), None)
    check("Undo: freier Winkel zurueck", u.get("undone") and an4 and an4.get("rot") == 0, str(an4 and an4.get("rot")))

    # --- Einbrennen (flatten): Annotationen weg, Formularfelder bleiben ---
    r = requests.post(f"{BASE}/api/save/{did}?flatten=1", timeout=20).json()
    check("Einbrennen-Speichern ok", r.get("ok") and r.get("flattened"), str(r))
    annots_flach = requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json()
    check("Nach Einbrennen keine beweglichen Objekte", not annots_flach, str(len(annots_flach)))
    flds = requests.get(f"{BASE}/api/fields/{did}", timeout=5).json()
    check("Formularfelder ueberleben Einbrennen", any(f["name"] == "Vorname" for f in flds), str(len(flds)))

    # --- Speichern unter MIT Einbrennen ---
    ziel2 = os.path.join(TMPD, "pw_test_saveas_burn.pdf")
    if os.path.isfile(ziel2):
        os.remove(ziel2)
    r = requests.post(f"{BASE}/api/stamp/{did}", data={"page": "0", "x": "150", "y": "500",
                      "width": "100", "fname": pwfile}, timeout=10)
    check("Stempel vor Speichern-unter gesetzt", r.ok, str(r.status_code))
    r = requests.get(f"{BASE}/api/saveas/{did}", params={"path": ziel2, "flatten": 1}, timeout=20).json()
    check("Speichern unter mit Einbrennen", r.get("ok") and r.get("flattened") and os.path.isfile(ziel2), str(r))
    check("Speichern-unter-Einbrennen: keine beweglichen Objekte",
          not requests.get(f"{BASE}/api/annots/{did}/0", timeout=5).json())

    # --- Originaltext editieren (echter Text, kein Bild) ---
    import json as _json
    alter = "FederPDF Demo-Dokument"
    zeilen0 = requests.get(f"{BASE}/api/text/{did}/0", timeout=5).json()["lines"]
    zeile = next((l for l in zeilen0 if alter in l["t"]), None)
    r = requests.get(f"{BASE}/api/textspan/{did}/0",
                     params={"x0": zeile["x0"], "y0": zeile["y0"], "x1": zeile["x1"], "y1": zeile["y1"]},
                     timeout=5).json()
    check("Textspanne erkannt (Groesse/Farbe)", abs(r.get("size", 0) - 18) < 3 and r.get("color") == [0, 0, 0], str(r))
    r = requests.post(f"{BASE}/api/text/replace/{did}", data={
        "page": "0", "rect": _json.dumps([zeile["x0"], zeile["y0"], zeile["x1"], zeile["y1"]]),
        "text": "FederPDF Demo GEANDERT"}, timeout=15)
    check("Originaltext ersetzt", r.ok and r.json().get("size", 0) > 10, str(r.status_code))
    t0 = requests.get(f"{BASE}/api/text/{did}/0", timeout=5).json()["lines"]
    check("Neuer Text im Seiteninhalt", any("GEANDERT" in l["t"] for l in t0), str(t0[:2]))
    check("Alter Text weg", not any(alter in l["t"] for l in t0))
    u = requests.post(f"{BASE}/api/undo/{did}", timeout=15).json()
    t0 = requests.get(f"{BASE}/api/text/{did}/0", timeout=5).json()["lines"]
    check("Undo: Originaltext zurueck",
          u.get("undone") and any(alter in l["t"] for l in t0) and not any("GEANDERT" in l["t"] for l in t0))

    # Seite loeschen
    r = requests.post(f"{BASE}/api/deletepage/{did}", data={"page": "2"}, timeout=10).json()
    check("Seite geloescht", r.get("ok") and r.get("pages") == 2, str(r))

    # Druckansicht (enthaelt eingebettete Seitenbilder)
    pr = requests.get(f"{BASE}/api/print/{did}", timeout=60)
    check("Druckansicht erzeugt", pr.status_code == 200 and "data:image/png;base64" in pr.text)

    save = requests.post(f"{BASE}/api/save/{did}", timeout=15).json()
    check("Speichern", save.get("ok", False))

    # ---------- v0.18: Markierungen, Formen, OCR, KI, Dokument-Schriften ----------
    # Frisches Demo als eigenes Arbeitsdokument: die v0.18-Checks duerfen den
    # obigen Ablauf (Drehen, Einbrennen, Ersetzen) nicht beeinflussen und umgekehrt.
    vdid = requests.get(BASE + "/api/demo", timeout=15).json()["id"]
    # Woerter-Quads: duennes waagerechtes Band genau auf die Zeilenmitte gelegt
    t0 = requests.get(f"{BASE}/api/text/{vdid}/0", timeout=10).json()
    zl = next((l for l in t0["lines"] if "Markiere mich" in l["t"]), None)
    ym = round((zl["y0"] + zl["y1"]) / 2, 1) if zl else 116.0
    q = requests.get(f"{BASE}/api/textquads/{vdid}/0",
                     params={"x0": 70, "y0": ym, "x1": 300, "y1": ym + 0.3}, timeout=10).json()
    check("Textquads: duennes Band erfasst Woerter", len(q.get("quads", [])) >= 3 and "Markiere" in q.get("text", ""), str(q)[:90])
    quads = str(q["quads"])
    r = requests.post(f"{BASE}/api/annot/markup/{vdid}", data={
        "page": "0", "art": "h", "quads": quads, "farbe": "FFD300",
        "deckkraft": "45", "staerke": "1"}, timeout=10).json()
    mk_x = r.get("xref", 0)
    check("Marker angelegt", r.get("ok") and mk_x > 0, str(r))
    r = requests.post(f"{BASE}/api/annot/markup/{vdid}", data={
        "page": "0", "art": "u", "quads": quads, "farbe": "0000FF",
        "deckkraft": "100", "staerke": "2.5"}, timeout=10).json()
    un_x = r.get("xref", 0)
    check("Unterstreichen angelegt", r.get("ok") and un_x > 0, str(r))
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    subs = sorted(a["sub"] for a in annots if a["type"] == "markup")
    check("Markierungen gelistet (h+u)", subs == ["h", "u"], str(subs))
    mke = next((a for a in annots if a.get("xref") == mk_x), {})
    check("Marker-Stil lesbar", mke.get("farbe") == "FFD300" and abs(mke.get("deckkraft", 0) - 45) < 1, str(mke)[:90])

    # Formen: Rechteck, Pfeil, Tinte
    r = requests.post(f"{BASE}/api/annot/shape/{vdid}", data={
        "page": "0", "typ": "rect", "rect": "[100,380,220,440]", "punkte": "[]",
        "breite": "2.5", "farbe": "E0242F", "fuellung": "FFFF00", "deckkraft": "100"}, timeout=10).json()
    rect_x = r.get("xref", 0)
    check("Rechteck angelegt", r.get("ok") and rect_x > 0, str(r))
    r = requests.post(f"{BASE}/api/annot/shape/{vdid}", data={
        "page": "0", "typ": "arrow", "rect": "[0,0,0,0]", "punkte": "[[100,470],[260,500]]",
        "breite": "2", "farbe": "0B6EC9"}, timeout=10).json()
    arr_x = r.get("xref", 0)
    check("Pfeil angelegt", r.get("ok") and arr_x > 0, str(r))
    r = requests.post(f"{BASE}/api/annot/shape/{vdid}", data={
        "page": "0", "typ": "ink", "rect": "[0,0,0,0]",
        "punkte": "[[[100,560],[140,575],[180,550]]]", "breite": "3", "farbe": "000000"}, timeout=10).json()
    ink_x = r.get("xref", 0)
    check("Tinte angelegt", r.get("ok") and ink_x > 0, str(r))
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    fsubs = sorted(a["sub"] for a in annots if a["type"] == "shape")
    check("Formen gelistet (rect/arrow/ink)", fsubs == ["arrow", "ink", "rect"], str(fsubs))

    # Form verschieben+skalieren (shapemove)
    alt_rect = next(a["rect"] for a in annots if a.get("xref") == rect_x)
    neu_rect = [alt_rect[0] + 40, alt_rect[1] + 30, alt_rect[2] + 60, alt_rect[3] + 40]
    r = requests.post(f"{BASE}/api/annot/shapemove/{vdid}", data={
        "page": "0", "xref": str(rect_x), "alt": str(alt_rect), "neu": str(neu_rect)}, timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    neu_gelesen = next((a["rect"] for a in annots if a.get("xref") == rect_x), None)
    check("Form verschoben+skaliert", r.get("ok") and neu_gelesen and abs(neu_gelesen[0] - neu_rect[0]) < 1.5,
          f"{neu_gelesen}")
    # Pfeil: Move synkt NM-Punkte, Flip (gespiegelter Zug) + Undo, gefuellte Spitze (/IC)
    arr_alt = next(a["rect"] for a in annots if a.get("xref") == arr_x)
    arr_punkte_vor = next(a["punkte"] for a in annots if a.get("xref") == arr_x)
    arr_neu = [arr_alt[0] + 25, arr_alt[1] + 20, arr_alt[2] + 25, arr_alt[3] + 20]   # reine Verschiebung
    requests.post(f"{BASE}/api/annot/shapemove/{vdid}", data={
        "page": "0", "xref": str(arr_x), "alt": str(arr_alt), "neu": str(arr_neu)}, timeout=10)
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    arr_np = next((a["punkte"] for a in annots if a.get("xref") == arr_x), None)
    check("Pfeil-Move: NM-Punkte nachgezogen", arr_np and abs(arr_np[0][0] - (arr_punkte_vor[0][0] + 25)) < 1.5, str(arr_np))
    flip_neu = [arr_neu[2] - 20, arr_neu[3] - 20, arr_neu[0] + 20, arr_neu[1] + 20]   # gespiegelt: x1<x0, y1<y0
    requests.post(f"{BASE}/api/annot/shapemove/{vdid}", data={
        "page": "0", "xref": str(arr_x), "alt": str(arr_neu), "neu": str(flip_neu)}, timeout=10)
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    arr_fp = next((a["punkte"] for a in annots if a.get("xref") == arr_x), None)
    check("Pfeil-Flip: Spitze folgt dem Griff", bool(arr_fp) and arr_fp[1][0] < arr_fp[0][0] and arr_fp[1][1] < arr_fp[0][1], str(arr_fp))
    requests.post(f"{BASE}/api/undo/{vdid}", timeout=10)
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    arr_up = next((a for a in annots if a.get("xref") == arr_x), None)
    check("Pfeil-Flip-Undo: Punkte zurueck, Rect normal",
          bool(arr_up) and abs(arr_up["punkte"][1][0] - arr_np[1][0]) < 1 and abs(arr_up["punkte"][1][1] - arr_np[1][1]) < 1
          and arr_up["rect"][2] > arr_up["rect"][0], str(arr_up)[:120])
    pdf_bytes = requests.get(f"{BASE}/api/download/{vdid}", timeout=15).content
    check("Pfeilspitze gefuellt im PDF (/LE + /IC)", b"/ClosedArrow" in pdf_bytes and b"/IC" in pdf_bytes)
    # Stil aendern
    r = requests.post(f"{BASE}/api/annot/style/{vdid}", data={
        "page": "0", "xref": str(rect_x), "farbe": "00AA00", "breite": "4"}, timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    gestylt = next((a for a in annots if a.get("xref") == rect_x), {})
    check("Form-Stil geaendert", r.get("ok") and gestylt.get("farbe") == "00AA00" and abs(gestylt.get("breite", 0) - 4) < 0.1, str(gestylt)[:90])
    # Loeschen + Undo legt wieder an
    requests.post(f"{BASE}/api/annot/delete/{vdid}", data={"page": "0", "xref": str(ink_x)}, timeout=10)
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    check("Tinte geloescht", not any(a.get("xref") == ink_x for a in annots))
    u = requests.post(f"{BASE}/api/undo/{vdid}", timeout=10).json()
    annots = requests.get(f"{BASE}/api/annots/{vdid}/0", timeout=10).json()
    check("Undo: Tinte wieder da", u.get("undone") and any(a["type"] == "shape" and a["sub"] == "ink" for a in annots))

    # OCR: Scan-PDF (Bildseite ohne Text) oeffnen, erkennen, durchsuchbar machen.
    # Fixtures erzeugt der Test selbst: Bildseite (fuer OCR) + Arial eingebettet.
    import pymupdf
    from PIL import ImageDraw, ImageFont
    os.makedirs(FIXDIR, exist_ok=True)
    scan_pfad = os.path.join(FIXDIR, "pw_test_scan.pdf")
    img = Image.new("RGB", (1240, 1754), "white")
    dr = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("arial.ttf", 52)
    except Exception:
        fnt = ImageFont.load_default()
    for i in range(12):
        dr.text((100, 120 + i * 110), f"Beispieltext Zeile {i + 1}", fill="black", font=fnt)
    img_pfad = os.path.join(FIXDIR, "pw_test_scan.png")
    img.save(img_pfad)
    sdoc = pymupdf.open()
    spg = sdoc.new_page(width=595, height=842)
    spg.insert_image(spg.rect, filename=img_pfad)
    sdoc.save(scan_pfad)
    scan = requests.get(BASE + "/api/open",
                        params={"q": scan_pfad}, timeout=20).json()
    sdid = scan["id"]
    oi = requests.get(f"{BASE}/api/ocr/info/{sdid}", timeout=10).json()
    check("OCR-Info: Scan ohne Text", oi.get("seiten_ohne_text") == [0] and "deu" in oi.get("tessdata", []), str(oi)[:90])
    r = requests.post(f"{BASE}/api/ocr/{sdid}", data={"page": "0", "lang": "deu+eng", "dpi": "300"}, timeout=120).json()
    check("OCR-Seite ausgefuehrt", r.get("ok") and not r.get("skip") and r.get("zeilen", 0) >= 10, str(r))
    s = requests.get(f"{BASE}/api/search/{sdid}", params={"q": "Beispieltext"}, timeout=10).json()
    check("OCR: Scan danach durchsuchbar", len(s.get("hits", [])) >= 5, str(len(s.get("hits", []))))
    r = requests.post(f"{BASE}/api/ocr/{sdid}", data={"page": "0", "lang": "deu+eng"}, timeout=30).json()
    check("OCR: Seite mit Text wird uebersprungen", r.get("ok") and r.get("skip"), str(r))

    # KI-Endpunkte: Validierung ohne Konfiguration
    r = requests.get(f"{BASE}/api/ai/models", params={"url": "", "key": "", "art": "openai"}, timeout=10)
    check("KI-Modelle: leere URL abgewiesen", r.status_code in (400, 502), str(r.status_code))
    r = requests.post(f"{BASE}/api/ai/chat", data={"mid": "gibtsnicht", "nachrichten": "[]"}, timeout=10)
    check("KI-Chat: unbekanntes Modell 404", r.status_code == 404, str(r.status_code))
    ft = requests.get(f"{BASE}/api/fulltext/{vdid}", timeout=10).json()
    check("Volltext mit Seitenmarkern", ft.get("zeichen", 0) > 100 and "--- Seite 1 ---" in ft.get("text", ""), str(ft.get("zeichen")))

    # Dokument-Schriften: Font-PDF mit eingebettetem Arial (Fixtures s.o.)
    font_pfad = os.path.join(FIXDIR, "pw_test_font.pdf")
    fdoc = pymupdf.open()
    fpg = fdoc.new_page(width=595, height=842)
    fpg.insert_font(fontname="Arial", fontfile=r"C:\Windows\Fonts\arial.ttf")
    fpg.insert_text((72, 100), "Schriftprobe mit eingebettetem Arial", fontname="Arial", fontsize=14)
    fpg.insert_text((72, 130), "Zweite Zeile fuer die Schriftprobe", fontname="Arial", fontsize=12)
    fdoc.save(font_pfad)
    fdok = requests.get(BASE + "/api/open",
                        params={"q": font_pfad}, timeout=20).json()
    fid = fdok["id"]
    fonts = requests.get(f"{BASE}/api/fonts/{fid}", timeout=10).json()
    arial = next((f for f in fonts if "Arial" in f.get("basefont", "") and f.get("nutzbar")), None)
    check("Eingebettete Schrift erkannt (Arial)", arial is not None, str(fonts)[:90])
    if arial:
        fr = requests.get(f"{BASE}/api/font/file/{fid}/{arial['xref']}", timeout=10)
        check("Schrift extrahierbar", fr.ok and len(fr.content) > 10000, f"{len(fr.content)} Bytes")
        kodierung = f"doc~{arial['xref']}~{arial['basefont']}"
        r = requests.post(f"{BASE}/api/annot/text/{fid}", data={
            "page": "0", "rect": "[100,200,330,230]", "text": "Arial Schriftprobe",
            "size": "14", "font": kodierung, "color": "0,0,0"}, timeout=10).json()
        annots = requests.get(f"{BASE}/api/annots/{fid}/0", timeout=10).json()
        tfa = next((a for a in annots if a["type"] == "text"), {})
        check("Text in Dokument-Schrift", r.get("ok") and tfa.get("font") == kodierung, str(tfa)[:90])

    # Original-Text loeschen (Redaction)
    lines1 = requests.get(f"{BASE}/api/text/{did}/1", timeout=10).json()["lines"]
    ziel = lines1[0]
    rects = [[round(ziel["x0"], 1), round(ziel["y0"], 1), round(ziel["x1"], 1), round(ziel["y1"], 1)]]
    r = requests.post(f"{BASE}/api/delete/{did}", data={"page": "1", "rects": str(rects)}, timeout=10).json()
    lines1b = requests.get(f"{BASE}/api/text/{did}/1", timeout=10).json()["lines"]
    check("Original-Text geloescht", r.get("ok") and not any(l["t"] == ziel["t"] for l in lines1b))

    # Suche
    s = requests.get(f"{BASE}/api/search/{did}", params={"q": "Beispieltext"}, timeout=10).json()
    check("Suche findet Treffer", len(s.get("hits", [])) >= 10, str(len(s.get("hits", []))))

    # Seite drehen (Rendermass soll getauscht werden)
    png_before = requests.get(f"{BASE}/api/page/{did}/0", timeout=15).content
    w_before = int.from_bytes(png_before[16:20], "big")
    h_before = int.from_bytes(png_before[20:24], "big")
    r = requests.post(f"{BASE}/api/rotate/{did}", data={"page": "0", "delta": "90"}, timeout=10).json()
    png_after = requests.get(f"{BASE}/api/page/{did}/0", timeout=15).content
    w_after = int.from_bytes(png_after[16:20], "big")
    h_after = int.from_bytes(png_after[20:24], "big")
    check("Seite gedreht (Format getauscht)", r.get("ok") and (w_before - h_before) * (w_after - h_after) < 0,
          f"{w_before}x{h_before} -> {w_after}x{h_after}")

    # --- Eingebettete Bilder: Skalieren + Drehen (v0.19.1) ---
    import pymupdf
    tdoc = pymupdf.open()
    tpg = tdoc.new_page(width=595, height=842)
    tpg.insert_text((72, 90), "Bildtest", fontsize=14)
    ibuf = io.BytesIO()
    Image.new("RGBA", (200, 140), (200, 30, 30, 255)).save(ibuf, "PNG")
    tpg.insert_image(pymupdf.Rect(80, 120, 280, 260), stream=ibuf.getvalue())
    tb = io.BytesIO()
    tdoc.save(tb)
    r = requests.post(f"{BASE}/api/upload", files={"file": ("pw_bild_test.pdf", tb.getvalue(), "application/pdf")},
                      timeout=15).json()
    check("Bild-Test-PDF hochgeladen", r.get("id"), str(r))
    bid = r["id"]
    ii = requests.get(f"{BASE}/api/imageinfo/{bid}/0", timeout=10).json()
    bild0 = ii["bilder"][0]
    check("Bildinfo: Platzierung+xref", bild0["bbox"] == [80.0, 120.0, 280.0, 260.0] and bild0["xref"] > 0, str(ii))
    r = requests.get(f"{BASE}/api/image/file/{bid}/0/{bild0['xref']}", timeout=10)
    check("Bildbytes: PNG mit Alpha", r.status_code == 200 and r.content[:4] == b"\x89PNG", str(r.status_code))
    r = requests.post(f"{BASE}/api/image/move/{bid}", data={
        "page": "0", "xref": str(bild0["xref"]), "alt": "[80,120,280,260]", "neu": "[80,120,180,190]"},
        timeout=10).json()
    ii = requests.get(f"{BASE}/api/imageinfo/{bid}/0", timeout=10).json()
    check("Bild skaliert (100x70)", r.get("ok") and ii["bilder"][-1]["bbox"] == [80.0, 120.0, 180.0, 190.0],
          str(ii["bilder"][-1]))
    r = requests.post(f"{BASE}/api/image/rotate/{bid}", data={
        "page": "0", "xref": str(bild0["xref"]), "alt": "[80,120,180,190]", "winkel": "90"}, timeout=10).json()
    check("Bild gedreht: Ruegabe-Rect (Huelle 100x70 -> 70x100 um Mitte 130,155)", r.get("ok") and r.get("rect") == [95.0, 105.0, 165.0, 205.0], str(r))
    ii = requests.get(f"{BASE}/api/imageinfo/{bid}/0", timeout=10).json()
    check("Bild gedreht: Huelle in der Sitzung", ii["bilder"][-1]["bbox"] == [95.0, 105.0, 165.0, 205.0],
          str(ii["bilder"][-1]))
    u = requests.post(f"{BASE}/api/undo/{bid}", timeout=10).json()
    ii = requests.get(f"{BASE}/api/imageinfo/{bid}/0", timeout=10).json()
    check("Undo: Rotation zurueck", u.get("undone") and ii["bilder"][-1]["bbox"] == [80.0, 120.0, 180.0, 190.0],
          str(ii["bilder"][-1]))
    u = requests.post(f"{BASE}/api/undo/{bid}", timeout=10).json()
    ii = requests.get(f"{BASE}/api/imageinfo/{bid}/0", timeout=10).json()
    check("Undo: Skalierung zurueck", u.get("undone") and ii["bilder"][-1]["bbox"] == [80.0, 120.0, 280.0, 260.0],
          str(ii["bilder"][-1]))
    # Datei-Level-Beweis: 30° drehen, speichern, frisch oeffnen (Huelle 243.2x221.2 um 180,190)
    r = requests.post(f"{BASE}/api/image/rotate/{bid}", data={
        "page": "0", "xref": str(bild0["xref"]), "alt": "[80,120,280,260]", "winkel": "30"}, timeout=10).json()
    check("Bild um 30 Grad gedreht", r.get("ok") and abs(r["rect"][0] - 58.4) < 1.5, str(r))
    bild_ziel = os.path.join(TMPD, "pw_test_bild.pdf")
    if os.path.isfile(bild_ziel):
        os.remove(bild_ziel)
    r = requests.get(f"{BASE}/api/saveas/{bid}", params={"path": bild_ziel}, timeout=15)
    check("Bild-PDF gesichert", r.ok and os.path.isfile(bild_ziel), str(r.status_code))
    frisch = pymupdf.open(bild_ziel)
    platz = [i["bbox"] for i in frisch[0].get_image_info(xrefs=True)]
    huelle = [round(v, 1) for v in [58.4, 79.4, 301.6, 300.6]]
    check("Datei-Level: 30-Grad-Huelle gespeichert",
          any(all(abs(a - b) < 1.2 for a, b in zip(p, huelle)) for p in platz), str(platz))
    frisch.close()

    # --- Sperrzustand nach Server-Neustart (zweiter Prozess, anderer Port) ---
    PORT2 = PORT + 1
    srv2 = subprocess.Popen([EXE, "--port", str(PORT2)], creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        for _ in range(40):
            time.sleep(0.5)
            try:
                if requests.get(f"http://127.0.0.1:{PORT2}/api/health", timeout=2).json().get("ok"):
                    break
            except Exception:
                pass
        B2 = f"http://127.0.0.1:{PORT2}"
        from urllib.parse import quote
        r = requests.get(B2 + f"/api/signature/file/{quote(pwfile)}", timeout=5)
        check("Nach Neustart: Abruf gesperrt (401)", r.status_code == 401, str(r.status_code))
        r = requests.post(B2 + "/api/signature/unlock", data={"fname": pwfile, "password": "falsch"}, timeout=20)
        check("Falsches Passwort abgewiesen", r.status_code == 401, str(r.status_code))
        r = requests.post(B2 + "/api/signature/unlock", data={"fname": pwfile, "password": "geheim"}, timeout=20)
        check("Richtiges Passwort entsperrt", r.ok and r.json().get("ok"), str(r.status_code))
        r = requests.get(B2 + f"/api/signature/file/{quote(pwfile)}", timeout=5)
        check("Entsperrt liefert PNG", r.status_code == 200 and r.content[:4] == b"\x89PNG", str(r.status_code))
    finally:
        srv2.kill()
except Exception as e:
    failures.append("Ausnahme: " + repr(e)[:200])
finally:
    srv.kill()
    # Aufgeraeumt: Wegwerf-Signaturen loeschen, damit nichts uebrig bleibt
    sigdir = os.path.join(os.path.dirname(EXE), "signatures")
    try:
        for fn in os.listdir(sigdir):
            if fn.startswith(("TestSig", "UndoSig", "TestSig Umbenannt", "PwSig")):
                os.remove(os.path.join(sigdir, fn))
    except Exception:
        pass
    for tmpf in (os.path.join(TMPD, "pw_test_saveas.pdf"), os.path.join(TMPD, "pw_test_saveas_burn.pdf"),
                 os.path.join(TMPD, "pw_test_bild.pdf")):
        try:
            os.remove(tmpf)
        except Exception:
            pass
    try:
        shutil.rmtree(FIXDIR, ignore_errors=True)
    except Exception:
        pass
    print("Testserver gestoppt")
    print("ERGEBNIS: " + ("ALLE PASS" if not failures else "FEHLER: " + ", ".join(failures)))
