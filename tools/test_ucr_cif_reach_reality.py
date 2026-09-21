"""PR-W7-* -- Production Reality for the W7 reach calibration.

Two kinds of gate, kept apart on purpose.

CONTROL FACTS (PR-W7-C*) re-derive this wave's headline claims from the
persisted measurement and assert them. A number in a report that nothing
re-checks is prose; these make the report's claims break the build when
they stop being true.

LIVE DRIVES (PR-W7-L*) run the REAL `sdd_tier.evaluate` in a FRESH
SUBPROCESS -- no warm ledger, no shared interpreter state, no fixture --
against REAL repositories on this host, and assert what the agent would
actually have been shown.

One gate here is a CHARACTERIZATION, marked as such: it pins the selector
saturation this wave discovered. It is EXPECTED to go red the day
applicability is repaired, and must then be inverted in place rather than
deleted -- the diff between the two versions is the evidence that the
defect existed.

Run:  python tools/test_ucr_cif_reach_reality.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

REPORT = PP_ROOT / "vault" / "audits" / "ucr_cif" / "w7_reach_control.json"
SHADOW = PP_ROOT / "vault" / "audits" / "ucr_cif" / "w7_shadow.json"

_PASS = 0
_FAIL = 0


def _ok(gate: str, ev: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  OK   {gate}  {ev}")


def _fail(gate: str, diag: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}  {diag}")


def _check(gate: str, cond: bool, ev: str, diag: str = "") -> None:
    _ok(gate, ev) if cond else _fail(gate, diag or ev)


# --- a real prompt, of the shape this estate actually issues ------------
_REAL_INTENT = (
    "Extend the knowledge acquisition module so a governance overlay "
    "decision is recorded with its provenance, and wire deep research "
    "evidence into the same ledger before the spec is written."
)
_FOREIGN_INTENT = (
    "Add a barista training workflow for the espresso machine so the "
    "cafe staff rota schema tracks milk steaming certification."
)

_DRIVER = r"""
import json, sys
sys.path.insert(0, %(root)r)
from modules.pp_agents.signals import sdd_tier
sig = sdd_tier.evaluate(prompt=%(prompt)r, cwd=%(cwd)r)
out = {
    "emitted": sig is not None,
    "named_owners": bool(sig and "ADJUDICATED evidence" in (sig.advisory or "")),
    "advisory_bytes": len((sig.advisory or "").encode("utf-8")) if sig else 0,
    "actionable_bytes": len((sig.actionable or "").encode("utf-8")) if sig else 0,
}
print(json.dumps(out))
"""


def _drive(prompt: str, cwd: Path) -> dict:
    """Run the live signal in a fresh interpreter and return what it said."""
    code = _DRIVER % {"root": str(PP_ROOT), "prompt": prompt,
                      "cwd": str(cwd)}
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, timeout=180,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"driver exit {proc.returncode}: "
                           f"{proc.stderr[-300:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


# ------------------------------------------------------------- control
def t_control_facts() -> None:
    if not REPORT.exists():
        _fail("PR-W7-C0-REPORT-PRESENT",
              f"{REPORT} missing -- run tools/ucr_cif_reach.py --funnel")
        return
    rep = json.loads(REPORT.read_text(encoding="utf-8"))["prompt_side"]
    gt = rep["ground_truth"]

    _check("PR-W7-C1-REACH-MEASURED-ON-REAL-INTENTS",
           rep["engineering_population"] >= 500
           and rep["reached_tier2"] > 0,
           f"{rep['engineering_population']} real prompts from "
           f"{rep['sessions_sampled']} sessions; "
           f"{rep['reached_tier2']} reached Tier>=2",
           "population too small to support a reach claim")

    _check("PR-W7-C2-USEFUL-POSITIVE-EXISTS",
           rep["owners_rendered"] > 0 and gt["tp"] > 0,
           f"{rep['owners_rendered']} prompts were shown owners; "
           f"{gt['tp']} of them landed in a routed owner path",
           "no positive case -- the boundary never usefully fired")

    _check("PR-W7-C3-THE-MISS-IS-REAL-AND-COUNTED",
           rep["owners_computed_but_silent"] > 0 and gt["fn"] > 0,
           f"{rep['owners_computed_but_silent']} prompts had owners "
           f"COMPUTED and rendered to nobody; {gt['fn']} of those are "
           "independently labelled RELEVANT",
           "no measured miss -- the gap claim is unsupported")

    _check("PR-W7-C4-NO-FALSE-ACTIVATION",
           gt["fp"] == 0,
           f"FP={gt['fp']} against TN={gt['tn']} -- the shipped boundary "
           "showed an owner to nobody whose work went elsewhere")

    _check("PR-W7-C5-CORRECT-OWNER-NOT-MERELY-AN-OWNER",
           gt["tp_correct_owner"] == gt["tp"],
           f"{gt['tp_correct_owner']}/{gt['tp']} true positives routed "
           "the owner the work actually landed in")

    _check("PR-W7-C6-DENOMINATOR-IS-EXPOSED",
           gt["labelled"] < rep["judgeable"]
           and sum(gt["labels"].values()) == rep["judgeable"],
           f"labelled {gt['labelled']} of {rep['judgeable']}; every "
           f"unjudged case is named: {sorted(gt['labels'])}",
           "the label counts do not reconstruct the judgeable population")

    unl = sum(v for k, v in gt["labels"].items() if k.startswith("UNL"))
    _check("PR-W7-C7-UNLABELLED-NEVER-BECAME-NEGATIVE",
           unl > 0 and gt["tn"] + gt["fp"] + gt["tp"] + gt["fn"]
           == gt["labelled"],
           f"{unl} unlabelled cases sit OUTSIDE the confusion matrix, "
           f"which sums to the labelled population exactly")


def t_shadow_facts() -> None:
    """Score the candidates by RUNNING the scorer, never by reading its file.

    The first version of this read `w7_shadow.json` from disk. Mutation W30
    then broke the scorer's population and every assertion here still
    passed, because a stale artifact answers exactly as a correct one does.
    A gate that reads a producer's output is a reader, not a consumer --
    the distinction W5 was called to make, reproduced inside W7's own
    evidence. The scorer is now imported and driven.
    """
    if not REPORT.exists():
        _fail("PR-W7-S0-REPORT-PRESENT", f"{REPORT} missing")
        return
    sys.path.insert(0, str(PP_ROOT / "tools"))
    import ucr_cif_shadow as shadow  # noqa: PLC0415

    cases = [c for c in json.loads(REPORT.read_text(encoding="utf-8"))[
        "prompt_side"]["cases"] if not c.get("is_slash_command")]
    calib, holdout = shadow._split(cases)
    _check("PR-W7-S0-HOLDOUT-IS-A-REAL-SPLIT",
           len(calib) > 100 and len(holdout) > 100
           and len(calib) + len(holdout) == len(cases),
           f"calibration {len(calib)} + holdout {len(holdout)} = "
           f"{len(cases)}, split by session digest so no session "
           "straddles the boundary")

    sh = {"holdout": [shadow.score(holdout, p) for p in shadow.POLICIES],
          "whole": [shadow.score(cases, p) for p in shadow.POLICIES]}
    hold = {s["policy"]: s for s in sh["holdout"]}
    ctrl = hold["P0-CONTROL-create_spec"]

    _check("PR-W7-S1-CONTROL-IS-PRECISE-ON-THE-HOLDOUT",
           ctrl["precision"] == 1.0 and ctrl["false_activation_rate"] == 0.0,
           f"holdout precision {ctrl['precision']:.2f}, FAR "
           f"{ctrl['false_activation_rate']:.2f}")

    beat = [p for p, s in hold.items()
            if p != "P0-CONTROL-create_spec"
            and (s["precision"] or 0) >= (ctrl["precision"] or 0)
            and (s["recall"] or 0) > (ctrl["recall"] or 0)]
    _check("PR-W7-S2-NO-PARETO-IMPROVING-CANDIDATE",
           not beat,
           "no candidate raised recall without losing precision on the "
           "holdout -- the rejection is measured, not assumed",
           f"candidates claiming Pareto improvement: {beat}")

    dominated = [p for p, s in hold.items()
                 if p.startswith(("P2", "P5"))
                 and (s["recall"] or 0) < (ctrl["recall"] or 0)]
    _check("PR-W7-S3-INTENT-FILTERS-ARE-STRICTLY-DOMINATED",
           len(dominated) == 2,
           f"{dominated} score BELOW the control on recall as well as "
           "precision -- narrowing by intent loses on both axes")

    # Two instruments, one claim. The funnel and the shadow scorer build
    # their populations independently, so agreement is evidence and
    # disagreement localises a denominator bug in one of them. Measured
    # 2026-09-21: the shadow first scored over the whole stream, which
    # handed the control 132 free true negatives from Tier-1 prompts no
    # candidate is ever offered, and halved every false-activation rate.
    whole = {s["policy"]: s for s in sh["whole"]}
    wctrl = whole["P0-CONTROL-create_spec"]
    rep = json.loads(REPORT.read_text(encoding="utf-8"))["prompt_side"]
    g = rep["ground_truth"]
    _check("PR-W7-S5-THE-TWO-INSTRUMENTS-AGREE",
           (wctrl["tp"], wctrl["fp"], wctrl["fn"], wctrl["tn"])
           == (g["tp"], g["fp"], g["fn"], g["tn"]),
           f"shadow control {wctrl['tp']}/{wctrl['fp']}/{wctrl['fn']}/"
           f"{wctrl['tn']} reproduces the funnel's "
           f"{g['tp']}/{g['fp']}/{g['fn']}/{g['tn']} exactly",
           f"shadow {(wctrl['tp'], wctrl['fp'], wctrl['fn'], wctrl['tn'])} "
           f"!= funnel {(g['tp'], g['fp'], g['fn'], g['tn'])} -- one of "
           "the two populations is wrong")

    noisy = hold["P1-ANY-OWNER"]
    _check("PR-W7-S4-WIDENING-COST-IS-MEASURED",
           noisy["owner_slots_emitted"] > 4 * ctrl["owner_slots_emitted"],
           f"P1 emits {noisy['owner_slots_emitted']} owner slots against "
           f"the control's {ctrl['owner_slots_emitted']} on the same "
           f"holdout stream ({noisy['fires_on_judgeable']} vs "
           f"{ctrl['fires_on_judgeable']} signals)")


# ----------------------------------------------------------------- live
def t_live() -> None:
    shut = PP_ROOT                      # this worktree holds vault/plans
    try:
        got_shut = _drive(_REAL_INTENT, shut)
    except Exception as exc:  # noqa: BLE001
        _fail("PR-W7-L0-DRIVER", f"{type(exc).__name__}: {exc}")
        return

    _check("PR-W7-L1-LIVE-MISS-IN-A-SPEC-BEARING-REPO",
           not got_shut["emitted"],
           "a real L/XL construction intent, run through the live signal "
           "in a fresh process with this worktree as cwd, produces NO "
           "advisory -- the spec exists, so the door is shut",
           f"{got_shut}")

    with tempfile.TemporaryDirectory(prefix="w7-pr-") as raw:
        fresh = Path(raw) / "greenfield"
        fresh.mkdir()
        (fresh / ".git").mkdir()
        got_open = _drive(_REAL_INTENT, fresh)
        got_foreign = _drive(_FOREIGN_INTENT, fresh)

    _check("PR-W7-L2-LIVE-POSITIVE-IN-A-GREENFIELD-REPO",
           got_open["emitted"] and got_open["named_owners"],
           f"the SAME intent in a repo with no spec names owners "
           f"({got_open['advisory_bytes']} B advisory, "
           f"{got_open['actionable_bytes']} B actionable)",
           f"{got_open}")

    _check("PR-W7-L3-LIVE-TRUE-NEGATIVE",
           got_foreign["emitted"] and not got_foreign["named_owners"],
           "a foreign-domain L/XL intent still gets its tier advisory and "
           "is routed NO owner -- the door being open is not a licence",
           f"{got_foreign}")

    _check("PR-W7-L4-THE-DOOR-NOT-THE-PROPOSAL-DECIDES",
           got_open["named_owners"] and not got_shut["emitted"],
           "one proposal, two repositories, opposite outcomes: activation "
           "is decided by a property of the DIRECTORY while its value is "
           "a property of the PROPOSAL")


# ------------------------------------------------- characterization pin
def t_characterization() -> None:
    """CHARACTERIZATION -- pins a DEFECT, not a desired behaviour.

    When applicability precision is repaired this gate MUST fail. Invert
    it in place at that point; do not delete it. A characterization that
    is deleted when it turns takes the evidence of the defect with it.
    """
    if not REPORT.exists():
        _fail("PR-W7-X1-SELECTOR-SATURATION", "report missing")
        return
    cases = json.loads(REPORT.read_text(encoding="utf-8"))["prompt_side"][
        "cases"]
    xl = [c for c in cases if c.get("reached_tier2")
          and c.get("length_bucket") == "xl"
          and c.get("miss_layer") not in ("cwd_unreadable", "error")]
    routed = [c for c in xl if c.get("owners_routed")]
    rate = len(routed) / len(xl) if xl else 0.0
    _check("PR-W7-X1-SELECTOR-SATURATION-ON-LONG-PROMPTS",
           xl and rate > 0.90,
           f"CHARACTERIZATION: {len(routed)}/{len(xl)} = {100 * rate:.1f} % "
           "of long real prompts route at least one owner. The "
           "DISTINCTIVE-term clause was proven on SHORT synthetic "
           "proposals and does not discriminate at this length. This gate "
           "is expected to go RED when applicability is repaired -- "
           "invert it in place then, never delete it",
           f"rate {rate:.3f} -- if applicability was just fixed, INVERT "
           "this gate rather than removing it")


def main() -> int:
    print("== PR-W7 PRODUCTION REALITY (control policy) ==")
    t_control_facts()
    t_shadow_facts()
    t_live()
    t_characterization()
    total = _PASS + _FAIL
    print(f"\nW7_PRODUCTION_REALITY_PASS={_PASS}/{total}  "
          f"threshold={total}/{total}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
