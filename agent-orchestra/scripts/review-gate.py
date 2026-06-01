#!/usr/bin/env python3
"""Stop hook for Agent Orchestra — the review/critic gate backstop.

Reads the gate sentinel that /agent-orchestra:run maintains and blocks the turn (exit 2) when:
- status == "review-pending" — work was delivered but the reviewer/critic haven't signed off; or
- status == "approved" but the reviewer/critic sign-off fields are missing — you can't mark work
  approved without recording that review actually happened. The hook enforces *that the sign-off was
  recorded*, not the reviewer's judgment itself (the independent reviewer/critic teammates, held by
  TeammateIdle/TaskCompleted, are what make the judgment real).
It does NOT block while "in-progress" (so the lead can pause mid-work), once "approved" WITH the
verdicts recorded, or when no gate exists. Enforces the bias-correction gate without trapping normal
pauses. Fails open on any error.

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

    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    gate_path = os.path.join(cwd, ".agent-orchestra", "state", "gate.json")

    try:
        with open(gate_path) as f:
            gate = json.load(f)
    except Exception:
        sys.exit(0)  # no/unreadable gate -> nothing to enforce

    status = gate.get("status")

    if status == "review-pending":
        print(
            "[agent-orchestra] Review gate not passed: work was delivered but the reviewer "
            "and critic have not signed off. Complete the gate (reviewer APPROVE + critic "
            "NO BLOCKING CONCERNS), then set .agent-orchestra/state/gate.json status to "
            "'approved' (recording the reviewer/critic verdicts) before reporting done.",
            file=sys.stderr,
        )
        sys.exit(2)

    if status == "approved":
        # Can't reach `approved` without recording the sign-offs the reviewer/critic actually gave.
        reviewer = (gate.get("reviewer") or "").upper()
        critic = (gate.get("critic") or "").upper()
        # "APPROVE" must be present AND not negated — otherwise "NOT APPROVED"/"DISAPPROVE" would slip the
        # substring check. (The documented negative is "CHANGES REQUIRED", which has no "APPROVE" anyway.)
        reviewer_ok = (
            "APPROVE" in reviewer
            and "NOT APPROVE" not in reviewer
            and "DISAPPROVE" not in reviewer
            and "CHANGES REQUIRED" not in reviewer
        )
        critic_ok = "NO BLOCKING" in critic
        if not reviewer_ok or not critic_ok:
            print(
                "[agent-orchestra] Gate is 'approved' but the reviewer/critic sign-offs are not "
                "recorded in .agent-orchestra/state/gate.json — you cannot approve un-reviewed work. "
                "After the reviewer returns APPROVE and the critic NO BLOCKING CONCERNS, record them in "
                'the "reviewer" and "critic" fields, then report done.',
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
