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
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_INVALIDATION_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
