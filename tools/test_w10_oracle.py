"""UCR-CIF W10 -- gates for the owner-relevance oracle.

W4-W9 found a defect in the INSTRUMENT more often than in the subject, so
this suite tests the measuring device. Every negative assertion carries a
positive control: a gate that refuses everything passes every refusal test
and is indistinguishable from one that works.

The load-bearing gate is V-W10-SUPPRESSION-CANNOT-FLATTER. It drives the
exact defect W9's arm-dependent truth set concealed, in both worlds.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.ucr_cif import structural_projection as sp          # noqa: E402
from modules.ucr_cif.disposition_consumer import (                # noqa: E402
    MAX_OWNERS, load_ledger, select_for)
from modules.ucr_cif.owner_truth import (                         # noqa: E402
    MIN_OWNER_UNIVERSE, modality, owner_universe, rank_of,
    structural_share, truth_owners)
from tools.ucr_cif_oracle import (                                # noqa: E402
    _case_verdict, analyse, classify, divergence_ok, sign_test)

_P = _F = 0


def ok(gate: str, msg: str) -> None:
    global _P
    _P += 1
    print(f"  OK   {gate:<42} {msg}")


def fail(gate: str, msg: str) -> None:
    global _F
    _F += 1
    print(f"  FAIL {gate:<42} {msg}")


def check(gate: str, cond: bool, good: str, bad: str) -> None:
    ok(gate, good) if cond else fail(gate, bad)


# --------------------------------------------------------------------
# 1. The pre-cap field decides nothing
# --------------------------------------------------------------------
def gate_precap_decides_nothing() -> None:
    probes = [
        "add a governance overlay that audits capability activation and "
        "records mistakes in the knowledge vault",
        "create a duplicate detection engine that compares proposed systems "
        "against existing owners using semantic similarity scoring",
        "build a deep research pipeline with provenance and quality scoring",
    ]
    bad = []
    for p in probes:
        s = select_for(p)
        rendered = [o.owner for o in s.owners]
        if rendered != list(s.precap_owners)[:MAX_OWNERS]:
            bad.append(p[:40])
    check("V-W10-PRECAP-DECIDES-NOTHING", not bad,
          f"over {len(probes)} real proposals the rendered selection is "
          f"exactly precap[:{MAX_OWNERS}] -- the field reports, it never "
          f"reorders",
          f"rendered selection diverged from the capped pre-cap list: {bad}")

    # Positive control: the field is actually POPULATED, or the assertion
    # above is satisfied by two empty lists and proves nothing.
    s = select_for(probes[0])
    check("V-W10-PRECAP-IS-POPULATED", len(s.precap_owners) > 0,
          f"the control proposal routes {len(s.precap_owners)} pre-cap "
          f"owners, so the equality above was not two empty lists",
          "pre-cap list is empty -- the equality gate is vacuous")


def gate_precap_is_not_sliced_by_the_cap() -> None:
    """Live proof that `precap_owners` survives the cap.

    Truncating it to MAX_OWNERS would make pre-cap and post-cap identical
    and silently delete the rank/cap decomposition this wave rests on --
    while every fixture gate kept passing. `MAX_OWNERS` is read at call
    time, so lowering it in-process drives the real selector down a path
    where the two lists MUST differ.
    """
    import modules.ucr_cif.disposition_consumer as dc
    probe = ("design an institutional capability runtime with governance "
             "overlay auditing, duplicate detection across proposed "
             "systems, deep research provenance, knowledge acquisition "
             "indexing, liveness checks, decision review records and "
             "frontier intelligence scoring")
    original = dc.MAX_OWNERS
    try:
        dc.MAX_OWNERS = 2
        s = dc.select_for(probe)
        wide, narrow = len(s.precap_owners), len(s.owners)
    finally:
        dc.MAX_OWNERS = original
    check("V-W10-PRECAP-NOT-SLICED-BY-CAP",
          narrow == 2 and wide > 2,
          f"with the cap forced to 2 the selector renders {narrow} owners "
          f"while the pre-cap list still carries {wide} -- the ranking's "
          f"full verdict survives truncation, which is what makes an "
          f"eviction observable",
          f"pre-cap ({wide}) did not exceed the forced cap ({narrow}); the "
          f"list is being sliced and the decomposition is an illusion")
    check("V-W10-CAP-RESTORED", dc.MAX_OWNERS == original,
          f"the cap is restored to {original} after the probe, so no later "
          f"gate inherits a mutated constant",
          "the forced cap leaked out of the gate")


# --------------------------------------------------------------------
# 2. Truth is independent of the arm  (the W9 defect)
# --------------------------------------------------------------------
def gate_truth_arm_independent() -> None:
    universe = ("modules/alpha", "modules/beta", "modules/gamma")
    touched = {"modules/beta/x.py", "README.md"}

    a = truth_owners(touched, universe)
    b = truth_owners(touched, universe)
    check("V-W10-TRUTH-IS-ARM-INDEPENDENT",
          a == b == ("modules/beta",),
          "the truth set is a function of (touched paths, owner universe) "
          "only -- no routed list, rank or score is an input",
          f"truth set is not stable: {a} vs {b}")

    # Positive control: it CAN return something else.
    c = truth_owners({"modules/gamma/y.py"}, universe)
    check("V-W10-TRUTH-CONTROL", c == ("modules/gamma",),
          "different commits produce a different truth set, so the "
          "stability above is not a constant function",
          f"expected gamma, got {c}")


def gate_suppression_cannot_flatter() -> None:
    """The defect W9's instrument could not see.

    Control routes the true owner at rank 4. Treatment drops it entirely.
    Under an ARM-DEPENDENT truth set the case yields no owner hits and
    leaves the population -- so suppressing a true owner IMPROVES the
    apparent score. Under W10's truth set it is an eviction, i.e. a loss.
    """
    universe = ("modules/governance-overlay", "modules/other")
    touched = {"modules/governance-overlay/core.md"}
    truth = truth_owners(touched, universe)

    control = ["a", "b", "c", "d", "modules/governance-overlay"]
    treatment = ["a", "b", "c", "d", "e"]        # true owner pushed out

    owner = truth[0]
    move = classify(rank_of(owner, control), rank_of(owner, treatment))
    check("V-W10-SUPPRESSION-CANNOT-FLATTER", move == "evicted",
          "dropping the true owner scores as `evicted` -- a LOSS that stays "
          "in the denominator, not a case that vanishes from it",
          f"expected `evicted`, got `{move}`")

    # The red world, reproduced: this is what W7's label_case does, and
    # what W9 measured through. It must NOT be what W10 reports.
    arm_dependent = [o for o in treatment if o in truth]
    check("V-W10-ARM-DEPENDENT-TRUTH-LOSES-THE-CASE",
          arm_dependent == [],
          "reproduced: crediting only ROUTED owners yields zero hits here, "
          "so the arm-dependent design silently drops the very case that "
          "records the harm -- which is why the truth set moved",
          "the arm-dependent reproduction did not behave as recorded; the "
          "premise of this wave needs re-measuring")


# --------------------------------------------------------------------
# 3. Universe integrity
# --------------------------------------------------------------------
def gate_universe_floor() -> None:
    rows = [{"disposition": "EXTEND_EXISTING_OWNER",
             "proposed_owner": f"modules/m{i}"} for i in range(3)]
    try:
        owner_universe(rows)
        fail("V-W10-UNIVERSE-FLOOR",
             "a 3-owner universe was accepted; a truncated ledger read "
             "would silently shrink every truth set downstream")
    except RuntimeError as exc:
        check("V-W10-UNIVERSE-FLOOR", str(MIN_OWNER_UNIVERSE) in str(exc),
              f"a universe below the floor of {MIN_OWNER_UNIVERSE} raises "
              f"and names the floor, rather than returning a short list",
              f"raised without naming the floor: {exc}")

    meta, real = load_ledger()
    uni = owner_universe(real)
    check("V-W10-UNIVERSE-CONTROL", len(uni) >= MIN_OWNER_UNIVERSE,
          f"the real ledger yields {len(uni)} owners, so the floor gate is "
          f"not simply refusing everything",
          f"real ledger produced only {len(uni)} owners")


def gate_prefix_not_substring() -> None:
    universe = ("modules/code-review",)
    bad = truth_owners({"modules/code-reviewer/x.py"}, universe)
    check("V-W10-PREFIX-NOT-SUBSTRING", bad == (),
          "`modules/code-reviewer` does not credit `modules/code-review` -- "
          "the match is on a path separator, never a bare string prefix",
          f"substring collision credited a neighbour: {bad}")
    good = truth_owners({"modules/code-review/x.py"}, universe)
    check("V-W10-PREFIX-CONTROL", good == ("modules/code-review",),
          "the genuine child path still credits the owner, so the gate "
          "above is not refusing every match",
          f"the real child path was not credited: {good}")


# --------------------------------------------------------------------
# 4. Absence is not a rank
# --------------------------------------------------------------------
def gate_absence_is_not_rank() -> None:
    check("V-W10-ABSENT-IS-NONE", rank_of("x", ["a", "b"]) is None,
          "an absent owner ranks None, never a large integer that would "
          "average into a 'demotion'",
          "an absent owner returned a numeric rank")
    cases = {
        ("evicted", classify(2, None)),
        ("admitted", classify(None, 2)),
        ("absent_both", classify(None, None)),
        ("improved", classify(3, 1)),
        ("worsened", classify(1, 3)),
        ("unchanged", classify(2, 2)),
    }
    bad = [(want, got) for want, got in cases if want != got]
    check("V-W10-MOVE-CLASSES-DISTINCT", not bad,
          "all six movement classes are distinguishable, so an eviction "
          "can never be read as a demotion nor a miss as agreement",
          f"movement classes collapsed: {bad}")


# --------------------------------------------------------------------
# 5. Statistics
# --------------------------------------------------------------------
def gate_sign_test() -> None:
    check("V-W10-TIES-EXCLUDED", sign_test(0, 0) is None,
          "zero discordant pairs returns None, not p = 1.0 -- no evidence "
          "is not evidence of no effect",
          "a tie-only population produced a p-value")
    p = sign_test(6, 12)
    check("V-W10-REPRODUCES-W9-P", p is not None and abs(p - 0.238) < 0.002,
          f"W9's own 6/12 split re-derives as p = {p:.4f} against the "
          f"0.238 it reported -- the test is the one that produced the "
          f"number this wave inherited",
          f"6/12 gave {p}, which does not reproduce W9's 0.238")
    check("V-W10-STRONG-SPLIT-RESOLVES", sign_test(2, 30) < 0.001,
          "a decisive split resolves, so the test is not merely incapable "
          "of ever returning a small p",
          "a 2/30 split failed to resolve -- the test cannot detect")


def gate_clustering() -> None:
    one = _case_verdict(["improved", "improved", "improved"])
    check("V-W10-CLUSTER-ONE-CASE-ONE-VOTE", one == "improved",
          "three owner pairs from ONE prompt collapse to one observation, "
          "so a multi-owner case cannot manufacture power",
          f"expected one `improved` verdict, got {one}")
    check("V-W10-MIXED-IS-NOT-RESOLVED",
          _case_verdict(["improved", "worsened"]) == "mixed",
          "a case that both gained and lost is `mixed`, never resolved "
          "toward the convenient pole",
          "a mixed case was silently resolved")
    check("V-W10-CLUSTER-CONTROL",
          _case_verdict(["absent_both", "absent_both"]) == "absent_both",
          "a case whose true owners neither arm routed contributes nothing "
          "rather than counting as agreement",
          "an all-absent case was counted as an observation")


# --------------------------------------------------------------------
# 6. Modality
# --------------------------------------------------------------------
def gate_modality() -> None:
    meta, rows = load_ledger()
    proj = sp.load(corpus_id=(meta or {}).get("compiled_corpus_id"))
    shares = structural_share(rows, proj)

    gov = shares.get("modules/governance-overlay")
    check("V-W10-MODALITY-REPRODUCES-W9",
          gov is not None and abs(gov - 0.137) < 0.003,
          f"governance-overlay measures {100 * gov:.1f} % structural "
          f"against W9's independently recorded 13.7 % -- the modality "
          f"instrument measures the quantity W9 measured",
          f"governance-overlay measured {gov}, not W9's 0.137")
    check("V-W10-MODALITY-PROSE",
          modality("modules/governance-overlay", shares) == "prose",
          "the estate's known prose-form owner classifies as prose",
          "the known prose owner did not classify as prose")
    check("V-W10-MODALITY-CODE",
          modality("modules/capability_runtime", shares) == "code",
          "a symbol-rich module classifies as code, so the classifier is "
          "not labelling everything prose",
          "a code-form owner did not classify as code")

    dead = sp.Projection(status=sp.UNREADABLE, terms={})
    check("V-W10-MODALITY-NEEDS-PROJECTION",
          structural_share(rows, dead) == {}
          and modality("modules/governance-overlay", {}) == "unknown",
          "an unusable projection yields NO shares and `unknown` modality "
          "-- never a dict of zeros that would report every owner as prose",
          "an unusable projection produced shares or a prose verdict")


# --------------------------------------------------------------------
# 7. The store is canonical; the report is derived
# --------------------------------------------------------------------
def _mini_store(truth_owner: str, control, treatment) -> dict:
    return {
        "fingerprint": {
            "oracle_schema": "ucr-cif-oracle/1", "corpus_id": "x",
            "ledger_rows": 1, "owner_universe_n": 40,
            "owner_universe_sha": "a", "case_set_sha": "b", "cases": 1,
            "sessions_swept": 1, "window_hours": 24, "max_owners": 5},
        "arm_divergence": {"routed_cases": 1, "reordered": 1, "rate": 1.0,
                           "floor": 0.05, "ok": True},
        "structural_share": {truth_owner: 0.9},
        "cases": [{
            "prompt_sha": "p1", "session_sha": "s1", "date": "2026-09-22",
            "cwd_group_id": "g", "semantic_class": "create", "tier": 3,
            "length_bucket": "M", "status": "LABELLED",
            "truth_owners": [truth_owner],
            "control_precap": control, "control_routed": control[:5],
            "treatment_precap": treatment, "treatment_routed": treatment[:5],
            "gt_label_w7": "RELEVANT"}],
    }


def gate_execution_proof() -> None:
    """Two identical arms and a dead harness must never be one observable."""
    check("V-W10-DEAD-ARM-IS-A-FAILURE", not divergence_ok(0, 900),
          "900 routed cases with zero reordering is reported as a HARNESS "
          "FAILURE, not as a treatment that does nothing -- W9 measured "
          "76-79 % reordering, so silence means the arm did not run",
          "a completely inert treatment arm passed the execution proof")
    check("V-W10-LIVE-ARM-PASSES", divergence_ok(982, 1285),
          "the real run's 982/1285 = 76.4 % clears the floor, so the proof "
          "is not simply rejecting everything",
          "the real measured divergence failed its own floor")
    check("V-W10-EMPTY-POPULATION-IS-A-FAILURE", not divergence_ok(0, 0),
          "an empty routed population cannot certify that the treatment "
          "ran -- 0/0 is unmeasured, never proof",
          "an empty population was accepted as an execution proof")


def gate_precap_reaches_past_the_cap() -> None:
    """The decomposition must be reachable in PRODUCTION, not just fixtures.

    A mutation that truncated `precap_owners` to MAX_OWNERS would make
    pre-cap and post-cap identical, silently deleting the rank/cap
    decomposition -- and every fixture-based gate above would still pass.
    Only real data can catch it, so this gate reads the canonical store.
    """
    store_path = PP_ROOT / "vault" / "ucr_cif" / "oracle_cases.json"
    if not store_path.exists():
        fail("V-W10-PRECAP-EXCEEDS-CAP-IN-PRODUCTION",
             f"canonical store absent at {store_path} -- the production "
             f"reachability of the decomposition is UNMEASURED, which is "
             f"not the same as satisfied")
        return
    store = json.loads(store_path.read_text(encoding="utf-8"))
    deep = [c for c in store["cases"]
            if len(c.get("control_precap") or ()) > MAX_OWNERS]
    check("V-W10-PRECAP-EXCEEDS-CAP-IN-PRODUCTION", bool(deep),
          f"{len(deep)} of {len(store['cases'])} real cases rank MORE than "
          f"{MAX_OWNERS} owners, so the cap genuinely bites and the pre-cap "
          f"list is not a truncated copy of the rendered one",
          f"no real case exceeds the cap -- either the cap never bites or "
          f"precap_owners is being truncated, and the decomposition this "
          f"wave rests on would be an illusion either way")

    evicted = [c for c in store["cases"]
               if c["status"] == "LABELLED"
               and any(rank_of(o, c["control_routed"]) is not None
                       and rank_of(o, c["treatment_routed"]) is None
                       for o in c["truth_owners"])]
    check("V-W10-EVICTION-OBSERVED-IN-PRODUCTION", bool(evicted),
          f"{len(evicted)} real labelled cases lose a TRUE owner to the cap "
          f"under treatment -- the harm W9 could only theorise is measured, "
          f"with named prompts behind it",
          "no real eviction was observed; the cap claim would rest on a "
          "fixture alone, which is what W9's failed gate already did")


def gate_store_is_canonical() -> None:
    owner = "modules/alpha"
    worse = _mini_store(owner, [owner, "b"], ["b", owner])
    better = _mini_store(owner, ["b", owner], [owner, "b"])

    rw = analyse(worse)["pre_cap"]
    rb = analyse(better)["pre_cap"]
    check("V-W10-REPORT-DERIVES-FROM-STORE",
          rw["worsened_incl_evicted"] == 1 and rb["improved_incl_admitted"] == 1,
          "changing a case in the canonical store changes the derived "
          "report -- the report is a projection, never the oracle",
          f"the report did not follow the store: {rw} / {rb}")

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "s.json"
        p.write_text(json.dumps(worse), encoding="utf-8")
        again = analyse(json.loads(p.read_text(encoding="utf-8")))["pre_cap"]
        check("V-W10-STORE-ROUNDTRIPS",
              again["worsened_incl_evicted"] == 1,
              "the store round-trips through disk unchanged, so a later "
              "session recomputes the same report from the same cases",
              "the store did not round-trip")


def gate_cap_decomposition() -> None:
    """Rank and cap are two effects, and the fixture must CROSS the cap.

    W9's fixture carried three owners against a cap of five and was
    therefore structurally unable to observe an eviction. This one has
    seven.
    """
    owner = "modules/alpha"
    control = [owner] + [f"f{i}" for i in range(6)]          # rank 0
    treatment = [f"f{i}" for i in range(6)] + [owner]        # rank 6
    store = _mini_store(owner, control, treatment)
    rep = analyse(store)

    pre = rep["pre_cap"]["moves"]
    post = rep["post_cap"]["moves"]
    check("V-W10-CAP-FIXTURE-CROSSES-THE-BOUNDARY",
          len(control) > MAX_OWNERS,
          f"the fixture carries {len(control)} owners against a cap of "
          f"{MAX_OWNERS}, so eviction is expressible at all",
          "the fixture cannot reach the cap -- W9's defect repeated")
    check("V-W10-RANK-AND-CAP-SEPARATE",
          pre["worsened"] == 1 and post["evicted"] == 1,
          "one movement reports as a pre-cap DEMOTION and a post-cap "
          "EVICTION -- the two effects are apportioned rather than summed "
          "into one number, which is what W9 could not do",
          f"decomposition collapsed: pre={pre} post={post}")


def main() -> int:
    print("== W10 OWNER-RELEVANCE ORACLE GATES ==")
    gate_precap_decides_nothing()
    gate_precap_is_not_sliced_by_the_cap()
    gate_truth_arm_independent()
    gate_suppression_cannot_flatter()
    gate_universe_floor()
    gate_prefix_not_substring()
    gate_absence_is_not_rank()
    gate_sign_test()
    gate_clustering()
    gate_modality()
    gate_execution_proof()
    gate_precap_reaches_past_the_cap()
    gate_store_is_canonical()
    gate_cap_decomposition()
    total = _P + _F
    print(f"\nW10_ORACLE_PASS={_P}/{total}  threshold={total}/{total}")
    return 0 if _F == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
