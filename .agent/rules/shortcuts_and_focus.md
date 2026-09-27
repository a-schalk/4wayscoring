---
trigger: file_edit
path_pattern: "src/.*\\.py"
---

# UI Focus & Shortcuts Invariant

When modifying or creating Qt widgets (buttons, combos, sliders) in `src/scoring.py` or other UI files:
- Always set `.setFocusPolicy(Qt.FocusPolicy.NoFocus)`.
- If a button steals focus, the user's global keyboard shortcuts (`Space`, `F`, `K`, `S`, `B`, `T`, arrow keys) will stop responding.
- Verify shortcut integrity by running `python3 tests/run_tests.py`.
