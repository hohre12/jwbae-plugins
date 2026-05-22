# templates/

Non-standard helper directory (not auto-discovered). `/agent-orchestra:init` reads these
via `${CLAUDE_PLUGIN_ROOT}/templates/` to scaffold a project's `.claude/`.

Scaffolding templates filled in **Task #2**: `CLAUDE.md.tmpl`, `rules/*.tmpl`, `mcp.json.tmpl`.

## `archetypes/` — worker agent templates

Six worker archetypes (`backend`, `frontend`, `test`, `explorer`, `architect`, `devops`).
`/agent-orchestra:init` reads these, fills the placeholders below from project triage, and
writes the result into the project's `.claude/agents/` as real worker definitions.

They live here (not in the plugin's `agents/`) because they contain `{{placeholders}}` and
must not be auto-loaded as live agents.

### Placeholder vocabulary (substituted by init)

| Placeholder | Meaning |
| --- | --- |
| `{{PROJECT_NAME}}` | The project's name |
| `{{STACK}}` | Tech stack summary (languages, frameworks, key libs) |
| `{{BUILD_CMD}}` | Build command |
| `{{TEST_CMD}}` | Test command |
| `{{LINT_CMD}}` | Lint/format command |
| `{{CONVENTIONS}}` | One-line summary of key project conventions |
| `{{RULES_PATHS}}` | Which `.claude/rules/*.md` apply to this role |
| `{{OUTPUT_DIR}}` | Project output dir for generated docs (default `docs/agent-orchestra`) — used by architect/CLAUDE.md |

See `DESIGN.md` §2.2, §2.3, §2.7.

## `mcp.json.tmpl` — MCP servers

`init` fills the Redmine/Supabase entries from the user's setup. Redmine MCP servers vary:

- **stdio server**: fill `{{REDMINE_MCP_COMMAND}}` / `{{REDMINE_MCP_ARGS}}` (e.g. `"uvx"` /
  `["some-redmine-mcp"]`) and keep `env` for `REDMINE_URL` + `${REDMINE_API_KEY}`.
- **http server** (e.g. PyPI `redmine-mcp-server` on `:8000`): replace the entry with
  `{ "type": "http", "url": "http://127.0.0.1:8000/mcp" }` instead of command/args.

Secrets stay as `${ENV_VAR}` references (e.g. `${REDMINE_API_KEY}`, `${SUPABASE_ACCESS_TOKEN}`) —
never inline. The `/agent-orchestra:briefing` skill is written tool-agnostically, so it adapts
to whichever Redmine MCP tool names the chosen server exposes.
