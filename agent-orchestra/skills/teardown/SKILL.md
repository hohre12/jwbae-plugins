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

1. **Shut down every teammate** — send each teammate the native graceful **shutdown request** (let
   it finish and stop cleanly; do **not** kill its pane to stop it) and **wait until they have
   actually stopped** (don't proceed while any is still running). Use the team config
   (`~/.claude/teams/{team}/config.json` → `members`) to know who's active.

2. **Delete the team** — call **`TeamDelete`** (the native team cleanup). It removes the shared team
   resources (`~/.claude/teams/{team}/`, `~/.claude/tasks/{team}/`) and **fails if any teammate is
   still running**, so step 1 must be complete first.

3. **Close the leftover cmux panes** — under `cmux claude-teams`, each teammate had its own cmux
   surface. Close them with the cmux CLI:
   - Identify your **own** surface from `$CMUX_SURFACE_ID` (env) — **do not close your own pane.**
   - Enumerate the workspace's surfaces (cmux CLI / socket at `$CMUX_SOCKET_PATH`) and
     `cmux close-surface --surface <id>` for each **teammate** surface (everything except yours).
   - If surface enumeration isn't available, close the surfaces you can identify as teammates'
     (their pane titles are the teammate/agent names, e.g. `agent-orchestra:reviewer`).

4. **Clear the gate sentinel (terminal)** — **remove** `.agent-orchestra/state/gate.json` and
   `.agent-orchestra/state/verified.json`. The run is over, so the gate should be *gone*, not left
   at `approved`: a lingering `approved` makes the objective `verify-gate` hook re-run the whole
   test/lint/build/e2e suite on **every** later Stop (even normal chat). Removing the file is the
   terminal state — no hook fires until the next run creates a fresh gate.

5. **Report** what was shut down, cleaned, and closed; note anything that couldn't be closed
   automatically so the user can close it by hand.

## Phase-boundary cleanup (partial)
Between phases of a long run (not the end), do **steps 1 + 3 only** for the teammates that finished —
graceful shutdown + `cmux close-surface` — and **skip step 2 (`TeamDelete`)** and step 4 (gate reset),
since the run continues. This stops dead teammates and empty panes from accumulating across phases.

## Safety
- Never close a pane whose teammate is still working — wait for shutdown first.
- Never close `$CMUX_SURFACE_ID` (the lead's own pane).
- Only the **lead** runs cleanup (teammates running cleanup can leave resources inconsistent).
