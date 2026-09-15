#!/usr/bin/env python3
"""V-GSDX-* -- the tier is measured, and the gate can prove it is not constant.

The failure this suite exists to catch is not a crash. It is a green run that
means nothing: the engine bottoms out on every prompt, the advisory is always
the floor, every other assertion passes, and the slice has replaced a constant
string with a constant function. That happened on the first real run of this
module -- 9 of 9 prompts returned LIGHT by floor -- so the discrimination gate
below is not defensive decoration, it is the finding that shaped the design.

Hence two gates that most suites do not have:

    DISCRIMINATION   two real prompts must land on two DIFFERENT tiers
    FLOOR RATE       a minimum share of a fixed corpus must be INFORMATIVE,
                     i.e. say something the constant string does not

Plus the pair that makes any of it attributable: a positive control that the
engine is genuinely reached (patch it to raise and require the failure to
surface in the reason) and a negative control that the unpatched path completes
(so the raise is attributable to the patch, not to the engine never running).

    python tools/test_gsd_x.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.gsd_x import heartbeat, tier          # noqa: E402

NODE = r"C:\Program Files\nodejs\node.exe"
HOOK = _ROOT / "hooks" / "gsd_x_tier.js"
REMINDER = Path.home() / ".claude" / "hooks" / "power-pack-reminder.js"

# A fixed corpus, written once. Shaped like real prompts from this estate's own
# history rather than like inputs chosen to make the gate pass.
CORPUS = [
    ("que hora es", False),
    ("fix the typo in the readme", False),
    ("wire the liveness module and register it so the gate can reach it", True),
    ("is this done and ready to ship to production?", True),
    ("deploy the plugin to the live server and restart it", True),
    ("build a new institutional knowledge fabric for the whole estate", True),
    ("add a column to the orders table and migrate existing rows", True),
    ("integrate the capability runtime with the done gate and verify it", True),
]
MIN_INFORMATIVE = 0.5          # over half the corpus must beat the constant


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g: str, ev: str) -> None:
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g: str, why: str) -> None:
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    print("# V-GSDX\n")

    # --- V1 discrimination ---------------------------------------------------
    verdicts = {p: tier.classify_prompt(p) for p, _ in CORPUS}
    distinct = sorted({v.tier for v in verdicts.values()})
    if len(distinct) >= 2:
        ok("V-GSDX-DISCRIMINATION", f"{len(distinct)} distinct tiers: {distinct}")
    else:
        bad("V-GSDX-DISCRIMINATION",
            f"every prompt landed on {distinct} -- the engine is a constant, and "
            "a constant function is not an improvement on a constant string")

    # --- V2 floor rate -------------------------------------------------------
    informative = [p for p, v in verdicts.items() if v.informative]
    rate = len(informative) / len(CORPUS)
    if rate >= MIN_INFORMATIVE:
        ok("V-GSDX-FLOOR-RATE",
           f"{len(informative)}/{len(CORPUS)} informative ({rate:.0%}) "
           f">= {MIN_INFORMATIVE:.0%}")
    else:
        bad("V-GSDX-FLOOR-RATE",
            f"only {rate:.0%} informative -- the advisory is mostly the floor")

    # --- V3 the heavy prompts outrank the trivial ones -----------------------
    order = {tier.LIGHT: 0, tier.STANDARD: 1, tier.DEEP: 2, tier.FORENSIC: 3}
    misranked = [
        p for p, heavy in CORPUS
        if heavy and order.get(verdicts[p].tier, -1) < order[tier.STANDARD]
    ]
    if not misranked:
        ok("V-GSDX-RANK", "every prompt marked heavy landed at STANDARD or above")
    else:
        bad("V-GSDX-RANK", f"heavy prompts at or below LIGHT: {misranked[:3]}")

    # --- V3b a trivial prompt must not ABSTAIN -------------------------------
    # This gate exists because the suite could not otherwise catch the dormancy
    # regression. With the dormancy filter reverted, trivial prompts abstain --
    # and discrimination, floor-rate and rank ALL still pass, because abstention
    # is neither a floor answer nor a misranking. A mutation nothing catches is
    # a hole in the suite, not a property of the code.
    abstaining_trivia = [
        p for p, heavy in CORPUS if not heavy and verdicts[p].abstained
    ]
    if not abstaining_trivia:
        ok("V-GSDX-TRIVIAL", "trivial prompts resolve, they do not abstain")
    else:
        bad("V-GSDX-TRIVIAL",
            f"trivial prompts abstained: {abstaining_trivia} -- an abstention "
            "that fires on everything carries no information")

    # --- V4 no new vocabulary ------------------------------------------------
    # The ladder must be spelled exactly as the incumbent spells it, or the model
    # receives one word carrying two meanings on the same event.
    if REMINDER.is_file():
        src = REMINDER.read_text(encoding="utf-8-sig", errors="replace")
        line = next((l for l in src.splitlines()
                     if all(w in l for w in tier.LADDER)), "")
        if line:
            ok("V-GSDX-NO-NEW-VOCAB",
               f"all of {list(tier.LADDER)} appear on the incumbent's own line")
        else:
            bad("V-GSDX-NO-NEW-VOCAB",
                "the incumbent no longer spells the ladder this way -- the two "
                "surfaces have drifted and neither is authoritative")
    else:
        bad("V-GSDX-NO-NEW-VOCAB",
            f"cannot read {REMINDER} -- vocabulary agreement unverified")

    # --- V5 abstain names the missing fact -----------------------------------
    # Driven synthetically: a real prompt may or may not reach this branch, and a
    # gate that depends on the corpus happening to trigger it is not a gate.
    class _Blocked:
        blocked = True
        capability_id = "synthetic"
        verdict = tier.Verdict.BLOCKED_BY_MISSING_EVIDENCE
    v = tier.classify([_Blocked()])
    if v.abstained and v.missing:
        ok("V-GSDX-ABSTAIN", f"abstains and names: {v.missing}")
    else:
        bad("V-GSDX-ABSTAIN",
            f"blocked-only input produced {v.tier!r} with missing={v.missing}")

    # --- V6 a dormant blocked contract must NOT force abstention -------------
    class _NotApplicable:
        blocked = False
        capability_id = "dormant"
        verdict = tier.Verdict.NOT_APPLICABLE
    v6 = tier.classify([_NotApplicable()])
    if v6.tier == tier.LIGHT and v6.by_floor and not v6.abstained:
        ok("V-GSDX-DORMANT", "a dormant capability yields the floor, not an abstention")
    else:
        bad("V-GSDX-DORMANT", f"dormant-only input produced {v6.tier!r}")

    # --- V6b a dormant verdict must not CANCEL an earned abstention ----------
    # The exact state the two spellings differ on: one capability addressed and
    # blocked, another dormant. `not applies` reads the dormant one as an
    # evaluation and suppresses the abstention; `not positives` does not. No
    # corpus prompt reaches this combination, so it is driven directly -- an
    # unreachable branch is an unpinned one, and this one stayed unpinned until
    # a mutation drill reported it SURVIVED.
    v6b = tier.classify([_Blocked(), _NotApplicable()])
    if v6b.abstained:
        ok("V-GSDX-ABSTAIN-DOMINANCE",
           "a dormant verdict does not cancel an abstention earned by a blocked one")
    else:
        bad("V-GSDX-ABSTAIN-DOMINANCE",
            f"blocked + dormant produced {v6b.tier!r} -- a capability declining "
            "to speak was counted as one that spoke")

    # --- V7 positive + negative control on engine reachability ---------------
    import modules.gsd_x.tier as tmod
    real = tmod.evaluate_all
    baseline = tmod.classify_prompt("deploy to production and restart")
    try:
        def _boom(*a, **k):
            raise RuntimeError("CONTROL_PATCH_REACHED")
        tmod.evaluate_all = _boom
        patched = tmod.classify_prompt("deploy to production and restart")
    finally:
        tmod.evaluate_all = real
    reached = "CONTROL_PATCH_REACHED" in patched.reason or "RuntimeError" in patched.reason
    if reached and not baseline.by_floor:
        ok("V-GSDX-ENGINE-REACHED",
           "patching the engine changed the result, and the unpatched path "
           f"completed at {baseline.tier} -- the raise is attributable")
    elif not reached:
        bad("V-GSDX-ENGINE-REACHED",
            "patching the engine changed nothing -- the module may never call it")
    else:
        bad("V-GSDX-ENGINE-REACHED",
            "negative control failed: the unpatched path was already the floor, "
            "so the patched result proves nothing")

    # --- V8 fail-open --------------------------------------------------------
    if patched.tier == tier.LIGHT and patched.by_floor and not patched.abstained:
        ok("V-GSDX-FAIL-OPEN", "an exploding engine degrades to the floor, never raises")
    else:
        bad("V-GSDX-FAIL-OPEN", f"engine failure produced {patched.tier!r}")

    # --- V9 heartbeat advances on a NON-firing judgement ---------------------
    with tempfile.TemporaryDirectory() as d:
        env_before = os.environ.get("CLAUDE_STATE_DIR")
        os.environ["CLAUDE_STATE_DIR"] = d
        try:
            import importlib
            hb = importlib.reload(heartbeat)
            before = hb.read().get("judgements", 0)
            hb.record(tier.LIGHT, by_floor=True, abstained=False,
                      informative=False, reason="floor")
            after = hb.read().get("judgements", 0)
            rate_none = hb.informative_rate()
        finally:
            if env_before is None:
                os.environ.pop("CLAUDE_STATE_DIR", None)
            else:
                os.environ["CLAUDE_STATE_DIR"] = env_before
            importlib.reload(heartbeat)
    if after == before + 1:
        ok("V-GSDX-HEARTBEAT",
           f"advanced {before}->{after} on a floor judgement that emitted nothing")
    else:
        bad("V-GSDX-HEARTBEAT",
            f"did not advance ({before}->{after}) -- 'did it run' stays unanswerable")
    if rate_none == 0.0:
        ok("V-GSDX-RATE-DENOM", "informative_rate is 0.0 with a real denominator")
    else:
        bad("V-GSDX-RATE-DENOM", f"expected 0.0 after one floor judgement, got {rate_none}")

    # --- V10/V11 the hook itself, driven as a real child process -------------
    if not Path(NODE).is_file():
        bad("V-GSDX-HOOK", f"node not found at {NODE} -- hook behaviour unverified")
    else:
        payload = json.dumps({"prompt": "deploy the plugin to the live server "
                                        "and restart it", "session_id": "vgate"})
        r = subprocess.run([NODE, str(HOOK)], input=payload, capture_output=True,
                           text=True, timeout=30)
        emitted = ""
        if r.returncode == 0 and r.stdout.strip():
            try:
                emitted = (json.loads(r.stdout)
                           .get("hookSpecificOutput", {})
                           .get("additionalContext", ""))
            except json.JSONDecodeError:
                emitted = ""
        if r.returncode == 0 and "MEASURED" in emitted and "FORENSIC" in emitted:
            ok("V-GSDX-HOOK", "hook emitted a measured tier in hookSpecificOutput")
        else:
            bad("V-GSDX-HOOK",
                f"rc={r.returncode} stdout={r.stdout[:120]!r} stderr={r.stderr[:120]!r}")

        r2 = subprocess.run([NODE, str(HOOK)], input="{not json",
                            capture_output=True, text=True, timeout=30)
        if r2.returncode == 0 and not r2.stdout.strip():
            ok("V-GSDX-HOOK-FAIL-OPEN", "malformed payload -> exit 0, silence")
        else:
            bad("V-GSDX-HOOK-FAIL-OPEN",
                f"rc={r2.returncode} stdout={r2.stdout[:80]!r}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
