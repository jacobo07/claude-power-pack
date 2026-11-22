#!/usr/bin/env python
"""V-AMRX-* gates: decision + environment + executor-loss recovery through the REAL supervisor pass.

Fixture = the kobicraft-web incident of 2026-10-12 (m-5cd1a041bc0f), at zero provider cost: repo policy
`use_worktrees: false`, a background worker the host lists `blocked` with no `waitingFor`, whose job record's
`needs` is the worker's own question about a worktree. Expected: one successor on the main tree carrying the
runtime's answer, worktree tools withheld -- not a 21 h park. Every refusal has a paired control.
Hermetic: state dir, jobs dir, Claude config dir and work trees are temp directories.

Run: python tools/test_mission_decision_recovery.py   (exit 0 = all pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="amrx-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cc")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "cc" / "projects")  # transcripts: never the real ones
for k in ("CPP_MISSION_RECOVERY", "CPP_MISSION_DECISION_RECOVERY", "CPP_ROUTE_ADMISSION", "CPP_CCR_ADMISSION",
          "CPP_COG_ADMISSION"):
    os.environ.pop(k, None)
# Hermetic: no quota reading exists in the temp state dir, so BAMR account admission (bf315ce6) refuses every launch
# as UNKNOWN. That refusal is test_mission_account_admission's subject, not this suite's.
os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_policy as mp  # noqa: E402

gm.progress_fingerprint = lambda work_dir: "fp-fixture"
GIT = gm.resolve_exe("git")
NOW = 1_800_000_000.0
GSD_OK = lambda wd, workstream=None: {"outcome": "OK"}  # noqa: E731
QUESTION = "cd` into the worktree and restart the session from there?"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}"[:220])
    else:
        fails += 1
        print(f"FAIL {gate} {ev}"[:400])


def make_repo(name: str, use_worktrees) -> Path:
    wd = Path(TMP) / name
    (wd / ".planning").mkdir(parents=True)
    cfg = {"runtime": "claude"}
    if use_worktrees is not None:
        cfg["workflow"] = {"use_worktrees": use_worktrees}
    (wd / ".planning" / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    (wd / ".planning" / "STATE.md").write_text("---\ncurrent_phase: 01\n---\n", encoding="utf-8")
    (wd / ".planning" / "ROADMAP.md").write_text("### Phase 1: Truth\n**Success Criteria**:\n  1. x\n", encoding="utf-8")
    for a in (("init", "-q"), ("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"),
              ("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed")):
        subprocess.run([GIT, "-C", str(wd), *a], capture_output=True, text=True, check=True)
    return wd


def blocked_mission(mid: str, wd: Path, *, needs: str | None = QUESTION, waiting_for=None, recoveries=0,
                    fp=None) -> dict:
    gm.create(str(wd), "/gsd-autonomous", mission_id=mid, now=NOW)
    sid = f"{mid}-worker"
    owner = {"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1, "kind": "background"}
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.BLOCKED,
                  epoch=1, max_hours=100.0, owner=owner, decision_recoveries=recoveries,
                  **({"decision_recovery_fp": fp} if fp else {}))
    if needs is not None or waiting_for:
        j = Path(os.environ["CPP_CLAUDE_JOBS_DIR"]) / sid[:8]
        j.mkdir(parents=True, exist_ok=True)
        (j / "state.json").write_text(json.dumps({"state": "blocked", "needs": needs, "detail": needs,
                                                  "waitingFor": waiting_for, "sessionId": sid}), encoding="utf-8")
    return gm.load(mid)


def host_rows(*mids, waiting_for=None):
    return [{"sessionId": f"{m}-worker", "id": f"{m}-worker"[:8], "kind": "background", "state": "blocked",
             **({"waitingFor": waiting_for} if waiting_for else {})} for m in mids]


ARGVS = []


def host(argv, cwd):
    ARGVS.append(argv)
    return subprocess.CompletedProcess(argv, 0, f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}", "")


def stop_ok(argv):
    return subprocess.CompletedProcess(argv, 0, "", "")


def pair(argv, flag, value):
    return any(argv[i] == flag and argv[i + 1] == value for i in range(len(argv) - 1))


def main() -> int:
    # Arrange: the incident repo (policy forbids worktrees).
    wd = make_repo("kobicraft-web", False)

    # 1. plan_next types the bare `blocked` from the job's `needs` and plans a replace that carries the answer.
    r1 = blocked_mission("m-bbb000000001", wd)
    p1 = gm.plan_next(r1, NOW + 60, host_rows("m-bbb000000001"), pid_alive=lambda p: False)
    check("V-AMRX-PLAN-REPLACE", p1["action"] == "replace" and p1.get("decision", {}).get("class") == "QUESTION_RESOLVABLE",
          f"{p1['action']}: {p1['reason'][:120]}")
    check("V-AMRX-PLAN-POLICY", (p1.get("decision") or {}).get("gate", {}).get("result") == "RESOLVE_BY_POLICY",
          "answered by .planning/config.json, not by a default")

    # 2. The real supervisor pass: one successor launched, worktree tools withheld, answer in the note, ledgered.
    ARGVS.clear()
    rows = gm._supervise_core(now=NOW + 60, sessions=host_rows("m-bbb000000001"), gsd_status=GSD_OK, runner=host,
                              stop_runner=stop_ok, pid_alive=lambda p: False)
    row = next((r for r in rows if r.get("mission_id") == "m-bbb000000001"), {})
    s1 = gm.load("m-bbb000000001")
    check("V-AMRX-SUCCESSOR-LAUNCHED", (row.get("launch") or {}).get("ok") and s1["state"] == gm.LAUNCHING
          and s1["epoch"] == 2 and len(ARGVS) == 1, f"state={s1['state']} epoch={s1['epoch']} launches={len(ARGVS)}")
    a = ARGVS[0] if ARGVS else []
    check("V-AMRX-ARGV-NO-WORKTREE", not pair(a, "--allowedTools", "EnterWorktree")
          and pair(a, "--disallowedTools", "EnterWorktree") and pair(a, "--disallowedTools", "ExitWorktree"),
          "use_worktrees=false compiled into the launch")
    check("V-AMRX-NOTE-ANSWER", "RUNTIME ANSWER" in (s1.get("note") or "") and "main checkout" in (s1.get("note") or ""),
          f"note chars {len(s1.get('note') or '')}")
    check("V-AMRX-CARD-ANSWER", "RUNTIME ANSWER" in (s1.get("card") or ""), "the card the successor reads carries it")
    ev = [e.get("event") for e in gm.lr.ledger_events("m-bbb000000001")]
    check("V-AMRX-LEDGER", "decision_recovered" in ev and s1.get("decision_recoveries") == 1,
          f"decision_recoveries={s1.get('decision_recoveries')}")
    check("V-AMRX-OLD-OWNER-RELEASED", (s1.get("previous_owner") or {}).get("session_id") == "m-bbb000000001-worker"
          and s1.get("owner") is None, "lease left the predecessor at the claim")

    # 3. Transaction: a second pass right after does not launch a second successor.
    ARGVS.clear()
    gm._supervise_core(now=NOW + 120, sessions=host_rows("m-bbb000000001"), gsd_status=GSD_OK, runner=host,
                       stop_runner=stop_ok, pid_alive=lambda p: False)
    check("V-AMRX-NO-DOUBLE-SUCCESSOR", len(ARGVS) == 0 and gm.load("m-bbb000000001")["epoch"] == 2,
          f"launches={len(ARGVS)}")

    # 4. WORKTREE_POLICY_VIOLATION: the predecessor actually worked inside a worktree its repo forbids.
    #    The successor is NOT sent into it (it was in M6-style following before AMR-X).
    import mission_spend as msp
    wt = Path(TMP) / "manual-wt"
    subprocess.run([GIT, "-C", str(wd), "worktree", "add", "-q", "-b", "gsd/manual", str(wt), "HEAD"],
                   capture_output=True, text=True, check=True)
    r8 = blocked_mission("m-bbb000000008", wd)
    d = msp.projects_root() / msp.encode_cwd(str(wd))
    d.mkdir(parents=True, exist_ok=True)
    (d / "m-bbb000000008-worker.jsonl").write_text(json.dumps({"type": "user", "cwd": str(wt), "message": {
        "content": "x"}}) + "\n", encoding="utf-8")
    followed = gm.effective_workdir("m-bbb000000008-worker", str(wd))
    ARGVS.clear()
    rows8 = gm._supervise_core(now=NOW + 60, sessions=host_rows("m-bbb000000008"), gsd_status=GSD_OK, runner=host,
                               stop_runner=stop_ok, pid_alive=lambda p: False)
    s8 = gm.load("m-bbb000000008")
    ev8 = [e.get("event") for e in gm.lr.ledger_events("m-bbb000000008")]
    check("V-AMRX-WORKTREE-NOT-FOLLOWED", followed is not None and "worktree_not_followed" in ev8
          and str(wt).lower() not in str(s8.get("work_dir") or "").lower() and len(ARGVS) == 1,
          f"fixture followed={bool(followed)} work_dir={s8.get('work_dir')} events={'worktree_not_followed' in ev8}")

    # Controls: what must STILL reach a human, or stay untouched.
    r = blocked_mission("m-bbb000000002", wd, needs=None, waiting_for="approve Bash")
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000002", waiting_for="approve Bash"), pid_alive=lambda p: False)
    check("V-AMRX-CTRL-PERMISSION", p["action"] == "surface_blocked", p["reason"][:100])
    r = blocked_mission("m-bbb000000003", wd, needs="Shall I push to main and deploy to production?")
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000003"), pid_alive=lambda p: False)
    check("V-AMRX-CTRL-OWNER-CLASS", p["action"] == "surface_blocked" and "OWNER_BOUNDARY" in p["reason"], p["reason"][:100])
    r = blocked_mission("m-bbb000000004", wd, needs="login required")
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000004"), pid_alive=lambda p: False)
    check("V-AMRX-CTRL-HOST-GATE", p["action"] == "surface_blocked" and "OWNER_BOUNDARY" not in p["reason"], p["reason"][:100])
    r = blocked_mission("m-bbb000000005", wd, needs=None)
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000005"), pid_alive=lambda p: False)
    check("V-AMRX-CTRL-NO-JOB", p["action"] == "surface_blocked", "no job record -> unchanged")
    r = blocked_mission("m-bbb000000006", wd, recoveries=gm.MAX_DECISION_RECOVERIES)
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000006"), pid_alive=lambda p: False)
    check("V-AMRX-CTRL-CAP", p["action"] == "surface_blocked" and "decision recoveries" in p["reason"], p["reason"][:100])
    # 2026-10-25 (GEX44 m-8f97c4d49069): the cap counts recoveries with NO progress between them.
    r = blocked_mission("m-bbb0000000c1", wd, recoveries=gm.MAX_DECISION_RECOVERIES, fp="fp-fixture")
    p = gm.plan_next(r, NOW, host_rows("m-bbb0000000c1"), pid_alive=lambda p: False)
    check("V-AMRX-CAP-NO-PROGRESS", p["action"] == "surface_blocked" and "decision recoveries" in p["reason"],
          "tree unchanged since the last recovery: the cap binds")
    r = blocked_mission("m-bbb0000000c2", wd, recoveries=gm.MAX_DECISION_RECOVERIES, fp="fp-before")
    p = gm.plan_next(r, NOW, host_rows("m-bbb0000000c2"), pid_alive=lambda p: False)
    check("V-AMRX-CAP-RESET-ON-PROGRESS", p["action"] == "replace", f"tree moved: {p['action']}")
    os.environ["CPP_DECISION_RECOVERY_CAP"] = "lifetime"
    p = gm.plan_next(r, NOW, host_rows("m-bbb0000000c2"), pid_alive=lambda p: False)
    os.environ.pop("CPP_DECISION_RECOVERY_CAP")
    check("V-AMRX-CAP-KILL-SWITCH", p["action"] == "surface_blocked", "lifetime restores the old cap")
    ARGVS.clear()
    gm._supervise_core(now=NOW + 60, sessions=host_rows("m-bbb0000000c2"), gsd_status=GSD_OK, runner=host,
                       stop_runner=stop_ok, pid_alive=lambda p: False)
    sc = gm.load("m-bbb0000000c2")
    check("V-AMRX-CAP-COUNTER-RESET", len(ARGVS) == 1 and sc.get("decision_recoveries") == 1
          and sc.get("decision_recovery_fp") == "fp-fixture",
          f"launches={len(ARGVS)} recoveries={sc.get('decision_recoveries')} fp={sc.get('decision_recovery_fp')}")
    os.environ["CPP_MISSION_DECISION_RECOVERY"] = "off"
    r = blocked_mission("m-bbb000000007", wd)
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000007"), pid_alive=lambda p: False)
    a_off = gm.worker_argv(r, "/gsd-autonomous")
    os.environ.pop("CPP_MISSION_DECISION_RECOVERY")
    check("V-AMRX-CTRL-KILL-SWITCH", p["action"] == "surface_blocked" and pair(a_off, "--allowedTools", "EnterWorktree"),
          "off restores both behaviours")
    p = gm.plan_next(r, NOW, [{"sessionId": "m-bbb000000007-worker", "id": "m-bbb0000", "kind": "background",
                                "state": "busy"}], pid_alive=lambda p: False)
    check("V-AMRX-CTRL-LIVE-WORKER", p["action"] != "replace", f"live busy worker: {p['action']}")

    # Review F3: the HOST row says waitingFor, the job file does not -> still a live permission prompt.
    r = blocked_mission("m-bbb000000009", wd, needs="Allow Bash(npm test)?")
    p = gm.plan_next(r, NOW, host_rows("m-bbb000000009", waiting_for="Bash"), pid_alive=lambda p: False)
    check("V-AMRX-CTRL-HOST-WAITINGFOR", p["action"] == "surface_blocked", p["reason"][:100])
    # Ascension T1 O5 (GEX44 MKWLIB m-36c04360244c, 2026-11-22): a live worktree-entry prompt IS recovered.
    r = blocked_mission("m-ddd00000000a", wd, needs="approve Entering worktree", waiting_for="approve Entering worktree")
    p = gm.plan_next(r, NOW, host_rows("m-ddd00000000a", waiting_for="approve Entering worktree"),
                     pid_alive=lambda p: False)
    check("V-AMRX-WORKTREE-PROMPT-RECOVERED", p["action"] == "replace" and "decision recovery" in p["reason"],
          p["reason"][:120])

    # Review F2: the launch fails after the answer was decided; the retry still carries it; adoption clears it.
    r10 = blocked_mission("m-bbb00000000a", wd)
    fail_host = lambda argv, cwd: subprocess.CompletedProcess(argv, 1, "", "launch refused")  # noqa: E731
    gm._supervise_core(now=NOW + 60, sessions=host_rows("m-bbb00000000a"), gsd_status=GSD_OK, runner=fail_host,
                       stop_runner=stop_ok, pid_alive=lambda p: False)
    s10 = gm.load("m-bbb00000000a")
    check("V-AMRX-ANSWER-PERSISTED", "RUNTIME ANSWER" in (s10.get("pending_decision") or "")
          and s10["state"] == gm.LAUNCHING, f"state={s10['state']} after a failed launch")
    ARGVS.clear()
    gm._supervise_core(now=NOW + 60 + gm.START_DEADLINE_S + 5, sessions=[], gsd_status=GSD_OK, runner=host,
                       stop_runner=stop_ok, pid_alive=lambda p: False)
    s10b = gm.load("m-bbb00000000a")
    mine = [a for a in ARGVS if "m-bbb00000000a" in a[a.index("-n") + 1]]  # other fixtures share the state dir
    check("V-AMRX-ANSWER-ON-RETRY", len(mine) == 1 and "RUNTIME ANSWER" in (s10b.get("card") or ""),
          f"retry launches for this mission={len(mine)} (all={len(ARGVS)})")
    new = gm.adopt_launched(s10b, {"sessionId": "succ-0000-1", "id": "9e9e9e9e", "state": "busy"}, now=NOW + 400)
    check("V-AMRX-ANSWER-CLEARED", not gm.load("m-bbb00000000a").get("pending_decision"), "adoption clears it")

    # Environment/topology controls: allowed + healthy keeps the tools; allowed + unhealthy falls back.
    wd_ok = make_repo("allows", True)
    rec_ok = {"cwd": str(wd_ok), "mission_id": "m-x", "epoch": 1}
    real_probe = mp.probe_capabilities
    mp.probe_capabilities = lambda needed, **k: {"git": {"health": "HEALTHY"}, "EnterWorktree": {"health": "HEALTHY"}}
    a_ok = gm.worker_argv(rec_ok, "/gsd-autonomous")
    mp.probe_capabilities = lambda needed, **k: {"git": {"health": "PATH_MISMATCH"}, "EnterWorktree": {"health": "UNHEALTHY"}}
    a_fb = gm.worker_argv(rec_ok, "/gsd-autonomous")
    mp.probe_capabilities = real_probe
    check("V-AMRX-CTRL-WORKTREE-ALLOWED", pair(a_ok, "--allowedTools", "EnterWorktree")
          and not pair(a_ok, "--disallowedTools", "EnterWorktree"), "policy allows + healthy -> unchanged")
    check("V-AMRX-ENV-FALLBACK", not pair(a_fb, "--allowedTools", "EnterWorktree")
          and pair(a_fb, "--disallowedTools", "EnterWorktree"), "unhealthy EnterWorktree -> main-tree fallback")
    i = a_ok.index("--autocompact") if "--autocompact" in a_ok else len(a_ok) - 1
    check("V-AMRX-ARGV-ORDER", all(a_ok.index(f) < i for f in ("--allowedTools", "--disallowedTools")),
          "variadic flags stay before the non-variadic separator")

    # B3 (GEX44 m-26ea4de62c50, 2026-11-14): the worker parked itself with `requires HEAD4 --path
    # inputs/OWNER-DECISION-HEAD4.md`, ended its turn on that question, and the runtime answered it
    # RESOLVE_BY_DEFAULT. The requirement survived the answer, so the sweep parked the successor on a file
    # nobody would write (17:00Z -> 19:50Z). The answer settles the obligation the question named; a sibling
    # obligation on another path is untouched (control).
    # bada2258afa1 (2026-11-16): the incident file was an OWNER-DECISION file; that ask is now Owner-class (checked
    # below, V-AMRX-B3-OWNER-FILE-PARKS). The mechanics are kept on a neutral file the runtime may answer.
    q = ("create inputs/HEAD4-CHOICE.md choosing (a) Pixal3D multi-view head with jaw rig and simple blink "
         "(agent's pick), (b) hand-sculpt face on GNM mesh, or (c) canonical stills only")
    wd_d = make_repo("self-park", None)
    (wd_d / "inputs").mkdir()
    (wd_d / "inputs" / "gpu.lock").write_text("x", encoding="utf-8")   # sibling obligation MET: admissible
    q_own = "write the independent head7 verdict in " + str(wd_d / "inputs" / "OWNER-DECISION-F1B.md")
    r_own = blocked_mission("m-bbb0000000d2", wd_d, needs=q_own)
    p_own = gm.plan_next(r_own, NOW, host_rows("m-bbb0000000d2"), pid_alive=lambda p: False)
    check("V-AMRX-B3-OWNER-FILE-PARKS", p_own["action"] == "surface_blocked" and "OWNER_BOUNDARY" in p_own["reason"],
          f"Owner decision file ask -> {p_own['action']}: {p_own['reason'][:100]}")
    blocked_mission("m-bbb0000000d1", wd_d, needs=q)
    gm.set_requires("m-bbb0000000d1", "HEAD4", [("path_exists", str(wd_d / "inputs" / "HEAD4-CHOICE.md"))])
    gm.set_requires("m-bbb0000000d1", "GPU", [("path_exists", str(wd_d / "inputs" / "gpu.lock"))])
    ARGVS.clear()
    gm._supervise_core(now=NOW + 60, sessions=host_rows("m-bbb0000000d1"), gsd_status=GSD_OK, runner=host,
                       stop_runner=stop_ok, pid_alive=lambda p: False)
    sd = gm.load("m-bbb0000000d1")
    evd = gm.lr.ledger_events("m-bbb0000000d1")
    names = [e.get("event") for e in evd]
    obls = sorted({r.get("obligation") for r in sd.get("requires") or []})
    rec_row = next((e for e in evd if e.get("event") == "decision_recovered" and e.get("gate")), {})
    check("V-AMRX-B3-RECOVERED", "decision_recovered" in names and rec_row.get("gate", "").startswith("RESOLVE_BY"),
          f"gate={rec_row.get('gate')}")
    check("V-AMRX-B3-ANSWER-CLEARS-ITS-REQUIRES", "HEAD4" not in obls and "requires_cleared_by_decision" in names,
          f"obligations left={obls} events={names[-6:]}")
    check("V-AMRX-B3-CTRL-SIBLING-KEPT", "GPU" in obls, f"obligations left={obls}")

    # Spec mission-unattended-continuity A3 (m-144eafe0ff5f 9.1 h, m-e78bdb938339 14 h): an Owner question parks only
    # itself when ROADMAP/STATE show another runnable unit; the successor is told not to touch the Owner's part.
    wd_i = make_repo("indep", None)
    (wd_i / ".planning" / "ROADMAP.md").write_text("- [ ] **Phase 1: Keys**\n- [ ] **Phase 2: Docs**\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(wd_i), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "roadmap"],
                   capture_output=True, text=True, check=True)
    q_key = "provide MIOSA_API_KEY and approve spend"
    r_i = blocked_mission("m-bbb0000000e1", wd_i, needs=q_key)
    p_i = gm.plan_next(r_i, NOW, host_rows("m-bbb0000000e1"), pid_alive=lambda p: False)
    check("V-AMRX-OWNERQ-CONTINUES", p_i["action"] == "replace" and (p_i.get("owner_question") or {}).get(
        "owner_class") == "SECURITY_OR_CREDENTIAL", f"{p_i['action']}: {p_i['reason'][:140]}")
    os.environ["CPP_MISSION_OWNER_PENDING_CONTINUE"] = "off"
    p_o = gm.plan_next(r_i, NOW, host_rows("m-bbb0000000e1"), pid_alive=lambda p: False)
    os.environ.pop("CPP_MISSION_OWNER_PENDING_CONTINUE")
    check("V-AMRX-OWNERQ-KILL-SWITCH", p_o["action"] == "surface_blocked", p_o["action"])
    # The real pass runs before the controls below exist: they would compete for the pass's launch slot.
    ARGVS.clear()
    gm._supervise_core(now=NOW + 60, sessions=host_rows("m-bbb0000000e1"), gsd_status=GSD_OK, runner=host,
                       stop_runner=stop_ok, pid_alive=lambda p: False)
    se = gm.load("m-bbb0000000e1")
    eve = [e.get("event") for e in gm.lr.ledger_events("m-bbb0000000e1")]
    mine_e = [a for a in ARGVS if "m-bbb0000000e1" in a[a.index("-n") + 1]]
    note_e = se.get("note") or ""
    check("V-AMRX-OWNERQ-SUCCESSOR", len(mine_e) == 1 and "owner_question_parked" in eve
          and "Do NOT do it" in note_e and "OWNER DECISION NEEDED" in note_e,
          f"launches={len(mine_e)} parked={'owner_question_parked' in eve} note={len(note_e)}")
    oqs = se.get("owner_questions") or []
    check("V-AMRX-OWNERQ-RECORDED", len(oqs) == 1 and "MIOSA_API_KEY" in oqs[0].get("question", "")
          and ("incident_notified" in eve or "incident_notify_failed" in eve), f"owner_questions={len(oqs)}")
    r_n = blocked_mission("m-bbb0000000e2", wd, needs=q_key)   # wd: one phase only -> no independent unit
    p_n = gm.plan_next(r_n, NOW, host_rows("m-bbb0000000e2"), pid_alive=lambda p: False)
    check("V-AMRX-OWNERQ-NO-EVIDENCE-SURFACES", p_n["action"] == "surface_blocked" and "OWNER_BOUNDARY" in p_n["reason"],
          f"{p_n['action']}: {p_n['reason'][:100]}")
    r_c = blocked_mission("m-bbb0000000e3", wd_i, needs=q_key, recoveries=gm.MAX_DECISION_RECOVERIES, fp="fp-fixture")
    p_c = gm.plan_next(r_c, NOW, host_rows("m-bbb0000000e3"), pid_alive=lambda p: False)
    check("V-AMRX-OWNERQ-CAP", p_c["action"] == "surface_blocked", f"cap spent, tree unchanged: {p_c['action']}")
    # Review M1: with the SAME independent evidence, a stop-class question still stops the whole mission.
    stops = {"AUTHORITY": "budget exhausted: raise the cap?", "GUARD_DISABLE": "should I disable the breaker?",
             "DEPLOY_OR_LIVE_WRITE": "OK to deploy to production?", "IRREVERSIBLE": "force-push the branch?"}
    leaked = {}
    for i, (cls_, qq) in enumerate(stops.items()):
        mid_s = f"m-bbb0000000f{i}"
        p_s = gm.plan_next(blocked_mission(mid_s, wd_i, needs=qq), NOW, host_rows(mid_s), pid_alive=lambda p: False)
        if p_s["action"] != "surface_blocked":
            leaked[cls_] = p_s["action"]
    check("V-AMRX-OWNERQ-STOP-CLASSES-SURFACE", not leaked, f"stop classes that continued: {leaked}")

    print(f"AMRX_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
