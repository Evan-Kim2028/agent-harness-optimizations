#!/usr/bin/env python3
"""Eval-only PreToolUse canary. Not in grok-harness.json.

Emits a unique additionalContext string. Grep the session chat_history
for CANARY_GROK_CTX_v1. Hit means Grok fed PreToolUse additionalContext
to the model. Miss means the channel is still dead.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_allow, read_event, session_id  # noqa: E402

CANARY = "CANARY_GROK_CTX_v1"


def main() -> None:
    data = read_event()
    emit_allow(additional=CANARY, sid=session_id(data))


if __name__ == "__main__":
    main()
