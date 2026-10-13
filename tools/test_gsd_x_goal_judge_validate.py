#!/usr/bin/env python3
"""Phase 5 / 05-01: the judge VALIDATEs an inherited certificate on its own evidence, or REPLAYs.

A gate that drops a marker file proves, without timing, whether it ran: a validated obligation leaves the
marker absent, a replayed one leaves it present. The judge must never read a `proof.inherited` event as a
fact -- the event is a claim, and these gates forge one while a causal path has moved.

Summary line: GSDX_JUDGE_VALIDATE_PASS=n/m  threshold=n/m
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

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="jv-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="jv-goals-")) / "goals"
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
from modules.gsd_x.mission import closure as mcl        # noqa: E402

REPO_ID = "7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b"
SWITCH = pf.INHERITANCE_SWITCH
GATE_CMD = f'"{sys.executable}" gate.py'
GATE_SRC = (
    "import os, sys\n"
    "m = os.environ.get('JV_MARK')\n"
    "if m:\n"
    "    open(m, 'a').write('ran\\n')\n"
    "sys.exit(1 if 'altered' in open('src/a.txt').read() else 0)\n"
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


def make_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="jv-repo-"))
    (repo / "src").mkdir()
    (repo / "docs").mkdir()
    (repo / "src" / "a.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
    (repo / "src" / "b.txt").write_text("beta\n", encoding="utf-8", newline="\n")
    (repo / "docs" / "n.txt").write_text("notes\n", encoding="utf-8", newline="\n")
    (repo / "gate.py").write_text(GATE_SRC, encoding="utf-8", newline="\n")
    for args in (("init", "-q"), ("config", "user.name", "t"), ("config", "user.email", "t@t"),
                 ("config", "core.autocrlf", "false"), ("add", "-A"), ("commit", "-q", "-m", "base")):
        rc_, out = gs._git(repo, *args)
        if rc_ != 0:
            raise RuntimeError(f"git {args[0]} failed: {out}")
    return repo


class JV:
    """A real tmp git repo and SATISFIED claims holding certificates at the first tree.

    `obs` is a list of (obligation id, causal paths). `pcc=False` builds a legacy goal: satisfied by a plain
    verdict, no contract and no certificate.
    """

    def __init__(self, name, obs=(("ob-one", ["src"]),), element=None, plane=None,
                 gate_class="unit", pcc=True):
        self.repo = make_repo()
        self.base = Path(tempfile.mkdtemp(prefix="jv-"))
        self.mark = self.base / "mark.txt"
        os.environ["JV_MARK"] = str(self.mark)
        self.log = GoalLog(REPO_ID, name, base=self.base)
        gc.declare(self.log, "Judge validate", ["it works"], [], {"paths": ["."]}, actor="founder")
        on = {plane} if plane else set()
        for p in cv.PLANES:
            claimed = p in cv.ALWAYS or p in on
            cv.set_plane(self.log, _st(self.log), p, claimed, "" if claimed else "not claimed", "founder")
        self.pin = gs.file_pin(self.repo, ["gate.py"])
        for oid, _paths in obs:
            cv.accept_obligation(self.log, _st(self.log), oid, plane or cv.OUTCOME, "do " + oid, GATE_CMD,
                                 self.pin, "founder", gate_class=gate_class)
        self.t1 = self.tree()
        for oid, paths in obs:
            ob = cv.project_convergence(_st(self.log)).obligations[oid]
            cid = pf.claim_id(ob)
            if not pcc:
                st = _st(self.log)
                res = cv.satisfy(self.log, st, oid,
                                 mcl.Verdict("gate.py", 0, "ok", self.t1, st.revision, gate_class, self.pin),
                                 "founder", source={"epoch": "ep-jv", "provider": "gate"})
                if not res.allowed:
                    raise RuntimeError(f"fixture: satisfy refused: {res.reason}")
                continue
            el = {"oracle": gate_class, "command": GATE_CMD, "gate_pin": [list(p) for p in self.pin],
                  "causal_paths": list(paths), "env_deps": [], "freshness_class": "DETERMINISTIC",
                  "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}
            el.update(element or {})
            pf.append_pcc(self.log, _st(self.log), pf.CONTRACT,
                          {"v": 1, "claim_id": cid, "obligation": oid, "combine": "AND",
                           "elements": [el]}, "founder")
            v = {"gate": "gate.py", "exit_status": 0, "observed": "ok", "tree_hash": self.t1,
                 "revision": _st(self.log).revision, "gate_class": gate_class,
                 "gate_pin": [list(p) for p in self.pin]}
            sw._apply_verdicts(self.log, SimpleNamespace(verdicts=[v], tree_before=self.t1, tree_after=self.t1),
                               SimpleNamespace(spec={"obligation": oid}, epoch_id="ep-0", provider="gate",
                                               handle={}), "sweep", root=self.repo)
        if pcc and len(pf.project_proofs(_st(self.log)).produced) != len(obs):
            raise RuntimeError("fixture: a claim produced no certificate")
        if self.mark.exists():
            self.mark.unlink()

    def git(self, *args):
        rc_, out = gs._git(self.repo, *args)
        if rc_ != 0:
            raise RuntimeError(f"git {args[0]} failed: {out}")

    def tree(self):
        return gs.tree_id(self.repo, ["."])

    def edit(self, rel, text):
        (self.repo / rel).write_text(text, encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "edit " + rel)

    def ran(self) -> int:
        return len(self.mark.read_text().splitlines()) if self.mark.exists() else 0

    def judge(self, env=None):
        return jd.judge(_st(self.log), self.tree(), self.repo, scope_paths=["."], env=env)

    def forge(self):
        led = pf.project_proofs(_st(self.log))
        d = led.produced[0]["data"]
        cid = d["claim_id"]
        pf.append_pcc(self.log, _st(self.log), pf.INHERITED_EV,
                      {"v": 1, "claim_id": cid, "certificate": pf.certificate_id(cid, led.produced[0]["seq"]),
                       "candidate": self.tree(), "premises": dict(d["premises"])}, "hand")

    def close(self):
        os.environ.pop("JV_MARK", None)
        shutil.rmtree(self.base, ignore_errors=True)
        shutil.rmtree(self.repo, ignore_errors=True)


def with_switch(value, fn):
    old = os.environ.get(SWITCH)
    try:
        if value is None:
            os.environ.pop(SWITCH, None)
        else:
            os.environ[SWITCH] = value
        return fn()
    finally:
        if old is None:
            os.environ.pop(SWITCH, None)
        else:
            os.environ[SWITCH] = old


def modes(rec) -> list:
    return [g.get("mode") for g in rec.gates]


def gate_hermetic():
    home = Path.home()
    ok = home.resolve() == _TMP_HOME.resolve() and home.resolve() != REAL_HOME.resolve()
    return ok, f"home={home.name}"


def gate_control_validates():
    w = JV("jv-ctl")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        rec = w.judge()
        row = rec.gates[0] if rec.gates else {}
        ok = (rec.verdict == jd.PASS and modes(rec) == ["VALIDATE"] and w.ran() == 0
              and row.get("certificate", "").startswith(("cert", "c")) and row.get("verdict") == jd.PASS)
        return ok, f"verdict={rec.verdict} modes={modes(rec)} gate_runs={w.ran()} row={sorted(row)}"
    finally:
        w.close()


def gate_forged_event_replays():
    w = JV("jv-forged")
    try:
        w.edit("src/a.txt", "altered\n")
        w.forge()
        rec = w.judge()
        runs_w = w.ran()
    finally:
        w.close()
    # the control owns the marker path next: same forged event, bytes unchanged -> validated
    c = JV("jv-forged-ctl")
    try:
        c.edit("docs/n.txt", "changed notes\n")
        c.forge()
        rec_c = c.judge()
        ok = (rec.verdict == jd.REFUSED and runs_w == 1 and modes(rec) == [None]
              and rec_c.verdict == jd.PASS and modes(rec_c) == ["VALIDATE"] and c.ran() == 0)
        return ok, (f"forged: verdict={rec.verdict} runs={runs_w} modes={modes(rec)}; "
                    f"control: verdict={rec_c.verdict} runs={c.ran()} modes={modes(rec_c)}")
    finally:
        c.close()


def gate_weakened_gate_refused():
    w = JV("jv-weak")
    try:
        w.edit("gate.py", GATE_SRC + "# weakened\n")
        w.edit("docs/n.txt", "changed notes\n")
        rec = w.judge()
        row = rec.gates[0] if rec.gates else {}
        ok = (rec.verdict == jd.REFUSED and "gate.py" in str(row.get("detail", "")) and w.ran() == 0
              and modes(rec) == [None])
        return ok, f"verdict={rec.verdict} runs={w.ran()} detail={str(row.get('detail', ''))[:60]!r}"
    finally:
        w.close()


def gate_causal_move_replays():
    w = JV("jv-causal")
    try:
        w.edit("src/b.txt", "beta two\n")
        rec = w.judge()
        ok = rec.verdict == jd.PASS and w.ran() == 1 and modes(rec) == [None]
        return ok, f"verdict={rec.verdict} runs={w.ran()} modes={modes(rec)}"
    finally:
        w.close()


def gate_doubt_replays():
    cases = (("unknown-fingerprint", {"element": {"causal_paths": ["../escape"]}}),
             ("fresh-required", {"element": {"freshness_class": "FRESH_REQUIRED"}}),
             ("risk-tag", {"element": {"risk_tags": ["security"]}}),
             ("never-opted-in", {"element": {"inheritability": "never"}}),
             ("reality-plane", {"plane": cv.REALITY, "gate_class": "in_game"}))
    res = {}
    for label, kw in cases:
        w = JV("jv-doubt-" + label, **kw)
        try:
            w.edit("docs/n.txt", "changed notes\n")
            rec = w.judge()
            res[label] = (rec.verdict == jd.PASS and w.ran() == 1 and modes(rec) == [None], w.ran())
        finally:
            w.close()
    return all(v[0] for v in res.values()), f"cases={res}"


def gate_same_candidate_replays():
    w = JV("jv-same")
    try:
        rec = w.judge()
        ok = rec.verdict == jd.PASS and w.ran() == 1 and modes(rec) == [None]
        return ok, f"verdict={rec.verdict} runs={w.ran()} modes={modes(rec)}"
    finally:
        w.close()


def gate_switch_off_is_legacy():
    w = JV("jv-off")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        rec = with_switch("off", w.judge)
        ok = rec.verdict == jd.PASS and w.ran() == 1 and modes(rec) == [None]
        return ok, f"verdict={rec.verdict} runs={w.ran()} modes={modes(rec)}"
    finally:
        w.close()


def gate_epoch_still_refuses():
    w = JV("jv-epoch")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        rec = w.judge(env={**os.environ, jd.EPOCH_ENV: "ep-builder"})
        ok = rec.verdict == jd.UNJUDGEABLE and not rec.gates and w.ran() == 0
        return ok, f"verdict={rec.verdict} gates={len(rec.gates)} runs={w.ran()}"
    finally:
        w.close()


def gate_mixed_order():
    w = JV("jv-mixed", obs=(("ob-one", ["src"]), ("ob-two", ["docs"])))
    try:
        w.edit("docs/n.txt", "changed notes\n")
        rec = w.judge()
        ids = [g.get("obligation") for g in rec.gates]
        ok = (rec.verdict == jd.PASS and ids == ["ob-one", "ob-two"] and modes(rec) == ["VALIDATE", None]
              and w.ran() == 1 and "1 validated" in rec.reason and "1 pinned gate(s) re-run" in rec.reason)
        return ok, f"ids={ids} modes={modes(rec)} runs={w.ran()} reason={rec.reason[:90]!r}"
    finally:
        w.close()


def gate_legacy_receipt_equal():
    w = JV("jv-legacy", pcc=False)
    try:
        rec = w.judge()
        row = rec.gates[0] if rec.gates else {}
        want = {"obligation", "gate", "verdict", "exit_status", "observed", "seconds"}
        ok = (rec.verdict == jd.PASS and set(row) == want and w.ran() == 1
              and rec.reason == f"1 pinned gate(s) re-run and passed at {w.tree()}")
        return ok, f"verdict={rec.verdict} keys={sorted(row)} reason={rec.reason[:70]!r}"
    finally:
        w.close()


GATES = [
    ("V-JV-HERMETIC-HOME", gate_hermetic),
    ("V-JV-CONTROL-VALIDATES", gate_control_validates),
    ("V-JV-FORGED-EVENT-REPLAYS", gate_forged_event_replays),
    ("V-JV-WEAKENED-GATE-REFUSED", gate_weakened_gate_refused),
    ("V-JV-CAUSAL-MOVE-REPLAYS", gate_causal_move_replays),
    ("V-JV-DOUBT-REPLAYS", gate_doubt_replays),
    ("V-JV-SAME-CANDIDATE-REPLAYS", gate_same_candidate_replays),
    ("V-JV-SWITCH-OFF-IS-LEGACY", gate_switch_off_is_legacy),
    ("V-JV-EPOCH-STILL-REFUSES", gate_epoch_still_refuses),
    ("V-JV-MIXED-ORDER", gate_mixed_order),
    ("V-JV-LEGACY-RECEIPT-EQUAL", gate_legacy_receipt_equal),
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_JUDGE_VALIDATE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
