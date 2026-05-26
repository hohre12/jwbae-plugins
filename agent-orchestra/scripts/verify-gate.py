#!/usr/bin/env python3
"""Objective gate for Agent Orchestra — runs the project's REAL checks (facts, not opinion).

On Stop, if the gate sentinel claims work is delivered/approved (status `review-pending` or
`approved`), this re-runs the project's own verify commands from `.agent-orchestra/verify.json`
and BLOCKS (exit 2) if any fail. This anchors the gate in machine-checked facts (test/lint/build/e2e
exit codes) instead of the LLM's self-reported sentinel — the orchestrator cannot mark work
"approved" past failing tests, because this hook re-runs them independently.

Fails open (exit 0) only when there is nothing to verify (no verify.json) — never fakes a pass.
"""
import json
import os
import subprocess
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # Only verify when the work is being claimed done — don't run the suite on every pause.
    try:
        with open(os.path.join(cwd, ".agent-orchestra", "state", "gate.json")) as f:
            status = json.load(f).get("status", "")
    except Exception:
        sys.exit(0)
    if status not in ("review-pending", "approved"):
        sys.exit(0)

    try:
        with open(os.path.join(cwd, ".agent-orchestra", "verify.json")) as f:
            verify = json.load(f)
    except Exception:
        sys.exit(0)  # nothing configured to verify -> can't check, don't fake a pass

    checks = [(k, verify[k]) for k in ("test", "lint", "build", "e2e") if verify.get(k)]
    failures = []
    for name, cmd in checks:
        try:
            r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=600)
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
    sys.exit(0)


if __name__ == "__main__":
    main()
