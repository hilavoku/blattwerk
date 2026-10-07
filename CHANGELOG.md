# PDF-Werkstatt — Changelog

Alle Versionen vom ersten Prototyp bis heute. Datum: 2026-10-07.

## v0.12.3 — Seitenvorschau: einklappen und Seite wählen
- Die Seitenvorschau lässt sich jetzt wie die Lesezeichen-Leiste **am Rand ein-
  und ausklappen** (neuer Griff neben der Spalte; der „Seiten"-Knopf unten wirkt
  weiterhin, beide steuern denselben Zustand).
- **Beide Bereiche sind frei positionierbar:** Seitenvorschau und Lesezeichen-
  Leiste haben je einen Pfeilknopf („auf die andere Seite verschieben") — so sind
  z. B. beide Bereiche links oder beide rechts möglich. Auch das wird gespeichert
  (wie Theme und Einklapp-Zustand, über `/api/prefs`).
- Technik: Layout über flex-`order` statt `row-reverse` (dafür waren die Bereiche
  zwangsläufig auf gegenüberliegenden Seiten). Alte Einstellung „Seitenleiste
  links" wird beim ersten Start automatisch auf das neue Modell übertragen.

## v0.12.2 — Ziehen verschiebt die Seite, Kopieren per Alt+Ziehen
- **Ziehen mit der Maustaste auf dem Papier schiebt jetzt die Ansicht** (Pan,
  Hand-Cursor beim Ziehen) — vorher wurde dabei die Kopier-Auswahl aufgezogen.
- Die Freihand-Textauswahl gibt es weiterhin, per **Alt+Ziehen**. Unverändert:
  einzelne Zeile anklicken kopiert, Strg+Klick hängt an, Doppelklick editiert
  den Originaltext.
- Nur im normalen Modus (Signatur-/Text-/Löschen-Modus arbeiten wie bisher).
  Kurzhilfe aktualisiert.

## v0.12.1 — Zoom hält den Mauspunkt fest
- **Strg+Mausrad zoomt auf den Punkt unterm Cursor** (vorher lief das Bild immer
  zur oberen linken Ecke der Seite). Nach dem Zoom bleibt derselbe Dokumentpunkt
  unter der Maus — rein- und rauszoomend, horizontal wie vertikal.
- Die +/−-Knöpfe der Zoomleiste zoomen jetzt auf die **Bildschirmmitte** statt
  zur Seitenoberkante (wie Browser/Word).
- Am Zoomlimit (30–400 %) ruckt es nicht mehr: überschüssige Radschläge
  verschieben die Ansicht nicht (vorher konnte der Anker-Ausgleich scrollen).
- Technik: `applyZoom` nimmt optional einen Fokus (Seite unterm Punkt + Anteil
  rx/ry); die Scroll-Korrektur läuft gebündelt in einem rAF, bei schnellen
  Radschlägen gewinnt der letzte Anker.

## v0.12 — Originaltext editieren (wie PDFgear, nur echter Text)
- **Doppelklick auf eine Textzeile** (echter Text, kein Scan-Bild) öffnet ein
  Eingabefeld direkt über dem Text, mit übernommener Schriftgröße/-farbe/-art
  (Helvetica/Times/Courier + Fett/Kursiv aus der dominanten Textspanne).
- Enter übernimmt: Originaltext wird an der Stelle entfernt (Redaction), der neue
  als echter Seiteninhalt mit gleicher Basislinie eingesetzt. Leerer Text/der rote
  Knopf = Originaltext entfernen. Strg+Z stellt den Originaltext zurück.
- Einzelklick kopiert weiterhin (Doppelklick kopiert nicht mehr aus Versehen);
  /api/textspan liefert die Schriftdaten für die Vorschau. Suite +5 Checks (47).

## v0.11.5 — Auswahlrechteck verschwindet beim Loslassen
- Fix: Das blaue Auswahlrechteck blieb nach dem Kopieren stehen und sammelte sich
  bei jedem weiteren Zug an (es wurde nie entfernt und wanderte beim Zoomen nicht
  mit). Jetzt wird es beim Loslassen entfernt; Sicherheitsnetz in clearFreeSel und
  beim Seiten-Neuaufbau. Beim Ziehen ist es weiterhin sichtbar.

## v0.11.4 — Knopf „Kopie herunterladen" entfernt, Auswahl-Hinweise
- „Kopie herunterladen" (Überbleibsel vor „Speichern unter") aus der Kopfzeile entfernt.
- Zieht man eine Text-Auswahl über einen Bereich ohne erkannten Text, sagt die
  Statusleiste jetzt „Kein Text in der Auswahl…" (vorher geschah sichtbar nichts).
- Kurzhilfe ergänzt: Kopieren per Aufziehen oder Zeilen-Klick.

## v0.11.3 — Freihand-Auswahl startet auf Textblöcken
- Fix: Das Aufziehen der Textauswahl startete nur auf „leerem Papier" — bei OCR-Seiten
  liegt aber fast überall ein Textblock-Overlay, also traf der Start fast immer einen
  Block und die Auswahl erschien nie (übrig blieb der Einzelklick pro OCR-Block).
  Jetzt startet das Aufziehen auch direkt auf Textblöcken; der Einzelklick kopiert
  weiterhin eine Zeile, Strg+Klick hängt an.

## v0.11.2 — Drehen ohne Springer
- Fix: Nach dem Drehen am Griff flippte die Signatur kurz auf die alte Darstellung
  zurück, bevor die neue kam. Jetzt bleibt die Live-Drehung bis zum Abschluss stehen;
  das gedrehte Bild wird vorab geladen und Kasten/Bild/Daten in einem Rutsch am
  vorhandenen Overlay ausgetauscht (kein Neuaufbau, kein Flackern — auch beim
  Winkelfeld und der 90°-Aktion).

## v0.11.1 — Drehgriff am Rahmen + Funktionsleisten-Start-Fix
- **Direkt drehen:** Runder Griff über der ausgewählten Signatur — daran ziehen dreht
  live (Rahmen dreht mit); Umschalt-Taste rastet auf 15°-Schritte, der Winkel wird
  während des Ziehens angezeigt. Winkelfeld bleibt für exakte Werte.
- Fix (Toolbar): Beim Start zeigte die Funktionsleiste nicht alles und brach erst nach
  manueller Fenstergrößenänderung um. Ursache: Breitenänderungen NACH dem Laden
  (Signatur-Vorschau im Knopf, Schriftart-Wechsel) erwischen die fixen Timeouts.
  Jetzt ereignisbasiert nachgeführt (ResizeObserver, load, document.fonts.ready,
  Vorschaubild-Load).

## v0.11 — Signaturen in beliebigen Winkeln drehen
- Winkel-Feld in der Eigenschaftsleiste (nur bei Signatur): Zielwinkel in Grad frei
  eingeben (positive Winkel = im Uhrzeigersinn). Rechtsklick → „Drehen (90°)" dreht
  wie bisher als Schnellaktion weiter.
- Der Server dreht das Bild IMMER vom Original aus um den Gesamtwinkel (keine
  Qualitätsverluste bei wiederholtem Drehen, kein Aufblähen durch Kaskadierung);
  der Auswahl-Kasten wird auf die gedrehte Hülle skaliert — die Signatur behält
  ihre Größe, der Kasten wächst nur um die schrägen Ecken.
- Overlay-Ansicht und eingebettetes PDF-Bild sind identisch (serverseitig gedrehte
  Vorschau über /api/signature/file?rot=…). Undo dreht zurück. Suite um freie
  Winkel erweitert (42 Checks).

## v0.10.3 — Einbrennen auch bei „Speichern unter"
- Fix: Die Einbrennen-Abfrage kam nur beim normalen „Speichern" — „Speichern unter"
  schrieb immer bewegliche Annotationen. Jetzt dieselbe Abfrage (bzw. direktes
  Speichern ohne Objekte) auch dort; Server: /api/saveas?flatten=1.
- Die Checkbox „Auswahl merken" ist entfallen: Wer einmal „beweglich + merken" gewählt
  hatte, kam nie wieder zur Einbrennen-Frage. Der Dialog erscheint jetzt bei jedem
  Speichern/Speichern-unter, sobald bewegliche Objekte vorhanden sind.
- Statusmeldungen präzisiert: „Gespeichert (eingebrannt)" bzw.
  „Gespeichert (beweglich) – Signaturen/Texte bleiben änderbar".
- Datei-Beweis geführt (frisch geöffnete PDFs): flatten=1 → Signatur im Seiteninhalt,
  keine Annotationen; flatten=0 → Annotation mit eingebettetem Bild in der Datei.

## v0.10.2 — „Speichern unter" wechselt das Arbeitsdokument
- Fix (UX): Nach „Speichern unter" blieb die Änderungsmarkierung stehen — beim Beenden
  kam die Warnung „nicht gespeicherte Änderungen", obwohl gerade gespeichert wurde.
  Jetzt wie üblich (Word & Co.): Die neue Datei wird das Arbeitsdokument — Warnung
  entfällt, Strg+S und Speichern-beim-Schließen schreiben die neue Datei, Statusleiste
  meldet den Wechsel. Server öffnet das Dokument nach dem Kopieren neu (ohne garbage,
  damit Undo-Referenzen stabil bleiben); Annotationen/Undo bleiben nutzbar.

## v0.10.1 — Logo im Startbildschirm
- Startbildschirm und Fehlerbildschirm zeigen das App-Logo (Base64 aus der
  Server-Instanz `server\_internal\static\logo.png`, Fallback: Entwicklungspfad bzw. Symbol)

## v0.10 — Speichern unter, Drehen, Einbrennen, Passwort-Signaturen
- **Speichern unter**: Toolbar-Knopf, Systemdialog (Wrapper), Kopie inkl. aller Änderungen
  über `/api/saveas`; Meldung per Skript-Rückkanal in die Statusleiste
- **Signatur drehen**: Rechtsklick → „Drehen (90°)", beliebig oft; Rect tauscht um das
  Zentrum, Bild wird vorgedreht neu eingebettet (NM-Marker führt den Winkel mit);
  Strg+Z dreht zurück. Neu anlegen statt AP-Tausch geht nicht: add_stamp_annot
  normalisiert das Rect (neue PyMuPDF-Falle, in AGENTS.md dokumentiert)
- **Einbrennen beim Speichern**: Speichern fragt (falls bewegliche Objekte da sind):
  „Einbrennen & speichern" (Signatur/Texte werden fixer Seiteninhalt, in keinem PDF-Programm
  mehr entfernbar; Formularfelder bleiben ausfüllbar) oder „Beweglich speichern".
  Auswahl merkbar (Einstellung `flatten`). Server: `bake(widgets=False)`
- **Passwortgeschützte Signaturen**: Beim Hochladen optionales Passwort → Datei liegt
  als `.pwdsig` AES-verschlüsselt (Fernet + PBKDF2-SHA256, 200k Iterationen) — im
  Gegensatz zu PDFgear ist die Signatur auf der Festplatte nicht mehr auslesbar.
  Passwort gilt bis Programmende (RAM), wird nie gespeichert. Galerie zeigt Schloss,
  Entsperr-Dialog mit Fehlermeldung bei falschem Passwort. Nach Serverneustart wieder
  gesperrt. Löschen/Umbenennen ohne Passwort möglich (Dateiname, nicht Inhalt)
- Fix (mitgefunden): Kopfzeilen-Knöpfe „Kopie herunterladen" und „Drucken" waren seit
  der Toolbar-Umstellung deaktiviert
- Neues Signatur-Icon (Unterschriftszug statt Stift)
- Suite um 8 Checks erweitert (33 gesamt): Speichern unter, Drehen+Undo, Einbrennen,
  verschlüsselte Ablage, Sperrzustand nach Neustart

## v0.9 — Einstellungen & Fenster bleiben gespeichert
- Fix: Einstellungen (Theme, Seitenleiste links/rechts + ein-/ausgeklappt, Miniaturen)
  überlebten den Neustart nicht — localStorage ist pro Server-Port, und der Port wechselt
  bei jedem Programmstart. Jetzt: `/api/prefs` (GET/POST) speichert in
  `PDF-Werkstatt\einstellungen.json` (neben der EXE, überlebt Server-Updates).
- Neu: Fensterposition, -größe und Maximiert-Zustand werden beim Schließen in `fenster.json`
  gespeichert und beim Start wiederhergestellt (Off-Screen-Schutz bei Monitorwechseln,
  DPI-korrekt da WinForms logische Koordinaten nutzt).
- Wrapper neu gebaut (`dotnet publish`); beim Deployment bleiben neben den Signaturen jetzt
  auch `einstellungen.json`/`fenster.json` erhalten.

## v0.8.1 — Fix: Signatur-Kopien & Löschen
- Fix: Nach Zoomen verdoppelten sich die Overlays (Signatur-/Text-"Kopien"). Ursache: Das
  Scharfstellen des Seitenrasters (loadFresh) feuerte img.onload → buildPage baute die Overlays
  NEU, ohne die alten zu entfernen. Jetzt: onload wird beim stillen Bildtausch gelöst; buildPage
  räumt vor dem Neuaufbau auf und entwertet laufende Aufbauten per Generationen-Token (deckt auch
  die Undo-Race zwischen refreshPage und reloadAnnots ab). Server-PDF war nie betroffen
  (nachgewiesen per Repro: set_rect erzeugt keine Duplikate).
- Neu: Rechtsklick auf Signatur/Text öffnet eigenes Kontextmenü (Löschen; Text zusätzlich
  Bearbeiten) — statt des WebView2-Bildmenüs ("Bild speichern"/"Bild kopieren"). Eingabefelder
  behalten ihr natives Menü.
- Neu: Entf-Taste löscht die ausgewählte Signatur/Text (Strg+Z holt beides zurück).

## v0.8 — Freihand-Auswahl, Miniaturen, Rückgängig
- Text per Maus aufziehen und kopieren (Auswahlrechteck, Chip „Kopieren", Strg+C)
- Miniatur-Leiste links (Klick springt, aktuelle Seite markiert, ein-/ausblendbar)
- Rückgängig (Strg+Z / Knopf) für Objekte, Verschieben, Formularfelder, Drehen
- Fix: Formularfelder leeren war unmöglich (PyMuPDF ignoriert „")
- Tests auf Isolation umgestellt (25 Checks, fassen Nutzerdaten nicht mehr an)

## v0.7.x — Inline-Text, Layout-Freiheit
- Texteingabe direkt auf dem PDF (kein Dialogfenster); Schrift/Stil/Größe/Farbe in der Kopfzeiste, wirkt live
- Fix: Verschieben von Text/Signatur sprang zur alten Position zurück (Server + Frontend)
- Theme-Schalter hell/dunkel (bleibt gespeichert)
- Seitenleiste: links/rechts verlegbar, einklappbar über Griff „< >" an der Kante
- Eigenschaftsleiste X/Y/Breite/Höhe für ausgewählte Objekte; Signatur nach Platzierung sofort ausgewählt
- Toolbar responsiv: Beschriftungen→Icons→Marke aus→zweite Reihe

## v0.6.x — Signatur-Verwaltung, Icons, Polish
- Signaturen-Galerie mit Vorschaubildern, Umbenennen und Löschen (Verweise in Dokumenten ziehen mit)
- Fix: erstes Zeichen von Signaturdateinamen wurde abgeschnitten (Off-by-one)
- Fix: Edge-Fehlerseite beim Start (Splash + Health-Poll, eigener Fehlerbildschirm)
- Fix: WebView2-Cache lieferte alte UI (globales no-cache)
- Fix: wörtliche \uXXXX-Escapes im HTML (62 Stellen auf echte Umlaute)
- Programm-Icon in drei Versionen (final: transparent, Deutschland-Schlinge)

## v0.5 — Aussehen und Grundausstattung
- Komplettes UI-Redesign (Fluent-dark), Statusleiste, Icons
- Zoom (jetzt v0.6.4 fluid: stufenlos, ohne Flackern, Scharfstellung im Hintergrund)
- Volltextsuche mit Treffer-Navigation, Seiten-Navigation, Drehen, Seite löschen
- Drucken (inkl. Signaturen, Texte, Formularwerte), Drag&Drop, Strg+S/O, Esc
- Schließen-Schutz bei ungespeicherten Änderungen (Dialog: Speichern/Verwerfen/Abbrechen)
- Lokale EXE-Installtion ersetzt den Webserver-Betrieb

## v0.4 — Annotation-Architektur
- Signaturen und Texte sind echte, bewegliche PDF-Annotationen (kein Einbrennen)
- Signaturen: Stamp-Annotation mit selbstgebauter Bild-Erscheinung (Bild+SMask+Form)
- Texte: FreeText-Annotationen, Editierbarkeit durch Neu-Erzeugen

## v0.3 — Die fünf Kernfunktionen
- Lesezeichenübersicht, Signaturen setzen (Hintergrund-Entfernung wie PDFgear),
  Text kopieren (Zeilen-Klick), Formularfelder, Text einfügen/löschen (Redaction)
- 6 Unterschriften aus PDFgear übernommen

## v0.2 — Erstes echtes Programm
- WebView2-Fenster + gebündelter PyInstaller-Server, Doppelklick-Vorbereitung
- Server, Suche-freie Grundansicht, Lesezeichen, Formularfelder, Speichern/Laden

## v0.1 — Prototyp
- Browser-Variante auf dem Entwicklungsrechner (später zugunsten der lokalen EXE eingestellt)
