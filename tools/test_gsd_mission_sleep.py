"""GGMC C5 -- a held mission sleeps, says what wakes it, and writes the ledger only when the hold changes.

Spec: vault/specs/goal-governed-mission-control.md (C5, Acceptance 5). Driven through the REAL supervise pass,
on the env-preflight hold (the most controllable precondition), plus the helper's own contract.

    python tools/test_gsd_mission_sleep.py           every gate
    python tools/test_gsd_mission_sleep.py --drill   each mutant must turn at least one gate red
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path

for _var in ("CPP_ENV_PREFLIGHT", "CPP_MISSION_PLANE", "CPP_LAUNCH_GATE", "CPP_PROVIDER_BREAKER",
             "CPP_BREAKER_CRED_RELEASE", "CPP_MISSION_RENEW"):
    os.environ.pop(_var, None)

TMP = tempfile.mkdtemp(prefix="sleep-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_launch_gate as mlg  # noqa: E402
import mission_sleep as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None   # hermetic: no git in TMP

NOW = 1_800_000_000.0
gone = lambda pid: False   # noqa: E731
RESULTS: list[tuple[str, bool, str]] = []
QUIET = [False]
_RUNS = [0]
_COUNTER = [0]


def check(name, cond, ev=""):
    RESULTS.append((name, bool(cond), str(ev)))
    if not QUIET[0]:
        print(f"{'PASS' if cond else 'FAIL'} {name}: {ev}")


def guarded(name, fn):
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a crash is a FAIL that names itself
        cond, ev = False, f"{type(exc).__name__}: {exc}"
    check(name, cond, ev)


class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def _transcript() -> Path:
    d = Path(tempfile.mkdtemp(prefix="sleep-fx-"))
    rows = [{"type": "user", "message": {"content": "go"}},
            {"type": "assistant", "timestamp": "2027-01-15T08:00:00+00:00",
             "message": {"model": "claude-opus-5-5", "content": [{"type": "text", "text": "Step done."}],
                         "usage": {"input_tokens": 120, "output_tokens": 40}}},
            {"type": "system", "subtype": "turn_duration", "durationMs": 418}]
    p = d / "normal.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


@contextlib.contextmanager
def world(answers: list):
    """Preflight ON; each supervise pass consumes the next verdict. HOME and find_transcript redirected."""
    saved = (gm.lr.find_transcript, mlg.preflight, {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")},
             os.environ.get("CPP_ENV_PREFLIGHT"))
    tr, home = _transcript(), tempfile.mkdtemp(prefix="sleep-home-")
    gm.lr.find_transcript = lambda sid: tr
    queue = list(answers)
    mlg.preflight = lambda now: queue.pop(0) if len(queue) > 1 else queue[0]
    for k in ("HOME", "USERPROFILE"):
        os.environ[k] = home
    os.environ["CPP_ENV_PREFLIGHT"] = "on"
    try:
        yield
    finally:
        gm.lr.find_transcript, mlg.preflight = saved[0], saved[1]
        for k, v in saved[2].items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        os.environ.pop("CPP_ENV_PREFLIGHT", None) if saved[3] is None else os.environ.__setitem__(
            "CPP_ENV_PREFLIGHT", saved[3])


def not_ready(*reasons):
    return {"verdict": "NOT_READY", "reasons": list(reasons), "unmeasured": []}


def _fresh(mid):
    _RUNS[0] += 1
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()
    return f"{mid}-r{_RUNS[0]}"


def drive(answers: list, passes: int, *, mid: str, between=None) -> dict:
    """A RUNNING mission with an idle owner, `passes` real supervise passes. `between(mid)` runs after pass 1."""
    mid = _fresh(mid)
    bg = {"session_id": f"s-{mid}", "pid": 5151, "kind": "background"}
    launches, stops, held = [], [], []

    def launch_run(argv, cwd):
        launches.append(argv)
        _COUNTER[0] += 1
        return R(f"backgrounded · bb{_COUNTER[0]:06x} · {argv[argv.index('-n') + 1]}")

    def stop_run(argv):
        stops.append(argv)
        return R("stopped")

    sessions = [{"sessionId": bg["session_id"], "status": "idle", "state": "working", "kind": "background",
                 "id": bg["session_id"][:8], "pid": 999}]
    with world(answers):
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                      state=gm.RUNNING, epoch=1, owner=bg)
        seq0 = gm.load(mid)["seq"]
        for i in range(passes):
            rows = gm.supervise(now=NOW + i, sessions=sessions, gsd_status=lambda c, workstream=None:
                                {"outcome": "OK", "reason": "ok"}, runner=launch_run, stop_runner=stop_run,
                                pid_alive=gone)
            held += [r.get("held") for r in rows if r.get("mission_id") == mid and r.get("held")]
            if i == 0 and between:
                between(mid)
    events = list(gm.lr.ledger_events(mid))
    rec = gm.load(mid)
    return {"mid": mid, "launches": len(launches), "stops": len(stops), "held": held, "rec": rec,
            "seq_delta": rec["seq"] - seq0, "refused": [e for e in events if e.get("event") == "launch_preflight_refused"]}


# ------------------------------------------------------------------------------------------- gates
def gates():
    def once():
        out = drive([not_ready("auth_expired")], 3, mid="m-sl-once")
        wake = (out["rec"].get("sleep") or {}).get("wake") or {}
        ok = (out["launches"] == 0 and out["stops"] == 0 and len(out["held"]) == 3 and len(out["refused"]) == 1
              and out["seq_delta"] == 1 and wake.get("kind") == "env_ready" and wake.get("reasons") == ["auth_expired"]
              and out["refused"][0].get("reasons") == ["auth_expired"])
        return ok, (f"launches={out['launches']} held_passes={len(out['held'])} refused_rows={len(out['refused'])} "
                    f"record_writes={out['seq_delta']} wake={wake}")
    guarded("V-SLEEP-ONE-ROW-PER-HOLD", once)

    def change():
        out = drive([not_ready("auth_expired"), not_ready("disk_low")], 2, mid="m-sl-chg")
        ok = len(out["held"]) == 2 and len(out["refused"]) == 2 and out["launches"] == 0
        return ok, f"held_passes={len(out['held'])} refused_rows={len(out['refused'])} (reason changed between passes)"
    guarded("V-SLEEP-CHANGE-WRITES", change)

    def movement():
        seen = {}

        def note(mid):
            r = gm.load(mid)
            gm.transition(mid, expect_epoch=r["epoch"], expect_state=r["state"], event="note_set", now=NOW,
                          note="moved")
            seen["after"] = "sleep" in gm.load(mid)
        out = drive([not_ready("auth_expired")], 2, mid="m-sl-mov", between=note)
        ok = seen.get("after") is False and len(out["refused"]) == 2 and len(out["held"]) == 2
        return ok, f"sleep_after_other_transition={seen.get('after')} refused_rows={len(out['refused'])}"
    guarded("V-SLEEP-MOVEMENT-ENDS-IT", movement)

    def wake_control():
        out = drive([not_ready("auth_expired"), {"verdict": "READY", "reasons": [], "unmeasured": []}], 2,
                    mid="m-sl-wake")
        ok = out["launches"] == 1 and "sleep" not in out["rec"] and len(out["refused"]) == 1
        return ok, f"launches={out['launches']} sleep_after_launch={out['rec'].get('sleep')} state={out['rec']['state']}"
    guarded("V-SLEEP-WAKES-AND-CLEARS", wake_control)

    def helper():
        a = ms.entry("x", {"kind": "time", "at": 5}, 1, "r", 10.0)
        b = ms.entry("x", {"kind": "time", "at": 5}, 1, "r", 99.0)
        c = ms.entry("x", {"kind": "time", "at": 5}, 2, "r", 10.0)
        try:
            ms.entry("x", {"kind": "maybe"}, 1, "r", 1.0)
            refused = False
        except ValueError:
            refused = True
        ok = (ms.same({"sleep": a}, b) and not ms.same({"sleep": a}, c) and not ms.same({}, a) and refused
              and ms.provider_wake({"quarantine": True})["kind"] == "owner"
              and ms.provider_wake({"until": 7})["at"] == 7)
        return ok, f"since_ignored={ms.same({'sleep': a}, b)} epoch_counts={not ms.same({'sleep': a}, c)} unknown_kind_refused={refused}"
    guarded("V-SLEEP-HELPER-CONTRACT", helper)

    def legacy_bytes():
        mid = _fresh("m-sl-leg")
        gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1)
        rec = gm.load(mid)
        return "sleep" not in rec, f"keys_without_sleep={'sleep' not in rec}"
    guarded("V-SLEEP-NEVER-SLEPT-KEEPS-BYTES", legacy_bytes)


# ------------------------------------------------------------------------------------------- drill
def _mutants():
    real_same, real_transition = ms.same, gm.transition

    def keep_sleep(mission_id, **kw):
        before = (gm.load(mission_id) or {}).get("sleep")
        rec = real_transition(mission_id, **kw)
        if before and "sleep" not in kw:   # the mutant: movement does not end the sleep
            rec["sleep"] = before
            gm._write(gm.mission_path(mission_id), rec)
        return rec
    return [("same-always-false", lambda: setattr(ms, "same", lambda rec, new: False)),
            ("same-always-true", lambda: setattr(ms, "same", lambda rec, new: True)),
            ("movement-keeps-sleep", lambda: setattr(gm, "transition", keep_sleep))], \
        lambda: (setattr(ms, "same", real_same), setattr(gm, "transition", real_transition))


def main(argv) -> int:
    if "--drill" in argv:
        mutants, restore = _mutants()
        QUIET[0] = True
        survived = []
        for name, apply in mutants:
            RESULTS.clear()
            apply()
            try:
                gates()
            finally:
                restore()
            red = [n for n, ok, _ in RESULTS if not ok]
            print(f"{'KILLED' if red else 'SURVIVED'} {name}: red={red}")
            if not red:
                survived.append(name)
        print(f"SLEEP_DRILL killed={len(mutants) - len(survived)}/{len(mutants)}")
        return 1 if survived else 0
    gates()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"SLEEP_PASS={passed}/{len(RESULTS)}  threshold={len(RESULTS)}/{len(RESULTS)}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
