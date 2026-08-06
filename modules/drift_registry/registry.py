"""What this estate detects about drift, discovered rather than remembered.

Eight-plus modules detect drift and each one works. No artifact names them,
so coverage cannot be stated, and a family nobody implemented is invisible.

The obvious fix -- write down the families -- is the defect. A registry
enrolled by hand measures what someone remembered; an undeclared component
is not scored UNKNOWN, it is absent from the denominator, and absence reads
as health (`PR-COVERAGE-BY-CONSTRUCTION-001`). The EGCC source that prompted
this module proposes a 160-class list and then rejects its own proposal for
the same reason: a rigid list becomes bureaucracy and goes stale.

So nothing here is enumerated. Both sets are read off the filesystem, and a
term earns the name "family" by RECURRENCE, not by appearing on a list:

    a family term is written `<word> drift` in >=2 distinct files,
    or appears as a `<word>_drift` / `<word>-drift` identifier.

That is the same instrument `schema.find_boilerplate_stops` already uses --
an ACTION shared verbatim by two rules is filler by definition, because a
real action is rule-specific. Here the inverse: a term written once in one
file is prose ("...mentions drift", "...cannot drift"), while a real family
recurs, because more than one person needed the words. Measured, not judged.

The first pass captured 246 terms including `about`, `very` and `into`. That
is what an unmeasured filter produces, and it is why the recurrence rule
exists. Single-file terms are COUNTED and retrievable (`--singletons`),
never silently dropped.

Two findings are produced, and both are falsifiable:

  unclassifiable_detectors  detects drift, names no family -- so its
                            coverage cannot be attributed
  undetected_families       a family this repo NAMES and no detector
                            mentions -- prose without a probe

WHAT THIS DELIBERATELY DOES NOT EMIT: "uncovered families" in the abstract.
A discovered sweep can witness what the estate wrote down. It cannot witness
a family nobody has ever named -- and a module reporting one would assert a
completeness it has no instrument for.

    python -m modules.drift_registry.registry
    python -m modules.drift_registry.registry --json --singletons
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]

#: Where to look. Directories, not files -- naming files would re-introduce
#: the curation this module exists to avoid.
SEARCH_ROOTS = ("modules", "vault/knowledge_base", "governance", "tools")

SKIP_PARTS = frozenset({
    "node_modules", "__pycache__", ".git", "compiled", "backups", "backup",
    ".venv", "venv", "dist", "build",
})

MAX_BYTES = 400_000
MAX_TERM_LEN = 24
MIN_FILES_FOR_FAMILY = 2      # the recurrence threshold, stated once

#: `configuration drift`, `config-drift`, `schema_drift`. Only the
#: <word>-BEFORE-drift form: `drift <word>` is almost always grammar
#: ("drift detection", "drift can occur") and contributed nearly all of
#: the first pass's noise.
_TERM_RE = re.compile(r"\b([a-z][a-z_-]{2,%d})[ _-]drift\b" % MAX_TERM_LEN)

#: Identifier form -- `config_drift`, `schema-drift`. One occurrence is
#: enough: a programmer naming a symbol has committed to the concept in a
#: way a sentence has not.
_IDENT_RE = re.compile(r"\b([a-z][a-z_]{2,%d})_drift\b" % MAX_TERM_LEN)

#: English function words. This excludes GRAMMAR, never families -- the
#: distinction that keeps the filter honest: no domain term is listed
#: here, and adding one would be the curation this module rejects.
_FUNCTION_WORDS = frozenset({
    "the", "and", "or", "not", "any", "all", "for", "from", "with", "when",
    "where", "which", "that", "this", "these", "those", "its", "their",
    "them", "they", "was", "were", "has", "have", "had", "can", "cannot",
    "could", "would", "should", "must", "may", "into", "onto", "about",
    "very", "more", "most", "less", "than", "then", "also", "such", "same",
    "each", "every", "some", "only", "just", "even", "still", "yet", "but",
    "how", "why", "what", "who", "one", "two", "does", "did", "are", "is",
    "be", "been", "being", "no", "nor", "so", "as", "at", "by", "in", "of",
    "on", "to", "up", "it", "if", "we", "our", "you", "your",
    "against", "never", "will", "without", "catch", "exact", "future",
    # verbs the corpus writes immediately before the noun
    "detectar",   # the corpus is bilingual; this is the Spanish verb
    "detect", "detects", "detected", "detecting", "mentions", "mention",
    "prevent", "prevents", "prevented", "finds", "find", "found", "cause",
    "causes", "caused", "produce", "produces", "produced", "reports",
    "report", "reported", "true", "false", "real", "half", "between",
})

#: A file that merely mentions drift is not a detector. One that defines a
#: comparison is. Matched on `def` lines only, so prose about detecting
#: cannot promote a document into a detector.
_DETECT_DEF_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+\w*"
    r"(detect|compare|reconcile|diff|scan|audit|verify|check|probe|weaken)"
    r"\w*\s*\(",
    re.M | re.I,
)

#: Excluded from the DETECTOR set, with the reason stated in the output.
#: A test exercises a detector; it is not one, and counting tests inflates
#: coverage with the very thing that is supposed to prove it. This module
#: excludes itself for the same reason -- a scanner that finds itself is
#: reporting its own vocabulary back as evidence.
def _is_detector_candidate(rel: str) -> tuple:
    name = rel.rsplit("/", 1)[-1]
    if rel.startswith("modules/drift_registry/"):
        return False, "the registry itself -- self-discovery is not evidence"
    if name.startswith("test_") or name.endswith("_test.py"):
        return False, "a test exercises a detector; it is not one"
    return True, ""


@dataclass
class Detector:
    path: str
    families: list = field(default_factory=list)
    verbs: list = field(default_factory=list)


@dataclass
class FamilyTerm:
    name: str
    files: set = field(default_factory=set)
    mentions: list = field(default_factory=list)
    identifier: bool = False


def _iter_files(root: Path):
    for rel in SEARCH_ROOTS:
        base = root / rel
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or SKIP_PARTS & set(p.parts):
                continue
            if p.suffix.lower() not in (".py", ".md", ".json", ".js"):
                continue
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield p


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _terms_in(line: str) -> tuple:
    """(prose_terms, identifier_terms) for one line, lowercased."""
    low = line.lower()
    prose = {m.group(1).strip("-_") for m in _TERM_RE.finditer(low)}
    ident = {m.group(1).strip("_") for m in _IDENT_RE.finditer(low)}
    keep = lambda s: {t for t in s if t and t not in _FUNCTION_WORDS}
    return keep(prose), keep(ident)


def scan(root: Path = PP_ROOT) -> dict:
    """Walk the estate. Everything returned was read off disk this call."""
    terms: dict = {}
    detector_rows: list = []
    excluded: list = []
    files_read = 0

    for p in _iter_files(root):
        text = _read(p)
        if "drift" not in text.lower():
            continue
        files_read += 1
        rel = p.relative_to(root).as_posix()
        in_file: set = set()

        for line_no, line in enumerate(text.splitlines(), 1):
            prose, ident = _terms_in(line)
            for tok in prose | ident:
                ft = terms.setdefault(tok, FamilyTerm(tok))
                ft.files.add(rel)
                if tok in ident:
                    ft.identifier = True
                if len(ft.mentions) < 5:
                    ft.mentions.append(f"{rel}:{line_no}")
                in_file.add(tok)

        if p.suffix.lower() != ".py":
            continue
        verbs = sorted({m.group(1).lower()
                        for m in _DETECT_DEF_RE.finditer(text)})
        if not verbs:
            continue
        ok, why = _is_detector_candidate(rel)
        if not ok:
            excluded.append({"path": rel, "reason": why})
            continue
        detector_rows.append((rel, in_file, verbs))

    # Recurrence gate -- measured, applied after the whole walk because it
    # is a property of the corpus, not of any one file.
    families = {n: ft for n, ft in terms.items()
                if len(ft.files) >= MIN_FILES_FOR_FAMILY or ft.identifier}
    singletons = sorted(set(terms) - set(families))

    detectors = [
        Detector(rel, sorted(t for t in found if t in families), verbs)
        for rel, found, verbs in sorted(detector_rows)
    ]
    detected = {f for d in detectors for f in d.families}

    return {
        "root": str(root),
        "files_examined": files_read,
        "recurrence_threshold": MIN_FILES_FOR_FAMILY,
        "families": {n: sorted(ft.files)[:5] for n, ft in sorted(families.items())},
        "family_evidence": {n: ft.mentions for n, ft in sorted(families.items())},
        "singletons_discarded": singletons,
        "detectors": [
            {"path": d.path, "families": d.families, "verbs": d.verbs}
            for d in detectors
        ],
        "excluded_from_detectors": excluded,
        "unclassifiable_detectors": sorted(
            d.path for d in detectors if not d.families),
        "undetected_families": sorted(set(families) - detected),
        "verdict": "NO_DETECTORS_FOUND" if not detectors else "SCANNED",
    }


def render(rep: dict, curated: list | None = None,
           show_singletons: bool = False) -> str:
    out = [
        "# DRIFT REGISTRY (discovered from disk -- not a maintained list)",
        "",
        f"verdict            : {rep['verdict']}",
        f"files examined     : {rep['files_examined']}",
        f"family terms       : {len(rep['families'])} "
        f"(recurrence >= {rep['recurrence_threshold']} files, or an identifier)",
        f"singletons dropped : {len(rep['singletons_discarded'])} "
        f"(one-file prose; --singletons to list)",
        f"detectors          : {len(rep['detectors'])} "
        f"({len(rep['excluded_from_detectors'])} excluded)",
        "",
    ]
    if rep["verdict"] == "NO_DETECTORS_FOUND":
        out += [
            "NO_DETECTORS_FOUND is a verdict, not a clean run. Either the "
            "search roots are wrong or this estate detects no drift at all; "
            "both are findings and neither is a pass.",
            "",
        ]
    out += ["## Detectors", ""]
    for d in rep["detectors"]:
        fams = ", ".join(d["families"]) or "(names no family)"
        out.append(f"- `{d['path']}`  [{', '.join(d['verbs'])}]  -> {fams}")

    out += ["", "## Detects drift, attributes it to no family", ""]
    out += ([f"- `{p}`" for p in rep["unclassifiable_detectors"]]
            or ["(none -- every detector names at least one family)"])

    out += ["", "## Named by this repo, mentioned by no detector", ""]
    out += ([f"- **{f}** -- e.g. {rep['family_evidence'][f][0]}"
             for f in rep["undetected_families"]]
            or ["(none)"])

    if rep["excluded_from_detectors"]:
        out += ["", "## Excluded from the detector set", ""]
        out += [f"- `{e['path']}` -- {e['reason']}"
                for e in rep["excluded_from_detectors"]]

    if show_singletons and rep["singletons_discarded"]:
        out += ["", "## Singletons discarded (named in one file only)", "",
                ", ".join(rep["singletons_discarded"])]

    out += [
        "",
        "## What this cannot witness",
        "",
        "A drift family nobody here has ever named. This scan is bounded by "
        "the repo's own vocabulary, so `undetected_families` means *named in "
        "prose, absent from code* -- never *missing from the world*. Reading "
        "it as completeness is the error this module was built to avoid.",
    ]
    if curated:
        missing = sorted(set(curated) - set(rep["families"]))
        out += [
            "",
            "## CURATED expectation list -- MEASURES MEMORY, NOT REALITY",
            "",
            "Supplied by hand, so it finds only what someone remembered to "
            "enrol. Reported apart from the discovered sets, never merged.",
            "",
        ]
        out += ([f"- **{f}** -- expected, never named in this repo"
                 for f in missing]
                or ["(every expected family is named somewhere)"])
    return "\n".join(out) + "\n"


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description="Discovered drift registry")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--singletons", action="store_true",
                    help="list the one-file terms the recurrence gate dropped")
    ap.add_argument("--expect", nargs="*", default=None, metavar="FAMILY",
                    help="curated expectation list; labelled memory-measuring")
    a = ap.parse_args(argv)
    rep = scan()
    if a.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        print(render(rep, a.expect, a.singletons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
