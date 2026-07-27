#!/usr/bin/env python3
"""PreToolUse: coach Shell toward native Grok tools; deny keep-alive noops."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    emit_allow,
    emit_deny,
    read_event,
    session_id,
    tool_input,
    tool_name,
)

# Models stall by running true / echo skip with no user-visible text.
# Session 019f9fa9…: 108 noops; runtime already warns — model ignores.
_NOOP_RE = re.compile(
    r"^(true|:|echo\s+skip|echo|pwd|sleep\s+\d+)\s*;?\s*$",
    re.I,
)


def main() -> None:
    data = read_event()
    if tool_name(data) != "run_terminal_command":
        emit_allow(sid=session_id(data))
        return

    cmd = tool_input(data).get("command") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        emit_allow(sid=session_id(data))
        return

    stripped = cmd.strip()
    if _NOOP_RE.match(stripped) or stripped in {"true", ":", "echo skip"}:
        emit_deny(
            "NOOP BLOCKED: do not run keep-alive shells (true / : / echo skip). "
            "Write the user-visible answer now, or call a real tool. End the turn."
        )
        return

    tips: list[str] = []

    if re.search(r"\b(ls|find)\b", cmd) and not re.search(
        r"\b(git|docker|ffmpeg|ffprobe|pytest|npm|pnpm|cargo|go)\b", cmd
    ):
        tips.append(
            "💡 Shell discovery: prefer list_dir / glob patterns, or grep for content. "
            "Avoid ls/find via Shell when native tools work."
        )

    if re.search(r"\b(cat|head|tail)\b", cmd):
        m = re.search(
            r"\b(?:cat|head|tail)\s+(?:-[a-zA-Z]+\s+)*(?:-n\s+\d+\s+)?(\S+)", cmd
        )
        f = m.group(1) if m else "<file>"
        tips.append(
            f"💡 Prefer read_file(target_file='{f}', offset=..., limit=...) over cat/head/tail."
        )

    if re.search(r"\b(grep|rg)\b", cmd) and "git " not in cmd[:20]:
        tips.append(
            "💡 Prefer the native grep tool (pattern/path/glob) over shell grep/rg."
        )

    if re.search(r"(^|[;&|])\s*cd\s+", cmd):
        tips.append(
            "💡 Avoid cd in Shell (cwd does not persist). Use absolute paths or git -C <path>."
        )

    if re.search(r"\bpython3?\s+-c\b", cmd) and re.search(
        r"open\s*\(|pathlib|os\.(listdir|walk)", cmd
    ):
        tips.append(
            "💡 Python one-liners for file I/O: prefer read_file / list_dir / grep."
        )

    tip = " ".join(tips[:2]) if tips else None  # cap noise
    emit_allow(additional=tip, sid=session_id(data))


if __name__ == "__main__":
    main()
