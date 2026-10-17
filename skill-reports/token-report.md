# Why `/mpl-review` v3 burned the session limit, and the lean v4

All numbers are measured from headless runs (`claude -p --output-format stream-json`) with
the same model (`claude-opus-5-5`) and effort (`high`), on fresh clones of the same open PRs.
Each API call's `usage` block was summed.

## Measurements

| Run | PR | API calls (main + subagents) | Cache-read tokens | Cache-write tokens | Output tokens | Cost | Wall time |
|---|---|---:|---:|---:|---:|---:|---:|
| v2 (first version) | 32380 | 16 | 680k | 54k | 8k | $0.74 | 115 s |
| v2 | 32331 | 20 | 1,036k | 69k | 18k | $1.12 | 289 s |
| v2 | 32285 | 25 | 1,242k | 70k | 19k | $1.19 | 292 s |
| **v3 (`76299c23`)** | 32331 | **27 + 45** (3 subagents) | **≥ 3,747k** | **≥ 246k** | **≥ 83k** | **≥ $3.92** | killed at 8.6 min, unfinished |
| **v4 (`d4efcc03`)** | 32380 | 6 | **235k** | 18k | 4k | **$0.27** | 45 s |
| v4 | 32331 | 7 | **308k** | 32k | 15k | **$0.62** | 164 s |
| v4 | 32285 | 4 | **157k** | 20k | 7k | **$0.33** | 72 s |
| `/code-review high` (for reference) | all 3 | – | 1,436k | 179k | 35k | $1.88 | 365 s |

On #32331, **v4 used about 12× fewer cache-read tokens and at most a sixth of the cost of
v3**, and it finished the review. Across all 3 PRs, v4 used **about 4× fewer tokens than v2
and cost 60% less** ($1.23 vs $3.05).

## Why v3 blew up

Almost all the cost is **cache-read tokens**. Every API call re-sends the whole conversation
so far, so the cost is roughly *(number of calls) × (context size)*. v3 made both factors
bigger:

1. **"Launch three finder agents in parallel."** This was the biggest factor.
   - Each subagent starts cold. It pays a fresh cache write for the system prompt, tool
     definitions and diff, then re-discovers the code and makes its own 10–20 calls.
   - In the run: 45 subagent calls used 2.1M tokens, more than the whole v2 review.
   - All three fire at once, so their usage lands in a burst.
2. **Unbounded execution.** "Run the existing test file for each touched module" and
   "verify every candidate by execution" grew without limit. One finder ended up running
   **the entire Matplotlib test suite twice** (main and PR) with a 50-minute timeout, and
   the main agent made 20 Bash calls. Every pytest output that comes back is re-sent on
   each later turn.
3. **Raw `gh api` JSON for the thread.** REST comment objects carry about 2–3 KB of user,
   URL and reaction metadata per comment. "Never truncate" kept all of it in context for
   the rest of the review. (This was in v2 too; v4 uses `--jq` to keep only author, state,
   path and body.)
4. **Whole-file reads and full diffs.** Matplotlib modules are huge (`axes/_axes.py` is
   about 100k tokens). Changed SVG/PDF baselines also show up in a plain `git diff`.
5. **Opus at high effort.** It thinks at length. v3 had already written 83k output tokens,
   which are the most expensive kind, before it produced any review text.

## "50% of my 5-hour limit in 7 seconds": how?

No model produces that many tokens in 7 seconds. Here is what most likely happened, in
order of likelihood:

1. **The meter jumped; it didn't measure 7 seconds of work.** Usage is counted when API
   calls complete, and the limit display refreshes in steps. Three subagents plus the main
   loop finishing calls at nearly the same moment add a few minutes of work all at once.
   That looks like a 7-second spike.
2. **v3 is several million tokens per review, on Opus.** Our measured run was at about 4M
   tokens and $4 and still not finished. Opus counts much more heavily against plan limits
   than Sonnet or Haiku, so a single v3 review can plausibly take a large slice of a
   5-hour window.
3. **The review probably ran inside an already-long session.** If `/mpl-review` was run in
   the same CLI session that had just done the large `gh` stats work, every turn re-sent
   that whole history, perhaps 100–200k tokens. Over 27 main turns that alone is several
   million cache-read tokens. Any forked subagent would inherit that context too.
   **This is the biggest thing you control: start a fresh session (`/clear`) before running
   the skill.**

I can't see your CLI transcript, so (1) and (3) can't be confirmed from here. To check
them, sum the usage in your local transcript, including subagent transcripts:

```bash
python3 - <<'EOF'
import json, glob, os, collections
p = max(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")), key=os.path.getmtime)
files = [p] + glob.glob(p[:-6] + "/subagents/*.jsonl")
tot = collections.Counter(); seen = set()
for f in files:
    for l in open(f):
        e = json.loads(l); m = e.get("message") or {}
        if e.get("type") == "assistant" and m.get("id") not in seen:
            seen.add(m.get("id"))
            for k, v in (m.get("usage") or {}).items():
                if isinstance(v, int): tot[k] += v
print(p); print(dict(tot))
EOF
```

## What changed in v4 (6.8 KB, down from 8.0 KB)

- **No subagents.** I removed `Agent` from `allowed-tools`. The three bug-hunt angles from
  v3 (changed conditions, callers and round-trips, tests that can fail) are now one
  paragraph the main agent works through itself.
- **A token budget** at the top: batch independent commands into one turn, aim for at most
  12 tool calls, read around each hunk with Grep `-n` plus Read `offset/limit` (≤ 150 lines)
  instead of whole modules, and pipe long output through `tail`.
- **Compact inputs:**
  - `gh pr diff --exclude '*/baseline_images/*'` and `git diff -- . ':!*/baseline_images/*'`,
    so changed baselines are listed in `--stat` and treated as claims to check.
  - `gh api ... --jq` for the thread, keeping only author, state, path and body.
- **Execution limits:** run tests only when `matplotlib` imports from this tree; run only the
  PR's new or changed tests by node id; at most 3 repros, and only for blocker candidates.
  No building, installing or `PYTHONPATH` swaps.
- **Kept from v3:** "changed baselines are claims", "getters return resolved values, so probe
  `'none'`, `None`, `'inherit'` and alpha", "don't downgrade a blocker".

## Did accuracy drop?

It didn't drop in these runs; it went up. But read the caveat below.

| Real blocking bugs (all verified by running the code) | v2 | `/code-review high` | **v4** |
|---|:-:|:-:|:-:|
| 32331 B1: `\overset{f}{\rightarrow}` loses relation spacing | ❌ | ❌ | ✅ |
| 32331 B2: `<`/`>` treated as delimiters, so `$a<=b$` is narrower than `$a>=b$` | ✅ | ✅ | ❌ |
| 32331 B3 (new, found by v4): `\boldsymbol{=b}` / `\boldsymbol{\rightarrow}` no longer bold the operator | ❌ | ❌ | ✅ |
| 32285 B1: `facecolor='none'` legend turns black after regeneration | ❌ | ✅ | ✅ |
| **Blockers found** | 1/4 | 2/4 | **3/4** |
| Correct verdict (LGTM / NEEDS WORK / NEEDS WORK) | 2/3 | n/a | **3/3** |
| False or speculative findings | 0 | ≈ 9 | 1 ¹ |

1. v4 claimed the test-71 baselines were regenerated needlessly. That is wrong: it confused
   test index 71 with 72.

How I verified B3: on the PR, `$\boldsymbol{=b}$` renders `=` from `DejaVuSans.ttf`; on main
it uses `DejaVuSans-Bold.ttf`. v4 also said this might raise `IndexError`; it doesn't.

**Caveats, and they matter:**
- Each PR was run **once**. Run-to-run variance is large: v2 and v4 found *different* bugs
  in #32331.
- The v3 heuristics that v4 kept (sentinel `'none'`, "baselines are claims") were written
  **after** seeing the misses on these same PRs. So part of v4's recall on this set is
  leakage, not a general improvement.
- v4 ran nothing, because `matplotlib` wasn't importable in the clones. Its repros are
  labelled "not executed", and I executed the ones that matter.

A fair accuracy check needs a few fresh PRs the heuristics weren't tuned on. Token use,
though, is clearly lower: about a quarter of v2's per review, and a small fraction of v3's.

## Practical advice for contributors running the skill

- Run it in a **fresh session** (`/clear` first). Never run it at the end of a long session.
- Opus at medium effort, or Sonnet, is probably enough for small PRs. The skill can't choose
  the model or effort for you.
- Run it once per PR revision. `LGTM` or `NITS ONLY` means stop.
