"""Usage: python tally.py run.jsonl [...]  -> per-run tokens, calls, cost, loop flags."""
import collections, json, sys
for path in sys.argv[1:]:
    seen, calls, tok, cmds, res = set(), collections.Counter(), collections.Counter(), [], None
    for line in open(path):
        try: e = json.loads(line)
        except ValueError: continue
        if e.get("type") == "result": res = e
        if e.get("type") != "assistant": continue
        m, who = e["message"], ("sub" if e.get("parent_tool_use_id") else "main")
        cmds += [json.dumps(b["input"]) for b in m.get("content", []) if b.get("type") == "tool_use"]
        if m.get("id") in seen: continue
        seen.add(m.get("id")); calls[who] += 1
        for k, v in (m.get("usage") or {}).items():
            if isinstance(v, int): tok[k] += v
    dup = max(collections.Counter(cmds).values(), default=0)
    mu = next(iter((res or {}).get("modelUsage", {}).values()), {})
    print(json.dumps({"run": path, "api_calls": dict(calls), "tool_calls": len(cmds),
        "cache_read": tok["cache_read_input_tokens"], "cache_write": tok["cache_creation_input_tokens"],
        "output": mu.get("outputTokens"), "cost_usd": (res or {}).get("total_cost_usd"),
        "wall_s": round((res or {}).get("duration_ms", 0) / 1000), "finished": bool(res),
        "max_repeat_of_one_call": dup, "flags": [f for f, c in [("LOOP?", dup > 1),
        ("SUBAGENTS", calls["sub"] > 0), ("OVER_12_CALLS", len(cmds) > 12)] if c]}))
