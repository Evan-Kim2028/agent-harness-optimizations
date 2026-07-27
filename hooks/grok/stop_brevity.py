#!/usr/bin/env python3
"""Stop: block only severe essay-shaped finals once per turn (soft brevity gate)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_stop_allow, emit_stop_block, g, read_event  # noqa: E402

# Soft thresholds — only catch egregious walls of text / essay templates.
# AGENTS.md still coaches normal brevity; this gate no longer fires on
# moderate structure, training-style --- separators, or short offer lines.
MAX_WORDS_LONG = 400          # with structure
MAX_HEADERS_LONG = 3          # with length
MAX_WORDS_HARD = 600          # length alone
MAX_HEADERS_ESSAY = 6         # headers alone
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

    problems: list[str] = []
    # Compound: long AND heavily structured
    if words > MAX_WORDS_LONG and headers > MAX_HEADERS_LONG:
        problems.append(
            f"too long + structured ({words} words, {headers} headers; "
            f"soft cap ~{MAX_WORDS_LONG}w / ≤{MAX_HEADERS_LONG} headers)"
        )
    # Length alone only when extreme
    elif words > MAX_WORDS_HARD:
        problems.append(f"final is {words} words (soft hard-cap ~{MAX_WORDS_HARD})")
    # Essay template shape
    if headers >= MAX_HEADERS_ESSAY:
        problems.append(f"essay shape ({headers} headers)")
    # Recap / offer only when already long enough that the filler matters
    if has_recap and words > 250:
        problems.append("recap stack (Summary/Bottom line/Next steps section)")
    if has_offer and words > 250:
        problems.append("closing offer on a long final")
    # Decorative --- intentionally not gated (false-positives on short training answers)

    if not problems:
        emit_stop_allow()
        return

    emit_stop_block(
        "BREVITY GATE: rewrite shorter before stopping.\n"
        f"Issues: {'; '.join(problems)}.\n"
        "First line = answer; ≤3 headers; no recap stack; no closing offers on long finals."
    )


if __name__ == "__main__":
    main()
