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
   files at the bare path (they have no Write tool). Keep `MEMORY.md` a concise index. **Write memory in
   the concrete output language you name in their spawn prompt (the literal `OUTPUT_LANGUAGE`, e.g.
   `한국어`) — never the abstract phrase "user's language", which regresses to English.**

If a memory file doesn't exist yet, note that and let the agent create it on first write.

## Gate contract (enforced by native team hooks + Stop backstop)

Maintain a sentinel at `.agent-orchestra/state/gate.json` (gitignored). Schema:

```json
{
  "request": "<short>",
  "status": "in-progress | review-pending | approved",
  "updated": "<iso8601>",
  "reviewer": "APPROVE",
  "critic": "NO BLOCKING CONCERNS"
}
```

- On forming the team for a work request: write `status: "in-progress"` (omit the verdict fields).
- When workers finish and review begins: set `status: "review-pending"`.
- Only after reviewer returns `APPROVE` **and** critic returns `NO BLOCKING CONCERNS` **and the objective
  checks are green**: set `status: "approved"` **and record the two verdicts** (the `reviewer` / `critic`
  fields). The `review-gate` hook **blocks an `approved` state whose verdict fields are missing** — you
  cannot mark work approved without recording that the reviewer/critic actually signed off. (The hook can
  enforce *that you recorded* the sign-off, not the reviewer's judgment itself — that is why the reviewer
  and critic run as independent teammates held by `TeammateIdle`/`TaskCompleted`.)
- After reporting and team cleanup: remove the file (the `shutdown` skill does this).

The sentinel drives the hooks (you don't call them; they run automatically):
- **`TaskCompleted`** — while `review-pending`, a non-review teammate cannot mark a task
  complete (the reviewer/critic completing their own review tasks is allowed).
- **`TeammateIdle`** — while `review-pending`, the reviewer/critic cannot go idle until they sign off.
- **`Stop` → `verify-gate`** (objective) — while `review-pending`/`approved`, **re-runs** the project's
  `.agent-orchestra/verify.json` checks (`test`/`lint`/`build`/`e2e`) and blocks if any fail — the
  fact-anchor a sentinel can't be self-`approved` past. It memoizes on the **working-tree signature**, so
  it re-runs when the code actually changed and skips when it didn't (no full-suite re-run on every idle
  pause while you wait for reviewers). Per-check timeouts are configurable via `verify.json` `"timeouts"`.
- **`Stop` → `review-gate`** (backstop) — while `review-pending`, blocks the lead's turn so you can't
  report done; **at `approved`, blocks if the `reviewer`/`critic` verdict fields are missing** (can't
  approve un-reviewed work). Doesn't block `in-progress` (pause for the user freely).

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

## Per-batch rhythm (HITL)

Decompose for **parallelism** (SKILL steps 2 & 4): independent tasks run **concurrently** on different
teammates — don't serialize "one task at a time." **Gate at a batch/phase boundary, not per individual
parallel task**, because the gate sentinel is one team-wide state (§ Gate contract): let a batch of
independent tasks all reach completion, flip it to `review-pending`, review it as a unit, then **report
to the user** (what changed, how verified) and proceed to the next batch/phase. Clarify the requirement
up front and approve the task plan once; don't run a large job end-to-end without these checkpoints, and
don't ask on every tool call either.

## Cleanup (and its limits)

Order matters: **shut down teammates → confirm stopped → `clean up the team` → close leftover panes.**
Cleanup *fails* if any teammate is still running, and Agent Teams shutdown is slow (a teammate finishes
its current request before exiting). After cleanup, cmux leaves the empty panes open — **close them with
the cmux CLI** (`cmux close-surface --surface <id>`, preserving your own `$CMUX_SURFACE_ID`). The
**`/agent-orchestra:shutdown`** skill does all of this in order. (A *hook* can't auto-close panes — no
"teammate exited" event — but a user-invoked shutdown skill can, via cmux's CLI/socket.)

## When the gate fails

- **Set the gate sentinel back to `in-progress`** while the worker fixes — `team-gate` blocks non-review
  task completions only while `review-pending`, so a worker can't close its fix task until you flip back.
- Route each finding to the **responsible worker** by name via the mailbox; have them fix and
  **re-verify** (run tests/lint), not just claim a fix.
- Flip back to `review-pending` and re-run reviewer/critic on the fix. Loop until both sign off, then
  **record their verdicts** and set `approved` (§ Gate contract).
- Record recurring problems: the reviewer/critic should capture them in their `MEMORY.md` so
  the next run anticipates them.

## External facts & latest info (full procedure)

Don't rely only on training-cutoff knowledge for things that change — library/framework APIs,
versions, breaking changes, current best practice. When a task genuinely needs current external
facts (a worker hits this and flags it via mailbox, or you do):
- **Anchor to the real current date** (check it — e.g. `date` — don't assume your training cutoff).
- **Ask the user before reaching out** (`AskUserQuestion`: what to look up + why). On approval,
  use `WebSearch`/`WebFetch` (or the `context7` MCP for library docs) scoped to *today's* date.
- **Cite source + date** in the result so the decision is traceable; prefer official docs.
Skip all this for stable knowledge — this is only for facts that move.
