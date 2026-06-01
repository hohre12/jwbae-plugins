# scripts/

Non-standard helper directory (not auto-discovered). Hooks invoke these via
`${CLAUDE_PLUGIN_ROOT}/scripts/...`.

Four enforcement scripts (see `DESIGN.md` §4):
- `guard-dangerous.py` — `PreToolUse` guard that blocks a small set of unambiguously
  destructive actions (and secret `.env` access).
- `team-gate.py` — `TaskCompleted` / `TeammateIdle` gate: while review is pending, a
  non-review teammate can't close a task and the reviewer/critic can't go idle.
- `review-gate.py` — `Stop` backstop: blocks reporting "done" while review is pending.
- `verify-gate.py` — `Stop` objective gate: re-runs the project's real `test`/`lint`/
  `build`/`e2e` from `.agent-orchestra/verify.json` so a sign-off can't pass on red.
