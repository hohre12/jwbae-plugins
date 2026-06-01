# cmux setup — watch the team in panes

Agent Orchestra is meant to be watched: workers, reviewer, and critic collaborate in
**cmux split panes** while you observe and steer. This is what makes the multi-agent
work *observable* (and what plain harness pipelines don't give you).

## How it works

`cmux claude-teams` is a **launcher** (verified against cmux docs, 2026-05). It:

1. sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`,
2. defaults `--teammate-mode auto`,
3. injects a tmux-like environment (`TMUX`, `TMUX_PANE`, `TERM=screen-256color`),
4. prepends a **private tmux shim** to `PATH` that translates Claude Code's tmux pane
   commands (`new-window`, `split-window`, `send-keys`, `capture-pane`, …) into cmux's
   native workspace/surface RPC, and
5. **forwards all following arguments to `claude`** and launches it.

Because Claude Code thinks it's inside tmux (auto mode → split panes) but the shim routes
to cmux, teammates open as **native cmux panes** even though Agent Teams doesn't natively
support Ghostty/cmux.

## Daily entry — one alias

Since `cmux claude-teams` launches `claude` itself and forwards flags, wrap it in your
existing `cgo` alias (in `~/.zshrc`):

```sh
alias cgo="cmux claude-teams --dangerously-skip-permissions"
```

Then your everyday flow is just:

```sh
cmux                       # the cmux app
cd ~/path/to/project
cgo                        # launches Claude Code with teams + cmux panes + bypass
/agent-orchestra:run <your request>
```

Notes:
- The shim is **per-launch** (the launcher sets it up each session) — no permanent PATH
  install needed. Always entering via `cgo` is enough.
- `teammateMode` in `.claude/settings.json` accepts `"auto"` (default — split panes in tmux/iTerm2,
  in-process otherwise), `"tmux"` (force split-pane), or `"in-process"`. The launcher already injects a
  TMUX-like env so `"auto"` yields cmux panes; `init` writes `"tmux"` as belt-and-suspenders. **Not
  required** under `cgo`; harmless to leave for non-cmux runs.
- All `claude` flags work through it, e.g. `cmux claude-teams --resume`.

## Verification checklist (run interactively once)

These can't be checked headless — verify the first time you use it:

- [ ] `cgo` launches Claude Code and `/agent-orchestra:run` forms a team.
- [ ] Teammates appear as **separate cmux panes** (reviewer pane shows blue, critic red).
- [ ] You can click into a teammate pane and message it directly.
- [ ] Closing/restarting cmux loses live panes (expected) — but `agent-memory/*/MEMORY.md`
      survives in the repo, so continuity is intact on relaunch.
- [ ] Confirm your installed cmux version supports `claude-teams` (update cmux if the
      subcommand is missing).

## Reference
- cmux: https://cmux.com/docs/agent-integrations/claude-code-teams
- cmux blog: https://cmux.com/blog/cmux-claude-teams
- Agent Teams: https://code.claude.com/docs/en/agent-teams
