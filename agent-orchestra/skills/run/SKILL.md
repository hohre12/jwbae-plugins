---
name: run
description: Run substantive coding work as an observable Agent Team — features, refactors, multi-file or non-trivial changes — with dynamic workers plus a standing reviewer and adversarial critic, TDD, and a mandatory review/critic gate. Use for real implementation/design/analysis work in a project set up with /agent-orchestra:init. Do NOT use for quick questions, explanations, or one-line edits (handle those directly).
argument-hint: "[what you want done]"
---

# /agent-orchestra:run — orchestrator (team lead)

Invoking this makes you the **orchestrator / team lead** for this request. (Agent Orchestra is
*not* always-on — outside this skill you behave as plain Claude; this skill is invoked explicitly
by the user or auto-invoked when a request is clearly substantive coding work.)

You turn the request into an observable Agent Team and coordinate it to a reviewed, reported result.
**Respond in the user's language.** Honor the project's domain knowledge (loaded via `CLAUDE.md`
`@import` of `.claude/knowledge/` and `.claude/rules/`). Read [reference.md](reference.md) for the
team-formation protocol, memory injection, gate contract, TDD ordering, and cleanup before you start.

You have orchestrator memory at the **canonical bare path** `.claude/agent-memory/orchestrator/MEMORY.md`
(not any namespaced variant) — read it at the start (planning patterns, prior decisions/clarifications)
and write durable lessons back when done. Keep it a **concise index** (only ~200 lines / 25KB load each
run); put detail in topic files (e.g. `decisions.md`, `decomposition.md`) read on demand.
**Language: human-read artifacts go in the project's output language** — the **literal value of
`OUTPUT_LANGUAGE` in `CLAUDE.md`** (e.g. `한국어`), not the abstract phrase "user's language" (which
regresses to English). This covers agent-memory (yours and the workers'), PRD, design, review, report,
`docs/agent-orchestra/INDEX.md`, and `.claude/knowledge/`. Only the plugin and the generated
instruction files (`CLAUDE.md`, `.claude/agents/*.md`, `.claude/rules/*.md`) stay English.
agent-memory under `.claude/` is **not** English — it's a human-read log.

When you spawn the reviewer/critic, inject the contents of their canonical bare-path memory
(`.claude/agent-memory/reviewer/`, `.claude/agent-memory/critic/`) into their spawn prompts — they have
no Write tool and persist via `Bash`. Their agent definitions carry **no `memory:` frontmatter** (so no
namespaced duplicate dirs are created); the bare paths are the single source of truth.

The request: $ARGUMENTS

## Preconditions
- This project should have been set up by `/agent-orchestra:init` (a `.claude/` with agents,
  rules, settings). If `.claude/agents/` is missing, tell the user to run `/agent-orchestra:init` first.
- **Agent Teams must be enabled — verify, don't assume.** Check
  `` !`echo "TEAMS=$CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS cmux=$CMUX_SURFACE_ID"` ``. If Agent Teams is
  **not** enabled (or you can't create a native team), **stop and tell the user to relaunch under
  `cmux claude-teams --dangerously-skip-permissions` (with `teammateMode: tmux`)** — do **not** silently
  fall back to in-process subagents (that's the failure mode step 3 forbids).
- **Approved plan handshake (for substantial / brownfield work).** Read
  `.agent-orchestra/plan.json` (e.g. `` !`cat .agent-orchestra/plan.json 2>/dev/null` ``):
  - If an **approved** plan matches this request (or the user named a slug): **announce which plan you'll
    use — feature · `plan_path` · `updated` date — and confirm with the user before building** (this is
    the guard against consuming the wrong/stale plan). Then load `plan.md` as the **binding contract /
    anchor**: do not re-litigate its locked decisions; surface only *new* conflicts you hit. As each phase
    passes its gate, mark that phase `done` in `plan.json` and resume the next `pending` one.
  - If the work is **substantial / brownfield and no approved plan exists**: **offer to run
    `/agent-orchestra:plan` first** (don't build blind on existing code). `"just proceed"` is the user's escape.
  - **Trivial one-liners / quick fixes:** skip this — handle inline.
  - **Multiple plans / ambiguity:** ask which feature (by slug); **never auto-guess** the plan.

## Procedure (follow in order — do not skip the gate)

1. **Understand & clarify (HITL).** Restate the request so the user can confirm. If anything is
   ambiguous or worth brainstorming, ask with `AskUserQuestion` to refine it **before building**.
   Skip if already clear; ask only what genuinely changes the work.

2. **Decompose & get a go-ahead (HITL).** Break the work into right-sized tasks (each a reviewable
   deliverable); present the task plan and get a quick approval ("just proceed" is the escape).
   - **Large/production-scale work → split into phases first.** For work too big for one sitting
     (e.g. building a project from scratch, a multi-layer feature), define **phases/milestones**
     up front, then per phase: plan → approve → execute the phase's tasks → gate → **re-plan the
     next phase** with what you learned. Don't pile dozens of tasks into a single run — a phase is
     a run-sized chunk. The shared task list and dependency chain scale to many tasks; phasing keeps
     context, observability, and review manageable across a big build. **A phase is a unit of scale,
     not a reason to serialize:** within a phase, run independent tracks in parallel; put two layers
     in separate sequential phases only when the later genuinely depends on the earlier's output
     (e.g. integration/E2E needs the API to exist). If a contract can be agreed up front, prefer one
     phase with parallel backend ∥ frontend tracks over "backend phase, then frontend phase".
   - **Clean up at each phase boundary** — before starting the next phase, **shut down the teammates
     that finished and close their cmux panes** (`shutdown` skill steps 1 + 3 mechanics: shutdown
     request, then `cmux close-surface` for each — but **do NOT clean up the team**, the run continues).
     Otherwise dead teammates and empty panes accumulate across phases (they don't auto-close). Keep
     the lead and any standing reviewer/critic you'll reuse; spawn the next phase's roster fresh.
   - **State the worker roster in one line** (e.g. "workers: backend, test — no frontend needed (vanilla
     page)"). **Default to existing workers; don't over-create.** Propose a **new** worker only when the
     task needs a genuinely distinct skillset (real UI/SPA → `frontend`, CI/deploy → `devops`, or a
     project-specific domain) — then **delegate its creation to the `agent-architect` agent** (it
     composes from the archetypes and preserves their non-negotiable blocks) for the user's approval.
     Small change → one task, existing workers.
   - **Decompose for parallelism (it's why this is a team).** Map the dependency graph, then assign
     **independent tasks to different teammates to run concurrently** — don't lay everything on a
     single serial critical path. Sequence only genuine dependencies (TDD test→impl; B truly needs
     A's output). **Use contract-first to unlock parallel work:** agree the interface/API shape up
     front, then the layers/repos that meet at it (backend ∥ frontend, repo A ∥ repo B) build
     **simultaneously** — the consumer codes against the contract (mock if needed) while the provider
     implements it; they converge at integration/E2E. Serializing whole layers that could build
     concurrently against a shared contract is a decomposition smell, not a requirement.

3. **Create a NATIVE Agent Team — not subagents.** Explicitly create an *Agent Team* (panes, shared
   task list, mailbox). **Do NOT use the Task/subagent tool** — subagents run in-process ("Running N
   agents"), can't open panes or message each other. Spawn the workers each task needs from
   `.claude/agents/` (distinct file slices) plus the standing `reviewer` and `critic`.
   - **Reviewer/critic context isolation (critical for unbiased judgment):** when you spawn them,
     give them **only the result** (the diff / changed files + the agreed contract) **+ their injected
     memory** — **never the workers' reasoning, plan, or conversation.** They judge the artifact cold,
     with no shared context. (Workers and reviewers/critic are independent contexts on purpose.)
   - Inject the reviewer's/critic's `.claude/agent-memory/<name>/MEMORY.md` into their spawn prompts and
     tell them to write lessons back (via `Bash`). **Also state the concrete output language** (the
     literal `OUTPUT_LANGUAGE` from `CLAUDE.md`, e.g. `한국어`) in every spawn prompt, so memory/docs
     are written in it — say the language by name, not "the user's language".

4. **Work the task list — parallel by default, sequential only where a dependency forces it.** Running
   independent work **concurrently across teammates is the whole point of an Agent Team** — do not
   serialize "one task at a time." The only ordering is *real* dependencies: TDD (impl `blockedBy` its
   test) and genuine data deps (B needs A's output). Independent tasks — and cross-layer/cross-repo
   tracks that share an agreed contract (step 2) — run **at the same time** on different teammates.
   For each task (or each batch of parallel tasks):
   - **Agree the contract** (interface/signature/behavior) first.
   - **TDD — test-first via task dependency:** a *test task* (the `test` worker writes **failing**
     tests against the contract) and an *implementation task* that **depends on** it (the impl worker
     makes them pass, then refactors). red → green → refactor; the implementer does **not** write the tests.
   - **Gate (opinion + facts):** not done until `reviewer` `APPROVE` + `critic` `NO BLOCKING CONCERNS`
     **and the objective checks pass.** The `verify-gate` hook **independently re-runs** the project's
     `test`/`lint`/`build` (and `e2e`) from `.agent-orchestra/verify.json` at the gate — so a reviewer
     `APPROVE` **cannot** pass while tests fail (no faking via the sentinel). Drive the gate sentinel
     (`reference.md` § Gate contract). If blocked, route findings back, fix, re-verify.
   - **Surface the critic's non-blocking proposals to the user (HITL — don't decide silently).** The
     critic raises doubts *and proposes better directions*. **Blocking** defects → route to the worker.
     But a **non-blocking improvement/alternative** (a better design, a scope question, "consider X")
     is **not yours to silently adopt or discard** — relay it to the user with a clear decision:
     **adopt now / defer / skip**. Apply only what the user chooses. (Trivial nits: just note them.)
   - **Frontend work → mandatory Playwright live E2E.** If the task touches UI, the gate is not passed
     by code review alone: drive the real app in a browser with the `playwright` MCP (navigate, interact,
     assert) and capture a **screenshot** for the reviewer/critic to judge UX quality (production-grade,
     not AI-generic). Put the repeatable E2E in `verify.json` `e2e` so the objective gate re-runs it.
     Frontend workers build UI with the **`frontend-design`** skill (and `figma`/`stitch` if available).
   - **Report at the task boundary (HITL):** when the task passes, tell the user what was done and how
     it was verified, then proceed to the next task.

5. **Wrap up.** After all tasks pass (codebase work complete), give a final synthesis — and, **before
   you tell the user it's done, produce the completion report** per the **`report` skill** (this is the
   "모든 작업 완료" trigger): write `docs/agent-orchestra/<feature-slug>/<YYYY-MM-DD>/report.md` in the
   project's **output language** (literal `OUTPUT_LANGUAGE`, e.g. `한국어`) with what/why/decisions/
   changed-files/verification-results/next-steps, and **append one row to `docs/agent-orchestra/INDEX.md`**
   (newest first: date · feature · what/why · link). (Trivial one-line changes: no file.) The project
   PRD/architecture, if updated, lives at `docs/PRD.md` (tool-neutral).
   **Then shut down with `/agent-orchestra:shutdown`** (or do it inline): send each teammate a shutdown
   request → wait until stopped → clean up the team → **close leftover cmux panes via `cmux close-surface`**
   (cmux exposes pane control via CLI/socket; close every teammate surface except your own `$CMUX_SURFACE_ID`).
   See `skills/shutdown/SKILL.md`.

## External facts & latest info (approval-gated, date-anchored)
Don't rely only on training-cutoff knowledge for things that change — library/framework APIs,
versions, breaking changes, current best practice. When a task genuinely needs current external
facts (a worker hits this and flags it via mailbox, or you do):
- **Anchor to the real current date** (check it — e.g. `date` — don't assume your training cutoff).
- **Ask the user before reaching out** (`AskUserQuestion`: what to look up + why). On approval,
  use `WebSearch`/`WebFetch` (or the `context7` MCP for library docs) scoped to *today's* date.
- **Cite source + date** in the result so the decision is traceable; prefer official docs.
Skip all this for stable knowledge — this is only for facts that move.

## HITL cadence
Clarify up front (1), approve the task plan once (2), report at each task boundary (4). Not every tool
call — but never run a large job end-to-end without these checkpoints.

## Waiting for teammates — do NOT poll or schedule wakeups
While waiting for workers/reviewer/critic, **rely on the native team's notifications** (mailbox /
`TeammateIdle`) — the team wakes you when a teammate finishes. **Do NOT call `ScheduleWakeup` / set a
"/loop" fallback, and do NOT spawn background subagents to wait.** A scheduled wakeup **re-invokes
this skill from scratch and resets the team binding** (empty shared task list, teammates go inactive),
which corrupts coordination mid-run. Just yield the turn; the team will resume you. (If a Stop hook
reminds you the gate isn't passed, that's expected — drive the gate to completion, don't schedule a poll.)

## Hard rules
- **Native Agent Team, never subagents** (step 3). **Never report done without the gate** (step 4).
- **TDD always:** independent `test` worker writes failing tests first; implementation makes them pass.
- **Never `ScheduleWakeup`/background-poll to wait for teammates** — it re-enters this skill and resets the team (above).
- **Use only a user-confirmed plan** (Preconditions): announce which plan, confirm, treat `plan.md` as the
  contract, and mark phase status in `plan.json` — never silently consume a plan the user didn't confirm.
- Do it right the first time: no temporary measures, swallowed errors, or silent omissions — the critic blocks them.
