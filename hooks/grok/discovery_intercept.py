#!/usr/bin/env python3
"""PreToolUse: during long manual streaks, coach toward subagents (non-blocking)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    AGENT_TOOLS,
    MANUAL_TOOLS,
    emit_allow,
    load_json,
    read_event,
    save_json,
    session_id,
    state_path,
    tool_input,
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
            inp = tool_input(data)
            if name == "read_file":
                p = inp.get("target_file") or inp.get("path") or ""
                tip = (
                    f"INTERCEPT: about to read_file '{p}' during a {streak}-call manual streak. "
                    "For multi-file work, spawn parallel explore/general-purpose subagents "
                    "(background=true) instead of grinding."
                )
            elif name == "grep":
                pat = str(inp.get("pattern", ""))[:40]
                tip = (
                    f"INTERCEPT: grep '{pat}…' during a {streak}-call manual streak. "
                    "Multi-concern research → parallel spawn_subagent explore agents."
                )
            elif name == "run_terminal_command":
                cmd = str(inp.get("command", ""))[:60]
                tip = (
                    f"INTERCEPT: shell '{cmd}…' during a {streak}-call manual streak. "
                    "Complex multi-step work often parallelizes via subagents."
                )
            else:
                tip = (
                    f"INTERCEPT: {streak}-call manual streak. "
                    "Delegate multi-file discovery to parallel subagents."
                )

    save_json(path, state)
    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
