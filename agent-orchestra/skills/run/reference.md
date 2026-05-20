# run reference — team protocol, memory injection, gate contract

Detail for `/agent-orchestra:run`.

## Team-formation protocol

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

Native `memory: project` may not auto-load when an agent runs as a *teammate*, so inject it yourself:

1. Before spawning the reviewer: `Read .claude/agent-memory/reviewer/MEMORY.md` and paste its
   content into the reviewer's spawn prompt under a "Your accumulated memory" heading.
2. Same for the critic with `.claude/agent-memory/critic/MEMORY.md`.
3. Tell each in the spawn prompt: when your task is done, append durable, distilled lessons to
   your own `MEMORY.md` (consolidate, don't dump; keep it the index).

If a memory file doesn't exist yet, note that and let the agent create it on first write.

## Gate contract (couples with the Stop hook)

Maintain a sentinel at `.agent-orchestra/state/gate.json` (gitignored). Schema:

```json
{ "request": "<short>", "status": "in-progress | review-pending | approved", "updated": "<iso8601>" }
```

- On forming the team for a work request: write `status: "in-progress"`.
- When workers finish and review begins: set `status: "review-pending"`.
- Only after reviewer returns `APPROVE` **and** critic returns `NO BLOCKING CONCERNS`:
  set `status: "approved"`.
- After reporting and team cleanup: set `approved` (or remove the file).

The **Stop hook** blocks the turn only when `status == "review-pending"` — i.e. work was
delivered but the gate hasn't passed. It does **not** block while `in-progress` (so you can
pause for the user mid-work) or once `approved`. This makes "report done without review"
structurally hard without trapping normal pauses.

Write the sentinel with the `Write` tool (create the directory if needed). Keep it accurate —
it is the backstop that enforces the bias-correction gate.

## When the gate fails

- Route each finding to the **responsible worker** by name via the mailbox; have them fix and
  **re-verify** (run tests/lint), not just claim a fix.
- Re-run reviewer/critic on the fix. Loop until both sign off. Then set `approved`.
- Record recurring problems: the reviewer/critic should capture them in their `MEMORY.md` so
  the next run anticipates them.
