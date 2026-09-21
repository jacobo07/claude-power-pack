#!/usr/bin/env python3
"""V-SA-* gates for modules/surface_architecture.

    python tools/test_surface_architecture.py

Every gate drives a branch that can come back the other way. A gate whose predicate
cannot fail is decoration, so each one below has a paired control or an input that
would flip it.

Run from the repo root.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.surface_architecture import archetypes as A          # noqa: E402
from modules.surface_architecture import boundaries as B          # noqa: E402
from modules.surface_architecture import resolver as R            # noqa: E402
from modules.surface_architecture.context import SurfaceContext   # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}  {diagnostic}")


def _check(gate: str, cond: bool, evidence: str, diagnostic: str = "") -> None:
    _ok(gate, evidence) if cond else _fail(gate, diagnostic or evidence)


# --------------------------------------------------------------- fixtures

def _complete(**over) -> SurfaceContext:
    """A context with every material fact measured. Overrides layer on top."""
    base = dict(
        product_kind="tool", primary_intent="do the thing",
        first_meaningful_value="a result",
        value_before_identity_possible=True, identity_driver="persistence",
        returning_parties_exist=True, work_possible_before_identity=True,
        work_survives_interruption=True, regulated=False, assurance_required=False,
        sensitive_data=False, external_consequences=False, payment_before_value=False,
        abuse_risk="low", tenancy="individual", invitation_based=False,
        artifacts_available=[], integrations_available=[])
    base.update(over)
    return SurfaceContext(**base)


# --------------------------------------------------------------- gates

def gate_absence_is_not_a_default() -> None:
    """An unmeasured fact must not resolve to a value."""
    d = R.resolve(SurfaceContext())
    _check("V-SA-ABSENCE-NOT-DEFAULT",
           d.outcome == R.UNDETERMINED
           and d.reason_code == R.MISSING_MATERIAL_FACTS
           and set(d.missing_facts) == set(SurfaceContext().missing_material_facts()),
           f"empty context -> {d.outcome}/{d.reason_code}, {len(d.missing_facts)} named",
           f"expected UNDETERMINED/MISSING_MATERIAL_FACTS, got {d.outcome}/{d.reason_code}")

    # CONTROL: the same predicate must NOT fire when everything is measured.
    c = R.resolve(_complete())
    _check("V-SA-ABSENCE-CONTROL", c.reason_code != R.MISSING_MATERIAL_FACTS,
           f"complete context -> {c.outcome}/{c.reason_code or '-'} (not a missing-facts refusal)",
           "a fully measured context still reported missing facts")


def gate_invalid_is_not_absent() -> None:
    """Measured-but-wrong and never-measured are different states.

    Regression: the first smoke run rendered an invalid value under the
    'nobody looked' label, which is the conflation this module exists to prevent.
    """
    d = R.resolve(_complete(identity_driver="vibes"))
    _check("V-SA-INVALID-NOT-ABSENT",
           d.outcome == R.UNDETERMINED
           and d.reason_code == R.INVALID_CONTEXT_VALUES
           and d.invalid_values and not d.missing_facts,
           f"invalid value -> {d.reason_code}, invalid={d.invalid_values}, missing={d.missing_facts}",
           f"invalid value leaked into missing_facts={d.missing_facts}")

    rendered = d.render()
    _check("V-SA-INVALID-RENDER",
           "INVALID" in rendered and "nobody looked" not in rendered,
           "render labels it INVALID and never says 'nobody looked'",
           f"render conflates the two states: {rendered!r}")


def gate_three_valued_conditions() -> None:
    """A condition over an unmeasured field is UNKNOWN, never False."""
    arch = A.BY_ID["INTEGRATION_FIRST"]
    v_unknown, _ = A.evaluate(arch, SurfaceContext())
    v_no, _ = A.evaluate(arch, _complete(integrations_available=[]))
    v_yes, _ = A.evaluate(arch, _complete(integrations_available=["a source"]))
    _check("V-SA-THREE-VALUED",
           v_unknown == A.UNKNOWN and v_no == A.NO and v_yes == A.YES,
           f"unmeasured={v_unknown} measured-empty={v_no} measured-present={v_yes}",
           f"expected UNKNOWN/NO/YES, got {v_unknown}/{v_no}/{v_yes}")


def gate_four_outcomes_are_reachable() -> None:
    """All four outcomes must be produced by a real context, with distinct exits."""
    seen = {}
    seen[R.resolve(SurfaceContext()).outcome] = R.resolve(SurfaceContext()).exit_code
    rec = R.resolve(_complete())
    seen[rec.outcome] = rec.exit_code
    esc = R.resolve(_complete(regulated=True, work_possible_before_identity=False,
                              value_before_identity_possible=False,
                              identity_driver="regulation"))
    seen[esc.outcome] = esc.exit_code
    # ABSTAIN is reachable only when every SPECIFIC archetype is disqualified by a
    # measured fact and only the zero-requirement residual survives. Nothing is left
    # unmeasured here, so the refusal is about the product, not about the measurement.
    residual = R.resolve(_complete(
        primary_intent=None, identity_driver="none",
        value_before_identity_possible=False, work_possible_before_identity=False,
        work_survives_interruption=False, returning_parties_exist=False,
        invitation_based=False, artifacts_available=[], integrations_available=[]))
    seen[residual.outcome] = residual.exit_code
    _check("V-SA-RESIDUAL-ABSTAINS",
           residual.outcome == R.ABSTAIN
           and residual.reason_code == R.NO_ARCHETYPE_JUSTIFIED,
           f"residual-only context -> {residual.outcome}/{residual.reason_code}, "
           f"fallback={residual.fallback}",
           f"expected ABSTAIN when only the residual survives, got "
           f"{residual.outcome}/{residual.reason_code} "
           f"archetypes={residual.archetypes}")

    _check("V-SA-FOUR-OUTCOMES", len(seen) == 4,
           f"reached {sorted(seen)} with exits {sorted(seen.values())}",
           f"only reached {sorted(seen)} -- an unreachable outcome is not an outcome")
    _check("V-SA-EXIT-CODES-DISJOINT", len(set(seen.values())) == len(seen),
           f"exit codes distinct: {sorted(seen.values())}",
           f"two outcomes share an exit code: {seen}")
    _check("V-SA-EXIT-VOCABULARY",
           R.EXIT[R.RECOMMEND] == 0 and R.EXIT[R.ABSTAIN] == 20
           and R.EXIT[R.REQUIRE_APPROVAL] == 21 and R.EXIT[R.UNDETERMINED] == 22,
           "0/20/21 match cdicf/selector.js; 22 is the added fourth",
           f"exit vocabulary drifted from CDICF: {R.EXIT}")


def gate_identity_conflict_is_named() -> None:
    """Earliest-justified after latest-safe has no valid position. Say so."""
    ctx = _complete(identity_driver="external_effect",
                    work_survives_interruption=False)
    p = B.identity_boundary(ctx)
    _check("V-SA-BOUNDARY-CONFLICT", p.status == B.CONFLICT,
           f"earliest=effect latest=work -> {p.status}",
           f"a contradictory pair was given a position anyway: {p.status}/{p.position}")

    d = R.resolve(ctx)
    _check("V-SA-CONFLICT-ESCALATES",
           d.outcome == R.REQUIRE_APPROVAL and d.reason_code == R.BOUNDARY_CONFLICT,
           f"resolver escalates: {d.outcome}/{d.reason_code}",
           f"a contradiction did not reach a human: {d.outcome}/{d.reason_code}")

    # CONTROL: relax the one fact and the conflict must disappear.
    ok = B.identity_boundary(_complete(identity_driver="external_effect",
                                       work_survives_interruption=True))
    _check("V-SA-CONFLICT-CONTROL", ok.status == B.PLACED,
           f"work that survives -> {ok.status} at {ok.position}",
           "the conflict predicate fires even when the constraints are satisfiable")


def gate_cited_ids_resolve() -> None:
    """Every archetype id a Decision names must exist in the registry.

    Covers rejected and fallback, not just the winner -- an invented id hides there
    and every unit test stays green.
    """
    contexts = [SurfaceContext(), _complete(),
                _complete(regulated=True, identity_driver="regulation",
                          value_before_identity_possible=False,
                          work_possible_before_identity=False),
                _complete(artifacts_available=["a document"]),
                _complete(integrations_available=["a source"]),
                _complete(invitation_based=True)]
    bad = []
    total = 0
    for ctx in contexts:
        for cid in R.resolve(ctx).cited_archetype_ids():
            total += 1
            if cid not in A.BY_ID:
                bad.append(cid)
    _check("V-SA-CITED-IDS-RESOLVE", not bad and total > 0,
           f"{total} cited id(s) across {len(contexts)} contexts, all resolve",
           f"decision cited unknown archetype id(s): {sorted(set(bad))}")


def gate_registry_is_consistent() -> None:
    """Ids unique; every declared fallback resolves; operators are known."""
    ids = [a.id for a in A.REGISTRY]
    _check("V-SA-IDS-UNIQUE", len(ids) == len(set(ids)),
           f"{len(ids)} archetypes, ids unique",
           f"duplicate archetype id: {sorted({i for i in ids if ids.count(i) > 1})}")

    orphan = [a.id for a in A.REGISTRY if a.fallback and a.fallback not in A.BY_ID]
    _check("V-SA-FALLBACKS-RESOLVE", not orphan,
           "every declared fallback names a registered archetype",
           f"fallback points at an id that does not exist: {orphan}")

    unknown_ops = sorted({c[1] for a in A.REGISTRY
                          for c in tuple(a.requires) + tuple(a.disqualifiers)
                          if c[1] not in A._OPS})
    _check("V-SA-OPERATORS-KNOWN", not unknown_ops,
           f"all conditions use the {len(A._OPS)} declared operators",
           f"registry uses an operator the evaluator does not implement: {unknown_ops}")

    unknown_fields = sorted({c[0] for a in A.REGISTRY
                             for c in tuple(a.requires) + tuple(a.disqualifiers)
                             if not hasattr(SurfaceContext(), c[0])})
    _check("V-SA-FIELDS-EXIST", not unknown_fields,
           "every condition names a real SurfaceContext field",
           f"registry conditions over fields that do not exist: {unknown_fields}")


def gate_kernel_is_domain_blind() -> None:
    """No domain noun may appear in the kernel package.

    `contaminates_kernel` matches by SUBSTRING (specialization.py:173-178, no \\b
    anchor, unlike applicability._hits). So a domain word here would make the first
    vertical's derivative uncompilable. This gate is the pre-check.
    """
    banned = ("signup", "sign-up", "onboarding", "onboard", "login", "log-in",
              "trial", "guest account", "e-mail address")
    pkg = _PP_ROOT / "modules" / "surface_architecture"
    hits = []
    for src in sorted(pkg.glob("*.py")):
        low = src.read_text(encoding="utf-8-sig").lower()
        hits += [(src.name, w) for w in banned if w in low]
    _check("V-SA-KERNEL-DOMAIN-BLIND", not hits,
           f"{len(list(pkg.glob('*.py')))} kernel file(s) carry no domain noun",
           f"domain vocabulary in the kernel: {hits}")

    # POSITIVE CONTROL: the detector must be able to find something.
    _check("V-SA-DOMAIN-DETECTOR-LIVE",
           any(w in "a signup surface for onboarding" for w in banned),
           "the banned-word detector fires on a known-contaminated string",
           "the detector cannot detect -- a clean result proves nothing")


def gate_no_store_is_created() -> None:
    """DS13: applicability decisions are returned to the caller, never persisted.

    Resolving must not create anything under vault/.
    """
    vault = _PP_ROOT / "vault"
    before = {p for p in vault.rglob("*") if "surface_architecture" in p.name.lower()}
    for _ in range(3):
        R.resolve(_complete())
        R.resolve(SurfaceContext())
    after = {p for p in vault.rglob("*") if "surface_architecture" in p.name.lower()}
    _check("V-SA-NO-STORE", before == after,
           f"{len(after)} surface-architecture path(s) under vault/, unchanged by resolving",
           f"resolving created persistence DS13 forbids: {sorted(after - before)}")


def gate_contract_activates() -> None:
    """A registered contract that no mission reaches is a file, not a capability.

    `validate()` proves the JSON is well-formed. It says nothing about whether any
    mission text reaches the capability -- gate 1.5 returns NOT_APPLICABLE the moment
    no trigger matches, and relevance divides by the trigger count. So assert the
    stack, with a control that must come back the other way.
    """
    from modules.capability_runtime.applicability import (  # noqa: PLC0415
        MissionContext, compile_stack,
    )
    from modules.capability_runtime.contract import (  # noqa: PLC0415
        CONTRACTS_DIR, load_contracts,
    )

    cid = "surface_architecture"
    on_disk = {c.id for c in load_contracts()}
    _check("V-SA-CONTRACT-LOADS", cid in on_disk,
           f"{len(on_disk)} contract(s) load; {cid} among them",
           f"{cid} is absent or failed validation on read; seed it with "
           f"tools/seed_surface_architecture_contract.py (dir={CONTRACTS_DIR})")
    if cid not in on_disk:
        return

    live = compile_stack(MissionContext(
        description="design the entry surface and first-run for a new product"))
    _check("V-SA-CONTRACT-ACTIVATES", cid in live["activate"],
           f"real mission -> activate={live['activate']}",
           f"contract exists but no mission reaches it: activate={live['activate']}, "
           f"dormant={live['dormant']}, blocked={live['blocked']}")

    # CONTROL, and it must fail for the RIGHT reason: an unrelated mission leaves it
    # dormant or unlisted, never BLOCKED. A blocked verdict would mean "wanted here
    # and cannot run", which is a different and wrong statement.
    off = compile_stack(MissionContext(description="fix a typo in a single file"))
    _check("V-SA-CONTRACT-CONTROL",
           cid not in off["activate"] and cid not in off["blocked"],
           f"unrelated mission -> not activated, not blocked "
           f"(activate={off['activate']}, blocked={list(off['blocked'])})",
           f"the contract activates on an unrelated mission, or reports BLOCKED "
           f"where the truth is irrelevance: {off}")


def gate_vertical_specialization() -> None:
    """The signup vertical must be a real specialization, not a rename."""
    from modules.capability_runtime.contract import load_contracts  # noqa: PLC0415
    from modules.surface_architecture.verticals import signup      # noqa: PLC0415

    parents = {c.id: c for c in load_contracts()}
    parent = parents.get("surface_architecture")
    if parent is None:
        _fail("V-SA-VERTICAL-PARENT", "kernel contract absent; seed it first")
        return

    sp = signup._load_specialization()
    spec = signup.build_spec(parent.non_scope)
    report = sp.audit(spec, parent.to_dict())

    _check("V-SA-VERTICAL-DEPTH",
           report["depth"] >= 2 and not report["name_level_only"],
           f"depth={report['depth']}/6 components={report['populated_components']}",
           f"HR-APA-016: depth {report['depth']} is a rename, not a specialization")
    _check("V-SA-VERTICAL-COMPILES", report["compiles"],
           "the six components compile into contract overrides",
           f"compile refused: {report['reason']}")
    _check("V-SA-VERTICAL-NO-CONTAMINATION", not report["kernel_contamination"],
           "no domain vocabulary reaches a kernel field",
           f"HR-APA-017: {report['kernel_contamination']}")

    # POSITIVE CONTROL. contaminates_kernel is fail-open -- hand it the wrong object
    # and `not isinstance(kernel_fields, dict)` returns [], i.e. CLEAN. So the empty
    # result above means nothing until the detector is shown to still fire.
    probe = signup.build_spec(parent.non_scope)
    probe.domain_pack.vocabulary = dict(probe.domain_pack.vocabulary)
    probe.domain_pack.vocabulary["probe"] = "boundary placement"
    fired = sp.contaminates_kernel(probe, parent.to_dict())
    _check("V-SA-CONTAMINATION-DETECTOR-LIVE", bool(fired),
           f"detector fires on a contaminated spec ({len(fired)} field(s))",
           "the detector found nothing in a contaminated spec -- a clean result "
           "from it proves nothing")

    # REGRESSION. The first real seed failed here: two of the parent's non_scope
    # entries had been paraphrased, and HR-APA-017 compares by value, so a reworded
    # boundary reads as a dropped one.
    child_non_scope = set(spec.domain_pack.non_scope)
    dropped = [e for e in parent.non_scope if e not in child_non_scope]
    _check("V-SA-VERTICAL-INHERITS-BOUNDARIES", not dropped,
           f"all {len(parent.non_scope)} inherited boundaries present verbatim",
           f"paraphrased or dropped inherited boundary: {dropped}")


def gate_derivative_stays_out_of_contracts() -> None:
    """A derivative in contracts/ would be scored against every unrelated mission."""
    from modules.capability_runtime.contract import (  # noqa: PLC0415
        CONTRACTS_DIR, load_contracts,
    )
    from modules.capability_runtime.derivatives import (  # noqa: PLC0415
        DERIVATIVES_DIR,
    )

    with_parent = [c.id for c in load_contracts() if c.parent]
    _check("V-SA-NO-DERIVATIVE-IN-CONTRACTS", not with_parent,
           f"{len(list(CONTRACTS_DIR.glob('*.json')))} contract(s), none with a parent",
           f"a derivative is registered as a kernel contract and will be scored "
           f"against every mission: {with_parent}")

    at_named = [p.name for p in CONTRACTS_DIR.glob("*.json") if "_at_" in p.name]
    _check("V-SA-DERIVATIVE-SINK",
           not at_named and DERIVATIVES_DIR.exists(),
           f"derivatives live in {DERIVATIVES_DIR.name}/ "
           f"({len(list(DERIVATIVES_DIR.glob('*.json')))} record(s))",
           f"derivative-shaped file in contracts/: {at_named}" if at_named
           else "derivatives/ does not exist; nothing was ever cut")


def gate_contrasting_fixtures() -> None:
    """Six contrasting scenarios. A resolver that encoded one flow family would give
    most of them the same answer, so the spread IS the falsification.

    Each fixture declares its expected outcome AND archetype, asserted together. A
    fixture that only checked the outcome would pass while the resolver named the
    wrong topology.
    """
    import json  # noqa: PLC0415

    from modules.surface_architecture.context import from_dict  # noqa: PLC0415

    path = _PP_ROOT / "fixtures" / "surface_architecture" / "scenarios.json"
    if not path.is_file():
        _fail("V-SA-FIXTURES-PRESENT", f"missing {path}")
        return
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cases = {k: v for k, v in data.items() if not k.startswith("_")}
    _check("V-SA-FIXTURES-PRESENT", len(cases) >= 6,
           f"{len(cases)} contrasting scenarios loaded",
           f"only {len(cases)} scenarios -- too few to falsify a single-family resolver")

    outcomes, archetypes, wrong = [], [], []
    for name, case in sorted(cases.items()):
        d = R.resolve(from_dict(case["context"]))
        outcomes.append(d.outcome)
        archetypes.append(d.archetype or None)
        want_o, want_a = case["expect_outcome"], case.get("expect_archetype")
        # Membership, not equality. The answer is a SET: several topologies can be
        # justified at once and a real surface is frequently more than one of them.
        # Requiring equality with a single leader would fail every honest composite.
        got_a = list(d.archetypes)
        archetypes.extend(got_a)
        ok_a = (want_a is None) or (want_a in got_a)
        if d.outcome != want_o or not ok_a:
            wrong.append(f"{name}: expected {want_o} with {want_a}, "
                         f"got {d.outcome} with {got_a or None} "
                         f"[{d.reason_code or '-'}]")

    _check("V-SA-FIXTURES-MATCH", not wrong,
           f"all {len(cases)} scenarios produced their declared outcome, and every "
           "declared archetype appears in the justified set",
           "; ".join(wrong))

    named = {a for a in archetypes if a}
    _check("V-SA-FIXTURES-DISCRIMINATE", len(named) >= 3 and len(set(outcomes)) >= 3,
           f"{len(named)} distinct archetype(s) across {len(set(outcomes))} outcome(s): "
           f"{sorted(named)}",
           f"the set does not discriminate: archetypes={sorted(named)}, "
           f"outcomes={sorted(set(outcomes))} -- one flow family would pass this")

    # The refusal case must exist and must name its gap, or the set only proves the
    # resolver can say yes.
    refusals = [n for n, c in cases.items() if c.get("expect_archetype") is None]
    _check("V-SA-FIXTURES-INCLUDE-REFUSAL", len(refusals) >= 2,
           f"{len(refusals)} scenario(s) require the resolver to name NO archetype",
           "no fixture requires a refusal -- the set only proves it can say yes")


def gate_dataset_drift() -> None:
    """The dataset part and the executable registry must not drift apart.

    A rename in one that is not made in the other would leave a document describing
    archetypes that no longer exist, which reads exactly like a document describing
    ones that do.
    """
    import re  # noqa: PLC0415

    doc = _PP_ROOT / "vault" / "knowledge_base" / "uacf" / "UACF-01-surface-architecture.md"
    if not doc.is_file():
        _fail("V-SA-DATASET-PRESENT", f"missing {doc}")
        return
    text = doc.read_text(encoding="utf-8-sig")

    # Ids are cited in backticks in the archetype table.
    cited = set(re.findall(r"`([A-Z][A-Z_]{3,})`", text))
    registry = set(A.IDS)
    missing = sorted(registry - cited)
    invented = sorted(c for c in cited - registry
                      if c not in {"RECOMMEND", "ABSTAIN", "REQUIRE_APPROVAL",
                                   "UNDETERMINED", "CONFLICT"})
    _check("V-SA-DATASET-DRIFT", not missing and not invented,
           f"all {len(registry)} registry ids appear in the dataset, and it invents none",
           f"missing from dataset: {missing}; in dataset but not the registry: {invented}")

    # The ordering principle belongs to CDIO-02. The dataset must CITE it, not restate
    # it -- two places a rule can be written is one place it can drift.
    _check("V-SA-DATASET-CITES-CDIO", "CDIO-02" in text,
           "the dataset cites CDIO-02 for the ordering principle rather than "
           "restating it",
           "the dataset does not cite CDIO-02; the value-before-friction rule now has "
           "two owners")


def main() -> int:
    print("V-SA gates -- modules/surface_architecture")
    gate_dataset_drift()
    gate_contrasting_fixtures()
    gate_contract_activates()
    gate_absence_is_not_a_default()
    gate_invalid_is_not_absent()
    gate_three_valued_conditions()
    gate_four_outcomes_are_reachable()
    gate_identity_conflict_is_named()
    gate_cited_ids_resolve()
    gate_registry_is_consistent()
    gate_kernel_is_domain_blind()
    gate_no_store_is_created()
    gate_vertical_specialization()
    gate_derivative_stays_out_of_contracts()
    total = _passes + _fails
    print(f"SURFACE_ARCHITECTURE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
