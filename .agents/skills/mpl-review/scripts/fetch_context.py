"""Gather a compact review context for /mpl-review in ONE call (fewer agent turns = fewer tokens).

Usage (from the repo root):
    python .agents/skills/mpl-review/scripts/fetch_context.py          # current branch + uncommitted
    python .agents/skills/mpl-review/scripts/fetch_context.py 12345    # PR number or URL

Writes <tmp>/context.md (meta, diffstat, baseline-image changes, thread, CI) and
<tmp>/diff.patch (code diff without baseline images), then prints both paths.
Never posts to GitHub or changes files/git state.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "matplotlib/matplotlib"
NO_BASELINES = ":!*/baseline_images/*"
BODY_MAX = 1500  # chars kept per comment; long bot/CI dumps are cut


def run(*cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr.strip()


def gh_json(*args):
    rc, out, err = run("gh", *args)
    if rc:
        raise RuntimeError(err or f"gh {' '.join(args)} failed")
    return json.loads(out or "null")


def thread(n):
    """Reviews, inline comments and conversation, compacted to author/state/path/body."""
    lines = []
    for kind, path in [("review", f"pulls/{n}/reviews"),
                       ("inline", f"pulls/{n}/comments"),
                       ("comment", f"issues/{n}/comments")]:
        pages = gh_json("api", "-X", "GET", "--paginate", "--slurp",
                        f"repos/{REPO}/{path}")
        for item in (x for page in pages for x in page):
            user = item.get("user") or {}
            if user.get("type") == "Bot":
                continue
            body = (item.get("body") or "").strip()
            state = item.get("state") or ""
            if not body and state in ("", "COMMENTED"):
                continue
            if len(body) > BODY_MAX:
                body = body[:BODY_MAX] + " …[cut]"
            where = f" {item['path']}:{item.get('line') or ''}" if item.get("path") else ""
            lines.append(f"- [{kind}{(' ' + state) if state else ''}] "
                         f"@{user.get('login')} ({item.get('author_association', '').lower()})"
                         f"{where} {(item.get('created_at') or item.get('submitted_at') or '')[:10]}: {body}")
    return lines or ["(no human reviews or comments)"]


def upstream_remote():
    _, out, _ = run("git", "remote", "-v")
    for line in out.splitlines():
        if REPO in line:
            return line.split()[0]
    raise SystemExit(f"No git remote points at {REPO}; add one (git remote add upstream ...).")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    m = re.search(r"(\d+)\s*$", target)
    out = Path(tempfile.mkdtemp(prefix="mpl-review-"))
    ctx, n = [], m.group(1) if m else None

    if n:  # PR mode: everything from GitHub
        meta = gh_json("pr", "view", n, "--repo", REPO, "--json",
                       "title,author,state,isDraft,headRefOid,baseRefName,body,files")
        rc, diff, err = run("gh", "pr", "diff", n, "--repo", REPO,
                            "--exclude", "*/baseline_images/*")
        if rc:
            raise SystemExit(f"gh pr diff failed: {err}")
        files = meta.get("files") or []
        stat = [f"{f['path']} (+{f['additions']}/-{f['deletions']})" for f in files]
        ctx += [f"# PR #{n}: {meta['title']}", f"author @{meta['author']['login']} · "
                f"{meta['state']}{' · DRAFT' if meta['isDraft'] else ''} · head {meta['headRefOid'][:10]}",
                "", "## Description", (meta.get("body") or "").strip()[:4000]]
        _, local_head, _ = run("git", "rev-parse", "HEAD")
        ctx.append("\nLocal checkout IS the PR head." if local_head.strip() == meta["headRefOid"]
                   else "\nLocal checkout is NOT the PR head: review from the diff; don't run tests.")
    else:  # local mode: current branch vs upstream main
        up = upstream_remote()
        _, base, _ = run("git", "merge-base", "HEAD", f"{up}/main")
        base = base.strip()
        _, diff, _ = run("git", "diff", base, "--", ".", NO_BASELINES)
        _, s, _ = run("git", "diff", "--stat=120", base)
        stat = s.splitlines()
        _, behind, _ = run("git", "rev-list", "--count", f"HEAD..{up}/main")
        _, untracked, _ = run("git", "ls-files", "--others", "--exclude-standard")
        _, branch, _ = run("git", "branch", "--show-current")
        ctx += [f"# Local branch `{branch.strip()}` vs {up}/main (base {base[:10]})",
                f"{behind.strip()} commits behind {up}/main (as of last fetch)."]
        if untracked.strip():
            ctx += ["Untracked files (Read the source ones):", untracked.strip()]
        rc, o, _ = run("gh", "pr", "list", "--repo", REPO, "--head", branch.strip(),
                       "--json", "number")
        prs = json.loads(o) if rc == 0 and o.strip() else []
        n = str(prs[0]["number"]) if len(prs) == 1 else None
        ctx.append(f"Open PR for this branch: #{n}" if n else "No unique PR found for this branch.")

    baselines = [s for s in stat if "baseline_images" in s]
    ctx += ["", "## Changed files", *stat]
    if baselines:
        ctx += ["", "## Baseline images changed (claims to verify, not evidence)", *baselines]

    if n:
        try:
            ctx += ["", "## Thread", *thread(n)]
        except Exception as e:  # unknown is not empty
            ctx += ["", f"## Thread: NOT FETCHED ({e}). Say so in the review."]
        rc, o, _ = run("gh", "pr", "checks", n, "--repo", REPO, "--json", "name,state")
        failing = [c["name"] for c in (json.loads(o) if rc == 0 and o.strip() else [])
                   if c.get("state") in ("FAILURE", "ERROR", "CANCELLED")]
        ctx += ["", "## CI", ("failing: " + ", ".join(failing)) if failing
                else ("no failing checks" if rc == 0 else "CI status not fetched")]

    (out / "context.md").write_text("\n".join(ctx) + "\n", encoding="utf-8")
    (out / "diff.patch").write_text(diff, encoding="utf-8")
    print(f"context: {out / 'context.md'}  ({len(ctx)} lines)")
    print(f"diff:    {out / 'diff.patch'}  ({diff.count(chr(10))} lines, baseline images excluded)")


if __name__ == "__main__":
    main()
