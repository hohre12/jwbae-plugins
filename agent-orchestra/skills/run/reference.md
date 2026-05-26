# run reference — team protocol, memory injection, gate contract

Detail for `/agent-orchestra:run`.

## Team-formation protocol

- **Use the NATIVE Agent Teams mechanism, never the Task/subagent tool.** Teammates must be real
  Agent Team members (own panes in tmux/iTerm2, shared task list, mailbox) so they collaborate and
  challenge each other. Subagents run in-process ("Running N agents"), can't open panes, and can't
  message each other — if you see that, you used the wrong mechanism.
- You (the session that runs this skill) are the **lead** for the team's lifetime — Agent
  Teams fix the lead and forbid nested teams, so don't try to promote a teammate or have a
  teammate spawn its own team.
- **One team at a time.** If a team is already active, finish/clean it up before forming a new one.
- Spawn teammates by referencing the project's agent types by name (e.g. "spawn a teammate
  using the `backend` agent type", "spawn the `reviewer`", "spawn the `critic`").
- Size the team to the work: typically 3–5 teammates. Give each worker a **distinct set of
  files**; two teammates editing the same file overwrite each other.
- Teammates inherit the lead's permissions. Under `cgo` (bypassPermissions) they run unattended.
- Teammates load `CLAUDE.md` and the project's rules automatically, but **not** your conversation
  history — put task-specific context in each spawn prompt.

## Memory injection (standing reviewer & critic)

reviewer/critic carry **no `memory: project` frontmatter** — memory is managed manually at the
**canonical bare paths** `.claude/agent-memory/{reviewer,critic}/` (no namespaced `agent-orchestra-*`
dirs). You inject and they persist via `Bash`:

1. Before spawning the reviewer: `Read .claude/agent-memory/reviewer/MEMORY.md` (+ its topic files)
   and paste the content into the reviewer's spawn prompt under a "Your accumulated memory" heading.
2. Same for the critic with `.claude/agent-memory/critic/MEMORY.md`.
3. Tell each: when done, **append** durable, distilled lessons via `Bash` to its own `MEMORY.md`/topic
   files at the bare path (they have no Write tool). Keep `MEMORY.md` a concise index. **Write in the
   user's language.**

If a memory file doesn't exist yet, note that and let the agent create it on first write.

## Gate contract (enforced by native team hooks + Stop backstop)

Maintain a sentinel at `.agent-orchestra/state/gate.json` (gitignored). Schema:

```json
{ "request": "<short>", "status": "in-progress | review-pending | approved", "updated": "<iso8601>" }
```

- On forming the team for a work request: write `status: "in-progress"`.
- When workers finish and review begins: set `status: "review-pending"`.
- Only after reviewer returns `APPROVE` **and** critic returns `NO BLOCKING CONCERNS`:
  set `status: "approved"`.
- After reporting and team cleanup: set `approved` (or remove the file).

The sentinel drives three hooks (you don't call them; they run automatically):
- **`TaskCompleted`** — while `review-pending`, a non-review teammate cannot mark a task
  complete (the reviewer/critic completing their own review tasks is allowed).
- **`TeammateIdle`** — while `review-pending`, the reviewer/critic cannot go idle until they sign off.
- **`Stop`** (session backstop) — while `review-pending`, the lead's turn is blocked, so you can't
  report done. It does **not** block while `in-progress` (pause for the user freely) or once `approved`.

Together these make "close work / report done without review" structurally hard, without trapping
normal pauses. Keep the sentinel accurate — it is what the hooks read.

Write the sentinel with the `Write` tool (create the directory if needed). Keep it accurate —
it is the backstop that enforces the bias-correction gate.

## TDD & task ordering (per task)

Enforce test-first using **native Agent Team task dependencies**:

1. **Agree the contract first** — the interface/signature/behavior the task must satisfy (the
   orchestrator or an architect teammate states it). Both the test and impl workers work to it.
2. **Test task (red):** the independent `test` worker writes tests against the contract that
   **fail** now (confirm they fail — a test that can't fail is worthless). It does **not** write
   implementation.
3. **Impl task (green):** create it with a **dependency on the test task** (a task with an open
   dependency can't be claimed until the dependency completes — this is how test-first is enforced
   structurally). The impl worker makes the tests pass, then refactors. It does **not** write its
   own tests first.
4. **Gate:** reviewer + critic review the result (reviewer checks the tests can actually fail and
   cover failure modes; critic checks the contract was the right one).

The implementer never authors the tests — independent test authorship is the same bias-correction
principle as independent review, applied to tests.

## Per-task rhythm (HITL)

Work the shared task list **one task at a time**. After each task passes the gate, **report to the
user** (what changed, how verified) and proceed. Clarify the requirement up front and approve the
task plan once; don't run a large job end-to-end without these checkpoints, and don't ask on every
tool call either.

## Cleanup (and its limits)

Order matters: **shut down teammates → confirm stopped → `clean up the team` → close leftover panes.**
Cleanup *fails* if any teammate is still running, and Agent Teams shutdown is slow (a teammate finishes
its current request before exiting). After cleanup, cmux leaves the empty panes open — **close them with
the cmux CLI** (`cmux close-surface --surface <id>`, preserving your own `$CMUX_SURFACE_ID`). The
**`/agent-orchestra:teardown`** skill does all of this in order. (A *hook* can't auto-close panes — no
"teammate exited" event — but a user-invoked teardown skill can, via cmux's CLI/socket.)

## When the gate fails

- Route each finding to the **responsible worker** by name via the mailbox; have them fix and
  **re-verify** (run tests/lint), not just claim a fix.
- Re-run reviewer/critic on the fix. Loop until both sign off. Then set `approved`.
- Record recurring problems: the reviewer/critic should capture them in their `MEMORY.md` so
  the next run anticipates them.
