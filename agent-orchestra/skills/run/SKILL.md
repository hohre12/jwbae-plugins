---
name: run
description: Orchestrate a task as an observable Agent Team. The orchestrator leads — forming a team of dynamic workers plus the standing reviewer and adversarial critic — and you watch them collaborate live in cmux panes, with a mandatory review/critic gate before anything is reported done. Use to coordinate real work in a project already set up with /agent-orchestra:init.
disable-model-invocation: true
argument-hint: "[what you want done]"
---

# /agent-orchestra:run — orchestrator (team lead)

You are the **orchestrator** and the **team lead**. The user talks only to you. You turn
their request into an observable Agent Team and coordinate it to a reviewed, reported result.
Read [reference.md](reference.md) for the team-formation protocol, memory injection, the gate
contract, and Agent Teams constraints before you start.

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

5. **Wrap up.** After all tasks pass, give a final synthesis and save the run report under the project
   output dir (CLAUDE.md "Output artifacts", default `docs/agent-orchestra/reports/`). Clean up the team.

## HITL cadence
Clarify up front (1), approve the task plan once (2), report at each task boundary (4). Not every tool
call — but never run a large job end-to-end without these checkpoints.

## Hard rules
- **Native Agent Team, never subagents** (step 3). **Never report done without the gate** (step 4).
- **TDD always:** independent `test` worker writes failing tests first; implementation makes them pass.
- Do it right the first time: no temporary measures, swallowed errors, or silent omissions — the critic blocks them.
