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

**⚠️ Multi-repo hub (empty cwd + attached repos):** the auto-signals only scan the **cwd**. If the cwd
is sparse/empty but **additional working directories are attached** (`--add-dir`, i.e. an orchestration
hub of several real repos), do **not** classify greenfield — that's the wrong call. Treat it as a
**brownfield hub**: read each attached repo, triage **per repo** (each may differ), set up the hub as the
control plane (`.claude/`, knowledge, `docs/`) while the real code stays in the attached repos, and make
`verify.json` chain the attached repos' checks (see verify.json row). Confirm the attached-repo list with
the user if it isn't obvious from the prompt.

## Standard-slot checklist

Walk every slot. Create from the template, or record an explicit reasoned N/A.

| Slot | Source template | Notes |
| --- | --- | --- |
| `CLAUDE.md` | `templates/CLAUDE.md.tmpl` | SSOT, <200 lines. Fill stack/commands/conventions/maturity/roster **and `{{OUTPUT_LANGUAGE}}`** — set it to the **concrete** language the user writes in (e.g. `한국어`, `日本語`, `English`), so downstream agents read a literal language, not the abstract "user's language" (which regresses to English) |
| `.claude/settings.json` | **MERGE (don't overwrite)** | Read existing first and **preserve keys like `enabledPlugins`** (a project-scope plugin install lives here!). Add `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:"1"` + `teammateMode:"tmux"`. **No `agent` key** (invoked, not always-on) |
| `.claude/rules/*.md` | `templates/rules/*.tmpl` | Fill `paths:` globs + commands. Add/remove rules to fit the project |
| `.claude/agents/*.md` | `templates/archetypes/*.md` | Instantiate the workers this project needs (below) |
| `.claude/agent-memory/{orchestrator,reviewer,critic,agent-architect}/MEMORY.md` | (create empty seed) | **Bare paths = canonical** (reviewer/critic/agent-architect carry no `memory:` frontmatter → no namespaced `agent-orchestra-*` dirs). Concise index seed; `/run` + agents fill via Bash over time. Committed & shared |
| `.claude/agents/<domain>.md` | **`agent-architect`** (composes archetypes) | Roster design is delegated — see § Roster design below. Not plain substitution |
| `.agent-orchestra/verify.json` | (write directly) | **Objective gate commands** from triage: `{"test":"<cmd>","lint":"<cmd>","build":"<cmd>"}`. The `verify-gate` hook **re-runs these at the gate** — work can't be reported done on failing checks (facts > LLM opinion). Add `"e2e"` (playwright) for frontend projects. Optional `"timeouts": {"test": 600, ...}` (seconds per check, default 250) for suites slower than the default. **Committed** (it's project config every contributor/run needs — a fresh clone without it makes the gate fail-open). For a multi-repo hub, chain the attached repos: e.g. `"test": "npm --prefix <repoA> run test && npm --prefix <repoB> run test"` |
| `.mcp.json` | `templates/mcp.json.tmpl` | Redmine/Supabase as needed; secrets via `${ENV_VAR}` |
| **output dir** | (set path only) | `{{OUTPUT_DIR}}` default `docs/agent-orchestra/`. **Don't pre-create category dirs** — feature folders (`<slug>/`, `<slug>/<date>/`) are made on demand, proportional to the work. Project PRD lives separately at `docs/PRD.md` (tool-neutral) |
| `docs/agent-orchestra/INDEX.md` | `templates/INDEX.md.tmpl` | **Onboarding timeline** — `/run` appends one row per substantial run (date · feature · what/why · links). A newcomer reads this for project history |
| **`.claude/knowledge/`** | (create + `index.md` + README) | Domain/business rules folder. Create `index.md` (seed, imported by CLAUDE.md `@import`) + `README.md` (usage). Goal 5 |
| `output-styles/` | — | Usually **N/A** (user-global preference). Create only if a project-specific report tone is wanted |

Output paths: **project PRD/architecture → `docs/PRD.md`** (product-level, tool-neutral, created here
for greenfield). **Tool artifacts → `{{OUTPUT_DIR}}/<feature-slug>/`** (optional `prd.md`/`design.md` for
big features) **and `<feature-slug>/<YYYY-MM-DD>/{review,critique,report}.md`** per run (reviewer→`review.md`,
critic→`critique.md`, run→`report.md`). Small changes: inline
review, no files. Knowledge folder = native-loaded domain
context: `.claude/knowledge/index.md` is `@import`ed by `CLAUDE.md` so it's in every session; always-apply
domain *rules* can also go in `.claude/rules/` (auto-loaded). See § Domain knowledge below.

**Language of seeds (split by reader, not folder):** seed the **human-read** artifacts in
**`{{OUTPUT_LANGUAGE}}`** (the concrete language you set in `CLAUDE.md`, e.g. `한국어`) —
`.claude/agent-memory/*/MEMORY.md`, `.claude/knowledge/{index,README}.md`,
`docs/agent-orchestra/INDEX.md`, `docs/PRD.md`. Keep the **model-facing config** in English —
`CLAUDE.md`, `.claude/agents/*.md`, `.claude/rules/*.md` (and the plugin itself). agent-memory and
knowledge live under `.claude/` but are read by people, so they are **not** English.

**Invocation model (not always-on):** do **not** set an `agent` key. Agent Orchestra runs only when
`/agent-orchestra:run` is invoked — explicitly by the user, or auto-invoked by Claude when a request
is clearly substantive coding work. Outside that, the project behaves as plain Claude (so the user can
opt out anytime). Add a one-line nudge in `CLAUDE.md` ("substantive code/design/analysis → use
`/agent-orchestra:run`") so it isn't forgotten. This matches plugin conventions and AI-DLC's
invoked, checkpoint-based model.

Also: ensure `.gitignore` covers `.claude/settings.local.json` and **`.agent-orchestra/state/`**
(transient hook state — `gate.json`, `verified.json`). **Do NOT ignore `.agent-orchestra/verify.json`
(gate config) or `.agent-orchestra/plan.json` (the approved-plan handshake)** — those are committed so
a fresh clone/teammate still has the objective gate and the plan handshake. Create the
`.agent-orchestra/state/` directory at scaffold time (so the first gate/plan write doesn't fail).
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

## Roster design & agent files — delegate to `agent-architect`

Writing the worker roster is **not** plain placeholder substitution — it's a design step
(which domains, how many agents, where to split/merge, which project-specific specialists).
Delegate it to the standing **`agent-architect`** agent (plugin-provided, hybrid: it composes
from the archetypes and **preserves their non-negotiable blocks verbatim**, so quality never
drifts while the roster gets tailored to this project).

- During init, hand `agent-architect` the triage result + `CLAUDE.md` values and have it
  propose the roster (agent · derived-from archetype · domain evidence · why). **It returns that table
  to you — you fold it into the single step-5 approval gate; agent-architect does NOT run its own
  `AskUserQuestion`** (a spawned subagent's prompts don't reach the user, and a second gate would
  double-ask). After approval, it writes the approved `.claude/agents/<domain>.md` files and self-verifies
  each still contains its non-negotiable markers before handing back.
- The 6 archetypes (`${CLAUDE_PLUGIN_ROOT}/templates/archetypes/`: backend, frontend, test,
  explorer, architect, devops) are the **quality floor / building blocks**, not the final roster.
  A backend-only API may yield `backend` + `test`; a greenfield app `architect` + `explorer`; a
  project with a distinct domain (payments, recsys, realtime-sync) gets a tailored specialist
  derived from the nearest archetype. Don't create roles the project has no use for.
- The standing `reviewer`, `critic`, and `agent-architect` itself come from the plugin and are
  **not** copied per project.
- *Fallback:* if delegating isn't possible, do the same yourself — read the archetype, substitute
  `{{PROJECT_NAME}}/{{STACK}}/{{BUILD_CMD}}/{{TEST_CMD}}/{{LINT_CMD}}/{{CONVENTIONS}}/{{RULES_PATHS}}`,
  keep the non-negotiable blocks verbatim, write to `.claude/agents/<domain>.md`.

## Post-apply verification (nothing forgotten — enforce, don't trust)

After applying, **verify every required slot actually exists on disk** — do not trust that the
apply step created them (LLM passes silently skip slots). Run a concrete existence check and
**create any missing slot before handing off**:

```
test -f CLAUDE.md
test -f .claude/settings.json
test -d .claude/agents && ls .claude/agents/*.md
test -f .claude/agent-memory/orchestrator/MEMORY.md
test -f .claude/agent-memory/reviewer/MEMORY.md
test -f .claude/agent-memory/critic/MEMORY.md
test -f .claude/agent-memory/agent-architect/MEMORY.md
test -f .agent-orchestra/verify.json
test -d .agent-orchestra/state            # gate.json + verified.json (transient, gitignored) — NOT plan.json
test -f docs/agent-orchestra/INDEX.md
test -f .claude/knowledge/index.md
test -f .claude/knowledge/README.md
```

**Also content-check the generated worker agents (enforce, don't trust agent-architect's self-report):**
the non-negotiable blocks must survive. The one block **every** archetype shares is `## Team protocol`,
so assert it on every generated agent (this is the reliable universal check):
```
grep -L "Team protocol" .claude/agents/*.md   # any file listed = a drifted agent → fix it
```
Then **spot-check the type-specific blocks** only on the agents that should carry them (these are NOT in
every archetype, so don't glob them or you'll false-flag correct files):
- impl agents (backend/frontend/devops): the **"temporary measures"** clause (case-insensitive) — that's
  the one impl marker present verbatim in **all three** impl archetypes (backend/frontend also say "swallowed
  errors", but devops's domain phrasing doesn't — so match on "temporary measures", not the paired phrase),
- the `test` agent: "write the tests FIRST",
- `frontend`: "Live browser verification".

If a generated agent dropped its block, regenerate/fix it before hand-off — same "enforce, not trust"
rule as slot existence.

Any slot that is intentionally N/A must have been declared so in the approved plan; everything
else must exist. Report the final list (created / N/A-with-reason) — a slot that is neither is a bug.

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
