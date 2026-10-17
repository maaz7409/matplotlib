#!/bin/bash
# run.sh <clone-name> <SKILL.md>: install skill at user level, run /mpl-review headless, stream-json log outside the clone
B=$(dirname $(readlink -f $0)); name=$1
cp $2 ~/.claude/skills/mpl-review/SKILL.md
cd $B/$name; start=$(date +%s)
claude -p "/mpl-review" --model claude-opus-5-5 --effort high --output-format stream-json --verbose \
  --allowedTools "Bash Read Grep Glob Agent Task" --disallowedTools "Edit Write NotebookEdit" \
  --max-budget-usd 4 < /dev/null > $B/$name.jsonl 2> $B/$name.err
echo "$name wall=$(( $(date +%s) - start ))s" >> $B/times.log
