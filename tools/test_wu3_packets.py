"""V-WU3-* gates for tools/wu3_packets.py (TOK-18 gen2 S5, offline).

Exclusion is driven from both poles (a dependency packet carries no other-unit private page; a packet
that does carry one is detected), and removal of a critical page must judge PAGE or DEOPT, with a
control where the page is present and admitted.

    python tools/test_wu3_packets.py      exit 0 on pass
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import source_packet as sp  # noqa: E402
import wu3_packets as w  # noqa: E402

passes = fails = 0


def check(gate, cond, evidence):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate} {evidence}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    # Arrange
    crit = {u: w.critical(u) for u in w.UNITS}
    proj = {u: w.projection(u) for u in w.UNITS}
    dep = {u: sp.build(str(w.ROOT), proj[u], **w.WHOLE) for u in w.UNITS}
    priv = {u: w.private(u) for u in w.UNITS}

    check("V-WU3-ORACLE", bool(crit["WU1"] and crit["WU2"]) and not set(crit["WU1"]) & set(crit["WU2"]),
          f"WU1={crit['WU1']} WU2={crit['WU2']}")
    check("V-WU3-PRIVATE-NONEMPTY", bool(priv["WU1"] and priv["WU2"]),
          f"WU1-only={sorted(priv['WU1'])} WU2-only={sorted(priv['WU2'])}")

    # Exclusion, positive pole: each dependency packet carries no page private to the other unit.
    for u, other in (("WU1", "WU2"), ("WU2", "WU1")):
        got = {e.get("path") for e in dep[u].manifest.get("entries") or []}
        check(f"V-WU3-EXCLUDE-{u}", bool(got) and not got & priv[other], f"{u} packet={sorted(got)}")
    # Exclusion, negative pole: a packet over both units' pages does carry them, and the check sees it.
    both = sp.build(str(w.ROOT), sorted(set(proj["WU1"]) | set(proj["WU2"])), **w.WHOLE)
    leaked = {e.get("path") for e in both.manifest.get("entries") or []} & (priv["WU1"] | priv["WU2"])
    check("V-WU3-EXCLUDE-CONTROL", leaked == priv["WU1"] | priv["WU2"], f"union packet leaks {sorted(leaked)}")

    # Control: WU2's critical pages are all present and whole -> ADMIT.
    v, f = w.judge(dep["WU2"], crit["WU2"])
    check("V-WU3-ADMIT-CONTROL", v == w.ADMIT and not f, f"WU2 judge={v} faults={f}")
    # WU1 historical: whatever the verdict, ADMIT iff every critical page is whole.
    v1, f1 = w.judge(dep["WU1"], crit["WU1"])
    check("V-WU3-WU1-NO-SILENT-PASS", (v1 == w.ADMIT) == (set(crit["WU1"]) <= w.included(dep["WU1"])),
          f"WU1 judge={v1} faults={f1}")

    # Mutation: remove one critical page from the packet -> PAGE (still on disk), never ADMIT.
    cut = "tools/wake_check.py"
    mutant = sp.build(str(w.ROOT), [p for p in proj["WU2"] if p != cut], **w.WHOLE)
    v, f = w.judge(mutant, crit["WU2"])
    check("V-WU3-MUTANT-PAGE", v == w.PAGE and [x[0] for x in f] == [cut], f"judge={v} faults={f}")
    # Mutation: page removed AND not readable where the worker runs -> DEOPT.
    with tempfile.TemporaryDirectory() as empty:
        v, f = w.judge(mutant, crit["WU2"], root=Path(empty))
    check("V-WU3-MUTANT-DEOPT", v == w.DEOPT and (cut, w.DEOPT, "absent-from-disk") in f, f"judge={v} faults={f}")
    # A truncated page at the default limits is a fault, not a pass.
    small = sp.build(str(w.ROOT), crit["WU2"])
    v, f = w.judge(small, crit["WU2"])
    check("V-WU3-TRUNCATED-IS-FAULT", v != w.ADMIT and any(x[2] == "truncated" for x in f), f"judge={v} faults={f}")
    # The builder could not answer -> DEOPT, never ADMIT.
    v, f = w.judge(sp.Packet(sp.UNJUDGED, gaps=["bridge down"]), crit["WU2"])
    check("V-WU3-UNJUDGED-DEOPT", v == w.DEOPT, f"judge={v}")

    print(f"WU3_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())