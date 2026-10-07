#!/usr/bin/env python3
"""V-GRAMMAR-F1/F2-*, V-GRAMMAR-COMPILE-*, V-WAIT-* gates for spec vault/specs/compiled-grammar-default.md
(WU-G2b: review findings F1/F2 of G1, law 5 `tools/gsd_compile.py`, law 6 `tools/mission_wait.py`).

Hermetic like tools/test_grammar_default.py: state goes to a temp dir BEFORE import, repos are temp git
repos, workers are injected runners. Every refusal is paired with an admitted control.

Mutation drill: GSD_MISSION_DRILL_DIR names a directory holding mutated copies of gsd_mission.py /
gsd_compile.py / mission_wait.py imported instead of the real ones. The last section builds them, re-runs
this file against each, and demands the matching gates go red (and an UNmutated copy stays green).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = tempfile.mkdtemp(prefix="grammar-compile-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
for _k in ("CPP_MISSION_GRAMMAR", "CPP_MISSION_RENEW", "CPP_MISSION_CONTINUATION", "CPP_ROUTE_ADMISSION",
           "CPP_PACKET_GATE_TIMEOUT", "CPP_SOURCE_PACKET_CARD"):
    os.environ.pop(_k, None)

sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402
import gsd_compile as gc  # noqa: E402
import mission_wait as mw  # noqa: E402

NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


class R:
    def __init__(self, out="", rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def runner(rc, calls):
    def run(cmd, cwd):
        calls.append((cmd, cwd))
        return R("gate tail\n", rc)
    return run


def events(mid):
    return [e["event"] for e in lr.ledger_events(mid)]


def git(*args, cwd):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, timeout=60)


def make_repo(path: Path, files: dict[str, str]) -> Path:
    path.mkdir(parents=True)
    git("init", "-q", "-b", "main", cwd=path)
    git("config", "user.email", "t@example.invalid", cwd=path)
    git("config", "user.name", "t", cwd=path)
    for name, text in files.items():
        f = path / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    git("add", "-A", cwd=path)
    git("commit", "-q", "-m", "seed", cwd=path)
    return path


def packet_mission(mid, repo, packet_text, **fields):
    """A mission in `repo` whose packet is registered through the real setter (sha256 recorded)."""
    gm.create(str(repo), "/gsd-autonomous", mission_id=mid, now=NOW)
    p = Path(TMP) / f"{mid}-packet.md"
    p.write_text(packet_text, encoding="utf-8")
    gm.set_envelope(mid, wu_packet=str(p), now=NOW)
    if fields:
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_fields", now=NOW, **fields)
    return p


# --------------------------------------------------------------------------------------------- F1
def gate_f1():
    repo = make_repo(Path(TMP) / "f1repo", {"a.txt": "a\n"})
    honest = "done_gate: python3 tools/test_x.py\n\n# WU\n"
    p = packet_mission("m-f1-drift", repo, honest)
    p.write_text("done_gate: true\n\n# WU\n", encoding="utf-8")   # the worker edits its own gate
    calls: list = []
    res = gm.packet_gate_passed(gm.load("m-f1-drift"), NOW, gate_runner=runner(0, calls))
    drift = [e for e in lr.ledger_events("m-f1-drift") if e["event"] == "packet_gate_drift"]
    check("V-GRAMMAR-F1-EDITED-GATE-NOT-JUDGED",
          res is None and not calls and len(drift) == 1 and "packet_gate_passed" not in events("m-f1-drift"),
          f"res={res} calls={calls}")
    packet_mission("m-f1-ctl", repo, honest)
    calls = []
    res = gm.packet_gate_passed(gm.load("m-f1-ctl"), NOW, gate_runner=runner(0, calls))
    check("V-GRAMMAR-F1-UNEDITED-CONTROL-PASSES",
          bool(res) and calls and calls[0][0] == "python3 tools/test_x.py" and "packet_gate_drift" not in events("m-f1-ctl"),
          str(res))
    packet_mission("m-f1-nosha", repo, honest)
    rec = gm.load("m-f1-nosha")
    rec["wu_packet"] = {k: v for k, v in rec["wu_packet"].items() if k != "sha256"}
    calls = []
    res = gm.packet_gate_passed(rec, NOW, gate_runner=runner(0, calls))
    check("V-GRAMMAR-F1-NO-RECORDED-SHA-NOT-JUDGED",
          res is None and not calls and "packet_gate_drift" in events("m-f1-nosha"), str(res))


# --------------------------------------------------------------------------------------------- F2
def gate_f2():
    repo = make_repo(Path(TMP) / "f2repo", {"a.txt": "a\n"})
    wt = Path(TMP) / "f2-worktree"
    git("worktree", "add", "-q", "-b", "wt-branch", str(wt), cwd=repo)
    other = make_repo(Path(TMP) / "f2-sibling-clone", {"a.txt": "a\n"})
    nested = repo / "sub" / "dir"
    nested.mkdir(parents=True)

    def run_with(mid, tree_line, **fields):
        text = (f"done_gate: python3 g.py\n{tree_line}\n" if tree_line else "done_gate: python3 g.py\n") + "# WU\n"
        packet_mission(mid, repo, text, **fields)
        calls: list = []
        res = gm.packet_gate_passed(gm.load(mid), NOW, gate_runner=runner(0, calls))
        return res, calls

    res, calls = run_with("m-f2-wt", f"work_tree: {wt}")
    check("V-GRAMMAR-F2-WORKTREE-OF-SAME-REPO-ADMITTED",
          bool(res) and calls and calls[0][1] == str(wt.resolve()), str(calls))
    res, calls = run_with("m-f2-inside", f"work_tree: {nested}")
    check("V-GRAMMAR-F2-DIR-UNDER-CWD-ADMITTED", bool(res) and calls and calls[0][1] == str(nested.resolve()), str(calls))
    res, calls = run_with("m-f2-sibling", f"work_tree: {other}")
    check("V-GRAMMAR-F2-SIBLING-CLONE-OF-OTHER-REPO-REFUSED",
          res is None and not calls and "packet_gate_unanswered" in events("m-f2-sibling"), str(calls))
    here = os.getcwd()
    os.chdir(TMP)
    try:
        res, calls = run_with("m-f2-rel", "work_tree: f2repo")   # a real directory relative to the cwd
    finally:
        os.chdir(here)
    check("V-GRAMMAR-F2-RELATIVE-PATH-REFUSED",
          res is None and not calls and "packet_gate_unanswered" in events("m-f2-rel"), str(calls))
    res, calls = run_with("m-f2-missing", f"work_tree: {repo}/no/such/dir")
    check("V-GRAMMAR-F2-MISSING-DIR-REFUSED",
          res is None and not calls and "packet_gate_unanswered" in events("m-f2-missing"), str(calls))
    outside = Path(TMP) / "f2-plain-dir"
    outside.mkdir()
    res, calls = run_with("m-f2-nogit", f"work_tree: {outside}")
    check("V-GRAMMAR-F2-NON-REPO-DIR-REFUSED", res is None and not calls, str(calls))

    # no work_tree line: the owner's tree, else work_dir, else cwd.
    real_ewd = gm.effective_workdir
    try:
        gm.effective_workdir = lambda sid, base, ws=None: str(wt)
        res, calls = run_with("m-f2-owner", None, owner={"session_id": "s-f2-owner", "pid": 1, "kind": "background",
                                                          "heartbeat_at": NOW, "epoch": 1})
        check("V-GRAMMAR-F2-NO-LINE-USES-OWNER-WORKER-TREE", bool(res) and calls[0][1] == str(wt), str(calls))
        gm.effective_workdir = lambda sid, base, ws=None: None
        res, calls = run_with("m-f2-workdir", None, work_dir=str(nested), owner={"session_id": "s-f2-wd", "pid": 1,
                              "kind": "background", "heartbeat_at": NOW, "epoch": 1})
        check("V-GRAMMAR-F2-NO-LINE-FALLS-BACK-TO-WORK-DIR", bool(res) and calls[0][1] == str(nested), str(calls))
    finally:
        gm.effective_workdir = real_ewd
    res, calls = run_with("m-f2-cwd", None)
    check("V-GRAMMAR-F2-NO-LINE-NO-OWNER-USES-CWD", bool(res) and calls[0][1] == gm.load("m-f2-cwd")["cwd"], str(calls))


# ---------------------------------------------------------------------------------- law 5 compile
ROADMAP = """# Roadmap fx

## Phases

- [ ] **Phase 1: Wire the thing** - make it
- [x] **Phase 2: Already done** - done
- [ ] **Phase 3: No gate here** - no gate line

## Phase Details

### Phase 1: Wire the thing
**Goal**: The widget owns frobnication and `mods/` is wired.
**Requirements**: REQ-1, REQ-2
**Success Criteria**:
  1. `widget.frob()` returns the frobnication ledger.
     It refuses an empty ledger.
  2. The gizmo registry lists every widget.
**Gate**: `python3 tools/test_widget.py`

### Phase 2: Already done
**Goal**: Done.
**Success Criteria**:
  1. It is done.

### Phase 3: No gate here
**Goal**: Nothing deterministic.
**Success Criteria**:
  1. Somebody looks at it.
"""


def gate_compile():
    repo = make_repo(Path(TMP) / "crepo", {
        ".planning/workstreams/fx/ROADMAP.md": ROADMAP,
        "mods/widget.py": '"""Widget owns frobnication."""\n\ndef frob():\n    return []\n',
        "mods/gizmo.py": "import widget\n\ndef registry():\n    return widget.frob()\n"})
    before = len(gm.all_missions())
    out = gc.compile_phase(str(repo), "fx", 1, dry_run=True)
    pdir = repo / ".planning" / "workstreams" / "fx" / "packets" / "phase-1"
    check("V-GRAMMAR-COMPILE-DRY-RUN-WRITES-AND-ARMS-NOTHING",
          out["dry_run"] and not pdir.exists() and out["mission"] is None and len(gm.all_missions()) == before, str(out["packet"]))
    check("V-GRAMMAR-COMPILE-GATE-FROM-PHASE-LINE", out["gate"] == "python3 tools/test_widget.py", out["gate"])
    out2 = gc.compile_phase(str(repo), "fx", 1, gate="python3 tools/other.py", dry_run=True)
    check("V-GRAMMAR-COMPILE-GATE-FLAG-WINS", out2["gate"] == "python3 tools/other.py", out2["gate"])

    def refused(**kw):
        try:
            gc.compile_phase(str(repo), "fx", kw.pop("phase"), dry_run=kw.pop("dry_run", True), **kw)
        except gc.CompileError as exc:
            return str(exc)
        return None

    why = refused(phase=3)
    check("V-GRAMMAR-COMPILE-NO-GATE-REFUSED", why is not None and "no gate" in why
          and not (repo / ".planning/workstreams/fx/packets/phase-3").exists(), str(why))
    check("V-GRAMMAR-COMPILE-NO-GATE-ADMITTED-WITH-FLAG", refused(phase=3, gate="python3 x.py") is None)
    why = refused(phase=2, gate="python3 x.py")
    check("V-GRAMMAR-COMPILE-DONE-PHASE-REFUSED", why is not None and "already complete" in why, str(why))
    why = refused(phase=9, gate="python3 x.py")
    check("V-GRAMMAR-COMPILE-ABSENT-PHASE-REFUSED", why is not None and "not in the roadmap" in why, str(why))

    res = gc.compile_phase(str(repo), "fx", 1)
    missions_after_compile = len(gm.all_missions())
    packet = Path(res["packet"])
    text = packet.read_text(encoding="utf-8")
    lines = text.splitlines()
    check("V-GRAMMAR-COMPILE-PACKET-HEADER-LINES",
          lines[0] == "done_gate: python3 tools/test_widget.py" and lines[1] == f"work_tree: {res['work_tree']}"
          and res["work_tree"].endswith("/.claude/worktrees/wu-fx-p1"), "\n".join(lines[:2]))
    check("V-GRAMMAR-COMPILE-PACKET-CRITERIA-VERBATIM",
          "  1. `widget.frob()` returns the frobnication ledger.\n     It refuses an empty ledger." in text
          and "2. The gizmo registry lists every widget." in text and "REQ-1, REQ-2" in text)
    check("V-GRAMMAR-COMPILE-PACKET-WORKTREE-RULE",
          "EnterWorktree with name `wu-fx-p1`" in text and "do not enter" not in text.lower().replace("do not run", "")
          and "never" in text.lower(), "")
    check("V-GRAMMAR-COMPILE-DOSSIER-RAN",
          (pdir / "dossier.md").is_file() and (pdir / "refs.jsonl").is_file()
          and res["dossier"]["concepts"] == 2 and res["dossier"]["modules"] >= 2
          and "mods/widget.py" in (pdir / "dossier.md").read_text(encoding="utf-8")
          and res["module_roots"] == ["mods"], str(res.get("dossier")))
    b = res["budget"]
    import route_admission as ra
    floor = ra.load_floors()["profiles"]["top-level-worker"]["floor"]
    packet_tokens = -(-packet.stat().st_size // 4)
    need = ra._with_margin(gc.DEFAULT_CALLS * (floor + packet_tokens), ra.DEFAULT_GROWTH_MARGIN)
    check("V-GRAMMAR-COMPILE-BUDGET-FROM-FLOOR",
          b["floor"] == floor and b["need_with_margin"] == need and b["token_estimate"] >= need
          and b["token_estimate"] - need < gc.ESTIMATE_STEP, f"{b} expected need {need}")
    check("V-GRAMMAR-COMPILE-WINDOW-FROM-FLOOR",
          b["autocompact"] >= floor + packet_tokens + gm.GRAMMAR_WINDOW_MARGIN and b["autocompact"] % 10_000 == 0
          and b["autocompact"] - (floor + packet_tokens + gm.GRAMMAR_WINDOW_MARGIN) < 10_000, str(b))
    check("V-GRAMMAR-COMPILE-NOTHING-ARMED-WITHOUT-FLAG", missions_after_compile == before and res["mission"] is None)

    # the real roadmaps of this repo: the first workstream with an open phase compiles (dry-run only).
    import re as _re
    real_roads = sorted((HERE.parent / ".planning" / "workstreams").glob("*/ROADMAP.md"))
    target = None
    for road in real_roads:
        m = _re.search(r"^- \[ \] \*\*Phase (\d+):", road.read_text(encoding="utf-8-sig"), _re.MULTILINE)
        if m:
            target = (road, int(m.group(1)))
            break
    if target:
        # compiled against a COPY of the real roadmap, so a mutated dry-run cannot write into this repo
        ws = target[0].parent.name
        copy = make_repo(Path(TMP) / "real-copy", {f".planning/workstreams/{ws}/ROADMAP.md":
                                                  target[0].read_text(encoding="utf-8-sig")})
        try:
            def snap():
                return sorted((str(f), f.stat().st_mtime_ns) for f in copy.rglob("*") if f.is_file() and ".git" not in f.parts)
            before_files = snap()
            rr = gc.compile_phase(str(copy), ws, target[1], gate="python3 tools/test_x.py", dry_run=True)
            ok = rr["dry_run"] and rr["budget"]["token_estimate"] > 0 and snap() == before_files
            ev = f"{ws} phase {target[1]} {rr['title']}"
        except gc.CompileError as exc:
            ok, ev = False, f"{ws} phase {target[1]}: {exc}"
        check("V-GRAMMAR-COMPILE-REAL-ROADMAP-DRY-RUN", ok, ev)
    else:
        check("V-GRAMMAR-COMPILE-REAL-ROADMAP-DRY-RUN", True, "no workstream has an open phase: nothing to compile")

    # --arm: arm(no launch) -> hold -> envelope -> admission -> release, in that ledger order.
    try:
        armed = gc.compile_phase(str(repo), "fx", 1, arm=True)
        mid, err = armed["mission"], ""
    except Exception as exc:  # noqa: BLE001 -- a failing arm must fail named gates, not abort the file
        armed, mid, err = {"packet": ""}, "m-arm-failed", f"{type(exc).__name__}: {exc}"
    rec = gm.load(mid) or {"state": None, "epoch": None, "wu_packet": {}}
    ev = events(mid) + ([err] if err else [])
    order = [ev.index(x) for x in ("owner_hold_set", "envelope_set", "route_admission", "owner_hold_released")
             if x in ev]
    check("V-GRAMMAR-COMPILE-ARM-SEQUENCE",
          len(order) == 4 and order == sorted(order) and rec["state"] == gm.PREPARED and rec["epoch"] == 0
          and not rec.get("owner_hold"), str(ev))
    check("V-GRAMMAR-COMPILE-ARM-ENVELOPE",
          rec["token_estimate"] == b["token_estimate"] and rec["model"] == "sonnet"
          and rec["autocompact"] == f"{b['autocompact'] // 1000}k" and rec["wu_packet"]["path"] == armed["packet"]
          and rec["wu_packet"]["sha256"] == gm._packet_digest(armed["packet"])
          and (rec.get("admission") or {}).get("verdict") == "ADMISSIBLE" and rec.get("workstream") == "fx",
          str({k: rec.get(k) for k in ("token_estimate", "model", "autocompact", "admission")}))
    launched: list = []

    def fake_launch(argv, cwd):
        launched.append(argv)
        return R(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")
    try:
        res_l = gm.launch_worker(mid, expect_epoch=0, expect_state=gm.PREPARED, reason="t", runner=fake_launch, now=NOW)
    except gm.MissionError as exc:
        res_l = {"ok": False, "why": str(exc)}
    check("V-GRAMMAR-COMPILE-ARMED-MISSION-LAUNCHES-NO-MANUAL-STEP", bool(res_l.get("ok")) and len(launched) == 1, str(res_l))

    # a refusal anywhere leaves the record HELD, never launchable half-set.
    bad = gc.compile_phase(str(repo), "fx", 1, calls=400)   # 400 calls cannot fit any single window -> admission says no
    check("V-GRAMMAR-COMPILE-CLI-REFUSES-WITH-EXIT-2",
          subprocess.run([sys.executable, "-I", str(HERE / "gsd_compile.py"), "compile", "--repo", str(repo),
                          "--workstream", "fx", "--phase", "3", "--dry-run"],
                         capture_output=True, text=True, timeout=60).returncode == 2 and bool(bad), "")


# ---------------------------------------------------------------------------------- law 6 wait
class Clock:
    def __init__(self):
        self.t, self.sleeps = 1000.0, 0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s
        self.sleeps += 1
        if self.sleeps > 60:
            raise RuntimeError("wait did not return")


def gate_wait():
    repo = make_repo(Path(TMP) / "wrepo", {"a.txt": "a\n"})
    spend = lambda rec: 4_242  # noqa: E731

    def mission(mid, state=gm.RUNNING, **f):
        gm.create(str(repo), "/gsd-autonomous", mission_id=mid, now=NOW)
        gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="seed", now=NOW, state=state,
                      epoch=1, owner={"session_id": f"{mid}-sid", "pid": 4242, "kind": "background",
                                      "heartbeat_at": NOW, "epoch": 1}, token_estimate=1_000_000, **f)

    def wait(mid, *, clk=None, **kw):
        clk = clk or Clock()
        try:
            res = mw.wait(mid, timeout=kw.pop("timeout", 100), poll=20, sleep=clk.sleep, clock=clk.now,
                          measure=spend, **kw)
        except RuntimeError as exc:   # the Clock's cap: a wait with no deadline must fail a gate, not hang
            res = {"reason": f"DID_NOT_RETURN: {exc}", "state": None, "processed_tokens": None,
                   "guarded_renewals": [], "gate": None}
        return res, clk

    for state in (gm.COMPLETED, gm.HALTED, gm.BLOCKED):
        mid = f"m-w-{state.lower()}"
        mission(mid)
        if state == gm.BLOCKED:
            gm.transition(mid, expect_epoch=1, expect_state=gm.RUNNING, event="t", now=NOW, state=gm.BLOCKED)
        else:
            gm.transition(mid, expect_epoch=1, expect_state=gm.RUNNING, event="t", now=NOW, state=state)
        res, clk = wait(mid, pid_alive=lambda p: True)
        check(f"V-WAIT-EXITS-ON-{state}", res["reason"] == state and clk.sleeps == 0
              and res["processed_tokens"] == 4242 and res["state"] == state, str(res["reason"]))
    mission("m-w-hold")
    gm.set_owner_hold("m-w-hold", "breaker")
    res, _ = wait("m-w-hold", pid_alive=lambda p: True)
    check("V-WAIT-EXITS-ON-OWNER-HOLD", res["reason"] == "OWNER_HOLD", res["reason"])

    gated = "done_gate: python3 g.py\nwork_tree: " + str(repo) + "\n# WU\n"
    packet_mission("m-w-gone", repo, gated)
    gm.transition("m-w-gone", expect_epoch=0, expect_state=gm.PREPARED, event="seed", now=NOW, state=gm.RUNNING,
                  epoch=1, owner={"session_id": "w-gone", "pid": 4243, "kind": "background", "heartbeat_at": NOW, "epoch": 1})
    calls: list = []
    res, _ = wait("m-w-gone", pid_alive=lambda p: False, gate_runner=runner(0, calls))
    check("V-WAIT-WORKER-GONE-GATE-PASSING-EXITS", res["reason"] == "WORKER_GONE_GATE_PASSED" and res["gate"]
          and calls, str(res["reason"]))
    packet_mission("m-w-gone-fail", repo, gated)
    gm.transition("m-w-gone-fail", expect_epoch=0, expect_state=gm.PREPARED, event="seed", now=NOW, state=gm.RUNNING,
                  epoch=1, owner={"session_id": "w-gone2", "pid": 4244, "kind": "background", "heartbeat_at": NOW, "epoch": 1})
    res, clk = wait("m-w-gone-fail", pid_alive=lambda p: False, gate_runner=runner(1, []), timeout=60)
    check("V-WAIT-WORKER-GONE-GATE-FAILING-KEEPS-WAITING", res["reason"] == "TIMEOUT" and clk.sleeps >= 3, str(res["reason"]))
    mission("m-w-alive")
    res, clk = wait("m-w-alive", pid_alive=lambda p: True, gate_runner=runner(0, []), timeout=60)
    check("V-WAIT-LIVE-WORKER-TIMES-OUT-AT-THE-DEADLINE",
          res["reason"] == "TIMEOUT" and clk.sleeps == 3 and res["state"] == gm.RUNNING, f"{res['reason']} {clk.sleeps}")

    # guard-renewals: a record renewed_from M is held and its worker stopped; M's own record and a stranger are not.
    mission("m-g-parent")
    mission("m-g-child", renewed_from="m-g-parent")
    mission("m-g-stranger")
    stops: list = []
    gm.transition("m-g-parent", expect_epoch=1, expect_state=gm.RUNNING, event="t", now=NOW, state=gm.COMPLETED)
    res, _ = wait("m-g-parent", guard=True, stop_runner=lambda a: stops.append(a) or R())
    child, stranger = gm.load("m-g-child"), gm.load("m-g-stranger")
    check("V-WAIT-GUARD-HOLDS-AND-STOPS-THE-RENEWAL",
          res["guarded_renewals"] == ["m-g-child"] and child.get("owner_hold")
          and stops == [[os.environ.get("CPP_CLAUDE_EXE") or "claude", "stop", "m-g-child-sid"]]
          and "renewal_guarded" in events("m-g-child"), str(res["guarded_renewals"]))
    check("V-WAIT-GUARD-LEAVES-STRANGERS-ALONE", not stranger.get("owner_hold") and res["reason"] == "COMPLETED")
    mission("m-n-parent")
    mission("m-n-child", renewed_from="m-n-parent")
    gm.transition("m-n-parent", expect_epoch=1, expect_state=gm.RUNNING, event="t", now=NOW, state=gm.COMPLETED)
    wait("m-n-parent", guard=False, stop_runner=lambda a: stops.append(a) or R())
    check("V-WAIT-WITHOUT-FLAG-NOTHING-IS-GUARDED", not gm.load("m-n-child").get("owner_hold"))

    out = Path(TMP) / "wait-result.json"
    mission("m-w-cli")
    gm.transition("m-w-cli", expect_epoch=1, expect_state=gm.RUNNING, event="t", now=NOW, state=gm.COMPLETED)
    p = subprocess.run([sys.executable, "-I", str(HERE / "mission_wait.py"), "--mission", "m-w-cli", "--poll", "1",
                        "--timeout", "30", "--out", str(out)], capture_output=True, text=True, timeout=90,
                       env={**os.environ})
    data = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    check("V-WAIT-DETACHABLE-WRITES-RESULT-JSON",
          p.returncode == 0 and data.get("reason") == "COMPLETED" and data.get("mission") == "m-w-cli",
          p.stdout[-200:] + p.stderr[-200:])


# ----------------------------------------------------------------------------------------- mutations
def mutation_drill():
    if os.environ.get("GSD_MISSION_DRILL_DIR"):
        return

    def run_drilled(files):
        d = tempfile.mkdtemp(prefix="grammar-compile-drill-")
        for name, text in files.items():
            (Path(d) / name).write_text(text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(Path(__file__).resolve())], capture_output=True, text=True,
                           env={**os.environ, "GSD_MISSION_DRILL_DIR": d}, timeout=900)
        return r.returncode, sorted({ln.split()[1] for ln in r.stdout.splitlines() if ln.startswith("FAIL ")})

    names = ("gsd_mission.py", "gsd_compile.py", "mission_wait.py")
    src = {n: (HERE / n).read_text(encoding="utf-8") for n in names}

    def mutated(name, old, new):
        assert src[name].count(old) == 1, f"mutation anchor not unique in {name}: {old[:70]!r}"
        return {name: src[name].replace(old, new, 1)}

    rc, red = run_drilled({n: src[n] for n in names})
    check("V-GRAMMAR-COMPILE-MUTATION-CONTROL-UNMUTATED-COPY-GREEN", rc == 0 and not red, f"rc={rc} red={red}")
    G = "gsd_mission.py"
    C = "gsd_compile.py"
    W = "mission_wait.py"
    drills = {
        "F1-NO-DRIFT-CHECK": (mutated(G, 'if not pkt.get("sha256") or now_sha != pkt["sha256"]:', "if False:"),
                              {"V-GRAMMAR-F1-EDITED-GATE-NOT-JUDGED", "V-GRAMMAR-F1-NO-RECORDED-SHA-NOT-JUDGED"}),
        "F1-ABSENT-SHA-ACCEPTED": (mutated(G, 'if not pkt.get("sha256") or now_sha != pkt["sha256"]:',
                                           'if pkt.get("sha256") and now_sha != pkt["sha256"]:'),
                                   {"V-GRAMMAR-F1-NO-RECORDED-SHA-NOT-JUDGED"}),
        "F2-WORK-TREE-LINE-IGNORED": (mutated(G, "    m = _TREE_RE.search(text or \"\")\n    if m:", "    m = None\n    if m:"),
                                      {"V-GRAMMAR-F2-WORKTREE-OF-SAME-REPO-ADMITTED"}),
        "F2-NO-SAME-REPO-CHECK": (mutated(G, "return str(p) if here and root and here[1] == root[1] else None",
                                          "return str(p)"),
                                  {"V-GRAMMAR-F2-SIBLING-CLONE-OF-OTHER-REPO-REFUSED",
                                   "V-GRAMMAR-F2-NON-REPO-DIR-REFUSED"}),
        "F2-NO-ABSOLUTE-CHECK": (mutated(G, "if not p.is_absolute() or not p.is_dir():", "if not p.is_dir():"),
                                 {"V-GRAMMAR-F2-RELATIVE-PATH-REFUSED"}),
        "F2-OWNER-TREE-IGNORED": (mutated(G, "wd = effective_workdir(rec[\"owner\"][\"session_id\"], rec[\"cwd\"], rec.get(\"workstream\")) or wd",
                                          "wd = wd"),
                                  {"V-GRAMMAR-F2-NO-LINE-USES-OWNER-WORKER-TREE"}),
        "L5-NO-GATE-REFUSAL": (mutated(C, '    if not chosen:\n        raise CompileError("no gate: give', '    if False:\n        raise CompileError("no gate: give'),
                               {"V-GRAMMAR-COMPILE-NO-GATE-REFUSED"}),
        "L5-DONE-PHASE-ACCEPTED": (mutated(C, "    if done:\n        raise", "    if False:\n        raise"),
                                   {"V-GRAMMAR-COMPILE-DONE-PHASE-REFUSED"}),
        "L5-DRY-RUN-WRITES": (mutated(C, "    if dry_run:\n        return result\n", "    if False:\n        return result\n"),
                              {"V-GRAMMAR-COMPILE-DRY-RUN-WRITES-AND-ARMS-NOTHING"}),
        "L5-DOSSIER-NOT-RUN": (mutated(C, '    result["dossier"] = gd.build(_dossier_args(dargs))\n',
                                       '    result["dossier"] = {"concepts": 0, "modules": 0}\n'),
                               {"V-GRAMMAR-COMPILE-DOSSIER-RAN"}),
        "L5-BUDGET-NOT-FROM-FLOOR": (mutated(C, 'estimate = -(-need["need_with_margin"] // ESTIMATE_STEP) * ESTIMATE_STEP',
                                             "estimate = 100_000_000"),
                                     {"V-GRAMMAR-COMPILE-BUDGET-FROM-FLOOR"}),
        "L5-WINDOW-NOT-FROM-FLOOR": (mutated(C, "window = -(-need_window // WINDOW_STEP) * WINDOW_STEP", "window = floor"),
                                     {"V-GRAMMAR-COMPILE-WINDOW-FROM-FLOOR"}),
        "L5-ARM-WITHOUT-HOLD": (mutated(C, '    gm.set_owner_hold(mid, "gsd_compile: envelope is being set")\n', ""),
                                {"V-GRAMMAR-COMPILE-ARM-SEQUENCE"}),
        "L5-ARM-WITHOUT-ADMISSION": (mutated(C, '    verdict = gm.admit_route(mid, route, floors_path=floors_path)["admission"]["verdict"]\n',
                                             '    verdict = "ADMISSIBLE"\n'),
                                     {"V-GRAMMAR-COMPILE-ARM-SEQUENCE", "V-GRAMMAR-COMPILE-ARMED-MISSION-LAUNCHES-NO-MANUAL-STEP"}),
        "L6-GATE-NOT-JUDGED-WHEN-WORKER-GONE": (mutated(W, "        gate = gm.packet_gate_passed(rec, now, gate_runner=gate_runner)\n",
                                                         "        gate = {\"gate\": \"unjudged\"}\n"),
                                                {"V-WAIT-WORKER-GONE-GATE-FAILING-KEEPS-WAITING"}),
        "L6-GUARD-FINDS-NO-RENEWALS": (mutated(W, 'if rec.get("renewed_from") in parents', "if False"),
                                       {"V-WAIT-GUARD-HOLDS-AND-STOPS-THE-RENEWAL"}),
        "L6-NO-DEADLINE": (mutated(W, "if clock() >= deadline:", "if False:"),
                           {"V-WAIT-LIVE-WORKER-TIMES-OUT-AT-THE-DEADLINE", "V-WAIT-WORKER-GONE-GATE-FAILING-KEEPS-WAITING"}),
        "L6-TERMINAL-NOT-DETECTED": (mutated(W, "if rec[\"state\"] in (gm.COMPLETED, gm.HALTED):", "if False:"),
                                     {"V-WAIT-EXITS-ON-COMPLETED", "V-WAIT-EXITS-ON-HALTED"}),
        "L6-SPEND-NOT-MEASURED": (mutated(W, "spent = (measure or ms.processed_tokens)(rec) if rec else None", "spent = 0"),
                                  {"V-WAIT-EXITS-ON-COMPLETED"}),
    }
    for name, (files, expected) in drills.items():
        rc, red = run_drilled({**{n: src[n] for n in names if n not in files}, **files})
        check(f"V-GRAMMAR-COMPILE-MUTATION-{name}-GOES-RED", rc != 0 and expected <= set(red),
              f"rc={rc} missing={sorted(expected - set(red))}")


def main() -> int:
    gate_f1()
    gate_f2()
    gate_compile()
    gate_wait()
    mutation_drill()
    print(f"GRAMMAR_COMPILE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
