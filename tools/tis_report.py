#!/usr/bin/env python3
"""TIS Capa 2 -- analytics CLI (TCO v1 extended).

Flags:

  --summary           per-session aggregate (calls / in / out / cache% / cost$)
  --by-skill          top-N skills by input_tokens (now includes
                      recommended-model column per TCO B3 audit trail)
  --cache-ratio       overall cache_read / (input + cache_read) percentage
  --cost-projection   compare actual cost vs TCO-routed cost; emits
                      estimated_savings_pct and top-3 routing opportunities
  --since DATE        filter entries from YYYY-MM-DD inclusive

Pricing source: vault/pricing/anthropic_2026-05.json (authoritative).
Fallback constants are kept inline as a last-resort if the pricing
file is unreadable -- but the live file is preferred.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import tis  # noqa: E402

PRICING_JSON = ROOT / "vault" / "pricing" / "anthropic_2026-05.json"
ROUTING_JSON = ROOT / "vault" / "config" / "model-routing.json"


# Last-resort fallback. The JSON file is the source of truth.
_FALLBACK_PRICING = {
    "claude-opus-4-7":          {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6":        {"input": 3.0,  "output": 15.0},
    "claude-sonnet-4-20250514": {"input": 3.0,  "output": 15.0},
    "claude-haiku-4-5":         {"input": 1.0,  "output": 5.0},
    "claude-code-hook":         {"input": 0.0,  "output": 0.0},
    "default":                  {"input": 3.0,  "output": 15.0},
}


def _load_pricing() -> dict:
    """Read pricing from authoritative JSON; fall back to inline
    constants if the file is missing or malformed. Always return
    a flat {model_id: {input, output}} map."""
    if not PRICING_JSON.is_file():
        return dict(_FALLBACK_PRICING)
    try:
        raw = json.loads(PRICING_JSON.read_text(encoding="utf-8"))
        models = raw.get("models") or {}
        if not models:
            return dict(_FALLBACK_PRICING)
        flat = {}
        for mid, m in models.items():
            flat[mid] = {
                "input": float(m.get("input", _FALLBACK_PRICING["default"]["input"])),
                "output": float(m.get("output", _FALLBACK_PRICING["default"]["output"])),
            }
        flat.setdefault("claude-code-hook", {"input": 0.0, "output": 0.0})
        flat.setdefault("default", _FALLBACK_PRICING["default"])
        return flat
    except (OSError, ValueError, KeyError, TypeError):
        return dict(_FALLBACK_PRICING)


def _load_routing() -> dict:
    if not ROUTING_JSON.is_file():
        return {"default_model": "claude-opus-4-7",
                "rules": [], "skill_to_task_type": {}}
    try:
        return json.loads(ROUTING_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"default_model": "claude-opus-4-7",
                "rules": [], "skill_to_task_type": {}}


PRICING = _load_pricing()
ROUTING = _load_routing()


def _price_for(model: str) -> dict:
    if model in PRICING:
        return PRICING[model]
    for key in PRICING:
        if key != "default" and key in (model or ""):
            return PRICING[key]
    return PRICING["default"]


def _cost_for(input_tokens: int, output_tokens: int, model: str) -> float:
    p = _price_for(model)
    return (input_tokens * p["input"] / 1_000_000 +
            output_tokens * p["output"] / 1_000_000)


def _cost_usd(entry: dict) -> float:
    return _cost_for(entry.get("input_tokens", 0),
                     entry.get("output_tokens", 0),
                     entry.get("model", ""))


def _recommend_model_for_skill(skill_name: str) -> tuple[str, str]:
    """Return (recommended_model, task_type). Default = opus / unmapped."""
    default = ROUTING.get("default_model", "claude-opus-4-7")
    task_type = ROUTING.get("skill_to_task_type", {}).get(skill_name)
    if task_type is None:
        return default, "unmapped"
    for r in ROUTING.get("rules", []):
        if r.get("task_type") == task_type:
            return r.get("recommended_model", default), task_type
    return default, task_type


def _print_table(headers, rows):
    if not rows:
        print(f"(no data for {headers})")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "  "
    print(sep.join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print(sep.join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print(sep.join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_summary(entries):
    per_session = defaultdict(lambda: {
        "calls": 0, "in": 0, "out": 0, "cr": 0, "cc": 0, "cost": 0.0,
    })
    for e in entries:
        s = per_session[e.get("session_id", "")]
        s["calls"] += 1
        s["in"]   += e.get("input_tokens", 0)
        s["out"]  += e.get("output_tokens", 0)
        s["cr"]   += e.get("cache_read_tokens", 0)
        s["cc"]   += e.get("cache_creation_tokens", 0)
        s["cost"] += _cost_usd(e)
    rows = []
    for sid, s in sorted(per_session.items()):
        denom = s["in"] + s["cr"]
        ratio = (s["cr"] / denom * 100) if denom else 0.0
        rows.append([sid, s["calls"], s["in"], s["out"],
                     f"{ratio:.1f}%", f"${s['cost']:.5f}"])
    _print_table(
        ["session", "calls", "in_tok", "out_tok", "cache%", "cost_usd"],
        rows,
    )
    return 0


def cmd_by_skill(entries, top_n: int = 10):
    """Per-skill aggregate. TCO B3 extension: include 'rec_model'
    (recommended per model-routing.json) and 'actual_model' (most
    common model observed in log) columns. Hook events (model =
    claude-code-hook) audit as 'free' -- they are telemetry, not
    LLM calls, so a routing recommendation does not apply."""
    agg = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0,
                                "cost": 0.0,
                                "models": defaultdict(int)})
    for e in entries:
        name = e.get("skill_name", "")
        a = agg[name]
        a["calls"] += 1
        a["in"]    += e.get("input_tokens", 0)
        a["out"]   += e.get("output_tokens", 0)
        a["cost"]  += _cost_usd(e)
        m = e.get("model", "") or "(unset)"
        a["models"][m] += 1
    ordered = sorted(agg.items(), key=lambda kv: kv[1]["in"], reverse=True)
    rows = []
    for name, a in ordered[:top_n]:
        rec_model, task_type = _recommend_model_for_skill(name)
        most_used = max(a["models"].items(), key=lambda kv: kv[1])[0] if a["models"] else "(none)"
        if most_used == "claude-code-hook":
            audit = "free"
        elif rec_model in most_used or most_used in rec_model:
            audit = "ok"
        else:
            audit = "MISMATCH"
        rows.append([name, a["calls"], a["in"], a["out"],
                     f"${a['cost']:.5f}", task_type,
                     rec_model.replace("claude-", ""),
                     most_used.replace("claude-", ""),
                     audit])
    _print_table(
        ["skill", "calls", "in_tok", "out_tok", "cost_usd",
         "task_type", "rec_model", "actual_model", "audit"],
        rows,
    )
    return 0


def cmd_cache_ratio(entries):
    total_in = sum(e.get("input_tokens", 0) for e in entries)
    total_cr = sum(e.get("cache_read_tokens", 0) for e in entries)
    denom = total_in + total_cr
    ratio = (total_cr / denom * 100) if denom else 0.0
    print(f"cache_hit_ratio = {ratio:.2f}% "
          f"(cache_read={total_cr} / (input={total_in} + cache_read={total_cr}))")
    print(f"entries={len(entries)}")
    return 0


def cmd_cost_projection(entries):
    """Compare actual vs TCO-routed cost. Emits estimated_savings_pct
    and top-3 routing opportunities.

    Filter rule: skip telemetry-only events (model = claude-code-hook).
    They are zero-cost pings to the TIS log -- including them in a
    routing projection is a category error. If no LLM-priced entries
    remain after filtering, emit explicit honest-zero reason."""
    if not entries:
        print("estimated_savings_pct: 0  (reason: NO_DATA -- TIS log empty)")
        print("top_3_routing_opportunities: []")
        return 0

    llm_entries = [e for e in entries
                   if (e.get("model") or "") != "claude-code-hook"]
    hook_count = len(entries) - len(llm_entries)
    if not llm_entries:
        print(f"estimated_savings_pct: 0  (reason: "
              f"NO_LLM_ENTRIES -- {hook_count} telemetry-only events skipped)")
        print("top_3_routing_opportunities: []")
        return 0

    skill_agg = defaultdict(lambda: {"in": 0, "out": 0,
                                      "actual_model_counts": defaultdict(int)})
    for e in llm_entries:
        name = e.get("skill_name", "")
        s = skill_agg[name]
        s["in"]  += e.get("input_tokens", 0)
        s["out"] += e.get("output_tokens", 0)
        m = e.get("model", "") or "(unset)"
        s["actual_model_counts"][m] += 1

    actual_total = 0.0
    optimized_total = 0.0
    opportunities = []

    for name, s in skill_agg.items():
        if not s["actual_model_counts"]:
            continue
        most_used_actual = max(s["actual_model_counts"].items(),
                                key=lambda kv: kv[1])[0]
        rec_model, task_type = _recommend_model_for_skill(name)
        actual_cost = _cost_for(s["in"], s["out"], most_used_actual)
        optimized_cost = _cost_for(s["in"], s["out"], rec_model)
        actual_total += actual_cost
        optimized_total += optimized_cost
        if actual_cost > optimized_cost + 1e-9:
            opportunities.append({
                "skill": name,
                "actual_model": most_used_actual,
                "recommended_model": rec_model,
                "task_type": task_type,
                "actual_cost_usd": round(actual_cost, 5),
                "optimized_cost_usd": round(optimized_cost, 5),
                "savings_usd": round(actual_cost - optimized_cost, 5),
                "in_tokens": s["in"],
                "out_tokens": s["out"],
            })

    if actual_total <= 0:
        pct = 0
        reason = "ZERO_ACTUAL_COST -- all entries free-tier (hook events)"
    else:
        pct = int((actual_total - optimized_total) * 100 / actual_total)
        if pct > 0:
            reason = "computed_from_log -- optimizable (route grunt to cheaper model)"
        elif pct == 0:
            reason = "computed_from_log -- already optimal"
        else:
            reason = ("computed_from_log -- actual cheaper than recommended; "
                      "router rule may be too conservative for this skill mix")

    opportunities.sort(key=lambda o: o["savings_usd"], reverse=True)
    top3 = opportunities[:3]

    print(f"actual_total_cost_usd:      ${actual_total:.5f}")
    print(f"optimized_total_cost_usd:   ${optimized_total:.5f}")
    print(f"estimated_savings_usd:      ${actual_total - optimized_total:.5f}")
    print(f"estimated_savings_pct:      {pct}%  (reason: {reason})")
    print()
    print("top_3_routing_opportunities:")
    if not top3:
        print("  (none -- all skills already on recommended model OR "
              "ZERO_ACTUAL_COST)")
    else:
        for o in top3:
            print(f"  - skill={o['skill']!r}  task_type={o['task_type']}")
            print(f"    actual={o['actual_model']} -> "
                  f"recommended={o['recommended_model']}")
            print(f"    in_tok={o['in_tokens']}  out_tok={o['out_tokens']}")
            print(f"    actual_cost=${o['actual_cost_usd']}  "
                  f"optimized=${o['optimized_cost_usd']}  "
                  f"savings=${o['savings_usd']}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--by-skill", action="store_true")
    ap.add_argument("--cache-ratio", action="store_true")
    ap.add_argument("--cost-projection", action="store_true",
                    help="TCO: actual vs routed cost + top-3 opportunities")
    ap.add_argument("--since", metavar="YYYY-MM-DD")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args(argv)

    if not any([args.summary, args.by_skill, args.cache_ratio,
                args.cost_projection]):
        ap.print_help()
        return 2

    entries = tis.read_log(since_date=args.since)
    if args.summary:
        return cmd_summary(entries)
    if args.by_skill:
        return cmd_by_skill(entries, top_n=args.top)
    if args.cache_ratio:
        return cmd_cache_ratio(entries)
    if args.cost_projection:
        return cmd_cost_projection(entries)
    return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main(sys.argv[1:]))
