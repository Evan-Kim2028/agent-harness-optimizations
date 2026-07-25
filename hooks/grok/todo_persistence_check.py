#!/usr/bin/env python3
"""PostToolUse: detect todo_write resets that drop completed history."""
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

RESET_THRESHOLD = 2


def main() -> None:
    data = read_event()
    if tool_name(data) != "todo_write":
        sys.exit(0)

    sid = session_id(data)
    if not sid:
        sys.exit(0)

    inp = tool_input(data)
    todos = inp.get("todos")
    if todos is None:
        sys.exit(0)
    if not isinstance(todos, list):
        sys.exit(0)

    # merge=true incremental updates are fine
    merge = inp.get("merge")
    if merge is True:
        # still track counts
        pass

    done = sum(1 for t in todos if isinstance(t, dict) and t.get("status") == "completed")
    # also accept kimi-style "done"
    done += sum(
        1
        for t in todos
        if isinstance(t, dict) and t.get("status") == "done"
    )
    total = len(todos)
    pending = sum(
        1
        for t in todos
        if isinstance(t, dict) and t.get("status") in ("pending", "in_progress", None)
    )

    path = state_path("todo-persistence", sid)
    state = load_json(path, {"last_done": 0, "last_total": 0, "tips": 0})
    if not isinstance(state, dict):
        state = {"last_done": 0, "last_total": 0, "tips": 0}

    prev_done = int(state.get("last_done", 0))
    prev_total = int(state.get("last_total", 0))
    tips = int(state.get("tips", 0))

    # Full replace without merge that wipes done history
    if (
        merge is not True
        and prev_done >= RESET_THRESHOLD
        and done == 0
        and pending > 0
        and tips < 3
    ):
        post_tip(
            sid,
            f"⚠️ TODO RESET: replaced a list with {prev_done} completed items with "
            f"{total} fresh items (0 done). Prefer todo_write(merge=true) status updates "
            "or keep completed items when rebuilding.",
        )
        state["tips"] = tips + 1

    elif (
        merge is not True
        and prev_total > total + 2
        and done == prev_done
        and tips < 3
    ):
        post_tip(
            sid,
            f"⚠️ TODO SHRINK: list shrank {prev_total}→{total} without new completions. "
            "Mark items completed instead of dropping them silently.",
        )
        state["tips"] = tips + 1

    state["last_done"] = done
    state["last_total"] = total
    save_json(path, state)
    sys.exit(0)


if __name__ == "__main__":
    main()
