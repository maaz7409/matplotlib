<!-- Draft for a GitHub issue on matplotlib/matplotlib. Use the "Maintenance" or blank template. -->

### Title

[MNT]: Offer an optional `mpl-review` self-review skill for contributors who already use AI agents

### Summary

Some contributors already use AI coding agents (Claude Code, Codex, Copilot, Cursor and
others). pandas recently added a `/pandas-review` skill (a short Markdown file of
instructions for the agent). Before asking for review, a contributor runs it on their own PR,
and it checks the PR "the way a maintainer would". It prints findings and a verdict in the
terminal. It never posts to GitHub and never edits code. pandas maintainers now ask
contributors to run it and to say the result on the PR.

I'd like to ask whether Matplotlib wants something similar, and if so, in what form.

### Why it might help

- When contributors use agents, the agent is usually never asked to check the work against
  *Matplotlib's* rules. Typical things that slip through: a behavior change with no
  deprecation or `next_api_changes` note, a missing `.pyi` stub update, a new baseline image
  where `check_figures_equal` would do, or edge cases such as NaN, empty input, units or
  `\overset`.
- A self-check that runs **before** a maintainer looks could catch some of this, so review
  time goes to design questions instead.

### What I tried

I wrote a draft skill (`.claude/skills/mpl-review/SKILL.md`, about 6 KB, adapted from the
pandas one). I tried it on 3 open PRs and compared it with a generic AI code review using the
same model and settings. Short version:

- The generic review found slightly more real bugs (2 of 3 vs 1 of 3), but it also reported
  about 9 findings that were false or speculative. The skill reported none.
- On a small, correct PR, the skill said "LGTM" and explained why. The generic review gave
  the author 4 "issues" to chase.
- The skill ran the tests and its examples itself, and gave a verdict (right on 2 of 3 PRs).
- Both missed one real regression, so this is **not** a replacement for maintainer review.
  At best it is a filter that catches the obvious things earlier.
- Details are in the linked report: <link to skill-report.md>.

### Usage numbers (rough)

Since mid-August 2026, about 45% of Matplotlib PRs say in their AI Disclosure that AI was
used. That is similar to pandas once its single heaviest user is excluded. Over the last 6
months, PRs that disclose AI were closed unmerged about twice as often as other PRs. So this
group is large, and its PRs are often the expensive ones to review.

One review with the skill costs roughly $0.30–0.60 on Opus and takes 1–3 minutes, as long as
it is run in a fresh session.

### Open questions for maintainers

1. Is this welcome at all, given our [AI policy](https://matplotlib.org/devdocs/devel/contribute.html#use-of-generative-ai)?
   I'd suggest it stays **optional** and is never required. People who don't use AI are
   unaffected, and the skill tells the contributor not to paste its output into GitHub and
   to answer reviewers in their own words.
2. Should it live in the repo (`.claude/skills/` or a tool-neutral location), or be linked
   from the developer guide as an external file?
3. Would an `AGENTS.md` (suggested in #30848 and #31457) be the better first step, with the
   review skill as a follow-up?

If there's interest, I'm happy to open a PR with the draft skill and adjust it to whatever
conventions you prefer.

### AI disclosure

I used Claude Code to collect the usage numbers, draft the skill, and run the comparison.
I checked the findings myself, and this issue text is my own.
