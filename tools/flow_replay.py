#!/usr/bin/env python3
"""S7 historical replay + champion/challenger (flow-compression Phase 7, FC-01/FC-09/FC-10/FC-11).

Replays a hash-pinned byte prefix of the host ledger twice -- champion (the six S1-S6 kill switches off) and
challenger (on) -- through the functions that really make each decision, and classifies every discovered incident
into the closed verdict set. Read-only: the ledger is opened binary read-only from the pin, every seam that writes
runs in a harness temp directory, and no switch, state, event or policy is added (FC-10).

  python3 tools/flow_replay.py pin    --ledger PATH --out PIN.json
  python3 tools/flow_replay.py replay --pin PIN.json [--json OUT] [--md OUT]

Exit 0 on a measured run, exit 2 when the pin does not verify (INCONCLUSIVE, never a pass).
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

SCHEMA = "flow-replay/1"

# --- the two policies (D-02). Verified spellings; each reader was read once to pick the value it treats as on. ----
#   S1 rotation_invariant_enabled: != "off"      S2 arm_preflight_on: != "off"        S3 gsd_backoff_on: != "off"
#   S4 mission_spend.lease_on:     != "off"      S5 (gsd_mission, annotation): != "off"
#   S6 blocker_compile_on:         not in ("0", "off", "false")
SWITCHES = {
    "CPP_ROTATION_INVARIANT": "S1",
    "CPP_ARM_PREFLIGHT": "S2",
    "CPP_GSD_HOLD_BACKOFF": "S3",
    "CPP_ECON_LEASE": "S4",
    "CPP_TERMINAL_RECONCILE": "S5",
    "CPP_BLOCKER_COMPILE": "S6",
}
POLICIES = {"champion": {k: "off" for k in SWITCHES}, "challenger": {k: "on" for k in SWITCHES}}
# Older mission features (premise correction 1): one recorded value in BOTH arms so they cannot pose as S2-S6 gains.
HELD = {"CPP_CCR_ADMISSION": "observe", "CPP_MISSION_RENEW": "on", "CPP_MISSION_BOUNDED_RENEWAL": "shadow"}
# State redirection for every seam that writes. All of these names are read by the repo's own tools.
REDIRECT_DIRS = ("GSD_LONG_RUN_STATE_DIR", "GSD_LONG_RUN_SESSIONS_DIR", "GSD_AUTORUN_MARKER_DIR", "CPP_CLAUDE_JOBS_DIR",
                 "GSD_LONG_RUN_PROJECTS_DIR", "PP_OWNER_QUEUE_STATE_DIR", "CLAUDE_CONFIG_DIR")
REDIRECT_FIXED = {"CPP_CLAUDE_EXE": "__no_such_claude_in_replay__", "CPP_RESOURCE_ADMISSION": "off"}

LOOP_MIN = 10          # a run of this many identical outcomes is an incident candidate
REDUCTION_MIN = 0.5    # discretionary: a challenger count this much lower than the champion's is PREVENTED
FAITHFUL_TOL = 0.10    # discretionary: a champion replay further than this from the recorded count is unfaithful
PASS_CAP = 400         # per-incident supervise pass cap (T-07-08)

PREVENTED, MOVED_EARLIER, LEGITIMATE_STOP, UNCHANGED, UNMEASURED = (
    "PREVENTED", "MOVED_EARLIER", "LEGITIMATE_STOP", "UNCHANGED", "UNMEASURED")
VERDICTS = (PREVENTED, MOVED_EARLIER, LEGITIMATE_STOP, UNCHANGED, UNMEASURED)


class Inconclusive(Exception):
    """The pin does not verify: nothing was judged, and that is never a pass."""


# ---------------------------------------------------------------------------------------------------- time
def _epoch(ts) -> float | None:
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        return _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _iso(t: float | None) -> str | None:
    return None if t is None else _dt.datetime.fromtimestamp(t, _dt.timezone.utc).isoformat(timespec="seconds")


def _mid(row: dict) -> str | None:
    return row.get("mission_id") or row.get("session_id")


# ---------------------------------------------------------------------------------------------------- pin
def _cut(data: bytes) -> bytes:
    """The longest prefix that ends on a newline: a torn tail line is never part of a pin."""
    i = data.rfind(b"\n")
    return data[:i + 1] if i >= 0 else b""


def _parse(data: bytes) -> tuple[list[dict], int]:
    rows, torn = [], 0
    for line in data.decode("utf-8-sig", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            torn += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            torn += 1
    return rows, torn


def pin(ledger: str | Path, out: str | Path | None = None, command: str | None = None) -> dict:
    """Pin the current ledger: path, byte length (ends on a newline), row count, sha256 of exactly those bytes, and the
    sha256 of every host mission record beside it. Reads only; the one file written is `out`."""
    ledger = Path(ledger)
    with open(ledger, "rb") as fh:                      # binary read-only: the only way this module opens the ledger
        data = _cut(fh.read())
    rows, torn = _parse(data)
    ts = [t for t in (_epoch(r.get("ts")) for r in rows) if t is not None]
    recs = {}
    for p in sorted(ledger.parent.glob("gsd-mission-*.json")):
        with open(p, "rb") as fh:
            recs[p.name] = hashlib.sha256(fh.read()).hexdigest()
    doc = {"schema": SCHEMA, "ledger": str(ledger), "bytes": len(data), "rows": len(rows), "torn": torn,
           "sha256": hashlib.sha256(data).hexdigest(), "first_ts": _iso(min(ts)) if ts else None,
           "last_ts": _iso(max(ts)) if ts else None, "missions_dir": str(ledger.parent), "mission_records": recs,
           "command": command or f"python3 tools/flow_replay.py pin --ledger {ledger} --out {out}",
           "pinned_at": _iso(time.time())}
    if out:
        Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def load_pin(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_prefix(pn: dict) -> tuple[list[dict], int]:
    """(rows, torn) of EXACTLY the pinned bytes, or Inconclusive. Rows appended after the pin cannot change a verdict."""
    n = int(pn["bytes"])
    with open(pn["ledger"], "rb") as fh:                # read-only, exactly the pinned length
        data = fh.read(n)
    if len(data) != n:
        raise Inconclusive(f"ledger shorter than the pin: {len(data)} < {n} bytes")
    if hashlib.sha256(data).hexdigest() != pn["sha256"]:
        raise Inconclusive("pinned prefix does not hash to the pin")
    return _parse(data)


def read_records(pn: dict) -> tuple[dict, dict]:
    """(records, drift): host mission records whose bytes still match the pin, and the ones that do not.
    A drifted record is never parsed: what it says now is not what it said at the pin."""
    recs, drift = {}, {}
    base = Path(pn["missions_dir"])
    for name, digest in sorted((pn.get("mission_records") or {}).items()):
        try:
            with open(base / name, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            drift[name] = {"pinned": digest, "now": None, "why": f"unreadable: {type(exc).__name__}"}
            continue
        now = hashlib.sha256(raw).hexdigest()
        if now != digest:
            drift[name] = {"pinned": digest, "now": now, "why": "record_changed_since_pin"}
            continue
        try:
            rec = json.loads(raw.decode("utf-8"))
        except ValueError:
            drift[name] = {"pinned": digest, "now": now, "why": "unparseable"}
            continue
        if isinstance(rec, dict) and rec.get("mission_id"):
            recs[rec["mission_id"]] = rec
    return recs, drift


def _record_file(mission_id: str) -> str:
    return f"gsd-mission-{mission_id}.json"


# ---------------------------------------------------------------------------------------------------- scopes
@contextlib.contextmanager
def _env(values: dict):
    """Set env values for the block and restore the exact prior state (absent stays absent) in a finally."""
    prior = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items():
            os.environ[k] = v
        yield
    finally:
        for k, v in prior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def policy_scope(name: str):
    """The six S1-S6 switches of `name` plus the HELD group at one value, restored in a finally block."""
    if name not in POLICIES:
        raise ValueError(f"unknown policy {name!r}")
    with _env({**POLICIES[name], **HELD}):
        yield


@contextlib.contextmanager
def sandbox():
    """A harness-owned temp directory that every state accessor of the repo's tools is redirected to. The host
    state directory is never reachable from inside: the pin, not an accessor, names the host paths."""
    root = Path(tempfile.mkdtemp(prefix="flow-replay-"))
    dirs = {k: str(root / k.lower()) for k in REDIRECT_DIRS}
    dirs["GSD_LONG_RUN_STATE_DIR"] = str(root)
    try:
        with _env({**dirs, **REDIRECT_FIXED}):
            yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _mods():
    """The real decision modules. First imported inside a sandbox, so no import-time path points at the host."""
    import gsd_mission as gm
    return gm


# ---------------------------------------------------------------------------------------------------- discovery
_NUM = re.compile(r"\d+")


def norm_reason(reason) -> str:
    return _NUM.sub("#", str(reason or "")).strip().lower()[:240]


def detect_loops(rows: list[dict], loop_min: int = LOOP_MIN) -> list[dict]:
    """Generic repeated-outcome detector, mission ids never named: consecutive rows of one event kind on one mission
    with one normalised reason, at least `loop_min` long. Rows of other kinds interleaved in between do not break it
    (a mission_blocked row sits inside the relay_held run it ends)."""
    seq: dict[tuple, list[tuple[int, dict]]] = {}
    for i, r in enumerate(rows):
        ev, mid = r.get("event"), _mid(r)
        if ev and mid:
            seq.setdefault((mid, ev), []).append((i, r))
    loops = []
    for (mid, ev), items in sorted(seq.items()):
        run: list[tuple[int, dict]] = []
        key = None
        for it in items + [(-1, None)]:
            k = None if it[1] is None else norm_reason(it[1].get("reason") if it[1].get("reason") is not None
                                                      else it[1].get("error") or it[1].get("why"))
            if run and k == key:
                run.append(it)
                continue
            if len(run) >= loop_min:
                ts = [t for t in (_epoch(r.get("ts")) for _, r in run) if t is not None]
                gaps = [b - a for a, b in zip(ts, ts[1:]) if b >= a]
                loops.append({"kind": ev, "mission_id": mid, "norm_reason": key, "count": len(run),
                              "first_idx": run[0][0], "last_idx": run[-1][0], "first_ts": min(ts) if ts else None,
                              "last_ts": max(ts) if ts else None,
                              "cadence_s": float(statistics.median(gaps)) if gaps else None,
                              "reason": str(run[0][1].get("reason") or run[0][1].get("error") or run[0][1].get("why")
                                            or "")})
            run, key = ([it], k) if it[1] is not None else ([], None)
    loops.sort(key=lambda l: (l["first_ts"] or 0, l["kind"], l["mission_id"]))
    return loops


# ---------------------------------------------------------------------------------------------------- verdict
def validate_verdict(v: str) -> str:
    if v not in VERDICTS:
        raise ValueError(f"verdict {v!r} is outside the closed set {VERDICTS}")
    return v


def verdict(champion: dict | None, challenger: dict | None, *, unmeasured_reason: str | None = None,
            assumption: str | None = None) -> dict:
    """One incident's verdict from the two arms' effects. An effect is {count, stops, stop_ts, stop_reason, ...}.
    UNMEASURED is chosen only by a named reason or a missing arm, and is never turned into PREVENTED or a zero."""
    basis = "inferred" if assumption else "measured"
    out = {"basis": basis, "assumption": assumption, "champion": champion, "challenger": challenger,
           "delta_s": None, "reason": None}
    if unmeasured_reason or champion is None or challenger is None:
        out.update(verdict=UNMEASURED, reason=unmeasured_reason or "inputs_incomplete", basis="unmeasured")
        return out
    cc, hc = champion.get("count"), challenger.get("count")
    if cc is not None and hc is not None and cc > 0 and (cc - hc) / cc >= REDUCTION_MIN:
        out.update(verdict=PREVENTED, reason=f"recurring outcome {cc} -> {hc} (reduction >= {REDUCTION_MIN})")
        return out
    cs, hs = champion.get("stop_ts"), challenger.get("stop_ts")
    if cs is not None and hs is not None and hs < cs:
        out.update(verdict=MOVED_EARLIER, delta_s=round(cs - hs, 3), reason=challenger.get("stop_reason"))
        return out
    if challenger.get("stops") and challenger.get("stop_reason"):
        out.update(verdict=LEGITIMATE_STOP, reason=challenger.get("stop_reason"))
        return out
    out.update(verdict=UNCHANGED, reason="both arms behave the same")
    return out


def effect_digest(champion, challenger) -> str:
    blob = json.dumps([champion, challenger], sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------------------- seams
_GSD_HOLD = re.compile(r"^gsd (NO_PHASES|UNAVAILABLE|ALL_COMPLETE): (.*)$", re.S)


def _short(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:10]


def recorded_hold_rows(rows: list[dict], loop: dict) -> int:
    """Hold-class rows the ledger holds for this loop: its relay_held rows plus the mission_blocked row(s) written by
    the pass on which the bounded hold turned into a block (that pass wrote no relay_held row)."""
    lo, hi = loop["first_ts"], loop["last_ts"]
    blocked = [r for r in rows if r.get("event") == "mission_blocked" and _mid(r) == loop["mission_id"]
               and lo is not None and (_epoch(r.get("ts")) or 0) >= lo and (_epoch(r.get("ts")) or 0) <= hi
               and str(r.get("reason") or "").startswith("gsd ")]
    return loop["count"] + len(blocked)


def s3_drive(loop: dict, passes: int, cadence_s: float, arm: str) -> dict:
    """Drive the REAL gsd_mission.supervise on a temp mission through `passes` passes at `cadence_s`, with a gsd_status
    answering the outcome the ledger recorded, under policy `arm`. Counts the passes that asked GSD and the hold-class
    rows written to the temp ledger."""
    m = _GSD_HOLD.match(loop["reason"])
    outcome, why = m.group(1), m.group(2)
    mid = "m-s7r" + _short(loop["mission_id"], loop["first_ts"], arm)
    t0 = 1_700_000_000.0
    calls = []

    def status(cwd, workstream=None):
        calls.append(1)
        return {"outcome": outcome, "reason": why}

    with sandbox() as root, policy_scope(arm):
        gm = _mods()
        gm.create(str(root), "/gsd-autonomous", mission_id=mid, now=t0,
                  max_hours=(passes * cadence_s) / 3600.0 + 48.0)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="s7_seed", now=t0, state=gm.RUNNING,
                      epoch=1, owner={"session_id": "s-s7", "pid": 5151, "kind": "background"})
        hs = [{"sessionId": "s-s7", "status": "idle", "kind": "background", "id": "s-s7", "pid": 999}]
        now = t0 + 800.0
        for _ in range(passes):
            gm.supervise(now=now, sessions=hs, gsd_status=status, runner=lambda a, c: None,
                         stop_runner=lambda a: None, pid_alive=lambda p: True)
            now += cadence_s
        ev = [json.loads(l) for l in (root / "gsd-autorun-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l]
        final = gm.load(mid)
    held = sum(1 for e in ev if e.get("event") == "relay_held")
    blocked = sum(1 for e in ev if e.get("event") == "mission_blocked")
    return {"passes": passes, "status_calls": len(calls), "relay_held_rows": held, "blocked_rows": blocked,
            "count": held + blocked, "final_state": final.get("state") if final else None}


def faithful(recorded: int, replayed: int, tol: float = FAITHFUL_TOL) -> dict:
    """The champion replay against the recorded history. Outside `tol` the incident is UNMEASURED (replay_unfaithful)."""
    dev = abs(replayed - recorded) / recorded if recorded else (0.0 if replayed == 0 else 1.0)
    return {"recorded": recorded, "champion_replay": replayed, "deviation": round(dev, 4), "tolerance": tol,
            "ok": dev <= tol}


def s3_incident(rows: list[dict], loop: dict, records: dict, drift: dict) -> dict:
    """S3 hold backoff on one discovered relay_held loop, through the real supervise path."""
    base = {"slice": "S3", "kind": loop["kind"], "mission_id": loop["mission_id"], "first_ts": _iso(loop["first_ts"]),
            "last_ts": _iso(loop["last_ts"]), "rows": loop["count"], "seam": "gsd_mission.supervise"}
    need = _record_need(loop["mission_id"], records, drift, rows)
    if need.get("unmeasured"):
        return {**base, **verdict(None, None, unmeasured_reason=need["unmeasured"]), "faithful": None}
    recorded = recorded_hold_rows(rows, loop)
    cadence = loop["cadence_s"] or 300.0
    if recorded > PASS_CAP:
        return {**base, **verdict(None, None, unmeasured_reason="pass_cap_exceeded"), "faithful": None}
    champ = s3_drive(loop, recorded, cadence, "champion")
    chal = s3_drive(loop, recorded, cadence, "challenger")
    fa = faithful(recorded, champ["count"])
    ce = {**champ, "stops": champ["blocked_rows"] > 0, "stop_ts": None, "stop_reason": None}
    he = {**chal, "stops": chal["blocked_rows"] > 0, "stop_ts": None,
          "stop_reason": "gsd hold bounded: blocked after the refusal did not clear" if chal["blocked_rows"] else None}
    v = verdict(ce, he, unmeasured_reason=None if fa["ok"] else "replay_unfaithful")
    return {**base, **v, "faithful": fa, "recorded_cadence_s": cadence, "command_source": need["source"]}


def _record_need(mission_id: str, records: dict, drift: dict, rows: list[dict]) -> dict:
    """What an incident needs from the host mission record: its resume command. A record that changed since the pin
    is not read (UNMEASURED); a mission with no pinned record falls back to the command its own ledger rows carry."""
    if _record_file(mission_id) in drift:
        return {"unmeasured": "record_changed_since_pin", "drift": drift[_record_file(mission_id)]}
    rec = records.get(mission_id)
    if rec is not None:
        cmd = rec.get("resume_command") or ""
        src = "pinned_record"
    else:
        cmd = next((r.get("command") for r in rows if _mid(r) == mission_id and r.get("command")), "") or ""
        src = "ledger_row"
    if not str(cmd).startswith("/gsd-"):
        return {"unmeasured": "not_a_gsd_resume_command"}
    return {"command": cmd, "source": src, "workstream": (rec or {}).get("workstream")}


def s2_incident(rows: list[dict], loop: dict, records: dict, drift: dict) -> dict:
    """S2 arm preflight on the NO_PHASES / ALL_COMPLETE arm of one loop, through the real arm_preflight."""
    base = {"slice": "S2", "kind": loop["kind"], "mission_id": loop["mission_id"], "first_ts": _iso(loop["first_ts"]),
            "last_ts": _iso(loop["last_ts"]), "rows": loop["count"], "seam": "gsd_mission.arm_preflight"}
    need = _record_need(loop["mission_id"], records, drift, rows)
    if need.get("unmeasured"):
        return {**base, **verdict(None, None, unmeasured_reason=need["unmeasured"]), "faithful": None}
    m = _GSD_HOLD.match(loop["reason"])
    outcome, why = m.group(1), m.group(2)
    mine = [r for r in rows if _mid(r) == loop["mission_id"]]
    arm_times = [t for t in (_epoch(r.get("ts")) for r in mine if r.get("event") in ("mission_prepared", "armed"))
                 if t is not None]
    arm_ts = min(arm_times) if arm_times else None
    stop = next((r for r in mine if r.get("event") in ("mission_blocked", "mission_halted")), None)
    stop_ts = _epoch(stop.get("ts")) if stop else None
    effects = {}
    for arm in ("champion", "challenger"):
        with sandbox() as root, policy_scope(arm):
            gm = _mods()
            res = gm.arm_preflight(str(root), need["command"], workstream=need["workstream"], launch=False,
                                   status_reader=lambda c, w: {"outcome": outcome, "reason": why})
        effects[arm] = res
    ce = {"count": None, "ok": effects["champion"]["ok"], "stops": stop is not None, "stop_ts": stop_ts,
          "stop_reason": str(stop.get("reason"))[:160] if stop else None}
    he = {"count": None, "ok": effects["challenger"]["ok"], "stops": not effects["challenger"]["ok"],
          "stop_ts": arm_ts if not effects["challenger"]["ok"] else None,
          "stop_reason": effects["challenger"]["refusal"]}
    first_obs = _epoch(rows[loop["first_idx"]].get("ts"))
    measured = arm_ts is not None and first_obs is not None and first_obs <= arm_ts
    assume = None if measured else "status unchanged between arm and first observation"
    bad = None
    if effects["champion"]["ok"] is not True:
        bad = "champion_arm_preflight_refused"
    if arm_ts is None:
        bad = "no_arm_row"
    v = verdict(ce, he, unmeasured_reason=bad, assumption=assume)
    return {**base, **v, "faithful": None, "arm_ts": _iso(arm_ts), "command_source": need["source"],
            "hold_window_s": None if loop["last_ts"] is None or arm_ts is None else round(loop["last_ts"] - arm_ts, 3)}


# ---------------------------------------------------------------------------------------------------- replay
def replay(pin_path: str | Path, command: str | None = None) -> dict:
    pn = load_pin(pin_path)
    rows, torn = read_prefix(pn)                         # raises Inconclusive on a mismatch
    records, drift = read_records(pn)
    loops = detect_loops(rows)
    incidents = []
    for lp in loops:
        if lp["kind"] == "relay_held" and _GSD_HOLD.match(lp["reason"]):
            incidents.append(s3_incident(rows, lp, records, drift))
            if _GSD_HOLD.match(lp["reason"]).group(1) in ("NO_PHASES", "ALL_COMPLETE"):
                incidents.append(s2_incident(rows, lp, records, drift))
    for inc in incidents:
        inc["id"] = _short(inc["slice"], inc["kind"], inc["mission_id"], inc["first_ts"])
        inc["effect_digest"] = effect_digest(inc["champion"], inc["challenger"])
    incidents.sort(key=lambda i: (i["first_ts"] or "", i["kind"], i["mission_id"], i["slice"]))
    counts = {v: sum(1 for i in incidents if i["verdict"] == v) for v in VERDICTS}
    return {"schema": SCHEMA,
            "command": command or f"python3 tools/flow_replay.py replay --pin {pin_path}",
            "pin": {"path": str(pin_path), "ledger": pn["ledger"], "bytes": pn["bytes"], "rows": pn["rows"],
                    "sha256": pn["sha256"]},
            "held": dict(HELD), "policies": {k: dict(v) for k, v in POLICIES.items()},
            "tolerances": {"LOOP_MIN": LOOP_MIN, "REDUCTION_MIN": REDUCTION_MIN, "FAITHFUL_TOL": FAITHFUL_TOL,
                           "PASS_CAP": PASS_CAP},
            "torn_rows": torn, "record_drift": sorted(drift), "loops_found": len(loops),
            "incidents": incidents, "counts_by_verdict": counts}


# ---------------------------------------------------------------------------------------------------- cli
def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="flow_replay")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pin")
    p.add_argument("--ledger", required=True)
    p.add_argument("--out", required=True)
    r = sub.add_parser("replay")
    r.add_argument("--pin", required=True)
    r.add_argument("--json")
    r.add_argument("--md")
    a = ap.parse_args(argv)
    cmd = "python3 tools/flow_replay.py " + " ".join(sys.argv[1:] if argv is None else argv)
    if a.cmd == "pin":
        d = pin(a.ledger, a.out, command=cmd)
        print(f"PIN bytes={d['bytes']} rows={d['rows']} sha256={d['sha256']}")
        return 0
    try:
        res = replay(a.pin, command=cmd)
    except Inconclusive as exc:
        print(f"INCONCLUSIVE: {exc}", file=sys.stderr)
        return 2
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"REPLAY pin={res['pin']['sha256'][:12]} incidents={len(res['incidents'])} counts={res['counts_by_verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
