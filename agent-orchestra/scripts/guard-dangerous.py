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


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        dangerous = [
            (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "recursive force delete (rm -rf)"),
            (r"\bgit\s+push\b[^\n]*(--force\b|--force-with-lease|\s-f\b)", "git force push"),
            (r"\bchmod\s+(-R\s+)?0?777\b", "chmod 777"),
            (r"(curl|wget)\s+[^|]*\|\s*(sudo\s+)?(sh|bash|zsh)\b", "pipe-to-shell from the network"),
            (r"\bmkfs\.", "filesystem format (mkfs)"),
            (r"\bdd\b[^\n]*\bof=/dev/", "raw disk write (dd of=/dev/...)"),
            (r">\s*/dev/sd[a-z]", "write to raw disk device"),
            (r":\s*\(\)\s*\{\s*:\s*\|", "fork bomb"),
        ]
        for pat, desc in dangerous:
            if re.search(pat, cmd):
                block(f"{desc}: {cmd!r}")

    elif tool in ("Read", "Edit", "Write"):
        fp = ti.get("file_path", "") or ""
        base = os.path.basename(fp)
        if (base == ".env" or base.startswith(".env.")) and not base.endswith(".example"):
            block(f"access to secret file {fp!r}. Use environment variables / userConfig, not the .env file.")

    sys.exit(0)


if __name__ == "__main__":
    main()
