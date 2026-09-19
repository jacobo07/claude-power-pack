#!/usr/bin/env python3
"""Probe evidence gates -- UCR-CIF W4.

Two capabilities sat UNKNOWN because their retirement condition could not be
measured. This file proves what the two probes that now cover them can and
cannot say, at every pole, because a probe that feeds lifecycle authority is
not judged by whether it returns an answer -- it is judged by whether it could
have returned the OTHER one.

Two properties are load-bearing and each has its own gate:

  * `probe_cdicf_installer` is new. Its three worlds -- redundancy realised,
    installer still guaranteeing, and cannot-judge -- must be reachable from
    real repository shapes, and an absent root must never read as absence of
    the subject (kernel vMAX-NULL-ERROR).

  * `probe_spec_depth_selection` already existed and could only ever answer
    UNEVALUABLE on this estate: its sample floor (200) sat AHEAD of the hit
    scan while the real incident corpus holds 99 records. The floor is correct
    and is untouched; its PLACEMENT was the defect. The pair
    V-PROBE-SPEC-PRESENCE-BEATS-FLOOR / V-PROBE-SPEC-ZERO-STILL-FLOORED is
    what separates fixing the instrument from buying a verdict, and the second
    gate is the one that fails if anyone later lowers the floor to close the
    UNKNOWN population.

Run: python tools/test_capability_probe_evidence.py   (exit 0 = all green)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.capability_runtime import retirement as R  # noqa: E402
from modules.capability_runtime.contract import load_contracts  # noqa: E402

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


# --------------------------------------------------------------------------- #
# Fixtures. Built on disk, owned and deleted by the test -- never the estate's
# own files (a destructive fixture over real data is unrecoverable by revert).
# --------------------------------------------------------------------------- #
_GUARANTEED_INSTALLER = (
    "// journalled installer\n"
    "const j = path.join(root, 'journal.json');\n"
    "function recover(target) { /* restores prior sha */ }\n"
    "const rec = { provenance: im.provenance, checksum: im.checksum };\n"
)


def _estate(td: str, *, installer: str | None = _GUARANTEED_INSTALLER,
            consumer: bool = True, module_dir: bool = True) -> Path:
    root = Path(td)
    if module_dir:
        (root / "modules" / "cdicf").mkdir(parents=True, exist_ok=True)
        if installer is not None:
            (root / "modules" / "cdicf" / "installer.js").write_text(
                installer, encoding="utf-8")
    (root / "tools").mkdir(parents=True, exist_ok=True)
    if consumer:
        (root / "tools" / "design_index.py").write_text(
            "rec = os.path.join(project_dir, '.cdicf', 'installed.json')\n",
            encoding="utf-8")
    return root


def _incidents(td: str, n: int, omissions: int = 0) -> Path:
    root = Path(td)
    d = root / "vault" / "osa"
    d.mkdir(parents=True, exist_ok=True)
    lines = []
    for i in range(n):
        note = "shipped without a spec" if i < omissions else "unrelated incident"
        lines.append(json.dumps({"note": note}) + "\n")
    (d / "never_again_log.jsonl").write_text("".join(lines), encoding="utf-8")
    return root


# --------------------------------------------------------------------------- #
# cdicf-installer.
# --------------------------------------------------------------------------- #
def t_cdicf_real_estate() -> None:
    """The negative pole against the REAL repository, not a fixture. A probe
    only tested on shapes the author invented has been tested against a world
    the author already believed in."""
    gate = "V-PROBE-CDICF-REAL-NOT-REDUNDANT"
    met, ev = R.probe_cdicf_installer(_ROOT)
    consumers = R._cdicf_provenance_consumers(_ROOT)
    if met is False and consumers:
        _ok(gate, f"{ev[:96]}… ({len(consumers)} consumer(s) discovered)")
    else:
        _fail(gate, f"met={met} consumers={len(consumers)} ev={ev[:120]}")


def t_cdicf_retire_pole() -> None:
    gate = "V-PROBE-CDICF-RETIRE-REACHABLE"
    with tempfile.TemporaryDirectory() as td:
        met, ev = R.probe_cdicf_installer(_estate(td, installer=None))
    if met is True:
        _ok(gate, f"cdicf module present with no installer -> retire ({ev[:60]}…)")
    else:
        _fail(gate, f"met={met} ev={ev}")


def t_cdicf_guarantee_gap() -> None:
    """An installer that copies bytes is not the subject of this condition.
    Missing a named guarantee is a contract/reality disagreement, which is not
    a verdict about retirement in either direction."""
    gate = "V-PROBE-CDICF-GUARANTEE-GAP"
    with tempfile.TemporaryDirectory() as td:
        root = _estate(td, installer="// copies files\nfs.copyFileSync(a, b);\n")
        met, ev = R.probe_cdicf_installer(root)
    if met is None and "transaction" in ev and "recovery" in ev:
        _ok(gate, "installer without journal/provenance/recovery -> cannot "
                  "judge, and the missing mechanisms are named")
    else:
        _fail(gate, f"met={met} ev={ev}")


def t_cdicf_no_consumer() -> None:
    gate = "V-PROBE-CDICF-UNOBSERVED-GUARANTEE"
    with tempfile.TemporaryDirectory() as td:
        met, ev = R.probe_cdicf_installer(_estate(td, consumer=False))
    if met is None and "no production file" in ev:
        _ok(gate, "guarantees present but nothing reads the record -> cannot "
                  "judge, never a silent 'still needed'")
    else:
        _fail(gate, f"met={met} ev={ev[:120]}")


def t_cdicf_absent_root_is_not_absence() -> None:
    """ABSENT != RETIRED. A root that cannot see the module must not report
    that the installer became redundant."""
    gate = "V-PROBE-CDICF-ABSENT-ROOT-NOT-RETIRED"
    with tempfile.TemporaryDirectory() as td:
        met, ev = R.probe_cdicf_installer(_estate(td, module_dir=False))
    if met is None:
        _ok(gate, f"no modules/cdicf -> cannot conclude, not retire ({ev[:56]}…)")
    else:
        _fail(gate, f"met={met} ev={ev}")


def t_cdicf_consumer_excludes_tests() -> None:
    """A test reading the record proves the record is testable. It is not
    evidence that anything depends on it."""
    gate = "V-PROBE-CDICF-TEST-IS-NOT-A-CONSUMER"
    with tempfile.TemporaryDirectory() as td:
        root = _estate(td, consumer=False)
        (root / "tools" / "test_cdicf_index.py").write_text(
            "rec = os.path.join(proj, '.cdicf', 'installed.json')\n",
            encoding="utf-8")
        met, _ = R.probe_cdicf_installer(root)
        found = R._cdicf_provenance_consumers(root)
    if met is None and not found:
        _ok(gate, "a test_* reader is not counted as a production consumer")
    else:
        _fail(gate, f"met={met} consumers={found}")


def t_cdicf_determinism() -> None:
    gate = "V-PROBE-CDICF-DETERMINISM"
    a = R.probe_cdicf_installer(_ROOT)
    b = R.probe_cdicf_installer(_ROOT)
    if a == b:
        _ok(gate, "two consecutive runs over the real estate are identical")
    else:
        _fail(gate, f"{a} != {b}")


# --------------------------------------------------------------------------- #
# spec_depth_selection -- floor placement.
# --------------------------------------------------------------------------- #
def t_spec_presence_beats_floor() -> None:
    """The blind spot. One incident is one incident: presence is positive
    evidence the condition has NOT come true and is not weakened by a small
    denominator. Reverting the order fails exactly here."""
    gate = "V-PROBE-SPEC-PRESENCE-BEATS-FLOOR"
    n = R._MIN_INCIDENT_SAMPLE // 4
    with tempfile.TemporaryDirectory() as td:
        met, ev = R.probe_spec_depth_selection(_incidents(td, n, omissions=1))
    if met is False:
        _ok(gate, f"1 spec-omission entry over {n} records (< floor "
                  f"{R._MIN_INCIDENT_SAMPLE}) -> stays ACTIVE ({ev[:50]}…)")
    else:
        _fail(gate, f"met={met} ev={ev}")


def t_spec_zero_still_floored() -> None:
    """The control that makes the gate above a fix rather than a purchase. A
    zero under the floor must still refuse to retire the guard."""
    gate = "V-PROBE-SPEC-ZERO-STILL-FLOORED"
    n = R._MIN_INCIDENT_SAMPLE // 4
    with tempfile.TemporaryDirectory() as td:
        met, ev = R.probe_spec_depth_selection(_incidents(td, n, omissions=0))
    if met is None and str(n) in ev:
        _ok(gate, f"0 entries over {n} records -> still UNEVALUABLE; the floor "
                  "was not lowered to close a population")
    else:
        _fail(gate, f"met={met} ev={ev}")


def t_spec_retire_pole_reachable() -> None:
    gate = "V-PROBE-SPEC-RETIRE-REACHABLE"
    n = R._MIN_INCIDENT_SAMPLE + 5
    with tempfile.TemporaryDirectory() as td:
        met, _ = R.probe_spec_depth_selection(_incidents(td, n, omissions=0))
    if met is True:
        _ok(gate, f"0 entries over {n} records (>= floor) -> retire")
    else:
        _fail(gate, f"met={met}")


def t_spec_real_estate_states_both_numbers() -> None:
    """An abstention is only actionable if it names what is missing. "Cannot
    conclude" sends someone to check everything; "0 hits, 99 of 200 records"
    names the one fact that would resolve it."""
    gate = "V-PROBE-SPEC-ABSTENTION-IS-NAMED"
    met, ev = R.probe_spec_depth_selection(_ROOT)
    if met is None and "0 spec-omission" in ev and str(R._MIN_INCIDENT_SAMPLE) in ev:
        _ok(gate, f"real estate -> {ev}")
    elif met is False:
        _ok(gate, f"real estate now carries a spec-omission entry -> ACTIVE: {ev}")
    else:
        _fail(gate, f"met={met} ev={ev}")


# --------------------------------------------------------------------------- #
# Population. A zero-target metric needs a population proved independently of
# the list that claims it (T-EXCLUSION-MATCHED-THE-WORKSPACE-001).
# --------------------------------------------------------------------------- #
def t_population_independent() -> None:
    gate = "V-PROBE-POPULATION-INDEPENDENT"
    contracts = load_contracts()
    ids = sorted(c.id for c in contracts)
    if len(ids) != len(set(ids)):
        _fail(gate, f"duplicate contract ids in the store: {ids}")
        return
    if len(ids) < 8:
        _fail(gate, f"only {len(ids)} contract(s) discovered -- the store sweep "
                    "may have stopped seeing files")
        return
    verdicts = {v.contract_id for v in R.evaluate_all()}
    if verdicts != set(ids):
        _fail(gate, f"evaluated set != contract set: "
                    f"{sorted(verdicts ^ set(ids))}")
        return
    _ok(gate, f"{len(ids)} contracts discovered from the store, every one "
              "evaluated, no duplicates, no extras")


def t_unresolved_are_named() -> None:
    """No anonymous unresolved pile: every capability the probes cannot settle
    carries a reason and, where one exists, the fact that would resolve it."""
    gate = "V-PROBE-NO-ANONYMOUS-UNRESOLVED"
    unresolved = [v for v in R.evaluate_all()
                  if v.status in (R.UNEVALUABLE, R.NO_CONDITION)]
    blank = [v.contract_id for v in unresolved if len(v.evidence.strip()) < 20]
    if blank:
        _fail(gate, f"unresolved with no usable reason: {blank}")
        return
    _ok(gate, f"{len(unresolved)} unresolved: "
              + "; ".join(f"{v.contract_id}={v.evidence[:44]}…"
                          for v in unresolved))


def main() -> int:
    for fn in (t_cdicf_real_estate, t_cdicf_retire_pole, t_cdicf_guarantee_gap,
               t_cdicf_no_consumer, t_cdicf_absent_root_is_not_absence,
               t_cdicf_consumer_excludes_tests, t_cdicf_determinism,
               t_spec_presence_beats_floor, t_spec_zero_still_floored,
               t_spec_retire_pole_reachable,
               t_spec_real_estate_states_both_numbers,
               t_population_independent, t_unresolved_are_named):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 -- a harness failure is not a finding
            _fail(f"HARNESS-FAILED:{fn.__name__}", f"{type(exc).__name__}: {exc}")
    total = _passes + _fails
    print(f"PROBE_EVIDENCE_PASS={_passes}/{total}  threshold={total}/{total}  "
          f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
