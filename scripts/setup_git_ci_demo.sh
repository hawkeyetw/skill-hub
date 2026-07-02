#!/usr/bin/env bash
# One-shot setup for the "git push triggers CI review" demo. Tears down and
# recreates:
#   - /root/skill-hub-git-server/skill-hub.git  (bare repo = "internal git server")
#   - /root/skill-hub/.git                       (your local working copy)
# then does the first commit+push, which triggers the post-receive hook and
# shows the CI review pass happening live. Run scripts/reset_demo.sh first if
# you want the 4 fixtures back in registry/pending/ before this.
#
# See .trellis/spec/architecture/03-deployment-and-auth.md Phase 1 for why this
# is a git hook and not GitHub Actions/GitLab CI (intranet-only, no cloud CI available).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_SERVER="/root/skill-hub-git-server/skill-hub.git"

echo "=== tearing down existing git state ==="
rm -rf "$ROOT/.git" "$(dirname "$GIT_SERVER")"

echo "=== creating bare repo (the 'internal git server') ==="
mkdir -p "$(dirname "$GIT_SERVER")"
git init --bare -q "$GIT_SERVER"
# git init --bare defaults HEAD to refs/heads/master on older git; force main so
# the hook's `git clone` below doesn't hit "remote HEAD refers to nonexistent ref".
git -C "$GIT_SERVER" symbolic-ref HEAD refs/heads/main

echo "=== installing CI hook ==="
cp "$ROOT/scripts/post-receive-hook.sh" "$GIT_SERVER/hooks/post-receive"
chmod +x "$GIT_SERVER/hooks/post-receive"

echo "=== initializing local working copy and pushing ==="
cd "$ROOT"
git init -q
git config user.email "cbw@internal"
git config user.name "cbw"
git remote add origin "$GIT_SERVER"
git add -A
git commit -q -m "Initial commit: skill-hub project (trellis scaffold, architecture/security spec, review pipeline scripts, 4 demo fixtures)"
git branch -M main

echo "=== pushing (watch the CI review run inline below) ==="
git push -u origin main

echo
echo "=== pulling CI's commit back down ==="
git pull -q origin main
echo
git log --oneline --graph --all
echo
echo "done. registry/approved, registry/rejected, registry/audit-log.jsonl, catalog.html,"
echo "and audit.html now reflect the automated review pass, all recorded as a real git commit."
