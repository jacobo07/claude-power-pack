"""What does this dependency cost the institution, and what can we actually know?

R1 of the UPAC audit (`vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md`). The
sweep found no module owning transitive surface, pin discipline, replacement cost
or an internalization threshold. `modules/cdicf` proved the LICENCE half is
tractable -- it fetched five upstream licence files and caught a Commons Clause a
README badge alone would have missed -- but it does that only for design component
absorption, not as a general gate.

    python -m modules.dependency_sovereignty.sovereignty            # report
    python -m modules.dependency_sovereignty.sovereignty --gate     # exit 1 on DO_NOT_USE
    python -m modules.dependency_sovereignty.sovereignty --json

THE HONESTY CONSTRAINT, which shapes everything below.

Most of what a dependency review wants -- CVE history, maintainer health, bus
factor, ecosystem maturity, API stability, reimplementation cost -- cannot be
measured from a repository with no network. The failure to avoid is not "we lack
data"; it is reporting a dependency as fine because the evidence that would have
condemned it was never fetched. Absence of evidence must never render as a
favourable verdict (T-DEFER-RENDERED-AS-NOVEL-001).

Three states, exactly as `effect_harness.coverage()` separates unmeasured debt
from unmeasurable-here:

    MEASURED          the repo itself witnesses it
    UNKNOWN           knowable in principle; this repo does not carry the evidence
    UNREACHABLE_HERE  needs the network or a judgment about upstream

Ladder rungs that depend only on UNREACHABLE_HERE signals are DECLARED unreachable
rather than guessed. That list is not decoration -- INTERNALIZE was emitted by the
first cut of this module and removed after it recommended internalizing Pillow,
PyYAML and Playwright. Deciding whether to absorb an upstream requires knowing what
reimplementing it costs, and no pin string or import count carries that.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]

# --- evidence states -------------------------------------------------------
MEASURED = "MEASURED"
UNKNOWN = "UNKNOWN"
UNREACHABLE_HERE = "UNREACHABLE_HERE"

# --- pin discipline --------------------------------------------------------
EXACT = "EXACT"
RANGE = "RANGE"
UNPINNED = "UNPINNED"

# --- the decision ladder ---------------------------------------------------
USE = "USE"
WRAP = "WRAP"
DO_NOT_USE = "DO_NOT_USE"
REVIEW = "REVIEW"

# Real rungs of the ladder that this gate does NOT emit, each with the reason it
# cannot. Declared rather than silently omitted, so the report states its own
# ceiling instead of implying the ladder has four rungs.
UNREACHABLE_RUNGS = {
    "CONNECT": "needs the upstream's integration surface and support posture",
    "EXTEND": "needs the upstream's contribution policy and roadmap",
    "FORK": "needs licence posture plus maintenance capacity to carry a fork",
    "REPLACE": "needs the alternatives' health, which is a network question",
    "INTERNALIZE": "needs reimplementation cost -- no pin string or import count "
                   "carries it; emitting it from those produced 'internalize "
                   "Pillow' on the first cut of this module",
}

# A dependency imported from this many distinct files is load-bearing: a breaking
# change touches every one, so the institutional move is one adapter rather than N
# call-site edits. "More than a handful", not fitted to a result.
WRAP_THRESHOLD = 5

SRC_SUFFIXES = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist",
             "build", ".pytest_cache", "vendor"}
MAX_SCANNED_FILES = 4000     # bound the sweep; a shortfall is reported, not hidden


@dataclass
class Dependency:
    name: str
    ecosystem: str                  # "npm" | "pypi"
    constraint: str
    declared_in: str
    pin: str                        # EXACT | RANGE | UNPINNED
    lockfile_present: bool
    transitive_surface: int | None   # None == UNKNOWN, never 0-as-unknown
    internal_call_sites: int
    usage_state: str                 # MEASURED | UNKNOWN
    vendored: bool
    verdict: str = ""
    evidence: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)


# --- parsing ---------------------------------------------------------------

_NPM_EXACT = re.compile(r"^\d+\.\d+\.\d+")
_PY_REQ = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*(.*)$")


def _npm_pin(spec: str) -> str:
    s = (spec or "").strip()
    if not s or s in {"*", "latest", "x"}:
        return UNPINNED
    return EXACT if _NPM_EXACT.match(s) else RANGE


def _py_pin(spec: str) -> str:
    s = (spec or "").strip()
    if not s:
        return UNPINNED
    return EXACT if s.startswith("==") else RANGE


def parse_package_json(path: Path) -> list:
    """Direct runtime dependencies only. devDependencies are a build-time surface
    with a different risk profile and are not folded in silently."""
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        return []
    return [(str(n), str(v), "npm") for n, v in deps.items()]


def parse_requirements(path: Path) -> list:
    out = []
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return out
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue          # -r / -e / --flag lines are not a named dependency
        m = _PY_REQ.match(line)
        if m:
            out.append((m.group(1), m.group(2).strip(), "pypi"))
    return out


def parse_pyproject(path: Path) -> list:
    """PEP 621 `dependencies = [...]` only, read without a TOML dependency.

    Deliberately narrow: it reads the one array it understands and returns nothing
    for a poetry-style table rather than guessing at a shape it has not verified.
    Returning [] for an unrecognised layout would report a dependency-bearing
    project as dependency-free, so the shortfall surfaces through
    `manifest_coverage()` instead of being swallowed here.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    m = re.search(r"^\s*dependencies\s*=\s*\[(.*?)\]", text, re.S | re.M)
    if not m:
        return []
    out = []
    for item in re.findall(r"[\"']([^\"']+)[\"']", m.group(1)):
        pm = _PY_REQ.match(item)
        if pm:
            out.append((pm.group(1), pm.group(2).strip(), "pypi"))
    return out


def _lock_for(manifest: Path) -> Path | None:
    for name in ("package-lock.json", "poetry.lock", "Pipfile.lock",
                 "requirements.lock"):
        cand = manifest.parent / name
        if cand.is_file():
            return cand
    return None


def _transitive_count(lock: Path | None) -> int | None:
    """Resolved-package count from a lockfile. None means UNKNOWN -- returning 0
    would make 'no lockfile' indistinguishable from 'no transitive deps', which is
    the favourable-reading-of-absence this module exists to refuse."""
    if lock is None:
        return None
    try:
        if lock.name == "package-lock.json":
            data = json.loads(lock.read_text(encoding="utf-8-sig"))
            pkgs = data.get("packages")
            if isinstance(pkgs, dict):
                return max(0, len(pkgs) - 1)      # "" is the root project
            deps = data.get("dependencies")
            return len(deps) if isinstance(deps, dict) else None
        text = lock.read_text(encoding="utf-8-sig")
        n = len(re.findall(r"^\s*\[\[package\]\]", text, re.M))
        return n or None
    except (OSError, ValueError):
        return None


# --- repo-side signals -----------------------------------------------------

def _import_patterns(name: str, ecosystem: str):
    esc = re.escape(name)
    if ecosystem == "npm":
        return (re.compile(r"""require\(\s*['"]%s(?:/[^'"]*)?['"]""" % esc),
                re.compile(r"""from\s+['"]%s(?:/[^'"]*)?['"]""" % esc))
    mod = re.escape(name.replace("-", "_"))
    return (re.compile(r"^\s*import\s+%s\b" % mod, re.M),
            re.compile(r"^\s*from\s+%s\b" % mod, re.M))


def _source_files(root: Path) -> tuple:
    """(files, truncated). Truncation is returned, never swallowed: a capped sweep
    that reads as complete would understate every call-site count."""
    out = []
    truncated = False
    for p in root.rglob("*"):
        if len(out) >= MAX_SCANNED_FILES:
            truncated = True
            break
        if not p.is_file() or p.suffix not in SRC_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return out, truncated


def count_call_sites(specs: list, files: list) -> dict:
    """One pass over the corpus, all dependencies tested per file.

    Per-dependency scanning re-read every source file once per dependency; at 16
    dependencies that was 16 full sweeps for one report.
    """
    pats = {(n, e): _import_patterns(n, e) for n, e in specs}
    hits = {k: 0 for k in pats}
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for key, (a, b) in pats.items():
            if a.search(text) or b.search(text):
                hits[key] += 1
    return hits


def _is_vendored(name: str, root: Path) -> bool:
    vendor = root / "vendor"
    if not vendor.is_dir():
        return False
    leaf = name.split("/")[-1]
    try:
        return any(d.is_dir() and d.name in {name, leaf} for d in vendor.iterdir())
    except OSError:
        return False


# --- the ladder ------------------------------------------------------------

def decide(dep: Dependency) -> Dependency:
    """Assign a rung. Any UNKNOWN that could change the answer forces REVIEW.

    Order matters: the disqualifying condition is checked before any favourable
    one, so a dependency can never earn USE on the strength of signals that were
    merely absent.
    """
    reasons = []

    # Disqualifying: you cannot know what you install.
    if dep.pin == UNPINNED and not dep.lockfile_present:
        reasons.append("unpinned constraint with no lockfile -- the resolved "
                       "version is whatever the registry serves at install time")
        dep.verdict, dep.reasons = DO_NOT_USE, reasons
        return dep

    # Load-bearing, and POSITIVELY observed. Requires usage_state MEASURED: a
    # count derived from an unobservable scope must not drive a verdict.
    if (dep.usage_state == MEASURED
            and dep.internal_call_sites >= WRAP_THRESHOLD and not dep.vendored):
        reasons.append(f"{dep.internal_call_sites} call sites -- a breaking "
                       "change edits every one; put it behind one adapter")
        dep.verdict, dep.reasons = WRAP, reasons
        return dep

    if dep.pin == EXACT and dep.lockfile_present:
        reasons.append("exact pin and a lockfile -- the installed graph is "
                       "reproducible from this repo alone")
        dep.verdict, dep.reasons = USE, reasons
        return dep

    if dep.pin != EXACT:
        reasons.append(f"pin discipline is {dep.pin}, so the installed version is "
                       "not determined by this repo")
    if not dep.lockfile_present:
        reasons.append("no lockfile -- transitive surface is UNKNOWN, not zero")
    if dep.usage_state == UNKNOWN:
        reasons.append("zero local call sites, which does NOT mean lightly used: "
                       "this manifest may describe a runtime whose code is not in "
                       "this scan scope. Usage is UNKNOWN, not low")
    reasons.append("upstream health, CVE history and reimplementation cost are "
                   "UNREACHABLE_HERE (no network); this verdict is deliberately "
                   "not USE")
    dep.verdict, dep.reasons = REVIEW, reasons
    return dep


# --- scan ------------------------------------------------------------------

MANIFESTS = (
    ("package.json", parse_package_json),
    ("requirements.txt", parse_requirements),
    ("pyproject.toml", parse_pyproject),
)
_MANIFEST_NAMES = {m for m, _ in MANIFESTS}


def find_manifests(root: Path) -> list:
    out = []
    for p in root.rglob("*"):
        if not p.is_file() or p.name not in _MANIFEST_NAMES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def scan(root: Path | None = None) -> list:
    root = Path(root) if root is not None else PP_ROOT
    files, truncated = _source_files(root)
    parsers = dict(MANIFESTS)

    rows = []
    for manifest in find_manifests(root):
        for name, constraint, eco in parsers[manifest.name](manifest):
            rows.append((manifest, name, constraint, eco))

    hits = count_call_sites(sorted({(n, e) for _, n, _, e in rows}), files)

    deps = []
    for manifest, name, constraint, eco in rows:
        lock = _lock_for(manifest)
        n_sites = hits.get((name, eco), 0)
        # Zero observed sites is ambiguous by construction: either genuinely
        # unused, or used by code outside this scan scope (a vps/ requirements
        # file describes a remote runtime). Those are different facts and are
        # not collapsed into one favourable reading.
        usage_state = MEASURED if n_sites > 0 else UNKNOWN
        dep = Dependency(
            name=name, ecosystem=eco, constraint=constraint,
            declared_in=str(manifest.relative_to(root)).replace("\\", "/"),
            pin=_npm_pin(constraint) if eco == "npm" else _py_pin(constraint),
            lockfile_present=lock is not None,
            transitive_surface=_transitive_count(lock),
            internal_call_sites=n_sites,
            usage_state=usage_state,
            vendored=_is_vendored(name, root),
        )
        dep.evidence = {
            "pin": MEASURED,
            "lockfile_present": MEASURED,
            "transitive_surface": (MEASURED if dep.transitive_surface is not None
                                   else UNKNOWN),
            "internal_call_sites": usage_state,
            "scan_truncated": truncated,
            "vendored": MEASURED,
            "licence": UNKNOWN,
            "cve_history": UNREACHABLE_HERE,
            "maintainer_health": UNREACHABLE_HERE,
            "bus_factor": UNREACHABLE_HERE,
            "api_stability": UNREACHABLE_HERE,
            "reimplementation_cost": UNREACHABLE_HERE,
        }
        deps.append(decide(dep))
    return deps


def manifest_coverage(root: Path | None = None) -> dict:
    """Manifests found vs manifests this module can actually parse. A manifest
    yielding nothing is reported, because 'parsed to empty' and 'unsupported
    layout' must not look alike."""
    root = Path(root) if root is not None else PP_ROOT
    parsers = dict(MANIFESTS)
    found, empty = [], []
    for m in find_manifests(root):
        rel = str(m.relative_to(root)).replace("\\", "/")
        found.append(rel)
        if not parsers[m.name](m):
            empty.append(rel)
    return {"found": found, "yielded_nothing": empty}


def render(deps: list, cov: dict) -> str:
    L = [f"dependency sovereignty: {len(deps)} direct dependency declaration(s) "
         f"across {len(cov['found'])} manifest(s)"]
    for d in sorted(deps, key=lambda x: (x.verdict, x.name, x.declared_in)):
        surf = "UNKNOWN" if d.transitive_surface is None else str(d.transitive_surface)
        sites = (str(d.internal_call_sites) if d.usage_state == MEASURED
                 else "UNKNOWN")
        L.append(f"  [{d.verdict:<11}] {d.name} ({d.ecosystem}) "
                 f"pin={d.pin} lock={'yes' if d.lockfile_present else 'no'} "
                 f"transitive={surf} call_sites={sites}")
        L.append(f"      declared in {d.declared_in}")
        for r in d.reasons:
            L.append(f"      - {r}")
    if cov["yielded_nothing"]:
        L.append("  manifests that yielded no dependency (unsupported layout or "
                 "genuinely empty -- verify before trusting):")
        for rel in cov["yielded_nothing"]:
            L.append(f"      {rel}")
    L.append("  ladder rungs this gate does NOT emit:")
    for rung, why in sorted(UNREACHABLE_RUNGS.items()):
        L.append(f"      {rung}: {why}")
    counts = {}
    for d in deps:
        counts[d.verdict] = counts.get(d.verdict, 0) + 1
    L.append("DEPENDENCY_SOVEREIGNTY " + "  ".join(
        f"{k}={v}" for k, v in sorted(counts.items())))
    return "\n".join(L)


def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = PP_ROOT
    if "--root" in args:
        root = Path(args[args.index("--root") + 1])
    deps = scan(root)
    cov = manifest_coverage(root)
    if "--json" in args:
        print(json.dumps({"dependencies": [asdict(d) for d in deps],
                          "manifest_coverage": cov,
                          "unreachable_rungs": UNREACHABLE_RUNGS},
                         ensure_ascii=False, indent=2))
    else:
        print(render(deps, cov))
    if "--gate" in args and any(d.verdict == DO_NOT_USE for d in deps):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
