# Antigravity Agent Guidelines

Please refer to [`AGENTS.md`](./AGENTS.md) for full project rules, architecture, and instructions.

### Core Rules for this Project:
1. **Context Restoration**: Always read [`SESSION_STATE.md`](./SESSION_STATE.md) first to resume work immediately.
2. **Token Efficiency**: Never view the full 3700 lines of `src/scoring.py`. Check [`docs/CODE_MAP.md`](./docs/CODE_MAP.md) for exact line ranges.
3. **NoFocus Invariant**: All interactive PyQt6 buttons must have `.setFocusPolicy(Qt.FocusPolicy.NoFocus)` so global shortcuts work.
4. **Automated Testing**: Use `python3 tests/run_tests.py` to verify changes in <0.3s.
5. **No `cd`**: Never run `cd` in bash tool commands.
