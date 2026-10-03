"""trait_scan.py -- the OFF-PATH producer of the structural trait cache (UCEP-02).

Runs from a CLI or a scheduled task, never inside a hook chain (the capsule G-3
doctrine): a walk of a real repository costs 0.3 to 48 seconds, the prompt path
has a 3000 ms chain deadline (audit G4). It walks one repository, reads which
structural markers exist, and publishes `traits_<repo_key>.json` into the
per-user state directory, atomically, so the read-only reader in `archetypes`
never sees a half-written file.

Bounded on every axis: a file cap (the `families._MAX_ENTRIES` convention), a
wall-clock budget, a skip set for dependency and generated trees, and no
following of links. A walk that was cut records `truncated` or `budget_hit`; a
cut walk keeps the positives it found and may never be read as proof of absence.

The cache holds paths and counts only, never file contents, and the producer
writes nothing inside the scanned repository.

This first slice has ONE detector: the persistent MARKER class (a schema or
migration file or directory), judged by names alone. Every other trait reads
UNJUDGED with cause `no-structural-detector`. The dependency-class detectors and
the rules that entitle a trait to read ABSENT arrive in plan 02-03.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

import modules.capability_runtime.archetypes as archetypes  # noqa: E402
from modules.repo_identity.identity import repo_key  # noqa: E402
from modules.tower.families import _SKIP_DIRS as _FAMILY_SKIP_DIRS  # noqa: E402

DEFAULT_CAP = 100_000
DEFAULT_BUDGET_S = 120.0

# The families' skip set plus dependency, vendored and generated trees. A schema
# folder inside a package cache is a dependency's, not this repository's
# (RESEARCH F5.1, Pitfall 12).
SKIP_DIRS = frozenset(_FAMILY_SKIP_DIRS) | frozenset({
    "vendor", "third_party", "site-packages", "Library", "PackageCache", "Temp",
    "obj", "bin", "Pods", ".gradle", "_knowledge_graph"})

# Outcomes of produce(). SKIPPED is reserved for the skip-if-unchanged rule of
# plan 02-04.
WRITTEN = "WRITTEN"
SKIPPED = "SKIPPED"
UNRESOLVABLE = "UNRESOLVABLE"
FAILED = "FAILED"

# Persistent marker class. The Elixir path priv/repo/migrations is covered by the
# directory name `migrations`.
_MARKER_FILES = frozenset({"schema.prisma", "schema.sql"})
_MARKER_DIRS = frozenset({"migrations", "alembic"})


def _rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def scan(root, *, cap=DEFAULT_CAP, budget_s=DEFAULT_BUDGET_S):
    """Bounded walk of `root` -> {"walk": {...}, "traits": {ten readings}}.

    The budget is measured with perf_counter: on this host time.monotonic has the
    15.6 ms resolution of GetTickCount64. The elapsed time is tested before each
    directory is entered, so a budget of 0 always cuts the walk."""
    start = time.perf_counter()
    files = 0
    truncated = False
    budget_hit = False
    markers = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if time.perf_counter() - start >= budget_s:
            budget_hit = True
            break
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        filenames.sort()
        for d in dirnames:
            if d in _MARKER_DIRS:
                markers.append(_rel(root, os.path.join(dirpath, d)))
        for fn in filenames:
            if files >= cap:
                truncated = True
                break
            files += 1
            if fn in _MARKER_FILES:
                markers.append(_rel(root, os.path.join(dirpath, fn)))
        if truncated:
            break
    traits = {t: archetypes.unjudged_reading("no-structural-detector")
              for t in archetypes.TRAITS}
    if markers:
        # Positives found before a cut stay valid. With no marker the trait stays
        # UNJUDGED: a marker class alone is never entitled to say ABSENT, because
        # a repository can hold durable state with no marker file at all
        # (RESEARCH F5.4). The entitlement rules are plan 02-03's.
        traits["persistent"] = archetypes.reading(
            archetypes.PRESENT, archetypes.OBSERVED, sorted(markers), "marker")
    return {
        "walk": {"files": files, "cap": cap, "truncated": truncated,
                 "seconds": round(time.perf_counter() - start, 3),
                 "budget_s": budget_s, "budget_hit": budget_hit},
        "traits": traits,
    }


def produce(root, *, state_dir=None, cap=DEFAULT_CAP, budget_s=DEFAULT_BUDGET_S):
    """Scan the repository containing `root` and publish its trait cache.

    Returns {"outcome": WRITTEN, "path", "doc"}, or UNRESOLVABLE (nothing
    written) for a root that is not an absolute existing directory, or FAILED
    with the reason when anything goes wrong (nothing published)."""
    sroot = archetypes.subject_root(root)
    if sroot is None:
        return {"outcome": UNRESOLVABLE, "reason": "unresolvable-root"}
    tmp = None
    try:
        result = scan(sroot, cap=cap, budget_s=budget_s)
        path = archetypes.cache_path(sroot, state_dir=state_dir)
        doc = {"schema": archetypes.SCHEMA, "repo_key": repo_key(sroot), "repo": sroot,
               "produced_at": time.time(), "producer": "trait_scan/1",
               "walk": result["walk"], "traits": result["traits"]}
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".traits_", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)   # atomic: no observable half-written cache
        tmp = None
        return {"outcome": WRITTEN, "path": path, "doc": doc}
    except Exception as exc:  # noqa: BLE001
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass
        return {"outcome": FAILED, "reason": "%s: %s" % (type(exc).__name__, exc)}
