# Grok Build CLI — harness results log

Tracking for the Grok port of this repo. Install cutover: **2026-07-25 ~11:33** (commit `7dcec8c`, `scripts/install-grok-hooks.sh`).

Raw numbers: [`results-2026-07-26.json`](results-2026-07-26.json).

## What we added into Grok

| Piece | Where it lives |
|-------|----------------|
| Hook suite (15 scripts) | [`hooks/grok/`](../../hooks/grok/) |
| Hook registration | `~/.grok/hooks/agent-harness-optimizations.json` ← from [`hooks/grok-harness.json`](../../hooks/grok-harness.json) |
| Global rules (swarm, tools, context) | `~/.grok/AGENTS.md` marker section ← [`AGENTS.grok.md`](../../AGENTS.grok.md) |
| Per-session state | `~/.grok/state/` (batch / swarm / re-read / tips trackers) |
| Installer | [`scripts/install-grok-hooks.sh`](../../scripts/install-grok-hooks.sh) |

**Hard blocks:** `strreplace_check` (stale `old_string`), `stop_brevity` (severe essay Stop only, once/turn — soft thresholds after 2026-07-27).  
**Coaching (allow + tip):** shell native-tools, batch, swarm/discovery, re-read, line-offset, parallel-agent, background spawn, todo persistence, failure coach.

Also co-exists with the separate **response-length** rules already at the top of `~/.grok/AGENTS.md` (brevity budget); harness section is appended below the markers.

## Method (2026-07-26 snapshot)

- Source: `~/.grok/sessions/**/chat_history.jsonl` over the last **5 days** (2026-07-21 → 2026-07-26).
- **Before:** 83 sessions with activity, mtime before cutover, no harness AGENTS marker in context.
- **After:** 71 sessions that injected the `agent-harness-optimizations (grok)` AGENTS section.
- Shell “discovery” = `run_terminal_command` whose command uses `cat` / `head` / `tail` / `find` / `rg` / `grep` / bare `ls` patterns.
- Finals = assistant messages with no tool calls (user-visible answers).
- “Essay final” = ≥200 words **and** ≥3 markdown headers.

Caveats: task mix isn’t controlled (product work vs one-off Q&A). Spawn remains rare in absolute terms. Response-length rules predated hooks and likely share credit for shorter finals.

## Before / after (primary table)

| Metric | Before | After (harness in context) | Δ |
|--------|--------|----------------------------|---|
| Sessions | 83 | 71 | — |
| Shell share of tools | **37.2%** | **24.4%** | −34% rel |
| Native discovery (`read_file`+`grep`+`list_dir`) | 41.3% | **57.2%** | +38% rel |
| Shell discovery cmds / session | **19.7** | **8.5** | −57% |
| Re-reads / session | 4.9 | 3.3 | −33% |
| Parallel tool batches (% of tool turns) | 62.9% | 67.3% | +7% rel |
| Sessions using `spawn_subagent` | 1.2% | 2.8% | still rare |
| Spawn / session | 0.01 | 0.09 | ↑ but small n |
| Median final words | **193** | **132** | −32% |
| Mean final words | 324 | 245 | −24% |
| p90 final words | 899 | 513 | −43% |
| Long finals (≥200 words) | 48.1% | 36.4% | −11.7 pp |
| Essay finals (≥200w + ≥3 headers) | **46.5%** | **17.4%** | −29 pp |
| Mean headers in finals | 4.2 | 1.5 | −64% |

### Tool mix shift

| Tool | Before | After |
|------|--------|-------|
| `run_terminal_command` | 37.2% | 24.4% |
| `read_file` | 28.3% | **39.6%** |
| `grep` | 10.8% | 13.7% |
| `list_dir` | 2.2% | 4.0% |
| `spawn_subagent` | ~0% | 0.2% |

### Daily trend (mtime day)

| Day | Sess | Harness | Shell % | Shell-discovery cmds | Median-ish signal |
|-----|------|---------|---------|----------------------|-------------------|
| 07-21 | 14 | 0 | 34% | 351 | pre |
| 07-22 | 3 | 0 | 53% | 144 | pre |
| 07-23 | 7 | 0 | 52% | 93 | pre |
| 07-24 | 33 | 0 | 39% | 732 | pre |
| 07-25 | 66 | 31 | 32% | 1001 | install day |
| 07-26 | 41 | 40 | **27%** | 456 | after |

Hook state after install (active coaching): ~76 sessions with batch/swarm/discovery trackers, ~70 with file-read trackers, tips queued in `pending-tips-*.json`.

## Still weak / next

1. **`spawn_subagent` adoption** — still rare. Coaching tips did not reach the model (PreToolUse `additionalContext` is not a Grok input). 2026-08-28 subtract unregistered those coaches. Next metric is spawn rate from `signals.json` / `updates.jsonl` after the subtract, plus a `CANARY_GROK_CTX_v1` channel probe. Do not treat this table as proof hooks tutored the model.
2. **Shell discovery share of shell** stayed ~73–76% — fewer discovery shells overall, but when shell is used it still often looks like discovery (git/build shells mixed in measurement).
3. **Brevity** improved a lot; residual long answers still happen on multi-step ship tasks (expected). Credit predates-hooks response-length rules in AGENTS.md.

## How to re-run

Re-parse last N days of Grok session logs, split on harness AGENTS marker + cutover time, refresh this file and the JSON sibling. Keep new snapshots as `docs/grok/results-YYYY-MM-DD.md` if the table grows.
