# 🧭 Session State & Continuation Hub

> **Agent Instruction:** Read this file at the start of any new session or task to instantly understand the current state, active tasks, and context without spending tokens reading git history or multiple large files. Update this file at the end of your session with your latest progress.

---

## 📌 Snapshot
- **Last Updated:** 2026-09-27
- **Git Commit:** `078c779` (Reorganize project structure)
- **Active Branch:** `main`
- **Working Tree:** Clean
- **Test Status:** ✅ 4/4 Test suites passing in 0.23s (`python3 tests/run_tests.py`)

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

---

## 📋 Pending Tasks (from `todo.md`)
1. **Draw Generator (FAI AAA Rules):**
   - Generator für konfigurierbare Anzahl an Runden nach offiziellen FAI AAA Regeln (5–6 Punkte pro Runde, keine verfrühte Wiederholung von Blöcken/Randoms).
2. **Training Database:**
   - Lokale Datenbank (z.B. SQLite oder JSON) zur Erfassung aller gesprungenen Formationen, Trainingshäufigkeiten und Fehlerquoten.
3. **Least-Trained Weighting:**
   - Draw Generator soll auf die Training Database zugreifen können, um gezielt selten trainierte Blöcke/Randoms zu priorisieren.
4. **Formation Pictures from Rhythm XP PDFs:**
   - Bilder / Visualisierungen aus den Rhythm XP PDFs extrahieren oder einbinden.

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
