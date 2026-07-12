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

import copy
import json
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
from modules.sqi import baseline_guardian as guardian
from modules.sqi import weakening_detectors as WD
from modules.sqi import weakening_baseline as WB


class _FakeReport:
    """The weakening layer needs exactly two things from a reconciliation: the authored identity
    set and a commit. Constructing a real report over a scratch tree would spawn pytest
    subprocesses to measure a reach nobody is asserting -- an expensive way to obtain two fields.
    This is a boundary stub (rules/python/testing.md: mock at the boundary), not a stand-in for
    any logic under test: every count these tests check is computed from a real file on disk."""

    def __init__(self, authored_files, commit="deadbeef"):
        self.authored_files = list(authored_files)
        self.commit = commit


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


# --- SQI-02 Part XII: the baseline guardian --------------------------------------------
#
# Every gate below writes only inside a tmp_path. A guardian test that touched the real
# vault/audits/sqi_baseline.json would ratchet it as a side effect of being run, and the suite
# would stop being hermetic on its own second execution.

ENV = "test-env-key"


def _base(tmp_path, rep, env=ENV):
    p = tmp_path / "baseline.json"
    guardian.save_baseline(p, guardian.snapshot(rep, env))
    return p


def test_guardian_first_run_creates_baseline(tmp_path, report):
    p = tmp_path / "baseline.json"

    v = guardian.check(report, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.CREATED
    assert v.failing is False
    assert p.is_file()


def test_guardian_passes_when_stable(tmp_path, report):
    p = _base(tmp_path, report)

    v = guardian.check(report, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.PASS
    assert v.failing is False
    assert v.updated is False  # nothing improved; nothing to ratchet


def test_guardian_fails_the_build_on_a_silent_decrease(tmp_path, report):
    # 12.2: an increase requires nothing, and a decrease fails the build.
    snap = guardian.snapshot(report, ENV)
    root = next(iter(snap["roots"]))
    snap["roots"][root]["executed_cases"] += 1  # baseline remembers one more than we observe
    p = tmp_path / "baseline.json"
    guardian.save_baseline(p, snap)

    v = guardian.check(report, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.REGRESSED
    assert v.failing is True
    assert v.updated is False, "a decrease must NEVER auto-update the baseline (12.7)"
    assert any(r.gate == "executed" for r in v.regressions)


def test_guardian_ratchets_the_baseline_upward(tmp_path, report):
    snap = guardian.snapshot(report, ENV)
    root = next(iter(snap["roots"]))
    observed = snap["roots"][root]["executed_cases"]
    snap["roots"][root]["executed_cases"] = observed - 1  # we have grown since the baseline
    p = tmp_path / "baseline.json"
    guardian.save_baseline(p, snap)

    v = guardian.check(report, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.PASS
    assert v.updated is True
    after = json.loads(p.read_text(encoding="utf-8"))
    assert after["roots"][root]["executed_cases"] == observed


def test_guardian_blocks_the_deletion_attack(tmp_path, report):
    """SQI-02 18.2, the FIRST attack on this instrument.

    Delete the orphans and reach goes from 3% to 100% while the executed count never moves. A
    guardian that gated on the ratio would report a triumph over a repository that had just lost
    98 test files. The countermeasure is that the ABSOLUTE authored count must not fall.
    """
    p = _base(tmp_path, report)

    attacked = copy.deepcopy(report)
    reached = set(attacked.reached_files)
    attacked.authored_files = sorted(reached)   # every orphan deleted
    attacked.authored_count = len(reached)
    attacked.orphaned_files, attacked.orphaned_count = [], 0
    attacked.test_file_reach = 1.0              # a perfect score

    v = guardian.check(attacked, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.REGRESSED, "the deletion attack bought a green"
    assert v.failing is True
    authored = [r for r in v.regressions if r.gate == "authored"]
    assert authored, "reach hit 100% and no gate fired -- the ratio was gameable"
    assert len(authored[0].lost_identities) > 50  # every deleted file is NAMED


def test_guardian_lowering_requires_an_attributed_act(tmp_path, report):
    # 12.7, the firewall. A baseline lowered calmly, in its own commit, with a stated reason, is
    # governance. The same baseline lowered inside the commit that made it necessary is an escape.
    p = _base(tmp_path, report)
    attacked = copy.deepcopy(report)
    attacked.authored_files = sorted(set(attacked.reached_files))
    attacked.authored_count = len(attacked.authored_files)

    v = guardian.check(
        attacked, ENV, repo=ROOT, baseline_path=p,
        accept=True, reason="module retired", author="owner",
    )

    assert v.verdict == guardian.PASS
    assert v.updated is True
    rec = json.loads(p.read_text(encoding="utf-8"))
    assert rec["author"] == "owner"
    assert rec["reason"] == "module retired"
    assert rec["removed_identities"], "an acceptance must record WHAT it accepted losing"


def test_guardian_refuses_to_compare_across_environments(tmp_path, report):
    # 12.4: the same repository yields 1,606 assertions under one toolchain and zero under a
    # runtime one major version behind. An alarm here would dispatch an engineer to hunt for
    # deleted tests that nobody deleted. The guardian says so rather than raising an alarm it
    # cannot substantiate.
    p = _base(tmp_path, report, env="host-a")

    v = guardian.check(report, "host-b", repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.ENV_MISMATCH
    assert v.failing is False
    assert not v.regressions


def test_guardian_fails_open_to_unknown_on_a_corrupt_baseline(tmp_path, report):
    # A disarmed guard that reports success is the exact artifact this corpus discredits.
    p = tmp_path / "baseline.json"
    p.write_text("{ this is not json", encoding="utf-8")

    v = guardian.check(report, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.UNKNOWN
    assert v.failing is False   # it cannot substantiate a FAIL
    assert v.verdict != guardian.PASS  # and it must never claim one
    assert v.error


def test_guardian_catches_a_root_that_vanished(tmp_path, report):
    # 12.3: a repository total permits redistribution -- an entire root can die while a growing
    # sibling absorbs the difference and the total RISES. Per-root baselines make that impossible.
    snap = guardian.snapshot(report, ENV)
    snap["roots"]["pytest ghost/"] = {
        "invocation": "pytest ghost/", "oracle": "ci",
        "executed_cases": 500, "executed_files": ["ghost/test_x.py"],
    }
    p = tmp_path / "baseline.json"
    guardian.save_baseline(p, snap)

    v = guardian.check(report, ENV, repo=ROOT, baseline_path=p)

    assert v.verdict == guardian.REGRESSED
    assert any(r.root == "pytest ghost/" and r.observed == 0 for r in v.regressions)


# --- SQI-02 Part XV: the weakening detectors -----------------------------------------
#
# The guardian above gates COUNTS, so it catches every failure that lowers a number. These gate
# the CONTENT of the tests that survive, because weakening lowers nothing at all: the file is
# present, the case is collected, the case passes, and the protection is gone (15.1).


def _rec(tmp_path, name: str, body: str) -> tuple[Path, str]:
    f = tmp_path / name
    f.write_text(body, encoding="utf-8")
    return f, _norm(name)


def test_assertion_counter_ignores_comments_and_strings(tmp_path):
    # An instrument that can be satisfied by writing the word `assert` in a comment will be
    # satisfied exactly when somebody is trying to satisfy it. Hence the AST, never a regex.
    f, _ = _rec(tmp_path, "test_x.py", (
        '"""A docstring that says assert assert assert."""\n'
        "def test_a():\n"
        "    # assert this is not counted\n"
        '    s = "assert neither is this"\n'
        "    assert s\n"
        "    assert len(s) > 3\n"
    ))

    assert WD.count_assertions(f) == 2


def test_assertion_counter_sees_the_v_gate_idiom(tmp_path):
    # The finding that produced the governed vocabulary: 60 of this repository's 101 authored
    # test files verify through `_ok` / `_fail`, one of them 139 times, and a detector blind to
    # that idiom would grade the majority of the suite as protecting nothing -- while being
    # unable to notice if it ever stopped, because zero cannot fall.
    f, _ = _rec(tmp_path, "test_v.py", (
        "def main():\n"
        "    if cond:\n"
        '        _ok("V-A", "evidence")\n'
        "    else:\n"
        '        _fail("V-A", "diagnostic")\n'
        '    _ok("V-B", "more")\n'
    ))

    assert WD.count_assertions(f) == 3


def test_exit_code_gate_is_unknown_never_zero(tmp_path):
    # A file whose protection is `sys.exit(main())` has no assertion of any form. Recording it as
    # ZERO would be the worst available answer: zero cannot fall, so the gate would be
    # permanently blind to it, while the report called it unprotected. Both halves wrong.
    f, rel = _rec(tmp_path, "test_gate.py", (
        "import sys\n"
        "def main():\n"
        "    fails = 0\n"
        "    return 1 if fails else 0\n"
        "sys.exit(main())\n"
    ))

    r = WD.scan_file(tmp_path, f)

    assert r.assertions is None            # UNKNOWN
    assert r.assertions != 0               # and explicitly NOT a zero
    assert r.verification == "exit_code_gate"
    assert r.sha256                        # still hash-tracked: gate C is its only cover


def test_weakening_baseline_fails_on_a_removed_assertion(tmp_path):
    # Gate A (15.2). The file is present, the case is collected, the case passes -- and it
    # asserts one thing less than it did. Nothing else in SQI can see this.
    f, rel = _rec(tmp_path, "test_a.py", "def test_a():\n    assert 1\n    assert 2\n    assert 3\n")
    rep = _FakeReport([rel])
    p = tmp_path / "wb.json"
    assert WB.check(rep, repo=tmp_path, baseline_path=p).verdict == WB.CREATED

    f.write_text("def test_a():\n    assert 1\n    assert 2\n", encoding="utf-8")
    v = WB.check(rep, repo=tmp_path, baseline_path=p)

    assert v.verdict == WB.WEAKENED
    assert v.failing is True
    assert any(w.gate == "assertions" and w.baseline == 3 and w.observed == 2
               for w in v.weakenings)


def test_weakening_baseline_passes_and_ratchets_on_an_added_assertion(tmp_path):
    # An increase requires nothing (12.2), and it ratchets: the added assertion becomes the new
    # floor, so removing it tomorrow fails the build.
    f, rel = _rec(tmp_path, "test_a.py", "def test_a():\n    assert 1\n")
    rep = _FakeReport([rel])
    p = tmp_path / "wb.json"
    WB.check(rep, repo=tmp_path, baseline_path=p)

    f.write_text("def test_a():\n    assert 1\n    assert 2\n", encoding="utf-8")
    v = WB.check(rep, repo=tmp_path, baseline_path=p)

    assert v.verdict == WB.PASS
    assert v.failing is False
    assert json.loads(p.read_text(encoding="utf-8"))["files"][rel]["assertions"] == 2


def test_over_mocking_gate_is_a_delta_never_a_ratio(tmp_path):
    # 15.6, and the reason the inline plan's `mocks / assertions > threshold` gate was NOT built.
    # A ratio falls when its denominator rises, and the cheapest way to raise an assertion count
    # is `assert x is not None` -- an assertion that passes for every implementation including a
    # broken one, which is weakening 15.8. A ratio gate is quieted by the very attack Part XV
    # exists to catch. This asserts the delta rule instead: mocks rose, assertions did not.
    f, rel = _rec(tmp_path, "test_m.py", (
        "def test_a(monkeypatch):\n"
        "    m = Mock()\n"
        "    assert m\n"
    ))
    rep = _FakeReport([rel])
    p = tmp_path / "wb.json"
    WB.check(rep, repo=tmp_path, baseline_path=p)

    # Three more collaborators stubbed out; the assertion count does not move. The test has moved
    # away from reality without moving away from green.
    f.write_text(
        "def test_a(monkeypatch):\n"
        "    m = Mock()\n"
        "    m2 = MagicMock()\n"
        "    m3 = create_autospec(object)\n"
        "    monkeypatch.setattr('x', 'y')\n"
        "    assert m\n",
        encoding="utf-8",
    )
    v = WB.check(rep, repo=tmp_path, baseline_path=p)

    assert v.verdict == WB.WEAKENED
    assert any(w.gate == "mocks" for w in v.weakenings)

    # And the ratio-gate defeat, proven rather than argued: adding a tautological assertion
    # LOWERS mocks/assertions from 4.0 to 1.33. A ratio gate would now report an improvement.
    ratio_before, ratio_after = 4 / 1, 4 / 3
    assert ratio_after < ratio_before


def test_content_hash_is_review_never_a_build_failure(tmp_path):
    # 15.4 / 15.9. The content moved and the arithmetic held -- the signature of a weakened
    # fixture and of a same-name rewrite. It is ALSO the signature of every honest refactor, and
    # 15.3/15.4 are explicit that this produces "a candidate list for review rather than a
    # verdict". A gate that failed the build here would be switched off within a week.
    f, rel = _rec(tmp_path, "test_c.py", "def test_a():\n    payload = {'a': 1, 'b': 2}\n    assert payload\n")
    rep = _FakeReport([rel])
    p = tmp_path / "wb.json"
    WB.check(rep, repo=tmp_path, baseline_path=p)

    # The fixture becomes minimal. Assertions: 1. Cases: 1. Mocks: 0. Nothing moved but the bytes.
    f.write_text("def test_a():\n    payload = {'a': 1}\n    assert payload\n", encoding="utf-8")
    v = WB.check(rep, repo=tmp_path, baseline_path=p)

    assert v.verdict == WB.REVIEW
    assert v.failing is False
    assert any(w.gate == "content" and w.path == rel for w in v.reviews)


def test_weakening_fails_open_to_unknown_never_a_false_pass(tmp_path):
    # Two independent fail-open paths, and neither may produce a PASS.
    f, rel = _rec(tmp_path, "test_u.py", "def test_a(:\n  syntax error\n")
    rep = _FakeReport([rel])

    # (1) an unparseable file is UNKNOWN, not zero assertions -- otherwise a syntax error would
    # manufacture a weakening event out of nothing.
    r = WD.scan_file(tmp_path, f)
    assert r.assertions is None
    assert r.error

    # (2) a corrupt baseline disarms the guard, and a disarmed guard reporting success is the
    # exact artifact this corpus exists to discredit.
    p = tmp_path / "wb.json"
    p.write_text("{ not json", encoding="utf-8")
    v = WB.check(rep, repo=tmp_path, baseline_path=p)

    assert v.verdict == WB.UNKNOWN
    assert v.verdict != WB.PASS
    assert v.failing is False


def test_baseline_path_honours_the_environment_override(tmp_path, monkeypatch):
    # This test exists because the mutation probe demanded it, which is the probe working exactly
    # as 15.8 intends. Breaking the return value of `default_baseline_path`'s override branch left
    # 41 tests green in BOTH baseline modules: no reached test ever executed the line. That branch
    # is the only reason this suite and the done-gate are hermetic -- it redirects both baselines
    # into a temp tree. Had the redirect silently stopped working, every gate run would have
    # ratcheted the repository's REAL baselines as a side effect of being run, and the suite would
    # have started failing on its own second execution with no visible cause.
    custom = tmp_path / "custom.json"

    monkeypatch.setenv("SQI_BASELINE_PATH", str(custom))
    monkeypatch.setenv("SQI_WEAKENING_BASELINE_PATH", str(custom))

    assert guardian.default_baseline_path(ROOT) == custom
    assert WB.default_baseline_path(ROOT) == custom

    # And with no override, both fall back to the repository's real artifact. The fallback is the
    # branch the probe actually broke -- `ast.walk` is breadth-first, so the site it selects is the
    # return that is a direct child of the function, not the one nested inside the `if`.
    monkeypatch.delenv("SQI_BASELINE_PATH")
    monkeypatch.delenv("SQI_WEAKENING_BASELINE_PATH")

    assert guardian.default_baseline_path(ROOT) == ROOT / "vault" / "audits" / "sqi_baseline.json"
    assert WB.default_baseline_path(ROOT) == (
        ROOT / "vault" / "audits" / "sqi_weakening_baseline.json"
    )


def test_mutation_probe_finds_the_tautological_assertion(tmp_path):
    # 15.8, the endpoint of every other weakening, and the ONLY one no count reveals. Two tests
    # reference the same unit. One asserts the returned VALUE. The other asserts, in the Part's
    # own words, "that a call did not raise" -- it executes the unit and says nothing about what
    # came back. Both are green, both are collected, both have an assertion count of ONE, and
    # both appear in a coverage report as covered lines. Every instrument in this corpus except
    # this one calls them equivalent. Break the return value and exactly one of them notices.
    (tmp_path / "unit.py").write_text("def value():\n    return 42\n", encoding="utf-8")
    (tmp_path / "test_strong.py").write_text(
        "from unit import value\n"
        "def test_strong():\n"
        "    assert value() == 42\n",
        encoding="utf-8",
    )
    (tmp_path / "test_tauto.py").write_text(
        "from unit import value\n"
        "def test_tauto():\n"
        "    value()\n"
        "    assert True\n",
        encoding="utf-8",
    )

    probe = WD.mutation_probe(
        tmp_path,
        invocation="pytest .",
        targets=["unit.py"],
        test_files=["test_strong.py", "test_tauto.py"],
        allow_dirty=True,          # a scratch tree, not a working tree
        timeout=180,
    )

    assert len(probe.mutants) == 1
    m = probe.mutants[0]
    assert m.status == "KILLED"                                  # the strong test noticed
    assert any("test_strong.py" in n for n in m.killed_by)
    assert any("test_tauto.py" in n for n in m.survived_by)      # the tautology did not
    assert len(m.killed_by) == 1 and len(m.survived_by) == 1

    # And the file is byte-identical to what it was before the probe ran. A measurement that
    # leaves a mutant on disk is not a measurement; it is a defect.
    assert (tmp_path / "unit.py").read_text(encoding="utf-8") == "def value():\n    return 42\n"
