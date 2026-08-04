#!/usr/bin/env python3
"""test_uceimr_residues.py -- V-gates for UCEIMR residues R1 and R2.

R1  corpus-to-capability adapter   modules/capability_runtime/corpus_adapter.py
R2  retirement-condition evaluator modules/capability_runtime/retirement.py

Both are propose-only by contract, so the gates assert the REFUSALS as hard as
they assert the happy path: a miner that can approve itself, or an evaluator
that can retire a capability without the Owner, would each be a gate that
grades itself.

Hermetic: every write goes to a TemporaryDirectory. The two gates that read
real repository state (V-UCEIMR-R2-EVALUATES-REAL, V-UCEIMR-R1-MINES-REAL)
assert SHAPE and mechanism, never a count that a later commit would move.

Run: python tools/test_uceimr_residues.py
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, load_contracts,
)
from modules.capability_runtime.corpus_adapter import (  # noqa: E402
    EvidenceUnit, approve, evidence_from_akos, evidence_from_corpus,
    evidence_from_research, extract_claims, load_proposals, mine, mine_unit,
    render, save_proposal,
)
from modules.capability_runtime import retirement as R  # noqa: E402

_passes, _fails = 0, 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"[PASS] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {diag}")


def _contract(cid: str, **kw) -> CapabilityContract:
    base = dict(id=cid, name=cid.replace("_", " ").title(), owner="tests/",
                triggers=["t"], consumers=["Owner"])
    base.update(kw)
    return CapabilityContract(**base)


# ---------------------------------------------------------------------------
# R1 -- corpus-to-capability adapter
# ---------------------------------------------------------------------------
def t_r1_extracts_capability_claims() -> None:
    gate = "V-UCEIMR-R1-EXTRACTS"
    habitual = EvidenceUnit(
        "test", "probe.md#1", "probe",
        "I always compare the Amazon reviews with the Reddit threads for the "
        "same product before deciding whether the demand is real.")
    narrative = EvidenceUnit(
        "test", "probe.md#2", "probe",
        "This is a nice video about ecommerce brands and their history in "
        "Europe over the last decade.")
    got, none = extract_claims(habitual), extract_claims(narrative)
    if got and not none:
        _ok(gate, f"capability sentence -> {len(got)} claim(s); "
                  "narrative sentence -> 0 (a verb-less fact is not a capability)")
    else:
        _fail(gate, f"habitual={len(got)} (want >=1), narrative={len(none)} (want 0)")


def t_r1_lineage_traceable() -> None:
    gate = "V-UCEIMR-R1-LINEAGE"
    u = EvidenceUnit("akos", "BRIEF.md#saas.7", "How I validate demand",
                     "I always compare the Amazon reviews with the Reddit "
                     "threads before validating a product's demand signal.")
    ps = mine_unit(u)
    if not ps:
        _fail(gate, "no proposal mined from a capability-bearing claim")
        return
    p = ps[0]
    chain = p.lineage()
    if (len(chain) == 4 and chain[0] == "akos:BRIEF.md#saas.7"
            and p.source_ref == u.source_ref and p.claim in u.text):
        _ok(gate, f"source -> evidence -> claim -> proposal ({' -> '.join(chain)[:88]}…)")
    else:
        _fail(gate, f"lineage broken: {chain}")


def t_r1_overlap_audited() -> None:
    gate = "V-UCEIMR-R1-OVERLAP-AUDITED"
    u = EvidenceUnit(
        "test", "probe.md#3", "probe",
        "Always compare a new proposal against every existing module and "
        "family registry to detect duplicate ownership before building.")
    ps = mine_unit(u)
    if not ps:
        _fail(gate, "claim restating an owned capability produced no proposal")
        return
    p = ps[0]
    # The estate demonstrably owns duplicate detection (d2a). The gate is that
    # the miner does NOT report it as genuinely new -- either it names the
    # parent as OWNED, or d2a caps it and the miner reports DEFER.
    if p.disposition in ("OWNED", "DEFER") and p.parent_id:
        _ok(gate, f"owned ground -> {p.disposition} (parent={p.parent_id} "
                  f"{p.coverage_pct}%), not CANDIDATE")
    else:
        _fail(gate, f"disposition={p.disposition} parent={p.parent_id!r} "
                    f"cov={p.coverage_pct} -- an owned capability read as novel")


def t_r1_defer_is_not_novelty() -> None:
    gate = "V-UCEIMR-R1-DEFER-NOT-CANDIDATE"
    from modules.duplicate_to_advantage.d2a_engine import DupeVerdict
    d = DupeVerdict("KB-X", "X", 45, 60, 30, 30, False, [], deferred=True)
    if d.deferred and d.coverage_pct < 50:
        # A capped verdict must never reach the Owner as "genuinely new";
        # approve() must refuse it outright.
        from modules.capability_runtime.corpus_adapter import CapabilityProposal
        p = CapabilityProposal(
            proposal_id="x", name="X", claim="c", sovereign_question="q",
            source_kind="test", source_ref="r", source_title="t",
            disposition="DEFER", parent_id="KB-X", coverage_pct=45)
        try:
            approve(p, owner="tests/")
            _fail(gate, "a DEFER proposal was approved -- unknown ownership admitted")
        except ContractError as e:
            _ok(gate, f"capped-coverage DEFER refused at approval ({str(e)[:64]}…)")
    else:
        _fail(gate, "DupeVerdict.deferred no longer marks a capped verdict")


def t_r1_propose_only() -> None:
    gate = "V-UCEIMR-R1-PROPOSE-ONLY"
    from modules.capability_runtime.corpus_adapter import CapabilityProposal
    owned = CapabilityProposal(
        proposal_id="p1", name="Detect duplicates", claim="c",
        sovereign_question="q", source_kind="test", source_ref="r",
        source_title="t", disposition="OWNED", parent_id="KB-D2A",
        coverage_pct=80)
    novel = CapabilityProposal(
        proposal_id="p2", name="Fuse cross community evidence", claim="c",
        sovereign_question="q", source_kind="test", source_ref="r",
        source_title="t", disposition="CANDIDATE")
    refusals = []
    try:
        approve(owned, owner="tests/")
    except ContractError:
        refusals.append("OWNED")
    try:
        approve(novel, owner="   ")
    except ContractError:
        refusals.append("empty-owner")
    if refusals == ["OWNED", "empty-owner"]:
        _ok(gate, "approval refused for an already-owned proposal and for an "
                  "absent owner (HR-UCEIMR-03 / HR-APA-018)")
    else:
        _fail(gate, f"expected both refusals, got {refusals}")


def t_r1_approve_writes_contract() -> None:
    gate = "V-UCEIMR-R1-APPROVE-WRITES"
    from modules.capability_runtime.corpus_adapter import CapabilityProposal
    p = CapabilityProposal(
        proposal_id="cross_community_evidence_fusion", name="Fuse evidence",
        claim="I always compare Amazon reviews with Reddit threads.",
        sovereign_question="Can this estate fuse cross-community evidence?",
        source_kind="akos", source_ref="BRIEF.md#saas.7", source_title="t",
        disposition="CANDIDATE", triggers=["evidence", "fusion"])
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        before = len(load_contracts(d))
        c = approve(p, owner="modules/capability_runtime/", contracts_dir=d)
        after = load_contracts(d)
        if before == 0 and len(after) == 1 and after[0].id == c.id and c.owner:
            _ok(gate, f"Owner-supplied owner -> 1 valid contract on disk "
                      f"({c.id}, owner={c.owner})")
        else:
            _fail(gate, f"before={before} after={len(after)}")


def t_r1_no_acquisition() -> None:
    gate = "V-UCEIMR-R1-NO-ACQUISITION"
    src = (_ROOT / "modules" / "capability_runtime" /
           "corpus_adapter.py").read_text(encoding="utf-8-sig")
    banned = [tok for tok in ("import requests", "urllib.request", "http.client",
                              "socket.", "subprocess") if tok in src]
    if not banned:
        _ok(gate, "no network/subprocess surface -- HR-UCEIMR-02 holds "
                  "(CrawlOS/AKOS acquire; this only reads what they wrote)")
    else:
        _fail(gate, f"acquisition surface present: {banned}")


def t_r1_failopen() -> None:
    gate = "V-UCEIMR-R1-FAILOPEN"
    try:
        a = evidence_from_akos(brief_path="C:/nope/does/not/exist.md")
        b = evidence_from_research(research_dir="C:/nope/does/not/exist")
        c = mine(units=[EvidenceUnit("t", "r", "t", "")])
        d = load_proposals(proposals_dir="C:/nope/does/not/exist")
        if a == [] and b == [] and c == [] and d == []:
            _ok(gate, "absent brief / absent research dir / empty unit / absent "
                      "proposals dir -> [] with no raise")
        else:
            _fail(gate, f"akos={len(a)} research={len(b)} mine={len(c)} load={len(d)}")
    except Exception as e:  # noqa: BLE001
        _fail(gate, f"raised {type(e).__name__}: {e}")


def t_r1_precision() -> None:
    """A labelled fixture. This gate CAN fail -- an earlier version of the
    extractor passed a yield-agnostic check while producing 148 noise
    proposals from the real corpus, which is `feedback_zero_cannot_fall` in
    test form: a gate whose every outcome is a pass measures nothing."""
    gate = "V-UCEIMR-R1-PRECISION"
    claims = [
        "I always compare the Amazon reviews with the Reddit threads before "
        "validating that a product's demand is real.",
        "You need to measure the error rate with matched pre and post windows "
        "or the comparison means nothing.",
        "Siempre comparo la tasa de siniestralidad contra la media nacional "
        "antes de aceptar cualquier cifra de marketing.",
        "The key is to track every deployment against the incident record so "
        "that a regression is attributable to a change.",
    ]
    noise = [
        "- **Error-rate monitoring** via Sentry / Bugsnag for a 30-minute soak.",
        "This is a nice video about ecommerce brands and their history.",
        "> Existe una vía sin reescritura completa que es la apropiada.",
        "Optimiza para citación dentro de la respuesta, no para el ranking.",
    ]
    tp = sum(1 for c in claims
             if extract_claims(EvidenceUnit("t", "r", "t", c)))
    fp = sum(1 for n in noise
             if extract_claims(EvidenceUnit("t", "r", "t", n)))
    if tp == len(claims) and fp == 0:
        _ok(gate, f"{tp}/{len(claims)} standing-practice claims found, "
                  f"{fp}/{len(noise)} false positives on markdown/narration")
    else:
        _fail(gate, f"recall {tp}/{len(claims)}, false positives {fp}/{len(noise)}")


def t_r1_corpus_yield() -> None:
    gate = "V-UCEIMR-R1-CORPUS-YIELD"
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "talk.txt").write_text(
            "Welcome everyone. I always compare the Amazon review corpus with "
            "the Reddit threads for the same product before I trust a demand "
            "signal. That is how we avoid buying a dead niche.\n",
            encoding="utf-8")
        (d / "notes.md").write_text(
            "Some heading text.\n\nYou need to track every supplier lead time "
            "against the promised ship date, otherwise the margin model is "
            "fiction.\n", encoding="utf-8")
        units = evidence_from_corpus(d)
        ps = mine(units=units)
    good = [p for p in ps if p.claim and p.source_ref and p.disposition]
    if len(units) == 2 and good and all(p.lineage()[0].startswith("corpus:")
                                        for p in good):
        _ok(gate, f"2 authored file(s) -> {len(ps)} proposal(s) "
                  f"({sorted({p.disposition for p in ps})}), lineage anchored "
                  "to the corpus file")
    else:
        _fail(gate, f"units={len(units)} proposals={len(ps)}")


def t_r1_store_starvation_is_visible() -> None:
    """The measured state of THIS repo's evidence stores. Not a pass/fail on
    the yield -- a pass/fail on whether the miner reports the yield honestly
    instead of silently returning nothing."""
    gate = "V-UCEIMR-R1-STORE-YIELD-REPORTED"
    ak = evidence_from_akos()
    rs = evidence_from_research()
    ps = mine(units=ak + rs)
    txt = render(ps)
    if txt.startswith(f"mined {len(ps)} claim(s)"):
        _ok(gate, f"akos={len(ak)} + research={len(rs)} unit(s) -> {len(ps)} "
                  "proposal(s); yield stated explicitly, never silent "
                  "(AKOS persists ~220-char leads; research holds the estate's "
                  "own notes -- neither is authored corpus)")
    else:
        _fail(gate, f"render() did not state the yield: {txt[:80]!r}")


def t_g5_persists_full_text() -> None:
    """G5. The fetchers held the full article/transcript and returned a
    1200-1500 char slice; the remainder was discarded. This asserts the full
    text survives AND that the digest slice is unchanged."""
    gate = "V-UCEIMR-G5-PERSISTS-FULL"
    from modules.autoresearch.enricher import persist_corpus
    full = ("I always compare the Amazon reviews with the Reddit threads. "
            * 200)                                  # ~11 k chars
    with tempfile.TemporaryDirectory() as td:
        p = persist_corpus(full, "https://example.com/talk", "jina", td)
        if p is None or not Path(p).is_file():
            _fail(gate, "nothing written")
            return
        body = Path(p).read_text(encoding="utf-8")
        # Idempotent: a second call must not rewrite.
        again = persist_corpus("DIFFERENT", "https://example.com/talk",
                               "jina", td)
        unchanged = Path(again).read_text(encoding="utf-8") == body
    if (len(body) > 10_000 and "source: https://example.com/talk" in body
            and "kind: jina" in body and unchanged):
        _ok(gate, f"{len(body)} chars persisted with source+kind+timestamp "
                  "header; re-fetch of the same source does not rewrite")
    else:
        _fail(gate, f"len={len(body)} unchanged={unchanged}")


def t_g5_closes_the_loop() -> None:
    """G5 + R1. The enricher writes; the miner reads the SAME default store
    with no configuration. A writer whose output no reader reaches is the
    `feedback_write_without_read_incomplete_system` shape."""
    gate = "V-UCEIMR-G5-LOOP-CLOSED"
    from modules.autoresearch.enricher import persist_corpus
    with tempfile.TemporaryDirectory() as td:
        persist_corpus(
            "Opening remarks. I always compare the supplier lead times "
            "against the promised ship dates before I trust a margin model. "
            "That is the whole discipline.",
            "https://example.com/ops-talk", "yt-dlp", td)
        units = evidence_from_corpus(td)
        ps = mine(units=units)
    if units and ps and all(p.source_ref for p in ps):
        _ok(gate, f"enricher wrote 1 file -> miner read {len(units)} unit(s) "
                  f"-> {len(ps)} proposal(s) "
                  f"({sorted({p.disposition for p in ps})})")
    else:
        _fail(gate, f"units={len(units)} proposals={len(ps)}")


def t_g5_default_store_is_read() -> None:
    gate = "V-UCEIMR-G5-DEFAULT-STORE"
    from modules.autoresearch.enricher import CORPUS_DIRNAME, _PP_ROOT as _E_ROOT
    import inspect
    from modules.capability_runtime import corpus_adapter as _ca
    writer = (_E_ROOT / CORPUS_DIRNAME).resolve()
    reader_src = inspect.getsource(_ca.evidence_from_corpus)
    # The reader's default must resolve to the writer's default, or the loop
    # only closes when someone remembers to pass a flag.
    if '"vault" / "corpus"' in reader_src and writer.name == "corpus":
        _ok(gate, f"writer default {writer} == reader default "
                  "<repo>/vault/corpus (no flag required)")
    else:
        _fail(gate, f"writer={writer} reader_default_missing")


def t_g5_failopen() -> None:
    gate = "V-UCEIMR-G5-FAILOPEN"
    from modules.autoresearch.enricher import persist_corpus
    try:
        a = persist_corpus("", "https://x", "jina", None)
        b = persist_corpus("text", "", "jina", None)
        c = persist_corpus("text", "https://x", "jina", "Z:/nope/nowhere/deep")
        if a is None and b is None and c is None:
            _ok(gate, "empty text / empty source / unwritable dir -> None, "
                      "never raises into the enrichment pipeline")
        else:
            _fail(gate, f"a={a} b={b} c={c}")
    except Exception as e:  # noqa: BLE001
        _fail(gate, f"raised {type(e).__name__}: {e}")


def t_r1_persists() -> None:
    gate = "V-UCEIMR-R1-PERSISTS"
    from modules.capability_runtime.corpus_adapter import CapabilityProposal
    p = CapabilityProposal(
        proposal_id="round_trip", name="N", claim="c", sovereign_question="q",
        source_kind="akos", source_ref="BRIEF.md#x.1", source_title="t",
        disposition="CANDIDATE")
    with tempfile.TemporaryDirectory() as td:
        save_proposal(p, td)
        back = load_proposals(td)
        if len(back) == 1 and back[0].source_ref == p.source_ref:
            _ok(gate, "proposal round-trips to disk with lineage intact")
        else:
            _fail(gate, f"round-trip lost data: {back}")


# ---------------------------------------------------------------------------
# R2 -- retirement-condition evaluator
# ---------------------------------------------------------------------------
def _plan(root: Path, name: str, date: str, verdict: str) -> None:
    d = root / "vault" / "plans"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(
        f"---\ntitle: t\ndate: {date}\nverdict: {verdict}\n---\n\nbody\n",
        encoding="utf-8")


def t_r2_evaluates_real() -> None:
    gate = "V-UCEIMR-R2-EVALUATES-REAL"
    vs = {v.contract_id: v for v in R.evaluate_all()}
    v = vs.get("duplicate_detection")
    if v is None:
        _fail(gate, "duplicate_detection contract not found on disk")
        return
    if v.status in (R.ACTIVE, R.RETIRED) and v.probe and v.evidence:
        _ok(gate, f"real repo state -> {v.status} ({v.evidence[:78]}…)")
    else:
        _fail(gate, f"status={v.status} probe={v.probe!r} evidence={v.evidence!r}")


def t_r2_retires_on_evidence() -> None:
    gate = "V-UCEIMR-R2-RETIRES"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i, d in enumerate(("2026-09-03", "2026-09-02", "2026-09-01")):
            _plan(root, f"audit-{i}.md", d, "GENUINELY_NEW")
        c = _contract("duplicate_detection",
                      retirement_condition="proposals stop measuring "
                                           "majority-owned across three "
                                           "consecutive audits")
        v = R.evaluate_contract(c, root=root)
        if v.status == R.RETIRED and v.retires:
            _ok(gate, f"3 consecutive non-majority audits -> {v.status} "
                      f"({v.evidence[:60]}…)")
        else:
            _fail(gate, f"expected {R.RETIRED}, got {v.status}: {v.evidence}")


def t_r2_does_not_retire_prematurely() -> None:
    gate = "V-UCEIMR-R2-EVIDENCE-THRESHOLD"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _plan(root, "a.md", "2026-09-03", "GENUINELY_NEW")
        _plan(root, "b.md", "2026-09-02", "MAJORITY_OWNED")
        _plan(root, "c.md", "2026-09-01", "GENUINELY_NEW")
        c = _contract("duplicate_detection",
                      retirement_condition="proposals stop measuring "
                                           "majority-owned across three "
                                           "consecutive audits")
        mixed = R.evaluate_contract(c, root=root)

        root2 = Path(td) / "sparse"
        _plan(root2, "a.md", "2026-09-03", "GENUINELY_NEW")
        sparse = R.evaluate_contract(c, root=root2)
    if mixed.status == R.ACTIVE and sparse.status == R.ACTIVE:
        _ok(gate, "one majority-owned verdict in the window, and a window with "
                  "only 1 audit, both stay ACTIVE -- 'consecutive' is enforced")
    else:
        _fail(gate, f"mixed={mixed.status} sparse={sparse.status}")


def t_r2_unevaluable_is_not_active() -> None:
    gate = "V-UCEIMR-R2-UNEVALUABLE"
    c = _contract("no_probe_registered_here",
                  retirement_condition="the ecosystem stops needing this")
    v = R.evaluate_contract(c)
    if v.status == R.UNEVALUABLE and not v.retires:
        _ok(gate, "free-text condition with no probe -> UNEVALUABLE, never "
                  "silently ACTIVE (feedback_zero_cannot_fall)")
    else:
        _fail(gate, f"expected {R.UNEVALUABLE}, got {v.status}")


def t_r2_never_and_missing() -> None:
    gate = "V-UCEIMR-R2-NEVER"
    never = R.evaluate_contract(
        _contract("perm", retirement_condition="never -- the failure is "
                                               "unrecoverable once it occurs"))
    none = R.evaluate_contract(_contract("blank", retirement_condition=""))
    if never.status == R.NEVER and none.status == R.NO_CONDITION:
        _ok(gate, "'never --' -> NEVER; empty condition -> NO_CONDITION "
                  "(a capability with no exit is visible, not assumed fine)")
    else:
        _fail(gate, f"never={never.status} blank={none.status}")


def t_r2_stale_probe() -> None:
    gate = "V-UCEIMR-R2-STALE"
    cs = [_contract("a", retirement_condition="x"),
          _contract("b", retirement_condition="y")]
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "log.json"
        never_evaluated = R.stale(contracts=cs, log_path=log, days=30)
        vs = [R.evaluate_contract(c) for c in cs]
        R.record_evaluation(vs, log)
        fresh = R.stale(contracts=cs, log_path=log, days=30)
        future = R.stale(contracts=cs, log_path=log, days=30,
                         now=datetime.now(timezone.utc) + timedelta(days=45))
    if never_evaluated == ["a", "b"] and fresh == [] and future == ["a", "b"]:
        _ok(gate, "never-evaluated -> stale; after recording -> fresh; "
                  "45 days later -> stale again")
    else:
        _fail(gate, f"never={never_evaluated} fresh={fresh} future={future}")


def t_r2_no_auto_delete() -> None:
    gate = "V-UCEIMR-R2-NO-AUTO-DELETE"
    d = _ROOT / "vault" / "capability_runtime" / "contracts"
    before = {p.name: p.stat().st_mtime_ns for p in d.glob("*.json")}
    R.evaluate_all()
    after = {p.name: p.stat().st_mtime_ns for p in d.glob("*.json")}
    if before == after and before:
        _ok(gate, f"{len(before)} contract file(s) untouched by a full sweep "
                  "-- retirement is proposed, never executed")
    else:
        _fail(gate, f"contract files changed: {set(before) ^ set(after)}")


def t_r2_failopen() -> None:
    gate = "V-UCEIMR-R2-FAILOPEN"
    try:
        a = R.evaluate_all(contracts_dir="C:/nope/does/not/exist")
        b = R.load_log("C:/nope/does/not/exist.json")
        c = R.evaluate_contract(_contract("duplicate_detection",
                                          retirement_condition="x"),
                                root="C:/nope/does/not/exist")
        if a == [] and b == {} and c.status in (R.ACTIVE, R.UNEVALUABLE):
            _ok(gate, "absent contracts dir -> []; absent log -> {}; probe over "
                      f"an absent root -> {c.status}, no raise")
        else:
            _fail(gate, f"a={a} b={b} c={c.status}")
    except Exception as e:  # noqa: BLE001
        _fail(gate, f"raised {type(e).__name__}: {e}")


def main() -> int:
    for t in (t_r1_extracts_capability_claims, t_r1_lineage_traceable,
              t_r1_overlap_audited, t_r1_defer_is_not_novelty,
              t_r1_propose_only, t_r1_approve_writes_contract,
              t_r1_no_acquisition, t_r1_failopen, t_r1_precision,
              t_r1_corpus_yield, t_r1_store_starvation_is_visible,
              t_r1_persists,
              t_g5_persists_full_text, t_g5_closes_the_loop,
              t_g5_default_store_is_read, t_g5_failopen,
              t_r2_evaluates_real, t_r2_retires_on_evidence,
              t_r2_does_not_retire_prematurely, t_r2_unevaluable_is_not_active,
              t_r2_never_and_missing, t_r2_stale_probe, t_r2_no_auto_delete,
              t_r2_failopen):
        try:
            t()
        except Exception as e:  # noqa: BLE001
            _fail(t.__name__, f"unhandled {type(e).__name__}: {e}")
    total = _passes + _fails
    print(f"\nUCEIMR_PASS={_passes}/{total}  threshold={total}/{total}  "
          f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
