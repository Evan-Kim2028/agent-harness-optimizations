#!/usr/bin/env python3
"""Stop: DISABLED — always allow.

Was blocking essay-shaped finals; caused rewrite loops where grok-4.5 (esp. long
sessions / plan mode) ran `true` noops or answered via echo/cat instead of
assistant text. See session 019f9fa9… (135+ NOOP denials, 55 bashBareEcho,
context 72%, user spam `?`).

Brevity is left to AGENTS.md coaching only. Re-enable extreme gate only after
the shell-as-answer / keep-alive failure mode is gone.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import emit_stop_allow, read_event  # noqa: E402


def main() -> None:
    read_event()  # drain stdin
    emit_stop_allow()


if __name__ == "__main__":
    main()
