# Grok Build CLI hooks

What Grok actually installs is one deny gate. The rest of this directory is unregistered (Kimi-port coaches). Grok does not feed PreToolUse `additionalContext` to the model.

## Installed

| Hook | Event | Role |
|------|--------|------|
| `strreplace_check` | PreToolUse `Edit\|search_replace` | **Blocks** if `old_string` is missing from the file |

Install: `scripts/install-grok-hooks.sh` (copies `hooks/grok-harness.json` → `~/.grok/hooks/agent-harness-optimizations.json` and splices `AGENTS.grok.md`).

Static swarm / tool-selection rules live in `AGENTS.grok.md` → `~/.grok/AGENTS.md`. They are prompt text, not hook injections.

## Unregistered (on disk, not on the hot path)

`tip_flush`, `shell_check`, `shell_output_truncator`, `re_read_guard`, `line_offset_enforcer`, `discovery_intercept`, `parallel_agent_guard`, `background_agent_nudge`, `batch_nudge`, `swarm_nudge_v2`, `todo_persistence_check`, `re_read_turn_guard`, `post_tool_failure_coach`, `stop_brevity`, `channel_probe`.

Do not re-register them unless a channel probe shows PreToolUse `additionalContext` in `chat_history.jsonl`. `stop_brevity` and shell noop deny already caused doom loops.

## Design notes

- Input: Grok camelCase (`toolName`, `toolInput`, `sessionId`); snake_case accepted.
- Live PreToolUse verbs: `allow`, `deny`, `updatedInput`. Deny is what the model sees (`Hook denied:`).
- `updatedInput` cannot change the tool name.
- State dir `~/.grok/state/` is leftover from the unregistered coaches. Safe to ignore for new sessions.
