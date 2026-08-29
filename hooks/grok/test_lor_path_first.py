"""Tests for hooks/grok/lor_path_first.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "lor_path_first.py"
LOR_CWD = "/home/evan/Documents/lake-of-rage"
HEALTH_SKILL = f"{LOR_CWD}/.claude/skills/lor-vps-health-sweep/SKILL.md"
IDENTITY_HOP = "/home/evan/.grok/skills/data/SKILL.md"
CENSUS_SCAN = "duckdb -c \"SELECT count(*) FROM iceberg_scan('gold.sales')\""


def _load():
    spec = importlib.util.spec_from_file_location("lor_path_first", HOOK)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lor_path_first"] = mod
    spec.loader.exec_module(mod)
    return mod


hook = _load()


def _run(monkeypatch, tmp_path: Path, payload: dict) -> tuple[int, dict, str]:
    monkeypatch.setattr(hook, "STATE_DIR", tmp_path)
    monkeypatch.setattr(hook, "state_path", lambda sid: tmp_path / f"lor-path-{sid}.json")
    monkeypatch.setattr(hook, "hops_path", lambda sid: tmp_path / f"lor-hops-{sid}.jsonl")
    stdout: list[str] = []
    stderr: list[str] = []

    def fake_print(*args: object, **kwargs: object) -> None:
        text = " ".join(str(a) for a in args)
        if kwargs.get("file") is hook.sys.stderr:
            stderr.append(text)
        else:
            stdout.append(text)

    monkeypatch.setattr("builtins.print", fake_print)
    with pytest.raises(SystemExit) as raised:
        hook.decide(payload)
    code = raised.value.code
    if code is None:
        code = 0
    body = json.loads(stdout[-1])
    return int(code), body, "\n".join(stderr)


def test_identity_first_hop_rewrites_to_router(monkeypatch, tmp_path: Path) -> None:
    code, body, _ = _run(
        monkeypatch,
        tmp_path,
        {
            "hookEventName": "pre_tool_use",
            "sessionId": "s1",
            "cwd": LOR_CWD,
            "toolName": "read_file",
            "toolInput": {"target_file": IDENTITY_HOP},
        },
    )
    assert code == 0
    assert body["hookSpecificOutput"]["updatedInput"]["target_file"].endswith(
        "skill-router/SKILL.md"
    )


def test_census_iceberg_scan_rewritten_to_metadata(monkeypatch, tmp_path: Path) -> None:
    code, body, _ = _run(
        monkeypatch,
        tmp_path,
        {
            "hookEventName": "pre_tool_use",
            "sessionId": "s2",
            "cwd": LOR_CWD,
            "toolName": "run_terminal_command",
            "toolInput": {"command": CENSUS_SCAN},
        },
    )
    assert code == 0
    updated = body["hookSpecificOutput"]["updatedInput"]["command"]
    assert "iceberg_scan" not in updated
    assert "metadata.json" in updated


def test_spawn_denied_until_health_post(monkeypatch, tmp_path: Path) -> None:
    sid = "s3"
    spawn = {
        "hookEventName": "pre_tool_use",
        "sessionId": sid,
        "cwd": LOR_CWD,
        "toolName": "spawn_subagent",
        "toolInput": {"prompt": "live DuckDB gold.sales sweep", "description": "sweep"},
    }
    _run(
        monkeypatch,
        tmp_path,
        {
            "hookEventName": "pre_tool_use",
            "sessionId": sid,
            "cwd": LOR_CWD,
            "toolName": "read_file",
            "toolInput": {"target_file": HEALTH_SKILL},
        },
    )
    code, body, _ = _run(monkeypatch, tmp_path, spawn)
    assert code == 2
    assert body["decision"] == "deny"
    _run(
        monkeypatch,
        tmp_path,
        {
            "hookEventName": "post_tool_use",
            "sessionId": sid,
            "cwd": LOR_CWD,
            "toolName": "read_file",
            "toolInput": {"target_file": HEALTH_SKILL},
        },
    )
    code, body, _ = _run(monkeypatch, tmp_path, spawn)
    assert code == 0
    assert body["decision"] == "allow"


def test_git_commit_mentioning_scan_is_not_rewritten(monkeypatch, tmp_path: Path) -> None:
    code, body, _ = _run(
        monkeypatch,
        tmp_path,
        {
            "hookEventName": "pre_tool_use",
            "sessionId": "s5",
            "cwd": LOR_CWD,
            "toolName": "run_terminal_command",
            "toolInput": {
                "command": "git commit -m 'rewrite iceberg_scan of gold.sales'",
            },
        },
    )
    assert code == 0
    assert body == {"decision": "allow"}


def test_non_lor_untouched(monkeypatch, tmp_path: Path) -> None:
    code, body, _ = _run(
        monkeypatch,
        tmp_path,
        {
            "hookEventName": "pre_tool_use",
            "sessionId": "s4",
            "cwd": "/tmp/other-project",
            "toolName": "read_file",
            "toolInput": {"target_file": IDENTITY_HOP},
        },
    )
    assert code == 0
    assert body == {"decision": "allow"}
