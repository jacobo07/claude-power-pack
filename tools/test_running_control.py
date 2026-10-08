"""V-RUNCTL-* gates: running control (expected-completion E2).

EAC reforecast + CONTINUE/CHECKPOINT decision in mission_spend.judge, the checkpoint hold in
gsd_mission._cost_breaker, the warn-as-checkpoint text in hooks/session_budget_guard.js.
Every gate is driven from both poles; the mutation drills run a COPY of the module with one hunk
reverted and require the gate to go red (the live file is never touched).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mission_spend as ms  # noqa: E402

FLOORS = json.loads((HERE.parent / "vault" / "config" / "route-floors.json").read_text(encoding="utf-8-sig"))
PROF = FLOORS["profiles"]["top-level-worker"]
NO_G = {k: v for k, v in PROF.items() if k != "growth_per_call"}
TARGET = 5_000_000

passes = fails = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate}: {evidence}")


def rec(**kw) -> dict:
    base = {"token_estimate": TARGET, "planned_calls": 28, "cost_mark": {"fp": "A", "tokens": 0}}
    base.update(kw)
    return base


def scenarios(mod) -> dict:
    """Run every canary against module `mod`; returns {gate: bool}."""
    out = {}
    # Canary 5: E1 replay, target 5M, warn hit at 6.3M with 38 calls done of 28 planned -> CHECKPOINT.
    v = mod.judge(rec(), 6_300_000, "B", ctx_now=200_000, calls_done=38, profile=PROF)
    out["c5_e1"] = v["decision"] == "CHECKPOINT" and v["trip"] is None
    # Canary 6: T2 replay, 4.09M over 27 calls: CONTINUE at every mark while the fingerprint moves.
    seq = [(1_000_000, 8), (2_000_000, 14), (3_000_000, 20), (4_090_000, 27)]
    ok = True
    for i, (spent, done) in enumerate(seq):
        v = mod.judge(rec(planned_calls=28, cost_mark={"fp": f"f{i}", "tokens": 0}), spent, f"f{i + 1}",
                      ctx_now=120_000 + 1_000 * done, calls_done=done, profile=PROF)
        ok = ok and v["decision"] == "CONTINUE"
    out["c6_t2"] = ok
    # Canary 7: absent g -> UNKNOWN, eac None, never CONTINUE.
    v = mod.judge(rec(), 1_000_000, "B", ctx_now=120_000, calls_done=5, profile=NO_G)
    out["c7_absent_g"] = v["decision"] == "UNKNOWN" and v["forecast"]["eac"] is None
    # Canary 10: fingerprint frozen while EAC is under target -> CHECKPOINT (progress required).
    v = mod.judge(rec(), 1_000_000, "A", ctx_now=120_000, calls_done=20, profile=PROF)
    out["c10_frozen"] = (v["decision"] == "CHECKPOINT" and v["forecast"]["eac"] <= TARGET
                         and v["trip"] is None)
    # Hard trip (2 x target) still wins over a forecast that would say CONTINUE.
    v = mod.judge(rec(planned_calls=1), 10_000_001, "B", ctx_now=1, calls_done=1, profile=PROF)
    out["hard_trip"] = bool(v["trip"]) and "2 x estimate" in v["trip"]
    # Stall trip unchanged.
    v = mod.judge(rec(), 3_000_000, "A", ctx_now=120_000, calls_done=5, profile=PROF)
    out["stall_trip"] = bool(v["trip"]) and "since the work tree last changed" in v["trip"]
    # Growth term is real: more remaining calls -> strictly larger EAC than the no-growth floor sum.
    f = mod.eac_forecast(1_000_000, 100_000, 20, 4, PROF)
    r = f["r"]
    out["growth_term"] = f["eac"] == int(round(1_000_000 + r * (100_000 + PROF["growth_per_call"]["value"] * r / 2)))
    return out


def load_copy(src: Path, old: str, new: str, tmp: Path, name: str):
    text = src.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"mutation anchor absent: {old!r}")
    p = tmp / f"{name}.py"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    live = scenarios(ms)
    check("V-RUNCTL-E1-CHECKPOINT", live["c5_e1"], "canary 5: 6.3M spent vs 5M target -> CHECKPOINT at warn")
    check("V-RUNCTL-T2-CONTINUE", live["c6_t2"], "canary 6: T2 replay 4.09M/27 calls -> CONTINUE at all 4 marks")
    check("V-RUNCTL-ABSENT-G", live["c7_absent_g"], "canary 7: no growth_per_call -> UNKNOWN, eac None")
    check("V-RUNCTL-FROZEN-FP", live["c10_frozen"], "canary 10: fingerprint frozen, EAC under target -> CHECKPOINT")
    check("V-RUNCTL-HARD-TRIP", live["hard_trip"], "2 x target trip still wins")
    check("V-RUNCTL-STALL-TRIP", live["stall_trip"], "stall trip unchanged")
    check("V-RUNCTL-EAC-FORMULA", live["growth_term"], "EAC = spent + r x (ctx + g x r / 2)")

    # Canary 11: context-rent trigger, both poles.
    t1 = ms.eac_forecast(2_000_000, 206_000, 40, 23, {**PROF, "calls_err": {"value": 0.0}})
    t2 = ms.eac_forecast(3_000_000, 150_000, 27, 24, {**PROF, "calls_err": {"value": 0.0}})
    check("V-RUNCTL-ROTATE-T1", t1["r"] == 17 and t1["rotate_recommended"] is True,
          f"canary 11: ctx 206k, r={t1['r']:g} -> rotate")
    check("V-RUNCTL-ROTATE-T2", t2["r"] == 3 and t2["rotate_recommended"] is False,
          f"canary 11: ctx 150k, r={t2['r']:g} -> no rotate")

    # Pure-function pole: no forecast inputs -> legacy shape, decision None.
    v = ms.judge(rec(), 1_000_000, "B")
    check("V-RUNCTL-LEGACY", v["decision"] is None and v["forecast"] is None and v["mark"],
          "no usage inputs -> no forecast, mark still emitted")

    # Sweep side: CHECKPOINT parks the mission with the existing owner hold; CONTINUE does not.
    import gsd_mission as gm
    held = []
    orig = gm.set_owner_hold
    gm.set_owner_hold = lambda mid, reason, now=None: (held.append(reason) or {"mission_id": mid, "hold": reason})
    appended = []
    orig_ap = gm.lr.ledger_append
    gm.lr.ledger_append = lambda *a, **k: appended.append((a, k))
    orig_prof = gm._route_profile
    gm._route_profile = lambda name: PROF
    try:
        base = {"mission_id": "m-test", "cwd": ".", "work_dir": ".", "epoch": 1, "state": "running",
                "token_estimate": TARGET, "planned_calls": 28, "route_profile": "top-level-worker",
                "cost_mark": {"fp": "A", "tokens": 0}}
        gm._cost_breaker(dict(base), 0.0, measure=lambda r: 6_300_000, fingerprint=lambda p: "B",
                         usage=lambda r: (200_000, 38))
        check("V-RUNCTL-SWEEP-HOLD", len(held) == 1 and held[0].startswith("checkpoint: EAC ")
              and "> target" in held[0], f"hold reason: {held[:1]}")
        held.clear()
        orig_tr = gm.transition
        gm.transition = lambda *a, **k: {"mission_id": "m-test"}
        try:
            gm._cost_breaker(dict(base), 0.0, measure=lambda r: 2_000_000, fingerprint=lambda p: "B",
                             usage=lambda r: (130_000, 12))
        finally:
            gm.transition = orig_tr
        check("V-RUNCTL-SWEEP-CONTINUE", held == [], "CONTINUE (EAC under target, fp moved) sets no hold")
    finally:
        gm.set_owner_hold = orig
        gm.lr.ledger_append = orig_ap
        gm._route_profile = orig_prof

    # Warn text is one imperative checkpoint instruction, reusing the closeout allowance.
    js = (HERE.parent / "hooks" / "session_budget_guard.js").read_text(encoding="utf-8")
    check("V-RUNCTL-WARN-TEXT", "SESSION BUDGET CHECKPOINT" in js and "progress receipt" in js
          and "closeout allowance" in js and "start nothing new" not in js,
          "warn text instructs a progress receipt and stop; old 'start nothing new' gone")

    # Mutation drills: revert one hunk in a COPY, require the matching canary to go red.
    src = HERE / "mission_spend.py"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        drills = [
            ("V-RUNCTL-MUT-GROWTH", "g * r / 2.0)", "0.0)", "growth_term", "growth term dropped from EAC"),
            ("V-RUNCTL-MUT-ABSENT-G", "if gv is None:", "gv = 0.0 if gv is None else gv\n    if False:",
             "c7_absent_g", "absent g treated as 0"),
            ("V-RUNCTL-MUT-FINGERPRINT", "and moved)", ")", "c10_frozen", "fingerprint check removed"),
            ("V-RUNCTL-MUT-HARD-TRIP", "if spent > ratio * est:", "if spent > ratio * est and False:",
             "hard_trip", "hard trip overridden"),
        ]
        for i, (gate, old, new, canary, what) in enumerate(drills):
            mut = load_copy(src, old, new, tmp, f"ms_mut{i}")
            res = scenarios(mut)
            check(gate, res[canary] is False, f"mutant '{what}' turns {canary} red")
    print(f"RUNCTL_PASS={passes}/{passes + fails}  threshold=N/N")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
