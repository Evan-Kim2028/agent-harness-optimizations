#!/usr/bin/env python3
"""PreToolUse: suggest background=true for independent explore/audit agents."""
from __future__ import annotations

import sys
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

DISCOVERY = [
    "explore",
    "investigate",
    "find",
    "audit",
    "analyze",
    "check",
    "discover",
    "map",
    "search",
    "locate",
    "identify",
    "review",
    "examine",
    "inspect",
    "survey",
    "trace",
]
DEPENDENT = [
    "fix",
    "implement",
    "edit",
    "change",
    "refactor",
    "migrate",
    "then",
    "after that",
    "before proceeding",
    "blocking",
    "depends on",
]


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
    if bg is True:
        emit_allow(sid=sid)
        return

    text = f"{inp.get('description', '')} {inp.get('prompt', '')} {inp.get('subagent_type', '')}".lower()
    hits = [k for k in DISCOVERY if k in text]
    deps = [k for k in DEPENDENT if k in text]
    score = len(hits) * 2 - len(deps)

    tip = None
    if score >= 2:
        path = state_path("background-agent-nudge", sid)
        state = load_json(path, {"tips": 0})
        if isinstance(state, dict) and int(state.get("tips", 0)) < 5:
            state["tips"] = int(state.get("tips", 0)) + 1
            save_json(path, state)
            tip = (
                "SWARM: set background=true and spawn more agents in parallel — "
                "don't wait on one foreground agent."
            )

    emit_allow(additional=tip, sid=sid)


if __name__ == "__main__":
    main()
