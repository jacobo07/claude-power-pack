#!/usr/bin/env python
"""V-MV2-* gates: capsule-v2 wired into tools/gsd_mission.py (spec vault/specs/mission-capsule-rollover.md, T6).

Drives the REAL supervise() pass with the host, the launcher, the stopper and GSD injected, and the
real adapter + rollover underneath (temp state dirs, a real git repo). Every v2 behaviour has a
control: the same scenario on a legacy record must show none of it, and every refusal has an
admitted twin, so a build that refuses (or rotates) everything cannot pass.

Hermetic (spec I6): every state dir is redirected BEFORE import; rollover.STATE_DIR (frozen at
import) points at a trap that must stay empty.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="mv2_t_"))
STATE = TMP / "rollover"
TRAP = TMP / "trap-import-time-state"
os.environ["CPP_ROLLOVER_STATE_DIR"] = str(STATE)
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(TMP / "missions")
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(TMP / "missions" / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = str(TMP / "missions")
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(TMP / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(TMP / "projects")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"  # RAM floor reads host memory; covered by test_a5_u6
os.environ.pop("CPP_CAPSULE_ROLLOVER", None)
(TMP / "missions" / "sessions").mkdir(parents=True)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover as ro  # noqa: E402
import mission_capsule as mc  # noqa: E402
import gsd_mission as gm  # noqa: E402

ro.STATE_DIR = TRAP
gm.progress_fingerprint = lambda work_dir: None   # unmeasured: the neutral answer (as test_gsd_mission)

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


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
NOW = 1_800_000_000.0
MANAGER = {"state_path": str(REPO / ".planning" / "STATE.md"),
           "recommended_actions": [{"phase": "2", "phase_name": "Wire it", "action": "execute"}],
           "phases": [{"number": "2", "name": "Wire it", "phase_complete": False}]}
CLEAR = {"verdict": "CLEAR", "pending": [], "unconsumed": []}
HOLD = {"verdict": "HOLD", "pending": ["a background child"], "unconsumed": []}
TRANSCRIPT = TMP / "outgoing.jsonl"
TRANSCRIPT.write_text(json.dumps({"type": "assistant", "message": {"content": []}}) + "\n", encoding="utf-8")
gone = lambda pid: False   # noqa: E731
GSD_OK = lambda c, workstream=None: {"outcome": "OK", "reason": "work remains"}  # noqa: E731


def io(children=CLEAR, transcript=True):
    return {"manager": MANAGER, "children": children,
            "find_transcript": (lambda sid: TRANSCRIPT) if transcript else (lambda sid: None)}


class R:
    def __init__(self, out):
        self.stdout, self.stderr, self.returncode = out, "", 0


stops, launches, armed_at_spawn = [], [], []


def stop_run(argv):
    stops.append(argv)
    return R("stopped")


def launch_run(argv, cwd):
    name = argv[argv.index("-n") + 1]
    mid = name.rsplit("-e", 1)[0]
    armed_at_spawn.append(ro.precert_read(mid, STATE))   # spec 3.3: the marker exists BEFORE spawn
    launches.append(argv)
    return R(f"backgrounded · 9e9e9e9e · {name}")


def mission(mid, *, v2=True, epoch=1, state=None, note=None, **extra):
    """A RUNNING mission whose worker <epoch> is owner `s-<mid>`, optionally in HANDOFF with a note."""
    for p in (TMP / "missions").glob(f"gsd-mission-{mid}.json"):
        p.unlink()
    gm.create(str(REPO), "/gsd-autonomous", mission_id=mid, now=NOW, permission_mode="auto",
              rollover_protocol=gm.CAPSULE_V2 if v2 else None)
    owner = {"session_id": f"s-{mid}", "pid": 999, "kind": "background"}
    rec = gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW,
                        state=gm.RUNNING, epoch=epoch, owner=owner, **extra)
    if note is not None:
        rec = gm.transition(mid, expect_epoch=epoch, expect_state=gm.RUNNING, event="t_handoff", now=NOW,
                            state=gm.HANDOFF, note=note,
                            pending={"kind": "handoff", "from": owner["session_id"], "deadline": NOW + 1800})
    if state:
        rec = gm.transition(mid, expect_epoch=epoch, expect_state=rec["state"], event="t_state", now=NOW,
                            state=state)
    return rec


def host(mid, **row):
    base = {"sessionId": f"s-{mid}", "status": "idle", "state": "working", "kind": "background",
            "id": f"s-{mid}"[:8], "pid": 999}
    base.update(row)
    return [{k: v for k, v in base.items() if v is not None}]


def run(sessions, now=NOW, children=CLEAR, transcript=True):
    rows = gm.supervise(now=now, sessions=sessions, gsd_status=GSD_OK, runner=launch_run,
                        stop_runner=stop_run, pid_alive=gone, capsule_io=io(children, transcript))
    return rows


def row_of(rows, mid):
    return next((r for r in rows if r.get("mission_id") == mid), {})


def events(mid):
    return [e.get("event") for e in gm.lr.ledger_events(mid)]


def wipe():
    for p in (TMP / "missions").glob("gsd-mission-*.json"):
        p.unlink()


SPENT = {"max_cycles": 1, "iterations": 5}
GSD_DONE = lambda c, workstream=None: {"outcome": "ALL_COMPLETE", "reason": "milestone done"}  # noqa: E731


def halt_run(sessions, now=NOW, children=CLEAR, transcript=True, gsd=GSD_OK, alive=gone, fp=None):
    return gm.supervise(now=now, sessions=sessions, gsd_status=gsd, runner=launch_run, stop_runner=stop_run,
                        pid_alive=alive, fingerprint=fp, capsule_io=io(children, transcript))


def sealed(key):
    p = ro.capsule_path(key, STATE)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def quiet(fn, *a, **k):
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        return fn(*a, **k)


def halt_section() -> None:
    """Spec 11.1 (S2): a v2 halt is a continuity transition. Every kind with its order of effects, every
    refusal with an admitted twin, and the legacy halt untouched."""
    # --- handoff: idle owner, seal BEFORE the stop, renewal carries the key -------------------------
    wipe()
    mission("m-hh", note="phase 2 half done: wire the gate next", **SPENT)
    n_s = len(stops)
    rows = halt_run(host("m-hh", name="m-hh-e1"))
    r, h, ev = row_of(rows, "m-hh"), gm.load("m-hh"), events("m-hh")
    cont = h.get("continuity") or {}
    check("V-MV2-HALT-HANDOFF",
          h["state"] == gm.HALTED and cont.get("kind") == "handoff" and cont.get("origin") == "worker_handoff"
          and "outgoing_stop_authorized" in ev and "mission_halted" in ev
          and ev.index("outgoing_stop_authorized") < ev.index("mission_halted") and len(stops) == n_s + 1,
          f"cont={cont} ev={ev[-5:]} stops={len(stops) - n_s}")
    nid = r.get("renewed_as")
    new = gm.load(nid) if nid else {}
    check("V-MV2-RENEW-KEY",
          new.get("capsule_key") == "mission-m-hh-e1" and (new.get("continuity_from") or {}).get("kind") == "handoff"
          and new.get("rollover_protocol") == gm.CAPSULE_V2 and new.get("state") == gm.PREPARED,
          f"renewed={nid} key={new.get('capsule_key')} from={new.get('continuity_from')}")
    # the renewal's first worker is a successor: armed before spawn, card block, certifies
    n_l = len(launches)
    halt_run([])
    mk = armed_at_spawn[-1] if len(launches) == n_l + 1 else None
    # A missing card is this gate's FAIL, never a crash: a crash is not a verdict (mutation_drill UNJUDGED).
    argv = launches[-1] if len(launches) == n_l + 1 else []
    card = argv[argv.index("--append-system-prompt") + 1] if "--append-system-prompt" in argv else ""
    check("V-MV2-RENEW-ARM",
          mk is not None and mk.get("worker") == f"{nid}-e1" and mk.get("capsule_key") == "mission-m-hh-e1"
          and not mk.get("certified_at") and "CAPSULE-V2 SUCCESSOR" in card and "mission-m-hh-e1" in card,
          f"mk={mk}")
    key = "mission-m-hh-e1"
    claimant = "9e9e9e9e-0000-4000-8000-0000000000aa"
    rc0 = quiet(ro.resume_flow, sealed(key), claimant, str(REPO), STATE, obligations=["execute phase 2: Wire it"])
    facts = ro.repo_facts(str(REPO))
    ans = {"goal": "STATE.md", "branch": facts.get("branch"), "head": (facts.get("head") or "")[:7],
           "next": "execute phase 2: Wire it"}
    rc1, res = quiet(ro.certify_flow, key, claimant, ans, STATE, mission_id=nid)
    mk = ro.precert_read(nid, STATE) or {}
    check("V-MV2-RENEW-CERTIFY-CROSS", rc0 == 0 and rc1 == 0 and bool(mk.get("certified_at")),
          f"rc={rc0},{rc1} verdict={res.get('verdict')} wrong={res.get('wrong')} mk={mk}")
    # control: the capsule's own mission id names the PREDECESSOR -- read there, the successor's marker stays locked
    ro.precert_arm("m-x2", {"worker": "m-x2-e1", "epoch": 1, "capsule_key": key, "cwd": str(REPO),
                            "resume_cmd": "/gsd-autonomous"}, STATE)
    ro._flip_precert(sealed(key), key, claimant, STATE)
    without = bool((ro.precert_read("m-x2", STATE) or {}).get("certified_at"))
    ro._flip_precert(sealed(key), key, claimant, STATE, "m-x2")
    with_id = bool((ro.precert_read("m-x2", STATE) or {}).get("certified_at"))
    check("V-MV2-RENEW-CERTIFY-CROSS-CONTROL", not without and with_id, f"without={without} with={with_id}")

    # --- handoff refused (no note) -> the degraded fallback at once, no grace wait --------------------
    wipe()
    mission("m-hf", **SPENT)
    rows = halt_run(host("m-hf", name="m-hf-e1"))
    cont = gm.load("m-hf").get("continuity") or {}
    check("V-MV2-HALT-FALLBACK", cont.get("kind") == "handoff" and cont.get("origin") == "supervisor_fallback"
          and bool(row_of(rows, "m-hf").get("renewed_as")), f"cont={cont}")

    # --- recovery: the budget overrides a busy HANDOFF owner; sealed AFTER the stop ------------------
    wipe()
    mission("m-hr", note="n", **SPENT)
    n_s = len(stops)
    rows = halt_run(host("m-hr", name="m-hr-e1", status="busy"))
    r, h, ev = row_of(rows, "m-hr"), gm.load("m-hr"), events("m-hr")
    cont = h.get("continuity") or {}
    cap = sealed("mission-m-hr-e1") or {}
    new = gm.load(r["renewed_as"]) if r.get("renewed_as") else {}
    check("V-MV2-HALT-RECOVERY",
          cont.get("kind") == "recovery" and cont.get("capsule_key") == "mission-m-hr-e1"
          and "outgoing_stop_authorized" not in ev and "continuity_recovery" in ev
          and ev.index("mission_halted") < ev.index("continuity_recovery") and len(stops) == n_s + 1
          and cap.get("seal_origin") == "recovery" and cap.get("degraded") is True
          and new.get("capsule_key") == "mission-m-hr-e1",
          f"cont={cont} ev={ev[-4:]} origin={cap.get('seal_origin')} renewed_key={new.get('capsule_key')}")
    check("V-MV2-HALT-RECOVERY-NEVER-SAFE-TO-FORGET",
          not any("SAFE_TO_FORGET" in str(e.get("reason") or "") for e in gm.lr.ledger_events("m-hr")
                  if e.get("event") in ("mission_halted", "continuity_recovery")),
          "a RECOVERY halt must not be reported SAFE_TO_FORGET")

    # --- refused: recovery seal impossible -> no renewal, named; twin = RECOVERY above ---------------
    wipe()
    mission("m-hx", note="n", **SPENT)
    rows = halt_run(host("m-hx", name="m-hx-e1", status="busy"), children=HOLD)
    r, h = row_of(rows, "m-hx"), gm.load("m-hx")
    check("V-MV2-HALT-REFUSED",
          (h.get("continuity") or {}).get("kind") == "refused" and not r.get("renewed_as")
          and "renewal_refused_no_capsule" in events("m-hx") and h["state"] == gm.HALTED,
          f"cont={h.get('continuity')} renewed={r.get('renewed_as')}")

    # --- UNKNOWN owner: never a successor beside it --------------------------------------------------
    wipe()
    mission("m-hu", **SPENT)
    n_s = len(stops)
    rows = halt_run([], alive=lambda pid: True)
    r, h = row_of(rows, "m-hu"), gm.load("m-hu")
    check("V-MV2-HALT-UNKNOWN",
          (h.get("continuity") or {}).get("kind") == "refused" and "UNKNOWN" in (h.get("continuity") or {}).get("reason", "")
          and not r.get("renewed_as") and sealed("mission-m-hu-e1") is None and len(stops) == n_s,
          f"plan={r.get('reason')} cont={h.get('continuity')}")

    # --- inherited: an uncertified worker has nothing to seal; the renewal keeps its capsule ---------
    wipe()
    mission("m-hi", epoch=2, capsule_key="mission-m-hi-e1", **SPENT)
    ro.precert_arm("m-hi", {"worker": "m-hi-e2", "epoch": 2, "capsule_key": "mission-m-hi-e1",
                            "cwd": str(REPO), "resume_cmd": "/gsd-autonomous"}, STATE)
    rows = halt_run(host("m-hi", state="stopped", status=None))
    r, h = row_of(rows, "m-hi"), gm.load("m-hi")
    new = gm.load(r["renewed_as"]) if r.get("renewed_as") else {}
    check("V-MV2-HALT-INHERITED",
          (h.get("continuity") or {}).get("kind") == "inherited" and new.get("capsule_key") == "mission-m-hi-e1"
          and sealed("mission-m-hi-e2") is None,
          f"cont={h.get('continuity')} renewed_key={new.get('capsule_key')}")

    # --- a halt during a same-session continuation: a RETIRED key is never inherited ----------------
    for gate, retired in (("V-MV2-HALT-CONTINUATION-RETIRED-KEY", True),
                          ("V-MV2-HALT-CONTINUATION-CONTROL-UNRETIRED", False)):
        wipe()
        mission("m-hk", epoch=2, capsule_key="mission-m-hk-e1", **SPENT)
        rec = gm.load("m-hk")
        gm.transition("m-hk", expect_epoch=2, expect_state=rec["state"], event="t", now=NOW, state=gm.LAUNCHING,
                      owner=None, previous_owner=rec["owner"],
                      pending={"kind": "turn_continuation", "epoch": 2, "bg_id": "s-m-hk"[:8],
                               "session_id": "s-m-hk", "deadline": NOW + 600})
        side = ro.capsule_path("mission-m-hk-e1", STATE).with_suffix(".certified")
        side.parent.mkdir(parents=True, exist_ok=True)
        if retired:
            side.write_text("2026-10-05T00:00:00Z", encoding="utf-8")
        elif side.exists():
            side.unlink()
        rows = halt_run(host("m-hk", name="m-hk-e2", status="busy"))
        cont = gm.load("m-hk").get("continuity") or {}
        if retired:
            check(gate, cont.get("kind") == "recovery" and cont.get("capsule_key") == "mission-m-hk-e2",
                  f"cont={cont} plan={row_of(rows, 'm-hk').get('reason')}")
            side.unlink()
        else:
            check(gate, cont.get("kind") == "inherited" and cont.get("capsule_key") == "mission-m-hk-e1", f"cont={cont}")

    # --- none: no renewal due -> nothing sealed; a first worker that never ran -> renewal, no key ----
    wipe()
    mission("m-hn", note="n", renewal=gm.MAX_RENEWALS, **SPENT)
    rows = halt_run(host("m-hn", name="m-hn-e1"))
    r, h = row_of(rows, "m-hn"), gm.load("m-hn")
    check("V-MV2-HALT-NONE",
          (h.get("continuity") or {}).get("kind") == "none" and not r.get("renewed_as")
          and sealed("mission-m-hn-e1") is None and "not renewed" in (r.get("renewal") or ""),
          f"cont={h.get('continuity')} renewal={r.get('renewal')}")
    wipe()
    gm.create(str(REPO), "/gsd-autonomous", mission_id="m-hp", now=NOW - 7200, max_hours=1,
              permission_mode="auto", rollover_protocol=gm.CAPSULE_V2)
    rows = halt_run([])
    r, h = row_of(rows, "m-hp"), gm.load("m-hp")
    new = gm.load(r["renewed_as"]) if r.get("renewed_as") else {}
    check("V-MV2-HALT-NONE-FIRST-WORKER",
          (h.get("continuity") or {}).get("kind") == "none" and bool(new) and not new.get("capsule_key")
          and (new.get("continuity_from") or {}).get("kind") == "none",
          f"cont={h.get('continuity')} new_from={new.get('continuity_from')}")

    # --- complete at budget: no capsule, no renewal ---------------------------------------------------
    wipe()
    mission("m-hc", note="n", **SPENT)
    rows = halt_run(host("m-hc", name="m-hc-e1"), gsd=GSD_DONE)
    check("V-MV2-HALT-COMPLETE", gm.load("m-hc")["state"] == gm.COMPLETED and sealed("mission-m-hc-e1") is None
          and not row_of(rows, "m-hc").get("renewed_as"), str(row_of(rows, "m-hc").get("action")))

    # --- no_progress: terminal, stated ----------------------------------------------------------------
    wipe()
    mission("m-np", note="n", progress={"fp": "X", "stalls": gm.NO_PROGRESS_EPOCHS - 1})
    rows = halt_run(host("m-np", name="m-np-e1"), fp=lambda wd: "X")
    h = gm.load("m-np")
    check("V-MV2-HALT-NOPROGRESS",
          h["state"] == gm.HALTED and (h.get("continuity") or {}).get("kind") == "none"
          and "no_progress" in (h.get("continuity") or {}).get("reason", "") and not row_of(rows, "m-np").get("renewed_as"),
          f"{h['state']} cont={h.get('continuity')} row={row_of(rows, 'm-np').get('reason')}")

    # --- busy-owner bound: clock on the first spent pass, forced RECOVERY past the grace --------------
    wipe()
    mission("m-bb", **SPENT)
    mission("m-bl", v2=False, **SPENT)
    busy = host("m-bb", name="m-bb-e1", status="busy") + host("m-bl", name="m-bl-e1", status="busy")
    n_s = len(stops)
    halt_run(busy)
    b1 = gm.load("m-bb")
    check("V-MV2-BUSY-BOUND-CLOCK", b1.get("budget_spent_at") == NOW and b1["state"] == gm.RUNNING
          and len(stops) == n_s, f"{b1['state']} spent_at={b1.get('budget_spent_at')}")
    rows = halt_run(busy, now=NOW + 600)
    check("V-MV2-BUSY-BOUND-WITHIN-GRACE", gm.load("m-bb")["state"] == gm.RUNNING, row_of(rows, "m-bb").get("reason") or "")
    rows = halt_run(busy, now=NOW + 1800 + 1)
    b2 = gm.load("m-bb")
    check("V-MV2-BUSY-BOUND",
          b2["state"] == gm.HALTED and (b2.get("continuity") or {}).get("kind") == "recovery"
          and "forced" in (row_of(rows, "m-bb").get("reason") or ""),
          f"{b2['state']} cont={b2.get('continuity')} reason={row_of(rows, 'm-bb').get('reason')}")
    lg = gm.load("m-bl")
    check("V-MV2-BUSY-BOUND-CONTROL-LEGACY", lg["state"] == gm.RUNNING and "budget_spent_at" not in lg,
          f"legacy {lg['state']} spent_at={lg.get('budget_spent_at')}")

    # --- legacy halt: none of it ------------------------------------------------------------------
    wipe()
    mission("m-hl", v2=False, note="n", **SPENT)
    rows = halt_run(host("m-hl", name="m-hl-e1"))
    r, h = row_of(rows, "m-hl"), gm.load("m-hl")
    new = gm.load(r["renewed_as"]) if r.get("renewed_as") else {}
    check("V-MV2-HALT-LEGACY-CONTROL",
          h["state"] == gm.HALTED and "continuity" not in h and bool(new) and "capsule_key" not in new
          and "continuity_from" not in new and sealed("mission-m-hl-e1") is None
          and "outgoing_stop_authorized" not in events("m-hl"),
          f"cont={h.get('continuity')} new_keys={sorted(k for k in new if 'capsule' in k or 'contin' in k)}")


def sup(now, sessions, gsd, children=CLEAR):
    return gm.supervise(now=now, sessions=sessions, gsd_status=gsd, runner=launch_run, stop_runner=stop_run,
                        pid_alive=gone, capsule_io=io(children))


def backoff_section() -> None:
    """Spec 11.2 (S3): a seal_refused hold is re-judged on a tree change or after its backoff, never
    every pass; quarantined after 4 refusals on one tree. A hold written before 11.2 is re-judged as before."""
    wipe()
    mission("m-l1", note="n", max_hours=1000)   # the passes span a day: the budget must not be what halts it
    run(host("m-l1"), children=HOLD)                               # first refusal: the G5 clock
    run(host("m-l1"), now=NOW + 1800 + 1, children=HOLD)           # the fallback refuses too: BLOCKED
    h = gm.load("m-l1").get("capsule_hold") or {}
    check("V-MV2-L1-HOLD-BACKOFF-FIELDS",
          h.get("kind") == "seal_refused" and h.get("retries") == 1 and h.get("next_at") == NOW + 1801 + 300
          and bool(h.get("fingerprint")) and h.get("quarantined") is False, str(h))
    asked = []

    def gsd_spy(c, workstream=None):
        asked.append(c)
        return {"outcome": "OK", "reason": "work remains"}

    n_ev = len(events("m-l1"))
    rows = sup(NOW + 1801 + 60, host("m-l1"), gsd_spy, HOLD)
    check("V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT",
          "backed off" in (row_of(rows, "m-l1").get("held") or "") and not asked and len(events("m-l1")) == n_ev,
          f"held={row_of(rows, 'm-l1').get('held')} gsd_calls={len(asked)} new_rows={len(events('m-l1')) - n_ev}")
    sup(NOW + 1801 + 301, host("m-l1"), gsd_spy, HOLD)
    h = gm.load("m-l1").get("capsule_hold") or {}
    check("V-MV2-L1-AFTER-BACKOFF-REJUDGED", len(asked) == 1 and h.get("retries") == 2
          and h.get("next_at") == NOW + 1801 + 301 + 600, f"gsd_calls={len(asked)} hold={h}")
    # a tree change is re-judged at once, inside the backoff, and the count starts again on the new tree
    # (a TRACKED file: the fingerprint is HEAD + tracked dirt, as progress_fingerprint reads the tree)
    change = REPO / ".planning" / "STATE.md"
    change.write_text("# State\nmoved\n", encoding="utf-8")
    try:
        sup(NOW + 1801 + 400, host("m-l1"), gsd_spy, HOLD)
    finally:
        git(REPO, "checkout", "--", ".planning/STATE.md")
    h2 = gm.load("m-l1").get("capsule_hold") or {}
    check("V-MV2-L1-TREE-CHANGE-REJUDGES", len(asked) == 2 and h2.get("retries") == 1
          and h2.get("fingerprint") != h.get("fingerprint"), f"gsd_calls={len(asked)} hold={h2}")
    # the 4th refusal on one tree quarantines: only a tree change re-judges, however long it waits
    rec = gm.load("m-l1")
    gm.transition("m-l1", expect_epoch=rec["epoch"], expect_state=gm.BLOCKED, event="t", now=NOW,
                  capsule_hold={**h, "retries": 3, "next_at": 0})
    sup(NOW + 9000, host("m-l1"), gsd_spy, HOLD)
    q = gm.load("m-l1").get("capsule_hold") or {}
    n_asked = len(asked)
    rows = sup(NOW + 90000, host("m-l1"), gsd_spy, HOLD)
    check("V-MV2-L1-QUARANTINE", q.get("retries") == 4 and q.get("quarantined") is True and len(asked) == n_asked
          and "QUARANTINED" in (row_of(rows, "m-l1").get("held") or ""),
          f"hold={q} held={row_of(rows, 'm-l1').get('held')}")
    # control: a hold written before 11.2 (no `retries`) is re-judged on the next idle pass, as T6 did
    rec = gm.load("m-l1")
    gm.transition("m-l1", expect_epoch=rec["epoch"], expect_state=gm.BLOCKED, event="t", now=NOW,
                  capsule_hold={"kind": "seal_refused", "reason": "old", "since": NOW})
    n_asked = len(asked)
    sup(NOW + 90001, host("m-l1"), gsd_spy, HOLD)
    check("V-MV2-L1-CONTROL-PRE-11-2-HOLD-REJUDGED", len(asked) == n_asked + 1, f"gsd_calls={len(asked) - n_asked}")


def deadline_section() -> None:
    """Spec 11.3 (S4): the budget binds before a capsule hold; at the certify deadline the uncertified
    successor is stopped and replaced (same capsule) below the cap, BLOCKED at it."""
    key = "mission-m-l2-e1"
    succ = "9e9e9e9e-0000-4000-8000-0000000000l2"

    def srow(**kw):
        return [{"sessionId": succ, "status": "busy", "state": "working", "kind": "background",
                 "id": "9e9e9e9e", "pid": 999, "name": "m-l2-e2", **kw}]

    def successor(**extra):
        wipe()
        mission("m-l2", epoch=2, capsule_key=key, capsule_acked_at=NOW, **extra)
        rec = gm.load("m-l2")
        gm.transition("m-l2", expect_epoch=2, expect_state=rec["state"], event="t", now=NOW,
                      owner={"session_id": succ, "pid": 999, "kind": "background"})
        ro.precert_arm("m-l2", {"worker": "m-l2-e2", "epoch": 2, "capsule_key": key, "cwd": str(REPO),
                                "resume_cmd": "/gsd-autonomous"}, STATE)

    # below the cap: stopped, counted, NOT blocked; the next pass replaces it on the same capsule
    successor()
    n_s, n_l = len(stops), len(launches)
    rows = run(srow(), now=NOW + gm.CAPSULE_CERTIFY_DEADLINE_S + 1)
    rec = gm.load("m-l2")
    check("V-MV2-L2-DEADLINE-STOPS-BELOW-CAP",
          rec["state"] == gm.RUNNING and (rec.get("capsule_attempts") or {}).get(key) == 1
          and len(stops) == n_s + 1 and not rec.get("capsule_hold") and not rec.get("capsule_acked_at"),
          f"{rec['state']} attempts={rec.get('capsule_attempts')} stops={len(stops) - n_s} "
          f"action={row_of(rows, 'm-l2').get('action')}")
    rows = run(srow(state="stopped", status=None), now=NOW + gm.CAPSULE_CERTIFY_DEADLINE_S + 60)
    mk = ro.precert_read("m-l2", STATE) or {}
    check("V-MV2-L2-REPLACED-SAME-CAPSULE",
          len(launches) == n_l + 1 and mk.get("worker") == "m-l2-e3" and mk.get("capsule_key") == key
          and not mk.get("certified_at"), f"mk={mk} row={row_of(rows, 'm-l2').get('action')}")
    # at the cap: BLOCKED for a human, as before 11.3
    successor(capsule_attempts={key: gm.MAX_SUCCESSOR_ATTEMPTS - 1})
    n_s = len(stops)
    run(srow(), now=NOW + gm.CAPSULE_CERTIFY_DEADLINE_S + 1)
    rec = gm.load("m-l2")
    check("V-MV2-L2-DEADLINE-AT-CAP-BLOCKS",
          rec["state"] == gm.BLOCKED and (rec.get("capsule_hold") or {}).get("kind") == "resume_not_certified"
          and len(stops) == n_s, f"{rec['state']} hold={rec.get('capsule_hold')}")
    # budget before hold: the blocked uncertified successor is halted by budget (inherited), not held for ever.
    # Built on its OWN at-cap BLOCKED state, never on the outcome above: a broken cap must fail its own gate,
    # not crash the suite (drill 2026-10-05: the CasConflict here left the whole run UNJUDGED).
    successor(capsule_attempts={key: gm.MAX_SUCCESSOR_ATTEMPTS})
    rec = gm.load("m-l2")
    gm.transition("m-l2", expect_epoch=rec["epoch"], expect_state=rec["state"], event="t", now=NOW,
                  state=gm.BLOCKED, capsule_hold={"kind": "resume_not_certified", "reason": "at the cap", "since": NOW},
                  **SPENT)
    p = gm.plan_next(gm.load("m-l2"), NOW + 4000, srow(), gone, v2=True)
    check("V-MV2-L2-BUDGET-BEFORE-HOLD", p["action"] == "halt" and "budget:" in p["reason"], str(p))
    rows = run(srow(), now=NOW + 4000)
    h = gm.load("m-l2")
    new = gm.load(row_of(rows, "m-l2")["renewed_as"]) if row_of(rows, "m-l2").get("renewed_as") else {}
    check("V-MV2-L2-BUDGET-HALT-INHERITS",
          h["state"] == gm.HALTED and (h.get("continuity") or {}).get("kind") == "inherited"
          and new.get("capsule_key") == key, f"cont={h.get('continuity')} new={new.get('capsule_key')}")
    # control: without budget the hold still sticks over the live owner (T6 G4 unchanged)
    p = gm.plan_next({**h, "state": gm.BLOCKED, "iterations": 0}, NOW + 4000, srow(), gone, v2=True)
    check("V-MV2-L2-CONTROL-NO-BUDGET-HOLDS", p["action"] == "none" and "capsule hold" in p["reason"], str(p))


def note_section() -> None:
    """Spec 11.4 (S5): an idle owner with no note is asked ONCE per epoch (same session, nothing sealed);
    still none at its next turn end -> the degraded fallback at once. An explicit note survives BLOCKED.
    The continuation-off control is m-fb in main (T6's grace path)."""
    resumed = []

    def resume_run(argv, cwd):
        if "--resume" in argv:
            resumed.append(argv)
            sid = argv[argv.index("--resume") + 1]
            return R(f"resumed · {sid[:8]} · {sid}")
        return launch_run(argv, cwd)

    def sup_n(now, mid):
        return gm.supervise(now=now, sessions=host(mid), gsd_status=GSD_OK, runner=resume_run,
                            stop_runner=stop_run, pid_alive=gone, capsule_io=io())

    wipe()
    mission("m-nn")
    n_s, n_l = len(stops), len(launches)
    rows = sup_n(NOW, "m-nn")
    rec = gm.load("m-nn")
    check("V-MV2-NOTE-ASKED-ONCE",
          len(resumed) == 1 and gm.NOTE_TAG in resumed[-1][-1] and (rec.get("capsule_note_asked") or {}).get("epoch") == 1
          and len(launches) == n_l and sealed("mission-m-nn-e1") is None and rec["state"] == gm.LAUNCHING
          and "capsule_note_asked" in events("m-nn"),
          f"resumed={len(resumed)} asked={rec.get('capsule_note_asked')} state={rec['state']} "
          f"action={row_of(rows, 'm-nn').get('action')} held={row_of(rows, 'm-nn').get('held')}")
    # the resumed session acks; its next turn end STILL has no note -> fallback at once (no 30-min wait)
    gm.ack_session("s-m-nn", now=NOW + 5)
    # Past the continuation deadline: a turn end is held until the resumed turn shows in the transcript
    # or that deadline passes, and this harness has no transcript. Still well inside the 30-min grace.
    import gsd_epoch as ge
    rows = sup_n(NOW + 5 + ge.CONTINUATION_DEADLINE_S + 1, "m-nn")
    rec = gm.load("m-nn")
    check("V-MV2-NOTE-STILL-NONE-FALLBACK-AT-ONCE",
          (rec.get("capsule_stop_authorized") or {}).get("origin") == "supervisor_fallback" and len(resumed) == 1
          and len(launches) == n_l + 1, f"auth={rec.get('capsule_stop_authorized')} resumed={len(resumed)} "
                                        f"row={row_of(rows, 'm-nn').get('action')}/{row_of(rows, 'm-nn').get('held')}")
    # an explicit note written in HANDOFF still counts after the mission went BLOCKED (no question asked)
    wipe()
    mission("m-nb", note="phase 2: the gate is wired, tests next")
    gm.transition("m-nb", expect_epoch=1, expect_state=gm.HANDOFF, event="t", now=NOW, state=gm.BLOCKED,
                  capsule_hold={"kind": "seal_refused", "reason": "x", "since": NOW})
    n_r = len(resumed)
    sup_n(NOW + 10, "m-nb")
    rec = gm.load("m-nb")
    check("V-MV2-NOTE-EXPLICIT-SURVIVES-BLOCKED",
          len(resumed) == n_r and (rec.get("capsule_stop_authorized") or {}).get("origin") == "worker_handoff",
          f"auth={rec.get('capsule_stop_authorized')} resumed={len(resumed) - n_r}")


def main() -> int:
    # --- arm: G11 + field absent on legacy ------------------------------------------------------
    try:
        gm.create(str(REPO), "/gsd-autonomous", mission_id="m-mode", now=NOW,
                  permission_mode="acceptEdits", rollover_protocol=gm.CAPSULE_V2)
        check("V-MV2-ARM-REFUSES-SHELLLESS-MODE", False, "acceptEdits was accepted for capsule-v2")
    except gm.MissionError as exc:
        check("V-MV2-ARM-REFUSES-SHELLLESS-MODE", "permission mode" in str(exc), str(exc))
    try:
        gm.create(str(REPO), "/gsd-autonomous", mission_id="m-proto", now=NOW, rollover_protocol="capsule-v3")
        check("V-MV2-ARM-REFUSES-UNKNOWN-PROTOCOL", False, "capsule-v3 accepted")
    except gm.MissionError as exc:
        check("V-MV2-ARM-REFUSES-UNKNOWN-PROTOCOL", "unknown rollover protocol" in str(exc), str(exc))
    v2rec = gm.create(str(REPO), "/gsd-autonomous", mission_id="m-armv2", now=NOW, permission_mode="auto",
                      rollover_protocol=gm.CAPSULE_V2)
    legrec = gm.create(str(REPO), "/gsd-autonomous", mission_id="m-armleg", now=NOW, permission_mode="auto")
    check("V-MV2-ARM-FIELD-ONLY-WHEN-ASKED",
          v2rec.get("rollover_protocol") == gm.CAPSULE_V2 and "rollover_protocol" not in legrec
          and "rollover_protocol" not in json.loads(gm.mission_path("m-armleg").read_text(encoding="utf-8")),
          f"v2={v2rec.get('rollover_protocol')} legacy keys has={('rollover_protocol' in legrec)}")
    rc = gm._cli(["arm", "--cwd", str(REPO), "--command", "/gsd-autonomous", "--no-launch",
                  "--rollover-protocol", gm.CAPSULE_V2])
    armed = [m for m in gm.all_missions() if m.get("rollover_protocol") == gm.CAPSULE_V2
             and m["mission_id"] not in ("m-armv2",)]
    check("V-MV2-CLI-ARM-FLAG", rc == 0 and len(armed) == 1, f"rc={rc} armed={[m['mission_id'] for m in armed]}")

    # --- argv: G9 MCP strip, legacy untouched --------------------------------------------------
    a2 = gm.worker_argv(v2rec, "/gsd-autonomous")
    al = gm.worker_argv(legrec, "/gsd-autonomous")
    check("V-MV2-ARGV-STRIPS-MCP", "--strict-mcp-config" in a2 and "--strict-mcp-config" not in al,
          f"v2 has={('--strict-mcp-config' in a2)} legacy has={('--strict-mcp-config' in al)}")
    wipe()

    # --- happy rotation: seal -> authorize -> stop -> arm -> spawn -> bind ---------------------
    mission("m-hap", note="phase 2 half done: wire the gate next")
    n_s, n_l = len(stops), len(launches)
    rows = run(host("m-hap"))
    r = row_of(rows, "m-hap")
    rec = gm.load("m-hap")
    key = "mission-m-hap-e1"
    ev = events("m-hap")
    mk = ro.precert_read("m-hap", STATE)
    check("V-MV2-ROTATE-SEALS-AND-AUTHORIZES",
          rec.get("capsule_key") == key and (rec.get("capsule_stop_authorized") or {}).get("origin") == "worker_handoff"
          and "outgoing_stop_authorized" in ev, f"capsule={r.get('capsule')} key={rec.get('capsule_key')}")
    check("V-MV2-AUTHORIZED-BEFORE-STOP-AND-CLAIM",
          "outgoing_stop_authorized" in ev and "launch_claimed" in ev
          and ev.index("outgoing_stop_authorized") < ev.index("launch_claimed") and len(stops) == n_s + 1,
          f"events={ev[-6:]} stops={len(stops) - n_s}")
    spawned_mk = armed_at_spawn[-1] if len(launches) == n_l + 1 else None
    check("V-MV2-MARKER-ARMED-BEFORE-SPAWN",
          spawned_mk is not None and spawned_mk.get("worker") == "m-hap-e2"
          and spawned_mk.get("capsule_key") == key and not spawned_mk.get("certified_at"), str(spawned_mk))
    check("V-MV2-MARKER-BOUND-TO-BG-ID", (mk or {}).get("bg_id") == "9e9e9e9e", str(mk))
    card = launches[-1][launches[-1].index("--append-system-prompt") + 1] if len(launches) == n_l + 1 else ""
    check("V-MV2-CARD-HAS-V2-BLOCK", "CAPSULE-V2 SUCCESSOR" in card and key in card
          and "mission_capsule.py resume --mission m-hap" in card, card[:200])
    check("V-MV2-SUCCESSOR-ARGV-STRIPS-MCP", "--strict-mcp-config" in (launches[-1] if launches else []))
    # spec 11.5: the marker the guard reads names the runnable script (one constant, also on the card)
    check("V-MV2-MARKER-NAMES-TOOL",
          spawned_mk is not None and spawned_mk.get("tool") == mc.TOOL and Path(mc.TOOL).is_file()
          and mc.TOOL.endswith("/mission_capsule.py") and f"python {mc.TOOL} resume" in card
          and spawned_mk.get("tool") != spawned_mk.get("resume_cmd"),
          f"tool={(spawned_mk or {}).get('tool')} resume_cmd={(spawned_mk or {}).get('resume_cmd')}")

    # ack: the successor's own hook binds its session and starts the certification clock
    succ = "9e9e9e9e-0000-4000-8000-000000000001"
    gm.ack_session(succ, now=NOW + 10)
    rec = gm.load("m-hap")
    mk = ro.precert_read("m-hap", STATE)
    check("V-MV2-ACK-BINDS-AND-CLOCKS", rec.get("capsule_acked_at") == NOW + 10
          and (mk or {}).get("owner_session") == succ, f"acked={rec.get('capsule_acked_at')} mk={mk}")

    # --- uncertified successor: never rotated while alive; BLOCKED past the deadline -----------
    busy = [{"sessionId": succ, "status": "idle", "state": "working", "kind": "background",
             "id": "9e9e9e9e", "pid": 999}]
    n_s, n_l = len(stops), len(launches)
    rows = run(busy, now=NOW + 60)
    r = row_of(rows, "m-hap")
    check("V-MV2-UNCERTIFIED-NOT-ROTATED", "has not certified" in (r.get("held") or "")
          and len(stops) == n_s and len(launches) == n_l, f"{r.get('action')} held={r.get('held')}")
    # At the per-capsule cap (spec 11.3; below it the successor is stopped and replaced, deadline_section).
    rec = gm.load("m-hap")
    gm.transition("m-hap", expect_epoch=rec["epoch"], expect_state=rec["state"], event="t", now=NOW + 60,
                  capsule_attempts={key: gm.MAX_SUCCESSOR_ATTEMPTS - 1})
    rows = run(busy, now=NOW + 10 + gm.CAPSULE_CERTIFY_DEADLINE_S + 1)
    rec = gm.load("m-hap")
    check("V-MV2-CERTIFY-DEADLINE-BLOCKS",
          rec["state"] == gm.BLOCKED and (rec.get("capsule_hold") or {}).get("kind") == "resume_not_certified",
          f"{rec['state']} hold={rec.get('capsule_hold')}")
    p = gm.plan_next(rec, NOW + 4000, busy, gone, v2=True)
    check("V-MV2-HOLD-STICKS-OVER-LIVE-OWNER", p["action"] == "none" and "capsule hold" in p["reason"], str(p))
    p_leg = gm.plan_next({**rec, "rollover_protocol": None}, NOW + 4000,
                         [{**busy[0], "status": "busy"}], gone)
    check("V-MV2-HOLD-CONTROL-LEGACY-UNBLOCKS", p_leg["action"] == "unblock", str(p_leg))
    ro.precert_write("m-hap", {"certified_at": NOW + 4100}, STATE)   # the flip rollover.certify_flow makes
    rows = run(busy, now=NOW + 4200)
    rec = gm.load("m-hap")
    check("V-MV2-CERTIFICATION-LIFTS-HOLD", rec["state"] == gm.RUNNING and not rec.get("capsule_hold")
          and row_of(rows, "m-hap").get("action") == "capsule_certified", f"{rec['state']} {rec.get('capsule_hold')}")

    # --- a dead uncertified successor: its replacement inherits the SAME capsule (G6) -----------
    wipe()
    mission("m-inh", epoch=2, capsule_key="mission-m-inh-e1")
    ro.precert_arm("m-inh", {"worker": "m-inh-e2", "epoch": 2, "capsule_key": "mission-m-inh-e1",
                             "cwd": str(REPO), "resume_cmd": "/gsd-autonomous"}, STATE)
    n_l = len(launches)
    rows = run(host("m-inh", state="stopped", status=None))
    mk = ro.precert_read("m-inh", STATE)
    check("V-MV2-DEAD-UNCERTIFIED-INHERITS",
          len(launches) == n_l + 1 and (mk or {}).get("worker") == "m-inh-e3"
          and mk.get("capsule_key") == "mission-m-inh-e1" and "inherited" in (row_of(rows, "m-inh").get("capsule") or ""),
          f"mk={mk} capsule={row_of(rows, 'm-inh').get('capsule')}")

    # --- refusal: nothing stopped; clock; fallback past grace; BLOCKED when that refuses too ---
    wipe()
    mission("m-ref", note="n")
    n_s, n_l = len(stops), len(launches)
    rows = run(host("m-ref"), children=HOLD)
    rec = gm.load("m-ref")
    check("V-MV2-REFUSED-NOTHING-STOPPED",
          len(stops) == n_s and len(launches) == n_l and rec.get("capsule_first_refused_at") == NOW
          and "fallback clock started" in (row_of(rows, "m-ref").get("held") or ""),
          f"stops={len(stops) - n_s} held={row_of(rows, 'm-ref').get('held')}")
    rows = run(host("m-ref"), now=NOW + 600, children=HOLD)
    check("V-MV2-REFUSED-WITHIN-GRACE-HELD", len(stops) == n_s and gm.load("m-ref")["state"] == gm.HANDOFF,
          row_of(rows, "m-ref").get("held") or "")
    rows = run(host("m-ref"), now=NOW + 1800 + 1, children=HOLD)
    rec = gm.load("m-ref")
    check("V-MV2-FALLBACK-IMPOSSIBLE-BLOCKS-NOT-STOPPED",
          rec["state"] == gm.BLOCKED and (rec.get("capsule_hold") or {}).get("kind") == "seal_refused"
          and len(stops) == n_s and len(launches) == n_l, f"{rec['state']} hold={rec.get('capsule_hold')}")

    # control twin: no note -> handoff refused, clock; past grace the degraded fallback seals and stops.
    # With same-session continuation OFF: nobody can be asked for a note (spec 11.4), so T6's grace path stands.
    wipe()
    mission("m-fb")
    n_s, n_l = len(stops), len(launches)
    os.environ["CPP_MISSION_CONTINUATION"] = "off"
    try:
        run(host("m-fb"))
        check("V-MV2-NO-NOTE-HANDOFF-REFUSED", len(stops) == n_s and gm.load("m-fb").get("capsule_first_refused_at"))
        run(host("m-fb"), now=NOW + 1800 + 1)
    finally:
        os.environ.pop("CPP_MISSION_CONTINUATION", None)
    rec = gm.load("m-fb")
    cap = json.loads(ro.capsule_path("mission-m-fb-e1", STATE).read_text(encoding="utf-8")) \
        if ro.capsule_path("mission-m-fb-e1", STATE).is_file() else {}
    check("V-MV2-FALLBACK-PAST-GRACE-SEALS-DEGRADED",
          (rec.get("capsule_stop_authorized") or {}).get("origin") == "supervisor_fallback" and cap.get("degraded")
          and len(stops) == n_s + 1 and len(launches) == n_l + 1, f"auth={rec.get('capsule_stop_authorized')}")

    # --- dead owner: recovery capsule (G21) --------------------------------------------------------
    wipe()
    mission("m-rec")
    n_l = len(launches)
    run(host("m-rec", state="stopped", status=None), transcript=False)
    rec = gm.load("m-rec")
    check("V-MV2-DEAD-OWNER-RECOVERY", (rec.get("capsule_stop_authorized") or {}).get("origin") == "recovery"
          and len(launches) == n_l + 1, str(rec.get("capsule_stop_authorized")))

    # --- arming failure: no marker, no spawn ------------------------------------------------------
    wipe()
    mission("m-arm", note="n")
    real_arm = mc.arm_successor
    mc.arm_successor = lambda *a, **k: (_ for _ in ()).throw(OSError("disk full"))
    try:
        n_l = len(launches)
        rows = run(host("m-arm"))
    finally:
        mc.arm_successor = real_arm
    check("V-MV2-ARM-FAILURE-NO-SPAWN", len(launches) == n_l and "not armed" in (row_of(rows, "m-arm").get("held") or "")
          and "capsule_arm_failed" in events("m-arm"), row_of(rows, "m-arm").get("held") or "")

    # --- kill switches: a v2 mission rotates the legacy way ---------------------------------------
    for gate, setup, teardown in (
            ("V-MV2-KILL-SWITCH-FILE", lambda: (STATE / "capsule-v2.off").write_text("", encoding="utf-8"),
             lambda: (STATE / "capsule-v2.off").unlink()),
            ("V-MV2-KILL-SWITCH-ENV", lambda: os.environ.__setitem__("CPP_CAPSULE_ROLLOVER", "off"),
             lambda: os.environ.pop("CPP_CAPSULE_ROLLOVER", None))):
        wipe()
        mission("m-ks", note="n")
        STATE.mkdir(parents=True, exist_ok=True)
        setup()
        try:
            n_l = len(launches)
            run(host("m-ks"))
        finally:
            teardown()
        rec = gm.load("m-ks")
        check(gate, len(launches) == n_l + 1 and not rec.get("capsule_key")
              and "outgoing_stop_authorized" not in events("m-ks"), f"key={rec.get('capsule_key')}")

    # --- legacy control: the same happy scenario, none of the v2 effects ---------------------------
    wipe()
    mission("m-leg", v2=False, note="n")
    n_l = len(launches)
    run(host("m-leg"))
    rec = gm.load("m-leg")
    card = launches[-1][launches[-1].index("--append-system-prompt") + 1] if len(launches) == n_l + 1 else ""
    check("V-MV2-LEGACY-CONTROL-UNTOUCHED",
          len(launches) == n_l + 1 and not rec.get("capsule_key") and ro.precert_read("m-leg", STATE) is None
          and "CAPSULE-V2" not in card and "outgoing_stop_authorized" not in events("m-leg"),
          f"key={rec.get('capsule_key')} marker={ro.precert_read('m-leg', STATE)}")

    # --- renewal carries the protocol (G20) --------------------------------------------------------
    wipe()
    rec = mission("m-ren", note="n")
    new = gm.renew_mission({**rec, "state": gm.HALTED}, now=NOW)
    check("V-MV2-RENEW-CARRIES-PROTOCOL", new.get("rollover_protocol") == gm.CAPSULE_V2, str(new.get("rollover_protocol")))

    # --- card: the v2 block survives the byte cap (G22) --------------------------------------------
    big = gm.render_card({**rec, "epoch": 2, "capsule_key": "mission-m-ren-e1", "note": "N" * 9000},
                         {"head": "abc", "dirty": 0, "recent": ["x"] * 5}, "G" * 3000)
    check("V-MV2-CARD-BLOCK-SURVIVES-CAP", "CAPSULE-V2 SUCCESSOR" in big and "[card truncated at cap]" in big
          and big.index("CAPSULE-V2") < big.index("GSD:"), f"{len(big.encode())} bytes")
    nokey = gm.render_card({**rec, "epoch": 1, "note": ""}, None)
    check("V-MV2-CARD-CONTROL-NO-KEY-NO-BLOCK", "CAPSULE-V2" not in nokey)

    # --- review M1: an undecidable v2 record is isolated, fail-closed, and blinds nobody else ----
    wipe()
    mission("m-err", note="n")
    mission("m-oth", v2=False, note="n")
    real_sd = mc.state_dir
    mc.state_dir = lambda explicit=None: (_ for _ in ()).throw(PermissionError("state dir held"))
    n_s, n_l = len(stops), len(launches)
    try:
        rows = run(host("m-err") + host("m-oth"))
    except Exception as exc:  # noqa: BLE001 -- the pre-fix shape: the pass itself dies
        rows = [{"mission_id": "m-err", "error": f"PASS ABORTED {type(exc).__name__}: {exc}"}]
    finally:
        mc.state_dir = real_sd
    r_err, r_oth = row_of(rows, "m-err"), row_of(rows, "m-oth")
    check("V-MV2-UNDECIDABLE-ISOLATED-FAIL-CLOSED",
          "capsule-v2 undecidable" in (r_err.get("error") or "") and gm.load("m-err")["state"] == gm.HANDOFF
          and not any(a[a.index("-n") + 1].startswith("m-err") for a in launches[n_l:])
          and not any("s-m-err"[:8] in " ".join(s) for s in stops[n_s:]),
          f"err={r_err.get('error')} state={gm.load('m-err')['state']}")
    check("V-MV2-UNDECIDABLE-CONTROL-OTHERS-SUPERVISED",
          (r_oth.get("launch") or {}).get("ok") is True, f"other={r_oth.get('action')} launch={r_oth.get('launch')}")

    halt_section()
    backoff_section()
    deadline_section()
    note_section()
    trap_hits = list(TRAP.rglob("*")) if TRAP.exists() else []
    check("V-MV2-TRAP-UNTOUCHED", not trap_hits, str(trap_hits[:3]))
    print(f"MV2_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
