---
trigger: file_edit
path_pattern: ".*"
---

# Agent Token Reduction & Fast Session Resumption

1. **Session Resumption**: Always read `SESSION_STATE.md` at the start of a turn to get instant context without reading git history or transcripts.
2. **File Size Awareness**: `src/scoring.py` is over 3600 lines. Check `docs/CODE_MAP.md` for exact line numbers before calling `view_file`.
3. **Automated Verification**: Run `python3 tests/run_tests.py` instead of creating scratch test scripts.
4. **Session Handoff**: Update `SESSION_STATE.md` before ending a turn with progress and next steps.
