---
name: plan
description: Deeply analyze a substantial or brownfield change (read-only, multi-agent exploration) and run an HITL interview to produce an APPROVED design agreement (plan.md) that /agent-orchestra:run then implements against. Use BEFORE run for non-trivial work in an existing codebase — especially cross-repo / multi-project integration — so implementation is anchored to a reviewed, persisted plan instead of guesses. Not for trivial one-line changes.
disable-model-invocation: true
argument-hint: "[what you want to plan / the feature]"
---

# /agent-orchestra:plan — analyze, interview, agree a plan (read-only)

Invoking this makes you the **planning lead**. You produce a reviewed **design agreement** for a
substantial change by *thoroughly analyzing the real code* and *interviewing the user on the genuine
decisions*, then persist it so `/agent-orchestra:run` implements against it. **You write NO product
code here** — read-only: analysis + the plan document + the handshake state. **Respond in the user's
language.** Read [reference.md](reference.md) for the analysis-team protocol, the `plan.md` structure,
the `plan.json` handshake/lifecycle, and the run wiring.

The request: $ARGUMENTS

## When to use / when to skip
- **Use** for **substantial brownfield work**: a new feature, a cross-layer or cross-repo/multi-project
  integration, or anything touching unfamiliar/existing code. Greenfield-from-scratch can also benefit.
- **Skip** for trivial one-liners / quick fixes — tell the user to just `/agent-orchestra:run` (handled inline).

## Procedure

1. **Frame the goal + pick a feature slug (HITL).** Restate what the user wants; confirm. Choose a
   kebab-case **feature slug** (e.g. `repoto-brain`). If `docs/agent-orchestra/<slug>/plan.md` already
   exists, this is a **revision** — load it and update in place (don't start over).

2. **Deep analysis — multi-agent, read-only (the heart of plan).** Brownfield ⇒ assume nothing; analyze
   the *real* code. Map — against the goal — the real components, data models, APIs/contracts, identifiers,
   auth/tenancy, existing patterns, and the **exact seams** where new code attaches. Verify in code (cite
   `file:line`); never assume. Honor existing domain knowledge (`.claude/knowledge/`).
   - **Preferred — run the analysis Workflow** (this skill instructing it is a sanctioned trigger; you do
     **not** need the user to opt in). First scout the work-list inline (which repos/areas, the cwd plus any
     attached dirs), then call `Workflow` with
     `scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/plan/workflows/analysis.mjs"` and
     `args: { goal, repos: [<area/repo paths>], outputLanguage: "<literal OUTPUT_LANGUAGE>", today: "<from \`date\`>", knowledgePaths: [<.claude/knowledge files>] }`.
     **Pass `args` as an actual JSON object in the Workflow tool call — NOT a JSON-encoded string.** A
     stringified value reaches the script as one string, so `args.repos`/`args.goal` come back undefined
     and the per-area fan-out silently collapses to a single explorer over `.` (the script now defends
     against this by parsing a stringified arg, but pass structured JSON so the scaling is correct).
     It fans out **one read-only explorer per repo/area in parallel** (schema-enforced: `file:line`,
     verified-vs-inferred), runs a completeness pass, and returns a synthesized cross-repo seam map. Pass
     `today` from the real date (the script can't call `Date`). Read the returned `findings`/`gaps`/`synthesis`
     and **own the final seam synthesis yourself** before interviewing.
   - **Fallback (no Workflow runtime / older Claude Code):** spawn an **`explorer` per repo/area** the old way
     — native Agent Team if available, else parallel read-only general agents given the explorer discipline
     inline (read-only, cite `file:line`, verified-vs-inferred). Don't skip the deep analysis for lack of the runtime.

3. **Surface decisions & interview (HITL).** From the analysis, extract the **genuine decisions**
   (architecture, data/DB, identity/tenancy, formats, scope) and the **open questions / risks / conflicts**
   with the goal. Walk the big ones with the user **one at a time** via `AskUserQuestion` to reach explicit
   agreement. For decisions with an industry standard, **research current best practice — date-anchored
   (use today's real date) and ask before any web access** — and bring it. Ask only what genuinely shapes
   the work; **don't re-litigate already-settled items.**

4. **Decompose into phases (parallel-first).** Turn the agreed design into **phases** (each run-sized),
   with tasks, real dependencies, and which repos/workers each touches. Prefer **contract-first parallel
   tracks** (backend ∥ frontend, repo A ∥ repo B) over serial layers; sequence only genuine dependencies.

5. **Write the plan (the agreement).** Save **`docs/agent-orchestra/<slug>/plan.md`** in the project's
   **output language** — the literal `OUTPUT_LANGUAGE` from `CLAUDE.md` (e.g. `한국어`; if `CLAUDE.md`/
   `OUTPUT_LANGUAGE` is missing or a placeholder, fall back to the language the user writes in), **not**
   the abstract phrase "user's language" (which regresses to English). `plan.md` is the binding contract
   `run` loads, so this matters. See `reference.md` for the template. It contains: goal · system map (analysis findings with
   `file:line`) · **locked decisions** · open questions/risks · **phases & tasks** · identifier/contract
   notes · out-of-scope · `version` + `updated`. A living, reviewable document.

6. **Adversarially review the plan (critic), then approve (HITL gate).** Before asking the user, **spawn
   the `critic` on `plan.md`** (read-only — give it the plan + the analysis findings, **not** your
   reasoning) to challenge the premise, scope, missing decisions, and risks. This applies the
   bias-correction gate **at design time, before any code is written** — the cheapest place to catch a
   wrong plan. Fold its concerns into `plan.md` (or note why not). **Then present the plan + the critic's
   surfaced concerns** and get explicit approval (`AskUserQuestion`: approve / adjust / just proceed).
   **Only after approval**, write the handshake to **BOTH** locations — the per-feature **authoritative**
   record `docs/agent-orchestra/<slug>/plan.json` **and** the active pointer `.agent-orchestra/plan.json`
   — each with `status: "approved"` (see `reference.md` § plan.json handshake for the two-location
   protocol; writing only the active pointer loses feature state when you later plan another feature). If
   the user adjusts, revise `plan.md` and re-confirm. Until approved, keep `status: "draft"`.

7. **Hand off.** Tell the user they can implement now: just `/agent-orchestra:run` (auto-picks this plan),
   or `/agent-orchestra:run <slug> [Phase N]`.

## Hard rules
- **Read-only.** No product code, no `.claude/agents/` changes — only `plan.md` + the two `plan.json`
  copies (per-feature authoritative record + active pointer).
- **Analyze the real code thoroughly** with `file:line` evidence; never assume on brownfield.
- **Interview on genuine decisions** (research standards date-anchored, with approval); don't over-ask,
  don't re-decide settled items.
- **Per-feature**: one plan folder per feature; revising rewrites that feature's `plan.md` (git keeps history).
- Set `plan.json` to `approved` **only after** the user approves — `run` trusts that flag.
