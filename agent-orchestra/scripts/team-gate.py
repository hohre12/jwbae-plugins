#!/usr/bin/env python3
"""Native Agent Teams gate for Agent Orchestra.

Handles two team-specific hook events, using the gate sentinel that the orchestrator
maintains at .agent-orchestra/state/gate.json:

- TeammateIdle: while the gate is `review-pending`, the reviewer/critic may NOT go idle
  (exit 2 keeps them working until they've signed off).
- TaskCompleted: while the gate is `review-pending`, a non-review teammate may NOT mark a
  task complete (exit 2) — work can't be closed before reviewer APPROVE + critic
  NO BLOCKING CONCERNS. Reviewer/critic completing their own review tasks is allowed.

This is the purpose-built, granular complement to the session-level Stop backstop. Fails
open on anything uncertain so it never traps a session.

NOTE: the exact JSON payload schema for TaskCompleted/TeammateIdle is not fully documented
(anthropics/claude-code#23545). `agent_type` is the documented agent-identifier field; we read it
defensively across a few plausible keys (see `teammate_identity`) so a schema variation can't silently
disable the gate. If you can capture a real payload, confirm the field name and tighten this.

Residual (accepted): if the real payload uses NONE of the known keys, identity is unknown ("") and the
TaskCompleted branch fails OPEN — a non-review worker could close a task while review-pending. We keep
fail-open here on purpose: failing CLOSED would also block a reviewer/critic (whose identity we likewise
couldn't read) from completing its own review task, wedging the gate. This escape is backstopped by the
Stop hooks — review-gate blocks reporting done and verify-gate re-runs the real checks — so un-reviewed or
red work still can't ship; only the team-level granular block is a no-op until the key is pinned (#23545).
"""
import json
import os
import sys


def is_review_agent(agent_type: str) -> bool:
    # Match the plugin's canonical review agents (reviewer, critic) + their delta spawns
    # (reviewer-d2, critic-d2, namespaced variants) — NOT a bare substring of "review", which
    # would mis-match a domain worker like "code-review-tooling".
    a = (agent_type or "").lower()
    return "reviewer" in a or "critic" in a


def teammate_identity(data: dict) -> str:
    # Extract the triggering teammate's TYPE name. `agent_type` is the documented field; fall back to
    # other plausible keys because the TaskCompleted/TeammateIdle payload schema is not fully documented
    # (#23545). Returning "" (unknown) makes the gate fail open below — never wedge on an unknown payload.
    for k in ("agent_type", "subagent_type", "agentType", "agent", "teammate", "teammate_name", "name"):
        v = data.get(k)
        if v:
            return str(v)
    return ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = data.get("hook_event_name", "")
    agent_type = teammate_identity(data)
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    gate_path = os.path.join(cwd, ".agent-orchestra", "state", "gate.json")

    try:
        with open(gate_path) as f:
            status = json.load(f).get("status", "")
    except Exception:
        sys.exit(0)  # no gate -> nothing to enforce

    if status != "review-pending":
        sys.exit(0)

    if event == "TeammateIdle":
        # Keep the reviewer/critic engaged until the gate clears.
        if is_review_agent(agent_type):
            print(
                "[agent-orchestra] Review gate is open: finish your review/critique and sign "
                "off (reviewer APPROVE / critic NO BLOCKING CONCERNS) before going idle.",
                file=sys.stderr,
            )
            sys.exit(2)
        sys.exit(0)

    if event == "TaskCompleted":
        # Don't let non-review work be closed while review is pending.
        if agent_type and not is_review_agent(agent_type):
            print(
                "[agent-orchestra] Review gate is open (review-pending): this task can't be "
                "completed until the reviewer returns APPROVE and the critic NO BLOCKING "
                "CONCERNS. Route findings back, fix, re-verify, then close.",
                file=sys.stderr,
            )
            sys.exit(2)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
