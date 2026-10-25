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


# ---------------------------------------------------------------------------------------------------- failure kinds
# Data, not a list of mission ids. Per ledger event kind: ordered (reason-regex | None, incident kind, slices, seam).
# `slices` empty = nothing in S1-S6 acts on it: counted, listed, reported UNCHANGED, never dropped.
FAILURE_KINDS = {
    "relay_held": [(r"^gsd (?:NO_PHASES|UNAVAILABLE|ALL_COMPLETE):", "gsd_hold", ("S3", "S2"),
                    "gsd_mission.supervise + arm_preflight"),
                   (None, "relay_hold_other", (), None)],
    "mission_blocked": [(None, "blocked_park", ("S6",), "blocker_compiler.compile_blocker")],
    "blocked_intent": [(None, "blocked_intent_companion", ("S6",), "blocker_compiler.compile_blocker (intent)")],
    "owner_hold_set": [(None, "owner_hold", ("S6",), "blocker_compiler.compile_blocker (hold)")],
    "recovery_owner_boundary": [(None, "owner_hold", ("S6",), "blocker_compiler.compile_blocker (hold)")],
    "cost_breaker_tripped": [(None, "cost_trip", ("S4",), "mission_spend.judge")],
    "epoch_compacted": [(None, "compaction", ("S1",), "gsd_mission.apply_rotation_invariant")],
    "envelope_set": [(None, "envelope", ("S1",), "gsd_mission.apply_rotation_invariant")],
    "mission_halted": [(r"budget:", "budget_halt", ("S5", "renewal"), "mission_reconcile + renewal_refusal"),
                       (None, "terminal_halt", ("S5",), "mission_reconcile.reconcile/dispose")],
    "mission_renewed": [(None, "renewal", ("renewal",), "gsd_mission.renewal_refusal")],
    "quota_held": [(None, "provider_wait", ("provider",), "provider holds, not the policy")],
    "provider_held": [(None, "provider_wait", ("provider",), "provider holds, not the policy")],
    "supervise_error": [(None, "supervise_error", (), None)],
    "launch_failed": [(None, "launch_failed", (), None)],
    "launch_held": [(None, "launch_held", (), None)],
    "launch_held_cwd": [(None, "launch_held", (), None)],
    "continuation_failed": [(None, "continuation_failed", (), None)],
}
# Real slice seams only. "renewal" is a labelled sensitivity axis and "provider" a wait the provider owns: neither is S2-S6.
SLICE_NAMES = ("S1", "S2", "S3", "S4", "S5", "S6")


def classify_row(row: dict) -> tuple[str, tuple] | None:
    """(incident kind, slices) for a failure-class row, else None. Exactly one answer per row."""
    table = FAILURE_KINDS.get(row.get("event"))
    if not table:
        return None
    reason = str(row.get("reason") or "")
    for rx, kind, slices, _seam in table:
        if rx is None or re.search(rx, reason):
            return kind, slices
    return None


def coverage(rows: list[dict], loops: list[dict]) -> dict:
    """The coverage line, COMPUTED from the pinned rows."""
    by_kind: dict[str, int] = {}
    mapped = unmapped = total = 0
    per_event = {k: 0 for k in sorted(FAILURE_KINDS)}
    for r in rows:
        c = classify_row(r)
        if c is None:
            continue
        total += 1
        per_event[r["event"]] += 1
        by_kind[c[0]] = by_kind.get(c[0], 0) + 1
        if any(sl in SLICE_NAMES for sl in c[1]):
            mapped += 1
        else:
            unmapped += 1
    unmapped_loops = []
    for l in loops:
        probe = {"event": l["kind"], "reason": l["reason"]}
        c = classify_row(probe)
        if c is None or not any(sl in SLICE_NAMES for sl in c[1]):
            unmapped_loops.append({"mission_id": l["mission_id"], "kind": l["kind"], "rows": l["count"],
                                   "first_ts": _iso(l["first_ts"]), "last_ts": _iso(l["last_ts"]),
                                   "sample": l["reason"][:160], "carried_to": "Phase 8",
                                   "in_failure_table": c is not None})
    return {"failure_rows_total": total, "mapped_to_slice": mapped, "unmapped": unmapped,
            "sums_to_total": sum(by_kind.values()) == total and mapped + unmapped == total,
            "rows_by_event": per_event, "rows_by_incident_kind": dict(sorted(by_kind.items())),
            "unmapped_loops": unmapped_loops}


# ---------------------------------------------------------------------------------------------------- seams: S6 / S4 / S1 / S5
def _row_incident(base: dict, v: dict, **extra) -> dict:
    return {**base, **v, "faithful": extra.pop("faithful", None), **extra}


def s6_incidents(rows: list[dict]) -> list[dict]:
    """Every mission_blocked / owner_hold_set row through the real compile_blocker with cwd=None: a historical row is
    never explained from today's ROADMAP or STATE (W2)."""
    import blocker_compiler as bc
    out = []
    intents = [(i, r) for i, r in enumerate(rows) if r.get("event") == "blocked_intent"]
    for i, r in enumerate(rows):
        if r.get("event") not in ("mission_blocked", "owner_hold_set"):
            continue
        is_hold = r["event"] == "owner_hold_set"
        t = _epoch(r.get("ts"))
        base = {"slice": "S6", "kind": r["event"], "mission_id": _mid(r), "first_ts": r.get("ts"),
                "last_ts": r.get("ts"), "rows": 1, "seam": "blocker_compiler.compile_blocker"}
        intent = next(({"kind": x.get("kind"), "action": x.get("action")} for _, x in intents
                       if _mid(x) == _mid(r) and x.get("epoch") == r.get("epoch")
                       and t is not None and abs((_epoch(x.get("ts")) or 0) - t) <= 60), None)
        effects = {}
        try:
            gm = _mods()
            for arm in ("champion", "challenger"):
                with policy_scope(arm):
                    on = gm.blocker_compile_on()
                    comp = bc.compile_blocker(r.get("reason"), hold={"reason": r.get("reason")} if is_hold else None,
                                              intent=intent, rec=None, cwd=None, is_hold=is_hold) if on else None
                effects[arm] = comp
        except Exception as exc:  # noqa: BLE001 -- an instrument that raises measured nothing
            out.append(_row_incident(base, verdict(None, None, unmeasured_reason=f"compile_error:{type(exc).__name__}")))
            continue
        ce = {"typed": False, "class": None, "count": None, "stops": True, "stop_ts": t, "stop_reason": None}
        comp = effects["challenger"]
        klass = comp["class"] if comp else None
        he = {"typed": comp is not None, "class": klass, "owner_required": comp and comp["owner_required"],
              "independent_work": comp and comp["independent_work"], "rule": comp and comp["rule"], "count": None,
              "stops": True, "stop_ts": t, "stop_reason": klass if klass and klass != bc.UNKNOWN else None}
        out.append(_row_incident(base, verdict(ce, he), hold=is_hold,
                                 fc06_inputs={"resolved": [{"text": str(r.get("reason") or ""),
                                                            "owner_required": bool(comp and comp["owner_required"])}]}
                                 if comp else None))
    return out


_TRIP_AUTH = re.compile(r"'authority_tokens':\s*(\d+)")
_N = lambda m: int(m.group(1).replace(",", ""))  # noqa: E731


def _trip_class(reason: str) -> str:
    if "(mission authority)" in reason:
        return "authority_ceiling"
    if "default policy ceiling" in reason:
        return "default_ceiling"
    if "since the work tree last changed" in reason:
        return "stall"
    if " x estimate" in reason:
        return "variance"
    return "other"


def s4_judge(rows: list[dict], idx: int) -> dict:
    """Rebuild (rec, spent, fp) for one cost_breaker_tripped row from the rows BEFORE it and call the real judge under
    both policies. A field the ledger cannot supply is named and the row is UNMEASURED, never defaulted."""
    r = rows[idx]
    mid, t = _mid(r), _epoch(r.get("ts"))
    reason, spent, est = str(r.get("reason") or ""), r.get("spent"), r.get("estimate")
    klass = _trip_class(reason)
    if spent is None or est is None or klass == "other":
        return {"class": klass, "unmeasured": "inputs_incomplete" if klass != "other" else "unrecognised_trip_reason"}
    prior = [x for x in rows[:idx] if _mid(x) == mid]
    auth = None
    for x in prior:
        if x.get("event") == "authority_set":
            m = _TRIP_AUTH.search(str(x.get("reason") or ""))
            auth = int(m.group(1)) if m else auth
        elif x.get("event") == "authority_topup_policy" and x.get("authority"):
            auth = int(x["authority"])
    rec = {"mission_id": mid, "token_estimate": int(est)}
    if auth:
        rec["authority_tokens"] = auth
    auto = [x for x in prior if x.get("event") == "envelope_auto_assigned"]
    if auto:
        m = re.search(r"=\s*([\d,]+)\s*$", str(auto[-1].get("reason") or ""))
        if m and _N(m) == int(est):
            rec["token_estimate_src"] = "auto"
    fp, assumption = None, None
    if klass == "stall":
        burned = re.search(r"([\d,]+) processed since", reason)
        stall = re.search(r"stall budget ([\d,]+)", reason)
        if not (burned and stall):
            return {"class": klass, "unmeasured": "inputs_incomplete"}
        rec["cost_mark"] = {"fp": "same", "tokens": int(spent) - _N(burned)}
        rec["token_stall_budget"] = _N(stall)
        fp = "same"
        assumption = "work tree unchanged since the mark, as the recorded reason states"
    elif klass == "variance" and auth:
        rcp = [x for x in prior if x.get("event") == "breaker_receipt" and x.get("fp")]
        if not rcp:
            return {"class": klass, "unmeasured": "fingerprint"}
        fp = rcp[-1]["fp"]
        rec["cost_mark"] = rcp[-1].get("mark") or {}
        if not rec["cost_mark"].get("fp"):
            return {"class": klass, "unmeasured": "fingerprint"}
        assumption = "no lease renewals had been taken before this trip (lease_renewals = 0)"
    elif klass == "authority_ceiling" and not auth:
        return {"class": klass, "unmeasured": "authority_unrecorded"}
    res = {}
    gm_ms = None
    for arm in ("champion", "challenger"):
        with policy_scope(arm):
            import mission_spend as ms
            gm_ms = ms
            res[arm] = ms.judge(dict(rec), int(spent), fp)
    trip = {a: bool(res[a].get("trip")) for a in res}
    if not trip["champion"]:
        return {"class": klass, "unmeasured": "replay_unfaithful", "rebuilt": {a: bool(res[a].get("trip")) for a in res}}
    return {"class": klass, "authority": bool(auth), "champion_trip": trip["champion"],
            "challenger_trip": trip["challenger"], "assumption": assumption, "ts": t,
            "level": res["champion"].get("level"), "spent": int(spent), "auth": int(auth) if auth else None}


def s4_incidents(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for i, r in enumerate(rows):
        if r.get("event") != "cost_breaker_tripped":
            continue
        j = s4_judge(rows, i)
        groups.setdefault((_mid(r), j["class"], bool(j.get("authority"))), []).append({**j, "ts_iso": r.get("ts")})
    out = []
    for (mid, klass, has_auth), js in sorted(groups.items(), key=lambda kv: (kv[1][0]["ts_iso"], kv[0][0], kv[0][1])):
        ok = [j for j in js if "unmeasured" not in j]
        bad = [j for j in js if "unmeasured" in j]
        base = {"slice": "S4", "kind": "cost_breaker_tripped", "mission_id": mid, "trip_class": klass,
                "first_ts": js[0]["ts_iso"], "last_ts": js[-1]["ts_iso"], "rows": len(js),
                "seam": "mission_spend.judge", "unmeasured_rows": len(bad),
                "unmeasured_reasons": sorted({j["unmeasured"] for j in bad})}
        if not ok:
            out.append(_row_incident(base, verdict(None, None, unmeasured_reason=bad[0]["unmeasured"])))
            continue
        ce = {"count": sum(j["champion_trip"] for j in ok), "stops": True, "stop_ts": ok[0]["ts"],
              "stop_reason": f"cost breaker: {klass}"}
        he_trips = [j for j in ok if j["challenger_trip"]]
        he = {"count": len(he_trips), "stops": bool(he_trips), "stop_ts": he_trips[0]["ts"] if he_trips else None,
              "stop_reason": f"cost breaker: {klass}" if he_trips else None}
        assume = next((j["assumption"] for j in ok if j.get("assumption")), None)
        grants = [{"kind": "spend", "amount": j["spent"], "granted": not j["challenger_trip"], "ceiling": j["auth"]}
                  for j in ok if j.get("auth")]
        out.append(_row_incident(base, verdict(ce, he, assumption=assume),
                                 fc06_inputs={"capital": {"authority": None, "topups": [], "grants": grants}}
                                 if grants else None))
    return out


_ENV_AUTOCOMPACT = re.compile(r"autocompact\s+\S+\s*->\s*(\d+[kKmM]?)")


def s1_incidents(rows: list[dict]) -> list[dict]:
    """Missions with recorded compactions, run through the real apply_rotation_invariant. The repair is the effect; the
    compactions it would have prevented cannot be shown (epoch_compacted carries no size): UNMEASURED."""
    gm = _mods()
    missions: dict[str, dict] = {}
    for r in rows:
        mid = _mid(r)
        if r.get("event") == "baseline_resolved" and isinstance(r.get("values"), dict):
            v = r["values"]
            missions.setdefault(mid, {})
            if v.get("autocompact"):
                missions[mid]["autocompact"] = v["autocompact"]
            if v.get("continue_max_tokens"):
                missions[mid]["continue_max_tokens"] = int(v["continue_max_tokens"])
        elif r.get("event") == "envelope_set":
            m = _ENV_AUTOCOMPACT.search(str(r.get("reason") or ""))
            if m:
                missions.setdefault(mid, {})["autocompact"] = m.group(1)
    comp: dict[str, list[dict]] = {}
    for r in rows:
        if r.get("event") == "epoch_compacted":
            comp.setdefault(_mid(r), []).append(r)
    out = []
    for mid, cs in sorted(comp.items(), key=lambda kv: kv[1][0]["ts"]):
        base = {"slice": "S1", "kind": "epoch_compacted", "mission_id": mid, "first_ts": cs[0]["ts"],
                "last_ts": cs[-1]["ts"], "rows": len(cs), "seam": "gsd_mission.apply_rotation_invariant"}
        rec = missions.get(mid)
        if not rec or not rec.get("autocompact"):
            out.append(_row_incident(base, verdict(None, None, unmeasured_reason="inputs_incomplete")))
            continue
        eff = {}
        for arm in ("champion", "challenger"):
            with policy_scope(arm):
                res = gm.apply_rotation_invariant(dict(rec))
            inv = res.get("rotation_invariant") or {}
            eff[arm] = {"count": None, "stops": False, "stop_ts": None, "stop_reason": None,
                        "repaired": inv.get("repaired") or {}, "derived": inv.get("derived") or {},
                        "continue_max_tokens": res.get("continue_max_tokens", gm.lr and rec.get("continue_max_tokens")),
                        "compactions_recorded": len(cs)}
        out.append(_row_incident(base, verdict(eff["champion"], eff["challenger"], unmeasured_reason="no_size_evidence"),
                                 repair_differs=eff["champion"]["repaired"] != eff["challenger"]["repaired"]))
    return out


def s5_incidents(rows: list[dict], records: dict, drift: dict, now: float) -> tuple[list[dict], dict]:
    """Terminal missions through the real reconcile + dispose, `now` fixed at the pin so the hours do not drift."""
    import mission_reconcile as mrc
    gm = _mods()
    missions = [r for r in records.values()]
    rep = mrc.dispose(events=rows, now=now, missions=missions)
    out = []
    for p in rep["per_mission"]:
        base = {"slice": "S5", "kind": "terminal_reconcile", "mission_id": p["id"], "first_ts": None, "last_ts": None,
                "rows": 1, "seam": "mission_reconcile.reconcile/dispose"}
        done_in = None
        if p["outcome"] == mrc.RECOVERED_DONE:    # a DONE claim is checked against the receipt the resolver named
            rec_ = records.get(p["id"]) or {}
            pkt = (rec_.get("wu_packet") or {}).get("path")
            done_in = {"done": [{"path": gm.resolve_receipt(pkt, rec_)["path"], "claimed": True}]} if pkt else None
        ce = {"count": None, "classified": False, "stops": False, "stop_ts": None, "stop_reason": None}
        he = {"count": None, "classified": True, "outcome": p["outcome"], "stops": False, "stop_ts": None,
              "stop_reason": None, **{b: p[b] for b in mrc.BUCKETS}}
        out.append(_row_incident(base, verdict(ce, he, assumption="the annotation (CPP_TERMINAL_RECONCILE) changes no "
                                                                  "launch decision; reconcile has no switch of its own"),
                                 fc06_inputs=done_in))
    for u in rep["unmeasured"]:
        out.append(_row_incident({"slice": "S5", "kind": "terminal_reconcile", "mission_id": u["id"], "first_ts": None,
                                  "last_ts": None, "rows": 1, "seam": "mission_reconcile.dispose"},
                                 verdict(None, None, unmeasured_reason="no_terminal_row")))
    for name in sorted(drift):
        mid = name[len("gsd-mission-"):-len(".json")]
        out.append(_row_incident({"slice": "S5", "kind": "terminal_reconcile", "mission_id": mid, "first_ts": None,
                                  "last_ts": None, "rows": 1, "seam": "mission_reconcile.dispose"},
                                 verdict(None, None, unmeasured_reason="record_changed_since_pin")))
    return out, {"buckets_h": rep["buckets_h"], "missions": rep["missions"], "quoted_not_measured": rep["quoted_not_measured"],
                 "unmeasured": rep["unmeasured"], "now": _iso(now)}


def renewal_axis(rows: list[dict], records: dict, drift: dict) -> dict:
    """Sensitivity over the real renewal_refusal, NOT part of the S2-S6 totals. A halt row's gsd outcome is used only
    when the ledger implies one (a later mission_renewed row means GSD answered OK); otherwise UNMEASURED."""
    gm = _mods()
    renewed_from = {r.get("session_id") for r in rows if r.get("event") == "mission_renewed" and r.get("successor")}
    items, refusals = [], {"unset": {}, "off": {}}
    for r in rows:
        if r.get("event") != "mission_halted" or "budget:" not in str(r.get("reason") or ""):
            continue
        mid = _mid(r)
        item = {"mission_id": mid, "halt_ts": r.get("ts"), "halt_reason": str(r["reason"])[:120]}
        if _record_file(mid) in drift:
            item["unmeasured"] = "record_changed_since_pin"
        elif mid not in records:
            item["unmeasured"] = "no_pinned_record"
        elif mid not in renewed_from:
            item["unmeasured"] = "gsd_outcome"
        else:
            item["gsd_outcome"] = "OK"
            item["assumption"] = "a later mission_renewed row implies GSD answered OK at renewal"
            for label, val in (("unset", ""), ("off", "off")):
                with policy_scope("challenger"), _env({"CPP_MISSION_RENEW": val}):
                    why = gm.renewal_refusal(dict(records[mid]), r["reason"], "OK")
                item[f"refusal_{label}"] = why
                key = (why or "renewable")[:60]
                refusals[label][key] = refusals[label].get(key, 0) + 1
        items.append(item)
    return {"axis": "renewal", "in_s2_s6_totals": False, "halts_budget": len(items),
            "unmeasured": sum(1 for i in items if "unmeasured" in i),
            "unmeasured_reasons": sorted({i["unmeasured"] for i in items if "unmeasured" in i}),
            "refusals_by_reason": {k: dict(sorted(v.items())) for k, v in refusals.items()}, "items": items}


def provider_incidents(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        c = classify_row(r)
        if c and c[0] == "provider_wait":
            groups.setdefault((r["event"], _mid(r)), []).append(r)
    out = []
    for (kind, mid), rs in sorted(groups.items(), key=lambda kv: (kv[1][0]["ts"], kv[0])):
        eff = {"count": len(rs), "stops": True, "stop_ts": _epoch(rs[0]["ts"]), "stop_reason": f"provider hold ({kind})"}
        out.append(_row_incident({"slice": "provider", "kind": kind, "mission_id": mid, "first_ts": rs[0]["ts"],
                                  "last_ts": rs[-1]["ts"], "rows": len(rs), "seam": "provider holds, not the policy"},
                                 verdict(dict(eff), dict(eff))))
    return out


def unmapped_incidents(rows: list[dict], loops: list[dict]) -> list[dict]:
    """Failure rows no slice acts on, and loops of ANY kind that nothing explains: reported UNCHANGED, never dropped."""
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        c = classify_row(r)
        if c and not any(sl in SLICE_NAMES or sl in ("provider", "renewal") for sl in c[1]):
            groups.setdefault((c[0], _mid(r)), []).append(r)
    out = []
    in_loop = {(l["kind"], l["mission_id"]): l for l in loops}
    for (kind, mid), rs in sorted(groups.items(), key=lambda kv: (kv[1][0]["ts"], kv[0])):
        lp = in_loop.get((rs[0]["event"], mid))
        eff = {"count": len(rs), "stops": False, "stop_ts": None, "stop_reason": None}
        out.append(_row_incident({"slice": "none", "kind": rs[0]["event"], "incident_kind": kind, "mission_id": mid,
                                  "first_ts": rs[0]["ts"], "last_ts": rs[-1]["ts"], "rows": len(rs),
                                  "seam": "no slice acts on this kind", "loop": bool(lp),
                                  "carried_to": "Phase 8" if lp else None}, verdict(dict(eff), dict(eff))))
    for lp in loops:
        c = classify_row({"event": lp["kind"], "reason": lp["reason"]})
        if c is None:
            eff = {"count": lp["count"], "stops": False, "stop_ts": None, "stop_reason": None}
            out.append(_row_incident({"slice": "none", "kind": lp["kind"], "incident_kind": "unexplained_loop",
                                      "mission_id": lp["mission_id"], "first_ts": _iso(lp["first_ts"]),
                                      "last_ts": _iso(lp["last_ts"]), "rows": lp["count"],
                                      "seam": "generic loop detector; kind not in the failure table", "loop": True,
                                      "carried_to": "Phase 8"}, verdict(dict(eff), dict(eff))))
    return out


# ---------------------------------------------------------------------------------------------------- FC-06 + mutants
# The REAL decision functions, captured once before any mutant is installed. The FC-06 assertions judge with these, never
# with whatever a mutant has put in the module namespace, so a mutant cannot grade itself.
_ORIG: dict | None = None


def _originals() -> dict:
    global _ORIG
    if _ORIG is None:
        with sandbox():
            gm = _mods()
            import receipt_judge as rj
            import blocker_compiler as bc
            import mission_spend as ms
            root = str(TOOLS.parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            from modules.autonomy_gate import gate
            _ORIG = {"arm_preflight": gm.arm_preflight, "_packet_digest_matches": gm._packet_digest_matches,
                     "apply_rotation_invariant": gm.apply_rotation_invariant, "renewal_refusal": gm.renewal_refusal,
                     "is_done": rj.is_done, "compile_blocker": bc.compile_blocker, "judge": ms.judge,
                     "classify": gate.classify, "PROTECTED": bc.PROTECTED, "UNKNOWN": bc.UNKNOWN}
    return _ORIG


ASSERTIONS = ("capital_ceiling", "packet_digest", "done_proof", "protections")


def _na() -> dict:
    return {"status": "not_applicable", "breaches": [], "checked": 0}


def _result(name: str, checked: int, breaches: list) -> dict:
    return {"status": "breach" if breaches else "clear", "breaches": [{"assertion": name, **b} for b in breaches],
            "checked": checked}


def _chk_capital(inp: dict) -> dict:
    """No spend, lease or renewal grant beyond the recorded authority plus recorded top-ups. No recorded authority means
    there is no ceiling to breach: not_applicable, never a pass."""
    c = (inp or {}).get("capital")
    if not c:
        return _na()
    base = None if c.get("authority") is None else int(c["authority"]) + sum(int(x) for x in c.get("topups") or [])
    checked, bad = 0, []
    for g in c.get("grants") or []:
        ceiling = g.get("ceiling", base)
        if ceiling is None:
            continue
        checked += 1
        if g.get("granted") and int(g["amount"]) > int(ceiling):
            bad.append({"detail": f"{g.get('kind')} granted {g['amount']} above the ceiling {ceiling}"})
    return _result("capital_ceiling", checked, bad) if checked else _na()


def _chk_digest(inp: dict) -> dict:
    """A packet is never admitted against a different digest: judged by the REAL _packet_digest_matches."""
    ds = (inp or {}).get("digests") or []
    if not ds:
        return _na()
    real = _originals()["_packet_digest_matches"]
    bad = [{"detail": f"admitted {d.get('path')} but its bytes do not match the stored digest"}
           for d in ds if d.get("admitted") and not real(d.get("stored"), d.get("path"))]
    return _result("packet_digest", len(ds), bad)


def _chk_done(inp: dict) -> dict:
    """DONE only with receipt_judge.is_done on the same receipt: judged by the REAL is_done."""
    ds = (inp or {}).get("done") or []
    if not ds:
        return _na()
    real = _originals()["is_done"]
    bad = [{"detail": f"DONE claimed on {d.get('path')} but receipt_judge.is_done is false"}
           for d in ds if d.get("claimed") and not real(d.get("path"))]
    return _result("done_proof", len(ds), bad)


def _chk_protect(inp: dict) -> dict:
    """An item resolved without the Owner that the REAL autonomy gate classes Owner, or that blocker_compiler.PROTECTED
    matches (capital, authority, branch protection, force-push), is a weakened protection."""
    rs = (inp or {}).get("resolved") or []
    if not rs:
        return _na()
    o = _originals()
    bad = []
    for it in rs:
        if it.get("owner_required"):
            continue
        text = str(it.get("text") or "")
        gate_owner = (o["classify"](text, authorized=()) or {}).get("owner") == "OWNER"
        if gate_owner or o["PROTECTED"].search(text):
            bad.append({"detail": f"resolved without the Owner: {text[:120]}",
                        "by": "autonomy_gate" if gate_owner else "PROTECTED"})
    return _result("protections", len(rs), bad)


def fc06_status(inputs: dict | None) -> dict:
    """{assertion: {status: clear|breach|not_applicable, breaches, checked}} for one scenario's inputs."""
    return {"capital_ceiling": _chk_capital(inputs or {}), "packet_digest": _chk_digest(inputs or {}),
            "done_proof": _chk_done(inputs or {}), "protections": _chk_protect(inputs or {})}


def fc06(scenario_result: dict) -> list[dict]:
    """The named breaches of one scenario result (empty = none). A scenario with no inputs has none to find."""
    st = fc06_status((scenario_result or {}).get("fc06_inputs"))
    return [b for a in ASSERTIONS for b in st[a]["breaches"]]


def attach_fc06(inc: dict) -> dict:
    inputs = inc.get("fc06_inputs")
    st = fc06_status(inputs)
    inc["fc06"] = {"status": {a: st[a]["status"] for a in ASSERTIONS}, "breaches": [b for a in ASSERTIONS for b in st[a]["breaches"]]}
    return inc


# --- the controls: each assertion fires on a seeded breach and stays quiet on a clean control built the same way
def fc06_selftest() -> dict:
    """{assertion: {breach_fires, clean_quiet}} using real files for the digest and receipt checks."""
    out = {}
    out["capital_ceiling"] = _selftest_pair(
        {"capital": {"authority": 1000, "topups": [500], "grants": [{"kind": "spend", "amount": 1501, "granted": True}]}},
        {"capital": {"authority": 1000, "topups": [500], "grants": [{"kind": "spend", "amount": 1500, "granted": True}]}},
        "capital_ceiling")
    d = Path(tempfile.mkdtemp(prefix="flow-fc06-"))
    try:
        pkt = d / "packet.md"
        pkt.write_text("packet one\n", encoding="utf-8")
        stored = hashlib.sha256(b"packet one\n").hexdigest()
        out["packet_digest"] = _selftest_pair(
            {"digests": [{"stored": "0" * 64, "path": str(pkt), "admitted": True}]},
            {"digests": [{"stored": stored, "path": str(pkt), "admitted": True}]}, "packet_digest")
        rj_real = _originals()["is_done"]
        bad_r, good_r = d / "stub.md", d / "done.md"
        bad_r.write_text("# Receipt\nStatus: IN PROGRESS\n", encoding="utf-8")
        good_r.write_text("# Receipt\nStatus: DONE\n", encoding="utf-8")
        assert rj_real(bad_r) is False and rj_real(good_r) is True, "receipt fixtures do not read as intended"
        out["done_proof"] = _selftest_pair({"done": [{"path": str(bad_r), "claimed": True}]},
                                           {"done": [{"path": str(good_r), "claimed": True}]}, "done_proof")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    out["protections"] = _selftest_pair(
        {"resolved": [{"text": "do not force-push the protected branch", "owner_required": False}]},
        {"resolved": [{"text": "rename the local helper variable", "owner_required": False}]}, "protections")
    return out


def _selftest_pair(breach_in: dict, clean_in: dict, name: str) -> dict:
    b, c = fc06_status(breach_in)[name], fc06_status(clean_in)[name]
    return {"breach_fires": b["status"] == "breach" and bool(b["breaches"]),
            "clean_quiet": c["status"] == "clear" and not c["breaches"]}


# --- seeded scenarios: constructed inputs for one real seam each, never host evidence
def _seed_rotation(root, arm):
    gm = _mods()
    res = gm.apply_rotation_invariant({"mission_id": "m-seed", "autocompact": "600k", "continue_max_tokens": 590000})
    inv = res.get("rotation_invariant") or {}
    return {"effect": {"repaired": inv.get("repaired") or {}, "continue_max_tokens": res.get("continue_max_tokens"),
                       "has_marker": "rotation_invariant" in res}}


def _seed_arm(outcome: str, reason: str):
    def run(root, arm):
        res = _mods().arm_preflight(str(root), "/gsd-autonomous", launch=False,
                                    status_reader=lambda c, w: {"outcome": outcome, "reason": reason})
        return {"effect": {"ok": res["ok"], "refusal": res["refusal"]}}
    return run


def _seed_renewal(rec: dict, halt: str, gsd: str, spent: int):
    def run(root, arm):
        why = _mods().renewal_refusal(dict(rec), halt, gsd)
        auth = rec.get("authority_tokens")
        return {"effect": {"refusal": why},
                "fc06_inputs": {"capital": {"authority": auth, "topups": [],
                                            "grants": [{"kind": "renewal", "amount": spent, "granted": why is None}]}}}
    return run


def _seed_spend(rec: dict, spent: int, fp=None):
    def run(root, arm):
        import mission_spend as ms
        res = ms.judge(dict(rec), spent, fp)
        auth = rec.get("authority_tokens")
        return {"effect": {"trip": bool(res.get("trip")), "level": res.get("level")},
                "fc06_inputs": {"capital": {"authority": auth, "topups": [],
                                            "grants": [{"kind": "spend", "amount": spent, "granted": not res.get("trip")}]}}}
    return run


def _seed_digest(match: bool):
    def run(root, arm):
        pkt = root / "packet.md"
        pkt.write_bytes(b"packet body\n")
        stored = hashlib.sha256(b"packet body\n" if match else b"another packet body\n").hexdigest()
        admitted = _mods()._packet_digest_matches(stored, str(pkt))
        return {"effect": {"admitted": bool(admitted)},
                "fc06_inputs": {"digests": [{"stored": stored, "path": str(pkt), "admitted": bool(admitted)}]}}
    return run


def _seed_receipt(done: bool):
    def run(root, arm):
        rcp = root / "receipt.md"
        rcp.write_text("# Receipt\nStatus: " + ("DONE" if done else "IN PROGRESS") + "\n", encoding="utf-8")
        truth = _originals()["is_done"](rcp)
        if truth is not done:                              # the S5 fixture incident: read is_done BEFORE trusting a fixture
            raise AssertionError(f"seed receipt reads is_done={truth}, intended {done}")
        claimed = _mods().receipt_complete(rcp)
        return {"effect": {"done_claimed": bool(claimed)},
                "fc06_inputs": {"done": [{"path": str(rcp), "claimed": bool(claimed)}]}}
    return run


def _seed_blocker(reason: str):
    def run(root, arm):
        import blocker_compiler as bc
        comp = bc.compile_blocker(reason, cwd=None)
        return {"effect": {"class": comp["class"], "owner_required": comp["owner_required"], "rule": comp["rule"]},
                "fc06_inputs": {"resolved": [{"text": reason, "owner_required": bool(comp["owner_required"])}]}}
    return run


_REN = {"mission_id": "m-seed", "epoch": 2, "renewal": 0, "token_estimate": 5_000_000, "authority_tokens": 9_000_000}
SEEDED = {
    "rotation_over_line": ("S1", "gsd_mission.apply_rotation_invariant", _seed_rotation),
    "arm_no_phases": ("S2", "gsd_mission.arm_preflight", _seed_arm("NO_PHASES", "GSD parses 0 phases from ROADMAP.md")),
    "arm_phases_remain": ("S2", "gsd_mission.arm_preflight", _seed_arm("OK", "phases remain")),
    "renewal_clean": ("renewal", "gsd_mission.renewal_refusal",
                      _seed_renewal(_REN, "budget: tokens", "OK", 4_000_000)),
    "renewal_cap_reached": ("renewal", "gsd_mission.renewal_refusal",
                            _seed_renewal({**_REN, "renewal": 3}, "budget: tokens", "OK", 4_000_000)),
    "renewal_authority_exhausted": ("renewal", "gsd_mission.renewal_refusal", _seed_renewal(
        {**_REN, "owner_hold": {"reason": "cost breaker (mission authority): processed 9,100,000 >= authority 9,000,000"}},
        "budget: tokens", "OK", 9_100_000)),
    "renewal_owner_hold": ("renewal", "gsd_mission.renewal_refusal", _seed_renewal(
        {**_REN, "owner_hold": {"reason": "owner park"}}, "budget: tokens", "OK", 4_000_000)),
    "renewal_never_launched": ("renewal", "gsd_mission.renewal_refusal",
                               _seed_renewal({**_REN, "epoch": 0}, "budget: tokens", "OK", 4_000_000)),
    "spend_within_authority": ("S4", "mission_spend.judge", _seed_spend(
        {"mission_id": "m-seed", "token_estimate": 600000, "authority_tokens": 1_000_000}, 300_000)),
    "spend_over_authority": ("S4", "mission_spend.judge", _seed_spend(
        {"mission_id": "m-seed", "token_estimate": 100000, "authority_tokens": 1_000_000}, 1_200_000)),
    "spend_no_authority": ("S4", "mission_spend.judge", _seed_spend(
        {"mission_id": "m-seed", "token_estimate": 100000, "token_estimate_src": "auto"}, 500_000)),
    "packet_digest_mismatch": ("admission", "gsd_mission._packet_digest_matches", _seed_digest(False)),
    "packet_digest_match": ("admission", "gsd_mission._packet_digest_matches", _seed_digest(True)),
    "receipt_not_done": ("S5", "gsd_mission.receipt_complete -> receipt_judge.is_done", _seed_receipt(False)),
    "receipt_done": ("S5", "gsd_mission.receipt_complete -> receipt_judge.is_done", _seed_receipt(True)),
    "blocker_capital": ("S6", "blocker_compiler.compile_blocker", _seed_blocker(
        "capital ceiling exhausted: the Owner must approve a top-up before work continues")),
    "blocker_force_push": ("S6", "blocker_compiler.compile_blocker", _seed_blocker(
        "needs a force-push of the rebased main branch")),
    "blocker_branch_protection": ("S6", "blocker_compiler.compile_blocker", _seed_blocker(
        "needs the branch protection on main relaxed so the merge can land")),
    "blocker_ordinary": ("S6", "blocker_compiler.compile_blocker", _seed_blocker(
        "rename the local helper variable in the scratch file")),
}


def _scrub(inputs):
    """Seeded inputs name temp files; the report keeps only the file's basename so two replays are byte-identical."""
    if not inputs:
        return inputs
    out = json.loads(json.dumps(inputs, default=str))
    for k in ("digests", "done"):
        for d in out.get(k) or []:
            if d.get("path"):
                d["path"] = Path(d["path"]).name
    return out


def run_seeded() -> list[dict]:
    """Every seeded scenario through the real seams under both policies. Reported apart; never counted as host evidence."""
    _originals()
    out = []
    for name in sorted(SEEDED):
        slice_, seam, fn = SEEDED[name]
        eff, inputs = {}, None
        for arm in ("champion", "challenger"):
            with sandbox() as root, policy_scope(arm):
                try:
                    r = fn(root, arm)
                    eff[arm] = r["effect"]
                    if arm == "challenger":
                        inputs = r.get("fc06_inputs")
                        st = fc06_status(inputs)          # judged inside the sandbox: files the check reads still exist
                except Exception as exc:  # noqa: BLE001 -- an instrument that raises measured nothing
                    eff[arm] = {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}
                    st = fc06_status(None)
        out.append({"id": "seed:" + name, "section": "seeded", "constructed": True, "slice": slice_, "seam": seam,
                    "champion": eff["champion"], "challenger": eff["challenger"], "fc06_inputs": _scrub(inputs),
                    "fc06": {"status": {a: st[a]["status"] for a in ASSERTIONS},
                             "breaches": [b for a in ASSERTIONS for b in st[a]["breaches"]]},
                    "effect_digest": effect_digest(eff["champion"], eff["challenger"])})
    return out


# --- policy mutants (D-05): attribute patches on the real modules, restored in a finally block
MUTANT_CALLS: dict[str, int] = {}


def _called(name: str) -> None:
    MUTANT_CALLS[name] = MUTANT_CALLS.get(name, 0) + 1


def mutant_admit_arm_preflight(cwd, resume_command, *, workstream=None, launch=True, status_reader=None,
                               memory_reader=None, **kw):
    _called("mutant_admit_arm_preflight")
    return {"ok": True, "checks": [{"check": "gsd_status", "status": "ok", "why": "mutant"}], "refusal": None}


def mutant_admit_packet_digest(stored, path):
    _called("mutant_admit_packet_digest")
    return True


def mutant_keep_rotation_invariant(rec):
    _called("mutant_keep_rotation_invariant")
    return rec


def mutant_renew_refusal(rec, halt_reason, gsd_outcome):
    _called("mutant_renew_refusal")
    return None


def mutant_proofless_is_done(path):
    _called("mutant_proofless_is_done")
    return True


def mutant_classless_compile_blocker(*a, **k):
    _called("mutant_classless_compile_blocker")
    out = dict(_originals()["compile_blocker"](*a, **k))
    out["class"], out["owner_required"] = None, False
    return out


def mutant_never_trip_judge(rec, spent, fp, as_of=None, now=None):
    _called("mutant_never_trip_judge")
    return {"trip": None, "mark": None}


def mutant_never_owner_classify(question, *, authorized=()):
    _called("mutant_never_owner_classify")
    return {"owner": "AGENT", "category": "self-answerable", "reversibility": None, "why": "mutant"}


MUTANTS = {
    "always-admit": {"intent": "arm_preflight refuses nothing and every packet digest matches",
                     "targets": [("gsd_mission", "arm_preflight", mutant_admit_arm_preflight),
                                 ("gsd_mission", "_packet_digest_matches", mutant_admit_packet_digest)]},
    "never-rotate": {"intent": "apply_rotation_invariant returns its record unchanged",
                     "targets": [("gsd_mission", "apply_rotation_invariant", mutant_keep_rotation_invariant)]},
    "always-renew": {"intent": "renewal_refusal returns None for every halt",
                     "targets": [("gsd_mission", "renewal_refusal", mutant_renew_refusal)]},
    "terminal-without-proof": {"intent": "receipt_judge.is_done is true for every path",
                               "targets": [("receipt_judge", "is_done", mutant_proofless_is_done)]},
    "drop-blocker-class": {"intent": "compile_blocker returns no class and owner_required false",
                           "targets": [("blocker_compiler", "compile_blocker", mutant_classless_compile_blocker)]},
    "expand-authority": {"intent": "mission_spend.judge never trips and the autonomy gate never answers Owner",
                         "targets": [("mission_spend", "judge", mutant_never_trip_judge),
                                     ("modules.autonomy_gate.gate", "classify", mutant_never_owner_classify)]},
}


def _module(name: str):
    import importlib
    root = str(TOOLS.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    return importlib.import_module(name)


@contextlib.contextmanager
def mutant_scope(name: str):
    """Install the named mutant's stubs on the real modules for the block and put the original objects back in a finally."""
    if name not in MUTANTS:
        raise ValueError(f"unknown mutant {name!r}")
    _originals()                                        # snapshot BEFORE any patch
    MUTANT_CALLS.clear()
    saved = []
    try:
        with sandbox():
            _mods()
        for modname, attr, stub in MUTANTS[name]["targets"]:
            mod = _module(modname)
            saved.append((mod, attr, getattr(mod, attr)))
            setattr(mod, attr, stub)
        yield
    finally:
        for mod, attr, prev in reversed(saved):
            setattr(mod, attr, prev)


def renewal_scenarios(res: dict) -> list[dict]:
    """Renewal-axis items as comparable scenarios (labelled sensitivity, outside the S2-S6 totals)."""
    out = []
    for it in res["renewal_axis"]["items"]:
        eff = {k: it.get(k) for k in ("unmeasured", "gsd_outcome", "refusal_unset", "refusal_off")}
        out.append({"id": "renewal:" + _short(it["mission_id"], it["halt_ts"]), "effect_digest": effect_digest(eff, eff),
                    "fc06": {"breaches": []}})
    return out


def _scenario_view(res: dict) -> dict:
    host = {i["id"]: i["effect_digest"] for i in res["incidents"]}
    host.update({s["id"]: s["effect_digest"] for s in renewal_scenarios(res)})
    seeded = {s["id"]: s["effect_digest"] for s in res["seeded"]}
    hb = sum(len(i["fc06"]["breaches"]) for i in res["incidents"])
    sb = sum(len(s["fc06"]["breaches"]) for s in res["seeded"])
    return {"host": host, "seeded": seeded, "host_breaches": hb, "seeded_breaches": sb}


def compare_mutant(name: str, base: dict, mut: dict) -> dict:
    """Caught = the set of (scenario, effect digest) differs from the challenger's, or FC-06 breaches exceed its count.
    Identical on every scenario with no extra breach = HARNESS_DEFECT, never a pass."""
    b, m = _scenario_view(base), _scenario_view(mut)
    diff_host = sorted(k for k in set(b["host"]) | set(m["host"]) if b["host"].get(k) != m["host"].get(k))
    diff_seed = sorted(k for k in set(b["seeded"]) | set(m["seeded"]) if b["seeded"].get(k) != m["seeded"].get(k))
    more_host, more_seed = m["host_breaches"] > b["host_breaches"], m["seeded_breaches"] > b["seeded_breaches"]
    by_host, by_seed = bool(diff_host) or more_host, bool(diff_seed) or more_seed
    caught = by_host or by_seed
    return {"name": name, "intent": MUTANTS[name]["intent"], "caught": caught,
            "caught_by": "both" if by_host and by_seed else "host" if by_host else "seeded" if by_seed else "none",
            "differing_scenarios": diff_host + diff_seed, "differing_host": len(diff_host),
            "differing_seeded": len(diff_seed),
            "fc06_breaches": m["host_breaches"] + m["seeded_breaches"],
            "fc06_breaches_challenger": b["host_breaches"] + b["seeded_breaches"],
            "stub_calls": dict(MUTANT_CALLS), "harness_defect": not caught}


def run_mutant(name: str, pin_path, base: dict) -> dict:
    with mutant_scope(name):
        mut = replay(pin_path)
        calls = dict(MUTANT_CALLS)
    out = compare_mutant(name, base, mut)
    out["stub_calls"] = calls
    return out


def run_mutants(pin_path, base: dict) -> list[dict]:
    return [run_mutant(n, pin_path, base) for n in MUTANTS]


def fc06_summary(res: dict) -> dict:
    inc_b = [b for i in res["incidents"] for b in i["fc06"]["breaches"]]
    seed_b = [b for s in res["seeded"] for b in s["fc06"]["breaches"]]
    table = {}
    for a in ASSERTIONS:
        row = {}
        for label, items in (("host", res["incidents"]), ("seeded", res["seeded"])):
            c = {"breach": 0, "clear": 0, "not_applicable": 0}
            for i in items:
                c[i["fc06"]["status"][a]] += 1
            row[label] = c
        table[a] = row
    return {"challenger_breaches": len(inc_b) + len(seed_b), "host_breaches": inc_b, "seeded_breaches": seed_b,
            "table": table, "selftest": fc06_selftest()}


def run_status(res: dict, mutants: list | None) -> tuple[int, list[str]]:
    """Exit code and lines. FC-06 first: a breach is a hard failure whatever the verdict totals or any speed gain say."""
    lines, rc = [], 0
    fc = res["fc06"]
    if fc["challenger_breaches"]:
        rc = 3
        lines.append(f"FC-06 BREACH x{fc['challenger_breaches']}: " + "; ".join(
            f"{b['assertion']}: {b['detail']}" for b in fc["host_breaches"] + fc["seeded_breaches"]))
    for m in mutants or []:
        if m["harness_defect"]:
            rc = rc or 4
            lines.append(f"HARNESS_DEFECT: mutant {m['name']} replays identical to the challenger")
        elif not m["caught"]:
            rc = rc or 4
            lines.append(f"MUTANT NOT CAUGHT: {m['name']}")
    return rc, lines


# ---------------------------------------------------------------------------------------------------- replay
def replay(pin_path: str | Path, command: str | None = None) -> dict:
    pn = load_pin(pin_path)
    rows, torn = read_prefix(pn)                         # raises Inconclusive on a mismatch
    records, drift = read_records(pn)
    now = _epoch(pn.get("last_ts")) or 0.0
    loops = detect_loops(rows)
    incidents = []
    for lp in loops:
        m = _GSD_HOLD.match(lp["reason"]) if lp["kind"] == "relay_held" else None
        if m:
            incidents.append(s3_incident(rows, lp, records, drift))
            if m.group(1) in ("NO_PHASES", "ALL_COMPLETE"):
                incidents.append(s2_incident(rows, lp, records, drift))
    with sandbox():                                      # first import of the decision modules happens inside the sandbox
        incidents += s6_incidents(rows)
        incidents += s4_incidents(rows)
        incidents += s1_incidents(rows)
        s5, s5_rep = s5_incidents(rows, records, drift, now)
        incidents += s5
        renewal = renewal_axis(rows, records, drift)
    incidents += provider_incidents(rows)
    incidents += unmapped_incidents(rows, loops)
    _originals()
    seeded = run_seeded()
    for inc in incidents:
        validate_verdict(inc["verdict"])
        attach_fc06(inc)
        inc["id"] = _short(inc["slice"], inc["kind"], inc["mission_id"], inc["first_ts"], inc.get("trip_class"))
        inc["effect_digest"] = effect_digest(inc["champion"], inc["challenger"])
    incidents.sort(key=lambda i: (i["first_ts"] or "", i["slice"], i["kind"], i["mission_id"] or "", i["id"]))
    counts = {v: sum(1 for i in incidents if i["verdict"] == v) for v in VERDICTS}
    by_slice = {sl: {v: sum(1 for i in incidents if i["slice"] == sl and i["verdict"] == v) for v in VERDICTS}
                for sl in sorted({i["slice"] for i in incidents})}
    cov = coverage(rows, loops)
    cens = _census_cross_check(rows)
    res = {"schema": SCHEMA,
            "command": command or f"python3 tools/flow_replay.py replay --pin {pin_path}",
            "pin": {"path": str(pin_path), "ledger": pn["ledger"], "bytes": pn["bytes"], "rows": pn["rows"],
                    "sha256": pn["sha256"]},
            "held": dict(HELD), "policies": {k: dict(v) for k, v in POLICIES.items()},
            "tolerances": {"LOOP_MIN": LOOP_MIN, "REDUCTION_MIN": REDUCTION_MIN, "FAITHFUL_TOL": FAITHFUL_TOL,
                           "PASS_CAP": PASS_CAP},
            "torn_rows": torn, "record_drift": sorted(drift), "loops_found": len(loops),
            "coverage": cov, "census_cross_check": cens, "incidents": incidents,
            "counts_by_verdict": counts, "counts_by_slice": by_slice, "s5": s5_rep, "renewal_axis": renewal,
            "seeded": seeded}
    res["fc06"] = fc06_summary(res)
    return res


def _census_cross_check(rows: list[dict]) -> dict:
    """The S6 population against the Phase 6 census snapshot (55 mission_blocked rows when it was taken): the pinned
    prefix may differ, and the difference is printed, not asserted equal."""
    now_n = sum(1 for r in rows if r.get("event") == "mission_blocked")
    return {"mission_blocked_at_phase6_snapshot": 55, "mission_blocked_in_pin": now_n, "difference": now_n - 55,
            "source": "06-CENSUS.md"}


# ---------------------------------------------------------------------------------------------------- time accounting
def _terminal_ts(rows: list[dict]) -> float | None:
    import gsd_epoch as ge
    return next((_epoch(r.get("ts")) for r in rows if ge.is_terminal_row(r)), None)


def mission_windows(rows: list[dict], end_of_pin: float) -> dict:
    """{mission: {start, end, open_at_pin, unmeasured}}; a mission with no usable start is listed, not counted."""
    by: dict[str, list[dict]] = {}
    for r in rows:
        if _mid(r):
            by.setdefault(_mid(r), []).append(r)
    out = {}
    for mid, rs in by.items():
        start = _epoch(rs[0].get("ts"))
        end = _terminal_ts(rs)
        if start is None:
            out[mid] = {"start": None, "end": None, "unmeasured": "no_start_in_prefix"}
        elif end is None:
            out[mid] = {"start": start, "end": end_of_pin, "open_at_pin": True, "unmeasured": None}
        else:
            out[mid] = {"start": start, "end": end, "open_at_pin": False, "unmeasured": None}
    return out


def summed_mission_hours(windows: dict) -> dict:
    """NUMBER 1: sum over missions of (end - start). Concurrent missions add."""
    ok = {m: w for m, w in windows.items() if w["unmeasured"] is None}
    return {"hours": round(sum(w["end"] - w["start"] for w in ok.values()) / 3600, 3), "missions": len(ok),
            "open_at_pin": sum(1 for w in ok.values() if w.get("open_at_pin")),
            "left_out": sorted(m for m, w in windows.items() if w["unmeasured"] is not None)}


def wall_clock_hours(windows: dict, first_launch: float | None, last_row: float | None) -> dict:
    """NUMBER 2: first launch to the last row of the window as ONE interval."""
    if first_launch is None or last_row is None:
        return {"hours": None, "unmeasured": "no_launch_in_prefix"}
    return {"hours": round((last_row - first_launch) / 3600, 3), "from": _iso(first_launch), "to": _iso(last_row)}


def critical_path_hours(rows: list[dict], windows: dict, records: dict) -> dict:
    """NUMBER 3: the longest chain of dependent missions by successor link, head start to tail end, gaps included."""
    import mission_reconcile as mrc
    by: dict[str, list[dict]] = {}
    for r in rows:
        if _mid(r):
            by.setdefault(_mid(r), []).append(r)
    succ = {}
    for mid, rs in by.items():
        sid, _how = mrc._successor_id(mid, rs, records.get(mid, {}))
        if not sid:
            for r in rs:
                m = re.search(r"superseded by (m-[0-9a-f]+)", str(r.get("reason") or "")) if r.get("event") == "mission_superseded" else None
                if m:
                    sid = m.group(1)
        if sid and sid in by and sid != mid:
            succ[mid] = sid
    heads = [m for m in by if m not in set(succ.values())]
    best = {"hours": 0.0, "chain": [], "unmeasured": []}
    for h in sorted(heads):
        chain, cur, seen = [h], h, {h}
        while cur in succ and succ[cur] not in seen:
            cur = succ[cur]
            chain.append(cur)
            seen.add(cur)
        if any(windows.get(m, {}).get("unmeasured") for m in (chain[0], chain[-1])):
            best["unmeasured"].append(h)
            continue
        hrs = (windows[chain[-1]]["end"] - windows[chain[0]]["start"]) / 3600
        if hrs > best["hours"]:
            best.update(hours=round(hrs, 3), chain=chain)
    best["basis"] = "ledger_lineage"
    best["chain_len"] = len(best["chain"])
    return best


def time_accounting(rows: list[dict], records: dict) -> dict:
    end = _epoch(rows[-1].get("ts")) if rows else None
    first = next((_epoch(r["ts"]) for r in rows if r.get("event") == "launch_claimed"), None)
    win = mission_windows(rows, end or 0.0)
    return {"definitions": {
        "summed_mission_hours": "sum over missions of (end - start); concurrent missions add",
        "wall_clock_hours": "first launch to last row of the window as one interval",
        "critical_path_wall_clock_hours": "longest successor chain, head start to tail end, gaps included"},
        "summed_mission_hours": summed_mission_hours(win),
        "wall_clock_hours": wall_clock_hours(win, first, end),
        "critical_path_wall_clock_hours": critical_path_hours(rows, win, records)}


# ---------------------------------------------------------------------------------------------------- avoidable idle
_BLOCKING = ("owner_hold_set", "mission_blocked", "quota_held", "provider_held", "cost_breaker_tripped",
             "mission_halted", "recovery_owner_boundary", "launch_held", "launch_held_cwd")


def _gap_record(rows: list[dict], mid: str, upto: int) -> dict | None:
    """The record as the ledger supports it at row index `upto`, or None when it cannot be rebuilt."""
    gm = _mods()
    mine = [r for r in rows[:upto + 1] if _mid(r) == mid]
    st = next((r for r in reversed(mine) if r.get("state")), None)
    sid = next((r.get("worker") for r in reversed(mine) if r.get("worker")), None)
    if not mine or st is None or (not sid and st["state"] != "PREPARED"):
        return None
    hold = None
    for r in mine:
        if r["event"] == "owner_hold_set":
            hold = {"reason": r.get("reason"), "kind": r.get("kind")}
        elif r["event"] in ("owner_hold_released", "hold_settled"):
            hold = None
    rec = {"mission_id": mid, "state": st["state"], "epoch": st.get("epoch")}
    if sid:   # the ledger records no owner kind; every recorded launch is a host-backgrounded worker
        rec["owner"] = {"session_id": sid, "pid": 1, "kind": "background"}
    if hold:
        rec["owner_hold"] = hold
    return rec


def idle_gaps(rows: list[dict]) -> list[dict]:
    """Quiet intervals of one mission: its last row of epoch N to the launch_claimed of epoch N+1, or to its terminal
    row. Basis inferred: the ledger records no explicit worker-end row."""
    import gsd_epoch as ge
    out = []
    by: dict[str, list[tuple[int, dict]]] = {}
    for i, r in enumerate(rows):
        if _mid(r):
            by.setdefault(_mid(r), []).append((i, r))
    for mid, ir in by.items():
        for k in range(1, len(ir)):
            i, r = ir[k]
            if r.get("event") != "launch_claimed":
                continue
            j, prev = ir[k - 1]
            t0, t1 = _epoch(prev.get("ts")), _epoch(r.get("ts"))
            if t0 is None or t1 is None or t1 <= t0:
                continue
            inside = [x for _, x in ir if t0 < (_epoch(x.get("ts")) or 0) < t1]
            out.append({"mission_id": mid, "start_idx": j, "start": t0, "end": t1, "hours": (t1 - t0) / 3600,
                        "ends_at": "launch_claimed", "inside": sorted({x["event"] for x in inside})})
    return out


def classify_gap(rows: list[dict], gap: dict, plan_next=None) -> dict:
    """Run the REAL plan_next on the record at the gap start with an always-dead pid_alive."""
    gm = _mods()
    pn = plan_next or gm.plan_next
    rec = _gap_record(rows, gap["mission_id"], gap["start_idx"])
    if rec is None:
        return {**gap, "class": "inputs_incomplete", "reason": "record not rebuildable from the ledger"}
    ans = pn(rec, gap["start"] + 1.0, [], pid_alive=lambda p: False, blocked_probe=lambda *a: None)
    action = ans.get("action")
    blocking = [e for e in gap["inside"] if e in _BLOCKING]
    if action in ("launch", "replace", "relay", "recover") and not rec.get("owner_hold") and not blocking:
        return {**gap, "class": "avoidable", "plan_next": action, "reason": ans.get("reason")}
    return {**gap, "class": "legitimate", "plan_next": action,
            "reason": ans.get("reason") if action not in ("launch", "replace", "relay", "recover")
            else "ledger shows " + ", ".join(blocking)}


def avoidable_idle(rows: list[dict], s2_missions: set | None = None, plan_next=None) -> dict:
    """Champion = gaps as recorded. Challenger recomputes only the gaps a seam changes (an S2 refusal removes the idle
    that follows a launch of a mission that would never have been armed); the rest are carried_unchanged."""
    cls = [classify_gap(rows, g, plan_next) for g in idle_gaps(rows)]
    s2 = s2_missions or set()
    for c in cls:
        c["challenger"] = ("removed_by_S2" if c["class"] == "avoidable" and c["mission_id"] in s2
                           else "carried_unchanged")
    h = lambda f: round(sum(c["hours"] for c in cls if f(c)), 3)  # noqa: E731
    before = h(lambda c: c["class"] == "avoidable")
    after = h(lambda c: c["class"] == "avoidable" and c["challenger"] == "carried_unchanged")
    return {"gaps": len(cls), "by_class": {k: sum(1 for c in cls if c["class"] == k)
                                           for k in ("avoidable", "legitimate", "inputs_incomplete")},
            "avoidable_h_before": before, "avoidable_h_after": after,
            "legitimate_h": h(lambda c: c["class"] == "legitimate"),
            "unmeasured_h": h(lambda c: c["class"] == "inputs_incomplete"),
            "moved": [{"mission_id": c["mission_id"], "hours": round(c["hours"], 3)} for c in cls
                      if c["challenger"] == "removed_by_S2"],
            "carried_unchanged": sum(1 for c in cls if c["challenger"] == "carried_unchanged"),
            "basis": "inferred: gap start is the mission's last row before the next launch (no worker-end row exists); the owner is rebuilt as a host-backgrounded worker, which plan_next leaves to the host (UNKNOWN -> none)",
            "note": "a challenger figure for a gap no seam recomputed is the champion figure, not a measured gain"}


# ---------------------------------------------------------------------------------------------------- S8 sentence
def s8_sentence(rows: list[dict]) -> dict:
    """Counts from RECORDED fields only. compile_blocker is never called with a cwd here (W2)."""
    blocked = [r for r in rows if r.get("event") == "mission_blocked"]
    have = [r for r in blocked if "independent_work" in r]
    true = [r for r in have if r.get("independent_work") is True]
    pre = len(blocked) - len(have)
    tail = ("W3: the recorded mission_blocked row carries no unblock_condition/independent_reason, so why a value is "
            "false is not recoverable; the replay does not need it. The replay does not depend on W2 "
            "(compile_blocker is called with cwd=None).")
    if true:
        ids = sorted({_mid(r) for r in true})
        form, body = "consumer_found", (f"S8 consumer found: {len(true)} of {len(have)} recorded independent_work "
                                        f"values are true (missions {', '.join(ids)}).")
    elif have:
        form, body = "none_found", f"S8: no consumer found among {len(have)} measured rows (0 true)."
    else:
        form, body = "unmeasured", ("S8 unmeasured: no recorded independent_work values exist yet; S8 stays dormant "
                                    "for lack of evidence.")
    return {"form": form, "recorded": len(have), "true": len(true), "pre_s6_unmeasured": pre,
            "sentence": f"{body} {pre} pre-S6 mission_blocked rows are unmeasured. {tail}"}


# ---------------------------------------------------------------------------------------------------- report
def tag(section, command: str, pin_sha: str):
    """Wrap a section so it carries the command and pin hash that produced it."""
    return {"_tag": {"command": command, "pin_sha256": pin_sha}, "data": section}


def validate_tagged(report: dict, path: str = "") -> None:
    """Raise when a numeric-bearing section lacks its tag."""
    for k, v in report.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and "data" in v and "_tag" in v:
            t = v["_tag"]
            if not (isinstance(t, dict) and t.get("command") and t.get("pin_sha256")):
                raise ValueError(f"section {path + k} has an empty tag")
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            raise ValueError(f"untagged number at {path + k}")
        elif isinstance(v, dict):
            validate_tagged(v, path + k + ".")
        elif isinstance(v, list) and any(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
            raise ValueError(f"untagged numbers at {path + k}")


def build_report(res: dict, rows: list[dict], records: dict, generated_at: str | None = None,
                 mutants: list | None = None) -> dict:
    cmd, sha_ = res["command"], res["pin"]["sha256"]
    s2m = {i["mission_id"] for i in res["incidents"] if i["slice"] == "S2" and i["verdict"] != "UNMEASURED"}
    rep = {
        "schema": "flow-replay-report/1",
        "pin": tag(res["pin"], cmd, sha_),
        "held": tag(res["held"], cmd, sha_),
        "policies": tag(res["policies"], cmd, sha_),
        "tolerances": tag(res["tolerances"], cmd, sha_),
        "verdict_totals": tag({"measured": {v: res["counts_by_verdict"][v] for v in VERDICTS if v != UNMEASURED},
                               "unmeasured_apart": res["counts_by_verdict"][UNMEASURED]}, cmd, sha_),
        "by_slice": tag(res["counts_by_slice"], cmd, sha_),
        "coverage": tag(res["coverage"], cmd, sha_),
        "census_cross_check": tag(res["census_cross_check"], cmd, sha_),
        "incidents": tag(res["incidents"], cmd, sha_),
        "renewal_axis": tag(res["renewal_axis"], cmd, sha_),
        "s5": tag(res["s5"], cmd, sha_),
        "fc06": tag(res["fc06"], cmd, sha_),
        "seeded": tag(res["seeded"], cmd, sha_),
        "time": tag(time_accounting(rows, records), cmd, sha_),
        "avoidable_idle": tag(avoidable_idle(rows, s2m), cmd, sha_),
        "s8": tag(s8_sentence(rows), cmd, sha_),
        "debt": tag({"W2": "compile_blocker reads ROADMAP/STATE when given a cwd; the replay passes cwd=None",
                     "W3": "mission_blocked rows lack unblock_condition/independent_reason",
                     "prior_failures": ["V-AMCR-ONE-RESOLVER-INVENTORY 37/38", "V-MSPEND-HOLD-PLAN-NONE 44/45"]},
                    cmd, sha_),
    }
    if mutants is not None:
        rep["mutants"] = tag(mutants, cmd, sha_)
    validate_tagged(rep)
    if generated_at:
        rep["generated_at"] = generated_at
    return rep


def render_md(rep: dict) -> str:
    g = lambda k: rep[k]["data"]  # noqa: E731
    cmd, sha_ = rep["incidents"]["_tag"]["command"], rep["pin"]["data"]["sha256"]
    t = g("time")
    out = [f"# S7 replay report", "", f"Command: `{cmd}`", f"Pin sha256: `{sha_}`", "",
           "## Verdicts (UNMEASURED shown beside, never inside)", ""]
    vt = g("verdict_totals")
    out += [f"- {k}: {v}" for k, v in vt["measured"].items()] + [f"- UNMEASURED (apart): {vt['unmeasured_apart']}", ""]
    cv = g("coverage")
    out += ["## Coverage", "", f"failure-class rows {cv['failure_rows_total']}; mapped to S1-S6 {cv['mapped_to_slice']}; "
            f"unmapped {cv['unmapped']}; unmapped loops {len(cv['unmapped_loops'])} (carried to Phase 8)", "",
            "## Time (three separate numbers)", ""]
    out += [f"- {k}: {t[k]}" for k in ("summed_mission_hours", "wall_clock_hours", "critical_path_wall_clock_hours")]
    out += [f"- definitions: {t['definitions']}", "", "## Avoidable idle", "", f"{g('avoidable_idle')}", "",
            "## S8", "", g("s8")["sentence"], "", "## Held group", "", f"{g('held')}", "",
            "## Incidents", "", "| slice | kind | mission | champion | challenger | verdict | basis | delta_s |",
            "|---|---|---|---|---|---|---|---|"]
    for i in g("incidents"):
        out.append(f"| {i['slice']} | {i['kind']} | {i['mission_id']} | {(i['champion'] or {}).get('count')} | "
                   f"{(i['challenger'] or {}).get('count')} | {i['verdict']} | {i['basis']} | {i['delta_s']} |")
    fc = g("fc06")
    out += ["", "## FC-06 invariants (challenger, host + seeded)", "",
            f"Challenger breaches: {fc['challenger_breaches']}", "", "| assertion | host clear/breach/n.a. | seeded clear/breach/n.a. |",
            "|---|---|---|"]
    for a_, row in fc["table"].items():
        h, sd = row["host"], row["seeded"]
        out.append(f"| {a_} | {h['clear']}/{h['breach']}/{h['not_applicable']} | {sd['clear']}/{sd['breach']}/{sd['not_applicable']} |")
    out += ["", "Self-test (breach fires, clean control quiet): " + json.dumps(fc["selftest"], sort_keys=True), "",
            "## Seeded scenarios (CONSTRUCTED; not host evidence; never counted in verdict totals)", "",
            "| scenario | seam | champion | challenger | FC-06 breaches |", "|---|---|---|---|---|"]
    for sc in g("seeded"):
        out.append(f"| {sc['id']} | {sc['seam']} | {json.dumps(sc['champion'], sort_keys=True)} | "
                   f"{json.dumps(sc['challenger'], sort_keys=True)} | {len(sc['fc06']['breaches'])} |")
    if "mutants" in rep:
        out += ["", "## Policy mutants (each must differ from the challenger)", "",
                "| mutant | caught | by | differing host | differing seeded | FC-06 breaches | stub calls |", "|---|---|---|---|---|---|---|"]
        for m in g("mutants"):
            out.append(f"| {m['name']} | {m['caught']} | {m['caught_by']} | {m['differing_host']} | {m['differing_seeded']} | "
                       f"{m['fc06_breaches']} | {sum(m['stub_calls'].values())} |")
    out += ["", f"Every number above carries command `{cmd}` and pin `{sha_[:12]}`.", ""]
    return "\n".join(out)


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
    r.add_argument("--mutants", action="store_true")
    q = sub.add_parser("report")
    q.add_argument("--pin", required=True)
    q.add_argument("--json")
    q.add_argument("--md")
    q.add_argument("--mutants", action="store_true")
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
    muts = run_mutants(a.pin, res) if a.mutants else None
    rc, msgs = run_status(res, muts)
    for m_ in msgs:
        print(m_, file=sys.stderr)
    if a.cmd == "report":
        pn = load_pin(a.pin)
        rows, _ = read_prefix(pn)
        records, _ = read_records(pn)
        rep = build_report(res, rows, records, mutants=muts)
        if a.json:
            Path(a.json).write_text(json.dumps(rep, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        if a.md:
            Path(a.md).write_text(render_md(rep), encoding="utf-8")
        print(f"REPORT pin={res['pin']['sha256'][:12]} incidents={len(res['incidents'])}")
        return rc
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"REPLAY pin={res['pin']['sha256'][:12]} incidents={len(res['incidents'])} counts={res['counts_by_verdict']}")
    if muts is not None:
        for m_ in muts:
            print(f"MUTANT {m_['name']} caught={m_['caught']} by={m_['caught_by']} calls={sum(m_['stub_calls'].values())}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
