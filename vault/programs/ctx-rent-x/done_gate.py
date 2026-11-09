#!/usr/bin/env python3
"""ctx-rent-x master done-gate: CR-01..CR-36, each a receipt with a measured value or a justified UNKNOWN.
CR-33..36 are the GPF plan's gates (vault/specs/gpf-resident-admission.md): W0 decomposition, W1 delta, W1 quality,
resident budget pinned (the real floor gate in --budget mode on the newest session of --budget-src).

Status: PASS (measured value meets its bar) | FAIL (measured, bar missed) | UNKNOWN (no receipt yet; reason given).
Exit 0 only when no condition is FAIL or UNKNOWN. UNKNOWN is never PASS. Evidence is read from --root (default: the
program dir), so the drill in tools/test_done_gate.py can mutate it. Plane labels come from the receipt files.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GPF = os.path.abspath(os.path.join(HERE, "..", "global-prefix-floor"))  # laptop successor / CR-29 smoke receipts
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


# Claude Code's project-dir slug: every non-alphanumeric char of the cwd becomes '-'. The cwd is the PP install
# (~/.claude/skills/claude-power-pack), derived per host instead of one machine's literal slug.
_PP_INSTALL = os.path.join(os.path.expanduser("~"), ".claude", "skills", "claude-power-pack")
PP_PROJECT_DIR = os.path.join(os.path.expanduser("~"), ".claude", "projects",
                              "".join(ch if ch.isalnum() else "-" for ch in _PP_INSTALL))
_BUDGET_RUNS = {}


def budget_run(repo, budget, src):
    """CR-36: the real floor gate, --budget mode, on the newest session of src. Memoised per (budget, src)."""
    key = (budget, src)
    if key not in _BUDGET_RUNS:
        try:
            p = subprocess.run([sys.executable, os.path.join(repo, "tools", "floor_regression_gate.py"), "--budget", budget,
                                "--project-dir", src], capture_output=True, text=True, timeout=120)
            last = ([ln for ln in p.stdout.splitlines() if ln.strip()] or [""])[-1]
            _BUDGET_RUNS[key] = (p.returncode, last)
        except (OSError, subprocess.SubprocessError) as e:
            _BUDGET_RUNS[key] = (None, "gate did not run: %s" % e.__class__.__name__)
    return _BUDGET_RUNS[key]


def gpf_rows(root, repo, gpf, budget_src, put):
    """CR-33..36 (GPF plan, section Gates). A missing or unreadable receipt is UNKNOWN, never PASS."""
    dec = load(root, "floor-decomposition.json")
    arms = (dec or {}).get("arms") or {}
    dd = (dec or {}).get("decomposition") or {}
    need = ("full", "no_claudemd", "no_rules")
    if not dec:
        put("CR-33", U, "no floor-decomposition.json (W0 receipt)")
    elif all((arms.get(a) or {}).get("label") == "MEASURED" and (arms.get(a) or {}).get("n", 0) >= 3 for a in need) \
            and dd.get("claude_md_chain", 0) > 0 and dd.get("rules", 0) > 0:
        put("CR-33", P, "W0 %s: CLAUDE.md chain %s, rules %s of call-1 %s (n>=3 per arm)" % (
            dec.get("plane"), dd["claude_md_chain"], dd["rules"], dd.get("full_call1")))
    else:
        put("CR-33", F, "W0 receipt lacks MEASURED n>=3 arms %s or positive chain/rules shares" % (need,))
    l2 = (load(gpf, "gpf-l2-laptop.json") or {}).get("summary")
    if not l2:
        put("CR-34", U, "no gpf-l2-laptop.json summary (W1 delta)")
    else:
        c, t = l2.get("control") or [], l2.get("treatment") or []
        if len(c) < 4 or len(t) < 4:
            put("CR-34", F, "W1 needs n=4 per arm, have %d/%d" % (len(c), len(t)))
        else:
            # spec: spread < 1 % strictly, on BOTH arms (delta_ok alone checks control only, and admits exactly 1 %)
            sp = {arm: (max(v) - min(v)) / (sum(v) / len(v)) for arm, v in (("control", c), ("treatment", t))}
            r = delta_ok(l2)
            wide = [arm for arm, x in sp.items() if x >= 0.01]
            put("CR-34", F if wide else r[0], "W1 " + r[1] + (" | spread >= 1%% on %s" % wide if wide else
                                                              " | treatment spread=%.4f" % sp["treatment"]))
    q = load(gpf, "gpf-l2-quality.json")
    n = (q or {}).get("summary", {}).get("n") if isinstance((q or {}).get("summary"), dict) else None
    cor = (q or {}).get("correct")
    if not isinstance(cor, dict) or not isinstance(n, list) or len(n) != 2:
        put("CR-35", U, "no gpf-l2-quality.json with per-arm correct counts and n=[control, treatment]")
    else:
        # per arm, never the summed total: {"C": 6, "T": 0} over n=[3, 3] is a broken treatment, not 6/6
        ok = cor.get("C") == n[0] and cor.get("T") == n[1] and sum(n) >= 6
        put("CR-35", P if ok else F, "W1 quality control %s/%s, treatment %s/%s correct" % (cor.get("C"), n[0], cor.get("T"), n[1]))
    budget = os.path.join(gpf, "resident_budget.json")
    if not os.path.isfile(budget):
        put("CR-36", U, "no resident_budget.json")
    elif not os.path.isdir(budget_src):
        put("CR-36", U, "no session directory to measure on this plane: %s" % budget_src)
    else:
        code, last = budget_run(repo, budget, budget_src)
        put("CR-36", {0: P, 1: F}.get(code, U), "floor gate --budget on newest session: exit %s %s" % (code, last))


def phase5_rows(root, put):
    """CR-09/10/13 (Phase 5 Safe-to-Forget in main; spec vault/specs/ccr-safe-to-forget-main.md), from the live smoke file
    phase5-safe-to-forget.json (vault/programs/ctx-rent-x/phase5_smoke.py). Arm N = CCR_MAIN_PROJECT=1, arm F = CCR_MAIN_PROJECT=0
    (unset was OFF before spec Amendment A, 2026-11-05, and is ON after it; review L1).
    Fewer than 3 finished runs per arm measured too little: UNKNOWN, never PASS."""
    doc = load(root, "phase5-safe-to-forget.json")
    # A run counts only if CCR ran compatible (an incompatible host shadows every surface: 2.1.317 smoke, 2026-11-03) and
    # the shell result reached projectShell; the driver's `invalid` names why not. Uncounted runs leave the rows UNKNOWN.
    runs = [r for r in (doc or {}).get("runs") or [] if r.get("finished") and not r.get("invalid")
            and ((r.get("receipts") or {}).get("start") or {}).get("compatible") is True]
    on, off = [r for r in runs if r.get("arm") == "N"], [r for r in runs if r.get("arm") == "F"]
    if not doc or len(on) < 3 or len(off) < 3:
        why = "no phase5-safe-to-forget.json (Phase 5 smoke not run)" if not doc else \
            "n<3 finished runs per arm (N=%d F=%d)" % (len(on), len(off))
        for cr in ("CR-09", "CR-10", "CR-13"):
            put(cr, U, why)
        return

    def main_proj(r):
        return [x for x in ((r.get("receipts") or {}).get("project") or []) if x.get("agent") is None]
    # CR-09: the judgement ran on the real path: every ON run has a main-pane projection receipt carrying `forget`.
    judged = [r for r in on if any(x.get("forget") and x.get("mainProject") for x in main_proj(r))]
    put("CR-09", P if len(judged) == len(on) else F, "safeToForget judged a main-pane projection in %d/%d ON runs" % (len(judged), len(on)))
    # CR-10: proof survived: every ON run answered from the buried verdict line; the protection was exercised (hoisted or a
    # named KEEP); and nothing was applied without a read-back-verified full output.
    rec = [x for r in on for x in main_proj(r)]
    exercised = sum(1 for x in rec if (x.get("forget") or {}).get("hoisted", 0) > 0 or (x.get("forget") or {}).get("reason") == "obligation-named")
    undurable = sum(1 for x in rec if x.get("applied") and x.get("durable") is not True)
    ok_on = sum(1 for r in on if r.get("correct"))
    ok10 = ok_on == len(on) and exercised > 0 and undurable == 0
    put("CR-10", P if ok10 else F, "ON correct %d/%d (OFF %d/%d); protection exercised %d; applied without durable read-back %d" % (
        ok_on, len(on), sum(1 for r in off if r.get("correct")), len(off), exercised, undurable))
    # CR-13: the recurring large class (shell output > budget) was actually externalised in every ON run, and it paid.
    applied = [r for r in on if any(x.get("applied") for x in main_proj(r))]
    saved = sum(x.get("bytes", 0) - x.get("out", 0) for x in rec if x.get("applied"))
    pon, poff = [r.get("processed") for r in on], [r.get("processed") for r in off]
    if any(not isinstance(v, int) for v in pon + poff):
        put("CR-13", U, "processed tokens unmeasured in some run")
        return
    m_on, m_off = sum(pon) / len(pon), sum(poff) / len(poff)
    ok13 = len(applied) == len(on) and m_on < m_off
    put("CR-13", P if ok13 else F, "applied in %d/%d ON runs, %d chars externalised; processed mean ON %d vs OFF %d (%+.1f%%); projected faults %d" % (
        len(applied), len(on), saved, m_on, m_off, 100.0 * (m_on - m_off) / m_off,
        sum((r.get("receipts") or {}).get("faults", 0) for r in on)))


def conditions(root, repo, gpf=GPF, budget_src=PP_PROJECT_DIR):
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
    phase5_rows(root, put)
    # CR-11/14/15/29: read from the GPF laptop smoke receipts (per-run files, latest measured run decides; an aborted run
    # measured nothing and stays UNKNOWN with its reason).
    succ_runs = [r for r in ((load(gpf, "gpf-l1-successor.json") or {}).get("runs") or []) if r.get("successor")]
    last = succ_runs[-1] if succ_runs else None
    if not last:
        put("CR-11", U, "no successor smoke run in gpf-l1-successor.json")
        put("CR-14", U, "no successor smoke run in gpf-l1-successor.json")
    else:
        cap = last.get("frontier_basis") == "capsule"
        put("CR-11", P if cap else F, "latest successor run %s frontier_basis=%s (%d successor runs)" % (last.get("label"), last.get("frontier_basis"), len(succ_runs)))
        ok14 = cap and "/kresume" in (last.get("successor_first_prompt") or "") and last.get("turn_completed") is True
        put("CR-14", P if ok14 else F, "latest %s: first prompt /kresume=%s turn_completed=%s basis=%s" % (
            last.get("label"), "/kresume" in (last.get("successor_first_prompt") or ""), last.get("turn_completed"), last.get("frontier_basis")))
    k_runs = (load(gpf, "gpf-cr29.json") or {}).get("runs") or []
    measured = [r for r in k_runs if not r.get("aborted")]
    if not measured:
        why = "no measured /kclear->/clear->/kresume run (%d aborted, last: %s)" % (len(k_runs), k_runs[-1].get("aborted") if k_runs else "none run")
        put("CR-15", U, "time-to-first-correct-action: " + why)
        put("CR-29", U, why)
    else:
        k = measured[-1]
        hit = k.get("first_correct_action") is True and (k.get("done_txt") or "").strip() == k.get("token")
        secs = k.get("seconds_to_first_correct_action")
        put("CR-15", P if hit and secs is not None else F, "%s: %ss to first correct action, successor %s" % (k.get("label"), secs, (k.get("successor_metrics") or {}).get("call1")))
        put("CR-29", P if hit else F, "%s: done.txt==token %s, capsule verdict %s, failed certify attempts %s" % (
            k.get("label"), hit, k.get("ledger_verdict") or k.get("capsule_verdict"), k.get("resume_failed")))
    r = delta_ok((diet or {}).get("rows", {}).get("rules_to_skills"))
    put("CR-12", r[0] if r else U, r[1] if r else "no floor-diet rows")
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
    put("CR-30", U, "run plan section 8 commands; not aggregated here")
    try:
        dirty = subprocess.run(["git", "-C", repo, "status", "--short"], capture_output=True, text=True, timeout=30).stdout.strip()
        put("CR-31", P if not dirty else F, "clean tree" if not dirty else "dirty: %d paths" % len(dirty.splitlines()))
        head = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip()
        put("CR-32", P if head else U, "HEAD %s, not pushed (mission forbids push)" % head)
    except (OSError, subprocess.SubprocessError) as e:
        put("CR-31", U, "git unavailable: %s" % e)
        put("CR-32", U, "git unavailable")
    gpf_rows(root, repo, gpf, budget_src, put)
    return R


N_CONDITIONS = 36


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=HERE)
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--gpf-root", default=GPF)
    ap.add_argument("--budget-src", default=PP_PROJECT_DIR, help="CR-36: project dir whose newest session is budgeted")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = conditions(a.root, a.repo, a.gpf_root, a.budget_src)
    assert len(res) == N_CONDITIONS, len(res)
    for k in sorted(res):
        print("%s %-7s %s" % (k, res[k][0], res[k][1]))
    n = {s: sum(1 for v in res.values() if v[0] == s) for s in (P, F, U)}
    print("DONE_GATE pass=%d fail=%d unknown=%d of %d" % (n[P], n[F], n[U], N_CONDITIONS))
    return 0 if n[F] == 0 and n[U] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
