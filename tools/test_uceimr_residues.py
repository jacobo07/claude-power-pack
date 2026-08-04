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
from modules.backlog_autopilot import stop1_queue as SQ  # noqa: E402

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


def t_g2_external_is_not_probe_debt() -> None:
    """G2. A condition no repository probe could ever settle must not sit in
    the same bucket as one this repo simply owes a probe for -- otherwise the
    debt count cannot fall for the right reason."""
    gate = "V-UCEIMR-G2-EXTERNAL"
    vs = {v.contract_id: v for v in R.evaluate_all()}
    ext = [k for k, v in vs.items() if v.status == R.EXTERNAL]
    uneval = [k for k, v in vs.items() if v.status == R.UNEVALUABLE]
    if "cost_routing" in ext and "cost_routing" not in uneval:
        _ok(gate, f"EXTERNAL={sorted(ext)} (market/toolchain facts) kept "
                  f"distinct from UNEVALUABLE={sorted(uneval)} (probe debt)")
    else:
        _fail(gate, f"external={ext} uneval={uneval}")


def t_g2_zero_needs_a_denominator() -> None:
    """G2. A zero over a tiny corpus is evidence of a small corpus, not of
    extinction. The probe must refuse to retire a live guard on it."""
    gate = "V-UCEIMR-G2-SAMPLE-GUARD"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "vault" / "osa"
        d.mkdir(parents=True, exist_ok=True)
        log = d / "never_again_log.jsonl"

        log.write_text("".join(
            '{"note": "unrelated incident"}\n' for _ in range(10)),
            encoding="utf-8")
        small = R.probe_spec_depth_selection(root)

        log.write_text("".join(
            '{"note": "unrelated incident"}\n'
            for _ in range(R._MIN_INCIDENT_SAMPLE + 5)), encoding="utf-8")
        big_clean = R.probe_spec_depth_selection(root)

        log.write_text("".join(
            ('{"note": "shipped without a spec"}\n' if i == 0
             else '{"note": "unrelated incident"}\n')
            for i in range(R._MIN_INCIDENT_SAMPLE + 5)), encoding="utf-8")
        big_dirty = R.probe_spec_depth_selection(root)

    if (small[0] is None and big_clean[0] is True and big_dirty[0] is False):
        _ok(gate, f"10 records -> UNEVALUABLE ({small[1][:44]}…); "
                  f"{R._MIN_INCIDENT_SAMPLE + 5} clean -> retire; "
                  "same corpus with 1 spec-omission entry -> stays ACTIVE")
    else:
        _fail(gate, f"small={small[0]} big_clean={big_clean[0]} "
                    f"big_dirty={big_dirty[0]}")


def t_g2_probe_coverage() -> None:
    gate = "V-UCEIMR-G2-COVERAGE"
    contracts = load_contracts()
    ids = {c.id for c in contracts}
    covered = set(R.PROBES) | set(R.EXTERNAL_CONDITIONS)
    vs = {v.contract_id: v for v in R.evaluate_all()}
    never = {k for k, v in vs.items() if v.status == R.NEVER}
    # Every contract is either probed, external, or declared permanent.
    unaccounted = ids - covered - never
    if not unaccounted:
        _ok(gate, f"{len(ids)} contract(s): {len(R.PROBES)} probed, "
                  f"{len(R.EXTERNAL_CONDITIONS)} external, {len(never)} "
                  "permanent, 0 unaccounted")
    else:
        _fail(gate, f"unaccounted: {sorted(unaccounted)}")


def _plan_fm(root: Path, name: str, status: str, date: str = "2026-08-01",
             body: str = "body text\n") -> Path:
    d = root / "vault" / "plans"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(f"---\ntitle: {name}\ndate: {date}\nstatus: {status}\n---\n\n{body}",
                 encoding="utf-8")
    return p


def t_g1_counts_front_matter_only() -> None:
    """G1. The first sweep for this rule reported 15 because it substring-
    matched `status:` anywhere in the head and caught body prose. A queue
    measured by substring is not a queue."""
    gate = "V-UCEIMR-G1-FRONT-MATTER-ONLY"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _plan_fm(root, "open.md", "STOP #1 — BLOCKING")
        _plan_fm(root, "decided.md", "STOP #1 RESOLVED — Owner chose B")
        _plan_fm(root, "mentions.md", "COMPLETE",
                 body="We discussed the STOP #1 protocol at length here.\n")
        (root / "vault" / "plans" / "nofm.md").write_text(
            "no front matter\nstatus: STOP #1\n", encoding="utf-8")
        rep = SQ.scan(root / "vault" / "plans")
    names = {Path(e.path).name for e in rep.entries}
    if names == {"open.md"} and rep.scanned == 3:
        _ok(gate, "1 open of 3 front-matter plans: a body mention, a "
                  "front-matter-less file and a RESOLVED entry are all excluded")
    else:
        _fail(gate, f"entries={sorted(names)} scanned={rep.scanned}")


def t_g1_undated_is_not_age_zero() -> None:
    gate = "V-UCEIMR-G1-UNDATED"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _plan_fm(root, "nodate.md", "STOP #1 — BLOCKING", date="not-a-date")
        rep = SQ.scan(root / "vault" / "plans")
    e = rep.entries[0] if rep.entries else None
    if e and e.undated and e.age_days < 0 and rep.undated == 1:
        _ok(gate, "an unparsable date reports `undated`, never age 0 -- a "
                  "missing date must not read as 'brand new'")
    else:
        _fail(gate, f"entry={e}")


def t_g1_resolve_is_the_producer() -> None:
    """G1. The whole point: something must be able to write the far side of
    the transition, and only with an Owner-supplied reason."""
    gate = "V-UCEIMR-G1-TRANSITION-PRODUCER"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p = _plan_fm(root, "open.md", "STOP #1 — BLOCKING",
                     body="Evidence paragraph that must survive.\n")
        refusals = []
        for kwargs in ({"status": "DONE", "reason": "x"},
                       {"status": SQ.RESOLVED, "reason": "   "}):
            try:
                SQ.resolve(p, **kwargs)
            except ValueError:
                refusals.append(kwargs["status"])
        before = SQ.scan(root / "vault" / "plans").open_count
        SQ.resolve(p, SQ.RESOLVED, "Owner selected option A")
        after = SQ.scan(root / "vault" / "plans").open_count
        text = p.read_text(encoding="utf-8")
    if (refusals == ["DONE", SQ.RESOLVED] and before == 1 and after == 0
            and "Evidence paragraph that must survive." in text
            and "was: STOP #1" in text):
        _ok(gate, "non-terminal status and empty reason refused; a reasoned "
                  "resolve moves 1 -> 0 open, preserves the body, and records "
                  "the prior status")
    else:
        _fail(gate, f"refusals={refusals} before={before} after={after}")


def t_g1_gate_reports_real_queue() -> None:
    gate = "V-UCEIMR-G1-REAL-QUEUE"
    ok, rep, msg = SQ.gate()
    if rep.scanned > 0 and isinstance(ok, bool) and str(rep.open_count) in msg:
        _ok(gate, f"live repo: {rep.open_count} open of {rep.scanned} "
                  f"front-matter plan(s), ok={ok}")
    else:
        _fail(gate, f"scanned={rep.scanned} msg={msg!r}")


def t_g1_failopen() -> None:
    gate = "V-UCEIMR-G1-FAILOPEN"
    try:
        rep = SQ.scan("Z:/nope/does/not/exist")
        ok, _r, _m = SQ.gate("Z:/nope/does/not/exist")
        if rep.open_count == 0 and rep.scanned == 0 and ok:
            _ok(gate, "absent plans dir -> empty report, gate passes, no raise")
        else:
            _fail(gate, f"open={rep.open_count} scanned={rep.scanned} ok={ok}")
    except Exception as e:  # noqa: BLE001
        _fail(gate, f"raised {type(e).__name__}: {e}")


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


def t_g3_scope_separates_unmeasurable_from_unmeasured() -> None:
    """G3. The whole finding. Coverage read "1 of 149" because 140 global rules
    governing other estates sat in the denominator beside 9 local ones. A rule
    nobody CAN measure here and a rule nobody HAS measured are different facts;
    only the second is debt."""
    gate = "V-UCEIMR-G3-SCOPE"
    from modules.rule_compiler.effect_harness import coverage
    cov = coverage()
    size, ins, oos = cov["corpus_size"], cov["in_scope"], cov["out_of_scope"]
    if size is None or ins is None:
        _fail(gate, "compiler unavailable -- scope could not be measured")
        return
    partitions = len(ins) + len(oos) == size and not (set(ins) & set(oos))
    if partitions and len(oos) > 0 and len(ins) > 0:
        _ok(gate, f"{size} rules partition into {len(ins)} measurable here and "
                  f"{len(oos)} out of scope; the two are disjoint and exhaust "
                  "the corpus")
    else:
        _fail(gate, f"size={size} in={len(ins)} out={len(oos)} "
                    f"overlap={sorted(set(ins) & set(oos))[:4]}")


def t_g3_coverage_rose_for_the_right_reason() -> None:
    """G3. Coverage must rise by MEASURING rules, never by shrinking the
    denominator -- `feedback_never_gate_on_a_ratio`. So the gate asserts an
    absolute count of measured rules, and that each names a real corpus rule."""
    gate = "V-UCEIMR-G3-COVERAGE-RISES"
    from modules.rule_compiler.effect_harness import coverage
    cov = coverage()
    ins, measured = set(cov["in_scope"] or []), set(cov["measured"])
    measured_in_scope = sorted(measured & ins)
    if len(measured_in_scope) >= 2:
        _ok(gate, f"{len(measured_in_scope)} in-scope rule(s) carry a measured "
                  f"claim (was 0): {measured_in_scope}; debt is a named set of "
                  f"{len(cov['unmeasured_in_scope'])}")
    else:
        _fail(gate, f"measured in scope: {measured_in_scope} (need >= 2)")


def t_g3_rules_fire_on_their_own_incident() -> None:
    """G3. The claim that matters: not that a rule is registered, but that its
    real detector, run against its real origin, actually fires."""
    gate = "V-UCEIMR-G3-REPLAY-FIRES"
    from modules.rule_compiler import counterfactual as CF
    results = CF.measure_all()
    if not results:
        _fail(gate, "no counterfactual claims registered")
        return
    bad = [r for r in results if r.verdict != CF.WOULD_BLOCK]
    if not bad:
        _ok(gate, f"{len(results)} incident(s) replayed; every rule fired on the "
                  "incident that produced it")
    else:
        _fail(gate, "; ".join(f"{r.claim.rule_id} vs {r.claim.incident_id} -> "
                              f"{r.verdict} ({r.reason})" for r in bad))


def t_g3_crashed_detector_is_not_a_rule_failure() -> None:
    """G3. Measured 2026-08-04: a probe missing one constructor argument was
    judged WOULD_NOT_BLOCK -- accusing a working rule of not covering its own
    origin, in the exact voice of a genuine finding. A crash is absence of
    evidence, never evidence of failure."""
    gate = "V-UCEIMR-G3-CRASH-IS-NOT-A-VERDICT"
    from modules.rule_compiler import counterfactual as CF
    claim = CF.CounterfactualClaim(
        rule_id="HR-FAKE", incident_id="synthetic", incident_input="x",
        probe=["python", "-c", "pass"], fires_pattern="^FIRED")
    crashed = CF.judge(claim, "DETECTOR_ERROR: TypeError: boom\n", 0)
    genuine = CF.judge(claim, "SILENT: no signal\n", 0)
    if crashed[0] == CF.UNMEASURABLE and genuine[0] == CF.WOULD_NOT_BLOCK:
        _ok(gate, "a crashed detector reports UNMEASURABLE; only a detector "
                  "that ran and stayed silent reports WOULD_NOT_BLOCK")
    else:
        _fail(gate, f"crashed={crashed[0]} genuine={genuine[0]}")


def t_g3_novelty_covers_its_own_class() -> None:
    """G3. HR-NOVELTY-001 fired on the IIG *compendium* and stayed silent on
    UCEIMR -- the seventh proposal of the class it governs -- because its title
    splits the two words of 'universal runtime'. A keyword gate is bounded by
    its vocabulary; the shape all seven shared is an enumerated dataset catalog."""
    gate = "V-UCEIMR-G3-NOVELTY-VOCABULARY"
    from modules.spec_gate.gate import check_novelty_gate as g
    fires = {
        "UCEIMR": "UCEIMR -- Universal Capability Evolution & Institutional "
                  "Mining Runtime corpus, 15 datasets.",
        "KSF": "Knowledge Substrate Fabric: 22 new dataset families.",
        "IIG": "Admit the IIG Compendium as an institutional compendium.",
    }
    silent = {
        "ordinary": "Add a retry to the uploader and fix the flaky test.",
        "reading": "Read the corpus of 148 hard rules and report coverage.",
        "rows": "Load 12 rows from the datasets directory into the cache.",
    }
    missed = [k for k, v in fires.items() if not g(v).applies]
    false_pos = [k for k, v in silent.items() if g(v).applies]
    if not missed and not false_pos:
        _ok(gate, f"{len(fires)}/{len(fires)} mega-corpus proposals detected "
                  f"(incl. UCEIMR, previously missed), 0/{len(silent)} false "
                  "positives on ordinary work")
    else:
        _fail(gate, f"missed={missed} false_positives={false_pos}")


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
              t_g2_external_is_not_probe_debt, t_g2_zero_needs_a_denominator,
              t_g2_probe_coverage,
              t_g1_counts_front_matter_only, t_g1_undated_is_not_age_zero,
              t_g1_resolve_is_the_producer, t_g1_gate_reports_real_queue,
              t_g1_failopen,
              t_g3_scope_separates_unmeasurable_from_unmeasured,
              t_g3_coverage_rose_for_the_right_reason,
              t_g3_rules_fire_on_their_own_incident,
              t_g3_crashed_detector_is_not_a_rule_failure,
              t_g3_novelty_covers_its_own_class,
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
