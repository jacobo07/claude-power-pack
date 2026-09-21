"""V-PBA-* gates: the PHASE-boundary advance is WIRED, and refuses correctly.

`phase_boundary_owed` shipped fully written, fully guarded, documented against a
real 14-hour stall (session fa6961b6) -- and with zero callers. The 93-gate GSDLR
suite was green throughout, because every one of those gates predates the wiring.
A predicate with no event and a predicate that passed are the same observable.

So this file's job is narrow and it is not "test the predicate": it drives the
CALL SITE in `sweep()`. The mutation that must turn it red is deleting the
`phase_boundary_owed(...)` call, not breaking a clause inside the function.

Hermetic: state/hooks/projects/sessions redirect to temp dirs, the marker module
and the delivery transport are recorders, so nothing here can type into a real
terminal or touch the Owner's live markers.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

TMP = Path(tempfile.mkdtemp(prefix="pba-"))
STATE, HOOKS, PROJECTS, SESSIONS = (TMP / n for n in ("state", "hooks", "projects", "sessions"))
for d in (STATE, HOOKS, PROJECTS, SESSIONS):
    d.mkdir(parents=True)
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(STATE), "GSD_LONG_RUN_HOOKS_DIR": str(HOOKS),
                   "GSD_LONG_RUN_PROJECTS_DIR": str(PROJECTS), "GSD_LONG_RUN_NO_SPAWN": "1",
                   "GSD_LONG_RUN_SESSIONS_DIR": str(SESSIONS)})

passes = fails = inconclusive = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def skip(gate, why):
    """Precondition unavailable -- not a verdict about the subject."""
    global inconclusive
    inconclusive += 1
    print(f"SKIP {gate}: INCONCLUSIVE -- {why}")


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lr = load(TOOLS / "gsd_long_run.py", "gsd_long_run_pba")

# --------------------------------------------------------------------- fixtures
DELIVERED: list[tuple] = []
BUMPED: list[str] = []


class _FakeMarkerModule:
    @staticmethod
    def bump_cycles(session_id: str):
        BUMPED.append(session_id)
        return len(BUMPED)


def _no_deliver(sid, cwd, transcript, tail, cmd, mtime):
    DELIVERED.append((sid, cwd, tail, cmd, mtime))
    return "terminal-inbox"


lr._recover_via_transport = _no_deliver
lr._marker_module = lambda: _FakeMarkerModule
lr.gsd_status = lambda project, timeout=45: {"outcome": "OK", "reason": "phase 2 of 4 ready"}


def sid() -> str:
    return "pba-" + uuid.uuid4().hex[:12]


def project(name: str) -> Path:
    p = TMP / f"proj-{name}"
    (p / ".planning").mkdir(parents=True, exist_ok=True)
    return p


def asst(text: str) -> dict:
    return {"type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def transcript(session: str, cwd: str, rows=(), idle_s: float = 0.0) -> Path:
    d = PROJECTS / "proj"
    d.mkdir(exist_ok=True)
    t = d / f"{session}.jsonl"
    lines = [{"type": "system", "cwd": cwd}] + list(rows)
    t.write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    if idle_s:
        ts = time.time() - idle_s
        os.utime(t, (ts, ts))
    return t


def marker(s: str, proj: Path, **kw) -> Path:
    body = {"session_id": s, "resume_command": "/gsd-autonomous", "cwd": str(proj),
            "cycles": 0, "max_cycles": 12, "armed_at": lr._iso(time.time())
            if hasattr(lr, "_iso") else None}
    body.update(kw)
    p = STATE / f"gsd-autorun-{s}.json"
    p.write_text(json.dumps({k: v for k, v in body.items() if v is not None}), encoding="utf-8")
    return p


def clear_markers():
    for p in STATE.glob("gsd-autorun-*.json"):
        p.unlink()
    DELIVERED.clear()
    BUMPED.clear()


def set_clock(seconds: float, name: str = "conversation"):
    """Pin the CONVERSATION clock. The transcript's mtime is set separately, so a
    gate can put the two in deliberate disagreement -- which is the whole point
    of V-PBA-CONSERVATIVE-CLOCK."""
    lr.session_idle_seconds = lambda t: (seconds, name)


def sweep_once(**kw):
    return lr.sweep(**kw)


def actions_of(acts, kind):
    return [a for a in acts if a.get("action") == kind]


# ------------------------------------------------------------------------ gates
def gate_advances_on_prose_tail():
    """The positive pole: a run that ended a phase on PROSE is re-entered.

    This is the exact shape of session fa6961b6 -- the turn ended
    "Next is phase 11: pagination ..." and the sweep logged `stalled` for
    fourteen hours because the tail matched neither the resume line nor
    `/compact`."""
    clear_markers()
    s = sid()
    proj = project("advance")
    transcript(s, str(proj), [asst("Next is phase 11: pagination with the N/M indicator.")],
               idle_s=3600)
    marker(s, proj, advance_on_phase_boundary=True)
    set_clock(3600.0)
    acts = sweep_once()
    adv = actions_of(acts, "advanced")
    check("V-PBA-ADVANCES-ON-PROSE-TAIL", len(adv) == 1 and adv[0]["line"] == "/gsd-autonomous",
          f"{adv or acts}")
    check("V-PBA-ADVANCE-DELIVERS-THE-LINE",
          len(DELIVERED) == 1 and DELIVERED[0][3] == "/gsd-autonomous",
          f"delivered={DELIVERED}")
    check("V-PBA-ADVANCE-SPENDS-A-CYCLE", BUMPED == [s], f"bumped={BUMPED}")
    rows = [e for e in lr.ledger_events(s) if e.get("event") == "resume_requested"]
    check("V-PBA-ADVANCE-IS-LEDGERED",
          len(rows) == 1 and rows[0].get("via") == "phase-boundary", f"{rows}")


def gate_opt_in_required():
    """Negative control. Without the marker field NOTHING is typed.

    This is the gate that makes the positive one mean something: an already-armed
    run must keep its old behaviour, so the wiring cannot start typing into panes
    armed before it existed."""
    clear_markers()
    s = sid()
    proj = project("optin")
    transcript(s, str(proj), [asst("Next is phase 11: pagination with the N/M indicator.")],
               idle_s=3600)
    marker(s, proj)  # no advance_on_phase_boundary
    set_clock(3600.0)
    acts = sweep_once()
    check("V-PBA-OPT-IN-REQUIRED",
          not actions_of(acts, "advanced") and not DELIVERED,
          f"advanced={actions_of(acts, 'advanced')} delivered={DELIVERED}")
    check("V-PBA-UNOPTED-STILL-STALLS", bool(actions_of(acts, "stalled")),
          f"{actions_of(acts, 'stalled')}")


def gate_question_not_advanced():
    """A turn ending in `?` is the agent asking its Owner something. Typing a
    resume over it answers for them."""
    clear_markers()
    s = sid()
    proj = project("question")
    transcript(s, str(proj), [asst("Should I use the cylinder or the arrow here?")], idle_s=3600)
    marker(s, proj, advance_on_phase_boundary=True)
    set_clock(3600.0)
    acts = sweep_once()
    check("V-PBA-QUESTION-NOT-ADVANCED", not actions_of(acts, "advanced") and not DELIVERED,
          f"advanced={actions_of(acts, 'advanced')} delivered={DELIVERED}")


def gate_conservative_clock():
    """The 40-minute clause is judged on the clock the CONVERSATION owns.

    Host metadata rows (custom-title, cost-state) advance a transcript's mtime
    without the session speaking -- measured to 19.0 h on a 48 h threshold. Here
    the file looks 60 minutes idle and the session spoke 2 minutes ago. Judging
    on the file would type into a pane whose Owner is mid-sentence."""
    clear_markers()
    s = sid()
    proj = project("clock")
    transcript(s, str(proj), [asst("Next is phase 11: pagination with the N/M indicator.")],
               idle_s=3600)
    marker(s, proj, advance_on_phase_boundary=True)
    set_clock(120.0)  # the session spoke 2 minutes ago
    acts = sweep_once()
    check("V-PBA-CONSERVATIVE-CLOCK", not actions_of(acts, "advanced") and not DELIVERED,
          f"mtime_idle=60m conv_idle=2m -> advanced={actions_of(acts, 'advanced')}")


def gate_fenced():
    """One boundary licenses ONE advance. Without the fence the same prose tail
    is re-typed on every sweep -- which is the three-times-retyped `/compact`
    this estate already paid for."""
    clear_markers()
    s = sid()
    proj = project("fence")
    transcript(s, str(proj), [asst("Next is phase 11: pagination with the N/M indicator.")],
               idle_s=3600)
    marker(s, proj, advance_on_phase_boundary=True)
    set_clock(3600.0)
    first = sweep_once()
    second = sweep_once()
    check("V-PBA-ADVANCE-IS-FENCED",
          len(actions_of(first, "advanced")) == 1 and not actions_of(second, "advanced"),
          f"first={len(actions_of(first, 'advanced'))} second={len(actions_of(second, 'advanced'))} "
          f"delivered={len(DELIVERED)}")


def gate_decline_is_nameable():
    """A sweep that declined every marker and one that judged none are otherwise
    the same empty result -- the distinction Phase 4 paid for on `kept`."""
    clear_markers()
    s = sid()
    proj = project("explain")
    transcript(s, str(proj), [asst("Should I use the cylinder or the arrow here?")], idle_s=3600)
    marker(s, proj, advance_on_phase_boundary=True)
    set_clock(3600.0)
    acts = sweep_once(explain=True)
    declined = actions_of(acts, "advance_declined")
    check("V-PBA-DECLINE-IS-NAMEABLE",
          len(declined) == 1 and "question" in declined[0]["reason"],
          f"{declined}")


def gate_dry_run_types_nothing():
    clear_markers()
    s = sid()
    proj = project("dry")
    transcript(s, str(proj), [asst("Next is phase 11: pagination with the N/M indicator.")],
               idle_s=3600)
    marker(s, proj, advance_on_phase_boundary=True)
    set_clock(3600.0)
    acts = sweep_once(dry_run=True)
    check("V-PBA-DRY-RUN-TYPES-NOTHING",
          len(actions_of(acts, "advanced")) == 1 and not DELIVERED and not BUMPED,
          f"advanced={len(actions_of(acts, 'advanced'))} delivered={DELIVERED} bumped={BUMPED}")


def main() -> int:
    if not hasattr(lr, "phase_boundary_owed"):
        skip("V-PBA-SUBJECT-PRESENT", "gsd_long_run.phase_boundary_owed is absent")
        print(f"PBA_PASS={passes}/{passes + fails}  inconclusive={inconclusive}")
        return 2
    for g in (gate_advances_on_prose_tail, gate_opt_in_required, gate_question_not_advanced,
              gate_conservative_clock, gate_fenced, gate_decline_is_nameable,
              gate_dry_run_types_nothing):
        try:
            g()
        except Exception as exc:  # a harness failure is not a verdict about the subject
            skip(g.__name__, f"{exc.__class__.__name__}: {exc}")
    total = passes + fails
    print(f"PBA_PASS={passes}/{total}  inconclusive={inconclusive}  threshold={total}/{total}")
    return 0 if fails == 0 and inconclusive == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
