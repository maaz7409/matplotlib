# `/mpl-review` skill vs `/code-review`: findings

Date: 2026-10-17 · Branch: `mpl-skill` · Skill: `.claude/skills/mpl-review/SKILL.md`

> **Update (v4):** The benchmark below measured the first version (v2). The current skill is
> the lean v4. It uses about 4× fewer tokens than v2 and much less than v3, and on the same
> 3 PRs it found 3 of 4 verified blockers with 3 of 3 correct verdicts. See `token-report.md`.
> The usage figures were corrected using full GitHub API access; see `stats.md`.

## TL;DR

| Question | Answer |
|---|---|
| 0. Environment OK? | Mostly. git, push to the fork, the headless `claude` CLI and github.com pages all worked. **The GitHub API for the upstream repos was blocked**, so the stats come from git refs plus GitHub search pages, and the benchmark could not test the skill's "read the PR thread" step. |
| 1. Is `/pandas-review` better than `/code-review`? | **Different, not strictly better.** In my test, `/code-review high` found **more real bugs** (2 of 3 blockers vs 1 of 3) but also more **noise** (about 5 findings that were false or speculative vs 0) and gives **no verdict**. The skill wins on precision, verdicts, project conventions and executed repros, and costs about 1.6× as much and takes about 1.9× as long. |
| 2. Usage? | **Corrected (see `stats.md`).** Since 2026-08-14, when both repos ask a yes/no AI question: Matplotlib **45%** of PRs show AI use; pandas 77%, or **47% without its top account** (the skill's author). About 60% of authors in both repos used AI. My first estimate for Matplotlib (2–7%) was wrong: it only counted trailers and the word "Claude", while most Matplotlib disclosures just say "AI". |
| pandas vs Matplotlib | **The usage level is similar.** The differences are cultural: Matplotlib has a stricter AI policy and no maintainer championing a skill. It works for Matplotlib, pitched as an optional self-check. |
| 2.5. Clashes? | **No existing issue or PR proposes a review skill or adds agent files.** Related: #30848 and #31457 (AI-policy discussions, where `AGENTS.md` was suggested but never added), #31026, #31124 and #31507 (AI disclosure in the PR template). |
| 3. Built and benchmarked? | Yes. I wrote a 6.4 KB skill (pandas-review is 9.7 KB), ran 6 timed reviews on 3 open PRs, and spent **$4.93** on benchmark runs. |

---

## 1. `/pandas-review` vs the built-in `/code-review`

The two tools do different jobs:

| | `/code-review` (built-in) | `/pandas-review` / `/mpl-review` |
|---|---|---|
| Goal | Hunt for bugs in a diff | Pre-review a PR as a maintainer would, for its author |
| Reads the PR thread (reviews, inline comments, linked issue) | No | **Yes**, and gives maintainer positions top priority |
| Knows project rules (whatsnew or API notes, deprecations, stubs, test style) | Only via CLAUDE.md, which pandas and Matplotlib don't have | **Yes**, written into the skill |
| Runs tests and repros | Usually not (it didn't in my runs) | **Yes**, it is told to show real output |
| Output | A JSON list of findings and no verdict. It targets about 5 findings ("Four findings came out, which is below the 5 target") | Ranked findings plus a **verdict** (`LGTM` … `CLOSE`) and a "stop iterating" rule |
| Guardrails | Can post (`--comment`) or edit (`--fix`) | Never posts or edits; tells the author to reply in their own words |
| What it is told to skip | Little | Hygiene, CI, description drift, lint, anything that is fine |

So the skill is a **workflow and policy layer**. Its bug-finding power comes from the same
model as `/code-review`; it does not have a better bug detector. The verdict and the
"don't report" list are what save maintainer time, because they cut noise and tell the
author when to stop. The thread-reading step also matters: a large share of real review
blockers are "a maintainer already said X", and `/code-review` cannot see those.

## 3. The benchmark

### Setup

- **Model / effort**: `claude-opus-5-5`, `--effort high` for both. The command was
  `/code-review high pr-N` against `/mpl-review`. Each ran headless (`claude -p`) in its own
  fresh clone, checked out at the PR head, with `origin/main` set to the PR's merge-base. See
  `raw/run.sh`.
- **Tools allowed**: read-only intent (Bash, Read, Grep, Glob, Agent), with Edit and Write
  disabled.
- **No PR thread access**: the GitHub API was blocked here, so both tools reviewed the diff
  only. This **removes the skill's main advantage**.
- **PRs** (open, chosen to be tricky in different ways):
  - **#32380** FigureImage transform: tiny and correct. Tests false positives.
  - **#32331** mathtext operator spacing: subtle parser logic and changed baseline images.
  - **#32285** Qt figure options legend: about 130 lines that copy legend state.

### Ground truth

I labelled each PR by reading the code and **running** the cases. I built a 3.11.2 wheel
with the PR's Python files swapped in and compared rendered widths. Two labels came from
the tools themselves; I only kept them after reproducing them (marked †).

| PR | ID | Label | Severity | How verified |
|---|---|---|---|---|
| 32380 | – | Fix is correct; the new test fails on main | **LGTM** | Reasoning; skill run |
| 32380 | n1 | Comment says the transform is "always identity", but `transform=` still overrides it | nit | Reading |
| 32331 | **B1** | `\overset{?}{=}`, `\underset{x}{\leftarrow}` and `{=}` lose relation spacing. amsmath makes these `\mathrel`, so TeX keeps the spacing. The PR's own regenerated baseline (`mathtext1_dejavusans_01`) records this regression | **blocking** | width `$a \overset{?}{=} b$`: 25 → 21 |
| 32331 | **B2**† | `<` and `>` count as delimiters, so mid-expression `$a<=b$` and `$x->y$` lose a space but `$a>=b$` does not | **blocking** | widths 38→36 vs 38→38 |
| 32331 | n1 | API note named after the issue (`23315-AM.rst`), not the PR (`32331-AM.rst`) | nit | README rule |
| 32331 | o1 | Binary operator at the end (`$a+$`) still spaced on the left (TeX makes it Ord) | optional | Reasoning |
| 32331 | o2 | `\left( x=\right)` vs `(x=)` handled inconsistently | optional | widths 26 vs 25 |
| 32285 | **B1**† | `facecolor='none'` (or `edgecolor`) plus framealpha → after regeneration the legend background is **80% black** | **blocking** | `(0,0,0,0)` → `(0,0,0,0.8)` |
| 32285 | o1 | `labelcolor`, `markerfirst`, `reverse`, `handler_map` and the shadow dict are still lost | optional | Skill repro |
| 32285 | n1 | Leftover `ncols` handling in the else branch | nit | Reading |

Expected verdicts: #32380 **LGTM**, #32331 **NEEDS WORK**, #32285 **NEEDS WORK**.

### Results

| PR | Tool | Wall time | Cost | Blockers found | Nits/optional found | False or speculative findings | Verdict |
|---|---|---:|---:|---|---|---:|---|
| 32380 | **/mpl-review** | 115 s | $0.74 | – (none exist) | 0/1 | **0** | **LGTM ✅** |
| 32380 | /code-review high | 56 s | $0.39 | – | 1/1 | 3 ¹ | none |
| 32331 | **/mpl-review** | 289 s | $1.12 | B2 ✅ (executed repro), B1 ❌ | 3/3 | **0** | **NEEDS WORK ✅** |
| 32331 | /code-review high | 214 s | $0.91 | B2 ✅, B1 ❌ ² | 3/3 | 2 false ³ + 2 speculative ⁴ | none |
| 32285 | **/mpl-review** | 292 s | $1.19 | B1 ❌ | 2/2 (executed repro) | **0** | NITS ONLY ❌ |
| 32285 | /code-review high | 95 s | $0.58 | **B1 ✅** | 2/2 | 2 speculative ⁵ | none |
| **Total** | **/mpl-review** | **696 s** (avg 3.9 min) | **$3.05** | **1 / 3** | 5 / 6 | **0** | **2 / 3 correct** |
| **Total** | /code-review high | **365 s** (avg 2.0 min) | **$1.88** | **2 / 3** | 6 / 6 | **≈ 9** | n/a |

1. Claimed that `is_transform_set()` now being True is a public behavior change needing an
   API note (the skill checked every caller and showed nothing that worked before breaks); a
   `stale_callback` problem that exists in `Figure.add_artist` on main and is not this PR's;
   and a missing subfigure test.
2. `/code-review` looked at the changed `\overset` baseline and called it "consistent with
   the code", which accepts the regression.
3. "Leading tab now spaced" and "`\substack` row end" both give **identical output** before
   and after the PR (verified).
4. A performance worry (building sets per token) and a suggested rewrite of the design.
5. `framealpha=None` after a manual `set_alpha(None)` (contrived), and an approach rewrite
   (keep the legend object).

### What the numbers say

- **Recall of real blockers**: `/code-review` 2/3, skill 1/3, from n = 3 PRs and one run
  each. LLM runs vary, so a single miss is weak evidence. Still, `/code-review`'s "hunt for
  about 5 findings" recipe digs further.
- **Precision**: the skill reported **no** false or speculative findings in three runs;
  `/code-review` reported about 9. On the clean PR (#32380) `/code-review` gave a newcomer 4
  "issues" to chase, while the skill said LGTM and showed why the suspicious-looking
  `is_transform_set` change is safe. For a contributor-facing tool, that difference matters.
- **Verdict**: the skill was right on 2 of 3. It under-called #32285 because it missed the
  `'none'` colour bug.
- **Evidence**: on its own initiative the skill built a working environment (3.11.2 wheel
  plus the PR's sources, and Xvfb plus PyQt6 for the Qt PR). It showed that each new test
  **fails on main and passes on the PR**, and **executed** its repros. `/code-review` ran
  nothing and labelled everything as read-only reasoning.
- **Both missed B1 on #32331**: the author described the changed `\overset` baseline as
  "correct", and neither tool challenged that.
- **Time and cost**: the skill takes about 1.9× the wall time and about 1.6× the cost,
  almost all of it spent building an environment and running tests. That cost would mostly
  disappear for a contributor with a working dev install.

### Answer to Q1

The pandas-style skill is **not a better bug finder** than `/code-review`. It is a **better
pre-review**: less noise, an actionable verdict, project rules, real repros, and (untested
here) awareness of the PR thread. If the goal is "catch the most bugs", `/code-review high`
did better on this small sample. If the goal is "send maintainers fewer, cleaner PRs and
tell authors when to stop", the skill fits better. The two can also be combined (run both,
about $5 per PR).

### Improvements suggested by this run (not applied, to keep the tested version honest)

1. Treat every **baseline image the PR changes** as a claim to verify: "the author says this
   change is correct; check it against TeX, usetex or main" (would target the #32331 B1 miss).
2. When state is copied or round-tripped (such as rebuilding an object from another's
   getters), probe the **sentinel values** `'none'`, `None`, `'inherit'` and alpha
   (would target the #32285 B1 miss).
3. Optionally: "after your own pass, look for 2–3 more defects before writing the verdict",
   to borrow some of `/code-review`'s recall without its quota.

## pandas vs Matplotlib

- **pandas** already has `AGENTS.md`, a policy that asks for tool, model and effort, a
  backed-up review queue, a maintainer who champions the skill, and a large and rising share
  of Claude Code PRs. Asking contributors to run `/pandas-review` is a natural fit there.
- **Matplotlib** has a stricter AI policy. It lists "solving topics that you wouldn't be able
  to solve yourself without AI" and agents interacting with GitHub as unacceptable, and the
  PR summary must be in the author's own words. AI use is *not* low: about 45% of recent PRs
  disclose it (`stats.md`), and AI PRs are closed unmerged about twice as often. Maintainers in #31457 and #30848 favoured
  `AGENTS.md` and better review strategies over tooling, so a mandatory "run this and post
  the verdict" request like pandas' would probably not be welcome.
- **It still works for Matplotlib.** The skill found real problems and produced correct
  verdicts on 2 of 3 PRs. The right pitch is "**optional** self-check for contributors who
  already use an agent; never post its output". That is how `issue.md` frames it.

## How to reproduce or run it yourself

```bash
# in a matplotlib checkout, on your PR branch, with the skill present at
# .claude/skills/mpl-review/SKILL.md (or ~/.claude/skills/mpl-review/SKILL.md)
claude --model claude-opus-5-5 --effort high
> /mpl-review            # local mode: reviews the current branch vs upstream main
> /mpl-review 32331      # PR mode: also reads the thread via `gh` (needs gh auth)
> /code-review high      # built-in, for comparison
```

The raw outputs of all 6 runs are in `raw/`, and the headless runner is `raw/run.sh`.

## Limitations

- n = 3 PRs and one run per tool. Treat these as anecdotes, not statistics.
- I made the ground truth, and two labels were found by the tools themselves; all labels
  were verified by execution.
- No PR-thread access, so the skill's maintainer-position check was not tested.
- Stats: commit trailers undercount, and search over PR text overcounts (see `stats.md`).
