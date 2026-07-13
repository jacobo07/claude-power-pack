#!/usr/bin/env python3
"""test_research_quality.py — gates for the deep_research quality layer.

Pure + offline: no network, no LLM, no disk writes. Every fixture below is
VERBATIM from the production defect observed on 2026-07-13 — the actual
keyword-soup query the system generated, and the actual code-bearing
learnings it persisted. A synthetic fixture would prove nothing; these
strings are the bug.

Run:  python test_research_quality.py
Exit: 0 = all gates pass, 1 = at least one gate failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from research_quality import (  # noqa: E402
    KEEP_LEVELS,
    RELEVANCE_DISCARD,
    RELEVANCE_HIGH,
    RELEVANCE_LOW,
    RELEVANCE_MEDIUM,
    build_learnings_prompt,
    build_relevance_prompt,
    build_serp_query_prompt,
    find_code_in_learning,
    is_natural_question,
    parse_relevance_ratings,
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


# =========================================================================
# V-QUERY-* — a query must be a question, not a pile of nouns
# =========================================================================

# THE BUG, verbatim. This is the query deep_research v0.1.0 actually sent.
BUG_QUERY = ("data mesh product contract semantic layer composable insight "
             "envelope schema versioning")

SOUP_QUERIES = [
    BUG_QUERY,
    "schema versioning data mesh",
    "semantic layer metrics governance federated ownership",
    "datacontract CLI breaking change detection",
]

GOOD_QUERIES = [
    "cómo los equipos de datos evitan que un cambio de schema rompa "
    "dashboards sin previo aviso",
    "how do data teams stop a schema change from silently breaking dashboards",
    "qué problemas resuelven los contratos de datos en equipos distribuidos",
    "what actually goes wrong when two teams define the same metric "
    "differently",
    "how much notice do downstream consumers need before a breaking change",
]


def test_queries() -> None:
    # Arrange / Act / Assert — the exact production soup must be refused.
    ok, reason = is_natural_question(BUG_QUERY)
    if not ok and "keyword soup" in reason:
        _ok("V-QUERY-BUG-REPRO", f"production soup refused: {reason[:60]}")
    else:
        _fail("V-QUERY-BUG-REPRO",
              f"the actual bug query was ACCEPTED (ok={ok}, reason={reason!r})")

    refused = [q for q in SOUP_QUERIES if not is_natural_question(q)[0]]
    if len(refused) == len(SOUP_QUERIES):
        _ok("V-QUERY-SOUP-ALL", f"{len(refused)}/{len(SOUP_QUERIES)} refused")
    else:
        leaked = [q for q in SOUP_QUERIES if is_natural_question(q)[0]]
        _fail("V-QUERY-SOUP-ALL", f"leaked through the gate: {leaked}")

    accepted = [q for q in GOOD_QUERIES if is_natural_question(q)[0]]
    if len(accepted) == len(GOOD_QUERIES):
        _ok("V-QUERY-NATURAL-ALL",
            f"{len(accepted)}/{len(GOOD_QUERIES)} real questions accepted")
    else:
        rejected = [(q, is_natural_question(q)[1])
                    for q in GOOD_QUERIES if not is_natural_question(q)[0]]
        _fail("V-QUERY-NATURAL-ALL",
              f"FALSE POSITIVE — good questions refused: {rejected}")

    # A query carrying CLI syntax is never something a human types.
    ok, _ = is_natural_question("how to run datacontract lint --old main")
    if not ok:
        _ok("V-QUERY-NO-CLI", "query with a --flag refused")
    else:
        _fail("V-QUERY-NO-CLI", "query containing a CLI flag was accepted")

    # The prompt itself must forbid the soup, not merely the gate.
    prompt = build_serp_query_prompt("data contracts", 3, [])
    if "FORBIDDEN" in prompt and "Concatenated technical terms" in prompt:
        _ok("V-QUERY-PROMPT-BANS-SOUP",
            "query prompt carries an explicit ban + a banned example")
    else:
        _fail("V-QUERY-PROMPT-BANS-SOUP",
              "query prompt does not forbid concatenated terms")


# =========================================================================
# V-LEARN-* — a learning never contains code
# =========================================================================

# THE BUG, verbatim: learnings deep_research v0.1.0 actually persisted.
BUG_LEARNINGS = [
    "Breaking vs non-breaking is a hard taxonomy: enforcement is layered — "
    "CI/CD shift-left (`datacontract lint` + `datacontract breaking --old "
    "...@main --new ...`, buf for Protobuf), schema registry at runtime.",
    "The canonical anatomy has 7 blocks: metadata, schema, SLA (freshness "
    "`PT1H`, availability 99.9%, updateFrequency `PT15M`), quality rules "
    "(null_rate < 0.05).",
    "Cross-domain metrics need identity mapping (customer_id↔user_id) "
    "resolved in the semantic layer.",
]

# Prose learnings that carry hard numbers + named entities but zero code.
# These MUST survive — a gate that eats them is worse than no gate.
GOOD_LEARNINGS = [
    "Organisations running distributed data teams report that one "
    "unannounced schema change fed wrong revenue numbers to marketing for "
    "nearly two weeks before anyone noticed, because the failure is silent: "
    "nothing crashes, the dashboard simply lies.",
    "The industry norm is to give downstream consumers 90 days notice before "
    "a breaking change, in four stages — announce, dual-write, warn, then "
    "remove. Teams that skip the notice period absorb the migration cost as "
    "unplanned incident work.",
    "Market Research Future projects the data mesh market to grow from USD "
    "1.78 billion in 2025 to USD 8.55 billion by 2035, a 17% CAGR, which "
    "means the tooling a company picks now will outlive the team that "
    "picked it.",
    "The hardest part is not the tooling but the culture change: producers "
    "must start treating their data as a product with customers, and that "
    "shift needs executive support and visible early wins.",

    # REGRESSION FIXTURES — both of these are verbatim learnings that the
    # FIRST version of the code gate wrongly discarded on the 2026-07-13 live
    # run. They are the two false-positive classes the gate must never repeat.
    #
    # (1) A single field name quoted as the EVIDENCE of a real incident. The
    #     field name is the whole point of the story; eating it eats the
    #     learning. Old rule: any snake_case token -> discard.
    "Schema changes almost never fail loudly — they fail silently, which is "
    "why they are expensive. A payments company's single field rename "
    "(transaction_amount to amount) silently produced NULL revenue for "
    "thousands of merchants across 14 dashboards while every job reported "
    "success. Budget for detection, not just prevention: your monitoring "
    "almost certainly watches for crashes, and this class of failure never "
    "crashes.",

    # (2) Spanish prose that merely NAMES a tool. "dbt ya existen" is a
    #     sentence, not an invocation. Old rule: tool + any lowercase word.
    "Cuando cada equipo calcula la misma métrica a su manera, la "
    "organización no discute resultados, discute definiciones. La solución "
    "que emerge es la capa semántica: el significado de cada métrica se "
    "define una sola vez y todas las herramientas lo heredan. Motores como "
    "el de dbt ya existen, así que la fricción se elimina a bajo coste.",
]


def test_learnings() -> None:
    caught = [ln for ln in BUG_LEARNINGS if find_code_in_learning(ln)]
    if len(caught) == len(BUG_LEARNINGS):
        reasons = [find_code_in_learning(ln) for ln in BUG_LEARNINGS]
        _ok("V-LEARN-BUG-REPRO",
            f"all {len(caught)} production code-learnings discarded; "
            f"first reason: {reasons[0]}")
    else:
        leaked = [ln for ln in BUG_LEARNINGS if not find_code_in_learning(ln)]
        _fail("V-LEARN-BUG-REPRO",
              f"code-bearing learning survived the gate: {leaked}")

    survivors = [ln for ln in GOOD_LEARNINGS if not find_code_in_learning(ln)]
    if len(survivors) == len(GOOD_LEARNINGS):
        _ok("V-LEARN-NO-FALSE-POSITIVE",
            f"{len(survivors)}/{len(GOOD_LEARNINGS)} prose learnings with "
            f"metrics + entities kept intact")
    else:
        eaten = [(ln[:50], find_code_in_learning(ln))
                 for ln in GOOD_LEARNINGS if find_code_in_learning(ln)]
        _fail("V-LEARN-NO-FALSE-POSITIVE",
              f"gate ATE a good prose learning: {eaten}")

    # Individual detector rules, each pinned to a distinct code shape.
    shapes = {
        "cli-flag": "Run the check with --breaking enabled in the pipeline.",
        "backtick": "Set `freshness` on the contract.",
        "schema-fields": "Map customer_id to user_id and keep order_id stable.",
        "yaml": "Declare version: 2.1.0 in the contract header.",
        "sql": "SELECT total FROM orders WHERE status = 'shipped'.",
        "cli-tool": "First npm install the package, then build.",
        "iso-duration": "Freshness is expressed as PT1H in the spec.",
    }
    # The mirror image of the rules above: one field name quoted inside a
    # story is prose, and a tool NAMED (not invoked) is prose. These must
    # NOT be detected as code — that is the 2026-07-13 false-positive class.
    not_code = {
        "single-field-anecdote": "Renaming transaction_amount broke revenue.",
        "tool-named-not-invoked": "Motores como el de dbt ya existen hoy.",
    }
    over_eager = [k for k, v in not_code.items() if find_code_in_learning(v)]
    if not over_eager:
        _ok("V-LEARN-NO-OVERREACH",
            "a single field name in a story, and a tool merely named in "
            "Spanish prose, both survive the gate")
    else:
        _fail("V-LEARN-NO-OVERREACH",
              f"gate over-reached on prose: {over_eager}")
    missed = [k for k, v in shapes.items() if not find_code_in_learning(v)]
    if not missed:
        _ok("V-LEARN-DETECTOR-COVERAGE",
            f"all {len(shapes)} code shapes detected "
            f"({', '.join(shapes)})")
    else:
        _fail("V-LEARN-DETECTOR-COVERAGE", f"undetected code shapes: {missed}")

    prompt = build_learnings_prompt("q", "content")
    banned_ok = "FORBIDDEN IN EVERY LEARNING" in prompt
    reader_ok = "founder or operator" in prompt or "founder/operator" in prompt
    if banned_ok and reader_ok:
        _ok("V-LEARN-PROMPT-BANS-CODE",
            "learnings prompt names the reader and forbids code explicitly")
    else:
        _fail("V-LEARN-PROMPT-BANS-CODE",
              f"prompt missing ban ({banned_ok}) or reader ({reader_ok})")


# =========================================================================
# V-REL-* — only operator-actionable learnings are persisted
# =========================================================================


def test_relevance() -> None:
    if KEEP_LEVELS == frozenset({RELEVANCE_HIGH, RELEVANCE_MEDIUM}):
        _ok("V-REL-KEEP-POLICY",
            "only HIGH + MEDIUM persist; LOW and DISCARD never reach the vault")
    else:
        _fail("V-REL-KEEP-POLICY", f"keep-policy drifted: {KEEP_LEVELS}")

    payload = {
        "ratings": [
            {"index": 0, "relevance": RELEVANCE_HIGH, "reason": "acts on it"},
            {"index": 1, "relevance": RELEVANCE_LOW, "reason": "infra only"},
            {"index": 2, "relevance": RELEVANCE_DISCARD, "reason": "vendor ad"},
            {"index": 3, "relevance": RELEVANCE_MEDIUM, "reason": "useful"},
        ]
    }
    ratings = parse_relevance_ratings(payload, 4)
    kept = [i for i in range(4) if ratings[i]["relevance"] in KEEP_LEVELS]
    if kept == [0, 3]:
        _ok("V-REL-FILTER", "HIGH+MEDIUM kept (0,3); LOW+DISCARD dropped (1,2)")
    else:
        _fail("V-REL-FILTER", f"expected [0, 3] kept, got {kept}")

    # A malformed rating must not silently mutate the corpus: an out-of-range
    # index, a bogus level and a non-integer index are all simply absent from
    # the map, and the caller treats absence as UNRATED (kept + flagged).
    junk = {
        "ratings": [
            {"index": 99, "relevance": RELEVANCE_HIGH, "reason": "x"},
            {"index": 0, "relevance": "SUPER_RELEVANT", "reason": "x"},
            {"index": "one", "relevance": RELEVANCE_HIGH, "reason": "x"},
        ]
    }
    if parse_relevance_ratings(junk, 2) == {}:
        _ok("V-REL-MALFORMED-SAFE",
            "out-of-range index, bogus level and non-int index all rejected")
    else:
        _fail("V-REL-MALFORMED-SAFE",
              f"malformed ratings leaked: {parse_relevance_ratings(junk, 2)}")

    prompt = build_relevance_prompt(["a learning"], None)
    has_30d = "30 days" in prompt
    has_transfer = "transfer" in prompt
    has_bias = "LOWER" in prompt
    if has_30d and has_transfer and has_bias:
        _ok("V-REL-PROMPT-CONTRACT",
            "relevance prompt asks the 30-day, decision and transfer "
            "questions, and biases ties downward")
    else:
        _fail("V-REL-PROMPT-CONTRACT",
              f"30d={has_30d} transfer={has_transfer} tie-bias={has_bias}")


def main() -> int:
    print("deep_research quality gates — fixtures are the real 2026-07-13 bug")
    print("\nV-QUERY  (natural-language questions, not keyword soup)")
    test_queries()
    print("\nV-LEARN  (prose insights, never code)")
    test_learnings()
    print("\nV-REL    (operator-actionable only)")
    test_relevance()
    total = _passes + _fails
    print(f"\nQUALITY_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
