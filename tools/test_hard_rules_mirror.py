"""V-HRM-* gates: the CLAUDE.md HARD RULES mirror carries no stub entries.

Run from the repo root: python tools/test_hard_rules_mirror.py
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP_ROOT))

from modules.hard_rules import writer as W  # noqa: E402

passes = 0
fails = 0

REAL_IDS = [
    *(f"HR-SECRET-00{i}" for i in range(1, 8)),
    *(f"HR-CASCADE-00{i}" for i in range(1, 6)),
    *(f"HR-OUTPUT-00{i}" for i in range(1, 4)),
    *(f"HR-ONESHOT-00{i}" for i in range(1, 4)),
    *(f"HR-COST-00{i}" for i in range(1, 4)),
    *(f"HR-BACKLOG-00{i}" for i in range(1, 4)),
    "HR-PREMISE-001", "HR-SPEC-001", "HR-CONTEXT-001",
    "HR-STALLED-SESSION-ADVISORY-001", "HR-NOVELTY-001",
]

STUB_ENTRY = (
    "### HR-009 -- Some Heading\n"
    "TRIGGER: Before: Some Heading 2026-05-26\n"
    "STOP: STOP. Verify preconditions in writing. Document what you are "
    "about to do. Get explicit confirmation if any step is irreversible.\n"
    "EVIDENCE: [session_lessons] Some Heading\n"
    "SEVERITY: CRITICAL | RECURRENCE: 1x\n"
    "<!-- digest:0000000000000001 -->\n"
)
TEST_ENTRY = (
    "### HR-010 -- Test Critical Bug For Auto-propose Pipeline\n"
    "TRIGGER: Test recognizer for pipeline\n"
    "STOP: Run auto_HR-010 proposal drafting\n"
    "EVIDENCE: [never_again] TEST CRITICAL bug for auto-propose pipeline ZZZ\n"
    "SEVERITY: CRITICAL | RECURRENCE: 1x\n"
)
REAL_ENTRY = (
    "### HR-FIXTURE-001 -- Real rule\n"
    "TRIGGER: About to stage a file named `.env*`.\n"
    "STOP: Verify .gitignore excludes the path BEFORE staging.\n"
    "EVIDENCE: [fixture] a real incident\n"
    "SEVERITY: HIGH | RECURRENCE: 0x\n"
)


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {diagnostic}")


def _block_ids(text: str) -> list[str]:
    _, _, inner = W._extract_block(text)
    return re.findall(r"^###\s+(HR-\S+)", inner, re.MULTILINE)


def main() -> int:
    claude = (PP_ROOT / "CLAUDE.md").read_text(encoding="utf-8-sig")
    ids = _block_ids(claude)
    _, _, inner = W._extract_block(claude)

    # Positive control: the block parsed and holds rules at all.
    if len(ids) >= len(REAL_IDS):
        _ok("V-HRM-BLOCK-PARSED", f"{len(ids)} rule ids in the mirror")
    else:
        _fail("V-HRM-BLOCK-PARSED", f"only {len(ids)} ids parsed")

    if "auto-propose pipeline" not in inner and "HR-002" not in ids:
        _ok("V-HRM-NO-TEST-ENTRY", "HR-002 pipeline test entry absent")
    else:
        _fail("V-HRM-NO-TEST-ENTRY", "HR-002 test entry still in the mirror")

    _, entries = W._split_entries(inner)
    stubs = [(rid, W.stub_reason(e)) for rid, e in entries if W.stub_reason(e)]
    if not stubs:
        _ok("V-HRM-NO-STUBS", f"0 stub entries among {len(entries)}")
    else:
        _fail("V-HRM-NO-STUBS", f"stubs remain: {stubs}")

    missing = [r for r in REAL_IDS if r not in ids]
    if not missing:
        _ok("V-HRM-REAL-KEPT", f"all {len(REAL_IDS)} real ids present")
    else:
        _fail("V-HRM-REAL-KEPT", f"missing: {missing}")

    # Both poles on a fixture, through the real prune path.
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "CLAUDE.md"
        p.write_text("# x\n\n" + W.SENTINEL_START + W.HARD_RULES_HEADER
                     + STUB_ENTRY + REAL_ENTRY + TEST_ENTRY
                     + W.SENTINEL_END + "\ntail\n", encoding="utf-8")
        dropped = dict(W.prune_stub_rules(p))
        after = p.read_text(encoding="utf-8")
        kept_ids = _block_ids(after)
    if set(dropped) == {"HR-009", "HR-010"} and "HR-009" not in kept_ids \
            and "HR-010" not in kept_ids:
        _ok("V-HRM-STUB-FILTERED", f"dropped {sorted(dropped)}")
    else:
        _fail("V-HRM-STUB-FILTERED", f"dropped={dropped} kept={kept_ids}")
    if kept_ids == ["HR-FIXTURE-001"] and REAL_ENTRY in after \
            and after.endswith(W.SENTINEL_END + "\ntail\n"):
        _ok("V-HRM-REAL-FIXTURE-KEPT", "real entry byte-identical, tail intact")
    else:
        _fail("V-HRM-REAL-FIXTURE-KEPT", f"kept={kept_ids}")

    print(f"HRM_PASS={passes}/{passes + fails}  threshold=6/6")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
