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

1. **Reconcile (light).** Compare the current repo against the maturity/roster in `CLAUDE.md`.
   If the project has clearly moved stages or needs different workers, **propose** the change
   and let the user approve (don't auto-apply); for a full reconcile, suggest `/agent-orchestra:init`.

2. **Create a NATIVE Agent Team — mandatory, step one of every run.** Explicitly create an
   *Agent Team* (the native mechanism with panes, a shared task list, and a mailbox). **Do NOT
   delegate this with the Task/subagent tool** — subagents run in-process (shown as "Running N
   agents"), can't open panes, and can't message each other. Use Agent Teams so teammates
   collaborate. Then:
   - Spawn the **workers** this request needs, from the project's `.claude/agents/` (archetype
     instances). Give each a distinct slice of files so they don't collide.
   - Spawn the **standing reviewer** (`reviewer` agent) and **adversarial critic** (`critic` agent)
     as teammates. **Before spawning each, inject their memory** (step 3).
   - Break the work into right-sized tasks on the shared task list. Assign or let teammates self-claim.

3. **Inject standing-agent memory (do this at spawn time).**
   - Read `.claude/agent-memory/reviewer/MEMORY.md` and include its content in the reviewer's
     spawn prompt. Do the same with `.claude/agent-memory/critic/MEMORY.md` for the critic.
   - Instruct each, in the spawn prompt, to **write durable lessons back** to its own
     `MEMORY.md` when its work is done.
   - (This is deterministic and does not depend on native teammate-memory behavior.)

4. **Run the team, observably.** Let workers implement and the reviewer/critic challenge them
   via the mailbox — the user watches this in cmux panes and may click in to steer. Keep
   teammates working until their tasks are genuinely complete; don't implement their tasks yourself.

5. **The gate — never skipped.** Work is **not done** until the reviewer returns `APPROVE`
   (no blockers/majors) **and** the critic returns `NO BLOCKING CONCERNS`. Track this with the
   gate sentinel (see `reference.md` § Gate contract): set it to `review-pending` once workers
   finish, and to `approved` only after both sign off. If either blocks, route findings back to
   the responsible worker, have them fix and re-verify, and re-run the gate.

6. **Report.** Only after the gate is `approved`, give the user a synthesis: what was done,
   what the reviewer and critic flagged and how it was resolved, and how it was verified.
   Clean up the team when finished.

## Hard rules
- **Always form a team** (step 2) — single-agent self-review is exactly the bias this exists to break.
- **Never report done without the gate** (step 5). The Stop hook backstops this via the sentinel.
- Do it right the first time: no temporary measures, no swallowed errors, no silent omissions.
  The critic will block them; don't let them through.
