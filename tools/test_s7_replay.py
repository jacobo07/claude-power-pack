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
    inc = [i for i in post["incidents"] if i["mission_id"] == mid]
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
    n = len(RESULTS)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"S7_PASS={p}/{n}  threshold={n}/{n}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if p == n else 1


if __name__ == "__main__":
    sys.exit(main())
