---
name: mpl-review
description: Self-review your own Matplotlib PR (or local branch before opening one) the way a Matplotlib maintainer would. Prints findings and a verdict in the terminal; never posts to GitHub or edits files.
disable-model-invocation: true
argument-hint: "[PR number]"
allowed-tools: Bash(gh pr view *), Bash(gh pr diff *), Bash(gh pr list *), Bash(gh api -X GET *), Bash(git diff *), Bash(git merge-base *), Bash(git rev-parse *), Bash(git branch --show-current), Bash(git remote -v), Bash(git show *), Bash(git log *), Bash(git status *), Bash(pytest *), Bash(python -m pytest *), Bash(python -c *), Read, Grep, Glob
---

Review a Matplotlib PR as a maintainer who did not write it, even if you did, and report to
its author. Target: $ARGUMENTS (a PR number → PR mode; anything else, including a literal
`$ARGUMENTS` → local mode). Verify claims in the description, commits and comments instead of
trusting them. Report only: never edit files, change git state, or post to GitHub.

**Token budget.** Every turn re-sends the whole context, so keep it small and turns few:
no subagents; batch independent commands into one turn; aim for ≤ 12 tool calls in total.
Read code with Grep `-n` plus Read `offset`/`limit` around the hunk (≤ 150 lines), never a
whole module. Pipe any command whose output may be long through `| tail -n 30`.

## 1. Get the change (one turn)

- **PR mode** (strip `#`): `gh pr view <n> --repo matplotlib/matplotlib --json title,author,headRefOid,files,body`
  and `gh pr diff <n> --repo matplotlib/matplotlib --exclude '*/baseline_images/*'`.
  If that fails, say so and stop.
- **Local mode**: `<up>` = the remote whose URL contains `matplotlib/matplotlib`; `B=$(git merge-base HEAD <up>/main)`.
  Run `git diff --stat $B`, `git diff $B -- . ':!*/baseline_images/*'`, `git status --porcelain`,
  and `git log --oneline HEAD..<up>/main | wc -l` (commits behind; mention if > 0). Read any
  `??` source file. If `gh pr list --repo matplotlib/matplotlib --head "$(git branch --show-current)" --json number`
  returns exactly one PR, do step 2 for it.

Changed baseline images appear only in `--stat`; treat each one as a claim (see 4.3).
In PR mode, if `git rev-parse HEAD` ≠ `headRefOid`, review from the diff alone.

## 2. Read the thread (compact)

One turn, three calls, each with `--paginate --jq '.[] | {u: .user.login, s: .state, p: .path, b: .body}'`:
`gh api -X GET repos/matplotlib/matplotlib/pulls/<n>/reviews`, `.../pulls/<n>/comments`,
`.../issues/<n>/comments`. A failed fetch is unknown, not empty: say the thread was not read.
Where a maintainer asked for something that conflicts with this file, follow the maintainer.

## 3. Execute only what decides a finding

If `python -c "import matplotlib; print(matplotlib.__file__)"` resolves into this tree, run
only the PR's new/changed tests by node id (`pytest <file>::<test> -q -x --no-header 2>&1 | tail -n 15`)
and the repros for findings you'd call blocking (≤ 3 short scripts). Otherwise review by
reading and say so. Never build, install, or swap tracked files; to compare with `main`, load
`git show $B:<path>` from a temp dir.

## 4. What to look for (priority order)

1. **Maintainer position**: a core dev saying not to proceed, wanting another approach, or
   waiting on a decision outranks everything.
2. **Unaddressed review comments**: neither fixed in the diff nor answered with a reason.
   Don't draft replies; authors answer in their own words.
3. **Correctness, above all regressions** (worked on `main`, breaks now). For each changed
   condition, set, regex or `isinstance` check, ask which inputs now take a different path
   and whether each new outcome is right; they often match more than intended. Grep the
   callers that consume or round-trip what changed. Probe the inputs that historically break
   Matplotlib: empty / length-1, NaN/inf, masked, int vs float, datetime/category units,
   log/inverted axes, `None` as "unset", rcParams defaults vs explicit kwargs, re-added
   artists, `stale`, DPI/savefig vs screen, and sibling backends. Getters return *resolved*
   values (RGBA with alpha applied, resolved fonts), so state rebuilt from getters can re-apply
   alpha or defaults: probe `'none'`, `None`, `'inherit'`, alpha. **Changed baselines are
   claims, not evidence**: check what changed against main, TeX/usetex, or the docs; the author
   calling it "correct" proves nothing. Partial coverage of sibling paths is optional, not a defect.
4. **API policy**: user-visible behavior or public signature changes need the deprecation
   machinery (`_api.deprecated`, `_api.warn_deprecated`, `_api.make_keyword_only`,
   `_api.rename_parameter`) and a note in `doc/api/next_api_changes/<kind>/<PR>-<initials>.rst`;
   features get `doc/release/next_whats_new/*.rst`. Signature changes need the `.pyi` stub;
   pyplot wrappers come from `tools/boilerplate.py`; new rcParams need a `rcsetup.py`
   validator and a `mpl-data/matplotlibrc` entry.
5. **Tests**: a bugfix needs a test that fails on `main` and assertions that can fail. Prefer
   `check_figures_equal` or numeric asserts over new baseline images.
6. **Necessity**: code, params or tests the fix doesn't need; a helper duplicating existing
   code (`file:line`); stylistic churn mixed into a fix. Not findings: naming taste,
   equal-size alternatives.

Do not report things that are fine, PR hygiene (labels, milestone, checkboxes, CI),
description-vs-diff drift, or anything linters catch. Drop candidates you can't support, and
don't call a blocker a nit to keep the verdict short.

## 5. Output

One or two sentences on what the PR does, then findings, most important first. Anchor each
localized finding as `path:line` (head line numbers) on its own line. Each ends with a
concrete fix. One short repro per distinct failure mode (actual vs expected), saying whether
you executed it. No list of what you inspected. End with the verdict, the last thing printed:

```
┏━━━━━━━━━━━━━━━━━━━━━━━┓
┃  VERDICT: NEEDS WORK  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┛
```

`LGTM` ready as-is · `NITS ONLY` nothing blocking · `NEEDS WORK` real defects, sound approach ·
`WRONG APPROACH` can't be patched into correctness · `BLOCKED → <verdict>` waiting on a
maintainer decision or another PR · `CLOSE` unlikely to merge in any form (say why).

## For the author

`LGTM` / `NITS ONLY` mean stop iterating; reruns on an unchanged diff only surface new nits.
Matplotlib's AI policy (`doc/devel/contribute.rst`, "Use of Generative AI") requires that you
understand and can defend every line, and that your PR text and replies are your own words.
Don't paste this output into GitHub; fill in the PR's "AI Disclosure" section.
