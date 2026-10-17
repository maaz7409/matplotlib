# `/mpl-review`: multi-session plan

Each session is sized to fit one fresh Claude Code session (about 1–2 hours, ≤ $10 of
review runs unless stated). **Start each session with `/clear`, read `CLAUDE.md`, then only
your session's section below.** When done, update the status table and add a dated line to
the session log at the bottom.

## Status

| # | Session | Depends on | Status |
|---|---|---|---|
| 0 | Prototype, benchmark, token fix (v2 → v4) | – | ✅ done 2026-10-17 |
| 1 | Make the eval harness reproducible | 0 | ⬜ |
| 2 | Build a held-out eval set (10–12 PRs) | 1 | ⬜ |
| 3 | Working dev environment for execution | – | ⬜ |
| 4 | Baseline: v4 vs `/code-review` on held-out, with variance | 2, 3 | ⬜ |
| 5 | Thread awareness (PR mode with real `gh`) | 2 | ⬜ |
| 6 | Token tuning: effort, model, prompt size | 4 | ⬜ |
| 7 | Accuracy round 1: error analysis → v5 | 4 | ⬜ |
| 8 | Robustness: unusual PRs and failure modes | 7 | ⬜ |
| 9 | Portability: non-Claude agents and tool-neutral location | 7 | ⬜ |
| 10 | Refresh stats and finalize the reports | 4, 7 | ⬜ |
| 11 | Upstream package: clean skill branch and issue text | 8, 9, 10 | ⬜ |
| 12 | After maintainer feedback: iterate and maintain | 11 + user opens issue | ⬜ |

Sessions 3, 5 and 9 can run in parallel with others. 6 and 7 can swap order.

---

## Session 1: make the eval harness reproducible

**Goal:** one command evaluates a skill version on a set of PRs and writes a results table.
No more hand-built scratch scripts.

**Steps**
1. Read `skill-eval/*.sh`, `tally.py` and `labels/tuning-set.json` (seeded in session 0).
2. Add `skill-eval/eval.py`:
   - Inputs: `--skill <SKILL.md|cr>`, `--set <labels.json>`, `--runs N`, `--budget`, `--effort`, `--model`.
   - For each PR: `mk_clone.sh` → `run_review.sh` → `tally.py`.
   - Save the review text to `results/<version>/<pr>-<run>.md` and the metrics to
     `results/<version>/metrics.jsonl`.
   - Runs are **sequential** for skill variants (they share `~/.claude/skills/mpl-review`).
     Parallel is OK only for `cr`. Or install the skill per run into a temp project-level
     `.claude/skills` *outside* the reviewed diff. Check whether a project-level skill in an
     untracked dir pollutes the review (it showed up as `??` before), and pick the cleaner
     option.
3. Add a scoring helper `score.py`. It shows each finding next to the labels and asks the
   human or Claude to mark it as hit / false positive / new-candidate. Store the marks in
   `results/<version>/scores.json` and print a summary: blockers found, false positives,
   verdict accuracy, tokens, cost, time.
4. Add a watchdog to `run_review.sh`: a background loop that runs `tally.py` every 30 s and
   kills the run on `LOOP?`, any subagent call, or more than 20 tool calls.
5. Dry run: one v4 run on 32380 (cheapest, about $0.30). Check the numbers match
   `token-report.md` within run-to-run noise.

**Deliverables:** `skill-eval/eval.py`, `score.py`, watchdog, `skill-eval/README.md`
(≤ 40 lines).
**Budget:** ≤ $2. **Done when:** `python skill-eval/eval.py --skill .claude/skills/mpl-review/SKILL.md --set skill-eval/labels/tuning-set.json --runs 1`
reproduces the session-0 table.

## Session 2: build a held-out eval set (10–12 PRs)

**Goal:** ground truth the skill was never tuned on, so accuracy claims are honest.

**How to pick PRs.** Prefer **closed or merged PRs where the truth is known**, not open PRs
labelled by guessing:
- **Bug found in review (4–5 PRs):** a maintainer's review comment identified a concrete
  defect that the author then fixed. The label is the defect at the *pre-fix* commit; review
  that commit.
- **Bug found after merge (2–3):** a later commit says "Fix regression from #NNNN" or is a
  revert. The label is the regression; review the original PR's head.
- **Clean (2–3):** merged quickly with two approvals and no follow-up fixes. Expected verdict
  `LGTM` or `NITS ONLY`; any blocker reported is a false positive.
- **Policy (1–2):** a public behavior change with a missing API note or deprecation, or a
  maintainer saying "won't merge". Expected `NEEDS WORK`, `BLOCKED` or `CLOSE`.
- Mix areas: mathtext/text, colors/colormaps, axes/ticks, transforms, backends,
  docs-only, and one PR touching `src/*.cpp`.

**Steps**
1. Find candidates with `git log --grep "regression\|revert\|Fix.*#[0-9]"` on upstream
   main, and with WebFetch of PR pages to read review threads. Use GitHub search pages, or
   `gh` if the API is available (session 5 notes).
2. For each PR, record in `labels/heldout-set.json`: the commit to review, the labels (each
   with a repro, **executed**, using the venv-swap trick from CLAUDE.md), the expected
   verdict, and the source of truth (comment URL or fix commit).
3. **Freeze the set:** after this session, nobody edits SKILL.md while looking at held-out
   outputs (see session 7).

**Budget:** ≤ $3 (no review runs; mostly reading). **Done when:** at least 10 PRs are
labelled, each with a source of truth and executed repros.

## Session 3: working dev environment for execution

**Goal:** the skill (and you) can run real tests. The review that executed code found and
confirmed more.

**Steps**
1. `read_documentation` topics `environment.network` and `environment.setup_script`. Find
   which hosts the meson build needs (the `sheenbidi`, freetype and qhull subproject
   downloads).
2. Option A: ask the user to allowlist those hosts and add a setup script running
   `pip install -e . --no-build-isolation` (or `pip install --group dev`).
   Option B: pre-download the subproject tarballs into `subprojects/packagecache/`.
3. Write a SessionStart hook (use the `session-start-hook` skill) so every cloud session has
   an importable dev build. Check that `python -c "import matplotlib; print(matplotlib.__file__)"`
   points into the repo.
4. Record build time and disk use in CLAUDE.md "Facts".

**Budget:** ≤ $2. **Done when:** `pytest lib/matplotlib/tests/test_mathtext.py -q -x` runs
in a fresh session without manual steps.
**Note:** the skill must still work without a build (read-only mode). Session 4 runs both.

## Session 4: baseline on the held-out set, with variance

**Goal:** honest numbers for v4 vs `/code-review high`, with run-to-run spread.

**Steps**
1. `eval.py` with v4 and with `cr`, held-out set, `--runs 2`, Opus 5.5 high. Run once with
   the dev build importable and once without, if session 3 is done.
2. Score with `score.py`. Each blocker hit needs its label's repro to match the finding's
   failure mode.
3. Report mean and range for blocker recall, false positives per review, verdict accuracy,
   tokens, cost and wall time. Add a short "where each tool wins" note.
4. Write `skill-reports/heldout-results.md`.

**Budget:** about 12 PRs × 2 runs × (v4 about $0.5 + cr about $0.7) ≈ $30. **Ask the user
before starting.** Use `--runs 1` if they want ≤ $15.

## Session 5: thread awareness (PR mode with real `gh`)

**Goal:** test the feature `/code-review` lacks: respecting maintainer positions and
unaddressed comments.

**Needs:** GitHub API access to matplotlib/matplotlib. The cloud session can't attach it
(the name clashes with the fork), so either:
- the user runs this session in a **local CLI** with `gh auth`, or
- the user starts a cloud session with `matplotlib/matplotlib` as the source.

**Steps**
1. Pick 4 PRs with informative threads:
   - a maintainer said "won't merge" or "wrong approach" (expect `CLOSE` or `WRONG APPROACH`);
   - an open review request not yet addressed (expect it listed);
   - the author answered a concern convincingly (expect it *not* re-raised);
   - a draft or blocked PR (expect `BLOCKED → …`).
2. Run `/mpl-review <N>` in PR mode. Check the `--jq` thread compaction keeps what matters
   (author, state, inline path, body). Measure the thread's token cost.
3. If bodies are huge (bots, long logs), add `| head -c` limits per comment, or filter bot
   authors in `--jq`.

**Budget:** ≤ $5. **Deliverable:** a section in `skill-report.md` plus any SKILL.md fixes
(re-run the tuning set to check nothing regressed).

## Session 6: token tuning (effort, model, prompt size)

**Goal:** the cheapest configuration whose accuracy is within about 10% of the best.

**Steps**
1. On the held-out set (1 run each), compare: Opus high (baseline), Opus medium,
   Sonnet 5.5 high, and Haiku 5.5 high (expected too weak; confirm).
2. Check whether skill frontmatter can set `model` or `effort` (read the Claude Code docs
   via the `claude-code-guide` agent). If it can, set the winning default. If not, recommend
   it in the "For the author" section.
3. Prompt diet: remove one SKILL.md section at a time (e.g. the long Matplotlib-pitfall
   list) and measure the accuracy change. Keep only lines that earn their tokens.
4. Measure the *per-turn* context: what fraction is system prompt plus SKILL.md vs diff vs
   tool output. Optimize the biggest.

**Budget:** ≤ $15. **Deliverable:** a "Recommended settings" table in `token-report.md`.

## Session 7: accuracy round 1, error analysis → v5

**Goal:** improve recall without adding false positives or tokens, **without leakage**.
Start from the "Directions for v5" table in `skill-report.md`. Each row is a hypothesis to
test, not something to apply blindly.

**Steps**
1. Split the held-out set: use half as a new tuning set (`tune2`) and keep half frozen
   (`test2`).
2. On `tune2` misses only: classify each miss as didn't-look, looked-but-reasoned-wrong,
   or needed-execution. Add **general** rules, at most 3 lines in total. Never add rules
   that name a specific PR's symbols.
3. Evaluate v5 on `test2` once. Report v4 vs v5 on `test2` only.
4. Keep SKILL.md ≤ 7 KB. If a rule doesn't move `test2`, delete it.

**Budget:** ≤ $10.

## Session 8: robustness, unusual PRs and failure modes

Run v5 once on each case and fix only clear failures:
- a huge PR (> 1,000 lines) — does the budget rule hold, and does it stay under about 0.6M
  tokens?
- docs-only or a gallery example (expect a light review and no test demands);
- a `src/*.cpp` change (no Python execution);
- a PR 300+ commits behind main;
- a draft PR;
- no `gh` auth (local mode must still work);
- a branch with untracked junk files (does it review them?);
- a non-English PR description.

**Budget:** ≤ $6. **Deliverable:** a table in `skill-report.md` and small SKILL.md fixes.

## Session 9: portability to non-Claude agents and a tool-neutral location

**Goal:** contributors using Codex, Copilot, Cursor or Gemini CLI can use it. About two
thirds of Matplotlib's AI users don't name Claude.

**Steps**
1. Research (docs only) where each agent loads skills or instructions: Agent Skills
   `SKILL.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.cursor/rules`.
2. Remove Claude-only assumptions from the SKILL.md body (`$ARGUMENTS`, tool names). Keep
   the frontmatter Claude-specific and the body generic.
3. Draft how this relates to the `AGENTS.md` idea from #30848 and #31457. Perhaps a tiny
   `AGENTS.md` that points to the review checklist. **Draft only; it's the maintainers'
   call.**
4. If the user has access to another agent, ask them to try one review and report back.

**Budget:** ≤ $3.

## Session 10: refresh stats and finalize the reports

1. Get the user's `scripts/fetch.py`, `fetch_rest.py` and `classify.py` (referenced in
   `stats.md`, not committed) and commit them under `skill-eval/stats/`.
2. Re-run for the latest window. Update `stats.md` (keep the "what changed" history).
3. Rewrite `skill-report.md` around the held-out results (sessions 4 and 7). Move the
   session-0 tuning-set results to an appendix marked "tuning set, optimistic".
4. Make `token-report.md` final: v2 → v3 → v4 → v5 table and recommended settings.

**Budget:** ≤ $2.

## Session 11: upstream package (clean branch and issue text)

1. Create the branch `mpl-review-skill` from **upstream** `main` with only
   `.claude/skills/mpl-review/SKILL.md`. No CLAUDE.md, reports or eval files.
2. Update `skill-reports/issue.md` with the held-out numbers. Keep it short, in plain
   language, and honest about misses and cost (about $0.3–0.6 per review, fresh session).
3. Prepare a short "how to try it" for maintainers (copy one file, run `/mpl-review`).
4. **Hand over to the user.** The user rewrites the issue in their own words and opens it.
   Claude does not post.

**Budget:** ≤ $1.

## Session 12: after maintainer feedback

- Apply what maintainers ask for: location, wording, scope, or "please don't".
- If they want a docs page instead of a repo file, draft it under `doc/devel/`.
- If accepted, set up a light maintenance loop: re-run the held-out set when SKILL.md
  changes or a new model ships, and keep the token ceiling per review at ≤ 0.4M.
- If declined, record why in `skill-report.md` and stop.

---

## Session log

- 2026-10-17 · S0: built v2 (6.4 KB); benchmarked against `/code-review high` on 32380,
  32331 and 32285 ($4.93). The user's v3 (3 parallel finder agents) burned about 4M+ tokens
  per review. v4 removed subagents, compacted the diff and thread, and capped execution:
  0.18–0.34M tokens, 3/3 correct verdicts and 1 false positive on the tuning set. Its raw 3/4 blocker count is biased (leakage plus one self-found bug); adjusted, it is level with `/code-review` or slightly behind. The v5 directions are in `skill-report.md`. Reverted unrelated
  `lib/` changes. Seeded `skill-eval/` and `labels/tuning-set.json`.
