#!/usr/bin/env python3
"""V-PFP-* gates: an authorization-class failure parks a mission until a qualifying precondition change.

Pillar C of the incremental-cognition program (ledger id C). The shape under test is the one measured on
the a7 install: a worker whose ONLY reply is the host's synthetic "Login expired - Please run /login"
(model "<synthetic>", zero usage, no tool call) was relaunched on every supervisor pass, 96+ times, because
that install predates tools/provider_breaker.py and gsd_mission.provider_hold's fallback checked quota only.

Hermetic: state, markers and ledger live in a temp dir set BEFORE importing gsd_mission; HOME is pointed at a
scratch dir while a scenario runs; no real ~/.claude, ~/a5-env or ~/a7-env path is read. The transcript is a
fixture that copies the SHAPE of the measured one. Credentials fixtures carry clearly fake canary strings.

    python3 tools/test_persistent_failure_park.py            run every gate
    python3 tools/test_persistent_failure_park.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="pfp-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import envelope_fixture  # noqa: E402  (compiled-grammar-default law 2: lifecycle gates need a bounded mission)
envelope_fixture.bound_missions(gm)
import provider_breaker as pb  # noqa: E402

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
                      mtime: float | None = None, raw: str | None = None) -> Path:
    """A scratch credentials file. Token values are clearly fake canaries (HR-SECRET-005)."""
    d = home / ".claude"
    d.mkdir(parents=True, exist_ok=True)
    p = d / ".credentials.json"
    if raw is not None:
        p.write_text(raw, encoding="utf-8")
    else:
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


@contextlib.contextmanager
def scenario(transcript: Path | None, home: Path, breaker: bool):
    """Every session id resolves to `transcript` (every successor also dies on the same refusal);
    HOME is the scratch dir; the breaker import is made to fail when breaker is False (the a7 condition)."""
    # Path.home() reads USERPROFILE on Windows and HOME elsewhere: redirect both, restore both.
    saved_find = gm.lr.find_transcript
    saved_homes = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    had_pb = "provider_breaker" in sys.modules
    saved_pb = sys.modules.get("provider_breaker")
    gm.lr.find_transcript = lambda sid: transcript
    for k in saved_homes:
        os.environ[k] = str(home)
    if not breaker:
        sys.modules["provider_breaker"] = None
    try:
        yield
    finally:
        gm.lr.find_transcript = saved_find
        for k, v in saved_homes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if had_pb:
            sys.modules["provider_breaker"] = saved_pb
        else:
            sys.modules.pop("provider_breaker", None)


_COUNTER = [0]
_RUNS = [0]


def drive(cycles: int, *, mid: str) -> dict:
    """Run `cycles` relay cycles of one fresh RUNNING mission through the REAL supervise pass.
    A launched successor is advanced to owner through the REAL adopt path (the host lists the bg_id
    the fake launcher printed), never by writing the record."""
    # The ledger is keyed by mission id and outlives a run: a unique id per run keeps the drill's
    # re-runs from counting each other's rows.
    _RUNS[0] += 1
    mid = f"{mid}-r{_RUNS[0]}"
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    bg = {"session_id": f"s-{mid}", "pid": 5151, "kind": "background"}
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                  state=gm.RUNNING, epoch=1, owner=bg)
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

    sessions = idle_row(bg["session_id"])
    held_rows = []
    for _ in range(cycles):
        rows = gm.supervise(now=NOW, sessions=sessions, gsd_status=gsd_ok, runner=launch_run,
                            stop_runner=stop_run, pid_alive=gone)
        held_rows += [r.get("held") for r in rows if r.get("mission_id") == mid and r.get("held")]
        rec = gm.load(mid)
        if rec["state"] == gm.LAUNCHING:
            bg_id = rec["pending"]["bg_id"]
            listed = [{"id": bg_id, "sessionId": f"{bg_id}-0000-1111", "pid": 4000 + _COUNTER[0],
                       "kind": "background", "state": "working", "status": "busy"}]
            gm.supervise(now=NOW, sessions=listed, gsd_status=gsd_ok, runner=launch_run,
                         stop_runner=stop_run, pid_alive=gone)
            rec = gm.load(mid)
            if rec["state"] != gm.RUNNING:
                raise AssertionError(f"adopt did not reach RUNNING: {rec['state']}")
            sessions = idle_row(rec["owner"]["session_id"])
    events = [e for e in gm.lr.ledger_events(mid)]
    return {"launches": len(launches), "held": held_rows, "events": events, "rec": gm.load(mid)}


def held_auth(events) -> list:
    return [e for e in events if e.get("event") == "provider_held" and e.get("provider_class") == "auth"
            and e.get("quarantine") is True]


def names(events, ev) -> int:
    return sum(1 for e in events if e.get("event") == ev)


# --------------------------------------------------------------------------- gate groups
def grp_fallback() -> None:
    """The measured a7 condition: provider_breaker.py is unimportable."""
    d = Path(tempfile.mkdtemp(prefix="pfp-fx-"))
    home = Path(tempfile.mkdtemp(prefix="pfp-home-"))     # no .claude/.credentials.json
    syn = write_transcript(d, "synthetic-login", "<synthetic>", LOGIN_EXPIRED)

    with scenario(syn, home, breaker=False):
        out = drive(3, mid="m-pfp-fb")
    ev = held_auth(out["events"])
    # GGMC C5: held on all 3 passes (sweep rows), announced ONCE (the hold did not change), asleep on an Owner waker.
    wake = ((out["rec"].get("sleep") or {}).get("wake") or {}).get("kind")
    check("V-PFP-137-FALLBACK-PARKS", out["launches"] == 0 and len(out["held"]) == 3 and len(ev) == 1
          and wake == "owner",
          f"launches={out['launches']} held_passes={len(out['held'])} provider_held(auth,quarantine) rows={len(ev)} "
          f"wake={wake} (3 relay cycles, breaker unimportable)")
    check("V-PFP-137-FALLBACK-VISIBLE", names(out["events"], "provider_breaker_unavailable") >= 1,
          f"provider_breaker_unavailable rows={names(out['events'], 'provider_breaker_unavailable')}")

    with scenario(syn, home, breaker=True):
        out = drive(3, mid="m-pfp-br")
    check("V-PFP-137-BREAKER-PARKS", out["launches"] == 0 and any("QUARANTINED" in (h or "") for h in out["held"]),
          f"launches={out['launches']} held={out['held'][:1]}")

    normal = write_transcript(d, "normal-reply", "claude-opus-5-5", "Done with the step; continuing next turn.",
                              usage_zero=False)
    with scenario(normal, home, breaker=False):
        out = drive(1, mid="m-pfp-nr")
    check("V-PFP-FALLBACK-NORMAL-REPLY-RELAYS", out["launches"] == 1, f"launches={out['launches']}")

    quoted = write_transcript(d, "quoted-login", "claude-opus-5-5",
                              "The docs say: Please run /login if the token is stale. Moving on.", usage_zero=False)
    with scenario(quoted, home, breaker=False):
        out = drive(1, mid="m-pfp-qt")
    check("V-PFP-FALLBACK-QUOTED-NOT-PARKED", out["launches"] == 1 and not held_auth(out["events"]),
          f"launches={out['launches']} (a model quoting 'Please run /login' is not a host refusal)")

    h_old = Path(tempfile.mkdtemp(prefix="pfp-home-old-"))
    write_credentials(h_old, expires_ms=int((NOW + 3600) * 1000), mtime=EVIDENCE_AT - 3600)
    with scenario(syn, h_old, breaker=False):
        out = drive(1, mid="m-pfp-hold")
    check("V-PFP-FALLBACK-HOLDS-WITHOUT-RELOGIN", out["launches"] == 0,
          f"launches={out['launches']} (credentials older than the refusal)")

    h_new = Path(tempfile.mkdtemp(prefix="pfp-home-new-"))
    write_credentials(h_new, expires_ms=int((NOW + 3600) * 1000), mtime=EVIDENCE_AT + 120)
    with scenario(syn, h_new, breaker=False):
        out = drive(1, mid="m-pfp-rel")
    check("V-PFP-FALLBACK-RELEASES-ON-RELOGIN", out["launches"] == 1, f"launches={out['launches']}")

    # WR-07: a rewrite that leaves the login dead (or unjudgeable) must not un-park the mission
    dead = {"expiresAt 0": dict(expires_ms=0, refresh_expires_ms=int((NOW + 86400) * 1000)),
            "lapsed, refresh expiry unknown": dict(expires_ms=int((NOW - 3600) * 1000)),
            "lapsed, no refresh token": dict(expires_ms=int((NOW - 3600) * 1000), refresh=False),
            "no expiresAt": dict()}
    got = {}
    for label, kw in dead.items():
        h_dead = Path(tempfile.mkdtemp(prefix="pfp-home-dead-"))
        write_credentials(h_dead, mtime=EVIDENCE_AT + 120, **kw)
        with scenario(syn, h_dead, breaker=False):
            got[label] = drive(1, mid="m-pfp-dead")["launches"]
    check("V-PFP-FALLBACK-DEAD-REWRITE-KEEPS-PARK", all(v == 0 for v in got.values()), f"launches by rewrite shape={got}")

    h_raw = Path(tempfile.mkdtemp(prefix="pfp-home-raw-"))
    write_credentials(h_raw, raw="{not json", mtime=EVIDENCE_AT + 120)
    with scenario(syn, h_raw, breaker=False):
        out = drive(1, mid="m-pfp-rawcred")
    check("V-PFP-FALLBACK-UNREADABLE-REWRITE-KEEPS-PARK", out["launches"] == 0,
          f"launches={out['launches']} (credentials rewritten but unparseable)")

    shapes = {"future": dict(expires_ms=int((NOW + 3600) * 1000)), "zero": dict(expires_ms=0),
              "lapsed+refresh future": dict(expires_ms=int((NOW - 3600) * 1000), refresh_expires_ms=int((NOW + 3600) * 1000)),
              "lapsed+refresh past": dict(expires_ms=int((NOW - 3600) * 1000), refresh_expires_ms=int((NOW - 60) * 1000)),
              "lapsed+refresh unknown": dict(expires_ms=int((NOW - 3600) * 1000)),
              "lapsed, none": dict(expires_ms=int((NOW - 3600) * 1000), refresh=False), "no expiry": dict()}
    diffs = {}
    for label, kw in shapes.items():
        h = Path(tempfile.mkdtemp(prefix="pfp-home-par-"))
        write_credentials(h, **kw)
        try:
            with scenario(syn, h, breaker=True):
                mine = gm._credentials_usable_without_breaker(NOW)
        except Exception as exc:  # noqa: BLE001 -- a missing reader reads as a failing gate, not a crash
            mine = f"{exc.__class__.__name__}: {exc}"
        theirs = pb.credentials_expired(pb.credentials_state(home=h), NOW) is False
        if mine != theirs:
            diffs[label] = (mine, theirs)
    check("V-PFP-FALLBACK-CRED-PARITY", not diffs, f"degraded reader disagrees with provider_breaker on: {diffs}")


def grp_parity() -> None:
    try:
        same = gm.AUTH_FALLBACK_RE.pattern == pb.AUTH_RE.pattern and gm.AUTH_FALLBACK_RE.flags == pb.AUTH_RE.flags
        check("V-PFP-AUTH-PARITY", same, f"pattern/flags equal={same}")
    except AttributeError as exc:
        check("V-PFP-AUTH-PARITY", False, f"AttributeError: {exc}")


def guarded(name: str, fn) -> None:
    """Run fn() -> (cond, evidence); an exception is a FAIL carrying its text (a missing symbol reads
    as a failing gate, never as a crash that hides the other gates)."""
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001
        cond, ev = False, f"{type(exc).__name__}: {exc}"
    check(name, cond, ev)


def _home_with(**kw) -> Path:
    h = Path(tempfile.mkdtemp(prefix="pfp-cred-"))
    write_credentials(h, **kw)
    return h


def grp_cred_reader() -> None:
    ms_future = int((NOW + 3600) * 1000)
    ms_past = int((NOW - 3600) * 1000)

    def shape_only():
        h = _home_with(expires_ms=1791058001914, refresh_expires_ms=1793000000000)
        st = pb.credentials_state(home=h)
        keys = {"path", "readable", "mtime", "expires_at", "refresh_token", "refresh_expires_at", "why"}
        leaked = "CANARY" in repr(st) or CANARY_ACCESS in repr(st) or CANARY_REFRESH in repr(st)
        return set(st) == keys and not leaked and st["refresh_token"] is True, f"keys={sorted(st)} leaked={leaked}"
    guarded("V-PFP-CRED-SHAPE-ONLY", shape_only)

    def expires_ms():
        st = pb.credentials_state(home=_home_with(expires_ms=1791058001914))
        z = pb.credentials_state(home=_home_with(expires_ms=0))
        return (abs(st["expires_at"] - 1791058001.914) < 1e-6 and z["expires_at"] == 0.0
                and isinstance(z["expires_at"], float)), f"ms->s={st['expires_at']} zero={z['expires_at']!r}"
    guarded("V-PFP-CRED-EXPIRES-MS", expires_ms)

    def expired_zero():
        st = pb.credentials_state(home=_home_with(expires_ms=0, refresh_expires_ms=ms_future))
        return pb.credentials_expired(st, NOW) is True, "expiresAt 0 (the measured a7 mark) -> expired even with a live refresh"
    guarded("V-PFP-CRED-EXPIRED-ZERO", expired_zero)

    def lapsed_refreshable():
        st = pb.credentials_state(home=_home_with(expires_ms=ms_past, refresh_expires_ms=ms_future))
        return pb.credentials_expired(st, NOW) is False, "past access token, refresh token present with a FUTURE refresh expiry -> not expired"
    guarded("V-PFP-CRED-LAPSED-REFRESHABLE", lapsed_refreshable)

    def lapsed_refresh_expiry_unknown():
        # WR-04: a lapsed access token whose refresh token has no known expiry is unknown, never "usable"
        none_key = pb.credentials_state(home=_home_with(expires_ms=ms_past, mtime=NOW - 60))
        non_numeric = pb.credentials_state(home=_home_with(
            raw=json.dumps({"claudeAiOauth": {"refreshToken": CANARY_REFRESH, "expiresAt": ms_past,
                                              "refreshTokenExpiresAt": "soon"}})))
        released = pb.auth_released(NOW - 7200, none_key, NOW)
        ok = (pb.credentials_expired(none_key, NOW) is None and pb.credentials_expired(non_numeric, NOW) is None
              and released is None)
        return ok, (f"no-key expired={pb.credentials_expired(none_key, NOW)!r} non-numeric expired="
                    f"{pb.credentials_expired(non_numeric, NOW)!r} auth_released={released!r}")
    guarded("V-PFP-CRED-LAPSED-REFRESH-EXPIRY-UNKNOWN", lapsed_refresh_expiry_unknown)

    def refresh_expired():
        st = pb.credentials_state(home=_home_with(expires_ms=ms_past, refresh_expires_ms=ms_past))
        return pb.credentials_expired(st, NOW) is True, "past access token and past refresh expiry -> expired"
    guarded("V-PFP-CRED-REFRESH-EXPIRED", refresh_expired)

    def no_refresh_past():
        st = pb.credentials_state(home=_home_with(expires_ms=ms_past, refresh=False))
        fut = pb.credentials_state(home=_home_with(expires_ms=ms_future, refresh=False))
        return (pb.credentials_expired(st, NOW) is True and pb.credentials_expired(fut, NOW) is False), \
            "past + no refresh token -> expired; future -> not expired"
    guarded("V-PFP-CRED-NO-REFRESH-PAST", no_refresh_past)

    def unreadable():
        h = _home_with(raw="{not json CANARY-RAW-DO-NOT-PRINT")
        st = pb.credentials_state(home=h)
        shape = pb.credentials_state(home=_home_with(raw=json.dumps({"claudeAiOauth": "x"})))
        noexp = pb.credentials_state(home=_home_with())
        ok = (st["readable"] is False and "CANARY" not in repr(st) and shape["readable"] is False
              and pb.credentials_expired(st, NOW) is None and pb.credentials_expired(noexp, NOW) is None)
        return ok, f"bad-json why={st['why']!r} wrong-shape why={shape['why']!r} no-expiresAt expired={pb.credentials_expired(noexp, NOW)!r}"
    guarded("V-PFP-CRED-UNREADABLE", unreadable)

    def missing():
        st = pb.credentials_state(home=Path(tempfile.mkdtemp(prefix="pfp-nocred-")))
        return (st["readable"] is False and st["why"] == "missing" and st["mtime"] is None
                and pb.credentials_expired(st, NOW) is None), f"why={st['why']!r}"
    guarded("V-PFP-CRED-MISSING", missing)


def _auth_outcome(sid):
    return {"class": pb.AUTH, "text": LOGIN_EXPIRED, "at": EVIDENCE_AT}


def _cred(mtime, **kw):
    """A credentials_state-shaped dict injected into decide (no file involved)."""
    base = {"path": "fake", "readable": True, "mtime": mtime, "expires_at": NOW + 3600, "refresh_token": True,
            "refresh_expires_at": None, "why": ""}
    base.update(kw)
    return base


def grp_decide() -> None:
    def release():
        trace: dict = {}
        r = pb.decide("m-pfp-dec1", "w1", NOW, workers=["w1"], outcome=_auth_outcome, cleared_at=None,
                      credentials=lambda: _cred(EVIDENCE_AT + 60), trace=trace)
        return r is None and bool(trace.get("released")), f"hold={r} trace={trace}"
    guarded("V-PFP-RELEASE-ON-RELOGIN", release)

    def unchanged():
        r = pb.decide("m-pfp-dec2", "w1", NOW, workers=["w1"], outcome=_auth_outcome, cleared_at=None,
                      credentials=lambda: _cred(EVIDENCE_AT - 60), trace={})
        return bool(r) and r["quarantine"] is True and r["class"] == pb.AUTH, f"hold={r}"
    guarded("V-PFP-HOLD-UNCHANGED", unchanged)

    def still_expired():
        r = pb.decide("m-pfp-dec3", "w1", NOW, workers=["w1"], outcome=_auth_outcome, cleared_at=None,
                      credentials=lambda: _cred(EVIDENCE_AT + 60, expires_at=0.0), trace={})
        return bool(r) and r["quarantine"] is True, f"hold={r} (rewritten after the refusal, but expiresAt 0)"
    guarded("V-PFP-HOLD-RELOGIN-STILL-EXPIRED", still_expired)

    def unreadable():
        bad = {"path": "fake", "readable": False, "mtime": EVIDENCE_AT + 60, "expires_at": None,
               "refresh_token": False, "refresh_expires_at": None, "why": "JSONDecodeError"}
        r = pb.decide("m-pfp-dec4", "w1", NOW, workers=["w1"], outcome=_auth_outcome, cleared_at=None,
                      credentials=lambda: bad, trace={})
        return bool(r) and r["quarantine"] is True, f"hold={r}"
    guarded("V-PFP-HOLD-CRED-UNREADABLE", unreadable)

    def kill_switch():
        saved = os.environ.get("CPP_BREAKER_CRED_RELEASE")
        os.environ["CPP_BREAKER_CRED_RELEASE"] = "off"
        try:
            r = pb.decide("m-pfp-dec5", "w1", NOW, workers=["w1"], outcome=_auth_outcome, cleared_at=None,
                          credentials=lambda: _cred(EVIDENCE_AT + 60), trace={})
        finally:
            if saved is None:
                os.environ.pop("CPP_BREAKER_CRED_RELEASE", None)
            else:
                os.environ["CPP_BREAKER_CRED_RELEASE"] = saved
        return bool(r) and r["quarantine"] is True, f"hold={r}"
    guarded("V-PFP-RELEASE-KILL-SWITCH", kill_switch)

    def only_auth():
        tr = lambda sid: {"class": pb.TRANSIENT, "text": "overloaded", "at": EVIDENCE_AT}  # noqa: E731
        r = pb.decide("m-pfp-dec6", "w4", NOW, workers=["w1", "w2", "w3", "w4"], outcome=tr, cleared_at=None,
                      credentials=lambda: _cred(EVIDENCE_AT + 60), trace={})
        return bool(r) and r["quarantine"] is True and r["class"] == pb.TRANSIENT and r["streak"] == 4, f"hold={r}"
    guarded("V-PFP-RELEASE-ONLY-AUTH", only_auth)


def grp_supervise_release() -> None:
    """Breaker importable, the real fixture, the real supervise pass, a real credentials file in a scratch HOME."""
    d = Path(tempfile.mkdtemp(prefix="pfp-fx2-"))
    syn = write_transcript(d, "synthetic-login", "<synthetic>", LOGIN_EXPIRED)
    ms_future = int((NOW + 3600) * 1000)

    def relogin():
        h = _home_with(expires_ms=ms_future, mtime=EVIDENCE_AT + 120)
        with scenario(syn, h, breaker=True):
            out = drive(1, mid="m-pfp-sup-rel")
        n = names(out["events"], "provider_released")
        return out["launches"] == 1 and n == 1, f"launches={out['launches']} provider_released rows={n}"
    guarded("V-PFP-SUP-RELOGIN-RELAYS", relogin)

    def no_relogin():
        h = _home_with(expires_ms=ms_future, mtime=EVIDENCE_AT - 3600)
        with scenario(syn, h, breaker=True):
            out = drive(3, mid="m-pfp-sup-hold")
        n = names(out["events"], "provider_released")
        # GGMC C5: three held passes, one announcement (the hold never changed).
        return (out["launches"] == 0 and n == 0 and len(out["held"]) == 3
                and len(held_auth(out["events"])) == 1), \
            (f"launches={out['launches']} provider_released={n} held_passes={len(out['held'])} "
             f"provider_held(auth)={len(held_auth(out['events']))}")
    guarded("V-PFP-SUP-NO-RELOGIN-PARKS", no_relogin)


GROUPS = [grp_fallback, grp_parity, grp_cred_reader, grp_decide, grp_supervise_release]


def run_all() -> int:
    for g in GROUPS:
        g()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"PFP_PASS={passed}/{total}  threshold={total}/{total}")
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


def _m_auth_re_never_matches():
    import re
    return _patch(gm, "AUTH_FALLBACK_RE", re.compile(r"(?!x)x"))


def _m_always_released():
    return _patch(pb, "auth_released", lambda evidence_at, cred, now: "mutant: always released")


def _m_never_released():
    return _patch(pb, "auth_released", lambda evidence_at, cred, now: None)


def _m_expiry_always_false():
    return _patch(pb, "credentials_expired", lambda cred, now: False)


def _m_fallback_ignores_synthetic():
    def mutant(session_id, now):
        # the real function minus the host-written (model == "<synthetic>") requirement
        try:
            t = gm.lr.find_transcript(session_id) if session_id else None
            if not t:
                return None
            for row in reversed(gm.lr._tail_rows(t)):
                if row.get("type") != "assistant":
                    continue
                msg = row.get("message") if isinstance(row.get("message"), dict) else {}
                text = " ".join(gm.lr._text_of(msg).split())
                if not gm.AUTH_FALLBACK_RE.search(text):
                    return None
                evidence_at = gm.lr._parse_iso(row.get("timestamp")) or os.path.getmtime(t)
                try:
                    if (Path.home() / ".claude" / ".credentials.json").stat().st_mtime > evidence_at:
                        return None
                except OSError:
                    pass
                return {"until": None, "reason": "mutant", "class": "auth", "streak": 1, "quarantine": True}
            return None
        except Exception:  # noqa: BLE001
            return None
    return _patch(gm, "_auth_hold_without_breaker", mutant)


def _m_fallback_any_rewrite_releases():
    return _patch(gm, "_credentials_usable_without_breaker", lambda now: True)


MUTANTS = [
    ("M1 AUTH_FALLBACK_RE never matches", _m_auth_re_never_matches, [grp_fallback],
     ["V-PFP-137-FALLBACK-PARKS"]),
    ("M2 auth_released always releases", _m_always_released, [grp_decide], ["V-PFP-HOLD-UNCHANGED"]),
    ("M3 auth_released never releases", _m_never_released, [grp_decide, grp_supervise_release],
     ["V-PFP-RELEASE-ON-RELOGIN", "V-PFP-SUP-RELOGIN-RELAYS"]),
    ("M4 credentials_expired always False", _m_expiry_always_false, [grp_decide],
     ["V-PFP-HOLD-RELOGIN-STILL-EXPIRED"]),
    ("M5 fallback ignores the synthetic check", _m_fallback_ignores_synthetic, [grp_fallback],
     ["V-PFP-FALLBACK-QUOTED-NOT-PARKED"]),
    ("M6 fallback releases on any credentials rewrite", _m_fallback_any_rewrite_releases, [grp_fallback],
     ["V-PFP-FALLBACK-DEAD-REWRITE-KEEPS-PARK", "V-PFP-FALLBACK-UNREADABLE-REWRITE-KEEPS-PARK"]),
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
