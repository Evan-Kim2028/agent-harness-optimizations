#!/usr/bin/env bash
# Install Grok Build harness hooks + merge AGENTS.grok.md into ~/.grok/AGENTS.md
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
GROK_HOME="${GROK_HOME:-$HOME/.grok}"
HOOKS_DIR="$GROK_HOME/hooks"
STATE_DIR="$GROK_HOME/state"
MARKER_BEGIN="# --- agent-harness-optimizations (grok) BEGIN ---"
MARKER_END="# --- agent-harness-optimizations (grok) END ---"

mkdir -p "$HOOKS_DIR" "$STATE_DIR"

# Point global hooks at repo scripts (editable in place)
cp -f "$REPO/hooks/grok-harness.json" "$HOOKS_DIR/agent-harness-optimizations.json"
# Substitute portable placeholder with this clone's absolute path
sed -i "s|__REPO_ROOT__|$REPO|g" "$HOOKS_DIR/agent-harness-optimizations.json"

chmod +x "$REPO"/hooks/grok/*.py 2>/dev/null || true

# Drop leftover copies from older installs
rm -f "$HOOKS_DIR/lor-path-first.json" "$HOOKS_DIR/lor_path_first.py"

# Merge AGENTS.grok.md into ~/.grok/AGENTS.md (idempotent via markers)
AGENTS="$GROK_HOME/AGENTS.md"
EXTRA="$REPO/AGENTS.grok.md"
if [[ -f "$EXTRA" ]]; then
  if [[ -f "$AGENTS" ]] && grep -qF "$MARKER_BEGIN" "$AGENTS"; then
    # Replace existing block
    tmp="$(mktemp)"
    awk -v b="$MARKER_BEGIN" -v e="$MARKER_END" '
      $0==b {skip=1; next}
      $0==e {skip=0; next}
      !skip {print}
    ' "$AGENTS" >"$tmp"
    {
      cat "$tmp"
      echo ""
      echo "$MARKER_BEGIN"
      cat "$EXTRA"
      echo "$MARKER_END"
    } >"$AGENTS"
    rm -f "$tmp"
  else
    {
      if [[ -f "$AGENTS" ]]; then cat "$AGENTS"; echo ""; fi
      echo "$MARKER_BEGIN"
      cat "$EXTRA"
      echo "$MARKER_END"
    } >"${AGENTS}.new"
    mv "${AGENTS}.new" "$AGENTS"
  fi
fi

echo "Installed:"
echo "  $HOOKS_DIR/agent-harness-optimizations.json"
echo "  $AGENTS (harness section)"
echo "  state dir: $STATE_DIR"
echo ""
echo "Start a NEW Grok session (or /hooks reload) so hooks load."
echo "Verify with /hooks-list or the Hooks tab."
