# 🤖 AGENTS.md — Agentic Development Guide & Instructions

Welcome! This repository contains the **FAI 4-Way Formation Skydiving Debriefing & Scoring System**, an application built with Python 3.10+, PyQt6, libmpv, and ffmpeg.

Follow the instructions below to maximize execution speed, maintain code stability, and conserve context tokens.

---

## ⚡ 1. Session Start Protocol (Immediate Context Restoration)

Whenever starting a session, task, or subagent:
1. **Read [`SESSION_STATE.md`](./SESSION_STATE.md) first:**  
   It contains the latest snapshot, git status, completed milestones, pending roadmap items, and recent architectural decisions in under 70 lines.
2. **Consult [`docs/CODE_MAP.md`](./docs/CODE_MAP.md):**  
   `src/scoring.py` is ~3700 lines long. **DO NOT load the entire file into context.** Use `docs/CODE_MAP.md` to identify exact line ranges before calling `view_file`.
3. **Verify system health:**  
   Run `python3 tests/run_tests.py` to ensure all existing functionality is intact (executes offscreen in <0.3s).

---

## 🛑 2. Golden Rules & Architectural Invariants

- **Global Keyboard Shortcuts (`GlobalShortcutFilter`):**  
  Every clickable button and interactive control must use `.setFocusPolicy(Qt.FocusPolicy.NoFocus)`. If focus is stolen by a button, global video and scoring shortcuts (`Space`, `F`, `K`, `S`, `B`, `T`, `Left/Right`) will stop firing.
- **Text Editing Safety:**  
  `GlobalShortcutFilter` intentionally passes keypresses through when typing in `QLineEdit`, `QTextEdit`, or active table item cells. Pressing `Escape` or `Enter` unfocuses and re-enables shortcuts.
- **`libmpv` Numeric Locale:**  
  Always execute `locale.setlocale(locale.LC_NUMERIC, 'C')` before importing `mpv`. Failure to do so causes float parsing errors in non-English system locales.
- **Headless & Offscreen Testing:**  
  Always set `os.environ["QT_QPA_PLATFORM"] = "offscreen"` before importing PyQt6 in test scripts. Use `os._exit(0)` on teardown to prevent libmpv C-level cleanup aborts.
- **Data Privacy & Git Hygiene:**  
  User video sessions and export reports belong in `debriefs/` and are excluded from Git via `.gitignore`. Never track or commit `*_debrief.json` or `*_report.md`.
- **Command Execution:**  
  Never use `cd` commands in shell execution. Use the `Cwd` parameter.

---

## 📉 3. Token Reduction Strategies for Agents

To conserve tokens and reduce latency:
1. **Targeted File Viewing:**  
   Always specify `StartLine` and `EndLine` when viewing `src/scoring.py` or `src/formation_tool.py`. Look up target ranges in `docs/CODE_MAP.md`.
2. **Use Pre-Built Tests:**  
   Do not write ad-hoc Python test scripts or print statements in scratch directories. Run `python3 tests/run_tests.py`. If you add new logic, add a test function directly into `tests/run_tests.py`.
3. **Targeted Code Replacements:**  
   Use `replace_file_content` with concise target/replacement chunks rather than replacing huge blocks.
4. **Knowledge Base Lookup:**  
   When working on FAI formations or rules, check `docs/KNOWLEDGE_BASE.md` instead of searching the web or asking the user.

---

## 📂 4. Project Layout

```text
4wayscoring/
├── run.py                      # Central CLI & GUI Launcher (python3 run.py [--3d])
├── src/                        # Production Python Code
│   ├── scoring.py              # Main Application (Debriefing, MPV Player, Trimmer, Scoring)
│   ├── formation_tool.py       # 3D Formation Visualizer & Slot Explorer
│   ├── formation_db.py         # FAI 4-Way Dive Pool Database & Coordinates
│   └── __init__.py
├── tests/                      # Fast Headless Test Suite
│   └── run_tests.py            # Headless runner executing all tests in <0.3s
├── docs/                       # Documentation & Knowledge Base
│   ├── CODE_MAP.md             # Code symbol index & exact line ranges
│   ├── KNOWLEDGE_BASE.md       # FAI Dive Pool & rules reference hub
│   ├── 4way_knowledge_base.md  # In-depth training & mechanics guide
│   ├── 4way.md                 # Architecture notes & roadmap
│   └── pdf/                    # Official FAI and coaching reference manuals
├── assets/                     # Media & Visual assets (4wayCheatSheet.svg)
├── debriefs/                   # Local user sessions (*_debrief.json, gitignored)
├── todo.md                     # Roadmap and user feature requests
├── SESSION_STATE.md            # Active state & continuation checkpoint
└── AGENTS.md                   # This instruction file
```

---

## 🛠️ 5. Fast Command Cheat Sheet

```bash
# Run complete test suite (syntax, dive pool logic, timing math, offscreen GUI)
python3 tests/run_tests.py

# Launch Main Debriefing & Scoring Tool
python3 run.py

# Launch 3D Formation Explorer
python3 run.py --3d

# Launch 3D Formation Explorer with specific formation (e.g. Block 12)
python3 run.py --3d 12

# Check syntax without running
python3 -m py_compile src/*.py run.py tests/run_tests.py
```

---

## 📝 6. Session End Protocol

Before finishing a turn or delegating to the next agent:
1. Run `python3 tests/run_tests.py` and ensure 100% pass rate.
2. Update [`SESSION_STATE.md`](./SESSION_STATE.md) with:
   - Summary of completed work.
   - Any newly discovered edge cases or decisions.
   - Updated pending tasks.
3. Commit working changes with clear, descriptive commit messages.
