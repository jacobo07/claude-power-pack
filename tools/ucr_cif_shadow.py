"""UCR-CIF W7 -- shadow evaluation of candidate activation policies.

SHADOW ONLY. Nothing here is wired into any gate, hook or signal. It
replays candidate emit-rules over the control report's already-derived
cases and reports what each WOULD have activated, so a policy can be
compared before it changes anybody's session.

ANTI-GAMING (brief sec. XXVI / XLVII). Each candidate is stated as a
MECHANISM -- a sentence about the mission lifecycle that would be worth
saying even if it scored badly -- and all of them were written down before
the confusion matrices were computed. The population is split by SESSION
digest, not by case, so the same session cannot appear on both sides; the
winner is re-scored on the holdout it was not selected on. A candidate
that can only be justified as "these examples pass" is rejected whatever
it scores.

The oracle's labels come from `reach_ground_truth` and are POST-HOC: they
describe where the work actually landed, never what was knowable at the
prompt.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

#: Intent families in which the decision UCR-CIF exists to influence --
#: "build a new one" versus "extend the one that exists" -- is actually on
#: the table. Repair and verification of an existing thing have already
#: chosen their location.
_CONSTRUCTION = frozenset({"create", "integrate", "extend"})


@dataclass(frozen=True)
class Policy:
    name: str
    mechanism: str
    emit: Callable[[dict], bool]


def _owners(c: dict) -> list:
    return c.get("owners_routed") or []


POLICIES: tuple[Policy, ...] = (
    Policy(
        "P0-CONTROL-create_spec",
        "Speak only when the repository has no spec at all. The shipped "
        "W6 rule: absence of a spec is the moment a new thing is about to "
        "be specified.",
        lambda c: c.get("miss_layer") == "none",
    ),
    Policy(
        "P1-ANY-OWNER",
        "Speak whenever the corpus holds adjudicated authority about the "
        "proposal. The VALUE of the signal is a property of the proposal; "
        "the current CONDITION is a property of the directory, and the "
        "two are independent.",
        lambda c: bool(_owners(c)),
    ),
    Policy(
        "P2-CONSTRUCTION-INTENT",
        "Speak when authority exists AND the prompt is about building, "
        "integrating or extending. A correct owner delivered during a "
        "repair arrives after the location was already chosen.",
        lambda c: bool(_owners(c))
        and c.get("semantic_class") in _CONSTRUCTION,
    ),
    Policy(
        "P3-TIER3-ONLY",
        "Speak when authority exists AND the work is Strategic/Platform. "
        "Duplication is most expensive where it becomes a standard.",
        lambda c: bool(_owners(c)) and c.get("tier") == 3,
    ),
    Policy(
        "P4-STRONG-EVIDENCE",
        "Speak when the corpus holds SUBSTANTIAL adjudicated authority "
        "about the owner, measured in units, not merely one match.",
        lambda c: sum(1 for _ in _owners(c)) > 0
        and int(c.get("owner_units") or 0) >= 10,
    ),
    Policy(
        "P5-CONSTRUCTION-AND-STRONG",
        "Both bounds at once: the decision must be open, and the corpus "
        "must have something substantial to say about it.",
        lambda c: bool(_owners(c))
        and c.get("semantic_class") in _CONSTRUCTION
        and int(c.get("owner_units") or 0) >= 10,
    ),
)


def _split(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split by SESSION digest so no session straddles the boundary.

    Splitting by case would put two prompts of one session on opposite
    sides, and they share a repository, a moment and usually an intent --
    which leaks the answer across the boundary the split exists to create.
    """
    calib, hold = [], []
    for c in cases:
        bucket = int(str(c.get("session_sha", "0"))[:8] or "0", 16) % 2
        (calib if bucket == 0 else hold).append(c)
    return calib, hold


def _judgeable(cases: list[dict]) -> list[dict]:
    """Cases any candidate could possibly act on.

    Every policy here is evaluated INSIDE `sdd_tier`, which returns None
    below Tier 2 before the gate is ever consulted. A Tier-1 prompt can
    therefore never be a false activation for any of them, and counting it
    as a true negative would dilute every false-activation rate with cases
    no candidate was ever offered. Measured 2026-09-21: scoring over the
    whole stream inflated the control's TN from 115-labelled to 247 and
    halved the candidates' FAR.
    """
    return [c for c in cases
            if c.get("reached_tier2")
            and c.get("miss_layer") not in ("cwd_unreadable", "error")]


def score(cases: list[dict], pol: Policy) -> dict:
    labelled = [c for c in _judgeable(cases)
                if c.get("gt_label") in ("RELEVANT", "NOT_RELEVANT")]
    tp = fp = fn = tn = 0
    exact = 0
    for c in labelled:
        fires = pol.emit(c)
        rel = c.get("gt_label") == "RELEVANT"
        if fires and rel:
            tp += 1
            if set(_owners(c)) & set(c.get("gt_owner_hits") or []):
                exact += 1
        elif fires and not rel:
            fp += 1
        elif (not fires) and rel:
            fn += 1
        else:
            tn += 1
    # Volume is measured over EVERY judgeable case, not only the labelled
    # ones: a policy's noise is paid on the whole stream, while its
    # accuracy can only be read on the part an oracle could judge.
    judgeable = _judgeable(cases)
    fired = [c for c in judgeable if pol.emit(c)]
    return {
        "policy": pol.name,
        "labelled": len(labelled),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "tp_correct_owner": exact,
        "precision": (tp / (tp + fp)) if (tp + fp) else None,
        "recall": (tp / (tp + fn)) if (tp + fn) else None,
        "false_activation_rate": (fp / (fp + tn)) if (fp + tn) else None,
        "fires_on_judgeable": len(fired),
        "judgeable": len(judgeable),
        "owner_slots_emitted": sum(len(_owners(c)) for c in fired),
    }


def _fmt(s: dict) -> str:
    def pct(v):
        return "  n/a " if v is None else f"{100 * v:5.1f}%"
    return (f"  {s['policy']:<26} "
            f"P{pct(s['precision'])} R{pct(s['recall'])} "
            f"FAR{pct(s['false_activation_rate'])} "
            f"| TP {s['tp']:<3} FP {s['fp']:<3} FN {s['fn']:<3} "
            f"TN {s['tn']:<3} "
            f"| fires {s['fires_on_judgeable']}/{s['judgeable']} "
            f"owners {s['owner_slots_emitted']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", default="vault/audits/ucr_cif/"
                                        "w7_reach_control.json")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    cases = data["prompt_side"]["cases"]
    cases = [c for c in cases if not c.get("is_slash_command")]
    calib, hold = _split(cases)

    print("== SHADOW POLICY COMPARISON ==")
    print(f"  cases {len(cases)}  calibration {len(calib)}  "
          f"holdout {len(hold)}  (split by session digest)")
    out = {"calibration": [], "holdout": [], "mechanisms": {}}
    print("\n  -- CALIBRATION HALF --")
    for pol in POLICIES:
        s = score(calib, pol)
        out["calibration"].append(s)
        out["mechanisms"][pol.name] = pol.mechanism
        print(_fmt(s))
    print("\n  -- HOLDOUT HALF (not used to choose anything) --")
    for pol in POLICIES:
        s = score(hold, pol)
        out["holdout"].append(s)
        print(_fmt(s))
    print("\n  -- WHOLE POPULATION --")
    for pol in POLICIES:
        print(_fmt(score(cases, pol)))
        out.setdefault("whole", []).append(score(cases, pol))

    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
