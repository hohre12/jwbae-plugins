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

You have orchestrator memory at `.claude/agent-memory/orchestrator/MEMORY.md` — read it at the start
(planning patterns, prior decisions/clarifications) and write durable lessons back when done.

The request: $ARGUMENTS

## Preconditions
- This project should have been set up by `/agent-orchestra:init` (a `.claude/` with agents,
  rules, settings). If `.claude/agents/` is missing, tell the user to run `/agent-orchestra:init` first.
- Agent Teams must be enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) and you should be
  running under `cmux claude-teams` with `teammateMode: tmux` so teammates open in cmux panes.

## Procedure (follow in order — do not skip the gate)

1. **Understand & clarify (HITL).** Restate the request so the user can confirm. If anything is
   ambiguous or worth brainstorming, ask with `AskUserQuestion` to refine it **before building**.
   Skip if already clear; ask only what genuinely changes the work.

2. **Decompose & get a go-ahead (HITL).** Break the work into right-sized tasks (each a reviewable
   deliverable); present the task plan and get a quick approval ("just proceed" is the escape).
   Light reconcile against `CLAUDE.md`; propose any roster/stage change for approval. Small change → one task.

3. **Create a NATIVE Agent Team — not subagents.** Explicitly create an *Agent Team* (panes, shared
   task list, mailbox). **Do NOT use the Task/subagent tool** — subagents run in-process ("Running N
   agents"), can't open panes or message each other. Spawn the workers each task needs from
   `.claude/agents/` (distinct file slices) plus the standing `reviewer` and `critic`. Inject the
   reviewer's/critic's `.claude/agent-memory/<name>/MEMORY.md` into their spawn prompts and tell them
   to write lessons back.

4. **Per-task loop (one task at a time).** Work the shared task list. For each task:
   - **Agree the contract** (interface/signature/behavior) first.
   - **TDD — test-first via task dependency:** a *test task* (the `test` worker writes **failing**
     tests against the contract) and an *implementation task* that **depends on** it (the impl worker
     makes them pass, then refactors). red → green → refactor; the implementer does **not** write the tests.
   - **Gate:** not done until `reviewer` `APPROVE` and `critic` `NO BLOCKING CONCERNS`. Drive the gate
     sentinel (`reference.md` § Gate contract); hooks enforce it. If blocked, route findings back, fix, re-verify.
   - **Report at the task boundary (HITL):** when the task passes, tell the user what was done and how
     it was verified, then proceed to the next task.

5. **Wrap up.** After all tasks pass, give a final synthesis and (for substantial work) save the run
   report at `docs/agent-orchestra/<feature-slug>/<YYYY-MM-DD>/report.md` (small changes: no file).
   The project PRD/architecture, if updated, lives at `docs/PRD.md` (tool-neutral). Then clean up the team.

## HITL cadence
Clarify up front (1), approve the task plan once (2), report at each task boundary (4). Not every tool
call — but never run a large job end-to-end without these checkpoints.

## Hard rules
- **Native Agent Team, never subagents** (step 3). **Never report done without the gate** (step 4).
- **TDD always:** independent `test` worker writes failing tests first; implementation makes them pass.
- Do it right the first time: no temporary measures, swallowed errors, or silent omissions — the critic blocks them.
