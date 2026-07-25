#!/usr/bin/env python3
"""PreToolUse: nudge targeted reads on large files without offset/limit."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    emit_allow,
    read_event,
    resolve_path,
    session_id,
    tool_input,
    tool_name,
)

LARGE_LINES = 250


def main() -> None:
    data = read_event()
    sid = session_id(data)
    if tool_name(data) != "read_file":
        emit_allow(sid=sid)
        return

    inp = tool_input(data)
    path_str = inp.get("target_file") or inp.get("path") or ""
    if not path_str:
        emit_allow(sid=sid)
        return

    # Already targeted
    if inp.get("offset") is not None or inp.get("line_offset") is not None:
        emit_allow(sid=sid)
        return
    if inp.get("limit") is not None or inp.get("n_lines") is not None:
        emit_allow(sid=sid)
        return

    resolved = resolve_path(str(path_str), data)
    if not resolved.is_file():
        emit_allow(sid=sid)
        return

    try:
        r = subprocess.run(
            ["wc", "-l", str(resolved)],
            capture_output=True,
            text=True,
            timeout=1.5,
        )
        n = int(r.stdout.strip().split()[0]) if r.returncode == 0 else 0
    except Exception:
        emit_allow(sid=sid)
        return

    tip = None
    if n > LARGE_LINES:
        tip = (
            f"⚠️ CONTEXT GUARD: '{path_str}' is ~{n} lines. "
            f"Prefer grep for the symbol, then read_file(offset=..., limit=80). "
            f"Full-file reads burn context."
        )
    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
