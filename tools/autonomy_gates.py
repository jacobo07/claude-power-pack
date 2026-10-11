"""WU-S7: deterministic V-gates for the 8 autonomy invariants, spend-agreement gate, reflex coverage counter.

Pure predicates over plain dicts (zero model). Each gate returns {"gate", "verdict", "why"} with verdict in
PASS / FAIL / INCONCLUSIVE. Missing input is INCONCLUSIVE, never PASS; an aggregate is green only if every gate PASS.
    python tools/autonomy_gates.py   # prints the reflex coverage number
"""
from __future__ import annotations

import sys
from pathlib import Path

PASS, FAIL, INC = "PASS", "FAIL", "INCONCLUSIVE"
TOOLS = Path(__file__).resolve().parent


def _r(gate, verdict, why=""):
    return {"gate": gate, "verdict": verdict, "why": why}


def g_duration(s):
    """No RUNNING mission older than max_age_s without a heartbeat inside max_age_s."""
    ms, now, mx = s.get("running"), s.get("now"), s.get("max_age_s")
    if ms is None or now is None or mx is None:
        return _r("duration", INC, "running/now/max_age_s missing")
    bad = [m["id"] for m in ms if now - m.get("heartbeat", m.get("started", 0)) > mx]
    return _r("duration", FAIL, f"stale: {bad}") if bad else _r("duration", PASS)


def g_goal_count(s):
    """Exactly one active goal bound to the programme root."""
    n = s.get("active_goals_for_root")
    if n is None:
        return _r("goal_count", INC, "count missing")
    return _r("goal_count", PASS) if n == 1 else _r("goal_count", FAIL, f"{n} goals")


def g_history(s):
    """Status output size must not grow with history: size(with history) <= size(without) + slack."""
    a, b = s.get("size_small_history"), s.get("size_large_history")
    if a is None or b is None:
        return _r("history", INC, "sizes missing")
    return _r("history", PASS) if b <= a + s.get("slack", 0) else _r("history", FAIL, f"{a}->{b}")


def g_capability(s):
    """Every pending unit has packet, route and a receipt path that resolve."""
    us = s.get("units")
    if us is None:
        return _r("capability", INC, "units missing")
    bad = [u.get("id") for u in us if not (Path(u.get("packet", "")).exists() and Path(u.get("route", "")).exists()
                                           and u.get("receipt"))]
    return _r("capability", FAIL, f"missing: {bad}") if bad else _r("capability", PASS)


def g_test_estate(s):
    """Every named guard module has a test_<module>.py beside it."""
    mods, d = s.get("guard_modules"), Path(s.get("tools_dir", TOOLS))
    if mods is None:
        return _r("test_estate", INC, "modules missing")
    bad = [m for m in mods if not (d / f"test_{m}.py").exists()]
    return _r("test_estate", FAIL, f"no test: {bad}") if bad else _r("test_estate", PASS)


def g_observability(s):
    """Spend is measured (not UNKNOWN) and telemetry is ok."""
    sp = s.get("spend")
    if not sp:
        return _r("observability", INC, "spend missing")
    if "UNKNOWN" in (sp.get("settled"), sp.get("reserved")) or sp.get("telemetry_ok") is not True:
        return _r("observability", FAIL, f"settled={sp.get('settled')} telemetry_ok={sp.get('telemetry_ok')}")
    return _r("observability", PASS)


def g_wait(s):
    """A non-running chain names the event it waits for; stopped_without_done is never a resting state."""
    a = s.get("action")
    if a is None:
        return _r("wait", INC, "action missing")
    if a == "stopped_without_done":
        return _r("wait", FAIL, "stopped_without_done")
    if a.startswith("wait") and not s.get("wait_event"):
        return _r("wait", FAIL, "waiting with no named event")
    return _r("wait", PASS)


def g_control(s):
    """settled + reserved + unknown never exceed the cap."""
    sp, cap = s.get("spend"), s.get("cap")
    if not sp or cap is None or "UNKNOWN" in (sp.get("settled"), sp.get("reserved"), sp.get("unknown")):
        return _r("control", INC, "spend or cap unknown")
    tot = sp["settled"] + sp["reserved"] + sp["unknown"]
    return _r("control", PASS) if tot <= cap else _r("control", FAIL, f"{tot}>{cap}")


def g_spend_agreement(s):
    """programme_status spend must equal the ledger goal-status view (the S7 UNKNOWN-vs-settled bug)."""
    a, b = s.get("status_spend"), s.get("ledger_spend")
    if not a or not b:
        return _r("spend_agreement", INC, "one source missing")
    if "UNKNOWN" in (a.get("settled"), b.get("settled")):
        return _r("spend_agreement", FAIL, f"status={a.get('settled')} ledger={b.get('settled')}")
    return _r("spend_agreement", PASS) if a["settled"] == b["settled"] else \
        _r("spend_agreement", FAIL, f"status={a['settled']} ledger={b['settled']}")


GATES = [g_duration, g_goal_count, g_history, g_capability, g_test_estate, g_observability, g_wait, g_control,
         g_spend_agreement]


def run_all(state: dict) -> dict:
    res = [g(state) for g in GATES]
    return {"green": all(r["verdict"] == PASS for r in res), "results": res}


# Known failure classes handled with zero model: class -> (reflex, evidence file that drives its test).
REFLEXES = {
    "worker_lingers_after_done": ("linger-kill", "test_gsd_mission.py"),
    "stale_mission_record": ("steward", "test_mission_steward.py"),
    "orphan_process": ("reapers", "test_gsd_mission.py"),
    "chain_refuses_unsafe_arm": ("chain refusals", "test_gsdx_chain.py"),
    "breaker_halt_with_handoff": ("chain residual continuation (R1)", "test_gsdx_chain.py"),
    "unchanged_unit_rerun": ("NO_WORK admission (S6)", "test_unit_proof_reuse.py"),
    "manual_rearm": ("chain", "test_gsdx_chain.py"),
    "manual_landing": ("land_worktree", "test_land_worktree.py"),
}


def reflex_coverage(tools_dir: Path | None = None, tests_dir: Path | None = None) -> dict:
    d = Path(tools_dir or TOOLS)
    covered = {k: v for k, v in REFLEXES.items() if (d / v[1]).exists() or (Path(tests_dir or d.parent / "tests") / v[1]).exists()}
    return {"covered": len(covered), "total": len(REFLEXES), "missing": sorted(set(REFLEXES) - set(covered))}


def _ledger_spend(goal: str):
    """The ledger's own settled view (the goal-status source), independent of programme_status."""
    try:
        import mission_spend as ms
        led = ms._goal_ledger(goal)
        with led._lock:
            g = led._gfold(led._read())
        return {"settled": int(sum(g["marks"].values())), "reserved": int(g["open"])}
    except Exception as ex:  # noqa: BLE001 -- unreadable ledger is a missing source (INCONCLUSIVE), never zero
        return {"settled": "UNKNOWN", "reserved": "UNKNOWN", "why": f"{type(ex).__name__}: {ex}"[:120]}


def live_state(chain_path, *, status=None, ledger=None, now=None, max_age_s=3600) -> dict:
    """Build the run_all state dict from LIVE state: programme_status.project + the ledger goal view.
    status/ledger are injectable for tests; None means load. Whatever cannot be read stays absent
    (INCONCLUSIVE), never defaulted to a passing value."""
    import json
    import time
    sys.path.insert(0, str(TOOLS))
    import programme_status as ps
    chain_path = Path(chain_path)
    st = status if status is not None else ps.project(chain_path)
    chain = json.loads(chain_path.read_text(encoding="utf-8-sig"))
    goal = chain.get("goal")
    led = ledger if ledger is not None else (_ledger_spend(goal) if goal else None)
    sp = st.get("spend") or {}
    units = [{"id": u["id"], "packet": u.get("packet", ""), "route": u.get("route", ""), "receipt": u.get("receipt")}
             for u in chain.get("units", []) if u["id"] in (st.get("debt") or {}).get("pending_ids", [])]
    state = {"now": now if now is not None else time.time(), "max_age_s": max_age_s, "units": units,
             "spend": {k: sp.get(k) for k in ("settled", "reserved", "unknown", "telemetry_ok")} if sp else None,
             "status_spend": sp or None, "ledger_spend": led,
             "action": st.get("action") if st.get("action") != "unknown" else None,
             "guard_modules": ["autonomy_gates", "programme_status", "gsdx_chain"], "tools_dir": str(TOOLS)}
    if chain.get("envelope") is not None and isinstance(chain["envelope"], (int, float)):
        state["cap"] = chain["envelope"]
    if st.get("state") == "waiting":
        state["wait_event"] = st.get("next_eligible_transition")
    return state


if __name__ == "__main__":
    import json as _json
    if "--live" in sys.argv:
        cp = Path(sys.argv[sys.argv.index("--live") + 1]) if len(sys.argv) > sys.argv.index("--live") + 1 \
            else TOOLS.parent / "vault" / "programs" / "autonomy" / "chain.json"
        out = run_all(live_state(cp))
        print(_json.dumps(out, indent=1))
        sys.exit(0 if out["green"] else 1)
    c = reflex_coverage()
    print(f"REFLEX_COVERAGE={c['covered']}/{c['total']} missing={c['missing']}")
    sys.exit(0)
