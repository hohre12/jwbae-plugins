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

> **Status: v0.5.0 (v1.4: invoked b+c — not always-on; separated PRD path; cleanup & memory guards).**
> See [`DESIGN.md`](./DESIGN.md) for the full design (§13 the 5 goals, §14 v1.3, §15 v1.4), and
> [`docs/e2e-checklist.md`](./docs/e2e-checklist.md) for the interactive test plan.
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

## Skills (namespaced)

| Command | Purpose |
| --- | --- |
| `/agent-orchestra:init` | Triage the project and scaffold the standard `.claude/` layout (re-runnable) |
| `/agent-orchestra:run` | Orchestrate a task as an observable Agent Team |
| `/agent-orchestra:briefing` | Brief assigned Redmine issues, then start work |
| `/agent-orchestra:teardown` | Shut down the team and close leftover cmux panes (run when a run is done/stuck) |

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
/agent-orchestra:run <your request>   # substantive work → reviewed/critiqued team in panes
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
