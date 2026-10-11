"""Semantics suite for the proof-conserving convergence seam (GSD X, Phase 2, plan 02-03+).

Drives modules/gsd_x/goal/proof.py through the real GoalLog: envelope, payload checks,
the CAS writer, transport, kill switches. Hermetic: HOME, USERPROFILE and GSDX_GOALS_ROOT
are redirected before any engine import; the live store is never touched.

Summary line: GSDX_PCC_SEMANTICS_PASS=n/m  threshold=m/m
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="pcc-sem-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="pcc-sem-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv        # noqa: E402
from modules.gsd_x.goal import log as gl                 # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402
from modules.gsd_x.mission import closure as mcl        # noqa: E402

SEM_REPO = "5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e"
PROOF_ABSENT = "RED-first: modules.gsd_x.goal.proof absent"
ENVELOPE_KEYS = {"seq", "type", "ts", "actor", "data", "prev_digest", "digest"}

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
    """A raise is a FAIL line, never an escape (audit G2): the summary line always prints."""
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- survive any gate body
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def load_proof():
    try:
        from modules.gsd_x.goal import proof  # noqa: PLC0415
        return proof
    except ImportError:
        return None


def sample_payloads() -> dict:
    pin = [["tools/gate.py", "9" * 64]]
    cand = "cf1:" + "c" * 64
    return {
        "obligation.contract": {
            "v": 1, "claim_id": "claim-1", "obligation": "ob-one", "combine": "AND",
            "elements": [{"oracle": "unit", "command": "python tools/gate.py", "gate_pin": pin,
                          "causal_paths": ["src"], "env_deps": [], "freshness_class": "unit",
                          "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}]},
        "proof.produced": {
            "v": 1, "claim_id": "claim-1", "candidate": cand, "binding": {"tree_hash": "git:" + "a" * 40},
            "revision": 1, "strength": "exact", "source": {"epoch": "ep-syn", "provider": "gate"}},
        "proof.inherited": {
            "v": 1, "claim_id": "claim-1", "certificate": "cert-1", "candidate": cand,
            "premises": {"claim": "equal", "oracle": "equal", "inputs": "equal", "env": "equal",
                         "gate_pin": "equal", "revision": "equal"}},
        "proof.invalidated": {
            "v": 1, "claim_id": "claim-1", "certificate": "cert-1", "reason": "premise changed"},
    }


def new_goal(name: str = "sem-goal"):
    """(GoalLog with one declared goal, state, base dir to remove)."""
    base = Path(tempfile.mkdtemp(prefix="pcc-sem-"))
    log = GoalLog(SEM_REPO, name, base=base)
    gc.declare(log, "Exercise the PCC seam", ["it works"], [], {"paths": ["src"]}, actor="founder")
    return log, gc.project(log), base


def gate_hermetic():
    home = Path.home()
    root = Path(os.environ["GSDX_GOALS_ROOT"]).resolve()
    ok = (home.resolve() == _TMP_HOME.resolve() and home.resolve() != REAL_HOME.resolve()
          and root.parent.parent == Path(tempfile.gettempdir()).resolve())
    return ok, f"home={home.name} goals_root_under_temp={root.parent.parent == Path(tempfile.gettempdir()).resolve()}"


def gate_envelope():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    log, state, base = new_goal("sem-envelope")
    try:
        data = sample_payloads()["proof.produced"]
        ledger = proof.append_pcc(log, state, proof.PRODUCED, data, "gate-receipt")
        ev = log.read()[-1]
        keys_ok = set(ev.to_dict()) == ENVELOPE_KEYS
        digest_ok = gl.event_digest(ev.to_dict()) == ev.digest
        rec = ledger.produced[-1] if ledger.produced else {}
        rec_ok = len(ledger.produced) == 1 and rec.get("seq") == ev.seq and rec.get("data") == data
        return keys_ok and digest_ok and rec_ok, f"keys={keys_ok} digest={digest_ok} ledger={rec_ok} seq={ev.seq}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def raw_append(log, type_: str, data: dict):
    return log.append(gc.project(log).last_seq + 1, type_, data, "pcc-sem")


def gate_malformed_raises():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    samples = sample_payloads()
    bad = []
    for t in proof.NEW_TYPES:
        log, _state, base = new_goal("sem-malformed")
        try:
            data = dict(samples[t])
            drop = next(k for k in proof.REQUIRED_FIELDS[t] if k != "v")
            del data[drop]
            ev = raw_append(log, t, data)
            try:
                proof.project_proofs(gc.project(log))
                bad.append(f"{t}: did not raise")
            except gl.GoalLogCorrupt as exc:
                if f"seq {ev.seq}: malformed {t}" not in str(exc):
                    bad.append(f"{t}: message {exc}")
        finally:
            shutil.rmtree(base, ignore_errors=True)
    return not bad, "four types raise GoalLogCorrupt naming seq and type" if not bad else "; ".join(bad)


def gate_legacy_readers():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    from modules.gsd_x.goal import convergence as cv, epoch as ep, evidence as evd, intervention as iv  # noqa: PLC0415
    samples = sample_payloads()
    log, _state, base = new_goal("sem-legacy")
    try:
        for t in proof.NEW_TYPES:
            data = dict(samples[t])
            del data[next(k for k in proof.REQUIRED_FIELDS[t] if k != "v")]
            raw_append(log, t, data)
        state = gc.project(log)
        ran = [
            cv.project_convergence(state) is not None,
            ep.project_epochs(state) is not None,
            iv.project_operator(state) is not None,
            evd.project_hypotheses(state) is not None,
            cv.goal_closure(state, "git:" + "a" * 40, ep.open_epochs(state)) is not None,
        ]
        return all(ran), f"projection,convergence,epochs,operator,hypotheses,closure ok={ran}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_higher_v():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    samples = sample_payloads()
    log, _state, base = new_goal("sem-higher-v")
    try:
        seqs = []
        for t in proof.NEW_TYPES:
            data = dict(samples[t])
            data["v"] = 2
            data["from_the_future"] = {"anything": [1, 2]}
            seqs.append(raw_append(log, t, data).seq)
        ledger = proof.project_proofs(gc.project(log))
        empty = not (ledger.contracts or ledger.produced or ledger.inherited or ledger.invalidated)
        return ledger.unsupported == seqs and empty, f"unsupported={ledger.unsupported} expected={seqs}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_writer_refuses():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    samples = sample_payloads()
    log, state, base = new_goal("sem-refuses")
    try:
        before = len(log.read())
        v2 = dict(samples[proof.PRODUCED])
        v2["v"] = 2
        broken = dict(samples[proof.PRODUCED])
        del broken["candidate"]
        cases = (("zz.other", {"v": 1}), (proof.PRODUCED, broken), (proof.PRODUCED, v2),
                 (proof.PRODUCED, "not-an-object"))
        seen = []
        for t, d in cases:
            try:
                proof.append_pcc(log, state, t, d, "pcc-sem")
                seen.append(f"{t}: accepted")
            except proof.ProofRefused:
                if len(log.read()) != before:
                    seen.append(f"{t}: event written despite refusal")
        control = proof.append_pcc(log, state, proof.PRODUCED, samples[proof.PRODUCED], "pcc-sem")
        ok = not seen and len(control.produced) == 1 and len(log.read()) == before + 1
        return ok, f"refused={len(cases) - len(seen)}/{len(cases)} control_appended={len(control.produced) == 1} {seen}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_writer_cas():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    samples = sample_payloads()
    log, stale, base = new_goal("sem-cas")
    try:
        proof.append_pcc(log, stale, proof.CONTRACT, samples[proof.CONTRACT], "pcc-sem")   # control: fresh state appends
        files = sorted(p.name for p in log.dir.iterdir())
        try:
            proof.append_pcc(log, stale, proof.PRODUCED, samples[proof.PRODUCED], "pcc-sem")
            return False, "stale state appended"
        except gl.LostRace:
            pass
        same = files == sorted(p.name for p in log.dir.iterdir())
        again = proof.append_pcc(log, gc.project(log), proof.PRODUCED, samples[proof.PRODUCED], "pcc-sem")
        return same and len(again.produced) == 1, f"lost_race_raised=True files_unchanged={same} fresh_retry_ok={len(again.produced) == 1}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_export_restore():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    import argparse  # noqa: PLC0415
    import subprocess  # noqa: PLC0415
    import gsd_x_goal as cli  # noqa: PLC0415
    from modules.gsd_x.goal import git_state  # noqa: PLC0415
    samples = sample_payloads()
    work = Path(tempfile.mkdtemp(prefix="pcc-sem-xr-"))
    repo = work / "repo"
    repo.mkdir()
    git = git_state.GIT_CANDIDATES[0]
    for args in (["init", "-q"], ["-c", "user.name=pcc", "-c", "user.email=noreply@anthropic.com",
                                  "commit", "-q", "--allow-empty", "-m", "root"]):
        subprocess.run([git, *args], cwd=repo, check=True, capture_output=True)
    root_a, root_b = work / "a" / "goals", work / "b" / "goals"
    saved = os.environ["GSDX_GOALS_ROOT"]
    try:
        os.environ["GSDX_GOALS_ROOT"] = str(root_a)
        rid = gl.repo_id(repo)
        log = GoalLog(rid, "g-xr")
        gc.declare(log, "Export and restore", ["it works"], [], {"paths": ["src"]}, actor="founder")
        for t in proof.NEW_TYPES:
            proof.append_pcc(log, gc.project(log), t, samples[t], "pcc-sem")
        digests_a = [e.digest for e in log.read()]
        ledger_a = proof.project_proofs(gc.project(log))
        out = work / "export.json"
        ns = argparse.Namespace(goal="g-xr", root=str(repo), actor="founder", to=str(out))
        rc_export = cli.cmd_export(ns)
        os.environ["GSDX_GOALS_ROOT"] = str(root_b)
        rc_restore = cli.cmd_restore(argparse.Namespace(**{"goal": "g-xr", "root": str(repo),
                                                           "actor": "founder", "from": str(out)}))
        log_b = GoalLog(rid, "g-xr")
        digests_b = [e.digest for e in log_b.read()]
        ledger_b = proof.project_proofs(gc.project(log_b))
        ok = (rc_export == 0 and rc_restore == 0 and digests_a == digests_b
              and ledger_a == ledger_b and len(digests_a) == 5)
        return ok, f"events={len(digests_a)} digests_equal={digests_a == digests_b} ledgers_equal={ledger_a == ledger_b}"
    finally:
        os.environ["GSDX_GOALS_ROOT"] = saved
        shutil.rmtree(work, ignore_errors=True)


ON_VALUES = (None, "", "on", "ON", " on ", "1", "true", "yes")
OFF_VALUES = ("off", "OFF", " off ", "0", "false", "of", "banana", "disabled")


def _with_env(name: str, value, fn):
    saved = os.environ.get(name)
    try:
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
        return fn()
    finally:
        if saved is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = saved


def gate_switch_parse():
    proof = load_proof()
    if proof is None or not hasattr(proof, "switch_on"):
        return False, "RED-first: proof.switch_on absent"
    bad = []
    for name in (proof.FRONTIER_SWITCH, proof.INHERITANCE_SWITCH):
        for v in ON_VALUES:
            if _with_env(name, v, lambda: proof.switch_on(name)) is not True:
                bad.append(f"{name}={v!r} should be ON")
        for v in OFF_VALUES:
            if _with_env(name, v, lambda: proof.switch_on(name)) is not False:
                bad.append(f"{name}={v!r} should be OFF")
    inh = [_with_env(proof.INHERITANCE_SWITCH, v, proof.inheritance_enabled) for v in ("off", "on")]
    if inh != [False, True]:
        bad.append(f"inheritance_enabled follows the switch: {inh}")
    return not bad, f"{len(ON_VALUES) + len(OFF_VALUES)} values x 2 switches {bad}"


def gate_switch_call_time():
    proof = load_proof()
    if proof is None or not hasattr(proof, "switch_on"):
        return False, "RED-first: proof.switch_on absent"
    name = proof.FRONTIER_SWITCH
    seq = [_with_env(name, v, lambda: proof.switch_on(name)) for v in ("off", "on", "0", "yes")]
    return seq == [False, True, False, True], f"answers={seq}"


# --- proof states, certificates, fingerprints (02-04) -----------------------------------

import ast  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402

TREE_A = "git:" + "a" * 40
TREE_B = "git:" + "b" * 40
GATE_PIN = (("tools/gate.py", "9" * 64),)
_NEEDS = "RED-first: proof state API absent"


def sat_goal(tree: str = TREE_A, gate_class: str = "unit", ob: str = "ob-one"):
    """(log, state, base) with one obligation SATISFIED by a verdict at `tree`."""
    log, state, base = new_goal("sem-states")
    cv.accept_obligation(log, state, ob, cv.OUTCOME, f"do {ob}", "python tools/gate.py", GATE_PIN,
                         "founder", gate_class=gate_class)
    st = gc.project(log)
    res = cv.satisfy(log, st, ob, mcl.Verdict("tools/gate.py", 0, "ok", tree, st.revision, gate_class,
                                              GATE_PIN), "founder", source={"epoch": "e", "provider": "gate"})
    if not res.allowed:
        raise RuntimeError(f"satisfy refused: {res.reason}")
    return log, gc.project(log), base


def _states(proof, state, cand, **kw):
    return {k: v["state"] for k, v in proof.proof_states(state, cand, **kw).items()}


def gate_truth_table():
    proof = load_proof()
    if proof is None or not hasattr(proof, "state_from_premises"):
        return False, _NEEDS
    cells = inh = bad = 0
    for combo in itertools.product((proof.EQUAL, proof.CHANGED, proof.UNKNOWN_OBS), repeat=len(proof.PREMISES)):
        obs = dict(zip(proof.PREMISES, combo))
        for ev, on in itertools.product((True, False), repeat=2):
            if proof.CHANGED in combo:
                want = proof.PS_STALE
            elif proof.UNKNOWN_OBS in combo or not on:
                want = proof.PS_UNKNOWN
            else:
                want = proof.PS_INHERITED if ev else proof.PS_UNKNOWN
            got = proof.state_from_premises(obs, ev, on)[0]
            cells += 1
            inh += got == proof.PS_INHERITED
            bad += got != want
    return cells == 2916 and inh == 1 and bad == 0, f"cells={cells} INHERITED={inh} disagreements={bad}"


def gate_no_event():
    proof = load_proof()
    if proof is None or not hasattr(proof, "state_from_premises"):
        return False, _NEEDS
    allq = {p: proof.EQUAL for p in proof.PREMISES}
    no_ev = proof.state_from_premises(allq, False, True)[0]
    ctl = proof.state_from_premises(allq, True, True)[0]
    empty = proof.state_from_premises({}, True, True)[0]
    return (no_ev, ctl, empty) == (proof.PS_UNKNOWN, proof.PS_INHERITED, proof.PS_UNKNOWN), f"no_event={no_ev} control={ctl} empty_premise_set={empty}"


def gate_switch_off_legacy():
    proof = load_proof()
    if proof is None or not hasattr(proof, "proof_states"):
        return False, _NEEDS
    log, state, base = sat_goal()
    try:
        before = _states(proof, state, TREE_A)
        proof.append_pcc(log, state, proof.PRODUCED, {
            "v": 1, "claim_id": next(iter(proof.proof_states(state, TREE_A).values()))["claim_id"],
            "candidate": TREE_B, "binding": {"scheme": "tree", "value": TREE_B},
            "revision": state.revision, "strength": "unit", "source": {"provider": "gate"}}, "founder")
        st2 = gc.project(log)
        proof.append_pcc(log, st2, proof.INHERITED_EV, {
            "v": 1, "claim_id": "x", "certificate": "c", "candidate": TREE_B, "premises": {}}, "founder")
        st3 = gc.project(log)
        off = _with_env(proof.INHERITANCE_SWITCH, "off", lambda: _states(proof, st3, TREE_A))
        return off == before, f"legacy={before} switch_off_with_events={off}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_unknown_tree():
    proof = load_proof()
    if proof is None or not hasattr(proof, "proof_states"):
        return False, _NEEDS
    from modules.gsd_x.goal import reconcile as rc  # noqa: PLC0415
    unk = "unknown:not-a-git-tree"
    log, state, base = sat_goal(tree=unk)
    try:
        o = next(iter(cv.project_convergence(state).obligations.values()))
        ctx = type("C", (), {"tree_hash": unk, "state": state})()
        legacy = rc._needs_a_gate_here(o, ctx)
        got = _states(proof, state, unk)
        other = _states(proof, state, TREE_A)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    log2, state2, base2 = sat_goal(tree=TREE_A)
    try:
        known = _states(proof, state2, TREE_A)
    finally:
        shutil.rmtree(base2, ignore_errors=True)
    ok = (legacy == "" and set(got.values()) == {proof.PS_UNKNOWN} and set(other.values()) == {proof.PS_UNKNOWN}
          and set(known.values()) == {proof.PS_FRESH})
    return ok, f"legacy_reason={legacy!r} unknown_vs_unknown={got} unknown_vs_known={other} control_known_tree={known}"


def gate_superseded():
    proof = load_proof()
    if proof is None or not hasattr(proof, "supersedes"):
        return False, _NEEDS
    b = {"scheme": "tree", "value": TREE_A}

    def c(strength, binding=b, claim="k1"):
        return {"claim_id": claim, "binding": binding, "strength": strength}
    cases = {
        "integration>unit": proof.supersedes(c("integration"), c("unit")) is True,
        "unit!>integration": proof.supersedes(c("unit"), c("integration")) is False,
        "equal-strength-same-binding": proof.supersedes(c("unit"), c("unit")) is True,
        "empty-class": proof.supersedes(c(""), c("unit")) is False and proof.supersedes(c("unit"), c("")) is False,
        "other-claim": proof.supersedes(c("live"), c("unit", claim="k2")) is False,
        "unknown-bindings": proof.supersedes(c("unit", {"scheme": "tree", "value": "unknown:x"}),
                                             c("unit", {"scheme": "tree", "value": "unknown:x"})) is False,
    }
    return all(cases.values()), str(cases)


def gate_order_stable():
    proof = load_proof()
    if proof is None or not hasattr(proof, "proof_states"):
        return False, _NEEDS
    log, state, base = sat_goal()
    try:
        cv.accept_obligation(log, state, "ob-two", cv.OUTCOME, "do two", "python tools/gate.py", GATE_PIN, "founder")
        st = gc.project(log)
        a = json.dumps(proof.proof_states(st, TREE_A), sort_keys=True, separators=(",", ":"))
        b = json.dumps(proof.proof_states(st, TREE_A), sort_keys=True, separators=(",", ":"))
        order = list(proof.proof_states(st, TREE_A))
        return a == b and order == list(cv.project_convergence(st).obligations), f"order={order}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_empty():
    proof = load_proof()
    if proof is None or not hasattr(proof, "causal_fingerprint"):
        return False, _NEEDS
    log, state, base = new_goal("sem-empty")
    root = Path(tempfile.mkdtemp(prefix="pcc-fp-"))
    try:
        cv.accept_obligation(log, state, "ob-one", cv.OUTCOME, "t", "python tools/gate.py", GATE_PIN, "founder")
        st = gc.project(log)
        none = _states(proof, st, TREE_A)
        fp = proof.causal_fingerprint(root, [])
        return set(none.values()) == {proof.NOT_APPLICABLE} and fp.startswith("unknown:"), f"no_verdict={none} empty_paths={fp}"
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(root, ignore_errors=True)


def _cert(proof, **over):
    base = {"claim": "c1", "revision": 1, "gate_pin": [["a.py", "9" * 64]], "fingerprint": "cf1:" + "1" * 64,
            "environment": "env1:" + "2" * 64, "policy": proof.POLICY_VERSION, "ts": 1000.0,
            "freshness_class": "DETERMINISTIC", "env_deps": []}
    base.update(over)
    return base


def _cert_state(proof, cert_over=None, cur_over=None, now=1000.0, event=True):
    cert, cur = _cert(proof, **(cert_over or {})), _cert(proof, **(cur_over or {}))
    obs = proof.observe_premises(cert, cur, now)
    return obs, proof.state_from_premises(obs, event, True)[0]


def _need(*names):
    proof = load_proof()
    return proof if proof is not None and all(hasattr(proof, n) for n in names) else None


def gate_cert_claim():
    proof = _need("observe_premises", "claim_id")
    if proof is None:
        return False, _NEEDS
    a = cv.GoalObligation("ob", cv.OUTCOME, "t", "python a.py", GATE_PIN, "r", gate_class="unit")
    b = cv.GoalObligation("ob", cv.OUTCOME, "t", "python b.py", GATE_PIN, "r", gate_class="unit")
    same = proof.claim_id(a) == proof.claim_id(cv.GoalObligation("ob", cv.OUTCOME, "t", "python a.py", GATE_PIN, "r", gate_class="unit"))
    _, st = _cert_state(proof, {"claim": proof.claim_id(a)}, {"claim": proof.claim_id(b)})
    _, ctl = _cert_state(proof, {"claim": proof.claim_id(a)}, {"claim": proof.claim_id(a)})
    return same and proof.claim_id(a) != proof.claim_id(b) and st == proof.PS_STALE and ctl == proof.PS_INHERITED, f"reaccept={st} control={ctl}"


def gate_cert_pin_scheme():
    proof = _need("observe_premises")
    if proof is None:
        return False, _NEEDS
    obs, st = _cert_state(proof, {"gate_pin": [["a.py", "blob:" + "9" * 40]]}, {"gate_pin": [["a.py", "9" * 64]]})
    mixed, mst = _cert_state(proof, {"gate_pin": [["a.py", "blob:" + "9" * 40], ["b.py", "9" * 64]]}, {})
    return obs["gate_pin"] == proof.UNKNOWN_OBS and st == proof.PS_UNKNOWN and mixed["gate_pin"] == proof.UNKNOWN_OBS, f"blob_vs_raw={st} mixed={mst}"


def gate_cert_revision():
    proof = _need("observe_premises")
    if proof is None:
        return False, _NEEDS
    obs, st = _cert_state(proof, {"revision": 1}, {"revision": 2})
    return obs["revision"] == proof.CHANGED and st == proof.PS_STALE, f"revision_changed={st}"


def gate_cert_policy():
    proof = _need("observe_premises")
    if proof is None:
        return False, _NEEDS
    obs, st = _cert_state(proof, {"policy": 0}, {"policy": 1})
    return proof.POLICY_VERSION == 1 and obs["policy"] == proof.CHANGED and st == proof.PS_STALE, f"policy_bump={st}"


def gate_cert_env():
    proof = _need("observe_premises")
    if proof is None:
        return False, _NEEDS
    sens = {"freshness_class": "ENVIRONMENT_SENSITIVE"}
    obs, st = _cert_state(proof, {**sens, "env_deps": []}, {**sens, "env_deps": []})
    obs2, st2 = _cert_state(proof, {**sens, "env_deps": ["python"]}, {**sens, "env_deps": ["python"]})
    return obs["environment"] == proof.UNKNOWN_OBS and st == proof.PS_UNKNOWN and st2 == proof.PS_INHERITED, f"undeclared={st} declared_control={st2}"


def gate_cert_future():
    proof = _need("observe_premises")
    if proof is None:
        return False, _NEEDS
    _, st = _cert_state(proof, {"ts": 1301.0}, {}, now=1000.0)
    _, edge = _cert_state(proof, {"ts": 1300.0}, {}, now=1000.0)
    return proof.FUTURE_SKEW_S == 300 and st == proof.PS_UNKNOWN and edge == proof.PS_INHERITED, f"future={st} at_skew_edge={edge}"


def gate_fp_absent():
    proof = _need("causal_fingerprint")
    if proof is None:
        return False, _NEEDS
    root = Path(tempfile.mkdtemp(prefix="pcc-fp-"))
    try:
        (root / "a.txt").write_bytes(b"x\n")
        present = proof.causal_fingerprint(root, ["a.txt"])
        absent = proof.causal_fingerprint(root, ["a.txt", "missing.txt"])
        again = proof.causal_fingerprint(root, ["a.txt"])
        return present.startswith("cf1:") and absent.startswith("cf1:") and present != absent and present == again, f"present={present[:12]} absent={absent[:12]}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def gate_fp_outside():
    proof = _need("causal_fingerprint")
    if proof is None:
        return False, _NEEDS
    root = Path(tempfile.mkdtemp(prefix="pcc-fp-"))
    outside = Path(tempfile.mkdtemp(prefix="pcc-fp-out-"))
    try:
        (root / "a.txt").write_bytes(b"x\n")
        (outside / "o.txt").write_bytes(b"y\n")
        got = {"dotdot": proof.causal_fingerprint(root, ["../x"]),
               "nested_dotdot": proof.causal_fingerprint(root, ["a.txt", "sub/../../x"]),
               "absolute": proof.causal_fingerprint(root, [str(outside / "o.txt")])}
        ctl = proof.causal_fingerprint(root, ["a.txt"])
        return all(v.startswith("unknown:") for v in got.values()) and ctl.startswith("cf1:"), f"refused={sorted(got)} control={ctl[:4]}"
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


def gate_fp_empty():
    proof = _need("causal_fingerprint", "environment_fingerprint")
    if proof is None:
        return False, _NEEDS
    root = Path(tempfile.mkdtemp(prefix="pcc-fp-"))
    try:
        (root / "a.txt").write_bytes(b"x")
        e1, e2 = proof.environment_fingerprint(["python"]), proof.environment_fingerprint(["node"])
        return (proof.causal_fingerprint(root, []).startswith("unknown:")
                and proof.causal_fingerprint(root, ["a.txt"]).startswith("cf1:")
                and e1.startswith("env1:") and e1 != e2 and e1 == proof.environment_fingerprint(["python"])), f"env={e1[:10]}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def gate_fp_eol():
    proof = _need("causal_fingerprint")
    if proof is None:
        return False, _NEEDS
    r1, r2 = Path(tempfile.mkdtemp(prefix="pcc-fp-")), Path(tempfile.mkdtemp(prefix="pcc-fp-"))
    try:
        (r1 / "a.txt").write_bytes(b"one\r\ntwo\r\n")
        (r2 / "a.txt").write_bytes(b"one\ntwo\n")
        (r2 / "b.txt").write_bytes(b"other\n")
        (r1 / "b.txt").write_bytes(b"different\n")
        same = proof.causal_fingerprint(r1, ["a.txt"]) == proof.causal_fingerprint(r2, ["a.txt"])
        diff = proof.causal_fingerprint(r1, ["b.txt"]) != proof.causal_fingerprint(r2, ["b.txt"])
        return same and diff, f"crlf_equals_lf={same} content_change_detected={diff}"
    finally:
        shutil.rmtree(r1, ignore_errors=True)
        shutil.rmtree(r2, ignore_errors=True)


def scan_disposition(source: str) -> list:
    """Offences against 'state is a projection': a disposition write or a disposition call."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            hits += [f"assign disposition L{node.lineno}" for t in targets
                     if isinstance(t, ast.Attribute) and t.attr == "disposition"]
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name == "disposition_obligation":
                hits.append(f"call {name} L{node.lineno}")
    return hits


def gate_not_in_disposition():
    proof = _need("proof_states")
    if proof is None:
        return False, _NEEDS
    src = Path(proof.__file__).read_text(encoding="utf-8")
    real = scan_disposition(src)
    ctl = scan_disposition('def f(o):\n    o.disposition = "STALE"\n    cv.disposition_obligation(o)\n')
    return real == [] and len(ctl) == 2, f"proof.py offences={real} control_flags={len(ctl)}"


def gate_produced_unknown_binding():
    proof = _need("proof_states")
    if proof is None:
        return False, _NEEDS
    unk = "unknown:not-a-git-tree"
    log, state, base = sat_goal(tree=TREE_A)
    try:
        cid = next(iter(proof.proof_states(state, TREE_A).values()))["claim_id"]
        payload = {"v": 1, "claim_id": cid, "candidate": unk, "binding": {"scheme": "tree", "value": unk},
                   "revision": state.revision, "strength": "unit", "source": {"provider": "gate"}}
        proof.append_pcc(log, state, proof.PRODUCED, payload, "founder")
        st = gc.project(log)
        got = _states(proof, st, unk)
        ctl = _states(proof, st, TREE_A)
        return set(got.values()) == {proof.PS_UNKNOWN} and set(ctl.values()) == {proof.PS_FRESH}, f"unknown_binding={got} control={ctl}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_produced_without_satisfied():
    proof = _need("proof_states")
    if proof is None:
        return False, _NEEDS
    log, state, base = new_goal("sem-prod")
    try:
        cv.accept_obligation(log, state, "ob-one", cv.OUTCOME, "t", "python tools/gate.py", GATE_PIN, "founder")
        st = gc.project(log)
        cid = next(iter(proof.proof_states(st, TREE_A).values()))["claim_id"]
        proof.append_pcc(log, st, proof.PRODUCED, {
            "v": 1, "claim_id": cid, "candidate": TREE_A, "binding": {"scheme": "tree", "value": TREE_A},
            "revision": st.revision, "strength": "unit", "source": {"provider": "gate"}}, "founder")
        got = _states(proof, gc.project(log), TREE_A)
        return set(got.values()) == {proof.NOT_APPLICABLE}, f"produced_for_unsatisfied={got}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_old_revision_unknown():
    proof = _need("proof_states")
    if proof is None:
        return False, _NEEDS
    log, state, base = new_goal("sem-rev")
    try:
        old = state.revision - 1 if isinstance(state.revision, int) else "older"
        raw_append(log, cv.OB_ACCEPTED, {"id": "ob-old", "plane": cv.OUTCOME, "text": "t", "done_gate": "python g.py",
                                         "gate_pin": [list(p) for p in GATE_PIN], "revision": old, "gate_class": "unit"})
        raw_append(log, cv.OB_SATISFIED, {"id": "ob-old", "verdict": {"tree_hash": TREE_A, "revision": state.revision,
                                                                       "gate_class": "unit", "gate": "tools/gate.py"},
                                          "source": {}})
        got = _states(proof, gc.project(log), TREE_A)
        return got == {"ob-old": proof.PS_UNKNOWN}, f"older_obligation_revision={got}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    run_gate("V-PCC-HERMETIC-HOME", gate_hermetic)
    run_gate("V-PCC-ENVELOPE", gate_envelope)
    run_gate("V-PCC-CONTRACT-MALFORMED-RAISES", gate_malformed_raises)
    run_gate("V-PCC-LEGACY-READERS-DO-NOT-RAISE", gate_legacy_readers)
    run_gate("V-PCC-CONTRACT-HIGHER-V-UNKNOWN", gate_higher_v)
    run_gate("V-PCC-WRITER-REFUSES", gate_writer_refuses)
    run_gate("V-PCC-WRITER-CAS", gate_writer_cas)
    run_gate("V-PCC-EXPORT-RESTORE-ROUNDTRIP", gate_export_restore)
    run_gate("V-PCC-SWITCH-PARSE", gate_switch_parse)
    run_gate("V-PCC-SWITCH-CALL-TIME", gate_switch_call_time)
    for name, fn in (("V-PCC-STATE-TRUTH-TABLE", gate_truth_table),
                     ("V-PCC-STATE-NO-EVENT-NOT-INHERITED", gate_no_event),
                     ("V-PCC-SWITCH-OFF-IS-LEGACY", gate_switch_off_legacy),
                     ("V-PCC-STATE-UNKNOWN-TREE", gate_unknown_tree),
                     ("V-PCC-STATE-SUPERSEDED-STRENGTH", gate_superseded),
                     ("V-PCC-STATE-ORDER-STABLE", gate_order_stable),
                     ("V-PCC-STATE-EMPTY", gate_empty),
                     ("V-PCC-CERT-CLAIM-REACCEPT", gate_cert_claim),
                     ("V-PCC-CERT-GATE-PIN-SCHEME", gate_cert_pin_scheme),
                     ("V-PCC-CERT-REVISION", gate_cert_revision),
                     ("V-PCC-CERT-POLICY-BUMP", gate_cert_policy),
                     ("V-PCC-CERT-ENV-UNDECLARED", gate_cert_env),
                     ("V-PCC-CERT-FUTURE-DATED", gate_cert_future),
                     ("V-PCC-FINGERPRINT-ABSENT", gate_fp_absent),
                     ("V-PCC-FINGERPRINT-OUTSIDE-ROOT", gate_fp_outside),
                     ("V-PCC-FINGERPRINT-EMPTY", gate_fp_empty),
                     ("V-PCC-FINGERPRINT-EOL", gate_fp_eol),
                     ("V-PCC-STATE-NOT-IN-DISPOSITION", gate_not_in_disposition),
                     ("V-PCC-STATE-PRODUCED-UNKNOWN-BINDING", gate_produced_unknown_binding),
                     ("V-PCC-STATE-PRODUCED-WITHOUT-SATISFIED", gate_produced_without_satisfied),
                     ("V-PCC-STATE-OLD-REVISION-UNKNOWN", gate_old_revision_unknown)):
        run_gate(name, fn)
    total = passes + fails
    print(f"\nGSDX_PCC_SEMANTICS_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
