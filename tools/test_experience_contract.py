#!/usr/bin/env python3
"""Done-gate for the CDIO-07 experience contract (V-EXP-*).

The axis must be OBSERVED REFUSING IN BOTH DIRECTIONS. A behavioural gate that has
only ever been seen asking for MORE feedback is a preference with a schema, so this
suite proves both poles: a silent action fails, and a cue that flashes below the
perception floor fails too.

Three properties matter more than the individual checks and are pinned here:

  ABSTENTION      `expressiveness: none` is a complete, PASSING contract. A suite
                  that could not express that would keep proposing animation to
                  interfaces whose users want speed and nothing else.
  UNASSESSED      a project with no contract is reported, never failed, and its
                  score is byte-identical to what it was before this axis existed.
  SEPARATION      contract compliance never moves the Design Quality Score. A
                  criterion that silently re-scores last month's surfaces is a
                  regression wearing a gate's clothes.

Run:  python tools/test_experience_contract.py
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cdio.scorer import (  # noqa: E402
    EXP_BREACHED,
    EXP_CONFORMING,
    EXP_UNASSESSED,
    Verdict,
    check_blocking_animation,
    check_experience_contract,
    check_feedback_ack,
    check_motion_sole_channel,
    check_progress_cue,
    check_reduced_motion,
    review_gate,
    score_review,
)
from tools.design_gate import (  # noqa: E402
    check_experience_coherence,
    design_gate,
    emit_context,
    main as gate_main,
    parse_design_md,
)

REPO_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "modules", "design-md", "DESIGN.md.template",
)

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


# An internal operations console. The correct amount of expressive behaviour here is
# zero, and the suite must be able to say so without recording a single finding.
ADMIN_CRUD = """---
name: OpsConsole
aesthetic_family: F4
experience:
  expressiveness: none
  motion_budget: none
  reduced_motion: equivalent
  feedback_latency_ms: 100
  progress_threshold_ms: 1000
  waiting: spinner
  progress_language: indeterminate
  success_posture: silent
  error_posture: terse
  celebration_policy: never
  character_policy: none
  trust_posture: elevated
colors:
  accent: "#faff69"
  neutral: "#181818"
typography:
  body-md:
    fontFamily: Inter
---
A batch operations console. Still by intent.
"""

# Declared with no contract at all: the state every project in the repo is in today.
NO_CONTRACT = """---
name: LegacyProject
aesthetic_family: F1
colors:
  accent: "#5e6ad2"
  neutral: "#ffffff"
typography:
  body-md:
    fontFamily: Inter
---
No experience block. Unassessed, not failing.
"""

# A contract that cannot be conformed to: the ceiling requires motion, and the
# declaration removes the equivalent that motion is only permitted to exist with.
INCOHERENT = """---
name: BrokenContract
aesthetic_family: F5
experience:
  expressiveness: high
  motion_budget: high
  reduced_motion: absent
  celebration_policy: never
  trust_posture: standard
colors:
  accent: "#c96442"
  neutral: "#181818"
typography:
  body-md:
    fontFamily: Lora
---
Refused at declaration time.
"""


def gate_floors_refuse() -> None:
    """Every floor check must be observed FAILING, with the severity the doctrine
    assigns. A check nobody can fail is not a check."""
    silent = check_feedback_ack(None)
    slow_costly = check_feedback_ack(400, costly=True)
    frozen = check_progress_cue(3000, has_cue=False)
    no_reduced = check_reduced_motion(motion_present=True, reduced_equivalent=False)
    sole = check_motion_sole_channel(["motion"])
    blocking = check_blocking_animation(600)

    checks = {
        "silent-action": (silent, "fail", "minor"),
        "slow-ack-costly": (slow_costly, "fail", "major"),
        "no-progress-cue": (frozen, "fail", "major"),
        "no-reduced-motion": (no_reduced, "fail", "critical"),
        "motion-sole-channel": (sole, "fail", "critical"),
        "blocking-animation": (blocking, "fail", "critical"),
    }
    wrong = {k: (v.status, v.severity) for k, (v, st, sev) in checks.items()
             if v.status != st or v.severity != sev}
    unmeasured = [k for k, (v, _, _) in checks.items() if not v.observed.strip()]
    if wrong or unmeasured:
        _fail("V-EXP-FLOORS-REFUSE",
              f"wrong severity/status: {wrong}; no observed value: {unmeasured}")
    else:
        _ok("V-EXP-FLOORS-REFUSE",
            "6 floor failures, correct severities, every one carrying an observed value")


def gate_floors_pass() -> None:
    """Both poles reachable: conformant behaviour records zero findings."""
    results = [
        check_feedback_ack(40),
        check_progress_cue(3000, has_cue=True),
        check_progress_cue(50, has_cue=False),
        check_reduced_motion(motion_present=True, reduced_equivalent=True),
        check_reduced_motion(motion_present=False, reduced_equivalent=False),
        check_motion_sole_channel(["motion", "text"]),
        check_motion_sole_channel([]),
        check_blocking_animation(0),
    ]
    bad = [r.criterion for r in results if r.status != "pass"]
    if bad:
        _fail("V-EXP-FLOORS-PASS", f"conformant input recorded findings: {bad}")
    else:
        _ok("V-EXP-FLOORS-PASS",
            f"{len(results)} conformant observations -> zero findings")


def gate_bidirectional() -> None:
    """The thesis of the axis: over-delivery is refusable, not only under-delivery."""
    absent = check_progress_cue(3000, has_cue=False)
    flash = check_progress_cue(80, has_cue=True)
    if absent.status == "fail" and flash.status == "fail" \
            and "no progress cue" in absent.observed \
            and "perception floor" in flash.observed:
        _ok("V-EXP-BIDIRECTIONAL",
            "an absent cue past the threshold AND a cue flashing below the floor "
            "both fail -- the axis can refuse expression, not only its absence")
    else:
        _fail("V-EXP-BIDIRECTIONAL",
              f"absent={absent.status}/{absent.observed!r} "
              f"flash={flash.status}/{flash.observed!r}")


def gate_abstention(tmp: str) -> None:
    """`expressiveness: none` is a passing contract, not an unfinished one."""
    path = _write(tmp, "ADMIN.md", ADMIN_CRUD)
    out = design_gate(path)
    coherence = next((f for f in out.get("passed", [])
                      if f["criterion"] == "experience-contract-coherent"), None)
    findings = len(out.get("critical", [])) + len(out.get("major", [])) \
        + len(out.get("minor", []))
    if out["verdict"] == "APPROVE" and coherence and findings == 0 \
            and out["experience_state"] == "declared":
        _ok("V-EXP-ABSTENTION",
            f"admin console declaring expressiveness=none -> APPROVE score="
            f"{out['score']}, zero findings")
    else:
        _fail("V-EXP-ABSTENTION",
              f"a still interface that declared stillness must pass; got "
              f"{out['verdict']} score={out['score']} findings={findings} "
              f"coherence={'present' if coherence else 'absent'}")


def gate_unassessed(tmp: str) -> None:
    """A project with no contract is reported, never failed -- and its score is
    byte-identical to what it was before this axis existed."""
    path = _write(tmp, "LEGACY.md", NO_CONTRACT)
    parsed = parse_design_md(path)
    coherence = check_experience_coherence(parsed["experience"])
    out = design_gate(path)
    criteria = {f["criterion"] for f in out.get("passed", [])}
    hf = check_experience_contract(None, None)

    appended_nothing = "experience-contract-coherent" not in criteria
    if parsed["experience"] is None and coherence is None and appended_nothing \
            and out["verdict"] == "APPROVE" and out["score"] == 100 \
            and out["experience_state"] == "unassessed" \
            and hf.passed and hf.state == EXP_UNASSESSED:
        _ok("V-EXP-UNASSESSED-NOT-FAIL",
            "no contract -> no verdict appended, score 100 unchanged, state reported "
            "as unassessed rather than passed or failed")
    else:
        _fail("V-EXP-UNASSESSED-NOT-FAIL",
              f"exp={parsed['experience']} coherence={coherence} "
              f"appended_nothing={appended_nothing} verdict={out['verdict']} "
              f"score={out['score']} state={out.get('experience_state')} "
              f"filter={hf.state}/{hf.passed}")


def gate_incoherent_refused(tmp: str) -> None:
    """A contract that contradicts itself is refused before a surface is built."""
    path = _write(tmp, "BROKEN.md", INCOHERENT)
    out = design_gate(path)
    crit = {f["criterion"] for f in out.get("critical", [])}

    trust = check_experience_coherence(
        {"trust_posture": "critical", "celebration_policy": "milestones_only"})
    outranked = check_experience_coherence(
        {"expressiveness": "restrained", "motion_budget": "high"})
    typo = check_experience_coherence({"waiting": "skelton"})
    inverted = check_experience_coherence(
        {"feedback_latency_ms": 2000, "progress_threshold_ms": 500})

    floor_blocked = out["verdict"] == "BLOCK" \
        and "experience-contract-coherent" in crit
    others = all(v is not None and v.status == "fail" and v.severity == "major"
                 for v in (trust, outranked, typo, inverted))
    if floor_blocked and others:
        _ok("V-EXP-INCOHERENT-REFUSED",
            "high+reduced_motion=absent BLOCKs as a floor breach; trust/budget/typo/"
            "inverted-thresholds each recorded as major")
    else:
        _fail("V-EXP-INCOHERENT-REFUSED",
              f"verdict={out['verdict']} criticals={sorted(crit)} "
              f"trust={trust and trust.severity} outranked={outranked and outranked.severity} "
              f"typo={typo and typo.severity} inverted={inverted and inverted.severity}")


def gate_breach_not_scored() -> None:
    """A non-floor contract breach is REPORTED and never moves the number."""
    verdicts = [Verdict("contrast-body", "visual", "fail", "major", observed="4.1:1")]
    baseline = score_review(verdicts)

    declared = {"motion_budget": "low", "celebration_policy": "never",
                "character_policy": "none", "success_posture": "confirm"}
    observed = {"motion_budget": "high", "celebrated_events": ["draft saved"],
                "character_present": True, "success_posture": "celebrate"}
    gated = review_gate(verdicts, declared_experience=declared,
                        observed_experience=observed)
    hf = gated.hard_filters[0]

    # The three axes must move independently: the SCORE is untouched, the VERDICT is
    # untouched, and the DONE-claim is withheld. Without the last one the filter would
    # be a finding nobody could act on -- reported, visible, and unable to stop
    # anything, which is the shape of a check that does not exist.
    if gated.score == baseline.score and gated.verdict == baseline.verdict \
            and gated.verdict == "APPROVE" and gated.is_done is False \
            and baseline.is_done is True \
            and hf["state"] == EXP_BREACHED and hf["passed"] is False \
            and hf["severity"] == "" and "NOT CONFORMING" in gated.reason \
            and len(hf["detail"]["breaches"]) == 4:
        _ok("V-EXP-BREACH-NOT-SCORED",
            f"4 breaches: score unchanged at {gated.score}, verdict unchanged at "
            f"{gated.verdict}, is_done withheld (True->False) -- quality, compliance "
            "and the done-claim move independently")
    else:
        _fail("V-EXP-BREACH-NOT-SCORED",
              f"score {baseline.score}->{gated.score} verdict {baseline.verdict}->"
              f"{gated.verdict} is_done {baseline.is_done}->{gated.is_done} "
              f"state={hf['state']} severity={hf['severity']!r} "
              f"breaches={len(hf['detail'].get('breaches', []))} "
              f"visible={'NOT CONFORMING' in gated.reason}")


def gate_floor_breach_blocks() -> None:
    """A floor breach is the one contract failure that DOES refuse the surface."""
    verdicts = [Verdict("contrast-body", "visual", "pass", observed="7.1:1")]
    declared = {"reduced_motion": "equivalent", "motion_budget": "medium"}
    observed = {"motion_present": True, "reduced_motion_equivalent": False,
                "motion_budget": "medium"}
    gated = review_gate(verdicts, declared_experience=declared,
                        observed_experience=observed)
    if gated.verdict == "BLOCK" and gated.reached_score is False \
            and gated.is_done is False and "accessibility floor" in gated.reason:
        _ok("V-EXP-FLOOR-BREACH-BLOCKS",
            "a missing reduced-motion equivalent blocks BEFORE the score; the review "
            "never reaches a number, which is different from scoring badly")
    else:
        _fail("V-EXP-FLOOR-BREACH-BLOCKS",
              f"verdict={gated.verdict} reached_score={gated.reached_score} "
              f"reason={gated.reason[:80]!r}")


def gate_score_equality() -> None:
    """The regression gate. With no filters, review_gate IS score_review."""
    verdicts = [
        Verdict("contrast-body", "visual", "fail", "critical", observed="2.6:1"),
        Verdict("type-levels", "visual", "fail", "major", observed="5 levels"),
        Verdict("spacing-system", "visual", "fail", "minor", observed="off 8px"),
    ]
    plain = score_review(verdicts)
    gated = review_gate(verdicts)
    if gated.score == plain.score == 65 and gated.verdict == plain.verdict \
            and gated.reason == plain.reason and gated.hard_filters == []:
        _ok("V-EXP-SCORE-EQUALITY",
            f"score={plain.score} verdict={plain.verdict}, reason byte-identical, "
            "zero filters -- adding the axis re-scored nothing")
    else:
        _fail("V-EXP-SCORE-EQUALITY",
              f"plain={plain.score}/{plain.verdict} gated={gated.score}/{gated.verdict} "
              f"reason_same={gated.reason == plain.reason} "
              f"filters={gated.hard_filters}")


def gate_context_derived(tmp: str) -> None:
    """The emitter derives what the document declares and OMITS what it does not."""
    declared_path = _write(tmp, "ADMIN2.md", ADMIN_CRUD)
    silent_path = _write(tmp, "LEGACY2.md", NO_CONTRACT)
    ctx = emit_context(declared_path)
    bare = emit_context(silent_path)

    derived_motion = ctx.get("motion_budget") == "none" \
        and ctx["_derivation"]["fields"]["motion_budget"].startswith("declared")
    defaulted_wcag = ctx.get("required_wcag") == "AA" \
        and "defaulted" in ctx["_derivation"]["fields"]["required_wcag"]
    omitted = "bundle_budget_kb" not in ctx and "bundle_budget_kb" in \
        ctx["_derivation"]["omitted"]
    silent_omits_motion = "motion_budget" not in bare \
        and "motion_budget" in bare["_derivation"]["omitted"]

    if derived_motion and defaulted_wcag and omitted and silent_omits_motion:
        _ok("V-EXP-CONTEXT-DERIVED",
            "motion_budget derived and labelled declared; required_wcag labelled "
            "defaulted; undeclared fields omitted and named, never guessed")
    else:
        _fail("V-EXP-CONTEXT-DERIVED",
              f"motion={derived_motion} wcag={defaulted_wcag} omitted={omitted} "
              f"silent={silent_omits_motion} ctx={ctx}")


def gate_conforming_filter() -> None:
    """A surface inside its contract reports CONFORMING, not merely 'not failing'."""
    declared = {"motion_budget": "low", "celebration_policy": "never",
                "character_policy": "none", "success_posture": "confirm",
                "reduced_motion": "equivalent"}
    observed = {"motion_budget": "low", "celebrated_events": [],
                "character_present": False, "success_posture": "confirm",
                "motion_present": True, "reduced_motion_equivalent": True}
    hf = check_experience_contract(declared, observed)
    partial = check_experience_contract(declared, None)
    if hf.passed and hf.state == EXP_CONFORMING \
            and partial.passed and partial.state == EXP_UNASSESSED \
            and "unmeasured" in partial.observed:
        _ok("V-EXP-CONFORMING",
            "conformance is stated positively; a declared-but-unmeasured contract is "
            "unassessed, never silently counted as conforming")
    else:
        _fail("V-EXP-CONFORMING",
              f"conforming={hf.state}/{hf.passed} declared_only={partial.state}/"
              f"{partial.passed}")


# --------------------------------------------------------------------------- #
# Regression gates from the independent review of this axis (2026-08-24).
# Each one reproduces a defect that shipped green under the original 11 gates,
# because every one of those gates exercised the spelling the author had in mind.
# --------------------------------------------------------------------------- #

def gate_floor_keyed_on_motion() -> None:
    """The floor must arm on MOTION being declared, not on one field's spelling.

    `expressiveness` is optional and the block is optional, so omitting it is
    ordinary. Keying the floor clause on it alone let the dataset's own canonical
    incoherence -- high motion with no reduced-motion equivalent -- pass as
    "internally coherent" whenever the sibling field happened to be absent.
    """
    cases = {
        "motion-only": {"motion_budget": "high", "reduced_motion": "absent"},
        "low-motion": {"expressiveness": "restrained", "motion_budget": "low",
                       "reduced_motion": "absent"},
        "expressiveness-only": {"expressiveness": "high", "reduced_motion": "absent"},
    }
    wrong = {}
    for name, exp in cases.items():
        v = check_experience_coherence(exp)
        if v is None or v.status != "fail" or v.severity != "critical":
            wrong[name] = (v and v.status, v and v.severity)

    # And the converse: no motion declared anywhere must NOT be a floor breach.
    still = check_experience_coherence(
        {"expressiveness": "none", "motion_budget": "none",
         "reduced_motion": "absent"})
    if wrong or still is None or still.status != "pass":
        _fail("V-EXP-FLOOR-KEYED-ON-MOTION",
              f"not-critical: {wrong}; still-surface={still and still.status}")
    else:
        _ok("V-EXP-FLOOR-KEYED-ON-MOTION",
            "3 spellings of declared motion + absent equivalent all CRITICAL; a "
            "declared-still surface with no motion is not a breach")


def gate_empty_block_not_declared(tmp: str) -> None:
    """A block that yields no field is `unassessed`, not an empty-but-valid contract.

    An author opening the block and leaving the values for the picker produced
    "0 field(s) declared, internally coherent" and `experience: declared` -- an
    unknown laundered into an affirmative pass, and the two halves of the axis
    disagreeing about the same document.
    """
    body = ("---\nname: StubProject\naesthetic_family: F1\nexperience:\n"
            "  # fill this in with the picker before shipping\n"
            "colors:\n  accent: \"#5e6ad2\"\n  neutral: \"#ffffff\"\n"
            "typography:\n  body-md:\n    fontFamily: Inter\n---\nStub.\n")
    path = _write(tmp, "STUB.md", body)
    parsed = parse_design_md(path)
    out = design_gate(path)
    criteria = {f["criterion"] for f in out.get("passed", [])}
    if parsed["experience"] is None and out["experience_state"] == "unassessed" \
            and "experience-contract-coherent" not in criteria:
        _ok("V-EXP-EMPTY-BLOCK-NOT-DECLARED",
            "an experience block yielding zero fields reads as unassessed, and no "
            "coherence verdict is manufactured for it")
    else:
        _fail("V-EXP-EMPTY-BLOCK-NOT-DECLARED",
              f"exp={parsed['experience']} state={out.get('experience_state')} "
              f"coherence_present={'experience-contract-coherent' in criteria}")


def gate_nested_key_not_hoisted(tmp: str) -> None:
    """A key nested below the contract's own indent is not a contract field.

    The field regex matched any indent, so a `reduced_motion` two levels down under
    a `notes:` key overwrote the real top-level declaration on a last-wins match --
    a silent wrong parse of the contract itself.
    """
    body = ("---\nname: NestedProject\naesthetic_family: F1\nexperience:\n"
            "  expressiveness: high\n  reduced_motion: equivalent\n"
            "  notes:\n    reduced_motion: absent means no equivalent\n"
            "colors:\n  accent: \"#5e6ad2\"\n  neutral: \"#ffffff\"\n"
            "typography:\n  body-md:\n    fontFamily: Inter\n---\nNested.\n")
    path = _write(tmp, "NESTED.md", body)
    exp = parse_design_md(path)["experience"]
    if exp and exp.get("reduced_motion") == "equivalent" \
            and exp.get("expressiveness") == "high":
        _ok("V-EXP-NESTED-KEY-NOT-HOISTED",
            "the top-level declaration survives a same-named key nested beneath "
            "another field")
    else:
        _fail("V-EXP-NESTED-KEY-NOT-HOISTED", f"parsed {exp}")


def gate_context_rejects_unknown(tmp: str) -> None:
    """A declared-but-unusable value is REJECTED and named, never passed through.

    In the consumer, an unknown `motion_budget` makes the MOTION_BUDGET filter unable
    to fire for any component, and an unknown `required_wcag` removes the entire
    candidate field. Emitting either produces exactly the fiction the emitter's
    docstring promises to avoid. Case, by contrast, is not a different requirement --
    it is normalised, and the normalisation is stated.
    """
    body = ("---\nname: BadVocabProject\naesthetic_family: F1\n"
            "required_wcag: aa\nexperience:\n  motion_budget: minimal\n"
            "colors:\n  accent: \"#5e6ad2\"\n  neutral: \"#ffffff\"\n"
            "typography:\n  body-md:\n    fontFamily: Inter\n---\nBad vocab.\n")
    path = _write(tmp, "BADVOCAB.md", body)
    ctx = emit_context(path)
    rejected = ctx["_derivation"]["rejected"]
    if "motion_budget" not in ctx and "motion_budget" in rejected \
            and ctx.get("required_wcag") == "AA" \
            and "normalised" in ctx["_derivation"]["fields"]["required_wcag"]:
        _ok("V-EXP-CONTEXT-REJECTS-UNKNOWN",
            "an out-of-vocabulary motion_budget is rejected and named; a lowercase "
            "WCAG level is normalised to the consumer's spelling, not rejected")
    else:
        _fail("V-EXP-CONTEXT-REJECTS-UNKNOWN",
              f"motion_in_ctx={'motion_budget' in ctx} rejected={list(rejected)} "
              f"wcag={ctx.get('required_wcag')}")


def gate_template_context_complete() -> None:
    """The workflow the template mandates must not be weaker than the hand-written
    context it replaces. Every provenance decision the selector can filter on is
    declared in front-matter, so nothing the document decided is silently omitted."""
    ctx = emit_context(REPO_TEMPLATE)
    d = ctx["_derivation"]
    have = {"motion_budget", "required_wcag", "bundle_budget_kb",
            "unresolved_ux_findings"} <= set(ctx)
    if have and d["omitted"] == [] and d["rejected"] == {}:
        _ok("V-EXP-TEMPLATE-CONTEXT-COMPLETE",
            f"the repo template emits every filterable decision "
            f"(bundle={ctx['bundle_budget_kb']}kB, wcag={ctx['required_wcag']}, "
            f"motion={ctx['motion_budget']}), nothing omitted")
    else:
        _fail("V-EXP-TEMPLATE-CONTEXT-COMPLETE",
              f"keys={sorted(k for k in ctx if k != '_derivation')} "
              f"omitted={d['omitted']} rejected={list(d['rejected'])}")


def gate_floor_not_declarable_away() -> None:
    """No declaration buys the reduced-motion exemption.

    The floor branch was gated on the CONTRACT saying `equivalent`, so declaring
    `absent` -- or omitting the field -- made the filter report CONFORMING for a
    surface shipping motion with no equivalent. Worse than silence: it asserted
    conformance, which a reviewer reads as "behaviour checked".
    """
    observed = {"motion_present": True, "reduced_motion_equivalent": False,
                "motion_budget": "low"}
    declared_absent = {"expressiveness": "restrained", "motion_budget": "low",
                       "reduced_motion": "absent"}
    declared_silent = {"expressiveness": "restrained", "motion_budget": "low"}

    a = check_experience_contract(declared_absent, observed)
    b = check_experience_contract(declared_silent, observed)
    gated = review_gate([Verdict("contrast-body", "visual", "pass", observed="7:1")],
                        declared_experience=declared_absent,
                        observed_experience=observed)
    if a.passed is False and a.severity == "critical" and a.state == EXP_BREACHED \
            and b.passed is False and b.severity == "critical" \
            and gated.verdict == "BLOCK" and gated.is_done is False:
        _ok("V-EXP-FLOOR-NOT-DECLARABLE-AWAY",
            "declaring reduced_motion=absent, and omitting it entirely, both still "
            "breach the floor and BLOCK -- the exemption cannot be bought")
    else:
        _fail("V-EXP-FLOOR-NOT-DECLARABLE-AWAY",
              f"absent={a.passed}/{a.severity} silent={b.passed}/{b.severity} "
              f"verdict={gated.verdict} is_done={gated.is_done}")


def gate_emit_fail_open(tmp: str) -> None:
    """Fail-open covers WRITING too. An unwritable --out is an operator path mistake;
    raising would exit 1, which this tool's own exit table means REVISE, so a CI
    wrapper could not tell a bad output directory from a failing design."""
    bad = os.path.join(tmp, "no-such-dir", "ctx.json")
    try:
        code = gate_main([REPO_TEMPLATE, "--emit-context", "--out", bad])
    except Exception as exc:                       # noqa: BLE001 -- that IS the defect
        _fail("V-EXP-EMIT-FAIL-OPEN", f"raised instead of failing open: {exc!r}")
        return
    if code == 0 and not os.path.exists(bad):
        _ok("V-EXP-EMIT-FAIL-OPEN",
            "an unwritable --out path returns 0 with the context still printed, "
            "never a traceback and never a REVISE exit code")
    else:
        _fail("V-EXP-EMIT-FAIL-OPEN", f"exit={code} wrote={os.path.exists(bad)}")


def main() -> int:
    print("V-EXP gates (CDIO-07 experience contract)")
    gate_floors_refuse()
    gate_floors_pass()
    gate_bidirectional()
    with tempfile.TemporaryDirectory() as tmp:
        gate_abstention(tmp)
        gate_unassessed(tmp)
        gate_incoherent_refused(tmp)
        gate_context_derived(tmp)
        gate_empty_block_not_declared(tmp)
        gate_nested_key_not_hoisted(tmp)
        gate_context_rejects_unknown(tmp)
        gate_emit_fail_open(tmp)
    gate_breach_not_scored()
    gate_floor_breach_blocks()
    gate_score_equality()
    gate_conforming_filter()
    gate_floor_keyed_on_motion()
    gate_template_context_complete()
    gate_floor_not_declarable_away()
    total = PASSES + FAILS
    print(f"\nEXPERIENCE_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
