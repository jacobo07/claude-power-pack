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
SPEND = r"C:\Users\User\.claude\skills\claude-power-pack\tools\mission_spend.py"

def load(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)

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
    pending, tgt = [], 0
    for u in chain["units"]:
        if u.get("deferred"):
            continue
        ok = False
        if os.path.exists(u["receipt"]):
            ok = load(u["receipt"]).get("status") in (u.get("accept") or ["DONE"])
        if ok:
            continue
        pending.append(u["id"])
        tgt += load(u["route"])["envelope"]["target"]
    s = a.plan_scale
    rem = {
        "expected": tgt * FACTOR + sum(v[0] for v in PLAN_LINES.values()) * M * s,
        "lower": tgt * FACTOR * 0.5 + sum(v[1] for v in PLAN_LINES.values()) * M * s,
        "safety": tgt + sum(v[2] for v in PLAN_LINES.values()) * M * s,
    }
    tot = {k: used + v for k, v in rem.items()}
    # U4: P50 = expected, P95 = safety, P80 interpolated at a CHOSEN 0.6 weight (not measured)
    tot["P50"], tot["P95"] = tot["expected"], tot["safety"]
    tot["P80"] = tot["expected"] + 0.6 * (tot["safety"] - tot["expected"])
    tot["P80_basis"] = "CHOSEN: expected + 0.6*(safety-expected); not measured"
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
    }
    print(json.dumps(f, indent=1))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(f, fh, indent=1)

main()
