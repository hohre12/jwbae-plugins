---
name: plan
description: Deeply analyze a substantial or brownfield change (read-only, multi-agent exploration) and run an HITL interview to produce an APPROVED design agreement (plan.md) that /agent-orchestra:run then implements against. Use BEFORE run for non-trivial work in an existing codebase — especially cross-repo / multi-project integration — so implementation is anchored to a reviewed, persisted plan instead of guesses. Not for trivial one-line changes.
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
   the *real* code. Spawn an **`explorer` per repo/area** (native Agent Team, or parallel read-only
   agents) to map — against the goal — the real components, data models, APIs/contracts, identifiers,
   auth/tenancy, existing patterns, and the **exact seams** where new code attaches. Cross-repo →
   **one explorer per repo, in parallel**. Verify in code (cite `file:line`); never assume. Honor existing
   domain knowledge (`.claude/knowledge/`).

3. **Surface decisions & interview (HITL).** From the analysis, extract the **genuine decisions**
   (architecture, data/DB, identity/tenancy, formats, scope) and the **open questions / risks / conflicts**
   with the goal. Walk the big ones with the user **one at a time** via `AskUserQuestion` to reach explicit
   agreement. For decisions with an industry standard, **research current best practice — date-anchored
   (use today's real date) and ask before any web access** — and bring it. Ask only what genuinely shapes
   the work; **don't re-litigate already-settled items.**

4. **Decompose into phases (parallel-first).** Turn the agreed design into **phases** (each run-sized),
   with tasks, real dependencies, and which repos/workers each touches. Prefer **contract-first parallel
   tracks** (backend ∥ frontend, repo A ∥ repo B) over serial layers; sequence only genuine dependencies.

5. **Write the plan (the agreement).** Save **`docs/agent-orchestra/<slug>/plan.md`** in the user's
   language — see `reference.md` for the template. It contains: goal · system map (analysis findings with
   `file:line`) · **locked decisions** · open questions/risks · **phases & tasks** · identifier/contract
   notes · out-of-scope · `version` + `updated`. A living, reviewable document.

6. **Review & approve (HITL gate).** Present the plan; get explicit approval (`AskUserQuestion`:
   approve / adjust / just proceed). **Only after approval**, write the handshake
   `.agent-orchestra/state/plan.json` with `status: "approved"` (see `reference.md` schema). If the user
   adjusts, revise `plan.md` and re-confirm. Until approved, keep `status: "draft"`.

7. **Hand off.** Tell the user they can implement now: just `/agent-orchestra:run` (auto-picks this plan),
   or `/agent-orchestra:run <slug> [Phase N]`.

## Hard rules
- **Read-only.** No product code, no `.claude/agents/` changes — only `plan.md` + `plan.json`.
- **Analyze the real code thoroughly** with `file:line` evidence; never assume on brownfield.
- **Interview on genuine decisions** (research standards date-anchored, with approval); don't over-ask,
  don't re-decide settled items.
- **Per-feature**: one plan folder per feature; revising rewrites that feature's `plan.md` (git keeps history).
- Set `plan.json` to `approved` **only after** the user approves — `run` trusts that flag.
