"""Reconcile the corpus this estate ENFORCES against the corpus it COMPILES.

`parser.load_corpus()` reads exactly two archives. The rules that actually fire
are largely in neither: measured 2026-08-07, 418 `HR-` ids are named across the
estate and 16 of them compile. `HR-SECRET-001`, `HR-CASCADE-001` and
`HR-PREMISE-001` are each enforced by a live hook and absent from the compiled
corpus, so the digest the router consults at every trigger point does not carry
them.

`verify_hard_rules.py` H7 cannot see this. It asserts that the sentinel MARKERS
are present in one of two files; both files carry them, and their contents share
9 of 42 ids. Marker presence and block agreement are different properties.

Two reconciliations live here, kept apart because they answer different
questions:

  R-A  mirror vs archive   -- which authored block holds which rule
  R-B  enforced vs compiled -- which fired rule never reaches the compiler

Nothing is enumerated. The id set is discovered by walking disk, because a
registry enrolled by hand measures what someone remembered: an undeclared
subject is not scored UNKNOWN, it is absent from the denominator, and absence
reads as health (PR-COVERAGE-BY-CONSTRUCTION-001).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
MIRROR = PP_ROOT / "CLAUDE.md"
ARCHIVE = PP_ROOT / "vault" / "hard_rules" / "HARD_RULES.md"

SENTINEL_START = "<!-- PP-HARD-RULES-START -->"
SENTINEL_END = "<!-- PP-HARD-RULES-END -->"

# Where a rule can be named. `hooks/` is listed like any other directory; what
# makes it special is read from the path at classification time, not from a
# separate scan, so the two can never fall out of step.
#
# `vault/` is deliberately absent. It holds the compiled artefacts, which
# restate every id by definition and would let the corpus vouch for its own
# coverage, and the plans and datasets that discuss rules in prose -- including
# the audit that produced this module, which would otherwise inflate the very
# counts it reported. The scope here is the surface that EXECUTES rules. A
# wider walk including `vault/` and `knowledge/` finds 418 named ids
# (EGCC_EXPANSION_DENOMINATOR.md); this narrower one finds fewer, and the
# difference is prose, not enforcement.
SCAN_DIRS = ("modules", "tools", "commands", "governance", "hooks", "agents")
SCAN_SUFFIXES = (".md", ".py", ".js", ".json")
SKIP_PARTS = {"__pycache__", "node_modules", ".git", ".venv"}

# The recurrence threshold, stated once. An id written in a single file is one
# author's line; written in two, the estate refers to it. This is the same
# measured instrument `find_boilerplate_stops` uses to call an ACTION filler and
# `drift_registry` uses to let a term earn a family name -- reused rather than
# reinvented, so all three move together if it is ever wrong.
MIN_FILES_FOR_REAL = 2

# Same shape as parser._HEADING_RE's id group: internal hyphens are part of the
# id (HR-SECRET-001), so the match must not stop at the first one.
_ID_RE = re.compile(r"\bHR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
_HEADING_RE = re.compile(
    r"^#{3,4}\s+(HR-[A-Z0-9]+(?:-[A-Z0-9]+)*)", re.M
)


@dataclass
class Named:
    """An `HR-` id discovered in the estate, with where it was found."""

    rule_id: str
    files: list[str] = field(default_factory=list)

    @property
    def hook_enforced(self) -> bool:
        """Named in at least one file under `hooks/`.

        A hook is the live enforcement surface. An id named there fires; an id
        named only in a command or a dataset is discussed. Only the first kind
        justifies a non-zero exit, because only the first kind means a rule is
        acting on the agent while invisible to the compiler.
        """
        return any(f.startswith("hooks/") for f in self.files)

    @property
    def recurrent(self) -> bool:
        return len(self.files) >= MIN_FILES_FOR_REAL

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "files": self.files,
            "hook_enforced": self.hook_enforced,
            "recurrent": self.recurrent,
        }


def _iter_files(root: Path):
    for name in SCAN_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in SCAN_SUFFIXES:
                continue
            if SKIP_PARTS & set(p.parts):
                continue
            yield p


def scan_estate(root: Path) -> dict[str, Named]:
    """Every `HR-` id named under SCAN_DIRS, with the files naming it."""
    found: dict[str, Named] = {}
    for p in _iter_files(root):
        rel = str(p.relative_to(root)).replace("\\", "/")
        try:
            body = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for rid in set(_ID_RE.findall(body)):
            found.setdefault(rid, Named(rid)).files.append(rel)
    for n in found.values():
        n.files.sort()
    return found


def block_ids(path: Path) -> set[str] | None:
    """Rule ids inside a file's sentinel block, or None if it has no block.

    None and the empty set are different answers: a file with no block cannot
    disagree with anything, while a file with an empty block disagrees with
    every rule the other one holds.
    """
    if not path.is_file():
        return None
    body = path.read_text(encoding="utf-8-sig", errors="replace")
    i, j = body.find(SENTINEL_START), body.find(SENTINEL_END)
    if i < 0 or j <= i:
        return None
    return set(_HEADING_RE.findall(body[i:j]))


def reconcile(root: Path, compiled_ids: set[str],
              mirror: Path | None = None,
              archive: Path | None = None) -> dict:
    """Both reconciliations over a discovered id set.

    `compiled_ids` is supplied by the caller rather than read here, so the
    reconciliation can be exercised against a synthetic corpus without the
    caller's machine having either archive on disk.
    """
    mirror = mirror if mirror is not None else root / "CLAUDE.md"
    archive = archive if archive is not None else root / "vault" / "hard_rules" / "HARD_RULES.md"

    named = scan_estate(root)

    # R-A -- the two authored blocks.
    m_ids, a_ids = block_ids(mirror), block_ids(archive)
    if m_ids is None or a_ids is None:
        block_verdict = "BLOCK_MISSING"
        both = mirror_only = archive_only = []
    else:
        block_verdict = "BLOCKS_COMPARED"
        both = sorted(m_ids & a_ids)
        mirror_only = sorted(m_ids - a_ids)
        archive_only = sorted(a_ids - m_ids)

    # R-B -- what fires vs what compiles.
    real = {k: v for k, v in named.items() if v.recurrent}
    singletons = sorted(k for k, v in named.items() if not v.recurrent)

    # An id that is a strict prefix of another discovered id is a family
    # reference in prose ("the HR-SECRET family"), not a rule. Separated rather
    # than dropped: it is counted and listed, so the distinction is auditable
    # instead of being a silent subtraction.
    prefixes = sorted(
        k for k in real
        if any(o != k and o.startswith(k + "-") for o in named)
    )
    prefix_set = set(prefixes)

    uncompiled = {
        k: v for k, v in real.items()
        if k not in compiled_ids and k not in prefix_set
    }
    enforced_not_compiled = sorted(k for k, v in uncompiled.items() if v.hook_enforced)
    referenced_not_compiled = sorted(k for k, v in uncompiled.items() if not v.hook_enforced)
    compiled_not_named = sorted(compiled_ids - set(named))

    if not named:
        verdict = "NO_IDS_FOUND"
    else:
        verdict = "RECONCILED"

    return {
        "verdict": verdict,
        "block_verdict": block_verdict,
        "scanned_dirs": [d for d in SCAN_DIRS if (root / d).is_dir()],
        "min_files_for_real": MIN_FILES_FOR_REAL,
        "named_total": len(named),
        "named_recurrent": len(real),
        "compiled_total": len(compiled_ids),
        "mirror_ids": len(m_ids) if m_ids is not None else None,
        "archive_ids": len(a_ids) if a_ids is not None else None,
        "both": both,
        "mirror_only": mirror_only,
        "archive_only": archive_only,
        "enforced_not_compiled": enforced_not_compiled,
        "referenced_not_compiled": referenced_not_compiled,
        "compiled_not_named": compiled_not_named,
        "family_prefixes": prefixes,
        "singletons": singletons,
        "detail": {k: v.as_dict() for k, v in sorted(uncompiled.items())},
    }


def render(res: dict, show_singletons: bool = False) -> str:
    """Counts and named ids. Never a ratio -- a ratio is satisfied by deleting
    members of its denominator, so it can improve while nothing is fixed."""
    L: list[str] = []
    a = L.append
    a("HARD-RULE CORPUS RECONCILIATION")
    a("=" * 62)
    a(f"verdict            : {res['verdict']}")

    if res["verdict"] == "NO_IDS_FOUND":
        a("")
        a("No `HR-` identifier was found in any scanned directory. This is")
        a("reported as its own verdict and never as agreement: an instrument")
        a("that found nothing has not established that nothing is wrong.")
        a(f"scanned            : {', '.join(res['scanned_dirs']) or '(no directory existed)'}")
        return "\n".join(L)

    a(f"ids named          : {res['named_total']}  "
      f"(recurrent in >={res['min_files_for_real']} files: {res['named_recurrent']})")
    a(f"ids compiled       : {res['compiled_total']}")
    a("")
    a("-- R-A  authored blocks --------------------------------------")
    if res["block_verdict"] == "BLOCK_MISSING":
        a("  a sentinel block is absent, so the two cannot be compared")
    else:
        a(f"  CLAUDE.md block    : {res['mirror_ids']} ids")
        a(f"  HARD_RULES.md block: {res['archive_ids']} ids")
        a(f"  in both            : {len(res['both'])}")
        a(f"  mirror only        : {len(res['mirror_only'])}")
        for r in res["mirror_only"]:
            a(f"      {r}")
        a(f"  archive only       : {len(res['archive_only'])}")
        for r in res["archive_only"]:
            a(f"      {r}")
        a("")
        a("  Divergence in both directions is not a lag. Only the archive is")
        a("  read by parser.load_corpus(), so a mirror-only rule never compiles.")

    a("")
    a("-- R-B  enforced vs compiled ---------------------------------")
    a(f"  HOOK-ENFORCED, NOT COMPILED : {len(res['enforced_not_compiled'])}")
    for r in res["enforced_not_compiled"]:
        files = res["detail"][r]["files"]
        hooks = [f for f in files if f.startswith("hooks/")]
        a(f"      {r:32s} {len(files)} files, fires from {hooks[0]}")
    a(f"  referenced, not compiled    : {len(res['referenced_not_compiled'])}")
    for r in res["referenced_not_compiled"][:15]:
        a(f"      {r:32s} {len(res['detail'][r]['files'])} files")
    if len(res["referenced_not_compiled"]) > 15:
        a(f"      ... {len(res['referenced_not_compiled']) - 15} more (use --json for all)")

    a("")
    a(f"  compiled but named nowhere else: {len(res['compiled_not_named'])}")
    a("  That half is already measured and interpreted by")
    a("  modules/rule_compiler/effect_harness.py:166 -- most compiled rules")
    a("  govern other estates. It is surfaced here, not re-derived, so the two")
    a("  do not become separate drifting sources of truth.")

    a("")
    a(f"  family prefixes (prose, not rules) : {len(res['family_prefixes'])}")
    for r in res["family_prefixes"]:
        a(f"      {r}")
    a(f"  singletons (one file only)         : {len(res['singletons'])}")
    if show_singletons:
        for r in res["singletons"]:
            a(f"      {r}")
    else:
        a("      (--singletons to list; counted, never dropped)")

    a("")
    a(f"scanned            : {', '.join(res['scanned_dirs'])}")
    a("`vault/` is excluded on purpose: it restates every compiled id and")
    a("discusses rules in prose, so including it would let the corpus and the")
    a("audit trail vouch for their own coverage.")
    a("")
    a("The referenced list is UNFILTERED. Strings like `HR-A` reach it because")
    a("they are genuinely written in the estate; a plausibility filter would be")
    a("a vocabulary gate, and an idiom it failed to recognise would score zero")
    a("and never fall. Noise in an advisory list is the cheaper error.")
    a("")
    a("What this cannot answer: whether a rule SHOULD exist that nobody has")
    a("named anywhere. The scan is bounded by the estate's own vocabulary, so")
    a("read these sets as named-and-divergent, never as complete.")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile the enforced hard-rule corpus against the compiled one.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--singletons", action="store_true", help="list one-file ids")
    ap.add_argument("--root", default=str(PP_ROOT), help="tree to scan")
    args = ap.parse_args(argv)

    from .parser import load_corpus

    compiled = {r.rule_id for r in load_corpus()}
    res = reconcile(Path(args.root), compiled)

    if args.json:
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        print(render(res, show_singletons=args.singletons))

    # Exit 1 only on a rule that FIRES from a hook and never reaches the
    # compiler. Prose divergence is reported and does not fail: a gate that
    # cries wolf on valid work is uninstalled by the third false alarm, and
    # then it protects nothing at all.
    return 1 if res["enforced_not_compiled"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
