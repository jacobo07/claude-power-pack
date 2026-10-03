#!/usr/bin/env python
"""V-MCAP-* gates for tools/mission_capsule.py (spec vault/specs/mission-capsule-rollover.md, T5).

Isolation (G24, spec I6), three layers:
1. every state directory is redirected to a temp dir BEFORE any import;
2. rollover.STATE_DIR (frozen at import) is pointed at a TRAP dir that must stay empty: an adapter
   that ever fell back to the import-time default would write there;
3. the live rollover state is fingerprinted before and after, with a positive control proving the
   fingerprint sees a write.

Every refusal has a paired control that is admitted, and the adapter-specific decisions are
re-checked against source-level mutants of the real file: each mutant must turn its check red.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="mcap_t_"))
STATE = TMP / "state"
TRAP = TMP / "trap-import-time-state"
os.environ["CPP_ROLLOVER_STATE_DIR"] = str(STATE)
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(TMP / "mission-state")
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(TMP / "mission-state" / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = str(TMP / "mission-state")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402
import mission_capsule as mc  # noqa: E402

ro.STATE_DIR = TRAP
LIVE = Path.home() / ".claude" / "state" / "rollover"
LIVE_MISSIONS = Path.home() / ".claude" / "state"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


# The live sentinel is SUBJECT-based, not mtime-based. Measured 2026-10-03: the production sweep and
# live workers rewrote P3's mission records during this suite's own run, so "nothing in the live dir
# changed" was false for reasons that are not ours -- an instrument that cannot tell a leak from a
# neighbour. What this suite could leak is its own subjects, and those are greppable.
SUBJECT_MARKS = (b"m-mcap", b"mcap_t_")


def ledgers(rollover_root: Path, missions_root: Path) -> tuple[Path, Path]:
    return rollover_root / "rollover-ledger.jsonl", missions_root / "gsd-autorun-ledger.jsonl"


def sizes(paths) -> dict:
    return {str(p): (p.stat().st_size if p.is_file() else 0) for p in paths}


def subject_hits(rollover_root: Path, missions_root: Path, since: dict) -> list[str]:
    """This suite's subjects in a state tree: capsule/marker file names, mission records, and the
    ledger bytes appended after `since`. Other writers' files and rows never match."""
    hits = [str(p) for sub in ("capsules", "mission-capsules", "precert") if (rollover_root / sub).is_dir()
            for p in (rollover_root / sub).glob("*mcap*")]
    hits += [str(p) for p in missions_root.glob("gsd-mission-m-mcap*.json")]
    for p in ledgers(rollover_root, missions_root):
        try:
            with open(p, "rb") as fh:
                fh.seek(since.get(str(p), 0))
                tail = fh.read()
        except OSError:
            continue
        hits += [f"{p.name}: {m.decode()}" for m in SUBJECT_MARKS if m in tail]
    return hits


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


def git(root, *args):
    subprocess.run([ro._git_exe(), "-C", str(root), *args], check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def make_repo() -> Path:
    repo = TMP / "repo"
    (repo / ".planning").mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "t")
    (repo / ".planning" / "STATE.md").write_text("# State\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


REPO = make_repo()
# Shape taken from a real `gsd-tools query init.manager` answer (2026-10-03, cognitive-resource-os).
MANAGER = {"state_path": str(REPO / ".planning" / "STATE.md"), "phase_count": 3, "completed_count": 1,
           "recommended_actions": [
               {"phase": "2", "phase_name": "Wire the adapter", "action": "execute", "reason": "planned",
                "command": "/gsd-execute-phase 2"},
               {"phase": "3", "phase_name": "Seal and hand back", "action": "plan", "reason": "next",
                "command": "/gsd-plan-phase 3"}],
           "phases": [{"number": "1", "name": "Spec", "phase_complete": True, "disk_status": "complete"},
                      {"number": "2", "name": "Wire the adapter", "phase_complete": False, "disk_status": "partial"},
                      {"number": "3", "name": "Seal and hand back", "phase_complete": False}]}
PARTIAL = {**MANAGER, "recommended_actions": []}
DONE = {**MANAGER, "recommended_actions": [], "phases": [{**p, "phase_complete": True} for p in MANAGER["phases"]]}
CLEAR = {"verdict": "CLEAR", "pending": [], "unconsumed": []}


def record(mid="m-mcap00000001", epoch=3, **kw) -> dict:
    rec = {"mission_id": mid, "epoch": epoch, "cwd": str(REPO), "workstream": None, "state": "RUNNING",
           "resume_command": "/gsd-autonomous", "lineage_id": "m-root0000001",
           "owner": {"session_id": f"{mid[2:10]}-worker-session", "kind": "background"}}
    rec.update(kw)
    return rec


def transcript(name="t.jsonl") -> Path:
    p = TMP / name
    p.write_text(json.dumps({"type": "assistant", "message": {"content": []}}) + "\n", encoding="utf-8")
    return p


def compile_(m, **kw):
    rec = kw.pop("rec", None) or record()
    kw.setdefault("manager", MANAGER)
    kw.setdefault("children", CLEAR)
    return m.compile_mission_capsule(rec, **kw)


def answers(cap: dict, obligations: list) -> dict:
    facts = ro.repo_facts(cap["cwd"])
    a = {"goal": "STATE.md", "branch": facts["branch"], "head": facts["head"][:7], "next": obligations[0]}
    if cap.get("degraded"):
        a["dirty"] = str(len(facts.get("dirty") or []))
    return a


# --------------------------------------------------------------------------- checks (module -> verdict)
def c_oblig_recommended(m):
    items, src = m.render_obligations(MANAGER)
    return items == ["execute phase 2: Wire the adapter", "plan phase 3: Seal and hand back"] and src, items


def c_oblig_partial(m):
    items, src = m.render_obligations(PARTIAL)
    return items == ["continue phase 2: Wire the adapter"] and src == "gsd first incomplete phase", items


def c_oblig_none_refused(m):
    cap = compile_(m, manager=DONE, origin="worker_handoff", note="n", transcript=str(transcript()))
    comp = ro.completeness(cap)
    return cap["obligations"] == [] and any(r.startswith("obligations") for r in comp["missing"]), comp["missing"]


def c_identity(m):
    import gsd_mission as gm
    cap = compile_(m, origin="worker_handoff", note="n", transcript=str(transcript()))
    run = cap["run"]
    ok = (cap["session_id"] == cap["capsule_key"] == "mission-m-mcap00000001-e3" and cap["schema"] == ro.SCHEMA_V2
          and cap["protocol"] == "capsule-v2" and run["epoch"] == 3 and run["successor_epoch"] == 4
          and run["lineage_id"] == "m-root0000001" and run["worker"] == "mcap0000-worker-session"
          and run["worker_name"] == gm.worker_name(record()) and ro.capsule_path(cap["session_id"], STATE).parent.name
          == "mission-capsules")
    return ok, run


def c_handoff_safe(m):
    tp = transcript("h.jsonl")
    cap = compile_(m, origin="worker_handoff", note="phase 2 half done", transcript=str(tp))
    s = m.seal_mission(cap, STATE)
    g = m.gate_before_stop(cap["session_id"], str(tp), STATE)
    return s["verdict"] == "SAFE_TO_FORGET" and g["verdict"] == "SAFE_TO_FORGET", (s["reasons"], g["reasons"])


def c_handoff_without_note_refused(m):
    cap = compile_(m, origin="worker_handoff", note="  ", transcript=str(transcript()))
    s = m.seal_mission(cap, STATE)
    return s["verdict"] == "REFUSED" and any("note" in r for r in s["reasons"]), s["reasons"]


def c_fallback_degraded_safe(m):
    rec = record(mid="m-mcapfallback1")
    cap = compile_(m, rec=rec, origin="supervisor_fallback", transcript=str(transcript("f.jsonl")))
    s = m.seal_mission(cap, STATE)
    return cap["degraded"] is True and s["verdict"] == "SAFE_TO_FORGET", s["reasons"]


def c_fallback_children_hold_refused(m):
    cap = compile_(m, origin="supervisor_fallback", children={"verdict": "HOLD", "pending": [{"x": 1}]},
                   transcript=str(transcript()))
    s = m.seal_mission(cap, STATE)
    return s["verdict"] == "REFUSED" and any(r.startswith("children") for r in s["reasons"]), s["reasons"]


def c_fallback_children_unknown_refused(m):
    cap = compile_(m, origin="supervisor_fallback", children={"verdict": "UNKNOWN", "reason": "no transcript"})
    s = m.seal_mission(cap, STATE)
    return s["verdict"] == "REFUSED" and any(r.startswith("children") for r in s["reasons"]), s["reasons"]


def c_recovery_no_transcript_admitted(m):
    rec = record(mid="m-mcaprecover1")
    cap = compile_(m, rec=rec, origin="recovery", children={"verdict": "UNKNOWN", "reason": "no transcript"})
    s = m.seal_mission(cap, STATE)
    return (cap["children"]["verdict"] == "EXPIRED" and cap["degraded"] and cap.get("custody_unchecked")
            and s["verdict"] == "SAFE_TO_FORGET" and any("lost" in w for w in s["warnings"])), (s, cap["children"])


def c_gsd_unavailable_refused(m):
    cap = compile_(m, manager=None, ask=lambda wd, ws: (None, "gsd-tools rc=1: boom"), origin="worker_handoff",
                   note="n", transcript=str(transcript()))
    comp = ro.completeness(cap)
    return (cap["goal"]["state"] == ro.UNKNOWN and "boom" in cap["goal"]["reason"] and not cap["obligations"]
            and not comp["complete"]), comp["missing"]


def c_state_missing_refused(m):
    cap = compile_(m, manager={**MANAGER, "state_path": str(REPO / "nope" / "STATE.md")}, origin="worker_handoff",
                   note="n", transcript=str(transcript()))
    return cap["goal"]["state"] == ro.UNKNOWN and not ro.completeness(cap)["complete"], cap["goal"]


def c_repo_unreadable_refused(m):
    bare = TMP / "not-a-repo"
    bare.mkdir(exist_ok=True)
    cap = compile_(m, origin="worker_handoff", note="n", work_dir=str(bare), transcript=str(transcript()))
    s = m.seal_mission(cap, STATE)
    return s["verdict"] == "REFUSED" and any(r.startswith("repo") for r in s["reasons"]), s["reasons"]


def c_bad_identity_raises(m):
    bad = []
    for rec, origin in ((record(epoch=0), "worker_handoff"), (record(mission_id=""), "worker_handoff"),
                        (record(), "whenever")):
        try:
            m.compile_mission_capsule(rec, origin=origin, manager=MANAGER, children=CLEAR)
            bad.append(origin)
        except ValueError:
            pass
    return not bad, f"accepted: {bad}"


def c_transcript_moved_refused(m):
    tp = transcript("moved.jsonl")
    rec = record(mid="m-mcapmoved0001")
    cap = compile_(m, rec=rec, origin="worker_handoff", note="n", transcript=str(tp))
    m.seal_mission(cap, STATE)
    before = m.gate_before_stop(cap["session_id"], str(tp), STATE)["verdict"]
    with open(tp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "user"}) + "\n")
    after = m.gate_before_stop(cap["session_id"], str(tp), STATE)
    return before == "SAFE_TO_FORGET" and after["verdict"] == "REFUSED", after["reasons"]


def c_tamper_refused(m):
    rec = record(mid="m-mcaptamper01")
    cap = compile_(m, rec=rec, origin="worker_handoff", note="n", transcript=str(transcript()))
    m.seal_mission(cap, STATE)
    p = ro.capsule_path(cap["session_id"], STATE)
    p.write_text(p.read_text(encoding="utf-8").replace('"note": "n"', '"note": "edited"'), encoding="utf-8")
    g = m.gate_before_stop(cap["session_id"], None, STATE)
    return g["verdict"] == "REFUSED", g["reasons"]


def c_wrong_epoch_no_capsule(m):
    g = m.gate_before_stop(ro.mission_key("m-mcap00000001", 9), None, STATE)
    return g["verdict"] == "NO_CAPSULE", g["verdict"]


def c_ledger_down_unknown(m):
    saved = ro.ledger
    ro.ledger = lambda *a, **k: False
    try:
        rec = record(mid="m-mcapledger01")
        s = m.seal_mission(compile_(m, rec=rec, origin="worker_handoff", note="n", transcript=str(transcript())), STATE)
    finally:
        ro.ledger = saved
    return s["verdict"] == ro.UNKNOWN, s["reasons"][-1:]


def c_bounded(m):
    big_packet = {"sha256": "ab" * 32, "path": "p.txt", "verdict": "COMPLETE", "bytes": 9,
                  "sources": [{"path": f"f{i}.py", "sha256": "0" * 64} for i in range(500)]}
    cap = compile_(m, origin="worker_handoff", note="x" * 10000, packet=big_packet, transcript=str(transcript()))
    size = len(json.dumps(cap).encode("utf-8"))
    return (len(cap["note"]) == m.NOTE_MAX_CHARS and "sources" not in cap["packet"]
            and cap["packet"]["sha256"] == "ab" * 32 and size < 8000), f"{size} B"


def c_roundtrip_certify(m):
    """The adapter's capsule through the canonical successor path: claim, refresh, exam, certify."""
    tp = transcript("rt.jsonl")
    rec = record(mid="m-mcaproundtr1")
    cap = compile_(m, rec=rec, origin="worker_handoff", note="phase 2 half done", transcript=str(tp))
    m.seal_mission(cap, STATE)
    now_items, _src = m.render_obligations(MANAGER)
    rc, out = quiet(ro.resume_flow, cap, "succ-1", cap["cwd"], STATE, obligations=now_items)
    leaked = any(x in out for x in (ro.repo_facts(cap["cwd"])["head"][:7],))
    (rc2, res), _ = quiet(ro.certify_flow, cap["session_id"], "succ-1", answers(cap, now_items), STATE)
    return rc == 0 and not leaked and rc2 == 0, f"resume={rc} leaked_head={leaked} certify={rc2} {res.get('wrong')}"


def c_roundtrip_wrong_next(m):
    """Control: the same path with a next obligation that GSD no longer recommends is refused."""
    rec = record(mid="m-mcaproundtr2")
    cap = compile_(m, rec=rec, origin="worker_handoff", note="n", transcript=str(transcript("rt2.jsonl")))
    m.seal_mission(cap, STATE)
    now_items, _src = m.render_obligations(PARTIAL)          # GSD moved on since the seal
    quiet(ro.resume_flow, cap, "succ-2", cap["cwd"], STATE, obligations=now_items)
    stale = {**answers(cap, now_items), "next": cap["obligations"][0]}
    (rc, res), _ = quiet(ro.certify_flow, cap["session_id"], "succ-2", stale, STATE)
    return rc != 0 and [w["key"] for w in res.get("wrong") or []] == ["next"], f"exit {rc} {res.get('wrong')}"


def c_state_dir_call_time(m):
    other = TMP / "late"
    saved = os.environ["CPP_ROLLOVER_STATE_DIR"]
    os.environ["CPP_ROLLOVER_STATE_DIR"] = str(other)
    try:
        got = m.state_dir()
    finally:
        os.environ["CPP_ROLLOVER_STATE_DIR"] = saved
    return got == other and m.state_dir(STATE) == STATE, str(got)


CHECKS = [("V-MCAP-OBLIG-RECOMMENDED", c_oblig_recommended), ("V-MCAP-OBLIG-PARTIAL", c_oblig_partial),
          ("V-MCAP-OBLIG-NONE-REFUSED", c_oblig_none_refused), ("V-MCAP-IDENTITY", c_identity),
          ("V-MCAP-HANDOFF-SAFE", c_handoff_safe), ("V-MCAP-HANDOFF-NO-NOTE-REFUSED", c_handoff_without_note_refused),
          ("V-MCAP-FALLBACK-DEGRADED-SAFE", c_fallback_degraded_safe),
          ("V-MCAP-FALLBACK-CHILDREN-HOLD-REFUSED", c_fallback_children_hold_refused),
          ("V-MCAP-FALLBACK-CHILDREN-UNKNOWN-REFUSED", c_fallback_children_unknown_refused),
          ("V-MCAP-RECOVERY-NO-TRANSCRIPT-ADMITTED", c_recovery_no_transcript_admitted),
          ("V-MCAP-GSD-UNAVAILABLE-REFUSED", c_gsd_unavailable_refused),
          ("V-MCAP-STATE-MISSING-REFUSED", c_state_missing_refused),
          ("V-MCAP-REPO-UNREADABLE-REFUSED", c_repo_unreadable_refused),
          ("V-MCAP-BAD-IDENTITY-RAISES", c_bad_identity_raises),
          ("V-MCAP-TRANSCRIPT-MOVED-REFUSED", c_transcript_moved_refused),
          ("V-MCAP-TAMPER-REFUSED", c_tamper_refused), ("V-MCAP-WRONG-EPOCH-NO-CAPSULE", c_wrong_epoch_no_capsule),
          ("V-MCAP-LEDGER-DOWN-UNKNOWN", c_ledger_down_unknown), ("V-MCAP-BOUNDED", c_bounded),
          ("V-MCAP-ROUNDTRIP-CERTIFY", c_roundtrip_certify), ("V-MCAP-ROUNDTRIP-STALE-NEXT-REFUSED", c_roundtrip_wrong_next),
          ("V-MCAP-STATE-DIR-CALL-TIME", c_state_dir_call_time)]


# --------------------------------------------------------------------------- markers, guard, CLI
REG = TMP / "sessions-registry"
GUARD = HERE.parent / "hooks" / "capsule_mutation_guard.js"


def guard_denies(session_id: str) -> bool:
    """The REAL guard process, hermetic: our state dir and our session registry only."""
    payload = {"session_id": session_id, "cwd": str(REPO), "tool_name": "Edit", "hook_event_name": "PreToolUse",
               "tool_input": {"file_path": str(TMP / "x.txt"), "old_string": "a", "new_string": "b"}}
    env = {**os.environ, "CPP_ROLLOVER_STATE_DIR": str(STATE), "CPP_CLAUDE_SESSIONS_DIR": str(REG),
           "CPP_CAPSULE_ROLLOVER": ""}
    r = subprocess.run([shutil.which("node") or "node", str(GUARD)], input=json.dumps(payload), capture_output=True,
                       text=True, timeout=60, env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    last = ((r.stdout or "").strip().splitlines() or ["{}"])[-1]
    return (json.loads(last).get("hookSpecificOutput") or {}).get("permissionDecision") == "deny"


def cli(m, args, session_id=None, manager=MANAGER):
    saved_sid, saved_ask = os.environ.pop("CLAUDE_CODE_SESSION_ID", None), m.ask_gsd
    if session_id:
        os.environ["CLAUDE_CODE_SESSION_ID"] = session_id
    m.ask_gsd = lambda wd, ws: (manager, "" if manager else "gsd down")
    try:
        return quiet(m._cli, [*args, "--state-dir", str(STATE)])
    finally:
        m.ask_gsd = saved_ask
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        if saved_sid:
            os.environ["CLAUDE_CODE_SESSION_ID"] = saved_sid


def mission_record(mid, *, owner_sid=None, capsule_key=True, epoch=4):
    """A real record in the isolated mission state, as T6 will leave it after a v2 rotation."""
    import gsd_mission as gm
    assert str(TMP) in str(gm.mission_path(mid)), "mission state is not isolated"
    gm.mission_path(mid).parent.mkdir(parents=True, exist_ok=True)
    gm.mission_path(mid).unlink(missing_ok=True)   # checks re-run against mutants with the same id
    gm.create(str(REPO), "/gsd-autonomous", mission_id=mid)
    fields = {"owner": {"session_id": owner_sid, "kind": "background"}} if owner_sid else {}
    if capsule_key:
        fields["capsule_key"] = ro.mission_key(mid, epoch - 1)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", state=gm.RUNNING,
                         epoch=epoch, **fields)


def c_arm_marker(m):
    m.arm_successor(record(mid="m-mcaparm00001"), STATE)
    mk = ro.precert_read("m-mcaparm00001", STATE) or {}
    return (mk.get("worker") == "m-mcaparm00001-e4" and mk.get("epoch") == 4
            and mk.get("capsule_key") == "mission-m-mcaparm00001-e3" and mk.get("cwd") == str(REPO)
            and not mk.get("certified_at")), mk


def c_arm_over_certified(m):
    ro.precert_write("m-mcaparm00002", {"certified_at": 1.0, "certified_by": "epoch-3-worker",
                                        "capsule_key": "mission-m-mcaparm00002-e2"}, STATE)
    m.arm_successor(record(mid="m-mcaparm00002"), STATE)
    mk = ro.precert_read("m-mcaparm00002", STATE) or {}
    return not mk.get("certified_at") and not mk.get("certified_by"), mk


def c_bind(m):
    try:
        m.bind_successor("m-mcapnoarm001", bg_id="abcd1234", sd=STATE)
        return False, "bound a marker that was never armed"
    except ValueError:
        pass
    m.arm_successor(record(mid="m-mcapbind0001"), STATE)
    mk = m.bind_successor("m-mcapbind0001", bg_id="abcd1234", sd=STATE)
    return (mk.get("bg_id") == "abcd1234" and mk.get("worker") == "m-mcapbind0001-e4"
            and not mk.get("certified_at")), mk


def c_guard_chain(m):
    """seal -> arm -> the real guard denies the worker -> resume (claim) -> certify -> marker lifted
    -> the real guard allows. Certify before resume is refused and keeps the worker denied."""
    mid, sid = "m-mcapchain001", "chainsess-0001-4a4a-8b8b"
    cap = compile_(m, rec=record(mid=mid, epoch=3), origin="worker_handoff", note="phase 2 half done",
                   transcript=str(transcript("chain.jsonl")))
    m.seal_mission(cap, STATE)
    m.arm_successor(record(mid=mid, epoch=3), STATE)
    REG.mkdir(exist_ok=True)
    (REG / "4242.json").write_text(json.dumps({"pid": 4242, "sessionId": sid, "name": f"{mid}-e4", "kind": "bg",
                                               "cwd": str(REPO)}), encoding="utf-8")
    mission_record(mid, owner_sid=sid)
    steps = {"denied_armed": guard_denies(sid)}
    ans = answers(cap, m.render_obligations(MANAGER)[0])
    early, _ = cli(m, ["certify", "--mission", mid] + [x for k, v in ans.items() for x in (f"--{k}", v)], sid)
    steps["early_certify_refused"] = early != 0 and guard_denies(sid)
    steps["resume"], _out = cli(m, ["resume", "--mission", mid], sid)
    steps["certify"], _ = cli(m, ["certify", "--mission", mid] + [x for k, v in ans.items() for x in (f"--{k}", v)], sid)
    steps["marker_certified"] = bool((ro.precert_read(mid, STATE) or {}).get("certified_at"))
    steps["allowed_after"] = not guard_denies(sid)
    ok = (steps["denied_armed"] and steps["early_certify_refused"] and steps["resume"] == 0
          and steps["certify"] == 0 and steps["marker_certified"] and steps["allowed_after"])
    return ok, steps


def c_cli_requires_session(m):
    rc, out = cli(m, ["resume", "--mission", "m-mcapchain001"], None)
    return rc == 2 and "CLAUDE_CODE_SESSION_ID" in out, rc


def c_cli_wrong_session(m):
    mission_record("m-mcapintrude1", owner_sid="realworker-0001")
    rc, out = cli(m, ["resume", "--mission", "m-mcapintrude1"], "intruder-0002-ffff")
    return rc == 5 and "not the current worker" in out, (rc, out.strip()[-80:])


def c_cli_no_capsule_key(m):
    mission_record("m-mcapnokey001", owner_sid="nokeyworker-01", capsule_key=False)
    rc, out = cli(m, ["resume", "--mission", "m-mcapnokey001"], "nokeyworker-01")
    return rc == 4 and "capsule_key" in out, rc


def c_cli_gsd_down_refused_before_claim(m):
    mid, sid = "m-mcapgsddown1", "gsddownworker-01"
    cap = compile_(m, rec=record(mid=mid, epoch=3), origin="worker_handoff", note="n", transcript=str(transcript()))
    m.seal_mission(cap, STATE)
    mission_record(mid, owner_sid=sid)
    rc, _out = cli(m, ["resume", "--mission", mid], sid, manager=None)
    return rc == 4 and ro.claim_holder(cap["session_id"], STATE) is None, rc


CHECKS += [("V-MCAP-ARM-MARKER", c_arm_marker), ("V-MCAP-ARM-OVER-CERTIFIED", c_arm_over_certified),
           ("V-MCAP-BIND", c_bind), ("V-MCAP-GUARD-CHAIN", c_guard_chain),
           ("V-MCAP-CLI-REQUIRES-SESSION", c_cli_requires_session), ("V-MCAP-CLI-WRONG-SESSION", c_cli_wrong_session),
           ("V-MCAP-CLI-NO-CAPSULE-KEY", c_cli_no_capsule_key),
           ("V-MCAP-CLI-GSD-DOWN-NO-CLAIM", c_cli_gsd_down_refused_before_claim)]

# Each mutant is a textual edit of the REAL file; the named check must go red against it.
MUTANTS = [
    ("ARM-MERGES", "return ro.precert_arm(mid, fields, state_dir(sd))",
     "return ro.precert_write(mid, fields, state_dir(sd))", "V-MCAP-ARM-OVER-CERTIFIED"),
    ("ANY-SESSION-IS-THE-WORKER", "if session_id == owner or (bg and session_id.startswith(bg)):", "if True:",
     "V-MCAP-CLI-WRONG-SESSION"),
    ("RESUME-WITHOUT-GSD", "    if not items:\n        # I4", "    if False:\n        # I4",
     "V-MCAP-CLI-GSD-DOWN-NO-CLAIM"),
    ("RECOVERY-LENIENCY-FOR-ALL", 'if origin == "recovery" and children.get', 'if children.get',
     "V-MCAP-FALLBACK-CHILDREN-UNKNOWN-REFUSED"),
    ("SEAL-IGNORES-LEDGER", 'verdict = stf["verdict"] if recorded else ro.UNKNOWN', 'verdict = stf["verdict"]',
     "V-MCAP-LEDGER-DOWN-UNKNOWN"),
    ("GATE-SKIPS-TRANSCRIPT", "        elif cur != sealed:", "        elif False:", "V-MCAP-TRANSCRIPT-MOVED-REFUSED"),
    ("PARTIAL-PHASE-DROPPED", 'return [f"continue phase', 'return [] or [f"continue phase-x',
     "V-MCAP-OBLIG-PARTIAL"),
    ("NOTE-UNBOUNDED", '"note": (note or "").strip()[:NOTE_MAX_CHARS]', '"note": (note or "").strip()',
     "V-MCAP-BOUNDED"),
    ("STATE-DIR-IMPORT-TIME", "    if explicit:\n        return Path(explicit)\n    env = os.environ.get",
     "    return ro.STATE_DIR\n    env = os.environ.get", "V-MCAP-STATE-DIR-CALL-TIME"),
]


def load_mutant(name: str, old: str, new: str):
    src = (HERE / "mission_capsule.py").read_text(encoding="utf-8")
    if src.count(old) != 1:
        return None
    path = TMP / f"mission_capsule_mut_{name.lower().replace('-', '_')}.py"
    path.write_text(src.replace(old, new), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Crashed(str):
    """A check that raised. Red against the real module; NOT a kill against a mutant -- measured
    2026-10-03: two mutants read as killed when their check crashed on a missing fixture dir, i.e.
    the check never judged the mutated line."""


def run(m, fn):
    try:
        ok, ev = fn(m)
        return bool(ok), ev
    except Exception as exc:  # noqa: BLE001 -- a crash is a red check, reported with its type
        return False, Crashed(f"{type(exc).__name__}: {exc}")


def main() -> int:
    live_since = sizes(ledgers(LIVE, LIVE_MISSIONS))
    try:
        print("T5 mission capsule adapter (real module)")
        for gate, fn in CHECKS:
            ok, ev = run(mc, fn)
            check(gate, ok, ev)
        print("T5 mutants of the real file (each must turn its check red)")
        by_name = dict(CHECKS)
        for name, old, new, target in MUTANTS:
            mod = load_mutant(name, old, new)
            if mod is None:
                check(f"V-MCAP-MUTANT-{name}", False, "mutation site not found exactly once: the mutant is stale")
                continue
            ok, ev = run(mod, by_name[target])
            check(f"V-MCAP-MUTANT-{name}", not ok and not isinstance(ev, Crashed),
                  f"{target} {'CRASHED (not a kill)' if isinstance(ev, Crashed) else 'red'} under the mutant: "
                  f"{str(ev)[:100]}")
        print("G24 isolation")
        trap_files = [p.name for p in TRAP.rglob("*")] if TRAP.exists() else []
        check("V-MCAP-NO-IMPORT-TIME-STATE", not trap_files, f"trap dir holds {trap_files[:3]}")
        check("V-MCAP-WROTE-WHERE-TOLD", any((STATE / "mission-capsules").glob("mission-*.json"))
              and (STATE / "rollover-ledger.jsonl").is_file(), "positive: the isolated dir did receive the seals")
        own = subject_hits(STATE, TMP / "mission-state", {})
        check("V-MCAP-SENTINEL-SEES-OWN-SUBJECTS", any("mission-capsules" in h for h in own)
              and any(h.startswith("rollover-ledger") for h in own),
              f"positive control: the same predicate finds this suite's subjects where they were written ({len(own)} hits)")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    leaked = subject_hits(LIVE, LIVE_MISSIONS, live_since)
    check("V-MCAP-LIVE-STATE-HOLDS-NO-TEST-SUBJECT", not leaked,
          f"live rollover dirs + mission records + ledger bytes appended during the run: {leaked[:3]}")
    print(f"MCAP_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
