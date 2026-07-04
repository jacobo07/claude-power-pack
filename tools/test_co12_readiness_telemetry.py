#!/usr/bin/env python3
"""test_co12_readiness_telemetry.py -- CO-12 dataset done-gate (V-gate convention).

CO-12 is a pure architecture dataset (no code), so these gates assert the dataset's
STRUCTURAL contracts, not runtime behavior: correct id (never CO-09/CO-10), real
parents, a concrete data source per metric, the Telemetry-Before-Claims contract,
zero code fences, index registration, and no regression of the sibling audit suites
(C68/C69/C70) it extends. Hermetic + re-runnable (pure file reads + subprocess).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PP = Path(__file__).resolve().parents[1]
DATASET = (_PP / "vault" / "knowledge_base" / "cognitive_os"
           / "cognitive_os_12_cognitive_readiness_telemetry.md")
INDEX = (_PP / "vault" / "knowledge_base" / "cognitive_os"
         / "COGNITIVE_OS_INDEX.md")

# CO-12 Part II defines 8 metrics, each carrying a "*Source (...)" marker.
EXPECTED_METRIC_SOURCES = 8
# Per-suite wall-clock bound for the no-regression subprocess run.
SIBLING_SUITE_TIMEOUT_S = 180

_passes = 0
_fails = 0


def _ok(gate: str, ev: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {ev}")


def main() -> int:
    if not DATASET.is_file():
        _fail("V-EXISTS", f"dataset missing: {DATASET}")
        print(f"\nCO12_PASS={_passes}/{_passes + _fails}")
        return 1
    text = DATASET.read_text(encoding="utf-8")
    idx = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else ""

    # V-NO-CODE: a pure architecture dataset carries zero fenced code blocks.
    if "```" not in text:
        _ok("V-NO-CODE", "0 fenced code blocks in the dataset")
    else:
        _fail("V-NO-CODE", "dataset contains a ``` code fence")

    # V-CORRECT-IDS: it IS CO-12 and seals C74; it never re-claims CO-09/CO-10.
    is_co12 = text.splitlines()[0].strip().endswith("Cognitive Readiness Telemetry") \
        and "CO-12" in text.splitlines()[0]
    seals_c74 = "SCS C74" in text
    # "never claims to BE CO-09/CO-10": no line seals this dataset as CO-09/CO-10
    mis_seal = any(("Sealed under SCS C61" in ln or "# Cognitive OS — CO-09" in ln
                    or "# Cognitive OS — CO-10" in ln) for ln in text.splitlines())
    if is_co12 and seals_c74 and not mis_seal:
        _ok("V-CORRECT-IDS", "H1=CO-12, seals C74, never re-claims CO-09/CO-10")
    else:
        _fail("V-CORRECT-IDS",
              f"is_co12={is_co12} seals_c74={seals_c74} mis_seal={mis_seal}")

    # V-PARENT-REFS: declares its real parents.
    parents = ["C68", "C69", "C70", "CO-01", "GK-09"]
    missing = [p for p in parents if p not in text]
    if not missing:
        _ok("V-PARENT-REFS", "parents C68/C69/C70 + CO-01 + GK-09 all named")
    else:
        _fail("V-PARENT-REFS", f"missing parent refs: {missing}")

    # V-REALITY-SCAN: positions itself as EXTEND (4th audit axis), not NEW-from-scratch.
    if "EXTEND" in text and "fourth audit axis" in text.lower():
        _ok("V-REALITY-SCAN", "declares EXTEND + 'fourth audit axis' (no duplication)")
    else:
        _fail("V-REALITY-SCAN", "missing EXTEND / fourth-audit-axis positioning")

    # V-TELEMETRY-REAL: every metric names a concrete data source (>=8 markers).
    # Whitespace-normalize first so a prose line-wrap between "*Source" and "("
    # does not hide a real marker (brittle-literal FP, cf. V-SCS-NO-COLLISION).
    n_src = " ".join(text.split()).count("*Source (")
    if n_src >= EXPECTED_METRIC_SOURCES:
        _ok("V-TELEMETRY-REAL", f"{n_src} metrics each name a data source")
    else:
        _fail("V-TELEMETRY-REAL", f"only {n_src} '*Source (' markers (<8)")

    # V-CONTRACT: the Telemetry-Before-Claims contract + the (metric,source,value) triple.
    has_contract = "Telemetry-Before-Claims Contract" in text
    has_triple = "(metric, source, value)" in text or "(metric, data-source, value)" in text
    if has_contract and has_triple:
        _ok("V-CONTRACT", "Telemetry-Before-Claims + (metric,source,value) triple present")
    else:
        _fail("V-CONTRACT", f"contract={has_contract} triple={has_triple}")

    # V-INDEX-REGISTERED: the family index links the dataset.
    if "cognitive_os_12_cognitive_readiness_telemetry.md" in idx and "CO-12" in idx:
        _ok("V-INDEX-REGISTERED", "COGNITIVE_OS_INDEX links CO-12")
    else:
        _fail("V-INDEX-REGISTERED", "index does not register CO-12")

    # V-NO-REGRESSION: the sibling audit suites still pass (CO-12 must not break them).
    siblings = ["test_token_corpus_audit.py", "test_conversation_quality_audit.py",
                "test_cognitive_leak_taxonomy.py"]
    bad = []
    for s in siblings:
        p = _PP / "tools" / s
        if not p.is_file():
            bad.append(f"{s}:missing")
            continue
        try:
            r = subprocess.run([sys.executable, str(p)], capture_output=True,
                               timeout=SIBLING_SUITE_TIMEOUT_S, cwd=str(_PP))
            if r.returncode != 0:
                bad.append(f"{s}:exit{r.returncode}")
        except (subprocess.TimeoutExpired, OSError) as e:
            bad.append(f"{s}:{type(e).__name__}")
    if not bad:
        _ok("V-NO-REGRESSION", "C68 + C69 + C70 suites exit 0")
    else:
        _fail("V-NO-REGRESSION", f"sibling suite issues: {bad}")

    total = _passes + _fails
    print(f"\nCO12_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
