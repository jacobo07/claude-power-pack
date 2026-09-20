#!/usr/bin/env python3
"""V-gates for applicability-aware selection over the authoritative corpus.

The READ half of UCR-CIF W5. These gates answer: can a non-authority reach a
mission, can a stale owner, can a generic word decide which owner a proposal
belongs to, and can an instrument failure be told apart from an honest "no".

Two populations are driven deliberately:

  REAL   the live ledger, so the gates measure the corpus that ships rather
         than a fixture that agrees with me. The refuted/abstain/unresolved
         leak gates are only worth anything against real non-authoritative
         rows -- a synthetic one is a row I chose to make excludable.
  SYNTH  a temporary repo with a hand-built ledger, for the states the real
         corpus does not currently contain: an owner that has left the repo,
         a disposition class this consumer does not route, a schema from the
         future, and a population below the floor. A drill pinned to a real
         defect has an interest in that defect surviving; these have none.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from modules.ucr_cif import disposition_consumer as DC       # noqa: E402
from modules.ucr_cif.disposition_ledger import (             # noqa: E402
    DISPOSITIONS, SCHEMA_VERSION, text_terms, unit_terms,
)
from modules.ucr_cif.ownership_evidence import (             # noqa: E402
    DISTINCTIVE_MAX_HOLDERS,
)

PASSES = 0
FAILS = 0

# A proposal shaped like a system the corpus demonstrably owns.
P_OWNED = ("I propose a new Universal Knowledge Acquisition Fabric: an "
           "institutional operating system for continuous acquisition of "
           "knowledge from every session, with harvesting, distillation, "
           "curation, retrieval and a knowledge graph, plus 12 new dataset "
           "families for governance overlays.")
# The same institutional boilerplate about something the corpus has never
# heard of. It reached the wrong owner before the distinctiveness clause.
P_FOREIGN = ("I propose a new institutional operating system for espresso: a "
             "kernel that tracks bean freshness, grind size and portafilter "
             "temperature in the kitchen.")


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


# --------------------------------------------------------------- synthetic --
def _row(uid, owner, terms, disposition="EXTEND_EXISTING_OWNER",
         reviewed_by="test:synthetic", proposed="EXTEND_EXISTING_OWNER",
         name=None, conf=0.1):
    return {"uid": uid, "unit_class": "concept", "kind": "law",
            "claim_class": "INFERRED", "name": name or f"unit {uid}",
            "text": " ".join(terms), "line_start": 0, "line_end": 0,
            "proposed_disposition": proposed, "proposed_owner": owner,
            "confidence": conf, "evidence_terms": list(terms),
            "disposition": disposition, "disposition_reason": "synthetic",
            "reviewed_by": reviewed_by}


def build_repo(tmp: Path, rows, owners=("modules/synthetic_owner",),
               schema=SCHEMA_VERSION, filler=260):
    """A throwaway repo whose ledger says exactly what a case needs."""
    for o in owners:
        (tmp / o).mkdir(parents=True, exist_ok=True)
    all_rows = list(rows)
    for i in range(filler):
        # Filler keeps the population above the floor without ever matching a
        # probe: its terms are minted, so they cannot collide with a prompt.
        # It is owned by the LAST owner, never the subject: the first version
        # gave it the same owner the lifecycle case deletes, so removing that
        # directory took the whole population below the floor and the case
        # reported a refusal where it meant to measure an exclusion.
        all_rows.append(_row(f"filler{i:04d}", owners[-1],
                             (f"zqxfiller{i:04d}a", f"zqxfiller{i:04d}b")))
    doc = {"schema_version": schema, "corpus_units": len(all_rows),
           "indexed_files": 1, "compiled_corpus_id": "synthetic0000",
           "note": "synthetic", "rows": all_rows,
           "adjudication": {"adjudicator": "test:synthetic"}}
    p = tmp / DC.LEDGER_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")
    return tmp


def main() -> int:
    live = DC.select_for(P_OWNED)
    foreign = DC.select_for(P_FOREIGN)
    meta, rows = DC.load_ledger()

    # ---- the join produces something at all, against the real corpus ------
    check("V-W5-SEL-LIVE-ROUTES",
          live.routed and live.refusal is None,
          f"{len(live.owners)} owner(s) from {live.population} authoritative "
          f"units, corpus {live.corpus_id}")

    check("V-W5-SEL-OWNERS-ARE-REAL",
          all((REPO / o.owner).exists() for o in live.owners),
          "every routed owner resolves on disk: "
          + ", ".join(o.owner for o in live.owners))

    # ---- AUTHORITY: a candidate is not an authority ----------------------
    cand = [r for r in rows
            if r.get("proposed_disposition") in DISPOSITIONS
            and not r.get("disposition")]
    routed_uids = {u for o in live.owners for u in o.uids}
    check("V-W5-SEL-CANDIDATE-IS-NOT-AUTHORITY",
          len(cand) >= 500 and not (routed_uids & {r["uid"] for r in cand}),
          f"{len(cand)} unreviewed candidates in the real ledger, 0 routed")

    # ---- REFUTED / ABSTAIN / UNRESOLVED cannot leak as authority ---------
    refuted = [r for r in rows if not r.get("disposition")
               and r.get("reviewed_by")
               and str(r.get("disposition_reason") or "").startswith(
                   "candidate rejected")]
    unresolved = [r for r in rows if r.get("proposed_disposition") == "UNRESOLVED"]
    abstain = [r for r in rows if not r.get("disposition")
               and not r.get("reviewed_by")
               and r.get("proposed_disposition") != "UNRESOLVED"]
    check("V-W5-SEL-REFUTED-LEAK",
          len(refuted) >= 600 and not (routed_uids & {r["uid"] for r in refuted}),
          f"{len(refuted)} REFUTED rows, 0 reachable as authority")
    check("V-W5-SEL-ABSTAIN-LEAK",
          len(abstain) >= 400 and not (routed_uids & {r["uid"] for r in abstain}),
          f"{len(abstain)} ABSTAIN rows, 0 reachable as authority")
    check("V-W5-SEL-UNRESOLVED-LEAK",
          len(unresolved) >= 200
          and not (routed_uids & {r["uid"] for r in unresolved}),
          f"{len(unresolved)} UNRESOLVED rows, 0 reachable as authority")
    # The three are different populations and the store can tell them apart.
    # Collapsing any two would satisfy every gate above while destroying the
    # distinction the kernel is built on.
    check("V-W5-SEL-THREE-NEGATIVES-ARE-DISTINCT",
          len({len(refuted), len(abstain), len(unresolved)}) == 3
          and len(refuted) + len(abstain) + len(unresolved)
          == len(rows) - live.population - live.excluded_lifecycle
          - live.excluded_semantics,
          f"refuted={len(refuted)} abstain={len(abstain)} "
          f"unresolved={len(unresolved)} partition the non-authoritative half")

    # ---- APPLICABILITY: the foreign proposal must not reach an owner -----
    check("V-W5-SEL-FOREIGN-DOES-NOT-ROUTE",
          not foreign.routed and foreign.refusal is None,
          f"espresso proposal: 0 owners, {foreign.rejected_generic} unit(s) "
          f"rejected as generic-only overlap, population {foreign.population}")
    # ...and the reason it does not route is the distinctiveness clause, not
    # a failure to overlap at all. Without this, a matcher that simply never
    # matched would pass the gate above.
    check("V-W5-SEL-FOREIGN-DID-OVERLAP",
          foreign.rejected_generic > 0,
          f"{foreign.rejected_generic} unit(s) DID share >= "
          f"{DC.MIN_TERM_OVERLAP} terms and were refused for carrying no "
          "distinctive one")

    # ---- the prohibited constant is imported, never redefined ------------
    src = (REPO / "modules/ucr_cif/disposition_consumer.py").read_text(
        encoding="utf-8-sig")
    check("V-W5-SEL-DISTINCTIVE-NOT-REDEFINED",
          DISTINCTIVE_MAX_HOLDERS == 3
          and "DISTINCTIVE_MAX_HOLDERS =" not in src
          and "import DISTINCTIVE_MAX_HOLDERS" in src,
          "consumer imports DISTINCTIVE_MAX_HOLDERS=3 and defines no copy")

    # ---- one tokenizer, not two -----------------------------------------
    # "loop" is four letters and not a stop word, so it is admitted from an
    # entity (min length 4) and refused from body text (min length 5). Without
    # a word of exactly that length the fixture cannot see the two thresholds
    # at all: the first version used "compile the mission", every word of
    # which survives either threshold, and the mutation that collapses them
    # sailed through a gate named for exactly that property.
    probe = {"entities": ["Mission Loop"], "text": "compile the loop mission"}
    expected = {"mission": 3 + 1, "loop": 3, "compile": 1}
    check("V-W5-SEL-ONE-TOKENIZER",
          dict(unit_terms(probe)) == expected
          and dict(text_terms("compile the loop mission")) == {"compile": 1,
                                                               "mission": 1}
          and dict(text_terms("compile the loop mission", 4)) == {
              "compile": 1, "loop": 1, "mission": 1},
          "unit_terms delegates to text_terms with both length thresholds "
          "intact (entities >=4, body >=5)")

    # ---- determinism ------------------------------------------------------
    again = DC.select_for(P_OWNED)
    check("V-W5-SEL-DETERMINISTIC",
          again.to_dict() == live.to_dict(),
          "same proposal + same corpus -> byte-identical selection")

    # ---- context economy --------------------------------------------------
    everything = " ".join(sorted({t for r in rows
                                  for t in (r.get("evidence_terms") or [])}))
    flood = DC.select_for(everything)
    ob = DC.routing_obligation(flood) or ""
    check("V-W5-SEL-BOUNDED-MATERIALIZATION",
          len(flood.owners) <= DC.MAX_OWNERS
          and all(len(o.uids) <= DC.MAX_UIDS_PER_OWNER
                  and len(o.terms) <= DC.MAX_TERMS_PER_OWNER
                  for o in flood.owners)
          and len(ob) < 4000,
          f"a proposal containing EVERY corpus term yields "
          f"{len(flood.owners)} owners / {len(ob)} bytes, not 996 units")
    check("V-W5-SEL-NO-CORPUS-TEXT",
          all((r.get("text") or "")[:60].lower() not in ob.lower()
              for r in rows if len(r.get("text") or "") > 60),
          "no corpus unit body reaches the obligation; owners, counts and "
          "uids only")

    # ---- the four refusals are four, not one -----------------------------
    tmp = Path(tempfile.mkdtemp(prefix="w5sel-"))
    try:
        # (a) unreadable
        empty = tmp / "unreadable"
        empty.mkdir()
        s = DC.select_for(P_OWNED, repo=empty)
        check("V-W5-SEL-REFUSAL-UNREADABLE",
              not s.routed and s.refusal and "unreadable" in s.refusal,
              f"no ledger -> {s.refusal!r}")

        # (b) schema from the future
        r2 = build_repo(tmp / "schema", [], schema=SCHEMA_VERSION + 99)
        s = DC.select_for(P_OWNED, repo=r2)
        check("V-W5-SEL-REFUSAL-SCHEMA",
              not s.routed and s.refusal and "schema_version" in s.refusal,
              f"unknown schema -> {s.refusal!r}")

        # (c) population below the floor: an empty answer nobody may read as
        #     "nothing applies"
        r3 = build_repo(tmp / "thin", [], filler=3)
        s = DC.select_for(P_OWNED, repo=r3)
        check("V-W5-SEL-REFUSAL-POPULATION",
              not s.routed and s.refusal and "below floor" in s.refusal
              and s.population == 3,
              f"3 authoritative units -> {s.refusal!r}")

        # (d) a real population with nothing applicable: an ANSWER, no alarm
        r4 = build_repo(tmp / "fat", [], filler=300)
        s = DC.select_for(P_OWNED, repo=r4)
        check("V-W5-SEL-EMPTY-IS-AN-ANSWER",
              not s.routed and s.refusal is None and s.population == 300,
              "300 authoritative units, none applicable -> no refusal")

        # ---- LIFECYCLE: an owner that left the repo stops routing ---------
        terms = ("kobiiwidget", "flarnsprocket", "zetamorph")
        rows_l = [_row("live1", "modules/present_owner", terms),
                  _row("live2", "modules/present_owner", terms,
                       name="second unit")]
        r5 = build_repo(tmp / "life", rows_l,
                        owners=("modules/present_owner", "modules/filler_o"))
        probe_txt = "a new kernel for kobiiwidget flarnsprocket zetamorph"
        s_before = DC.select_for(probe_txt, repo=r5)
        shutil.rmtree(r5 / "modules/present_owner")
        s_after = DC.select_for(probe_txt, repo=r5)
        check("V-W5-SEL-LIFECYCLE-POSITIVE",
              s_before.routed
              and s_before.owners[0].owner == "modules/present_owner",
              "owner present -> routed")
        check("V-W5-SEL-LIFECYCLE-BREAKS-THE-JOIN",
              not s_after.routed and s_after.excluded_lifecycle == 2,
              "owner removed -> 2 units excluded_lifecycle, nothing routed")

        # ---- SEMANTICS: an unroutable class is a gap, not a neighbour ----
        rows_s = [_row("imp1", "modules/present_owner", terms,
                       disposition="IMPLEMENT"),
                  _row("imp2", "modules/present_owner", terms,
                       disposition="IMPLEMENT", name="second")]
        r6 = build_repo(tmp / "sem", rows_s,
                        owners=("modules/present_owner", "modules/filler_o"))
        s = DC.select_for(probe_txt, repo=r6)
        check("V-W5-SEL-UNSUPPORTED-CLASS-IS-A-GAP",
              not s.routed and s.excluded_semantics == 2
              and "IMPLEMENT" in s.classes_unsupported
              and "IMPLEMENT" in s.classes_present,
              "2 IMPLEMENT units: present, reported unsupported, not routed")

        # ---- DUPLICATE SUPPRESSION ---------------------------------------
        rows_d = [_row("dup1", "modules/present_owner", terms, name="Same Law"),
                  _row("dup2", "modules/present_owner", terms, name="Same Law"),
                  _row("dup3", "modules/present_owner", terms, name="Other Law")]
        r7 = build_repo(tmp / "dup", rows_d,
                        owners=("modules/present_owner", "modules/filler_o"))
        s = DC.select_for(probe_txt, repo=r7)
        check("V-W5-SEL-DUPLICATES-SUPPRESSED",
              s.routed and s.owners[0].units == 2
              and s.duplicates_suppressed == 1,
              "3 units, one an exact restatement -> 2 obligations, 1 suppressed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = PASSES + FAILS
    print(f"\nDISPOSITION_SELECTION_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
