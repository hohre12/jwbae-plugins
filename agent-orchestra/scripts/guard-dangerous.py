#!/usr/bin/env python3
"""PreToolUse guard for Agent Orchestra.

Blocks a small set of unambiguously dangerous actions by exiting 2 (which Claude Code
treats as a blocking error and feeds the stderr message back to the model). Fails open
on any parse error so it can never wedge a session.
"""
import json
import os
import re
import sys


def block(msg: str) -> None:
    print(f"[agent-orchestra] BLOCKED: {msg}", file=sys.stderr)
    sys.exit(2)


def rm_recursive_force(cmd: str) -> bool:
    """True if any segment runs `rm` with BOTH a recursive and a force flag, in any spelling/order
    (-rf, -fr, -r -f, -R -f, --recursive --force). Plain `rm -r dir/` (no force) and `rm --force file`
    (no recursive) are NOT flagged — only the catastrophic unattended combo. Best-effort backstop."""
    for seg in re.split(r"[;&|\n]", cmd):
        if not re.search(r"\brm\b", seg):
            continue
        # `git rm --cached` is an index-only removal (keeps files on disk) — not a destructive recursive
        # disk delete; don't flag it. (`git rm -rf` WITHOUT --cached DOES delete from disk → still flagged.)
        if re.search(r"\bgit\s+rm\b", seg) and "--cached" in seg:
            continue
        longs = set(re.findall(r"--([a-zA-Z]+)", seg))
        short_letters = "".join(re.findall(r"(?<![\w-])-([a-zA-Z]+)\b", seg))
        recursive = ("recursive" in longs) or ("r" in short_letters) or ("R" in short_letters)
        force = ("force" in longs) or ("f" in short_letters)
        if recursive and force:
            return True
    return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        if rm_recursive_force(cmd):
            block(f"recursive force delete (rm -r -f): {cmd!r}")
        dangerous = [
            (r"\bgit\s+push\b[^\n]*(--force\b|--force-with-lease|\s-f\b)", "git force push"),
            (r"\bgit\s+reset\b[^\n]*--hard\b", "git reset --hard (discards uncommitted work)"),
            (r"\bgit\s+clean\b[^\n]*(?:\s-[a-zA-Z]*f|--force)", "git clean -f (deletes untracked files)"),
            (r"\bchmod\s+(-R\s+)?0?777\b", "chmod 777"),
            (r"(curl|wget)\s+[^|]*\|\s*(sudo\s+)?(sh|bash|zsh)\b", "pipe-to-shell from the network"),
            (r"\bmkfs\.", "filesystem format (mkfs)"),
            (r"\bdd\b[^\n]*\bof=/dev/", "raw disk write (dd of=/dev/...)"),
            (r">\s*/dev/sd[a-z]", "write to raw disk device"),
            (r":\s*\(\)\s*\{\s*:\s*\|", "fork bomb"),
            (r"\b(cat|less|more|head|tail|nl|xxd|od|bat|strings)\s+[^|;&]*\.env\b(?!\.example)",
             "read of secret .env file via shell"),
        ]
        for pat, desc in dangerous:
            if re.search(pat, cmd):
                block(f"{desc}: {cmd!r}")

    elif tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        fp = ti.get("file_path", "") or ti.get("notebook_path", "") or ""
        base = os.path.basename(fp)
        if (base == ".env" or base.startswith(".env.")) and not base.endswith(".example"):
            block(f"access to secret file {fp!r}. Use environment variables / userConfig, not the .env file.")

    sys.exit(0)


if __name__ == "__main__":
    main()
