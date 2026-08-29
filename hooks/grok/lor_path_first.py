#!/usr/bin/env python3
"""Steer lake-of-rage agents onto skill-router before portable data skills.

UserPromptSubmit (observe): mark the session as lor-work from cwd or prompt.
PreToolUse read_file: rewrite ~/.grok/skills/data* to skill-router until read.
PreToolUse shell: rewrite iceberg_scan of gold.sales / pkmn_sales to metadata.json.
PreToolUse spawn: deny DuckDB / gold.sales until health-sweep Post success.
PostToolUse: append {tool, target} hops; set read_router / read_health only then.
"""

from __future__ import annotations

import json
import os
import re
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

STATE_DIR = Path.home() / ".grok" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

LOR_PROMPT_RE = re.compile(
    r"lake-of-rage|lor-main|lake-vps-lor-main|gold\.sales|pkmn_sales|"
    r"gold tables|identity leak|identity DQ|pokemon tcg gold|"
    r"pokémon tcg gold|skill-router|card_oracle_mark",
    re.I,
)
HEAVY_RE = re.compile(
    r"iceberg_scan|gold\.sales|pkmn_sales|duckdb",
    re.I,
)
PORTABLE_SKILL_RE = re.compile(
    r"(?:^|/)(?:\.grok/)?skills/"
    r"(data|data-identity-resolution|data-semantic-quality|"
    r"data-apache-lakehouse|data-duckdb|data-product-eval|"
    r"data-pipeline-operations|data-table-lifecycle|data-api)"
    r"(?:/|$)",
    re.I,
)
ROUTER_MARKERS = ("skills/skill-router", "skill-router/SKILL.md")
HEALTH_MARKERS = ("lor-vps-health-sweep",)

DEFAULT_ROUTER = (
    Path.home() / "Documents" / "lake-of-rage" / ".claude" / "skills" / "skill-router" / "SKILL.md"
)


def g(data: dict, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def session_id(data: dict) -> str:
    return str(g(data, "sessionId", "session_id") or os.environ.get("GROK_SESSION_ID") or "unknown")


def cwd_of(data: dict) -> str:
    return str(
        g(data, "cwd", "workspaceRoot", "workspace_root")
        or os.environ.get("GROK_WORKSPACE_ROOT")
        or os.getcwd()
    )


def event_name(data: dict) -> str:
    return str(g(data, "hookEventName", "hook_event_name", default="") or "").lower()


def tool_name(data: dict) -> str:
    name = str(g(data, "toolName", "tool_name", default="") or "")
    return {
        "Read": "read_file",
        "ReadFile": "read_file",
        "Bash": "run_terminal_command",
        "Shell": "run_terminal_command",
        "shell": "run_terminal_command",
        "Task": "spawn_subagent",
        "Agent": "spawn_subagent",
    }.get(name, name)


def tool_input(data: dict) -> dict[str, Any]:
    raw = g(data, "toolInput", "tool_input", default={}) or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {"_raw": raw}
    return raw if isinstance(raw, dict) else {}


def state_path(sid: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sid)[:80]
    return STATE_DIR / f"lor-path-{safe}.json"


def hops_path(sid: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sid)[:80]
    return STATE_DIR / f"lor-hops-{safe}.jsonl"


def load_state(sid: str) -> dict[str, Any]:
    empty = {
        "lor_work": False,
        "read_router": False,
        "read_health": False,
        "pending_router": False,
    }
    path = state_path(sid)
    if not path.is_file():
        return dict(empty)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(empty)
    if not isinstance(raw, dict):
        return dict(empty)
    return {
        "lor_work": bool(raw.get("lor_work")),
        "read_router": bool(raw.get("read_router")),
        "read_health": bool(raw.get("read_health")),
        "pending_router": bool(raw.get("pending_router")),
    }


def save_state(sid: str, state: dict[str, Any]) -> None:
    with suppress(Exception):
        state_path(sid).write_text(json.dumps(state, sort_keys=True), encoding="utf-8")


def prompt_text(data: dict) -> str:
    inp = tool_input(data)
    chunks = [
        g(data, "prompt", "text", "userPrompt", "user_prompt", default=""),
        inp.get("prompt") or "",
        inp.get("command") or "",
        inp.get("description") or "",
    ]
    return " ".join(str(c) for c in chunks if c)


def is_lor_cwd(cwd: str) -> bool:
    return "lake-of-rage" in cwd.replace("\\", "/")


def touch_lor_work(*paths: str, state: dict[str, Any]) -> None:
    for path in paths:
        if "lake-of-rage" in path.replace("\\", "/").lower():
            state["lor_work"] = True


def mark_success_flags(target: str, state: dict[str, Any]) -> None:
    lowered = target.replace("\\", "/").lower()
    if any(marker in lowered for marker in ROUTER_MARKERS) or state.get("pending_router"):
        state["read_router"] = True
        state["pending_router"] = False
        state["lor_work"] = True
    if any(marker in lowered for marker in HEALTH_MARKERS):
        state["read_health"] = True
        state["lor_work"] = True


def hop_target(name: str, inp: dict[str, Any]) -> str:
    if name == "read_file":
        return read_target(inp)
    if name == "run_terminal_command":
        return str(inp.get("command") or "")
    if name == "spawn_subagent":
        return str(inp.get("description") or inp.get("prompt") or "")[:240]
    return ""


def append_hop(sid: str, tool: str, target: str) -> None:
    line = json.dumps({"tool": tool, "target": target}, sort_keys=True)
    with suppress(Exception):
        path = hops_path(sid)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


METADATA_CMD = (
    'python3 -c "'
    "from pathlib import Path;"
    "cands=["
    "Path('warehouse/gold.db/sales/metadata.json'),"
    "Path('/home/evan/data/pokemontcg_pipe/warehouse/gold.db/sales/metadata.json')"
    "];"
    "p=next((x for x in cands if x.is_file()), None);"
    "print((p.read_text()[:2000] if p else 'metadata.json missing'))"
    '"'
)


def router_path(cwd: str) -> str:
    local = Path(cwd) / ".claude" / "skills" / "skill-router" / "SKILL.md"
    if local.is_file():
        return str(local)
    nested = Path(cwd) / "lake-of-rage" / ".claude" / "skills" / "skill-router" / "SKILL.md"
    if nested.is_file():
        return str(nested)
    return str(DEFAULT_ROUTER)


def read_target(inp: dict[str, Any]) -> str:
    return str(inp.get("target_file") or inp.get("file_path") or inp.get("path") or "")


def portable_skill_path(path: str) -> bool:
    norm = path.replace("\\", "/")
    return bool(PORTABLE_SKILL_RE.search(norm))


def emit(obj: dict[str, Any], *, code: int = 0) -> None:
    print(json.dumps(obj))
    raise SystemExit(code)


def allow() -> None:
    emit({"decision": "allow"})


def deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    emit({"decision": "deny", "reason": reason}, code=2)


def rewrite_read(path: str) -> None:
    reason = (
        "lake-of-rage hop 1 is skill-router, not a portable ~/.grok/skills/data* file. "
        f"Reading {path} instead."
    )
    print(reason, file=sys.stderr)
    emit(
        {
            "decision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": {"target_file": path},
                "additionalContext": reason,
            },
        }
    )


def rewrite_shell(command: str) -> None:
    reason = (
        "Census live fact is snapshot metadata.json, not iceberg_scan of gold.sales. "
        "Rewriting the command."
    )
    print(reason, file=sys.stderr)
    emit(
        {
            "decision": "allow",
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": {"command": command},
                "additionalContext": reason,
            },
        }
    )


def handle_prompt(data: dict, state: dict[str, Any]) -> None:
    if is_lor_cwd(cwd_of(data)) or LOR_PROMPT_RE.search(prompt_text(data)):
        state["lor_work"] = True


def handle_pre_read(data: dict, state: dict[str, Any]) -> None:
    target = read_target(tool_input(data))
    touch_lor_work(target, cwd_of(data), state=state)
    if not state["lor_work"]:
        allow()
    if portable_skill_path(target) and not state["read_router"]:
        state["pending_router"] = True
        state["lor_work"] = True
        rewrite_read(router_path(cwd_of(data)))
    allow()


def handle_pre_heavy(data: dict, state: dict[str, Any]) -> None:
    name = tool_name(data)
    cmd = str(tool_input(data).get("command") or "")
    blob = prompt_text(data)
    touch_lor_work(cwd_of(data), blob, state=state)
    if not state["lor_work"]:
        allow()
    if name == "run_terminal_command":
        if re.search(r"iceberg_scan\s*\(", cmd, re.I) and re.search(
            r"gold\.sales|pkmn_sales", cmd, re.I
        ):
            rewrite_shell(METADATA_CMD)
        allow()
    if name == "spawn_subagent" and HEAVY_RE.search(blob) and not state["read_health"]:
        deny(
            "Do not spawn DuckDB / gold.sales until lor-vps-health-sweep "
            "PostToolUse has succeeded. Census uses snapshot metadata.json. "
            "Card queries use query_gold_sql on a cheap view, never pkmn_sales."
        )
    allow()


def handle_post(data: dict, state: dict[str, Any]) -> None:
    name = tool_name(data)
    target = hop_target(name, tool_input(data))
    touch_lor_work(target, cwd_of(data), state=state)
    if state["lor_work"]:
        append_hop(session_id(data), name, target)
        mark_success_flags(target, state)


def decide(data: dict) -> None:
    sid = session_id(data)
    state = load_state(sid)
    event = event_name(data)
    if "prompt" in event:
        handle_prompt(data, state)
        save_state(sid, state)
        allow()
    if event.startswith("pre"):
        name = tool_name(data)
        if name == "read_file":
            try:
                handle_pre_read(data, state)
            finally:
                save_state(sid, state)
        if name in {"spawn_subagent", "run_terminal_command"}:
            try:
                handle_pre_heavy(data, state)
            finally:
                save_state(sid, state)
        save_state(sid, state)
        allow()
    if event.startswith("post"):
        handle_post(data, state)
        save_state(sid, state)
        allow()
    save_state(sid, state)
    allow()


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        allow()
    if not isinstance(data, dict):
        allow()
    decide(data)


if __name__ == "__main__":
    main()
