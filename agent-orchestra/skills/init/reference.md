# init reference — triage, scaffolding, interview

Detailed procedures for `/agent-orchestra:init`. Read this before scaffolding.

## Maturity triage

Classify from the auto-collected signals:

| Stage | Signals | First action | Team weight |
| --- | --- | --- | --- |
| **greenfield** | no code, no manifest (maybe just an idea/arg) | standard interview → plan → skeleton | architect, explorer |
| **spec** | docs/PRD present, no code | extract intent from docs → plan stack | architect + early workers |
| **in-development** | partial code, some tests | analyze real idioms → match conventions | workers + reviewer |
| **mature** | full code, tests, CI | seed rubric from git history & tests | reviewer/critic-heavy |
| **legacy** | code present, not your history | archaeology pass (explorer first) | explorer + reviewer |

Pick the closest stage; if ambiguous, state both candidates and ask the user.

## Standard-slot checklist

Walk every slot. Create from the template, or record an explicit reasoned N/A.

| Slot | Source template | Notes |
| --- | --- | --- |
| `CLAUDE.md` | `templates/CLAUDE.md.tmpl` | SSOT, <200 lines. Fill stack/commands/conventions/maturity/roster |
| `.claude/settings.json` | (write directly) | `{"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"},"teammateMode":"tmux"}` — **no `agent` key** (Agent Orchestra is invoked, not always-on) |
| `.claude/rules/*.md` | `templates/rules/*.tmpl` | Fill `paths:` globs + commands. Add/remove rules to fit the project |
| `.claude/agents/*.md` | `templates/archetypes/*.md` | Instantiate the workers this project needs (below) |
| `.claude/agent-memory/{orchestrator,reviewer,critic}/MEMORY.md` | (create empty seed) | Concise index seed; agents fill over time. `orchestrator/` = coordination/planning memory (the `/run` skill reads/writes it). Committed & shared |
| `.mcp.json` | `templates/mcp.json.tmpl` | Redmine/Supabase as needed; secrets via `${ENV_VAR}` |
| **output dir** | (set path only) | `{{OUTPUT_DIR}}` default `docs/agent-orchestra/`. **Don't pre-create category dirs** — feature folders (`<slug>/`, `<slug>/<date>/`) are made on demand, proportional to the work. Project PRD lives separately at `docs/PRD.md` (tool-neutral) |
| **`.claude/knowledge/`** | (create + `index.md` + README) | Domain/business rules folder. Create `index.md` (seed, imported by CLAUDE.md `@import`) + `README.md` (usage). Goal 5 |
| `output-styles/` | — | Usually **N/A** (user-global preference). Create only if a project-specific report tone is wanted |

Output paths: **project PRD/architecture → `docs/PRD.md`** (product-level, tool-neutral, created here
for greenfield). **Tool artifacts → `{{OUTPUT_DIR}}/<feature-slug>/`** (optional `prd.md`/`design.md` for
big features) **and `<feature-slug>/<YYYY-MM-DD>/{review,report}.md`** per run. Small changes: inline
review, no files. Knowledge folder = native-loaded domain
context: `.claude/knowledge/index.md` is `@import`ed by `CLAUDE.md` so it's in every session; always-apply
domain *rules* can also go in `.claude/rules/` (auto-loaded). See § Domain knowledge below.

**Invocation model (not always-on):** do **not** set an `agent` key. Agent Orchestra runs only when
`/agent-orchestra:run` is invoked — explicitly by the user, or auto-invoked by Claude when a request
is clearly substantive coding work. Outside that, the project behaves as plain Claude (so the user can
opt out anytime). Add a one-line nudge in `CLAUDE.md` ("substantive code/design/analysis → use
`/agent-orchestra:run`") so it isn't forgotten. This matches plugin conventions and AI-DLC's
invoked, checkpoint-based model.

Also: ensure `.gitignore` covers `.claude/settings.local.json` and `.agent-orchestra/` (gate state).
`bypassPermissions` is **not** written here — the user runs `cgo` (the `--dangerously-skip-permissions` flag).

**Context-budget guard:** `CLAUDE.md` loads **in full** every session — keep it under ~200 lines.
If it grows, move topic-specific instructions into `.claude/rules/` (path-scoped: loaded only when
Claude touches matching files). Skill `reference.md` files stay under ~500 lines (progressive disclosure).

## Domain knowledge (goal 5) — native loading

Human-world rules the code can't reveal (business rules, domain constraints, external policies)
must be loadable by every agent. Use **native loading**, not a bare folder + custom instructions:

- Create `.claude/knowledge/` with:
  - `index.md` — concise seed that the project's `CLAUDE.md` `@import`s, so it's in **every
    session's context**. ⚠️ `@import` loads the file **in full** every session, so keep `index.md`
    short — it should **list/link** deeper docs (read on demand), **not** `@import` all of them.
    Importing large knowledge files would bloat every session's context.
  - `README.md` — explains: "Put project domain/business knowledge here as markdown. `index.md`
    is imported into every session; reference detailed files from it."
- Always-apply domain **rules** (vs reference knowledge) can alternatively live in `.claude/rules/`
  (auto-loaded), path-scoped if they only apply to certain files.
- The CLAUDE.md template already includes `@.claude/knowledge/index.md` and a "Domain knowledge"
  section, so init just creates the folder + seed files. Agents then see this context natively;
  no per-agent "go read the folder" wiring is required.

## Archetype instantiation

For each worker role the project needs (from the 6 in `${CLAUDE_PLUGIN_ROOT}/templates/archetypes/`:
backend, frontend, test, explorer, architect, devops):

1. Read the archetype file.
2. Substitute placeholders from triage:
   `{{PROJECT_NAME}}`, `{{STACK}}`, `{{BUILD_CMD}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}`,
   `{{CONVENTIONS}}`, `{{RULES_PATHS}}`.
3. Write the filled result to `.claude/agents/<role>.md`.

Pick roles by stage and project shape — e.g. a backend-only API project may need only
`backend` + `test`; a greenfield app may start with `architect` + `explorer`. Don't
instantiate roles the project has no use for. The standing `reviewer` and `critic` come
from the plugin and are **not** copied per project.

## Greenfield interview (standard depth)

Run in plan mode. Reach agreement on exactly these three, then stop and propose the plan:

1. **PRD core** — goal, scope, the handful of key user stories.
2. **Stack** — languages, frameworks, datastore, key libraries.
3. **Key architecture decisions** — the few choices that shape everything (e.g. data model
   spine, sync vs async, auth approach). Leave full data models / API surface for workers.

Rules:
- The artifact the user approves is the **project PRD**, not the chat. Write it to **`docs/PRD.md`**
  (tool-neutral, product-level — not under `docs/agent-orchestra/`).
- Offer "just proceed, I approve" as an escape at every step; keep questions to a/b/c where possible.
- Once a decision is approved, do not reopen it.
- Only after explicit approval: scaffold `.claude/` and the skeleton, then hand off.
