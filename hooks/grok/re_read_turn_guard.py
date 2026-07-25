#!/usr/bin/env python3
"""PostToolUse: warn on same-file re-read storms in a short window."""
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
)

THRESHOLD = 3


def main() -> None:
    data = read_event()
    if tool_name(data) != "read_file":
        sys.exit(0)

    sid = session_id(data)
    path_str = (
        tool_input(data).get("target_file")
        or tool_input(data).get("path")
        or ""
    )
    if not sid or not path_str:
        sys.exit(0)

    sp = state_path("turn-reads", sid)
    state = load_json(sp, {"recent": []})
    if not isinstance(state, dict):
        state = {"recent": []}
    recent = state.get("recent") or []
    if not isinstance(recent, list):
        recent = []
    recent.append(str(path_str))
    recent = recent[-20:]
    state["recent"] = recent
    save_json(sp, state)

    count = sum(1 for p in recent if p == path_str)
    if count == THRESHOLD:
        post_tip(
            sid,
            f"⚠️ TURN REREAD GUARD: read '{path_str}' {count} times recently. "
            "Cache findings in reasoning; use offset for sections only.",
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
