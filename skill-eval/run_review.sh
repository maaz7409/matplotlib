#!/bin/bash
# Usage: run_review.sh <clone-dir> <skill|cr> <out.jsonl> [skill-dir] [budget-usd] [effort] [model]
# One headless review with hard caps (budget, 25-min timeout). Logs stream-json OUTSIDE the clone.
# skill: copies <skill-dir> (default: this repo's .agents/skills/mpl-review) into the clone as
#        .agents/skills/mpl-review + .claude/skills symlink, hidden via .git/info/exclude so the
#        review never sees it in the diff or as untracked files.
clone=$1; mode=$2; out=$3; budget=${5:-4}; effort=${6:-high}; model=${7:-claude-opus-5-5}
skill=${4:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/.agents/skills/mpl-review}
rm -rf ~/.claude/skills/mpl-review   # avoid a stale user-level copy shadowing the project one
if [ "$mode" = skill ]; then
  mkdir -p "$clone/.agents/skills" "$clone/.claude/skills"
  rm -rf "$clone/.agents/skills/mpl-review" "$clone/.claude/skills/mpl-review"
  cp -r "$skill" "$clone/.agents/skills/mpl-review"
  ln -s ../../.agents/skills/mpl-review "$clone/.claude/skills/mpl-review"
  printf '.agents/\n.claude/\n' >> "$clone/.git/info/exclude"; prompt="/mpl-review"
else prompt="/code-review high $(git -C "$clone" branch --show-current)"; fi
cd "$clone"; start=$(date +%s)
timeout 1500 claude -p "$prompt" --model "$model" --effort "$effort" --output-format stream-json --verbose \
  --allowedTools "Bash Read Grep Glob Agent Task" --disallowedTools "Edit Write NotebookEdit" \
  --max-budget-usd "$budget" < /dev/null > "$out" 2> "${out%.jsonl}.err"
echo "$(basename "$out") wall=$(( $(date +%s) - start ))s exit=$?"
