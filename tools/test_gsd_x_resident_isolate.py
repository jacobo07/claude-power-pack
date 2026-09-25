#!/usr/bin/env python3
"""V-ISO gates: the resident's ISOLATED stage (vault/specs/gdd-resident-driver.md,
"ISOLATED stage").

A work epoch runs in its own worktree on `resident/<mission-id>`, the provider's
cwd is that worktree only, and at harvest every changed path -- committed or
not -- is judged against the goal's declared write set before anything is
ingested. The goal root's HEAD is hashed before and after EVERY scenario: the
resident never merges, pushes or rewrites it.

Providers are fakes implementing the engine's provider contract; the work fake
writes and commits in whatever cwd it is handed, so a resident that handed it
the goal root would show up as a moved main branch. No real codex / claude.

    python tools/test_gsd_x_resident_isolate.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import authority as au      # noqa: E402
from modules.gsd_x.goal import contract as gc       # noqa: E402
from modules.gsd_x.goal import convergence as cv    # noqa: E402
from modules.gsd_x.goal import epoch as ep          # noqa: E402
from modules.gsd_x.goal import git_state as gs      # noqa: E402
from modules.gsd_x.goal import log as gl            # noqa: E402
from modules.gsd_x.goal import sweep as sw          # noqa: E402
from modules.gsd_x.goal.resident import (control, cycle, isolate as iso,   # noqa: E402
                                         missions as ms, procs, store)

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PYTHONIOENCODING": "utf-8"}
REPO_ID = "15" * 20
AUTH_ENV = (au.ENV_ANCHOR, au.ENV_FOUNDER_KEY, au.ENV_JUDGE_KEY)
for _k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
    os.environ[_k] = ENV[_k]        # the resident's own git calls commit nothing, but be explicit


def git(repo: Path, *args: str) -> str:
    p = subprocess.run([GIT, "-C", str(repo), *args], check=True, env=ENV, capture_output=True,
                       text=True, stdin=subprocess.DEVNULL, timeout=60)
    return p.stdout.strip()


def git_rc(repo: Path, *args: str) -> int:
    return subprocess.run([GIT, "-C", str(repo), *args], env=ENV, capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=60).returncode


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_iso_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "src").mkdir()
    (d / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (d / "gate.py").write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    git(d, "add", ".")
    git(d, "commit", "-qm", "seed")
    return d


def main_state(repo: Path) -> tuple:
    """What 'the goal's main branch is untouched' means, measured."""
    return (git(repo, "rev-parse", "HEAD"), git(repo, "symbolic-ref", "HEAD"),
            git(repo, "status", "--porcelain", "--untracked-files=all"))


def make_goal(base: Path, gid: str, repo: Path, paths) -> gl.GoalLog:
    lg = gl.GoalLog(REPO_ID, gid, base=base)
    gc.declare(lg, f"isolate {gid}", ["the gate passes"], [], {"paths": paths})
    for plane in cv.PLANES:
        s = gc.project(lg)
        cv.set_plane(lg, s, plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed", "t")
    cv.accept_obligation(lg, gc.project(lg), "ob-outcome", cv.OUTCOME, "make the gate pass",
                         f'"{sys.executable}" gate.py', gs.file_pin(repo, ["gate.py"]), "t")
    sw.set_autonomous(lg, gc.project(lg), True, "test", "owner")
    return lg


def green_record() -> None:
    payload = {"head": gs.head(ROOT), "green": True,
               "suites": {s: {"ok": True} for s in sw.REQUIRED_SUITES}}
    rec = sw.record_path()
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps(payload), encoding="utf-8")


class FailingGate:
    """A gate epoch whose gate ran and failed: the engine's cue for WORK."""
    name = "gate"
    wall_bound_s = 60.0

    def __init__(self):
        self.started, self.dispatched = set(), []

    def dispatch(self, spec):
        self.started.add(spec["identity"]["run_token"])
        self.dispatched.append(spec["epoch_id"])
        return {"pid": None, "pgid": None, "token": spec["identity"]["run_token"],
                "root": spec["root"], "head_before": gs.head(Path(spec["root"]))}

    def observe(self, handle):
        return ep.Observation(ep.OBS_ENDED, ep.FAILED, "fake: gate exit 1")

    def harvest(self, handle, spec):
        root = Path(spec["root"])
        return ep.Receipt(spec["epoch_id"], self.name, spec["revision"],
                          head_before=handle.get("head_before", ""), head_after=gs.head(root),
                          failures=[{"summary": "gate exit 1", "signature": "gate-exit:1"}],
                          narrative="fake gate")

    def cancel(self, handle):
        pass

    def probe(self, identity):
        tok = identity.get("run_token", "")
        return {"pid": None, "token": tok} if tok in self.started else None


class FakeWork:
    """A work provider (named codex). It does its 'work' in the cwd it is
    handed -- `spec["root"]` -- exactly as the real providers' Popen(cwd=root)."""
    wall_bound_s = 60.0

    def __init__(self, action, name="codex"):
        self.name = name
        self.action = action
        self.specs: list = []
        self.started: set = set()

    def dispatch(self, spec):
        cwd = Path(spec["root"])
        self.specs.append(dict(spec))
        self.started.add(spec["identity"]["run_token"])
        before = gs.head(cwd)
        self.action(cwd)
        return {"pid": None, "pgid": None, "token": spec["identity"]["run_token"],
                "root": str(cwd), "epoch_id": spec["epoch_id"], "head_before": before}

    def observe(self, handle):
        return ep.Observation(ep.OBS_ENDED, ep.COMPLETED, "fake: exit 0")

    def harvest(self, handle, spec):
        root = Path(handle["root"])
        after = gs.head(root)
        return ep.Receipt(spec["epoch_id"], self.name, spec["revision"],
                          head_before=handle["head_before"], head_after=after,
                          commits=gs.commits_between(root, handle["head_before"], after),
                          narrative="fake work")

    def cancel(self, handle):
        pass

    def probe(self, identity):
        tok = identity.get("run_token", "")
        return {"pid": None, "token": tok, "root": ""} if tok in self.started else None


class FakeInfo(procs.ProcInfo):
    def available(self):
        return True

    def exists(self, pid):
        return pid is not None and int(pid) == os.getpid()

    def start_time(self, pid):
        return 1 if pid is not None and int(pid) == os.getpid() else None

    def pgid_members(self, pgid):
        return None if pgid is None else []


# --- work actions --------------------------------------------------------------------

def commit_all(wt: Path, msg: str) -> None:
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", msg)


def act_in_scope(wt):
    (wt / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    commit_all(wt, "in scope")


def act_out_committed(wt):
    (wt / "src" / "app.py").write_text("x = 3\n", encoding="utf-8")
    (wt / "README.md").write_text("outside\n", encoding="utf-8")
    commit_all(wt, "out of scope, committed")


def act_out_uncommitted(wt):
    (wt / "src" / "app.py").write_text("x = 4\n", encoding="utf-8")
    commit_all(wt, "in scope")
    (wt / "notes.txt").write_text("left behind, outside the write set\n", encoding="utf-8")


def act_in_uncommitted(wt):
    (wt / "src" / "draft.py").write_text("y = 1\n", encoding="utf-8")   # in scope, never committed


def act_left_branch(wt):
    git(wt, "checkout", "-q", "-b", "elsewhere")
    (wt / "src" / "app.py").write_text("x = 5\n", encoding="utf-8")
    commit_all(wt, "on another branch")


def act_move_main(wt):
    (wt / "src" / "app.py").write_text("x = 6\n", encoding="utf-8")
    commit_all(wt, "in scope, then pushed into main")
    main_ref = git(wt, "config", "--get", "resident.test.mainref")
    git(wt, "update-ref", main_ref, "HEAD")      # worktrees share refs


# --- harness -------------------------------------------------------------------------

def new_state() -> Path:
    return Path(tempfile.mkdtemp(prefix="gsdx_iso_state_"))


def build(goals_root, gid, action, paths=("src",), state=None, fault=None, work_name="codex",
          gain_window_s=6 * 3600.0):
    repo = make_repo()
    lg = make_goal(goals_root, gid, repo, list(paths))
    gate, work = FailingGate(), FakeWork(action, work_name)
    st = state or new_state()
    r = cycle.Resident(ROOT, {"gate": gate, work_name: work}, goals=[(lg, repo)], state_dir=st,
                       config=cycle.Config(cancel_grace_s=0.0, gain_window_s=gain_window_s),
                       info=FakeInfo(), fault=fault)
    r.start()
    return repo, lg, gate, work, r, st


def work_missions(r):
    return [m for m in r.missions.all() if m.get("provider") in cycle.WORK_PROVIDERS]


def drive(r, cycles=5):
    reps = []
    for _ in range(cycles):
        reps.append(r.once())
        wm = work_missions(r)
        if wm and all(m["state"] in ms.TERMINAL for m in wm):
            break
    return reps


def receipts_for(lg, epoch_id):
    return ep.project_epochs(gc.project(lg))[epoch_id].receipts


def branch_exists(repo, branch):
    return git_rc(repo, "rev-parse", "--verify", "-q", f"refs/heads/{branch}") == 0


def main() -> int:
    passes, fails = [], []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    for k in AUTH_ENV:
        os.environ.pop(k, None)
    goals_root = Path(tempfile.mkdtemp(prefix="gsdx_iso_goals_")) / "goals"
    goals_root.mkdir(parents=True)
    os.environ["GSDX_GOALS_ROOT"] = str(goals_root)
    green_record()

    # --- unit: the write set -----------------------------------------------------------
    repo0 = make_repo()
    r_ok, _ = iso.validate_write_set(repo0, ["src"])
    check("V-ISO-WRITESET-CONTROL", r_ok == "", "control: ['src'] is admissible", r_ok)
    cases = {"empty": ([], iso.EMPTY_WRITE_SET), "blank": ([""], iso.EMPTY_WRITE_SET),
             "dotdot": (["../elsewhere"], iso.WRITE_SET_ESCAPES_REPO),
             "abs": ([str(Path(tempfile.gettempdir()))], iso.WRITE_SET_ESCAPES_REPO),
             "dotgit": ([".git/hooks"], iso.WRITE_SET_ESCAPES_REPO),
             "inner-dotdot": (["src/../../x"], iso.WRITE_SET_ESCAPES_REPO)}
    got = {n: iso.validate_write_set(repo0, p)[0] for n, (p, _) in cases.items()}
    check("V-ISO-WRITESET-REFUSALS", all(got[n] == want for n, (_, want) in cases.items()),
          f"empty/blank -> EMPTY_WRITE_SET, ../abs/.git/inner .. -> ESCAPES ({got})", f"{got}")
    check("V-ISO-IN-WRITE-SET",
          iso.in_write_set("src/a.py", ["src"]) and not iso.in_write_set("srcx/a.py", ["src"])
          and not iso.in_write_set("README.md", ["src"]) and iso.in_write_set("x/y", ["."]),
          "src/a.py in; srcx/a.py and README.md out (prefix is a path, not a string); '.' is all",
          "prefix matching is wrong")
    base, why, _ = iso.clean_base(repo0, ["src"])
    (repo0 / "src" / "app.py").write_text("dirty\n", encoding="utf-8")
    base2, why2, det2 = iso.clean_base(repo0, ["src"])
    check("V-ISO-NO-CLEAN-BASE", bool(base) and not why and not base2 and why2 == iso.NO_CLEAN_BASE,
          f"clean scope -> base {base[:12]}; dirty scope -> NO_CLEAN_BASE ({det2[:60]})",
          f"{base!r} {why!r} {base2!r} {why2!r}")

    # --- in scope: worktree at base, cwd is the worktree, harvested, cleaned ---------------
    repo, lg, gate, work, r, st = build(goals_root, "g-inscope", act_in_scope)
    before_main = main_state(repo)
    seen = {}

    orig_launch = r._launch

    def spy_launch(log, e, prov, spec, d, key, rep, what):
        if d.provider == "codex":
            wt = Path(spec["root"])
            seen.update(wt=wt, head=gs.head(wt), ref=iso.root_ref(wt),
                        mission=r.missions.get(e.epoch_id))
        return orig_launch(log, e, prov, spec, d, key, rep, what)
    r._launch = spy_launch
    drive(r)
    wm = work_missions(r)
    m = wm[0] if wm else {}
    after_main = main_state(repo)
    check("V-ISO-WORKTREE-AT-BASE",
          seen and seen["head"] == before_main[0] and seen["ref"] == f"refs/heads/resident/{m.get('id')}"
          and seen["mission"]["state"] == ms.ISOLATED
          and seen["mission"]["base_commit"] == before_main[0],
          f"worktree created at the goal HEAD {before_main[0][:12]} on resident/<mission>, "
          "mission ISOLATED before the provider was called", f"{seen}")
    spec = work.specs[0] if work.specs else {}
    check("V-ISO-CWD-IS-WORKTREE",
          spec and Path(spec["root"]) == st / "worktrees" / m.get("id", "?")
          and Path(spec["root"]).resolve() != repo.resolve()
          and spec.get("prompt") and spec.get("brief") and spec.get("scope_paths") == ["src"],
          f"provider cwd = {spec.get('root')} (the worktree, not the repo); prompt+brief compiled",
          f"{spec.get('root')} vs repo {repo}")
    check("V-ISO-INSCOPE-HARVESTED",
          m.get("state") == ms.RECONCILED and len(receipts_for(lg, m["id"])) == 1
          and m.get("deliverable_head") and m.get("deliverable_head") != before_main[0]
          and branch_exists(repo, m.get("branch", "")),
          f"RECONCILED, 1 receipt ingested, deliverable {str(m.get('deliverable_head'))[:12]} "
          f"on {m.get('branch')}", f"{m.get('state')} {m.get('refusal')}")
    check("V-ISO-CLEAN-WORKTREE-REMOVED-BRANCH-KEPT",
          m.get("worktree_removed") and not Path(m.get("worktree", "")).exists()
          and git(repo, "rev-parse", f"refs/heads/{m.get('branch')}") == m.get("deliverable_head"),
          "clean worktree removed after harvest; the branch (the deliverable) kept at its tip",
          f"removed={m.get('worktree_removed')} exists={Path(m.get('worktree', '')).exists()}")
    check("V-ISO-MAIN-UNTOUCHED-INSCOPE", after_main == before_main,
          f"goal HEAD/ref/status identical before and after ({before_main[0][:12]})",
          f"{before_main} -> {after_main}")
    # The engine would pay for the same work again at the same tree: refused.
    n_before = len(work.specs)
    reps = [r.once() for _ in range(2)]
    notes = " ".join(n for rp in reps for n in rp.notes)
    check("V-ISO-AWAITING-MERGE",
          len(work.specs) == n_before and iso.WORK_AWAITING_MERGE in notes
          and main_state(repo) == before_main,
          "an unmerged delivered branch blocks re-dispatch; nothing spent, main untouched",
          f"dispatches {n_before}->{len(work.specs)}; notes {notes[:200]}")
    git(repo, "merge", "-q", "--ff-only", m["branch"])
    check("V-ISO-AWAITING-MERGE-CONTROL",
          not iso.awaiting_merge(repo, m["deliverable_head"], m["base_commit"]),
          "control: once a person merges the branch the guard lifts", "still awaiting")
    r.close()

    # --- out of scope, committed ----------------------------------------------------------
    repo, lg, gate, work, r, st = build(goals_root, "g-outc", act_out_committed)
    before_main = main_state(repo)
    drive(r)
    m = work_missions(r)[0]
    ev = m.get("refusal_evidence") or {}
    e = ep.project_epochs(gc.project(lg))[m["id"]]
    check("V-ISO-OUTSCOPE-COMMITTED-REFUSED",
          m["state"] == ms.REFUSED and m.get("refusal") == iso.WRITE_SET_VIOLATION
          and ev.get("offending") == ["README.md"] and e.receipts == []
          and e.state == "ended" and e.outcome == ep.FAILED,
          f"REFUSED, offending {ev.get('offending')}, 0 receipts ingested, epoch ended failed",
          f"{m['state']} {m.get('refusal')} {ev.get('offending')} receipts={e.receipts} "
          f"{e.state}/{e.outcome}")
    check("V-ISO-MAIN-UNTOUCHED-OUTC", main_state(repo) == before_main,
          "goal main identical after the violation (nothing merged or reverted)",
          f"{before_main} -> {main_state(repo)}")
    check("V-ISO-REFUSED-BRANCH-KEPT",
          branch_exists(repo, m["branch"]) and not Path(m["worktree"]).exists(),
          "refusal evidence recorded, clean worktree removed, the branch kept as evidence",
          f"branch={branch_exists(repo, m['branch'])} wt={Path(m['worktree']).exists()}")
    r.close()

    # --- out of scope, uncommitted ------------------------------------------------------------
    repo, lg, gate, work, r, st = build(goals_root, "g-outu", act_out_uncommitted)
    before_main = main_state(repo)
    drive(r)
    m = work_missions(r)[0]
    ev = m.get("refusal_evidence") or {}
    check("V-ISO-OUTSCOPE-UNCOMMITTED-REFUSED",
          m["state"] == ms.REFUSED and ev.get("offending") == ["notes.txt"]
          and receipts_for(lg, m["id"]) == [],
          f"an UNCOMMITTED out-of-scope file is caught: {ev.get('offending')}; nothing ingested",
          f"{m['state']} {ev}")
    check("V-ISO-DIRTY-WORKTREE-NEVER-DELETED",
          (Path(m["worktree"]) / "notes.txt").is_file() and not m.get("worktree_removed")
          and "uncommitted" in (m.get("worktree_kept") or ""),
          f"the worktree with uncommitted bytes is kept: {m.get('worktree_kept', '')[:80]}",
          f"removed={m.get('worktree_removed')} kept={m.get('worktree_kept')}")
    check("V-ISO-MAIN-UNTOUCHED-OUTU", main_state(repo) == before_main, "main identical",
          f"{before_main} -> {main_state(repo)}")
    r.close()

    # --- in scope but uncommitted: harvested, worktree kept ------------------------------------
    repo, lg, gate, work, r, st = build(goals_root, "g-inu", act_in_uncommitted)
    before_main = main_state(repo)
    drive(r)
    m = work_missions(r)[0]
    check("V-ISO-INSCOPE-UNCOMMITTED-KEPT",
          m["state"] == ms.RECONCILED and (Path(m["worktree"]) / "src" / "draft.py").is_file()
          and not m.get("worktree_removed"),
          "in-scope uncommitted work passes the write set; its worktree is not removed",
          f"{m['state']} removed={m.get('worktree_removed')}")
    check("V-ISO-MAIN-UNTOUCHED-INU", main_state(repo) == before_main, "main identical",
          f"{before_main} -> {main_state(repo)}")
    r.close()

    # --- left its branch -------------------------------------------------------------------------
    repo, lg, gate, work, r, st = build(goals_root, "g-left", act_left_branch)
    before_main = main_state(repo)
    drive(r)
    m = work_missions(r)[0]
    reasons = " ".join((m.get("refusal_evidence") or {}).get("reasons", []))
    check("V-ISO-LEFT-BRANCH-REFUSED", m["state"] == ms.REFUSED and iso.LEFT_BRANCH in reasons,
          f"a provider that switched branch is refused ({reasons[:90]})", f"{m['state']} {reasons}")
    check("V-ISO-MAIN-UNTOUCHED-LEFT", main_state(repo) == before_main, "main identical",
          f"{before_main} -> {main_state(repo)}")
    r.close()

    # --- a provider that moves main through the shared refs ----------------------------------------
    repo, lg, gate, work, r, st = build(goals_root, "g-main", act_move_main)
    git(repo, "config", "resident.test.mainref", git(repo, "symbolic-ref", "HEAD"))
    before_main = main_state(repo)
    drive(r)
    m = work_missions(r)[0]
    reasons = " ".join((m.get("refusal_evidence") or {}).get("reasons", []))
    check("V-ISO-MAIN-MOVED-DETECTED",
          m["state"] == ms.REFUSED and iso.MAIN_BRANCH_MOVED in reasons
          and receipts_for(lg, m["id"]) == [],
          f"main moved by the epoch is detected and nothing ingested ({reasons[:100]})",
          f"{m['state']} {reasons}")
    r.close()
    # control: a PERSON's fast-forward commit on main during the epoch is not a violation
    holder = {}

    def act_then_person(wt):
        act_in_scope(wt)
        rp = holder["repo"]
        (rp / "OTHER.md").write_text("a person's commit\n", encoding="utf-8")
        git(rp, "add", "OTHER.md")
        git(rp, "commit", "-qm", "person")
    repo, lg, gate, work, r, st = build(goals_root, "g-person", act_then_person)
    holder["repo"] = repo
    drive(r)
    m = work_missions(r)[0]
    check("V-ISO-PERSON-COMMIT-NOT-VIOLATION", m["state"] == ms.RECONCILED,
          "control: an ordinary fast-forward on main by someone else is not MAIN_BRANCH_MOVED",
          f"{m['state']} {(m.get('refusal_evidence') or {}).get('reasons')}")
    r.close()

    # --- pre-spend refusals through the cycle ------------------------------------------------------
    for gid, paths, want in (("g-empty", [], iso.EMPTY_WRITE_SET),
                             ("g-escape", ["../outside"], iso.WRITE_SET_ESCAPES_REPO)):
        # The gate's failure IS information gain, so inside the gain window health
        # reads HEALTHY by the existing precedence; outside it the refusal must
        # surface as a person's decision, never as RUNNING or STALLED.
        repo, lg, gate, work, r, st = build(goals_root, gid, act_in_scope, paths=paths,
                                            gain_window_s=1e-6)
        before_main = main_state(repo)
        reps = [r.once() for _ in range(3)]
        notes = " ".join(n for rp in reps for n in rp.notes)
        eps = [x for x in ep.project_epochs(gc.project(lg)).values() if x.provider == "codex"]
        check(f"V-ISO-{want}-BEFORE-SPEND",
              want in notes and not work.specs and not eps and not work_missions(r)
              and main_state(repo) == before_main
              and reps[-1].health == "WAITING_FOR_AUTHORITY",
              f"{want}: no epoch begun, no mission, no dispatch; health {reps[-1].health}",
              f"specs={len(work.specs)} eps={len(eps)} health={reps[-1].health} notes={notes[:160]}")
        r.close()

    # --- worktree path exists: refused, the foreign path untouched ------------------------------
    repo, lg, gate, work, r, st = build(goals_root, "g-exists", act_in_scope)
    before_main = main_state(repo)
    real_create = iso.create

    def colliding_create(root, path, branch, base):
        Path(path).mkdir(parents=True, exist_ok=True)
        (Path(path) / "someone_elses.txt").write_text("not the resident's\n", encoding="utf-8")
        return real_create(root, path, branch, base)
    cycle.iso.create = colliding_create
    try:
        reps = [r.once() for _ in range(3)]
    finally:
        cycle.iso.create = real_create
    m = work_missions(r)[0] if work_missions(r) else {}
    e = ep.project_epochs(gc.project(lg)).get(m.get("id", ""), None)
    check("V-ISO-PATH-EXISTS-REFUSED",
          m.get("state") == ms.REFUSED and m.get("refusal") == iso.WORKTREE_PATH_EXISTS
          and not work.specs and e is not None and e.outcome == ep.CANCELLED
          and (Path(m["worktree"]) / "someone_elses.txt").is_file()
          and m.get("worktree_foreign") and main_state(repo) == before_main,
          "existing path: REFUSED before dispatch, epoch cancelled, the foreign dir untouched",
          f"{m.get('state')} {m.get('refusal')} specs={len(work.specs)} "
          f"{e.outcome if e else None}")
    r.close()

    # --- crash after ISOLATED (before the intent): census INCOMPLETE, pristine discarded ----------
    class Crash(Exception):
        pass

    def crash_after_isolated(point, **ctx):
        if point == "after_isolated":
            raise Crash(point)
    st = new_state()
    repo, lg, gate, work, r, _ = build(goals_root, "g-crash", act_in_scope, state=st,
                                       fault=crash_after_isolated)
    before_main = main_state(repo)
    crashed = False
    for _ in range(4):
        try:
            r.once()
        except Crash:
            crashed = True
            break
    wm = work_missions(r)
    mid = wm[0]["id"] if wm else ""
    wt_path = Path(wm[0]["worktree"]) if wm else Path("?")
    wt_existed = wt_path.is_dir()
    r.lock.release()
    r2 = cycle.Resident(ROOT, {"gate": gate, "codex": work}, goals=[(lg, repo)], state_dir=st,
                        config=cycle.Config(cancel_grace_s=0.0), info=FakeInfo())
    out = r2.start()
    row = next((x for x in out["census"] if x["mission"] == mid), {})
    m2 = r2.missions.get(mid) or {}
    check("V-ISO-CRASH-AFTER-ISOLATED-INCOMPLETE",
          crashed and wt_existed and row.get("from") == ms.ISOLATED
          and row.get("classification") == control.INCOMPLETE and m2.get("state") == ms.LOST
          and not work.specs,
          f"crash after isolation: census {row.get('classification')} -> {m2.get('state')}; "
          "the provider was never called", f"crashed={crashed} wt={wt_existed} {row} {m2.get('state')}")
    check("V-ISO-CRASH-PRISTINE-DISCARDED",
          not wt_path.exists() and branch_exists(repo, wm[0]["branch"] if wm else "?")
          and main_state(repo) == before_main,
          "the pristine worktree is removed by the cleanup rule; branch kept; main identical",
          f"wt exists={wt_path.exists()}")
    r2.close()

    # --- crash after ISOLATED, then someone wrote in the worktree: UNCERTAIN, kept --------------
    st = new_state()
    repo, lg, gate, work, r, _ = build(goals_root, "g-crash2", act_in_scope, state=st,
                                       fault=crash_after_isolated)
    before_main = main_state(repo)
    try:
        for _ in range(4):
            r.once()
    except Crash:
        pass
    wm = work_missions(r)
    mid = wm[0]["id"]
    wt_path = Path(wm[0]["worktree"])
    (wt_path / "src" / "hand.py").write_text("somebody's bytes\n", encoding="utf-8")
    r.lock.release()
    r3 = cycle.Resident(ROOT, {"gate": gate, "codex": work}, goals=[(lg, repo)], state_dir=st,
                        config=cycle.Config(cancel_grace_s=0.0), info=FakeInfo())
    out = r3.start()
    row = next((x for x in out["census"] if x["mission"] == mid), {})
    rep = r3.once()
    m3 = r3.missions.get(mid)
    check("V-ISO-CRASH-DIRTY-UNCERTAIN-KEPT",
          row.get("classification") == control.UNCERTAIN and m3["state"] == ms.UNCERTAIN
          and (wt_path / "src" / "hand.py").is_file() and not work.specs
          and main_state(repo) == before_main,
          f"worktree with uncommitted work after a crash: UNCERTAIN, never deleted "
          f"({row.get('reason', '')[:70]})", f"{row} {m3['state']}")
    check("V-ISO-UNCERTAIN-BLOCKS-GOAL",
          any("UNRESOLVED_UNCERTAIN_MISSION" in s for s in rep.skipped),
          "control of the block: the goal dispatches nothing more until a person reconciles",
          f"{rep.skipped}")
    r3.close()

    total = len(passes) + len(fails)
    if fails:
        print(f"\nFAILED: {fails}")
    print(f"GSDX_RESIDENT_ISOLATE_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
