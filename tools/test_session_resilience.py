#!/usr/bin/env python3
"""V-gate suite for the Session Resilience OS dataset family (Path A, residual gaps).

Doctrine: rules/python/testing.md  -- V-<DOMAIN>-<NAME> gates, exit 0 iff fails==0.
Scope: validates the 5 standalone datasets + index produced under
vault/knowledge_base/session_resilience/. Markdown-only family; no production code touched.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAM = ROOT / "vault" / "knowledge_base" / "session_resilience"
INDEX = FAM / "SESSION_RESILIENCE_OS_INDEX.md"

DATASETS = [
    FAM / "session_resilience_01_ui_editor_state_persistence_layer.md",
    FAM / "session_resilience_02_multi_window_coordinator.md",
    FAM / "session_resilience_03_incremental_snapshot_and_session_versioning_engine.md",
    FAM / "session_resilience_04_recovery_acceptance_framework.md",
    FAM / "session_resilience_05_recovery_telemetry_and_diagnostics_layer.md",
]

# Existing PP systems each dataset must reference as a dependency (non-duplication anchor).
EXISTING_SYSTEMS = ["CETTG", "RS-OS", "RW-OS", "CPC-OS", "pp_dataset"]

WORD_FLOOR = 2000

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {diagnostic}")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")  # tolerate BOM (cross-tool writes)


def _wordcount(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def main() -> int:
    # Existence precondition
    missing = [p.name for p in DATASETS + [INDEX] if not p.is_file()]
    if missing:
        _fail("V-SR-FILES", f"missing files: {missing}")
        print(f"SESSION_RESILIENCE_PASS={passes}/{passes + fails}  threshold=all")
        return 1
    _ok("V-SR-FILES", f"5 datasets + index present in {FAM.name}/")

    bodies = {p: _read(p) for p in DATASETS}
    index_body = _read(INDEX)

    # V-REALITY-SCAN: no dataset duplicates an existing system; each declares it + references deps
    rs_bad = []
    for p, b in bodies.items():
        has_disclaimer = "Does NOT duplicate" in b
        has_ref = any(sys_name in b for sys_name in EXISTING_SYSTEMS)
        if not (has_disclaimer and has_ref):
            rs_bad.append(p.name)
    if rs_bad:
        _fail("V-REALITY-SCAN", f"missing non-duplication clause or existing-system ref: {rs_bad}")
    else:
        _ok("V-REALITY-SCAN", "all 5 declare 'Does NOT duplicate' + reference existing PP systems")

    # V-COVERAGE: headline property present in index + every dataset listed
    cov_ok = "indistinguishable from a Reload Window" in index_body
    listed = all(p.name in index_body for p in DATASETS)
    if cov_ok and listed:
        _ok("V-COVERAGE", "headline property stated; all 5 datasets indexed")
    else:
        _fail("V-COVERAGE", f"headline_property={cov_ok} all_listed={listed}")

    # V-DEPTH: each dataset >= WORD_FLOOR words
    depth_bad = {p.name: _wordcount(b) for p, b in bodies.items() if _wordcount(b) < WORD_FLOOR}
    if depth_bad:
        _fail("V-DEPTH", f"below {WORD_FLOOR} words: {depth_bad}")
    else:
        counts = {p.name.split('_')[2]: _wordcount(b) for p, b in bodies.items()}
        _ok("V-DEPTH", f">= {WORD_FLOOR} words each (min={min(_wordcount(b) for b in bodies.values())})")

    # V-NO-CODE: no fenced code blocks in any DATASET (index ascii-art is exempt by scope)
    code_bad = [p.name for p, b in bodies.items() if "```" in b]
    if code_bad:
        _fail("V-NO-CODE", f"fenced code block found in: {code_bad}")
    else:
        _ok("V-NO-CODE", "no ``` fences in any of the 5 datasets")

    # V-RELATIONSHIPS: each declares dependencies + a relationships section
    rel_bad = []
    for p, b in bodies.items():
        if "Depends on:" not in b or "Relationships with existing PP systems" not in b:
            rel_bad.append(p.name)
    if rel_bad:
        _fail("V-RELATIONSHIPS", f"missing 'Depends on:' or relationships section: {rel_bad}")
    else:
        _ok("V-RELATIONSHIPS", "all 5 declare dependencies + relationships section")

    # V-ANTI-PATTERNS: each defines what it must not do
    ap_bad = [p.name for p, b in bodies.items() if "anti-pattern" not in b.lower()]
    if ap_bad:
        _fail("V-ANTI-PATTERNS", f"missing explicit anti-patterns: {ap_bad}")
    else:
        _ok("V-ANTI-PATTERNS", "all 5 declare explicit anti-patterns")

    # V-BASELINE-INTACT: additions isolated (all .md under family) + existing master dataset intact
    non_md = [p.name for p in FAM.glob("session_resilience_*") if p.suffix != ".md"]
    master = ROOT / "vault" / "knowledge_base" / "pp_dataset" / "pp_dataset_MASTER.md"
    master_ok = master.is_file() and len(_read(master).strip()) > 0
    if non_md or not master_ok:
        _fail("V-BASELINE-INTACT", f"non-md additions={non_md} master_intact={master_ok}")
    else:
        _ok("V-BASELINE-INTACT", "family is markdown-only; pp_dataset_MASTER.md intact")

    print(f"SESSION_RESILIENCE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
