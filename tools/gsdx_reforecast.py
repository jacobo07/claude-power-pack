"""Deterministic programme forecast (zero model calls). Pending chain units = route target x 0.35 (K7)
plus the unfunded Master Plan lines. Retired/superseded work (recon P2/P3/CP50/P8/P9, W3 residual) counts 0 here."""
import argparse, json, os, subprocess, sys

FACTOR = 0.35
M = 1_000_000
# Master Plan sec 3 lines still funded here: (expected, lower, safety) in M tokens
PLAN_LINES = {
    "GEX44 port": (1.0, 0.5, 2.0),
    "Part A residual": (2.5, 1.2, 4.5),
    "rows not mapped to a phase": (2.0, 0.5, 3.0),
    "reserves+control (PLAN-2 basis)": (6.5, 2.5, 10.5),
}
SPEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mission_spend.py")

def load(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)

def _pct(s, q):
    k = (len(s) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

def distribution(samples, spent=0):
    """Remaining-spend percentiles (caller adds used). n==0 UNKNOWN; n<5 WIDE (stated widening); else NORMAL."""
    s = sorted(float(x) for x in samples)
    keys = ("lower", "p50", "p80", "p95", "ceiling")
    n = len(s)
    if n == 0:
        d = {k: None for k in keys}
        d["confidence"], d["n"] = "UNKNOWN", 0
        return d
    if n == 1:
        p50, p80, p95 = s[0], s[0] * 1.25, s[0] * 1.5
    else:
        p50, p80, p95 = _pct(s, 0.5), _pct(s, 0.8), _pct(s, 0.95)
    if n < 5:
        return {"lower": s[0] * 0.5, "p50": p50, "p80": p80, "p95": p95, "ceiling": 2 * p95,
                "confidence": "WIDE", "n": n}
    return {"lower": s[0], "p50": p50, "p80": p80, "p95": p95, "ceiling": s[-1],
            "confidence": "NORMAL", "n": n}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--chain", required=True)
    a.add_argument("--goal-json")
    a.add_argument("--goal", default="gsdx-factory-2")
    a.add_argument("--previous")
    a.add_argument("--out")
    a.add_argument("--plan-scale", type=float, default=1.0)
    a = a.parse_args()
    chain = load(a.chain)
    if a.goal_json:
        used = load(a.goal_json)["used"]
    else:
        r = subprocess.run([sys.executable, SPEND, "goal-status", "--goal", a.goal], capture_output=True, text=True, timeout=60)
        used = json.loads(r.stdout.strip().splitlines()[-1])["used"]
    pending, tgt, unit_samples = [], 0, []
    for u in chain["units"]:
        if u.get("deferred"):
            continue
        ok = False
        if os.path.exists(u["receipt"]):
            ok = load(u["receipt"]).get("status") in (u.get("accept") or ["DONE"])
        if ok:
            continue
        pending.append(u["id"])
        t = load(u["route"])["envelope"]["target"]
        tgt += t
        unit_samples.append(t * FACTOR)
    s = a.plan_scale
    rem = {
        "expected": tgt * FACTOR + sum(v[0] for v in PLAN_LINES.values()) * M * s,
        "lower": tgt * FACTOR * 0.5 + sum(v[1] for v in PLAN_LINES.values()) * M * s,
        "safety": tgt + sum(v[2] for v in PLAN_LINES.values()) * M * s,
    }
    tot = {k: used + v for k, v in rem.items()}
    samples = unit_samples + [v[0] * M * s for v in PLAN_LINES.values()]
    dist = distribution(samples)
    tdist = {k: (used + v if isinstance(v, (int, float)) and k not in ("n",) else v) for k, v in dist.items()}
    prev = None
    if a.previous and os.path.exists(a.previous):
        prev = load(a.previous).get("total", {}).get("expected")
    delta = round(abs(tot["expected"] - prev) / prev * 100, 6) if prev else None
    env = chain.get("envelope", 40_000_000)
    f = {
        "used": used,
        "chain": {"pending": pending, "route_targets": tgt, "factor": FACTOR},
        "plan_lines_M": PLAN_LINES,
        "not_counted": "recon P2/P3/CP50/P8/P9 (gen3 track), W3 residual (dgl/ce-lifecycle-v3), W5/W7: 0 here",
        "remaining": rem, "total": tot, "previous_expected": prev, "delta_pct": delta,
        "iterate": bool(delta is not None and delta > 25),
        "owner_needed": tot["expected"] > env,
        "safety_over_envelope": tot["safety"] > env,
        "envelope": env,
        "distribution": dist, "total_distribution": tdist,
    }
    print(json.dumps(f, indent=1))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(f, fh, indent=1)

if __name__ == "__main__":
    main()
