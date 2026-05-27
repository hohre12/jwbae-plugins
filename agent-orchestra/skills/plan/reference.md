# plan reference — analysis team, plan.md, the run handshake

Detailed procedures for `/agent-orchestra:plan`. Read before planning.

## Analysis team (step 2) — read-only, thorough

- This is brownfield: **assume nothing, verify in code.** The depth here is the whole point of a
  separate `plan` skill — `run` should never have to guess on existing code.
- **One `explorer` per repo / major area**, run in **parallel** (native Agent Team if available, else
  parallel read-only agents). Each maps, against the goal: components, data models, API/contracts,
  identifiers, auth/tenancy, existing patterns, and the **exact seams** where new code attaches.
- Cross-repo / multi-project: each explorer owns one repo; the lead synthesizes the seams *between* them.
- Explorers cite `file:line`; distinguish **verified** from **inferred**. No edits, no `Write` to code.
- Pull in `.claude/knowledge/` domain context; reconcile the goal against what the code actually does.

## Interview (step 3) — reach explicit agreement

- Convert findings into a short list of **genuine decisions** + **open questions/risks/conflicts**.
- Use `AskUserQuestion`, big decisions **one at a time**. Offer "just proceed" to accept your recommendation.
- For decisions with an industry standard (architecture/security/data), **research current best practice**:
  anchor to **today's real date** (check `date`), **ask the user before reaching out**, then
  `WebSearch`/`WebFetch`/`context7`, cite source + date. (Same approval-gated rule as `run`.)
- Don't over-ask, don't reopen settled decisions, don't fabricate a contract the code doesn't support.

## `plan.md` structure (the agreement)

Save to `docs/agent-orchestra/<slug>/plan.md`, in the user's language:

```
# <Feature> — design agreement (plan)
> version: <n> · updated: <YYYY-MM-DD> · status: draft|approved

## 1. Goal / requirements
## 2. System map (analysis findings)   ← per repo, with file:line; verified vs inferred
## 3. Locked decisions                   ← what was agreed + the why (incl. standards researched)
## 4. Open questions / risks
## 5. Phases & tasks                      ← parallel-first; deps; repos/workers per task
## 6. Identifiers / contracts / formats   ← keys, API shapes, tenancy, data formats
## 7. Out of scope / later
```

Keep it the **living source of truth** for the feature. Revising re-writes it (git holds history); bump `version`.

## `plan.json` handshake (the run protocol)

Write only after approval, to `.agent-orchestra/state/plan.json`:

```json
{
  "feature": "<slug>",
  "plan_path": "docs/agent-orchestra/<slug>/plan.md",
  "status": "approved",
  "version": 1,
  "updated": "<ISO8601>",
  "phases": [
    { "id": "P1", "title": "...", "status": "pending" },
    { "id": "P2", "title": "...", "status": "pending" }
  ]
}
```

- `status`: `draft` (in progress) → `approved` (run may consume) . Phase `status`: `pending` → `done`
  (run marks a phase done when its gate passes). This lets `run` resume the next pending phase and avoids
  re-running consumed work.
- **Single active pointer**: `plan.json` names the current feature plan. Multiple features each keep their
  own `plan.md`; `plan.json` points to the active one. If several plans exist, `run` asks which (by slug)
  — it never auto-guesses.

## How `run` uses it (wrong-plan safeguards)

`run` reads `plan.json` at its precondition step and:
1. **Announces & confirms** the plan it will use — feature, `plan_path`, `updated` date — before building.
   (HITL confirmation is the primary guard against consuming the wrong/stale plan.)
2. Loads `plan.md` as the **binding contract/anchor**; does not re-litigate locked decisions, surfaces only
   *new* conflicts found during implementation.
3. Marks phase `status` in `plan.json` as phases complete; resumes the next `pending` phase.
4. If `status` is stale/old and code has changed materially, suggests re-running `/plan` to revise.
5. No approved plan for substantial brownfield work → offers to run `/plan` first.
