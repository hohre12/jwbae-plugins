# E2E checklist

What can be verified automatically vs. what must be checked interactively (Agent Teams +
cmux can't run headless).

## Automated (verified during build)

- [x] `claude plugin validate ./agent-orchestra` passes with no warnings.
- [x] `marketplace.json` is valid JSON and lists `agent-orchestra` (source `./agent-orchestra`).
- [x] `scripts/guard-dangerous.py`: blocks `rm -r -f` (any spelling/order), `git push --force`,
      `git reset --hard`, `git clean -f`, `.env` reads; allows `rm -r`/`rm --force` (single), safe
      commands, and `.env.example`.
- [x] `scripts/review-gate.py`: blocks `review-pending` **and** `approved`-without-recorded-verdicts;
      allows `in-progress`, verdict-complete `approved`, and no-gate.
- [x] `scripts/verify-gate.py`: re-runs `verify.json` checks and blocks on failure; **memoizes on the
      working-tree signature** (skips when code is unchanged, re-runs after any change); per-check timeout
      configurable via `verify.json`.
- [x] `scripts/team-gate.py`: blocks non-review `TaskCompleted` and reviewer/critic `TeammateIdle` while
      `review-pending`; reads the teammate identity defensively (`agent_type` + fallbacks).
- [x] `init` triage shell signals run without fatal error on empty and brownfield repos.

Re-run anytime:
```bash
claude plugin validate ./agent-orchestra
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf x"}}' | python3 agent-orchestra/scripts/guard-dangerous.py; echo $?   # -> 2
```

## Interactive (run once in a real session)

Greenfield walkthrough:

1. [ ] `claude plugin install agent-orchestra@jwbae-plugins` (or `--plugin-dir`); `/help`
       lists `/agent-orchestra:init`, `:plan`, `:run`, `:report`, `:shutdown`, `:briefing`.
2. [ ] In an **empty** project, `cgo` then `/agent-orchestra:init "a small habit tracker"`:
       triage = greenfield → standard interview in plan mode → asks for PRD core + stack +
       key architecture → **does not write code until you approve**.
3. [ ] After approval, `.claude/` is scaffolded: `CLAUDE.md`, `settings.json` (teams env +
       teammateMode), `rules/`, `agents/` (archetype instances),
       `agent-memory/{orchestrator,reviewer,critic,agent-architect}/`,
       `.mcp.json`. No standard slot silently skipped.
4. [ ] Relaunch (`cgo`), then `/agent-orchestra:run <feature>`: a team forms; workers +
       reviewer (blue) + critic (red) appear as **separate cmux panes** and message each other.
5. [ ] Reviewer/critic spawn prompts include their `MEMORY.md`; after work they write lessons back.
6. [ ] You cannot get a "done" report until reviewer `APPROVE` + critic `NO BLOCKING CONCERNS`
       (try to force it — the Stop gate blocks on `review-pending`).
7. [ ] `rm -rf` / `git push --force` attempts by a teammate are blocked by the guard hook.

Brownfield + reconcile:

8. [ ] In an existing repo, `/agent-orchestra:init` triages as in-development/mature, analyzes
       real conventions, and (if a prior harness exists) proposes integration instead of overwriting.
9. [ ] Re-running `/agent-orchestra:run` proposes team/stage changes for approval (never auto-applies).

Redmine + memory continuity:

10. [ ] With a Redmine MCP configured, `/agent-orchestra:briefing` lists your assigned open issues.
11. [ ] Restart cmux mid-work: live panes are lost but `agent-memory/*/MEMORY.md` persists, so
        the reviewer/critic recall the codebase on the next run.

Plan → run → report → shutdown:

12. [ ] `/agent-orchestra:plan <brownfield feature>` spawns explorer(s), interviews you on the real
        decisions, has the **critic challenge the plan**, then (on approval) writes
        `docs/agent-orchestra/<slug>/plan.md` + `plan.json` in **both** the feature folder and
        `.agent-orchestra/`. Read-only — no product code changes.
13. [ ] `/agent-orchestra:run` with an approved plan **announces which plan** and confirms before
        building; marks each phase `done` in both `plan.json` copies as gates pass.
14. [ ] On run completion a `report.md` is written under `docs/agent-orchestra/<slug>/<date>/` in the
        output language, and a row is appended to `INDEX.md`. `/agent-orchestra:report` regenerates on demand.
15. [ ] You cannot reach a clean "done": forcing `approved` without recording reviewer/critic verdicts is
        blocked by `review-gate`, and failing tests are blocked by `verify-gate` (it re-runs them).
16. [ ] `/agent-orchestra:shutdown` sends each teammate a shutdown request, cleans up the team, closes
        leftover cmux panes (except yours), and removes the gate sentinel + finalizes a fully-done plan.
