"""System families -- which constitutive baseline a mission or a repo belongs to.

Spec: docs/superpowers/specs/2026-09-24-family-baselines-design.md (S1).
Subjects predeclared before this file existed:
vault/audits/ucr_cif/18_FAMILY_MISSION_PREDECLARATION.md (commit 247ffc0).

WHY NOT CAPABILITY CONTRACTS. UBC (`capability_runtime/applicability.py`) already
matches a mission against triggers with anti-triggers as a veto. But a contract
that matches drives the ExecutionOS tier (`gsd_x/tier.classify`: one MANDATORY
-> DEEP, two -> FORENSIC), so registering "web site" as a contract would silently
raise the tier of every web prompt. This module reuses UBC's MATCHER and GRAMMAR
-- `_hits`, word-boundary, anti-triggers first -- and not its verdict. One
matcher, one grammar, no second decider.

Two questions, deliberately separate:
  classify_prompt(text)  which families does THIS mission build? -> injection
  repo_families(path)    which families does THIS repo belong to? -> promotion
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

FAMILIES_DIR = os.path.join(_PP_ROOT, "vault", "tower", "families")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
              "build", ".next", "target", "_build", "deps", ".claude"}
# Sized to a REAL repo, not to a guess. At 4000 (family_scan's bound) the
# predeclared IN subject KobiiCraft Core Files was judged OUT: 48,461 entries,
# first pom.xml at entry 5,408. Membership is computed at promotion time, not on
# the prompt path, so a full walk is affordable; a walk that still hits this
# ceiling reports the family UNJUDGED, never OUT.
_MAX_ENTRIES = 100_000
_MAX_READ = 64 * 1024


@dataclass
class Family:
    id: str
    name: str
    triggers: list = field(default_factory=list)
    anti_triggers: list = field(default_factory=list)
    # Structural repo markers. Each: {"file": <basename or glob-free name>}
    # optionally with "contains": [substrings, any of which must appear].
    repo_markers: list = field(default_factory=list)
    delegate: str = ""          # e.g. "family_scan" for persistent_state


def _fold(s: str) -> str:
    """Lowercase and strip accents, so `migración` and `migracion` are one word.
    Applied to BOTH the prompt and the phrases -- folding one side only makes
    every accented trigger unreachable."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def load_families(directory: str | None = None) -> list:
    d = directory or FAMILIES_DIR
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(d, fn), "r", encoding="utf-8-sig") as fh:
            raw = json.load(fh)
        out.append(Family(id=raw["id"], name=raw.get("name", raw["id"]),
                          triggers=list(raw.get("triggers") or []),
                          anti_triggers=list(raw.get("anti_triggers") or []),
                          repo_markers=list(raw.get("repo_markers") or []),
                          delegate=str(raw.get("delegate") or "")))
    return out


def _match(text: str, phrases) -> list:
    from modules.capability_runtime.applicability import _hits
    return _hits(_fold(text), [_fold(p) for p in phrases or []])


def classify_prompt(text: str, families: list | None = None) -> list:
    """[(family_id, [trigger hits])] for every family this mission builds.
    Anti-triggers veto first, exactly as UBC's gate 1."""
    fams = families if families is not None else load_families()
    out = []
    for f in fams:
        if _match(text, f.anti_triggers):
            continue
        hits = _match(text, f.triggers)
        if hits:
            out.append((f.id, hits))
    return out


def _marker_hits(path: str, markers: list) -> tuple:
    """Bounded walk -> (hits, truncated). A repo is characterised by its shape;
    an unbounded walk over 42 projects is the instrument consuming the host it
    measures. `truncated` is returned, never swallowed: a cut walk that found
    nothing has not judged the repo."""
    want = {}
    for m in markers or []:
        want.setdefault(m["file"].lower(), []).append(m)
    found, seen = [], 0
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [x for x in dirnames if x not in _SKIP_DIRS]
        for fn in filenames:
            seen += 1
            if seen > _MAX_ENTRIES:
                return found, True
            specs = want.get(fn.lower())
            if not specs:
                continue
            full = os.path.join(dirpath, fn)
            for spec in specs:
                needles = spec.get("contains") or []
                if not needles:
                    found.append(os.path.relpath(full, path))
                    continue
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as fh:
                        body = fh.read(_MAX_READ)
                except OSError:
                    continue
                if any(n in body for n in needles):
                    found.append(os.path.relpath(full, path))
    return found, False


def repo_family_report(path: str, families: list | None = None) -> dict:
    """{"in": {family_id: [evidence]}, "unjudged": [family_id]}.

    UNJUDGED is its own answer: a family whose walk was cut before finding a
    marker, or whose delegate failed. Promotion must not treat it as OUT."""
    fams = families if families is not None else load_families()
    report: dict = {"in": {}, "unjudged": []}
    for f in fams:
        if f.delegate == "family_scan":
            try:
                sys.path.insert(0, os.path.join(_PP_ROOT, "tools"))
                from family_scan import scan_repo
                res = scan_repo(path)
            except Exception:  # noqa: BLE001
                report["unjudged"].append(f.id)
                continue
            if res.get("present"):
                report["in"][f.id] = res["present"]
            continue
        hits, truncated = _marker_hits(path, f.repo_markers)
        if hits:
            report["in"][f.id] = hits[:5]
        elif truncated:
            report["unjudged"].append(f.id)
    return report


def repo_families(path: str, families: list | None = None) -> dict:
    """{family_id: [evidence]} for every family this repo is PROVEN to be in."""
    return repo_family_report(path, families)["in"]
