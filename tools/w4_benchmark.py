"""W4 benchmark: slim-t2 worker sessions vs the W1 baseline. Measurement only; transcripts are read-only."""
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pricing_source import current_pricing_path  # noqa: E402
OUT = ROOT / "vault" / "programs" / "factory-tranche-a"
REF_MODEL = "claude-opus-5-5"
SESSIONS = {
    "W3a": "c6c0e19d-c447-4de8-be77-4b4dd1abd63b",
    "W3b": "dab6a4f1-5520-4887-b07c-604aeee8ebde",
    "W3c": "c3c64013-d65a-415d-b32d-e068f3c715a3",
    "W3d": "943a6303-6d4a-4794-ad85-6965b2412dd2",
}
OLD = {"executor_per_session": 57.1 / 21, "worker_per_epoch": 28.0 / 8}


def _processed(u):
    """input + cache read + cache write (output excluded)."""
    return (int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0)
            + int(u.get("cache_creation_input_tokens") or 0))


def resolve_pricing():
    """Resolved current pricing file. Raises FileNotFoundError when none exists: never price at 0."""
    return Path(current_pricing_path())


def _rel(p):
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def load_prices(path=None):
    path = resolve_pricing() if path is None else path
    return json.loads(Path(path).read_text(encoding="utf-8"))["models"]


def price(tot, model, prices):
    """USD for token totals at model; None (UNPRICED) when the model has no row."""
    p = prices.get(model)
    if not p:
        return None
    return (tot["input"] * p["input"] + tot["cache_read"] * p["cache_read"]
            + tot["cw5"] * p["cache_write_5m"] + tot["cw1h"] * p["cache_write_1h"]
            + tot["output"] * p["output"]) / 1e6


def find_transcript(sid):
    hits = glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", sid + ".jsonl"))
    return hits[0] if hits else None


def analyze(path, prices):
    if not path or not Path(path).is_file():
        return {"error": "transcript not found: %s" % path}
    seen, rows, hooks = set(), [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            a = r.get("attachment")
            if isinstance(a, dict) and a.get("type") == "hook_additional_context":
                for c in a.get("content") or []:
                    if isinstance(c, str) and "BUDGET" in c.upper() and c not in [h["text"] for h in hooks]:
                        hooks.append({"timestamp": r.get("timestamp"), "text": c,
                                      "calls_before": len(rows)})
            m = r.get("message")
            if not isinstance(m, dict) or r.get("type") != "assistant":
                continue
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            rows.append((m.get("model"), u))
    if not rows:
        return {"error": "no assistant usage rows in %s" % path}
    t = dict(input=0, cache_read=0, cw5=0, cw1h=0, cw_total=0, output=0)
    models, cum, last_cum = {}, 0, 0
    per_model = {}
    for model, u in rows:
        cc = u.get("cache_creation") or {}
        w = int(u.get("cache_creation_input_tokens") or 0)
        if cc and ("ephemeral_1h_input_tokens" in cc or "ephemeral_5m_input_tokens" in cc):
            w1, w5 = int(cc.get("ephemeral_1h_input_tokens") or 0), int(cc.get("ephemeral_5m_input_tokens") or 0)
        else:
            w1, w5 = 0, w  # no split in the row: billed as 5m (lower bound), flagged below
        row = dict(input=int(u.get("input_tokens") or 0), cache_read=int(u.get("cache_read_input_tokens") or 0),
                   cw5=w5, cw1h=w1, output=int(u.get("output_tokens") or 0))
        for k, v in row.items():
            t[k] += v
            pm = per_model.setdefault(model, dict(input=0, cache_read=0, cw5=0, cw1h=0, output=0))
            pm[k] += v
        t["cw_total"] += w
        models[model] = models.get(model, 0) + 1
        cum += _processed(u)
    processed = t["input"] + t["cache_read"] + t["cw_total"]
    if sum(_processed(u) for _, u in rows) != processed:
        return {"error": "internal: processed mismatch"}
    denom = processed
    costs, unpriced = 0.0, []
    for model, tot in per_model.items():
        c = price(tot, model, prices)
        if c is None:
            unpriced.append(model)
        else:
            costs += c
    cost = None if unpriced else costs
    ref = price(dict(input=t["input"], cache_read=t["cache_read"], cw5=t["cw5"], cw1h=t["cw1h"],
                     output=t["output"]), REF_MODEL, prices)
    out = {
        "calls": len(rows), "call1_processed": _processed(rows[0][1]), "processed": processed,
        "input": t["input"], "cache_read": t["cache_read"], "cache_write": t["cw_total"],
        "cache_write_5m": t["cw5"], "cache_write_1h": t["cw1h"], "output": t["output"],
        "cache_hit_ratio": (t["cache_read"] / denom) if denom else None,
        "models": models, "cost_usd": cost,
        "cost_status": "UNPRICED: " + ",".join(unpriced) if unpriced else "priced",
        "cost_usd_at_opus_5_5": ref,
        "last_call_cumulative_processed": processed,
        "budget_hook_texts": hooks,
    }
    try:
        from mission_spend import session_tokens
        st = session_tokens(Path(path))
        out["session_tokens_crosscheck"] = {"tokens_incl_output": st["tokens"],
                                            "ours_incl_output": processed + t["output"],
                                            "match": st["tokens"] == processed + t["output"]}
    except Exception as e:  # cross-check is advisory
        out["session_tokens_crosscheck"] = {"error": repr(e)}
    return out


def _f(x, d=2):
    return "UNKNOWN" if x is None else ("%.*f" % (d, x))


def judge(res):
    """Done-gate verdicts. res: sid-label -> analyze() dict."""
    v = []
    ok = {k: r for k, r in res.items() if "error" not in r}
    for k, r in res.items():
        if "error" in r:
            v.append(("data", k, "ERROR", r["error"]))
    for k, r in ok.items():
        for nm, base in OLD.items():
            for lab, c in (("transcript model", r["cost_usd"]), ("Opus 5.5", r["cost_usd_at_opus_5_5"])):
                if c is None:
                    v.append(("cost<=40%% vs %s @%s" % (nm, lab), k, "UNKNOWN", "UNPRICED"))
                else:
                    v.append(("cost<=40%% vs %s @%s" % (nm, lab), k,
                              "PASS" if c <= 0.4 * base else "FAIL",
                              "$%s vs limit $%s (old $%s)" % (_f(c, 3), _f(0.4 * base, 3), _f(base, 3))))
        v.append(("first call <=20k", k, "PASS" if r["call1_processed"] <= 20000 else "FAIL",
                  "%d" % r["call1_processed"]))
        v.append(("cache-hit >=85%", k, "PASS" if (r["cache_hit_ratio"] or 0) >= 0.85 else "FAIL",
                  "%.1f%%" % (100 * (r["cache_hit_ratio"] or 0))))
    if ok:
        cr = sum(r["cache_read"] for r in ok.values())
        pr = sum(r["processed"] for r in ok.values())
        v.append(("cache-hit >=85% pooled", "pooled", "PASS" if pr and cr / pr >= 0.85 else "FAIL",
                  "%.1f%%" % (100 * cr / pr if pr else 0)))
    return v


def render_md(res, verdicts, pricing_path=None):
    pricing_path = resolve_pricing() if pricing_path is None else pricing_path
    L = ["# W4 benchmark: slim-t2 units vs W1 baseline", "",
         "Measured from transcripts (read-only); pricing %s. " % _rel(pricing_path) +
         "Processed = input + cache read + cache write (output excluded). Calls = deduplicated assistant usage rows.", "",
         "| unit | calls | call-1 | processed | input | cache read | cw 5m | cw 1h | output | hit | $ transcript model | $ @Opus 5.5 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        if "error" in r:
            L.append("| %s | ERROR: %s |" % (k, r["error"]))
            continue
        L.append("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %.1f%% | %s | %s |" % (
            k, r["calls"], r["call1_processed"], r["processed"], r["input"], r["cache_read"],
            r["cache_write_5m"], r["cache_write_1h"], r["output"], 100 * (r["cache_hit_ratio"] or 0),
            "UNPRICED" if r["cost_usd"] is None else "$" + _f(r["cost_usd"], 3),
            "$" + _f(r["cost_usd_at_opus_5_5"], 3) if r["cost_usd_at_opus_5_5"] is not None else "UNPRICED"))
    L += ["", "Old-arm comparators (W1): gsd-executor $57.1/21 = $%s per session; worker epoch $28.0/8 = $%s. "
          "Limit = 40%% of each. The old figures cover different work, so the ratio is indicative, not like-for-like."
          % (_f(OLD["executor_per_session"], 3), _f(OLD["worker_per_epoch"], 3)), "",
          "## Done-gate", "", "| criterion | unit | verdict | number |", "|---|---|---|---|"]
    for c, k, s, n in verdicts:
        L.append("| %s | %s | %s | %s |" % (c, k, s, n))
    d = res.get("W3d", {})
    L += ["", "## W3d cap-trip probe", ""]
    if "error" in d:
        L.append("NOT OBSERVED: %s" % d["error"])
    else:
        L.append("Total processed at last call: %d of a 150,000 stop. Budget-hook texts seen in the transcript:" % d["processed"])
        for h in d["budget_hook_texts"]:
            L.append("- %s (after %d calls): `%s`" % (h["timestamp"], h["calls_before"], h["text"]))
        if not d["budget_hook_texts"]:
            L.append("- none: NOT OBSERVED")
        L.append("")
        L.append("The hook text is a projected-reserve trip (processed + next call + closeout reserve would cross the stop), "
                 "not a trip at processed ~150k. Whether that counts as 'at or near its cap' is the Owner's call; "
                 "the receipt's claimed 61,515 is compared with the transcript's hook text above.")
    L += ["", "## Open", "", "- Second consumer (an unrelated PP task): NOT RUN in this tranche. OPEN, not pass."]
    return "\n".join(L) + "\n"


def main():
    try:
        pricing_path = resolve_pricing()
    except FileNotFoundError as e:
        print("FAIL: no current pricing file: %s" % e, file=sys.stderr)
        return 2
    prices = load_prices(pricing_path)
    res = {k: analyze(find_transcript(s), prices) for k, s in SESSIONS.items()}
    verdicts = judge(res)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "W4-benchmark.json").write_text(json.dumps(
        {"sessions": SESSIONS, "results": res, "verdicts": verdicts, "old_arm": OLD}, indent=1), encoding="utf-8")
    (OUT / "W4-benchmark.md").write_text(render_md(res, verdicts, pricing_path), encoding="utf-8")
    print("wrote W4-benchmark.json/.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
