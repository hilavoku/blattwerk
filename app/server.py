# PDF-Werkstatt - lokaler PDF-Server
# Läuft auf 127.0.0.1, wird vom WebView2-Wrapper (PdfWerkstatt.exe) gestartet.
import os
import sys
import io
import json
import uuid
import base64
import shutil

import pymupdf
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, Response, FileResponse
if getattr(sys, "frozen", False):
    # Als PyInstaller-EXE: Dateien neben der EXE, gebündelte Assets in _MEIPASS
    BASE = os.path.dirname(sys.executable)
    STATIC = os.path.join(getattr(sys, "_MEIPASS", BASE), "static")
else:
    BASE = r"<Projektordner>"
    STATIC = os.path.join(BASE, "app", "static")

UPLOADS = os.path.join(BASE, "uploads")
SIGN_DIR = os.path.join(BASE, "signatures")
DEMO = os.path.join(BASE, "demo", "demo.pdf")
# Einstellungen NEBEN dem Programmordner: Deployment = PDF-Werkstatt\einstellungen.json
# (ueberlebt server-Aktualisierungen); Entwicklung = Projektwurzel
PREFS_FILE = os.path.join(os.path.dirname(BASE) if getattr(sys, "frozen", False) else BASE,
                          "einstellungen.json")
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(SIGN_DIR, exist_ok=True)

app = FastAPI(title="PDF-Werkstatt")


@app.middleware("http")
async def _kein_cache(request, call_next):
    """Lokaler Server: niemals cachen - sonst laeuft die UI nach Updates auf alten Stand."""
    resp = await call_next(request)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


docs = {}     # doc_id -> {"path": str, "doc": pymupdf.Document}
current = {}  # zuletzt geöffnetes Dokument (für Doppelklick-Start)
undo_stacks = {}  # did -> Liste von Undo-Einträgen
sig_unlocked = {}  # fname -> entschlüsselte PNG-Bytes (nur im RAM, bis Serverstop)

# ---------- Passwort-geschützte Signaturen (.pwdsig, Fernet/PBKDF2) ----------

def _fernet_schluessel(passwort: str, salt: bytes):
    """Ableitung: PBKDF2-HMAC-SHA256, 200k Iterationen."""
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
    return base64.urlsafe_b64encode(kdf.derive(passwort.encode("utf-8")))


def _sig_verschluesseln(png_bytes: bytes, passwort: str) -> str:
    import base64
    from cryptography.fernet import Fernet
    salt = os.urandom(16)
    tok = Fernet(_fernet_schluessel(passwort, salt)).encrypt(png_bytes)
    return json.dumps({"v": 1, "salt": base64.b64encode(salt).decode(),
                       "token": tok.decode()})


def _sig_entschluesseln(inhalt: str, passwort: str) -> bytes:
    import base64
    from cryptography.fernet import Fernet, InvalidToken
    daten = json.loads(inhalt)
    salt = base64.b64decode(daten["salt"])
    try:
        return Fernet(_fernet_schluessel(passwort, salt)).decrypt(daten["token"].encode())
    except InvalidToken:
        raise HTTPException(401, "Falsches Passwort")


def _sig_gesperrt(fname: str) -> bool:
    return fname.lower().endswith(".pwdsig")


def _sig_bytes(fname: str):
    """PNG-Bytes einer Signatur; None, wenn geschützt und noch nicht entsperrt."""
    fname = os.path.basename(fname)
    pfad = os.path.join(SIGN_DIR, fname)
    if not os.path.isfile(pfad):
        return None
    if _sig_gesperrt(fname):
        return sig_unlocked.get(fname)
    with open(pfad, "rb") as f:
        return f.read()


def push_undo(did, entry):
    st = undo_stacks.setdefault(did, [])
    st.append(entry)
    if len(st) > 60:
        st.pop(0)


def _txt_props(did_page_annot_nm, fallback_rect=None):
    """Liest Text-Eigenschaften aus einem PDFW-TXT-NM-Marker."""
    nm = did_page_annot_nm or ""
    font, size, color = "helv", 11.0, [0, 0, 0]
    if nm.startswith("PDFW-TXT:"):
        try:
            _, f, s, c = nm.split(":", 3)
            font = f or font
            size = float(s)
            color = [float(v) for v in c.split(",")]
        except Exception:
            pass
    return font, size, color


def _doc(did: str) -> pymupdf.Document:
    if did not in docs:
        raise HTTPException(404, "Dokument nicht (mehr) geoeffnet")
    return docs[did]["doc"]


def _open(path: str) -> dict:
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        raise HTTPException(404, "Datei nicht gefunden: " + path)
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        raise HTTPException(400, "Kann PDF nicht oeffnen: " + str(e))
    did = uuid.uuid4().hex[:12]
    docs[did] = {"path": path, "doc": doc}
    current.clear()
    current.update({
        "id": did,
        "name": os.path.basename(path),
        "pages": doc.page_count,
        "toc": doc.get_toc(simple=True),
    })
    return dict(current)


def _ensure_demo():
    if os.path.isfile(DEMO):
        return
    os.makedirs(os.path.dirname(DEMO), exist_ok=True)
    doc = pymupdf.open()
    toc = []
    p = doc.new_page()
    p.insert_text((72, 90), "PDF-Werkstatt Demo-Dokument", fontsize=18)
    p.insert_text((72, 120), "Seite 1: Markiere mich - diese Zeile ist zum Kopieren da.", fontsize=11)
    p.insert_text((72, 140), "Klicke auf eine Zeile, um sie in die Zwischenablage zu legen.", fontsize=11)
    toc.append([1, "Einleitung", 1])
    p = doc.new_page()
    p.insert_text((72, 90), "Kapitel 1: Lesezeichen", fontsize=16)
    for i in range(20):
        p.insert_text((72, 120 + i * 16), f"Beispieltext Zeile {i+1} auf Seite 2.", fontsize=11)
    toc.append([1, "Kapitel 1 - Lesezeichen", 2])
    toc.append([2, "Unterabschnitt", 2])
    p = doc.new_page()
    p.insert_text((72, 90), "Kapitel 2: Formular", fontsize=16)
    p.insert_text((72, 130), "Vorname:", fontsize=11)
    p.insert_text((72, 170), "Nachname:", fontsize=11)
    p.insert_text((72, 210), "Lieblingsfarbe:", fontsize=11)
    for name, y in (("Vorname", 130), ("Nachname", 170), ("Lieblingsfarbe", 210)):
        w = pymupdf.Widget()
        w.rect = pymupdf.Rect(160, y - 12, 380, y + 8)
        w.field_name = name
        w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        w.border_width = 0.5
        p.add_widget(w)
    toc.append([1, "Kapitel 2 - Formular", 3])
    doc.set_toc(toc)
    doc.save(DEMO)
    doc.close()


@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(STATIC, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/favicon.ico")
def favicon():
    path = os.path.join(STATIC, "logo.png")
    if not os.path.isfile(path):
        raise HTTPException(404)
    return Response(content=open(path, "rb").read(), media_type="image/png")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/prefs")
def get_prefs():
    """Gespeicherte UI-Einstellungen (portunabhaengig, da der Serverport pro Start wechselt)."""
    try:
        with open(PREFS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@app.post("/api/prefs")
async def set_prefs(data: dict = Body(...)):
    if len(data) > 40:
        raise HTTPException(400, "Zu viele Eintraege")
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, "Einstellungen nicht speicherbar: " + str(e))


@app.get("/api/current")
def current_doc():
    return dict(current) if current else {}


@app.get("/api/demo")
def demo():
    _ensure_demo()
    return _open(DEMO)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    did_prefix = uuid.uuid4().hex[:8]
    name = os.path.basename(file.filename or "dokument.pdf")
    path = os.path.join(UPLOADS, did_prefix + "_" + name)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return _open(path)


@app.get("/api/open")
def open_by_path(q: str):
    return _open(q)


@app.get("/api/page/{did}/{n}")
def page(did: str, n: int, dpi: int = 110):
    d = _doc(did)
    if n < 0 or n >= d.page_count:
        raise HTTPException(404, "Seite existiert nicht")
    pix = d[n].get_pixmap(dpi=dpi, annots=False)
    return Response(content=pix.tobytes("png"), media_type="image/png")


@app.get("/api/text/{did}/{n}")
def text(did: str, n: int):
    d = _doc(did)
    words = d[n].get_text("words")
    lines = {}
    for w in words:
        lines.setdefault((w[5], w[6]), []).append(w)
    out = []
    for key in sorted(lines):
        ws = sorted(lines[key], key=lambda w: w[0])
        out.append({
            "x0": min(w[0] for w in ws),
            "y0": min(w[1] for w in ws),
            "x1": max(w[2] for w in ws),
            "y1": max(w[3] for w in ws),
            "t": " ".join(w[4] for w in ws),
        })
    return {"page_w": d[n].rect.width, "page_h": d[n].rect.height, "lines": out}


@app.get("/api/fields/{did}")
def fields(did: str):
    d = _doc(did)
    out = []
    for pno, pg in enumerate(d):
        for w in pg.widgets():
            out.append({
                "page": pno,
                "name": w.field_name,
                "type": w.field_type_string,
                "value": "" if w.field_value is None else str(w.field_value),
                "rect": list(w.rect),
            })
    return out


def _feld_wert_setzen(doc, w, value):
    """Setzt Widget-Wert; Leerstring braucht /V-Diretcing (PyMuPDF ignoriert '')."""
    if value == "":
        w.field_value = " "
        w.update()
        doc.xref_set_key(w.xref, "V", "()")
    else:
        w.field_value = value
        w.update()


@app.post("/api/field/{did}")
async def set_field(did: str, page: int = Form(...), name: str = Form(...), value: str = Form(...)):
    d = _doc(did)
    found = False
    for w in d[page].widgets():
        if w.field_name == name:
            old = "" if w.field_value is None else str(w.field_value)
            if w.field_type_string in ("CheckBox", "RadioButton"):
                w.field_value = value.lower() in ("1", "true", "yes", "an", "x")
                w.update()
            else:
                _feld_wert_setzen(d, w, value)
            found = True
            push_undo(did, {"op": "field", "page": page, "name": name, "value": old})
    if not found:
        raise HTTPException(404, "Feld nicht gefunden: " + name)
    return {"ok": True}


@app.get("/api/hasannots/{did}")
def hasannots(did: str):
    """Gibt es bewegliche Objekte (Signaturen/Texte)? - fuer die Einbrennen-Rueckfrage."""
    d = _doc(did)
    for pg in d:
        for a in pg.annots():
            if a.type[1] in ("Stamp", "FreeText"):
                return {"any": True}
    return {"any": False}


@app.post("/api/save/{did}")
def save(did: str, flatten: int = 0):
    d = _doc(did)
    if flatten:
        # Signaturen/Texte einbrennen: werden Seiteninhalt, nicht mehr entfernbar.
        # widgets=False: Formularfelder bleiben ausfuellbar. Danach ist Undo sinnlos.
        d.bake(widgets=False)
        undo_stacks[did] = []
    path = docs[did]["path"]
    try:
        d.saveIncr()
    except Exception:
        tmp = path + ".tmp"
        d.save(tmp, garbage=3, deflate=True)
        d.close()
        shutil.move(tmp, path)
        docs[did]["doc"] = pymupdf.open(path)
    return {"ok": True, "path": path, "flattened": bool(flatten)}


@app.get("/api/saveas/{did}")
def saveas(did: str, path: str, flatten: int = 0):
    """Dokument unter neuem Namen speichern - die neue Datei wird zum Arbeitsdokument
    (wie ueblich bei "Speichern unter"). Ohne garbage: Xref-Nummern bleiben stabil,
    Undo-Referenzen ueberleben. Original-Datei bleibt unveraendert liegen.
    flatten=1 brennt Signaturen/Texte vorher ein (wie beim normalen Speichern)."""
    d = _doc(did)
    path = os.path.normpath(path)
    if path.lower() == os.path.normpath(docs[did]["path"]).lower():
        raise HTTPException(400, "Ziel ist die bereits geöffnete Datei – bitte 'Speichern' nutzen")
    try:
        if flatten:
            d.bake(widgets=False)
            undo_stacks[did] = []
        d.save(path, deflate=True)
        d.close()
        docs[did]["doc"] = pymupdf.open(path)
        docs[did]["path"] = path
        if current.get("id") == did:
            current["name"] = os.path.basename(path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, "Speichern unter fehlgeschlagen: " + str(e))
    return {"ok": True, "path": path, "flattened": bool(flatten)}


@app.get("/api/download/{did}")
def download(did: str):
    d = _doc(did)
    path = docs[did]["path"]
    buf = io.BytesIO()
    d.save(buf, garbage=3, deflate=True)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{os.path.basename(path)}"'},
    )


# ---------- Signaturen ----------

def _entferne_weissen_hintergrund(img):
    """Macht nahezu weisse Pixel transparent (wie PDFgears Signatur-Trick). Im RAM."""
    from PIL import Image
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r > 232 and g > 232 and b > 232 and a > 0:
                px[x, y] = (r, g, b, 0)
    return img


@app.get("/api/signatures")
def signatures():
    out = []
    for fn in sorted(os.listdir(SIGN_DIR)):
        locked = _sig_gesperrt(fn)
        if fn.lower().endswith((".png", ".jpg", ".jpeg")) or locked:
            out.append({"file": fn, "name": os.path.splitext(fn)[0],
                        "locked": locked, "unlocked": locked and fn in sig_unlocked})
    return out


def _alle_stamp_verweise_umbenennen(old: str, new: str):
    """NM-Marker aller gesetzten Signatur-Annotationen auf neuen Dateinamen ziehen.
    Rot-Suffix (':90' etc.) bleibt erhalten; Dateinamen enthalten nie ':' (Windows)."""
    praefix = f"PDFW-SIG:{old}"
    for did in list(docs.keys()):
        d = docs[did]["doc"]
        for pno in range(d.page_count):
            for a in d[pno].annots():
                if a.type[1] == "Stamp":
                    nm = a.info.get("id", "") or ""
                    if nm.startswith(praefix):
                        rest = nm[len(praefix):]      # '' oder ':rot'
                        if new:
                            d.xref_set_key(a.xref, "NM", f"(PDFW-SIG:{new}{rest})")
                        else:                          # Loeschen: Verweis leeren
                            d.xref_set_key(a.xref, "NM", "(PDFW-SIG:)")


@app.post("/api/signature/rename")
async def signature_rename(old: str = Form(...), new: str = Form(...)):
    old = os.path.basename(old)
    new = "".join(c for c in new if c not in '\\/:*?"<>|').strip()
    if not new:
        raise HTTPException(400, "Name ist leer")
    src = os.path.join(SIGN_DIR, old)
    if not os.path.isfile(src):
        raise HTTPException(404, "Signatur nicht gefunden")
    ext = os.path.splitext(old)[1] or ".png"
    dst = os.path.join(SIGN_DIR, new + ext)
    if os.path.isfile(dst):
        raise HTTPException(400, "Dieser Name existiert bereits")
    os.rename(src, dst)
    if old in sig_unlocked:
        sig_unlocked[new + ext] = sig_unlocked.pop(old)
    _alle_stamp_verweise_umbenennen(old, new + ext)
    return {"ok": True, "file": new + ext}


@app.post("/api/signature/delete")
async def signature_delete(fname: str = Form(...)):
    fname = os.path.basename(fname)
    path = os.path.join(SIGN_DIR, fname)
    if os.path.isfile(path):
        os.remove(path)
    sig_unlocked.pop(fname, None)
    # Verweise leeren -> Vorschau zeigt Platzhalter; gespeicherte PDFs bleiben unberuehrt
    _alle_stamp_verweise_umbenennen(fname, "")
    return {"ok": True}


@app.get("/api/signature/file/{fname}")
def signature_file(fname: str):
    fname = os.path.basename(fname)
    path = os.path.join(SIGN_DIR, fname)
    if not os.path.isfile(path):
        raise HTTPException(404, "Signatur nicht gefunden")
    if _sig_gesperrt(fname):
        if fname not in sig_unlocked:
            raise HTTPException(401, "Signatur ist passwortgeschützt – erst entsperren")
        return Response(content=sig_unlocked[fname], media_type="image/png")
    media = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    return Response(content=open(path, "rb").read(), media_type=media)


@app.post("/api/signature/unlock")
async def signature_unlock(fname: str = Form(...), password: str = Form(...)):
    """Prueft das Passwort und haelt die entschluesselten Bytes bis Serverstop im RAM."""
    fname = os.path.basename(fname)
    path = os.path.join(SIGN_DIR, fname)
    if not _sig_gesperrt(fname) or not os.path.isfile(path):
        raise HTTPException(404, "Keine passwortgeschützte Signatur")
    with open(path, encoding="utf-8") as f:
        daten = _sig_entschluesseln(f.read(), password)
    sig_unlocked[fname] = daten
    return {"ok": True, "file": fname}


@app.post("/api/signature/upload")
async def signature_upload(file: UploadFile = File(...), remove_bg: str = Form("1"),
                           password: str = Form("")):
    from PIL import Image
    import io as _io
    name = os.path.splitext(os.path.basename(file.filename or "Signatur"))[0]
    name = "".join(c for c in name if c not in '\\/:*?"<>|') or "Signatur"
    roh = await file.read()
    try:
        img = Image.open(_io.BytesIO(roh))
    except Exception:
        raise HTTPException(400, "Keine Bilddatei")
    if remove_bg == "1":
        try:
            img = _entferne_weissen_hintergrund(img)
        except Exception:
            pass  # ohne Hintergrund-Entfernung weiterbenutzen
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    png = buf.getvalue()
    if password:
        path = os.path.join(SIGN_DIR, name + ".pwdsig")
        with open(path, "w", encoding="utf-8") as f:
            f.write(_sig_verschluesseln(png, password))
        sig_unlocked[name + ".pwdsig"] = png   # frisch hochgeladen: gleich entsperren
    else:
        path = os.path.join(SIGN_DIR, name + ".png")
        with open(path, "wb") as f:
            f.write(png)
    return {"ok": True, "file": os.path.basename(path)}


def _sig_nmteilen(nm: str):
    """NM-Marker 'PDFW-SIG:datei(:rot)?' -> (dateiname, rotation)."""
    if not (nm or "").startswith("PDFW-SIG:"):
        return "", 0
    rest = nm[9:]
    fname, _, rot = rest.partition(":")
    try:
        rot = int(rot) if rot else 0
    except ValueError:
        rot = 0
    return fname, rot % 360


@app.post("/api/stamp/{did}")
async def stamp(did: str, page: int = Form(...), x: float = Form(...), y: float = Form(...),
                width: float = Form(140), fname: str = Form(...)):
    """Signatur als VERSCHIEBBARE Stamp-Annotation mit Bild-Erscheinung setzen."""
    d = _doc(did)
    if page < 0 or page >= d.page_count:
        raise HTTPException(404, "Seite existiert nicht")
    fname = os.path.basename(fname)
    png = _sig_bytes(fname)
    if png is None:
        if _sig_gesperrt(fname):
            raise HTTPException(401, "Signatur ist passwortgeschützt – erst entsperren")
        raise HTTPException(404, "Signatur nicht gefunden: " + fname)
    from PIL import Image
    import io as _io
    with Image.open(_io.BytesIO(png)) as im:
        iw, ih = im.size
    w = max(30.0, min(float(width), 400.0))
    h = w * ih / iw
    pg = d[page]
    annot = pg.add_stamp_annot(pymupdf.Rect(float(x), float(y), float(x) + w, float(y) + h))
    form_xref = _bild_als_erscheinung(d, png)
    d.xref_set_key(annot.xref, "AP", f"<< /N {form_xref} 0 R >>")
    d.xref_set_key(annot.xref, "NM", f"(PDFW-SIG:{fname})")
    push_undo(did, {"op": "annot-delete", "page": page, "xref": annot.xref})
    return {"ok": True, "xref": annot.xref, "rect": list(annot.rect), "page": page}


def _bild_als_erscheinung(doc, png_bytes: bytes, rot: int = 0) -> int:
    """Baut Form-XObject mit Bild+Alphamaske als Annotation-Erscheinung.
    rot: Vielfache von 90 - das Bild wird vorgedreht eingebettet (BBox passt dann zum
    getauschten Rect). Liefert Form-XRef."""
    from PIL import Image
    import io as _io
    with Image.open(_io.BytesIO(png_bytes)) as im0:
        im = im0.convert("RGBA")
        if rot % 360:
            im = im.rotate(-(rot % 360), expand=True)
        iw, ih = im.size
        rgb = im.convert("RGB").tobytes()
        alpha = im.getchannel("A").tobytes()

    smask = doc.get_new_xref()
    doc.update_object(smask, f"<< /Type /XObject /Subtype /Image /Width {iw} /Height {ih} "
                             f"/ColorSpace /DeviceGray /BitsPerComponent 8 >>")
    doc.update_stream(smask, alpha, new=1)

    img = doc.get_new_xref()
    doc.update_object(img, f"<< /Type /XObject /Subtype /Image /Width {iw} /Height {ih} "
                           f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /SMask {smask} 0 R >>")
    doc.update_stream(img, rgb, new=1)

    form = doc.get_new_xref()
    doc.update_object(form, f"<< /Type /XObject /Subtype /Form /BBox [0 0 {iw} {ih}] "
                            f"/Resources << /XObject << /Img0 {img} 0 R >> >> >>")
    doc.update_stream(form, f"q {iw} 0 0 {ih} 0 0 cm /Img0 Do Q".encode(), new=1)
    return form


@app.post("/api/annot/rotate/{did}")
async def annot_rotate(did: str, page: int = Form(...), xref: int = Form(...),
                       delta: int = Form(90)):
    """Signatur um delta Grad drehen (90-Schritte): neue AP mit vorgedrehtem Bild,
    Rect um das Zentrum tauschen (bei 90/270 wechseln sich Breite/Hoehe)."""
    d = _doc(did)
    pg = d[page]
    an = pg.load_annot(xref)
    if an is None:
        raise HTTPException(404, "Annotation nicht gefunden")
    nm = an.info.get("id", "") or ""
    fname, rot_alt = _sig_nmteilen(nm)
    png = _sig_bytes(fname) if fname else None
    if png is None:
        if fname and _sig_gesperrt(fname):
            raise HTTPException(401, "Signatur ist passwortgeschützt – erst entsperren")
        raise HTTPException(400, "Signaturdatei nicht mehr vorhanden")
    delta = int(delta) % 360
    if delta % 90:
        raise HTTPException(400, "Nur 90-Grad-Schritte")
    rot_neu = (rot_alt + delta) % 360
    rect_alt = pymupdf.Rect(an.rect)                     # vor allen Aenderungen sichern
    form_xref = _bild_als_erscheinung(d, png, rot_neu)
    d.xref_set_key(xref, "AP", f"<< /N {form_xref} 0 R >>")
    nm_neu = f"(PDFW-SIG:{fname}:{rot_neu})" if rot_neu else f"(PDFW-SIG:{fname})"
    d.xref_set_key(xref, "NM", nm_neu)
    r = rect_alt
    if delta % 180:  # 90 oder 270: Seitenverhaeltnis kippt
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        w, h = r.width, r.height
        r = pymupdf.Rect(cx - h / 2, cy - w / 2, cx + h / 2, cy + w / 2)
    an = pg.load_annot(xref)   # frische Annot-Referenz nach AP/NM-Aenderung
    an.set_rect(r)
    push_undo(did, {"op": "sig-rotate", "page": page, "xref": xref,
                    "rect": list(rect_alt), "fname": fname, "rot": rot_alt})
    return {"ok": True, "rot": rot_neu, "rect": list(an.rect)}


@app.get("/api/annots/{did}/{n}")
def annots(did: str, n: int):
    """Liste aller beweglichen Annotationen einer Seite (Signaturen + Freitexte)."""
    d = _doc(did)
    if n < 0 or n >= d.page_count:
        raise HTTPException(404, "Seite existiert nicht")
    out = []
    for a in d[n].annots():
        t = a.type[1]
        if t == "FreeText":
            name = a.info.get("id", "") or ""
            font, size, color = "helv", 11.0, [0, 0, 0]
            if name.startswith("PDFW-TXT:"):
                try:
                    _, f, s, c = name.split(":", 3)
                    font = f or "helv"
                    size = float(s)
                    color = [float(v) for v in c.split(",")]
                except Exception:
                    pass
            out.append({
                "xref": a.xref, "type": "text", "rect": list(a.rect),
                "text": (a.info.get("content") or "").rstrip("\n"),
                "font": font, "size": size, "color": color,
            })
        elif t == "Stamp":
            name = a.info.get("id", "") or ""
            sig, rot = _sig_nmteilen(name)  # "PDFW-SIG:" ist 9 Zeichen
            out.append({"xref": a.xref, "type": "sign", "rect": list(a.rect), "file": sig,
                        "rot": rot, "locked": bool(sig) and _sig_gesperrt(sig),
                        "unlocked": bool(sig) and sig in sig_unlocked})
    return out


@app.post("/api/annot/move/{did}")
async def annot_move(did: str, page: int = Form(...), xref: int = Form(...), rect: str = Form(...)):
    d = _doc(did)
    pg = d[page]  # Seitenobjekt EINMAL holen - jede d[page]-Zugriff waere ein neues Objekt
    r = pymupdf.Rect(*[float(v) for v in json.loads(rect)])
    an = pg.load_annot(xref)
    if an is None:
        raise HTTPException(404, "Annotation nicht gefunden")
    old_rect = list(an.rect)
    an.set_rect(r)
    if an.type[1] == "FreeText":
        an.update()
        an.set_rect(r)   # update() kann das Rect zuruecksetzen -> danach final setzen
    push_undo(did, {"op": "annot-move", "page": page, "xref": xref, "rect": old_rect,
                    "is_text": an.type[1] == "FreeText"})
    return {"ok": True}


@app.post("/api/annot/delete/{did}")
async def annot_delete(did: str, page: int = Form(...), xref: int = Form(...)):
    d = _doc(did)
    pg = d[page]
    an = pg.load_annot(xref)
    if an is None:
        raise HTTPException(404, "Annotation nicht gefunden")
    t = an.type[1]
    old_rect = list(an.rect)
    if t == "Stamp":
        nm = an.info.get("id", "") or ""
        fname, rot = _sig_nmteilen(nm)
        push_undo(did, {"op": "stamp-recreate", "page": page, "rect": old_rect,
                        "fname": fname, "rot": rot})
    elif t == "FreeText":
        nm = an.info.get("id", "") or ""
        font, size, color = _txt_props(nm)
        txt = (an.info.get("content") or "").rstrip("\n")
        push_undo(did, {"op": "text-recreate", "page": page, "rect": old_rect, "text": txt,
                        "font": font, "size": size, "color": color})
    pg.delete_annot(an)
    return {"ok": True}


FONTS = {"helv": "Helvetica", "hebo": "Helvetica Fett", "heit": "Helvetica Kursiv", "hebi": "Helvetica Fett-Kursiv",
         "tiro": "Times", "tibo": "Times Fett", "tiit": "Times Kursiv", "tibi": "Times Fett-Kursiv",
         "cour": "Courier", "cobo": "Courier Fett", "coit": "Courier Kursiv", "cobi": "Courier Fett-Kursiv"}


@app.post("/api/annot/text/{did}")
async def annot_text(did: str, page: int = Form(...), rect: str = Form(...), text: str = Form(""),
                     size: float = Form(11), font: str = Form("helv"), color: str = Form("0,0,0"),
                     xref: int = Form(0)):
    """Freitext-Annotation anlegen oder (bei xref>0) mit neuen Eigenschaften neu erzeugen."""
    d = _doc(did)
    if page < 0 or page >= d.page_count:
        raise HTTPException(404, "Seite existiert nicht")
    if font not in FONTS:
        font = "helv"
    r = pymupdf.Rect(*[float(v) for v in json.loads(rect)])
    col = tuple(float(c) for c in color.split(","))
    pg = d[page]
    o_font, o_size, o_color, o_text = "helv", 11.0, [0, 0, 0], ""
    if xref:
        old = pg.load_annot(xref)
        if old is not None:
            r = pymupdf.Rect(old.rect)  # Rect der alten Annotation behalten (Groesse via Move aendern)
            old_nm = old.info.get("id", "") or ""
            o_font, o_size, o_color = _txt_props(old_nm)
            o_text = (old.info.get("content") or "").rstrip("\n")
            pg.delete_annot(old)
    a = pg.add_freetext_annot(r, text, fontsize=float(size), fontname=font, text_color=col)
    a.update()
    # Eigenschaften im NM-Marker konservieren (PyMuPDF-Ruecklesen ist unzuverlaessig)
    marker = f"PDFW-TXT:{font}:{size}:{col[0]},{col[1]},{col[2]}"
    d.xref_set_key(a.xref, "NM", f"({marker})")
    if xref:
        push_undo(did, {"op": "text-restore", "page": page, "new_xref": a.xref,
                        "old": {"rect": list(r), "text": o_text, "font": o_font,
                                "size": o_size, "color": o_color}})
    else:
        push_undo(did, {"op": "annot-delete", "page": page, "xref": a.xref})
    return {"ok": True, "xref": a.xref}


@app.post("/api/inserttext/{did}")
async def inserttext(did: str, page: int = Form(...), x: float = Form(...), y: float = Form(...),
                     text: str = Form(...), size: float = Form(11)):
    d = _doc(did)
    if page < 0 or page >= d.page_count:
        raise HTTPException(404, "Seite existiert nicht")
    d[page].insert_text((float(x), float(y)), text, fontsize=float(size))
    return {"ok": True, "page": page}


@app.post("/api/delete/{did}")
async def delete_text(did: str, page: int = Form(...), rects: str = Form(...)):
    """rects: JSON-Liste [x0,y0,x1,y1] - entfernt Text in diesen Bereichen (Redaction)."""
    d = _doc(did)
    if page < 0 or page >= d.page_count:
        raise HTTPException(404, "Seite existiert nicht")
    areas = json.loads(rects)
    if not areas:
        return {"ok": True, "removed": 0}
    pg = d[page]
    for r in areas:
        pg.add_redact_annot(pymupdf.Rect(r[0], r[1], r[2], r[3]))
    pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    return {"ok": True, "removed": len(areas)}


@app.get("/api/print/{did}")
def print_view(did: str):
    """Druckansicht: alle Seiten MIT Annotationen und ausgefuellten Formularen."""
    d = _doc(did)
    imgs = []
    for pno in range(d.page_count):
        pix = d[pno].get_pixmap(dpi=120, annots=True)
        b64 = base64.encodebytes(pix.tobytes("png")).decode().replace("\n", "")
        imgs.append(f'<img src="data:image/png;base64,{b64}">')
    html = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>body{margin:0}img{display:block;width:100%;page-break-after:always}"
            "@page{margin:0}</style></head><body>" + "".join(imgs) + "</body></html>")
    return HTMLResponse(html)


@app.get("/api/search/{did}")
def search(did: str, q: str):
    d = _doc(did)
    if not q.strip():
        return {"hits": []}
    hits = []
    for pno in range(d.page_count):
        try:
            for r in d[pno].search_for(q):
                hits.append({"page": pno, "rect": [r.x0, r.y0, r.x1, r.y1]})
        except Exception:
            pass
        if len(hits) >= 800:
            break
    return {"hits": hits}


@app.post("/api/rotate/{did}")
async def rotate(did: str, page: int = Form(...), delta: int = Form(90)):
    d = _doc(did)
    pg = d[page]
    pg.set_rotation((pg.rotation + int(delta)) % 360)
    push_undo(did, {"op": "rotate", "page": page, "delta": -int(delta)})
    return {"ok": True, "rotation": pg.rotation}


@app.post("/api/deletepage/{did}")
async def deletepage(did: str, page: int = Form(...)):
    d = _doc(did)
    if d.page_count <= 1:
        raise HTTPException(400, "Die letzte Seite kann nicht geloescht werden")
    d.delete_page(page)
    undo_stacks[did] = []   # Seitenindizes verschieben sich - Stapel sicherheitshalber leeren
    return {"ok": True, "pages": d.page_count}


@app.post("/api/undo/{did}")
def undo(did: str):
    d = _doc(did)
    stack = undo_stacks.get(did) or []
    if not stack:
        return {"ok": True, "undone": False}
    e = stack.pop()
    if e["page"] >= d.page_count:
        return {"ok": True, "undone": False}
    pg = d[e["page"]]
    op = e["op"]
    if op == "annot-delete":
        an = pg.load_annot(e["xref"])
        if an is not None:
            pg.delete_annot(an)
    elif op == "annot-move":
        an = pg.load_annot(e["xref"])
        if an is not None:
            r = pymupdf.Rect(e["rect"])
            an.set_rect(r)
            if an.type[1] == "FreeText":
                an.update()
                an.set_rect(r)
    elif op == "text-restore":
        an = pg.load_annot(e["new_xref"])
        if an is not None:
            pg.delete_annot(an)
        o = e["old"]
        a = pg.add_freetext_annot(pymupdf.Rect(o["rect"]), o["text"], fontsize=o["size"],
                                  fontname=o["font"], text_color=tuple(o["color"]))
        a.update()
        d.xref_set_key(a.xref, "NM",
                       f"(PDFW-TXT:{o['font']}:{o['size']}:{o['color'][0]},{o['color'][1]},{o['color'][2]})")
    elif op == "stamp-recreate":
        fname = os.path.basename(e.get("fname") or "")
        png = _sig_bytes(fname) if fname else None
        if png is not None:
            rot = int(e.get("rot") or 0)
            annot = pg.add_stamp_annot(pymupdf.Rect(e["rect"]))
            form_xref = _bild_als_erscheinung(d, png, rot)
            d.xref_set_key(annot.xref, "AP", f"<< /N {form_xref} 0 R >>")
            nm = f"(PDFW-SIG:{fname}:{rot})" if rot else f"(PDFW-SIG:{fname})"
            d.xref_set_key(annot.xref, "NM", nm)
    elif op == "sig-rotate":
        an = pg.load_annot(e["xref"])
        if an is not None:
            fname = e.get("fname") or ""
            png = _sig_bytes(fname) if fname else None
            rot_alt = int(e.get("rot") or 0)
            if png is None:
                pg.delete_annot(an)   # Signaturdatei weg - besser loeschen als falsch herum
            else:
                form_xref = _bild_als_erscheinung(d, png, rot_alt)
                d.xref_set_key(e["xref"], "AP", f"<< /N {form_xref} 0 R >>")
                nm = f"(PDFW-SIG:{fname}:{rot_alt})" if rot_alt else f"(PDFW-SIG:{fname})"
                d.xref_set_key(e["xref"], "NM", nm)
                an = pg.load_annot(e["xref"])
                an.set_rect(pymupdf.Rect(e["rect"]))
    elif op == "text-recreate":
        a = pg.add_freetext_annot(pymupdf.Rect(e["rect"]), e["text"], fontsize=e["size"],
                                  fontname=e["font"], text_color=tuple(e["color"]))
        a.update()
        d.xref_set_key(a.xref, "NM",
                       f"(PDFW-TXT:{e['font']}:{e['size']}:{e['color'][0]},{e['color'][1]},{e['color'][2]})")
    elif op == "field":
        for w in pg.widgets():
            if w.field_name == e["name"]:
                if w.field_type_string in ("CheckBox", "RadioButton"):
                    w.field_value = e["value"].lower() in ("1", "true", "yes", "an", "x")
                    w.update()
                else:
                    _feld_wert_setzen(d, w, e["value"])
    elif op == "rotate":
        pg.set_rotation((pg.rotation + e["delta"]) % 360)
    return {"ok": True, "undone": True, "page": e["page"], "op": op, "left": len(stack)}


if __name__ == "__main__":
    import argparse
    import uvicorn

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8491)
    ap.add_argument("--file", default=None, help="PDF, das beim Start geöffnet wird")
    args = ap.parse_args()
    if args.file:
        try:
            _open(args.file)
        except Exception:
            pass
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
