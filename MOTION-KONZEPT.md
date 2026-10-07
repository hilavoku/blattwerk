# PDF-Werkstatt — Motion-Konzept (Entwurf, Stand 2026-10-07)

> Ziel: Die App soll sich lebendig und hochwertig anfühlen — jede Eingabe, jedes
> Fenster, jede Änderung bekommt eine zielgerichtete Bewegung. Grundlage: die
> etablierten Systeme Material 3 Motion, Fluent 2 (Windows-Anmutung passt zu
> WebView2), die View Transitions API und die Micro-Interaction-Praxis
> (funktional statt dekorativ, kurz, GPU-freundlich, Reduced-Motion-fähig).

---

## 1. Vier Zwecke — jede Bewegung muss einen davon erfüllen

1. **Kausalität**: Meine Aktion hat eine sichtbare Folge (Knopf drückt sich,
   gesetzte Signatur „popt").
2. **Orientierung**: Woher kam etwas, wohin geht es (Panels gleiten aus ihrer
   Seite, Dialoge wachsen aus dem Knopf, der sie öffnete).
3. **Zustand**: Was ändert sich gerade (Speichern-Spinner, Dirty-Punkt pulsiert,
   aktives Werkzeug leuchtet).
4. **Charakter**: Ein bis zwei „Signature Moments" machen Spaß — alles andere
   bleibt dezent (Regel: Movement darf auffallen, darf nicht nerven).

Anti-Regel: Keine rein dekorative Animation, keine Schleifen außer dem
Dirty-Punkt, nichts länger als 500 ms.

---

## 2. Motion-Tokens (CSS-Variablen, eine Quelle der Wahrheit)

```css
:root {
  /* Dauer */
  --d1: 120ms;   /* Mikro: Hover, Press, Farbwechsel          */
  --d2: 180ms;   /* Klein: Dialoge, Menüs, Chips, Icons       */
  --d3: 260ms;   /* Mittel: Panels, Einblendungen, Pop-ins    */
  --d4: 380ms;   /* Groß: Seitenwechsel, Theme, Stagger-Züge  */
  /* Easing (Material-3-Familie + ein Spring für Charakter) */
  --e-standard: cubic-bezier(.2, 0, 0, 1);      /* Alles日常liche */
  --e-in:      cubic-bezier(.3, 0, 1, 1);        /* Austritt (beschleunigt) */
  --e-out:     cubic-bezier(0, 0, 0, 1);        /* Eintritt (abbremsend)   */
  --e-emph:    cubic-bezier(.2, 0, 0, 1);       /* betonte Flächen         */
  --e-pop:     cubic-bezier(.34, 1.56, .64, 1); /* leichtes Überschwingen  */
}
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: .01ms !important; transition-duration: .01ms !important;
      scroll-behavior: auto !important; }
}
```

Merksätze aus den Standards: **accelerate beim Austreten, decelerate beim
Eintritt**; Dauern 100–500 ms; nur `transform`/`opacity` animieren
(GPU-Compositing), Layout-Eigenschaften (width/height) nur wo unvermeidlich
(Panel-Einklappen).

---

## 3. Inventar — jede Interaktion mit ihrer Bewegung

### 3.1 Symbolleiste
| Element | Bewegung | Token |
|---|---|---|
| Alle Knöpfe :hover | Hintergrund-Hellung | --d1 --e-standard |
| Alle Knöpfe :active | scale(0.96) | --d1 --e-standard |
| Modus-Knopf aktiv (Auswahl/Text/Löschen) | Farbwechsel + Pop (1→1.06→1) | --d2 --e-pop |
| Modus-Pill (Stufe 3) | aktiver Hintergrund gleitet zwischen Knöpfen | --d3 --e-standard |
| „Auswahl"-Aktivierung | Icon macht Mini-Nudge nach links | --d2 --e-pop |
| Rückgängig | Icon rotiert kurz rückwärts (−90°→0) | --d2 --e-out |
| Speichern | Erfolg: Häkchen-Badge „stempelt" auf den Knopf (Signature Moment) | --d3 --e-pop + Ring 400 ms |
| Theme-Knopf | Kreis-Reveal vom Knopfpunkt über die ganze UI (View Transitions API) | --d4 |
| Suche | Trefferzähler slidet, Treffer-Highlight pulst einmal | --d2 / 600 ms |

### 3.2 Dialoge (Entsperren, Umbenennen, Passwort, Upload, Löschen-Frage)
| Phase | Bewegung | Token |
|---|---|---|
| Eintritt | opacity 0→1, scale .94→1, translateY(6px)→0; transform-origin an der öffnenden Knopf-Ecke | --d2 --e-out |
| Austritt | opacity→0, scale→.96 | --d1 --e-in |
| Upload-Dialog Vorschau | Schachbrett statisch (seriös); Slider wirkt live (existiert) | — |
| Fehler | kurzes horizontales Shake (2× 4 px) | 240 ms |

### 3.3 Signaturen
| Element | Bewegung | Token |
|---|---|---|
| „Signatur…"-Panel | fade + slide von der Knopfposition; Kacheln staggern (20 ms Versatz) | --d2 --e-out |
| Kachel :hover | translateY(−2px) + Schatten | --d1 |
| Kachel Drag-Start | scale(1.04), Schatten, 2° Neigung („anfassen") | --d2 --e-out |
| Drop auf Papier | Platzierungs-Ring pulst an der Aufsetzstelle (existierendes sigdrop-Leuchten bleibt) | 400 ms |
| Signatur gesetzt | pop-in scale .85→1 mit Overshoot | --d3 --e-pop |
| Signatur löschen | opacity→0 + scale .9, dann entfernen | --d2 --e-in |
| Undo einer Löschung | symmetrisches pop-in | --d3 --e-pop |
| Schloss-Knopf Erfolg | Kachel-Badge wechselt mit Farb-Crossfade | --d2 |

### 3.4 Dokument/Viewer
| Element | Bewegung | Token |
|---|---|---|
| Seitenwechsel (Seite vor/zurück, Eingabe, Lesezeichen, Thumbnail) | weiches Scrollen statt Sprung (`scrollTo smooth`) | --d4 |
| Scharfstellen nach Zoom | scharfes Bild crossfaded über das gestretchte (150 ms) statt hartem Tausch | 150 ms |
| Dokument öffnen | Seiten + Thumbnails staggern ein (translateY 8 px, 30 ms Versatz) | --d3 --e-out |
| Textauswahl-Treffer | „Kopieren (n Zeilen)"-Chip pop-in | --d2 --e-pop |
| Originaltext-Editor | Textfeld fade+scale in, wie Dialoge | --d2 --e-out |
| Neue Text-Annotation | pop-in wie Signatur | --d3 --e-pop |
| Löschen-Modus | Zeilenmarkierung slidet von links ein; „Löschen ausführen" slidet in die Fußleiste | --d2 |

### 3.5 Panels (Lesezeichen/Seitenvorschau)
| Element | Bewegung | Token |
|---|---|---|
| Einklappen | width-Transition (existiert) + Inhalt blendet vorauseilend | --d3 + --d2 |
| Griff-Pfeil | rotiert 180° beim Zustandswechsel | --d2 --e-standard |
| Öffnen | Inhalte staggern | --d3 --e-out |

### 3.6 Status & Zustand
| Element | Bewegung | Token |
|---|---|---|
| Statusmeldung | slide-up + fade; Erfolg mit gezeichnetem Häkchen (SVG stroke-dashoffset) | --d2 / 250 ms |
| Dirty-Dot | sanfter Puls (opacity .6↔1, 1.6 s Loop — einzige Daueranimation) | Loop |
| Formularfeld-Fokus | Umrandung blendet ein | --d1 |
| Spinner „wird verarbeitet…" | rotierender Bogen am Knopf, nicht als blockierendes Modal | Loop |

---

## 4. Signature Moments (das ist der Spaß)

1. **Speichern-Stempel**: Nach erfolgreichem Speichern „stempelt" ein grünes
   Häkchen auf den Speichern-Knopf (scale-in mit Überschwingen + Ring), einmalig
   600 ms. Das Gefühl: erledigt, fest, gut.
2. **Theme-Kreis**: Hell/Dunkel wechselt als wachsender Kreis vom Theme-Knopf
   über die ganze UI (View Transitions API, Feature-Detect, Fallback: Crossfade).
3. **Modus-Pill**: Der aktive Werkzeughintergrund gleitet physisch zwischen
   Auswahl/Text/Löschen statt zu springen.
4. **Anfassen**: Signaturen-Kacheln und -Annotationen neigen sich beim Greifen
   leicht (2°) und heben ab — „Papier-Physik".

---

## 5. Technische Umsetzung

- **Tokens** wie in Abschnitt 2 zentral in `:root`; keine hart codierten
  Dauern/Easings mehr in einzelnen Regeln.
- **Helfer**: CSS-Klassen (`.pop-in`, `.fade-out`) + Mini-JS `animIn(el, name)`
  für remove-after-animation-Elemente; View Transitions mit
  `if (document.startViewTransition)` umschlossen.
- **Performance**: nur `transform`/`opacity`; `will-change` nur während der
  Animation setzen und entfernen; keine Layout-Animationen außer Panel-Breite;
  Endlos-Animationen nur Dirty-Dot.
- **Reduced Motion**: Media-Query (Abschnitt 2) + View-Transitions nur ohne
  Reduced-Motion. Windows-Seitig respektiert das die Systemeinstellung
  „Animationseffekte".
- **Cache**: WebView2 erhält durch den bestehenden `Cache-Control: no-cache`
  Header immer die aktuelle UI — Motion-CSS läuft darüber mit.

## 6. Rollout (jede Stufe einzeln liefer- und testbar)

1. **Stufe 1 — Fundament (v0.13.0)**: Tokens, Reduced-Motion, Knöpfe, Dialoge,
   Signatur-Panel/Kacheln, Statusleiste, Copy-Chip, Dirty-Dot.
2. **Stufe 2 — lebendiges Dokument (v0.13.1)**: weiches Scrollen,
   Scharfstellen-Crossfade, Annotations-Pop/Lösch-Fade, Stagger beim Öffnen,
   Drag-Lift, Treffer-Puls.
3. **Stufe 3 — Signature Moments (v0.13.2)**: Speichern-Stempel, Modus-Pill,
   Theme-Kreis (View Transitions), Löschen-Modus-Bewegungen.

## 7. Testkriterien je Stufe

- Bewegungen wirken ausgelöst, nicht abspielend; nichts dauert > 500 ms.
- Bei aktivem Reduced-Motion (Windows-Setting) bleibt die App voll bedienbar
  und ohne Bewegung.
- E2E-Suite bleibt grün (synthetische Events beachten Transitions — Waits
  anpassen, notfalls Testmodus ohne Transition).
- Kein Layout-Flackern; Zoomen/Scrollen bleibt flüssig (GPU-Compositing).
