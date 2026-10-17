---
name: mpl-review
description: Self-review your own Matplotlib PR (or local branch before opening one) the way a Matplotlib maintainer would. Prints findings and a verdict in the terminal; never posts to GitHub or edits files.
disable-model-invocation: true
argument-hint: "[PR number]"
allowed-tools: Bash(gh pr view *), Bash(gh pr diff *), Bash(gh pr list *), Bash(gh api -X GET *), Bash(git diff *), Bash(git merge-base *), Bash(git rev-parse *), Bash(git branch --show-current), Bash(git remote -v), Bash(git show *), Bash(git log *), Bash(git status *), Bash(pytest *), Bash(python -m pytest *), Bash(python -c *), Read, Grep, Glob, Agent
---

Review a Matplotlib PR as a maintainer who did not write it, even if you did, and report
to its author. Target: $ARGUMENTS (a PR number → PR mode; anything else, including a
literal `$ARGUMENTS` → local mode). Verify claims in the description, commits and comments
instead of trusting them. Report only: never edit files, change git state, or post to GitHub.

## 1. Get the change

- **PR mode** (strip `#`): `gh pr view <n> --repo matplotlib/matplotlib --json title,author,state,isDraft,headRefOid,files,body`
  and `gh pr diff <n> --repo matplotlib/matplotlib`. If that fails, say so and stop.
- **Local mode**: `<up>` = the remote whose URL contains `matplotlib/matplotlib`. Diff with
  `git diff $(git merge-base HEAD <up>/main)`, and Read every `??` file from
  `git status --porcelain -uall`. If `gh pr list --repo matplotlib/matplotlib --head "$(git branch --show-current)" --author "@me" --json number`
  returns exactly one PR, also do step 2 for it.

The local tree is the code under review in local mode, or in PR mode when `git rev-parse HEAD`
equals `headRefOid`; otherwise read files with
`gh api -X GET "repos/matplotlib/matplotlib/contents/<path>?ref=<headRefOid>" -H "Accept: application/vnd.github.raw"`.
If local and `git log --oneline HEAD..<up>/main` is non-empty, say how many commits behind.

## 2. Read the thread

Run `gh api -X GET --paginate repos/matplotlib/matplotlib/<path>` for each of
`pulls/<n>/reviews` (verdicts), `pulls/<n>/comments` (inline), `issues/<n>/comments`
(conversation), and the linked issue's comments. Never truncate; write long output to a file
and Read it. A failed fetch is unknown, not empty: retry, or say the thread was not read.
Where a maintainer on the thread asked for something that conflicts with this file, follow the maintainer.

## 3. Investigate

Grep/Read the surrounding code and compare with how Matplotlib already does it. Consult
`doc/devel/{coding_guide,api_changes,testing,document}.rst` only when a question arises.
First check `python -c "import matplotlib; print(matplotlib.__file__)"` resolves into this tree
(an editable install elsewhere tests the wrong code). If it does and the tree is the code under
review, run the PR's new/changed tests and the existing test file for each touched module
(`pytest lib/matplotlib/tests/test_<mod>.py -x -q`), and every repro you report; show real
output. Otherwise say so and review by reading; don't build or install packages. To compare
with `main`, never swap tracked files, even temporarily: `git show <base>:<path>` into a temp
dir and load it from there.

## 4. What to look for (priority order)

1. **Maintainer position**: a core dev saying not to proceed, wanting another approach, or
   waiting on a decision outranks everything.
2. **Unaddressed review comments**: neither fixed in the diff nor answered with a reason.
   Don't draft replies; authors answer in their own words.
3. **Correctness, above all regressions** (worked on `main`, breaks now). Probe the inputs
   that historically break Matplotlib: empty / length-1 data, NaN/inf, masked arrays,
   integer vs float, datetime/category units, log/inverted axes, 2-D vs 1-D, `None` as
   "unset" vs a real value, rcParams defaults vs explicit kwargs, re-adding/removing artists,
   repeated draws, `stale` not set after a state change, DPI/savefig vs screen, and other
   backends that share the touched code. When state is copied, rebuilt from getters or
   round-tripped, remember getters return *resolved* values (RGBA with alpha baked in, resolved
   fonts), so feeding them back can re-apply alpha or defaults; probe `'none'`, `None`,
   `'auto'`, `'inherit'`, alpha, and rcParams-derived defaults. Partial coverage of sibling
   paths is an optional follow-up, not a defect.
   **Changed baseline images are claims, not evidence.** For each modified baseline, state
   what changed and check it against main, TeX/usetex, or documented behavior; an author
   calling it "correct" proves nothing.
4. **API policy**: any user-visible behavior or signature change to public API needs the
   deprecation machinery (`_api.deprecated`, `_api.warn_deprecated`,
   `_api.make_keyword_only`, `_api.rename_parameter`, ...) and a note in
   `doc/api/next_api_changes/{behavior,deprecations,removals,development}/<PR>-<initials>.rst`;
   new features get `doc/release/next_whats_new/*.rst`. Public signature changes need the
   matching `.pyi` stub updated; pyplot wrappers come from `tools/boilerplate.py`, never hand
   edits. New rcParams need a validator in `rcsetup.py` and an entry in `mpl-data/matplotlibrc`.
5. **Tests**: a bugfix needs a test that fails on `main`. Prefer `check_figures_equal` or
   numeric asserts over new baseline images (repo size); new `image_comparison` tests
   should justify themselves.
6. **Necessity**: code, params or tests the fix doesn't need; a helper duplicating existing
   code (name it `file:line`); purely stylistic churn mixed into a fix. Not findings: naming
   taste, equal-size alternatives.

Do not report: things that are fine, PR hygiene (labels, milestone, checkboxes, CI status),
description-vs-diff drift, or anything `prek`/linters catch.

**Bug hunt.** Before writing output, launch three read-only finder agents in parallel, each
given the diff and one angle, each returning candidate defects with a repro:
(a) every changed condition or branch: which inputs take a different path than on `main`,
and is each new outcome right (sets, regexes and `isinstance` checks often match more than
intended); (b) every caller and consumer of changed code: `grep` for code that indexes,
unpacks or round-trips its output or state, and check it still holds;
(c) tests: does each new test fail on `main`, and can each assertion actually fail?
Then verify every candidate yourself, by execution where possible. Drop what doesn't
reproduce, and don't call a blocker a nit to keep the verdict short.

## 5. Output

One or two sentences on what the PR does, then findings, most important first. Anchor each
localized finding as `path:line` (line at the head) on its own line; diffuse findings in
prose. Every finding ends with a concrete fix. One runnable repro per distinct failure mode
(imports included, actual vs expected), stating whether you executed it. No checklist of
what you inspected. End with the verdict, the last thing printed:

```
┏━━━━━━━━━━━━━━━━━━━━━━━┓
┃  VERDICT: NEEDS WORK  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┛
```

`LGTM` ready for review as-is · `NITS ONLY` nothing blocking · `NEEDS WORK` real defects,
sound approach · `WRONG APPROACH` can't be patched into correctness · `BLOCKED → <verdict>`
waiting on a maintainer decision or another PR · `CLOSE` unlikely to merge in any form (say why).

## For the author

`LGTM` / `NITS ONLY` mean stop iterating; reruns on an unchanged diff only surface new nits.
This review does not replace your own understanding of the change: Matplotlib's AI policy
(`doc/devel/contribute.rst`, "Use of Generative AI") requires that you understand and can
defend every line, and that your PR summary and replies are in your own words. Don't paste
this output into GitHub; fill in the PR's "AI Disclosure" section (tool, model, effort).
