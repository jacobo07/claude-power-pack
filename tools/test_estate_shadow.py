#!/usr/bin/env python3
"""V-SHADOW-* gates: C3 estate spawn governor (scheduler.decide_spawn) + replay plumbing.

Pure and hermetic. Each deferral branch is paired with the ALLOW control it must not
cross, and the decider is checked to be shadow-only (no live caller blocks on it)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from modules.cognitive_os import scheduler as S  # noqa: E402
import estate_shadow as es  # noqa: E402

PASS = FAIL = 0
BANDS = {"p90": {"active_sessions": 10, "active_subagents": 5, "calls_per_h": 500},
         "p99": {"active_sessions": 20, "active_subagents": 9, "calls_per_h": 900},
         "prompt_spawns_p90": 6}
CALM = {"active_sessions": 3, "active_subagents": 1, "calls_per_h": 100}
HOT = {"active_sessions": 15, "active_subagents": 3, "calls_per_h": 300}     # > p90 only
BURNING = {"active_sessions": 30, "active_subagents": 12, "calls_per_h": 1200}


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def v(prio, load, n=1):
    return S.decide_spawn(prio, load, n, BANDS).verdict


def main() -> int:
    ok("V-SHADOW-PRIORITY", [S.spawn_priority("MISSION", "gsd-plan-checker"),
                             S.spawn_priority("HUMAN", "general-purpose"),
                             S.spawn_priority("CONTINUATION", "Explore"),
                             S.spawn_priority("MISSION", "gsd-executor"),
                             S.spawn_priority("UNKNOWN", None)]
       == [S.PRIO_VERIFY, S.PRIO_INTERACTIVE, S.PRIO_NORMAL, S.PRIO_BACKGROUND, S.PRIO_BACKGROUND],
       "verifier > interactive > normal > background; unknown root is background")
    ok("V-SHADOW-BACKGROUND-DEFERS", v(S.PRIO_BACKGROUND, HOT) == S.SPAWN_WOULD_DEFER
       and v(S.PRIO_BACKGROUND, CALM) == S.SPAWN_ALLOW, "above p90 defers; calm control allows")
    ok("V-SHADOW-NORMAL-NEEDS-P99", v(S.PRIO_NORMAL, HOT) == S.SPAWN_ALLOW
       and v(S.PRIO_NORMAL, BURNING) == S.SPAWN_WOULD_DEFER, "normal survives p90, defers above p99")
    ok("V-SHADOW-PROTECTED", all(v(p, BURNING, 99) == S.SPAWN_ALLOW for p in S.PROTECTED),
       "verify + interactive allowed at p99 load and 99 spawns in one prompt")
    ok("V-SHADOW-ENVELOPE", v(S.PRIO_NORMAL, CALM, 7) == S.SPAWN_WOULD_DEFER
       and v(S.PRIO_NORMAL, CALM, 6) == S.SPAWN_ALLOW, "7th spawn beyond p90=6 defers; 6th allowed")
    unmeasured = {"active_sessions": None, "active_subagents": None, "calls_per_h": None}
    ok("V-SHADOW-UNMEASURED-NEVER-DEFERS", v(S.PRIO_BACKGROUND, unmeasured) == S.SPAWN_ALLOW,
       "None load is unknown, not over a band")
    r = S.decide_spawn(S.PRIO_BACKGROUND, BURNING, 9, BANDS)
    ok("V-SHADOW-REASONS", r.verdict == S.SPAWN_WOULD_DEFER and len(r.reasons) == 2
       and any("p90" in x for x in r.reasons) and any("envelope" in x for x in r.reasons),
       f"{r.reasons}")
    ok("V-SHADOW-PCT", es._pct([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.9) == 9
       and es._pct([], 0.9) is None, "nearest-rank percentile; empty -> None")

    # Bands must precede the judged window inside replay() itself, not only in the CLI
    # (audit G8): otherwise a caller can tune the thresholds on the window it judges.
    try:
        es.replay(None, 0.0, 200.0, 100.0, 300.0)
        tuned = "accepted"
    except ValueError as e:
        tuned = f"refused: {e}"
    ok("V-SHADOW-BANDS-BEFORE-WINDOW", tuned.startswith("refused"), tuned)

    # A spawn made from a subagent transcript belongs to the project dir that holds
    # that transcript, never to the literal "subagents" folder (plan s12 commit 3).
    import usage_index as ux
    con = ux.connect(Path(":memory:"))
    base = r"C:\x\projects\C--proj\S1"
    con.execute("INSERT INTO spawns(tool_use_id, ts, subagent_type, prompt_id, file) VALUES"
                "('tuA', 5, 'Explore', 'P1', ?), ('tuB', 6, 'Explore', 'P1', ?)",
                (base + ".jsonl", base + r"\subagents\agent-a.jsonl"))
    got = {s["tool_use_id"]: (s["project"], s["nested"]) for s in es.spawns_in(con, 0, 10)}
    ok("V-SHADOW-NESTED-PROJECT", got == {"tuA": ("C--proj", False), "tuB": ("C--proj", True)},
       f"{got}")
    con.close()

    # Shadow only: no module outside the shadow tool and the tests calls decide_spawn.
    callers = []
    for p in list((HERE.parent / "modules").rglob("*.py")) + list((HERE.parent / "hooks").rglob("*.js")) \
            + list(HERE.glob("*.py")):
        if p.name in ("scheduler.py", "estate_shadow.py", "test_estate_shadow.py",
                      "test_spawn_policy_v2.py"):
            continue
        try:
            if re.search(r"decide_spawn", p.read_text(encoding="utf-8", errors="replace")):
                callers.append(str(p))
        except OSError:
            pass
    swept = sum(1 for _ in (HERE.parent / "modules").rglob("*.py"))
    ok("V-SHADOW-ONLY", callers == [] and swept > 100,
       f"live callers={callers} over {swept} module files swept (population floor 100)")

    total = PASS + FAIL
    print(f"ESTATE_SHADOW_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
