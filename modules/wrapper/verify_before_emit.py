#!/usr/bin/env python3
"""verify_before_emit.py -- L-SELFCORR gate (Cognitive Leak Taxonomy, C70).

C69 P1 measured the single largest behavioral leak: 71 agent self-corrections
costing 370,081 output tokens -- a turn ships an unverified completion claim,
the next turn redoes it. C69 DETECTS the pattern post-hoc; this PREVENTS it at
the emission boundary.

Given a DRAFT emission plus the recent evidence stream (tool results / test
output the agent has actually seen this turn), `verify_before_emit` fires an
advisory when the draft asserts completion ("done", "tests pass", "fixed",
"listo") but the evidence stream carries NO verification signal (no observed
PASS/FAIL, exit code, N/N gate, etc.). It is the pre-emission complement of
HR-OUTPUT-002 (which fires when a ship claim lacks an observed PASS).

ADVISORY ONLY, fail-open: no completion claim -> silent; a claim WITH evidence
-> silent; only a claim WITHOUT evidence advises. It never blocks and never
fabricates -- it points at the specific unverified claim so the agent runs the
check before emitting, not after.

Wiring (Owner-side, HR-001 -- documented, not auto-registered): a pre-emission
hook (or the wrapper's output path) calls verify_before_emit(draft, evidence)
and, when a.advise, prepends a.message so the agent verifies first.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Assertive completion cues (EN + ES). Matched as whole words, case-insensitive.
_COMPLETION_CUES = (
    r"done", r"shipped", r"ready to ship", r"complete[d]?", r"finished",
    r"it works", r"works now", r"fixed", r"resolved", r"all green",
    r"tests? pass(?:ing|ed)?", r"passing", r"good to go",
    r"listo", r"funciona", r"arreglad[oa]", r"terminad[oa]", r"completad[oa]",
    r"solucionad[oa]", r"ya est[aá]",
)
_CLAIM_RX = re.compile(r"\b(" + "|".join(_COMPLETION_CUES) + r")\b", re.I)

# Negation / hedge immediately before the cue -> not an assertive claim.
_NEG_RX = re.compile(
    r"\b(not|isn'?t|aren'?t|won'?t|can'?t|no|nunca|todav[ií]a no|a[uú]n no|"
    r"almost|casi|not yet|sin)\s*\w{0,12}$", re.I)

# Verification signals in the evidence stream. Any one -> the claim is backed.
_EVIDENCE_RX = re.compile(
    r"(\bPASS\b|\bFAIL\b|exit[ =_-]?code|exit[ =]0|\bexit=\d|"
    r"\b\d+\s*/\s*\d+\b|DOMAIN_PASS|_PASS=|tests? (?:passed|failed)|"
    r"\bobserved\b|\bV-[A-Z0-9]|OK:|Ran \d+ test|\bassert)", re.I)


@dataclass
class Advisory:
    advise: bool
    claim: str | None = None
    message: str | None = None


def _completion_claim(draft: str) -> str | None:
    """The first assertive completion cue in the draft, or None. A cue directly
    preceded by a negation/hedge is skipped (not an assertion of completion)."""
    if not draft:
        return None
    for m in _CLAIM_RX.finditer(draft):
        prefix = draft[:m.start()].rstrip()
        if _NEG_RX.search(prefix):
            continue
        return m.group(0)
    return None


def has_verification(evidence: str) -> bool:
    """True if the evidence stream carries any observed verification signal."""
    return bool(evidence and _EVIDENCE_RX.search(evidence))


def verify_before_emit(draft: str, evidence: str = "") -> Advisory:
    """Fail-open advisory. Fires only when the draft asserts completion AND the
    evidence stream shows no verification was observed."""
    try:
        claim = _completion_claim(draft)
        if not claim:
            return Advisory(advise=False)
        # Evidence may be in the recent stream OR cited in the draft itself
        # (agent quoting the PASS/N-N it observed) -- either backs the claim.
        if has_verification(evidence) or has_verification(draft):
            return Advisory(advise=False, claim=claim)
        return Advisory(
            advise=True, claim=claim,
            message=(f"PP verify-before-emit: draft claims '{claim}' but no "
                     f"verification signal (PASS/FAIL, exit code, N/N gate) is "
                     f"in this turn's evidence. Run the check and observe the "
                     f"result BEFORE emitting -- prevents the P1 redo leak."))
    except Exception:  # noqa: BLE001 -- absolute fail-open
        return Advisory(advise=False)


def main(argv=None) -> int:
    import argparse
    import sys
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--draft", default=None)
    ap.add_argument("--evidence", default="")
    args = ap.parse_args(argv)
    draft = args.draft if args.draft is not None else sys.stdin.read()
    a = verify_before_emit(draft, args.evidence)
    if a.advise:
        print(a.message)
        return 1
    print(f"# silent (claim={a.claim})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
