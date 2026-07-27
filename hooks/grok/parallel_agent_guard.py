#!/usr/bin/env python3
"""PreToolUse: nudge parallel background spawn_subagent instead of serial FG agents."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    emit_allow,
    load_json,
    read_event,
    save_json,
    session_id,
    state_path,
    tool_input,
    tool_name,
)

SAME_TURN_WINDOW_S = 3.0


def main() -> None:
    data = read_event()
    sid = session_id(data)
    if tool_name(data) != "spawn_subagent":
        emit_allow(sid=sid)
        return

    inp = tool_input(data)
    bg = inp.get("background")
    if bg is None:
        bg = inp.get("run_in_background")

    path = state_path("parallel-agent-guard", sid)
    state = load_json(
        path,
        {
            "last_agent_time": 0,
            "last_agent_bg": True,
            "consecutive_sequential": 0,
        },
    )
    if not isinstance(state, dict):
        state = {
            "last_agent_time": 0,
            "last_agent_bg": True,
            "consecutive_sequential": 0,
        }

    now = time.time()
    tip = None

    # Background agents are fine
    if bg is True:
        state["last_agent_time"] = now
        state["last_agent_bg"] = True
        state["consecutive_sequential"] = 0
        save_json(path, state)
        emit_allow(sid=sid)
        return

    # Foreground / unknown
    last_t = float(state.get("last_agent_time") or 0)
    last_bg = bool(state.get("last_agent_bg", True))
    if last_t and not last_bg:
        dt = now - last_t
        if dt <= SAME_TURN_WINDOW_S:
            # same-turn parallel burst — ok
            state["last_agent_time"] = now
            state["last_agent_bg"] = False
            save_json(path, state)
            emit_allow(sid=sid)
            return

        state["consecutive_sequential"] = int(state.get("consecutive_sequential", 0)) + 1
        n = state["consecutive_sequential"]
        # Same strong rule whether n is 1 or 5 — keep short.
        tip = (
            f"SWARM: {n} sequential spawn(s). Always parallelize — "
            "multiple spawn_subagent in ONE turn with background=true, then poll."
        )
    else:
        state["consecutive_sequential"] = 0

    state["last_agent_time"] = now
    state["last_agent_bg"] = False
    save_json(path, state)
    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
