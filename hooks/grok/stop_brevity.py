#!/usr/bin/env python3
"""Stop: block essay-shaped finals once per turn (Grok-native brevity gate)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_stop_allow, emit_stop_block, g, read_event  # noqa: E402

# Align with ~/.grok/AGENTS.md empirical thresholds
MAX_WORDS_NORMAL = 220
MAX_HEADERS = 2
OFFER_RE = re.compile(
    r"(would you like me to|i can also|happy to dig|want me to|let me know if you)",
    re.I,
)
RECAP_RE = re.compile(
    r"(^|\n)##?\s*(summary|bottom line|next steps|key takeaways|what i did|follow-?ups)\b",
    re.I,
)
DEEP_OK_RE = re.compile(
    r"\b(adversarial|deep dive|full review|implementation plan|design doc|prd)\b",
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

    # Allow explicitly deep-shaped work products
    if DEEP_OK_RE.search(msg[:500]):
        emit_stop_allow()
        return

    words = len(msg.split())
    headers = len(re.findall(r"(?m)^#{1,3}\s+\S", msg))
    has_offer = bool(OFFER_RE.search(msg))
    has_recap = bool(RECAP_RE.search(msg))
    has_hr = "\n---\n" in msg or msg.strip().startswith("---")

    problems: list[str] = []
    if words > MAX_WORDS_NORMAL and headers > MAX_HEADERS:
        problems.append(
            f"too long + structured ({words} words, {headers} headers; "
            f"normal cap ~{MAX_WORDS_NORMAL} words / ≤{MAX_HEADERS} headers)"
        )
    elif words > 400:
        problems.append(f"final is {words} words (p90 target ~200–300 for normal turns)")
    if headers >= 5:
        problems.append(f"essay shape ({headers} headers)")
    if has_recap:
        problems.append("recap stack (Summary/Bottom line/Next steps section)")
    if has_offer:
        problems.append("closing offer ('want me to…')")
    if has_hr and words > 150:
        problems.append("decorative horizontal rules")

    if not problems:
        emit_stop_allow()
        return

    emit_stop_block(
        "BREVITY GATE: rewrite the final response shorter before stopping.\n"
        f"Issues: {'; '.join(problems)}.\n"
        "Rules: first line = answer/outcome; ≤2 headers; no recap stack; no closing offers; "
        "after code work use Done/bullets/Verified. Only expand if user asked deep/full/plan/review."
    )


if __name__ == "__main__":
    main()
