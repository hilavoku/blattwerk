# PDF-Werkstatt — Changelog

Alle Versionen vom ersten Prototyp bis heute. Datum: 2026-10-06 (Entwicklungstag).

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
