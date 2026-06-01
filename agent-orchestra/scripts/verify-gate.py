#!/usr/bin/env python3
"""Objective gate for Agent Orchestra — runs the project's REAL checks (facts, not opinion).

On Stop, when the gate sentinel claims work is delivered (`review-pending`) or approved (`approved`),
this re-runs the project's own verify commands from `.agent-orchestra/verify.json` and BLOCKS (exit 2)
if any fail. This anchors the gate in machine-checked facts (test/lint/build/e2e exit codes), not the
LLM's self-reported sentinel — the orchestrator cannot mark work done past failing tests, because the
hook re-runs them independently.

Idempotency is keyed on the **working-tree state** (git HEAD + status + diff + untracked files), NOT on
gate.json: once the suite passes, a marker records that signature and later Stops skip re-running until
the **code actually changes**. This is correct for BOTH `review-pending` and `approved` — a worker's fix
changes the signature and forces a fresh run, while merely pausing to wait for reviewers (no code change)
does NOT re-run the whole suite. (The previous gate.json-keyed marker couldn't memoize `review-pending`,
because a code fix didn't change gate.json; the working-tree key fixes that without risking a stale green.)
Non-git tree → no signature → always re-verify (safe degrade: correctness over speed). `shutdown` removes
the gate file + marker, so nothing fires after cleanup.

Per-check timeouts come from verify.json (`"timeouts": {check: secs}` or `"timeout": secs`, default 250),
bounded by a total budget kept under the hook's own timeout so a slow suite can't get the hook killed
(which would fail-open). A check that can't run within budget is reported as a failure, never silently skipped.

Exit-0 (no block) paths: malformed stdin; `stop_hook_active` (already verified once this turn, so a
continued turn isn't re-run — note this skips even a failing suite on the continuation, by design);
no gate / status not in (review-pending, approved); no verify.json (nothing to check); signature unchanged
since the last green (memoized); or all checks pass. It NEVER exits 0 on a failing check on a fresh
first-Stop — it never fakes a pass.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

DEFAULT_CHECK_TIMEOUT = 250   # seconds per check unless verify.json overrides
TOTAL_BUDGET = 1700           # seconds for signature + all checks combined; < hooks.json timeout (1800)


def working_tree_signature(cwd):
    """Signature of the current code state, so the suite re-runs exactly when the code changed (not on
    every idle pause). Git-aware: HEAD + porcelain status + diff-vs-HEAD + untracked files (size+mtime).
    Returns None when cwd isn't a git work tree — callers then never memoize (always re-verify), the safe
    degrade for non-git projects. Reads only; never mutates the repo (no `git add`/stash)."""
    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd, capture_output=True, text=True, timeout=10,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return None
        h = hashlib.sha256()
        # Exclude the tool's OWN output dir (reports/reviews/critiques/plans/index) — it is never
        # code-under-test, so a reviewer writing review.md or run writing report.md must NOT invalidate
        # the verified signature. Code (src/tests/…) and .agent-orchestra/verify.json (the check config)
        # stay in the signature. (.agent-orchestra/state/ is gitignored, so it's already excluded.)
        # Exclude the tool's OWN dirs: docs/agent-orchestra (reports/reviews/critiques/plans/index — never
        # code-under-test) and .agent-orchestra/state (gate.json + this very marker — excluded by gitignore
        # in well-set-up projects, but excluded HERE too so memoization works even if a project forgot to
        # gitignore state/; otherwise the marker write would itself churn the signature). Code (src/tests/…)
        # and .agent-orchestra/verify.json (the check config) stay in the signature.
        scope = ["--", ".", ":(exclude)docs/agent-orchestra", ":(exclude).agent-orchestra/state"]
        h.update(subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd,
                                 capture_output=True, text=True, timeout=20).stdout.encode())
        h.update(b"\0")
        for args in (["git", "status", "--porcelain"] + scope,
                     ["git", "diff", "HEAD", "--no-color"] + scope):
            r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
            h.update(("\0".join(args)).encode())
            h.update(b"\0")
            h.update(r.stdout.encode("utf-8", "replace"))
            h.update(b"\0")
        # Untracked (but not gitignored) files: diff-vs-HEAD doesn't capture their content. Hash
        # name+size+mtime (cheap, and changes when the file is rewritten) rather than reading bytes.
        others = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"] + scope,
            cwd=cwd, capture_output=True, text=True, timeout=30,
        )
        for rel in others.stdout.splitlines():
            rel = rel.strip()
            if not rel:
                continue
            h.update(rel.encode("utf-8", "replace"))
            try:
                st = os.stat(os.path.join(cwd, rel))
                h.update(f":{st.st_size}:{st.st_mtime_ns}".encode())
            except OSError:
                pass
            h.update(b"\0")
        return h.hexdigest()
    except Exception:
        return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Already blocked once this turn → don't loop. Also avoids re-running the suite while Claude retries
    # the Stop (it caps and force-overrides anyway). We verify at most once per turn.
    if data.get("stop_hook_active"):
        sys.exit(0)

    # Budget clock starts HERE (before the signature) so signature time counts against TOTAL_BUDGET and
    # the whole hook (signature + checks) stays under the hooks.json timeout.
    start = time.monotonic()

    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    ao = os.path.join(cwd, ".agent-orchestra")
    state_dir = os.path.join(ao, "state")

    # Only verify when the work is being claimed done — don't run the suite on every pause.
    try:
        with open(os.path.join(state_dir, "gate.json")) as f:
            status = json.load(f).get("status", "")
    except Exception:
        sys.exit(0)
    if status not in ("review-pending", "approved"):
        sys.exit(0)

    try:
        with open(os.path.join(ao, "verify.json")) as f:
            verify = json.load(f)
    except Exception:
        sys.exit(0)  # nothing configured to verify -> can't check, don't fake a pass

    # Idempotency keyed on the WORKING-TREE state (see module docstring): skip only when the code is
    # byte-for-byte what we last verified green. Safe for review-pending AND approved; a real fix changes
    # the signature and forces a fresh run. Non-git → sig None → never skip (always re-verify).
    sig = working_tree_signature(cwd)
    marker_path = os.path.join(state_dir, "verified.json")
    if sig is not None:
        try:
            with open(marker_path) as f:
                if json.load(f).get("sig") == sig:
                    sys.exit(0)
        except Exception:
            pass

    timeouts = verify.get("timeouts") or {}
    try:
        default_to = int(verify.get("timeout", DEFAULT_CHECK_TIMEOUT))
    except (TypeError, ValueError):
        default_to = DEFAULT_CHECK_TIMEOUT

    checks = [(k, verify[k]) for k in ("test", "lint", "build", "e2e") if verify.get(k)]
    failures = []
    for name, cmd in checks:
        remaining = TOTAL_BUDGET - (time.monotonic() - start)
        if remaining <= 1:
            failures.append(f"- {name} (`{cmd}`): not run — time budget exhausted before this check")
            continue
        try:
            per = int(timeouts.get(name, default_to))
        except (TypeError, ValueError):
            per = default_to
        per = max(1, min(per, int(remaining)))
        try:
            r = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=per
            )
        except subprocess.TimeoutExpired:
            failures.append(
                f"- {name} (`{cmd}`): TIMED OUT after {per}s "
                f"(raise the per-check budget via verify.json \"timeouts\")"
            )
            continue
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

    # Green: record the verified working-tree signature so we don't re-run until the code changes again.
    if sig is not None:
        try:
            os.makedirs(state_dir, exist_ok=True)
            with open(marker_path, "w") as f:
                json.dump({"sig": sig, "status": status}, f)
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
