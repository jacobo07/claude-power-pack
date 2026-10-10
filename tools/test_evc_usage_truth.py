#!/usr/bin/env python
"""V-EVC-* gates for the usage-truth reader (EVC phase 1, plan 01).

Purpose: pin mission_spend.usage_truth, the one canonical reader of a mission's spend (last copy per
(message.id, requestId) per transcript, per-column maximum across transcripts), and the int projection
processed_tokens. Each later plan of the phase appends its own section and REQUIRED names.

Hermetic: every state directory is pointed at a fresh temp dir BEFORE any project import. Final line:
    EVC_USAGE_TRUTH_PASS=p/t threshold=t/t NOT_OBSERVED=k

Mutation drill: GSD_MISSION_DRILL_DIR holding mutated copies is imported first (position 0 of sys.path).
Use isolated copies only; the live files are never edited to prove a gate can go red.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

REAL_STATE = os.environ.get("GSD_LONG_RUN_STATE_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "state")

TMP = tempfile.mkdtemp(prefix="evc-usage-truth-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_USAGE_INDEX"] = str(Path(TMP) / "usage_index.sqlite")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ.pop("CPP_MISSION_RENEW", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
# Order matters: plan 02 appends mission_surface and gsd_mission AFTER these (gsd_mission resets sys.path[0]).
import tis_observed  # noqa: E402,F401
import usage_index  # noqa: E402,F401
import mission_spend as ms  # noqa: E402
import mission_surface  # noqa: E402,F401
import gsd_mission as gm  # noqa: E402

passes = fails = notobs_n = 0
SEEN: list[str] = []
REQUIRED = ["V-EVC-STREAM-LAST", "V-EVC-STREAM-LAST-CONTROL"]
CREATED = 1_800_000_000.0          # 2027-01-15T08:00:00Z
WORK_DIR = "/home/kobii/missions/evc-fix"


def check(gate, cond, ev=""):
    global passes, fails
    SEEN.append(gate)
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def notobs(gate, ev=""):
    global notobs_n
    notobs_n += 1
    print(f"NOT_OBSERVED {gate} {ev}")


def ts(minute=0, sec=0):
    return f"2027-01-15T08:{minute:02d}:{sec:02d}Z"


def aline(mid, req, t, inp=0, cw=0, cr=0, out=0, cc=None, model="claude-sonnet-5-5"):
    u = {"input_tokens": inp, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr,
         "output_tokens": out}
    if cc:
        u["cache_creation"] = cc
    o = {"type": "assistant", "timestamp": t, "message": {"id": mid, "model": model, "usage": u}}
    if req is not None:
        o["requestId"] = req
    if mid is None:
        del o["message"]["id"]
    return json.dumps(o) + "\n"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def mission_rec():
    return {"mission_id": "m-evcfix", "work_dir": WORK_DIR, "created_at": CREATED}


def build_fixs(root: Path):
    d = root / ms.encode_cwd(WORK_DIR)
    f = write(d / "s1.jsonl",
              aline("m1", "r1", ts(0, 10), inp=1, cr=100, out=5)
              + aline("m1", "r1", ts(0, 11), inp=1, cr=100, out=50))
    return f


def section_reader():
    root = Path(TMP) / "projects_fixs"
    f = build_fixs(root)
    rec = mission_rec()
    sess = ({"s1"}, set())
    pt = ms.processed_tokens(rec, root, None, sess)
    ut = ms.usage_truth(rec, root, None, sess) if hasattr(ms, "usage_truth") else None
    tree_p = (ut or {}).get("tree", {}).get("processed")
    check("V-EVC-STREAM-LAST", pt == 151 and tree_p == 151, f"processed_tokens={pt} tree.processed={tree_p}")
    first = ms._file_tokens(f, None)
    check("V-EVC-STREAM-LAST-CONTROL", first == 106 and first < 151 and 151 - first == 45,
          f"_file_tokens={first} diff={151 - first}")


def build_fix1(root: Path, synth_model="<synthetic>", crossfile=True, name="fix1"):
    d = root / ms.encode_cwd(WORK_DIR)
    main = (json.dumps({"type": "user", "timestamp": ts(0, 5), "message": {"role": "user", "content": "hi"}}) + "\n"
            + aline("m1", "r1", ts(0, 10), inp=1, cr=100, out=5)
            + aline("m1", "r1", ts(0, 11), inp=1, cr=100, out=50)
            + aline("m2", "r2", ts(1, 0), inp=2, cw=300, cr=1000, out=10,
                    cc={"ephemeral_5m_input_tokens": 100, "ephemeral_1h_input_tokens": 200})
            + aline("ms", "rs", ts(1, 30), out=999, model=synth_model)
            + aline(None, None, ts(2, 0), out=7)
            + aline("m0", "r0", "2020-01-01T00:00:00Z", cr=5000))
    f1 = write(d / "s1.jsonl", main)
    sub = aline("m3", "r3", ts(3, 0), inp=3, cr=400, out=20, model="claude-opus-5-5")
    if crossfile:
        sub += aline("m1", "r1", ts(0, 12), inp=1, cr=90, out=60)
    f2 = write(d / "s1" / "subagents" / "agent-x.jsonl", sub)
    return d, f1, f2


def section_truth():
    now = 1_800_000_500.0
    sess = ({"s1"}, set())
    rec = mission_rec()
    root = Path(TMP) / "projects_fix1"
    d, f1, f2 = build_fix1(root)
    t = ms.usage_truth(rec, root, None, sess, now) or {}
    tr, ss, sa = t.get("tree", {}), t.get("sessions", {}), t.get("subagents", {})
    m, a = ss.get("s1", {}), sa.get("s1", {})
    check("V-EVC-SUBAGENT-IN-TREE",
          m.get("processed") == 1480 and a.get("processed") == 423 and tr.get("processed") == 1903
          and m.get("processed", 0) + a.get("processed", 0) == tr.get("processed"),
          f"session={m.get('processed')} subagents={a.get('processed')} tree={tr.get('processed')} "
          f"main={m} sub={a} tree={tr}")
    r2 = Path(TMP) / "projects_fix1_real"
    build_fix1(r2, synth_model="claude-sonnet-5-5")
    t2 = ms.usage_truth(rec, r2, None, sess, now) or {}
    check("V-EVC-SYNTHETIC-EXCLUDED",
          tr.get("output") == 97 and t2.get("tree", {}).get("output") == 1096,
          f"output={tr.get('output')} control(real model)={t2.get('tree', {}).get('output')}")
    r3 = Path(TMP) / "projects_fix1_nocross"
    build_fix1(r3, crossfile=False)
    t3 = ms.usage_truth(rec, r3, None, sess, now) or {}
    check("V-EVC-CROSSFILE-MAX",
          tr.get("cache_read") == 1500 and tr.get("output") == 97 and tr.get("calls") == 4
          and m.get("cache_read") == 1100 and m.get("output") == 77
          and t3.get("tree", {}).get("output") == 87,
          f"calls={tr.get('calls')} main.cache_read={m.get('cache_read')} main.output={m.get('output')} "
          f"control(no cross copy) output={t3.get('tree', {}).get('output')}")
    # identity-less: once on cold and warm, twice at two offsets
    cache: dict = {}
    c1 = ms.usage_truth(rec, root, cache, sess, now) or {}
    c2 = ms.usage_truth(rec, root, cache, sess, now) or {}
    r4 = Path(TMP) / "projects_idless"
    write(r4 / ms.encode_cwd(WORK_DIR) / "s1.jsonl", aline(None, None, ts(2, 0), out=7) + aline(None, None, ts(2, 5), out=7))
    t4 = ms.usage_truth(rec, r4, None, sess, now) or {}
    check("V-EVC-IDLESS-ONCE",
          c1.get("sessions", {}).get("s1", {}).get("calls") == 3 and c2.get("sessions", {}).get("s1", {}).get("calls") == 3
          and t4.get("tree", {}).get("calls") == 2 and t4.get("tree", {}).get("output") == 14,
          f"cold main calls={c1.get('sessions', {}).get('s1', {}).get('calls')} "
          f"warm={c2.get('sessions', {}).get('s1', {}).get('calls')} two-rows calls={t4.get('tree', {}).get('calls')}")
    nosince = ms.usage_truth({"mission_id": "m-x", "work_dir": WORK_DIR}, root, None, sess, now) or {}
    check("V-EVC-SINCE",
          tr.get("cache_read") == 1500 and nosince.get("tree", {}).get("cache_read") == 6500,
          f"with created_at cache_read={tr.get('cache_read')} control(no created_at)={nosince.get('tree', {}).get('cache_read')}")
    # categories
    cols = ("input", "cache_write", "cache_read", "output")
    bm = t.get("by_model", {})
    buckets = [tr] + list(ss.values()) + list(sa.values()) + [{**v, "processed": sum(v[c] for c in cols)} for v in bm.values()]
    s_ok = all(sum(b.get(c, 0) for c in cols) == b.get("processed") for b in buckets) and bool(buckets)
    sum_ok = all(m.get(c, 0) + a.get(c, 0) == tr.get(c) for c in cols + ("calls",))
    bm_ok = sum(v["calls"] for v in bm.values()) == tr.get("calls") and \
        all(sum(v[c] for v in bm.values()) == tr.get(c) for c in cols)
    mt = max(f1.stat().st_mtime, f2.stat().st_mtime)
    age = ms.truth_age(t, now + 90) if hasattr(ms, "truth_age") else {}
    age_ok = age.get("measured_age_s") == 90.0 and age.get("last_call_age_s") is not None \
        and age.get("files_age_s") is not None
    age_none = ms.truth_age({"measured_at": now, "tree": {}, "files_mtime_max": None}, now + 1) \
        if hasattr(ms, "truth_age") else {}
    check("V-EVC-CATEGORIES-SUM",
          s_ok and sum_ok and bm_ok and tr.get("last_call_ts") == ts(3) and m.get("last_call_ts") == ts(2)
          and a.get("last_call_ts") == ts(3) and t.get("measured_at") == now and t.get("files") == 2
          and t.get("files_mtime_max") == mt and age_ok
          and age_none.get("last_call_age_s") is None and age_none.get("files_age_s") is None,
          f"sums={s_ok}/{sum_ok}/{bm_ok} last={tr.get('last_call_ts')}/{m.get('last_call_ts')}/{a.get('last_call_ts')} "
          f"files={t.get('files')} mtime_ok={t.get('files_mtime_max') == mt} age={age}")
    # unknown-not-zero
    gone = ms.usage_truth({"mission_id": "m-g", "work_dir": "/no/such/dir", "created_at": CREATED}, root, None, sess, now)
    nosess = ms.usage_truth(rec, root, None, ({}, {}), now)
    r5 = Path(TMP) / "projects_zero"
    write(r5 / ms.encode_cwd(WORK_DIR) / "s1.jsonl", aline("o", "ro", "2020-01-01T00:00:00Z", cr=5))
    zero = ms.usage_truth(rec, r5, None, sess, now) or {}
    nofile = ms.usage_truth(rec, r5, None, ({"s7"}, set()), now) or {}
    check("V-EVC-UNKNOWN-NOT-ZERO",
          gone is None and nosess is None and zero.get("tree", {}).get("processed") == 0 and zero.get("files") == 1
          and nofile.get("files") == 0 and nofile.get("tree", {}).get("processed") == 0,
          f"nodir={gone} nosessions={nosess} control measured-zero processed={zero.get('tree', {}).get('processed')} "
          f"files={zero.get('files')} no-file files={nofile.get('files')}")
    # cache hit
    cache = {}
    ms.usage_truth(rec, root, cache, sess, now)
    n = {"c": 0}
    real = tis_observed.calls_from

    def counting(*a_, **k_):
        n["c"] += 1
        return real(*a_, **k_)
    try:
        tis_observed.calls_from = counting
        warm = ms.usage_truth(rec, root, cache, sess, now)
        reread0 = n["c"]
        with open(f2, "a", encoding="utf-8") as fh:
            fh.write(aline("m4", "r4", ts(4, 0), out=11, model="claude-opus-5-5"))
        n["c"] = 0
        after = ms.usage_truth(rec, root, cache, sess, now)
        reread1 = n["c"]
    finally:
        tis_observed.calls_from = real
    check("V-EVC-CACHE-HIT",
          reread0 == 0 and warm == t and reread1 == 1 and after["tree"]["output"] == 108,
          f"unchanged re-reads={reread0} equal={warm == t}; control after append re-reads={reread1} "
          f"output={after['tree']['output']}")
    # cache shared across records with different created_at
    r6 = Path(TMP) / "projects_since"
    write(r6 / ms.encode_cwd(WORK_DIR) / "s1.jsonl",
          aline("a", "ra", "2027-01-15T07:00:00Z", out=10) + aline("b", "rb", ts(1), out=20))
    recA = {"mission_id": "m-a", "work_dir": WORK_DIR, "created_at": CREATED}
    recB = {"mission_id": "m-b", "work_dir": WORK_DIR, "created_at": CREATED - 7200}
    solo = [ms.processed_tokens(r_, r6, None, sess) for r_ in (recA, recB)]
    sh1 = {}
    o1 = [ms.processed_tokens(r_, r6, sh1, sess) for r_ in (recA, recB)]
    sh2 = {}
    o2 = [ms.processed_tokens(r_, r6, sh2, sess) for r_ in (recB, recA)][::-1]
    check("V-EVC-CACHE-SINCE", o1 == solo and o2 == solo and solo[0] != solo[1],
          f"cacheless={solo} shared A,B={o1} shared B,A={o2}")
    # unreadable
    r7 = Path(TMP) / "projects_unread"
    build_fix1(r7)
    ok0 = ms.usage_truth(rec, r7, None, ({"s1", "s9"}, set()), now) or {}
    (r7 / ms.encode_cwd(WORK_DIR) / "s9.jsonl").mkdir()
    bad = ms.usage_truth(rec, r7, None, ({"s1", "s9"}, set()), now) or {}
    check("V-EVC-UNREADABLE",
          bad.get("unreadable") == 1 and ok0.get("unreadable") == 0
          and bad.get("tree", {}).get("processed") == ok0.get("tree", {}).get("processed") == 1903,
          f"unreadable={bad.get('unreadable')} control={ok0.get('unreadable')} processed={bad.get('tree', {}).get('processed')}")


T2_GATES = ["V-EVC-SUBAGENT-IN-TREE", "V-EVC-SYNTHETIC-EXCLUDED", "V-EVC-CROSSFILE-MAX", "V-EVC-IDLESS-ONCE",
            "V-EVC-SINCE", "V-EVC-CATEGORIES-SUM", "V-EVC-UNKNOWN-NOT-ZERO", "V-EVC-CACHE-HIT",
            "V-EVC-CACHE-SINCE", "V-EVC-UNREADABLE"]
REQUIRED.extend(T2_GATES)


T3_PRICES = {"claude-sonnet-5": {"input": 3, "cache_write_5m": 3.75, "cache_write_1h": 6,
                                 "cache_read": 0.3, "output": 15},
             "claude-opus-5": {"input": 5, "cache_write_5m": 6.25, "cache_write_1h": 10,
                               "cache_read": 0.5, "output": 25}}


def section_index_guard():
    import shutil
    sess = ({"s1"}, set())
    rec = mission_rec()
    root = Path(TMP) / "projects_t3"
    build_fix1(root)
    t = ms.usage_truth(rec, root, None, sess, 1_800_000_500.0) or {}
    tr = t.get("tree", {})
    sub = t.get("subagents", {}).get("s1", {})
    far = 4_000_000_000.0

    def indexed(r, name):
        con = usage_index.connect(Path(TMP) / name)
        try:
            usage_index.refresh(con, r, deadline_s=30)
            return usage_index.window(con, CREATED, far, T3_PRICES)
        finally:
            con.close()
    w = indexed(root, "t3_full.sqlite")
    cols = (("input", "input"), ("cache_write", "cache_write"), ("cache_read", "cache_read"),
            ("output", "output"), ("calls", "calls"))
    eq = all(w.get(a) == tr.get(b) for a, b in cols) and w.get("subagent_calls") == sub.get("calls") == 1
    r2 = Path(TMP) / "projects_t3_nosub"
    shutil.copytree(root, r2, ignore=shutil.ignore_patterns("subagents"))
    w2 = indexed(r2, "t3_nosub.sqlite")
    ctl = w2.get("output", 1 << 60) < w.get("output") and w2.get("calls") == w.get("calls") - 1
    check("V-EVC-EQ-INDEX", eq and ctl,
          f"reader={[tr.get(b) for _, b in cols]} sub_calls={sub.get('calls')} "
          f"index={[w.get(a) for a, _ in cols]} sub_calls={w.get('subagent_calls')}; "
          f"control no-subagents output={w2.get('output')} calls={w2.get('calls')}")

    # guard divergence: byte-identical duplicates -> no divergence; streamed growth -> exactly 45
    ident = Path(TMP) / "projects_t3_ident"
    line = aline("m1", "r1", ts(0, 10), inp=1, cr=100, out=5)
    fi = write(ident / ms.encode_cwd(WORK_DIR) / "s1.jsonl", line + line)
    ti = ms.usage_truth(rec, ident, None, sess) or {}
    fixs = Path(TMP) / "projects_t3_fixs"
    fs = build_fixs(fixs)
    ts_ = ms.usage_truth(rec, fixs, None, sess) or {}
    fti, fts = ms._file_tokens(fi, None), ms._file_tokens(fs, None)
    try:
        st_i = ms.session_tokens(fi, None)
        st_s = ms.session_tokens(fs, None)
        st_ok = (st_i or {}).get("tokens") == fti and (st_s or {}).get("tokens") == fts
        st_ev = f"session_tokens={(st_i or {}).get('tokens')}/{(st_s or {}).get('tokens')}"
    except Exception as e:  # noqa: BLE001
        st_ok, st_ev = False, f"session_tokens raised {type(e).__name__}: {e}"
    check("V-EVC-GUARD-DIVERGENCE",
          fti == ti.get("tree", {}).get("processed") and fts == 106 and ts_.get("tree", {}).get("processed") == 151
          and 151 - fts == 45 and st_ok,
          f"identical dup: _file_tokens={fti} reader={ti.get('tree', {}).get('processed')}; streamed: "
          f"_file_tokens={fts} reader={ts_.get('tree', {}).get('processed')} diff={151 - fts}; {st_ev}; "
          f"named debt: guard undercount, Phase 5")

    root1 = Path(TMP) / "projects_t3_proj"
    build_fix1(root1)
    pt = ms.processed_tokens(rec, root1, None, sess)
    ut = ms.usage_truth(rec, root1, None, sess) or {}
    none_pt = ms.processed_tokens({"mission_id": "m-g", "work_dir": "/no/such/dir", "created_at": CREATED},
                                  root1, None, sess)
    check("V-EVC-PROJECTION",
          isinstance(pt, int) and pt == ut.get("tree", {}).get("processed") == 1903 and none_pt is None,
          f"processed_tokens={pt} tree.processed={ut.get('tree', {}).get('processed')} no-directory={none_pt}")


REQUIRED.extend(["V-EVC-EQ-INDEX", "V-EVC-GUARD-DIVERGENCE", "V-EVC-PROJECTION"])

NOW = CREATED
gone = lambda pid: False   # noqa: E731


def _held_mission(mid: str) -> dict:
    """A RUNNING mission with a background owner "<mid>-w", estimate 100_000 and a long clock."""
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": 4242, "proc_start": None, "heartbeat_at": NOW,
             "epoch": 1, "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, max_hours=1000.0, token_estimate=100_000, owner=owner)


def _host_rows(mid: str, state: str) -> list:
    return [{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background", "state": state}]


def section_statement():
    empty = Path(TMP) / "projects_empty_t1"
    empty.mkdir(parents=True, exist_ok=True)
    real_root = ms.projects_root
    ms.projects_root = lambda: empty
    try:
        mid = "m-evcalive"
        rec = _held_mission(mid)
        held = gm._cost_breaker(rec, NOW + 60, measure=lambda r: 10_000_000, fingerprint=lambda w: None)
        meas = (held.get("owner_hold") or {}).get("measured") or {}
        p = gm.plan_next(held, NOW + 3660, _host_rows(mid, "running"), pid_alive=gone)
        tail = ("measured 10,000,000 as of 2027-01-15T08:01:00Z (age 1h00m); "
                "worker LIVE -> total current UNKNOWN, >= 10,000,000")
        check("V-EVC-STATEMENT-ALIVE",
              meas.get("processed") == 10_000_000 and meas.get("measured_at") == NOW + 60
              and p["action"] == "none" and p["reason"].endswith(tail)
              and "recorded at 2027-01-15T08:01:00Z (age 1h00m)" in p["reason"],
              f"measured={meas} action={p['action']} reason={p['reason']!r}")
        pd = gm.plan_next(held, NOW + 3660, _host_rows(mid, "done"), pid_alive=gone)
        check("V-EVC-STATEMENT-ALIVE-CONTROL",
              pd["action"] == "settle" and "host lists session done" in pd["reason"]
              and "worker LIVE" not in pd["reason"],
              f"action={pd['action']} reason={pd['reason']!r}")
    finally:
        ms.projects_root = real_root


REQUIRED.extend(["V-EVC-STATEMENT-ALIVE", "V-EVC-STATEMENT-ALIVE-CONTROL"])

S1_LAST = "2027-01-15T07:59:30Z"


def _s1(**kw):
    s = {"processed": 141_000_000, "input": None, "cache_write": None, "cache_read": None, "output": None,
         "calls": 10, "measured_at": NOW, "last_call_ts": S1_LAST, "files_mtime_max": None, "files": 29,
         "unreadable": 0}
    s.update(kw)
    return s


def section_statement_forms():
    A, B, D, U = ms.V_LIVE, ms.V_BLOCKED, ms.V_DEAD, ms.V_UNKNOWN
    check("V-EVC-VERDICT-CONSTANTS",
          (ms.V_LIVE, ms.V_BLOCKED, ms.V_DEAD, ms.V_UNKNOWN) == (gm.LIVE, gm.WAITING_HUMAN, gm.DEAD, gm.UNKNOWN)
          == ("ALIVE", "BLOCKED", "DEAD", "UNKNOWN"),
          f"{(ms.V_LIVE, ms.V_BLOCKED, ms.V_DEAD, ms.V_UNKNOWN)}")
    # stale branch: a predicate driven green by the real renderer and red by a bare-figure one
    def honest(text, snap):
        return "as of" in text and "age" in text and "total current UNKNOWN" in text

    def bare(snap, verdicts, now, fresh=False):
        return f"{snap['processed']:,}"
    s1 = _s1()
    real = ms.spend_statement(s1, [(A, "x")], NOW + 262800)
    wrong = bare(s1, [(A, "x")], NOW + 262800)
    check("V-EVC-STATEMENT-ALIVE-STALE",
          honest(real, s1) and "age 3d1h" in real and not honest(wrong, s1),
          f"GREEN real={real!r} RED bare={wrong!r}")
    exp = "worker liveness UNKNOWN -> total current UNKNOWN, >= 141,000,000"
    outs = {repr(v): ms.spend_statement(s1, v, NOW) for v in ([B], [U], [B, D], [], None)}
    check("V-EVC-STATEMENT-UNKNOWN-VERDICT",
          all(o.endswith(exp) for o in outs.values())
          and "worker LIVE" in ms.spend_statement(s1, [A, D], NOW), f"{outs}")
    f = ms.spend_statement(s1, [D], NOW, fresh=True)
    nf = ms.spend_statement(s1, [D], NOW)
    mixed = ms.spend_statement(s1, [D, A], NOW, fresh=True)
    check("V-EVC-STATEMENT-DEAD",
          f.endswith(f"no live worker -> 141,000,000 is final as of last call {S1_LAST}")
          and f"was the total as of last call {S1_LAST}; calls after 2027-01-15T08:00:00Z not counted (not re-measured)" in nf
          and "is final" not in nf and "no live worker" not in mixed, f"fresh={f!r} stored={nf!r}")
    u2 = ms.spend_statement(_s1(unreadable=2), [A], NOW)
    u0 = ms.spend_statement(_s1(unreadable=0), [A], NOW)
    check("V-EVC-STATEMENT-UNREADABLE",
          u2.endswith("2 transcript(s) unreadable -> total UNKNOWN, >= 141,000,000") and "unreadable" not in u0,
          f"{u2!r}")
    nm = "spend UNKNOWN (not measurable)"
    bad = [None, {}, _s1(files=0), _s1(processed=None), _s1(processed="12"), _s1(processed=True),
           _s1(processed=-5), _s1(processed=1.5)]
    try:
        got = [ms.spend_statement(b, [A], NOW) for b in bad]
    except Exception as exc:  # noqa: BLE001
        got = [repr(exc)]
    zero = ms.spend_statement(_s1(processed=0, files=1), [A], NOW)
    check("V-EVC-STATEMENT-NOT-MEASURABLE",
          got == [nm] * len(bad) and zero.startswith("measured 0 as of"), f"{got} zero={zero!r}")
    leg = ms.hold_text({"reason": "TOK-18 S0 park", "set_at": NOW}, None, NOW + 3600)
    noset = ms.hold_text({"reason": "TOK-18 S0 park"}, None, NOW)
    cut = ms.hold_text({"reason": "TOK-18 S0 park", "set_at": NOW}, None, NOW, limit=5)
    h = gm.set_owner_hold(_held_mission("m-evcleg")["mission_id"], "plain park", now=NOW)
    check("V-EVC-LEGACY-HOLD",
          leg == "recorded at 2027-01-15T08:00:00Z (age 1h00m): TOK-18 S0 park; not re-measured"
          and noset.startswith("recorded at an unknown time (age unknown): ")
          and cut.startswith("recorded at 2027-01-15T08:00:00Z (age 0s): TOK-1;")
          and "measured" not in (h.get("owner_hold") or {}),
          f"{leg!r} {noset!r} {cut!r}")


REQUIRED.extend(["V-EVC-VERDICT-CONSTANTS", "V-EVC-STATEMENT-ALIVE-STALE", "V-EVC-STATEMENT-UNKNOWN-VERDICT",
                 "V-EVC-STATEMENT-DEAD", "V-EVC-STATEMENT-UNREADABLE", "V-EVC-STATEMENT-NOT-MEASURABLE",
                 "V-EVC-LEGACY-HOLD"])

# one line that reads the reason key of a hold dict (interpolation or concatenation)
_HOLD_REASON_RE = re.compile(r"owner[ _]hold\b[^\n]*(?:\.get\(\s*['\"]reason['\"]|\[\s*['\"]reason['\"]\s*\])")


def _scan(text: str) -> int:
    return sum(1 for ln in text.splitlines()
               if not ln.lstrip().startswith("#") and _HOLD_REASON_RE.search(ln))


def section_surfaces():
    tools = Path(__file__).resolve().parent
    hits = {n: _scan((tools / n).read_text(encoding="utf-8")) for n in ("gsd_mission.py", "mission_surface.py")}
    ctl_bad = _scan("    return f\"owner hold: {rec['owner_hold'].get('reason')}\"")
    ctl_ok = _scan("    return 'owner hold: ' + hold_text(rec['owner_hold'], None, now)")
    empty = Path(TMP) / "projects_empty_t2"
    empty.mkdir(parents=True, exist_ok=True)
    real_root = ms.projects_root
    ms.projects_root = lambda: empty
    try:
        mid = "m-evcsurf"
        held = gm._cost_breaker(_held_mission(mid), NOW + 60, measure=lambda r: 141_000_000,
                                fingerprint=lambda w: None)
        later = NOW + 3660
        tail_re = re.compile(r"(measured [\d,]+ as of .*|spend UNKNOWN \(not measurable\)|not re-measured)$")
        pn = gm.plan_next(held, later, _host_rows(mid, "running"), pid_alive=gone)
        ps = gm.plan_next(held, later, _host_rows(mid, "done"), pid_alive=gone)
        lau = dict(held, state=gm.LAUNCHING, owner=None, pending={"kind": "worker_start", "bg_id": "f92cdad1"})
        lrows = [{"sessionId": "f92cdad1-0000", "id": "f92cdad1", "kind": "background", "state": "done"}]
        pl = gm.plan_next(lau, later, lrows, pid_alive=gone)
        rr = gm.renewal_refusal(held, "owner BLOCKED and budget: older than 1.0 h", "OK", now=later)
        rows = [{"mission_id": mid, "state": held["state"], "epoch": held["epoch"], "plan": pn}]
        why = gm.status_surface(rows, [held], later)["attempts"][0]["why"]
        rows2 = [{"mission_id": mid, "state": held["state"], "epoch": held["epoch"],
                  "plan": {"action": "launch", "reason": "UNRELATED"}}]
        why2 = gm.status_surface(rows2, [held], later)["attempts"][0]["why"]
        import inspect
        npos = len(inspect.signature(mission_surface.classify).parameters)
        ok = (hits == {"gsd_mission.py": 0, "mission_surface.py": 0} and ctl_bad == 1 and ctl_ok == 0
              and pn["action"] == "none" and "recorded at" in pn["reason"] and "worker LIVE" in pn["reason"]
              and ps["action"] == "settle" and "host lists session done" in ps["reason"]
              and "recorded at" in ps["reason"] and "calls after" in ps["reason"]
              and pl["action"] == "settle" and "launched worker f92cdad1" in pl["reason"]
              and "recorded at" in pl["reason"] and "calls after" in pl["reason"]
              and rr is not None and rr.startswith("owner hold") and "recorded at" in rr
              and bool(tail_re.search(rr))
              and "recorded at" in why and "UNRELATED" not in why2 and "recorded at" in why2
              and npos == 4)
        check("V-EVC-SURFACES-ONE-RENDERER", ok,
              f"scan_hits={hits} control_bad={ctl_bad} control_renderer={ctl_ok} classify_params={npos} "
              f"none={pn['reason']!r} settle={ps['reason']!r} launch={pl['reason']!r} renew={rr!r} "
              f"why={why!r} why2={why2!r}")
    finally:
        ms.projects_root = real_root


REQUIRED.append("V-EVC-SURFACES-ONE-RENDERER")


def main() -> int:
    section_reader()
    section_truth()
    section_index_guard()
    section_statement()
    section_statement_forms()
    section_surfaces()
    missing = [g for g in REQUIRED if g not in SEEN]
    check("V-EVC-ALL-GATES-RAN", not missing, f"missing={missing}")
    print(f"EVC_USAGE_TRUTH_PASS={passes}/{passes + fails} threshold={len(REQUIRED) + 1}/{len(REQUIRED) + 1} "
          f"NOT_OBSERVED={notobs_n}")
    return 0 if fails == 0 and passes >= len(REQUIRED) + 1 else 1


if __name__ == "__main__":
    sys.exit(main())
