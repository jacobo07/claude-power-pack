#!/usr/bin/env python3
"""ctx-rent-x master done-gate: CR-01..CR-32, each a receipt with a measured value or a justified UNKNOWN.

Status: PASS (measured value meets its bar) | FAIL (measured, bar missed) | UNKNOWN (no receipt yet; reason given).
Exit 0 only when no condition is FAIL or UNKNOWN. UNKNOWN is never PASS. Evidence is read from --root (default: the
program dir), so the drill in tools/test_done_gate.py can mutate it. Plane labels come from the receipt files.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
P, F, U = "PASS", "FAIL", "UNKNOWN"


def load(root, name):
    try:
        with open(os.path.join(root, name)) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def delta_ok(summary):
    """summary: control/treatment lists + delta_mean. PASS needs n>=2 per arm, delta>0, control spread <= 1%."""
    if not summary:
        return None
    c, t = summary.get("control") or [], summary.get("treatment") or []
    if len(c) < 2 or len(t) < 2:
        return F, "n<2 per arm %s" % (summary.get("n"),)
    d = sum(c) / len(c) - sum(t) / len(t)
    spread = (max(c) - min(c)) / (sum(c) / len(c))
    if spread > 0.01:
        return F, "control spread %.4f > 1%%" % spread
    return (P if d > 0 else F), "call-1 delta_mean=%d n=%d/%d spread=%.4f" % (d, len(c), len(t), spread)


def conditions(root, repo):
    est = load(root, "estate-laptop-w0.json")
    gex = load(root, "estate-gex44-w0.json")
    car = load(root, "carriage-A.json")
    dead = load(root, "dead-rent.json")
    wait = load(root, "waiting-gex44-w0.json")
    diet = load(root, "floor-diet-results.json")
    ca, cb = load(root, "main-canary-A.json"), load(root, "main-canary-B.json")
    qual = load(root, "main-canary-quality.json")
    delta_txt = os.path.exists(os.path.join(root, "weekly-delta.txt")) and os.path.getsize(os.path.join(root, "weekly-delta.txt")) > 0
    R = {}

    def put(cr, st, why):
        R[cr] = (st, why)

    # CR-01 / CR-02
    if est and est.get("active_release"):
        put("CR-01", P, "laptop estate active_release=%s" % est["active_release"])
    else:
        put("CR-01", U, "no laptop estate with active_release")
    cls = (est or {}).get("classes") or {}
    put("CR-02", P if est and len(cls) >= 2 else U, "classes=%s" % sorted(cls) if cls else "no per-class estate")
    # CR-03 / CR-04 / CR-06 / CR-07
    put("CR-03", P if (gex and est and delta_txt) else U, "gex44+laptop estate + weekly-delta.txt" if (gex and est and delta_txt) else "estate or weekly delta missing")
    put("CR-04", P if car and car.get("calls", 0) > 0 else U, "carriage calls=%s" % (car or {}).get("calls"))
    ok_dead = isinstance(dead, list) and len([x for x in dead if x.get("dead_rent_tokens_UPPER_BOUND") is not None]) >= 2
    put("CR-05", P if ok_dead else U, "dead-rent transcripts=%d (APPROX upper bound)" % (len(dead) if isinstance(dead, list) else 0))
    put("CR-06", P if car and car.get("mean_est_by_class_APPROX") else U, "dominant class from carriage-A by_class" if car else "no carriage")
    put("CR-07", U, "no receipt reports provider cache read and logical rent as separate fields yet")
    # CR-08 owners extended, not created
    owners = ["tools/ccr_release.py", "tools/mission_capsule.py", "tools/gsd_epoch.py", "tools/ccr_pgo.py", "tools/mission_spend.py", "mods/cpp-cognitive-runtime/hooks/policy.ts"]
    miss = [o for o in owners if not os.path.exists(os.path.join(repo, o))]
    put("CR-08", F if miss else P, "missing owners %s" % miss if miss else "all %d plan-section-1 owners present; new tools are ctx_rent/ctx_wait/floor_diet extensions" % len(owners))
    put("CR-09", U, "Safe-to-Forget consumer (Phase 5) not run")
    put("CR-10", U, "Phase 5 not run")
    put("CR-11", U, "capsule frontier smoke (Phase 4) not run")
    r = delta_ok((diet or {}).get("rows", {}).get("rules_to_skills"))
    put("CR-12", r[0] if r else U, r[1] if r else "no floor-diet rows")
    put("CR-13", U, "Phase 5 externalisation not run")
    put("CR-14", U, "Phase 4 successor smoke not run")
    put("CR-15", U, "fresh-start cost not measured")
    put("CR-16", U, "gsd_epoch breakeven advisory exists but its inputs (successor floor, bootstrap, page-ins) are unmeasured")
    # CR-17 needs a live arm with quality; call-1 alone is not a Work Unit
    # L6 schema: {"pairs":int,"delta_processed":num,"correct_all":bool,"page_faults":n,"repairs":n,"rereads":n}
    q = qual if isinstance(qual, dict) else {}
    put("CR-17", P if q.get("pairs", 0) >= 3 and q.get("delta_processed", 0) > 0 else U, "needs L6 quality file with pairs>=3 and delta_processed>0")
    put("CR-18", P if q.get("correct_all") is True else U, "needs L6 correct_all=true")
    put("CR-19", P if all(k in q for k in ("page_faults", "repairs", "rereads")) else U, "needs L6 page_faults/repairs/rereads")
    put("CR-20", P if wait and wait.get("wait_calls", 0) > 0 else U, "waiting calls=%s share=%s (shadow)" % ((wait or {}).get("wait_calls"), (wait or {}).get("wait_processed_share")))
    ra, rb = delta_ok((ca or {}).get("summary")), delta_ok((cb or {}).get("summary"))
    if ra and rb:
        st = P if ra[0] == P and rb[0] == P else F
        put("CR-21", st, "canary A: %s | B: %s" % (ra[1], rb[1]))
    else:
        put("CR-21", U, "no canary receipts")
    put("CR-22", U, "KSR-style replay (Phase 7) not run")
    put("CR-23", U, "X -> X-prime report (Phase 7) not written")
    put("CR-24", P if (est and (est.get("total") or 0) and delta_txt) else U, "laptop week total measured + weekly delta" if est else "no estate")
    for cr in ("CR-25", "CR-26", "CR-27", "CR-28", "CR-29"):
        put(cr, U, "Phase 8 institutionalisation not done")
    put("CR-30", U, "run plan section 8 commands; not aggregated here")
    try:
        dirty = subprocess.run(["git", "-C", repo, "status", "--short"], capture_output=True, text=True, timeout=30).stdout.strip()
        put("CR-31", P if not dirty else F, "clean tree" if not dirty else "dirty: %d paths" % len(dirty.splitlines()))
        head = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip()
        put("CR-32", P if head else U, "HEAD %s, not pushed (mission forbids push)" % head)
    except (OSError, subprocess.SubprocessError) as e:
        put("CR-31", U, "git unavailable: %s" % e)
        put("CR-32", U, "git unavailable")
    return R


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=HERE)
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = conditions(a.root, a.repo)
    assert len(res) == 32, len(res)
    for k in sorted(res):
        print("%s %-7s %s" % (k, res[k][0], res[k][1]))
    n = {s: sum(1 for v in res.values() if v[0] == s) for s in (P, F, U)}
    print("DONE_GATE pass=%d fail=%d unknown=%d of 32" % (n[P], n[F], n[U]))
    return 0 if n[F] == 0 and n[U] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
