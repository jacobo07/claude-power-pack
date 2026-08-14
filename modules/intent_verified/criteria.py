"""Criteria discovered from a spec's acceptance section.

The intent artifact already exists: `vault/specs/*.md`, bound to a task by
`covers:` front matter. This module reads the criteria out of it. It does not
define a second schema -- the second copy is the one that goes stale.

A criterion is mechanical when it names a V-gate id, because a V-gate id is a
falsifiable predicate: satisfied when a file emitting it is observed to pass.
An acceptance section that names none is reported as CRITERIA_NOT_MECHANICAL
rather than invented into one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# The heading that opens an acceptance section, in the spellings the repo's
# own specs use.
_SECTION = re.compile(
    r"^#{2,4}[^\n]*(?:acceptance|done-gate|done gate|completion gate)[^\n]*$",
    re.I | re.M)
_NEXT_H2 = re.compile(r"^#{1,3} ", re.M)

VID = re.compile(r"\bV-[A-Z0-9][A-Z0-9_\-]*\b")

# A criterion is critical unless the row says otherwise. A forgotten mark must
# fail toward blocking; the other direction is how a criterion silently stops
# counting.
_ADVISORY = re.compile(r"\badvisor(?:y|io)\b|\bnice[- ]to[- ]have\b", re.I)


@dataclass(frozen=True)
class Criterion:
    id: str
    assertion: str
    critical: bool
    spec: str

    def as_dict(self) -> dict:
        return {"id": self.id, "assertion": self.assertion,
                "critical": self.critical, "spec": self.spec}


def acceptance_section(text: str) -> str | None:
    """The body of the spec's acceptance section, or None."""
    m = _SECTION.search(text or "")
    if not m:
        return None
    rest = text[m.end():]
    nxt = _NEXT_H2.search(rest)
    return rest[:nxt.start()] if nxt else rest


def _assertion_of(line: str, vid: str) -> str:
    """The human-readable claim beside the id, cleaned of table pipes."""
    cells = [c.strip() for c in line.split("|") if c.strip()]
    for cell in cells:
        if vid not in cell:
            continue
        others = [c for c in cells if c is not cell]
        if others:
            return re.sub(r"\s+", " ", " ".join(others)).strip(" `")
    stripped = re.sub(r"^\s*[-*]\s*", "", line)
    stripped = stripped.replace(vid, "", 1)
    return re.sub(r"[`|]", "", stripped).strip(" -:—").strip()


def parse_criteria(text: str, spec_label: str = "") -> list[Criterion]:
    """Every V-id in the acceptance section, in document order, de-duplicated."""
    body = acceptance_section(text)
    if body is None:
        return []
    out: list[Criterion] = []
    seen: set[str] = set()
    for line in body.splitlines():
        ids = VID.findall(line)
        if not ids:
            continue
        critical = not _ADVISORY.search(line)
        for vid in ids:
            if vid in seen:
                continue
            seen.add(vid)
            out.append(Criterion(id=vid, assertion=_assertion_of(line, vid),
                                 critical=critical, spec=spec_label))
    return out


def spec_label(spec_path: Path, root: Path | None = None) -> str:
    if root is None:
        return str(spec_path)
    try:
        return str(spec_path.relative_to(root))
    except ValueError:
        # Outside the root: the absolute path is the honest label.
        return str(spec_path)


def read_criteria(spec_path: Path, root: Path | None = None) -> list[Criterion]:
    """Criteria declared by one spec file.

    Propagates OSError on purpose. An unreadable spec and a spec with no
    criteria are different facts, and swallowing the first makes it read as
    the second.
    """
    text = spec_path.read_text(encoding="utf-8-sig", errors="replace")
    return parse_criteria(text, spec_label(spec_path, root))


def criteria_for_task(task_description: str,
                      cwd: Path | str | None = None
                      ) -> tuple[list[Criterion], Path | None, str]:
    """Criteria of the spec bound to THIS task.

    Returns (criteria, spec_path, reason). An unbound task yields ([], None,
    reason) -- that is INTENT_NOT_CAPTURED upstream, not an error here.
    """
    root = Path(cwd) if cwd else Path.cwd()
    try:
        from modules.sdd_os.spec_binding import find_bound_spec
    except ImportError as exc:
        return [], None, f"spec binding unavailable: {exc}"
    binding = find_bound_spec(task_description, root)
    if not binding.bound or binding.spec_path is None:
        return [], None, binding.reason
    return read_criteria(binding.spec_path, root), binding.spec_path, \
        binding.reason


def iter_specs(root: Path) -> list[Path]:
    """Every spec-shaped file, via the binding module's own glob set."""
    try:
        from modules.sdd_os.spec_binding import SPEC_GLOBS, iter_candidates
    except ImportError:
        return sorted(root.glob("vault/specs/*.md"))
    return iter_candidates(root, SPEC_GLOBS)


__all__ = ["Criterion", "VID", "acceptance_section", "parse_criteria",
           "spec_label", "read_criteria", "criteria_for_task", "iter_specs"]
