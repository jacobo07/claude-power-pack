#!/usr/bin/env python3
"""V-W9-* -- structural ownership evidence at selection time.

Two subjects, deliberately:

  * the REAL corpus, for SUPPLY. Whether the lever exists at all is a fact
    about this estate and cannot be established on a fixture I designed.
  * a SYNTHETIC repository, for MECHANISM. Discrimination, monotonicity and
    the degradation ladder need a world where I control which owner builds
    what, and a fixture built out of real values would inherit the estate's
    own debt and fail for reasons unrelated to the clause under test.

Every pole is driven. The gates that matter most here are the ones asserting
a NEGATIVE -- that absence is not refutation, that ranking cannot drop an
owner -- and each of those carries a positive control, because a selector
that routed nothing would satisfy every negative assertion in the file.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.ucr_cif import disposition_consumer as dc          # noqa: E402
from modules.ucr_cif import ownership_evidence as oe            # noqa: E402
from modules.ucr_cif import structural_projection as sp         # noqa: E402

PASS = 0
FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global PASS
    PASS += 1
    print("  OK   %-42s %s" % (gate, evidence))


def _fail(gate: str, diagnostic: str) -> None:
    global FAIL
    FAIL += 1
    print("  FAIL %-42s %s" % (gate, diagnostic))


def _check(gate: str, cond: bool, evidence: str, diagnostic: str = "") -> bool:
    if cond:
        _ok(gate, evidence)
    else:
        _fail(gate, diagnostic or evidence)
    return bool(cond)


# --------------------------------------------------------------------------
# Synthetic repository.
#
# Clean by construction: three owners, terms chosen so that exactly one owner
# BUILDS each distinctive term while all three MENTION it in the corpus. That
# is the real defect in miniature -- lexically indistinguishable owners, one
# of which actually holds the capability.
# --------------------------------------------------------------------------
BUILDER = "modules/quarantine_engine"
MENTIONER = "modules/prose_overlay"
THIRD = "modules/other_thing"

#: Distinct tags for the optional filler owners. Each filler needs its OWN
#: distinctive term: sharing one across them pushes it past
#: DISTINCTIVE_MAX_HOLDERS and the selector correctly refuses everything.
FILLER_TAGS = ("orchid", "basalt", "kelvin", "tundra", "marlin", "cobalt")


def _mk_repo(tmp: Path, *, with_projection=True, projection_mangle=None,
             extra_owners=0) -> Path:
    repo = tmp / "repo"
    for owner in (BUILDER, MENTIONER, THIRD):
        (repo / owner).mkdir(parents=True, exist_ok=True)
        (repo / owner / "__init__.py").write_text("", encoding="utf-8")

    # The builder DEFINES the term; the mentioner only talks about it.
    (repo / BUILDER / "quarantine.py").write_text(
        "def quarantine_batch(x):\n    return x\n", encoding="utf-8")
    (repo / MENTIONER / "notes.md").write_text(
        "quarantine " * 400, encoding="utf-8")
    (repo / THIRD / "misc.py").write_text("def unrelated():\n    pass\n",
                                          encoding="utf-8")

    rows = []
    uid = 0

    def row(owner, terms, name):
        nonlocal uid
        uid += 1
        return {"uid": "u%03d" % uid, "name": name,
                "proposed_owner": owner, "evidence_terms": list(terms),
                "disposition": "EXTEND_EXISTING_OWNER",
                "reviewed_by": "test", "confidence": 0.5}

    # All three owners are lexically applicable on the same distinctive pair.
    for i in range(3):
        rows.append(row(BUILDER, ["quarantine", "batch"], "builder %d" % i))
        rows.append(row(MENTIONER, ["quarantine", "batch"], "mention %d" % i))
        rows.append(row(THIRD, ["quarantine", "batch"], "third %d" % i))

    # Optional extra lexical-only owners, so a fixture can exceed MAX_OWNERS
    # and observe what truncation does. Without this the cap never binds and
    # a gate about eviction cannot see its own subject.
    #
    # Each filler gets its OWN distinctive term. Sharing `batch` across them
    # was the first attempt and it routed NOTHING: seven owners holding one
    # term puts it past DISTINCTIVE_MAX_HOLDERS, every match became generic
    # and the selector refused the lot. Adding owners to a term destroys its
    # distinctiveness -- that is the clause working, and a fixture has to
    # respect it rather than fight it.
    for n in range(extra_owners):
        tag = FILLER_TAGS[n]
        name = "modules/filler_%s" % tag
        (repo / name).mkdir(parents=True, exist_ok=True)
        (repo / name / "notes.md").write_text(
            ("quarantine %s " % tag) * 50, encoding="utf-8")
        for i in range(3):
            rows.append(row(name, ["quarantine", tag],
                            "filler %s-%d" % (tag, i)))
    # Padding so the authoritative population clears its floor.
    for i in range(dc.MIN_AUTHORITATIVE_POPULATION + 20):
        rows.append(row(THIRD, ["filler%d" % i, "padding"], "pad %d" % i))

    doc = {"schema_version": dc.SCHEMA_VERSION,
           "compiled_corpus_id": "synthetic0001", "rows": rows}
    led = repo / "vault" / "ucr_cif" / "disposition_ledger.json"
    led.parent.mkdir(parents=True, exist_ok=True)
    led.write_text(json.dumps(doc), encoding="utf-8")

    if with_projection:
        pdoc = sp.build(repo)
        if projection_mangle:
            projection_mangle(pdoc)
        sp.save(pdoc, repo)
    return repo


def _fresh(repo, text, require=False, rank=True):
    """One selection with every cache cleared, so each case is independent.

    `rank` defaults TRUE here and FALSE in production. The mechanism gates
    exist to prove the structural key works; the shipped default is that it
    does not decide, and that default has its own gate below rather than
    being smuggled in as this helper's behaviour.
    """
    dc._CACHE.clear()
    sp._CACHE.clear()
    saved = {k: os.environ.get(k) for k in (dc._REQUIRE_ENV, dc._RANK_ENV)}
    for k, want in ((dc._REQUIRE_ENV, require), (dc._RANK_ENV, rank)):
        if want:
            os.environ[k] = "1"
        else:
            os.environ.pop(k, None)
    try:
        return dc.select_for(text, repo)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


PROPOSAL = ("a quarantine batch subsystem that performs quarantine of a batch "
            "of records, with quarantine batch review")


# --------------------------------------------------------------------------
def gate_supply_real_corpus() -> None:
    """SUPPLY, on the real estate. The lever must exist before it is used."""
    led = ROOT / dc.LEDGER_REL
    doc = json.loads(led.read_text(encoding="utf-8-sig"))
    auth = [r for r in doc["rows"]
            if r.get("disposition") and r.get("reviewed_by")]
    _check("V-W9-SUPPLY-POPULATION-FLOOR", len(auth) >= 900,
           "%d authoritative units examined" % len(auth),
           "population %d below the floor -- a sweep that silently matched "
           "nothing reads exactly like a clean one" % len(auth))

    index = oe.build_structural_index(ROOT)
    owners = {str(r.get("proposed_owner") or "") for r in auth} - {""}

    # (a) UNIT level -- the family that is a PROJECTION of W3's adjudication.
    unit_with = sum(
        1 for r in auth
        if oe.evidence_for(str(r.get("proposed_owner") or ""),
                           {str(t).lower()
                            for t in (r.get("evidence_terms") or [])},
                           index).attributing)
    _check("V-W9-UNIT-LEVEL-IS-A-PROJECTION", unit_with == len(auth),
           "%d/%d = 100%% -- constant, therefore zero discrimination; pinned "
           "so it cannot be re-proposed as coverage" % (unit_with, len(auth)),
           "expected the unit-level predicate to be constant at 100%%, got "
           "%d/%d -- if this has genuinely changed, W3's adjudication changed"
           % (unit_with, len(auth)))

    # (b) TERM level -- the granularity the adjudication did not fix.
    spread = defaultdict(set)
    for r in auth:
        for t in (r.get("evidence_terms") or []):
            spread[str(t).lower()].add(str(r.get("proposed_owner") or ""))
    corpus_holders = {t: len(o) for t, o in spread.items()}

    pairs = held = dpairs = dheld = 0
    for r in auth:
        owner = str(r.get("proposed_owner") or "")
        for t in {str(x).lower() for x in (r.get("evidence_terms") or [])}:
            mine = owner in oe.structural_holders(t, index)
            pairs += 1
            held += bool(mine)
            if corpus_holders.get(t, 1) <= oe.DISTINCTIVE_MAX_HOLDERS:
                dpairs += 1
                dheld += bool(mine)
    rate = held / max(1, pairs)
    drate = dheld / max(1, dpairs)
    _check("V-W9-TERM-LEVEL-DISCRIMINATES", 0.05 < drate < 0.60,
           "distinctive pairs %d/%d = %.1f%% attributed (all pairs %.1f%%) -- "
           "materially below the unit level's 100%%, so the channels are not "
           "the same measurement" % (dheld, dpairs, 100 * drate, 100 * rate),
           "distinctive attribution %.1f%% leaves no lever (at 100%% it is a "
           "projection, at 0%% there is no evidence)" % (100 * drate))

    proj = sp.load(ROOT)
    _check("V-W9-PROJECTION-BOUNDED",
           proj.status == sp.LOADED and 0 < len(proj.terms) <= 5000,
           "projection %s with %d terms over %d ledger owners"
           % (proj.status, len(proj.terms), len(owners)),
           "projection status=%s terms=%d" % (proj.status, len(proj.terms)))


def gate_mechanism(repo: Path) -> None:
    """Discrimination, on a world where I know who builds what."""
    sel = _fresh(repo, PROPOSAL)
    names = [o.owner for o in sel.owners]
    _check("V-W9-CONTROL-ROUTES", len(names) >= 2,
           "positive control: %d owners routed, so the negative gates below "
           "are not satisfied by an empty selection" % len(names),
           "control routed %d owners -- every negative assertion in this file "
           "is vacuous" % len(names))

    _check("V-W9-BUILDER-OUTRANKS-MENTIONER",
           bool(names) and names[0] == BUILDER,
           "%s ranks first; it DEFINES quarantine_batch while %s only mentions "
           "the term 400 times" % (BUILDER, MENTIONER),
           "rank order was %s -- the owner that builds the term did not win"
           % names)

    by = {o.owner: o for o in sel.owners}
    b, m = by.get(BUILDER), by.get(MENTIONER)
    if b and m:
        _check("V-W9-LEXICAL-TIE-BROKEN-STRUCTURALLY",
               abs(b.strength - m.strength) < 1e-9
               and b.structural_strength > m.structural_strength,
               "lexical strength identical (%.4f), structural %.4f vs %.4f -- "
               "the ordering is produced by the new channel and by nothing "
               "else" % (b.strength, b.structural_strength,
                         m.structural_strength),
               "lexical %.4f/%.4f structural %.4f/%.4f"
               % (b.strength, m.strength, b.structural_strength,
                  m.structural_strength))
    else:
        _fail("V-W9-LEXICAL-TIE-BROKEN-STRUCTURALLY",
              "builder or mentioner missing from %s" % names)

    for o in sel.owners:
        if o.structural_strength > o.strength + 1e-9:
            _fail("V-W9-STRUCTURAL-IS-SUB-SUM",
                  "%s structural %.4f exceeds lexical %.4f -- it is supposed "
                  "to be a subset sum and cannot invent support"
                  % (o.owner, o.structural_strength, o.strength))
            break
    else:
        _ok("V-W9-STRUCTURAL-IS-SUB-SUM",
            "every owner: structural <= lexical, so no term is counted twice "
            "and a projection cannot corroborate its source")

    for o in sel.owners:
        if not set(o.attributed) <= set(o.terms):
            _fail("V-W9-ATTRIBUTED-SUBSET-OF-MATCHED",
                  "%s attributed %s not within matched %s"
                  % (o.owner, o.attributed, o.terms))
            break
    else:
        _ok("V-W9-ATTRIBUTED-SUBSET-OF-MATCHED",
            "attributed terms are always terms the prompt actually matched")


def gate_absence_and_degradation(tmp: Path) -> None:
    """Absence of evidence is not evidence of absence, four ways."""
    base = _mk_repo(tmp / "a")
    control = _fresh(base, PROPOSAL)
    control_owners = {o.owner for o in control.owners}

    # No projection at all.
    noproj = _mk_repo(tmp / "b", with_projection=False)
    sel = _fresh(noproj, PROPOSAL)
    _check("V-W9-ABSENT-IS-NOT-REFUTATION",
           sel.structural_status == sp.ABSENT
           and {o.owner for o in sel.owners} == control_owners
           and all(o.structural_strength == 0.0 for o in sel.owners),
           "status=ABSENT, the same %d owners still routed, all structural "
           "strengths 0.0 -- no projection means UNKNOWN, never 'these owners "
           "lack structure'" % len(control_owners),
           "status=%s owners=%s" % (sel.structural_status,
                                    sorted(o.owner for o in sel.owners)))

    # Corrupt projection.
    bad = _mk_repo(tmp / "c")
    (bad / sp.PROJECTION_REL).write_text("{not json", encoding="utf-8")
    sel = _fresh(bad, PROPOSAL)
    _check("V-W9-UNREADABLE-IS-INSTRUMENT-FAILURE",
           sel.structural_status == sp.UNREADABLE
           and {o.owner for o in sel.owners} == control_owners,
           "status=UNREADABLE and routing unchanged -- an instrument failure "
           "is distinguishable from an absence and costs no owner",
           "status=%s" % sel.structural_status)

    # Wrong schema.
    def bump(d):
        d["schema_version"] = sp.SCHEMA_VERSION + 99
    sch = _mk_repo(tmp / "d", projection_mangle=bump)
    sel = _fresh(sch, PROPOSAL)
    _check("V-W9-SCHEMA-MISMATCH-DEGRADES",
           sel.structural_status == sp.SCHEMA
           and {o.owner for o in sel.owners} == control_owners,
           "status=SCHEMA and routing unchanged -- a reader that does not "
           "speak the layout guesses at nothing",
           "status=%s" % sel.structural_status)

    # Ledger regenerated under the projection.
    stale = _mk_repo(tmp / "e")
    led = stale / dc.LEDGER_REL
    doc = json.loads(led.read_text(encoding="utf-8"))
    doc["compiled_corpus_id"] = "a-different-generation"
    led.write_text(json.dumps(doc), encoding="utf-8")
    sel = _fresh(stale, PROPOSAL)
    _check("V-W9-STALE-LEDGER-DETECTED",
           sel.structural_status == sp.STALE_LEDGER
           and all(o.structural_strength == 0.0 for o in sel.owners),
           "status=STALE_LEDGER -- the term universe belongs to a generation "
           "this projection was not built for, so it contributes nothing",
           "status=%s" % sel.structural_status)

    # ...and the same thing at IDENTICAL BYTE SIZE, which is the case that
    # matters and the one the gate above cannot see.
    #
    # Written because mutation W46 SURVIVED: disabling the corpus_id
    # comparison entirely left the suite green, since rewriting the ledger
    # with a longer generation string also changed its length and the SIZE
    # check caught it. The assertion was passing for a reason unrelated to
    # the clause it named. A regenerated ledger of similar length is the
    # ORDINARY outcome of an adjudication pass, so this is a reachable hole
    # rather than a theoretical one, and the fix is a same-length id.
    same = _mk_repo(tmp / "e2")
    led2 = same / dc.LEDGER_REL
    before = led2.stat().st_size
    raw = led2.read_text(encoding="utf-8")
    assert "synthetic0001" in raw, "fixture id missing -- HARNESS defect"
    led2.write_text(raw.replace("synthetic0001", "synthetic0002"),
                    encoding="utf-8")
    after = led2.stat().st_size
    if before != after:
        _fail("V-W9-STALE-DETECTED-AT-EQUAL-SIZE",
              "HARNESS: the id swap changed the file size %d -> %d, so this "
              "case degenerates into the size check again" % (before, after))
    else:
        sel = _fresh(same, PROPOSAL)
        _check("V-W9-STALE-DETECTED-AT-EQUAL-SIZE",
               sel.structural_status == sp.STALE_LEDGER,
               "corpus id moved with the ledger at an identical %d bytes and "
               "the projection still degraded -- the content channel works "
               "with the size channel blind" % after,
               "status=%s at equal size: a regenerated ledger of the same "
               "length was served as current" % sel.structural_status)


def gate_control_switch(tmp: Path) -> None:
    """The paired measurement's control arm must provably BE a control."""
    repo = _mk_repo(tmp / "s")
    treatment = _fresh(repo, PROPOSAL)

    prev = os.environ.get(sp.DISABLE_ENV)
    os.environ[sp.DISABLE_ENV] = "1"
    try:
        dc._CACHE.clear()
        sp._CACHE.clear()
        control = dc.select_for(PROPOSAL, repo)
    finally:
        if prev is None:
            os.environ.pop(sp.DISABLE_ENV, None)
        else:
            os.environ[sp.DISABLE_ENV] = prev
        dc._CACHE.clear()
        sp._CACHE.clear()

    _check("V-W9-CONTROL-ARM-IS-W8",
           control.structural_status == sp.DISABLED
           and all(o.structural_strength == 0.0 for o in control.owners)
           and {o.owner for o in control.owners}
           == {o.owner for o in treatment.owners},
           "status=DISABLED, every structural strength 0.0, identical owner "
           "set -- withholding the evidence reproduces W8's ordering over the "
           "same population, which is what makes the two arms comparable",
           "status=%s" % control.structural_status)

    _check("V-W9-DISABLED-IS-NOT-ABSENT",
           sp.DISABLED != sp.ABSENT
           and control.structural_status != sp.ABSENT,
           "DISABLED is its own status -- 'switched off for this run' and "
           "'never built' are different facts, and a control arm that cannot "
           "tell them apart cannot say it was one",
           "DISABLED collapsed into ABSENT")

    _check("V-W9-CONTROL-AND-TREATMENT-DIFFER",
           [o.owner for o in control.owners]
           != [o.owner for o in treatment.owners],
           "the two arms produce different orders on one population, so the "
           "switch is measuring something rather than toggling a no-op",
           "both arms identical -- the control proves nothing because the "
           "treatment does nothing")


def gate_freshness_and_cost(tmp: Path) -> None:
    """The binding must survive a clone and must not re-read the ledger."""
    repo = _mk_repo(tmp / "f")

    # mtime alone must NOT invalidate: no clone preserves it.
    led = repo / dc.LEDGER_REL
    st = led.stat()
    os.utime(led, ns=(st.st_atime_ns + 10**9, st.st_mtime_ns + 10**9))
    sp._CACHE.clear()
    proj = sp.load(repo, corpus_id="synthetic0001")
    _check("V-W9-BINDING-SURVIVES-MTIME-CHANGE", proj.status == sp.LOADED,
           "ledger mtime moved by 1 s and the projection is still LOADED -- "
           "a fresh checkout does not silently lose structural evidence",
           "status=%s after an mtime-only change" % proj.status)

    # The read path must not consult the ledger body.
    sp._CACHE.clear()
    original = sp._ledger_binding

    def explode(*a, **k):
        raise AssertionError("_ledger_binding was called on the read path")

    sp._ledger_binding = explode
    try:
        proj = sp.load(repo, corpus_id="synthetic0001")
        _check("V-W9-NO-LEDGER-REPARSE-ON-READ", proj.status == sp.LOADED,
               "load() completed with _ledger_binding disabled, so the 1.9 MB "
               "ledger is not re-parsed per selection (that cost 70.8 ms)",
               "status=%s" % proj.status)
    except AssertionError as exc:
        _fail("V-W9-NO-LEDGER-REPARSE-ON-READ", str(exc))
    finally:
        sp._ledger_binding = original

    # Source movement is detectable, explicitly.
    (repo / BUILDER / "newfile.py").write_text("def added():\n    pass\n",
                                               encoding="utf-8")
    sp._CACHE.clear()
    info = sp.verify(repo)
    _check("V-W9-SOURCE-MOVEMENT-DETECTED", info.get("source_fresh") is False,
           "a new source file makes --verify report source_fresh=False while "
           "the binding stays valid -- the two tiers are independent",
           "verify reported %r" % (info.get("source_fresh"),))


def gate_ranking_cannot_drop_an_owner(tmp: Path) -> None:
    """M2 reorders. It must never change WHICH owners are routed."""
    repo = _mk_repo(tmp / "g")
    with_structural = _fresh(repo, PROPOSAL)

    # The W8 world: same repo, projection removed. Ranking is the only
    # difference, so the routed SET must be identical.
    noproj = _mk_repo(tmp / "h", with_projection=False)
    w8 = _fresh(noproj, PROPOSAL)

    a = {o.owner for o in with_structural.owners}
    b = {o.owner for o in w8.owners}
    _check("V-W9-RANKING-PRESERVES-THE-OWNER-SET", a == b and len(a) >= 2,
           "identical owner sets (%d owners, below the cap of %d) with and "
           "without structural evidence; BELOW THE CAP only the order differs"
           % (len(a), dc.MAX_OWNERS),
           "with=%s without=%s" % (sorted(a), sorted(b)))

    order_changed = ([o.owner for o in with_structural.owners]
                     != [o.owner for o in w8.owners])
    _check("V-W9-RANKING-ACTUALLY-CHANGES-ORDER", order_changed,
           "the order DID change (%s -> %s), so the preceding gate is not "
           "passing because the mechanism is inert"
           % ([o.owner for o in w8.owners][:2],
              [o.owner for o in with_structural.owners][:2]),
           "order identical -- V-W9-RANKING-PRESERVES-THE-OWNER-SET would "
           "pass even with the mechanism disconnected")


def gate_shipped_default_and_the_cap(tmp: Path) -> None:
    """What actually ships, and what ranking costs once the list is cut.

    Both claims here were WRONG in this wave's first version. I wrote that
    ranking "cannot lose a true positive by construction" and the gate above
    agreed -- on a fixture with three owners against a cap of five, which is
    a fixture structurally unable to observe the property. The paired run on
    real prompts then found two labelled cases whose true owner sat at index
    4, the last visible slot, and was pushed out of the selection entirely.
    """
    n_filler = 4
    repo = _mk_repo(tmp / "cap", extra_owners=n_filler)
    # The prompt must name each filler's own distinctive term, or the filler
    # is not applicable and the candidate list never exceeds the cap.
    prompt = PROPOSAL + " " + " ".join(FILLER_TAGS[:n_filler])

    shipped = _fresh(repo, prompt, rank=False)
    ranked = _fresh(repo, prompt, rank=True)

    lex_order = sorted((o.owner for o in shipped.owners),
                       key=lambda n: dc._rank_key_lexical(
                           next(x for x in shipped.owners if x.owner == n)))
    _check("V-W9-SHIPPED-DEFAULT-IS-W8",
           dc.STRUCTURAL_RANKING_ENABLED is False
           and [o.owner for o in shipped.owners] == lex_order,
           "STRUCTURAL_RANKING_ENABLED is False and the emitted order is "
           "exactly W8's lexical key -- W9 measured the structural key "
           "against the independent oracle and did not promote it",
           "the shipped default is not W8's ordering")

    _check("V-W9-STRUCTURAL-STILL-COMPUTED-WHEN-OFF",
           shipped.structural_status == sp.LOADED
           and any(o.structural_strength > 0 for o in shipped.owners),
           "with ranking off the evidence is still computed and reported "
           "(status=%s) -- available to explain and to re-measure, it simply "
           "does not decide" % shipped.structural_status,
           "structural evidence vanished when ranking was disabled")

    sh = [o.owner for o in shipped.owners]
    rk = [o.owner for o in ranked.owners]
    evicted = set(sh) - set(rk)
    _check("V-W9-CAP-CAN-EVICT-AN-OWNER",
           len(sh) == dc.MAX_OWNERS and bool(evicted),
           "above the cap, enabling structural ranking evicts %s from the %d "
           "visible slots -- a reorder IS a loss once the list is truncated, "
           "which is the measured reason the promotion was withdrawn"
           % (sorted(x.split("/")[-1] for x in evicted), dc.MAX_OWNERS),
           "with %d visible owners and a cap of %d nothing was evicted, so "
           "this gate cannot see the property it names"
           % (len(sh), dc.MAX_OWNERS))


def gate_m3_admission(tmp: Path) -> None:
    """The clause that CAN refuse: off by default, and only ever enabled."""
    repo = _mk_repo(tmp / "i")
    _check("V-W9-M3-OFF-BY-DEFAULT",
           dc.REQUIRE_STRUCTURAL_ATTRIBUTION is False,
           "REQUIRE_STRUCTURAL_ATTRIBUTION is False in source -- admission is "
           "a measured candidate, not a default",
           "shipped default is %r" % dc.REQUIRE_STRUCTURAL_ATTRIBUTION)

    off = _fresh(repo, PROPOSAL, require=False)
    on = _fresh(repo, PROPOSAL, require=True)
    off_owners = {o.owner for o in off.owners}
    on_owners = {o.owner for o in on.owners}
    _check("V-W9-M3-REFUSES-LEXICAL-ONLY-OWNERS",
           BUILDER in on_owners and MENTIONER in off_owners
           and MENTIONER not in on_owners,
           "clause ON drops %s (mentions only) and keeps %s (defines it); "
           "%d owners -> %d" % (MENTIONER, BUILDER, len(off_owners),
                                len(on_owners)),
           "off=%s on=%s" % (sorted(off_owners), sorted(on_owners)))
    _check("V-W9-M3-REFUSALS-ARE-COUNTED",
           on.rejected_no_attribution > 0 and off.rejected_no_attribution == 0,
           "rejected_no_attribution %d with the clause on, %d with it off -- "
           "a run can never be read as having filtered when it did not"
           % (on.rejected_no_attribution, off.rejected_no_attribution),
           "on=%d off=%d" % (on.rejected_no_attribution,
                             off.rejected_no_attribution))

    prev = dc.REQUIRE_STRUCTURAL_ATTRIBUTION
    dc.REQUIRE_STRUCTURAL_ATTRIBUTION = True
    os.environ[dc._REQUIRE_ENV] = "0"
    try:
        _check("V-W9-M3-ENV-CANNOT-WEAKEN", dc._require_structural() is True,
               "with the source default ON, the env var set to '0' does not "
               "turn it off -- an environment cannot silently disable a "
               "released filter",
               "env '0' disabled a source-enabled clause")
    finally:
        dc.REQUIRE_STRUCTURAL_ATTRIBUTION = prev
        os.environ.pop(dc._REQUIRE_ENV, None)


def main() -> int:
    print("=== UCR-CIF W9 -- structural ownership evidence ===")
    t0 = time.perf_counter()
    tmp = Path(tempfile.mkdtemp(prefix="w9_"))
    try:
        print("-- supply (real corpus)")
        gate_supply_real_corpus()
        print("-- mechanism (synthetic)")
        gate_mechanism(_mk_repo(tmp / "m"))
        print("-- absence and degradation")
        gate_absence_and_degradation(tmp)
        print("-- control switch")
        gate_control_switch(tmp)
        print("-- freshness and cost")
        gate_freshness_and_cost(tmp)
        print("-- ranking safety")
        gate_ranking_cannot_drop_an_owner(tmp)
        print("-- shipped default and the cap")
        gate_shipped_default_and_the_cap(tmp)
        print("-- M3 admission")
        gate_m3_admission(tmp)
    finally:
        dc._CACHE.clear()
        sp._CACHE.clear()
        shutil.rmtree(tmp, ignore_errors=True)

    total = PASS + FAIL
    print("W9_STRUCTURAL_PASS=%d/%d  threshold=%d/%d  (%.1fs)"
          % (PASS, total, total, total, time.perf_counter() - t0))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
