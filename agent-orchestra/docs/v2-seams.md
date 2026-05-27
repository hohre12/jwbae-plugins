# v2 interface seams (fixed in v1, implemented in v2)

These contracts are **fixed now** so v2 features plug in without touching the orchestrator.
v1 does not implement the v2 backends; it only commits to the call shapes below. No stub MCP
server ships in v1 (a non-functional server would be worse than none).

## Seam 1 — `critic.review` (heterogeneous critic)

**Contract**
```
critic.review(target, context) -> findings
  target:  what to scrutinize (diff, files, task, plan)
  context: project conventions + the request + relevant memory
  findings: blocking concerns + proposals, ending with
            "CONCERNS: <n blocking, m proposals>" or "NO BLOCKING CONCERNS"
```

- **v1 implementation:** the native `critic` agent (teammate). Output format already matches
  this contract (see `agents/critic.md`). The orchestrator (`/agent-orchestra:run`) depends on
  the *contract*, not on the critic being a Claude agent.
- **v2 swap:** wrap a different-vendor model (e.g. GPT) as an MCP tool exposing the same
  `critic.review` shape, and point the orchestrator at it instead of the native critic.
  Rationale: an adversarial critic benefits from being stateless and uncorrelated with the
  builder model (breaks shared blind spots). Reviewer stays native (it benefits from
  accumulated `memory: project`).
- **No orchestrator change required** — only which implementation backs the contract changes.

## Seam 2 — `investigate_incident` (server-resident diagnosis)

**Contract**
```
investigate_incident(service, symptom) -> diagnosis
  service:   which deployed service
  symptom:   observed problem (error, latency, alert)
  diagnosis: root-cause analysis + evidence + suggested fix
```

- **v1 implementation:** none (not wired). The orchestrator does not call this yet.
- **v2 swap:** a Claude Code agent resident on the deployment server, exposed as an MCP tool
  with this shape (with read-only access to logs/metrics/DB). The local orchestrator calls it
  as a tool to diagnose production issues — agent-to-agent across machines, with a clean
  permission boundary.
- Pairs naturally with the existing Supabase MCP (`get_logs`, `get_advisors`) for first-pass
  triage before reaching for the remote agent.

## Why fix these now

Recording the call shapes in v1 means v2 is additive: drop in an MCP server that satisfies the
contract and re-point one call site. It avoids reshaping the orchestrator later, consistent with
"do it right the first time" (principle 4). See `DESIGN.md` §10.1, §12.
