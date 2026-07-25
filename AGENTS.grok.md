# Grok Build harness rules (global)

Combine with response-length rules. Hooks reinforce these in-session.

## Parallel execution first

Before non-trivial work, decide strategy. Default is **not** single-threaded grinding.

| Question | If yes |
|----------|--------|
| >1 file or >1 concern? | Parallel `spawn_subagent` |
| Need exploration first? | `explore` subagent(s), `background=true` |
| >2 sequential tool calls expected? | Prefer subagents / batch tools |
| Simple Q&A, no edits? | Direct response OK |

**4-call rule:** about to make a 4th sequential manual call (read/grep/shell) without an agent for this subtask → stop and delegate.

**Anti-pattern:** dispatch agents early, then 50+ manual calls. After agents return, if integration needs >2 tools, spawn again.

### Swarm pattern

1. Parallel explore agents for multi-concern discovery  
2. `todo_write` into single-file / single-concern tasks  
3. ≥3 items → parallel background coders  
4. Poll with `get_command_or_subagent_output`  
5. Integrate once

Dispatch **independent** agents in **one** turn with `background=true`.

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

See response-length section (scale to ask, structure budget, after-work template). Hooks may block essay-shaped finals once per turn.

## Self-check

1. First line is the answer?  
2. Could this be parallel subagents?  
3. Am I about to shell-cat a file native tools handle?  
4. Headers ≤ 2 / no closing offers?
