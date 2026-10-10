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


def main() -> int:
    section_reader()
    section_truth()
    missing = [g for g in REQUIRED if g not in SEEN]
    check("V-EVC-ALL-GATES-RAN", not missing, f"missing={missing}")
    print(f"EVC_USAGE_TRUTH_PASS={passes}/{passes + fails} threshold={len(REQUIRED) + 1}/{len(REQUIRED) + 1} "
          f"NOT_OBSERVED={notobs_n}")
    return 0 if fails == 0 and passes >= len(REQUIRED) + 1 else 1


if __name__ == "__main__":
    sys.exit(main())
