"""F0 floor split: first-call floor of fresh sessions vs the blocks injected before that call.

Deterministic, zero model. For each top-level transcript under ~/.claude/projects modified in the last
DAYS days: floor = input + cache_creation + cache_read of the FIRST assistant message with usage; content
chars per attachment type (and the user prompt) BEFORE that message. Fits floor = a + b * chars by least
squares: a = what every call carries that the transcript does not show (system prompt + tool schemas),
b = tokens per char. Prints JSON.
"""
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

DAYS = float(sys.argv[1]) if len(sys.argv) > 1 else 7
ROOT = Path(os.path.expanduser("~")) / ".claude" / "projects"
cutoff = time.time() - DAYS * 86400


def text_chars(v) -> int:
    if isinstance(v, str):
        return len(v)
    if isinstance(v, dict):
        return sum(text_chars(x) for k, x in v.items() if k not in ("type", "uuid", "toolUseID", "hookName",
                                                                    "hookEvent", "timestamp"))
    if isinstance(v, list):
        return sum(text_chars(x) for x in v)
    return 0


rows = []
for d in ROOT.iterdir():
    if not d.is_dir():
        continue
    for p in d.glob("*.jsonl"):
        try:
            if p.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        per = defaultdict(int)
        floor = None
        model = None
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for n, line in enumerate(fh):
                    if n > 400:
                        break
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    t = r.get("type")
                    if t == "attachment":
                        a = r.get("attachment") or {}
                        per["att:" + str(a.get("type"))] += text_chars(a)
                    elif t == "user":
                        m = r.get("message") or {}
                        per["user_prompt"] += text_chars(m.get("content"))
                    elif t == "assistant":
                        m = r.get("message") or {}
                        u = m.get("usage")
                        if u and m.get("model") != "<synthetic>":
                            floor = sum(int(u.get(k) or 0) for k in
                                        ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                            model = m.get("model")
                            break
                        # an assistant entry without usage before the first counted one: resumed/odd; skip file
                        per["__assistant_before"] += 1
        except OSError:
            continue
        if floor and not per.get("__assistant_before"):
            rows.append({"file": p.name[:8], "project": d.name[-40:], "model": model, "floor": floor,
                         "chars": dict(per), "total_chars": sum(per.values())})

n = len(rows)
out = {"days": DAYS, "n": n}
if n >= 3:
    xs = [r["total_chars"] for r in rows]
    ys = [r["floor"] for r in rows]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx if sxx else None
    a = my - b * mx if b is not None else None
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys)) if b is not None else None
    ss_tot = sum((y - my) ** 2 for y in ys)
    out.update(intercept_tokens=round(a) if a is not None else None, tokens_per_char=b,
               r2=(1 - ss_res / ss_tot) if ss_tot else None,
               floor_median=sorted(ys)[n // 2], floor_min=min(ys), floor_max=max(ys),
               chars_median=sorted(xs)[n // 2], chars_min=min(xs), chars_max=max(xs))
    types = sorted({k for r in rows for k in r["chars"]})
    out["median_chars_by_type"] = {k: sorted(r["chars"].get(k, 0) for r in rows)[n // 2] for k in types}
    out["models"] = {m: sum(1 for r in rows if r["model"] == m) for m in {r["model"] for r in rows}}
    out["projects"] = len({r["project"] for r in rows})
GROUPS = {
    "instructions": ["att:instructions"],
    "skill_listing": ["att:skill_listing"],
    "agent_listing": ["att:agent_listing_delta"],
    "hook_context": ["att:hook_additional_context"],
    "hook_success": ["att:hook_success"],
    "prompt_snapshot": ["att:prompt_snapshot"],
    "mcp_deferred": ["att:mcp_instructions_delta", "att:deferred_tools_delta"],
    "user_prompt": ["user_prompt"],
}


def solve(A, y):
    """Least squares via normal equations + Gaussian elimination with partial pivoting."""
    k = len(A[0])
    M = [[sum(r[i] * r[j] for r in A) for j in range(k)] + [sum(r[i] * yy for r, yy in zip(A, y))] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-12:
            return None
        for r in range(k):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return [M[i][k] / M[i][i] for i in range(k)]


if n >= 20:
    names = list(GROUPS)
    A = [[1.0] + [float(sum(r["chars"].get(t, 0) for t in GROUPS[g])) for g in names] for r in rows]
    y = [float(r["floor"]) for r in rows]
    coef = solve(A, y)
    if coef:
        pred = [sum(c * x for c, x in zip(coef, row)) for row in A]
        my = sum(y) / n
        r2 = 1 - sum((a - b) ** 2 for a, b in zip(y, pred)) / sum((a - my) ** 2 for a in y)
        med = {g: sorted(sum(r["chars"].get(t, 0) for t in GROUPS[g]) for r in rows)[n // 2] for g in names}
        out["multi"] = {"r2": r2, "intercept_tokens": round(coef[0]),
                        "per_group": {g: {"tok_per_char": round(coef[i + 1], 4), "median_chars": med[g],
                                          "median_tokens": round(coef[i + 1] * med[g])}
                                      for i, g in enumerate(names)}}


def fit1(xs, ys):
    m = len(xs)
    mx, my = sum(xs) / m, sum(ys) / m
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    r2 = 1 - sum((y - a - b * x) ** 2 for x, y in zip(xs, ys)) / sum((y - my) ** 2 for y in ys)
    return round(a), round(b, 4), round(r2, 4)


if n >= 20:
    ys = [r["floor"] for r in rows]
    variants = {"all": set(), "no_hook_success": {"att:hook_success"}, "no_prompt_snapshot": {"att:prompt_snapshot"},
                "no_both": {"att:hook_success", "att:prompt_snapshot"},
                "no_hook_context": {"att:hook_additional_context"}}
    out["variants"] = {}
    for vname, drop in variants.items():
        xs = [sum(v for k, v in r["chars"].items() if k not in drop) for r in rows]
        out["variants"][vname] = dict(zip(("intercept", "tok_per_char", "r2"), fit1(xs, ys)))
print(json.dumps(out, indent=1))
