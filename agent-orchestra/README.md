# Agent Orchestra

**Observable multi-agent orchestration for Claude Code.**

You talk to one orchestrator. It forms a native **Agent Team** — dynamic workers
plus a **standing reviewer** and an **adversarial critic** — and you watch them
collaborate and challenge each other **live in cmux panes**. Every change passes a
review/critic gate before you get the final report.

Agent Orchestra's focus is *visual, conversational team coordination* (Agent Teams +
cmux), distinct from harness-pipeline tools. It also scaffolds the standard `.claude/`
layout so nothing gets forgotten, briefs you on assigned Redmine issues, and works over
Remote Control.

> **Status:** invoked (b+c) — not always-on. Objective gate, `agent-architect` roster design, the
> `plan`↔`run` handshake, run-completion report, and team shutdown are all in. The current version lives
> in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json) (single source of truth — not repeated
> here, to avoid drift). See [`DESIGN.md`](./DESIGN.md) for the full design (§13 the 5 goals, §14–15 the
> invoked model, §16 objective gate / FE live E2E / agent-architect, §17 `/plan`, §18 report + shutdown,
> §19 cold-audit fixes) and [`docs/e2e-checklist.md`](./docs/e2e-checklist.md) for the interactive test plan.
>
> Set up a project with `/agent-orchestra:init` (which proposes its plan and waits for your
> approval). Then run substantive work with **`/agent-orchestra:run <request>`** (or let Claude
> auto-invoke it for clearly substantive coding work) — it runs as a reviewed/critiqued Agent
> Team. It's **not always-on**: quick questions and one-line edits stay plain Claude, so you can
> opt out anytime. Project PRD lives at `docs/PRD.md`; tool artifacts under `docs/agent-orchestra/`;
> domain rules in `.claude/knowledge/` load into every session.

## Why

Single-agent Claude tends to confirm its own work (self-confirmation bias). Agent
Orchestra runs every task as a team where an independent reviewer and an adversarial
critic must sign off — bias correction, enforced by hooks, not by asking nicely.

The gate is **objective, not self-reported**: a Stop hook independently re-runs the
project's `test`/`lint`/`build` (and frontend `e2e`) from `.agent-orchestra/verify.json`,
so a reviewer "APPROVE" can't pass while checks fail. Frontend work additionally requires
**Playwright live-browser E2E + screenshot** (generic AI-looking UI is a finding). Every
substantial run appends to `docs/agent-orchestra/INDEX.md` — an onboarding history a new
joiner can read.

## Standing agents

The plugin ships three standing agents (not copied per project):

| Agent | Role |
| --- | --- |
| `reviewer` (blue) | Independent, cold, result-only production-grade review; runs the tests itself |
| `critic` (red) | Adversarial — doubts the approach and **proposes better directions** (relayed to you) |
| `agent-architect` (purple) | Designs the project's worker roster and writes `.claude/agents/*.md` by **composing from quality-floor archetypes** (preserves their non-negotiable TDD/gate/ownership blocks) — tailored roster, no quality drift |

## Skills (namespaced)

| Command | Purpose |
| --- | --- |
| `/agent-orchestra:init` | Triage the project and scaffold the standard `.claude/` layout (re-runnable) |
| `/agent-orchestra:plan` | Deeply analyze a substantial/brownfield change (read-only, multi-agent) + HITL interview → an approved design agreement (`plan.md`) that `run` implements against |
| `/agent-orchestra:run` | Orchestrate a task as an observable Agent Team (auto-picks up an approved plan) |
| `/agent-orchestra:report` | Summarize the completed work into a Korean/output-language `report.md` (auto on run completion, or on demand) |
| `/agent-orchestra:shutdown` | Shut down the team (shutdown request + clean up the team) and close leftover cmux panes (when a run is done/stuck) |
| `/agent-orchestra:briefing` | Brief assigned Redmine issues, then start work |

## Develop / test locally

```bash
claude --plugin-dir ./agent-orchestra      # load without installing
/reload-plugins                            # pick up edits
claude plugin validate                     # run before publishing
```

## Install

```bash
/plugin marketplace add hohre12/jwbae-plugins
/plugin install agent-orchestra@jwbae-plugins
```

## Daily use

Prerequisites: the [cmux](https://cmux.com) app, and Claude Code with Agent Teams. Add this
alias to your shell (`cmux claude-teams` launches Claude with teams + cmux panes and forwards
flags — see [`docs/cmux-setup.md`](./docs/cmux-setup.md)):

```sh
alias cgo="cmux claude-teams --dangerously-skip-permissions"
```

Then:

```sh
cmux
cd ~/your-project
cgo
/agent-orchestra:init                 # once per project (re-runnable); proposes plan, waits for approval
# relaunch so the teams env applies, then:
/agent-orchestra:plan <feature>       # substantial/brownfield: analyze + agree a plan first (read-only)
/agent-orchestra:run <your request>   # substantive work → reviewed/critiqued team in panes (auto-picks the plan)
# quick questions / one-line edits: just ask — Orchestra is not always-on
/agent-orchestra:briefing             # (optional) start from assigned Redmine issues
```

## Docs

- [`DESIGN.md`](./DESIGN.md) — full design, decisions, enforcement layer
- [`docs/cmux-setup.md`](./docs/cmux-setup.md) — cmux launcher, alias, verification
- [`docs/v2-seams.md`](./docs/v2-seams.md) — heterogeneous critic + server-diagnosis seams
- [`docs/e2e-checklist.md`](./docs/e2e-checklist.md) — interactive test plan

## License

MIT
