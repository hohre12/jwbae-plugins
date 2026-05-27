---
name: report
description: Summarize the work completed in this run/session into a structured report.md at the protocol path, written in the project's output language (e.g. 한국어). On-demand report (re)generation for a feature. (At run completion the report is produced inline by /agent-orchestra:run's wrap-up — this skill is the manual/standalone entry, so it doesn't double-fire.)
disable-model-invocation: true
argument-hint: "[optional: feature slug]"
---

# /agent-orchestra:report — write the completed-work report

Summarize **what was actually done** in this run/session into a persisted, human-read report so the
team and future joiners can see the history. **Write it in the project's output language** (the literal
`OUTPUT_LANGUAGE` from `CLAUDE.md`, e.g. `한국어` — not English, not the abstract phrase "user's
language"). Read [reference.md](reference.md) for the structure and path.

The argument (optional feature slug): $ARGUMENTS

## When this runs
- **Automatically** at the end of `/agent-orchestra:run` — when the codebase work is complete (all
  tasks/phases passed the gate) and you are about to tell the user it's done, you produce this report
  **before** signing off. (This is the "모든 작업 완료" trigger — run knows deterministically when it finished.)
- **On demand** — the user invokes `/agent-orchestra:report [slug]` to (re)generate it any time.
- Skip only for trivial one-line changes that warranted no run report.

## Procedure
1. **Determine the feature + date.** Use the active feature (from `.agent-orchestra/state/plan.json` or
   the run's slug) and today's real date (check `date`). Path:
   `docs/agent-orchestra/<feature>/<YYYY-MM-DD>/report.md` (create dirs as needed).
2. **Gather the facts** of the completed work — don't narrate the chat; report the outcome:
   what was built/changed, key decisions made, files touched, how it was verified (test/lint/build/e2e
   results), and what remains / next steps. Pull from the run's actual results, the gate sign-offs, and
   `plan.md` if present.
3. **Write `report.md`** in `OUTPUT_LANGUAGE`, with the structure in `reference.md`. If a report for this
   feature+date already exists, **update/extend it** (don't silently duplicate).
4. **Append one row to `docs/agent-orchestra/INDEX.md`** (newest first): date · feature · one-line
   what/why · link to this report — so the onboarding timeline stays current.
5. **Tell the user** where the report was saved.

## Hard rules
- **Output language only** — write the report in the literal `OUTPUT_LANGUAGE` from `CLAUDE.md`
  (e.g. `한국어`). **If `CLAUDE.md`/`OUTPUT_LANGUAGE` is missing or still a placeholder, fall back to the
  language the user is writing in** (and note that fallback).
- **Report outcomes faithfully** — if something failed, was skipped, or is unfinished, say so plainly;
  don't claim done what isn't (the verify-gate facts are the source of truth).
- **Fixed protocol path** (`docs/agent-orchestra/<feature>/<date>/report.md`) — don't scatter reports.
