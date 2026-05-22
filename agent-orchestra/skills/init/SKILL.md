---
name: init
description: Set up (or reconcile) the standard .claude layout for a project — triage project maturity, then scaffold CLAUDE.md, settings, rules, agents, and agent-memory with nothing forgotten. Run once per project; re-runnable to reconcile. Use when onboarding a project to Agent Orchestra.
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash Write Edit AskUserQuestion
argument-hint: "[optional: one-line project idea for an empty repo]"
---

# /agent-orchestra:init — standard .claude scaffolder

You set up the standard `.claude/` layout for this project so nothing is forgotten, and
keep it reconciled on later runs. Plugin templates live at `${CLAUDE_PLUGIN_ROOT}/templates/`.
Detailed checklists are in [reference.md](reference.md) — read it before scaffolding.

## Repository signals (auto-collected)

- Top level: !`ls -A 2>/dev/null | head -40`
- Manifests: !`ls package.json pyproject.toml requirements.txt go.mod Cargo.toml pom.xml build.gradle composer.json Gemfile 2>/dev/null || echo none`
- Git: !`git rev-parse --is-inside-work-tree 2>/dev/null && git log --oneline -3 2>/dev/null || echo "NO GIT"`
- Tests/CI: !`{ ls -d tests test spec .github/workflows 2>/dev/null; } | head; find . -maxdepth 3 \( -name '*test*' -o -name '*spec*' \) 2>/dev/null | head -5`
- Docs: !`{ find . -maxdepth 1 -iname 'readme*' 2>/dev/null; find docs -maxdepth 1 -name '*.md' 2>/dev/null; } | head -10 || true`
- Existing Claude config: !`{ test -f CLAUDE.md && echo "CLAUDE.md present"; ls -R .claude 2>/dev/null; } || echo "none"`
- Argument (idea, if empty repo): $ARGUMENTS

## Procedure

1. **Triage maturity** from the signals above using the table in `reference.md`
   (greenfield · spec · in-development · mature · legacy). State the stage you chose and why.

2. **If greenfield** (no code, maybe just an idea): run the **standard interview** in plan
   mode (see `reference.md` § Greenfield interview). Capture PRD core + stack + key
   architecture decisions in a `docs/` plan/PRD doc. **Do not scaffold or write code until
   the user explicitly approves the plan.** Offer "just proceed" as an escape; never
   re-litigate an approved decision.

3. **If brownfield** (code exists): analyze actual conventions, stack, build/test/lint
   commands, and existing patterns. If an existing harness is present (other agents/skills/
   loops), **do not overwrite it** — propose how to integrate (principle: no clobbering).

4. **Not a git repo?** Propose `git init` (worktree isolation + commits need it). Proceed
   only with the user's OK; if declined, note that workers run in-process and must split files.

5. **Propose the plan — HITL gate (ALL stages, not just greenfield).** Before writing anything,
   present the full scaffolding plan as a table by walking `reference.md` § Standard-slot checklist:
   each slot → *create* (from which template + key placeholder values) or *reasoned N/A*; which
   worker archetypes to instantiate; which rules; output dir; knowledge folder. Then **stop and get
   explicit approval** with `AskUserQuestion` (options: "approve all" / "let me adjust" / "just
   proceed"). **Write no files before approval.** The user approves one consolidated plan, not
   nothing — so make the proposal complete and specific.

6. **Apply the approved plan.** Create each approved slot from the matching
   `${CLAUDE_PLUGIN_ROOT}/templates/` file with placeholders filled from triage; instantiate the
   approved worker archetypes (`reference.md` § Archetype instantiation). Never silently skip a slot.
   If the user asked to adjust, revise the plan and re-confirm before applying.

7. **Reconcile (re-run):** if `.claude/` already exists, diff current repo state against the
   recorded maturity/roster in `CLAUDE.md` and **propose** changes (add/retire workers, stage
   change) the same way — propose → approve → apply. Never auto-apply.

8. **Hand off.** Print what you created/changed and the explicit N/As. Remind the user that
   the Agent Teams env var takes effect next session, so they should relaunch (`cgo`) before
   substantive work.

## Hard rules

- **Propose → approve → apply for every stage.** Never write `.claude/` files before the user
  approves the plan (greenfield approves the PRD/plan; brownfield/mature/legacy approve the
  scaffolding plan table). "Just proceed" is the only way to skip the per-item review.
- Nothing forgotten: every standard slot is created or explicitly marked N/A with a reason.
- Secrets (Redmine/Supabase keys) go in `.mcp.json` as `${ENV_VAR}` references, never inline.
- Greenfield: code only after explicit plan approval.
- This skill proposes; the user approves. Do not auto-apply reconcile changes.
