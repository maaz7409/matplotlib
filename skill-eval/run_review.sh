#!/bin/bash
# Usage: run_review.sh <clone-dir> <skill|cr> <out.jsonl> [SKILL.md] [budget-usd] [effort] [model]
# Runs one headless review with hard caps (budget, 25-min timeout). Logs stream-json OUTSIDE the clone.
# skill: installs SKILL.md at ~/.claude/skills/mpl-review/ (run skill variants sequentially!)
clone=$1; mode=$2; out=$3; skill=${4:-}; budget=${5:-4}; effort=${6:-high}; model=${7:-claude-opus-5-5}
if [ "$mode" = skill ]; then
  mkdir -p ~/.claude/skills/mpl-review && cp "$skill" ~/.claude/skills/mpl-review/SKILL.md; prompt="/mpl-review"
else prompt="/code-review high $(git -C "$clone" branch --show-current)"; fi
cd "$clone"; start=$(date +%s)
timeout 1500 claude -p "$prompt" --model "$model" --effort "$effort" --output-format stream-json --verbose \
  --allowedTools "Bash Read Grep Glob Agent Task" --disallowedTools "Edit Write NotebookEdit" \
  --max-budget-usd "$budget" < /dev/null > "$out" 2> "${out%.jsonl}.err"
echo "$(basename "$out") wall=$(( $(date +%s) - start ))s exit=$?"
