#!/usr/bin/env python3
"""V-LG-* gates: one pre-launch authority for every successor the mission supervisor starts.

Pillars B and C of the incremental-cognition program (ledger ids B, C). Two refusals meet at the same
boundary (tools/mission_launch_gate.py, called from gsd_mission.supervise just before turn-end / stop /
continue / launch):

  C  a budget RENEWAL must not launder a quarantine. The measured a7 lineage was renewed after its dead
     iterations: plan_next halts a quarantined mission at its hours budget before any provider hold is
     consulted, GSD answers OK, the renewal is permitted, and the PREPARED successor takes the `launch`
     action, which has no owner and so never reaches the relay-only provider hold.
  B  on a DECLARED mission plane the env preflight (tools/gex44_env_preflight.py) refuses a launch when it
     measures NOT_READY. UNMEASURABLE never reads as READY and never refuses.

Hermetic: state, markers and ledger live in a temp dir set BEFORE importing gsd_mission; HOME is pointed at a
scratch dir while a scenario runs; no real ~/.claude, ~/a5-env or ~/a7-env path is read. The transcripts are
fixtures that copy the SHAPE of the measured ones. Credentials fixtures carry clearly fake canary strings.
Env vars the gate reads are cleared at import (an outer shell that sourced a deployed env.sh must not leak a
plane into the suite).

    python3 tools/test_mission_launch_gate.py            run every gate
    python3 tools/test_mission_launch_gate.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import json
import os
import sys
import tempfile
from pathlib import Path

for _var in ("CPP_ENV_PREFLIGHT", "CPP_MISSION_PLANE", "CPP_LAUNCH_GATE", "CPP_PROVIDER_BREAKER",
             "CPP_BREAKER_CRED_RELEASE", "CPP_MISSION_RENEW"):
    os.environ.pop(_var, None)

TMP = tempfile.mkdtemp(prefix="lg-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import envelope_fixture  # noqa: E402  (compiled-grammar-default law 2: lifecycle gates need a bounded mission)
envelope_fixture.bound_missions(gm)
import provider_breaker as pb  # noqa: E402
import mission_launch_gate as mlg  # noqa: E402

# Hermetic: the default fingerprint would run git in TMP, which may resolve to an enclosing repository.
gm.progress_fingerprint = lambda work_dir: None

NOW = 1_800_000_000.0
EVIDENCE_AT = NOW - 600          # the refusal row's own timestamp
LOGIN_EXPIRED = "Login expired · Please run /login"
CANARY_ACCESS = "CANARY-ACCESS-DO-NOT-PRINT"
CANARY_REFRESH = "CANARY-REFRESH-DO-NOT-PRINT"
gone = lambda pid: False   # noqa: E731

RESULTS: list[tuple[str, bool, str]] = []
QUIET = [False]


def check(name: str, cond, ev="") -> None:
    ok = bool(cond)
    RESULTS.append((name, ok, str(ev)))
    if not QUIET[0]:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {ev}")


def guarded(name: str, fn) -> None:
    """Run fn() -> (cond, evidence); an exception is a FAIL carrying its text (a missing symbol reads
    as a failing gate, never as a crash that hides the other gates)."""
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001
        cond, ev = False, f"{type(exc).__name__}: {exc}"
    check(name, cond, ev)


# --------------------------------------------------------------------------- fixtures
class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def iso(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).isoformat(timespec="seconds")


def write_transcript(directory: Path, name: str, model: str, text: str, usage_zero: bool = True) -> Path:
    """The measured shape: a user row, ONE assistant row, a turn_duration system row."""
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
             "cache_creation_input_tokens": 0} if usage_zero else {"input_tokens": 120, "output_tokens": 40}
    rows = [
        {"type": "user", "message": {"content": "go"}},
        {"type": "assistant", "timestamp": iso(EVIDENCE_AT),
         "message": {"model": model, "content": [{"type": "text", "text": text}], "usage": usage}},
        {"type": "system", "subtype": "turn_duration", "durationMs": 418},
    ]
    path = directory / f"{name}.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def write_credentials(home: Path, *, expires_ms=None, refresh_expires_ms=None, refresh=True,
                      mtime: float | None = None) -> Path:
    """A scratch credentials file. Token values are clearly fake canaries (HR-SECRET-005)."""
    d = home / ".claude"
    d.mkdir(parents=True, exist_ok=True)
    p = d / ".credentials.json"
    oauth = {"accessToken": CANARY_ACCESS, "scopes": ["user:inference"], "subscriptionType": "fake"}
    if refresh:
        oauth["refreshToken"] = CANARY_REFRESH
    if expires_ms is not None:
        oauth["expiresAt"] = expires_ms
    if refresh_expires_ms is not None:
        oauth["refreshTokenExpiresAt"] = refresh_expires_ms
    p.write_text(json.dumps({"claudeAiOauth": oauth}), encoding="utf-8")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def fresh_home(**cred) -> Path:
    h = Path(tempfile.mkdtemp(prefix="lg-home-"))
    if cred:
        write_credentials(h, **cred)
    return h


@contextlib.contextmanager
def scenario(transcript: Path | None, home: Path, env: dict | None = None):
    """Every session id resolves to `transcript`; HOME is the scratch dir; `env` is set for the scenario
    and everything touched (env vars, HOME, find_transcript) is restored in `finally`."""
    # Path.home() reads USERPROFILE on Windows and HOME elsewhere: redirect both, restore both.
    saved_find = gm.lr.find_transcript
    saved_homes = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    env = env or {}
    saved_env = {k: os.environ.get(k) for k in env}
    gm.lr.find_transcript = lambda sid: transcript
    for k in saved_homes:
        os.environ[k] = str(home)
    for k, v in env.items():
        os.environ[k] = v
    try:
        yield
    finally:
        gm.lr.find_transcript = saved_find
        for k, v in saved_homes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


_COUNTER = [0]
_RUNS = [0]


def _fresh_state(mid: str) -> str:
    # The ledger is keyed by mission id and outlives a run: a unique id per run keeps re-runs (the drill)
    # from counting each other's rows.
    _RUNS[0] += 1
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    return f"{mid}-r{_RUNS[0]}"


def _hooks():
    """Fakes shared by every drive: (launches, stops, launch_run, stop_run, gsd_ok, idle_row)."""
    launches: list = []
    stops: list = []

    def stop_run(argv):
        stops.append(argv)
        return R("stopped")

    def launch_run(argv, cwd):
        launches.append(argv)
        _COUNTER[0] += 1
        return R(f"backgrounded · bb{_COUNTER[0]:06x} · {argv[argv.index('-n') + 1]}")

    def gsd_ok(c, workstream=None):
        return {"outcome": "OK", "reason": "ok"}

    def idle_row(sid):
        return [{"sessionId": sid, "status": "idle", "state": "working", "kind": "background",
                 "id": sid[:8], "pid": 999}]
    return launches, stops, launch_run, stop_run, gsd_ok, idle_row


def names(events, ev) -> int:
    return sum(1 for e in events if e.get("event") == ev)


def drive_renewal(*, mid: str) -> dict:
    """A RUNNING mission 25 h old with a live idle owner, through the REAL supervise pass TWICE:
    pass 1 budget-halts it and renews it; pass 2 meets the PREPARED successor."""
    mid = _fresh_state(mid)
    t0 = NOW - 25 * 3600
    bg = {"session_id": f"s-{mid}", "pid": 5151, "kind": "background"}
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=t0)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=t0,
                  state=gm.RUNNING, epoch=1, owner=bg)
    launches, stops, launch_run, stop_run, gsd_ok, idle_row = _hooks()
    sessions = idle_row(bg["session_id"])
    pass1 = gm.supervise(now=NOW, sessions=sessions, gsd_status=gsd_ok, runner=launch_run,
                         stop_runner=stop_run, pid_alive=gone)
    row1 = next((r for r in pass1 if r.get("mission_id") == mid), {})
    succ = row1.get("renewed_as")
    out = {"mid": mid, "row1": row1, "successor": succ, "launches_after_pass1": len(launches),
           "pred": gm.load(mid), "held": [], "rows2": []}
    if succ:
        pass2 = gm.supervise(now=NOW, sessions=sessions, gsd_status=gsd_ok, runner=launch_run,
                             stop_runner=stop_run, pid_alive=gone)
        out["rows2"] = [r for r in pass2 if r.get("mission_id") == succ]
        out["held"] = [r.get("held") for r in out["rows2"] if r.get("held")]
        out["events"] = list(gm.lr.ledger_events(succ))
    else:
        out["events"] = []
    out["launches"] = len(launches) - out["launches_after_pass1"]
    out["stops"] = stops
    return out


def held_lineage(events, pred_id) -> list:
    return [e for e in events if e.get("event") == "provider_held" and e.get("inherited_from") == pred_id]


# --------------------------------------------------------------------------- gate groups
def grp_renewal() -> None:
    d = Path(tempfile.mkdtemp(prefix="lg-fx-"))
    syn = write_transcript(d, "synthetic-login", "<synthetic>", LOGIN_EXPIRED)
    normal = write_transcript(d, "normal-reply", "claude-opus-5-5", "Done with the step; continuing next turn.",
                              usage_zero=False)

    def precondition():
        with scenario(syn, fresh_home()):
            out = drive_renewal(mid="m-lg-pre")
        pred = out["pred"]
        ok = (bool(out["successor"]) and pred["state"] == gm.HALTED and bool((pred.get("owner") or {}).get("session_id"))
              and out["launches_after_pass1"] == 0)
        return ok, (f"renewed_as={out['successor']} predecessor={pred['state']} owner_kept="
                    f"{bool((pred.get('owner') or {}).get('session_id'))} launches_in_pass1={out['launches_after_pass1']}")
    guarded("V-LG-RENEWAL-PRECONDITION", precondition)

    def no_launder():
        with scenario(syn, fresh_home()):
            out = drive_renewal(mid="m-lg-nol")
        rows = held_lineage(out["events"], out["mid"])
        ok = (bool(out["successor"]) and out["launches"] == 0 and any("inherited" in (h or "") for h in out["held"])
              and len(rows) >= 1)
        return ok, f"launches={out['launches']} held={out['held'][:1]} provider_held(inherited_from=predecessor) rows={len(rows)}"
    guarded("V-LG-RENEWAL-NO-LAUNDER", no_launder)

    def control_healthy():
        with scenario(normal, fresh_home()):
            out = drive_renewal(mid="m-lg-ok")
        return bool(out["successor"]) and out["launches"] == 1 and not out["held"], \
            f"launches={out['launches']} held={out['held']} (predecessor's last reply is an ordinary model reply)"
    guarded("V-LG-RENEWAL-CONTROL-HEALTHY", control_healthy)

    def relogin():
        h = fresh_home(expires_ms=int((NOW + 3600) * 1000), mtime=EVIDENCE_AT + 120)
        with scenario(syn, h):
            out = drive_renewal(mid="m-lg-rel")
        return bool(out["successor"]) and out["launches"] == 1, \
            f"launches={out['launches']} (credentials rewritten after the refusal, access token usable)"
    guarded("V-LG-RENEWAL-RELOGIN-LAUNCHES", relogin)


class _Sink:
    def __init__(self, buf):
        self.buf = buf

    def write(self, text):
        self.buf.append(text)

    def flush(self):
        pass


def _record(mid: str, *, renewed_from=None, owner=None) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    kw: dict = {}
    if renewed_from:
        kw["renewed_from"] = renewed_from
    if owner:
        kw.update(state=gm.RUNNING, epoch=1, owner=owner)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, **kw)


def grp_lineage() -> None:
    d = Path(tempfile.mkdtemp(prefix="lg-fx2-"))
    syn = write_transcript(d, "synthetic-login", "<synthetic>", LOGIN_EXPIRED)

    def multihop():
        base = _fresh_state("m-lg-mh")
        p, s1, s2 = base + "-p", base + "-s1", base + "-s2"
        _record(p, owner={"session_id": f"s-{p}", "pid": 5151, "kind": "background"})
        _record(s1, renewed_from=p)
        rec2 = _record(s2, renewed_from=s1)
        with scenario(syn, fresh_home()):
            h = pb.lineage_hold(rec2, NOW)
        ok = bool(h) and h.get("inherited_from") == p and h.get("quarantine") is True and h.get("class") == "auth"
        return ok, f"hold={ {k: h[k] for k in ('class', 'quarantine', 'inherited_from')} if h else None } (S2 <- S1 <- P, only P had an owner)"
    guarded("V-LG-LINEAGE-MULTIHOP", multihop)

    def cycle():
        base = _fresh_state("m-lg-cy")
        a, b = base + "-a", base + "-b"
        _record(a, renewed_from=b)
        _record(b, renewed_from=a)
        rec_a = gm.load(a)
        calls: list = []

        def counting_load(mission_id):
            calls.append(mission_id)
            return gm.load(mission_id)
        with scenario(syn, fresh_home()):
            h = pb.lineage_hold(rec_a, NOW, load=counting_load)
        ok = h is None and len(calls) <= pb.MAX_LINEAGE_HOPS
        return ok, f"hold={h} loads={len(calls)} (cap {pb.MAX_LINEAGE_HOPS})"
    guarded("V-LG-LINEAGE-CYCLE-BOUNDED", cycle)

    def operator_surfaces():
        # WR-06: `status` and `clear` take the id the supervisor row and the logs show -- the held SUCCESSOR's
        base = _fresh_state("m-lg-op")
        p, s1, other = base + "-p", base + "-s", base + "-other"
        _record(p, owner={"session_id": f"s-{p}", "pid": 5151, "kind": "background"})
        rec_s = _record(s1, renewed_from=p)
        _record(other)

        def cli(*argv):
            buf = []
            with contextlib.redirect_stdout(_Sink(buf)):
                rc = pb._cli(list(argv))
            return rc, "".join(buf)
        saved_now = gm.lr._now_iso
        gm.lr._now_iso = lambda: iso(NOW)        # the operator's clear lands after the evidence, as it would live
        try:
            with scenario(syn, fresh_home()):
                held0 = pb.lineage_hold(rec_s, NOW)
                rc_st, out_st = cli("status", "--mission", s1)
                shown = json.loads(out_st).get("hold") if out_st.strip().startswith("{") else None
                cli("clear", "--mission", other)                       # control: another mission's clear releases nothing
                held_other = pb.lineage_hold(rec_s, NOW)
                rc_cl, out_cl = cli("clear", "--mission", s1)
                held1 = pb.lineage_hold(rec_s, NOW)
                gate = mlg.refusal(rec_s, "launch", NOW)
        finally:
            gm.lr._now_iso = saved_now
        ok = (bool(held0) and held0.get("quarantine") is True and bool(shown) and shown.get("inherited_from") == p
              and bool(held_other) and rc_cl == 0 and held1 is None and gate is None)
        return ok, (f"held_before={bool(held0)} status_shows_hold={bool(shown)} inherited_from={(shown or {}).get('inherited_from')} "
                    f"other_clear_releases={held_other is None} clear_rc={rc_cl} held_after_clear={bool(held1)} gate={gate}")
    guarded("V-LG-LINEAGE-OPERATOR-SURFACES", operator_surfaces)


# ----------------------------------------------------------------- env preflight (pillar B)
def drive_relay(*, mid: str) -> dict:
    """A healthy RUNNING mission whose owner is idle, ONE real supervise pass: the relay a launch gate must judge."""
    mid = _fresh_state(mid)
    bg = {"session_id": f"s-{mid}", "pid": 5151, "kind": "background"}
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                  state=gm.RUNNING, epoch=1, owner=bg)
    launches, stops, launch_run, stop_run, gsd_ok, idle_row = _hooks()
    rows = gm.supervise(now=NOW, sessions=idle_row(bg["session_id"]), gsd_status=gsd_ok, runner=launch_run,
                        stop_runner=stop_run, pid_alive=gone)
    row = next((r for r in rows if r.get("mission_id") == mid), {})
    return {"mid": mid, "launches": len(launches), "stops": stops, "row": row,
            "events": list(gm.lr.ledger_events(mid)), "rec": gm.load(mid)}


@contextlib.contextmanager
def spy_preflight(answer):
    """Replace mission_launch_gate.preflight (the module's own boundary) with a counting fake. `answer` is a
    verdict dict, or an exception instance to raise. Restored in `finally`."""
    calls: list = []
    saved = mlg.preflight

    def fake(now):
        calls.append(now)
        if isinstance(answer, BaseException):
            raise answer
        return answer
    mlg.preflight = fake
    try:
        yield calls
    finally:
        mlg.preflight = saved


def verdict(v: str, reasons=(), why: str = "") -> dict:
    return {"verdict": v, "reasons": list(reasons), "unmeasured": [{"check": "interpreters", "why": why}] if why else []}


def grp_preflight() -> None:
    d = Path(tempfile.mkdtemp(prefix="lg-fx3-"))
    normal = write_transcript(d, "normal-reply", "claude-opus-5-5", "Done with the step; continuing next turn.",
                              usage_zero=False)
    ON = {"CPP_ENV_PREFLIGHT": "on"}

    def run(answer, env, mid):
        with scenario(normal, fresh_home(), env):
            with spy_preflight(answer) as calls:
                out = drive_relay(mid=mid)
        out["calls"] = len(calls)
        return out

    def refuses():
        out = run(verdict("NOT_READY", ["auth_expired"]), ON, "m-lg-nr")
        ref = [e for e in out["events"] if e.get("event") == "launch_preflight_refused"]
        ok = (out["launches"] == 0 and len(ref) == 1 and "auth_expired" in (ref[0].get("reasons") or [])
              and "auth_expired" in (out["row"].get("held") or "") and out["row"].get("launch_gate") == "NOT_READY")
        return ok, f"launches={out['launches']} refused_rows={len(ref)} held={out['row'].get('held')!r}"
    guarded("V-LG-PREFLIGHT-REFUSES", refuses)

    def before_stop():
        refused = run(verdict("NOT_READY", ["auth_expired"]), ON, "m-lg-bs")
        control = run(verdict("READY"), ON, "m-lg-bsc")
        ok = (refused["launches"] == 0 and refused["stops"] == [] and refused["rec"]["epoch"] == 1
              and refused["rec"]["state"] == gm.RUNNING and len(control["stops"]) >= 1 and control["launches"] == 1)
        return ok, (f"refused: stops={len(refused['stops'])} epoch={refused['rec']['epoch']} state={refused['rec']['state']}; "
                    f"control(READY): stops={len(control['stops'])} launches={control['launches']}")
    guarded("V-LG-GATE-BEFORE-STOP", before_stop)

    def unmeasurable():
        out = run(verdict("UNMEASURABLE", why="interpreters: no engine range"), ON, "m-lg-um")
        um = names(out["events"], "launch_preflight_unmeasurable")
        ok = (out["launches"] == 1 and um == 1 and out["row"].get("launch_gate") == "UNMEASURABLE"
              and names(out["events"], "launch_preflight_refused") == 0)
        return ok, f"launches={out['launches']} unmeasurable_rows={um} launch_gate={out['row'].get('launch_gate')!r}"
    guarded("V-LG-PREFLIGHT-UNMEASURABLE-LAUNCHES", unmeasurable)

    def ready():
        out = run(verdict("READY"), ON, "m-lg-rd")
        ok = out["launches"] == 1 and out["row"].get("launch_gate") == "READY" and not out["row"].get("held")
        return ok, f"launches={out['launches']} launch_gate={out['row'].get('launch_gate')!r}"
    guarded("V-LG-PREFLIGHT-READY-LAUNCHES", ready)

    def raises():
        out = run(RuntimeError("probe blew up"), ON, "m-lg-rz")
        um = [e for e in out["events"] if e.get("event") == "launch_preflight_unmeasurable"]
        named = bool(um) and "RuntimeError" in json.dumps(um[0].get("unmeasured"))
        ok = out["launches"] == 1 and len(um) == 1 and named and out["row"].get("launch_gate") == "UNMEASURABLE"
        return ok, f"launches={out['launches']} unmeasurable_rows={len(um)} names_class={named} launch_gate={out['row'].get('launch_gate')!r}"
    guarded("V-LG-PREFLIGHT-RAISES", raises)

    def unknown_verdict():
        out = run({"verdict": "MAYBE", "reasons": []}, ON, "m-lg-uk")
        ok = out["launches"] == 1 and out["row"].get("launch_gate") == "UNMEASURABLE"
        return ok, f"launches={out['launches']} launch_gate={out['row'].get('launch_gate')!r} (an unknown answer is not READY)"
    guarded("V-LG-PREFLIGHT-UNKNOWN-IS-UNMEASURABLE", unknown_verdict)

    def plane_default_on():
        out = run(verdict("NOT_READY", ["auth_expired"]), {"CPP_MISSION_PLANE": "gex44"}, "m-lg-pl")
        return out["calls"] == 1 and out["launches"] == 0, f"preflight calls={out['calls']} launches={out['launches']} (CPP_MISSION_PLANE=gex44 alone)"
    guarded("V-LG-PLANE-DEFAULT-ON", plane_default_on)

    def preflight_off():
        a = run(verdict("NOT_READY", ["auth_expired"]), {"CPP_MISSION_PLANE": "gex44", "CPP_ENV_PREFLIGHT": "off"}, "m-lg-of1")
        b = run(verdict("NOT_READY", ["auth_expired"]), {"CPP_ENV_PREFLIGHT": "off"}, "m-lg-of2")
        ok = a["calls"] == 0 and b["calls"] == 0 and a["launches"] == 1 and b["launches"] == 1
        return ok, f"plane+off: calls={a['calls']} launches={a['launches']}; off alone: calls={b['calls']} launches={b['launches']}"
    guarded("V-LG-PREFLIGHT-OFF", preflight_off)

    def unmarked():
        out = run(verdict("NOT_READY", ["auth_expired"]), {}, "m-lg-un")
        blank = run(verdict("NOT_READY", ["auth_expired"]), {"CPP_MISSION_PLANE": "  "}, "m-lg-un2")
        ok = (out["calls"] == 0 and out["launches"] == 1 and "launch_gate" not in out["row"]
              and blank["calls"] == 0 and blank["launches"] == 1)
        return ok, f"undeclared: calls={out['calls']} launches={out['launches']} gate_key={'launch_gate' in out['row']}; blank plane: calls={blank['calls']}"
    guarded("V-LG-UNMARKED-NOT-CALLED", unmarked)

    def gate_off():
        out = run(verdict("NOT_READY", ["auth_expired"]), {"CPP_ENV_PREFLIGHT": "on", "CPP_LAUNCH_GATE": "off"}, "m-lg-go")
        syn = write_transcript(d, "synthetic-login", "<synthetic>", LOGIN_EXPIRED)
        with scenario(syn, fresh_home(), {"CPP_LAUNCH_GATE": "off"}):
            lin = drive_renewal(mid="m-lg-go2")
        ok = out["calls"] == 0 and out["launches"] == 1 and bool(lin["successor"]) and lin["launches"] == 1
        return ok, f"preflight calls={out['calls']} launches={out['launches']}; quarantined renewal launches={lin['launches']} (kill switch documented)"
    guarded("V-LG-GATE-OFF", gate_off)

    def unavailable():
        saved = sys.modules.get("mission_launch_gate")
        sys.modules["mission_launch_gate"] = None
        try:
            out = run(verdict("NOT_READY", ["auth_expired"]), ON, "m-lg-ua")
        finally:
            sys.modules["mission_launch_gate"] = saved
        n = names(out["events"], "launch_gate_unavailable")
        return out["launches"] == 1 and n >= 1, f"launches={out['launches']} launch_gate_unavailable rows={n}"
    guarded("V-LG-GATE-UNAVAILABLE", unavailable)


def grp_real_preflight() -> None:
    """No spy: the real gex44_env_preflight over a scratch HOME. The host's other checks (this node, this
    install) may add reasons of their own, so the gates are about auth_expired, not about overall READY."""
    d = Path(tempfile.mkdtemp(prefix="lg-fx4-"))
    normal = write_transcript(d, "normal-reply", "claude-opus-5-5", "Done with the step; continuing next turn.",
                              usage_zero=False)
    ON = {"CPP_ENV_PREFLIGHT": "on"}

    def e2e():
        with scenario(normal, fresh_home(expires_ms=0), ON):
            out = drive_relay(mid="m-lg-e2e")
        ref = [e for e in out["events"] if e.get("event") == "launch_preflight_refused"]
        reasons = (ref[0].get("reasons") if ref else None) or []
        ok = out["launches"] == 0 and len(ref) == 1 and "auth_expired" in reasons and out["stops"] == []
        return ok, f"launches={out['launches']} refused_rows={len(ref)} reasons={reasons} held={out['row'].get('held')!r}"
    guarded("V-LG-REAL-PREFLIGHT-E2E", e2e)

    def control():
        with scenario(normal, fresh_home(expires_ms=int((NOW + 3600) * 1000)), ON):
            out = drive_relay(mid="m-lg-e2c")
        ref = [e for e in out["events"] if e.get("event") == "launch_preflight_refused"]
        reasons = (ref[0].get("reasons") if ref else None) or []
        ran = out["row"].get("launch_gate") in ("READY", "NOT_READY", "UNMEASURABLE")
        ok = ran and "auth_expired" not in reasons
        return ok, (f"preflight ran={ran} launch_gate={out['row'].get('launch_gate')!r} launches={out['launches']} "
                    f"auth_expired in reasons={'auth_expired' in reasons} (other reasons on this host: {reasons})")
    guarded("V-LG-REAL-PREFLIGHT-CONTROL", control)


GROUPS = [grp_renewal, grp_lineage, grp_preflight, grp_real_preflight]


def run_all() -> int:
    for g in GROUPS:
        g()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"LG_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


# --------------------------------------------------------------------------- mutation drill
def _quiet(groups) -> dict[str, bool]:
    """Run groups with printing off; {gate: passed} for what they recorded."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for g in groups:
            g()
    finally:
        QUIET[0] = False
    return {n: ok for n, ok, _ in RESULTS[start:]}


def _patch(obj, attr, value):
    saved = getattr(obj, attr)
    setattr(obj, attr, value)
    return lambda: setattr(obj, attr, saved)


def _m_lineage_none():
    return _patch(pb, "lineage_hold", lambda rec, now, load=None: None)


def _m_ignore_not_ready():
    real = mlg._env

    def mutant(rec, act, now):
        res = real(rec, act, now)
        return {**res, "refuse": False}
    return _patch(mlg, "_env", mutant)


def _m_unmeasurable_refuses():
    real = mlg._env

    def mutant(rec, act, now):
        res = real(rec, act, now)
        return {**res, "refuse": True} if res.get("verdict") == "UNMEASURABLE" else res
    return _patch(mlg, "_env", mutant)


def _m_ignore_plane():
    return _patch(mlg, "preflight_enabled", lambda: os.environ.get("CPP_ENV_PREFLIGHT", "").strip().lower() == "on")


def _m_always_enabled():
    return _patch(mlg, "preflight_enabled", lambda: True)


def _m_first_hop_only():
    def mutant(rec, now, load=None):
        if not pb.enabled() or rec.get("owner"):
            return None
        pred = (load or pb._gm().load)(rec.get("renewed_from")) if rec.get("renewed_from") else None
        if not isinstance(pred, dict) or not pred.get("owner"):
            return None   # the mutation: the walk stops at the first hop
        h = pb.hold_for(pred, now)
        return None if h is None else {**h, "inherited_from": pred.get("mission_id")}
    return _patch(pb, "lineage_hold", mutant)


MUTANTS = [
    ("M1 lineage_hold always None", _m_lineage_none, [grp_renewal], ["V-LG-RENEWAL-NO-LAUNDER"]),
    ("M2 refusal ignores NOT_READY", _m_ignore_not_ready, [grp_preflight], ["V-LG-PREFLIGHT-REFUSES"]),
    ("M3 UNMEASURABLE refuses", _m_unmeasurable_refuses, [grp_preflight], ["V-LG-PREFLIGHT-UNMEASURABLE-LAUNCHES"]),
    ("M4 preflight_enabled ignores CPP_MISSION_PLANE", _m_ignore_plane, [grp_preflight], ["V-LG-PLANE-DEFAULT-ON"]),
    ("M5 preflight_enabled always True", _m_always_enabled, [grp_preflight], ["V-LG-UNMARKED-NOT-CALLED"]),
    ("M6 lineage_hold stops after the first hop", _m_first_hop_only, [grp_lineage], ["V-LG-LINEAGE-MULTIHOP"]),
]


def run_drill() -> int:
    """Each mutant is applied in-process, the gates it must kill are re-run, the mutant is restored.
    A drill whose unmutated control is red proves nothing, so the control runs first and must be green."""
    control = _quiet(GROUPS)
    control_ok = bool(control) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: "
          f"{sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, groups, targets in MUTANTS:
        restore = apply()
        try:
            seen = _quiet(groups)
        finally:
            restore()
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)}")
        else:
            survived = [t for t in targets if seen.get(t) is not False]
            print(f"SURVIVED {label} (still green: {', '.join(survived)})")
    after = _quiet(GROUPS)
    clean = bool(after) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: "
          f"{sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
