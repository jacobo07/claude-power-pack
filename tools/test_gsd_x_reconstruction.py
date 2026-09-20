#!/usr/bin/env python3
"""V-RECON-* -- the reconstruction-parity capability, driven from both poles.

WHY A CONTRACT AND NOT A CODE CHANGE. `modules/gsd_x/tier.py` says of itself
"this module is not a new decider", and its tier is a pure function of the
capability verdicts the Capability Runtime returns. Raising posture for a
reconstruction mission by editing `tier.py` would install a second decider in
the one module whose entire thesis is that it is not one. So the lever is a
contract, `tier.py` is untouched, and V-RECON-NO-DECIDER pins that.

WHAT THE CONTRACT IS FOR. Invocation independence: a mission that carries a
working reference, a candidate, and a fidelity requirement should raise its own
posture without the operator naming differential execution, earliest divergence
or any laboratory. The natural-phrasing case is the whole point, and it is the
first gate.

THE FAILURE THIS FILE IS MOST LIKELY TO HAVE. A contract that fires on
everything raises posture on every prompt and is indistinguishable from raising
the floor -- which carries no information and trains the reader to ignore it.
V-RECON-NO-GOODHART is the control, and it is the reason the unrelated-prompt
corpus below is drawn from ordinary estate work rather than from prompts chosen
to stay silent.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.applicability import (  # noqa: E402
    MissionContext, Verdict, evaluate,
)
from modules.capability_runtime.contract import load_contracts  # noqa: E402
from modules.gsd_x import tier  # noqa: E402

CONTRACT_ID = "reconstruction_parity"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _contract():
    for c in load_contracts():
        if c.id == CONTRACT_ID:
            return c
    return None


def _verdict(c, prompt: str, evidence=("source",)) -> Verdict:
    ctx = MissionContext(description=prompt, available_evidence=list(evidence))
    return evaluate(c, ctx).verdict


# The corpus is ordinary estate work, NOT prompts curated to stay quiet. A
# silence control built from text chosen for its silence proves nothing.
UNRELATED = (
    "fix the typo in the README heading",
    "que hora es",
    "add a unit test for the date parser",
    "why is the hook dispatcher timing out on the Stop chain",
    "rename the variable in line 40",
    "update the changelog for this release",
    "the build is failing on Windows with a path separator error",
    "summarise what changed in the last three commits",
    "increase the log level to debug in the staging config",
    "remove the unused import from the scorer",
)


def main() -> int:
    c = _contract()
    if c is None:
        _fail("V-RECON-LOADS", f"{CONTRACT_ID} not found by load_contracts()")
        print(f"\nRECON_PASS={_passes}/{_passes + _fails}  threshold=9/9")
        return 1
    _ok("V-RECON-LOADS", f"{CONTRACT_ID} loaded, owner={c.owner!r}")

    # 1. Invocation independence. The operator names no machinery whatsoever.
    natural = "Port this APK game to Wii faithfully"
    v = _verdict(c, natural)
    if v is Verdict.MANDATORY:
        _ok("V-RECON-NATURAL", f"{natural!r} -> {v.value} with no tool named")
    else:
        _fail("V-RECON-NATURAL", f"{natural!r} -> {v.value}, expected MANDATORY")

    # 2. Posture SCALES. One signal is weaker evidence than two, and must not
    #    buy the same posture, or the ladder has one rung.
    v1 = _verdict(c, "we need better fidelity here")
    if v1 is Verdict.RECOMMENDED:
        _ok("V-RECON-SCALES", f"single trigger -> {v1.value}, not MANDATORY")
    else:
        _fail("V-RECON-SCALES", f"single trigger -> {v1.value}, expected RECOMMENDED")

    # 3. The network sense of 'port' is vetoed rather than scored.
    v2 = _verdict(c, "change the port number to 8080 in the config")
    if v2 is Verdict.NOT_APPLICABLE:
        _ok("V-RECON-ANTI", f"'port number' -> {v2.value} (anti-trigger veto)")
    else:
        _fail("V-RECON-ANTI", f"'port number' -> {v2.value}, expected NOT_APPLICABLE")

    # 4. Dormant by default on a mission that never reached for it.
    v3 = _verdict(c, "fix the typo in the README heading")
    if v3 is Verdict.NOT_APPLICABLE:
        _ok("V-RECON-DORMANT", f"trivial prompt -> {v3.value}")
    else:
        _fail("V-RECON-DORMANT", f"trivial prompt -> {v3.value}, expected NOT_APPLICABLE")

    # 5. ANTI-GOODHART. If this fires across ordinary work it has raised the
    #    floor, not measured anything.
    fired = [p for p in UNRELATED
             if _verdict(c, p) is not Verdict.NOT_APPLICABLE]
    if not fired:
        _ok("V-RECON-NO-GOODHART", f"0/{len(UNRELATED)} unrelated prompts activated it")
    else:
        _fail("V-RECON-NO-GOODHART",
              f"{len(fired)}/{len(UNRELATED)} unrelated prompts activated it: {fired}")

    # 6. The contract makes an EXISTING owner reachable. Before it, modules/osr
    #    had no production caller at all -- only its own test and an audit tool.
    if c.owner.strip() == "modules/osr":
        _ok("V-RECON-OWNER", "owner=modules/osr -- the incumbent, not a new module")
    else:
        _fail("V-RECON-OWNER", f"owner={c.owner!r}, expected modules/osr")

    # 7. The sealed boundaries are encoded in the contract itself, so a reader
    #    of the contract cannot mistake its remit.
    ns = {s.strip().lower() for s in c.non_scope}
    need = {"publishing a fidelity number",      # DAIF-03 s1.7 by Owner ruling
            "acquiring the reference evidence",  # OSR BOUNDARY_CONTRACT
            "investigating the cause of a divergence",  # craif
            "architecture reconstruction"}       # graphify's contract
    missing = sorted(need - ns)
    if not missing:
        _ok("V-RECON-BOUNDARY", "all four sealed boundaries declared in non_scope")
    else:
        _fail("V-RECON-BOUNDARY", f"non_scope missing: {missing}")

    # 8. NO SECOND DECIDER. The tier must come out of the contract path alone.
    #    If tier.py ever grows a reconstruction branch of its own, the tier
    #    would still be right and this gate would still pass -- so the gate is
    #    on tier.py's SOURCE, which is the only thing that can witness it.
    src = (_PP_ROOT / "modules" / "gsd_x" / "tier.py").read_text(encoding="utf-8")
    leaked = [t for t in ("reconstruction", "parity", "reference_implementation")
              if t in src.lower()]
    if not leaked:
        _ok("V-RECON-NO-DECIDER", "tier.py carries no reconstruction vocabulary")
    else:
        _fail("V-RECON-NO-DECIDER", f"tier.py mentions {leaked} -- second decider")

    # 9. End to end, through the real classifier, on the natural phrasing.
    verdict = tier.classify_prompt(natural, root=_PP_ROOT)
    drivers = [cid for cid, _ in verdict.drivers]
    if verdict.tier in (tier.DEEP, tier.FORENSIC) and CONTRACT_ID in drivers:
        _ok("V-RECON-E2E",
            f"classify_prompt -> {verdict.tier}, driven by {CONTRACT_ID}")
    else:
        _fail("V-RECON-E2E",
              f"classify_prompt -> {verdict.tier}, drivers={drivers}, "
              f"by_floor={verdict.by_floor}")

    total = _passes + _fails
    print(f"\nRECON_PASS={_passes}/{total}  threshold=9/9")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
