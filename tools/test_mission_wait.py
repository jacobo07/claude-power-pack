#!/usr/bin/env python3
"""V-WAIT-* gates for the WAIT_ON_RESOURCE vocabulary in tools/mission_recovery.py (ccr-v5 phase 3).

Every refusal is paired with an admitted control inside its gate, so a validator that refuses everything or a
decision that never resumes would fail the controls. The last gate builds mutants of a TEMP COPY of the module
by exact text replacement and requires each to turn its named gate red; the loaded file is never mutated.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
SRC = TOOLS / "mission_recovery.py"
T0 = 1_800_000_000.0
TMO = T0 + 3600.0


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def good_row(paths=("vault/knowledge_base/ukdl-universal.md",)):
    return {
        "wait_id": "w-1", "kind": "WAIT_ON_RESOURCE", "state": "OPEN", "goal": "ccr", "wu": "P3-merge",
        "opened_at": T0, "timeout_at": TMO, "live_head_at_open": "77e1cbf0",
        "resources": [{"path": p, "writer": {"verdict": "LIVE"}} for p in paths],
        "expected_event": ["COMMIT", "LEASE_RELEASE", "WRITER_DEAD"],
        "resume_action": {"kind": "land_worktree", "strategy": "merge", "worktree": "wt/ccr-v5",
                          "live": "main", "branch": "ccr/v5"},
        "validation": {"tests": ["python tools/test_lease.py"], "rollback": "any_red", "baseline_red": []},
    }


def ev(dirty=True, committed=False, lease=None, writer="LIVE"):
    return {"dirty": dirty, "committed_since_open": committed, "lease": lease, "writer": writer}


def gates(m):
    """name -> (ok, evidence). Decision gates are separable so the mutants can re-run them."""
    P = "vault/knowledge_base/ukdl-universal.md"
    row = good_row()
    out = {}
    wd, vr = m.wait_decision, m.validate_wait_row

    # --- validator gates
    out["V-WAIT-VALID-ROW"] = (vr(row) == [] and vr(good_row(("a/b.md", "c.py"))) == [], f"problems={vr(row)}")

    miss_ok, miss_ev = True, []
    for k in ("goal", "wu", "resources", "expected_event", "resume_action", "validation", "timeout_at"):
        r = copy.deepcopy(row)
        del r[k]
        pr = vr(r)
        hit = any(p.startswith(k) for p in pr)
        miss_ok = miss_ok and hit
        miss_ev.append(f"{k}={'named' if hit else 'MISSED'}")
    out["V-WAIT-REFUSES-MISSING-FIELD"] = (miss_ok and vr(row) == [], " ".join(miss_ev))

    bad = copy.deepcopy(row)
    bad["resume_action"]["kind"] = "shell"
    bad2 = copy.deepcopy(row)
    bad2["resume_action"]["command"] = "rm -rf /"
    out["V-WAIT-REFUSES-FOREIGN-ACTION"] = (
        any("resume_action.kind" in p for p in vr(bad)) and vr(row)[:1] == [] and
        row["resume_action"]["kind"] in m.RESUME_KINDS and "command" not in "".join(m.RESUME_KINDS),
        f"foreign={vr(bad)} control_kind={row['resume_action']['kind']} extra_key_does_not_widen={vr(bad2)}")

    esc_ok, esc_ev = True, []
    for bad_path in ("/etc/passwd", "C:/x/y.md", "C:\\x\\y.md", "../outside.md", "a/../../b.md", "a\\b.md", ""):
        r = copy.deepcopy(row)
        r["resources"][0]["path"] = bad_path
        r2 = copy.deepcopy(row)
        r2["resume_action"]["union"] = [bad_path]
        both = bool(vr(r)) and bool(vr(r2))
        esc_ok = esc_ok and both
        esc_ev.append(f"{bad_path!r}={'refused' if both else 'ADMITTED'}")
    ctl = copy.deepcopy(row)
    ctl["resources"][0]["path"] = "vault/a/b.md"
    ctl["resume_action"]["union"] = ["vault/knowledge_base/ukdl-universal.md", "x/y.md"]
    ctl_absent = vr(row) == []
    out["V-WAIT-REFUSES-ESCAPING-PATH"] = (esc_ok and vr(ctl) == [] and ctl_absent, " ".join(esc_ev))

    nr = copy.deepcopy(row)
    nr["validation"]["rollback"] = "on_red_only"
    nr2 = copy.deepcopy(row)
    del nr2["validation"]["rollback"]
    out["V-WAIT-REFUSES-NON-ROLLBACK"] = (
        any("rollback" in p for p in vr(nr)) and any("rollback" in p for p in vr(nr2)) and vr(row) == [],
        f"{vr(nr)} / {vr(nr2)}")

    et_ok = True
    for bad_tests in ([], "python x.py", [""], [1], None):
        r = copy.deepcopy(row)
        r["validation"]["tests"] = bad_tests
        et_ok = et_ok and any("tests" in p for p in vr(r))
    out["V-WAIT-REFUSES-EMPTY-TESTS"] = (et_ok and vr(row) == [], f"control={vr(row)}")

    t1 = copy.deepcopy(row)
    t1["timeout_at"] = 3600
    t2 = copy.deepcopy(row)
    t2["timeout_at"] = T0 - 1
    t3 = copy.deepcopy(row)
    t3["timeout_at"] = "2026-10-16"
    out["V-WAIT-TIMEOUT-ABSOLUTE"] = (
        all(any("timeout_at" in p for p in vr(r)) for r in (t1, t2, t3)) and vr(row) == [],
        f"relative={vr(t1)} before_open={vr(t2)} str={vr(t3)}")

    # --- decision gates
    d = wd(row, {P: ev(True, writer="LIVE"), "other_paths": 3}, T0 + 10)
    out["V-WAIT-HOLDS-WHILE-DIRTY-LIVE-WRITER"] = (
        d["action"] == "WAIT" and d["blocked"] == [P] and
        wd(row, {P: ev(False, True), "other_paths": 3}, T0 + 10)["action"] == "RESUME",
        f"dirty_live={d['action']}")

    dn = wd(row, {P: ev(None, writer="DEAD"), "other_paths": 3}, T0 + 10)
    dm = wd(row, {"other_paths": 3}, T0 + 10)
    out["V-WAIT-UNMEASURED-IS-NOT-FREE"] = (
        dn["action"] != "RESUME" and dm["action"] != "RESUME" and dm["blocked"] == [P] and dn["action"] == "WAIT" and
        wd(row, {P: ev(False)}, T0 + 10)["action"] == "RESUME",
        f"dirty_none={dn['action']} missing_entry={dm['action']}")

    rc = wd(row, {P: ev(False, True)}, T0 + 10)
    out["V-WAIT-RESUME-ON-COMMIT"] = (
        rc["action"] == "RESUME" and rc["event"] == "COMMIT" and rc["cleared"] == [P] and
        wd(row, {P: ev(True, True)}, T0 + 10)["action"] == "WAIT",
        f"{rc['action']}/{rc['event']}")

    rl = wd(row, {P: ev(False, False, {"free": True, "state": "RELEASED", "holder": "pane-9"})}, T0 + 10)
    out["V-WAIT-RESUME-ON-LEASE-RELEASE"] = (
        rl["action"] == "RESUME" and rl["event"] == "LEASE_RELEASE" and
        wd(row, {P: ev(False)}, T0 + 10)["event"] == "CLEARED",
        f"{rl['action']}/{rl['event']}")

    lh = wd(row, {P: ev(False, True, {"free": False, "state": "ACTIVE", "holder": "pane-9"})}, T0 + 10)
    out["V-WAIT-LEASE-HELD-BLOCKS"] = (
        lh["action"] == "WAIT" and lh["blocked"] == [P] and
        wd(row, {P: ev(False, True, {"free": True, "state": "FREE", "holder": None})}, T0 + 10)["action"] == "RESUME",
        f"held={lh['action']}")

    co = wd(row, {P: ev(True, writer="DEAD"), "other_paths": 2}, T0 + 10)
    unk = wd(row, {P: ev(True, writer="UNKNOWN"), "other_paths": 2}, T0 + 10)
    out["V-WAIT-CARVE-OUT-ON-DEAD-WRITER"] = (
        co["action"] == "CARVE_OUT" and co["event"] == "WRITER_DEAD" and co["carve_out"] == [P] and
        unk["action"] == "WAIT",
        f"dead={co['action']} unknown={unk['action']}")

    row2 = good_row(("a.md", "b.md"))
    mx = wd(row2, {"a.md": ev(True, writer="DEAD"), "b.md": ev(True, writer="LIVE"), "other_paths": 2}, T0 + 10)
    both_dead = wd(row2, {"a.md": ev(True, writer="DEAD"), "b.md": ev(True, writer="DEAD"), "other_paths": 2}, T0 + 10)
    out["V-WAIT-MIXED-WRITERS-WAIT"] = (
        mx["action"] == "WAIT" and both_dead["action"] == "CARVE_OUT" and both_dead["carve_out"] == ["a.md", "b.md"],
        f"mixed={mx['action']} both_dead={both_dead['action']}")

    ua = [wd(row, {P: ev(True, writer=w), "other_paths": 2}, T0 + 10)["action"] for w in ("UNKNOWN", "AMBIGUOUS")]
    out["V-WAIT-UNKNOWN-NEVER-ABANDONED"] = (
        ua == ["WAIT", "WAIT"] and wd(row, {P: ev(True, writer="DEAD"), "other_paths": 2}, T0 + 10)["action"] == "CARVE_OUT",
        f"unknown/ambiguous={ua}")

    late = TMO + 1
    c_pos = wd(row, {P: ev(True, writer="LIVE"), "other_paths": 4}, late)
    c_zero = wd(row, {P: ev(True, writer="LIVE"), "other_paths": 0}, late)
    c_none = wd(row, {P: ev(True, writer="LIVE"), "other_paths": None}, late)
    c_early = wd(row, {P: ev(True, writer="LIVE"), "other_paths": 4}, TMO - 1)
    out["V-WAIT-TIMEOUT-CARVE-OR-ESCALATE"] = (
        c_pos["action"] == "CARVE_OUT" and c_pos["event"] == "TIMEOUT" and c_zero["action"] == "ESCALATE" and
        c_none["action"] == "ESCALATE" and c_early["action"] == "WAIT" and
        wd(row, {P: ev(True, writer="LIVE"), "other_paths": 4}, TMO)["action"] == "CARVE_OUT",
        f"pos={c_pos['action']} zero={c_zero['action']} none={c_none['action']} early={c_early['action']}")
    return out


def liveness_gate(m):
    held = {"state": "RUNNING", "owner_hold": {"kind": "cost", "recovery": {"state": "DURABLE_WAIT"}}}
    park = {"state": "RUNNING", "owner_hold": {"kind": "owner", "reason": "park"}}
    return (m.goal_liveness(held) == "DURABLE_WAIT" and m.goal_liveness(park) == "OWNER_BOUNDARY" and
            m.goal_liveness({"state": "COMPLETED"}) == "TERMINAL" and
            m.goal_liveness({"state": "RUNNING"}) == "ACTIVE",
            f"held={m.goal_liveness(held)} park={m.goal_liveness(park)}")


MUTANTS = (
    ("unmeasured-as-clear", 'if dirty is False and lease_free:', 'if dirty is not True and lease_free:',
     "V-WAIT-UNMEASURED-IS-NOT-FREE"),
    ("unknown-as-dead", 'dead_ok.append(e.get("writer") == "DEAD" and',
     'dead_ok.append(e.get("writer") in ("DEAD", "UNKNOWN") and', "V-WAIT-UNKNOWN-NEVER-ABANDONED"),
    ("timeout-ignored", 'if now >= row["timeout_at"]:', 'if False:', "V-WAIT-TIMEOUT-CARVE-OR-ESCALATE"),
)


def mutant_gate(real_red: set):
    text = SRC.read_text(encoding="utf-8")
    lines, ok = [], not real_red
    with tempfile.TemporaryDirectory() as td:
        for name, old, new, gate in MUTANTS:
            if text.count(old) != 1:
                return False, f"mutant {name}: target text occurs {text.count(old)} times"
            mutated = text.replace(old, new)
            if mutated == text:
                return False, f"mutant {name}: replacement did not change the text"
            p = Path(td) / f"mut_{name.replace('-', '_')}.py"
            p.write_text(mutated, encoding="utf-8")
            mm = load(p, "mission_recovery_mut_" + name.replace("-", "_"))
            res = gates(mm)
            red = sorted(g for g, (good, _e) in res.items() if not good)
            lines.append(f"{name}->{gate}:{'RED' if gate in red else 'STILL-GREEN'}(red={len(red)})")
            ok = ok and gate in red
    return ok, " ".join(lines)


def main() -> int:
    m = load(SRC, "mission_recovery_under_test")
    res = gates(m)
    res["V-WAIT-LIVENESS-CHARACTERIZATION"] = liveness_gate(m)
    real_red = {g for g, (good, _e) in res.items() if not good}
    res["V-WAIT-MUTANTS"] = mutant_gate(real_red)
    passes = fails = 0
    for g, (good, e) in res.items():
        if good:
            passes += 1
            print(f"  PASS {g}: {e}")
        else:
            fails += 1
            print(f"  FAIL {g}: {e}")
    print(f"WAIT_PASS={passes}/{passes + fails}  threshold=18/18")
    return 0 if fails == 0 and passes == 18 else 1


if __name__ == "__main__":
    sys.exit(main())
