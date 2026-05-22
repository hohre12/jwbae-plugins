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
"""
import json
import os
import sys


def is_review_agent(agent_type: str) -> bool:
    a = (agent_type or "").lower()
    return "review" in a or "critic" in a


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    event = data.get("hook_event_name", "")
    agent_type = data.get("agent_type", "")
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
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
