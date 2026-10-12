"""Certificate suite for proof-conserving convergence (GSD X, Phase 4, plan 04-02).

Drives the real `sweep._apply_verdicts` producer: a successful gate receipt writes one causal
`proof.produced`; a candidate that moved while the gate ran writes none and invalidates the
live certificate. Hermetic: HOME, USERPROFILE and GSDX_GOALS_ROOT are redirected first.

Summary line: GSDX_CERTIFICATE_PASS=n/m  threshold=m/m
"""
from __future__ import annotations

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
_TMP_HOME = Path(tempfile.mkdtemp(prefix="cert-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="cert-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import proof                     # noqa: E402
from modules.gsd_x.goal import sweep                     # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402

REPO_ID = "7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b7b"
PIN = (("tools/gate.py", "9" * 64),)
TREE_A, TREE_B = "work:" + "a" * 40, "work:" + "b" * 40
SWITCH = proof.INHERITANCE_SWITCH

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
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- survive any gate body
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def _st(log):
    return gc.project(log)


class World:
    """One goal with one accepted obligation, a scope directory, and (optionally) a typed contract."""

    def __init__(self, name: str, typed: bool = True):
        self.base = Path(tempfile.mkdtemp(prefix="cert-"))
        self.root = Path(tempfile.mkdtemp(prefix="cert-root-"))
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8", newline="\n")
        self.log = GoalLog(REPO_ID, name, base=self.base)
        gc.declare(self.log, "Certify", ["it works"], [], {"paths": ["src"]}, actor="founder")
        for plane in cv.PLANES:
            cv.set_plane(self.log, _st(self.log), plane, plane in cv.ALWAYS,
                         "" if plane in cv.ALWAYS else "not claimed", "founder")
        cv.accept_obligation(self.log, _st(self.log), "ob-one", cv.OUTCOME, "do it",
                             "python tools/gate.py", PIN, "founder", gate_class="unit")
        self.cid = proof.claim_id(cv.project_convergence(_st(self.log)).obligations["ob-one"])
        if typed:
            proof.append_pcc(self.log, _st(self.log), proof.CONTRACT, {
                "v": 1, "claim_id": self.cid, "obligation": "ob-one", "combine": "AND",
                "elements": [{"oracle": "unit", "command": "python tools/gate.py",
                              "gate_pin": [list(p) for p in PIN], "causal_paths": ["src"],
                              "env_deps": [], "freshness_class": "DETERMINISTIC", "risk_tags": [],
                              "nondeterministic": False, "inheritability": "inheritable"}]}, "founder")

    def harvest(self, tree_before=TREE_A, tree_after=TREE_A, verdict_tree=None, epoch="ep-1"):
        st = _st(self.log)
        v = {"gate": "tools/gate.py", "exit_status": 0, "observed": "ok",
             "tree_hash": tree_after if verdict_tree is None else verdict_tree,
             "revision": st.revision, "gate_class": "unit", "gate_pin": [list(p) for p in PIN]}
        receipt = SimpleNamespace(verdicts=[v], tree_before=tree_before, tree_after=tree_after)
        record = SimpleNamespace(spec={"obligation": "ob-one"}, epoch_id=epoch, provider="gate",
                                 handle={"h": 1})
        return sweep._apply_verdicts(self.log, receipt, record, "sweep", root=self.root)

    def ledger(self):
        return proof.project_proofs(_st(self.log))

    def types(self):
        return [e.type for e in _st(self.log).events]

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)
        shutil.rmtree(self.root, ignore_errors=True)


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


def gate_produced_on_satisfy():
    w = World("cert-a")
    try:
        lines = w.harvest()
        led = w.ledger()
        d = led.produced[-1]["data"] if led.produced else {}
        prem = d.get("premises") or {}
        want_fp = proof.causal_fingerprint(w.root, ["src"])
        ok = (len(led.produced) == 1 and set(prem) == set(proof.PREMISES)
              and d.get("freshness_class") == proof.DETERMINISTIC and d.get("env_deps") == []
              and isinstance(d.get("contract_hash"), str) and d["contract_hash"]
              and d.get("binding") == {"scheme": "causal", "value": want_fp}
              and prem.get("fingerprint") == want_fp and prem.get("claim") == w.cid
              and d.get("claim_id") == w.cid and d.get("candidate") == TREE_A
              and d.get("strength") == "unit"
              and proof.certificate_id(w.cid, led.produced[-1]["seq"]).startswith("cert:")
              and "SATISFIED" in " ".join(lines))
        return ok, f"produced={len(led.produced)} binding={d.get('binding', {}).get('scheme')} premises={sorted(prem)}"
    finally:
        w.close()


def gate_only_after_satisfy():
    w = World("cert-b")
    try:
        w.harvest(verdict_tree="")          # a verdict naming no tree is refused by evaluate
        types = w.types()
        ok = proof.PRODUCED not in types and cv.OB_SATISFIED not in types
        return ok, f"types={sorted(set(types) & {proof.PRODUCED, cv.OB_SATISFIED})}"
    finally:
        w.close()


def gate_moved_under_verification():
    cases = {}
    for label, before, after in (("tree-moved", TREE_A, TREE_B), ("before-unknown", "", TREE_A),
                                 ("after-unknown", TREE_A, "unknown:not-a-git-tree")):
        w = World("cert-c-" + label)
        try:
            w.harvest()                                     # a live certificate at TREE_A
            live = w.ledger().produced[-1]["seq"]
            n_prod = len(w.ledger().produced)
            w.harvest(tree_before=before, tree_after=after, verdict_tree=TREE_B if after != TREE_A else TREE_A,
                      epoch="ep-2")
            led = w.ledger()
            inv = [i for i in led.invalidated
                   if i["data"].get("certificate") == proof.certificate_id(w.cid, live)]
            cases[label] = (len(led.produced) == n_prod and len(inv) == 1
                            and "candidate moved under verification" in inv[0]["data"].get("reason", ""))
        finally:
            w.close()
    w = World("cert-c-legacy")
    try:
        w.harvest(tree_before=TREE_A, tree_after=TREE_B)
        legacy_ok = cv.OB_SATISFIED in w.types() and proof.PRODUCED not in w.types()
    finally:
        w.close()
    return all(cases.values()) and legacy_ok, f"cases={cases} legacy_satisfied_unchanged={legacy_ok}"


def gate_binding_scheme():
    typed, legacy = World("cert-d1", typed=True), World("cert-d2", typed=False)
    try:
        typed.harvest()
        legacy.harvest()
        bt = typed.ledger().produced[-1]["data"]["binding"]["scheme"]
        bl = legacy.ledger().produced[-1]["data"]["binding"]["scheme"]
        shutil.rmtree(typed.root / "src")
        typed.harvest(epoch="ep-3")
        return bt == "causal" and bl == "tree", f"typed={bt} legacy_no_causal_paths={bl}"
    finally:
        typed.close()
        legacy.close()


def gate_switch_off():
    on, off = World("cert-e1"), World("cert-e2")
    try:
        with_switch("off", off.harvest)
        with_switch(None, on.harvest)
        extra = [t for t in on.types() if t not in off.types()]
        ok = proof.PRODUCED not in off.types() and extra == [proof.PRODUCED]
        return ok, f"off_has_produced={proof.PRODUCED in off.types()} on_adds={extra}"
    finally:
        on.close()
        off.close()


def gate_law_conservation():
    w = World("cert-f")
    try:
        w.harvest()
        w.harvest(epoch="ep-2")             # the same claim at the same binding, harvested again
        led = w.ledger()
        idempotent = len(led.produced) == 1 and proof.law_proof_conservation(led) == []
        d = dict(led.produced[0]["data"])
        proof.append_pcc(w.log, _st(w.log), proof.PRODUCED, d, "hand")
        tripped = bool(proof.law_proof_conservation(w.ledger()))
        return idempotent and tripped, f"re-harvest_writes_one={idempotent} duplicate_trips_law={tripped}"
    finally:
        w.close()


GATES = [
    ("V-CERT-PRODUCED-ON-SATISFY", gate_produced_on_satisfy),
    ("V-CERT-ONLY-AFTER-SATISFY", gate_only_after_satisfy),
    ("V-CERT-MOVED-UNDER-VERIFICATION", gate_moved_under_verification),
    ("V-CERT-BINDING-SCHEME", gate_binding_scheme),
    ("V-CERT-SWITCH-OFF", gate_switch_off),
    ("V-CERT-LAW-CONSERVATION", gate_law_conservation),
]


def main() -> int:
    home_ok = Path.home().resolve() == _TMP_HOME.resolve() != REAL_HOME.resolve()
    check("V-CERT-HERMETIC-HOME", home_ok, f"home={Path.home().name}")
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_CERTIFICATE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
