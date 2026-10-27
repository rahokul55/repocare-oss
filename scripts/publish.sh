#!/usr/bin/env bash
# Push an existing local source tree to a public empty repository created by its owner.
set -euo pipefail
cd "$(dirname "$0")/.."
repo_url="${1:-https://github.com/rahokul55/repocare-oss.git}"
if [[ ! -d .git ]]; then git init; fi
git branch -M main
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$repo_url"
elif [[ "$(git remote get-url origin)" != "$repo_url" ]]; then
  echo 'Existing origin differs; refusing to replace it.' >&2
  exit 1
fi
git add .
if ! git diff --cached --quiet; then
  git commit -m 'Initial RegressionProof source release'
fi
git push -u origin main
