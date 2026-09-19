#!/usr/bin/env python3
"""V-W3-LIFE-* -- capability lifecycle: authority, revocation, history (W3).

The claim this file defends is not "a status can be stored". It is:

    a revoked capability stops being inherited by the REAL selector, on every
    path that reaches it, and its history stays reconstructable.

Every destructive case runs against a contract store this file CREATES, OWNS
and DELETES. The real store is read (for the ratchet) and never mutated -- a
destructive fixture built from live data is the one mistake reverting a commit
cannot undo.

Structure, and why each half exists:

  migration   PR-W3-1  deterministic, idempotent, no blind default-ACTIVE
  inheritance PR-W3-2  an ACTIVE capability IS selected by the real consumer
  revocation  PR-W3-3  the same capability, revoked, is NOT -- same code path
  history     PR-W3-4  the revoked capability is still reconstructable
  supersession PR-W3-5 lineage survives replacement; a successor is required
  unknown     PR-W3-6  absence never becomes ACTIVE
  bypass      PR-W3-7  every route to the selector honours it, incl. derive()
  conflict    PR-W3-8  a moved subject is refused, not overwritten
  resume      PR-W3-10 an interrupted migration completes without duplicating
  ratchet              the UNKNOWN population may only shrink

PR-W3-2 and PR-W3-3 are one experiment with the lifecycle as its only variable.
Asserting the revoked case alone would pass against a selector that returns
nothing at all, so the ACTIVE pole is what makes the revoked pole mean anything.

Run: python tools/test_capability_lifecycle.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.applicability import (  # noqa: E402
    MissionContext, Verdict, compile_stack, evaluate, evaluate_all,
)
from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, load_contracts, save_contract,
)
from modules.capability_runtime.derivatives import derive  # noqa: E402
from modules.capability_runtime.lifecycle import (  # noqa: E402
    Lifecycle, LifecycleError, WITHDRAWN, classify_population,
    current_from_log, history, inheritable, load_log, reconstruct_at,
    state_of, transition,
)

RATCHET = _PP_ROOT / "vault" / "capability_runtime" / "lifecycle_ratchet.json"

_PASS = 0
_FAIL = 0


def _ok(gate, ev):
    global _PASS
    _PASS += 1
    print(f"  PASS {gate}: {ev}")


def _fail(gate, diag):
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}: {diag}")


def _check(gate, cond, ev, diag=""):
    _ok(gate, ev) if cond else _fail(gate, diag or ev)


# --------------------------------------------------------------------------- #
# Fixture. A capability whose triggers a test prompt hits, with no required
# evidence and no prerequisites, so NOTHING but lifecycle can decide its fate.
# Handing the selector the weakest surrounding conditions is what makes the
# lifecycle the only live variable.
# --------------------------------------------------------------------------- #
PROMPT = "please run the zzyzx widget audit now"


def _fixture(cid="zzyzx_audit", **over) -> CapabilityContract:
    d = dict(
        id=cid, name="Zzyzx Audit", owner="test-harness",
        triggers=["zzyzx widget audit"], consumers=["test-harness"],
        scope=["zzyzx"], failure_risk_if_omitted="critical",
        expected_leverage="high", maturity="mature",
        activation_cost="low", context_cost="low", operational_cost="low",
        retirement_condition="never",
    )
    d.update(over)
    return CapabilityContract(**d)


def _store(tmp: Path, *contracts) -> Path:
    d = tmp / "contracts"
    d.mkdir(parents=True, exist_ok=True)
    for c in contracts:
        save_contract(c, d)
    return d


def _selected(contracts_dir, prompt=PROMPT) -> dict:
    ctx = MissionContext(description=prompt)
    return compile_stack(ctx, contracts_dir=contracts_dir)


# --------------------------------------------------------------------------- #
# PR-W3-2 / PR-W3-3 -- inheritance, then revocation, on one subject.
# --------------------------------------------------------------------------- #
def t_inheritance_and_revocation() -> None:
    print("\n[PR-W3-2 / PR-W3-3 -- active inherits, revoked does not]")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        log = tmp / "lifecycle_log.jsonl"
        cdir = _store(tmp, _fixture(lifecycle="active"))

        stack = _selected(cdir)
        _check("V-W3-LIFE-ACTIVE-INHERITED",
               "zzyzx_audit" in stack["activate"],
               f"ACTIVE capability selected: activate={stack['activate']}",
               f"an ACTIVE, relevant capability was not selected: {stack}")

        # The institutional route -- not a hand-edited file.
        ev = transition("zzyzx_audit", Lifecycle.REVOKED,
                        expected=Lifecycle.ACTIVE, actor="owner:test",
                        reason="incident: fabricated findings",
                        evidence=["vault/audits/fake.md"],
                        contracts_dir=cdir, log_path=log)
        _check("V-W3-LIFE-TRANSITION-RECORDED",
               ev.from_state == "active" and ev.to_state == "revoked"
               and ev.actor == "owner:test",
               f"transition recorded {ev.from_state} -> {ev.to_state} "
               f"by {ev.actor}",
               f"transition did not record provenance: {ev.to_dict()}")

        stack2 = _selected(cdir)
        _check("V-W3-LIFE-REVOKED-NOT-INHERITED",
               "zzyzx_audit" not in stack2["activate"],
               f"revoked capability withheld: activate={stack2['activate']}",
               f"REVOKED capability still activated: {stack2['activate']}")
        _check("V-W3-LIFE-REVOKED-REPORTED",
               stack2["withheld"].get("zzyzx_audit") == "revoked",
               f"reported in its own bucket: withheld={stack2['withheld']}",
               f"withheld bucket did not name it: {stack2}")

        # The refusal must say WHY, and must not masquerade as a missing fact.
        res = [r for r in stack2["results"] if r.capability_id == "zzyzx_audit"]
        _check("V-W3-LIFE-REFUSAL-IS-TYPED",
               res and res[0].verdict is Verdict.WITHHELD_BY_LIFECYCLE
               and "revoked" in res[0].reason,
               f"verdict={res[0].verdict.value}, reason={res[0].reason!r}",
               f"refusal is untyped or unexplained: {res}")


# --------------------------------------------------------------------------- #
# PR-W3-7 -- every route to the selector, and the derivative route.
# --------------------------------------------------------------------------- #
def t_bypass() -> None:
    print("\n[PR-W3-7 -- bypass attempts]")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        c = _fixture(lifecycle="revoked")
        cdir = _store(tmp, c)
        ctx = MissionContext(description=PROMPT)

        _check("V-W3-LIFE-BYPASS-EVALUATE",
               evaluate(c, ctx).verdict is Verdict.WITHHELD_BY_LIFECYCLE,
               "evaluate() withholds",
               "evaluate() let a revoked capability through")

        allres = evaluate_all(ctx, contracts_dir=cdir)
        _check("V-W3-LIFE-BYPASS-EVALUATE-ALL",
               all(r.verdict is Verdict.WITHHELD_BY_LIFECYCLE for r in allres),
               "evaluate_all() withholds",
               f"evaluate_all() let it through: {[r.verdict for r in allres]}")

        # Gate 0 must beat a mission that supplies EVERYTHING a capability could
        # want -- evidence, runtime, prerequisites, resolved owner. If any later
        # gate could overturn it, this is where it would show.
        rich = MissionContext(
            description=PROMPT, available_evidence=["source", "tests"],
            runtime="python", resolved_owners=["test-harness"],
            satisfied_prerequisites=["everything"], held_scopes=[])
        _check("V-W3-LIFE-BYPASS-RICH-CONTEXT",
               evaluate(c, rich).verdict is Verdict.WITHHELD_BY_LIFECYCLE,
               "a maximally-satisfied mission still cannot activate it",
               "a richer context overturned the lifecycle gate")

        # The real product consumer, through its own entry point, at BOTH poles.
        #
        # `drivers` holds (capability_id, verdict) PAIRS. The first version of
        # this check tested `"zzyzx_audit" not in drivers`, which compares a
        # string against tuples and can therefore never match -- it passed with
        # the gate removed. Asserting on the verdict a driver carries is what
        # makes it discriminating.
        from modules.gsd_x.tier import classify_prompt
        POSITIVE = {"MANDATORY", "RECOMMENDED", "AVAILABLE_ON_TRIGGER"}

        active_dir = _store(tmp / "active", _fixture(lifecycle="active"))
        tv_on = classify_prompt(PROMPT, contracts_dir=active_dir)
        drove = {v for cid, v in tv_on.drivers if cid == "zzyzx_audit"}
        _check("V-W3-LIFE-CONTROL-TIER-CAN-DRIVE",
               drove & POSITIVE and not tv_on.abstained,
               f"active: tier={tv_on.tier} driven by {sorted(drove)}",
               f"the tier consumer never drives on this fixture "
               f"(tier={tv_on.tier}, drivers={tv_on.drivers}); the revoked "
               "assertion below would pass vacuously")

        tv_off = classify_prompt(PROMPT, contracts_dir=cdir)
        drove_off = {v for cid, v in tv_off.drivers if cid == "zzyzx_audit"}
        _check("V-W3-LIFE-BYPASS-TIER",
               not (drove_off & POSITIVE),
               f"revoked: tier={tv_off.tier}, zzyzx_audit carries "
               f"{sorted(drove_off) or 'no verdict'} -- never a positive one",
               f"the live tier consumer drove on a revoked capability: "
               f"{tv_off.drivers}")

        # Derivation: a live child may not be cut from withdrawn authority.
        try:
            derive(c, "someproject", {"triggers": ["zzyzx widget audit", "x"]})
            _fail("V-W3-LIFE-BYPASS-DERIVE",
                  "derived a live child from a REVOKED parent")
        except ContractError as exc:
            _check("V-W3-LIFE-BYPASS-DERIVE", "lifecycle" in str(exc).lower(),
                   f"derive() refused: {str(exc)[:80]}",
                   f"refused for the wrong reason: {exc}")

        # Laundering: set the child's lifecycle straight through an override.
        active_parent = _fixture(cid="zzyzx_parent", lifecycle="unknown")
        try:
            derive(active_parent, "someproject",
                   {"lifecycle": "active", "triggers": ["a", "b"]})
            _fail("V-W3-LIFE-BYPASS-LAUNDER",
                  "an override minted ACTIVE authority with no transition")
        except ContractError as exc:
            _check("V-W3-LIFE-BYPASS-LAUNDER", "lifecycle" in str(exc).lower(),
                   f"override refused: {str(exc)[:80]}",
                   f"refused for the wrong reason: {exc}")


# --------------------------------------------------------------------------- #
# PR-W3-4 / PR-W3-5 -- history and supersession.
# --------------------------------------------------------------------------- #
def t_history_and_supersession() -> None:
    print("\n[PR-W3-4 / PR-W3-5 -- history, supersession, lineage]")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        log = tmp / "lifecycle_log.jsonl"
        old = _fixture(cid="zzyzx_v1", lifecycle="active")
        new = _fixture(cid="zzyzx_v2", lifecycle="active")
        cdir = _store(tmp, old, new)

        # SUPERSEDED without naming the successor is refused.
        try:
            transition("zzyzx_v1", Lifecycle.SUPERSEDED,
                       expected=Lifecycle.ACTIVE, actor="owner:test",
                       reason="v2 replaces it", contracts_dir=cdir,
                       log_path=log)
            _fail("V-W3-LIFE-SUPERSEDE-NEEDS-SUCCESSOR",
                  "SUPERSEDED accepted with no successor")
        except LifecycleError as exc:
            _check("V-W3-LIFE-SUPERSEDE-NEEDS-SUCCESSOR",
                   "successor" in str(exc),
                   f"refused: {str(exc)[:70]}", str(exc))

        ev = transition("zzyzx_v1", Lifecycle.SUPERSEDED,
                        expected=Lifecycle.ACTIVE, actor="owner:test",
                        reason="v2 supersedes v1", successor="zzyzx_v2",
                        contracts_dir=cdir, log_path=log)
        _check("V-W3-LIFE-SUPERSEDE-LINEAGE",
               ev.successor == "zzyzx_v2",
               "supersession names its successor in the record",
               f"lineage lost: {ev.to_dict()}")

        stack = _selected(cdir)
        _check("V-W3-LIFE-SUCCESSOR-TAKES-AUTHORITY",
               "zzyzx_v2" in stack["activate"] and "zzyzx_v1" not in stack["activate"],
               f"authority moved to the successor: activate={stack['activate']}",
               f"supersession did not move authority: {stack['activate']}")

        # PR-W3-4: the superseded capability is still fully reconstructable.
        evs = load_log(log)
        h = history("zzyzx_v1", events=evs)
        _check("V-W3-LIFE-HISTORY-PRESERVED",
               len(h) == 1 and h[0].from_state == "active"
               and h[0].reason and h[0].evidence is not None,
               f"history readable: {h[0].from_state} -> {h[0].to_state} "
               f"({h[0].reason!r})",
               f"history not reconstructable: {[e.to_dict() for e in h]}")

        before = reconstruct_at("zzyzx_v1", "2000-01-01T00:00:00+00:00",
                                events=evs)
        after = reconstruct_at("zzyzx_v1", "2999-01-01T00:00:00+00:00",
                               events=evs)
        _check("V-W3-LIFE-RECONSTRUCT-AT",
               before is Lifecycle.UNKNOWN and after is Lifecycle.SUPERSEDED,
               f"state at t0={before.value}, at t1={after.value}",
               f"reconstruction wrong: t0={before}, t1={after}")

        # Terminal for inheritance, not for history: it may not be resurrected.
        try:
            transition("zzyzx_v1", Lifecycle.ACTIVE,
                       expected=Lifecycle.SUPERSEDED, actor="owner:test",
                       reason="undo", contracts_dir=cdir, log_path=log)
            _fail("V-W3-LIFE-SUPERSEDED-IS-TERMINAL",
                  "a superseded capability was resurrected in place")
        except LifecycleError as exc:
            _check("V-W3-LIFE-SUPERSEDED-IS-TERMINAL",
                   "not a legal transition" in str(exc),
                   f"refused: {str(exc)[:70]}", str(exc))


def t_suspended_is_not_revoked() -> None:
    print("\n[semantics -- SUSPENDED != REVOKED]")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        log = tmp / "lifecycle_log.jsonl"
        cdir = _store(tmp, _fixture(lifecycle="active"))

        transition("zzyzx_audit", Lifecycle.SUSPENDED,
                   expected=Lifecycle.ACTIVE, actor="owner:test",
                   reason="pending incident review", contracts_dir=cdir,
                   log_path=log)
        _check("V-W3-LIFE-SUSPENDED-WITHHELD",
               "zzyzx_audit" not in _selected(cdir)["activate"],
               "a suspended capability is withheld",
               "SUSPENDED was inherited")

        transition("zzyzx_audit", Lifecycle.ACTIVE,
                   expected=Lifecycle.SUSPENDED, actor="owner:test",
                   reason="incident closed, evidence restored",
                   contracts_dir=cdir, log_path=log)
        _check("V-W3-LIFE-SUSPENDED-IS-REVERSIBLE",
               "zzyzx_audit" in _selected(cdir)["activate"],
               "suspension lifted -- authority returns",
               "SUSPENDED behaved as terminal; it is not REVOKED")

        # And REVOKED genuinely is terminal, so the two are not synonyms.
        transition("zzyzx_audit", Lifecycle.REVOKED,
                   expected=Lifecycle.ACTIVE, actor="owner:test",
                   reason="withdrawn for good", contracts_dir=cdir,
                   log_path=log)
        try:
            transition("zzyzx_audit", Lifecycle.ACTIVE,
                       expected=Lifecycle.REVOKED, actor="owner:test",
                       reason="undo", contracts_dir=cdir, log_path=log)
            _fail("V-W3-LIFE-REVOKED-IS-TERMINAL", "a REVOKED capability returned")
        except LifecycleError as exc:
            _check("V-W3-LIFE-REVOKED-IS-TERMINAL",
                   "not a legal transition" in str(exc),
                   "REVOKED cannot be resurrected in place", str(exc))


# --------------------------------------------------------------------------- #
# PR-W3-6 -- unknown stays unknown.
# --------------------------------------------------------------------------- #
def t_unknown() -> None:
    print("\n[PR-W3-6 -- absence never becomes ACTIVE]")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # No lifecycle field at all, and a nonsense one.
        cdir = _store(tmp, _fixture(cid="zzyzx_absent"),
                      _fixture(cid="zzyzx_garbage", lifecycle="definitely-fine"))
        cs = {c.id: c for c in load_contracts(cdir)}
        _check("V-W3-LIFE-ABSENT-IS-UNKNOWN",
               state_of(cs["zzyzx_absent"]) is Lifecycle.UNKNOWN,
               "a contract with no lifecycle reads UNKNOWN, not ACTIVE",
               f"absence resolved to {state_of(cs['zzyzx_absent'])}")
        _check("V-W3-LIFE-GARBAGE-IS-UNKNOWN",
               state_of(cs["zzyzx_garbage"]) is Lifecycle.UNKNOWN,
               "an unrecognised lifecycle reads UNKNOWN, not ACTIVE",
               f"garbage resolved to {state_of(cs['zzyzx_garbage'])}")

        stack = _selected(cdir)
        _check("V-W3-LIFE-UNKNOWN-IS-UNVERIFIED",
               set(stack["unverified"]) == {"zzyzx_absent", "zzyzx_garbage"},
               f"both reported unverified: {sorted(stack['unverified'])}",
               f"unverified bucket wrong: {stack['unverified']}")

        # A WRITE of an unrecognised state must fail closed, unlike a read.
        try:
            transition("zzyzx_absent", "definitely-fine", actor="owner:test",
                       reason="x", contracts_dir=cdir,
                       log_path=tmp / "l.jsonl")
            _fail("V-W3-LIFE-WRITE-FAILS-CLOSED",
                  "an unrecognised state was written as a classification")
        except LifecycleError as exc:
            _check("V-W3-LIFE-WRITE-FAILS-CLOSED",
                   "not a lifecycle state" in str(exc),
                   f"refused: {str(exc)[:70]}", str(exc))


# --------------------------------------------------------------------------- #
# PR-W3-8 -- institutional concurrent mutation.
# --------------------------------------------------------------------------- #
def t_conflict() -> None:
    print("\n[PR-W3-8 -- concurrent mutation, no lost update]")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        log = tmp / "lifecycle_log.jsonl"
        cdir = _store(tmp, _fixture(lifecycle="active"))

        # Writer A reads ACTIVE. Writer B lands a suspension first.
        a_expected = Lifecycle.ACTIVE
        transition("zzyzx_audit", Lifecycle.SUSPENDED, expected=a_expected,
                   actor="writer:B", reason="B got there first",
                   contracts_dir=cdir, log_path=log)

        # A now commits against the state it reviewed. It must be refused.
        try:
            transition("zzyzx_audit", Lifecycle.REVOKED, expected=a_expected,
                       actor="writer:A", reason="A's decision",
                       contracts_dir=cdir, log_path=log)
            _fail("V-W3-LIFE-CONFLICT-REFUSED",
                  "A overwrote B -- a lost institutional update")
        except LifecycleError as exc:
            _check("V-W3-LIFE-CONFLICT-REFUSED",
                   "expected" in str(exc) and "suspended" in str(exc),
                   f"stale writer refused: {str(exc)[:90]}", str(exc))

        cs = {c.id: c for c in load_contracts(cdir)}
        _check("V-W3-LIFE-CONFLICT-NO-WRITE",
               state_of(cs["zzyzx_audit"]) is Lifecycle.SUSPENDED
               and len(load_log(log)) == 1,
               "B's state survived and the refusal wrote no history row",
               f"state={state_of(cs['zzyzx_audit'])}, rows={len(load_log(log))}")

        # A caller that did not look at all is refused on a classified subject.
        try:
            transition("zzyzx_audit", Lifecycle.REVOKED, expected=None,
                       actor="writer:C", reason="did not look",
                       contracts_dir=cdir, log_path=log)
            _fail("V-W3-LIFE-CONFLICT-BLIND-REFUSED",
                  "a blind write was accepted on a classified subject")
        except LifecycleError as exc:
            _check("V-W3-LIFE-CONFLICT-BLIND-REFUSED",
                   "state the expected state" in str(exc),
                   f"blind write refused: {str(exc)[:80]}", str(exc))

        # Provenance is not optional.
        for field_name, kw in (("actor", {"actor": "", "reason": "r"}),
                               ("reason", {"actor": "a", "reason": ""})):
            try:
                transition("zzyzx_audit", Lifecycle.REVOKED,
                           expected=Lifecycle.SUSPENDED, contracts_dir=cdir,
                           log_path=log, **kw)
                _fail(f"V-W3-LIFE-PROVENANCE-{field_name.upper()}",
                      f"a transition with no {field_name} was accepted")
            except LifecycleError:
                _ok(f"V-W3-LIFE-PROVENANCE-{field_name.upper()}",
                    f"a transition with no {field_name} is refused")


# --------------------------------------------------------------------------- #
# PR-W3-1 / PR-W3-10 -- migration determinism, resume, no blind ACTIVE.
# --------------------------------------------------------------------------- #
def t_migration() -> None:
    print("\n[PR-W3-1 / PR-W3-10 -- migration: deterministic, resumable]")
    import tools.capability_lifecycle_migrate as M  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        log = tmp / "lifecycle_log.jsonl"
        # One with a probeable-permanent condition, one with none at all.
        cdir = _store(
            tmp,
            _fixture(cid="zzyzx_permanent", retirement_condition="never"),
            _fixture(cid="zzyzx_silent", retirement_condition=""),
        )
        cs = load_contracts(cdir)
        p1 = M.plan(contracts=cs, contracts_dir=cdir)
        p2 = M.plan(contracts=load_contracts(cdir), contracts_dir=cdir)
        _check("V-W3-MIG-DETERMINISTIC",
               json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True),
               "the same repository state yields the same plan",
               "plan is not deterministic")

        ids_write = {r["id"] for r in p1["to_write"]}
        ids_unknown = {r["id"] for r in p1["stays_unknown"]}
        _check("V-W3-MIG-NO-BLIND-ACTIVE",
               ids_write == {"zzyzx_permanent"}
               and ids_unknown == {"zzyzx_silent"},
               "a contract with no retirement condition stays UNKNOWN while a "
               "declared-permanent one is classified",
               f"write={sorted(ids_write)} unknown={sorted(ids_unknown)}")
        _check("V-W3-MIG-REASON-IS-NAMED",
               all(r["why"] for r in p1["stays_unknown"]),
               "every UNKNOWN carries its own named reason",
               "an UNKNOWN has no reason -- an anonymous unresolved pile")

        M.apply(p1, contracts_dir=cdir, log_path=log)
        rows_after_first = len(load_log(log))

        # PR-W3-10: resume. Re-planning and re-applying after a completed run
        # must add nothing -- this is the interrupted-and-restarted case, since
        # each contract is independent and the log is append-only.
        p3 = M.plan(contracts_dir=cdir)
        out3 = M.apply(p3, contracts_dir=cdir, log_path=log)
        _check("V-W3-MIG-RESUME-NO-DUPLICATE",
               out3["written"] == [] and len(load_log(log)) == rows_after_first,
               f"re-run wrote 0 rows; log stayed at {rows_after_first}",
               f"re-run duplicated: {out3}, rows={len(load_log(log))}")

        cs2 = {c.id: c for c in load_contracts(cdir)}
        _check("V-W3-MIG-PROJECTION-MATCHES-LOG",
               all(state_of(c) is current_from_log(c.id, log)
                   for c in cs2.values()),
               "every contract's projection agrees with its replayed history",
               "projection and log disagree")


# --------------------------------------------------------------------------- #
# Ratchet over the REAL store. Read-only.
# --------------------------------------------------------------------------- #
def t_ratchet() -> None:
    print("\n[ratchet -- the UNKNOWN population may only shrink]")
    pop = classify_population()
    _check("V-W3-RATCHET-POPULATION-FLOOR",
           pop["total"] >= 10,
           f"{pop['total']} contracts seen",
           f"only {pop['total']} contracts -- the sweep may have stopped "
           "seeing the store")

    try:
        baseline = json.loads(RATCHET.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        _fail("V-W3-RATCHET-BASELINE", f"no readable baseline at {RATCHET}")
        return

    known = set(baseline.get("unknown", []))
    now = set(pop["unknown"])
    added = sorted(now - known)
    removed = sorted(known - now)
    _check("V-W3-RATCHET-SHRINK-ONLY",
           not added,
           f"unknown={len(now)} (baseline {len(known)}), "
           f"resolved since: {removed or 'none'}",
           f"NEW unclassified capabilities: {added} -- a capability may not "
           "enter the store unclassified")
    _check("V-W3-RATCHET-NO-STALE-ENTRY",
           not [i for i in removed if i in known and i not in now
                and i not in {c.id for c in load_contracts()}],
           "no baseline entry names a capability that no longer exists",
           "the baseline outlived its subjects")


# --------------------------------------------------------------------------- #
# Instrument controls.
# --------------------------------------------------------------------------- #
def t_controls() -> None:
    print("\n[instrument controls]")
    # Gate 0 must be FIRST. A test that only checks the outcome cannot tell a
    # gate that runs first from one that happens to win today.
    src = (_PP_ROOT / "modules" / "capability_runtime"
           / "applicability.py").read_text(encoding="utf-8", errors="replace")
    body = src[src.index("def _evaluate("):]
    i_life = body.find("inheritable(c)")
    i_anti = body.find("c.anti_triggers")
    i_trig = body.find("_hits(text, c.triggers)")
    _check("V-W3-LIFE-CONTROL-GATE-IS-FIRST",
           0 < i_life < i_anti < i_trig,
           "the lifecycle gate precedes the anti-trigger and dormancy gates",
           f"gate order wrong: lifecycle@{i_life} anti@{i_anti} trig@{i_trig}")

    # Negative control: the harness can distinguish activation from silence.
    with tempfile.TemporaryDirectory() as td:
        cdir = _store(Path(td), _fixture(lifecycle="active"))
        _check("V-W3-LIFE-CONTROL-SELECTOR-CAN-SELECT",
               "zzyzx_audit" in _selected(cdir)["activate"],
               "the fixture IS selectable when active -- so a withheld result "
               "means withheld, not 'the selector never returns anything'",
               "the fixture is never selected; every revocation assertion "
               "above would pass vacuously")
        _check("V-W3-LIFE-CONTROL-IRRELEVANT-PROMPT",
               "zzyzx_audit" not in _selected(cdir, "unrelated chatter")["activate"],
               "an unrelated prompt does not select it -- relevance still works",
               "the fixture activates on anything; relevance is broken")


def main() -> int:
    print("V-W3-LIFE -- capability lifecycle, revocation and history")
    t_inheritance_and_revocation()
    t_bypass()
    t_history_and_supersession()
    t_suspended_is_not_revoked()
    t_unknown()
    t_conflict()
    t_migration()
    t_ratchet()
    t_controls()
    total = _PASS + _FAIL
    print(f"\nLIFECYCLE_PASS={_PASS}/{total}  failures={_FAIL}")
    if total < 28:
        print(f"HARNESS-FAILED: only {total} gates ran; this file defines more")
        return 2
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
