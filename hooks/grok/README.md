# Grok Build CLI hooks

Port of the Kimi harness coaching suite for [Grok Build](https://x.ai), plus Grok-only gates.

## What is installed

| Hook | Event | Role |
|------|--------|------|
| `tip_flush` | PreToolUse `.*` | Flush queued PostToolUse tips into model context |
| `shell_check` | Shell | Native-tool coaching (cat/grep/cd/find) |
| `shell_output_truncator` | Shell | Unbounded output warnings |
| `strreplace_check` | search_replace | **Blocks** if `old_string` missing |
| `re_read_guard` | read_file | Unchanged re-read warning |
| `line_offset_enforcer` | read_file | Large-file full reads |
| `discovery_intercept` | manual tools | Swarm nudge on long streaks |
| `parallel_agent_guard` | spawn_subagent | Sequential agent warning |
| `background_agent_nudge` | spawn_subagent | Prefer `background=true` |
| `batch_nudge` | PostToolUse | 3+ same-tool sequential |
| `swarm_nudge_v2` | PostToolUse | Manual-since-agent tracking |
| `todo_persistence_check` | todo_write | Reset/shrink detection |
| `re_read_turn_guard` | read_file post | Re-read storms |
| `post_tool_failure_coach` | PostToolUseFailure | Recovery coaching |
| `stop_brevity` | Stop | **Blocks** only severe essay finals once/turn (soft thresholds) |

State: `~/.grok/state/`. Install: `scripts/install-grok-hooks.sh`.

## Design notes

- Input: Grok camelCase (`toolName`, `toolInput`, `sessionId`); snake_case accepted.
- Coaching: `decision=allow` + `hookSpecificOutput.additionalContext`; PostToolUse tips are **queued** and flushed on the next PreToolUse.
- Spawn/swarm tips share one short `SPAWN_TIP` in `_common.py` (“always subagents + parallelize”) — not long situational essays.
- `strreplace_check` and `stop_brevity` are the only hard blocks by default.
