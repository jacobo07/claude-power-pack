"""Invalidation suite for proof-conserving convergence (GSD X, Phase 4).

Drives R12 (unknown trees never equal), candidate snapshots on git objects, the
`candidate.promoted` event, and (plans 04-03/04-04) proof inheritance. Hermetic: HOME,
USERPROFILE and GSDX_GOALS_ROOT are redirected before any engine import.

Summary line: GSDX_INVALIDATION_PASS=n/m  threshold=m/m
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="inv-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="inv-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import git_state as gs          # noqa: E402
from modules.gsd_x.goal import reconcile as rc          # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402
from modules.gsd_x.mission import closure as mcl        # noqa: E402

REPO_ID = "6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a6a"
PIN = (("tools/gate.py", "9" * 64),)
UNKNOWN_TREE = "unknown:not-a-git-tree"
REAL_TREE = "a" * 40

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


def goal_with_satisfied(tree: str, name: str):
    """(log, state, base): one obligation SATISFIED by a verdict bound to `tree`."""
    base = Path(tempfile.mkdtemp(prefix="inv-"))
    log = GoalLog(REPO_ID, name, base=base)
    gc.declare(log, "Exercise invalidation", ["it works"], [], {"paths": ["src"]}, actor="founder")
    for plane in cv.PLANES:
        cv.set_plane(log, _st(log), plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed", "founder")
    cv.accept_obligation(log, _st(log), "ob-one", cv.OUTCOME, "do it", "python tools/gate.py",
                         PIN, "founder")
    st = _st(log)
    res = cv.satisfy(log, st, "ob-one",
                     mcl.Verdict("tools/gate.py", 0, "ok", tree, st.revision, "unit", PIN),
                     "founder", source={"epoch": "ep-inv", "provider": "gate"})
    if not res.allowed:
        raise RuntimeError(f"satisfy refused: {res.reason}")
    return log, _st(log), base


# --- R12: an unknown tree is never equal to anything, itself included -----------------

def gate_r12_closure():
    log, st, base = goal_with_satisfied(UNKNOWN_TREE, "inv-r12a")
    try:
        got = cv.goal_closure(st, UNKNOWN_TREE)
        blocked = any("ob-one" in b for b in got.blocking)
        return blocked and not got.may_close, f"may_close={got.may_close} blocking={got.blocking[:1]}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_r12_needs_gate():
    log, st, base = goal_with_satisfied(UNKNOWN_TREE, "inv-r12b")
    try:
        o = cv.project_convergence(st).obligations["ob-one"]
        ctx = SimpleNamespace(tree_hash=UNKNOWN_TREE, state=st)
        why = rc._needs_a_gate_here(o, ctx)
        return bool(why), f"reason={why[:60]!r}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_r12_control():
    log, st, base = goal_with_satisfied(REAL_TREE, "inv-r12c")
    try:
        got = cv.goal_closure(st, REAL_TREE)
        o = cv.project_convergence(st).obligations["ob-one"]
        why = rc._needs_a_gate_here(o, SimpleNamespace(tree_hash=REAL_TREE, state=st))
        blocked_other = cv.goal_closure(st, "b" * 40).blocking
        ok = (not any("ob-one" in b for b in got.blocking)) and why == "" and bool(blocked_other)
        return ok, f"real_equal_closes={not any('ob-one' in b for b in got.blocking)} needs_gate={why!r} other_tree_blocks={bool(blocked_other)}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


# --- candidate snapshots on git objects ------------------------------------------------

def load_candidate():
    try:
        from modules.gsd_x.goal import candidate  # noqa: PLC0415
        return candidate
    except ImportError:
        return None


def load_proof():
    from modules.gsd_x.goal import proof  # noqa: PLC0415
    return proof


def make_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="inv-repo-"))
    (repo / "src").mkdir()
    (repo / "src" / "a.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
    (repo / "src" / "b.txt").write_text("beta\n", encoding="utf-8", newline="\n")
    for args in (("init", "-q"), ("config", "user.name", "t"), ("config", "user.email", "t@t"),
                 ("config", "core.autocrlf", "false"), ("add", "-A"), ("commit", "-q", "-m", "base")):
        rc_, out = gs._git(repo, *args)
        if rc_ != 0:
            raise RuntimeError(f"git {args[0]} failed: {out}")
    return repo


def _head_tree(repo: Path) -> str:
    return gs._git(repo, "rev-parse", "HEAD^{tree}")[1].strip()


def _refs(repo: Path) -> str:
    return gs._git(repo, "for-each-ref")[1] + gs._git(repo, "rev-parse", "HEAD")[1]


def _index_digest(repo: Path) -> str:
    return hashlib.sha256((repo / ".git" / "index").read_bytes()).hexdigest()


def need_candidate():
    c = load_candidate()
    return c, "RED-first: modules.gsd_x.goal.candidate absent"


def gate_cand_oid():
    c, why = need_candidate()
    if c is None:
        return False, why
    repo = make_repo()
    try:
        clean = c.snapshot(repo, ["src"])
        (repo / "src" / "a.txt").write_text("alpha changed\n", encoding="utf-8", newline="\n")
        dirty = c.snapshot(repo, ["src"])
        head = _head_tree(repo)
        ok = clean == head and dirty != head and len(dirty) == 40 and not dirty.startswith("unknown:")
        return ok, f"clean_equals_HEAD_tree={clean == head} dirty_differs={dirty != head} len={len(dirty)}"
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def gate_cand_no_side_effect():
    c, why = need_candidate()
    if c is None:
        return False, why
    repo = make_repo()
    try:
        (repo / "src" / "a.txt").write_text("alpha changed\n", encoding="utf-8", newline="\n")
        (repo / "src" / "new.txt").write_text("new\n", encoding="utf-8", newline="\n")
        before = (_index_digest(repo), _refs(repo), gs._git(repo, "status", "--porcelain")[1])
        oid = c.snapshot(repo, ["src"])
        after = (_index_digest(repo), _refs(repo), gs._git(repo, "status", "--porcelain")[1])
        leftovers = sorted(p.name for p in (repo / ".git").glob("*.snap*"))
        return before == after and not oid.startswith("unknown:") and not leftovers, \
            f"index_same={before[0] == after[0]} refs_same={before[1] == after[1]} status_same={before[2] == after[2]} leftovers={leftovers}"
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def gate_cand_unknown_on_doubt():
    c, why = need_candidate()
    if c is None:
        return False, why
    repo = make_repo()
    plain = Path(tempfile.mkdtemp(prefix="inv-plain-"))
    try:
        cases = {
            "not-a-repo": c.snapshot(plain, ["src"]),
            "dotdot": c.snapshot(repo, [".."]),
            "absolute": c.snapshot(repo, [str(repo / "src")]),
            "empty": c.snapshot(repo, []),
            "missing-root": c.snapshot(repo / "nope", ["src"]),
        }
        bad = {k: v for k, v in cases.items() if not v.startswith("unknown:")}
        return not bad, f"all_unknown={not bad} bad={bad}"
    finally:
        shutil.rmtree(repo, ignore_errors=True)
        shutil.rmtree(plain, ignore_errors=True)


def gate_cand_stable():
    c, why = need_candidate()
    if c is None:
        return False, why
    repo = make_repo()
    try:
        a = c.snapshot(repo, ["src"])
        b = c.snapshot(repo, ["src"])
        (repo / "src" / "b.txt").write_text("beta!\n", encoding="utf-8", newline="\n")
        d = c.snapshot(repo, ["src"])
        return a == b and a != d, f"same_content_same_oid={a == b} one_byte_differs={a != d}"
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def gate_cand_drift():
    c, why = need_candidate()
    if c is None:
        return False, why
    promoted = {"v": 1, "candidate": "snap:" + "1" * 40, "tree": "1" * 40, "fingerprint": "cf1:" + "f" * 64}
    same = c.drift(promoted, "1" * 40)
    moved = c.drift(promoted, "2" * 40)
    unk = c.drift(promoted, "unknown:x")
    unk2 = c.drift(dict(promoted, tree="unknown:y"), "1" * 40)
    return same is False and moved is True and unk is None and unk2 is None, \
        f"same={same} moved={moved} current_unknown={unk} promoted_unknown={unk2}"


def gate_promoted_projection():
    proof = load_proof()
    if not hasattr(proof, "PROMOTED"):
        return False, "RED-first: proof.PROMOTED absent"
    base = Path(tempfile.mkdtemp(prefix="inv-"))
    try:
        log = GoalLog(REPO_ID, "inv-promoted", base=base)
        gc.declare(log, "Promote", ["it works"], [], {"paths": ["src"]}, actor="founder")
        data = {"v": 1, "candidate": "snap:" + "1" * 40, "tree": "1" * 40, "fingerprint": "cf1:" + "f" * 64}
        ledger = proof.append_pcc(log, _st(log), proof.PROMOTED, data, "reconciler")
        rec = ledger.promoted[-1] if ledger.promoted else {}
        newer = dict(data, v=2)
        refused = False
        try:
            proof.append_pcc(log, _st(log), proof.PROMOTED, newer, "reconciler")
        except proof.ProofRefused:
            refused = True
        log.append(_st(log).last_seq + 1, proof.PROMOTED, newer, "other-writer")
        ledger2 = proof.project_proofs(_st(log))
        ok = (len(ledger.promoted) == 1 and rec.get("data") == data and refused
              and len(ledger2.unsupported) == 1 and len(ledger2.promoted) == 1
              and proof.PROMOTED in proof.NEW_TYPES)
        return ok, f"projected={len(ledger.promoted)} newer_v_refused={refused} unsupported={ledger2.unsupported}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


# --- inheritance: observe -> plan -> apply, and the pure consumer (plan 04-03) ----------------

import time  # noqa: E402

from modules.gsd_x.goal import frontier as fr           # noqa: E402
from modules.gsd_x.goal import proof as pf              # noqa: E402
from modules.gsd_x.goal import sweep as sw              # noqa: E402

SWITCH = pf.INHERITANCE_SWITCH
GATE_CMD = f'"{sys.executable}" gate.py'


def load_inherit():
    try:
        from modules.gsd_x.goal import inherit  # noqa: PLC0415
        return inherit
    except ImportError:
        return None


class Inh:
    """A real tmp git repo and one SATISFIED claim holding a certificate at the first tree."""

    def __init__(self, name, element=None, plane=None, gate_class="unit"):
        self.repo = make_repo()
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "n.txt").write_text("notes\n", encoding="utf-8", newline="\n")
        (self.repo / "gate.py").write_text("print('1 passed')\n", encoding="utf-8", newline="\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture")
        self.base = Path(tempfile.mkdtemp(prefix="inv-"))
        self.log = GoalLog(REPO_ID, name, base=self.base)
        gc.declare(self.log, "Inherit", ["it works"], [], {"paths": ["."]}, actor="founder")
        on = {plane} if plane else set()
        for p in cv.PLANES:
            claimed = p in cv.ALWAYS or p in on
            cv.set_plane(self.log, _st(self.log), p, claimed, "" if claimed else "not claimed", "founder")
        self.pin = gs.file_pin(self.repo, ["gate.py"])
        cv.accept_obligation(self.log, _st(self.log), "ob-one", plane or cv.OUTCOME, "do it", GATE_CMD,
                             self.pin, "founder", gate_class=gate_class)
        self.cid = pf.claim_id(cv.project_convergence(_st(self.log)).obligations["ob-one"])
        el = {"oracle": gate_class, "command": GATE_CMD, "gate_pin": [list(p) for p in self.pin],
              "causal_paths": ["src"], "env_deps": [], "freshness_class": "DETERMINISTIC",
              "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}
        el.update(element or {})
        combine = el.pop("combine", "AND")
        pf.append_pcc(self.log, _st(self.log), pf.CONTRACT,
                      {"v": 1, "claim_id": self.cid, "obligation": "ob-one", "combine": combine,
                       "elements": [el]}, "founder")
        self.t1 = self.tree()
        v = {"gate": "gate.py", "exit_status": 0, "observed": "ok", "tree_hash": self.t1,
             "revision": _st(self.log).revision, "gate_class": gate_class,
             "gate_pin": [list(p) for p in self.pin]}
        sw._apply_verdicts(self.log, SimpleNamespace(verdicts=[v], tree_before=self.t1, tree_after=self.t1),
                           SimpleNamespace(spec={"obligation": "ob-one"}, epoch_id="ep-0", provider="gate",
                                           handle={}), "sweep", root=self.repo)
        if not pf.project_proofs(_st(self.log)).produced:
            raise RuntimeError("fixture: the claim produced no certificate")

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

    def step(self, apply=True):
        inh = load_inherit()
        tree = self.tree()
        plan = inh.plan(_st(self.log), self.repo, tree, time.time())
        if apply:
            inh.apply(self.log, plan, tree, "sweep")
        return [p for p in plan if p["obligation"] == "ob-one"][0]["action"]

    def inherited(self):
        return load_inherit().inherited_ids(_st(self.log), self.tree())

    def ledger(self):
        return pf.project_proofs(_st(self.log))

    def cert(self):
        led = self.ledger()
        return led.produced[0]["data"], pf.certificate_id(self.cid, led.produced[0]["seq"])

    def forge(self, premises=None):
        d, cert = self.cert()
        pf.append_pcc(self.log, _st(self.log), pf.INHERITED_EV,
                      {"v": 1, "claim_id": self.cid, "certificate": cert, "candidate": self.tree(),
                       "premises": premises or dict(d["premises"])}, "hand")

    def close(self):
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


def red_if_absent():
    return None if load_inherit() is not None else (False, "RED-first: modules.gsd_x.goal.inherit absent")


def gate_inh_ok():
    if (r := red_if_absent()):
        return r
    w = Inh("inh-ok")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        t2 = w.tree()
        act = w.step()
        got = w.inherited()
        st = _st(w.log)
        o = cv.project_convergence(st).obligations["ob-one"]
        ctx = SimpleNamespace(tree_hash=t2, state=st)
        closes = not any("ob-one" in b for b in cv.goal_closure(st, t2, inherited=got).blocking)
        closes_plain = not any("ob-one" in b for b in cv.goal_closure(st, t2).blocking)
        with_set = rc._needs_a_gate_here(o, ctx, got)
        plain = rc._needs_a_gate_here(o, ctx)
        ok = (act == "INHERIT" and got == frozenset({"ob-one"}) and closes and not closes_plain
              and with_set == "" and bool(plain) and t2 != w.t1)
        return ok, f"action={act} inherited={sorted(got)} closes={closes} closes_without_set={closes_plain}"
    finally:
        w.close()


def gate_inh_false_reuse():
    if (r := red_if_absent()):
        return r
    w = Inh("inh-false")
    try:
        w.edit("src/a.txt", "altered\n")
        act = w.step()
        _, cert = w.cert()
        led = w.ledger()
        dead = [i for i in led.invalidated if i["data"].get("certificate") == cert]
        ok = act == "INVALIDATE" and not w.inherited() and len(dead) == 1 and not led.inherited
        return ok, f"action={act} inherited={sorted(w.inherited())} invalidated={len(dead)}"
    finally:
        w.close()


def gate_inh_unknown_not_clean():
    if (r := red_if_absent()):
        return r
    res = {}
    for label, element in (("unknown-fingerprint", {"causal_paths": ["../escape"]}),
                           ("unknown-environment", {"freshness_class": "ENVIRONMENT_SENSITIVE"})):
        w = Inh("inh-unk-" + label, element=element)
        try:
            w.edit("docs/n.txt", "changed notes\n")
            act = w.step()
            res[label] = (act == "RUN" and not w.inherited() and not w.ledger().inherited, act)
        finally:
            w.close()
    return all(v[0] for v in res.values()), f"cases={res}"


def gate_inh_fresh_required_never():
    if (r := red_if_absent()):
        return r
    cases = (("fresh-required", {"element": {"freshness_class": "FRESH_REQUIRED"}}),
             ("risk-tag", {"element": {"risk_tags": ["security"]}}),
             ("legacy-never", {"element": {"inheritability": "never"}}),
             ("unknown-class", {"element": {"freshness_class": "BOGUS"}}),
             ("reality-plane", {"plane": cv.REALITY, "gate_class": "in_game"}))
    res = {}
    for label, kw in cases:
        w = Inh("inh-fr-" + label, **kw)
        try:
            w.edit("docs/n.txt", "changed notes\n")
            act = w.step()
            w.forge()
            res[label] = (act == "RUN" and not w.inherited(), act)
        finally:
            w.close()
    return all(v[0] for v in res.values()), f"cases={res}"


def gate_inh_omitted_without_event():
    if (r := red_if_absent()):
        return r
    w = Inh("inh-omit")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        act = w.step(apply=False)
        ok = act == "INHERIT" and not w.inherited() and not w.ledger().inherited
        return ok, f"planned={act} inherited={sorted(w.inherited())} events={len(w.ledger().inherited)}"
    finally:
        w.close()


def gate_inh_event_disagrees():
    if (r := red_if_absent()):
        return r
    w = Inh("inh-disagree")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        d, _ = w.cert()
        fp = dict(d["premises"], fingerprint="cf1:" + "0" * 64)
        env = dict(d["premises"], environment="env1:" + "0" * 64)
        rev = dict(d["premises"], revision="r-not-this-one")
        refused = []
        for label, prem in (("fingerprint", fp), ("environment", env), ("revision", rev)):
            w.forge(prem)
            refused.append(not w.inherited())
        w.step()
        control = w.inherited() == frozenset({"ob-one"})
        return all(refused) and control, f"forged_ignored={refused} truthful_event_control={control}"
    finally:
        w.close()


def gate_inh_switch_off():
    if (r := red_if_absent()):
        return r
    w = Inh("inh-off")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        w.step()
        on = w.inherited()
        off_set = with_switch("off", w.inherited)
        off_act = with_switch("off", lambda: w.step(apply=False))
        events_before = len(w.ledger().inherited)
        with_switch("off", lambda: w.step())
        ok = (on == frozenset({"ob-one"}) and not off_set and off_act == "RUN"
              and len(w.ledger().inherited) == events_before)
        return ok, f"on={sorted(on)} off={sorted(off_set)} off_action={off_act}"
    finally:
        w.close()


def _ctx(w):
    return rc.Context(state=_st(w.log), tree_hash=w.tree(), scope_hash="s", observations={},
                      now=time.time(), budget={}, providers=("gate",), engine="e")


def gate_inh_frontier_consumes():
    if (r := red_if_absent()):
        return r
    a, b = Inh("inh-fr-a"), Inh("inh-fr-b")
    try:
        for w in (a, b):
            w.edit("docs/n.txt", "changed notes\n")
        a.step()                                   # a carries the event, b does not
        ra = [o.identifier for o, _k in fr._runnable_gate_obligations(_ctx(a))]
        rb = [o.identifier for o, _k in fr._runnable_gate_obligations(_ctx(b))]
        ea = [u["obligation"] for u in fr.compile_frontier(_ctx(a)).execution]
        eb = [u["obligation"] for u in fr.compile_frontier(_ctx(b)).execution]
        ok = ra == [] and ea == [] and rb == ["ob-one"] and eb == ["ob-one"]
        return ok, f"with_event runnable={ra} exec={ea}; without runnable={rb} exec={eb}"
    finally:
        a.close()
        b.close()


def _drain(w, limit_s=90.0):
    acted = []
    end = time.time() + limit_s
    while time.time() < end:
        got = sw.sweep_goal(w.log, w.repo, providers=("gate",), run_dir=w.base / "runs")
        acted.extend(got)
        open_ = [e for e in sw.ep.project_epochs(_st(w.log)).values() if e.state != "ended"]
        if not open_ and not any("dispatched" in a or "harvested" in a for a in got):
            return acted
        time.sleep(0.4)
    acted.append("DRAIN TIMEOUT")
    return acted


def gate_inh_sweep_e2e():
    if (r := red_if_absent()):
        return r
    a, b = Inh("inh-e2e-a"), Inh("inh-e2e-b")
    try:
        a.edit("docs/n.txt", "changed notes\n")          # outside the causal set
        b.edit("src/a.txt", "altered\n")                  # inside it
        first_a = sw.sweep_goal(a.log, a.repo, providers=("gate",), run_dir=a.base / "runs")
        la = a.ledger()
        skipped = (len(la.inherited) == 1 and la.inherited[0]["data"]["candidate"] == a.tree()
                   and not any("dispatched" in x for x in first_a)
                and any("verification set run=[] inherit=['ob-one']" in x for x in first_a))
        acted_b = _drain(b)
        lb = b.ledger()
        _, cert_b = b.cert()
        reran = (any("dispatched" in x for x in acted_b) and "DRAIN TIMEOUT" not in acted_b
                 and any(i["data"].get("certificate") == cert_b for i in lb.invalidated)
                 and not lb.inherited and len(lb.produced) == 2)
        return skipped and reran, (f"A inherited={len(la.inherited)} dispatched={any('dispatched' in x for x in first_a)}; "
                                   f"B invalidated={len(lb.invalidated)} produced={len(lb.produced)} dispatched={any('dispatched' in x for x in acted_b)}")
    finally:
        a.close()
        b.close()


# --- algebra, minimal verification set, fresh islands, drift substrate (plan 04-04) -----------

def gate_inv_algebra():
    if not hasattr(pf, "combine_states"):
        return False, "RED-first: proof.combine_states absent"
    F, I, S, U = pf.PS_FRESH, pf.PS_INHERITED, pf.PS_STALE, pf.PS_UNKNOWN
    cs = pf.combine_states
    table = [
        (("AND", [F, F]), F), (("AND", [F, I]), I), (("AND", [F, S]), S), (("AND", [F, U]), U),
        (("AND", [U, S]), S), (("AND", [pf.PS_SUPERSEDED, F]), S), (("AND", []), U),
        (("OR", [S, F]), F), (("OR", [I, S]), I), (("OR", [U, U]), U), (("OR", [S, U]), U),
        (("OR", [S, S]), S), (("OR", []), U),
        (("SEQ", [F, I, F]), I), (("SEQ", [F, U, S]), U), (("SEQ", [S, F]), S), (("SEQ", [F, F]), F),
        (("XOR", [F, F]), U),
    ]
    bad = [(k, want, cs(k[0], k[1])) for k, want in table if cs(k[0], k[1]) != want]
    quorum = [((2, [F, I, S]), I), ((2, [F, F, S]), F), ((2, [F, U, S]), U), ((2, [F, S, S]), S),
              ((2, [U, U, S]), U), ((0, [F]), U), ((3, [F, F]), U), ((True, [F]), U)]
    bad += [(("QUORUM",) + k, want, cs("QUORUM", k[1], k[0]))
            for k, want in quorum if cs("QUORUM", k[1], k[0]) != want]
    never = all(cs(op, [x]) not in (F, I) for op in ("AND", "OR", "SEQ") for x in (S, U))
    return not bad and never, f"mismatches={bad[:3]} unknown_or_stale_never_satisfy={never}"


def gate_inv_nonand_runs():
    if (r := red_if_absent()):
        return r
    if not hasattr(load_inherit(), "verification_set"):
        return False, "RED-first: inherit.verification_set absent"
    res = {}
    for combine in ("OR", "SEQ", "QUORUM"):
        w = Inh("inv-nonand-" + combine.lower(), element={"combine": combine})
        try:
            w.edit("docs/n.txt", "changed notes\n")
            w.step()
            vs = load_inherit().verification_set(_st(w.log), w.repo, w.tree(), time.time())
            res[combine] = ("ob-one" in vs["run"] and "ob-one" not in vs["inherit"])
        finally:
            w.close()
    w = Inh("inv-nonand-control")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        w.step()
        vs = load_inherit().verification_set(_st(w.log), w.repo, w.tree(), time.time())
        control = "ob-one" in vs["inherit"] and "ob-one" not in vs["run"]
    finally:
        w.close()
    return all(res.values()) and control, f"non_and_in_run={res} and_control_inherits={control}"


def gate_inv_vset_evidence():
    if (r := red_if_absent()):
        return r
    if not hasattr(load_inherit(), "verification_set"):
        return False, "RED-first: inherit.verification_set absent"
    inh = load_inherit()
    w = Inh("inv-evidence")
    try:
        at_verdict = inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())
        w.edit("docs/n.txt", "changed notes\n")
        w.step(apply=False)
        planned = inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())
        w.step()
        applied = inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())
        ok = (at_verdict["fresh"] == ["ob-one"] and "ob-one" not in at_verdict["run"]
              and planned["run"] == ["ob-one"] and not planned["inherit"]
              and applied["inherit"] == ["ob-one"] and not applied["run"])
        return ok, f"fresh={at_verdict['fresh']} planned_run={planned['run']} applied_inherit={applied['inherit']}"
    finally:
        w.close()


def gate_inv_vset_unknown_full():
    if (r := red_if_absent()):
        return r
    if not hasattr(load_inherit(), "verification_set"):
        return False, "RED-first: inherit.verification_set absent"
    inh = load_inherit()
    res = {}
    for label, element in (("no-causal-paths", {"causal_paths": []}),
                           ("unknown-fingerprint", {"causal_paths": ["../escape"]})):
        w = Inh("inv-full-" + label, element=element)
        try:
            w.edit("docs/n.txt", "changed notes\n")
            w.step()
            vs = inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())
            res[label] = bool(vs["full"]) and "ob-one" in vs["run"]
        finally:
            w.close()
    w = Inh("inv-full-control")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        w.step()
        control = not inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())["full"]
    finally:
        w.close()
    return all(res.values()) and control, f"unknown_is_full={res} known_is_not_full={control}"


def gate_inv_fresh_islands():
    if (r := red_if_absent()):
        return r
    inh = load_inherit()
    if not hasattr(inh, "fresh_islands") or not hasattr(inh, "verification_set"):
        return False, "RED-first: inherit.fresh_islands / verification_set absent"
    cases = (("fresh-required", {"element": {"freshness_class": "FRESH_REQUIRED"}}),
             ("risk-tag", {"element": {"risk_tags": ["security"]}}),
             ("reality-plane", {"plane": cv.REALITY, "gate_class": "in_game"}))
    res = {}
    for label, kw in cases:
        w = Inh("inv-island-" + label, **kw)
        try:
            w.edit("docs/n.txt", "changed notes\n")
            w.step()
            w.forge()
            vs = inh.verification_set(_st(w.log), w.repo, w.tree(), time.time())
            names = [i["obligation"] for i in inh.fresh_islands(_st(w.log))]
            res[label] = names == ["ob-one"] and "ob-one" not in vs["inherit"] \
                and [i["obligation"] for i in vs["islands"]] == ["ob-one"]
        finally:
            w.close()
    w = Inh("inv-island-control")
    try:
        control = inh.fresh_islands(_st(w.log)) == []
    finally:
        w.close()
    return all(res.values()) and control, f"islands={res} ordinary_claim_not_listed={control}"


def gate_inv_vset_no_overlap():
    if (r := red_if_absent()):
        return r
    if not hasattr(load_inherit(), "verification_set"):
        return False, "RED-first: inherit.verification_set absent"
    inh = load_inherit()
    w = Inh("inv-overlap")
    try:
        cv.accept_obligation(w.log, _st(w.log), "ob-two", cv.OUTCOME, "second", GATE_CMD, w.pin, "founder",
                             gate_class="unit")
        w.edit("docs/n.txt", "changed notes\n")
        w.step()
        rows = {}
        for label, state in (("with-event", _st(w.log)),):
            vs = inh.verification_set(state, w.repo, w.tree(), time.time())
            groups = [set(vs["run"]), set(vs["inherit"]), set(vs["fresh"])]
            disjoint = sum(len(g) for g in groups) == len(set().union(*groups))
            rows[label] = (disjoint, set().union(*groups) == {"ob-one", "ob-two"}, vs["run"], vs["inherit"])
        ok = all(a and b for a, b, _, _ in rows.values()) and rows["with-event"][2] == ["ob-two"] \
            and rows["with-event"][3] == ["ob-one"]
        return ok, f"rows={rows}"
    finally:
        w.close()


def gate_inv_drift_substrate():
    if (r := red_if_absent()):
        return r
    inh = load_inherit()
    if not hasattr(inh, "promoted_drift"):
        return False, "RED-first: inherit.promoted_drift absent"
    base = Path(tempfile.mkdtemp(prefix="inv-"))
    try:
        log = GoalLog(REPO_ID, "inv-drift", base=base)
        gc.declare(log, "Drift", ["it works"], [], {"paths": ["src"]}, actor="founder")
        none_yet = inh.promoted_drift(_st(log), "1" * 40)
        pf.append_pcc(log, _st(log), pf.PROMOTED, {"v": 1, "candidate": "snap:" + "1" * 40, "tree": "1" * 40,
                                                   "fingerprint": "cf1:" + "f" * 64}, "reconciler")
        same = inh.promoted_drift(_st(log), "1" * 40)
        moved = inh.promoted_drift(_st(log), "2" * 40)
        unknown = inh.promoted_drift(_st(log), "unknown:scope")
        pf.append_pcc(log, _st(log), pf.PROMOTED, {"v": 1, "candidate": "snap:" + "2" * 40, "tree": "2" * 40,
                                                   "fingerprint": "cf1:" + "e" * 64}, "reconciler")
        newest = inh.promoted_drift(_st(log), "2" * 40)
        rule = (sw._moved_under_verification(SimpleNamespace(tree_before="1" * 40, tree_after="2" * 40))
                and not sw._moved_under_verification(SimpleNamespace(tree_before="1" * 40, tree_after="1" * 40))
                and sw._moved_under_verification(SimpleNamespace(tree_before="unknown:x", tree_after="unknown:x")))
        ok = none_yet is None and same is False and moved is True and unknown is None and newest is False and rule
        return ok, (f"no_event={none_yet} same={same} moved={moved} unknown={unknown} "
                    f"newest_promotion_wins={newest} moved_under_verification_rule={rule}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_hermetic():
    home = Path.home()
    ok = home.resolve() == _TMP_HOME.resolve() and home.resolve() != REAL_HOME.resolve()
    return ok, f"home={home.name}"


GATES = [
    ("V-INV-HERMETIC-HOME", gate_hermetic),
    ("V-INV-R12-CLOSURE", gate_r12_closure),
    ("V-INV-R12-NEEDS-GATE", gate_r12_needs_gate),
    ("V-INV-R12-CONTROL", gate_r12_control),
    ("V-CAND-SNAPSHOT-OID", gate_cand_oid),
    ("V-CAND-NO-SIDE-EFFECT", gate_cand_no_side_effect),
    ("V-CAND-UNKNOWN-ON-DOUBT", gate_cand_unknown_on_doubt),
    ("V-CAND-STABLE", gate_cand_stable),
    ("V-CAND-DRIFT", gate_cand_drift),
    ("V-INV-PROMOTED-PROJECTION", gate_promoted_projection),
    ("V-INV-INHERIT-OK", gate_inh_ok),
    ("V-INV-FALSE-REUSE", gate_inh_false_reuse),
    ("V-INV-UNKNOWN-NOT-CLEAN", gate_inh_unknown_not_clean),
    ("V-INV-FRESH-REQUIRED-NEVER", gate_inh_fresh_required_never),
    ("V-INV-OMITTED-WITHOUT-EVENT", gate_inh_omitted_without_event),
    ("V-INV-EVENT-DISAGREES", gate_inh_event_disagrees),
    ("V-INV-SWITCH-OFF", gate_inh_switch_off),
    ("V-INV-FRONTIER-CONSUMES-INHERITED", gate_inh_frontier_consumes),
    ("V-INV-SWEEP-E2E", gate_inh_sweep_e2e),
    ("V-INV-ALGEBRA-TRUTH", gate_inv_algebra),
    ("V-INV-NONAND-RUNS-FULL", gate_inv_nonand_runs),
    ("V-INV-VSET-SKIPS-ONLY-WITH-EVIDENCE", gate_inv_vset_evidence),
    ("V-INV-VSET-UNKNOWN-FULL", gate_inv_vset_unknown_full),
    ("V-INV-FRESH-ISLANDS", gate_inv_fresh_islands),
    ("V-INV-VSET-NO-OVERLAP", gate_inv_vset_no_overlap),
    ("V-INV-DRIFT-SUBSTRATE", gate_inv_drift_substrate),
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_INVALIDATION_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
