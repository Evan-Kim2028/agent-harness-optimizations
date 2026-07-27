# Grok Build CLI — tracking index

Dedicated place to track the Grok port of agent-harness-optimizations (separate from Kimi).

| Path | Purpose |
|------|---------|
| [`RESULTS.md`](RESULTS.md) | Before/after metrics, what landed in `~/.grok`, open gaps |
| [`results-2026-07-26.json`](results-2026-07-26.json) | Machine-readable snapshot |
| [`../../hooks/grok/`](../../hooks/grok/) | Hook source |
| [`../../hooks/grok/README.md`](../../hooks/grok/README.md) | Hook event map |
| [`../../AGENTS.grok.md`](../../AGENTS.grok.md) | Rules injected into `~/.grok/AGENTS.md` |
| [`../../scripts/install-grok-hooks.sh`](../../scripts/install-grok-hooks.sh) | Installer |
| [`../../config.grok.toml.example`](../../config.grok.toml.example) | Config notes |

**Live install targets:** `~/.grok/hooks/agent-harness-optimizations.json`, `~/.grok/AGENTS.md` (marker section), `~/.grok/state/`.
