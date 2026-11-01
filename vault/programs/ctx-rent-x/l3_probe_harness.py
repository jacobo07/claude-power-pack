"""ctx-rent-x L3 harness: per-row apply -> probe -> revert on the LIVE home, counterbalanced (C T C T, then T C T C).
Contract P2-floor-diet-v1 (frozen in 908989eb). Revert runs in finally; a tree hash proves the live tree is restored."""
import hashlib, json, os, subprocess, sys, time
from pathlib import Path

WT = Path(os.environ["TEMP"]) / "claude" / "ctxrx-w0"
sys.path.insert(0, str(WT / "tools"))
import floor_diet as fd  # noqa: E402

HOME = Path(os.environ["USERPROFILE"])
CL = HOME / ".claude"
PROBE_CWD = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CLAUDE = os.environ.get("CLAUDE_EXE", "claude")


def tree_hash() -> str:
    h = hashlib.sha256()
    for d in ("agents", "agents-parked", "rules") + tuple(f"skills/{r}" for r in fd.RULES_TO_SKILLS):
        base = CL / d
        if not base.exists():
            h.update(f"{d}:absent".encode()); continue
        for f in sorted(base.rglob("*")):
            if f.is_file() and ".git" not in f.parts:
                h.update(str(f.relative_to(CL)).encode()); h.update(f.read_bytes())
    return h.hexdigest()


def probe() -> dict:
    t = time.time()
    r = subprocess.run([CLAUDE, "-p", "reply OK", "--model", "haiku", "--output-format", "json"],
                       cwd=PROBE_CWD, capture_output=True, text=True, timeout=180, encoding="utf-8", errors="replace")
    try:
        j = json.loads(r.stdout)
    except Exception:
        return {"ok": False, "rc": r.returncode, "err": (r.stderr or r.stdout)[-300:]}
    u = j.get("usage") or {}
    call1 = int(u.get("input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0)) + int(u.get("cache_read_input_tokens", 0))
    return {"ok": True, "call1": call1, "turns": j.get("num_turns"), "answer": (j.get("result") or "")[:40],
            "session": j.get("session_id"), "secs": round(time.time() - t, 1)}


def run_arm(row: str, treat: bool, full_plan: dict, tag: str) -> dict:
    if not treat:
        return {"row": row, "arm": "C", **probe()}
    p = {"agents_park": [], "rules_to_skills": [], "memory_trim": []}
    p[row] = full_plan[row]
    bdir = None
    try:
        bdir = fd.apply(HOME, p, f"{tag}")
        return {"row": row, "arm": "T", "backup": str(bdir), **probe()}
    finally:
        if bdir is not None:
            fd.revert(HOME, bdir)


def main() -> int:
    h0 = tree_hash()
    plan = fd.plan(HOME, set(), set())
    res = {"contract": "P2-floor-diet-v1", "tree_hash_before": h0, "rows": {}, "probes": []}
    seqs = {"A": "CTCT", "B": "TCTC"}
    for row in ("agents_park", "rules_to_skills"):
        if not plan[row]:
            res["rows"][row] = "EMPTY"; continue
        for s, seq in seqs.items():
            for i, a in enumerate(seq):
                r = run_arm(row, a == "T", plan, f"{int(time.time())}-{row}-{s}{i}")
                r["seq"] = f"{s}{i}"
                res["probes"].append(r)
                h = tree_hash()
                if h != h0:
                    res["ABORT"] = f"tree hash changed after {row} {s}{i}: {h}"
                    OUT.write_text(json.dumps(res, indent=1)); print(res["ABORT"]); return 2
                print(row, s, i, a, r.get("call1"), r.get("ok"), flush=True)
    res["tree_hash_after"] = tree_hash()
    for row in ("agents_park", "rules_to_skills"):
        c = [p["call1"] for p in res["probes"] if p["row"] == row and p["arm"] == "C" and p.get("ok")]
        t = [p["call1"] for p in res["probes"] if p["row"] == row and p["arm"] == "T" and p.get("ok")]
        if c and t:
            spread = (max(c) - min(c)) / max(c)
            res["rows"][row] = {"control": c, "treatment": t, "control_spread": round(spread, 4),
                                "control_within_1pct": spread <= 0.01,
                                "delta_mean": round(sum(c) / len(c) - sum(t) / len(t)), "n": [len(c), len(t)]}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["rows"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
