# plan reference — analysis team, plan.md, the run handshake

Detailed procedures for `/agent-orchestra:plan`. Read before planning.

## Analysis team (step 2) — read-only, thorough

- This is brownfield: **assume nothing, verify in code.** The depth here is the whole point of a
  separate `plan` skill — `run` should never have to guess on existing code. **One explorer per repo /
  major area, in parallel**; each maps (against the goal) components, data models, API/contracts,
  identifiers, auth/tenancy, existing patterns, and the **exact seams** where new code attaches. Cite
  `file:line`; distinguish **verified** from **inferred**; no edits, no `Write` to code. Pull in
  `.claude/knowledge/` domain context; reconcile the goal against what the code actually does.

### Preferred mechanism — the analysis Workflow

The read-only fan-out is delegated to a Workflow (deterministic parallelism + schema-enforced output),
keeping this skill's **HITL parts (slug, interview, critic, approval, plan.md/plan.json writes) in the
main session** — the Workflow does no HITL and writes no files.

- **Script:** `${CLAUDE_PLUGIN_ROOT}/skills/plan/workflows/analysis.mjs`. Call `Workflow` with
  `scriptPath` + `args`. A skill instructing `Workflow` is a sanctioned trigger — no user opt-in needed.
- **`args` contract:** `{ goal, repos: string[], outputLanguage, today, knowledgePaths: string[] }`.
  - `repos`: scout the work-list inline first (cwd + any `--add-dir` attached repos / major areas). Defaults to `['.']`.
  - `today`: pass the **real date** (`date`) — the script can't call `Date.now()`/`new Date()`.
  - `outputLanguage`: the literal `OUTPUT_LANGUAGE` (findings come back as raw English data; *you* write plan.md in it).
- **What it does / returns:** `phase Explore` (one `agentType:'Explore'` explorer per area, in parallel,
  `FINDINGS_SCHEMA`) → `phase Completeness` (one pass flagging unmapped areas / uncited seams / unverified
  "inferred" claims) → `phase Synthesize` (one cross-repo seam map). Returns
  `{ goal, today, areas, findings, gaps, synthesis }`. **You still own the final seam synthesis** and the
  decision of what to interview on — treat `synthesis` as a strong draft, not the last word.
- **Scale** the explorer count to the number of real repos/areas; don't fan out blindly.

### Fallback — no Workflow runtime (older Claude Code)

Spawn an **`explorer` per repo/area** the old way: native Agent Team if available, else parallel read-only
general agents given the explorer discipline inline (read-only, cite `file:line`, verified-vs-inferred).
**If no `explorer` agent exists on disk** (init's roster may omit it): have `agent-architect` instantiate
one from the `explorer` archetype, or use general read-only agents with the discipline inline. Don't skip
the deep analysis for lack of the runtime or a pre-made explorer. The lead synthesizes the seams *between* repos.

## Interview (step 3) — reach explicit agreement

- Convert findings into a short list of **genuine decisions** + **open questions/risks/conflicts**.
- Use `AskUserQuestion`, big decisions **one at a time**. Offer "just proceed" to accept your recommendation.
- For decisions with an industry standard (architecture/security/data), **research current best practice**:
  anchor to **today's real date** (check `date`), **ask the user before reaching out**, then
  `WebSearch`/`WebFetch`/`context7`, cite source + date. (Same approval-gated rule as `run`.)
- Don't over-ask, don't reopen settled decisions, don't fabricate a contract the code doesn't support.

## `plan.md` structure (the agreement)

Save to `docs/agent-orchestra/<slug>/plan.md`, in the project's **output language** — the literal
`OUTPUT_LANGUAGE` from `CLAUDE.md` (e.g. `한국어`; fall back to the language the user writes in if absent),
never the abstract "user's language" (which regresses to English):

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

## Plan critique (step 6) — bias correction at design time

Before the user-approval gate, **spawn the `critic` on the drafted `plan.md`** (read-only: hand it the
plan + the analysis findings, **not** your reasoning — same cold, independent stance as in `run`). It
challenges the **premise** (does this solve the real problem?), **scope** (over/under-built?), **missing
decisions**, and **risks** — the cheapest place to catch a wrong plan is *before any code is written*.
Fold its concerns into `plan.md` (or record why not), then surface the remaining concerns to the user
alongside the plan. The critic writes no code and no files here — it returns concerns to you; you decide
and the user approves. (This is the design-time analogue of the build-time review/critic gate.)

## `plan.json` handshake (the run protocol)

State lives in **two committed locations** (the durable handshake; `.agent-orchestra/state/` holds only
transient hook state):

- **Per-feature record (authoritative)** — `docs/agent-orchestra/<slug>/plan.json`, beside that feature's
  `plan.md`. The source of truth for *that feature's* phases/status. It **survives even when you go plan
  or run a different feature** — so feature A's progress is never lost because you started feature B.
- **Active pointer** — `.agent-orchestra/plan.json`, a copy of the **currently active** feature's record.
  `run` reads this to know which plan is live now. Switching features overwrites this pointer **but never
  touches any feature's own `docs/.../<slug>/plan.json`**; returning to a feature re-reads its folder record.

Write both only after approval (`mkdir -p .agent-orchestra docs/agent-orchestra/<slug>` as needed). Same schema in each:

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

- `status`: `draft` (in progress) → `approved` (run may consume) → `done` (all phases finished; set by
  `shutdown` so a stale approved plan isn't auto-surfaced to the next unrelated run). Phase `status`:
  `pending` → `done` (run marks a phase done when its gate passes — **update the feature record, then
  refresh the active pointer**). This lets `run` resume the next pending phase and avoids re-running work.
- If several features have plans, `run` asks which (by slug) — it never auto-guesses — then loads that
  feature's record into the active pointer.

## How `run` uses it (wrong-plan safeguards)

`run` reads `plan.json` at its precondition step and:
1. **Announces & confirms** the plan it will use — feature, `plan_path`, `updated` date — before building.
   (HITL confirmation is the primary guard against consuming the wrong/stale plan.)
2. Loads `plan.md` as the **binding contract/anchor**; does not re-litigate locked decisions, surfaces only
   *new* conflicts found during implementation.
3. Marks phase `status` complete in **both** the feature's `docs/.../<slug>/plan.json` (authoritative)
   and the active pointer `.agent-orchestra/plan.json`; resumes the next `pending` phase.
4. If `status` is stale/old and code has changed materially, suggests re-running `/plan` to revise.
5. No approved plan for substantial brownfield work → offers to run `/plan` first.
