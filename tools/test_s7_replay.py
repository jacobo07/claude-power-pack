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
    probe_dir.mkdir()
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
    inc = s3_of(res_main)
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


res_main: dict = {}


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
    import flow_replay as f
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


def main() -> int:
    global res_main
    gate_pin()
    gate_scope()
    res_main = run_replay(PIN)
    gate_tracer(res_main)
    gate_faithful()
    gate_readonly()
    gate_drift()
    gate_realseam()
    gate_discover(res_main)
    gate_slices(res_main)
    gate_verdicts(res_main)
    gate_nonewstate()
    gate_time()
    gate_idle(res_main)
    gate_s8()
    gate_report(res_main)
    n = len(RESULTS)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"S7_PASS={p}/{n}  threshold={n}/{n}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if p == n else 1


if __name__ == "__main__":
    sys.exit(main())
