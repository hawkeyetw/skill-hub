#!/usr/bin/env bash
# skill-hub CI hook: runs on the "internal git server" (this bare repo) whenever
# something is pushed to main. This is the "CI 在 merge 后..." step from
# .trellis/spec/architecture/03-deployment-and-auth.md Phase 1, implemented with
# nothing but a git hook - no GitHub Actions/GitLab CI needed, matching the
# intranet-only constraint.
#
# This file is tracked in the repo (scripts/post-receive-hook.sh) and copied to
# <bare-repo>/hooks/post-receive by scripts/setup_git_ci_demo.sh - git hook
# directories are not themselves version-controlled by git, so keeping the
# canonical copy here is the only way to review/diff changes to it.
#
# What it does on every push to main:
#   1. Clones this bare repo into a scratch worktree at the pushed commit (a real
#      `git clone`, not a manual checkout-into-bare-repo trick - an earlier
#      version of this hook used `--work-tree checkout -f rev -- .` against the
#      bare repo directly, which left the resulting commit with NO PARENT (an
#      orphan root commit) - `git pull` on any real clone then refused with
#      "unrelated histories". Cloning properly sets up HEAD/index/parent
#      linkage, so the CI commit is a normal, fast-forwardable child of the
#      pushed commit.
#   2. Runs review_pipeline.py --approve against every skill still sitting in
#      registry/pending/ (i.e. anything newly added/changed by this push).
#   3. Regenerates index.json / marketplace.json / catalog.html / audit.html.
#   4. Commits the result ("CI: automated review pass") and pushes it back to
#      this same bare repo. That push re-triggers this hook once more, but by
#      then registry/pending/ is empty of anything the first pass didn't already
#      resolve, so the second invocation is a harmless no-op and recursion
#      terminates there.
set -euo pipefail

# Git hooks inherit GIT_DIR (and friends) pointing at THIS bare repo from the
# receiving git process. Left set, every `git` call below (clone, checkout, add,
# commit) silently operates against the bare repo instead of the fresh clone we
# make below - clone "succeeds" but then `cd $WORKTREE && git checkout` fails
# with "fatal: not a git repository: '.'" because git ignores cwd and goes
# straight for $GIT_DIR. Unset before doing anything else.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE || true

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

while read -r oldrev newrev refname; do
  branch="$(basename "$refname")"
  [[ "$branch" == "main" || "$branch" == "master" ]] || continue
  [[ "$newrev" != "0000000000000000000000000000000000000000" ]] || continue  # branch deletion

  echo "[skill-hub CI] push received on $branch ($oldrev -> $newrev)"

  WORKTREE="$(mktemp -d)"
  git clone -q "$REPO_DIR" "$WORKTREE"
  cd "$WORKTREE"
  git checkout -q "$newrev"

  pending_count=0
  for skill_dir in registry/pending/*/; do
    [[ -d "$skill_dir" ]] || continue
    pending_count=$((pending_count + 1))
    name="$(basename "$skill_dir")"
    echo "[skill-hub CI] reviewing: $name"
    python3 scripts/review_pipeline.py "$name" --approve || echo "[skill-hub CI] $name did not pass (see audit log)"
  done

  if [[ "$pending_count" -eq 0 ]]; then
    echo "[skill-hub CI] nothing pending, nothing to do"
    rm -rf "$WORKTREE"
    continue
  fi

  python3 scripts/generate_index.py
  python3 scripts/generate_catalog_html.py
  python3 scripts/generate_audit_html.py

  git add -A
  if git diff --cached --quiet; then
    echo "[skill-hub CI] no changes to commit after review"
  else
    git -c user.email="skill-hub-ci@internal" -c user.name="skill-hub CI" \
      commit -q -m "CI: automated review pass ($pending_count skill(s) processed)"
    git push -q origin "HEAD:$branch"
    echo "[skill-hub CI] committed and pushed review results as $(git rev-parse HEAD)"
  fi

  rm -rf "$WORKTREE"
done

echo "[skill-hub CI] done - pull to see the results (approved/rejected state, catalog.html, audit.html)"
