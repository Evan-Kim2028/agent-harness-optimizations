#!/usr/bin/env python3
"""PreToolUse: block search_replace when old_string is missing from the file."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    emit_allow,
    emit_deny,
    read_event,
    resolve_path,
    session_id,
    tool_input,
    tool_name,
)


def main() -> None:
    data = read_event()
    if tool_name(data) != "search_replace":
        emit_allow(sid=session_id(data))
        return

    inp = tool_input(data)
    path = inp.get("file_path") or inp.get("path") or ""
    old = inp.get("old_string") or inp.get("old") or ""
    if not path or not old:
        emit_allow(sid=session_id(data))
        return

    resolved = resolve_path(str(path), data)
    try:
        content = resolved.read_text(encoding="utf-8")
    except Exception:
        emit_allow(sid=session_id(data))  # fail open
        return

    if old not in content:
        emit_deny(
            f"search_replace would fail: old_string not found in {path}. "
            "Re-read the file (read_file) for exact current text. "
            "Common causes: whitespace drift, prior edit, or stale memory."
        )
        return

    emit_allow(sid=session_id(data))


if __name__ == "__main__":
    main()
