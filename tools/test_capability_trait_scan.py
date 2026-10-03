"""V-TSCAN-* -- the structural trait producer of UCEP ROADMAP Phase 2.

What this file proves: `modules/capability_runtime/trait_scan.py` judges structural
traits from DECLARED dependency names (parsed per ecosystem) and from named
markers, never from a substring or free text; weak evidence is classed WEAK; and
what it reads or skips is bounded. Every gate that says "nothing found" carries a
control in which the same detector finds the thing, so a detector that stopped
detecting cannot show a clean green.

Hermetic: HOME, USERPROFILE and CLAUDE_STATE_DIR point at a temp dir BEFORE any
`modules/` import, and the gates call `ts.scan(repo)` directly (no cache is written).

The gate list grows across plans; `EXPECTED` is a literal that the exit code
enforces, so a gate that silently stops running cannot read as green.

Run: python tools/test_capability_trait_scan.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile

# -- hermetic environment: BEFORE any import under modules/ ----------------------
_HOME = tempfile.mkdtemp(prefix="ctscan-home-")
_SAVED_ENV = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE", "CLAUDE_STATE_DIR")}
os.environ["HOME"] = _HOME
os.environ["USERPROFILE"] = _HOME
os.environ["CLAUDE_STATE_DIR"] = os.path.join(_HOME, ".claude", "state")

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

# Guarded imports: a RED run fails on gate predicates and never crashes.
try:
    from modules.capability_runtime import archetypes as ar
    _AR_ERR = ""
except Exception as _exc:  # noqa: BLE001
    ar, _AR_ERR = None, "%s: %s" % (type(_exc).__name__, _exc)
try:
    from modules.capability_runtime import trait_scan as ts
    _TS_ERR = ""
except Exception as _exc:  # noqa: BLE001
    ts, _TS_ERR = None, "%s: %s" % (type(_exc).__name__, _exc)

_PASS = 0
_FAIL = 0
_TEMP_DIRS = [_HOME]


def check(gate: str, cond, evidence) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-34s %s" % (gate, str(evidence)[:170]))
    else:
        _FAIL += 1
        print("  FAIL %-34s %s" % (gate, str(evidence)[:600]))


def run_gate(name: str, pred) -> None:
    """pred() -> (ok, evidence). An exception is a FAIL carrying `type: message`."""
    try:
        ok, evidence = pred()
    except Exception as exc:  # noqa: BLE001
        ok, evidence = False, "%s: %s" % (type(exc).__name__, exc)
    check(name, ok, evidence)


class Counting:
    """Counting wrapper: lets a gate prove its seam was reached."""
    def __init__(self, fn):
        self.fn, self.calls = fn, 0

    def __call__(self, *a, **k):
        self.calls += 1
        return self.fn(*a, **k)


def make_repo(files: dict) -> str:
    """A fixture repo (empty .git so canonical_repo stops there) holding `files`:
    relative path -> text; a path ending in `/` is an empty directory."""
    root = tempfile.mkdtemp(prefix="ctscan-repo-")
    _TEMP_DIRS.append(root)
    os.makedirs(os.path.join(root, ".git"))
    for rel, text in files.items():
        full = os.path.join(root, *[p for p in rel.split("/") if p])
        if rel.endswith("/"):
            os.makedirs(full, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    return root


_READINGS = []   # every reading any gate produced: V-TSCAN-EVIDENCE-SHAPE audits them all


def scan_files(files: dict, **kw) -> dict:
    res = ts.scan(make_repo(files), **kw)
    _READINGS.extend(res["traits"].values())
    return res


def with_manifest(files: dict) -> dict:
    """Add a neutral manifest, so a trait with no evidence can be entitled to read ABSENT."""
    out = dict(files)
    out.setdefault("package.json", json.dumps({"name": "fixture", "dependencies": {"react": "1.0.0"}}))
    return out


def reading_of(files: dict, trait: str) -> dict:
    return scan_files(with_manifest(files))["traits"][trait]


def npm(deps=None, dev=None, **extra) -> str:
    doc = {"name": "fixture"}
    if deps is not None:
        doc["dependencies"] = {d: "1.0.0" for d in deps}
    if dev is not None:
        doc["devDependencies"] = {d: "1.0.0" for d in dev}
    doc.update(extra)
    return json.dumps(doc)


def state_of(result: dict, trait: str) -> str:
    return result["traits"][trait]["state"]


def _sets(fn, text):
    runtime, dev = fn(text)
    return set(runtime), set(dev)


# -- the eight parsers -------------------------------------------------------------

NPM_TEXT = json.dumps({
    "name": "x",
    "dependencies": {"React": "1", "left-pad": "1"},
    "devDependencies": {"jest": "1"},
    "peerDependencies": {"react-dom": "1"},
    "optionalDependencies": {"fsevents": "1"},
})

PIP_TEXT = """# a comment

requests==2.31.0
uvicorn[standard]>=0.20
numpy ; python_version < "3.9"
Flask~=2.0  # inline comment
-r other.txt
-e git+https://example.com/x#egg=y

pydantic>=1.0,<3
psycopg2_binary==2.9.9
mypkg @ https://example.com/mypkg.zip
https://example.com/plain-url.tar.gz
"""

PYPROJECT_TEXT = """[project]
name = "x"
dependencies = ["fastapi>=0.100", "uvicorn[standard]", "SQLAlchemy ; python_version > '3.8'"]

[project.optional-dependencies]
dev = ["pytest>=7", "ruff"]
docs = ["mkdocs"]

[tool.poetry.dependencies]
python = "^3.11"
httpx = "^0.27"

[tool.poetry.group.dev.dependencies]
black = "^24"
"""

MIX_TEXT = """defmodule Fixture.MixProject do
  use Mix.Project
  defp deps do
    [
      {:phoenix, "~> 1.7"},
      {:ecto_sql, "~> 3.10"},
      {:credo, "~> 1.7", only: [:dev, :test], runtime: false},
      {:dialyxir, "~> 1.4", only: :dev},
      {:mox, "~> 1.0", only: [:test]},
      {:jason, ">= 0.0.0", only: [:dev, :prod]},
      {:local_dep, path: "../local"}
    ]
  end
end
"""

POM_TEXT = """<project>
  <dependencyManagement>
    <dependencies>
      <dependency><groupId>g</groupId><artifactId>managed-only</artifactId></dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
    <dependency>
      <groupId>org.hibernate</groupId>
      <artifactId>Hibernate-Core</artifactId>
      <version>6.4.0</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>junit</groupId><artifactId>junit</artifactId><scope>test</scope>
    </dependency>
    <!-- <dependency><artifactId>commented-out</artifactId></dependency> -->
  </dependencies>
  <build><plugins><plugin>
    <artifactId>maven-plugin-x</artifactId>
    <dependencies><dependency><artifactId>plugin-only</artifactId></dependency></dependencies>
  </plugin></plugins></build>
</project>
"""

GRADLE_TEXT = """plugins { id 'java' }
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web:3.2.0'
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    api "com.squareup.retrofit2:retrofit:2.9.0"
    compileOnly 'org.projectlombok:lombok:1.18.30'
    runtimeOnly 'org.postgresql:postgresql:42.7.0'
    testImplementation 'junit:junit:4.13.2'
    testImplementation("org.mockito:mockito-core:5.8.0")
    // implementation 'com.example:commented-out:1'
}
"""

CARGO_TEXT = """[package]
name = "x"

[dependencies]
serde = "1"
sqlx = { version = "0.7", features = ["sqlite"] }
Tokio = { version = "1" }

[dev-dependencies]
criterion = "0.5"
"""

GOMOD_TEXT = """module example.com/m

go 1.21

require (
\tgithub.com/gin-gonic/gin v1.9.1
\tgorm.io/gorm v1.25.0 // indirect
\tgithub.com/lib/pq v1.10.9
)

require golang.org/x/text v0.14.0

replace github.com/lib/pq => ./local-pq
"""


def pred_V_TSCAN_PARSE_NPM():
    got = _sets(ts._parse_package_json, NPM_TEXT)
    want = ({"react", "left-pad", "react-dom", "fsevents"}, {"jest"})
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_PIP():
    got = _sets(ts._parse_requirements, PIP_TEXT)
    # Names are returned as declared, lower-cased: `_` and `-` are folded at match time.
    want = ({"requests", "uvicorn", "numpy", "flask", "pydantic", "psycopg2_binary", "mypkg"}, set())
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_PYPROJECT():
    got = _sets(ts._parse_pyproject, PYPROJECT_TEXT)
    want = ({"fastapi", "uvicorn", "sqlalchemy", "httpx"}, {"pytest", "ruff", "mkdocs", "black"})
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_MIX():
    got = _sets(ts._parse_mix_exs, MIX_TEXT)
    want = ({"phoenix", "ecto_sql", "jason", "local_dep"}, {"credo", "dialyxir", "mox"})
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_MAVEN():
    got = _sets(ts._parse_pom, POM_TEXT)
    want = ({"spring-boot-starter-web", "hibernate-core"}, {"junit"})
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_GRADLE():
    got = _sets(ts._parse_gradle, GRADLE_TEXT)
    want = ({"spring-boot-starter-web", "kotlinx-coroutines-core", "retrofit", "lombok", "postgresql"},
            {"junit", "mockito-core"})
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_CARGO():
    got = _sets(ts._parse_cargo, CARGO_TEXT)
    want = ({"serde", "sqlx", "tokio"}, {"criterion"})
    return got == want, "runtime=%s dev=%s" % (sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_GOMOD():
    got = _sets(ts._parse_gomod, GOMOD_TEXT)
    want = ({"github.com/gin-gonic/gin", "github.com/lib/pq", "golang.org/x/text"}, set())
    return got == want, "runtime=%s dev=%s (the `// indirect` gorm.io/gorm is not a declared dependency)" % (
        sorted(got[0]), sorted(got[1]))


def pred_V_TSCAN_PARSE_MALFORMED():
    repo = make_repo({"package.json": "{not json at all", "pyproject.toml": "[[[ not toml"})
    res = ts.scan(repo)
    walk = res["walk"]
    errors = sorted(e["path"] for e in walk["manifest_errors"])
    p = res["traits"]["persistent"]
    ok = (walk["manifests_parsed"] == 0 and errors == ["package.json", "pyproject.toml"]
          and p["state"] == ar.UNJUDGED and p["reason"] == "no-manifest-ecosystem")
    return ok, "manifests_parsed=%s errors=%s persistent=%s/%s" % (
        walk["manifests_parsed"], errors, p["state"], p["reason"])


def pred_V_TSCAN_DEP_NOT_TEXT():
    """RESEARCH F5.1: a description string fired `scheduled`. It must not."""
    text = npm(deps=["react"], description="schedule every job and charge customers by card")
    res = scan_files({"package.json": text})
    bad = [t for t in ("scheduled", "money") if state_of(res, t) in (ar.PRESENT, ar.WEAK)]
    # Control: the same detector fires on a declared dependency, so a clean result is not blindness.
    ctl = scan_files({"package.json": npm(deps=["react", "node-cron", "stripe"])})
    control = state_of(ctl, "scheduled") == ar.PRESENT and state_of(ctl, "money") == ar.PRESENT
    ok = res["walk"]["manifests_parsed"] == 1 and not bad and control
    return ok, "text-only: scheduled=%s money=%s (bad=%s); control declared deps: scheduled=%s money=%s" % (
        state_of(res, "scheduled"), state_of(res, "money"), bad,
        state_of(ctl, "scheduled"), state_of(ctl, "money"))


def pred_V_TSCAN_SUBSTRING_NOT_DEP():
    """family_scan incident: `ecto` matched inside `vector` in 129 of 163 repos."""
    res = scan_files({"package.json": npm(deps=["vector-math", "detector-js", "selector-engine"])})
    p = res["traits"]["persistent"]
    ctl = scan_files({"package.json": npm(deps=["vector-math", "pg"])})
    c = ctl["traits"]["persistent"]
    ok = (p["state"] == ar.ABSENT and c["state"] == ar.PRESENT and c["evidence"] == ["package.json:pg"])
    return ok, "lookalike names: persistent=%s; control with pg: %s %s" % (p["state"], c["state"], c["evidence"])


def pred_V_TSCAN_DEV_ONLY_WEAK():
    res = scan_files({"package.json": npm(deps=["react"], dev=["stripe"])})
    states = (state_of(res, "external_effect"), state_of(res, "money"))
    ctl = scan_files({"package.json": npm(deps=["stripe"])})
    cstates = (state_of(ctl, "external_effect"), state_of(ctl, "money"))
    ok = states == (ar.WEAK, ar.WEAK) and cstates == (ar.PRESENT, ar.PRESENT)
    return ok, "stripe in devDependencies: external_effect/money=%s; control in dependencies: %s" % (states, cstates)


# trait -> (manifest, text with one listed signal at runtime, expected evidence, text without it)
POLES = {
    "persistent": ("package.json", npm(deps=["prisma"]), "package.json:prisma", npm(deps=["left-pad"])),
    "external_effect": ("requirements.txt", "requests==2.31\n", "requirements.txt:requests", "flask==3.0\n"),
    "money": ("requirements.txt", "braintree==4.0\n", "requirements.txt:braintree", "flask==3.0\n"),
    "multi_actor": ("mix.exs", "defp deps do\n  [{:phoenix, \"~> 1.7\"}]\nend\n", "mix.exs:phoenix",
                    "defp deps do\n  [{:jason, \"~> 1.4\"}]\nend\n"),
    "scheduled": ("package.json", npm(deps=["node-cron"]), "package.json:node-cron", npm(deps=["left-pad"])),
    "distributed": ("requirements.txt", "kafka-python==2.0\n", "requirements.txt:kafka-python", "flask==3.0\n"),
    "policy_layers": ("requirements.txt", "casbin==1.0\n", "requirements.txt:casbin", "flask==3.0\n"),
}


def pred_V_TSCAN_DEP_POLES():
    problems, lines = [], []
    for trait, (manifest, pos, want_ev, neg) in sorted(POLES.items()):
        want_state = ar.WEAK if trait == "policy_layers" else ar.PRESENT
        p = scan_files({manifest: pos})["traits"][trait]
        n = scan_files({manifest: neg})["traits"][trait]
        lines.append("%s:%s/%s|%s" % (trait, p["state"], want_ev if want_ev in p["evidence"] else p["evidence"], n["state"]))
        if p["state"] != want_state or want_ev not in p["evidence"]:
            problems.append("%s positive: %s %s (want %s %s)" % (trait, p["state"], p["evidence"], want_state, want_ev))
        if n["state"] != ar.ABSENT:
            problems.append("%s negative: %s/%s (want ABSENT)" % (trait, n["state"], n["reason"]))
    return not problems and len(lines) == 7, "; ".join(problems) or "14 outcomes: " + " ".join(lines)


def pred_V_TSCAN_MANIFEST_BOUNDED():
    pad = " " * (ts.MANIFEST_READ_MAX + 2000)
    big = '{"name": "x", "description": "%s", "dependencies": {"stripe": "1"}}' % pad
    res = scan_files({"package.json": big})
    walk = res["walk"]
    errs = [e["path"] for e in walk["manifest_errors"]]
    # Control: the same document with a small pad parses and the detector fires.
    small = '{"name": "x", "description": "%s", "dependencies": {"stripe": "1"}}' % (" " * 50)
    ctl = scan_files({"package.json": small})
    ok = (state_of(res, "external_effect") != ar.PRESENT and errs == ["package.json"]
          and walk["manifests_parsed"] == 0 and state_of(ctl, "external_effect") == ar.PRESENT
          and len(big) > ts.MANIFEST_READ_MAX)
    return ok, "oversized manifest (%d bytes > %d): external_effect=%s manifest_errors=%s; control small: %s" % (
        len(big), ts.MANIFEST_READ_MAX, state_of(res, "external_effect"), errs, state_of(ctl, "external_effect"))


# -- plan 02-03 Task 3: marker classes, weak evidence, skips, secrets ---------------
# Every marker fixture also carries a neutral manifest (a parsed `react` package.json),
# so "nothing found" reads ABSENT and a missing detector shows as ABSENT, not as a
# hidden UNJUDGED.

def pred_V_TSCAN_MARKER_PERSISTENT():
    pos = [("schema.prisma", "model A {}\n"), ("schema.sql", "create table t (id int);\n"),
           ("migrations/", ""), ("priv/repo/migrations/", ""), ("alembic/", "")]
    problems, lines = [], []
    for rel, text in pos:
        want = rel.rstrip("/")
        r = reading_of({rel: text}, "persistent")
        lines.append("%s=%s" % (want, r["state"]))
        if r["state"] != ar.PRESENT or want not in r["evidence"]:
            problems.append("%s: %s %s" % (want, r["state"], r["evidence"]))
    for rel in ("docs/schema-notes.md", "schema.md"):
        r = reading_of({rel: "notes about a schema\n"}, "persistent")
        lines.append("%s=%s" % (rel, r["state"]))
        if r["state"] != ar.ABSENT:
            problems.append("lookalike name %s read %s (names are exact, never substrings)" % (rel, r["state"]))
    return not problems, "; ".join(problems) or " ".join(lines)


def pred_V_TSCAN_DATAFILE_WEAK():
    """RESEARCH F5.3: a data file is not code, so it is WEAK evidence of persistence."""
    items = ["data/app.db", "x.sqlite", "x.sqlite3", "world/level.dat", "world/region/r.0.0.mca", "playerdata/"]
    problems, lines = [], []
    for rel in items:
        want = rel.rstrip("/")
        r = reading_of({rel: "x"}, "persistent")
        lines.append("%s=%s" % (want, r["state"]))
        if r["state"] != ar.WEAK or want not in r["evidence"]:
            problems.append("%s: %s %s (want WEAK, never PRESENT)" % (want, r["state"], r["evidence"]))
    ctl = reading_of({"Thumbs.db": "x"}, "persistent")
    if ctl["state"] != ar.ABSENT:
        problems.append("CONTROL: a Windows thumbnail cache Thumbs.db read %s" % ctl["state"])
    return not problems, "; ".join(problems) or " ".join(lines) + "; Thumbs.db=ABSENT"


def pred_V_TSCAN_CODE_MODULE_WEAK():
    """R-3: a source module under a save/persistence/storage segment is WEAK and provisional."""
    rel = "src/engine/save/save_manager.c"
    r = reading_of({rel: "int save(void) { return 0; }\n"}, "persistent")
    problems = []
    if not (r["state"] == ar.WEAK and rel in r["evidence"]):
        problems.append("%s: %s %s" % (rel, r["state"], r["evidence"]))
    for neg in ("src/engine/render/draw.c", "docs/storage/notes.md", "src/storage.c"):
        n = reading_of({neg: "x\n"}, "persistent")
        if n["state"] != ar.ABSENT:
            problems.append("negative %s read %s" % (neg, n["state"]))
    return not problems, "; ".join(problems) or (
        "%s -> persistent WEAK, evidence %s; this class is provisional (R-3): KobiiSports Resort "
        "calibration is Phase 7 and is not planned here" % (rel, r["evidence"]))


def pred_V_TSCAN_MARKER_DISTRIBUTED():
    strong = [("docker-compose.yml", "services: {}\n"), ("compose.yaml", "services: {}\n"),
              ("fly.toml", "app = 'x'\n"),
              ("k8s/app.yaml", "apiVersion: apps/v1\nkind: Deployment\nmetadata: {}\n"),
              ("helm/templates/db.yaml", "kind: StatefulSet\n"), ("deploy/job.yaml", "kind: CronJob\n")]
    problems, lines = [], []
    for rel, text in strong:
        r = reading_of({rel: text}, "distributed")
        lines.append("%s=%s" % (rel, r["state"]))
        if r["state"] != ar.PRESENT or rel not in r["evidence"]:
            problems.append("%s: %s %s" % (rel, r["state"], r["evidence"]))
    d = reading_of({"Dockerfile": "FROM scratch\n"}, "distributed")
    if d["state"] != ar.WEAK:
        problems.append("lone Dockerfile read %s (want WEAK)" % d["state"])
    for rel, text in (("k8s/notes.yaml", "kind: ConfigMap\n"), ("docs/example.yaml", "kind: Deployment\n")):
        n = reading_of({rel: text}, "distributed")
        if n["state"] != ar.ABSENT:
            problems.append("%s read %s (no workload kind under a k8s directory)" % (rel, n["state"]))
    return not problems, "; ".join(problems) or " ".join(lines) + " Dockerfile=WEAK notes/example=ABSENT"


def pred_V_TSCAN_MARKER_SCHEDULED():
    flow = "name: nightly\non:\n  schedule:\n    - cron: '0 3 * * *'\njobs: {}\n"
    problems = []
    r = reading_of({".github/workflows/nightly.yml": flow}, "scheduled")
    if r["state"] != ar.PRESENT or ".github/workflows/nightly.yml" not in r["evidence"]:
        problems.append("workflow with cron: %s %s" % (r["state"], r["evidence"]))
    for label, text in (("no-cron", "name: ci\non: push\njobs: {}\n"),
                        ("commented-cron", "name: ci\non: push\n# cron: later\njobs: {}\n")):
        n = reading_of({".github/workflows/ci.yml": text}, "scheduled")
        if n["state"] != ar.ABSENT:
            problems.append("%s workflow read %s" % (label, n["state"]))
    v = reading_of({"vercel.json": json.dumps({"crons": [{"path": "/api/x", "schedule": "0 * * * *"}]})}, "scheduled")
    if v["state"] != ar.PRESENT or "vercel.json" not in v["evidence"]:
        problems.append("vercel.json with crons: %s %s" % (v["state"], v["evidence"]))
    vn = reading_of({"vercel.json": json.dumps({"rewrites": []})}, "scheduled")
    if vn["state"] != ar.ABSENT:
        problems.append("vercel.json without crons read %s" % vn["state"])
    return not problems, "; ".join(problems) or \
        "workflow cron PRESENT, no-cron and commented cron ABSENT, vercel crons PRESENT, vercel without crons ABSENT"


def pred_V_TSCAN_MARKER_MULTI_ACTOR():
    problems = []
    for rel in ("src/main/resources/plugin.yml", "paper-plugin.yml"):
        r = reading_of({rel: "name: X\nmain: a.b.C\n"}, "multi_actor")
        if r["state"] != ar.PRESENT or rel not in r["evidence"]:
            problems.append("%s: %s %s" % (rel, r["state"], r["evidence"]))
    n = reading_of({"plugin.json": "{}\n"}, "multi_actor")
    if n["state"] != ar.ABSENT:
        problems.append("plugin.json read %s" % n["state"])
    return not problems, "; ".join(problems) or "plugin.yml and paper-plugin.yml PRESENT, plugin.json ABSENT"


def pred_V_TSCAN_MARKER_POLICY_WEAK():
    problems = []
    for rel, want in (("policies/read.rego", "policies"), ("rls/rule.sql", "rls")):
        r = reading_of({rel: "x\n"}, "policy_layers")
        if r["state"] != ar.WEAK or want not in r["evidence"]:
            problems.append("%s: %s %s (want WEAK)" % (rel, r["state"], r["evidence"]))
    n = reading_of({"policies/": ""}, "policy_layers")
    if n["state"] != ar.ABSENT:
        problems.append("an empty policies directory read %s" % n["state"])
    return not problems, "; ".join(problems) or "policies/ and rls/ holding a file are WEAK; an empty policies/ is ABSENT"


def pred_V_TSCAN_UI_THRESHOLD():
    def ui_reading(n):
        return reading_of({"src/c%02d.tsx" % i: "export {}\n" for i in range(n)}, "ui")
    got = {n: ui_reading(n) for n in (0, 5, 25)}
    want = {0: ar.ABSENT, 5: ar.WEAK, 25: ar.PRESENT}
    bad = ["%d files -> %s (want %s)" % (n, got[n]["state"], want[n]) for n in want if got[n]["state"] != want[n]]
    edge = {19: ui_reading(19)["state"], 20: ui_reading(20)["state"]}
    if edge != {19: ar.WEAK, 20: ar.PRESENT}:
        bad.append("threshold edge %s (want 19 WEAK, 20 PRESENT)" % edge)
    return not bad, "; ".join(bad) or "0 -> ABSENT, 5 -> WEAK, 25 -> PRESENT, edge 19 -> WEAK / 20 -> PRESENT (UI_PRESENT_MIN=%d)" % ts.UI_PRESENT_MIN


def pred_V_TSCAN_SKIP_VENDORED():
    skipped = {"vendor/lib/package.json": npm(deps=["stripe"]),
               "node_modules/pg/package.json": npm(deps=["pg"]),
               "Library/PackageCache/.tmp-1/clone/docs/migrations/001.sql": "create table t (id int);\n",
               "third_party/schema.prisma": "model A {}\n"}
    res = scan_files(skipped)
    leaked = {t: r["evidence"] for t, r in res["traits"].items() if r["evidence"]}
    # Control: the same files at paths that are not skipped DO produce evidence.
    moved = {"lib/package.json": npm(deps=["stripe"]), "pg/package.json": npm(deps=["pg"]),
             "docs/migrations/001.sql": "create table t (id int);\n", "models/schema.prisma": "model A {}\n"}
    ctl = scan_files(moved)
    ee, pe = ctl["traits"]["external_effect"], ctl["traits"]["persistent"]
    control = (ee["state"] == ar.PRESENT and "lib/package.json:stripe" in ee["evidence"]
               and pe["state"] == ar.PRESENT and "docs/migrations" in pe["evidence"]
               and "models/schema.prisma" in pe["evidence"])
    ok = not leaked and res["walk"]["files"] == 0 and res["walk"]["manifests_parsed"] == 0 and control
    return ok, "skipped trees: evidence=%s files=%d manifests=%d; control at plain paths: external_effect=%s persistent=%s %s" % (
        leaked, res["walk"]["files"], res["walk"]["manifests_parsed"], ee["state"], pe["state"], pe["evidence"])


def _make_link(link, target):
    """-> kind of link created. A junction on Windows (no privilege needed), else a symlink."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(target, link)
        return "directory junction (_winapi.CreateJunction)" if os.path.isjunction(link) else "NOT-A-JUNCTION"
    os.symlink(target, link, target_is_directory=True)
    return "directory symlink" if os.path.islink(link) else "NOT-A-SYMLINK"


def _drop_link(link):
    try:
        os.rmdir(link)        # a junction or Windows directory link: removes only the link
    except OSError:
        os.unlink(link)       # a POSIX symlink


def pred_V_TSCAN_JUNCTION_SKIP():
    """A10: a link back at the fixture root must be pruned, never followed."""
    files = {"package.json": npm(deps=["stripe"]), "src/a.txt": "x\n"}
    root = make_repo(files)
    before = ts.scan(root)
    link = os.path.join(root, "linkloop")
    kind = _make_link(link, root)
    try:
        if kind.startswith("NOT"):
            return False, "fixture link was not created as a link: %s" % kind
        after = ts.scan(root, cap=500)
        names = [e for r in after["traits"].values() for e in r["evidence"] if "linkloop" in e]
        # Control: with the link test disabled the walk DOES enter the link (the files
        # count changes or the cap cuts the walk), so this gate can fail.
        real_islink, real_isjunction = os.path.islink, getattr(os.path, "isjunction", None)
        os.path.islink = lambda p: False
        if real_isjunction is not None:
            os.path.isjunction = lambda p: False
        try:
            mutated = ts.scan(root, cap=500)
        finally:
            os.path.islink = real_islink
            if real_isjunction is not None:
                os.path.isjunction = real_isjunction
        m_names = [e for r in mutated["traits"].values() for e in r["evidence"] if "linkloop" in e]
        entered = (mutated["walk"]["files"] != before["walk"]["files"] or bool(m_names)
                   or mutated["walk"]["truncated"])
    finally:
        _drop_link(link)
    ok = (not after["walk"]["truncated"] and after["walk"]["files"] == before["walk"]["files"]
          and not names and entered)
    return ok, "%s: files with link %d == without %d, truncated=%s, evidence naming the link=%s; control with the link test disabled: files=%d truncated=%s link-evidence=%s" % (
        kind, after["walk"]["files"], before["walk"]["files"], after["walk"]["truncated"], names,
        mutated["walk"]["files"], mutated["walk"]["truncated"], m_names)


def pred_V_TSCAN_NO_SECRET_READ():
    """V8: only files selected by exact name are opened, and never a secret-shaped one."""
    import builtins
    import io
    files = {".env": "API_TOKEN=not-a-real-value\n", ".env.local": "X=1\n", "id_rsa": "not a key\n",
             "secrets/server.key": "not a key\n", "certs/site.pem": "not a certificate\n",
             "package.json": npm(deps=["react"]), ".github/workflows/ci.yml": "on: push\n",
             "k8s/app.yaml": "kind: ConfigMap\n", "vercel.json": "{}\n"}
    root = make_repo(files)
    opened = []

    def recorder(real):
        def wrapper(file, *a, **k):
            try:
                opened.append(os.fsdecode(file))
            except TypeError:
                pass          # an integer file descriptor names no path
            return real(file, *a, **k)
        return wrapper

    real_builtin, real_io = builtins.open, io.open
    own = vars(ts).get("open")
    builtins.open, io.open = recorder(real_builtin), recorder(real_io)
    if own is not None:
        ts.open = recorder(own)
    try:
        ts.scan(root)
    finally:
        builtins.open, io.open = real_builtin, real_io
        if own is not None:
            ts.open = own
    names = sorted({os.path.basename(p).lower() for p in opened})
    # Positive control: a wrapper that saw nothing proves nothing.
    if "package.json" not in names:
        return False, "BLIND: the open wrapper never saw package.json (opened=%s)" % names
    content_markers = {"ci.yml", "app.yaml", "vercel.json"}
    problems = []
    secret = [n for n in names if n.startswith(".env") or n.endswith((".key", ".pem")) or n.startswith("id_rsa")]
    if secret:
        problems.append("secret-shaped files opened: %s" % secret)
    stray = [n for n in names if n not in ts.PARSERS and n not in content_markers]
    if stray:
        problems.append("files opened outside the named set: %s" % stray)
    if not content_markers <= set(names):
        problems.append("named content markers never opened (the allow-list clause would be vacuous): %s" % sorted(content_markers - set(names)))
    return not problems, "; ".join(problems) or "opened basenames=%s, none secret-shaped" % names


def pred_V_TSCAN_PERSIST_VOCAB_SUPERSET():
    """The persistent vocabulary is a superset of tools/family_scan.MARKERS."""
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import family_scan
    markers = family_scan.MARKERS
    problems = []
    if not isinstance(getattr(ts, "MARKER_SIGNALS", None), dict) or "persistent" not in ts.MARKER_SIGNALS:
        problems.append("trait_scan.MARKER_SIGNALS has no persistent entry")
    for name in markers["orm_dependency"]:
        if ts.DEP_SIGNALS["persistent"].get(name) != ts.STRONG:
            problems.append("orm dependency %s is not a STRONG persistent signal" % name)
    for rel in markers["migrations_dir"]:
        r = reading_of({rel + "/": ""}, "persistent")
        if r["state"] != ar.PRESENT or rel not in r["evidence"]:
            problems.append("migrations_dir %s: %s %s" % (rel, r["state"], r["evidence"]))
    for name in markers["declared_schema"]:
        r = reading_of({name: "x\n"}, "persistent")
        if r["state"] != ar.PRESENT or name not in r["evidence"]:
            problems.append("declared_schema %s: %s %s" % (name, r["state"], r["evidence"]))
    for ext in markers["durable_ledger"]:
        r = reading_of({"ledger" + ext: "x"}, "persistent")
        if r["state"] != ar.WEAK or ("ledger" + ext) not in r["evidence"]:
            problems.append("durable_ledger %s: %s %s" % (ext, r["state"], r["evidence"]))
    n = sum(len(v) for v in markers.values())
    return not problems, "; ".join(problems) or "all %d family_scan.MARKERS entries recognised (orm STRONG, dirs and schemas STRONG, ledgers WEAK)" % n


def pred_V_TSCAN_EVIDENCE_SHAPE():
    """Last on purpose: audits every reading the earlier gates produced."""
    sentinel = "SENTINEL-NOT-STORED-7f3a91"
    res = ts.scan(make_repo({"package.json": npm(deps=["stripe"], description=sentinel), "README.md": sentinel + "\n"}))
    _READINGS.extend(res["traits"].values())
    blob = json.dumps(res)
    parsed = res["walk"]["manifests_parsed"] == 1 and state_of(res, "external_effect") == ar.PRESENT
    problems = []
    for r in _READINGS:
        for e in r["evidence"]:
            if "\\" in e or re.match(r"^[A-Za-z]:[\\/]", e) or e.startswith("/") or "\n" in e or len(e) > 300:
                problems.append("evidence not repo-relative with forward slashes: %r" % e[:80])
        if len(r["evidence"]) > ts.EVIDENCE_MAX:
            problems.append("%d evidence strings (max %d)" % (len(r["evidence"]), ts.EVIDENCE_MAX))
    with_evidence = sum(1 for r in _READINGS if r["evidence"])
    if len(_READINGS) < 100 or with_evidence < 20:
        problems.append("audit population too small to mean anything: %d readings, %d with evidence" % (
            len(_READINGS), with_evidence))
    if sentinel in blob:
        problems.append("file content reached the result: the manifest description was stored")
    if not parsed:
        problems.append("CONTROL: the sentinel manifest was not parsed, so its absence from the result proves nothing")
    return not problems, "; ".join(problems[:4]) or "%d readings (%d with evidence) all relative, forward-slash, <= %d each; sentinel not stored (manifest parsed)" % (
        len(_READINGS), with_evidence, ts.EVIDENCE_MAX)


GATES = [
    ("V-TSCAN-PARSE-NPM", pred_V_TSCAN_PARSE_NPM),
    ("V-TSCAN-PARSE-PIP", pred_V_TSCAN_PARSE_PIP),
    ("V-TSCAN-PARSE-PYPROJECT", pred_V_TSCAN_PARSE_PYPROJECT),
    ("V-TSCAN-PARSE-MIX", pred_V_TSCAN_PARSE_MIX),
    ("V-TSCAN-PARSE-MAVEN", pred_V_TSCAN_PARSE_MAVEN),
    ("V-TSCAN-PARSE-GRADLE", pred_V_TSCAN_PARSE_GRADLE),
    ("V-TSCAN-PARSE-CARGO", pred_V_TSCAN_PARSE_CARGO),
    ("V-TSCAN-PARSE-GOMOD", pred_V_TSCAN_PARSE_GOMOD),
    ("V-TSCAN-PARSE-MALFORMED", pred_V_TSCAN_PARSE_MALFORMED),
    ("V-TSCAN-DEP-NOT-TEXT", pred_V_TSCAN_DEP_NOT_TEXT),
    ("V-TSCAN-SUBSTRING-NOT-DEP", pred_V_TSCAN_SUBSTRING_NOT_DEP),
    ("V-TSCAN-DEV-ONLY-WEAK", pred_V_TSCAN_DEV_ONLY_WEAK),
    ("V-TSCAN-DEP-POLES", pred_V_TSCAN_DEP_POLES),
    ("V-TSCAN-MANIFEST-BOUNDED", pred_V_TSCAN_MANIFEST_BOUNDED),
    ("V-TSCAN-MARKER-PERSISTENT", pred_V_TSCAN_MARKER_PERSISTENT),
    ("V-TSCAN-DATAFILE-WEAK", pred_V_TSCAN_DATAFILE_WEAK),
    ("V-TSCAN-CODE-MODULE-WEAK", pred_V_TSCAN_CODE_MODULE_WEAK),
    ("V-TSCAN-MARKER-DISTRIBUTED", pred_V_TSCAN_MARKER_DISTRIBUTED),
    ("V-TSCAN-MARKER-SCHEDULED", pred_V_TSCAN_MARKER_SCHEDULED),
    ("V-TSCAN-MARKER-MULTI-ACTOR", pred_V_TSCAN_MARKER_MULTI_ACTOR),
    ("V-TSCAN-MARKER-POLICY-WEAK", pred_V_TSCAN_MARKER_POLICY_WEAK),
    ("V-TSCAN-UI-THRESHOLD", pred_V_TSCAN_UI_THRESHOLD),
    ("V-TSCAN-SKIP-VENDORED", pred_V_TSCAN_SKIP_VENDORED),
    ("V-TSCAN-JUNCTION-SKIP", pred_V_TSCAN_JUNCTION_SKIP),
    ("V-TSCAN-NO-SECRET-READ", pred_V_TSCAN_NO_SECRET_READ),
    ("V-TSCAN-PERSIST-VOCAB-SUPERSET", pred_V_TSCAN_PERSIST_VOCAB_SUPERSET),
    ("V-TSCAN-EVIDENCE-SHAPE", pred_V_TSCAN_EVIDENCE_SHAPE),   # last: audits every earlier reading
]

# A literal, enforced by the exit code: a count that satisfies itself would let a
# dropped gate read as green.
EXPECTED = 27


def main() -> int:
    try:
        if ts is None or ar is None:
            print("  note: module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR))
        for name, pred in GATES:
            run_gate(name, pred)
        print("CAPABILITY_TRAIT_SCAN_PASS=%d/%d  threshold=%d/%d" % (
            _PASS, _PASS + _FAIL, EXPECTED, EXPECTED))
        return 0 if _FAIL == 0 and _PASS == EXPECTED else 1
    finally:
        for key, old in _SAVED_ENV.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
        for d in _TEMP_DIRS:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
