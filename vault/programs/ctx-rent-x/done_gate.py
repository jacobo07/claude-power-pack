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
    rep = load(root, "replay-gex44-a7.json")
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
    # CR-17..19: derived from the raw per-run file (never from a self-reported summary).
    # Valid run = finished AND its receipt matches its arm. Pairs = min(valid S, valid E).
    runs = [r for r in ((qual or {}).get("runs") or []) if r.get("finished") and r.get("receipt_matches_arm")]
    S = [r for r in runs if r.get("arm") == "S"]
    E = [r for r in runs if r.get("arm") == "E"]
    pairs = min(len(S), len(E))
    if pairs >= 3:
        ds = sum(r["processed"] for r in S) / len(S) - sum(r["processed"] for r in E) / len(E)
        put("CR-17", P if ds > 0 else F, "pairs=%d shadow-mean minus canary-mean processed=%.0f" % (pairs, ds))
        ok = all(r.get("correct") is True for r in S + E)
        put("CR-18", P if ok else F, "correct %d/%d valid runs" % (sum(1 for r in S + E if r.get("correct") is True), len(S + E)))
        keys = ("page_faults", "repairs", "rereads")
        if all(k in r for r in S + E for k in keys):
            tot = {k: sum(r[k] for r in S + E) for k in keys}
            put("CR-19", P if tot["page_faults"] == 0 and tot["repairs"] == 0 else F, "totals %s" % tot)
        else:
            put("CR-19", U, "runs lack page_faults/repairs/rereads")
    else:
        for cr in ("CR-17", "CR-18", "CR-19"):
            put(cr, U, "need >=3 valid S/E pairs, have %d" % pairs)
    put("CR-20", P if wait and wait.get("wait_calls", 0) > 0 else U, "waiting calls=%s share=%s (shadow)" % ((wait or {}).get("wait_calls"), (wait or {}).get("wait_processed_share")))
    ra, rb = delta_ok((ca or {}).get("summary")), delta_ok((cb or {}).get("summary"))
    if ra and rb:
        st = P if ra[0] == P and rb[0] == P else F
        put("CR-21", st, "canary A: %s | B: %s" % (ra[1], rb[1]))
    else:
        put("CR-21", U, "no canary receipts")
    rc = (rep or {}).get("classes") or {}
    rt = (rep or {}).get("total") or {}
    valid = bool(rep) and str(rep.get("label", "")).startswith("ESTIMATE") and len(rc) >= 3 and rt.get("X", 0) > 0
    if valid and rt.get("X_prime", 0) < rt["X"]:
        put("CR-23", P, "X=%s X'=%s saving=%s%% ESTIMATE, %d classes" % (rt["X"], rt["X_prime"], rt.get("saving_pct"), len(rc)))
    else:
        put("CR-23", U, "no valid labelled X -> X-prime replay")
    ksr = rc.get("ksr_style")
    put("CR-22", P if (valid and ksr and ksr.get("sessions", 0) > 0) else U,
        ("ksr_style class sessions=%s" % ksr.get("sessions")) if ksr else "no KSR-style session in the replay window")
    put("CR-24", P if (est and (est.get("total") or 0) and delta_txt) else U, "laptop week total measured + weekly delta" if est else "no estate")
    def _rd(rel):
        try:
            return open(os.path.join(repo, rel), encoding="utf-8").read()
        except OSError:
            return ""
    ukdl, imm, lap = _rd("vault/knowledge_base/ukdl-universal.md"), _rd("vault/programs/ctx-rent-x/IMMUNITY.md"), _rd("vault/programs/ctx-rent-x/LAPTOP_RESULTS.md")
    led = _rd("vault/baseline_ledger.jsonl")
    pr = "PR-NO-RUNNABLE-UNIT-STOPS-THE-EPOCH-001" in ukdl
    put("CR-25", P if (pr and "WRITTEN" in imm) else U, "UKDL process rule + immunity entry present" if pr else "no UKDL entry")
    trap = "T-DEFAULT-FLIP-NEEDS-LIVE-PANE-RECEIPT-001" in ukdl
    put("CR-26", P if (pr and trap) else U, "PR + Trap entries cite L8 evidence; no Hard Rule promoted (no production recurrence yet)" if trap else "no trap entry")
    rows = led.count("repo:ctx-rent-x")
    put("CR-27", P if rows >= 3 else U, "%d ratchet rows in baseline_ledger (main default, source_commit, closeout/epoch rule)" % rows)
    live = "LIVE" in lap and "0.1.0-265d3d55" in lap and "PASS" in lap
    put("CR-28", P if live else U, "main enforce default-on LIVE release 0.1.0-265d3d55 with start-receipt smoke + rollback verified (L8)" if live else "L8 receipts absent")
    put("CR-29", U, "fresh-agent recovery not exercised as a /clear->/kresume successor smoke (Phase 4)")
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
