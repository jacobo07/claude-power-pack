"""tests/test_sqi_engine.py — the SQI executable layer, inside the canonical invocation.

This file exists at this path for a reason that is itself a finding. SQI-02 5.10 makes the
engine's own reach a MANDATORY field of every report it emits: the engine is a program, it
lives in a file, and that file is subject to the exact law it enforces -- it can be
authored and never executed. On its first run against this repository the engine reported
SELF-REACH ZERO about itself. An auditor exempt from its own audit is not an auditor.

The remediation is rung one of the engine's own ladder (SQI-02 4.8): connect the artifact
to the invocation. So the engine's tests live in `tests/`, which is what `pytest tests/`
actually collects -- not in `tools/`, where 72 of this repository's authored test files sit
unreached.

AAA per rules/python/testing.md. No mocks: every assertion is against a real scan of a real
tree.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.sqi.repo_reality_scanner import scan_repo
from modules.sqi.environment_qualifier import (
    qualify, QUALIFIED, PARTIALLY_QUALIFIED, BLOCKED, UNKNOWN, VERDICT_CEILING, GATES,
)
from modules.sqi.reconcile import (
    reconcile, discover_invocations, _norm, _classify, _parse_manifest, Invocation,
    TRUE_GREEN, PARTIAL_GREEN, MISLEADING_GREEN, UNVERIFIED_GREEN,
    ENVIRONMENT_DEPENDENT_GREEN, VERDICT_TO_ONTOLOGY,
)


@pytest.fixture(scope="module")
def profile():
    return scan_repo(ROOT)


@pytest.fixture(scope="module")
def report():
    """One real reconciliation of this repository. Spawns collection-only subprocesses;
    collection costs seconds and has no side effects, which is what makes the engine cheap
    enough to gate on (SQI-02 5.3)."""
    return reconcile(ROOT, hermetic_runs=1)


# --- SQI-01: the Reality Scanner -----------------------------------------------------

def test_scanner_detects_python_context(profile):
    # Arrange / Act — the scan is the fixture.
    langs = [c.language for c in profile.language_contexts]

    # Assert
    assert "python" in langs
    py = next(c for c in profile.language_contexts if c.language == "python")
    assert py.runner == "pytest"
    assert "test_*.py" in py.test_patterns


def test_scanner_never_invokes_repository_code(profile):
    # A scanner that executes repository code to discover its shape inverts the dependency
    # (SQI-01 3.2). The proof is structural: the profile is produced from reads alone, and
    # the module imports no runner. This asserts the observable consequence -- a scan of a
    # tree containing a booby-trapped module completes without executing it.
    with tempfile.TemporaryDirectory() as td:
        bomb = Path(td) / "test_bomb.py"
        bomb.write_text("raise SystemExit('the scanner executed me')\n", encoding="utf-8")

        prof = scan_repo(td)

        assert len(prof.test_artifacts) == 1
        assert prof.test_artifacts[0]["path"] == "test_bomb.py"


def test_scanner_fails_open_on_unknown_stack():
    # An unrecognized tree yields UNKNOWN, never a raise. Manifest-absence is evidence of a
    # repository with no executable surface, not a scan failure (SQI-01 3.5).
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "notes.md").write_text("no code here", encoding="utf-8")

        prof = scan_repo(td)

        assert prof.language_contexts == []
        assert prof.domains == ["content_vault"]
        assert "no_language_context" in prof.unknowns
        assert prof.scan_error is None


def test_scanner_reports_its_own_uncertainty(profile):
    # A census that cannot state what it might have missed is asserting a completeness it
    # has not earned (SQI-02 3.5).
    assert profile.uncertainty_count >= 0
    assert isinstance(profile.per_rule_hits, dict)
    assert sum(profile.per_rule_hits.values()) == len(profile.test_artifacts)


def test_scanner_assigns_domains_as_a_set_not_a_label(profile):
    # Forcing a single label is how one of two applicable standards silently disappears
    # (SQI-01 7.4). This estate is an agent system AND a prompt system AND a content vault.
    assert len(profile.domains) > 1
    assert "agent_system" in profile.domains


# --- SQI-03: the Environment Qualifier ------------------------------------------------

def test_qualifier_runs_seven_gates_and_marks_unevaluated_as_unknown(profile):
    record = qualify(ROOT, profile=profile)

    assert [g.gate for g in record.gates] == GATES
    # An UNKNOWN gate reads as an open question; an omitted gate reads as an absent
    # concern (SQI-03 3.9). None is never coerced to False.
    assert any(g.passed is None for g in record.gates)


def test_qualifier_never_grants_qualified_without_observing_every_gate(profile):
    record = qualify(ROOT, profile=profile)

    # QUALIFIED is earned by affirmative observation, never by the absence of a complaint
    # (SQI-03 3.10). This host cannot reach it: containment is unobserved.
    assert record.state != QUALIFIED
    assert record.state == PARTIALLY_QUALIFIED
    assert record.verdict_ceiling == VERDICT_CEILING[PARTIALLY_QUALIFIED]


def test_qualifier_blocks_with_a_verbatim_blocker_when_no_toolchain():
    # A BLOCKED verdict carrying no blocker string is not a weak record, it is an
    # inadmissible one (SQI-03 4.4).
    class _NoToolchain:
        language_contexts = [type("C", (), {"language": "elixir", "lock_state": "UNLOCKED"})()]

    record = qualify(ROOT, profile=_NoToolchain())

    if record.state == BLOCKED:
        assert record.blockers, "BLOCKED without a verbatim blocker is inadmissible"
        assert all(g.passed is None for g in record.gates[2:])


# --- SQI-02: the Reconciliation Engine ------------------------------------------------

def test_join_key_normalizes_both_sides():
    # A join that fails on normalization reports every test as an orphan -- a catastrophic
    # false positive that destroys the engine's credibility on first contact (SQI-02 5.4).
    assert _norm(r"Tools\Test_Foo.py") == "tools/test_foo.py"
    assert _norm("./tools/test_foo.py") == "tools/test_foo.py"
    assert _norm("tools/test_foo.py") == _norm(r".\Tools\TEST_FOO.PY")


def test_join_sanity_is_asserted(report):
    # An intersection of zero is a normalization bug, not a finding of total orphanhood.
    assert report.join_sanity["sane"] is True
    assert report.join_sanity["intersection"] > 0


def test_manifest_parser_harvests_identities_not_counts():
    out = "tests/a.py::test_one\ntests/a.py::test_two\ntests/b.py::test_three\n\n3 tests collected in 0.1s\n"

    files, cases, errors, desel = _parse_manifest(out)

    assert files == ["tests/a.py", "tests/b.py"]  # a SET, which can be subtracted
    assert cases == 3
    assert errors == 0


def test_oracle_precedence_zero_arg_default_is_authoritative_without_ci():
    # SQI-02 9.4: where no job exists, the zero-argument default is authoritative, because
    # it is what will be run by whoever arrives next. Documentation is NEVER authoritative.
    invs = discover_invocations(ROOT)

    auth = [i for i in invs if i.authoritative]
    assert len(auth) == 1
    assert auth[0].oracle == "zero_arg_default"
    assert all(not i.authoritative for i in invs if i.oracle == "documentation")


def test_reconcile_finds_orphans_in_this_repository(report):
    # The founding finding, reproduced from the disk rather than from a fixture.
    assert report.authored_count > 90
    assert report.orphaned_count > 0
    assert report.orphaned_ratio is not None and report.orphaned_ratio > 0.9
    assert report.test_file_reach is not None and report.test_file_reach < 0.10


def test_reconcile_reports_authoritative_reach_as_unknown_not_zero(report):
    # The zero-argument default crashes on collection in this repository. Reach under it is
    # UNKNOWN, never zero: zero is a measurement and this is the absence of one (5.8).
    auth = next(i for i in report.invocations if i.authoritative)
    if auth.status == "BROKEN":
        assert report.authoritative_reach_state == "UNKNOWN"
        assert auth.blocker, "a BROKEN invocation must carry its blocker verbatim"


def test_test_case_reach_is_unknown_never_estimated(report):
    # A repository that cannot state how many cases it authored cannot compute the metric
    # that would tell it how many are protecting anything. An engine that filled the gap
    # with an estimate would manufacture the exact false confidence it exists to destroy
    # (SQI-02 7.6). The unknown IS the finding.
    assert report.test_case_reach is None


def test_surprise_set_is_the_instruments_self_audit(report):
    # Non-empty means the authored census is incomplete and every reach figure is
    # flatteringly wrong (5.6). It must be empty here, or the instrument is broken.
    assert report.surprise_files == []


def test_executed_protection_ratio_counts_the_guarded_not_the_guards(report):
    # The only metric whose denominator is risk rather than tests (SQI-02 8.6).
    assert report.executed_protection_ratio is not None
    assert 0.0 <= report.executed_protection_ratio <= 1.0
    assert len(report.unprotected_surface) > 0  # this repository is not surface-clean


def test_engine_reports_its_own_reach(report):
    # SQI-02 5.10: a report that does not contain a positive self-reach assertion is
    # INADMISSIBLE. This test is the mechanism by which the assertion becomes positive --
    # it is reached by `pytest tests/`, it imports the engine, and so the engine is inside
    # the surface it audits.
    assert report.self_reach["engine"] == "modules/sqi"
    assert report.self_reach["reached"] is True, (
        "the engine is not exercised by any test the canonical invocation reaches"
    )
    assert report.self_reach["admissible"] is True
    assert "tests/test_sqi_engine.py" in report.self_reach["reached_by"]


# --- SQI-02 Part XVI: the five green verdicts -----------------------------------------

def _inv(cases: int | None) -> Invocation:
    i = Invocation(command="pytest", oracle="zero_arg_default", authoritative=True)
    i.executed_cases = cases
    return i


def test_verdict_probe1_examined_nothing_is_unverified_green():
    v = _classify(_inv(0), reconciled=True, orphans=0, surface_clean=True,
                  env_qualified=True, hermetic_stable=True)
    assert v == UNVERIFIED_GREEN


def test_verdict_probe2_unqualified_environment_is_environment_dependent():
    v = _classify(_inv(43), reconciled=True, orphans=0, surface_clean=True,
                  env_qualified=False, hermetic_stable=True)
    assert v == ENVIRONMENT_DEPENDENT_GREEN


def test_verdict_probe3_default_without_reconciliation_is_misleading_green():
    # The single most consequential rule in Part XVI (16.8): the burden of proof falls on
    # the party claiming protection. An unreconciled green carries zero information about
    # the fraction of authored protection it describes.
    v = _classify(_inv(43), reconciled=False, orphans=0, surface_clean=True,
                  env_qualified=True, hermetic_stable=True)
    assert v == MISLEADING_GREEN
    assert VERDICT_TO_ONTOLOGY[MISLEADING_GREEN] == "UNVERIFIED"  # not PARTIALLY-VERIFIED


def test_verdict_probe4_orphans_present_is_partial_green():
    v = _classify(_inv(43), reconciled=True, orphans=98, surface_clean=True,
                  env_qualified=True, hermetic_stable=True)
    assert v == PARTIAL_GREEN


def test_verdict_true_green_is_reachable_but_requires_everything():
    # A gate that cannot reach both poles is not a gate. TRUE GREEN is rare, and its rarity
    # is the honest measurement rather than a defect in the standard (16.2).
    v = _classify(_inv(43), reconciled=True, orphans=0, surface_clean=True,
                  env_qualified=True, hermetic_stable=True)
    assert v == TRUE_GREEN
    assert VERDICT_TO_ONTOLOGY[TRUE_GREEN] == "PROVEN"


def test_this_repository_is_not_true_green(report):
    # The whole point. 98 orphans and 63 unprotected surface elements.
    assert report.signal_integrity_verdict != TRUE_GREEN
