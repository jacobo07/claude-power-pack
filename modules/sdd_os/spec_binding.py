#!/usr/bin/env python3
"""SDD-OS task-to-spec binding -- closes RC-2 (BL-SDD-ACT-001).

The pre-existing spec gate asked "does this repo contain a spec-shaped
file?". It accepted any `vault/plans/*.md`, so a repo with 131 historical
plan files (KobiiCraft) passed the gate forever, for every future task,
on files describing unrelated work. The question it must ask is "does
THIS TASK have a spec?".

Binding contract (Owner decision OD-1, 2026-07-26): a spec DECLARES what
it covers in front matter. A task binds to a spec when the task's tokens
contain every sub-token of at least one `covers` entry.

    ---
    title: Waitlist gate rework
    covers: [waitlist, signup-flow, gate]
    tier: 2
    ---

A spec with no `covers` key binds to nothing. That is deliberate: the
27 repos whose gate was auto-satisfied by undeclared plan files stop
passing silently, which is the defect being closed. `infer_covers()`
exists to make migration cheap, but it never writes on its own -- an
inferred value is a suggestion to a human, not a binding.

Stdlib only, cwd-relative, no hardcoded paths (E11). Works in any repo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Spec locations honored, in priority order. Superset of the legacy
# spec_gate.SPEC_GLOBS so no existing location loses eligibility -- the
# narrowing happens on `covers`, not on where a spec may live.
SPEC_GLOBS: tuple[str, ...] = (
    ".specify/specs/*/spec.md",
    "vault/specs/*.md",
    "vault/plans/*.md",
    "docs/specs/*.md",
    "*.prd.md",
    "spec.md", "SPEC.md", "PRD.md", "requirements.md",
    "docs/spec.md", "docs/PRD.md", "docs/requirements.md",
)

# Bilingual: the Owner's prompts mix English and Spanish, so a
# single-language stoplist would leak connectives into the token set and
# make every spec match every task.
_STOPWORDS: frozenset[str] = frozenset("""
the and for with from this that then than into onto over under also
are was were will would should could must can may not but any all
each other more most some such only own same too very just now
new add fix use using make made get set put run task work code file
files repo project system need needs want sure please
para por con sin desde hasta este esta esto esos esas como cual
que qué los las una unos unas del les son ser estar hacer
todo toda todos todas cada otro otra donde cuando porque pero
mas más muy solo sólo ya sea si no nuevo nueva
create creating build building implement implementing update updating
change changing improve improving refactor refactoring support
crear crea construir implementar actualizar cambiar mejorar
""".split())
# Action verbs belong in the stoplist, not in `covers`. A spec declaring
# `covers: [create]` would bind to nearly every task -- which is RC-2
# wearing a different hat. Empirically caught 2026-07-26: infer_covers()
# on "create a new billing integration module" proposed 'create' as its
# first entry.

_TOKEN_RX = re.compile(r"[a-z0-9]+")
_FM_FENCE = "---"
_MIN_TOKEN_LEN = 3


@dataclass
class SpecBinding:
    """Result of resolving a task against the repo's declared specs."""
    bound: bool
    spec_path: Path | None = None
    covers: tuple[str, ...] = ()
    matched: tuple[str, ...] = ()
    reason: str = ""
    candidates_seen: int = 0
    undeclared: tuple[Path, ...] = field(default_factory=tuple)


def tokenize(text: str) -> set[str]:
    """Lowercase alnum tokens, stopwords and sub-3-char noise removed."""
    return {
        t for t in _TOKEN_RX.findall((text or "").lower())
        if len(t) >= _MIN_TOKEN_LEN and t not in _STOPWORDS
    }


def parse_front_matter(text: str) -> dict[str, object]:
    """Parse the leading `---` fenced block. Minimal YAML subset.

    Supports `key: value`, `key: [a, b]`, and a block list:

        key:
          - a
          - b

    Returns {} when there is no leading fence. Never raises: a malformed
    header yields the keys it could read, so one bad line cannot make a
    whole spec invisible.
    """
    if not text:
        return {}
    lines = text.splitlines()
    # Tolerate a UTF-8 BOM and blank lines before the fence.
    start = 0
    while start < len(lines) and not lines[start].strip().lstrip("﻿"):
        start += 1
    if start >= len(lines):
        return {}
    if lines[start].strip().lstrip("﻿") != _FM_FENCE:
        return {}

    out: dict[str, object] = {}
    pending_key: str | None = None
    for raw in lines[start + 1:]:
        stripped = raw.strip()
        if stripped == _FM_FENCE:
            break
        if not stripped or stripped.startswith("#"):
            continue
        # Continuation of a block list.
        if stripped.startswith("- ") and pending_key:
            item = stripped[2:].strip().strip("'\"")
            if item:
                cur = out.get(pending_key)
                if isinstance(cur, list):
                    cur.append(item)
                else:
                    out[pending_key] = [item]
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if not key:
            continue
        if not value:
            out[key] = []
            pending_key = key
            continue
        pending_key = None
        if value.startswith("[") and value.endswith("]"):
            items = [
                v.strip().strip("'\"")
                for v in value[1:-1].split(",")
            ]
            out[key] = [v for v in items if v]
        else:
            out[key] = value.strip("'\"")
    return out


def _as_entries(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(v).strip() for v in value if str(v).strip())
    if isinstance(value, str) and value.strip():
        # Tolerate `covers: waitlist, signup-flow` written without braces.
        return tuple(v.strip() for v in value.split(",") if v.strip())
    return ()


def read_covers(spec_path: Path) -> tuple[str, ...] | None:
    """Declared `covers` entries, or None when the spec declares none."""
    try:
        text = spec_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    fm = parse_front_matter(text)
    entries = _as_entries(fm.get("covers"))
    return entries or None


def read_tier(spec_path: Path) -> int | None:
    """Declared `tier`, when the spec carries one."""
    try:
        text = spec_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    raw = parse_front_matter(text).get("tier")
    try:
        tier = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return tier if 0 <= tier <= 3 else None


def entry_matches(entry: str, task_tokens: set[str]) -> bool:
    """A `covers` entry matches when ALL its sub-tokens are in the task.

    Multi-word entries (`signup-flow`, `spec gate`) are conjunctive on
    purpose: matching on any single sub-token would let a generic word
    like "gate" bind an unrelated spec, which is RC-2 in a new costume.
    """
    sub = tokenize(entry)
    if not sub:
        return False
    return sub.issubset(task_tokens)


def iter_candidates(cwd: Path,
                    globs: tuple[str, ...] = SPEC_GLOBS) -> list[Path]:
    """Every spec-shaped file in the repo, newest first, de-duplicated."""
    seen: set[Path] = set()
    found: list[Path] = []
    for pattern in globs:
        try:
            matches = cwd.glob(pattern)
        except (OSError, ValueError):
            continue
        for p in matches:
            try:
                if not p.is_file():
                    continue
                resolved = p.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(p)
    return found


def find_bound_spec(task_description: str,
                    cwd: Path | str | None = None,
                    globs: tuple[str, ...] = SPEC_GLOBS) -> SpecBinding:
    """Resolve the spec that covers THIS task, if any.

    Newest matching spec wins. Specs without a `covers` declaration are
    reported in `undeclared` so a migration nudge can name them, but they
    never bind.
    """
    root = Path(cwd) if cwd else Path.cwd()
    task_tokens = tokenize(task_description)
    candidates = iter_candidates(root, globs)

    if not candidates:
        return SpecBinding(
            bound=False, reason="no spec-shaped file in this repo",
            candidates_seen=0)

    def _mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except OSError:
            return 0.0

    candidates.sort(key=_mtime, reverse=True)

    undeclared: list[Path] = []
    for spec in candidates:
        covers = read_covers(spec)
        if covers is None:
            undeclared.append(spec)
            continue
        matched = tuple(e for e in covers if entry_matches(e, task_tokens))
        if matched:
            return SpecBinding(
                bound=True, spec_path=spec, covers=covers, matched=matched,
                reason=f"covers {list(matched)} present in task",
                candidates_seen=len(candidates),
                undeclared=tuple(undeclared))

    declared = len(candidates) - len(undeclared)
    if declared == 0:
        reason = (f"{len(undeclared)} spec-shaped file(s) found, none "
                  f"declares `covers` -- none can bind to a task")
    else:
        reason = (f"{len(candidates)} spec(s) scanned ({declared} declared); "
                  f"no `covers` entry matches this task")
    return SpecBinding(
        bound=False, reason=reason, candidates_seen=len(candidates),
        undeclared=tuple(undeclared))


def infer_covers(task_description: str, top_n: int = 6) -> list[str]:
    """Suggest `covers` entries from a task description.

    Suggestion only -- never written automatically. Order is first
    appearance in the task, which reads more naturally to a human
    reviewer than frequency order on a one-line task.
    """
    seen: list[str] = []
    for tok in _TOKEN_RX.findall((task_description or "").lower()):
        if len(tok) < _MIN_TOKEN_LEN or tok in _STOPWORDS:
            continue
        if tok not in seen:
            seen.append(tok)
        if len(seen) >= top_n:
            break
    return seen


__all__ = [
    "SPEC_GLOBS",
    "SpecBinding",
    "tokenize",
    "parse_front_matter",
    "read_covers",
    "read_tier",
    "entry_matches",
    "iter_candidates",
    "find_bound_spec",
    "infer_covers",
]
