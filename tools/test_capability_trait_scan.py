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


def scan_files(files: dict, **kw) -> dict:
    return ts.scan(make_repo(files), **kw)


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
]

# A literal, enforced by the exit code: a count that satisfies itself would let a
# dropped gate read as green.
EXPECTED = 14


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
