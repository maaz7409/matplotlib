# AI-agent usage in pandas vs Matplotlib PRs

Collected 2026-10-17. Windows: **last 12 months** (PRs created on or after 2025-10-17) and
**last 6 months** (on or after 2026-04-17). Open, closed and merged PRs are all counted.

## How this was measured (and the limits)

This cloud session could not use the GitHub API for the upstream repos, so I used two
independent sources:

- **A. GitHub search over PR descriptions** (`is:pr created:>=DATE <word> in:body`, read from
  github.com search pages). This catches AI disclosures written in the PR text, for example
  Matplotlib's "AI Disclosure" section or pandas' tool/model/effort line. It is an **upper
  bound**: a body that says "no Claude was used" also matches, and bot PRs are in the totals.
- **B. Commit trailers.** I fetched every PR head (`refs/pull/*/head`) over git and scanned
  each PR's own commits for agent fingerprints: `Co-Authored-By: Claude`, `noreply@anthropic.com`,
  `Generated with Claude Code`, `claude.ai/code`, Copilot coding agent, `cursoragent@cursor.com`,
  Codex, Gemini/Jules, Aider, Devin, OpenHands, Amp and Junie. Bot authors (dependabot,
  pre-commit-ci and similar) are excluded. This is a **lower bound**: contributors who strip
  trailers, squash locally, or use chat assistants leave no trace.

The true share is somewhere between A and B.

## A. PR descriptions mentioning a tool (GitHub search)

| | pandas 12 mo | pandas 6 mo | Matplotlib 12 mo | Matplotlib 6 mo |
|---|---:|---:|---:|---:|
| All PRs created | 4,617 | 2,558 | 1,387 | 776 |
| Body mentions **Claude** | 1,607 (**34.8%**) | 1,228 (**48.0%**) | 82 (**5.9%**) | 57 (**7.3%**) |
| …of which merged | 1,193 | – | 41 | – |
| Body mentions Copilot | 28 (0.6%) | – | 17 (1.2%) | – |
| Body mentions Cursor / Codex / Gemini / ChatGPT | 89 (1.9%) | – | 47 (3.4%) | – |

## B. Commits carrying an agent trailer (git scan, human-authored PRs only)

| | pandas 12 mo | pandas 6 mo | Matplotlib 12 mo | Matplotlib 6 mo |
|---|---:|---:|---:|---:|
| PRs scanned | 4,475 | 2,530 | 1,058 | 566 |
| PRs with a **Claude Code** trailer | 1,903 (42.5%) | 1,484 (58.7%) | 13 (1.2%) | 10 (1.8%) |
| PRs with **any** agent trailer | 1,911 (42.7%) | 1,490 (58.9%) | 21 (2.0%) | 15 (2.7%) |
| Distinct PR authors | 969 | 485 | 358 | 186 |
| Authors with ≥1 Claude Code PR | 113 (11.7%) | 81 (16.7%) | 11 (3.1%) | 8 (4.3%) |
| Other agents seen (PRs) | Cursor 5, Copilot 4, other 1 | Cursor 4, Copilot 1, other 1 | Copilot 5, Cursor 3 | Cursor 3, Copilot 2 |

### The pandas headline number is one person

In pandas, **1,702 of the 1,903 Claude Code PRs (89%) come from a single core maintainer
account, jbrockmendel**, who also wrote `/pandas-review`. The top 5 accounts make up 93% of
them. With that account excluded:

| pandas, excluding the top account | 12 mo | 6 mo |
|---|---:|---:|
| PRs | 2,629 | 1,135 |
| PRs with a Claude Code trailer | 201 (**7.6%**) | 138 (**12.2%**) |

In Matplotlib, Claude Code PRs are spread across many accounts (no account has more than 2).

### Monthly trend (PRs created / PRs with a Claude trailer)

| Month | pandas | Matplotlib |
|---|---|---|
| 2025-10 | 301 / 0 | 47 / 0 |
| 2025-12 | 204 / 13 | 64 / 0 |
| 2026-02 | 281 / 12 | 88 / 1 |
| 2026-03 | 488 / 230 | 134 / 1 |
| 2026-05 | 292 / 132 | 100 / 2 |
| 2026-07 | 354 / 208 | 95 / 1 |
| 2026-09 | 617 / 370 | 106 / 1 |
| 2026-10 (to 17th) | 470 / 330 | 59 / 1 |

pandas jumped in March 2026 and has kept climbing. Matplotlib has stayed flat at about 1–2
trailer-PRs a month.

## What this means

- **pandas**: Claude Code is by far the dominant agent; other agents barely show up in
  trailers. Outside the heaviest user, about 1 in 13 PRs over 12 months, and 1 in 8 over 6
  months, carries a Claude Code trailer, and about 35–48% of PR descriptions mention Claude.
  Asking contributors to run `/pandas-review` reaches a large and growing group.
- **Matplotlib**: about 6–7% of PR descriptions mention Claude and about 2–3% of PRs carry
  any agent trailer. The gap between A and B suggests most Matplotlib AI use is chat or
  assistant use declared in the "AI Disclosure" section, not agent-authored commits. A review
  skill would reach a **small minority** of contributors.
- **Contributors without Claude Code**: `SKILL.md` follows the open Agent Skills format,
  which other agent CLIs and IDE agents (for example Codex, Copilot, Cursor and Gemini CLI)
  can also load. It is plain Markdown, so any chat LLM can be pointed at it. People who use
  no AI at all are unaffected; the skill must stay optional for them.
- **Other agents with an applicable skill format** together account for roughly 0.5–3.5% of
  PRs in either repo by these measures (Copilot plus Cursor/Codex/Gemini mentions).

### Verdict for question 2

**The case is much stronger for pandas than for Matplotlib.** pandas has a large and rising
share of Claude Code PRs, an `AGENTS.md`, and a maintainer who already backs the workflow.
Technically the skill works for Matplotlib too, but only about 2–7% of its PRs would be
covered. So it should be pitched as an optional self-check for contributors who already use
an agent, not as a request to every contributor.
