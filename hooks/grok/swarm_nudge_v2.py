#!/usr/bin/env python3
"""PostToolUse: swarm-first coaching; tracks manual work since last agent."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    AGENT_TOOLS,
    MANUAL_TOOLS,
    load_json,
    post_tip,
    read_event,
    save_json,
    session_id,
    state_path,
    tool_input,
    tool_name,
)

MANUAL_SINCE_AGENT = 8
RATIO = 5.0
TOTAL_MANUAL = 4
COOLDOWN = 15


def main() -> None:
    data = read_event()
    sid = session_id(data)
    name = tool_name(data)
    if not sid or not name:
        sys.exit(0)

    path = state_path("swarm-tracker-v2", sid)
    state = load_json(
        path,
        {
            "total": 0,
            "agents": 0,
            "manual": 0,
            "manual_since_agent": 0,
            "last_tip": 0,
            "tips": 0,
        },
    )
    if not isinstance(state, dict):
        state = {
            "total": 0,
            "agents": 0,
            "manual": 0,
            "manual_since_agent": 0,
            "last_tip": 0,
            "tips": 0,
        }

    state["total"] = int(state.get("total", 0)) + 1
    if name in MANUAL_TOOLS:
        state["manual"] = int(state.get("manual", 0)) + 1
        state["manual_since_agent"] = int(state.get("manual_since_agent", 0)) + 1
    elif name in AGENT_TOOLS:
        state["agents"] = int(state.get("agents", 0)) + 1
        state["manual_since_agent"] = 0

    total = state["total"]
    last_tip = int(state.get("last_tip", 0))
    can = last_tip == 0 or (total - last_tip) >= COOLDOWN
    tip = None

    if (
        can
        and state["manual_since_agent"] >= MANUAL_SINCE_AGENT
        and state["agents"] > 0
    ):
        tip = (
            f"TIP: {state['manual_since_agent']}+ manual tools since last agent. "
            "Delegate remaining discovery/edits to parallel spawn_subagent "
            "(background=true), then poll outputs."
        )
    elif (
        can
        and state["agents"] > 0
        and state["manual"] / max(state["agents"], 1) >= RATIO
    ):
        r = state["manual"] / max(state["agents"], 1)
        tip = (
            f"TIP: manual:agent ratio {r:.1f}:1. Too much solo grind — "
            "default to subagents for subtasks needing >2 tool calls."
        )
    elif can and state["agents"] == 0 and state["manual"] >= TOTAL_MANUAL:
        tip = (
            f"TIP: {state['manual']}+ manual discovery/edit calls, zero agents. "
            "Dispatch parallel explore agents instead of sequential read/grep/shell."
        )

    # complex shell during manual streak
    if tip is None and name == "run_terminal_command" and state["manual_since_agent"] >= 4:
        cmd = str(tool_input(data).get("command") or "")
        if cmd.count("\n") > 2 or cmd.count("&&") > 1 or len(cmd) > 300:
            if can:
                tip = (
                    "TIP: complex multi-step shell with no recent agents. "
                    "Split independent concerns across background subagents."
                )

    if tip:
        state["last_tip"] = total
        state["tips"] = int(state.get("tips", 0)) + 1
        post_tip(sid, tip)

    save_json(path, state)
    sys.exit(0)


if __name__ == "__main__":
    main()
