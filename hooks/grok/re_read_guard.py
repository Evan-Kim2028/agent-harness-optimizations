#!/usr/bin/env python3
"""PreToolUse: warn when re-reading an unchanged file section."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    emit_allow,
    load_json,
    read_event,
    resolve_path,
    save_json,
    session_id,
    state_path,
    tool_input,
    tool_name,
)


def main() -> None:
    data = read_event()
    sid = session_id(data)
    if tool_name(data) != "read_file":
        emit_allow(sid=sid)
        return

    inp = tool_input(data)
    path_str = inp.get("target_file") or inp.get("path") or inp.get("file_path") or ""
    if not path_str:
        emit_allow(sid=sid)
        return

    offset = inp.get("offset")
    limit = inp.get("limit") or inp.get("n_lines")
    # kimi line_offset alias
    if offset is None:
        offset = inp.get("line_offset")

    resolved = resolve_path(str(path_str), data)
    try:
        st = resolved.stat()
        mtime, size = st.st_mtime, st.st_size
        key = str(resolved.resolve())
    except OSError:
        emit_allow(sid=sid)
        return

    path = state_path("file-reads", sid)
    state = load_json(path, {})
    if not isinstance(state, dict):
        state = {}

    tip = None
    prev = state.get(key)
    if isinstance(prev, dict):
        same_file = abs(mtime - prev.get("mtime", 0)) < 0.001 and size == prev.get(
            "size", -1
        )
        same_section = prev.get("offset") == offset and prev.get("limit") == limit
        if same_file and same_section:
            tip = (
                f"⚠️ CONTEXT GUARD: already read '{path_str}' this session "
                f"(offset={offset or 'start'}, limit={limit or 'default'}) and file unchanged. "
                f"Re-read wastes ~{max(1, size // 4):,} tokens. Use a different offset or skip."
            )

    state[key] = {"mtime": mtime, "size": size, "offset": offset, "limit": limit}
    # bound state growth
    if len(state) > 200:
        for k in list(state.keys())[:50]:
            del state[k]
    save_json(path, state)
    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
