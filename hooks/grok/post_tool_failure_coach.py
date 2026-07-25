#!/usr/bin/env python3
"""PostToolUseFailure: coach recovery on failed edits / shell / reads."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    load_json,
    post_tip,
    read_event,
    save_json,
    session_id,
    state_path,
    tool_input,
    tool_name,
    tool_result,
)


def main() -> None:
    data = read_event()
    sid = session_id(data)
    name = tool_name(data)
    if not sid or not name:
        sys.exit(0)

    path = state_path("failure-coach", sid)
    state = load_json(path, {"tips": 0})
    if not isinstance(state, dict):
        state = {"tips": 0}
    if int(state.get("tips", 0)) >= 8:
        sys.exit(0)

    err = str(tool_result(data) or g_err(data))[:400]
    tip = None
    inp = tool_input(data)

    if name == "search_replace":
        fp = inp.get("file_path") or inp.get("path") or "<file>"
        tip = (
            f"FAILURE COACH: search_replace failed on {fp}. "
            "Re-read the file with read_file, copy exact old_string (whitespace), "
            "or use a smaller unique hunk. Do not retry the same stale string."
        )
    elif name == "run_terminal_command":
        tip = (
            "FAILURE COACH: Shell command failed. Read the error, fix the command "
            "(paths, flags, cwd). Prefer absolute paths over cd. Don't re-run blindly."
        )
    elif name == "read_file":
        tip = (
            "FAILURE COACH: read_file failed. Check path exists (list_dir / absolute path). "
            "Don't invent paths from memory."
        )
    elif name == "write":
        tip = (
            "FAILURE COACH: write failed. Ensure parent dir exists; check permissions."
        )
    elif name == "spawn_subagent":
        tip = (
            "FAILURE COACH: subagent spawn failed. Check subagent_type and prompt size; "
            "retry with a tighter prompt if needed."
        )
    else:
        tip = (
            f"FAILURE COACH: {name} failed. Inspect the error, adjust inputs, "
            "don't loop the identical call."
        )

    if tip:
        if err and len(err) < 200:
            tip = f"{tip} Error snippet: {err}"
        post_tip(sid, tip)
        state["tips"] = int(state.get("tips", 0)) + 1
        save_json(path, state)
    sys.exit(0)


def g_err(data: dict) -> str:
    for k in ("error", "errorDetails", "error_message", "message"):
        if data.get(k):
            return str(data[k])
    return ""


if __name__ == "__main__":
    main()
