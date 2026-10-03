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
import re
import sys
import tempfile
import time

try:                      # stdlib on 3.11+; a missing tomllib records a manifest error, never raises
    import tomllib
except ImportError:       # pragma: no cover
    tomllib = None

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

# Marker classes: names and directory shapes, matched exactly (never as substrings).
# Content is read only for the decisive token of a file selected by name or by
# directory, bounded to MANIFEST_READ_MAX, and never by searching source for trait
# words (RESEARCH F5.2). The Elixir path priv/repo/migrations is covered by the
# directory name `migrations`.
MARKER_SIGNALS = {
    "persistent": {
        "strong_files": frozenset({"schema.prisma", "schema.sql"}),
        "strong_dirs": frozenset({"migrations", "alembic"}),
        # Data files are not code (RESEARCH F5.3): WEAK, never PRESENT.
        "weak_extensions": (".db", ".sqlite", ".sqlite3", ".mca"),
        "weak_files": frozenset({"level.dat"}),
        "weak_dirs": frozenset({"playerdata"}),
        "ignored_files": frozenset({"thumbs.db"}),    # a Windows thumbnail cache is not a database
    },
    "distributed": {
        "strong_files": frozenset({"docker-compose.yml", "docker-compose.yaml", "compose.yml",
                                   "compose.yaml", "fly.toml"}),
        "weak_files": frozenset({"dockerfile"}),
        "workload_dirs": frozenset({"k8s", "kubernetes", "deploy", "helm"}),
        "workload_kinds": ("Deployment", "StatefulSet", "DaemonSet", "CronJob"),
    },
    "scheduled": {
        "workflow_parts": (".github", "workflows"),
        "json_files": frozenset({"vercel.json"}),
        "json_key": "crons",
    },
    "multi_actor": {"strong_files": frozenset({"plugin.yml", "paper-plugin.yml"})},
    "policy_layers": {"weak_dirs": frozenset({"policies", "rls"})},
}

# A source module under one of these directory segments is WEAK evidence of persistence.
# PROVISIONAL (R-3): the class ships WEAK and its calibration against KobiiSports Resort
# is Phase 7, not planned here.
CODE_MODULE_SEGMENTS = ("save", "saves", "savegame", "savedata", "persistence", "persist", "storage")
CODE_MODULE_EXTENSIONS = (".c", ".cpp", ".h", ".hpp", ".cs", ".java", ".py", ".ex", ".exs",
                          ".rs", ".go", ".kt", ".ts", ".js")

# ui is judged by counting files: at least UI_PRESENT_MIN is PRESENT, one to fewer is WEAK (A8).
UI_EXTENSIONS = (".tsx", ".jsx", ".vue", ".svelte", ".html", ".css", ".scss", ".astro",
                 ".cshtml", ".razor", ".xaml", ".uxml", ".uss")
UI_PRESENT_MIN = 20

_MARKER_TRAITS = frozenset(MARKER_SIGNALS) | {"ui"}   # traits with a marker or count detector
_FOUND_CAP = 50                                        # evidence kept per trait and class while walking
_YAML_EXTENSIONS = (".yml", ".yaml")
_WORKLOAD_RE = re.compile(r"^[ \t]*kind:[ \t]*(?:%s)[ \t\r]*$" % "|".join(
    MARKER_SIGNALS["distributed"]["workload_kinds"]), re.M)
_CRON_RE = re.compile(r"^[ \t]*(?:-[ \t]*)?cron:", re.M)


def _is_secret_name(fn):
    """A file this producer must never open, whatever selected it."""
    low = fn.lower()
    return low.startswith(".env") or low.endswith((".key", ".pem")) or low.startswith("id_rsa")


def _is_link(path):
    """A symlink or, on Windows, a directory junction: pruned, never followed (A10:
    os.walk(followlinks=False) still descends a junction on this host)."""
    isjunction = getattr(os.path, "isjunction", None)
    return os.path.islink(path) or (isjunction is not None and isjunction(path))


def _read_bounded(path, walk):
    """The text of one file selected by name, at most MANIFEST_READ_MAX bytes, or None."""
    if _is_secret_name(os.path.basename(path)):
        return None
    try:
        with open(path, "rb") as fh:
            return fh.read(MANIFEST_READ_MAX).decode("utf-8-sig", errors="replace")
    except OSError:
        walk["unreadable"] += 1       # a file we could not read is a place we could not see
        return None


def _add(found, trait, cls, evidence, kind):
    bucket = found[trait]
    if sum(1 for c, _e, _k in bucket if c == cls) < _FOUND_CAP:
        bucket.append((cls, evidence, kind))


def _dir_markers(rel_dir, parts, dirnames, filenames, found):
    """Directory-shaped markers: child directories by name, and the directory itself."""
    persistent = MARKER_SIGNALS["persistent"]
    for d in dirnames:
        low = d.lower()
        rel = d if rel_dir == "." else rel_dir + "/" + d
        if low in persistent["strong_dirs"]:
            _add(found, "persistent", STRONG, rel, "marker")
        elif low in persistent["weak_dirs"]:
            _add(found, "persistent", WEAK, rel, "data-file")
    if parts and filenames and parts[-1] in MARKER_SIGNALS["policy_layers"]["weak_dirs"]:
        _add(found, "policy_layers", WEAK, rel_dir, "marker")


def _file_markers(dirpath, rel, rel_dir, parts, fn, walk, found, ui):
    """File-shaped markers for one file, selected by exact name, extension or directory."""
    low = fn.lower()
    ext = os.path.splitext(low)[1]
    persistent = MARKER_SIGNALS["persistent"]
    if low in persistent["strong_files"]:
        _add(found, "persistent", STRONG, rel, "marker")
    elif low not in persistent["ignored_files"] and (
            ext in persistent["weak_extensions"] or low in persistent["weak_files"]):
        _add(found, "persistent", WEAK, rel, "data-file")
    if ext in CODE_MODULE_EXTENSIONS and any(seg in CODE_MODULE_SEGMENTS for seg in parts):
        _add(found, "persistent", WEAK, rel, "code-module")
    distributed = MARKER_SIGNALS["distributed"]
    if low in distributed["strong_files"]:
        _add(found, "distributed", STRONG, rel, "marker")
    elif low in distributed["weak_files"]:
        _add(found, "distributed", WEAK, rel, "marker")
    elif ext in _YAML_EXTENSIONS and any(seg in distributed["workload_dirs"] for seg in parts):
        text = _read_bounded(os.path.join(dirpath, fn), walk)
        if text is not None and _WORKLOAD_RE.search(text):
            _add(found, "distributed", STRONG, rel, "marker")
    scheduled = MARKER_SIGNALS["scheduled"]
    if ext in _YAML_EXTENSIONS and tuple(parts[-2:]) == scheduled["workflow_parts"]:
        text = _read_bounded(os.path.join(dirpath, fn), walk)
        if text is not None and _CRON_RE.search(text):
            _add(found, "scheduled", STRONG, rel, "marker")
    elif low in scheduled["json_files"]:
        text = _read_bounded(os.path.join(dirpath, fn), walk)
        try:
            doc = json.loads(text) if text is not None else None
        except ValueError:
            doc = None
        if isinstance(doc, dict) and doc.get(scheduled["json_key"]):
            _add(found, "scheduled", STRONG, rel, "marker")
    if low in MARKER_SIGNALS["multi_actor"]["strong_files"]:
        _add(found, "multi_actor", STRONG, rel, "marker")
    if ext in UI_EXTENSIONS:
        ui["count"] += 1
        if len(ui["samples"]) < EVIDENCE_MAX:
            ui["samples"].append(rel)


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


_REQ_NAME_RE = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _req_name(spec):
    """The distribution name of one PEP 508 requirement string, lower-cased ('' if none)."""
    m = _REQ_NAME_RE.match(spec)
    return m.group(1).lower() if m else ""


def _parse_requirements(text):
    """requirements.txt -> (runtime_names, set()). Comments, blank lines, `-r`/`-e`
    options and bare URLs are ignored; `name @ url` keeps the name."""
    runtime = set()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        if "://" in line and " @ " not in line:
            continue
        name = _req_name(line)
        if name:
            runtime.add(name)
    return runtime, set()


def _toml(text):
    if tomllib is None:
        raise RuntimeError("tomllib unavailable")
    return tomllib.loads(text)


def _table(obj, *path):
    for key in path:
        obj = obj.get(key) if isinstance(obj, dict) else None
    return obj if isinstance(obj, dict) else {}


def _spec_names(specs):
    return {n for n in (_req_name(s) for s in (specs if isinstance(specs, list) else ())
                        if isinstance(s, str)) if n}


def _parse_pyproject(text):
    """PEP 621 `[project]` dependencies (runtime) and optional-dependencies (dev), plus
    Poetry `[tool.poetry.dependencies]` (runtime, `python` excluded) and the Poetry dev group."""
    data = _toml(text)
    project = _table(data, "project")
    runtime = _spec_names(project.get("dependencies"))
    dev = set()
    for group in _table(project, "optional-dependencies").values():
        dev |= _spec_names(group)
    poetry = _table(data, "tool", "poetry")
    runtime |= {k.lower() for k in _table(poetry, "dependencies") if k.lower() != "python"}
    dev |= {k.lower() for k in _table(poetry, "group", "dev", "dependencies")}
    return runtime, dev


# `{:name, ...` up to the next brace; only the atoms of an `only:` option decide dev use.
# Tuples elsewhere in a mix.exs may add names no signal lists, which is harmless.
_MIX_DEP_RE = re.compile(r"\{:([a-z_][A-Za-z0-9_]*)\s*,([^{}]*)")
_MIX_ONLY_RE = re.compile(r"only:\s*(\[[^\]]*\]|:[a-z_]+)")
_MIX_ATOM_RE = re.compile(r":([a-z_]+)")


def _parse_mix_exs(text):
    runtime, dev = set(), set()
    for m in _MIX_DEP_RE.finditer(text):
        only = _MIX_ONLY_RE.search(m.group(2))
        atoms = set(_MIX_ATOM_RE.findall(only.group(1))) if only else set()
        if atoms and atoms <= {"dev", "test"}:
            dev.add(m.group(1))
        else:
            runtime.add(m.group(1))
    return runtime, dev


def _strip_xml_comments(text):
    out, i = [], 0
    while True:
        j = text.find("<!--", i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        k = text.find("-->", j + 4)
        if k < 0:
            break
        i = k + 3
    return "".join(out)


# One regex over the tags that matter, one pass, no nested quantifiers.
_POM_TAG_RE = re.compile(r"<(/?)(dependencyManagement|plugins|dependency|artifactId|scope)\b[^>]*>([^<]*)")


def _parse_pom(text):
    """artifactIds inside <dependency> blocks; scope `test` is dev. A BOM entry under
    <dependencyManagement> and a plugin's own dependencies are not this project's."""
    runtime, dev = set(), set()
    skip, in_dep, artifact, scope = 0, False, "", ""
    for m in _POM_TAG_RE.finditer(_strip_xml_comments(text)):
        if m.group(0).endswith("/>"):
            continue
        closing, tag, body = m.group(1) == "/", m.group(2), m.group(3).strip()
        if tag in ("dependencyManagement", "plugins"):
            skip = max(0, skip - 1) if closing else skip + 1
        elif tag == "dependency":
            if closing and in_dep and skip == 0 and artifact:
                (dev if scope == "test" else runtime).add(artifact)
            in_dep, artifact, scope = (not closing), "", ""
        elif in_dep and not closing:
            if tag == "artifactId" and not artifact:
                artifact = body.lower()
            elif tag == "scope":
                scope = body.lower()
    return runtime, dev


_GRADLE_RE = re.compile(
    r"^[ \t]*(implementation|api|compileOnly|runtimeOnly|testImplementation|testCompileOnly|"
    r"testRuntimeOnly|androidTestImplementation)[ \t]*\(?[ \t]*['\"]([^'\":\s]+):([^'\":\s]+)[^'\"]*['\"]",
    re.M)


def _parse_gradle(text):
    """`implementation 'g:a:v'` and `implementation("g:a:v")` -> the artifact part;
    `test*` configurations are dev. Version-catalog aliases are a recall gap."""
    runtime, dev = set(), set()
    for m in _GRADLE_RE.finditer(text):
        name = m.group(3).lower()
        (dev if m.group(1).lower().startswith(("test", "androidtest")) else runtime).add(name)
    return runtime, dev


def _parse_cargo(text):
    data = _toml(text)
    return _names(data.get("dependencies")), _names(data.get("dev-dependencies"))


def _gomod_module(code, comment):
    """The module path of one require entry, or '' (an `// indirect` entry is not declared)."""
    parts = code.split()
    if "indirect" in comment or len(parts) < 2:
        return ""
    return parts[0].lower()


def _parse_gomod(text):
    runtime, in_block = set(), False
    for raw in text.splitlines():
        line = raw.strip()
        if in_block:
            if line.startswith(")"):
                in_block = False
                continue
            code, _sep, comment = line.partition("//")
            name = _gomod_module(code, comment)
            if name:
                runtime.add(name)
        elif line.split(None, 1)[:1] == ["require"]:
            rest = line[len("require"):].strip()
            if rest.startswith("("):
                in_block = True
                continue
            code, _sep, comment = rest.partition("//")
            name = _gomod_module(code, comment)
            if name:
                runtime.add(name)
    return runtime, set()


# Manifests are matched by exact lower-cased basename.
PARSERS = {
    "package.json": _parse_package_json,
    "requirements.txt": _parse_requirements,
    "pyproject.toml": _parse_pyproject,
    "mix.exs": _parse_mix_exs,
    "pom.xml": _parse_pom,
    "build.gradle": _parse_gradle,
    "build.gradle.kts": _parse_gradle,
    "cargo.toml": _parse_cargo,
    "go.mod": _parse_gomod,
}
ECOSYSTEMS = {
    "package.json": "npm", "requirements.txt": "pip", "pyproject.toml": "pyproject",
    "mix.exs": "mix", "pom.xml": "maven", "build.gradle": "gradle",
    "build.gradle.kts": "gradle", "cargo.toml": "cargo", "go.mod": "go",
}

# Dependency-class signals: trait -> {declared name: evidence class}. Closed and fitted
# (RESEARCH A4; executors may add names, never remove these): an unknown library is a
# recall gap that reads ABSENT only when a manifest was visible, never a precision gap.
# Matching is name equality on parsed names with `_` and `-` folded together, never a
# substring (family_scan read `ecto` inside `vector`).
def _strong(*names):
    return {n: STRONG for n in names}


DEP_SIGNALS = {
    "persistent": _strong(
        "prisma", "@prisma/client", "drizzle-orm", "typeorm", "sequelize", "mongoose",
        "mongodb", "pg", "mysql2", "better-sqlite3", "sqlite3", "knex",
        "@supabase/supabase-js", "sqlalchemy", "asyncpg", "psycopg2", "psycopg2-binary",
        "psycopg", "alembic", "peewee", "django", "ecto", "ecto_sql", "postgrex", "myxql",
        "hibernate-core", "spring-boot-starter-data-jpa", "mybatis", "diesel", "sqlx",
        "rusqlite", "gorm.io/gorm"),
    "external_effect": _strong(
        "stripe", "@stripe/stripe-js", "resend", "nodemailer", "@sendgrid/mail", "sendgrid",
        "twilio", "axios", "node-fetch", "got", "requests", "httpx", "aiohttp", "openai",
        "anthropic", "@anthropic-ai/sdk", "discord.js", "discord.py", "finch", "req",
        "httpoison", "tesla", "swoosh", "okhttp", "retrofit", "reqwest", "slack_sdk",
        "@slack/web-api"),
    "money": _strong(
        "stripe", "@stripe/stripe-js", "stripity_stripe", "braintree",
        "@paypal/checkout-server-sdk", "mollie-api-python", "@lemonsqueezy/lemonsqueezy.js",
        "vault", "vaultapi"),
    "multi_actor": _strong(
        "phoenix", "phoenix_live_view", "phoenix_pubsub", "socket.io", "ws",
        "@supabase/realtime-js", "channels", "paper-api", "spigot-api", "bukkit",
        "velocity-api", "colyseus", "pusher"),
    "scheduled": _strong(
        "oban", "quantum", "celery", "apscheduler", "rq-scheduler", "schedule", "node-cron",
        "node-schedule", "cron", "bull", "bullmq", "agenda", "quartz", "@nestjs/schedule"),
    "distributed": _strong(
        "libcluster", "horde", "kafkajs", "kafka-python", "confluent-kafka", "amqplib",
        "pika", "nats", "@grpc/grpc-js", "grpcio"),
    # A library for policy layers says little about how many layers there are: always WEAK.
    "policy_layers": {n: WEAK for n in (
        "casl", "@casl/ability", "oso", "casbin", "pycasbin", "django-guardian", "bodyguard")},
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


def _canon(name):
    """`_` and `-` fold together (pip treats them alike); both sides of a match use this."""
    return name.lower().replace("_", "-")


def _dependency_evidence(parsed, found):
    """Add declared-dependency evidence. A name declared only in a dev section is WEAK.
    The evidence string carries the name as declared, lower-cased."""
    tables = {t: {_canon(k): v for k, v in table.items()} for t, table in DEP_SIGNALS.items()}
    for rel, _eco, runtime, dev in parsed:
        for trait, table in tables.items():
            for name in sorted(runtime):
                cls = table.get(_canon(name))
                if cls:
                    found[trait].append((cls, "%s:%s" % (rel, name), "dependency"))
            for name in sorted(dev - runtime):
                if _canon(name) in table:
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
    ui = {"count": 0, "samples": []}

    def onerror(_exc):          # a directory that could not be listed: counted, never raised
        walk["unreadable"] += 1

    for dirpath, dirnames, filenames in _walk(root, followlinks=False, onerror=onerror):
        if time.perf_counter() - start >= budget_s:
            walk["budget_hit"] = True
            break
        # Skipped trees, symlinks and junctions are pruned before the walk descends.
        dirnames[:] = sorted(d for d in dirnames
                             if d not in SKIP_DIRS and not _is_link(os.path.join(dirpath, d)))
        filenames.sort()
        rel_dir = _safe_rel(root, dirpath)
        if rel_dir is None:
            continue
        parts = [] if rel_dir == "." else [p.lower() for p in rel_dir.split("/")]
        _dir_markers(rel_dir, parts, dirnames, filenames, found)
        for fn in filenames:
            if walk["files"] >= cap:
                walk["truncated"] = True
                break
            walk["files"] += 1
            if _is_secret_name(fn):         # counted, never opened, never named in evidence
                continue
            rel = fn if rel_dir == "." else rel_dir + "/" + fn
            _file_markers(dirpath, rel, rel_dir, parts, fn, walk, found, ui)
            if fn.lower() in PARSERS:
                _read_manifest(root, dirpath, fn, walk, parsed, ecosystems)
        if walk["truncated"]:
            break
    walk["ecosystems"] = sorted(ecosystems)
    walk["seconds"] = round(time.perf_counter() - start, 3)
    _dependency_evidence(parsed, found)
    if ui["count"]:
        cls = STRONG if ui["count"] >= UI_PRESENT_MIN else WEAK
        for sample in ui["samples"]:
            found["ui"].append((cls, sample, "%d ui files" % ui["count"]))
    traits = {t: _entitle(t, found[t], walk) for t in archetypes.TRAITS}
    return {"walk": walk, "traits": traits, "evidence_paths": _evidence_paths(found)}


def _evidence_paths(found):
    """Relative paths of the files that produced positive evidence, shallowest first,
    at most `archetypes.EVIDENCE_FILES_MAX`. These are what the reader re-stats: an
    edit to one of them moves a reading without moving any directory listing. A
    dependency item reads `<manifest path>:<name>`, so its path is cut at the last
    colon. Beyond the cap the remainder is covered only by the age bound."""
    paths = set()
    for items in found.values():
        for _cls, evidence, kind in items:
            paths.add(evidence.rsplit(":", 1)[0] if kind == "dependency" else evidence)
    return sorted(paths, key=lambda p: (p.count("/"), p))[:archetypes.EVIDENCE_FILES_MAX]


def produce(root, *, state_dir=None, cap=DEFAULT_CAP, budget_s=DEFAULT_BUDGET_S):
    """Scan the repository containing `root` and publish its trait cache.

    Returns {"outcome": WRITTEN, "path", "doc"}, or UNRESOLVABLE (nothing
    written) for a root that is not an absolute existing directory, or FAILED
    with the reason when anything goes wrong (nothing published).

    The document carries a `fingerprint` block that the reader compares: depth-1 and
    depth-2 fingerprints and the root manifest stats, all taken BEFORE the walk so a
    change made during the walk reads STALE on the next read instead of being
    absorbed; and the stats of the evidence files, taken right after it."""
    sroot = archetypes.subject_root(root)
    if sroot is None:
        return {"outcome": UNRESOLVABLE, "reason": "unresolvable-root"}
    tmp = None
    try:
        fingerprint = {"fp1": archetypes.fingerprint(sroot, 1),
                       "fp2": archetypes.fingerprint(sroot, 2),
                       "root_manifests": archetypes.root_manifest_stats(sroot)}
        result = scan(sroot, cap=cap, budget_s=budget_s)
        fingerprint["evidence_files"] = archetypes.evidence_stats(sroot, result["evidence_paths"])
        path = archetypes.cache_path(sroot, state_dir=state_dir)
        doc = {"schema": archetypes.SCHEMA, "repo_key": repo_key(sroot), "repo": sroot,
               "produced_at": time.time(), "producer": "trait_scan/1",
               "walk": result["walk"], "fingerprint": fingerprint,
               "traits": result["traits"]}
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
