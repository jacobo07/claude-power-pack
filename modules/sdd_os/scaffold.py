#!/usr/bin/env python3
"""SDD-OS repo scaffold + spec-drift detection -- closes RC-4.

Two halves of the same problem. The scaffold half means a repo that has
never seen the Power Pack gets its spec substrate on first contact, so
the gate's "no spec" branch has somewhere to land instead of nagging
forever. The drift half means a spec that stops describing the code is
detected, because a stale spec is worse than no spec -- it is a false
source of truth that future agents will act on (T-SDD-OS-SPEC-DRIFT-001).

Non-destructive is a hard contract here, not a preference: this runs
against repos with years of real documentation. Nothing existing is ever
overwritten; the scaffold only adds what is absent and reports what it
skipped.

Stdlib only, cwd-relative, no hardcoded paths (E11).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.sdd_os.spec_binding import iter_candidates, read_covers  # noqa: E402

# Manifest -> stack label. Order matters: the first hit names the repo.
_MANIFESTS: tuple[tuple[str, str], ...] = (
    ("pyproject.toml", "Python"),
    ("mix.exs", "Elixir / OTP"),
    ("Cargo.toml", "Rust"),
    ("go.mod", "Go"),
    ("pom.xml", "Java / Maven"),
    ("build.gradle", "Java / Gradle"),
    ("build.gradle.kts", "Kotlin / Gradle"),
    ("plugin.yml", "Minecraft plugin"),
    ("package.json", "Node / JavaScript"),
    ("requirements.txt", "Python"),
    ("CMakeLists.txt", "C / C++"),
    ("Makefile", "Make-driven"),
)

_TEST_DIRS = ("tests", "test", "spec", "__tests__")
_CI_PATHS = (".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml")
_SOURCE_SUFFIXES = frozenset({
    ".py", ".js", ".ts", ".tsx", ".jsx", ".ex", ".exs", ".go", ".rs",
    ".java", ".kt", ".c", ".h", ".cpp", ".cs", ".rb", ".php", ".swift",
})
_SKIP_DIRS = frozenset({
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
    "build", "target", ".next", "vendor", ".pnpm", "site-packages",
    ".mypy_cache", ".pytest_cache", "_build", "deps", "coverage",
})

SCAFFOLD_FILES = ("ARCHITECTURE.md", "ROADMAP.md")


@dataclass
class RepoProfile:
    root: Path
    stack: str
    manifests: tuple[str, ...]
    top_dirs: tuple[str, ...]
    source_files: int
    has_tests: bool
    has_ci: bool
    default_tier: int
    spec_dir: Path
    existing_specs: int
    declared_specs: int


@dataclass
class ScaffoldResult:
    root: Path
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    profile: RepoProfile | None = None

    @property
    def changed(self) -> bool:
        return bool(self.created)


@dataclass
class DriftReport:
    spec_path: Path
    spec_mtime: datetime
    newest_source: Path | None
    newest_source_mtime: datetime | None
    drifted: bool
    reason: str


def _iter_source_files(root: Path, limit: int = 4000):
    """Walk the repo skipping vendored trees. Bounded so a monorepo scan
    cannot become the slow thing that gets the gate disabled."""
    count = 0
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if count >= limit:
                return
            try:
                if entry.is_dir():
                    if entry.name in _SKIP_DIRS or entry.name.startswith("."):
                        continue
                    stack.append(entry)
                elif entry.suffix.lower() in _SOURCE_SUFFIXES:
                    count += 1
                    yield entry
            except OSError:
                continue


def profile_repo(cwd: Path | str | None = None) -> RepoProfile:
    """Infer what this repo is from evidence on disk. No guessing beyond
    what a manifest or directory actually states."""
    from modules.sdd_os.pre_exec_gate import resolve_spec_dir

    root = Path(cwd) if cwd else Path.cwd()

    manifests = tuple(
        name for name, _ in _MANIFESTS if (root / name).is_file())
    stack = next(
        (label for name, label in _MANIFESTS if (root / name).is_file()),
        "undetermined")

    try:
        top_dirs = tuple(sorted(
            d.name for d in root.iterdir()
            if d.is_dir() and d.name not in _SKIP_DIRS
            and not d.name.startswith(".")))
    except OSError:
        top_dirs = ()

    source_files = sum(1 for _ in _iter_source_files(root))
    has_tests = any((root / d).is_dir() for d in _TEST_DIRS)
    has_ci = any((root / p).exists() for p in _CI_PATHS)

    specs = iter_candidates(root)
    declared = sum(1 for s in specs if read_covers(s))

    # Baseline rigor for the repo. A repo with CI, tests and real volume
    # is production substrate and starts at Feature/System rigor; a small
    # or scratch repo starts at Standard. This is the FLOOR, never a cap:
    # per-task classification can always escalate above it.
    if has_ci and has_tests and source_files >= 40:
        default_tier = 2
    elif source_files >= 5:
        default_tier = 1
    else:
        default_tier = 0

    return RepoProfile(
        root=root, stack=stack, manifests=manifests, top_dirs=top_dirs,
        source_files=source_files, has_tests=has_tests, has_ci=has_ci,
        default_tier=default_tier, spec_dir=resolve_spec_dir(root),
        existing_specs=len(specs), declared_specs=declared)


def is_scaffolded(cwd: Path | str | None = None) -> bool:
    root = Path(cwd) if cwd else Path.cwd()
    return all((root / name).exists() for name in SCAFFOLD_FILES)


def _architecture_body(p: RepoProfile) -> str:
    dirs = "\n".join(f"- `{d}/`" for d in p.top_dirs[:24]) or "- (none detected)"
    manifests = ", ".join(f"`{m}`" for m in p.manifests) or "none detected"
    return f"""---
title: {p.root.name} -- Architecture Spec
covers: [architecture, structure, overview]
tier: {p.default_tier}
date: {date.today().isoformat()}
status: inferred
---

# {p.root.name} -- Architecture Spec

Generated by the SDD-OS scaffold on {date.today().isoformat()} from
evidence on disk. Everything below marked *observed* was read from the
filesystem. Everything marked *open* needs a human or a later pass --
they are stated as questions rather than filled with invented content,
because an Architecture Spec that confidently describes a system nobody
verified is exactly the false source of truth this document exists to
prevent.

## Observed

| Property | Value |
|---|---|
| Stack | {p.stack} |
| Manifests | {manifests} |
| Source files | {p.source_files} |
| Test directory | {"present" if p.has_tests else "not found"} |
| CI configuration | {"present" if p.has_ci else "not found"} |
| Spec-shaped files | {p.existing_specs} ({p.declared_specs} declare `covers`) |
| Baseline rigor | Tier {p.default_tier} |

### Top-level structure (observed)

{dirs}

## Open -- components and responsibilities

For each directory above: what is it responsible for, and what depends
on it?

## Open -- system flow

Input, decision, execution, validation, output, fallback, error handling.

## Open -- contracts

For each boundary: what it receives, what it produces, what it must never
produce, and what happens on failure.

## Open -- failure modes

Where does this system break under load, bad input, or partial failure?

## Open -- what must not be touched

Load-bearing paths where a change is high-blast-radius.

## Baseline rigor for this repo

Tier {p.default_tier} is the FLOOR, not a cap. Per-task classification
may escalate above it; it may not silently fall below it.
"""


def _roadmap_body(p: RepoProfile) -> str:
    return f"""---
title: {p.root.name} -- Roadmap
covers: [roadmap, planning, phases]
tier: {p.default_tier}
date: {date.today().isoformat()}
status: draft
---

# {p.root.name} -- Roadmap

Five-phase structure from Dataset SDD-OS 1, PARTE I sec. 7. A phase is
complete when its acceptance criteria are observed, not when its code
compiles.

## Phase 1 -- Minimum correct system

The smallest thing that works seriously end to end.

## Phase 2 -- Robust system

Validation, edge cases, error paths, contracts, observability.

## Phase 3 -- Scalable system

Reuse, configuration, cross-repo portability, integration.

## Phase 4 -- Self-improving system

Learning from failures, updating standards, preventing recurrence.

## Phase 5 -- Institutionalized standard

What was learned becomes a permanent rule for future features.

## Current position

Baseline rigor Tier {p.default_tier}; {p.source_files} source files;
tests {"present" if p.has_tests else "absent"}; CI
{"present" if p.has_ci else "absent"}.
"""


def scaffold(cwd: Path | str | None = None,
             dry_run: bool = False) -> ScaffoldResult:
    """Create the SDD-OS substrate for a repo. Never overwrites."""
    root = Path(cwd) if cwd else Path.cwd()
    profile = profile_repo(root)
    result = ScaffoldResult(root=root, profile=profile)

    bodies = {
        "ARCHITECTURE.md": _architecture_body(profile),
        "ROADMAP.md": _roadmap_body(profile),
    }

    for name, body in bodies.items():
        target = root / name
        if target.exists():
            result.skipped.append(target)
            continue
        if dry_run:
            result.created.append(target)
            continue
        try:
            target.write_text(body, encoding="utf-8")
            result.created.append(target)
        except OSError:
            result.skipped.append(target)

    spec_dir = profile.spec_dir
    if not spec_dir.exists():
        if dry_run:
            result.created.append(spec_dir)
        else:
            try:
                spec_dir.mkdir(parents=True, exist_ok=True)
                result.created.append(spec_dir)
            except OSError:
                result.skipped.append(spec_dir)
    else:
        result.skipped.append(spec_dir)

    return result


def _mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def check_drift(cwd: Path | str | None = None,
                spec_path: Path | str | None = None) -> list[DriftReport]:
    """Report specs older than the code they describe.

    A spec whose declared coverage exists but whose mtime predates the
    newest source file has stopped describing reality. This is a
    heuristic and says so: it detects *staleness*, which is a necessary
    condition for drift, not a proof of it. It never edits a spec.
    """
    root = Path(cwd) if cwd else Path.cwd()

    if spec_path is not None:
        specs = [Path(spec_path)]
    else:
        specs = [s for s in iter_candidates(root) if read_covers(s)]

    if not specs:
        return []

    newest: Path | None = None
    newest_ts: datetime | None = None
    for src in _iter_source_files(root):
        ts = _mtime(src)
        if ts is None:
            continue
        if newest_ts is None or ts > newest_ts:
            newest, newest_ts = src, ts

    reports: list[DriftReport] = []
    for spec in specs:
        spec_ts = _mtime(spec)
        if spec_ts is None:
            continue
        if newest_ts is None:
            reports.append(DriftReport(
                spec, spec_ts, None, None, False,
                "no source files found to compare against"))
            continue
        drifted = spec_ts < newest_ts
        if drifted:
            delta = newest_ts - spec_ts
            reason = (f"code moved {delta.days}d after the spec was last "
                      f"touched (newest: {newest.name if newest else '?'})")
        else:
            reason = "spec is at least as recent as the newest source file"
        reports.append(DriftReport(
            spec, spec_ts, newest, newest_ts, drifted, reason))

    return reports


__all__ = [
    "SCAFFOLD_FILES",
    "RepoProfile",
    "ScaffoldResult",
    "DriftReport",
    "profile_repo",
    "is_scaffolded",
    "scaffold",
    "check_drift",
]
