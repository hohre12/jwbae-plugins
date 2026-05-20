---
name: briefing
description: Brief the user on their assigned, unresolved Redmine issues, then start work on a selected issue or take a free-form request. Use at the start of a workday or when checking assigned tickets.
disable-model-invocation: true
argument-hint: "[optional filter, e.g. project or priority]"
---

# /agent-orchestra:briefing — assigned Redmine issues

Brief the user on their open Redmine work, then route into orchestration.

## Precondition
A Redmine MCP server must be configured (in `.mcp.json` via `/agent-orchestra:init`, or
`claude mcp add`). If no Redmine MCP tools are available this session, tell the user how to
add one and stop — do not fabricate issues.

## Procedure

1. **Fetch assigned, unresolved issues** via the Redmine MCP. Tool names vary by server;
   the common one is `list_redmine_issues` with the current user as assignee and an open
   status — e.g. `assignee_id` / `assigned_to_id` = `"me"`, `status_id` = open. Use whatever
   the configured server exposes; if "me" isn't supported, resolve the current user first.
   Apply `$ARGUMENTS` as an extra filter if given (project, priority, etc.).

2. **Brief concisely.** List each issue as: `#id  [priority]  subject  (status, due)`.
   Sort by priority then due date. Keep it scannable; summarize if there are many.

3. **Route.** Ask the user to either:
   - pick an issue number → fetch its full description and start `/agent-orchestra:run` with
     that issue as the request context (include the issue id so updates can link back), or
   - give a free-form request instead.

4. **On completion** (after the orchestrated work passes its gate and is reported): offer to
   update the Redmine issue via the MCP — set status and add a comment summarizing what was
   done. Only do this with the user's confirmation.

## Notes
- Read-only briefing is safe to run anytime; writes (status/comment) require confirmation.
- To auto-brief at session start, add a `SessionStart` hook that invokes this skill — opt-in,
  since it requires Redmine configured and network access (not wired by default).
