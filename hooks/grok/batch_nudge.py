#!/usr/bin/env python3
"""PostToolUse: detect 3+ sequential same-tool calls → queue batch tip."""
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
    tool_name,
)

WINDOW = 5

TIPS = {
    "read_file": (
        "TIP: 3+ sequential read_file. Batch multiple reads in one turn; "
        "grep first for line numbers, then targeted offset/limit."
    ),
    "grep": "TIP: 3+ sequential grep. Batch patterns in one turn.",
    "run_terminal_command": (
        "TIP: 3+ sequential Shell. Combine into one script, or use native "
        "read_file/grep/list_dir where possible."
    ),
    "spawn_subagent": (
        "TIP: 3+ sequential agents. Use background=true and dispatch in one turn; "
        "poll with get_command_or_subagent_output."
    ),
    "search_replace": (
        "TIP: 3+ sequential search_replace. Multi-hunk → one careful edit path; "
        "multi-file → parallel subagents when independent."
    ),
}


def main() -> None:
    data = read_event()
    sid = session_id(data)
    name = tool_name(data)
    if not sid or not name:
        sys.exit(0)

    path = state_path("batch-tracker", sid)
    window = load_json(path, [])
    if not isinstance(window, list):
        window = []
    window.append({"tool": name})
    window = window[-WINDOW:]
    save_json(path, window)

    recent = [w.get("tool") for w in window[-3:] if isinstance(w, dict)]
    if len(recent) < 3 or len(set(recent)) != 1:
        sys.exit(0)

    tip = TIPS.get(name)
    if tip:
        post_tip(sid, tip)
    sys.exit(0)


if __name__ == "__main__":
    main()
