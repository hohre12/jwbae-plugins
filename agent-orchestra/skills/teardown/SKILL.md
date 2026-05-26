---
name: teardown
description: Cleanly shut down the current Agent Team and close its leftover cmux panes. Use when a run is finished (or stuck) and teammates' panes are still open. Run from the team lead session.
disable-model-invocation: true
---

# /agent-orchestra:teardown — shut down the team & close panes

Agent Teams shutdown is slow and cmux does not auto-close empty teammate panes. This skill does
the full teardown in the right order. **Run it from the lead session, only when the work is done**
(closing a pane with a still-running teammate loses its state).

## Steps

1. **Shut down every teammate** — ask each teammate to shut down gracefully, and **wait until they
   have actually stopped** (don't proceed while any is still running). Use the team config
   (`~/.claude/teams/{team}/config.json` → `members`) to know who's active.

2. **Clean up the team** — run the native cleanup ("clean up the team"). It removes the shared
   team resources (`~/.claude/teams/{team}/`, `~/.claude/tasks/{team}/`). It will fail if a teammate
   is still running, so step 1 must be complete first.

3. **Close the leftover cmux panes** — under `cmux claude-teams`, each teammate had its own cmux
   surface. Close them with the cmux CLI:
   - Identify your **own** surface from `$CMUX_SURFACE_ID` (env) — **do not close your own pane.**
   - Enumerate the workspace's surfaces (cmux CLI / socket at `$CMUX_SOCKET_PATH`) and
     `cmux close-surface --surface <id>` for each **teammate** surface (everything except yours).
   - If surface enumeration isn't available, close the surfaces you can identify as teammates'
     (their pane titles are the teammate/agent names, e.g. `agent-orchestra:reviewer`).

4. **Reset the gate sentinel** — set `.agent-orchestra/state/gate.json` to `approved` (or remove it),
   so a stale `review-pending` doesn't block the next turn.

5. **Report** what was shut down, cleaned, and closed; note anything that couldn't be closed
   automatically so the user can close it by hand.

## Safety
- Never close a pane whose teammate is still working — wait for shutdown first.
- Never close `$CMUX_SURFACE_ID` (the lead's own pane).
- Only the **lead** runs cleanup (teammates running cleanup can leave resources inconsistent).
