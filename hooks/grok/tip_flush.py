#!/usr/bin/env python3
"""PreToolUse (matcher .*): flush queued PostToolUse tips into additionalContext.

Run this on a broad matcher so tips from batch/swarm/failure coaches reach the model
even when the next tool isn't covered by another coaching hook.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_allow, read_event, session_id  # noqa: E402


def main() -> None:
    data = read_event()
    emit_allow(sid=session_id(data))


if __name__ == "__main__":
    main()
