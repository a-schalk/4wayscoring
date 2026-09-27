# 🧭 Session State & Continuation Hub

> **Agent Instruction:** Read this file at the start of any new session or task to instantly understand the current state, active tasks, and context without spending tokens reading git history or multiple large files. Update this file at the end of your session with your latest progress.

---

## 📌 Snapshot
- **Last Updated:** 2026-09-27
- **Git Commit:** `0c25f7e` (Implement FAI AAA draw generator, training database, and Rhythm XP visual cards)
- **Active Branch:** `main`
- **Working Tree:** Clean
- **Test Status:** ✅ 6/6 Test suites passing in 0.44s (`python3 tests/run_tests.py`)

---

## 🚀 Recent Accomplishments
1. **FAI Block Splitting:** Blöcke 1–22 werden in `expand_draw_to_points_sequence` als 2 getrennte Wertungspunkte (`-1` und `-2`) geführt. Zyklen rotieren korrekt durch alle Punkte.
2. **Timing Math & Error Detection:** Exakte Berechnung von Hold Time und Transition Time. Negative Eingabefehler werden mit `⚠️` in Rot in der Tabelle hervorgehoben (nicht mehr mit `max(0, ...)` kaschiert).
3. **Point Selection Mode:** Klick auf Timeline oder Tabelle schaltet Punkt in Bearbeitungsmodus; `F` setzt Fertig-Zeit, `K` setzt Key-Zeit, `S`/`B` schaltet Status um, `Esc` bricht ab. In-Cell-Editing & Kontextmenü aktiv.
4. **Draw Update on Debriefs:** Button `🔄 Draw anwenden` passt Formationen aller Punkte an neues Draw an, während Zeiten, Keys und Notizen unberührt bleiben.
5. **Project Restructuring:**
   - Python-Code: `src/` (`scoring.py`, `formation_tool.py`, `formation_db.py`, `__init__.py`).
   - Launcher: `run.py` im Projekt-Root.
   - Docs & PDFs: `docs/`, `docs/pdf/`.
   - Debriefs: Lokaler Ordner `debriefs/` (vom Git-Repo per `.gitignore` ausgeschlossen).
   - Fast Headless Test Runner: `tests/run_tests.py` (<0.3s Laufzeit).
6. **Extended Features 3, 4, 5 & 6 (Draw Generator, Training DB & Rhythm XP Cards):**
   - **Rhythm XP Card Extraction (`src/card_manager.py`):** 16 Randoms (A–Q) und 22 Blöcke (1–22 jeweils `-1` und `-2`) verlustfrei aus Rhythm XP PDFs extrahiert und in `assets/cards/` abgelegt.
   - **Training Database (`src/training_db.py`):** Indiziert alle Debriefs, aggregiert Sprunganzahl, Scores, Busts, Erfolgsquote (%), Hold Times und Transition Times je Formation. Liefert `least_trained` Formationen.
   - **FAI AAA Draw Generator (`src/draw_generator.py`):** Generiert 1–20 Runden strikt nach FAI AAA Regeln (5–6 Punkte/Runde, Blöcke 2 Pkt, Randoms 1 Pkt, Erschöpfung des Pools vor Wiederholung). Bietet Modus `least_trained` mit Priorisierung selten trainierter Formationen.
   - **Draw & Training GUI Dialog (`src/draw_dialog.py`):** 3-Tab Interface mit interaktivem FAI AAA Generator inklusive horizontaler Rhythm XP Kartenvorschau und "Apply to Debrief", Trainingsstatistik-Tabelle mit Farbhervorhebung und Dive-Pool-Katalog.
   - **GUI Integration (`src/scoring.py`):** Generator-Button im Header, Rhythm XP Bildkarten in Sequenzleiste (Klick & Rechtsklick) und Punktetabellen-Kontextmenü, automatische Session-Registrierung in der Training-DB.

---

## 📋 Pending Tasks & Roadmap
- [x] All items from `todo.md` (Fixes 1–2, Extended Features 1–6) completed and tested.
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
