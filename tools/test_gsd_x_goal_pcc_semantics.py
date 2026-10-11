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
from modules.gsd_x.goal import log as gl                 # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402

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
    total = passes + fails
    print(f"\nGSDX_PCC_SEMANTICS_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
