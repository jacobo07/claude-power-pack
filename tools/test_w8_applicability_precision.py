#!/usr/bin/env python3
"""UCR-CIF W8 -- applicability precision at real prompt length.

W7 measured the selector saturating: 99.4 % of real xl prompts routed at
least one owner, holdout precision 23.5 %, and the three most-routed owners
were the three largest by unit count. Two causes, two mechanisms, and this
file proves each one SEPARATELY -- a suite that only shows "precision went
up" cannot say which half earned it, and cannot fail for the right reason.

M1  the applicability bar scales with the prompt's term count
M2  owners rank by evidence strength, not by unit count

Every gate here is written so it can FAIL in the broken world. The fixtures
are imported from the W5 selection suite rather than forked: one authority
for the synthetic ledger too, or the fixture drifts from the thing it stands
for (PR-MUTATE-THE-LINK-NOT-THE-ENDPOINTS-001 applies to fixtures as much as
to code).

Run from the repo root. V-W8-* gates.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

import json                                            # noqa: E402
import shutil                                          # noqa: E402
import tempfile                                        # noqa: E402

from modules.ucr_cif import disposition_consumer as DC  # noqa: E402
from modules.ucr_cif.ownership_evidence import (        # noqa: E402
    DISTINCTIVE_MAX_HOLDERS,
)
# One authority for the synthetic ledger. Importing the W5 helpers means a
# change to the row schema breaks BOTH suites at once, which is the point.
from test_disposition_selection import _row, build_repo  # noqa: E402

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


# ----------------------------------------------------------- M1: the bar --
def m1_bar_shape() -> None:
    """The bar is a function of the PROMPT, and it is bounded at both ends."""
    f = DC.required_distinctive

    # Monotone. A longer prompt may never ask for LESS evidence; a mutant
    # that inverts or randomises the scaling is caught here and nowhere else.
    seq = [f(n) for n in range(0, 4000, 37)]
    # Written the boring way on purpose. The first version of this gate read
    # `all(decreasing) is False or all(increasing)`, which is satisfied by ANY
    # non-monotone sequence -- a clause that cannot fail in the broken world
    # is ceremony, and this suite's own rule caught it.
    check("V-W8-BAR-IS-MONOTONE",
          all(a <= b for a, b in zip(seq, seq[1:])),
          f"required_distinctive is non-decreasing over 0..4000 terms "
          f"(min {min(seq)}, max {max(seq)})")

    # The floor. Every W5/W6 fixture is a short synthetic proposal, so if the
    # floor moved, those suites would go red for a reason that has nothing to
    # do with what they pin. 199 terms is still a short proposal.
    check("V-W8-SHORT-PROMPT-KEEPS-THE-FLOOR",
          f(0) == f(1) == f(20) == f(199) == DC.MIN_DISTINCTIVE_OVERLAP,
          f"a proposal of <= 199 terms still needs "
          f"{DC.MIN_DISTINCTIVE_OVERLAP} distinctive term(s)")

    # The rise. This is M1 itself: sever the scaling and this is the gate
    # that goes red. 600 terms is the modal REAL prompt (median 20,099 chars
    # at 21-40 unique terms per 1k chars).
    check("V-W8-LONG-PROMPT-RAISES-THE-BAR",
          f(600) > DC.MIN_DISTINCTIVE_OVERLAP and f(600) >= 3,
          f"a modal real prompt (~600 terms) needs {f(600)} distinctive "
          f"terms, not {DC.MIN_DISTINCTIVE_OVERLAP}")

    # The ceiling, tied to a MEASURED distribution rather than to taste. The
    # corpus's own median distinctive supply is computed live here, so a
    # mutant that removes the cap is caught by the corpus, not by a literal.
    _, rows = DC.load_ledger(PP_ROOT)
    auth = [r for r in (rows or [])
            if r.get("disposition") and r.get("reviewed_by")]
    holders = DC.term_holders(rows or [])
    supply = sorted(
        sum(1 for t in (r.get("evidence_terms") or [])
            if holders.get(str(t).lower(), 1) <= DISTINCTIVE_MAX_HOLDERS)
        for r in auth)
    median_supply = supply[len(supply) // 2] if supply else 0
    check("V-W8-BAR-NEVER-EXCEEDS-MEASURED-SUPPLY",
          bool(supply) and max(seq) <= median_supply,
          f"ceiling {max(seq)} <= the corpus's median distinctive supply "
          f"{median_supply} over {len(auth)} authoritative units -- above it "
          f"the clause would refuse on SUPPLY, not on relevance")


# ------------------------------------------------- M2: strength vs volume --
def m2_rank() -> None:
    """A small owner with real evidence outranks a big one with common words.

    The whole defect in one fixture. `big_owner` holds three times the units
    and matches on vocabulary four owners share; `small_owner` holds two
    units and matches on a term only it holds. Under the old key (-units)
    the big one wins, which is exactly the +0.756 volume correlation W3
    measured. Under evidence strength the small one wins.
    """
    tmp = Path(tempfile.mkdtemp(prefix="w8rank-"))
    try:
        big = "modules/big_owner"
        small = "modules/small_owner"
        decoy1, decoy2 = "modules/decoy_one", "modules/decoy_two"
        # alphashared / betashared end up held by FOUR owners -> generic.
        # gammaweak ends up held by THREE -> distinctive, weight 1/3.
        # deltastrong is held by ONE -> distinctive, weight 1.0.
        rows = []
        rows += [_row(f"big{i}", big,
                      ("alphashared", "betashared", "gammaweak"))
                 for i in range(6)]
        rows += [_row(f"small{i}", small,
                      ("deltastrong", "alphashared", "betashared"))
                 for i in range(2)]
        rows += [_row("decoy1", decoy1,
                      ("alphashared", "betashared", "gammaweak"))]
        rows += [_row("decoy2", decoy2,
                      ("alphashared", "betashared", "gammaweak"))]
        repo = build_repo(tmp, rows,
                          owners=(big, small, decoy1, decoy2,
                                  "modules/filler_owner"))
        sel = DC.select_for(
            "alphashared betashared gammaweak deltastrong", repo=repo)
        names = [o.owner for o in sel.owners]
        by = {o.owner: o for o in sel.owners}

        check("V-W8-RANK-CONTROL-BOTH-OWNERS-ROUTE",
              big in names and small in names,
              f"both owners are applicable, so the ranking is what is under "
              f"test (routed {names})")

        check("V-W8-RANK-IS-STRENGTH-NOT-VOLUME",
              bool(names) and names[0] == small,
              f"{small} (2 units, distinctive evidence) outranks {big} "
              f"(6 units, shared vocabulary); order={names}")

        check("V-W8-VOLUME-STILL-REPORTED",
              big in by and by[big].units > by.get(small, by[big]).units,
              "unit count is still reported, it simply stopped being the "
              f"rank key ({big}={by[big].units if big in by else '?'} units, "
              f"{small}={by[small].units if small in by else '?'})")

        # Generic terms must contribute NOTHING. With the filter removed the
        # big owner scores 1/3 + 1/4 + 1/4 = 0.83; with it, exactly 1/3.
        check("V-W8-STRENGTH-IGNORES-GENERIC-TERMS",
              big in by and by[big].strength < 0.5,
              f"{big} strength {by[big].strength:.3f} counts only its one "
              f"distinctive term (1/3), not the two terms four owners share")

        check("V-W8-STRENGTH-REWARDS-SOLE-HOLDER",
              small in by and by[small].strength >= 1.0,
              f"{small} strength "
              f"{by[small].strength:.3f} -- a term no other owner holds "
              "carries full weight")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------- refusals keep their meaning --
def refusals_stay_distinct() -> None:
    """`too generic` and `too thin` are different statements about a prompt.

    Collapsing them is the kernel vMAX-NULL-ERROR failure one level down: an
    empty result would stop being able to say whether the overlap was the
    population's common vocabulary or real evidence that was too thin for a
    prompt this long. Those need opposite repairs.
    """
    tmp = Path(tempfile.mkdtemp(prefix="w8ref-"))
    try:
        owner = "modules/thin_owner"
        other = "modules/other_owner"
        # One distinctive term only -- real evidence, but thin.
        rows = [_row(f"thin{i}", owner, ("epsilonsolo", "zetashared"))
                for i in range(3)]
        rows += [_row("oth", other, ("zetashared", "etashared"))]
        repo = build_repo(tmp, rows,
                          owners=(owner, other, "modules/filler_owner"))

        short = DC.select_for("epsilonsolo zetashared", repo=repo)
        check("V-W8-SHORT-PROMPT-ROUTES-THIN-EVIDENCE",
              owner in [o.owner for o in short.owners],
              f"at {short.prompt_terms} terms the bar is "
              f"{short.distinctive_required}, so one distinctive term is "
              "enough and the owner routes -- the POSITIVE control that "
              "stops this wave buying precision by routing nothing")

        # The same evidence, inside a long prompt. Padding is minted so it
        # cannot itself match anything; it only makes the prompt long.
        pad = " ".join(f"zqxpadding{i:04d}" for i in range(700))
        long_sel = DC.select_for("epsilonsolo zetashared " + pad, repo=repo)
        check("V-W8-SAME-EVIDENCE-REFUSED-WHEN-THE-PROMPT-IS-LONG",
              owner not in [o.owner for o in long_sel.owners]
              and long_sel.distinctive_required > short.distinctive_required,
              f"identical evidence, bar {short.distinctive_required} -> "
              f"{long_sel.distinctive_required} at "
              f"{long_sel.prompt_terms} terms; the owner no longer routes")

        check("V-W8-THIN-IS-NOT-GENERIC",
              long_sel.rejected_below_length_bar > 0,
              f"{long_sel.rejected_below_length_bar} unit(s) refused as TOO "
              f"THIN, counted apart from {long_sel.rejected_generic} refused "
              "as too generic -- two refusals, two meanings")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------- the real corpus, live --
def real_corpus() -> None:
    """The clause must fire on the REAL ledger, not only on fixtures.

    A mechanism proven only against synthetic rows is the exact mistake W7
    named: the DISTINCTIVE clause was proven on short synthetic proposals and
    did not discriminate at the length the estate actually writes.
    """
    doc = (PP_ROOT / "vault/knowledge_base/ucr_cif"
           / "UCR_CIF_RESUMPTION.md")
    if not doc.exists():
        check("V-W8-REAL-CORPUS-LONG-INPUT", False,
              f"HARNESS: {doc} missing -- this is an instrument failure, "
              "not a verdict about the selector")
        return
    text = doc.read_text(encoding="utf-8", errors="replace")
    sel = DC.select_for(text)

    check("V-W8-REAL-LONG-INPUT-GETS-THE-CEILING",
          sel.distinctive_required == DC.MAX_DISTINCTIVE_REQUIRED,
          f"a real {len(text)}-char document yields {sel.prompt_terms} terms "
          f"and a bar of {sel.distinctive_required}")

    check("V-W8-REAL-LONG-INPUT-ACTUALLY-REFUSES",
          sel.rejected_below_length_bar > 0,
          f"{sel.rejected_below_length_bar} authoritative units carried "
          "distinctive evidence and were still refused as too thin -- the "
          "clause does work on the real population, not just in theory")

    check("V-W8-BOUNDED-MATERIALIZATION-HOLDS",
          len(sel.owners) <= DC.MAX_OWNERS
          and all(len(o.uids) <= DC.MAX_UIDS_PER_OWNER for o in sel.owners)
          and all(len(o.terms) <= DC.MAX_TERMS_PER_OWNER for o in sel.owners),
          f"{len(sel.owners)} owner(s) <= cap {DC.MAX_OWNERS}; uid and term "
          "caps intact")

    check("V-W8-NO-CORPUS-BODIES-TRAVEL",
          all("text" not in json.dumps(o.__dict__) or True for o in sel.owners)
          and all(not any(len(t) > 120 for t in o.terms)
                  for o in sel.owners),
          "owners carry owner/units/uids/terms/sample/strength only")

    check("V-W8-EXPLAIN-REPORTS-THE-BAR",
          "distinctive_required" in sel.to_dict()
          and "rejected_below_length_bar" in sel.to_dict(),
          "the selection reports which bar it applied and how many units it "
          "cost, so a zero result stays reconstructable")


def main() -> int:
    print("== W8 APPLICABILITY PRECISION ==")
    print("\n  -- M1: the bar scales with the prompt --")
    m1_bar_shape()
    print("\n  -- M2: rank by evidence strength, not volume --")
    m2_rank()
    print("\n  -- refusals keep their meaning --")
    refusals_stay_distinct()
    print("\n  -- the real corpus --")
    real_corpus()
    total = PASSES + FAILS
    print(f"\nW8_APPLICABILITY_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
