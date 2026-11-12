#!/usr/bin/env python3
"""Analyse the DRX yield experiment exactly as pre-registered (vault/research/drx_eval/yield/PREREGISTRATION.md).

    python tools/drx_yield_analysis.py vault/research/drx_eval/yield [--json out.json]
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
from pathlib import Path

ARMS = ("A_t120_c25k", "B_t240_c25k", "C_t120_c12k")
_PROG = re.compile(r"arm=(\S+) mission=(\d) rep=(\d) rc=(-?\d+) secs=(\d+)")


def load(root: Path) -> dict[tuple[str, int, int], dict]:
    runs: dict[tuple[str, int, int], dict] = {}
    for line in (root / "progress.txt").read_text(encoding="utf-8-sig").splitlines():
        # Runner v2 logs lock-held attempts as "... INFRA lock_held arm=.. rc=3 ..." -- a run that never ran
        # is infrastructure loss (rule 6), never an INSUFFICIENT run, so it must not enter the table.
        if " INFRA " in f" {line} ":
            continue
        m = _PROG.search(line)
        if m:
            arm, mi, rep, rc, secs = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
            runs[(arm, mi, rep)] = {"rc": rc, "secs": secs}
    for (arm, mi, rep), r in runs.items():
        d = root / arm / f"m{mi}_rep{rep}"
        raws = list(d.glob("*.raw.jsonl"))
        rows = [json.loads(x) for x in raws[0].read_text(encoding="utf-8").splitlines() if x.strip()] if raws else []
        calls = [x for x in rows if x.get("type") == "llm_call"]
        ext = [c for c in calls if c["kind"] == "extract"]
        led = list(d.glob("*.ledger.json"))
        summ = json.loads(led[0].read_text(encoding="utf-8"))["summary"] if led else {}
        r.update({
            "lost": not raws,  # no artifacts at all = infrastructure loss, reported separately
            "learnings": sum(1 for x in rows if x.get("type") == "learning"),
            "insufficient": r["rc"] == 3,
            "persisted": summ.get("claims_persisted") or 0,
            "persisted_with_span": summ.get("persisted_with_verified_span") or 0,
            "extract_calls": len(ext),
            "extract_timeouts": sum(1 for c in ext if c["timeout"]),
            "extract_secs": [c["secs"] for c in ext if c["ok"]],
        })
    return runs


def analyse(runs: dict) -> dict:
    out: dict = {"per_arm": {}, "vs_A": {}}
    for arm in ARMS:
        rs = [r for (a, _, _), r in runs.items() if a == arm and not r["lost"]]
        secs = [s for r in rs for s in r["extract_secs"]]
        kept = sum(r["persisted"] for r in rs)
        out["per_arm"][arm] = {
            "runs": len(rs), "lost": sum(1 for (a, _, _), r in runs.items() if a == arm and r["lost"]),
            "yield_mean": round(st.mean(r["learnings"] for r in rs), 2) if rs else None,
            "insufficient": sum(r["insufficient"] for r in rs),
            "verified_quote_rate": round(sum(r["persisted_with_span"] for r in rs) / kept, 3) if kept else None,
            "extract_timeouts": sum(r["extract_timeouts"] for r in rs),
            "extract_calls": sum(r["extract_calls"] for r in rs),
            "extract_secs_median": st.median(secs) if secs else None,
            "extract_secs_max": max(secs) if secs else None,
            "wall_secs_mean": round(st.mean(r["secs"] for r in rs)) if rs else None,
        }
    a = out["per_arm"]["A_t120_c25k"]
    for arm in ARMS[1:]:
        pairs = [(runs[(arm, m, k)], runs[("A_t120_c25k", m, k)]) for m in (1, 2, 3) for k in (1, 2, 3)
                 if (arm, m, k) in runs and ("A_t120_c25k", m, k) in runs
                 and not runs[(arm, m, k)]["lost"] and not runs[("A_t120_c25k", m, k)]["lost"]]
        d = [x["learnings"] - y["learnings"] for x, y in pairs]
        n = len(d)
        mean = st.mean(d) if d else 0.0
        se = (st.stdev(d) / n ** 0.5) if n > 1 else float("inf")
        beats = n > 1 and mean > 2 * se
        me = out["per_arm"][arm]
        rate_ok = (me["verified_quote_rate"] is not None and a["verified_quote_rate"] is not None
                   and me["verified_quote_rate"] >= a["verified_quote_rate"] - 0.10)
        out["vs_A"][arm] = {"pairs": n, "diffs": d, "mean_diff": round(mean, 2),
                            "two_se": round(2 * se, 2) if se != float("inf") else None,
                            "beats_A": beats, "rate_guard_ok": rate_ok,
                            "insufficient_guard_ok": me["insufficient"] <= a["insufficient"],
                            "adoptable": beats and rate_ok and me["insufficient"] <= a["insufficient"]}
    a_runs = [r for (x, _, _), r in runs.items() if x == "A_t120_c25k" and not r["lost"]]
    with_to = [r["learnings"] for r in a_runs if r["extract_timeouts"]]
    without = [r["learnings"] for r in a_runs if not r["extract_timeouts"]]
    out["H1_mechanism"] = {
        "A_runs_with_extract_timeout": len(with_to), "A_yield_mean_with_timeout": round(st.mean(with_to), 2) if with_to else None,
        "A_runs_without": len(without), "A_yield_mean_without": round(st.mean(without), 2) if without else None,
    }
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[0])
    res = analyse(load(root))
    print(json.dumps(res, indent=1))
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
