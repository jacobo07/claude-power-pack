#!/usr/bin/env python3
"""adapter_conformance.py -- the conformance checker CRAIF's seam catalogue never had.

`CRAIF_D2A_REINFORCEMENT_PACKAGES.md` catalogues one reinforcement package per real
owner CRAIF's STOP #1 audit found already governing a slice of the surface, and states
a per-package schema in its own prose: Owner, Mechanism Strengthened, Missing
Adapter/Contract, Integration Point, Test/Eval, No-Duplication Proof, Done-Gate, Target.

The catalogue is honest about what is missing. Nothing verified that a package actually
declares the contract the catalogue says it must, and nothing noticed when a package's
named Owner moved or was deleted -- so a seam could silently point at a path that no
longer exists while still reading as a governed integration point.

Two discovery rules, both deliberate (PR-COVERAGE-BY-CONSTRUCTION-001):

  * The PACKAGE SET is discovered from the document's own headings, never from a list
    in this file. A catalogue that enrolled its subjects by hand would measure what
    someone remembered, and a package added tomorrow would not be scored -- it would be
    absent from the denominator, and absence reads as health.
  * The FIELD SET is discovered from the document's own "Schema per package:" sentence,
    never hardcoded here. If the catalogue adds a ninth field, this checker enforces it
    on the next run with no edit. If someone deletes the schema sentence, that is a hard
    error, not a pass -- a checker with an empty vocabulary would find zero violations
    in every possible document, and zero cannot fall.

Scope is deliberately one file: verify the catalogue's own contract. It does not audit
whether an owner module implements CRAIF's runtime objects -- that is CRAIF-01's
Verification Contract, and duplicating it here would be the second placement compiler
the estate keeps refusing to build.

Fail-LOUD, not fail-open: this is a gate, and a gate that degrades to silence when it
cannot read its subject is the inert kill switch the estate has already been bitten by.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_REL = "vault/knowledge_base/craif/CRAIF_D2A_REINFORCEMENT_PACKAGES.md"

CONFORMING = "CONFORMING"
NONCONFORMING = "NONCONFORMING"

# `## 3. DRK-to-Repair-Authority Package`
_PACKAGE_RE = re.compile(r"(?m)^##\s+(\d+)\.\s+(.+?)\s*$")
# The catalogue's own schema sentence, e.g.
# "Schema per package: **Owner** . **Mechanism Strengthened** . ... **Target** (...)"
_SCHEMA_INTRO_RE = re.compile(r"Schema per package:(.*?)(?:\n\s*\n|---)", re.S)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
# Backtick-quoted repo paths in an Owner line: `modules/liveness/reachability.py`
_PATH_RE = re.compile(r"`([A-Za-z0-9_./-]+/[A-Za-z0-9_./-]+)`")


def _norm(name: str) -> str:
    """Schema labels and body labels differ in case and hyphenation.

    The schema sentence says "Mechanism Strengthened" and "Done-Gate"; the bodies say
    "Mechanism strengthened" and "Done-gate". Comparing raw strings would report every
    field missing in every package -- a checker failing 100% is as useless as one
    passing 100%, so the comparison is on a normalized key.
    """
    return re.sub(r"[^a-z0-9]+", "", name.lower())


@dataclass
class SeamVerdict:
    number: int
    title: str
    verdict: str
    missing_fields: list[str] = field(default_factory=list)
    empty_fields: list[str] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)
    owner_paths: list[str] = field(default_factory=list)
    unverifiable_owner: bool = False

    @property
    def reasons(self) -> list[str]:
        out = []
        if self.missing_fields:
            out.append("missing field(s): " + ", ".join(self.missing_fields))
        if self.empty_fields:
            out.append("declared but empty: " + ", ".join(self.empty_fields))
        if self.missing_paths:
            out.append("Owner path not on disk: " + ", ".join(self.missing_paths))
        if self.unverifiable_owner:
            out.append("Owner names no backtick-quoted repo path -- nothing in this "
                       "seam is machine-verifiable; name the owning file or directory")
        return out


class CatalogueError(RuntimeError):
    """The catalogue could not be read or carries no enforceable schema."""


def discover_schema(text: str) -> list[str]:
    """The required field names, read from the catalogue's own schema sentence."""
    m = _SCHEMA_INTRO_RE.search(text)
    if not m:
        raise CatalogueError(
            "no 'Schema per package:' sentence found -- the catalogue declares no "
            "contract, so there is nothing to enforce. Refusing to report a pass.")
    fields = [f.strip() for f in _BOLD_RE.findall(m.group(1))]
    if not fields:
        raise CatalogueError(
            "the schema sentence names zero bold fields -- an empty vocabulary would "
            "find zero violations in any document. Refusing to report a pass.")
    return fields


def discover_packages(text: str) -> list[tuple[int, str, str]]:
    """(number, title, body) per package, discovered from the document's headings."""
    marks = list(_PACKAGE_RE.finditer(text))
    out: list[tuple[int, str, str]] = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((int(m.group(1)), m.group(2).strip(), text[m.end():end]))
    return out


def check_seam(number: int, title: str, body: str, schema: list[str],
               root: Path) -> SeamVerdict:
    v = SeamVerdict(number=number, title=title, verdict=CONFORMING)

    # A field's value runs from the end of its label to the start of the NEXT
    # label (or the end of the package), so multi-line values are captured whole.
    # Anchoring on a single line instead would truncate every wrapped Owner, and
    # a whitespace-greedy one-line capture silently swallows the blank line and
    # returns the '---' separator as the value -- which reads as a populated
    # field and let an empty one score CONFORMING until a negative test caught it.
    labels = list(re.finditer(r"(?m)^\*\*(.+?)\*\*[ \t]*:?[ \t]*", body))
    present: dict[str, str] = {}
    for i, m in enumerate(labels):
        end = labels[i + 1].start() if i + 1 < len(labels) else len(body)
        raw = body[m.end():end]
        # The trailing horizontal rule belongs to the package, not to its last field.
        present[_norm(m.group(1))] = re.sub(r"(?m)^-{3,}\s*$", "", raw).strip()

    for line_field in schema:
        key = _norm(line_field)
        if key not in present:
            v.missing_fields.append(line_field)
        elif not present[key]:
            v.empty_fields.append(line_field)

    owner = present.get(_norm("Owner"), "")
    for p in _PATH_RE.findall(owner):
        v.owner_paths.append(p)
        if not (root / p).exists():
            v.missing_paths.append(p)

    # A seam whose Owner is prose names nothing this checker can verify. Left
    # unflagged it would score CONFORMING on the strength of having no checkable
    # content at all -- the gate's vocabulary would not reach it, and a zero it
    # cannot see can never fall. An unverifiable Owner is the defect.
    if _norm("Owner") in present and not v.owner_paths:
        v.unverifiable_owner = True

    if (v.missing_fields or v.empty_fields or v.missing_paths
            or v.unverifiable_owner):
        v.verdict = NONCONFORMING
    return v


def run(root: Path | None = None, catalogue: Path | None = None) -> list[SeamVerdict]:
    root = root or PP_ROOT
    path = catalogue or (root / CATALOGUE_REL)
    if not path.is_file():
        raise CatalogueError(f"catalogue not found: {path}")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    schema = discover_schema(text)
    packages = discover_packages(text)
    if not packages:
        raise CatalogueError(
            f"{path.name} declares a schema but contains zero '## N. Title' packages -- "
            "a checker reporting 0/0 clean is reporting nothing. Refusing to pass.")
    return [check_seam(n, t, b, schema, root) for n, t, b in packages]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="CRAIF adapter-conformance checker: every catalogued seam declares "
                    "the contract the catalogue itself specifies, and names an Owner "
                    "that still exists on disk.")
    ap.add_argument("--root", default=None, help="repo root (default: this repo)")
    ap.add_argument("--catalogue", default=None, help="override catalogue path")
    ap.add_argument("--list", action="store_true",
                    help="list the discovered seams and exit 0")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else PP_ROOT
    cat = Path(args.catalogue).resolve() if args.catalogue else None

    try:
        verdicts = run(root=root, catalogue=cat)
    except CatalogueError as exc:
        print(f"CRAIF_ADAPTER_CONFORMANCE: CATALOGUE ERROR -- {exc}", file=sys.stderr)
        return 2

    if args.list:
        for v in verdicts:
            paths = ", ".join(v.owner_paths) or "(no path-shaped Owner)"
            print(f"{v.number}. {v.title} -- owner: {paths}")
        print(f"seams discovered: {len(verdicts)}")
        return 0

    bad = [v for v in verdicts if v.verdict == NONCONFORMING]
    for v in verdicts:
        if v.verdict == CONFORMING:
            print(f"  [OK]   {v.number}. {v.title}")
        else:
            print(f"  [FAIL] {v.number}. {v.title}")
            for r in v.reasons:
                print(f"           {r}")
    print(f"\nCRAIF_ADAPTER_CONFORMANCE={len(verdicts) - len(bad)}/{len(verdicts)} "
          f"seams conforming")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
