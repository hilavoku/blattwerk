# Blattwerk — Changelog

Alle Versionen vom ersten Prototyp bis heute. Datum: 2026-10-07.

## v0.17.3 — Block-Markierung bleibt nach Zeilenersatz erhalten
- Nach dem zeilenweisen Ersetzen (v0.17.2) bekam die neue Zeile eine eigene
  PDF-Blocknummer und leuchtete beim Überfahren nicht mehr mit dem Rest des
  Blocks mit. Die Block-Gruppierung fasst jetzt zusammen, was zusammengehört:
  gleicher PDF-Block **oder** gleiche Zeile (y-Überlappung) — ersetzte
  Tabellen-Zeilen (Betrag/Datum) bleiben optisch Teil ihres Blocks, wie vor
  der Bearbeitung.

## v0.17.2 — Tabellen/Spalten beim Bearbeiten nicht mehr zerstört
- Mehrfach-Auswahlen mit **Spalteninhalt** (Datum links, Beschreibung Mitte,
  Betrag rechts sind im PDF eigene Zeilen auf gleicher Höhe) wurden beim
  Übernehmen zu einem fließenden Textblock zusammengezogen — das Spaltenlayout
  war hinüber. Jetzt erkennt Blattwerk überlappende Zeilen und ersetzt
  **zeilenweise an der jeweiligen Originalposition**: Unveränderte Zeilen
  bleiben völlig unberührt, geänderte landen exakt dort, wo ihre Originalzeile
  lag (Spalten-x und Zeilen-y). Absatz-Blöcke (Zeilen untereinander) nutzen
  weiterhin das verschiebbare Sammelobjekt mit erhaltenem Zeilenraster.

## v0.17.1 — Originaltext-Editor voll deckend (Doppeltext sicher ausgeschlossen)
- Der deckende Hintergrund des Originaltext-Editors (v0.17.0) war mit 96 %
  fast deckend — Restdurchschein des alten Texts ist jetzt sicher
  ausgeschlossen (voll opak). Hinweis: Die Ansicht zeigt den Fix erst nach
  einem App-Neustart.

## v0.17.0 — Mehrzeiligen Originaltext positionsgetreu bearbeiten
- **Zeilenpositionen bleiben erhalten:** Beim Bearbeiten mehrzeiliger
  Originaltexte (Block-Doppelklick oder Umschalt+Klick-Sammlung) übernimmt der
  neue Text jetzt die **Baseline der ersten Zeile und den gemessenen
  Zeilenabstand** des Originals — nicht mehr das starre 1,25-fache Raster.
  Unveränderte Zeilen stehen nach dem Übernehmen auf Zehntel-Punkt exakt dort,
  wo das Original stand; auch im gespeicherten PDF (Zeilenabstand wird im
  NM-Marker geführt und gilt für Overlay, Appearance, Verschieben und Undo).
- **Originaltext-Editor deckend:** Unter dem Eingabefeld steht beim
  Originaltext der alte Text noch im Papier — das Feld hat deshalb jetzt einen
  deckenden Papier-Hintergrund (vorher durchscheinend: „Buchstabenwald").
  Neu eingetippter Text bleibt wie gewohnt transparent.
- Längere Zeilen erweitern das Textobjekt jetzt nach Bedarf in der Breite
  (zuvor wurde längerer Text an der Original-Blockbreite abgeschnitten).

## v0.16.10 — Fix: weiße Striche im Fensterrand nach dem Vergrößern weg
- Beim Ziehen der Fensterkante blieben stellenweise kleine weiße vertikale
  Striche in der Verlaufszone stehen (das WebView2 malt während der
  Größenänderung kurz über die Randzone, bevor die Form sie wieder
  übermalt). Der Rand wird jetzt nach jedem Größenänderungsschritt
  vollständig neu gezeichnet — sofort und nochmals nach dem Layout
  (mit Handle-Schutz, sonst wäre die App beim Start weggeworfen worden).

## v0.16.9 — Schwarz-Rot-Gold-Rand jetzt in beiden Designs
- Der Verlaufsrand (nahtloser Umlauf, v0.16.7) gehört nicht mehr nur zum
  hellen Design — konsequenterweise trägt ihn jetzt auch das dunkle.
  Maximiert bleibt das Fenster randlos wie gehabt.

## v0.16.8 — Design-Knopf fix oben rechts neben den Fenstertasten
- Der Design-Umschalter (Sonne/Mond) wanderte beim Umbrechen der Leiste mit
  in Folgezeilen. Er sitzt jetzt in der fixen Zone der ersten Zeile, direkt
  links neben Minimieren — bei jeder Fensterbreite. Der Leisteninhalt hält
  rechts entsprechend mehr Abstand.

## v0.16.7 — Rand-Verlauf als nahtloser Umlauf
- Der Schwarz-Rot-Gold-Verlauf lief je Seite einzeln und sprang an zwei Ecken
  von Gold auf Schwarz. Jetzt läuft er als geschlossener Umlauf ums Fenster:
  oben schwarz→gold, rechts gold→schwarz, unten (weiter im Uhrzeigersinn)
  schwarz→gold, links gold→schwarz — an jeder Ecke treffen gleiche Farben
  aufeinander, kein Sprung mehr.

## v0.16.6 — Heller Fensterrand: Schwarz-Rot-Gold statt Schwarz
- Im hellen Design war der Fensterrand komplett schwarz — hart am hellen
  Fenster. Jetzt zeigt er dort den Marken-Verlauf **Schwarz → Rot → Gold**
  (wie Icon und Kopfzeilen-Band), rundum auf allen vier Seiten. Im dunklen
  Design bleibt der Rand dunkel wie bisher.
- Die UI meldet dem Fenster beim Start und bei jedem Designwechsel den
  Theme-Zustand (`theme|light/dark` über den WebView2-Kanal); maximiert
  bleibt das Fenster randlos.

## v0.16.5 — Fensterrand rundum: oben geschlossen (und greifbar)
- Der dunkle Fensterrand lief bisher nur unten/links/rechts — oben endete das
  Fenster unsichtbar an der Bildschirmkante. Jetzt zieht sich die 6px-Leiste
  rundum, auch über der Kopfzeile: Das Fenster ist oben klar abgegrenzt.
- Die obere Kante ist zugleich Größengriff (wie unten/links/rechts): Ziehen
  verändert die Fensterhöhe; die Ecken oben-links/oben-rechts ändern die
  Größe diagonal. Maximiert bleibt das Fenster randlos über dem Bildschirm.

## v0.16.4 — Fenstertasten IMMER oben rechts (auch bei Umbruch)
- Die Tasten Minimieren/Maximieren/Schließen wanderten bei engen Fenstern
  mit in die zweite Kopfzeilenzeile. Jetzt sind sie absolut oben rechts
  verankert: Sie bleiben IMMER in der ersten Zeile, während der Rest der
  Leiste bei Bedarf in Folgezeilen umbricht (die Tastenzone bleibt rechts
  immer frei — kein Element läuft unter die Tasten).
- Die Stufen der Leiste (Beschriftungen aus → Marke schlank → zweite Reihe)
  wirken unverändert, messen aber jetzt den Inhaltsstreifen.

## v0.16.3 — Block-Editor: Undo stellt jede Zeile exakt wieder her
- Nach der Block-Bearbeitung (v0.15.0) hingen die Zeilen nur als ein Objekt
  zusammen, und Undo setzte den gesamten Text an die Position der ersten
  Zeile. Jetzt tilgt der Server alle beteiligten Zeilen in einem Zug
  (`/api/text/blockreplace`) — der EINE Undo-Eintrag („origzeilen") stellt
  **JEDE Zeile an ihrer eigenen alten Position** wieder her: erst Strg+Z
  nimmt das neue Textobjekt weg, das zweite Strg+Z holt alle Originalzeilen
  unverrückt zurück. Die Zeilen-Rückrestoration nutzt die exakte Basislinie
  aus dem Dokument (neuer Helfer `_zeile_in_rect`), nicht die einer
  Nachbarzeile (dort irrte die alte Spannensuche bei engem Zeilenabstand).
- Der Entfernen-Knopf im Editor geht denselben Weg (alle Zeilen, ein Undo).
- **Mehrzeilige Textobjekte stimmen jetzt mit dem gespeicherten PDF überein:**
  MuPDFs eigenes Freitext-Aussehen rendert Zeilen mit ~2,4-fachem Abstand und
  schneidet Folgelinien an der Box ab (4. Zeile war nach dem Speichern weg).
  Blattwerk setzt deshalb IMMER seinen eigenen Appearance-Stream (1,25-faches
  Leading, Baseline wie das Overlay) — nicht mehr nur bei Zeichenabstand.
- **Doppel-Commit gebunden:** Das Übernehmen mit Enter entfernte die Textarea,
  deren blur-Handler startete den Commit sofort ein zweites Mal (Rennen:
  verschwundene Annotationen, doppelte Redactions). Der Editor-Status wird
  jetzt entzogen, bevor DOM-Knoten entfernt werden — gilt auch für den
  Neutext-Editor.
- Mehrzeilige Textobjekte zeigen ihre Zeilenumbrüche jetzt auch als Overlay.
- Bekannt (bestehendes Verhalten, nicht neu): Redaction arbeitet wortgenau —
  bei einzeln gesammelten Zeilen mit weniger als ~1,3 Zeilenabstand kann eine
  dazwischenliegende Nachbarspalte mit entfernt werden (gilt seit v0.12 für
  Einzeledits genauso). Ganze Blöcke sind nicht betroffen.

## v0.16.2 — Fenstertasten sticky: bleiben bei schmalen Fenstern immer oben rechts sichtbar (opake Fläche)
## v0.16.1 — Kopfzeile höher mit Logo/Name zurück und Grifffunken als sichtbare Zieh-Zonen; Fenstertasten rechts
## v0.16.0 — Rahmenloses Fenster: Kopfzeile als Titelleiste (Ziehen/Doppelklick-Max), Fenstertasten min/max/zu über Wrapper-PostMessage, Resize-Ränder per WM_NCHITTEST, taskbar-sicheres MaximizedBounds

## v0.15.0 — Textblöcke: Hover, Block-Editor, Zeilen sammeln
- **Block- Hover:** Originaltext-Zeilen werden serverseitig zu Blöcken gruppiert
  (Absätze) — fährt man mit der Maus über eine Zeile, leuchtet der ganze Block.
- **Doppelklick bearbeitet den ganzen Block:** Der Editor öffnet mit allen Zeilen
  des Blocks als mehrzeiligem Text; nach dem Übernehmen ist der ganze Block ein
  verschiebbares Objekt (Schrift, Größe, Farbe, Abstand wie gewohnt änderbar).
- **Umschalt+Klick sammelt Zeilen:** Mehrere einzelne Zeilen markieren und dann
  per Doppelklick auf eine der Markierten gemeinsam bearbeiten.
- Server: `/api/text` liefert je Zeile die Blocknummer (`b`, aus PyMuPDF-Blocks).

## v0.14.7 — Bedienung: Mausrad für Größe/Abstand, bequeme Exits im Text-Modus
- **Mausrad über den Feldern „Schriftgröße" und „Zeichenabstand"** ändert die
  Werte (± 1 bzw. ± 0,25) — ohne das Feld anzuklicken; wirkt live auf Editor
  und ausgewählte Texte.
- **Text-Modus beenden:** Rechtsklick auf die Seite, Esc (schließt den Editor
  mit) oder Klick neben ein offenes Textfeld — zusätzlich zu T/Auswahl.
  Esc im Originaltext-Editor verwirft weiterhin die Änderung und beendet.
- Der Freitext-Editor selbst erlaubt weiter Mehrzeilentippen über Enter
  (Commit nur über Strg+Enter oder Klick neben dem Feld).

## v0.14.6 — Editier-Feld transparent: Hintergrund beim Tippen sehen
- Das Eingabefeld (neuer Text wie Originaltext-Editor) ist jetzt **transparent** —
  beim Tippen sieht man das Papier bzw. das Formular darunter und kann Text,
  Position und Zeichenabstand direkt daran ausrichten. Der gestrichelte Rahmen
  markiert weiter den Bearbeitungsbereich.

## v0.14.5 — Fix: Schriftänderung wirkt jetzt auf angeklickte Texte (und Fett/Kursiv überall)
- **Die Werkzeugleiste wirkt live auf angeklickte Text-Annotationen:** Text
  anklicken, Schrift/Familie/Stil/Größe/Farbe/Abstand oben ändern — sofort
  übernommen, Selektion bleibt erhalten. Vorher reagierte die Leiste nur während
  des Editors (und ein Klick in die Leiste schloss den Doppelklick-Editor nicht).
- **Fix: Fett/Kursiv bei Times und Courier schlug still auf Helvetica zurück** —
  die Alias-Bildung 'tirob'/'courb' war ungültig (richtig: tibo/cobo); jetzt
  systematische Alias-Tabelle im Client und Rück-Aufsplitten beim Editor-Öffnen
  (Fett-Texte zeigen Familie+Stil korrekt in der Leiste).
- Der Editor-Pfad (Doppelklick) bleibt unverändert; auch dort gilt die
  korrekte Alias-Bildung jetzt beim Übernehmen.

## v0.14.4 — Zeichenabstand (Spacing) für Text
- **Neues Werkzeugleisten-Feld „Zeichenabstand"** (Punkte, auch negativ für
  engere Texte): wirkt live in der Editor-Vorschau und auf neue und bearbeitete
  Text-Annotationen.
- Umsetzung: bei Spacing ≠ 0 erzeugt der Server einen eigenen Appearance-Stream
  für die Annotation (PDF-Operator `Tc`); der Spacing-Wert wandert in den
  NM-Marker (5. Feld) und bleibt damit bei Verschieben, Bearbeiten, Undo und
  „Speichern unter" erhalten.
- **Einbrennen:** Gespacete Freitexte werden vor dem Einbrennen zeichenweise als
  echter Seiteninhalt eingesetzt (Zeichenabstand bleibt exakt erhalten), danach
  wie üblich gebaked.

## v0.14.3 — Eingebettete Bilder verschieben
- **Grafiken im PDF bewegen:** Eingebettete Bilder (Logos, Fotos) werden im
  normalen Modus als greifbare Objekte angezeigt (gestrichelter Rahmen beim
  Hovern) — anklicken, ziehen, fertig. Die alte Stelle wird weiß überdeckt, das
  Bild an der neuen Stelle wieder eingesetzt (gleiche eingebettete Grafik per
  xref, keine Re-Qualitätseinbuße). Strg+Z schiebt zurück.
- Neue Endpunkte: `/api/imageinfo` (Platzierungen je Seite) und `/api/image/move`.
  Ganzseitenbilder (Scans) und Inline-Bilder bleiben bewusst fix.
- Grenzen: Die alte Bildstelle bleibt in der Datei erhalten (nur weiß überdeckt);
  bei erneutem Verschieben nach Neuladen wird die neue Platzierung gegriffen.

## v0.14.2 — Text-Modus: Bereich aufziehen statt nur Punkt klicken
- **Mit gedrückter Maustaste den Textbereich aufziehen:** Im Text-Modus zeichnet
  man jetzt den Kasten für den neuen Text direkt auf (Rahmen wie bei der
  Freihand-Auswahl); der Editor öffnet sich exakt in diesem Bereich, und die
  Annotation übernimmt die aufgezogene Größe (WYSIWYG — bei längerem Text wächst
  der Kasten noch mit). Der Editor schrumpft beim Tippen nicht mehr auf eine
  Zeile zusammen.
- Ein stiller Klick behält das bisherige Verhalten (Standard-Kasten an der
  Klickstelle, Breite passt sich dem Text an).

## v0.14.1 — Originaltext-Editor: Schrift erreichbar, Text verschiebbar
- **Fix:** Ein Klick in die Schrift-Werkzeuge hat den Editor sofort committet und
  geschlossen (Blur-Committ ohne Ausnahme für die Werkzeugleiste) — deshalb wirkte
  Schriftänderung „unmöglich". Jetzt bleibt der Editor offen, solange in der
  Leiste gearbeitet wird (wie beim Freitext-Editor).
- **Der geänderte Text wird jetzt zum verschiebbaren Objekt:** Nach dem Übernehmen
  wird die Originalzeile wegredigiert und der neue Text als Freitext-Annotation
  an derselben Stelle angelegt — greifen & ziehen, Schrift/Größe/Farbe später per
  Doppelklick änderbar, Einbrennen beim Speichern wie bei jeder Annotation.
  Strg+Z nimmt die Änderung mehrschrittig zurück (Objekt weg, Originalzeile zurück).
- Reines Entfernen (Löschen im Editor) bleibt echte Redaction ohne Objekt.

## v0.14.0 — Die App heißt jetzt **Blattwerk**
- Umbenennung an allen sichtbaren Stellen: Fenstertitel und Taskbar („Blattwerk –
  Datei.pdf"), Splash-Screen, Kopfzeile, HTML-Titel, Demodokument
  („Blattwerk Demo-Dokument"), Fehler- und Hinweisdialoge, FastAPI-Titel.
- Technische Namen bleiben unverändert (Exe PdfWerkstatt.exe /
  PdfWerkstattServer.exe, Projektordner pdf-werkstatt, Dateizuordnung und
  Deploy-Pfade funktionieren weiter wie gehabt).
- Vollswap-Deployment nötig, da der Wrapper (Fenstertitel) geändert wurde;
  Einstellungen, Fensterlage und Signatur-Ordner wurden gesichert und
  zurückgespielt. Demodokument wird beim nächsten Start mit neuem Titel erzeugt.
- Namensfindung: „Blattwerk" = Blatt (PDF-Seite) + Werk; im PDF-Markt
  kollisionsfrei (Nutzerentscheidung aus 3 Kandidaten).

## v0.13.4 — Dark Theme: dunkles Grau + weiche Flaggen-Verlaufskante
- Rückmeldung umgesetzt: Der Dark-Theme-Grundton ist wieder **dunkles Grau**
  (statt fast Schwarz) — damit heben sich schwarze Elemente sichtbar ab.
- Die Schwarz-Rot-Gold-Kante der Kopfzeile verläuft jetzt als **weicher
  Farbverlauf** (Schwarz → Rot → Gold) statt in harten Dritteln.

## v0.13.3 — Dark Theme in Schwarz-Rot-Gold
- **Nationalfarben im Dark Theme:** tiefschwarze Flächen (Dokumentbereich,
  Kopfzeile, Panels), **Gold** als Akzentfarbe (aktives Werkzeug, Pill,
  Auswahlrahmen, Auswahlfeld-Ränder, Slider, primäre Dialogknöpfe), **Rot** für
  Gefahr/Löschen. Dazu eine dezente Schwarz-Rot-Gold-Kante an der Oberkante der
  Kopfzeile.
- Die Auswahl- und Fokusfarben (Freihand-Auswahl, Zeilenmarkierung, Textfelder)
  sind jetzt themengesteuert: Dark = Gold, Light = unverändert Blau. Das Light
  Theme bleibt komplett, wie es war.

## v0.13.2 — Fix: eingebrannte Signatur bleibt nach dem Speichern sichtbar
- Beim Speichern mit Einbrennen verschwand die Signatur optisch aus der Ansicht:
  die Overlays wurden entfernt, aber das Seitenbild stammte noch von vor dem
  Einbrennen. Erst das Neuladen des Dokuments zeigte sie wieder.
- Jetzt liefert `/api/save` die betroffenen Seiten mit (Seiten mit Annotationen
  vor dem Einbrennen), und die UI lädt genau diese Seitenbilder neu — die
  eingebrannte Signatur ist sofort sichtbar. „Speichern unter" mit Einbrennen
  aktualisiert die Seiten mit Overlays ebenfalls (Wrapper-Pfad).

## v0.13.1 — Fix: Modus-Pill sitzt exakt, auch nach Größenwechseln
- Die gleitende Werkzeug-Pill war vertikal statisch verankert und maß ihre
  Position nur einmal — sobald die Knopfbeschriftungen verschwanden (schmales
  Fenster), saß sie verschoben und in alter Größe. Jetzt: vertikale Position
  dynamisch, und die drei Modus-Knöpfe werden per ResizeObserver beobachtet —
  die Pill folgt jeder Größenänderung pixelgenau.

## v0.13.0 — Motion: die App bewegt sich (alle Stufen des Motion-Konzepts)
- **Fundament:** Motion-Tokens (Dauern 120/180/260/380 ms, Kurven standard/in/out/
  pop) als CSS-Variablen; `prefers-reduced-motion` schaltet alles ab; Knöpfe
  federn beim Drücken (scale .96); Dialoge und das Signatur-Menü wachsen aus
  ihrer Knopfposition, Kacheln staggern hinein; Kachel-Hover hebt an.
- **Lebendiges Dokument:** Seitenwechsel scrollen weich statt zu springen; das
  Scharfstellen nach dem Zoom crossfaded statt hart zu tauschen; platzierte
  Signaturen poppen, gelöschte verblassen; Thumbnails und Dokumentseiten
  staggern beim Öffnen ein; Thumbnails heben sich beim Hover; Treffer zählen
  und pulsieren; der Copy-Chip poppt.
- **Signature Moments:** der aktive Werkzeughintergrund **gleitet als Pill**
  zwischen Auswahl/Text/Löschen; nach erfolgreichem Speichern **stempelt** ein
  Häkchen auf den Speichern-Knopf; Hell/Dunkel wechselt als **wachsender Kreis**
  vom Theme-Knopf aus (View Transitions API, Feature-Detect); Statusmeldungen
  mit Erfolgshäkchen; Löschen-ausführen slidet in die Fußleiste; Rückgängig-
  Icon dreht kurz rückwärts.
- Konzept: `MOTION-KONZEPT.md` (Tokens, Inventar, Regeln — u. a. nur transform/
  opacity animieren, nichts länger als 500 ms, Reduced Motion respektieren).

## v0.12.10 — Originaltext-Editor: neue Zeilen und Schriftwechsel
- **Umschalt+Enter fügt eine neue Zeile ein** (Enter übernimmt weiterhin sofort).
  Der ersetzte Text wird mehrzeilig als echter Seiteninhalt eingesetzt, Folgezeilen
  rücken entsprechend tiefer; auch Strg+Z stellt mehrzeilig zurück.
- **Schrift änderbar:** Die Werkzeugleiste (Familie, Stil, Größe, Farbe) ist mit
  dem Originaltext-Editor verbunden — sie zeigt beim Öffnen die ermittelte Schrift
  der Zeile und übernimmt Änderungen sofort in Vorschau und Ergebnis.
- Server: `/api/text/replace` nimmt optional `size`/`font`/`color` (Übersteuerung
  der Zeilenschrift) und setzt mehrzeiligen Text; Undo berücksichtigt die Zeilen.

## v0.12.9 — Signatur-Upload mit Vorschau und Transparenz-Regler
- **Vorschaudialog beim Hochladen:** Bild gewählt → Dialog mit Titel, Vorschau
  auf **Schachbrettmuster** (wie aus Bildprogrammen bekannt — das Muster zeigt,
  wo der Hintergrund entfernt wurde), Passwortfeld und Schwellwert-Regler.
- **Transparenz einstellbar:** Der Regler (0–255, Standard 232, 0 = aus) steuert,
  ab welcher Helligkeit Weiß durchsichtig wird. Die Vorschau rechnet live und
  immer vom Originalbild neu; der Upload übernimmt exakt den eingestellten Wert.
  Serverseitig nimmt `/api/signature/upload` dafür den Parameter `threshold`.

## v0.12.8 — Symbolleiste schlanker: Signatur-Klickmodus entfällt
- Der Werkzeugknopf „Signatur" (Klick-Platzierung) ist entfernt — Signaturen
  werden ausschließlich per **Drag & Drop aus dem „Signatur…"-Menü** aufs Papier
  gezogen (seit v0.12.5). Die Leiste zeigt jetzt: Auswahl · Text · Löschen.
- Der Signatur-Menü-Knopf behält seine Verwaltungsfunktion (Hochladen,
  Umbenennen, Passwort, Löschen, Vorschau). Kurzhilfe und Tooltip angepasst.

## v0.12.7 — Signatur-Menü: Passwort beim Hochladen & Schloss-Knopf
- **Passwort direkt beim Hochladen:** Nach der Bildauswahl erscheint im Menü
  eine Zeile mit Passwortfeld und „Hochladen" — wer will, verschlüsselt die neue
  Signatur sofort. Das lose Passwortfeld am Menüende ist entfallen.
- **Schloss-Knopf an jeder Kachel** (neben Umbenennen/Löschen): Passwort
  nachträglich setzen, ändern oder – bei leerem Feld – den Schutz entfernen. Der
  Server verschlüsselt die Signatur um bzw. legt sie wieder ungeschützt ab;
  bestehende Platzierungen folgen dem neuen Dateinamen. Gesperrte Kacheln
  führen zunächst zum Entsperren-Dialog.
- Fix: Klicks in den schwebenden Dialogen (Entsperren/Passwort/Umbenennen)
  schlossen das Signatur-Menü im Hintergrund und ließen dessen Kacheln veraltet.

## v0.12.6 — Griff der Seitenleiste wandert mit
- Fix: Beim Verschieben der Lesezeichen-Leiste auf die linke Seite blieb der
  Ein-/Ausklapp-Griff fälschlich am rechten Fensterrand (in v0.12.3 war nur der
  Leiste selbst die neue Position zugewiesen worden, nicht dem Griff). Jetzt
  sitzt der Griff immer direkt zwischen Leiste und Dokument.

## v0.12.5 — Signaturen per Drag & Drop aufs Papier ziehen
- **Direkt aus der Liste ziehen:** Kachel im „Signatur…"-Menü anfassen, aufs
  Dokument ziehen, loslassen — die Signatur landet genau an der Stelle (das
  Papier leuchtet beim Darüberziehen auf, danach wie üblich greifen & ziehen).
  Klicken zum Auswählen funktioniert wie bisher.
- **Passwort-Logik verständlich gemacht:** Das Passwortfeld im Menü verschlüsselt
  die als nächstes hochgeladene Signatur (Schloss-Symbol). Gesperrte Kacheln sind
  erst nach dem Entsperren auswählbar und ziehbar; Entsperren gilt bis
  Programmende. Hinweiszeile im Menü erklärt den Ablauf.
- Kurzhilfe aktualisiert.

## v0.12.4 — „Auswahl"-Knopf: Modus verlassen, gesetzten Text verschieben
- Neuer Knopf **„Auswahl" (Mauszeiger-Symbol)** links neben „Signatur": Er kehrt
  aus dem Text-/Löschen-/Signatur-Modus in den normalen Modus zurück (geht
  weiterhin auch mit Esc). Das aktive Werkzeug ist in der Leiste hervorgehoben —
  inklusive „Auswahl" als Startzustand.
- **Nach dem Setzen eines Textes kehrt die App automatisch in den Auswahl-Modus
  zurück** (wie bei Signaturen schon üblich). Der neue Text ist damit sofort
  greifbar und verschiebbar — vorher blieb der Text-Modus aktiv und der
  Verschiebe-Cursor log (Ziehen tat nichts). Wer mehrere Texte hintereinander
  platziert, bleibt durch Klick aufs Papier im Text-Modus.
- Der Vier-Pfeil-Cursor auf Signaturen/Texten erscheint nur noch, wenn sie auch
  wirklich verschiebbar sind (im Text-/Signatur-Modus kein falscher Hinweis).

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
