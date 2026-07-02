#!/usr/bin/env bash
# Resets the demo to its starting state (all 4 fixtures back in registry/pending/,
# nothing approved/rejected/installed yet) so DEMO.md can be re-run from scratch.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# git doesn't track empty directories - once CI moves every fixture out of
# registry/pending/, that dir has no representation in the commit, and the next
# `git checkout`/`git clone` simply won't recreate it. mv into a nonexistent
# parent then fails ("No such file or directory"). Guard against that.
mkdir -p registry/pending

for d in registry/approved/* registry/rejected/*; do
  [[ -d "$d" ]] || continue
  name="$(basename "$d")"
  rm -f "$d/REJECTION_REASON.json"
  # restore review_status to pending in the manifest before moving back
  if [[ -f "$d/skill-hub.json" ]]; then
    python3 - "$d/skill-hub.json" <<'PY'
import json, sys
p = sys.argv[1]
m = json.load(open(p))
m["review_status"] = "pending"
json.dump(m, open(p, "w"), indent=2)
PY
  fi
  rm -rf "registry/pending/$name"
  mv "$d" "registry/pending/$name"
done

rm -rf demo-client/.agents registry/index.json registry/.claude-plugin registry/catalog.html registry/audit.html registry/audit-log.jsonl
echo "demo reset: all 4 fixtures back in registry/pending/, demo-client/, index, catalog, and audit log cleared"
ls registry/pending
