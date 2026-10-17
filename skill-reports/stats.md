# AI-agent usage in pandas vs Matplotlib PRs

Collected 2026-10-17. **This is a rewrite, made with full GitHub API access.** The first
version had no API access and undercounted Matplotlib's AI use about 4–5×. The section
"What changed from the first version" explains why.

Windows: **12 months** (PRs created on or after 2025-10-17), **6 months** (on or after
2026-04-17), and **since 2026-08-14**. Since 2026-08-14 is the fair comparison window,
because it is the first period in which *both* repos ask every PR a yes/no AI question.
Bots (dependabot, pre-commit-ci, Copilot agent and similar) and auto-backport PRs are
excluded. Open, closed and merged PRs are all counted.

## Headline

| Since 2026-08-14 (both repos ask yes/no) | pandas, all | pandas, without its top account | **Matplotlib** |
|---|---:|---:|---:|
| Human PRs | 1,258 | 509 | 169 |
| PRs showing AI use | 970 (77%) | 241 (**47%**) | 76 (**45%**) |
| …naming Claude | 874 (69%) | 145 (28%) | 24 (14%) |
| PR authors | 211 | 210 | 59 |
| Authors with ≥1 AI PR | 122 (58%) | 121 (58%) | 37 (**63%**) |

**Once pandas' single heaviest user is excluded, Matplotlib's AI use is about the same as
pandas': roughly 45% of PRs and about 60% of authors.** The real difference is *which* tool
people name. pandas contributors mostly name Claude. Matplotlib contributors usually just
write "AI" or "an AI assistant" without naming a tool, and Claude is the most-named one.

"Shows AI use" means one of the following:
- **Matplotlib**: the PR's "AI Disclosure" section says AI was used, or a commit carries an
  agent trailer, or the PR has the `ai-contribution` label.
- **pandas**: the "I used AI" checkbox is ticked, or the PR text names an AI tool and does
  not tick "I did not use AI".

## Matplotlib in detail

### The AI Disclosure section

The PR template has had an "AI Disclosure" section since Feb–Mar 2026, and has always asked
for it since #31507 (2026-04-16). Every answer from the last 6 months was classified as
yes / no / empty by regex. The ~40 that didn't match a pattern were read and labelled by
hand.

| Human PRs | 6 months | 12 months |
|---|---:|---:|
| PRs | 526 | 1,071 |
| Section answered (yes or no) | 358 | 461 |
| **Answered "AI used"** | **157 (44% of answered, 30% of all)** | 206 (45% of answered) |
| Answered "no AI" | 201 | 255 |
| Section missing or empty | 168 | 606 (mostly before the section existed) |
| PRs with an agent commit trailer | 13 (Claude 8, Cursor 3, Copilot 2) | 21 |
| `ai-contribution` label ("AI generated without a human in the loop") | 33, all closed | 38 |
| **Any AI signal** (disclosure, trailer or label) | **192 (36.5%)** | 252 (23.5%; lower bound, since the section did not exist for the first 5 months) |
| Authors with any AI signal | 104 of 174 (60%) | 137 of 340 (40%) |

**Tools named in the 157 "AI used" answers (6 months):**

| Tool | Answers |
|---|---:|
| No tool named ("AI", "an AI assistant", "LLM") | 79 |
| Claude / Claude Code | 55 |
| Codex / ChatGPT | 15 |
| Cursor | 5 |
| Copilot | 4 |
| Other | 1 |

**What the AI was used for (rough regex split):**
- 92 answers say it wrote or drafted code or tests.
- 65 say it only helped them explore, debug, review or proofread.
- 51 name an agent tool (Claude Code, Codex, Cursor, Copilot and so on) that could run a
  skill file directly.

**Outcomes (6 months):**

| | Merged | Closed unmerged | Open |
|---|---:|---:|---:|
| PRs with an AI signal | 40% | 33% | 27% |
| PRs without one | 75% | 15% | 11% |

PRs with an AI signal are merged about half as often and closed unmerged about twice as
often. Maintainer review time is being spent on those closed PRs.

**Monthly trend** (human PRs; answered the section; said AI was used):

| Month | PRs | Answered | AI used |
|---|---:|---:|---:|
| 2026-03 | 149 | 71 | 41 |
| 2026-04 | 103 | 61 | 20 |
| 2026-05 | 109 | 53 | 23 |
| 2026-06 | 75 | 44 | 19 |
| 2026-07 | 90 | 64 | 26 |
| 2026-08 | 65 | 47 | 13 |
| 2026-09 | 80 | 67 | 38 |
| 2026-10 (to 17th) | 53 | 51 | 25 |

Before March 2026 there was no disclosure section, so AI use in that period can't be seen
(only 0–4 trailer PRs a month).

## pandas in detail

pandas' template only asks "I used AI / I did **not** use AI" since #66767 (2026-08-14).
Before that, it only had "*if* I used AI, I prompted it to follow AGENTS.md". So for
pandas, the 6- and 12-month numbers are lower bounds based on tool names.

| Human PRs | 6 months | 12 months |
|---|---:|---:|
| PRs | 2,400 | 4,340 |
| Share from the top account (jbrockmendel, author of `/pandas-review`) | 54% | 40% |
| PRs showing AI use, all accounts | 1,230 (51%) | 1,619 (37%) |
| PRs showing AI use, without the top account | 281 (25%) | 311 (12%) |
| PRs naming Claude, without the top account | 172 (15.5%) | 192 (7.4%) |

**Since 2026-08-14, excluding the top account:**
- 210 of 509 PRs ticked a checkbox.
- 177 of those 210 (84%) ticked "I used AI".

**Commit trailers** (from the first version's git scan of `refs/pull/*/head`; not re-run):
- 1,903 pandas PRs carry a Claude Code trailer over 12 months.
- 89% of those are from the top account.

The PR-text search in the first version was correct for pandas. Only about 170 PR
descriptions contain the template's example text `claude opus 4.8 (xhigh)`, and the counts
above remove that text before matching.

## What changed from the first version

| Claim in the first version | Corrected | Why |
|---|---|---|
| Matplotlib: "about 6–7% of PR descriptions mention Claude" | That figure is correct, but **about 30–45% of Matplotlib PRs disclose AI use** | Most Matplotlib disclosures say "AI" without naming a tool, so searching for "Claude" missed them |
| Matplotlib: "only about 2–3% of PRs carry any agent trailer, so it would reach a small minority" | The trailer count is correct (verified: 13 PRs in 6 months), but trailers are a poor proxy here | Most Matplotlib contributors' AI use leaves no trailer |
| "The case is much stronger for pandas than for Matplotlib" | **The AI usage level is about the same.** The difference is pandas' single power user, plus the choice of tool | See the headline table |
| Monthly trend: "Matplotlib flat at 1–2 trailer PRs/month" | 13–41 PRs a month say they used AI | Wrong measure |

## What this means for the skill

- **Reach**: In Matplotlib, about 45% of recent PRs and about 60% of recent authors used AI.
  About a third of those named an agent that can load a `SKILL.md` directly (Claude Code,
  Codex, Cursor, Copilot, Gemini CLI). For the rest, the file is plain Markdown and can be
  pasted into any chat model. People who don't use AI are unaffected.
- **Need**: 33 PRs in 6 months were closed with the `ai-contribution` label. Overall, AI PRs
  are closed unmerged at about twice the rate of other PRs. A pre-review step that runs
  before a maintainer looks targets exactly this group.
- **Fit**: The usage argument is now similar for both projects. The remaining differences
  are cultural: Matplotlib's stricter AI policy, and no maintainer currently championing a
  skill. See `skill-report.md`.

## Reproduce

The scripts are in `scripts/`:
- `fetch.py`: GraphQL; bodies, labels and commit messages.
- `fetch_rest.py`: REST search; bodies only, and lighter on rate limits.
- `classify.py`: parses the disclosure section and detects trailers.

```bash
python scripts/fetch.py matplotlib/matplotlib 2025-10-17 2026-10-18 mpl.json 14
python scripts/classify.py mpl.json mpl_rows.json
python scripts/fetch_rest.py pandas-dev/pandas 2025-10-17 2026-10-18 pandas.json
```

GraphQL with nested commits quickly hits GitHub's secondary rate limit. Use the REST
script for large repos.

**Limits**:
- The yes/no classification uses regex plus hand-labelling of about 40 unclear answers, so
  expect a few percent error.
- Disclosures are self-reported, and some AI use goes undisclosed.
- Templates differ between the repos (Matplotlib uses free text; pandas uses checkboxes).
