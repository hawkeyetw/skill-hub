#!/usr/bin/env bash
# skill-hub install script - the thing skill-hub has to provide itself because
# OpenCode has no native marketplace/registry mechanism (see
# architecture/01-registry-model.md decision 1).
#
# Usage: install.sh <skill-name> [target-dir]
#   target-dir defaults to ./.agents/skills (project-level, agentskills.io convention,
#   readable by OpenCode, Claude Code, and any other agentskills.io-compatible tool).
#   Pass ~/.config/opencode/skills for a global OpenCode install instead.
set -euo pipefail

SKILL_HUB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="${1:?usage: install.sh <skill-name> [target-dir]}"
TARGET_BASE="${2:-./.agents/skills}"
SRC="$SKILL_HUB_ROOT/registry/approved/$NAME"

if [[ ! -d "$SRC" ]]; then
  echo "error: '$NAME' is not in registry/approved/ (either it doesn't exist, or it hasn't cleared review yet)" >&2
  echo "approved skills:" >&2
  ls "$SKILL_HUB_ROOT/registry/approved" >&2 2>/dev/null || true
  exit 1
fi

MANIFEST="$SRC/skill-hub.json"
if [[ -f "$MANIFEST" ]]; then
  STATUS=$(python3 -c "import json; print(json.load(open('$MANIFEST')).get('review_status','unknown'))")
  if [[ "$STATUS" != "approved" ]]; then
    echo "error: '$NAME' manifest review_status is '$STATUS', not 'approved' - refusing to install" >&2
    exit 1
  fi
fi

mkdir -p "$TARGET_BASE"
DEST="$TARGET_BASE/$NAME"
rm -rf "$DEST"
cp -r "$SRC" "$DEST"
echo "installed '$NAME' -> $DEST"
echo "(OpenCode/Claude Code/any agentskills.io-reading tool pointed at $TARGET_BASE will now see it)"
