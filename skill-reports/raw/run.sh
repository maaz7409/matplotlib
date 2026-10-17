#!/bin/bash
# usage: run.sh <skill|cr> <PR>
t=$1; n=$2; S=$(dirname "$0"); d=$S/$t-$n
if [ $t = skill ]; then p="/mpl-review"; else p="/code-review high pr-$n"; fi
cd $d
start=$(date +%s)
claude -p "$p" --model claude-opus-5-5 --effort high --output-format json \
  --allowedTools "Bash Read Grep Glob Agent Task" --disallowedTools "Edit Write NotebookEdit" \
  --max-budget-usd 8 > $S/out-$t-$n.json 2> $S/err-$t-$n.log
echo "$t $n wall=$(( $(date +%s) - start ))s" >> $S/times.log
