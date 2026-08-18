#!/usr/bin/env python3
"""test_research_engines.py — gates for the four deep_research engines.

Pure + offline: no network, no LLM, no disk writes.

The fixtures are the BUG, not a synthetic analogue. The vendor-blog URL shape,
the label-without-a-number, and the un-corroborated VERIFIED claim below are the
exact failure the 2026-08-18 topic-cluster run produced: a learning persisted
from a single vendor page, carrying no marker that its evidence was thin.

Run:  python test_research_engines.py
Exit: 0 = all gates pass, 1 = at least one gate failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from research_engines import (  # noqa: E402
    AXIS_BOUNDARY,
    AXIS_COUNTEREXAMPLE,
    AXIS_EVIDENCE,
    AXIS_MECHANISM,
    AXIS_TRANSFERABILITY,
    COVERAGE_COVERED,
    COVERAGE_THIN,
    COVERAGE_UNCLASSIFIED,
    COVERAGE_VENDOR_ONLY,
    EPI_DERIVED,
    EPI_HYPOTHESIS,
    EPI_OBSERVED,
    EPI_REJECTED,
    EPI_VERIFIED,
    FAMILY_ACADEMIC,
    FAMILY_MEASURED,
    FAMILY_PRACTITIONER,
    FAMILY_VENDOR,
    MIN_AXES_COVERED,
    QUALITY_HIGH,
    QUALITY_LOW,
    QUALITY_MEDIUM,
    axes_covered,
    build_capability_learnings_prompt,
    build_contradiction_prompt,
    build_decomposition_correction_prompt,
    build_decomposition_prompt,
    cap_epistemic,
    classify_source,
    decomposition_is_sufficient,
    epistemic_distribution,
    format_contradiction_section,
    format_labeled_learning,
    has_measurable_datum,
    landscape_verdict,
    missing_axes,
    normalize_axis,
    normalize_epistemic,
    parse_contradictions,
    parse_learning_records,
    rank_sources_for_extraction,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  --  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  --  {diagnostic}")


# The Owner's query, verbatim. Every engine is exercised against it.
QUERY = ("how do content teams know when a topic cluster is saturated and "
         "adding more articles stops helping")


# =========================================================================
# V-DECOMP-* — ENGINE 1
# =========================================================================

def gate_decomposition() -> None:
    print("\nV-DECOMP — Engine 1: problem decomposition")

    prompt = build_decomposition_prompt(QUERY, breadth=5)
    missing = [a for a in (AXIS_EVIDENCE, AXIS_MECHANISM, AXIS_BOUNDARY,
                           AXIS_COUNTEREXAMPLE, AXIS_TRANSFERABILITY)
               if a not in prompt]
    if not missing and QUERY in prompt:
        _ok("V-DECOMP-PROMPT-AXES",
            "all 5 axes + the topic present in the built prompt")
    else:
        _fail("V-DECOMP-PROMPT-AXES", f"missing from prompt: {missing}")

    # A decomposition on a single axis is a rephrasing, not a decomposition.
    narrow = [
        {"query": "what metrics measure topic cluster saturation",
         "axis": "EVIDENCE", "researchGoal": "..."},
        {"query": "what data shows saturation happening", "axis": "EVIDENCE",
         "researchGoal": "..."},
    ]
    ok, reason = decomposition_is_sufficient(narrow)
    if not ok and "1 axis" in reason:
        _ok("V-DECOMP-REJECTS-NARROW", f"single-axis set rejected: {reason[:60]}")
    else:
        _fail("V-DECOMP-REJECTS-NARROW",
              f"single-axis set was accepted (ok={ok}, reason={reason!r})")

    wide = narrow + [
        {"query": "why does adding pages eventually hurt rankings",
         "axis": "MECHANISM", "researchGoal": "..."},
        {"query": "which sites kept publishing and kept gaining traffic",
         "axis": "COUNTEREXAMPLE", "researchGoal": "..."},
    ]
    ok, reason = decomposition_is_sufficient(wide)
    if ok and len(axes_covered(wide)) == 3:
        _ok("V-DECOMP-ACCEPTS-WIDE",
            f"3-axis set accepted (floor {MIN_AXES_COVERED})")
    else:
        _fail("V-DECOMP-ACCEPTS-WIDE",
              f"3-axis set rejected (ok={ok}, axes={axes_covered(wide)})")

    gaps = missing_axes(wide)
    if set(gaps) == {AXIS_BOUNDARY, AXIS_TRANSFERABILITY}:
        _ok("V-DECOMP-NAMES-GAPS", f"gaps named exactly: {gaps}")
    else:
        _fail("V-DECOMP-NAMES-GAPS", f"unexpected gap set: {gaps}")

    correction = build_decomposition_correction_prompt(wide, breadth=5)
    if AXIS_BOUNDARY in correction and AXIS_TRANSFERABILITY in correction:
        _ok("V-DECOMP-CORRECTION",
            "corrective re-ask names the uncovered axes")
    else:
        _fail("V-DECOMP-CORRECTION", "correction prompt omits the gaps")

    # An unknown axis label must not be silently bucketed into a real one, or
    # measured coverage inflates with questions nobody classified.
    if normalize_axis("EVIDENCE") == AXIS_EVIDENCE and normalize_axis("vibes") is None:
        _ok("V-DECOMP-AXIS-NORM",
            "canonical label kept, unknown label -> None (no silent default)")
    else:
        _fail("V-DECOMP-AXIS-NORM",
              f"normalize_axis mismatch: {normalize_axis('vibes')!r}")


# =========================================================================
# V-LANDSCAPE-* — ENGINE 2
# =========================================================================

# THE BUG, verbatim in shape: the single vendor blog that founded the original
# saturation learning. A conversion surface with no measurement of its own.
VENDOR_PAGE = {
    "url": "https://theseoengine.example/blog/topic-cluster-saturation",
    "title": "Topic Cluster Saturation: The Complete Guide",
    "snippet": "Learn how our platform detects saturation. Book a demo today.",
    "body": "Our platform helps agencies scale content. Book a demo to see "
            "how our software finds saturated clusters. Free trial available. "
            "Talk to sales about pricing plans.",
}

ACADEMIC_PAGE = {
    "url": "https://link.springer.com/article/10.1007/s11031-006-9048-3",
    "title": "Diminishing returns in topical content expansion",
    "snippet": "Abstract. We hypothesise that marginal returns decline.",
    "body": "Abstract. Methodology. We analysed 412 sites over 18 months. "
            "The result was statistically significant (p < 0.01).",
}

PRACTITIONER_PAGE = {
    "url": "https://news.ycombinator.com/item?id=12345",
    "title": "What actually happened when we doubled our content output",
    "snippet": "Discussion of tradeoffs at scale.",
    "body": "In production we saw latency and throughput tradeoffs. Our "
            "architecture changed after we deployed the new pipeline.",
}

MEASURED_PAGE = {
    "url": "https://someco.example/engineering/content-postmortem",
    "title": "Post-mortem: why our traffic fell 34% after publishing more",
    "snippet": "We ran a 6 month test across 240 pages.",
    "body": "We ran an A/B test over 6 months across 240 pages. Our data "
            "shows a 34% decline in sessions and a 12% drop in impressions. "
            "Post-mortem: root cause was internal cannibalisation.",
}

VENDOR_WITH_DATA = {
    "url": "https://vendor.example/blog/our-study",
    "title": "We studied 500 sites",
    "snippet": "Book a demo.",
    "body": "We ran a study of 500 sites over 12 months. Our data shows a 22% "
            "lift. Free trial available, talk to sales about pricing plans.",
}


def gate_landscape() -> None:
    print("\nV-LANDSCAPE — Engine 2: source-family coverage gate")

    v = classify_source(**VENDOR_PAGE)
    if v["family"] == FAMILY_VENDOR and v["quality"] == QUALITY_LOW:
        _ok("V-LANDSCAPE-VENDOR", f"vendor page -> {v['family']}/{v['quality']}")
    else:
        _fail("V-LANDSCAPE-VENDOR", f"got {v['family']}/{v['quality']}")

    a = classify_source(**ACADEMIC_PAGE)
    if a["family"] == FAMILY_ACADEMIC and a["quality"] == QUALITY_HIGH:
        _ok("V-LANDSCAPE-ACADEMIC", f"springer -> {a['family']}/{a['quality']}")
    else:
        _fail("V-LANDSCAPE-ACADEMIC", f"got {a['family']}/{a['quality']}")

    p = classify_source(**PRACTITIONER_PAGE)
    if p["family"] == FAMILY_PRACTITIONER:
        _ok("V-LANDSCAPE-PRACTITIONER", f"HN thread -> {p['family']}")
    else:
        _fail("V-LANDSCAPE-PRACTITIONER", f"got {p['family']}")

    m = classify_source(**MEASURED_PAGE)
    if m["family"] == FAMILY_MEASURED and m["quality"] == QUALITY_HIGH:
        _ok("V-LANDSCAPE-MEASURED", f"post-mortem -> {m['family']}/{m['quality']}")
    else:
        _fail("V-LANDSCAPE-MEASURED", f"got {m['family']}/{m['quality']}")

    # A real measurement on a selling page is evidence, but not INDEPENDENT
    # evidence. Keeping it at HIGH is how vendor marketing launders into fact.
    vd = classify_source(**VENDOR_WITH_DATA)
    if vd["family"] == FAMILY_MEASURED and vd["quality"] == QUALITY_MEDIUM:
        _ok("V-LANDSCAPE-VENDOR-SELFREPORT",
            "vendor-hosted measurement kept as evidence but capped to MEDIUM")
    else:
        _fail("V-LANDSCAPE-VENDOR-SELFREPORT",
              f"got {vd['family']}/{vd['quality']}")

    # THE CORE GATE. The original run's landscape: one vendor blog, nothing else.
    lv = landscape_verdict([v])
    if lv["verdict"] == COVERAGE_VENDOR_ONLY:
        _ok("V-LANDSCAPE-REJECTS-D-ONLY",
            "vendor-only landscape -> VENDOR_ONLY (the 2026-08-18 bug)")
    else:
        _fail("V-LANDSCAPE-REJECTS-D-ONLY", f"got {lv['verdict']}")

    thin = landscape_verdict([v, p])
    if thin["verdict"] == COVERAGE_THIN and thin["quality"] == QUALITY_MEDIUM:
        _ok("V-LANDSCAPE-THIN",
            "one load-bearing family + vendor -> THIN/MEDIUM")
    else:
        _fail("V-LANDSCAPE-THIN", f"got {thin['verdict']}/{thin['quality']}")

    covered = landscape_verdict([v, p, a, m])
    if covered["verdict"] == COVERAGE_COVERED and covered["quality"] == QUALITY_HIGH:
        _ok("V-LANDSCAPE-COVERED",
            f"3 load-bearing families -> COVERED/HIGH "
            f"({', '.join(covered['load_bearing'])})")
    else:
        _fail("V-LANDSCAPE-COVERED",
              f"got {covered['verdict']}/{covered['quality']}")

    # An empty landscape is not neutral. Nothing fetched means nothing proven.
    if landscape_verdict([])["verdict"] == COVERAGE_VENDOR_ONLY:
        _ok("V-LANDSCAPE-EMPTY", "empty landscape refuses to be load-bearing")
    else:
        _fail("V-LANDSCAPE-EMPTY", "empty landscape did not refuse")

    # THE REGRESSION. On 2026-08-18 the live run fetched 13 real pages, scored
    # 12 UNKNOWN because the classifier's vocabulary was software-only, read
    # UNKNOWN as vendor, and refused all three questions -> 0 learnings. An
    # unrecognised page is unidentified, NOT marketing.
    unclassifiable = classify_source(
        url="https://example.org/some-article",
        title="An article about content strategy",
        snippet="General discussion.",
        body="This page discusses the subject at length without measurement "
             "language, academic markers, or a sales pitch.",
    )
    unk = landscape_verdict([unclassifiable, unclassifiable])
    if unk["verdict"] == COVERAGE_UNCLASSIFIED:
        _ok("V-LANDSCAPE-UNKNOWN-IS-NOT-VENDOR",
            "unidentified sources -> UNCLASSIFIED, not a refusal "
            "(the 2026-08-18 zero-learning regression)")
    else:
        _fail("V-LANDSCAPE-UNKNOWN-IS-NOT-VENDOR", f"got {unk['verdict']}")

    if landscape_verdict([v, unclassifiable])["verdict"] == COVERAGE_UNCLASSIFIED:
        _ok("V-LANDSCAPE-MIXED-UNKNOWN",
            "a vendor page plus an unidentified one is still not vendor-ONLY")
    else:
        _fail("V-LANDSCAPE-MIXED-UNKNOWN", "mixed landscape mis-refused")

    # Broadening the practitioner vocabulary must not launder marketing into a
    # load-bearing family. First-hand phrasing on a selling page stays family D.
    laundering = classify_source(
        url="https://vendor.example/blog/lessons",
        title="Lessons learned from our clients",
        snippet="In our experience, what worked was our platform.",
        body="In our experience, lessons learned show what worked. Book a demo, "
             "free trial available, talk to sales about pricing plans.",
    )
    if laundering["family"] == FAMILY_VENDOR:
        _ok("V-LANDSCAPE-NO-LAUNDERING",
            "first-hand phrasing on a conversion surface stays family D")
    else:
        _fail("V-LANDSCAPE-NO-LAUNDERING", f"got {laundering['family']}")

    # And the broadening must actually WORK on a non-software domain, which is
    # the whole point of the fix.
    non_software = classify_source(
        url="https://someeditor.example/notes/publishing",
        title="What we learned running an editorial calendar for six years",
        snippet="In our experience, output alone stopped helping.",
        body="Over the years we found that adding more posts stopped helping. "
             "In practice, lessons learned pushed us to consolidate.",
    )
    if non_software["family"] == FAMILY_PRACTITIONER:
        _ok("V-LANDSCAPE-DOMAIN-AGNOSTIC",
            "first-hand reporting outside software now resolves to family C")
    else:
        _fail("V-LANDSCAPE-DOMAIN-AGNOSTIC", f"got {non_software['family']}")

    ranked = rank_sources_for_extraction([v, a, m, p])
    if [r["family"] for r in ranked] == [FAMILY_MEASURED, FAMILY_ACADEMIC,
                                         FAMILY_PRACTITIONER, FAMILY_VENDOR]:
        _ok("V-LANDSCAPE-RANK",
            "extraction order puts load-bearing families ahead of the vendor")
    else:
        _fail("V-LANDSCAPE-RANK", f"got {[r['family'] for r in ranked]}")

    if v["signals"]:
        _ok("V-LANDSCAPE-EXPLAINS", f"verdict carries evidence: {v['signals'][0]}")
    else:
        _fail("V-LANDSCAPE-EXPLAINS", "classifier gave no signals")


# =========================================================================
# V-EPISTEMIC-* — ENGINE 3
# =========================================================================

def gate_epistemic() -> None:
    print("\nV-EPISTEMIC — Engine 3: capability + reality extraction")

    prompt = build_capability_learnings_prompt(QUERY, "<content/>")
    if "capability" in prompt and "epistemic" in prompt and "evidence" in prompt:
        _ok("V-EPISTEMIC-PROMPT-FIELDS",
            "extraction prompt demands capability + epistemic + evidence")
    else:
        _fail("V-EPISTEMIC-PROMPT-FIELDS", "prompt is missing a required field")

    if normalize_epistemic("nonsense") == EPI_HYPOTHESIS and \
            normalize_epistemic("observed") == EPI_OBSERVED:
        _ok("V-EPISTEMIC-DEGRADE-ONLY",
            "unknown label -> HYPOTHESIS (never OBSERVED, never a silent pass)")
    else:
        _fail("V-EPISTEMIC-DEGRADE-ONLY",
              f"got {normalize_epistemic('nonsense')}")

    if has_measurable_datum("traffic fell 34% in 6 months") and \
            not has_measurable_datum("traffic fell noticeably over time"):
        _ok("V-EPISTEMIC-MEASURABLE",
            "quantity detector separates a measured claim from an impression")
    else:
        _fail("V-EPISTEMIC-MEASURABLE", "measurable-datum detector mis-fired")

    # THE CORE CAP. The original output asserted saturation "is measurable" with
    # no number behind it. A label is a request; the cap is the contract.
    lvl, reason = cap_epistemic(
        EPI_OBSERVED,
        "Saturation is measurable before rankings fall.",
        "The article states that saturation can be detected early.",
        supporting_sources=1, coverage=COVERAGE_COVERED,
    )
    if lvl == EPI_DERIVED and "quantity" in reason:
        _ok("V-EPISTEMIC-CAP-OBSERVED",
            "OBSERVED without a number -> DERIVED (the 2026-08-18 bug)")
    else:
        _fail("V-EPISTEMIC-CAP-OBSERVED", f"got {lvl} / {reason!r}")

    lvl, reason = cap_epistemic(
        EPI_OBSERVED,
        "Publishers report impressions flattening 6 weeks before sessions drop.",
        "Two contents give the lag in weeks.",
        supporting_sources=2, coverage=COVERAGE_COVERED,
    )
    if lvl == EPI_OBSERVED and not reason:
        _ok("V-EPISTEMIC-KEEPS-EARNED",
            "OBSERVED with a real quantity survives — the cap is not a blanket")
    else:
        _fail("V-EPISTEMIC-KEEPS-EARNED", f"got {lvl} / {reason!r}")

    lvl, reason = cap_epistemic(
        EPI_VERIFIED, "Consolidation recovers traffic in 3 months.",
        "One case study reports it.", supporting_sources=1,
        coverage=COVERAGE_COVERED,
    )
    if lvl == EPI_OBSERVED and "corroboration" in reason:
        _ok("V-EPISTEMIC-CAP-VERIFIED",
            "VERIFIED on 1 source -> demoted; corroboration must be countable")
    else:
        _fail("V-EPISTEMIC-CAP-VERIFIED", f"got {lvl} / {reason!r}")

    lvl, reason = cap_epistemic(
        EPI_OBSERVED, "Clusters saturate after 40 articles.",
        "The vendor blog says so.", supporting_sources=1,
        coverage=COVERAGE_VENDOR_ONLY,
    )
    if lvl == EPI_REJECTED and "VENDOR_ONLY" in reason:
        _ok("V-EPISTEMIC-CAP-VENDOR",
            "vendor-only landscape rejects the claim regardless of its label")
    else:
        _fail("V-EPISTEMIC-CAP-VENDOR", f"got {lvl} / {reason!r}")

    lvl, reason = cap_epistemic(
        EPI_OBSERVED, "Clusters saturate after 40 articles.",
        "An article states the figure.", supporting_sources=2,
        coverage=COVERAGE_UNCLASSIFIED,
    )
    if lvl == EPI_DERIVED and "provenance" in reason:
        _ok("V-EPISTEMIC-CAP-UNCLASSIFIED",
            "unidentified provenance caps at DERIVED — costs confidence, "
            "does not delete the work")
    else:
        _fail("V-EPISTEMIC-CAP-UNCLASSIFIED", f"got {lvl} / {reason!r}")

    # End-to-end: a well-formed payload against a THIN landscape.
    payload = {
        "learnings": [
            {"capability": "You can read a traffic plateau as a consolidation "
                           "signal instead of a volume problem.",
             "learning": "Impressions on new pages flatten 6 weeks before "
                         "sessions decline.",
             "epistemic": "VERIFIED", "evidence": "Two contents give the lag.",
             "supporting_sources": 3},
            {"capability": "You can stop assuming more articles always help.",
             "learning": "Adding pages past the cluster's demand ceiling "
                         "cannibalises the pages that already rank.",
             "epistemic": "OBSERVED", "evidence": "Asserted, no figure given.",
             "supporting_sources": 1},
            {"capability": "", "learning": "orphan with no capability",
             "epistemic": "OBSERVED", "evidence": "x", "supporting_sources": 1},
        ],
        "followUpQuestions": [],
    }
    cov = landscape_verdict([classify_source(**PRACTITIONER_PAGE),
                             classify_source(**VENDOR_PAGE)])
    records = parse_learning_records(payload, cov)

    if len(records) == 2:
        _ok("V-EPISTEMIC-DROPS-MALFORMED",
            "record with no capability dropped, not patched into existence")
    else:
        _fail("V-EPISTEMIC-DROPS-MALFORMED", f"kept {len(records)} records")

    # supporting_sources=3 was claimed against a 2-document landscape.
    if records and records[0]["supporting_sources"] == 2:
        _ok("V-EPISTEMIC-SOURCE-ARITHMETIC",
            "claimed corroboration capped at the number of documents fetched")
    else:
        _fail("V-EPISTEMIC-SOURCE-ARITHMETIC",
              f"got {records[0]['supporting_sources'] if records else 'n/a'}")

    if len(records) > 1 and records[1]["epistemic"] == EPI_DERIVED and \
            records[1]["capped"]:
        _ok("V-EPISTEMIC-CAP-RECORDED",
            f"demotion recorded with its reason: {records[1]['cap_reason'][:48]}")
    else:
        _fail("V-EPISTEMIC-CAP-RECORDED", "demotion not recorded on the record")

    if records and records[0]["source_quality"] == QUALITY_MEDIUM:
        _ok("V-EPISTEMIC-QUALITY-INHERIT",
            "learning inherits MEDIUM from a practitioner+vendor landscape")
    else:
        _fail("V-EPISTEMIC-QUALITY-INHERIT",
              f"got {records[0]['source_quality'] if records else 'n/a'}")

    rendered = format_labeled_learning(records[0]) if records else ""
    if rendered.startswith("[VERIFIED][MEDIUM]") and "Capacidad:" in rendered \
            and "Evidencia:" in rendered:
        _ok("V-EPISTEMIC-FORMAT", f"labels lead the string: {rendered[:34]}...")
    else:
        _fail("V-EPISTEMIC-FORMAT", f"got {rendered[:70]!r}")

    dist = epistemic_distribution(records)
    if dist[EPI_VERIFIED] == 1 and dist[EPI_DERIVED] == 1:
        _ok("V-EPISTEMIC-DISTRIBUTION", f"confidence profile computed: {dist}")
    else:
        _fail("V-EPISTEMIC-DISTRIBUTION", f"got {dist}")


# =========================================================================
# V-CONTRA-* — ENGINE 4
# =========================================================================

CORPUS = [
    "[OBSERVED][HIGH] Consolidating a saturated cluster recovers traffic "
    "within 3 months.",
    "[OBSERVED][HIGH] Consolidation typically takes 9 to 12 months to recover "
    "the lost sessions.",
    "[DERIVED][MEDIUM] Saturation is visible in impressions before sessions.",
]


def gate_contradiction() -> None:
    print("\nV-CONTRA — Engine 4: contradiction detection")

    prompt = build_contradiction_prompt(CORPUS)
    if "[0]" in prompt and "[2]" in prompt and "not to settle it" in prompt:
        _ok("V-CONTRA-PROMPT",
            "prompt indexes the corpus and forbids picking a winner")
    else:
        _fail("V-CONTRA-PROMPT", "prompt missing indices or the no-resolve rule")

    good = {"contradictions": [
        {"index_a": 0, "index_b": 1, "axis": "TIMEFRAME",
         "claim_a": "Recovery takes about 3 months.",
         "claim_b": "Recovery takes 9 to 12 months.",
         "guidance": "Prefer the shorter window only for clusters under 50 "
                     "pages; the longer figure comes from larger sites."},
        # Hallucinated: index 7 does not exist in a 3-learning corpus.
        {"index_a": 0, "index_b": 7, "axis": "CONTEXT",
         "claim_a": "a", "claim_b": "b", "guidance": "c"},
        # Self-contradiction of one learning is not a contradiction.
        {"index_a": 2, "index_b": 2, "axis": "SCOPE",
         "claim_a": "a", "claim_b": "b", "guidance": "c"},
        # Duplicate of the first pair, order flipped.
        {"index_a": 1, "index_b": 0, "axis": "SCOPE",
         "claim_a": "a", "claim_b": "b", "guidance": "c"},
        # Missing guidance — an unresolved conflict with no operator advice.
        {"index_a": 1, "index_b": 2, "axis": "SCOPE",
         "claim_a": "a", "claim_b": "b", "guidance": ""},
    ]}
    rows = parse_contradictions(good, len(CORPUS))

    if len(rows) == 1 and rows[0]["index_a"] == 0 and rows[0]["index_b"] == 1:
        _ok("V-CONTRA-VALIDATES",
            "1 real pair kept; out-of-range, self-pair, duplicate and "
            "guidance-less rows all discarded")
    else:
        _fail("V-CONTRA-VALIDATES", f"kept {len(rows)} rows: {rows}")

    if rows and rows[0]["axis"] == "TIMEFRAME":
        _ok("V-CONTRA-AXIS", "conflict axis preserved")
    else:
        _fail("V-CONTRA-AXIS", "axis lost")

    bad_axis = parse_contradictions({"contradictions": [
        {"index_a": 0, "index_b": 1, "axis": "VIBES", "claim_a": "a",
         "claim_b": "b", "guidance": "c"}]}, len(CORPUS))
    if bad_axis and bad_axis[0]["axis"] == "UNKNOWN":
        _ok("V-CONTRA-AXIS-NORM",
            "unrecognised axis -> UNKNOWN, not an invented explanation")
    else:
        _fail("V-CONTRA-AXIS-NORM", f"got {bad_axis}")

    section = format_contradiction_section(rows)
    if "CONTRADICCIÓN" in section and "NO está resuelto" in section and \
            "Para el operador:" in section:
        _ok("V-CONTRA-FORMAT",
            "report block states the conflict, marks it unresolved, advises")
    else:
        _fail("V-CONTRA-FORMAT", f"got {section[:120]!r}")

    empty = format_contradiction_section([])
    if "Ninguna" in empty and "no significa consenso" in empty:
        _ok("V-CONTRA-EMPTY-EXPLICIT",
            "zero contradictions is written, not silently omitted")
    else:
        _fail("V-CONTRA-EMPTY-EXPLICIT", f"got {empty[:120]!r}")


def main() -> int:
    print("test_research_engines — deep_research E1-E4 gates")
    gate_decomposition()
    gate_landscape()
    gate_epistemic()
    gate_contradiction()
    total = _passes + _fails
    print(f"\nENGINES_PASS={_passes}/{total}  fails={_fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
