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
| `.claude/settings.json` | (write directly) | `{"agent":"orchestrator","env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"},"teammateMode":"tmux"}` |
| `.claude/rules/*.md` | `templates/rules/*.tmpl` | Fill `paths:` globs + commands. Add/remove rules to fit the project |
| `.claude/agents/*.md` | `templates/archetypes/*.md` | Instantiate the workers this project needs (below) |
| `.claude/agent-memory/{reviewer,critic}/MEMORY.md` | (create empty seed) | One-line seed; the agents fill these over time |
| `.mcp.json` | `templates/mcp.json.tmpl` | Redmine/Supabase as needed; secrets via `${ENV_VAR}` |
| **output dir** | (create dirs) | `{{OUTPUT_DIR}}` default `docs/agent-orchestra/` with `prd/ design/ review/ reports/`. Fill `{{OUTPUT_DIR}}` in CLAUDE.md. Goal 4 |
| **`.claude/knowledge/`** | (create + `index.md` + README) | Domain/business rules folder. Create `index.md` (seed, imported by CLAUDE.md `@import`) + `README.md` (usage). Goal 5 |
| `output-styles/` | — | Usually **N/A** (user-global preference). Create only if a project-specific report tone is wanted |

Output dir = where all generated docs go (PRD/design/review/reports). `{{OUTPUT_DIR}}` is configurable
per project; agents save deliverables there (not scattered). Knowledge folder = native-loaded domain
context: `.claude/knowledge/index.md` is `@import`ed by `CLAUDE.md` so it's in every session; always-apply
domain *rules* can also go in `.claude/rules/` (auto-loaded). See § Domain knowledge below.

The `"agent": "orchestrator"` line makes the orchestrator the project's **default main thread**
(always-on, project-scoped) — so the user never has to type `/agent-orchestra:run`; every
substantive request is orchestrated and gated by default. This is set per-project on purpose
(not globally), so other projects are unaffected.

Also: ensure `.gitignore` covers `.claude/settings.local.json` and `.agent-orchestra/` (gate state).
`bypassPermissions` is **not** written here — the user runs `cgo` (the `--dangerously-skip-permissions` flag).

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
- The artifact the user approves is the **plan/PRD doc**, not the chat. Write it to `docs/`.
- Offer "just proceed, I approve" as an escape at every step; keep questions to a/b/c where possible.
- Once a decision is approved, do not reopen it.
- Only after explicit approval: scaffold `.claude/` and the skeleton, then hand off.
