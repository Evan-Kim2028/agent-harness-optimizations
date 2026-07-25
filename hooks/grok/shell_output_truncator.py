#!/usr/bin/env python3
"""PreToolUse: warn on Shell commands likely to dump unbounded output."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_allow, read_event, session_id, tool_input, tool_name  # noqa: E402


def main() -> None:
    data = read_event()
    sid = session_id(data)
    if tool_name(data) != "run_terminal_command":
        emit_allow(sid=sid)
        return

    cmd = tool_input(data).get("command") or ""
    if not isinstance(cmd, str):
        emit_allow(sid=sid)
        return

    warnings: list[str] = []

    if re.search(r"\bgit\s+log\b", cmd) and not re.search(
        r"-\d+|--max-count|--oneline|-n\s+\d+", cmd
    ):
        warnings.append("git log: add --oneline -n 20 (or -n N)")

    if re.search(r"\bdocker\s+logs?\b", cmd) and not re.search(r"--tail\b|-n\s+\d+", cmd):
        warnings.append("docker logs: add --tail 50")

    if re.search(r"\bfind\b", cmd) and not re.search(r"-maxdepth\b", cmd):
        warnings.append("find: add -maxdepth N to avoid huge trees")

    if re.search(r"\b(journalctl|dmesg)\b", cmd) and not re.search(
        r"-n\s+\d+|--lines|head|tail", cmd
    ):
        warnings.append("logs dump: bound with -n / head / tail")

    if re.search(r"\bls\s+.*-R\b|\bls\s+.*--recursive", cmd):
        warnings.append("ls -R: prefer list_dir / find with maxdepth")

    if re.search(r"\bkubectl\s+logs?\b", cmd) and not re.search(r"--tail\b", cmd):
        warnings.append("kubectl logs: add --tail 50")

    tip = None
    if warnings:
        tip = "⚠️ OUTPUT GUARD: " + "; ".join(warnings) + ". Unbounded output burns context."

    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
