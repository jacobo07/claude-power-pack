"""V-HRM-* gates: the CLAUDE.md HARD RULES block is a generated projection.

The archive (vault/hard_rules/HARD_RULES.md) is the single authority;
regenerating the mirror from it must be byte-identical to CLAUDE.md's
block, and the mirror carries no stub entries.

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
    "HR-PANE-MAP-FRESHNESS-001", "HR-REVIVAL-LIVENESS-IS-PROCESS-001",
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
MECH_ENTRY = REAL_ENTRY.replace("HR-FIXTURE-001", "HR-FIXTURE-002").replace(
    "[fixture] a real incident", "[fixture] modules/hard_rules/writer.py")
OBSOLETE_ENTRY = REAL_ENTRY.replace("HR-FIXTURE-001", "HR-FIXTURE-003").replace(
    "Real rule", "Real rule (RETIRED 2026-10-07)")


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
    archive = W.DEFAULT_ARCHIVE.read_text(encoding="utf-8-sig")
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

    # Drift: the mirror is exactly what the archive projects to.
    rendered = W.render_mirror_block(archive)
    if rendered == inner:
        _ok("V-HRM-NO-DRIFT", f"block byte-identical to projection "
            f"({len(rendered)} chars)")
    else:
        _fail("V-HRM-NO-DRIFT", "CLAUDE.md block differs from the archive "
              "projection -- run python -m modules.hard_rules.writer --project")

    a_ids = _block_ids(archive)
    orphans = [r for r in ids if r not in a_ids]
    if not orphans:
        _ok("V-HRM-ARCHIVE-AUTHORITY", f"every mirror id in the archive "
            f"({len(a_ids)} archive ids)")
    else:
        _fail("V-HRM-ARCHIVE-AUTHORITY", f"mirror-only ids: {orphans}")

    with tempfile.TemporaryDirectory() as td:
        # Both poles on a fixture, through the real prune path.
        p = Path(td) / "CLAUDE.md"
        p.write_text("# x\n\n" + W.SENTINEL_START + W.HARD_RULES_HEADER
                     + STUB_ENTRY + REAL_ENTRY + TEST_ENTRY
                     + W.SENTINEL_END + "\ntail\n", encoding="utf-8")
        dropped = dict(W.prune_stub_rules(p))
        after = p.read_text(encoding="utf-8")
        kept_ids = _block_ids(after)

        # Projection: drift detected, written, then in sync; prose ahead
        # of the header leaves the block; the mutated mirror goes red.
        arc = Path(td) / "HARD_RULES.md"
        arc.write_text("# a\n\n" + W.SENTINEL_START + W.HARD_RULES_HEADER
                       + REAL_ENTRY + STUB_ENTRY + MECH_ENTRY
                       + W.SENTINEL_END + "\n", encoding="utf-8")
        mir = Path(td) / "M.md"
        mir.write_text("# m\n\n" + W.SENTINEL_START + "\n## Prose\n\nkeep me\n"
                       + W.HARD_RULES_HEADER + REAL_ENTRY + W.SENTINEL_END
                       + "\ntail\n", encoding="utf-8")
        first = W.project_mirror(mir, arc)
        second = W.project_mirror(mir, arc, check=True)
        proj = mir.read_text(encoding="utf-8")
        mutated = proj.replace(MECH_ENTRY, "")
        mir.write_text(mutated, encoding="utf-8")
        red = W.project_mirror(mir, arc, check=True)

        # Ids come from the archive, and stubs are refused.
        arc2 = Path(td) / "A2.md"
        arc2.write_text("# a\n\n" + W.SENTINEL_START + W.HARD_RULES_HEADER
                        + "### HR-007 -- Archive only\nTRIGGER: t\nSTOP: s\n"
                        "EVIDENCE: e\n" + W.SENTINEL_END + "\n",
                        encoding="utf-8")
        new_id = W.append_hard_rule("### HR-NEXT -- New\nTRIGGER: t2\n"
                                    "STOP: s2\nEVIDENCE: e2\n",
                                    Path(td) / "C2.md", arc2)
        try:
            W.append_hard_rule(STUB_ENTRY.replace("HR-009", "HR-NEXT"),
                               Path(td) / "C2.md", arc2)
            refused = False
        except ValueError:
            refused = True
        c2_ids = _block_ids((Path(td) / "C2.md").read_text(encoding="utf-8"))

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
    if first and not second and red and "keep me\n\n" + W.SENTINEL_START in proj \
            and STUB_ENTRY not in proj and proj.endswith("\ntail\n"):
        _ok("V-HRM-PROJECTION", "drift->write->in sync; prose moved out; "
            "deleted rule -> red")
    else:
        _fail("V-HRM-PROJECTION", f"first={first} second={second} red={red}")
    if new_id == "HR-008" and refused and c2_ids == ["HR-007", "HR-008"]:
        _ok("V-HRM-ARCHIVE-IDS", "next id from archive (HR-008); stub refused")
    else:
        _fail("V-HRM-ARCHIVE-IDS", f"id={new_id} refused={refused} ids={c2_ids}")

    labels = {e: W.classify_rule(e) for e in
              (STUB_ENTRY, TEST_ENTRY, REAL_ENTRY, MECH_ENTRY, OBSOLETE_ENTRY)}
    want = ["stub", "test", "judgmental", "mechanical", "obsolete"]
    if list(labels.values()) == want:
        _ok("V-HRM-CLASSIFY", "all five labels reachable")
    else:
        _fail("V-HRM-CLASSIFY", f"{list(labels.values())} != {want}")

    print(f"HRM_PASS={passes}/{passes + fails}  threshold=11/11")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
