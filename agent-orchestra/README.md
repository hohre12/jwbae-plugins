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

> **Status: in development (v0.1.0, skeleton).** See [`DESIGN.md`](./DESIGN.md) for the
> full frozen design and the build plan.

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

## License

MIT
