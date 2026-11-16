"""Regression: an ask for the Owner's decision is Owner-class, never auto-answered (backlog bada2258afa1).

Incident GEX44 m-26ea4de62c50 2026-11-14 20:50Z-21:38Z: the worker parked on inputs/OWNER-DECISION-F1(B).md and ended
its turn asking for it; gate_question matched no Owner class -> RESOLVE_BY_DEFAULT -> decision recovery relaunched a
worker 5 times (epochs 11-15) while the mission waited for the Owner. The texts below are the ledger's own
`launch_cause` lines. Portable: depends only on mission_policy (the bigger suites diverge between hosts).
Exit 0 = all pass. Mutation check: remove the OWNER_DECISION entry from OWNER_CLASSES -> this test must fail."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mission_policy as mp  # noqa: E402

INCIDENT = [
    "write /home/kobii/missions/cw-icp-series/inputs/OWNER-DECISION-F1.md (gsd_mission requires)",
    "review deliver/look3-test/head6/ and write /home/kobii/missions/cw-icp-series/inputs/OWNER-DECISION-F1.md",
    "Review deliver/look3-test/head7/ and write F1B-REVIEW to /home/kobii/missions/cw-icp-series/inputs/"
    "OWNER-DECISION-F1B.md to resume",
    "write the independent head7 verdict in /home/kobii/missions/cw-icp-series/inputs/OWNER-DECISION-F1B.md",
    "write verdict at /home/kobii/missions/cw-icp-series/inputs/OWNER-DECISION-F1B.md",
]
SYNTH = ["Waiting for the Owner's decision on the look before continuing", "Needs Owner approval of Gate C",
         "OWNER DECISION NEEDED: pick Meshy or the artist", "Espero la decisión del Owner sobre la cabeza",
         "falta la aprobación del Owner del look", "write inputs/owner_decision_head4.md"]
ORDINARY = ["Should I write the decision log before the render?", "Record the decision in STATE.md and continue?",
            "The owner of the lock file is pid 4170; wait for it?", "Write the review notes to deliver/REVIEW.md?",
            "Which approval test runs first, unit or smoke?", "write inputs/DECISIONS.md summary first?"]


def main() -> int:
    fails = []
    for s in INCIDENT + SYNTH:
        g = mp.gate_question(s, {})
        if g.get("result") != "OWNER_REQUIRED":
            fails.append(f"not Owner-class: {s[:70]!r} -> {g.get('result')}")
    for s in ORDINARY:
        g = mp.gate_question(s, {})
        if g.get("result") != "RESOLVE_BY_DEFAULT":
            fails.append(f"wrongly escalated: {s[:70]!r} -> {g.get('owner_class') or g.get('result')}")
    for s in INCIDENT:
        c = mp.classify_blocked({"state": "blocked", "needs": s}, {})["class"]
        if c != "QUESTION_OWNER":
            fails.append(f"blocked job would relaunch ({c}): {s[:70]!r}")
    n = len(INCIDENT) * 2 + len(SYNTH) + len(ORDINARY)
    for f in fails:
        print("FAIL", f)
    print(f"OWNER_DECISION_GATE {n - len(fails)}/{n}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
