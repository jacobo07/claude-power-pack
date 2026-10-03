"""trait_scan.py -- the OFF-PATH producer of the structural trait cache (UCEP-02).

Runs from a CLI or a scheduled task, never inside a hook chain (the capsule G-3
doctrine): a walk of a real repository costs 0.3 to 48 seconds, the prompt path
has a 3000 ms chain deadline (audit G4). It walks one repository, reads which
structural markers and declared dependencies exist, and publishes
`traits_<repo_key>.json` into the per-user state directory, atomically, so the
read-only reader in `archetypes` never sees a half-written file.

Bounded on every axis: a file cap (the `families._MAX_ENTRIES` convention), a
wall-clock budget, a skip set for dependency and generated trees, no following of
links, and manifest reads bounded to `MANIFEST_READ_MAX` bytes. A walk that was cut
records `truncated` or `budget_hit`; a cut walk keeps the positives it found and
may never be read as proof of absence.

The cache holds relative paths, dependency names and counts only, never file
contents, and the producer writes nothing inside the scanned repository.

Honest absence (D-05): a trait with no positive evidence reads ABSENT only when
`_entitle` can say the walk could have seen it. Otherwise it reads UNJUDGED with
the precise cause. The cause precedence is documented on `_entitle`.
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

# Evidence classes. A WEAK reading never reaches REQUIRED (the ceiling enforces it).
STRONG = "STRONG"
WEAK = "WEAK"

MANIFEST_READ_MAX = 40 * 1024   # a manifest is read at most this far, and never parsed beyond it
EVIDENCE_MAX = 5                # evidence strings kept per trait
_MANIFEST_ERRORS_MAX = 10

# The test seam for the walk (a drill replaces it). The scan calls it by module-global
# name, with followlinks=False and an onerror callback that counts and never raises.
_walk = os.walk

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
_MARKER_TRAITS = frozenset({"persistent"})


# -- manifest parsers: declared names only, never text ------------------------------

def _names(obj):
    return {str(k).lower() for k in obj} if isinstance(obj, dict) else set()


def _parse_package_json(text):
    """-> (runtime_names, dev_names). Raises on invalid JSON (the caller records it)."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("package.json is not an object")
    runtime = set()
    for key in ("dependencies", "peerDependencies", "optionalDependencies"):
        runtime |= _names(data.get(key))
    return runtime, _names(data.get("devDependencies"))


# Manifests are matched by exact lower-cased basename.
PARSERS = {"package.json": _parse_package_json}
ECOSYSTEMS = {"package.json": "npm"}

# Dependency-class signals: trait -> {exact lower-cased declared name: evidence class}.
# Closed and fitted (RESEARCH A4): an unknown library is a recall gap that reads ABSENT
# only when a manifest was visible, never a precision gap. Matching is name equality on
# parsed names, never a substring (family_scan read `ecto` inside `vector`).
def _strong(*names):
    return {n: STRONG for n in names}


DEP_SIGNALS = {
    "persistent": _strong(
        "prisma", "@prisma/client", "drizzle-orm", "typeorm", "sequelize", "mongoose",
        "mongodb", "pg", "mysql2", "better-sqlite3", "sqlite3", "knex",
        "@supabase/supabase-js"),
}


def _rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def _safe_rel(root, path):
    """Relative forward-slash path, or None. A device-file name such as `nul` makes
    os.path.relpath raise ValueError on Windows (the incident recorded in
    `family_scan.scan_repo`): that entry is skipped, never the sweep."""
    try:
        return _rel(root, path)
    except ValueError:
        return None


def _manifest_error(walk, rel, error):
    if len(walk["manifest_errors"]) < _MANIFEST_ERRORS_MAX:
        walk["manifest_errors"].append({"path": rel, "error": error})


def _read_manifest(root, dirpath, fn, walk, parsed, ecosystems):
    """Read and parse one manifest selected by its exact basename. A failure is
    recorded in `walk["manifest_errors"]` and the manifest does not count as parsed."""
    low = fn.lower()
    path = os.path.join(dirpath, fn)
    rel = _safe_rel(root, path)
    if rel is None:
        return
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MANIFEST_READ_MAX + 1)
    except OSError as exc:
        _manifest_error(walk, rel, "unreadable: %s" % type(exc).__name__)
        return
    if len(raw) > MANIFEST_READ_MAX:
        # A partly read manifest is not a parsed one: absence read from it would be a guess.
        _manifest_error(walk, rel, "read-limit: larger than %d bytes" % MANIFEST_READ_MAX)
        return
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        runtime, dev = PARSERS[low](text)
    except Exception as exc:  # noqa: BLE001 -- adversarial manifest text must never raise
        _manifest_error(walk, rel, "%s" % type(exc).__name__)
        return
    parsed.append((rel, ECOSYSTEMS[low], runtime, dev))
    ecosystems.add(ECOSYSTEMS[low])
    walk["manifests_parsed"] += 1


def _has_dependency_detector(trait):
    return trait in DEP_SIGNALS


def _has_detector(trait):
    return trait in DEP_SIGNALS or trait in _MARKER_TRAITS


def _entitle(trait, found, walk):
    """The one function that turns a trait's evidence and the walk's bookkeeping into
    a reading.

    `found` is a list of (class, evidence, kind). Positive evidence wins whatever the
    walk did (a positive found before a cut stays valid): PRESENT if any STRONG
    evidence exists, else WEAK. With no positive evidence the cause precedence is:

      1. the trait has no structural detector at all      -> UNJUDGED no-structural-detector
      2. the walk stopped at `cap`                        -> UNJUDGED truncated
      3. the walk stopped at `budget_s`                   -> UNJUDGED budget-exhausted
      4. a directory could not be listed                  -> UNJUDGED unreadable-subtree
      5. a dependency-class detector and no manifest was
         parsed                                           -> UNJUDGED no-manifest-ecosystem
      6. otherwise                                        -> ABSENT, OBSERVED
    """
    for cls, state in ((STRONG, archetypes.PRESENT), (WEAK, archetypes.WEAK)):
        evidence = sorted({e for c, e, _k in found if c == cls})
        if evidence:
            kinds = "+".join(sorted({k for c, _e, k in found if c == cls}))
            return archetypes.reading(state, archetypes.OBSERVED, evidence, kinds)
    if not _has_detector(trait):
        return archetypes.unjudged_reading("no-structural-detector")
    if walk["truncated"]:
        return archetypes.unjudged_reading("truncated")
    if walk["budget_hit"]:
        return archetypes.unjudged_reading("budget-exhausted")
    if walk["unreadable"] > 0:
        return archetypes.unjudged_reading("unreadable-subtree")
    if _has_dependency_detector(trait) and walk["manifests_parsed"] == 0:
        return archetypes.unjudged_reading("no-manifest-ecosystem")
    seen = ", ".join(walk["ecosystems"]) or "none"
    return archetypes.reading(archetypes.ABSENT, archetypes.OBSERVED, (),
                              "no %s evidence in a complete walk (ecosystems seen: %s)" % (trait, seen))


def _dependency_evidence(parsed, found):
    """Add declared-dependency evidence. A name declared only in a dev section is WEAK."""
    for rel, _eco, runtime, dev in parsed:
        for trait, table in DEP_SIGNALS.items():
            for name in sorted(runtime):
                cls = table.get(name)
                if cls:
                    found[trait].append((cls, "%s:%s" % (rel, name), "dependency"))
            for name in sorted(dev - runtime):
                if name in table:
                    found[trait].append((WEAK, "%s:%s" % (rel, name), "dependency"))


def scan(root, *, cap=DEFAULT_CAP, budget_s=DEFAULT_BUDGET_S):
    """Bounded walk of `root` -> {"walk": {...}, "traits": {ten readings}}.

    The budget is measured with perf_counter: on this host time.monotonic has the
    15.6 ms resolution of GetTickCount64. The elapsed time is tested before each
    directory is entered, so a budget of 0 always cuts the walk."""
    start = time.perf_counter()
    walk = {"files": 0, "cap": cap, "truncated": False, "seconds": 0.0,
            "budget_s": budget_s, "budget_hit": False, "manifests_parsed": 0,
            "ecosystems": [], "unreadable": 0, "manifest_errors": []}
    found = {t: [] for t in archetypes.TRAITS}
    parsed, ecosystems = [], set()

    def onerror(_exc):          # a directory that could not be listed: counted, never raised
        walk["unreadable"] += 1

    for dirpath, dirnames, filenames in _walk(root, followlinks=False, onerror=onerror):
        if time.perf_counter() - start >= budget_s:
            walk["budget_hit"] = True
            break
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        filenames.sort()
        for d in dirnames:
            if d in _MARKER_DIRS:
                rel = _safe_rel(root, os.path.join(dirpath, d))
                if rel is not None:
                    found["persistent"].append((STRONG, rel, "marker"))
        for fn in filenames:
            if walk["files"] >= cap:
                walk["truncated"] = True
                break
            walk["files"] += 1
            if fn in _MARKER_FILES:
                rel = _safe_rel(root, os.path.join(dirpath, fn))
                if rel is not None:
                    found["persistent"].append((STRONG, rel, "marker"))
            if fn.lower() in PARSERS:
                _read_manifest(root, dirpath, fn, walk, parsed, ecosystems)
        if walk["truncated"]:
            break
    walk["ecosystems"] = sorted(ecosystems)
    walk["seconds"] = round(time.perf_counter() - start, 3)
    _dependency_evidence(parsed, found)
    traits = {t: _entitle(t, found[t], walk) for t in archetypes.TRAITS}
    return {"walk": walk, "traits": traits}


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
