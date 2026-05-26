#!/usr/bin/env python3
"""Stop hook for Agent Orchestra — the review/critic gate backstop.

Reads the gate sentinel that /agent-orchestra:run maintains and blocks the turn (exit 2)
only when status == "review-pending" — i.e. work was delivered but the reviewer and critic
have not signed off. It does NOT block while "in-progress" (so the lead can pause for the
user mid-work) or once "approved" or when no gate exists. This enforces the bias-correction
gate without trapping normal pauses. Fails open on any error.

Blocks at most ONCE per turn: it honors `stop_hook_active` (set by Claude Code when a Stop hook
already blocked and the turn is being continued). Without this, a lead legitimately waiting for
async reviewers gets every pause blocked, spamming the message until Claude's built-in cap force-
overrides it. We remind once, then let the lead proceed (it's a reminder, not a jail — the objective
verify-gate still independently re-runs the tests).
"""
import json
import os
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    # Already blocked once this turn → don't loop/spam; let the lead continue.
    if data.get("stop_hook_active"):
        sys.exit(0)

    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    gate_path = os.path.join(cwd, ".agent-orchestra", "state", "gate.json")

    try:
        with open(gate_path) as f:
            gate = json.load(f)
    except Exception:
        sys.exit(0)  # no/unreadable gate -> nothing to enforce

    if gate.get("status") == "review-pending":
        print(
            "[agent-orchestra] Review gate not passed: work was delivered but the reviewer "
            "and critic have not signed off. Complete the gate (reviewer APPROVE + critic "
            "NO BLOCKING CONCERNS), then set .agent-orchestra/state/gate.json status to "
            "'approved' before reporting done.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
