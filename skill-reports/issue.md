<!-- Draft for a GitHub issue on matplotlib/matplotlib. Use the "Maintenance" or blank template.
     Rewrite it in your own words before posting; Claude must not post it. -->

### Title

[MNT]: Optional `mpl-review` self-check, so AI-assisted PRs arrive without the obvious problems

### Summary

pandas has a review queue problem similar to ours. Its maintainers now ask contributors who
use AI agents to run a small "self-review" skill on their own PR before asking for review:
`pandas-review`, proposed for their contributing guide in pandas#70954. The skill is a short
Markdown file of instructions for the agent. It prints findings and a verdict (`LGTM`,
`NITS ONLY`, `NEEDS WORK`, …) in the contributor's terminal, and it never posts to GitHub or
edits code. Contributors there now report verdicts such as "Ran pandas-review, verdict NITS
ONLY. Added the whatsnew entry it flagged".

I'd like to ask whether Matplotlib wants something similar, and if so, in what form.

### Why it might help

Since mid-August, about 45% of our PRs say in their AI Disclosure that AI was used. Over the
last 6 months those PRs were closed unmerged about twice as often as others. Many fail on
**obvious** things a maintainer spots in a minute:
- a file in the wrong place that does nothing;
- a bugfix with no test, or a test that would pass on `main`;
- a behavior change with no deprecation or `next_api_changes` note;
- a missing `.pyi` stub;
- a baseline image changed without a reason.

A quick check that the contributor runs **before** a maintainer looks could catch those, so
maintainer time goes to the problems that are not obvious.

### What I tried

I wrote a draft, `mpl-review`: a 6 KB skill plus one small script that gathers the diff, the
review thread and failing CI in one go. It is tuned to be **fast and cheap**: about 25–80
seconds and $0.18–0.35 per review on Claude Opus. It deliberately doesn't hunt for subtle
bugs.

I tried it on 3 recent PRs I hadn't used while writing it, and compared it with a generic AI
code review using the same model:

- **#32537:** it flagged first exactly what the closing reviewer said: the file sits at the
  repository root and does nothing.
- **#32504:** it flagged the baseline/xfail mismatch and the fragile version check. It didn't
  re-raise the points the author had already fixed after review.
- **#32515** (approved): it said `LGTM`. The generic review raised 6 points on this approved
  PR.
- **Compared with the generic review:** that review digs deeper and found two extra valid
  points on #32504, but it gives no verdict, is noisier on clean PRs, and cost about 40%
  more.

This is a small sample (3 PRs, one run each), and "LGTM" from the skill only means "nothing
obvious", not "correct". Details: <link to skill-report.md>.

### Open questions for maintainers

1. Is this welcome at all, given our [AI policy](https://matplotlib.org/devdocs/devel/contribute.html#use-of-generative-ai)?
   I'd suggest it stays **optional**: contributors who don't use AI are unaffected, and the
   skill tells authors not to paste its output and to reply to reviewers in their own words.
2. Where should it live? pandas uses the tool-neutral `.agents/skills/` (with a
   `.claude/skills` symlink), so Codex, Copilot, Cursor and others can use it too. The
   alternative is a page in the developer guide.
3. Would an `AGENTS.md` (suggested in #30848 and #31457) be a better first step, with this
   skill as a follow-up?

If there's interest, I'm happy to open a PR with the draft and adjust it to whatever you
prefer.

### AI disclosure

I used Claude Code to collect the numbers, draft the skill, and run the comparison. I checked
the findings myself, and this issue text is my own.
