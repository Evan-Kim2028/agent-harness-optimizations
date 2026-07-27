#!/usr/bin/env python3
"""Stop: block only extreme essay finals once per turn (very soft gate).

History: tighter thresholds caused rewrite loops → model ran `true` noops
instead of answering (see session 019f9fa9…, 108 noops). Prefer AGENTS.md
coaching; only block catastrophic walls of text.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_stop_allow, emit_stop_block, g, read_event  # noqa: E402

# Very soft — only egregious dumps. Most turns should never hit this.
MAX_WORDS_LONG = 700          # with heavy structure
MAX_HEADERS_LONG = 5
MAX_WORDS_HARD = 1000         # length alone
MAX_HEADERS_ESSAY = 8
DEEP_OK_RE = re.compile(
    r"\b(adversarial|deep dive|full review|implementation plan|design doc|prd|"
    r"interview prep|training mode)\b",
    re.I,
)


def main() -> None:
    data = read_event()
    reason = str(g(data, "reason", default="") or "")
    if reason and reason != "end_turn":
        emit_stop_allow()
        return

    # Already continued once from a stop hook this turn — don't loop
    if g(data, "stopHookActive", "stop_hook_active") is True:
        emit_stop_allow()
        return

    msg = str(g(data, "lastAssistantMessage", "last_assistant_message", default="") or "")
    if not msg.strip():
        emit_stop_allow()
        return

    if DEEP_OK_RE.search(msg[:800]):
        emit_stop_allow()
        return

    words = len(msg.split())
    headers = len(re.findall(r"(?m)^#{1,3}\s+\S", msg))

    problems: list[str] = []
    if words > MAX_WORDS_LONG and headers > MAX_HEADERS_LONG:
        problems.append(
            f"extreme length + structure ({words} words, {headers} headers)"
        )
    elif words > MAX_WORDS_HARD:
        problems.append(f"extreme length ({words} words)")
    if headers >= MAX_HEADERS_ESSAY:
        problems.append(f"essay shape ({headers} headers)")
    # No --- / offer / recap gates — those caused false-positive rewrite loops

    if not problems:
        emit_stop_allow()
        return

    emit_stop_block(
        "BREVITY GATE: rewrite much shorter before stopping.\n"
        f"Issues: {'; '.join(problems)}.\n"
        "First line = answer; few headers; no recap stack."
    )


if __name__ == "__main__":
    main()
