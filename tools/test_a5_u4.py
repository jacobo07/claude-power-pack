#!/usr/bin/env python3
import itertools, json, os, random, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reality_cover as rc

R = []
def check(name, fn):
    try:
        ok = bool(fn())
    except Exception as e:
        ok = False; print("EXC", name, e)
    R.append(ok); print(("PASS " if ok else "FAIL ") + name)

def O(i, host="h1", m=5, owner=True, pre=()):
    return {"obs_id": i, "host": host, "surface": i, "preconditions": list(pre), "est_minutes": m, "owner_needed": owner}

def spec(**kw):
    s = {"epoch": "E1", "observations": [O("a"), O("b", "h2")],
         "claims": [{"id": "c1", "observations": ["a", "b"]}, {"id": "c2", "observations": ["a"]}, {"id": "c3", "observations": ["b", "a"]}]}
    s.update(kw); return s

def once(dedupe=True):
    p = rc.compile_plan(spec(), dedupe)
    return p, sum(len(x["observations"]) for x in p["sessions"])

# 1 duplicate observation planned once, fanned out
p, n = once()
check("dup_planned_once", lambda: n == 2 and p["fanout"]["a"] == ["c1", "c2", "c3"])
# control: distinct observations are each planned
check("control_distinct_planned", lambda: len(rc.compile_plan({"epoch": "E", "observations": [O("x"), O("y")],
     "claims": [{"id": "c", "observations": ["x", "y"]}]})["observations_planned"]) == 2)
# same (host,surface,preconditions) under two ids merges
s2 = {"observations": [dict(O("a"), surface="s"), dict(O("a2"), surface="s")],
      "claims": [{"id": "c1", "observations": ["a"]}, {"id": "c2", "observations": ["a2"]}]}
check("same_key_merges", lambda: len(rc.compile_plan(s2)["observations_planned"]) == 1)
# 2 missing observation -> OPEN, never proven (even if everything else captured)
sm = spec(claims=[{"id": "ok", "observations": ["a"]}, {"id": "bad", "observations": ["a", "ghost"]}],
          captured={"a": "E1"})
pm = rc.compile_plan(sm)
check("missing_obs_stays_open", lambda: pm["claims"]["bad"]["status"] == "OPEN" and pm["claims"]["bad"]["missing"] == ["ghost"])
check("control_complete_claim_proven", lambda: pm["claims"]["ok"]["status"] == "PROVEN")
check("planned_not_proven_without_capture", lambda: rc.compile_plan(spec())["claims"]["c1"]["status"] == "PLANNED")
check("stale_capture_epoch_not_proven", lambda: rc.compile_plan(spec(captured={"a": "E0", "b": "E0"}))["claims"]["c1"]["status"] == "PLANNED")
# acquired in this epoch -> not re-planned
pa = rc.compile_plan(spec(acquired={"a": "E1"}))
check("acquired_this_epoch_skipped", lambda: pa["observations_planned"] == ["b"])
# 3 optimal on exhaustive fixture
def inst(seed):
    r = random.Random(seed); n = r.randint(3, 7)
    sess = []
    for k in range(r.randint(3, 7)):
        sess.append({"id": f"s{k}", "setup": float(r.randint(1, 9)), "obs": set(r.sample(range(n), r.randint(1, n)))})
    for e in range(n):
        sess.append({"id": f"u{e}", "setup": 9.0, "obs": {e}})
    return set(range(n)), sess
fix_u = {1, 2, 3, 4}
fix_s = [{"id": "A", "setup": 3.0, "obs": {1, 2}}, {"id": "B", "setup": 3.0, "obs": {3, 4}}, {"id": "C", "setup": 10.0, "obs": {1, 2, 3, 4}}]
g, left = rc.greedy_cover(fix_u, fix_s)
check("cover_optimal_fixture", lambda: not left and sum(s["setup"] for s in g) == rc.exhaustive_cover(fix_u, fix_s)[0] == 6.0)
def bound_ok():
    for sd in range(60):
        u, ss = inst(sd); g, left = rc.greedy_cover(u, ss); opt = rc.exhaustive_cover(u, ss)[0]
        m = max(len(s["obs"]) for s in ss)
        if left or sum(s["setup"] for s in g) > rc.harmonic(m) * opt + 1e-9: return False
    return True
check("greedy_within_harmonic_bound", bound_ok)
# owner packet: owner steps ordered after dependencies; automation around them
po = rc.compile_plan({"epoch": "E", "observations": [O("l2", pre=["l1"]), O("l1", pre=["tool"]), O("cap", owner=False, pre=["l2"])],
                      "claims": [{"id": "c", "observations": ["l2", "l1", "cap"]}]})
kinds = [x["kind"] for x in po["sessions"][0]["steps"]]
ow = [x["obs"] for x in po["sessions"][0]["steps"] if x["kind"] == "OWNER"]
check("owner_packet_order", lambda: kinds[0] == "AUTOMATED_PREP" and kinds[-1] == "AUTOMATED_CAPTURE" and ow == ["l1", "l2"])
# DWS end-to-end via CLI
dws = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vault", "programs", "cognitive-economy", "a5", "inputs", "dws-reality-obs.json")
def cli():
    with tempfile.TemporaryDirectory() as t:
        out = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "reality_cover.py"), dws],
                             capture_output=True, text=True, cwd=t, timeout=20)
        d = json.loads(out.stdout)
        return len(d["sessions"]) == 1 and d["owner_minutes"] < d["per_claim_baseline"]["owner_minutes"] and all(v["status"] == "PLANNED" for v in d["claims"].values())
check("dws_cli_plan", cli)
# 4 mutant: dedupe off must be detected (the dup check goes red)
pm_, nm = once(dedupe=False)
check("mutant_dedupe_off_is_red", lambda: not (nm == 2 and pm_["fanout"].get("a") == ["c1", "c2", "c3"]) and nm == 5)

print(f"A5_U4_PASS={sum(R)}/{len(R)}")
sys.exit(0 if all(R) else 1)
