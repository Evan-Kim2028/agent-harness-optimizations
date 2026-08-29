#!/usr/bin/env python3
"""Score one Grok session after the 2026-08-28 subtract.

Swarm-tracker files are stale (unregistered coaches). Read the session dir.

Metrics:
  hook_names          unique hook_execution names (want only strreplace_check)
  hook_runs           PreToolUse processes spawned
  hook_runs_per_tool  tax (baseline ~3–5; want ~0 except on search_replace)
  spawn_n / spawn_pct spawn_subagent share of tools
  canary_in_history   CANARY_GROK_CTX_v1 in chat_history (channel probe)
  swarm_tip_in_history flushed SPAWN_TIP string in chat_history
  deny_in_updates     strreplace Hook denied / blocked:true

Usage:
  python3 scripts/measure-grok-session.py ~/.grok/sessions/<cwd-enc>/<id>
  python3 scripts/measure-grok-session.py --latest
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

CANARY = "CANARY_GROK_CTX_v1"
SWARM = "Always use spawn_subagent and parallelize"
GROK_HOME = Path.home() / ".grok"


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def latest_session() -> Path | None:
    root = GROK_HOME / "sessions"
    best = None
    best_m = 0.0
    for p in root.rglob("updates.jsonl"):
        m = p.stat().st_mtime
        if m > best_m:
            best_m, best = m, p.parent
    return best


def measure(sess: Path) -> dict:
    signals = load_json(sess / "signals.json", {}) or {}
    summary = load_json(sess / "summary.json", {}) or {}
    tools = list(signals.get("toolsUsed") or [])
    tool_n = int(signals.get("toolCallCount") or 0)

    hook_names: Counter[str] = Counter()
    hook_events = 0
    hook_runs = 0
    blocked = 0
    tool_calls = 0
    spawn_n = 0
    with (sess / "updates.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if '"hook_execution"' not in line and '"tool_call"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            u = (o.get("params") or {}).get("update") or {}
            kind = u.get("sessionUpdate")
            if kind == "hook_execution":
                hook_events += 1
                for r in u.get("runs") or []:
                    hook_runs += 1
                    hook_names[r.get("name") or "?"] += 1
                    st = r.get("status") or {}
                    if st.get("blocked") or st.get("status") == "failed":
                        blocked += 1
            elif kind == "tool_call":
                tool_calls += 1
                title = (u.get("title") or "").lower()
                if "spawn_subagent" in title or title == "spawn_subagent":
                    spawn_n += 1

    # Only user/assistant text. tool_result hits are false positives from reading
    # channel_probe.py / _common.py source.
    user_text = []
    hp = sess / "chat_history.jsonl"
    if hp.exists():
        with hp.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("type") not in ("user", "assistant"):
                    continue
                for part in o.get("content") or []:
                    if isinstance(part, dict) and part.get("type") == "text":
                        user_text.append(part.get("text") or "")
    joined = "\n".join(user_text)

    spawn_from_signals = tool_n and "spawn_subagent" in tools
    denom = tool_n or tool_calls or 1
    return {
        "session": str(sess),
        "id": (summary.get("info") or {}).get("id") or sess.name,
        "title": summary.get("generated_title") or summary.get("session_summary"),
        "toolCallCount_signals": tool_n,
        "tool_call_updates": tool_calls,
        "toolsUsed": tools,
        "spawn_n": spawn_n,
        "spawn_pct": round(100.0 * spawn_n / denom, 2),
        "spawn_in_toolsUsed": bool(spawn_from_signals),
        "hook_events": hook_events,
        "hook_runs": hook_runs,
        "hook_runs_per_tool": round(hook_runs / denom, 2),
        "hook_names": dict(hook_names),
        "deny_or_blocked": blocked,
        "canary_in_history": CANARY in joined,
        "swarm_tip_in_history": SWARM in joined,
        "contextTokensUsed": signals.get("contextTokensUsed"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_dir", nargs="?", type=Path)
    ap.add_argument("--latest", action="store_true")
    args = ap.parse_args()
    sess = args.session_dir
    if args.latest or sess is None:
        sess = latest_session()
    if sess is None or not (sess / "updates.jsonl").exists():
        print("no session dir with updates.jsonl", file=sys.stderr)
        return 2
    print(json.dumps(measure(sess.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
