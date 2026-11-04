# CLAUDE.md: `mpl-review` skill project (fork branch `mpl-skill`)

This branch of `maaz7409/matplotlib` develops `/mpl-review`. It is a contributor-side
self-review skill for Matplotlib PRs, modelled on pandas' `/pandas-review`. Work is split
into sessions in `skill-reports/PLAN.md`. **Each session: read this file, then only your
session's section of PLAN.md, and update its status table when done.**

This file is loaded into every turn, so keep it short. Details go in PLAN.md or the reports.

## Layout

| Path | What |
|---|---|
| `.agents/skills/mpl-review/` | The skill (v5, final): `SKILL.md` (≤ 6 KB; every line costs tokens in every review) plus `scripts/fetch_context.py` (one call gathers the diff, thread and CI). `.claude/skills/mpl-review` is a symlink to it, as in pandas. |
| `skill-eval/` | Harness: `mk_clone.sh` (PR clone, base = merge-base), `run_review.sh` (headless run with caps), `tally.py` (tokens, cost, loop flags), `labels/` (`tuning-set.json` is biased; `fresh-set-2026-11.json` is held out) |
| `skill-reports/` | `skill-report.md` (quality), `token-report.md` (cost), `stats.md` (AI-usage stats), `issue.md` (draft upstream issue), `PLAN.md` (sessions), `raw/` (review outputs) |

## Hard rules

- **Never post to matplotlib/matplotlib** (issues, PRs, comments, reviews). Matplotlib's AI
  policy forbids agents interacting with the project. The user opens the issue or PR
  themselves, in their own words.
- **Only skill-project files on this branch.** No `lib/`, `src/` or other code fixes. Those
  were reverted in `2fdac0aa` (still recoverable from `76299c23`). Use a separate branch for
  code fixes.
- **This CLAUDE.md, `skill-eval/` and `skill-reports/` must never go into an upstream PR.**
  An upstream PR gets only `.agents/skills/mpl-review/` and the `.claude/skills/mpl-review`
  symlink (plus docs if maintainers ask), on a clean branch from upstream `main`.
- **Every review run goes through `skill-eval/run_review.sh`**, with its caps (`--max-budget-usd`,
  25-min timeout). Watch long runs with `tally.py`: flag repeated identical calls, any
  subagent, or more than 12 tool calls. Stop runaway runs early; v3 once ran the whole test
  suite twice.
- **No leakage.** `labels/tuning-set.json` (PRs 32380, 32331, 32285) is the tuning set.
  Report accuracy only on held-out PRs. `fresh-set-2026-11.json` (32537, 32504, 32515) was
  held out for v5. Once you edit SKILL.md after reading its outputs, it becomes tuning data
  too.
- **Verify labels by execution.** A tool's finding becomes a label only after you reproduce it.
- Ask before spending more than the session budget in PLAN.md. Default: ≤ $10 of review runs
  per session.

## Facts learned (don't re-derive)

- Cost ≈ API calls × context size; cache reads dominate. Subagents multiply both. Measured
  per review: v2 0.7–1.3M tokens ($0.7–1.2), v3 ≥ 4M ($3.9+, unfinished), v4 0.18–0.34M
  ($0.27–0.62), **v5 0.16–0.31M ($0.18–0.35, 25–81 s)**.
- The skill's purpose (same as pandas): a fast gate for *obvious* problems, so maintainers
  review the rest. Don't add deep bug-hunting to the default path; that is what made v3
  explode.
- pandas (2026-11-04): `pandas-review` moved to `.agents/skills/` with `fetch_context.py`.
  The policy PR pandas#70954 was approved by mroeschke but still has "Needs Discussion".
  Contributors post verdicts (e.g. #71767, #71823).
- Matplotlib modules are huge (`axes/_axes.py` is about 100k tokens): read around hunks, not
  whole files. Changed SVG/PDF baselines bloat diffs: exclude `*/baseline_images/*`.
- Cloud sessions: the GitHub API for upstream repos is blocked unless the repo is attached.
  `git fetch https://github.com/matplotlib/matplotlib refs/pull/N/head` and WebFetch of
  github.com pages work. Source builds fail (the `sheenbidi` download is blocked).
  Workaround for running code: `pip install matplotlib==3.11.2` into a venv, then swap in the
  PR's pure-Python files (works when the C extensions are unchanged).
- Headless runs: `claude -p ... < /dev/null`. Put logs outside the clone, or the skill
  reviews them as untracked files. `run_review.sh` copies the skill into the clone and hides
  it via `.git/info/exclude`.
- Matplotlib maintainers rarely use "request changes", so `review:changes_requested` search
  finds almost nothing. Get ground truth from review comments and from close reasons.
- Complex `while`/associative-array Monitor commands trip a safety check; put watchers in a
  small script instead.
- `pkill -f <pattern>` also kills your own shell when the pattern is in the command line.
  Use `pgrep -f "^claude -p"`, then kill the PIDs.
- Usage stats (see `stats.md`): since 2026-08-14 about 45% of Matplotlib PRs disclose AI
  use, about the same as pandas without its top account (jbrockmendel, 89% of pandas'
  Claude-trailer PRs). The user's GraphQL/REST stats scripts (`scripts/*.py`) are **not in
  the repo yet**; ask the user for them.

## Conventions

- Commit trailer lines go at the end of the message as the session's system prompt specifies.
  Push to `mpl-skill` and mirror to `claude/mpl-review-skill-proposal-024ntx`.
- Reports are plain, short Markdown with tables. Give numbers with their method and caveats.
