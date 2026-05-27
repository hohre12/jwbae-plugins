#!/usr/bin/env python3
"""Objective gate for Agent Orchestra — runs the project's REAL checks (facts, not opinion).

On Stop, if the gate sentinel claims work is delivered (status `review-pending`) or just approved
(status `approved`), this re-runs the project's own verify commands from `.agent-orchestra/verify.json`
and BLOCKS (exit 2) if any fail. This anchors the gate in machine-checked facts (test/lint/build/e2e
exit codes) instead of the LLM's self-reported sentinel — the orchestrator cannot mark work
"approved" past failing tests, because this hook re-runs them independently.

Idempotent on `approved`: once an `approved` gate state has been verified green, this records a
marker and SKIPS on subsequent Stops for that same gate state — so a finished run does NOT re-run
the whole suite on every later pause/turn. A `review-pending` delivery is always re-verified (it is
the active gate moment). `shutdown` removes the gate file entirely, so nothing fires after cleanup.

Fails open (exit 0) only when there is nothing to verify (no verify.json) — never fakes a pass.
"""
import hashlib
import json
import os
import subprocess
import sys

PER_CHECK_TIMEOUT = 300  # seconds per check; keep the sum under the hook's timeout in hooks.json


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Already blocked once this turn → don't loop. Also avoids re-running the whole suite N times
    # while Claude retries the Stop (it caps and force-overrides anyway). We verify once per turn.
    if data.get("stop_hook_active"):
        sys.exit(0)

    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    state_dir = os.path.join(cwd, ".agent-orchestra", "state")

    # Only verify when the work is being claimed done — don't run the suite on every pause.
    try:
        with open(os.path.join(state_dir, "gate.json")) as f:
            gate_raw = f.read()
        status = json.loads(gate_raw).get("status", "")
    except Exception:
        sys.exit(0)
    if status not in ("review-pending", "approved"):
        sys.exit(0)

    # Idempotency: skip re-running an already-verified `approved` state (finished run, idle turns).
    sig = hashlib.sha256(gate_raw.encode("utf-8")).hexdigest()
    marker_path = os.path.join(state_dir, "verified.json")
    if status == "approved":
        try:
            with open(marker_path) as f:
                if json.load(f).get("sig") == sig:
                    sys.exit(0)
        except Exception:
            pass

    try:
        with open(os.path.join(cwd, ".agent-orchestra", "verify.json")) as f:
            verify = json.load(f)
    except Exception:
        sys.exit(0)  # nothing configured to verify -> can't check, don't fake a pass

    checks = [(k, verify[k]) for k in ("test", "lint", "build", "e2e") if verify.get(k)]
    failures = []
    for name, cmd in checks:
        try:
            r = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=PER_CHECK_TIMEOUT
            )
        except Exception as e:
            failures.append(f"- {name} (`{cmd}`): could not run — {e}")
            continue
        if r.returncode != 0:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
            failures.append(f"- {name} (`{cmd}`) FAILED (exit {r.returncode}):\n{tail}")

    if failures:
        print(
            "[agent-orchestra] OBJECTIVE GATE FAILED — these must pass before reporting done "
            "(reviewer APPROVE alone is not enough):\n\n" + "\n\n".join(failures),
            file=sys.stderr,
        )
        sys.exit(2)

    # Green: record the verified signature so an idle `approved` state isn't re-run next Stop.
    if status == "approved":
        try:
            os.makedirs(state_dir, exist_ok=True)
            with open(marker_path, "w") as f:
                json.dump({"sig": sig}, f)
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
