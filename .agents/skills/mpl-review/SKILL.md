---
name: mpl-review
description: Quick self-review of your own Matplotlib PR (or local branch before opening one) for the obvious problems a maintainer would flag first. Prints findings and a verdict in the terminal; never posts to GitHub or edits files.
disable-model-invocation: true
argument-hint: "[PR number or URL]"
allowed-tools: Bash(python .agents/skills/mpl-review/scripts/fetch_context.py), Bash(python .agents/skills/mpl-review/scripts/fetch_context.py *), Bash(git diff *), Bash(git show *), Bash(git log *), Bash(git grep *), Bash(pytest *), Bash(python -m pytest *), Bash(python -c *), Read, Grep, Glob
---

Matplotlib's review queue is the bottleneck. This skill is a **fast gate**: catch the obvious
problems *before* a maintainer looks, so their time goes to what isn't obvious. It is not a
deep audit. Review as a maintainer who did not write the code, even if you did. Verify
claims instead of trusting them. Report only: never edit files, change git state, or post
anything to GitHub.

Target: $ARGUMENTS (PR number or URL → that PR; anything else, including a literal
`$ARGUMENTS` → the current branch with uncommitted changes).

**Budget.** About 8 tool calls after step 1. Batch independent calls into one turn. Use no
subagents. Read code with Grep `-n` and Read `offset`/`limit` (≤ 150 lines), never a whole
module. Pipe long output through `| tail -n 30`. Stop once the checklist is done.

## 1. Context (one call)

`python .agents/skills/mpl-review/scripts/fetch_context.py [<PR>]`, then Read the
`context.md` and `diff.patch` it prints. If the script fails, report its error and stop. If
the thread was not fetched, say so: unknown is not empty. Where a maintainer on the thread
asked for something that conflicts with this file, follow the maintainer.

## 2. Checklist: obvious problems only, in priority order

1. **Maintainer position.** A core dev said not to proceed (`CLOSE`), wants another
   approach (`WRONG APPROACH`), or it waits on a decision (`BLOCKED → …`). Report that and
   little else.
2. **Unaddressed review comments**: neither fixed in the diff nor answered with a reason.
   Don't draft replies; authors answer in their own words.
3. **Wrong place or no effect**: code outside `lib/matplotlib` that users can't import,
   examples outside `galleries/`, a change that is never called, or unrelated files or
   churn mixed in.
4. **Tests**: a bugfix with no test; a test that would pass on `main` (check the assertion
   against the old code); assertions that can't fail; new baseline images where
   `check_figures_equal` or a numeric assert would do. Changed baselines are claims: say
   what changed and whether that is right.
5. **API policy**: a user-visible behavior or signature change without the deprecation
   machinery (`_api.deprecated`, `_api.warn_deprecated`, `_api.make_keyword_only`,
   `_api.rename_parameter`) and a note in
   `doc/api/next_api_changes/<kind>/<PR>-<initials>.rst`. Features need
   `doc/release/next_whats_new/*.rst`. Signature changes need the `.pyi` stub. pyplot
   wrappers come from `tools/boilerplate.py`. New rcParams need a `rcsetup.py` validator and
   an entry in `mpl-data/matplotlibrc`.
6. **Obvious correctness**: a crash or a wrong result on the inputs the PR targets, or on
   common ones (empty, NaN, masked, units, `None` as "unset"). Three quick checks:
   - For each changed set, regex or condition, look at its *full* membership.
   - Grep the callers of each changed function or structure.
   - When state is rebuilt from getters, check resolved values (`'none'`, alpha, rcParams
     defaults).
   Don't hunt for subtle bugs; that is the maintainer's job.
7. **CI** failures that the diff causes; quote the failing check.

**Run code only if it decides a finding**, and only when `python -c "import matplotlib;
print(matplotlib.__file__)"` resolves into this tree:
- the PR's new tests by node id: `pytest <file>::<test> -q -x --no-header 2>&1 | tail -n 15`;
- at most 2 short repros.

Otherwise review by reading and say so. Never build, install, or swap files.

Do not report: things that are fine, PR hygiene (labels, milestone, checkboxes), CI failures
the diff didn't cause, description-vs-diff drift, or anything linters catch. Partial fixes
of sibling paths are optional follow-ups. Before reporting, re-check each finding's
`file:line` and quoted code in one batched call, and drop anything you can't support.

## 3. Output (short)

One sentence on what the PR does. Then the findings, most important first:
- Anchor each finding as `path:line` (head line numbers).
- Give a one-line reason and a concrete fix.
- For a correctness finding, add a short repro (actual vs expected) and say whether you
  executed it.

Don't list what you inspected. End with the verdict, the last thing printed:

```
┏━━━━━━━━━━━━━━━━━━━━━━━┓
┃  VERDICT: NEEDS WORK  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┛
```

`LGTM` nothing obvious found · `NITS ONLY` nothing blocking · `NEEDS WORK` real defects,
sound approach · `WRONG APPROACH` can't be patched into correctness · `BLOCKED → <verdict>`
waiting on a maintainer decision · `CLOSE` unlikely to merge in any form (say why).

## For the author

`LGTM` means no *obvious* problems, not that the PR is correct; a maintainer still reviews
it. After `LGTM` or `NITS ONLY`, stop: reruns only surface new nits. Run it in a fresh
session (`/clear`). Matplotlib's AI policy (`doc/devel/contribute.rst`, "Use of Generative
AI") requires that you understand and can defend every line, and that your PR text and
replies are your own words. Don't paste this output into GitHub; fill in the PR's "AI
Disclosure" section.
