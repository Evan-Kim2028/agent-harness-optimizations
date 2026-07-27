#!/usr/bin/env python3
"""PreToolUse: during long manual streaks, strong spawn/parallel tip (non-blocking)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    AGENT_TOOLS,
    MANUAL_TOOLS,
    SPAWN_TIP,
    emit_allow,
    load_json,
    read_event,
    save_json,
    session_id,
    state_path,
    tool_name,
)

STREAK_THRESHOLD = 4
COOLDOWN = 3


def main() -> None:
    data = read_event()
    sid = session_id(data)
    name = tool_name(data)
    path = state_path("discovery-intercept", sid)
    state = load_json(
        path, {"manual_streak": 0, "intercept_count": 0, "agents_used": 0}
    )
    if not isinstance(state, dict):
        state = {"manual_streak": 0, "intercept_count": 0, "agents_used": 0}

    if name in AGENT_TOOLS:
        state["agents_used"] = int(state.get("agents_used", 0)) + 1
        state["manual_streak"] = 0
        save_json(path, state)
        emit_allow(sid=sid)
        return

    if name not in MANUAL_TOOLS:
        emit_allow(sid=sid)
        return

    state["manual_streak"] = int(state.get("manual_streak", 0)) + 1
    tip = None
    streak = state["manual_streak"]

    if streak >= STREAK_THRESHOLD:
        state["intercept_count"] = int(state.get("intercept_count", 0)) + 1
        ic = state["intercept_count"]
        if ic == 1 or ic % COOLDOWN == 0:
            tip = SPAWN_TIP

    save_json(path, state)
    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
