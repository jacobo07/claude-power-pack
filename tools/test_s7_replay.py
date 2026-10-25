#!/usr/bin/env python
"""V-S7-* gates: S7 historical replay + champion/challenger (flow-compression Phase 7).

Every negative control below was run against the REAL reader (flow_replay, gsd_mission, the pinned host ledger) and its
output read before the assertion was written. A control that has not been seen to fire is not a gate. Prints S7_PASS=n/n.
"""
from __future__ import annotations

import ast
import builtins
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="s7-replay-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["PP_OWNER_QUEUE_STATE_DIR"] = str(Path(TMP) / "owner-queue")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cc")
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import flow_replay as fr  # noqa: E402
import gsd_mission as gm  # noqa: E402

PHASE = ROOT / ".planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger"
PIN = PHASE / "07-PIN.json"
SRC = TOOLS / "flow_replay.py"
RESULTS: list[tuple[str, bool, str]] = []


def check(gate: str, cond, ev: str = "") -> None:
    RESULTS.append((gate, bool(cond), ev))
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree_digest(d: Path) -> dict:
    return {str(p.relative_to(d)): sha(p) for p in sorted(Path(d).rglob("*")) if p.is_file()}


PN = fr.load_pin(PIN)
ROWS, _TORN = fr.read_prefix(PN)


def copy_host(dst: Path, *, records: list[str] | None = None, queue: bool = True) -> Path:
    """A temp copy of the pinned ledger prefix, the Owner queue and (selected) mission records; returns the ledger."""
    dst.mkdir(parents=True, exist_ok=True)
    led = dst / "gsd-autorun-ledger.jsonl"
    with open(PN["ledger"], "rb") as fh:
        led.write_bytes(fh.read(PN["bytes"]))
    src = Path(PN["missions_dir"])
    if queue and (src / "OWNER_QUEUE.jsonl").is_file():
        shutil.copy2(src / "OWNER_QUEUE.jsonl", dst / "OWNER_QUEUE.jsonl")
    for p in sorted(src.glob("gsd-mission-*.json")):
        if records is None or p.name in records:
            shutil.copy2(p, dst / p.name)
    return led


# ----------------------------------------------------------------------------------------- write probe
class WriteProbe:
    """Records every open / mutate call whose target sits under `roots` with a write, append or create intent."""

    def __init__(self, roots):
        self.roots = [os.path.realpath(str(r)) for r in roots]
        self.writes: list[str] = []
        self.opens = 0

    def _under(self, p) -> bool:
        try:
            rp = os.path.realpath(os.fspath(p))
        except (TypeError, ValueError):
            return False
        return any(rp == r or rp.startswith(r + os.sep) for r in self.roots)

    def __enter__(self):
        self._saved = {}
        probe = self

        def wrap_open(real):
            def inner(file, mode="r", *a, **k):
                probe.opens += 1
                if isinstance(file, (str, bytes, os.PathLike)) and probe._under(file) and \
                        any(c in str(mode) for c in "wax+"):
                    probe.writes.append(f"open({file!r},{mode!r})")
                return real(file, mode, *a, **k)
            return inner

        def wrap_osopen(real):
            def inner(path, flags, *a, **k):
                probe.opens += 1
                if probe._under(path) and flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC):
                    probe.writes.append(f"os.open({path!r},{flags})")
                return real(path, flags, *a, **k)
            return inner

        def wrap_path(name, real):
            def inner(*args, **k):
                if args and isinstance(args[0], (str, bytes, os.PathLike)) and probe._under(args[0]):
                    probe.writes.append(f"os.{name}({args[0]!r})")
                return real(*args, **k)
            return inner

        for obj, name, maker in ((builtins, "open", wrap_open), (io, "open", wrap_open), (os, "open", wrap_osopen)):
            self._saved[(obj, name)] = getattr(obj, name)
            setattr(obj, name, maker(getattr(obj, name)))
        for name in ("remove", "unlink", "rename", "replace", "mkdir", "makedirs", "rmdir", "truncate", "utime"):
            if hasattr(os, name):
                self._saved[(os, name)] = getattr(os, name)
                setattr(os, name, wrap_path(name, getattr(os, name)))
        return self

    def __exit__(self, *exc):
        for (obj, name), real in self._saved.items():
            setattr(obj, name, real)


_RES_CACHE: dict = {}


def RES() -> dict:
    """The full replay of the module under test, computed once per module object."""
    k = id(fr)
    if k not in _RES_CACHE:
        _RES_CACHE.clear()
        _RES_CACHE[k] = fr.replay(PIN)
    return _RES_CACHE[k]


def run_replay(pin_path: Path) -> dict:
    return fr.replay(pin_path)


def s3_of(res: dict) -> dict | None:
    return next((i for i in res["incidents"] if i["slice"] == "S3" and i["kind"] == "relay_held"
                 and i["rows"] == 53), None)


def s2_of(res: dict) -> dict | None:
    return next((i for i in res["incidents"] if i["slice"] == "S2" and i["rows"] == 53), None)


# ----------------------------------------------------------------------------------------- gates (Task 1)
def gate_pin():
    base = Path(TMP) / "pin-case"
    led = copy_host(base, records=[], queue=False)
    pin_p = base / "pin.json"
    pn = fr.pin(led, pin_p)
    r1, _ = fr.read_prefix(pn)
    with open(led, "ab") as fh:                                  # the live ledger grows after the pin
        fh.write(b'{"ts": "2030-01-01T00:00:00+00:00", "session_id": "x", "event": "late_row"}\n')
    r2, _ = fr.read_prefix(pn)
    grew = sha(led) != pn["sha256"]
    check("V-S7-TRACER-PIN-STABLE", r1 == r2 and len(r1) == pn["rows"] and grew and
          not any(r.get("event") == "late_row" for r in r2),
          f"rows={len(r1)} identical after append; ledger bytes grew={grew}")
    flipped = base / "flipped.jsonl"
    raw = bytearray(led.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    flipped.write_bytes(bytes(raw))
    bad_pn = dict(pn, ledger=str(flipped))
    try:
        fr.read_prefix(bad_pn)
        raised = False
    except fr.Inconclusive:
        raised = True
    bad_pin = base / "bad-pin.json"
    bad_pin.write_text(json.dumps(bad_pn), encoding="utf-8")
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = fr.main(["replay", "--pin", str(bad_pin)])
    good_rc = fr.main(["replay", "--pin", str(pin_p)])
    check("V-S7-TRACER-PIN-FLIPPED-BYTE", raised and rc == 2 and good_rc == 0 and "INCONCLUSIVE" in err.getvalue(),
          f"flipped byte raises; bad pin exit {rc}; the unflipped pin exit {good_rc}")
    committed_ok = True
    try:
        rows, _ = fr.read_prefix(PN)
        committed_ok = len(rows) == PN["rows"]
    except fr.Inconclusive:
        committed_ok = False
    check("V-S7-TRACER-PIN-COMMITTED-VERIFIES", committed_ok, f"committed pin sha {PN['sha256'][:12]} rows={PN['rows']}")


def gate_readonly():
    host = Path(PN["missions_dir"])
    # the probe itself must fire: a control against the real wrapper, not an assumption
    probe_dir = Path(TMP) / "probe-control"
    probe_dir.mkdir(exist_ok=True)
    with WriteProbe([probe_dir]) as pr:
        with open(probe_dir / "f", "a") as fh:
            fh.write("x")
        Path(probe_dir / "g").write_text("y")
    check("V-S7-READONLY-PROBE-FIRES", len(pr.writes) >= 2, f"{pr.writes}")
    # part one: a full replay against a temp COPY, with the copy being what every implicit accessor would resolve to
    cp = Path(TMP) / "copy-host"
    led = copy_host(cp)
    pin_p = cp / "pin.json"
    fr.pin(led, pin_p)
    before = tree_digest(cp)
    with fr._env({"GSD_LONG_RUN_STATE_DIR": str(cp), "PP_OWNER_QUEUE_STATE_DIR": str(cp)}):
        res = run_replay(pin_p)
    after = tree_digest(cp)
    # control: the same byte comparison goes red when a writer reaches the copy through the implicit accessor
    with fr._env({"GSD_LONG_RUN_STATE_DIR": str(cp)}):
        gm.lr.ledger_append("s7-control", "s7_control_row")
    leaked = tree_digest(cp) != before
    led.write_bytes(open(PN["ledger"], "rb").read(PN["bytes"]))     # restore the copy for the later parts
    check("V-S7-READONLY-COPY-IDENTICAL", before == after and len(before) > 2 and len(res["incidents"]) > 0 and leaked,
          f"{len(before)} copied files byte-identical after a full replay; incidents={len(res['incidents'])}; "
          f"control: an implicit-accessor append is seen as a change={leaked}")
    # part two: the real host paths, probed for any write-mode open; whole-file hashes of live files are NOT compared
    with WriteProbe([host]) as pr:
        res2 = run_replay(PIN)
    check("V-S7-READONLY-NO-HOST-WRITE", pr.writes == [] and pr.opens > 0 and len(res2["incidents"]) > 0,
          f"opens probed={pr.opens} host writes={pr.writes[:3]}")


def gate_drift():
    base = Path(TMP) / "drift"
    mid = next(r["mission_id"] for r in ROWS if r.get("event") == "relay_held" and _is_loop_mission(r))
    led = copy_host(base, records=[fr._record_file(mid)], queue=False)
    pin_p = base / "pin.json"
    fr.pin(led, pin_p)
    pre = run_replay(pin_p)
    ctl = s3_of(pre)
    rec_p = base / fr._record_file(mid)
    d = json.loads(rec_p.read_text(encoding="utf-8"))
    d["edited_after_pin"] = True
    rec_p.write_text(json.dumps(d), encoding="utf-8")
    post = run_replay(pin_p)
    inc = [i for i in post["incidents"] if i["mission_id"] == mid and i["slice"] in ("S2", "S3", "S5")]
    check("V-S7-RECORD-DRIFT-UNMEASURED",
          ctl is not None and ctl["verdict"] != fr.UNMEASURED and inc and
          all(i["verdict"] == fr.UNMEASURED and i["reason"] == "record_changed_since_pin" for i in inc) and
          fr._record_file(mid) in post["record_drift"],
          f"before edit {ctl and ctl['verdict']}; after edit {[(i['slice'], i['verdict'], i['reason']) for i in inc]}")


def _is_loop_mission(r) -> bool:
    return any(l["mission_id"] == r["mission_id"] and l["count"] == 53 for l in fr.detect_loops(ROWS))


def gate_scope():
    keys = list(fr.SWITCHES) + list(fr.HELD)
    saved = {k: os.environ.get(k) for k in keys}
    try:
        for i, k in enumerate(keys):
            if i % 2:
                os.environ[k] = "sentinel-" + k
            else:
                os.environ.pop(k, None)
        prior = {k: os.environ.get(k) for k in keys}
        with fr.policy_scope("champion"):
            inside_c = {k: os.environ.get(k) for k in keys}
        after_ok = {k: os.environ.get(k) for k in keys} == prior
        try:
            with fr.policy_scope("challenger"):
                inside_h = {k: os.environ.get(k) for k in keys}
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        after_exc = {k: os.environ.get(k) for k in keys} == prior
        dirs = ["GSD_LONG_RUN_STATE_DIR", "PP_OWNER_QUEUE_STATE_DIR", "CPP_CLAUDE_EXE"]
        sand_prior = {k: os.environ.get(k) for k in dirs}
        with fr.sandbox() as root:
            in_root = os.environ["GSD_LONG_RUN_STATE_DIR"] == str(root)
        sand_after = {k: os.environ.get(k) for k in dirs} == sand_prior and not root.exists()
        diff = [k for k in fr.SWITCHES if inside_c[k] != "off" or inside_h[k] != "on"]
        held_eq = all(inside_c[k] == inside_h[k] == fr.HELD[k] for k in fr.HELD)
        check("V-S7-SCOPE-RESTORED", after_ok and after_exc and in_root and sand_after and not diff and held_eq,
              f"normal={after_ok} exception={after_exc} sandbox restored={sand_after} six switches differ, held equal={held_eq}")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def gate_tracer(res: dict):
    inc = s3_of(res)
    ok = (inc is not None and inc["champion"]["count"] > inc["challenger"]["count"] and
          inc["verdict"] in fr.VERDICTS and inc["basis"] in ("measured", "inferred") and
          inc["verdict"] == fr.PREVENTED)
    check("V-S7-TRACER-S3-DIFFERS", ok,
          f"champion {inc and inc['champion']['count']} hold rows / {inc and inc['champion']['status_calls']} GSD asks "
          f"vs challenger {inc and inc['challenger']['count']} / {inc and inc['challenger']['status_calls']}; "
          f"verdict {inc and inc['verdict']} ({inc and inc['basis']}); faithful {inc and inc['faithful']}")
    s2 = s2_of(res)
    mine = [r for r in ROWS if r.get("mission_id") == (s2 or {}).get("mission_id")]
    t = lambda ev: next((fr._epoch(r["ts"]) for r in mine if r.get("event") == ev), None)  # noqa: E731
    arm_t, blk_t = t("mission_prepared"), t("mission_blocked")
    # neighbour: the same real call with a status that has phases is not refused under the challenger
    with fr.sandbox() as root, fr.policy_scope("challenger"):
        okcase = gm.arm_preflight(str(root), "/gsd-autonomous", launch=False,
                                  status_reader=lambda c, w: {"outcome": "OK", "reason": "phases remain"})
    check("V-S7-TRACER-S2-REFUSES",
          s2 is not None and s2["challenger"]["ok"] is False and "NO_PHASES" in (s2["challenger"]["stop_reason"] or "")
          and s2["champion"]["ok"] is True and arm_t is not None and blk_t is not None and
          abs(s2["delta_s"] - (blk_t - arm_t)) < 1e-6 and okcase["ok"] is True and s2["verdict"] == fr.MOVED_EARLIER,
          f"challenger refuses '{s2 and s2['challenger']['stop_reason'][:60]}'; champion ok; delta {s2 and s2['delta_s']} s "
          f"= blocked - prepared; OK status is not refused; basis {s2 and s2['basis']}: {s2 and s2['assumption']}")


def gate_faithful():
    good, bad = fr.faithful(54, 54), fr.faithful(54, 20)
    inc = s3_of(RES())
    loop = next(l for l in fr.detect_loops(ROWS) if l["count"] == 53 and l["kind"] == "relay_held")
    real_drive = fr.s3_drive

    def unfaithful(lp, passes, cadence, arm):
        out = real_drive(lp, passes, cadence, arm)
        if arm == "champion":                      # a champion whose replay misses the recorded history
            out = dict(out, count=out["count"] // 3)
        return out

    fr.s3_drive = unfaithful
    try:
        seeded = fr.s3_incident(ROWS, loop, *fr.read_records(PN))
    finally:
        fr.s3_drive = real_drive
    check("V-S7-FAITHFUL-CONTROL", good["ok"] and not bad["ok"] and inc["verdict"] != fr.UNMEASURED and
          seeded["verdict"] == fr.UNMEASURED and seeded["reason"] == "replay_unfaithful" and seeded["faithful"]["ok"] is False,
          f"faithful(54,54)={good['ok']} faithful(54,20)={bad['ok']}; seeded champion {seeded['faithful']['champion_replay']} vs "
          f"recorded {seeded['faithful']['recorded']} -> {seeded['verdict']}/{seeded['reason']}; unseeded {inc['verdict']}")


def gate_realseam():
    counts = {"supervise": 0, "arm_preflight": 0}
    real_s, real_a = gm.supervise, gm.arm_preflight

    def cs(*a, **k):
        counts["supervise"] += 1
        return real_s(*a, **k)

    def ca(*a, **k):
        counts["arm_preflight"] += 1
        return real_a(*a, **k)

    gm.supervise, gm.arm_preflight = cs, ca
    try:
        res = run_replay(PIN)
    finally:
        gm.supervise, gm.arm_preflight = real_s, real_a
    defs = {n.name for n in ast.walk(ast.parse(SRC.read_text(encoding="utf-8"))) if isinstance(n, ast.FunctionDef)}
    banned = {"supervise", "arm_preflight", "plan_next", "judge", "reconcile", "dispose", "compile_blocker",
              "apply_rotation_invariant", "renewal_refusal"}
    check("V-S7-TRACER-REALSEAM", counts["supervise"] >= 2 and counts["arm_preflight"] >= 2 and not (defs & banned),
          f"supervise called {counts['supervise']}x, arm_preflight {counts['arm_preflight']}x, re-implemented defs: {sorted(defs & banned)}")
    return res




# ----------------------------------------------------------------------------------------- gates (Task 2)
def _ledger_rows() -> list[dict]:
    rows, _ = fr.read_prefix(fr.load_pin(PIN))
    return rows


def gate_discover(res: dict):
    import re
    rows = _ledger_rows()
    cov = res["coverage"]
    raw = sum(1 for r in rows if r.get("event") in fr.FAILURE_KINDS)
    check("V-S7-DISCOVER-COVERAGE", cov["sums_to_total"] and cov["failure_rows_total"] == raw and raw > 0
          and cov["mapped_to_slice"] + cov["unmapped"] == raw
          and set(cov["rows_by_event"]) == set(fr.FAILURE_KINDS),
          f"total={raw} mapped={cov['mapped_to_slice']} unmapped={cov['unmapped']} (recount from raw events)")
    src = SRC.read_text()
    check("V-S7-NO-IDS", not re.search(r"\bm-[0-9a-f]{12}\b", src), "no mission id literal in the tracer source")
    loops = cov["unmapped_loops"]
    se = [l for l in loops if l["kind"] == "supervise_error"]
    check("V-S7-UNMAPPED-LOOP", se and max(l["rows"] for l in se) >= 500 and all(l["carried_to"] == "Phase 8" for l in loops),
          f"supervise_error loop rows={max((l['rows'] for l in se), default=0)} listed, carried to Phase 8")
    gsd = fr.detect_loops([r for r in rows if r.get("event") == "relay_held"])
    mapped_loop = [l for l in fr.coverage(rows, gsd)["unmapped_loops"] if str(l["sample"]).startswith("gsd ")]
    check("V-S7-UNMAPPED-LOOP-NEIGHBOUR", not mapped_loop, "a gsd_hold loop (S3/S2) is NOT listed unmapped")
    cc = res["census_cross_check"]
    check("V-S7-CENSUS-DIFFERENCE-PRINTED", cc["difference"] == cc["mission_blocked_in_pin"] - 55
          and cc["source"] == "06-CENSUS.md", f"pin={cc['mission_blocked_in_pin']} snapshot=55")


def gate_slices(res: dict):
    import re
    inc = res["incidents"]
    s6 = [i for i in inc if i["slice"] == "S6"]
    typed = [i for i in s6 if i["challenger"] and i["challenger"].get("typed") and not i["champion"]["typed"]
             and i["challenger"].get("class") != "UNKNOWN"]
    check("V-S7-S6-CLASSED", len(typed) >= 10 and all(i["verdict"] == "LEGITIMATE_STOP" for i in typed),
          f"{len(typed)} blocks typed only by the challenger, via compile_blocker(cwd=None)")
    check("V-S7-S6-UNKNOWN-IS-UNCHANGED", any(i["verdict"] == "UNCHANGED" for i in s6)
          and all((i["challenger"] or {}).get("class") == "UNKNOWN" for i in s6 if i["verdict"] == "UNCHANGED"),
          "UNKNOWN is the neighbour of a typed class")
    s4 = [i for i in inc if i["slice"] == "S4"]
    stall = [i for i in s4 if i.get("trip_class") == "stall"]
    check("V-S7-S4-TRIP-NO-AUTH-LEGIT", stall and all(i["verdict"] == "LEGITIMATE_STOP" for i in stall),
          f"{len(stall)} stall groups stay trips in both arms")
    check("V-S7-S4-PREVENTED-NEEDS-AUTHORITY", all(i.get("trip_class") in ("variance", "authority_ceiling")
                                                    for i in s4 if i["verdict"] == "PREVENTED"),
          "only a variance trip with recorded authority can be prevented")
    base = [{"event": "authority_set", "mission_id": "x", "reason": "{'authority_tokens': 900000}"},
            {"event": "cost_breaker_tripped", "mission_id": "x", "ts": "2026-10-01T00:00:00+00:00", "spent": 500000,
             "estimate": 100000, "reason": "spent 500,000 tokens = 5.0 x estimate 100,000"}]
    miss = fr.s4_judge(base, 1)
    ctrl = fr.s4_judge([{"event": "breaker_receipt", "mission_id": "x", "fp": "f1", "mark": {"fp": "f1", "tokens": 1}}]
                       + base, 2)
    check("V-S7-S4-FP-MISSING-UNMEASURED", miss.get("unmeasured") == "fingerprint"
          and ctrl.get("unmeasured") != "fingerprint", f"no receipt -> {miss.get('unmeasured')}; with receipt -> "
                                                        f"{ctrl.get('unmeasured') or 'judged'}")
    s1 = [i for i in inc if i["slice"] == "S1"]
    check("V-S7-S1-EFFECT-UNMEASURED", s1 and all(i["verdict"] == "UNMEASURED" for i in s1)
          and {i["reason"] for i in s1} <= {"no_size_evidence", "inputs_incomplete"},
          f"{len(s1)} compaction groups never counted as prevented")
    s5 = res["s5"]
    check("V-S7-S5-NO-149H-CLAIM", "LAPTOP" in str(s5["quoted_not_measured"]).upper()
          and not any(re.search(r"\b149(\.\d+)?\s*h", json.dumps(i)) for i in inc), "quoted, never an incident claim")
    check("V-S7-S5-NOW-FIXED", s5["now"] == fr.load_pin(PIN)["last_ts"].replace("+00:00", "+00:00")
          or s5["now"][:19] == fr.load_pin(PIN)["last_ts"][:19], f"now={s5['now']} (the pin's last row)")
    ra = res["renewal_axis"]
    check("V-S7-RENEWAL-AXIS-LABELLED", ra["in_s2_s6_totals"] is False and "renewal" not in res["counts_by_slice"]
          and ra["axis"] == "renewal", f"{ra['halts_budget']} budget halts, own section, outside S2-S6 totals")
    check("V-S7-RENEWAL-OUTCOME-UNMEASURED", ra["unmeasured"] > 0 and "gsd_outcome" in ra["unmeasured_reasons"],
          "no recorded GSD outcome: named, not defaulted")
    seen = {}
    for arm in ("champion", "challenger"):
        with fr.policy_scope(arm):
            seen[arm] = {k: os.environ.get(k) for k in fr.HELD}
    check("V-S7-HELD-EQUAL", seen["champion"] == seen["challenger"] == fr.HELD
          and not set(fr.HELD) & set(fr.SWITCHES), "held group identical in both arms")
    before = {k: os.environ.get(k) for k in list(fr.SWITCHES) + list(fr.HELD)}
    with fr.policy_scope("challenger"):
        pass
    check("V-S7-HELD-RESTORED", before == {k: os.environ.get(k) for k in before})


def gate_verdicts(res: dict):
    f = fr
    stop = lambda t, r="named": {"count": None, "stops": True, "stop_ts": t, "stop_reason": r}  # noqa: E731
    nostop = {"count": None, "stops": False, "stop_ts": None, "stop_reason": None}
    cases = {
        "PREVENTED": (f.verdict({"count": 10, "stops": True, "stop_ts": 5, "stop_reason": "x"},
                                {"count": 2, "stops": False, "stop_ts": None, "stop_reason": None}),
                      f.verdict({"count": 10, "stops": False, "stop_ts": None, "stop_reason": None},
                                {"count": 9, "stops": False, "stop_ts": None, "stop_reason": None}), "UNCHANGED"),
        "MOVED_EARLIER": (f.verdict(stop(100, "a"), stop(40, "a")), f.verdict(stop(100, "a"), stop(100, "a")),
                          "LEGITIMATE_STOP"),
        "LEGITIMATE_STOP": (f.verdict(nostop, stop(None, "a")), f.verdict(nostop, nostop), "UNCHANGED"),
        "UNCHANGED": (f.verdict(nostop, nostop), f.verdict(nostop, stop(None, "a")), "LEGITIMATE_STOP"),
        "UNMEASURED": (f.verdict(None, None, unmeasured_reason="r"), f.verdict(nostop, nostop), "UNCHANGED"),
    }
    for name, (pos, neigh, nname) in cases.items():
        check(f"V-S7-VERDICT-POS-{name}", pos["verdict"] == name, pos["verdict"])
        check(f"V-S7-VERDICT-NEIGHBOUR-{name}", neigh["verdict"] == nname != name, f"neighbour -> {neigh['verdict']}")
    raised = False
    try:
        f.validate_verdict("MAYBE")
    except ValueError:
        raised = True
    check("V-S7-VERDICT-CLOSED", raised and all(i["verdict"] in f.VERDICTS for i in res["incidents"])
          and set(res["counts_by_verdict"]) == set(f.VERDICTS), "outside the set raises; every real incident inside")
    um = [i for i in res["incidents"] if i["verdict"] == "UNMEASURED"]
    check("V-S7-UNMEASURED-REACHABLE-REAL", len(um) >= 1 and res["counts_by_verdict"]["UNMEASURED"] == len(um),
          f"{len(um)} UNMEASURED incidents on the real ledger")
    prev = [i for i in res["incidents"] if i["verdict"] == "PREVENTED"]
    check("V-S7-UNMEASURED-NOT-PREVENTED", not any(i["basis"] == "unmeasured" for i in prev)
          and all(i["basis"] == "unmeasured" for i in um) and sum(res["counts_by_verdict"].values()) == len(res["incidents"]),
          "no unmeasured incident is counted prevented; counts partition the incidents")
    real = {v: res["counts_by_verdict"][v] for v in f.VERDICTS}
    check("V-S7-ALL-FIVE-REAL", all(real[v] > 0 for v in f.VERDICTS), str(real))


def gate_nonewstate():
    import re
    names = set(re.findall(r"CPP_[A-Z0-9_]+", SRC.read_text()))
    allowed = set(fr.SWITCHES) | set(fr.HELD) | {"CPP_CLAUDE_JOBS_DIR", "CPP_CLAUDE_EXE", "CPP_RESOURCE_ADMISSION"}
    check("V-S7-NO-NEW-STATE", names <= allowed, f"unknown CPP_ names: {sorted(names - allowed)}")


# ----------------------------------------------------------------------------------------- gates (Task 3)
def _iso_h(h: float) -> str:
    return fr._iso(1_790_000_000.0 + h * 3600)


def _row(h, mid, event, **kw):
    return {"ts": _iso_h(h), "session_id": mid, "mission_id": mid, "event": event, **kw}


def _constructed_time():
    """A 0-10 h, B 2-8 h (concurrent), C 12-20 h is A's renewed successor, D 30-31 h unrelated after an idle gap."""
    rows = []
    for mid, a, z in (("A", 0, 10), ("B", 2, 8), ("C", 12, 20), ("D", 30, 31)):
        rows.append(_row(a, mid, "launch_claimed", epoch=1, state="LAUNCHING"))
        if mid == "A":
            rows.append(_row(5, mid, "mission_renewed", successor="C"))
        rows.append(_row(z, mid, "mission_completed", epoch=1, state="COMPLETED", seq=9))
    rows.sort(key=lambda r: r["ts"])
    return rows


def gate_time():
    rows = _constructed_time()
    t = fr.time_accounting(rows, {})
    sm, wc, cp = (t["summed_mission_hours"]["hours"], t["wall_clock_hours"]["hours"],
                  t["critical_path_wall_clock_hours"]["hours"])
    check("V-S7-TIME-THREE-DISTINCT", (sm, wc, cp) == (25.0, 31.0, 20.0) and len({sm, wc, cp}) == 3,
          f"sum={sm} (10+6+8+1) wall={wc} (0..31) critical={cp} (A->C 0..20)")
    import ast
    tree = ast.parse(SRC.read_text())
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    names = ("summed_mission_hours", "wall_clock_hours", "critical_path_hours")
    cross = {a: {n.id for n in ast.walk(fns[a]) if isinstance(n, ast.Name)} & (set(names) - {a}) for a in names}
    check("V-S7-TIME-NEVER-CONFLATED", all(a in fns for a in names) and not any(cross.values())
          and len(t["definitions"]) == 3, f"cross-references: {cross}")
    open_rows = [r for r in rows if r["mission_id"] != "D"] + [_row(30, "E", "mission_prepared")]
    open_rows = [r for r in open_rows if not (r["mission_id"] == "B" and r["event"] == "launch_claimed")]
    # B now has a terminal row but no start row of its own: its first row IS the terminal row (zero length, measured);
    # the unmeasured case is a row with no parseable ts
    bad = open_rows + [{"ts": "not-a-time", "mission_id": "F", "event": "launch_claimed"}]
    w = fr.mission_windows(bad, fr._epoch(bad[-2]["ts"]))
    ts = fr.summed_mission_hours(w)
    check("V-S7-TIME-UNMEASURED-NOT-ZERO", "F" in ts["left_out"] and w["F"]["unmeasured"] and ts["open_at_pin"] >= 1,
          f"left_out={ts['left_out']}, open_at_pin={ts['open_at_pin']}")


def _idle_rows(hold: bool, worker: bool = True):
    rows = [_row(0, "M", "mission_prepared", epoch=0, state="PREPARED")] if worker else \
        [_row(0, "M", "launch_claimed", epoch=1, state="LAUNCHING")]
    if hold:
        rows.append(_row(0.5, "M", "owner_hold_set", reason="owner park", kind="owner"))
    rows.append(_row(1.5, "M", "launch_claimed", epoch=2, state="LAUNCHING"))
    return rows


def gate_idle(res: dict):
    calls = []
    real = fr._mods().plan_next

    def probe(*a, **k):
        calls.append(1)
        return real(*a, **k)
    pos = fr.avoidable_idle(_idle_rows(False), plan_next=probe)
    gap = [c for c in [fr.classify_gap(_idle_rows(False), g, probe) for g in fr.idle_gaps(_idle_rows(False))]]
    check("V-S7-IDLE-REALSEAM", len(calls) > 0 and "def plan_next" not in SRC.read_text(), f"plan_next called {len(calls)}x")
    check("V-S7-IDLE-AVOIDABLE-POS", gap and gap[0]["class"] == "avoidable" and gap[0]["plan_next"] in
          ("launch", "replace", "relay", "recover"), f"{gap[0].get('plan_next')}: {str(gap[0].get('reason'))[:80]}")
    neigh = [fr.classify_gap(_idle_rows(True), g) for g in fr.idle_gaps(_idle_rows(True))]
    check("V-S7-IDLE-LEGIT-NEIGHBOUR", neigh and neigh[0]["class"] == "legitimate" and neigh[0]["reason"],
          f"{neigh[0].get('plan_next')}: {str(neigh[0].get('reason'))[:80]}")
    inc = fr.avoidable_idle(_idle_rows(False, worker=False))
    check("V-S7-IDLE-INCOMPLETE", inc["by_class"]["inputs_incomplete"] == 1 and inc["unmeasured_h"] > 0
          and inc["avoidable_h_before"] == 0, f"unmeasured_h={inc['unmeasured_h']} avoidable_h={inc['avoidable_h_before']}")
    two = _idle_rows(False) + [{**r, "mission_id": "N", "session_id": "N"} for r in _idle_rows(False)]
    ba = fr.avoidable_idle(sorted(two, key=lambda r: r["ts"]), s2_missions={"M"})
    check("V-S7-IDLE-BEFORE-AFTER", ba["avoidable_h_after"] < ba["avoidable_h_before"] and ba["carried_unchanged"] >= 1
          and ba["moved"] and ba["moved"][0]["mission_id"] == "M",
          f"before={ba['avoidable_h_before']} after={ba['avoidable_h_after']}, N carried_unchanged")


def gate_s8():
    blk = lambda **kw: _row(1, "S", "mission_blocked", reason="x", **kw)  # noqa: E731
    none_found = fr.s8_sentence([blk(independent_work=False)])
    found = fr.s8_sentence([blk(independent_work=True)])
    empty = fr.s8_sentence([blk()])
    zero = fr.s8_sentence([])
    check("V-S7-S8-SENTENCE-FORMS", (found["form"], none_found["form"], empty["form"]) ==
          ("consumer_found", "none_found", "unmeasured") and zero["form"] == "unmeasured"
          and "W3" in empty["sentence"] and "W2" in empty["sentence"],
          "an empty measured population never yields the none-found form")
    import blocker_compiler as bc
    seen = []
    real = bc.compile_blocker
    bc.compile_blocker = lambda *a, **k: seen.append(k.get("cwd")) or real(*a, **k)
    try:
        fr.s8_sentence(_ledger_rows())
    finally:
        bc.compile_blocker = real
    check("V-S7-S8-NO-CWD-READ", not seen, f"compile_blocker calls during the S8 count: {len(seen)}")


def gate_report(res: dict):
    rows = _ledger_rows()
    records, _ = fr.read_records(fr.load_pin(PIN))
    rep = fr.build_report(res, rows, records)
    raised = False
    try:
        fr.validate_tagged({**rep, "stray": 7})
    except ValueError:
        raised = True
    try:
        broken = {**rep, "time": {"_tag": {"command": "", "pin_sha256": ""}, "data": {}}}
        fr.validate_tagged(broken)
        raised = False
    except ValueError:
        pass
    check("V-S7-REPORT-TAGGED", raised and all(v["_tag"]["command"] and v["_tag"]["pin_sha256"] == res["pin"]["sha256"]
                                               for v in rep.values() if isinstance(v, dict) and "_tag" in v),
          "an untagged number and an empty tag both raise; every section carries command and pin hash")
    vt = rep["verdict_totals"]["data"]
    check("V-S7-REPORT-UNMEASURED-APART", "UNMEASURED" not in vt["measured"]
          and vt["unmeasured_apart"] == res["counts_by_verdict"]["UNMEASURED"] > 0
          and sum(vt["measured"].values()) + vt["unmeasured_apart"] == len(res["incidents"]),
          f"measured={sum(vt['measured'].values())} apart={vt['unmeasured_apart']}")
    a = json.dumps(fr.build_report(res, rows, records), sort_keys=True, default=str)
    b = json.dumps(fr.build_report(run_replay(PIN), rows, records), sort_keys=True, default=str)
    check("V-S7-DETERMINISTIC", a == b and len(a) > 1000, f"two replays, {len(a)} bytes, byte-identical")
    md = fr.render_md(rep)
    check("V-S7-REPORT-MD", res["pin"]["sha256"] in md and "UNMEASURED (apart)" in md and "Time (three separate numbers)" in md)


# ----------------------------------------------------------------------------------------- FC-06 + mutants (07-02 task 1)
MUT_RESULTS: list[dict] = []


def _digests(res: dict) -> dict:
    return {i["id"]: i["effect_digest"] for i in res["incidents"] + res["seeded"]}


def gate_fc06(res: dict):
    st = res["fc06"]["selftest"]
    tab = res["fc06"]["table"]
    for gate, name in (("V-S7-FC06-CAPITAL", "capital_ceiling"), ("V-S7-FC06-DIGEST", "packet_digest"),
                       ("V-S7-FC06-DONE-PROOF", "done_proof"), ("V-S7-FC06-PROTECTIONS", "protections")):
        measured = tab[name]["host"]["clear"] + tab[name]["seeded"]["clear"]
        fired = [m["name"] for m in MUT_RESULTS if any(
            b["assertion"] == name for b in m.get("breach_list", []))]
        check(gate, st[name]["breach_fires"] and st[name]["clean_quiet"] and measured > 0 and fired,
              f"selftest={st[name]} measured_clear={measured} breach_under_mutants={fired}")
    check("V-S7-FC06-CHALLENGER-CLEAN", res["fc06"]["challenger_breaches"] == 0,
          f"challenger breaches={res['fc06']['challenger_breaches']}")
    good = dict(res)
    bad = dict(res, fc06=dict(res["fc06"], challenger_breaches=1,
                              host_breaches=[{"assertion": "capital_ceiling", "detail": "x"}], seeded_breaches=[]))
    rc_good, _ = fr.run_status(good, [])
    rc_bad, msgs = fr.run_status(bad, [])
    unc = fr.run_status(good, [{"name": "m", "harness_defect": False, "caught": False}])[0]
    dfc = fr.run_status(good, [{"name": "m", "harness_defect": True, "caught": False}])[0]
    check("V-S7-FC06-HARD-FAIL", rc_good == 0 and rc_bad == 3 and unc == 4 and dfc == 4 and msgs,
          f"clean={rc_good} breach={rc_bad} uncaught={unc} defect={dfc} (breach exits nonzero whatever the verdict totals)")


def _scoped_targets():
    return [(m, a, getattr(__import__(m, fromlist=["x"]), a)) for mu in fr.MUTANTS.values() for m, a, _ in mu["targets"]]


def gate_mutants(res: dict):
    src_before = sha(SRC)
    before = _scoped_targets()
    MUT_RESULTS.clear()
    for name in fr.MUTANTS:
        with fr.mutant_scope(name):
            r = fr.replay(PIN)
        m = fr.compare_mutant(name, res, r)
        m["stub_calls"] = dict(fr.MUTANT_CALLS)
        m["breach_list"] = [b for i in r["incidents"] + r["seeded"] for b in i["fc06"]["breaches"]]
        MUT_RESULTS.append(m)
    by = {m["name"]: m for m in MUT_RESULTS}
    for gate, name in (("V-S7-MUTANT-ALWAYS-ADMIT", "always-admit"), ("V-S7-MUTANT-NEVER-ROTATE", "never-rotate"),
                       ("V-S7-MUTANT-ALWAYS-RENEW", "always-renew"),
                       ("V-S7-MUTANT-TERMINAL-NO-PROOF", "terminal-without-proof"),
                       ("V-S7-MUTANT-DROP-CLASS", "drop-blocker-class"),
                       ("V-S7-MUTANT-EXPAND-AUTHORITY", "expand-authority")):
        m = by[name]
        check(gate, m["caught"] and not m["harness_defect"],
              f"caught_by={m['caught_by']} differing host={m['differing_host']} seeded={m['differing_seeded']} "
              f"fc06={m['fc06_breaches']} vs challenger {m['fc06_breaches_challenger']}")
    # identical replay is a named defect, never a pass: a stub that IS the original changes nothing
    fr.MUTANTS["noop-control"] = {"intent": "control", "targets": [("receipt_judge", "is_done", fr._originals()["is_done"])]}
    try:
        with fr.mutant_scope("noop-control"):
            r = fr.replay(PIN)
        nm = fr.compare_mutant("noop-control", res, r)
    finally:
        fr.MUTANTS.pop("noop-control", None)
    check("V-S7-MUTANT-IDENTICAL-IS-DEFECT", nm["harness_defect"] and not nm["caught"] and nm["caught_by"] == "none"
          and fr.run_status(res, [nm])[0] == 4 and all(not m["harness_defect"] for m in MUT_RESULTS),
          f"noop mutant defect={nm['harness_defect']} real mutants defect-free")
    after = _scoped_targets()
    check("V-S7-MUTANT-SCOPE-RESTORED", all(a[2] is b[2] for a, b in zip(before, after)),
          f"{len(after)} patched names restored to the identical objects")
    check("V-S7-MUTANT-NO-SOURCE-EDIT", src_before == sha(SRC), f"flow_replay.py sha256 {src_before[:12]} unchanged")
    check("V-S7-MUTANT-STUB-CALLED", all(sum(m["stub_calls"].values()) > 0 for m in MUT_RESULTS)
          and all(v > 0 for m in MUT_RESULTS for v in m["stub_calls"].values()),
          {m["name"]: sum(m["stub_calls"].values()) for m in MUT_RESULTS})


def gate_seeded_apart(res: dict):
    ids = {i["id"] for i in res["incidents"]}
    sd = res["seeded"]
    check("V-S7-SEEDED-APART",
          sd and all(s["constructed"] and s["section"] == "seeded" for s in sd)
          and not ids & {s["id"] for s in sd}
          and sum(res["counts_by_verdict"].values()) == len(res["incidents"])
          and all("verdict" not in s for s in sd),
          f"{len(sd)} seeded scenarios, none in the {len(ids)} host incidents or the verdict totals")
    again = fr.replay(PIN)
    check("V-S7-NO-REDEFINE-AFTER-MUTANTS", _digests(again) == _digests(res),
          "a replay after every mutant ran is digest-identical to the one before: nothing leaked")


GROUPS = {
    "pin": lambda: gate_pin(), "scope": lambda: gate_scope(),
    "tracer": lambda: gate_tracer(RES()), "faithful": lambda: gate_faithful(), "readonly": lambda: gate_readonly(),
    "drift": lambda: gate_drift(), "realseam": lambda: gate_realseam(), "discover": lambda: gate_discover(RES()),
    "slices": lambda: gate_slices(RES()), "verdicts": lambda: gate_verdicts(RES()),
    "nonewstate": lambda: gate_nonewstate(), "time": lambda: gate_time(), "idle": lambda: gate_idle(RES()),
    "s8": lambda: gate_s8(), "report": lambda: gate_report(RES()),
    "mutants": lambda: gate_mutants(RES()), "fc06": lambda: gate_fc06(RES()),
    "seeded": lambda: gate_seeded_apart(RES()),
}

# ----------------------------------------------------------------------------------------- negative controls (07-02 task 2d)
def gate_negcontrols():
    """Each control is run against the REAL reader and must produce the failing signal it exists to produce."""
    base = Path(TMP) / "neg"
    led = copy_host(base, records=[], queue=False)
    pn = fr.pin(led, base / "pin.json")
    raw = bytearray(led.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    (base / "flip.jsonl").write_bytes(bytes(raw))
    try:
        fr.read_prefix(dict(pn, ledger=str(base / "flip.jsonl")))
        sig = False
    except fr.Inconclusive:
        sig = True
    check("V-S7-NEGCONTROL-FLIPPED-BYTE", sig, "a flipped byte in the pinned prefix raises Inconclusive")
    loop = next(l for l in fr.detect_loops(ROWS) if l["count"] == 53 and l["kind"] == "relay_held")
    real = fr.s3_drive

    def unfaithful(lp, passes, cadence, arm):
        out = real(lp, passes, cadence, arm)
        return dict(out, count=out["count"] // 3) if arm == "champion" else out

    fr.s3_drive = unfaithful
    try:
        inc = fr.s3_incident(ROWS, loop, *fr.read_records(PN))
    finally:
        fr.s3_drive = real
    check("V-S7-NEGCONTROL-UNFAITHFUL", inc["verdict"] == fr.UNMEASURED and inc["reason"] == "replay_unfaithful",
          f"a champion replay far from the recorded count is {inc['verdict']}/{inc['reason']}")
    big = {"count": 10, "stops": True, "stop_ts": 5, "stop_reason": "x"}
    small = {"count": 1, "stops": False, "stop_ts": None, "stop_reason": None}
    um = fr.verdict(big, small, unmeasured_reason="named")
    check("V-S7-NEGCONTROL-UNMEASURED-NOT-PREVENTED", um["verdict"] == fr.UNMEASURED
          and fr.verdict(big, small)["verdict"] == fr.PREVENTED,
          "a 10 -> 1 drop with a named unmeasured reason stays UNMEASURED; without it the same pair is PREVENTED")
    e = fr.s8_sentence([])
    check("V-S7-NEGCONTROL-EMPTY-S8", e["form"] == "unmeasured" and e["recorded"] == 0,
          "an empty recorded population never yields the none-found form")
    try:
        fr.validate_tagged({"x": {"_tag": {"command": "", "pin_sha256": "a"}, "data": {}}})
        raised = False
    except ValueError:
        raised = True
    check("V-S7-NEGCONTROL-MISSING-COMMAND", raised, "a section whose command is empty is refused")
    st = fr.fc06_selftest()
    check("V-S7-NEGCONTROL-SEEDED-FC06", all(v["breach_fires"] and v["clean_quiet"] for v in st.values()) and len(st) == 4,
          f"all four FC-06 assertions fire on a seeded breach and stay quiet on the control: {st}")
    fr.MUTANTS["noop-neg"] = {"intent": "control", "targets": [("receipt_judge", "is_done", fr._originals()["is_done"])]}
    try:
        with fr.mutant_scope("noop-neg"):
            r = fr.replay(PIN)
        nm = fr.compare_mutant("noop-neg", RES(), r)
    finally:
        fr.MUTANTS.pop("noop-neg", None)
    check("V-S7-NEGCONTROL-IDENTICAL-STUB", nm["harness_defect"] and fr.run_status(RES(), [nm])[0] == 4,
          "a mutant whose stub is the real function replays identical and is named a HARNESS_DEFECT")


# ----------------------------------------------------------------------------------------- mutation drills (07-02 task 2)
# A drill mutates a TEMP COPY of flow_replay.py (one textual substitution, or a test-side instrument for the probe gate),
# imports it under another module name, points the global `fr` at it, re-runs the gate groups that hold the gates the
# mutation is mapped to, and requires each mapped gate red (absent or crashing counts red) AND green on the baseline.
import importlib.util  # noqa: E402

REAL_FR = fr
REAL_SRC = SRC
REAL_TEXT = SRC.read_text(encoding="utf-8")
VAR_DIR = Path(TMP) / "variants"
VARIANTS: list = []
_SEEN_FILE = "TOOLS = Path(__file__).resolve().parent"


MUTATIONS: dict[str, list[tuple[str, str]]] = {
    # pin and read-only
    "M-PIN-NO-HASH": [('if hashlib.sha256(data).hexdigest() != pn["sha256"]:', "if False:")],
    "M-PIN-READS-WHOLE": [("data = fh.read(n)\n    if len(data) != n:", "data = fh.read()\n    if False:"),
                          ('if hashlib.sha256(data).hexdigest() != pn["sha256"]:', "if False:")],
    "M-PIN-DROPS-ROW": [("    return _parse(data)\n\n\ndef read_records", "    _r, _t = _parse(data)\n    return _r[:-1], _t\n\n\ndef read_records")],
    "M-HELD-LEAKS": [("    with _env({**POLICIES[name], **HELD}):\n        yield\n",
                      "    os.environ.update({k: str(v) for k, v in {**POLICIES[name], **HELD}.items()})\n    yield\n")],
    "M-INCONCLUSIVE-EXITS-ZERO": [('print(f"INCONCLUSIVE: {exc}", file=sys.stderr)\n        return 2',
                                   'print(f"INCONCLUSIVE: {exc}", file=sys.stderr)\n        return 0')],
    "M-LEDGER-WRITE-MODE": [('with open(pn["ledger"], "rb") as fh:                # read-only, exactly the pinned length',
                             'with open(pn["ledger"], "r+b") as fh:')],
    "M-SANDBOX-STATE-NOT-REDIRECTED": [('    dirs["GSD_LONG_RUN_STATE_DIR"] = str(root)\n', "    dirs.pop('GSD_LONG_RUN_STATE_DIR', None)\n")],
    "M-DRIFT-READ-ANYWAY": [("if now != digest:", "if False:")],
    "M-ENV-NOT-RESTORED": [("    finally:\n        for k, v in prior.items():\n            if v is None:\n                os.environ.pop(k, None)\n            else:\n                os.environ[k] = v",
                            "    finally:\n        pass")],
    "M-SWITCH-MISSING": [('"champion": {k: "off" for k in SWITCHES}', '"champion": {k: "off" for k in SWITCHES if k != "CPP_GSD_HOLD_BACKOFF"}')],
    "M-HELD-DIFFERS": [("with _env({**POLICIES[name], **HELD}):", 'with _env({**POLICIES[name], **(HELD if name == "champion" else {})}):')],
    "M-CHAMPION-IS-CHALLENGER": [('"champion": {k: "off" for k in SWITCHES}', '"champion": {k: "on" for k in SWITCHES}')],
    "M-S2-OUTCOME-OK": [('status_reader=lambda c, w: {"outcome": outcome, "reason": why})', 'status_reader=lambda c, w: {"outcome": "OK", "reason": why})')],
    "M-FAITHFUL-DISABLED": [('"ok": dev <= tol}', '"ok": True}')],
    "M-REIMPLEMENT-SEAM": [("def effect_digest(champion, challenger) -> str:", "def plan_next(rec):\n    return {}\n\n\ndef effect_digest(champion, challenger) -> str:")],
    "M-LOOP-THRESHOLD": [("LOOP_MIN = 10 ", "LOOP_MIN = 100 ")],
    # discovery
    "M-COVERAGE-DROPS-ROW": [('"failure_rows_total": total,', '"failure_rows_total": total - 1,')],
    "M-HARDCODED-MISSION-ID": [('SCHEMA = "flow-replay/1"', 'SCHEMA = "flow-replay/1"\nSEED_MISSION = "m-0123456789ab"')],
    "M-LOOP-NOT-CARRIED": [('"sample": l["reason"][:160], "carried_to": "Phase 8",', '"sample": l["reason"][:160], "carried_to": None,')],
    "M-ALL-LOOPS-UNMAPPED": [("if c is None or not any(sl in SLICE_NAMES for sl in c[1]):\n            unmapped_loops", "if True:\n            unmapped_loops")],
    "M-CENSUS-DIFF-ZERO": [('"difference": now_n - 55,', '"difference": now_n - 54,')],
    # slices
    "M-S6-UNTYPED": [('he = {"typed": comp is not None,', 'he = {"typed": False,')],
    "M-S6-UNKNOWN-STOPS": [('"stop_reason": klass if klass and klass != bc.UNKNOWN else None}', '"stop_reason": klass or "unknown"}')],
    "M-S4-NO-STALL-CLASS": [('if "since the work tree last changed" in reason:\n        return "stall"', 'if "since the work tree last changed" in reason:\n        return "variance"')],
    "M-REDUCTION-ZERO": [("REDUCTION_MIN = 0.5 ", "REDUCTION_MIN = 0.0 ")],
    "M-REDUCTION-NEVER": [("REDUCTION_MIN = 0.5 ", "REDUCTION_MIN = 5.0 ")],
    "M-S4-FP-DEFAULTED": [('return {"class": klass, "unmeasured": "fingerprint"}', 'return {"class": klass, "unmeasured": "inputs_incomplete"}')],
    "M-S1-EFFECT-COUNTED": [('unmeasured_reason="no_size_evidence"),', "unmeasured_reason=None),")],
    "M-S5-QUOTE-DROPPED": [('"quoted_not_measured": rep["quoted_not_measured"],', '"quoted_not_measured": {},')],
    "M-S5-NOW-CLOCK": [('"now": _iso(now)}', '"now": _iso(time.time())}')],
    "M-RENEWAL-IN-TOTALS": [('"in_s2_s6_totals": False', '"in_s2_s6_totals": True')],
    "M-RENEWAL-OUTCOME-DEFAULTED": [('item["unmeasured"] = "gsd_outcome"', 'item["gsd_outcome"] = "OK"')],
    # verdicts
    "M-VERDICT-PREVENTED-UNREACHABLE": [("(cc - hc) / cc >= REDUCTION_MIN:", "(cc - hc) / cc >= 2:")],
    "M-VERDICT-PREVENTED-LOOSE": [("(cc - hc) / cc >= REDUCTION_MIN:", "(cc - hc) / cc > 0:")],
    "M-VERDICT-MOVED-INVERTED": [("and hs < cs:", "and hs > cs:")],
    "M-VERDICT-MOVED-LOOSE": [("and hs < cs:", "and hs <= cs:")],
    "M-VERDICT-LEGIT-OFF": [('if challenger.get("stops") and challenger.get("stop_reason"):', "if False:")],
    "M-VERDICT-LEGIT-ALWAYS": [('if challenger.get("stops") and challenger.get("stop_reason"):', "if True:")],
    "M-VERDICT-UNCHANGED-WRONG": [('out.update(verdict=UNCHANGED, reason="both arms behave the same")', 'out.update(verdict=LEGITIMATE_STOP, reason="both arms behave the same")')],
    "M-VERDICT-UNMEASURED-OFF": [("if unmeasured_reason or champion is None or challenger is None:", "if False:")],
    "M-VERDICT-UNMEASURED-ALWAYS": [("if unmeasured_reason or champion is None or challenger is None:", "if True:")],
    "M-VERDICT-UNMEASURED-AS-UNCHANGED": [('out.update(verdict=UNMEASURED, reason=unmeasured_reason or "inputs_incomplete", basis="unmeasured")', 'out.update(verdict=UNCHANGED, reason=unmeasured_reason or "inputs_incomplete", basis="unmeasured")')],
    "M-VERDICT-UNMEASURED-AS-PREVENTED": [('out.update(verdict=UNMEASURED, reason=unmeasured_reason or "inputs_incomplete", basis="unmeasured")', 'out.update(verdict=PREVENTED, reason=unmeasured_reason or "inputs_incomplete", basis="unmeasured")')],
    "M-VERDICT-NOT-VALIDATED": [("    if v not in VERDICTS:\n        raise ValueError", "    if False:\n        raise ValueError")],
    "M-VERDICT-SET-WIDENED": [("VERDICTS = (PREVENTED, MOVED_EARLIER, LEGITIMATE_STOP, UNCHANGED, UNMEASURED)", 'VERDICTS = (PREVENTED, MOVED_EARLIER, LEGITIMATE_STOP, UNCHANGED, UNMEASURED, "MAYBE")')],
    "M-NEW-STATE-VAR": [('SCHEMA = "flow-replay/1"', 'SCHEMA = "flow-replay/1"\n_NEW = os.environ.get("CPP_REPLAY_SECRET_STATE")')],
    # time
    "M-WALL-IS-SUM": [('"wall_clock_hours": wall_clock_hours(win, first, end),', '"wall_clock_hours": summed_mission_hours(win),')],
    "M-WALL-CALLS-SUM": [("    if first_launch is None or last_row is None:", "    _ = summed_mission_hours(windows)\n    if first_launch is None or last_row is None:")],
    "M-UNMEASURED-HOURS-ZERO": [('out[mid] = {"start": None, "end": None, "unmeasured": "no_start_in_prefix"}', 'out[mid] = {"start": 0.0, "end": 0.0, "unmeasured": None}')],
    # idle
    "M-IDLE-NO-PLAN-NEXT": [('ans = pn(rec, gap["start"] + 1.0, [], pid_alive=lambda p: False, blocked_probe=lambda *a: None)', 'ans = {"action": "launch", "reason": "stub"}')],
    "M-IDLE-NEVER-AVOIDABLE": [('if action in ("launch", "replace", "relay", "recover") and not rec.get("owner_hold") and not blocking:', "if False:")],
    "M-IDLE-HOLD-IGNORED": [('if action in ("launch", "replace", "relay", "recover") and not rec.get("owner_hold") and not blocking:', 'if True:')],
    "M-IDLE-INCOMPLETE-LEGIT": [('"class": "inputs_incomplete", "reason": "record not rebuildable from the ledger"}', '"class": "legitimate", "reason": "record not rebuildable from the ledger"}')],
    "M-IDLE-NO-S2-REMOVAL": [('c["class"] == "avoidable" and c["mission_id"] in s2', 'False')],
    # s8
    "M-S8-EMPTY-NONE-FOUND": [("    elif have:\n", "    elif True:\n")],
    "M-S8-READS-CWD": [('    blocked = [r for r in rows if r.get("event") == "mission_blocked"]\n    have', '    blocked = [r for r in rows if r.get("event") == "mission_blocked"]\n    import blocker_compiler as _bc\n    _bc.compile_blocker("x", cwd=".")\n    have')],
    # report
    "M-REPORT-NOT-VALIDATED": [('if not (isinstance(t, dict) and t.get("command") and t.get("pin_sha256")):', "if False:")],
    "M-REPORT-UNMEASURED-MERGED": [('for v in VERDICTS if v != UNMEASURED},', "for v in VERDICTS},")],
    "M-REPORT-NONDETERMINISTIC": [('"schema": "flow-replay-report/1",', '"schema": "flow-replay-report/1" + str(time.time_ns()),')],
    "M-REPORT-MD-LABEL": [("- UNMEASURED (apart):", "- UNMEASURED:")],
    # FC-06
    "M-FC06-CAPITAL-OFF": [('c = (inp or {}).get("capital")\n    if not c:', "c = None\n    if not c:")],
    "M-FC06-DIGEST-OFF": [('ds = (inp or {}).get("digests") or []', "ds = []")],
    "M-FC06-DONE-OFF": [('ds = (inp or {}).get("done") or []', "ds = []")],
    "M-FC06-PROTECT-OFF": [('rs = (inp or {}).get("resolved") or []', "rs = []")],
    "M-FC06-CHALLENGER-BREACH": [('"fc06_inputs": {"resolved": [{"text": reason, "owner_required": bool(comp["owner_required"])}]}}', '"fc06_inputs": {"resolved": [{"text": reason, "owner_required": False}]}}')],
    "M-FC06-BREACH-SOFT": [("        rc = 3\n", "        rc = 0\n")],
    # policy mutants
    "M-STUB-ALWAYS-ADMIT-REAL": [('("gsd_mission", "arm_preflight", mutant_admit_arm_preflight),', '("gsd_mission", "arm_preflight", lambda *a, **k: _originals()["arm_preflight"](*a, **k)),'),
                                 ('("gsd_mission", "_packet_digest_matches", mutant_admit_packet_digest)]},', '("gsd_mission", "_packet_digest_matches", lambda *a, **k: _originals()["_packet_digest_matches"](*a, **k))]},')],
    "M-STUB-NEVER-ROTATE-REAL": [('("gsd_mission", "apply_rotation_invariant", mutant_keep_rotation_invariant)]},', '("gsd_mission", "apply_rotation_invariant", lambda *a, **k: _originals()["apply_rotation_invariant"](*a, **k))]},')],
    "M-STUB-ALWAYS-RENEW-REAL": [('("gsd_mission", "renewal_refusal", mutant_renew_refusal)]},', '("gsd_mission", "renewal_refusal", lambda *a, **k: _originals()["renewal_refusal"](*a, **k))]},')],
    "M-STUB-TERMINAL-REAL": [('("receipt_judge", "is_done", mutant_proofless_is_done)]},', '("receipt_judge", "is_done", lambda *a, **k: _originals()["is_done"](*a, **k))]},')],
    "M-STUB-DROP-CLASS-REAL": [('("blocker_compiler", "compile_blocker", mutant_classless_compile_blocker)]},', '("blocker_compiler", "compile_blocker", lambda *a, **k: _originals()["compile_blocker"](*a, **k))]},')],
    "M-STUB-EXPAND-REAL": [('("mission_spend", "judge", mutant_never_trip_judge),', '("mission_spend", "judge", lambda *a, **k: _originals()["judge"](*a, **k)),'),
                           ('("modules.autonomy_gate.gate", "classify", mutant_never_owner_classify)]},', '("modules.autonomy_gate.gate", "classify", lambda *a, **k: _originals()["classify"](*a, **k))]},')],
    "M-IDENTICAL-NOT-DEFECT": [('"harness_defect": not caught}', '"harness_defect": False}')],
    "M-SCOPE-NOT-RESTORED": [("        for mod, attr, prev in reversed(saved):\n            setattr(mod, attr, prev)", "        pass")],
    "M-SOURCE-TOUCHED": [("    MUTANT_CALLS.clear()\n    saved = []", '    MUTANT_CALLS.clear()\n    Path(__file__).write_text(Path(__file__).read_text(encoding="utf-8") + "\\n# touched\\n", encoding="utf-8")\n    saved = []')],
    "M-STUB-NEVER-COUNTED": [("def _called(name: str) -> None:\n    MUTANT_CALLS[name] = MUTANT_CALLS.get(name, 0) + 1", "def _called(name: str) -> None:\n    pass")],
    "M-SEEDED-MERGED": [("    seeded = run_seeded()\n    for inc in incidents:", '    seeded = [dict(s, verdict="UNCHANGED") for s in run_seeded()]\n    for inc in incidents:')],
}

# test-side mutations: break the instrument the gate itself uses (the module under test is untouched)
TEST_SIDE = {}


def _probe_blind():
    global WriteProbe
    real = WriteProbe

    class Blind(real):
        def __enter__(self):
            self._saved = {}
            return self
    WriteProbe = Blind
    return real


def _ctx_probe_blind():
    global WriteProbe
    real = WriteProbe
    _probe_blind()
    try:
        yield
    finally:
        WriteProbe = real


TEST_SIDE["M-PROBE-BLIND"] = contextlib.contextmanager(_ctx_probe_blind)


def make_variant(mid: str, subs: list):
    text = REAL_TEXT.replace(_SEEN_FILE, f"TOOLS = Path({str(TOOLS)!r})", 1)
    for old, new in subs:
        if old not in text:
            raise ValueError(f"mutation {mid}: pattern not found: {old[:70]!r}")
        text = text.replace(old, new)
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    n = len(VARIANTS)
    path = VAR_DIR / f"flow_replay_v{n}.py"
    path.write_text(text, encoding="utf-8")
    name = f"flow_replay_v{n}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    VARIANTS.append(mod)
    return mod, path


def _real_targets():
    return [(m, a, getattr(__import__(m, fromlist=["x"]), a)) for mu in REAL_FR.MUTANTS.values() for m, a, _ in mu["targets"]]


@contextlib.contextmanager
def using(mod, path):
    """Point the gates at `mod`; afterwards put back the globals, the environment and every patched module attribute."""
    global fr, SRC
    prev, env, tg = (fr, SRC), dict(os.environ), _real_targets()
    fr, SRC = mod, path
    try:
        yield
    finally:
        fr, SRC = prev
        os.environ.clear()
        os.environ.update(env)
        for m, a, v in tg:
            setattr(__import__(m, fromlist=["x"]), a, v)


NEEDS = {"fc06": ["mutants"], "seeded": ["mutants"]}
GROUP_ORDER = ["pin", "scope", "tracer", "faithful", "readonly", "drift", "realseam", "discover", "slices", "verdicts",
               "nonewstate", "time", "idle", "s8", "report", "mutants", "fc06", "seeded", "negcontrols"]
GROUPS["negcontrols"] = lambda: gate_negcontrols()


def run_groups(names) -> dict:
    """Run gate groups in isolation against the module `fr` currently names; {gate: ok}. A group that raises reports the
    gates it never reached as absent (= red)."""
    want = []
    for n in sorted(set(names), key=GROUP_ORDER.index):
        for need in NEEDS.get(n, []):
            if need not in want:
                want.append(need)
        if n not in want:
            want.append(n)
    saved = RESULTS[:]
    RESULTS.clear()
    crashed = {}
    out_io = io.StringIO()
    with contextlib.redirect_stdout(out_io):
        for n in sorted(set(want), key=GROUP_ORDER.index):
            try:
                GROUPS[n]()
            except Exception as exc:  # noqa: BLE001 -- a crashing gate is a red gate
                crashed[n] = f"{type(exc).__name__}: {exc}"[:160]
    out = {g: ok for g, ok, _ in RESULTS}
    RESULTS[:] = saved
    out["__crashed__"] = crashed
    return out


def run_mutation(mid: str, groups) -> dict:
    if mid in TEST_SIDE:
        with using(fr, SRC), TEST_SIDE[mid]():
            return run_groups(groups)
    mod, path = make_variant(mid, MUTATIONS[mid])
    with using(mod, path):
        return run_groups(groups)


# gate -> mutations that must turn it red. Filled from the calibration matrix and checked by V-S7-MUTANT-MAP.
MUTANT_FOR: dict[str, list[str]] = {
    'V-S7-ALL-FIVE-REAL': ['M-S2-OUTCOME-OK', 'M-VERDICT-MOVED-INVERTED'],
    'V-S7-CENSUS-DIFFERENCE-PRINTED': ['M-CENSUS-DIFF-ZERO'],
    'V-S7-DETERMINISTIC': ['M-REPORT-NONDETERMINISTIC', 'M-S5-NOW-CLOCK'],
    'V-S7-DISCOVER-COVERAGE': ['M-COVERAGE-DROPS-ROW'],
    'V-S7-FAITHFUL-CONTROL': ['M-FAITHFUL-DISABLED', 'M-SWITCH-MISSING'],
    'V-S7-FC06-CAPITAL': ['M-FC06-CAPITAL-OFF'],
    'V-S7-FC06-CHALLENGER-CLEAN': ['M-FC06-CHALLENGER-BREACH'],
    'V-S7-FC06-DIGEST': ['M-FC06-DIGEST-OFF', 'M-STUB-ALWAYS-ADMIT-REAL'],
    'V-S7-FC06-DONE-PROOF': ['M-FC06-DONE-OFF', 'M-STUB-TERMINAL-REAL'],
    'V-S7-FC06-HARD-FAIL': ['M-FC06-BREACH-SOFT', 'M-FC06-CHALLENGER-BREACH'],
    'V-S7-FC06-PROTECTIONS': ['M-FC06-PROTECT-OFF'],
    'V-S7-HELD-EQUAL': ['M-HELD-DIFFERS'],
    'V-S7-IDLE-AVOIDABLE-POS': ['M-IDLE-NEVER-AVOIDABLE'],
    'V-S7-IDLE-BEFORE-AFTER': ['M-IDLE-NEVER-AVOIDABLE', 'M-IDLE-NO-S2-REMOVAL'],
    'V-S7-IDLE-INCOMPLETE': ['M-IDLE-INCOMPLETE-LEGIT'],
    'V-S7-IDLE-LEGIT-NEIGHBOUR': ['M-IDLE-HOLD-IGNORED'],
    'V-S7-IDLE-REALSEAM': ['M-IDLE-NO-PLAN-NEXT', 'M-REIMPLEMENT-SEAM'],
    'V-S7-MUTANT-ALWAYS-ADMIT': ['M-STUB-ALWAYS-ADMIT-REAL'],
    'V-S7-MUTANT-ALWAYS-RENEW': ['M-STUB-ALWAYS-RENEW-REAL'],
    'V-S7-MUTANT-DROP-CLASS': ['M-STUB-DROP-CLASS-REAL'],
    'V-S7-MUTANT-EXPAND-AUTHORITY': ['M-STUB-EXPAND-REAL'],
    'V-S7-MUTANT-IDENTICAL-IS-DEFECT': ['M-IDENTICAL-NOT-DEFECT', 'M-STUB-ALWAYS-RENEW-REAL'],
    'V-S7-MUTANT-NEVER-ROTATE': ['M-STUB-NEVER-ROTATE-REAL'],
    'V-S7-MUTANT-NO-SOURCE-EDIT': ['M-SOURCE-TOUCHED'],
    'V-S7-MUTANT-SCOPE-RESTORED': ['M-SCOPE-NOT-RESTORED'],
    'V-S7-MUTANT-STUB-CALLED': ['M-STUB-ALWAYS-RENEW-REAL', 'M-STUB-NEVER-COUNTED'],
    'V-S7-MUTANT-TERMINAL-NO-PROOF': ['M-STUB-TERMINAL-REAL'],
    'V-S7-NEGCONTROL-EMPTY-S8': ['M-S8-EMPTY-NONE-FOUND'],
    'V-S7-NEGCONTROL-FLIPPED-BYTE': ['M-PIN-NO-HASH', 'M-PIN-READS-WHOLE'],
    'V-S7-NEGCONTROL-IDENTICAL-STUB': ['M-IDENTICAL-NOT-DEFECT', 'M-SCOPE-NOT-RESTORED'],
    'V-S7-NEGCONTROL-MISSING-COMMAND': ['M-REPORT-NOT-VALIDATED'],
    'V-S7-NEGCONTROL-SEEDED-FC06': ['M-FC06-CAPITAL-OFF', 'M-FC06-DIGEST-OFF'],
    'V-S7-NEGCONTROL-UNFAITHFUL': ['M-FAITHFUL-DISABLED', 'M-VERDICT-UNMEASURED-OFF'],
    'V-S7-NEGCONTROL-UNMEASURED-NOT-PREVENTED': ['M-REDUCTION-NEVER', 'M-VERDICT-UNMEASURED-OFF'],
    'V-S7-NO-IDS': ['M-HARDCODED-MISSION-ID'],
    'V-S7-NO-NEW-STATE': ['M-NEW-STATE-VAR'],
    'V-S7-NO-REDEFINE-AFTER-MUTANTS': ['M-SCOPE-NOT-RESTORED'],
    'V-S7-READONLY-NO-HOST-WRITE': ['M-LEDGER-WRITE-MODE', 'M-PROBE-BLIND'],
    'V-S7-READONLY-PROBE-FIRES': ['M-PROBE-BLIND'],
    'V-S7-RECORD-DRIFT-UNMEASURED': ['M-DRIFT-READ-ANYWAY', 'M-SWITCH-MISSING'],
    'V-S7-RENEWAL-AXIS-LABELLED': ['M-RENEWAL-IN-TOTALS'],
    'V-S7-RENEWAL-OUTCOME-UNMEASURED': ['M-RENEWAL-OUTCOME-DEFAULTED'],
    'V-S7-REPORT-MD': ['M-REPORT-MD-LABEL'],
    'V-S7-REPORT-TAGGED': ['M-REPORT-NOT-VALIDATED'],
    'V-S7-REPORT-UNMEASURED-APART': ['M-REPORT-UNMEASURED-MERGED', 'M-VERDICT-UNMEASURED-AS-UNCHANGED'],
    'V-S7-S1-EFFECT-UNMEASURED': ['M-S1-EFFECT-COUNTED', 'M-VERDICT-UNMEASURED-AS-UNCHANGED'],
    'V-S7-S4-FP-MISSING-UNMEASURED': ['M-S4-FP-DEFAULTED'],
    'V-S7-S4-PREVENTED-NEEDS-AUTHORITY': ['M-REDUCTION-ZERO'],
    'V-S7-S4-TRIP-NO-AUTH-LEGIT': ['M-REDUCTION-ZERO', 'M-S4-NO-STALL-CLASS'],
    'V-S7-S5-NO-149H-CLAIM': ['M-S5-QUOTE-DROPPED'],
    'V-S7-S5-NOW-FIXED': ['M-S5-NOW-CLOCK'],
    'V-S7-S6-CLASSED': ['M-S6-UNTYPED', 'M-VERDICT-MOVED-LOOSE'],
    'V-S7-S6-UNKNOWN-IS-UNCHANGED': ['M-S6-UNKNOWN-STOPS', 'M-VERDICT-MOVED-LOOSE'],
    'V-S7-S8-NO-CWD-READ': ['M-S8-READS-CWD'],
    'V-S7-S8-SENTENCE-FORMS': ['M-S8-EMPTY-NONE-FOUND'],
    'V-S7-SCOPE-RESTORED': ['M-ENV-NOT-RESTORED', 'M-HELD-LEAKS', 'M-SANDBOX-STATE-NOT-REDIRECTED'],
    'V-S7-SEEDED-APART': ['M-SEEDED-MERGED'],
    'V-S7-TIME-NEVER-CONFLATED': ['M-WALL-CALLS-SUM'],
    'V-S7-TIME-THREE-DISTINCT': ['M-WALL-IS-SUM'],
    'V-S7-TIME-UNMEASURED-NOT-ZERO': ['M-UNMEASURED-HOURS-ZERO'],
    'V-S7-TRACER-PIN-COMMITTED-VERIFIES': ['M-PIN-DROPS-ROW', 'M-PIN-READS-WHOLE'],
    'V-S7-TRACER-PIN-FLIPPED-BYTE': ['M-INCONCLUSIVE-EXITS-ZERO', 'M-PIN-NO-HASH'],
    'V-S7-TRACER-PIN-STABLE': ['M-PIN-DROPS-ROW', 'M-PIN-READS-WHOLE'],
    'V-S7-TRACER-REALSEAM': ['M-LOOP-THRESHOLD', 'M-REIMPLEMENT-SEAM'],
    'V-S7-TRACER-S2-REFUSES': ['M-CHAMPION-IS-CHALLENGER', 'M-LOOP-THRESHOLD'],
    'V-S7-TRACER-S3-DIFFERS': ['M-LOOP-THRESHOLD', 'M-REDUCTION-NEVER'],
    'V-S7-UNMAPPED-LOOP': ['M-LOOP-NOT-CARRIED'],
    'V-S7-UNMAPPED-LOOP-NEIGHBOUR': ['M-ALL-LOOPS-UNMAPPED'],
    'V-S7-UNMEASURED-NOT-PREVENTED': ['M-VERDICT-UNMEASURED-AS-PREVENTED'],
    'V-S7-UNMEASURED-REACHABLE-REAL': ['M-VERDICT-UNMEASURED-AS-PREVENTED', 'M-VERDICT-UNMEASURED-AS-UNCHANGED'],
    'V-S7-VERDICT-CLOSED': ['M-VERDICT-NOT-VALIDATED', 'M-VERDICT-SET-WIDENED'],
    'V-S7-VERDICT-NEIGHBOUR-LEGITIMATE_STOP': ['M-VERDICT-LEGIT-ALWAYS', 'M-VERDICT-UNCHANGED-WRONG'],
    'V-S7-VERDICT-NEIGHBOUR-MOVED_EARLIER': ['M-VERDICT-LEGIT-OFF', 'M-VERDICT-MOVED-LOOSE'],
    'V-S7-VERDICT-NEIGHBOUR-PREVENTED': ['M-REDUCTION-ZERO', 'M-VERDICT-PREVENTED-LOOSE'],
    'V-S7-VERDICT-NEIGHBOUR-UNCHANGED': ['M-VERDICT-LEGIT-OFF', 'M-VERDICT-UNMEASURED-ALWAYS'],
    'V-S7-VERDICT-NEIGHBOUR-UNMEASURED': ['M-VERDICT-LEGIT-ALWAYS', 'M-VERDICT-UNCHANGED-WRONG'],
    'V-S7-VERDICT-POS-LEGITIMATE_STOP': ['M-VERDICT-LEGIT-OFF', 'M-VERDICT-UNMEASURED-ALWAYS'],
    'V-S7-VERDICT-POS-MOVED_EARLIER': ['M-VERDICT-MOVED-INVERTED', 'M-VERDICT-UNMEASURED-ALWAYS'],
    'V-S7-VERDICT-POS-PREVENTED': ['M-REDUCTION-NEVER', 'M-VERDICT-PREVENTED-UNREACHABLE'],
    'V-S7-VERDICT-POS-UNCHANGED': ['M-VERDICT-LEGIT-ALWAYS', 'M-VERDICT-UNCHANGED-WRONG'],
    'V-S7-VERDICT-POS-UNMEASURED': ['M-VERDICT-UNMEASURED-AS-PREVENTED', 'M-VERDICT-UNMEASURED-AS-UNCHANGED'],
}
UNMUTATED: dict[str, str] = {
    "V-S7-HELD-RESTORED": "an env leak persists after its first occurrence, so this before/after cannot see a leak that an earlier call already made; the restore itself is pinned red by V-S7-SCOPE-RESTORED under M-HELD-LEAKS",
    "V-S7-READONLY-COPY-IDENTICAL": "its subject is the temp copy tree, which no flow_replay line targets; its in-gate control (an implicit-accessor append must read as a change) is what proves it can fail, and V-S7-READONLY-PROBE-FIRES is drilled by M-PROBE-BLIND",
}


def drills(base: dict, group_of: dict) -> None:
    mids = sorted({m for ms in MUTANT_FOR.values() for m in ms})
    for mid in mids:
        expected = sorted(g for g, ms in MUTANT_FOR.items() if mid in ms)
        groups = sorted({group_of[g] for g in expected if g in group_of}, key=GROUP_ORDER.index)
        try:
            got = run_mutation(mid, groups)
        except Exception as exc:  # noqa: BLE001 -- a mutation that cannot be applied is a failed drill
            check(f"V-S7-DRILL-{mid}", False, f"mutation not applicable: {type(exc).__name__}: {exc}")
            continue
        still_green = [g for g in expected if got.get(g) is True]
        never_green = [g for g in expected if base.get(g) is not True]
        check(f"V-S7-DRILL-{mid}", bool(expected) and not still_green and not never_green,
              f"expected_red={len(expected)} still_green={still_green} baseline_not_green={never_green} "
              f"crashed={list(got['__crashed__'])}")


def drill_control(base: dict, group_of: dict) -> None:
    """The harness itself must be able to fail: with every mutation replaced by a no-op, every mapped gate stays green,
    which each drill reads as a failed drill. If this does not hold, the drills above prove nothing."""
    expected = sorted(MUTANT_FOR)
    groups = sorted({group_of[g] for g in expected if g in group_of}, key=GROUP_ORDER.index)
    with using(*make_variant("noop", [])):
        got = run_groups(groups)
    still_green = [g for g in expected if got.get(g) is True]
    mids = sorted({m for ms in MUTANT_FOR.values() for m in ms})
    would_fail = [m for m in mids
                  if not [g for g, ms in MUTANT_FOR.items() if m in ms and got.get(g) is not True]]
    check("V-S7-DRILL-CONTROL-NOOP-FIRES", bool(expected) and len(still_green) == len(expected) and len(would_fail) == len(mids),
          f"no-op substitution left {len(still_green)}/{len(expected)} mapped gates green: all {len(would_fail)}/{len(mids)} "
          f"drills would read it as a failure")


def map_gate(names: list) -> None:
    gate_names = [n for n in names if not n.startswith("V-S7-DRILL-") and n != "V-S7-MUTANT-MAP"]
    unmapped = [n for n in gate_names if n not in MUTANT_FOR and n not in UNMUTATED]
    stale = [g for g in MUTANT_FOR if g not in gate_names]
    undefined = sorted({m for ms in MUTANT_FOR.values() for m in ms if m not in MUTATIONS and m not in TEST_SIDE})
    unused = sorted(m for m in list(MUTATIONS) + list(TEST_SIDE) if not any(m in ms for ms in MUTANT_FOR.values()))
    check("V-S7-MUTANT-MAP", not unmapped and not stale and not undefined and not unused and len(gate_names) >= 80,
          f"unmapped={unmapped} stale={stale} undefined={undefined} unused={unused} gates={len(gate_names)} "
          f"unmutated={sorted(UNMUTATED)}")


def main() -> int:
    real_before = sha(REAL_SRC)
    group_of = {}
    for name in GROUP_ORDER:
        before = len(RESULTS)
        GROUPS[name]()
        for n, _, _ in RESULTS[before:]:
            group_of[n] = name
    base = {n: ok for n, ok, _ in RESULTS}
    if len(sys.argv) > 2 and sys.argv[1] == "--calibrate":
        mid = sys.argv[2]
        got = run_mutation(mid, list(GROUP_ORDER))
        red = sorted(g for g in group_of if got.get(g) is False and base.get(g) is True)
        absent = sorted(g for g in group_of if g not in got and base.get(g) is True)
        print("CALIBRATE", json.dumps({"mutation": mid, "red": red, "all": sorted(group_of), "absent": len(absent), "crashed": got["__crashed__"]}, default=str))
        shutil.rmtree(TMP, ignore_errors=True)
        return 0
    drills(base, group_of)
    drill_control(base, group_of)
    check("V-S7-DRILL-REAL-FILE-UNTOUCHED", sha(REAL_SRC) == real_before and REAL_TEXT == REAL_SRC.read_text(encoding="utf-8"),
          f"tools/flow_replay.py sha256 {real_before[:12]} identical before and after {len(VARIANTS)} mutated copies")
    map_gate(list(group_of))
    n = len(RESULTS)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    for name, ok, ev in RESULTS:
        if not ok:
            print(f"FAIL {name} {ev}")
    print(f"S7_PASS={p}/{n}  threshold={n}/{n}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if p == n else 1


if __name__ == "__main__":
    sys.exit(main())
