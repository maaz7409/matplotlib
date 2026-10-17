#!/bin/bash
# Usage: mk_clone.sh <dest-dir> <PR-number>
# Fresh clone of the local repo checked out at the upstream PR head, with origin/main
# (and main) set to the PR's merge-base, so "diff vs main" is exactly the PR.
set -e
dest=$1; n=$2; src=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
git -C "$src" fetch -q https://github.com/matplotlib/matplotlib "refs/pull/$n/head:refs/upr/$n"
git -C "$src" fetch -q https://github.com/matplotlib/matplotlib main:refs/upr/main 2>/dev/null || true
mb=$(git -C "$src" merge-base "refs/upr/$n" refs/upr/main)
rm -rf "$dest"; git clone -q --shared --no-checkout "$src" "$dest"
git -C "$dest" fetch -q "$src" "refs/upr/$n:refs/heads/pr-$n"; git -C "$dest" checkout -q "pr-$n"
git -C "$dest" branch -f main "$mb"
git -C "$dest" remote set-url origin https://github.com/matplotlib/matplotlib
git -C "$dest" for-each-ref --format='%(refname)' refs/remotes/origin | xargs -r -n1 git -C "$dest" update-ref -d
git -C "$dest" update-ref refs/remotes/origin/main "$mb"
git -C "$dest" symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
echo "$dest at PR #$n, base ${mb:0:10}: $(git -C "$dest" diff --stat "$mb" | tail -1)"
