# 🧭 Session State & Continuation Hub

> **Agent Instruction:** Read this file at the start of any new session or task to instantly understand the current state, active tasks, and context without spending tokens reading git history or multiple large files. Update this file at the end of your session with your latest progress.

---

## 📌 Snapshot
- **Last Updated:** 2026-09-27
- **Git Commit:** Pending (`Fix 3D Formation view, align with Rhythm XP Continuity Booklet, and overhaul layout`)
- **Active Branch:** `main`
- **Working Tree:** Clean / Ready to commit
- **Test Status:** ✅ 7/7 Test suites passing in 0.48s (`python3 tests/run_tests.py`)

---

## 🚀 Recent Accomplishments
1. **FAI Block Splitting:** Blöcke 1–22 werden in `expand_draw_to_points_sequence` als 2 getrennte Wertungspunkte (`-1` und `-2`) geführt. Zyklen rotieren korrekt durch alle Punkte.
2. **Timing Math & Error Detection:** Exakte Berechnung von Hold Time und Transition Time. Negative Eingabefehler werden mit `⚠️` in Rot in der Tabelle hervorgehoben (nicht mehr mit `max(0, ...)` kaschiert).
3. **Point Selection Mode:** Klick auf Timeline oder Tabelle schaltet Punkt in Bearbeitungsmodus; `F` setzt Fertig-Zeit, `K` setzt Key-Zeit, `S`/`B` schaltet Status um, `Esc` bricht ab. In-Cell-Editing & Kontextmenü aktiv.
4. **Draw Update on Debriefs:** Button `🔄 Draw anwenden` passt Formationen aller Punkte an neues Draw an, während Zeiten, Keys und Notizen unberührt bleiben.
5. **Project Restructuring:**
   - Python-Code: `src/` (`scoring.py`, `formation_tool.py`, `formation_db.py`, `card_manager.py`, `draw_generator.py`, `training_db.py`, `draw_dialog.py`).
   - Launcher: `run.py` im Projekt-Root.
   - Docs & PDFs: `docs/`, `docs/pdf/`.
   - Debriefs: Lokaler Ordner `debriefs/` (vom Git-Repo per `.gitignore` ausgeschlossen).
   - Fast Headless Test Runner: `tests/run_tests.py` (<0.6s Laufzeit, 7 Suiten).
6. **Extended Features 1–6 (Draw Generator, Training DB & Rhythm XP Cards):**
   - **Rhythm XP Card Extraction (`src/card_manager.py`):** 16 Randoms (A–Q) und 22 Blöcke (1–22 jeweils `-1` und `-2`) verlustfrei aus Rhythm XP PDFs extrahiert und in `assets/cards/` abgelegt.
   - **Training Database (`src/training_db.py`):** Indiziert alle Debriefs, aggregiert Sprunganzahl, Scores, Busts, Erfolgsquote (%), Hold Times und Transition Times je Formation. Liefert `least_trained` Formationen.
   - **FAI AAA Draw Generator (`src/draw_generator.py`):** Generiert 1–20 Runden strikt nach FAI AAA Regeln (5–6 Punkte/Runde, Blöcke 2 Pkt, Randoms 1 Pkt, Erschöpfung des Pools vor Wiederholung). Bietet Modus `least_trained` mit Priorisierung selten trainierter Formationen.
   - **Draw & Training GUI Dialog (`src/draw_dialog.py`):** 3-Tab Interface mit interaktivem FAI AAA Generator inklusive horizontaler Rhythm XP Kartenvorschau und "Apply to Debrief", Trainingsstatistik-Tabelle mit Farbhervorhebung und Dive-Pool-Katalog.
   - **GUI Integration (`src/scoring.py`):** Generator-Button im Header, Rhythm XP Bildkarten in Sequenzleiste (Klick & Rechtsklick) und Punktetabellen-Kontextmenü, automatische Session-Registrierung in der Training-DB.
7. **Fixes 3, 4 & 5 (3D Formation Visualizer, Continuity Booklet Alignment & Layout Overhaul):**
   - **Fix 3 (Opening Error):** `AttributeError: combo_formation` beim Öffnen oder Wechseln von Formationen aus dem Debriefing-Tool behoben. `select_formation(code, part)` in `FormationExplorerWindow` implementiert, C++ Widget-Liveness geprüft und nahtloses Umschalten sichergestellt.
   - **Fix 4 (Continuity Booklet Alignment):**
     - SDC Rhythm XP Farbstandard korrigiert: Point = Rot (`#EF4444`), Outside Center = Grün (`#10B981`), Inside Center = Blau (`#3B82F6`), Tail = Gelb (`#EAB308`).
     - Block 2 und Block 12 Drehungen, Achsen, Flugfiguren und Keyer mit dem Continuity Booklet synchronisiert.
     - Alle 28 offiziellen Diagrammstreifen (inkl. Flat/Vertikal-Varianten für Blöcke 6, 11, 13, 18, 21, 22) verlustfrei nach `assets/cards/continuity/` extrahiert.
   - **Fix 5 (UI Layout & Readability):**
     - Rechte Seite in 6 kompakte Tabs aufgeteilt (`📖 Continuity`, `📋 Übersicht`, `🔴 Point`, `🟢 OC`, `🔵 IC`, `🟡 Tail`).
     - Offiziellen Rhythm XP Diagrammstreifen scrollbar in Tab 0 eingebettet.
     - Detail-Ansichten mit aufgeräumten Info-Karten für Key-Mechanik, Coach-Tipps, Bust-Gefahren und 5-Schritte-Debriefing-Checkliste versehen.
     - 3D-Kamera-Zoom verdoppelt (2.2x) für optimale Erkennbarkeit der Flyer und Grips, farbige High-Contrast Pill-Badges hinter den Slot-Namen.
     - Filter-Buttons links auf ein aufgeräumtes 2x2 Raster umgestellt (`Alle`, `Randoms`, `Blocks`, `Vertikal`), kein Abschneiden mehr.
8. **Piece-Based Kinematics Engine & Volumetric 3D Shading (Option A):**
   - **Kinematics Engine (`PieceKinematics`, `interpolate_piece_kinematics`):** Ersetzt die fehlerhafte lineare `lerp`-Interpolation durch polare orbitale Rotationsmechanik. Drehungen über 360°, 540° und 180° rotieren Subgruppen/Pieces exakt um ihren Drehpunkt. Flyer durchdringen sich nicht mehr und halten ihren Partnerabstand auf das Millionstel exakt (`diff = 0.0`).
   - **Volumetrische 3D-Modelle:** Flyer besitzen nun echte 3D-Tiefe mit schattiertem Torso, Fallschirm-Gurtzeug (Charcoal-Rig mit Pin-Flap), 3D-Helm mit radialem Glanzlicht und richtungsweisendem Visier entlang des Blickvektors, Mantis-Beinen mit sichtbaren Außengriffen und Booties sowie Armen mit weißen Handgelenkmanschetten.
   - **Entrümpelung (Decluttering):** Alle riesigen Textboxen und Banner direkt über den Flyern wurden entfernt. Griffe und Figuren sind völlig unverdeckt sichtbar. Subtile 16px Pin-Badges an den Beinen (`P`, `OC`, `IC`, `T`), dezente goldene Keyer-Aura und eine aufgeräumte Statusleiste am unteren Bildrand sorgen für perfekte Übersicht.
   - **Kamera & Shortcuts:** Taste `[V]` schaltet sofort zwischen Draufsicht (Top-Down Coach-View, 2D) und 3D-Perspektive um, `[Leertaste]` pausiert/startet die Animation.

---

## 📋 Pending Tasks & Roadmap
- [x] All items from `todo.md` (Fixes 1–5, Extended Features 1–6) completed and tested.
- 💡 Optional future enhancements:
  - FAI AA / A / Rookie Draw Generator Profile (angepasste Pools).
  - Erweiterter HTML/PDF Debriefing Report mit eingebetteten Rhythm XP Diagrammen.
  - Multi-Kamera Dual-Cam Synchronisation mit interaktivem Frame-Offset Slider.

---

## ⚠️ Critical Architecture Constraints
- **Global Shortcuts:** Alle interaktiven Buttons müssen `setFocusPolicy(Qt.FocusPolicy.NoFocus)` behalten, damit Tastatur-Shortcuts immer über `GlobalShortcutFilter` abgefangen werden.
- **MPV Numeric Locale:** Vor dem MPV-Import muss stets `locale.setlocale(locale.LC_NUMERIC, 'C')` gesetzt sein.
- **Offscreen Tests:** Bei Headless-Tests immer `os.environ['QT_QPA_PLATFORM'] = 'offscreen'` vor Qt-Imports setzen und Tests mit `os._exit(0)` beenden.
- **Token Efficiency:** Vor dem Betrachten von Code in `src/scoring.py` immer `docs/CODE_MAP.md` konsultieren, um gezielte Zeilenausschnitte abzurufen.

---

## ⚡ Fast Command Reference
```bash
# 1. Automated Tests (<0.3s)
python3 tests/run_tests.py

# 2. Start Main Scoring Tool
python3 run.py

# 3. Start 3D Formation Explorer
python3 run.py --3d
```
