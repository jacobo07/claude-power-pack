#!/usr/bin/env python3
"""Done-gate for the two EGCC residues (spec: vault/specs/egcc-residue-rc1-rc2.md).

Rc1 -- a compiled rule can declare WHERE it binds.
Rc2 -- the drift registry, discovered from disk.

Every gate is asserted in BOTH directions. A gate observed only to PASS is
not a gate, it is a function that returns True (`enforcement_scs_c92`).

Hermetic: the only writes go to a tempdir that is removed. The corpus is
read, never written, so a second run in the same session sees the same
numbers -- the property `feedback_hermetic_test_global_writes_time_window`
exists to protect.

    python tools/test_egcc_residue.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.drift_registry.registry import render, scan          # noqa: E402
from modules.rule_compiler.compiler import compile_rules          # noqa: E402
from modules.rule_compiler.digest import build_digest             # noqa: E402
from modules.rule_compiler.parser import parse_archive            # noqa: E402
from modules.rule_compiler.schema import (                        # noqa: E402
    BINDING_LADDER,
    Binding,
    Form,
    Rule,
    binding_coverage,
    find_boilerplate_stops,
    read_binding,
    validate,
)

# Pinned at the boundary BEFORE the change, not re-derived from the state
# being judged -- a reference computed after the edit cannot witness a loss
# (`feedback_reference_derived_from_post_state`).
BASELINE_VALID = 149
BASELINE_REJECTED = 13
DIGEST_CAP = 4096

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"[PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {diagnostic}")


def _check(gate: str, cond: bool, ok: str, bad: str) -> None:
    _ok(gate, ok) if cond else _fail(gate, bad)


# --------------------------------------------------------------------- Rc1
def t_ladder() -> None:
    bad = []
    for b in BINDING_LADDER:
        for spelling in (b.value, b.value.lower(), b.value.replace("_", "-"),
                         f"  **{b.value}**  ", b.value.replace("_", " ")):
            if read_binding(spelling) is not b:
                bad.append(f"{spelling!r}->{read_binding(spelling).value}")
    _check("V-RC1-LADDER", not bad,
           f"{len(BINDING_LADDER)} levels round-trip across 5 spellings each",
           f"misread: {bad[:5]}")


def t_undeclared_not_rejection() -> None:
    good = Rule(rule_id="HR-T1", title="Never deploy without a green suite",
                form=Form.FIELDED, source="t",
                trigger="about to deploy to a live production substrate",
                stop="STOP and run the suite first", evidence="incident 2026-01-01")
    validate(good, frozenset())
    # Negative direction: a real defect must still reject, or the gate is inert.
    broken = Rule(rule_id="HR-T2", title="x", form=Form.FIELDED, source="t",
                  trigger="", stop="", evidence="")
    validate(broken, frozenset())
    _check("V-RC1-UNDECLARED-NOT-REJECTION",
           good.valid and good.binding is Binding.UNDECLARED and not broken.valid,
           "a rule declaring no enforcement stays valid; a malformed rule "
           "still rejects",
           f"good.valid={good.valid} binding={good.binding.value} "
           f"broken.valid={broken.valid}")


def t_unrecognized_distinct() -> None:
    _check("V-RC1-UNRECOGNIZED-DISTINCT",
           read_binding("banana") is Binding.UNRECOGNIZED
           and read_binding("") is Binding.UNDECLARED
           and read_binding("   ") is Binding.UNDECLARED
           and Binding.UNRECOGNIZED not in BINDING_LADDER
           and Binding.UNDECLARED not in BINDING_LADDER,
           "present-but-unknown stays apart from absent; neither is on the ladder",
           f"banana->{read_binding('banana').value} "
           f"empty->{read_binding('').value}")


def t_parse_aliases(tmp: Path) -> None:
    archive = tmp / "HARD_RULES.md"
    archive.write_text(
        "### HR-A1 -- Never ship without evidence\n"
        "TRIGGER: about to declare a build complete\n"
        "STOP: run the suite\n"
        "EVIDENCE: incident A\n"
        "ENFORCEMENT: BLOCK_DEPLOY\n\n"
        "### HR-A2 -- Never rotate a key silently\n"
        "TRIGGER: about to rotate a live credential\n"
        "STOP: ask the Owner\n"
        "EVIDENCE: incident B\n"
        "ENFORCEMENT_LEVEL: REQUIRE_HUMAN_AUTHORIZATION\n\n"
        "### HR-A3 -- Never widen scope quietly\n"
        "TRIGGER: about to touch a file outside the declared scope\n"
        "STOP: pause and re-confirm\n"
        "EVIDENCE: incident C\n"
        "BINDING: warn\n\n"
        "### HR-A4 -- Never assume an API exists\n"
        "TRIGGER: about to code against an unverified signature\n"
        "STOP: read the real source\n"
        "EVIDENCE: incident D\n"
        "NIVEL: advisory\n",
        encoding="utf-8", newline="\n")
    rules = {r.rule_id: r for r in parse_archive(archive, "t")}
    want = {
        "HR-A1": Binding.BLOCK_DEPLOY,
        "HR-A2": Binding.REQUIRE_HUMAN_AUTHORIZATION,
        "HR-A3": Binding.WARN,
        "HR-A4": Binding.ADVISORY,
    }
    bad = [f"{rid}->{rules[rid].binding.value}" for rid, exp in want.items()
           if rid not in rules or rules[rid].binding is not exp]
    # The alias must not eat the fields around it: EVIDENCE stays intact.
    ev_ok = all(rules[rid].evidence.startswith("incident") for rid in want
                if rid in rules)
    _check("V-RC1-PARSE", not bad and ev_ok,
           "ENFORCEMENT / ENFORCEMENT_LEVEL / BINDING / NIVEL all parse, and "
           "the longest-first alternation leaves neighbouring fields intact",
           f"misparsed={bad} evidence_intact={ev_ok}")


def t_coverage_absolute() -> None:
    rules = [
        Rule("HR-C1", "t", Form.FIELDED, "t", enforcement="BLOCK_BUILD"),
        Rule("HR-C2", "t", Form.FIELDED, "t", enforcement=""),
        Rule("HR-C3", "t", Form.FIELDED, "t", enforcement="nonsense"),
    ]
    cov = binding_coverage(rules)
    floats = [k for k, v in cov.items() if isinstance(v, float)]
    _check("V-RC1-COVERAGE-ABSOLUTE",
           cov["declared"] == ["HR-C1"] and cov["undeclared"] == ["HR-C2"]
           and cov["unrecognized"] == ["HR-C3"] and cov["total"] == 3
           and not floats,
           "named id lists and integer counts; no ratio key exists to be "
           "satisfied by deleting an undeclared rule",
           f"cov={cov} floats={floats}")


def t_corpus_unbroken() -> None:
    """Enforcement must not participate in validity, at ANY corpus size.

    The first version of this gate pinned valid==149. That is a tripwire
    for the wrong event: this repo has concurrent panes sealing rules, so
    the corpus legitimately grows between sessions and the gate would go
    red on someone else's correct commit. A gate that cries wolf on valid
    work is uninstalled by the third false alarm.

    The invariant that actually needed protecting is that adding the field
    changed nothing about which rules bind. That is provable directly:
    validate the live corpus twice, once as-is and once with `enforcement`
    stripped, and require identical verdicts. It holds at 149 rules and at
    500, and it fails loudly if `validate` ever starts reading the field.
    """
    from dataclasses import replace
    res = compile_rules()
    with_field = {r.rule_id: r.valid for r in res.valid + res.rejected}

    stripped = [replace(r, enforcement="", rejections=[])
                for r in res.valid + res.rejected]
    boiler = find_boilerplate_stops(stripped)
    for r in stripped:
        validate(r, boiler)
    without = {r.rule_id: r.valid for r in stripped}

    diverged = sorted(rid for rid in with_field
                      if with_field[rid] != without.get(rid))
    _check("V-RC1-CORPUS-UNBROKEN",
           not diverged and len(with_field) == len(without),
           f"validity identical with and without the enforcement field "
           f"across {len(with_field)} rules "
           f"(valid={len(res.valid)} rejected={len(res.rejected)}; "
           f"baseline at build time was "
           f"{BASELINE_VALID}/{BASELINE_REJECTED})",
           f"validity diverged for {diverged[:5]} -- `validate` is reading "
           f"the enforcement field, which would let an undeclared rule be "
           f"denied the ability to fire")


def t_digest_budget() -> None:
    res = compile_rules()
    _check("V-RC1-DIGEST-BUDGET",
           res.digest_bytes <= DIGEST_CAP and res.within_budget,
           f"{res.digest_bytes} B <= {DIGEST_CAP} B cap",
           f"{res.digest_bytes} B exceeds {DIGEST_CAP} -- the kill switch "
           f"would be unreadable again")


def t_digest_reports_binding() -> None:
    """The section must appear when undeclared rules exist AND vanish when
    they do not. A banner that is always on stops being read."""
    undeclared = [Rule("HR-D1", "t", Form.FIELDED, "t", trigger="deploy")]
    declared = [Rule("HR-D2", "t", Form.FIELDED, "t", trigger="deploy",
                     enforcement="BLOCK_DEPLOY")]
    on, _ = build_digest(undeclared, [], "cli")
    off, _ = build_digest(declared, [], "cli")
    _check("V-RC1-DIGEST-REPORTS-BINDING",
           "NOT DECLARED" in on and "NOT DECLARED" not in off
           and "BLOCK_DEPLOY=1" in off,
           "the defect section appears with undeclared rules and disappears "
           "without them; the distribution replaces it",
           f"on={'NOT DECLARED' in on} off={'NOT DECLARED' in off}")


def t_digest_cli_anchor_resolves() -> None:
    """The digest points at `--binding`. A digest naming a command that does
    not exist is the broken-anchor defect this package was born from."""
    res = compile_rules()
    from tools.hardrule_compile import main as cli_main
    referenced = "--binding" in res.digest_text
    try:
        code = cli_main(["--binding"])
        runs = code in (0, 1)
    except SystemExit as e:            # argparse rejects an unknown flag
        runs = False
        code = e.code
    _check("V-RC1-DIGEST-CLI-ANCHOR",
           referenced and runs,
           f"the digest names --binding and the CLI accepts it (exit {code})",
           f"referenced={referenced} runs={runs} -- the digest points at a "
           f"command that does not resolve")


# --------------------------------------------------------------------- Rc2
def _plant(tmp: Path) -> Path:
    root = tmp / "estate"
    (root / "modules" / "alpha").mkdir(parents=True)
    (root / "modules" / "beta").mkdir(parents=True)
    (root / "tools").mkdir(parents=True)
    # A detector: names a family twice-over and defines a detect verb.
    (root / "modules" / "alpha" / "watch.py").write_text(
        "# handles schema drift\n"
        "def detect_schema_drift(a, b):\n    return a != b\n",
        encoding="utf-8", newline="\n")
    # Second file naming the same family -> clears the recurrence gate.
    (root / "modules" / "beta" / "notes.md").write_text(
        "schema drift matters here too\n", encoding="utf-8", newline="\n")
    # A one-file term -> must be dropped as prose.
    (root / "modules" / "beta" / "solo.md").write_text(
        "unicorn drift was mentioned once\n", encoding="utf-8", newline="\n")
    # A test that mentions drift and defines a check verb -> NOT a detector.
    (root / "tools" / "test_alpha.py").write_text(
        "# schema drift\ndef check_drift():\n    return True\n",
        encoding="utf-8", newline="\n")
    return root


def t_rc2_discovered(root: Path) -> None:
    rep = scan(root)
    paths = {d["path"] for d in rep["detectors"]}
    _check("V-RC2-DISCOVERED",
           rep["verdict"] == "SCANNED"
           and "modules/alpha/watch.py" in paths,
           "a detector planted in a temp tree is found by walking, with no "
           "path appearing in the module's source",
           f"verdict={rep['verdict']} detectors={sorted(paths)}")


def t_rc2_recurrence(root: Path) -> None:
    rep = scan(root)
    _check("V-RC2-RECURRENCE",
           "schema" in rep["families"]
           and "unicorn" in rep["singletons_discarded"]
           and "unicorn" not in rep["families"],
           "a term in 2 files is a family; a term in 1 file is dropped as "
           "prose and remains retrievable, not silently deleted",
           f"families={sorted(rep['families'])} "
           f"singletons={rep['singletons_discarded']}")


def t_rc2_excludes_tests(root: Path) -> None:
    rep = scan(root)
    paths = {d["path"] for d in rep["detectors"]}
    excluded = {e["path"] for e in rep["excluded_from_detectors"]}
    _check("V-RC2-EXCLUDES-TESTS",
           "tools/test_alpha.py" in excluded
           and "tools/test_alpha.py" not in paths,
           "a test exercising a detector is excluded from the detector set, "
           "with the reason stated rather than dropped",
           f"detectors={sorted(paths)} excluded={sorted(excluded)}")


def t_rc2_empty_is_verdict(tmp: Path) -> None:
    empty = tmp / "empty"
    (empty / "modules").mkdir(parents=True)
    rep = scan(empty)
    _check("V-RC2-EMPTY-IS-A-VERDICT",
           rep["verdict"] == "NO_DETECTORS_FOUND"
           and "NO_DETECTORS_FOUND is a verdict" in render(rep),
           "an empty walk returns NO_DETECTORS_FOUND and says so in prose, "
           "never an empty pass",
           f"verdict={rep['verdict']}")


def t_rc2_no_uncovered_claim(root: Path) -> None:
    rep = scan(root)
    text = render(rep)
    bad_keys = [k for k in rep if "uncovered" in k.lower()]
    _check("V-RC2-NO-UNCOVERED-CLAIM",
           not bad_keys and "cannot witness" in text
           and "undetected_families" in rep,
           "no 'uncovered families' verdict is emitted; the report states "
           "what it cannot witness",
           f"bad_keys={bad_keys}")


def t_rc2_curated_labelled(root: Path) -> None:
    rep = scan(root)
    text = render(rep, curated=["schema", "phlogiston"])
    _check("V-RC2-CURATED-LABELLED",
           "MEASURES MEMORY" in text and "phlogiston" in text
           and "phlogiston" not in rep["families"],
           "a hand-supplied expectation list is labelled memory-measuring "
           "and kept out of the discovered sets",
           "curated list was merged or unlabelled")


def t_rc2_finds_real_detectors() -> None:
    rep = scan(PP_ROOT)
    paths = {d["path"] for d in rep["detectors"]}
    want = "modules/setup_os/drift_detector.py"
    _check("V-RC2-FINDS-KNOWN",
           want in paths and len(rep["detectors"]) >= 5,
           f"the live walk finds {len(rep['detectors'])} detectors including "
           f"{want}, by discovery",
           f"{want} in paths={want in paths}; found {len(rep['detectors'])}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="egcc_residue_"))
    try:
        root = _plant(tmp)
        t_ladder()
        t_undeclared_not_rejection()
        t_unrecognized_distinct()
        t_parse_aliases(tmp)
        t_coverage_absolute()
        t_corpus_unbroken()
        t_digest_budget()
        t_digest_reports_binding()
        t_digest_cli_anchor_resolves()
        t_rc2_discovered(root)
        t_rc2_recurrence(root)
        t_rc2_excludes_tests(root)
        t_rc2_empty_is_verdict(tmp)
        t_rc2_no_uncovered_claim(root)
        t_rc2_curated_labelled(root)
        t_rc2_finds_real_detectors()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = _passes + _fails
    print(f"\nEGCC_RESIDUE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
