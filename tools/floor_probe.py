#!/usr/bin/env python3
"""floor_probe.py -- C4.0 startup-floor decomposition, zero model calls.

Plan: vault/plans/cognitive-control-plane-2026-10-02.md section 11 (C4.0).

What the transcript shows. Before a session's (or subagent's) first model call the
harness records the injected startup components as `attachment` lines -- for example
`instructions` (CLAUDE.md + rules + memory), `skill_listing`, `deferred_tools_*`,
`prompt_snapshot` (the task payload), `environment` -- plus the opening user message.
Their TEXT is in the file; their TOKEN count is not.

How tokens are attributed (MEASURED fit, labelled):
  first_call_context ~ sum_c(rate * chars_c) + intercept[agent_type]
One shared tokens-per-char rate is fitted by least squares across every transcript,
with one intercept per agent type. The intercept is what the transcript cannot see
(system prompt, tool schemas, agent definition body): PROVIDER_OR_RUNTIME, and it is
reported as a remainder, never as a decomposition. The fit's residual is reported so
the attribution can be judged.

Lifetime rent: every startup component stays resident for the whole transcript, so
its rent = tokens x calls in that transcript (calls from the usage index).

CLI:
  probe [--since ISO] [--until ISO] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import usage_index as ux  # noqa: E402

# Component -> (floor class, controllability). Classes per the C4.0 brief.
COMPONENTS = {
    "instructions": ("GLOBAL_RULES+PROJECT_CONTEXT+MEMORY", "CPP_NOW"),
    "skill_listing": ("SKILL_DIRECTORY", "CPP_NOW"),
    "deferred_tools_delta": ("TOOLS/MCP", "CPP_WITH_ADAPTER"),
    "deferred_tools_record": ("TOOLS/MCP", "CPP_WITH_ADAPTER"),
    "prompt_snapshot": ("MISSION_PAYLOAD", "CPP_NOW"),
    "opening_message": ("MISSION_PAYLOAD", "CPP_NOW"),
    "environment": ("OTHER_RUNTIME", "PROVIDER"),
    "model": ("OTHER_RUNTIME", "PROVIDER"),
    "session_context": ("OTHER_RUNTIME", "PROVIDER"),
    # C4.1: the four largest former other_attachments types, named (window 09-30..10-02:
    # agent_listing_delta 64 %, hook records 13 %, SessionStart context 11 %, MCP 4 %).
    "agent_listing_delta": ("AGENT_DIRECTORY", "CPP_NOW"),
    "hook_additional_context": ("HOOK_INJECTION", "CPP_NOW"),
    "mcp_instructions_delta": ("TOOLS/MCP", "CPP_WITH_ADAPTER"),
    # The hook's stdout as recorded; whether the harness sends it to the model as well as
    # the hook_additional_context it carries is not verified, so it is not called CPP_NOW.
    "hook_success": ("HOOK_RECORD (injection unverified)", "UNKNOWN"),
    "hook_cancelled": ("HOOK_RECORD (injection unverified)", "UNKNOWN"),
    "other_attachments": ("OTHER", "UNKNOWN"),
}

CONTROLLABLE = ("CPP_NOW", "CPP_WITH_ADAPTER")


def instruction_class(path: str, home: Path | None = None) -> str:
    """Which owner an `instructions` file belongs to, by where it lives."""
    h = str(home or Path.home()).replace("\\", "/").rstrip("/").lower()
    p = path.replace("\\", "/").lower()
    if p == f"{h}/.claude/claude.md":
        return "GLOBAL_CLAUDE_MD"
    if p.startswith(f"{h}/.claude/rules/"):
        return "GLOBAL_RULE"
    if p.endswith("/memory.md"):
        return "MEMORY"
    return "PROJECT_CONTEXT"


def startup_components(path: Path, detail: dict | None = None):
    """(components chars, first_call_context) for one transcript, or None when it has
    no real call. Reads only up to the first usage line. When `detail` is given it also
    receives chars per `instructions` file ("file:<path>") and per unmapped attachment
    type ("type:<t>"); its file entries sum to at most comp["instructions"]."""
    comp = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                o = json.loads(ln)
            except ValueError:
                continue
            msg = o.get("message") if isinstance(o.get("message"), dict) else None
            if o.get("type") == "assistant" and msg and isinstance(msg.get("usage"), dict):
                if msg.get("model") == "<synthetic>":
                    return None
                u = msg["usage"]
                ctx = sum(u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens",
                                                   "cache_creation_input_tokens"))
                return dict(comp), ctx
            a = o.get("attachment") if isinstance(o.get("attachment"), dict) else None
            if a:
                t = a.get("type") or "unknown"
                key = t if t in COMPONENTS else "other_attachments"
                comp[key] += len(json.dumps(a, ensure_ascii=False))
                if detail is not None:
                    if t == "instructions" and isinstance(a.get("files"), list):
                        for it in a["files"]:
                            if isinstance(it, dict) and it.get("path"):
                                detail[f"file:{it['path']}"] = detail.get(f"file:{it['path']}", 0) \
                                    + len(json.dumps(it, ensure_ascii=False))
                    elif key == "other_attachments":
                        detail[f"type:{t}"] = detail.get(f"type:{t}", 0) \
                            + len(json.dumps(a, ensure_ascii=False))
            elif o.get("type") == "user" and msg is not None:
                comp["opening_message"] += len(json.dumps(msg.get("content"), ensure_ascii=False))
    return None


def fit(rows: list[dict]) -> dict:
    """One shared tokens-per-char rate (rows' total visible chars) + an intercept
    per agent type, by least squares on centred data within each type.
    Within-type centring removes the intercepts, leaving a 1-D regression."""
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)
    num = den = 0.0
    for rs in by_type.values():
        if len(rs) < 2:
            continue
        mx = statistics.mean(r["chars"] for r in rs)
        my = statistics.mean(r["ctx"] for r in rs)
        for r in rs:
            num += (r["chars"] - mx) * (r["ctx"] - my)
            den += (r["chars"] - mx) ** 2
    if den <= 0:
        return {"rate": None, "reason": "no within-type variation in visible chars"}
    rate = num / den
    icpt = {t: statistics.median(r["ctx"] - rate * r["chars"] for r in rs)
            for t, rs in by_type.items()}
    resid = [abs(r["ctx"] - (rate * r["chars"] + icpt[r["type"]])) for r in rows]
    return {"rate": rate, "intercepts": icpt,
            "abs_residual_median": statistics.median(resid),
            "abs_residual_p90": sorted(resid)[int(0.9 * (len(resid) - 1))]}


def probe(con, since: float, until: float, proj: Path = ux.DEFAULT_PROJ) -> dict:
    files = con.execute(
        "SELECT f.path, f.is_sub, s.agent_type, count(c.k) FROM files f "
        "LEFT JOIN subagents s ON s.file = f.path "
        "JOIN calls c ON c.file = f.path WHERE c.ts > ? AND c.ts <= ? "
        "GROUP BY f.path", (since, until)).fetchall()
    rows, skipped = [], 0
    for path, is_sub, atype, ncalls in files:
        detail: dict = {}
        try:
            res = startup_components(Path(path), detail)
        except OSError:
            res = None
        if res is None:
            skipped += 1
            continue
        comp, ctx = res
        t = (atype or "UNKNOWN_AGENT") if is_sub else "MAIN_SESSION"
        rows.append({"path": path, "type": t, "comp": comp, "ctx": ctx, "calls": ncalls,
                     "chars": sum(comp.values()), "detail": detail})
    f = fit(rows)
    if f.get("rate") is None:
        return {"verdict": "UNMEASURED", **f, "transcripts": len(rows)}
    rate = f["rate"]
    per_type = defaultdict(lambda: {"n": 0, "calls": 0, "ctx": [], "comp": defaultdict(list)})
    rent = defaultdict(float)
    rent_opaque = 0.0
    for r in rows:
        pt = per_type[r["type"]]
        pt["n"] += 1
        pt["calls"] += r["calls"]
        pt["ctx"].append(r["ctx"])
        for k, chars in r["comp"].items():
            pt["comp"][k].append(chars * rate)
            rent[k] += chars * rate * r["calls"]
        rent_opaque += max(0.0, f["intercepts"][r["type"]]) * r["calls"]
    types = {}
    for t, pt in sorted(per_type.items(), key=lambda kv: -kv[1]["calls"]):
        types[t] = {"transcripts": pt["n"], "calls": pt["calls"],
                    "first_call_ctx_median": statistics.median(pt["ctx"]),
                    "components_tokens_median": {k: round(statistics.median(v + [0] * (pt["n"] - len(v))))
                                                 for k, v in pt["comp"].items()},
                    "provider_or_runtime_remainder": round(f["intercepts"][t])}
    total_rent = sum(rent.values()) + rent_opaque
    ranked = sorted(((k, v) for k, v in rent.items()), key=lambda kv: -kv[1])
    return {
        "window": [ux._iso(since), ux._iso(until)],
        "transcripts": len(rows), "skipped_no_real_call": skipped,
        "fit": {"tokens_per_char": round(rate, 4),
                "abs_residual_median_tokens": round(f["abs_residual_median"]),
                "abs_residual_p90_tokens": round(f["abs_residual_p90"]),
                "label": "MEASURED fit; component tokens are ATTRIBUTED, not counted"},
        "by_agent_type": dict(list(types.items())[:12]),
        "lifetime_rent_tokens": {
            "total_startup_floor": round(total_rent),
            "by_component": [{"component": k, "class": COMPONENTS.get(k, ("?", "UNKNOWN"))[0],
                              "control": COMPONENTS.get(k, ("?", "UNKNOWN"))[1],
                              "tokens": round(v), "share": round(v / total_rent, 3)}
                             for k, v in ranked]
                            + [{"component": "provider_or_runtime_remainder",
                                "class": "PROVIDER_OPAQUE (system prompt, tool schemas, agent body)",
                                "control": "PARTIAL (agent body is CPP)", "tokens": round(rent_opaque),
                                "share": round(rent_opaque / total_rent, 3)}]},
        "c41": rank_detail(rows, rate, total_rent, ranked),
    }


def rank_detail(rows: list[dict], rate: float, total_rent: float, ranked,
                home: Path | None = None) -> dict:
    """C4.1: where the controllable rent lives. Shares are of the WHOLE startup floor,
    so they compare directly with by_component. Rent is token-calls of resident context,
    mostly served as cache reads: it ranks levers, it is not a price."""
    files, unmapped = defaultdict(float), defaultdict(float)
    seen = defaultdict(int)
    for r in rows:
        for k, chars in (r.get("detail") or {}).items():
            v = chars * rate * r["calls"]
            if k.startswith("file:"):
                files[k[5:]] += v
                seen[k[5:]] += 1
            else:
                unmapped[k[5:]] += v
    by_class = defaultdict(float)
    for p, v in files.items():
        by_class[instruction_class(p, home)] += v

    def share(v):
        return round(v / total_rent, 4)
    return {
        "controllable_ranked": [
            {"component": k, "control": COMPONENTS[k][1], "tokens": round(v), "share": share(v)}
            for k, v in ranked if COMPONENTS.get(k, ("", ""))[1] in CONTROLLABLE],
        "instructions_by_class": {c: {"tokens": round(v), "share": share(v)}
                                  for c, v in sorted(by_class.items(), key=lambda kv: -kv[1])},
        "instructions_top_files": [
            {"path": p, "class": instruction_class(p, home), "transcripts": seen[p],
             "tokens": round(v), "share": share(v)}
            for p, v in sorted(files.items(), key=lambda kv: -kv[1])[:25]],
        "unmapped_attachment_types": [
            {"type": t, "tokens": round(v), "share": share(v)}
            for t, v in sorted(unmapped.items(), key=lambda kv: -kv[1])[:10]],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["probe"])
    ap.add_argument("--db", default=str(ux.DEFAULT_DB))
    ap.add_argument("--since", default="2026-09-30T17:00:00Z")
    ap.add_argument("--until", default="2026-10-02T09:40:00Z")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    con = ux.connect(Path(a.db))
    res = probe(con, ux._epoch(a.since), ux._epoch(a.until))
    text = json.dumps(res, indent=1, default=str)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
