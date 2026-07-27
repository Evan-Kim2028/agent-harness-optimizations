# Grok Build harness rules (global)

Combine with response-length rules. Hooks reinforce these in-session.

## Always subagents + parallelize

**Default:** for anything beyond a short Q&A or a one-file tweak, **use `spawn_subagent` and parallelize**. Do not sequential-grind `read_file` / `grep` / shell across a multi-file or multi-concern task.

- Independent concerns → **multiple** `spawn_subagent` in **one** turn, `background=true`
- Exploration → `explore` agents; implementation slices → `general-purpose` (or role agents)
- After agents finish → parent integrates summaries; if integration needs >2 tools, spawn again
- Simple single-hop Q&A with no repo walk → direct answer is fine

Hooks inject a short **SWARM** tip when you keep grinding manually — treat it as a hard preference, not optional flavor.

| Question | If yes |
|----------|--------|
| >1 file or >1 concern? | Parallel `spawn_subagent` |
| Need exploration first? | `explore` subagent(s), `background=true` |
| >2 sequential tool calls expected? | Subagents / batch tools — not a long solo loop |
| Simple Q&A, no edits? | Direct response OK |

**4-call rule:** about to make a 4th sequential manual call (read/grep/shell) without an agent for this subtask → **stop and `spawn_subagent`**.

**Anti-pattern:** one agent early, then 50+ manual calls. Or serial foreground agents when they could run in parallel.

### Swarm pattern

1. Parallel explore agents for multi-concern discovery  
2. `todo_write` into single-file / single-concern tasks  
3. ≥3 items → parallel background coders  
4. Poll with `get_command_or_subagent_output`  
5. Integrate once

## Tool selection

- **Discovery:** `grep`, `list_dir`, `read_file` (with `offset`/`limit` on large files) — not `cat`/`find`/`rg` via Shell  
- **Shell:** git, tests, builds, package managers, long pipelines only  
- **No `cd`:** absolute paths or `git -C <path>`  
- **Edits:** `search_replace` with exact current text; re-read if it fails — do not retry stale strings  
- **Batch:** multiple independent reads/greps in one turn

## Context discipline

- Never re-read unchanged files; use different `offset` if needed  
- Large files: grep first, then windowed `read_file`  
- Delegate multi-file research so parent keeps summaries, not raw dumps  
- Bound shell output (`git log -n`, `docker logs --tail`, `find -maxdepth`)

## Todos

- Prefer `todo_write(merge=true)` status updates  
- Do not wipe completed items when adding work  

## Response length

See response-length section (scale to ask, structure budget, after-work template). Hooks may block severe essay-shaped finals once per turn.

## Self-check

1. First line is the answer?  
2. Should this be parallel subagents? (default yes if multi-file/multi-concern)  
3. Am I about to shell-cat a file native tools handle?  
4. Headers ≤ 2 / no closing offers?
