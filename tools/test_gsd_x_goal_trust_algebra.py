#!/usr/bin/env python3
"""Phase 5.2 / 05-2-04: non-AND claims are evaluated through the algebra, element by element.

A claim whose contract combines its elements with OR / SEQ / QUORUM must inherit exactly when
`proof.combine_states` over the per-element premise states says INHERITED -- never by treating the
aggregate fingerprint as an AND, and never by skipping an element whose state is UNKNOWN.

Summary line: GSDX_TRUST_ALGEBRA_PASS=n/m  threshold=n/m
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

_TMP_HOME = Path(tempfile.mkdtemp(prefix="alg-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="alg-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)
os.environ.pop("GSDX_GOAL_EPOCH", None)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import git_state as gs          # noqa: E402
from modules.gsd_x.goal import judge as jd              # noqa: E402
from modules.gsd_x.goal import proof as pf              # noqa: E402
from modules.gsd_x.goal import sweep as sw              # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402

REPO_ID = "7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c"
GATE_CMD = f'"{sys.executable}" gate.py'
GATE_SRC = (
    "import os, sys\n"
    "m = os.environ.get('ALG_MARK')\n"
    "if m:\n"
    "    open(m, 'a').write('ran\\n')\n"
    "sys.exit(0)\n"
)

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}".rstrip())
    else:
        fails += 1
        print(f"FAIL {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    """A raise is a FAIL line, never an escape: the summary line always prints."""
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- survive any gate body
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def _st(log):
    return gc.project(log)


def load_inherit():
    try:
        from modules.gsd_x.goal import inherit  # noqa: PLC0415
        return inherit
    except ImportError:
        return None


def make_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="alg-repo-"))
    for d in ("src", "docs"):
        (repo / d).mkdir()
    for name, text in (("src/a.txt", "alpha\n"), ("src/b.txt", "beta\n"), ("src/c.txt", "gamma\n"),
                       ("docs/n.txt", "notes\n"), ("gate.py", GATE_SRC)):
        (repo / name).write_text(text, encoding="utf-8", newline="\n")
    for args in (("init", "-q"), ("config", "user.name", "t"), ("config", "user.email", "t@t"),
                 ("config", "core.autocrlf", "false"), ("add", "-A"), ("commit", "-q", "-m", "base")):
        rc_, out = gs._git(repo, *args)
        if rc_ != 0:
            raise RuntimeError(f"git {args[0]} failed: {out}")
    return repo


class Alg:
    """A tmp git repo and one SATISFIED claim whose contract has one element per entry of `paths`."""

    def __init__(self, name, combine, paths, k=None, legacy=False):
        self.repo = make_repo()
        self.base = Path(tempfile.mkdtemp(prefix="alg-"))
        self.mark = self.base / "mark.txt"
        os.environ["ALG_MARK"] = str(self.mark)
        self.log = GoalLog(REPO_ID, name, base=self.base)
        gc.declare(self.log, "Algebra", ["it works"], [], {"paths": ["."]}, actor="founder")
        for p in cv.PLANES:
            claimed = p in cv.ALWAYS
            cv.set_plane(self.log, _st(self.log), p, claimed, "" if claimed else "not claimed", "founder")
        self.pin = gs.file_pin(self.repo, ["gate.py"])
        cv.accept_obligation(self.log, _st(self.log), "ob-one", cv.OUTCOME, "do it", GATE_CMD,
                             self.pin, "founder", gate_class="unit")
        cid = pf.claim_id(cv.project_convergence(_st(self.log)).obligations["ob-one"])
        elements = [{"oracle": "unit", "command": GATE_CMD, "gate_pin": [list(p) for p in self.pin],
                     "causal_paths": [p], "env_deps": [], "freshness_class": "DETERMINISTIC",
                     "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}
                    for p in paths]
        body = {"v": 1, "claim_id": cid, "obligation": "ob-one", "combine": combine, "elements": elements}
        if k is not None:
            body["k"] = k
        pf.append_pcc(self.log, _st(self.log), pf.CONTRACT, body, "founder")
        self.t1 = self.tree()
        v = {"gate": "gate.py", "exit_status": 0, "observed": "ok", "tree_hash": self.t1,
             "revision": _st(self.log).revision, "gate_class": "unit", "gate_pin": [list(p) for p in self.pin]}
        orig = pf.certificate_payload
        if legacy:
            def stripped(*a, **kw):
                out = orig(*a, **kw)
                if isinstance(out, dict):
                    out.pop("element_premises", None)
                return out
            pf.certificate_payload = stripped
        try:
            sw._apply_verdicts(self.log, SimpleNamespace(verdicts=[v], tree_before=self.t1, tree_after=self.t1),
                               SimpleNamespace(spec={"obligation": "ob-one"}, epoch_id="ep-0",
                                               provider="gate", handle={}), "sweep", root=self.repo)
        finally:
            pf.certificate_payload = orig
        if not pf.project_proofs(_st(self.log)).produced:
            raise RuntimeError("fixture: the claim produced no certificate")
        if self.mark.exists():
            self.mark.unlink()

    def git(self, *args):
        rc_, out = gs._git(self.repo, *args)
        if rc_ != 0:
            raise RuntimeError(f"git {args[0]} failed: {out}")

    def tree(self):
        return gs.tree_id(self.repo, ["."])

    def edit(self, *rels):
        for rel in rels:
            (self.repo / rel).write_text("changed " + rel + "\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "edit " + ",".join(rels))

    def action(self):
        inh = load_inherit()
        plan = inh.plan(_st(self.log), self.repo, self.tree(), time.time())
        return [p for p in plan if p["obligation"] == "ob-one"][0]["action"]

    def ran(self) -> int:
        return len(self.mark.read_text().splitlines()) if self.mark.exists() else 0

    def judge(self):
        return jd.judge(_st(self.log), self.tree(), self.repo, scope_paths=["."])

    def close(self):
        os.environ.pop("ALG_MARK", None)
        shutil.rmtree(self.base, ignore_errors=True)
        shutil.rmtree(self.repo, ignore_errors=True)


def red_if_absent():
    return None if load_inherit() is not None else (False, "RED-first: modules.gsd_x.goal.inherit absent")


def scenario(combine, paths, edits_list, k=None):
    """One fresh claim per edit set; returns the planned action for each."""
    out = []
    for edits in edits_list:
        w = Alg("alg", combine, paths, k=k)
        try:
            if edits:
                w.edit(*edits)
            out.append(w.action())
        finally:
            w.close()
    return out


def gate_or():
    if (r := red_if_absent()):
        return r
    one, both = scenario("OR", ["src/a.txt", "src/b.txt"], [["src/a.txt"], ["src/a.txt", "src/b.txt"]])
    return one == "INHERIT" and both == "INVALIDATE", f"one-edit={one} both-edits={both}"


def gate_seq():
    if (r := red_if_absent()):
        return r
    a, b, doc = scenario("SEQ", ["src/a.txt", "src/b.txt"], [["src/a.txt"], ["src/b.txt"], ["docs/n.txt"]])
    return a != "INHERIT" and b != "INHERIT" and doc == "INHERIT", f"a={a} b={b} docs={doc}"


def gate_quorum():
    if (r := red_if_absent()):
        return r
    paths = ["src/a.txt", "src/b.txt", "src/c.txt"]
    one, two = scenario("QUORUM", paths, [["src/a.txt"], ["src/a.txt", "src/b.txt"]], k=2)
    return one == "INHERIT" and two != "INHERIT", f"k=2 of 3: one-edit={one} two-edits={two}"


def gate_unknown():
    if (r := red_if_absent()):
        return r
    b, doc = scenario("OR", ["../escape", "src/b.txt"], [["src/b.txt"], ["docs/n.txt"]])
    return b == "RUN" and doc == "INHERIT", f"b-edited={b} docs-edited={doc}"


def gate_without_premises():
    if (r := red_if_absent()):
        return r
    w = Alg("alg-legacy", "OR", ["src/a.txt", "src/b.txt"], legacy=True)
    s = Alg("alg-single", "OR", ["src/a.txt"])
    try:
        legacy, single = w.action(), s.action()
    finally:
        w.close()
        s.close()
    return legacy != "INHERIT" and single != "INHERIT", f"legacy-cert={legacy} single-element={single}"


def gate_judge():
    if (r := red_if_absent()):
        return r
    w = Alg("alg-j1", "OR", ["src/a.txt", "src/b.txt"])
    x = Alg("alg-j2", "OR", ["src/a.txt", "src/b.txt"])
    try:
        w.edit("src/a.txt")
        rec_w = w.judge()
        modes_w = [g.get("mode") for g in rec_w.gates]
        runs_w = w.ran()
        x.edit("src/a.txt", "src/b.txt")
        rec_x = x.judge()
        modes_x = [g.get("mode") for g in rec_x.gates]
        runs_x = x.ran()
    finally:
        w.close()
        x.close()
    ok = modes_w == ["VALIDATE"] and runs_w == 0 and modes_x == [None] and runs_x == 1
    return ok, f"one-edit modes={modes_w} runs={runs_w}; both-edits modes={modes_x} runs={runs_x}"


def gate_vset():
    if (r := red_if_absent()):
        return r
    inh = load_inherit()
    w = Alg("alg-vs", "OR", ["src/a.txt", "src/b.txt"])
    try:
        w.edit("src/a.txt")
        vs = inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())
        got = (vs.get("elements") or {}).get("ob-one")
    finally:
        w.close()
    return got == {"run": [0], "inherit": [1]}, f"elements[ob-one]={got}"


run_gate("V-ALG-OR-ONE-EQUAL-INHERITS", gate_or)
run_gate("V-ALG-SEQ-FIRST-BREAK", gate_seq)
run_gate("V-ALG-QUORUM-K", gate_quorum)
run_gate("V-ALG-UNKNOWN-NEVER-SKIPS", gate_unknown)
run_gate("V-ALG-NONAND-WITHOUT-ELEMENT-PREMISES-RUNS", gate_without_premises)
run_gate("V-ALG-JUDGE-VALIDATES-OR", gate_judge)
run_gate("V-ALG-VSET-LISTS-CHANGED-ELEMENTS", gate_vset)

print(f"GSDX_TRUST_ALGEBRA_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
