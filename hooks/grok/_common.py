#!/usr/bin/env python3
"""Shared helpers for Grok Build harness hooks.

Grok sends camelCase JSON on stdin (toolName, toolInput, sessionId, hookEventName).
Claude/Kimi snake_case is also accepted. Coaching tips are delivered via:
  - PreToolUse: decision=allow + hookSpecificOutput.additionalContext
  - PostToolUse: queued to state, flushed on the next PreToolUse allow
  - PreToolUse deny / Stop block: decision reason (hard feedback)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

STATE_DIR = Path.home() / ".grok" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Normalize Grok tool names ↔ coaching labels
TOOL_ALIASES = {
    "Bash": "run_terminal_command",
    "Shell": "run_terminal_command",
    "shell": "run_terminal_command",
    "Read": "read_file",
    "ReadFile": "read_file",
    "Edit": "search_replace",
    "Write": "write",
    "MultiEdit": "search_replace",
    "StrReplaceFile": "search_replace",
    "StrReplace": "search_replace",
    "Grep": "grep",
    "Glob": "list_dir",
    "ListDir": "list_dir",
    "Task": "spawn_subagent",
    "Agent": "spawn_subagent",
    "SetTodoList": "todo_write",
    "TodoWrite": "todo_write",
}

MANUAL_TOOLS = frozenset(
    {"read_file", "grep", "run_terminal_command", "list_dir", "search_replace"}
)
AGENT_TOOLS = frozenset({"spawn_subagent"})


def read_event() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def g(data: dict, *keys: str, default: Any = None) -> Any:
    """Get first present key (camelCase or snake_case)."""
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return default


def session_id(data: dict) -> str:
    return str(
        g(data, "sessionId", "session_id")
        or os.environ.get("GROK_SESSION_ID")
        or "unknown"
    )


def event_name(data: dict) -> str:
    return str(g(data, "hookEventName", "hook_event_name", default="") or "").lower()


def tool_name(data: dict) -> str:
    name = str(g(data, "toolName", "tool_name", default="") or "")
    return TOOL_ALIASES.get(name, name)


def tool_input(data: dict) -> dict[str, Any]:
    raw = g(data, "toolInput", "tool_input", default={}) or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {"_raw": raw}
    return raw if isinstance(raw, dict) else {}


def tool_result(data: dict) -> Any:
    return g(data, "toolResult", "tool_result", "tool_output", "toolResponse", default="")


def cwd(data: dict) -> str:
    return str(
        g(data, "cwd", "workspaceRoot", "workspace_root")
        or os.environ.get("GROK_WORKSPACE_ROOT")
        or os.getcwd()
    )


def resolve_path(path_str: str, data: dict) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return Path(cwd(data)) / p


def state_path(name: str, sid: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sid)[:80]
    return STATE_DIR / f"{name}-{safe}.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, obj: Any) -> None:
    try:
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    except Exception:
        pass


def queue_tip(sid: str, tip: str) -> None:
    if not tip or not sid:
        return
    path = state_path("pending-tips", sid)
    tips = load_json(path, [])
    if not isinstance(tips, list):
        tips = []
    # de-dupe last tip
    if tips and tips[-1] == tip:
        return
    tips.append(tip)
    save_json(path, tips[-8:])  # cap


def flush_tips(sid: str) -> list[str]:
    path = state_path("pending-tips", sid)
    tips = load_json(path, [])
    if not isinstance(tips, list) or not tips:
        return []
    save_json(path, [])
    return [t for t in tips if isinstance(t, str) and t.strip()]


def emit_allow(additional: str | None = None, sid: str | None = None) -> None:
    """Allow PreToolUse; optionally inject coaching + flushed pending tips."""
    parts: list[str] = []
    if sid:
        parts.extend(flush_tips(sid))
    if additional:
        parts.append(additional)
    if not parts:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    ctx = "\n".join(parts)
    # stderr for TUI scrollback; additionalContext for model when supported
    print(ctx, file=sys.stderr)
    print(
        json.dumps(
            {
                "decision": "allow",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": ctx,
                },
            }
        )
    )
    sys.exit(0)


def emit_deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    print(json.dumps({"decision": "deny", "reason": reason}))
    sys.exit(2)


def emit_stop_block(reason: str) -> None:
    print(reason, file=sys.stderr)
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def emit_stop_allow() -> None:
    sys.exit(0)


def post_tip(sid: str, tip: str) -> None:
    """PostToolUse: queue tip for next PreToolUse + stderr for scrollback."""
    queue_tip(sid, tip)
    print(tip, file=sys.stderr)
