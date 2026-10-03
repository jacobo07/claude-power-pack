"""V-ARCH-* -- the capability subject contract of UCEP ROADMAP Phase 2.

What this file proves: a capability subject is produced from structure that an
out-of-band producer (`modules/capability_runtime/trait_scan.py`) wrote to a
per-user cache, read back WITHOUT any walk by `modules/capability_runtime/
archetypes.py`, and combined with the prompt into archetype assessments. A miss
reads UNJUDGED with a named cause, never ABSENT. The shared vocabulary (ten
traits, three single-segment archetype ids, a strength namespace, the bridge
into the donegate N/A vocabulary) is pinned here.

Hermetic: HOME, USERPROFILE and CLAUDE_STATE_DIR point at a temp dir BEFORE any
`modules/` import (01-REVIEW WR-07 lesson), and every produce/read call takes an
explicit `state_dir=`, so nothing is written under the real ~/.claude.

The gate list grows across plans 02-01..02-05; `EXPECTED` is a literal that the
exit code enforces, so a gate that silently stops running cannot read as green.

Run: python tools/test_capability_archetypes.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import ast
import glob
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# -- hermetic environment: BEFORE any import under modules/ ----------------------
_HOME = tempfile.mkdtemp(prefix="carch-home-")
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
try:
    from modules.tower import donegate
    _DG_ERR = ""
except Exception as _exc:  # noqa: BLE001
    donegate, _DG_ERR = None, "%s: %s" % (type(_exc).__name__, _exc)
try:
    from modules.gsd_x.mission import obligation
    _OB_ERR = ""
except Exception as _exc:  # noqa: BLE001
    obligation, _OB_ERR = None, "%s: %s" % (type(_exc).__name__, _exc)
try:
    from modules.tower import families
    from modules.tower.families import _fold, _match
    from modules.capability_runtime.applicability import _hits
    _FA_ERR = ""
except Exception as _exc:  # noqa: BLE001
    families = _fold = _match = _hits = None
    _FA_ERR = "%s: %s" % (type(_exc).__name__, _exc)

_PASS = 0
_FAIL = 0
_TEMP_DIRS = [_HOME]
_STATE_SEQ = [0]

STATE = os.path.join(_HOME, ".claude", "state", "tower")


def check(gate: str, cond, evidence) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-40s %s" % (gate, str(evidence)[:150]))
    else:
        _FAIL += 1
        print("  FAIL %-40s %s" % (gate, str(evidence)[:400]))


def run_gate(name: str, pred) -> None:
    """pred() -> (ok, evidence). An exception is a FAIL carrying `type: message`."""
    try:
        ok, evidence = pred()
    except Exception as exc:  # noqa: BLE001
        ok, evidence = False, "%s: %s" % (type(exc).__name__, exc)
    check(name, ok, evidence)


class Counting:
    """Counting wrapper: lets a drill prove the seam actually reached a replacement."""
    def __init__(self, fn):
        self.fn, self.calls = fn, 0

    def __call__(self, *a, **k):
        self.calls += 1
        return self.fn(*a, **k)


def new_state() -> str:
    """A fresh, empty state dir under the temp HOME (never the real one)."""
    _STATE_SEQ[0] += 1
    return os.path.join(_HOME, ".claude", "state", "tower-%d" % _STATE_SEQ[0])


def make_repo(kind: str) -> str:
    """A fixture repo with an empty .git directory, so canonical_repo stops there."""
    root = tempfile.mkdtemp(prefix="carch-repo-")
    _TEMP_DIRS.append(root)
    os.makedirs(os.path.join(root, ".git"))
    if kind == "persistent_prisma":
        os.makedirs(os.path.join(root, "prisma"))
        os.makedirs(os.path.join(root, "src"))
        with open(os.path.join(root, "prisma", "schema.prisma"), "w", encoding="utf-8") as fh:
            fh.write("model Subscription {\n  id Int @id\n}\n")
        with open(os.path.join(root, "package.json"), "w", encoding="utf-8") as fh:
            json.dump({"name": "fixture", "dependencies": {"@prisma/client": "^5.0.0"}}, fh)
        with open(os.path.join(root, "src", "index.js"), "w", encoding="utf-8") as fh:
            fh.write("console.log('fixture');\n")
    elif kind == "prisma_marker_react":
        # The persistent evidence is the schema marker; the root package.json declares only
        # react, so it produces NO evidence and is not in the cache's evidence-file list. Only
        # the root fingerprint can see an edit to it (plan 02-04 V-ARCH-STALE-MANIFEST).
        os.makedirs(os.path.join(root, "prisma"))
        with open(os.path.join(root, "prisma", "schema.prisma"), "w", encoding="utf-8") as fh:
            fh.write("model Subscription {\n  id Int @id\n}\n")
        with open(os.path.join(root, "package.json"), "w", encoding="utf-8") as fh:
            json.dump({"name": "fixture", "dependencies": {"react": "^18.0.0"}}, fh)
    elif kind == "ephemeral":
        os.makedirs(os.path.join(root, "src"))
        with open(os.path.join(root, "package.json"), "w", encoding="utf-8") as fh:
            json.dump({"name": "fixture", "dependencies": {"react": "^18.0.0"}}, fh)
        with open(os.path.join(root, "src", "App.jsx"), "w", encoding="utf-8") as fh:
            fh.write("export default function App() { return null }\n")
    elif kind in ("truncated_near", "truncated_far"):
        # A bulk directory of 60 small files next to a schema file. The walk visits
        # directories in sorted name order, so `00_models` comes before `zz_bulk`
        # (near: the marker is reached before a cap of 10 cuts the walk) and `zz_models`
        # comes after `aa_bulk` (far: the cap cuts the walk first).
        near = kind == "truncated_near"
        model_dir, bulk_dir = ("00_models", "zz_bulk") if near else ("zz_models", "aa_bulk")
        with open(os.path.join(root, "package.json"), "w", encoding="utf-8") as fh:
            json.dump({"name": "fixture", "dependencies": {"react": "^18.0.0"}}, fh)
        os.makedirs(os.path.join(root, model_dir))
        os.makedirs(os.path.join(root, bulk_dir))
        with open(os.path.join(root, model_dir, "schema.prisma"), "w", encoding="utf-8") as fh:
            fh.write("model Thing {\n  id Int @id\n}\n")
        for i in range(60):
            with open(os.path.join(root, bulk_dir, "n%02d.txt" % i), "w", encoding="utf-8") as fh:
                fh.write("x\n")
    elif kind in ("persistent_pip", "pip_fastapi", "scheduled_pip"):
        # No marker file: the only structure is a declared dependency in requirements.txt.
        reqs = {"persistent_pip": "sqlalchemy==2.0.30\nasyncpg\n",
                "pip_fastapi": "fastapi==0.110.0\n",
                "scheduled_pip": "apscheduler==3.10.4\n"}[kind]
        os.makedirs(os.path.join(root, "app"))
        with open(os.path.join(root, "requirements.txt"), "w", encoding="utf-8") as fh:
            fh.write(reqs)
        with open(os.path.join(root, "app", "models.py"), "w", encoding="utf-8") as fh:
            fh.write("VALUE = 1\n")
    elif kind == "external_npm":
        with open(os.path.join(root, "package.json"), "w", encoding="utf-8") as fh:
            json.dump({"name": "fixture", "dependencies": {"resend": "^3.0.0", "stripe": "^14.0.0"}}, fh)
    elif kind == "zero_manifest":
        # RESEARCH F5: three real repos had no manifest any parser knows.
        os.makedirs(os.path.join(root, "src"))
        os.makedirs(os.path.join(root, "include"))
        with open(os.path.join(root, "src", "main.c"), "w", encoding="utf-8") as fh:
            fh.write("int main(void) { return 0; }\n")
        with open(os.path.join(root, "include", "game.h"), "w", encoding="utf-8") as fh:
            fh.write("#define GAME 1\n")
        with open(os.path.join(root, "Makefile"), "w", encoding="utf-8") as fh:
            fh.write("all:\n\tcc src/main.c\n")
    else:
        raise ValueError("unknown fixture kind: %s" % kind)
    return root


def listing(root: str) -> list:
    """Every path under root (the .git directory included) with size and mtime."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in sorted(dirnames + filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if os.path.isfile(full):
                st = os.stat(full)
                out.append((rel, st.st_size, st.st_mtime_ns))
            else:
                out.append((rel, -1, 0))
    return sorted(out)


PROMPT_ADD_TABLE = "add a subscriptions table with its migration"


def _find(archetypes, archetype_id: str):
    for a in archetypes:
        if a.get("id") == archetype_id:
            return a
    return None


# -- gate predicates -------------------------------------------------------------

def pred_V_ARCH_HERMETIC_HOME():
    home_ok = Path.home() == Path(_HOME)
    expand_ok = os.path.expanduser("~") == _HOME
    return home_ok and expand_ok, "Path.home()=%s expanduser=%s" % (Path.home(), os.path.expanduser("~"))


def pred_V_ARCH_TRACER_PRODUCE():
    if ts is None or ar is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state = new_state()
    repo = make_repo("persistent_prisma")
    before = listing(repo)
    res = ts.produce(repo, state_dir=state)
    after = listing(repo)
    if res.get("outcome") != ts.WRITTEN:
        return False, "outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    files = [f for f in os.listdir(state) if f.startswith("traits_") and f.endswith(".json")]
    if len(files) != 1 or len(os.listdir(state)) != 1:
        return False, "state dir holds %r" % sorted(os.listdir(state))
    want = ar.cache_path(repo, state_dir=state)
    if os.path.normcase(os.path.abspath(os.path.join(state, files[0]))) != \
            os.path.normcase(os.path.abspath(want)):
        return False, "file %s != cache_path %s" % (files[0], want)
    with open(os.path.join(state, files[0]), "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("schema") != "ucep-traits/1":
        return False, "schema=%r" % doc.get("schema")
    if set(doc.get("traits") or {}) != set(ar.TRAITS):
        return False, "trait keys %r" % sorted(doc.get("traits") or {})
    if before != after:
        return False, "fixture repo changed: %d -> %d entries" % (len(before), len(after))
    return True, "one cache file %s, ten trait keys, repo untouched (%d entries)" % (files[0], len(after))


def pred_V_ARCH_TRACER_WORLD_MUTATION():
    state = new_state()
    repo = make_repo("persistent_prisma")
    ts.produce(repo, state_dir=state)
    subject = ar.resolve(PROMPT_ADD_TABLE, repo, state_dir=state)
    wm = _find(subject["archetypes"], "WORLD_MUTATION")
    if wm is None:
        return False, "no WORLD_MUTATION entry in %r" % [a.get("id") for a in subject["archetypes"]]
    evidence = subject["traits"]["persistent"]["evidence"]
    ok = (wm["strength"] == ar.Strength.REQUIRED and wm["anchor_state"] == ar.PRESENT
          and "prisma/schema.prisma" in evidence)
    return ok, "strength=%s anchor_state=%s evidence=%s" % (wm["strength"], wm["anchor_state"], evidence)


def pred_V_ARCH_TRACER_MISS():
    state = new_state()
    repo = make_repo("persistent_prisma")          # never produced
    subject = ar.resolve(PROMPT_ADD_TABLE, repo, state_dir=state)
    traits = subject["traits"]
    persistent = traits["persistent"]
    absent = [t for t, r in traits.items() if r["state"] == ar.ABSENT]
    wm = _find(subject["archetypes"], "WORLD_MUTATION")
    ok = (persistent["state"] == ar.UNJUDGED and persistent["reason"] == "no-cache"
          and persistent["fact_state"] == ar.UNKNOWN
          and set(traits) == set(ar.TRAITS) and not absent
          and subject["cache"]["state"] == ar.CACHE_MISSING
          and wm is not None and wm["strength"] != ar.Strength.REQUIRED)
    return ok, "persistent=%s/%s cache=%s absent=%s wm=%s" % (
        persistent["state"], persistent["reason"], subject["cache"]["state"], absent,
        wm["strength"] if wm else None)


def pred_V_ARCH_LIVENESS_DECLARED():
    path = os.path.join(_PP_ROOT, "vault", "liveness", "reachability_registry.json")
    with open(path, "r", encoding="utf-8-sig") as fh:
        reg = json.load(fh)
    mods = reg.get("modules") or {}
    problems = []
    for unit in ("capability_runtime/archetypes", "capability_runtime/trait_scan"):
        row = mods.get(unit)
        if not row or row.get("class") != "PLANNED":
            problems.append("%s not PLANNED (%r)" % (unit, row))
            continue
        note = row.get("note") or ""
        marker = "Owner queue: "
        if marker not in note:
            problems.append("%s note lacks %r" % (unit, marker))
            continue
        rel = note.split(marker, 1)[1].strip().split()[0]
        if not os.path.isfile(os.path.join(_PP_ROOT, rel)):
            problems.append("%s owner queue %s missing on disk" % (unit, rel))
    return not problems, "; ".join(problems) or "both rows PLANNED with a resolvable Owner queue"


_TEN = ("persistent", "multi_actor", "bulk", "destructive", "distributed",
        "external_effect", "scheduled", "money", "policy_layers", "ui")
_ARCH_PATH = os.path.join(_PP_ROOT, "modules", "capability_runtime", "archetypes.py")
_TS_PATH = os.path.join(_PP_ROOT, "modules", "capability_runtime", "trait_scan.py")


def _read_src(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return fh.read()


def _traits_ok(t) -> bool:
    return tuple(t) == _TEN and len(set(t)) == len(_TEN)


def pred_V_ARCH_TRAITS_TEN():
    ok = _traits_ok(ar.TRAITS)
    # Instrument control: the same predicate must reject a reordered and a
    # duplicated tuple, so a green here is not a predicate that accepts anything.
    control = (not _traits_ok(tuple(reversed(_TEN)))) and (not _traits_ok(_TEN[:9] + (_TEN[0],)))
    return ok and control, "TRAITS=%s control_rejects_mutants=%s" % (tuple(ar.TRAITS), control)


def pred_V_ARCH_ID_SHAPE():
    rx = ar.ARCHETYPE_ID_RE
    bad = [k for k in ar.ARCHETYPES if not rx.match(k)]
    # Instrument control (R-5, Pitfall 11): the pattern must reject the shapes it exists to refuse.
    rejects = [s for s in ("WORLD_MUTATION/persistent-state", "world_mutation", "", "WORLD_MUTATION\n")
               if rx.match(s) is None]
    control = len(rejects) == 4 and rx.match("WORLD_MUTATION") is not None
    return (not bad) and bool(ar.ARCHETYPES) and control, \
        "ids=%s bad=%s control=%s" % (sorted(ar.ARCHETYPES), bad, control)


def pred_V_ARCH_ARCHETYPES_THREE():
    want = {"WORLD_MUTATION", "EXTERNAL_EFFECT", "BACKGROUND_JOB"}
    if set(ar.ARCHETYPES) != want:
        return False, "archetype ids %s != %s" % (sorted(ar.ARCHETYPES), sorted(want))
    problems = []
    for aid, spec in sorted(ar.ARCHETYPES.items()):
        anchor, mods = spec.get("anchor"), spec.get("modifiers")
        dem, desc = spec.get("demoters"), spec.get("description")
        if anchor not in ar.TRAITS:
            problems.append("%s anchor %r not a trait" % (aid, anchor))
        if not isinstance(mods, tuple) or any(m not in ar.TRAITS for m in mods) or anchor in mods:
            problems.append("%s modifiers %r" % (aid, mods))
        if not isinstance(dem, tuple) or not dem or any(not isinstance(d, str) or not d for d in dem):
            problems.append("%s demoters %r" % (aid, dem))
        if not isinstance(desc, str) or not desc.strip():
            problems.append("%s description empty" % aid)
    return not problems, "; ".join(problems) or "three archetypes, well-formed conjunctions"


def _imports_from(src: str, module: str, names) -> bool:
    """True when `src` has `from <module> import ...` naming every one of `names`."""
    found = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            found.update(a.name for a in node.names)
    return set(names) <= found


def pred_V_ARCH_VOCAB_SHARED():
    ob = "modules.gsd_x.mission.obligation"
    same = (ar.EXTRACTED is obligation.EXTRACTED and ar.OBSERVED is obligation.OBSERVED
            and ar.UNKNOWN is obligation.UNKNOWN and ar.FACT_STATES is obligation.FACT_STATES)
    # Identity of interned strings cannot prove a name was imported rather than
    # re-spelled, so the source is checked too, with a control on trait_scan.py
    # (which does not import them) to show the detector can answer False.
    imported = _imports_from(_read_src(_ARCH_PATH), ob, ("OBSERVED", "EXTRACTED", "UNKNOWN", "FACT_STATES"))
    control = not _imports_from(_read_src(_TS_PATH), ob, ("EXTRACTED",))
    bad = [c for c in ar.UNJUDGED_CAUSES if ar.unjudged_reading(c)["fact_state"] not in obligation.FACT_STATES]
    return same and imported and control and not bad and bool(ar.UNJUDGED_CAUSES), \
        "same=%s imported=%s control=%s bad_causes=%s" % (same, imported, control, bad)


def _na_bridge_problems(mapping) -> list:
    problems = []
    if set(mapping) != set(ar.TRAITS):
        problems.append("keys %s" % sorted(mapping))
    values = list(mapping.values())
    if len(set(values)) != len(values):
        problems.append("values not distinct")
    if not set(values) <= set(donegate.NA_REASONS):
        problems.append("values outside donegate.NA_REASONS: %s" % sorted(set(values) - set(donegate.NA_REASONS)))
    return problems


def pred_V_ARCH_NA_BRIDGE():
    problems = _na_bridge_problems(ar.TRAIT_NA_REASON)
    dup = dict(ar.TRAIT_NA_REASON)
    dup["ui"] = dup["persistent"]
    bogus = dict(ar.TRAIT_NA_REASON)
    bogus["ui"] = "no-such-reason"
    control = bool(_na_bridge_problems(dup)) and bool(_na_bridge_problems(bogus))
    # The module bridges by value only: it must not import the donegate module.
    no_import = not any(
        "donegate" in (getattr(n, "module", None) or "") or any("donegate" in a.name for a in n.names)
        for n in ast.walk(ast.parse(_read_src(_ARCH_PATH)))
        if isinstance(n, (ast.Import, ast.ImportFrom)))
    return (not problems) and control and no_import, \
        "problems=%s control=%s no_donegate_import=%s" % (problems, control, no_import)


def pred_V_ARCH_NO_BARE_REQUIRED():
    s = ar.Strength
    ok = (not hasattr(ar, "REQUIRED") and s.REQUIRED == "REQUIRED" and s.CONDITIONAL == "CONDITIONAL"
          and s.NONE == "NONE" and tuple(s.ALL) == ("REQUIRED", "CONDITIONAL", "NONE"))
    # Control: the sibling namespace this exists to avoid really does expose REQUIRED.
    from modules.tower import baselines
    control = hasattr(baselines, "REQUIRED")
    return ok and control, "bare_REQUIRED=%s strengths=%s baselines.REQUIRED_exists=%s" % (
        hasattr(ar, "REQUIRED"), tuple(s.ALL), control)


def _reach_findings(src: str) -> list:
    """References that would let a reader reach the walk: an import of trait_scan, a
    from-import of os.walk, or any `os.walk` attribute reference (call or alias)."""
    found = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            found += ["import %s" % a.name for a in node.names if a.name.split(".")[-1] == "trait_scan"]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[-1] == "trait_scan":
                found.append("from %s" % mod)
            for a in node.names:
                if a.name == "trait_scan":
                    found.append("from %s import trait_scan" % mod)
                if mod == "os" and a.name == "walk":
                    found.append("from os import walk")
        elif isinstance(node, ast.Attribute):
            if node.attr == "walk" and isinstance(node.value, ast.Name) and node.value.id == "os":
                found.append("os.walk reference")
    return found


def pred_V_ARCH_READER_NO_WALK_IMPORT():
    reader = _reach_findings(_read_src(_ARCH_PATH))
    # Instrument controls: the detector must fire on the producer, and on each
    # synthetic shape it exists to catch (including the alias form 02-03 will use).
    producer = _reach_findings(_read_src(_TS_PATH))
    controls = {
        "producer_walk": "os.walk reference" in producer,
        "alias": "os.walk reference" in _reach_findings("import os\n_walk = os.walk\n"),
        "import_trait_scan": bool(_reach_findings("from modules.capability_runtime import trait_scan\n")),
        "from_os_walk": bool(_reach_findings("from os import walk\n")),
    }
    ok = not reader and all(controls.values())
    return ok, "reader_findings=%s controls=%s" % (reader, controls)


# -- plan 02-02: the strength ceiling (audit G16) --------------------------------
# Predeclared prompts, fixed before implementation (02-02-PLAN.md `<context>`).
WM_ES = "añade una tabla de suscripciones con su migración al backend de InfinityOps"
WM_EN = "save each player's coins when they disconnect"


def _wm(subject):
    return _find(subject["archetypes"], "WORLD_MUTATION")


def pred_V_ARCH_INTENT_ONLY_CAP():
    """A mutate intent with NO structural anchor is at most CONDITIONAL, stamped
    EXTRACTED, in both languages. Builds and produces its own fixtures, so a drill
    that mutates the ceiling reaches producer and reader alike."""
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state_a, repo_a = new_state(), make_repo("persistent_prisma")      # never produced
    state_b, repo_b = new_state(), make_repo("ephemeral")
    res = ts.produce(repo_b, state_dir=state_b)                        # produced, no persistent PRESENT
    if res.get("outcome") != ts.WRITTEN:
        return False, "ephemeral produce outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    subjects = [("cache-miss", repo_a, state_a), ("produced-ephemeral", repo_b, state_b)]
    seen, problems = [], []
    for label, repo, state in subjects:
        for prompt in (WM_ES, WM_EN):
            tag = "%s/%s" % (label, prompt[:24])
            subject = ar.resolve(prompt, repo, state_dir=state)
            seen.extend((tag, a) for a in subject["archetypes"])
            wm = _wm(subject)
            if wm is None:
                problems.append("%s: no WORLD_MUTATION entry" % tag)
                continue
            if wm["anchor_state"] == ar.PRESENT:
                problems.append("%s: precondition broken, anchor is PRESENT" % tag)
            span = wm.get("intent_span") or ""
            good = (wm["strength"] == ar.Strength.CONDITIONAL and wm["basis"] == "intent"
                    and wm["fact_state"] == ar.EXTRACTED and wm["intent_fact_state"] == ar.EXTRACTED
                    and 0 < len(span) <= 160)
            if not good:
                problems.append("INTENT-ONLY-NOT-CAPPED[%s]: strength=%s basis=%s fact_state=%s "
                                "intent_fact_state=%s span_len=%d" % (
                                    tag, wm["strength"], wm["basis"], wm["fact_state"],
                                    wm["intent_fact_state"], len(span)))
    leaks = ["%s/%s" % (tag, a["id"]) for tag, a in seen
             if a["basis"] == "intent" and a["strength"] == ar.Strength.REQUIRED]
    if leaks:
        problems.append("INTENT-BASIS-REQUIRED: %s" % leaks)
    return not problems, "; ".join(problems) or \
        "%d assessments over 2 intent-only subjects x 2 prompts: all CONDITIONAL/intent/EXTRACTED, no basis=intent REQUIRED" % len(seen)


def pred_V_ARCH_INTENT_CONTROL():
    """Control for the cap: the same two prompts over real persistent structure."""
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state, repo = new_state(), make_repo("persistent_prisma")
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        return False, "produce outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    problems, got = [], []
    for prompt in (WM_ES, WM_EN):
        wm = _wm(ar.resolve(prompt, repo, state_dir=state))
        if wm is None:
            problems.append("%s: no WORLD_MUTATION entry" % prompt[:24])
            continue
        got.append("%s=%s/%s" % (prompt[:12], wm["strength"], wm["basis"]))
        if not (wm["strength"] == ar.Strength.REQUIRED and wm["basis"] == "structural+intent"
                and wm["anchor_fact_state"] == ar.OBSERVED):
            problems.append("CONTROL-NOT-REQUIRED[%s]: strength=%s basis=%s anchor_fact_state=%s reason=%s" % (
                prompt[:24], wm["strength"], wm["basis"], wm["anchor_fact_state"], wm["reason"]))
    return not problems, "; ".join(problems) or "REQUIRED/structural+intent/OBSERVED for both: %s" % got


# -- plan 02-02 Task 2: bilingual verb-object intent, demoters, orthogonality ----
NO_INTENT = "cambia el color del botón del hero"
EE_ES = "envía un correo de confirmación al cliente cuando pague"
EE_EN = "send a webhook notification to Slack when an order ships"
BJ_ES = "programa una tarea que sincronice el inventario cada noche"
BJ_EN = "run a nightly cleanup job that purges expired sessions"
DEMOTED_ES = "actualiza la tabla de saldos en modo dry run, sin escribir"
DEMOTED_EN = "update the balances table as a dry run, read-only"
ORTHO_B = "guarda las monedas de cada jugador cuando se desconecta"
DESTR_ES = "borra todos los registros de usuarios inactivos"
DESTR_EN = "delete all inactive user records"
ORTHO_A = "¿qué es un schema de base de datos?"

# archetype id -> (anchor trait, Spanish intent prompt, English intent prompt)
ARCH_PROMPTS = {
    "WORLD_MUTATION": ("persistent", WM_ES, WM_EN),
    "EXTERNAL_EFFECT": ("external_effect", EE_ES, EE_EN),
    "BACKGROUND_JOB": ("scheduled", BJ_ES, BJ_EN),
}

# The twelve strings of the predeclared table (02-02-PLAN.md `<context>`).
SHAPE_PROMPTS = [WM_ES, WM_EN, EE_ES, EE_EN, BJ_ES, BJ_EN, NO_INTENT,
                 DEMOTED_ES, DEMOTED_EN, ORTHO_B, DESTR_ES, DESTR_EN]

NOUN_ONLY = ["schema", "database", "la tabla", "webhook", "email", "cron", "job",
             "¿qué es un schema de base de datos?", "¿qué es un webhook?"]

# Strings with accents, punctuation, apostrophes and mixed case for the parity corpus.
PARITY_EXTRAS = [
    "Añade una TABLA; Envía un CORREO!", "player's coins, don't DELETE", "¿Qué es un Webhook?",
    "cron-job nightly (sync) y limpieza", "read-only: dry run", "SIN ESCRIBIR, por favor",
    "Migración/migraciones del esquema", "all-in-one batch; todos los registros.",
    "Borra TODAS LAS cuentas", "e-mail, e mail, email", "O'Brien's invoice: pay it", "",
    "crea el informe diario y publícalo", "modo prueba: simulado, sin enviar", "one-off, una sola vez",
]


def _anchor_reading(state):
    if state == "PRESENT":
        return ar.reading(ar.PRESENT, ar.OBSERVED, ["fixture"], "injected")
    if state == "WEAK":
        return ar.reading(ar.WEAK, ar.OBSERVED, ["fixture"], "injected")
    if state == "ABSENT":
        return ar.reading(ar.ABSENT, ar.OBSERVED, [], "injected")
    raise ValueError("unknown anchor state %r" % state)


def _inj(anchor=None, state=None, anchors=None):
    """Injected structural readings: the named anchor(s) at `state`, every other
    trait UNJUDGED `no-structural-detector`. Tests the conjunction without
    depending on any detector."""
    traits = {t: ar.unjudged_reading("no-structural-detector") for t in ar.TRAITS}
    names = anchors if anchors is not None else ([anchor] if anchor else [])
    for name in names:
        traits[name] = _anchor_reading(state)
    return traits


def _arch(traits, prompt, aid):
    return _find(ar.assess(traits, prompt), aid)


def _strip_phrases(text, phrases):
    """`text` with every phrase removed (longest first), whitespace collapsed."""
    out = text
    for p in sorted(phrases, key=len, reverse=True):
        out = re.sub(re.escape(p), " ", out, flags=re.I)
    return " ".join(out.replace(",", " ").split())


def make_docs_vocab_repo():
    """Fixture kind `docs_vocab`: `.git/`, README.md and docs/design-notes.md whose
    prose repeats the persistence vocabulary, with no manifest and no file or
    directory a structural marker detector recognises."""
    root = tempfile.mkdtemp(prefix="carch-repo-")
    _TEMP_DIRS.append(root)
    os.makedirs(os.path.join(root, ".git"))
    os.makedirs(os.path.join(root, "docs"))
    prose = ("The schema of the database defines every table, and each migration changes the "
             "table. La tabla, el esquema y la base de datos: schema, database, table, migration, "
             "tabla, esquema. ") * 60
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# Notes\n\n" + prose + "\n")
    with open(os.path.join(root, "docs", "design-notes.md"), "w", encoding="utf-8") as fh:
        fh.write("# Design notes\n\n" + prose + "\n")
    return root


def pred_V_ARCH_WEAK_CAP():
    problems, n = [], 0
    for aid, (anchor, es, en) in sorted(ARCH_PROMPTS.items()):
        traits = _inj(anchor, "WEAK")
        for prompt in (es, en):
            a = _arch(traits, prompt, aid)
            n += 1
            if not (a["strength"] == ar.Strength.CONDITIONAL and a["basis"] == "structural+intent"):
                problems.append("WEAK-INTENT[%s/%s]: strength=%s basis=%s" % (
                    aid, prompt[:16], a["strength"], a["basis"]))
        a = _arch(traits, NO_INTENT, aid)
        n += 1
        if not (a["strength"] == ar.Strength.CONDITIONAL and a["basis"] == "structural"):
            problems.append("WEAK-NO-INTENT[%s]: strength=%s basis=%s" % (aid, a["strength"], a["basis"]))
    return not problems, "; ".join(problems) or "%d WEAK-anchor assessments, all CONDITIONAL, never REQUIRED" % n


def pred_V_ARCH_DEMOTE_NOT_VETO():
    problems, n = [], 0
    demoters = ar.ARCHETYPES["WORLD_MUTATION"]["demoters"]
    traits = _inj("persistent", "PRESENT")
    for prompt in (DEMOTED_ES, DEMOTED_EN):
        a = _arch(traits, prompt, "WORLD_MUTATION")
        n += 1
        if not (a["strength"] == ar.Strength.CONDITIONAL and a["demoted_by"]):
            problems.append("DEMOTED[%s]: strength=%s demoted_by=%s" % (prompt[:16], a["strength"], a["demoted_by"]))
        # Control: every demoter phrase removed -> the same sentence is REQUIRED.
        control = _strip_phrases(prompt, demoters)
        left = _match(control, demoters)
        a = _arch(traits, control, "WORLD_MUTATION")
        n += 1
        if left or a["strength"] != ar.Strength.REQUIRED:
            problems.append("CONTROL[%r]: demoters_left=%s strength=%s" % (control, left, a["strength"]))
    a = _arch(traits, NO_INTENT + ", dry run", "WORLD_MUTATION")
    n += 1
    if not (a["strength"] == ar.Strength.CONDITIONAL and a["demoted_by"]):
        problems.append("DEMOTER-NO-INTENT: strength=%s demoted_by=%s (must stay CONDITIONAL, never NONE)" % (
            a["strength"], a["demoted_by"]))
    return not problems, "; ".join(problems) or \
        "%d checks: demoted -> CONDITIONAL, demoters removed -> REQUIRED, no-intent+demoter -> CONDITIONAL" % n


def pred_V_ARCH_STRUCTURE_ONLY_CONDITIONAL():
    problems, n = [], 0
    for aid, (anchor, _es, _en) in sorted(ARCH_PROMPTS.items()):
        a = _arch(_inj(anchor, "PRESENT"), NO_INTENT, aid)
        n += 1
        if not (a["strength"] == ar.Strength.CONDITIONAL and a["basis"] == "structural"):
            problems.append("PRESENT-NO-INTENT[%s]: strength=%s basis=%s" % (aid, a["strength"], a["basis"]))
        a = _arch(_inj(anchor, "ABSENT"), NO_INTENT, aid)
        n += 1
        if a["strength"] != ar.Strength.NONE:
            problems.append("ABSENT-NO-INTENT[%s]: strength=%s" % (aid, a["strength"]))
        a = _arch(_inj(), NO_INTENT, aid)
        n += 1
        if not (a["strength"] == ar.Strength.NONE and anchor in a["unjudged"]):
            problems.append("UNJUDGED-NO-INTENT[%s]: strength=%s unjudged=%s" % (aid, a["strength"], a["unjudged"]))
    return not problems, "; ".join(problems) or \
        "%d checks: structure alone -> CONDITIONAL/structural, ABSENT and UNJUDGED -> NONE" % n


def _positive_pred(aid):
    def pred():
        anchor, es, en = ARCH_PROMPTS[aid]
        problems, n = [], 0
        for prompt in (es, en):
            a = _arch(_inj(anchor, "PRESENT"), prompt, aid)
            n += 1
            if not (a["strength"] == ar.Strength.REQUIRED and a["basis"] == "structural+intent"
                    and a["fact_state"] == ar.OBSERVED):
                problems.append("PRESENT[%s]: strength=%s basis=%s fact_state=%s reason=%s" % (
                    prompt[:16], a["strength"], a["basis"], a["fact_state"], a["reason"]))
            a = _arch(_inj(anchor, "ABSENT"), prompt, aid)
            n += 1
            if not (a["strength"] == ar.Strength.CONDITIONAL and a["basis"] == "intent"
                    and a["fact_state"] == ar.EXTRACTED):
                problems.append("ABSENT[%s]: strength=%s basis=%s fact_state=%s" % (
                    prompt[:16], a["strength"], a["basis"], a["fact_state"]))
        a = _arch(_inj(anchor, "PRESENT"), NO_INTENT, aid)
        n += 1
        if a["strength"] == ar.Strength.REQUIRED:
            problems.append("NO-INTENT-REQUIRED: a PRESENT anchor without intent reached REQUIRED")
        return not problems, "; ".join(problems) or \
            "%s: %d checks, REQUIRED over PRESENT, CONDITIONAL/intent over ABSENT, no-intent not REQUIRED" % (aid, n)
    return pred


pred_V_ARCH_POSITIVE_UNIT_WORLD_MUTATION = _positive_pred("WORLD_MUTATION")
pred_V_ARCH_POSITIVE_UNIT_EXTERNAL_EFFECT = _positive_pred("EXTERNAL_EFFECT")
pred_V_ARCH_POSITIVE_UNIT_BACKGROUND_JOB = _positive_pred("BACKGROUND_JOB")


def pred_V_ARCH_NOUN_ONLY_NEG():
    """D-04: a prompt that is only nouns makes no intent fact and no REQUIRED."""
    anchors = ("persistent", "external_effect", "scheduled")
    traits = _inj(anchors=anchors, state="PRESENT")
    problems = []
    for prompt in NOUN_ONLY:
        facts = ar.intent_facts(prompt)
        bad = [t for t in anchors if facts[t]["state"] == ar.PRESENT]
        if bad:
            problems.append("NOUN-ONLY-INTENT[%r]: PRESENT for %s" % (prompt, bad))
        for a in ar.assess(traits, prompt):
            if a["strength"] == ar.Strength.REQUIRED:
                problems.append("NOUN-ONLY-REQUIRED[%r]: %s" % (prompt, a["id"]))
    # Instrument control: the same machinery must be able to answer PRESENT.
    control = ar.intent_facts("add a table")["persistent"]["state"] == ar.PRESENT
    if not control:
        problems.append("CONTROL: `add a table` did not read PRESENT, the detector is dead")
    return not problems, "; ".join(problems) or \
        "%d noun-only prompts: no PRESENT intent, no REQUIRED with every anchor PRESENT; control PRESENT=%s" % (
            len(NOUN_ONLY), control)


def pred_V_ARCH_VOCAB_OVERLAP_NEG():
    """D-04, D-07: a repo whose docs are full of persistence prose, asked the bare
    prompt `schema`, has no active archetype, while the family matcher DOES hit."""
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state, repo = new_state(), make_docs_vocab_repo()
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        return False, "docs_vocab produce outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    subject = ar.resolve("schema", repo, state_dir=state)
    active = ar.active_archetypes(subject)
    persistent = subject["traits"]["persistent"]
    fam_ids = [fid for fid, _fam_hits in families.classify_prompt("schema")]
    problems = []
    if active:
        problems.append("VOCAB-ACTIVE-ARCHETYPE: %s active for the bare prompt `schema` over a docs-only repo" % active)
    if persistent["state"] in (ar.PRESENT, ar.WEAK):
        problems.append("VOCAB-PERSISTENT-READ: %s from prose alone" % persistent["state"])
    if "persistent_state" not in fam_ids:
        problems.append("CONTROL: classify_prompt('schema') = %s lacks persistent_state" % fam_ids)
    return not problems, "; ".join(problems) or \
        "active=%s persistent=%s AND classify_prompt('schema')=%s" % (active, persistent["state"], fam_ids)


def pred_V_ARCH_ORTHOGONAL_A():
    state, repo = new_state(), make_repo("ephemeral")
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        return False, "produce outcome=%r" % res.get("outcome")
    subject = ar.resolve(ORTHO_A, repo, state_dir=state)
    fam_ids = [f["id"] for f in subject["families"]]
    active = ar.active_archetypes(subject)
    return ("persistent_state" in fam_ids and active == []), \
        "families=%s active_archetypes=%s (family hit, zero archetypes)" % (fam_ids, active)


def pred_V_ARCH_ORTHOGONAL_B():
    pre = families.classify_prompt(ORTHO_B)
    if pre != []:
        return False, "precondition broken: classify_prompt(%r) = %s" % (ORTHO_B, pre)
    state, repo = new_state(), make_repo("persistent_prisma")
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        return False, "produce outcome=%r" % res.get("outcome")
    subject = ar.resolve(ORTHO_B, repo, state_dir=state)
    wm = _wm(subject)
    ok = (wm is not None and wm["strength"] == ar.Strength.REQUIRED and subject["families"] == [])
    return ok, "families=%s WORLD_MUTATION=%s (archetype REQUIRED, zero families)" % (
        subject["families"], wm["strength"] if wm else None)


def pred_V_ARCH_TRAIT_INTENT_SHAPE():
    undetected = {"multi_actor", "distributed", "policy_layers", "ui"}
    problems = []
    for prompt in SHAPE_PROMPTS:
        facts = ar.intent_facts(prompt)
        if set(facts) != set(ar.TRAITS):
            problems.append("KEYS[%s]: %s" % (prompt[:16], sorted(facts)))
            continue
        for trait, r in facts.items():
            st = r["state"]
            if st == ar.PRESENT:
                if not (r["fact_state"] == ar.EXTRACTED and r["span"]):
                    problems.append("PRESENT-SHAPE[%s/%s]: fact_state=%s span=%r" % (
                        prompt[:12], trait, r["fact_state"], r["span"]))
            elif st == ar.UNJUDGED:
                if r["fact_state"] != ar.UNKNOWN or r["reason"] not in ("no-intent-match", "no-intent-detector"):
                    problems.append("UNJUDGED-SHAPE[%s/%s]: fact_state=%s reason=%s" % (
                        prompt[:12], trait, r["fact_state"], r["reason"]))
            else:
                problems.append("STATE[%s/%s]: %s (intent is PRESENT or UNJUDGED, never ABSENT)" % (
                    prompt[:12], trait, st))
        nd = {t for t, r in facts.items() if r["reason"] == "no-intent-detector"}
        if nd != undetected:
            problems.append("NO-DETECTOR-SET[%s]: %s" % (prompt[:12], sorted(nd)))
    for prompt in (DESTR_ES, DESTR_EN):
        facts = ar.intent_facts(prompt)
        if not (facts["destructive"]["state"] == ar.PRESENT and facts["bulk"]["state"] == ar.PRESENT):
            problems.append("DESTRUCTIVE-BULK[%s]: destructive=%s bulk=%s" % (
                prompt[:16], facts["destructive"]["state"], facts["bulk"]["state"]))
    return not problems, "; ".join(problems) or \
        "%d prompts x 10 traits well-shaped; destructive+bulk PRESENT for both; no-detector set exact" % len(SHAPE_PROMPTS)


def pred_V_ARCH_MATCHER_PARITY():
    """D-01: the offsets helper must agree with `_hits` on presence, always."""
    phrases = []
    for spec in ar.TRAIT_INTENT.values():
        phrases += list(spec["verbs"]) + list(spec["objects"])
    for spec in ar.ARCHETYPES.values():
        phrases += list(spec["demoters"])
    corpus = list(SHAPE_PROMPTS) + list(NOUN_ONLY) + [ORTHO_A] + PARITY_EXTRAS
    n = agree_true = agree_false = 0
    mismatches = []
    for text in corpus:
        folded = _fold(text)
        for phrase in phrases:
            fp = _fold(phrase)
            mine = bool(ar._spans(folded, fp))
            theirs = bool(_hits(folded, [fp]))
            n += 1
            if mine != theirs:
                mismatches.append("%r in %r: spans=%s hits=%s" % (phrase, text[:20], mine, theirs))
            elif mine:
                agree_true += 1
            else:
                agree_false += 1
    ok = not mismatches and agree_true > 0 and agree_false > 0
    return ok, "comparisons=%d agree_true=%d agree_false=%d mismatches=%s" % (
        n, agree_true, agree_false, mismatches[:3])


def pred_V_ARCH_INTENT_BOUNDED():
    filler = ("alpha beta " * 3000)[:25000]
    far = ar.intent_facts(filler + " add a table")["persistent"]["state"]
    near = ar.intent_facts(("alpha beta " * 9)[:100] + " add a table")["persistent"]["state"]
    big = "add table " * 20000
    t0 = time.perf_counter()
    ar.intent_facts(big)
    ms = (time.perf_counter() - t0) * 1000.0
    ok = (far == ar.UNJUDGED and near == ar.PRESENT and len(big) == 200000
          and ms < 1000.0 and ar.INTENT_MAX_CHARS == 20000)
    return ok, "200000-char prompt intent_facts=%.0f ms (limit 1000); pair at 25000 -> %s, at offset 100 -> %s; max_chars=%s" % (
        ms, far, near, getattr(ar, "INTENT_MAX_CHARS", None))


# -- plan 02-02 Task 3: falsification drills --------------------------------------
# A control that has never been seen to go red proves nothing. Each drill installs a
# mutation of the code under test, re-runs the target predicate(s), and requires: the
# predicate went RED, the counting wrapper was reached (so a pass is not an unreached
# seam), the red evidence names the sub-assertion being drilled (so it did not go red
# for an unrelated setup reason), and, after the restore in `finally`, the same
# predicate is GREEN again on real code. Every target builds its own fixtures inside
# the predicate, so producer and reader run under the same mutation.

def _drill_report(label, results):
    for name, ok, evidence in results:
        print("    [drill %s] mutated %s ok=%s evidence: %s" % (label, name, ok, str(evidence)[:700]))


def pred_V_ARCH_DRILL_CEILING():
    """RESEARCH drill 1: a ceiling that lets any intent reach REQUIRED must turn the
    intent-only cap red."""
    original = ar.ceiling

    def weakened(anchor_state, intent_hit, demoted):
        if intent_hit:
            return ar.Strength.REQUIRED, "intent"
        return original(anchor_state, intent_hit, demoted)

    counter = Counting(weakened)
    ar.ceiling = counter
    try:
        ok_m, ev_m = pred_V_ARCH_INTENT_ONLY_CAP()
    finally:
        ar.ceiling = original
    restored_is_original = ar.ceiling is original
    ok_r, ev_r = pred_V_ARCH_INTENT_ONLY_CAP()
    _drill_report("ceiling", [("V-ARCH-INTENT-ONLY-CAP", ok_m, ev_m)])
    named = "INTENT-ONLY-NOT-CAPPED" in ev_m and "strength=REQUIRED" in ev_m and "INTENT-BASIS-REQUIRED" in ev_m
    ok = ok_m is False and counter.calls > 0 and named and restored_is_original and ok_r is True
    return ok, "mutated ok=%s calls=%d named_sub_assertion=%s restored ok=%s | %s" % (
        ok_m, counter.calls, named, ok_r, ev_m)


def pred_V_ARCH_DRILL_NOUN_LIST():
    """RESEARCH drill 5: an intent detector degraded to a bag of persistence nouns
    must turn the vocabulary-overlap and noun-only controls red."""
    original = ar.intent_facts
    nouns = tuple(ar.TRAIT_INTENT["persistent"]["objects"])

    def noun_bag(prompt):
        out = original(prompt)
        hit = _match(str(prompt or "")[:ar.INTENT_MAX_CHARS], nouns)
        if hit:   # no verb required: any persistence noun is "intent"
            out["persistent"] = {"state": ar.PRESENT, "fact_state": ar.EXTRACTED,
                                 "span": hit[0], "reason": "noun-only"}
        return out

    counter = Counting(noun_bag)
    ar.intent_facts = counter
    try:
        ok_v, ev_v = pred_V_ARCH_VOCAB_OVERLAP_NEG()
        ok_n, ev_n = pred_V_ARCH_NOUN_ONLY_NEG()
    finally:
        ar.intent_facts = original
    restored_is_original = ar.intent_facts is original
    ok_vr, _ev_vr = pred_V_ARCH_VOCAB_OVERLAP_NEG()
    ok_nr, _ev_nr = pred_V_ARCH_NOUN_ONLY_NEG()
    _drill_report("noun-list", [("V-ARCH-VOCAB-OVERLAP-NEG", ok_v, ev_v), ("V-ARCH-NOUN-ONLY-NEG", ok_n, ev_n)])
    named = "VOCAB-ACTIVE-ARCHETYPE" in ev_v and "NOUN-ONLY-INTENT" in ev_n and "NOUN-ONLY-REQUIRED" in ev_n
    ok = (ok_v is False and ok_n is False and counter.calls > 0 and named
          and restored_is_original and ok_vr is True and ok_nr is True)
    return ok, "mutated vocab ok=%s noun-only ok=%s calls=%d named_sub_assertions=%s restored ok=%s/%s | %s" % (
        ok_v, ok_n, counter.calls, named, ok_vr, ok_nr, ev_v)


# -- plan 02-03 Task 1: honest absence (RESEARCH F5, D-05) ------------------------
# A trait with no positive evidence reads ABSENT only when the walk was complete.
# A cut, starved, blind or partly unreadable walk reads UNJUDGED with the cause.

def _produce_read(repo, **kw):
    """Produce into a fresh state dir -> (state, produce result, read_traits result)."""
    state = new_state()
    res = ts.produce(repo, state_dir=state, **kw)
    return state, res, ar.read_traits(repo, state_dir=state)


def pred_V_ARCH_TRUNCATED():
    if ts is None or ar is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    problems, notes = [], []
    # (a) the schema file is reached before the cap: the positive is kept.
    repo_a = make_repo("truncated_near")
    state_a, res_a, read_a = _produce_read(repo_a, cap=10)
    walk_a = (res_a.get("doc") or {}).get("walk") or {}
    pa = read_a["traits"]["persistent"]
    if not walk_a.get("truncated"):
        problems.append("near: walk.truncated=%r" % walk_a.get("truncated"))
    if not (pa["state"] == ar.PRESENT and "00_models/schema.prisma" in pa["evidence"]):
        problems.append("near: persistent=%s/%s evidence=%s" % (pa["state"], pa["reason"], pa["evidence"]))
    wm_a = _wm(ar.resolve(WM_ES, repo_a, state_dir=state_a))
    if wm_a is None or wm_a["strength"] != ar.Strength.REQUIRED:
        problems.append("near: WORLD_MUTATION=%s" % (wm_a and (wm_a["strength"], wm_a["basis"])))
    # (b) the cap cuts the walk before the schema file: the trait is UNJUDGED truncated.
    repo_b = make_repo("truncated_far")
    state_b, res_b, read_b = _produce_read(repo_b, cap=10)
    walk_b = (res_b.get("doc") or {}).get("walk") or {}
    pb = read_b["traits"]["persistent"]
    if not walk_b.get("truncated"):
        problems.append("far: walk.truncated=%r" % walk_b.get("truncated"))
    if not (pb["state"] == ar.UNJUDGED and pb["reason"] == "truncated"):
        problems.append("far: persistent=%s/%s (want UNJUDGED/truncated, never ABSENT or no-structural-detector)"
                        % (pb["state"], pb["reason"]))
    wm_b = _wm(ar.resolve(WM_ES, repo_b, state_dir=state_b))
    if wm_b is None or not (wm_b["strength"] == ar.Strength.CONDITIONAL and wm_b["basis"] == "intent"
                            and "persistent" in wm_b["unjudged"]):
        problems.append("far: WORLD_MUTATION=%s" % (wm_b and (wm_b["strength"], wm_b["basis"], wm_b["unjudged"])))
    notes.append("near persistent=%s %s; far persistent=%s/%s" % (pa["state"], pa["evidence"], pb["state"], pb["reason"]))
    return not problems, "; ".join(problems) or "; ".join(notes)


def pred_V_ARCH_BUDGET():
    if ts is None or ar is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    problems = []
    # budget_s=0 must cut on every run: the scan compares time.perf_counter() with >=
    # before each directory (time.monotonic ticks at 15.6 ms on this host).
    repo = make_repo("persistent_prisma")
    _state, res, read = _produce_read(repo, budget_s=0)
    walk = (res.get("doc") or {}).get("walk") or {}
    traits = read["traits"]
    absent = [t for t, r in traits.items() if r["state"] == ar.ABSENT]
    reasons = sorted({r["reason"] for r in traits.values() if r["state"] == ar.UNJUDGED})
    p = traits["persistent"]
    if walk.get("budget_hit") is not True:
        problems.append("budget_hit=%r" % walk.get("budget_hit"))
    if absent:
        problems.append("ABSENT under a cut walk: %s" % absent)
    if not (p["state"] == ar.PRESENT or (p["state"] == ar.UNJUDGED and p["reason"] == "budget-exhausted")):
        problems.append("persistent=%s/%s" % (p["state"], p["reason"]))
    if "budget-exhausted" not in reasons:
        problems.append("no trait carries budget-exhausted (reasons=%s)" % reasons)
    # Control: the same repo with the default budget is not cut.
    repo2 = make_repo("persistent_prisma")
    _s2, res2, _r2 = _produce_read(repo2)
    walk2 = (res2.get("doc") or {}).get("walk") or {}
    if walk2.get("budget_hit") is not False:
        problems.append("CONTROL: default budget budget_hit=%r" % walk2.get("budget_hit"))
    return not problems, "; ".join(problems) or \
        "budget_s=0 -> budget_hit, persistent=%s/%s, reasons=%s, no ABSENT; default budget not cut" % (
            p["state"], p["reason"], reasons)


def pred_V_ARCH_BLIND_ECOSYSTEM():
    if ts is None or ar is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    problems = []
    _s, _res, read = _produce_read(make_repo("zero_manifest"))
    p = read["traits"]["persistent"]
    if not (p["state"] == ar.UNJUDGED and p["reason"] == "no-manifest-ecosystem"):
        problems.append("zero_manifest persistent=%s/%s (want UNJUDGED/no-manifest-ecosystem)" % (p["state"], p["reason"]))
    # Control: a repo with a parsed manifest and a complete walk can read ABSENT.
    _s2, _res2, read2 = _produce_read(make_repo("ephemeral"))
    c = read2["traits"]["persistent"]
    if not (c["state"] == ar.ABSENT and c["fact_state"] == ar.OBSERVED):
        problems.append("CONTROL: ephemeral persistent=%s/%s fact_state=%s (want ABSENT/OBSERVED)" % (
            c["state"], c["reason"], c["fact_state"]))
    return not problems, "; ".join(problems) or \
        "zero_manifest persistent=UNJUDGED/no-manifest-ecosystem; control ephemeral persistent=ABSENT/%s (%s)" % (
            c["fact_state"], c["reason"])


def pred_V_ARCH_UNREADABLE_SUBTREE():
    if ts is None or ar is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    original = ts._walk

    def failing_first(top, topdown=True, onerror=None, followlinks=False):
        if onerror is not None:
            onerror(PermissionError(13, "Permission denied", os.path.join(top, "fabricated-subdir")))
        return original(top, topdown=topdown, onerror=onerror, followlinks=followlinks)

    counter = Counting(failing_first)
    problems = []
    ts._walk = counter
    try:
        _s, res, read = _produce_read(make_repo("ephemeral"))
        _s2, res2, read2 = _produce_read(make_repo("persistent_prisma"))
    finally:
        ts._walk = original
    walk = (res.get("doc") or {}).get("walk") or {}
    p, p2 = read["traits"]["persistent"], read2["traits"]["persistent"]
    if counter.calls < 2:
        problems.append("the wrapper was reached %d times, wanted 2" % counter.calls)
    if not (p["state"] == ar.UNJUDGED and p["reason"] == "unreadable-subtree"):
        problems.append("ephemeral persistent=%s/%s (want UNJUDGED/unreadable-subtree)" % (p["state"], p["reason"]))
    if walk.get("unreadable") != 1:
        problems.append("walk.unreadable=%r" % walk.get("unreadable"))
    if p2["state"] != ar.PRESENT:
        problems.append("positive lost under the same wrapper: persistent=%s/%s" % (p2["state"], p2["reason"]))
    if ts._walk is not original:
        problems.append("ts._walk not restored")
    return not problems, "; ".join(problems) or \
        "ephemeral persistent=UNJUDGED/unreadable-subtree unreadable=1; persistent_prisma still %s; wrapper calls=%d" % (
            p2["state"], counter.calls)


GATES = [
    ("V-ARCH-HERMETIC-HOME", pred_V_ARCH_HERMETIC_HOME),
    ("V-ARCH-TRACER-PRODUCE", pred_V_ARCH_TRACER_PRODUCE),
    ("V-ARCH-TRACER-WORLD_MUTATION", pred_V_ARCH_TRACER_WORLD_MUTATION),
    ("V-ARCH-TRACER-MISS", pred_V_ARCH_TRACER_MISS),
    ("V-ARCH-LIVENESS-DECLARED", pred_V_ARCH_LIVENESS_DECLARED),
    ("V-ARCH-TRAITS-TEN", pred_V_ARCH_TRAITS_TEN),
    ("V-ARCH-ID-SHAPE", pred_V_ARCH_ID_SHAPE),
    ("V-ARCH-ARCHETYPES-THREE", pred_V_ARCH_ARCHETYPES_THREE),
    ("V-ARCH-VOCAB-SHARED", pred_V_ARCH_VOCAB_SHARED),
    ("V-ARCH-NA-BRIDGE", pred_V_ARCH_NA_BRIDGE),
    ("V-ARCH-NO-BARE-REQUIRED", pred_V_ARCH_NO_BARE_REQUIRED),
    ("V-ARCH-READER-NO-WALK-IMPORT", pred_V_ARCH_READER_NO_WALK_IMPORT),
    ("V-ARCH-INTENT-ONLY-CAP", pred_V_ARCH_INTENT_ONLY_CAP),
    ("V-ARCH-INTENT-CONTROL", pred_V_ARCH_INTENT_CONTROL),
    ("V-ARCH-WEAK-CAP", pred_V_ARCH_WEAK_CAP),
    ("V-ARCH-DEMOTE-NOT-VETO", pred_V_ARCH_DEMOTE_NOT_VETO),
    ("V-ARCH-STRUCTURE-ONLY-CONDITIONAL", pred_V_ARCH_STRUCTURE_ONLY_CONDITIONAL),
    ("V-ARCH-POSITIVE-UNIT-WORLD_MUTATION", pred_V_ARCH_POSITIVE_UNIT_WORLD_MUTATION),
    ("V-ARCH-POSITIVE-UNIT-EXTERNAL_EFFECT", pred_V_ARCH_POSITIVE_UNIT_EXTERNAL_EFFECT),
    ("V-ARCH-POSITIVE-UNIT-BACKGROUND_JOB", pred_V_ARCH_POSITIVE_UNIT_BACKGROUND_JOB),
    ("V-ARCH-NOUN-ONLY-NEG", pred_V_ARCH_NOUN_ONLY_NEG),
    ("V-ARCH-VOCAB-OVERLAP-NEG", pred_V_ARCH_VOCAB_OVERLAP_NEG),
    ("V-ARCH-ORTHOGONAL-A", pred_V_ARCH_ORTHOGONAL_A),
    ("V-ARCH-ORTHOGONAL-B", pred_V_ARCH_ORTHOGONAL_B),
    ("V-ARCH-TRAIT-INTENT-SHAPE", pred_V_ARCH_TRAIT_INTENT_SHAPE),
    ("V-ARCH-MATCHER-PARITY", pred_V_ARCH_MATCHER_PARITY),
    ("V-ARCH-INTENT-BOUNDED", pred_V_ARCH_INTENT_BOUNDED),
    ("V-ARCH-DRILL-CEILING", pred_V_ARCH_DRILL_CEILING),
    ("V-ARCH-DRILL-NOUN-LIST", pred_V_ARCH_DRILL_NOUN_LIST),
    ("V-ARCH-TRUNCATED", pred_V_ARCH_TRUNCATED),
    ("V-ARCH-BUDGET", pred_V_ARCH_BUDGET),
    ("V-ARCH-BLIND-ECOSYSTEM", pred_V_ARCH_BLIND_ECOSYSTEM),
    ("V-ARCH-UNREADABLE-SUBTREE", pred_V_ARCH_UNREADABLE_SUBTREE),
]

# -- plan 02-03 Task 2: each archetype REQUIRED end to end (D-07) -----------------
# fixture repo -> producer -> cache -> resolve, for the Spanish and the English
# prompt of the 02-02 table, with the evidence naming the manifest and the
# dependency; the negative pole removes that dependency and the archetype falls to
# CONDITIONAL with basis `intent`.

def _archetype_positive(aid, pos_kind, neg_kind, evidence_item):
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    anchor, es, en = ARCH_PROMPTS[aid]
    pos_state, pos_repo = new_state(), make_repo(pos_kind)
    neg_state, neg_repo = new_state(), make_repo(neg_kind)
    for repo, state in ((pos_repo, pos_state), (neg_repo, neg_state)):
        res = ts.produce(repo, state_dir=state)
        if res.get("outcome") != ts.WRITTEN:
            return False, "produce outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    problems, seen = [], []
    for lang, prompt in (("es", es), ("en", en)):
        subject = ar.resolve(prompt, pos_repo, state_dir=pos_state)
        entry = _find(subject["archetypes"], aid)
        evidence = subject["traits"][anchor]["evidence"]
        if entry is None or not (entry["strength"] == ar.Strength.REQUIRED
                                 and entry["basis"] == "structural+intent"
                                 and evidence_item in evidence):
            problems.append("positive[%s]: %s evidence=%s (want REQUIRED structural+intent naming %s)" % (
                lang, entry and (entry["strength"], entry["basis"]), evidence, evidence_item))
        else:
            seen.append("%s=REQUIRED %s" % (lang, evidence))
        neg_subject = ar.resolve(prompt, neg_repo, state_dir=neg_state)
        neg = _find(neg_subject["archetypes"], aid)
        if neg is None or not (neg["strength"] == ar.Strength.CONDITIONAL and neg["basis"] == "intent"):
            problems.append("negative[%s]: %s (want CONDITIONAL intent)" % (
                lang, neg and (neg["strength"], neg["basis"], neg["anchor_state"])))
        else:
            seen.append("%s-neg=CONDITIONAL/intent(anchor %s)" % (lang, neg["anchor_state"]))
    return not problems, "; ".join(problems) or " | ".join(seen)


def pred_V_ARCH_POSITIVE_WORLD_MUTATION():
    return _archetype_positive("WORLD_MUTATION", "persistent_pip", "pip_fastapi", "requirements.txt:sqlalchemy")


def pred_V_ARCH_POSITIVE_EXTERNAL_EFFECT():
    return _archetype_positive("EXTERNAL_EFFECT", "external_npm", "ephemeral", "package.json:resend")


def pred_V_ARCH_POSITIVE_BACKGROUND_JOB():
    return _archetype_positive("BACKGROUND_JOB", "scheduled_pip", "pip_fastapi", "requirements.txt:apscheduler")


def make_rich_repo():
    """Fixture kind `rich`: prisma schema and client, resend, apscheduler, a compose
    file and 25 UI files, so five traits can be judged PRESENT on one repository."""
    root = make_repo("persistent_prisma")
    with open(os.path.join(root, "package.json"), "w", encoding="utf-8") as fh:
        json.dump({"name": "fixture", "dependencies": {"@prisma/client": "^5.0.0", "resend": "^3.0.0"}}, fh)
    with open(os.path.join(root, "requirements.txt"), "w", encoding="utf-8") as fh:
        fh.write("apscheduler==3.10.4\n")
    with open(os.path.join(root, "docker-compose.yml"), "w", encoding="utf-8") as fh:
        fh.write("services: {}\n")
    os.makedirs(os.path.join(root, "src", "ui"))
    for i in range(25):
        with open(os.path.join(root, "src", "ui", "c%02d.tsx" % i), "w", encoding="utf-8") as fh:
            fh.write("export {}\n")
    return root


def pred_V_ARCH_NO_STRUCTURAL_DETECTOR():
    """RESEARCH F5 finding 4: a trait nothing can detect (bulk, destructive) reads
    UNJUDGED `no-structural-detector` on every repository, even a rich one. The
    control shows the scan did judge: five detected traits read PRESENT on the same
    produced cache. This gate has held since 02-01 by design; its control is what
    makes the green informative."""
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state, repo = new_state(), make_rich_repo()
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        return False, "produce outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    traits = ar.read_traits(repo, state_dir=state)["traits"]
    problems = []
    for t in ("bulk", "destructive"):
        r = traits[t]
        if not (r["state"] == ar.UNJUDGED and r["reason"] == "no-structural-detector"):
            problems.append("%s read %s/%s (want UNJUDGED/no-structural-detector)" % (t, r["state"], r["reason"]))
    judged = {t: traits[t]["state"] for t in ("persistent", "external_effect", "scheduled", "distributed", "ui")}
    not_present = {t: s for t, s in judged.items() if s != ar.PRESENT}
    if not_present:
        problems.append("CONTROL: the scan did not judge these PRESENT on the rich fixture: %s" % not_present)
    return not problems, "; ".join(problems) or \
        "bulk and destructive UNJUDGED/no-structural-detector; control judged %s" % judged


GATES += [
    ("V-ARCH-POSITIVE-WORLD_MUTATION", pred_V_ARCH_POSITIVE_WORLD_MUTATION),
    ("V-ARCH-POSITIVE-EXTERNAL_EFFECT", pred_V_ARCH_POSITIVE_EXTERNAL_EFFECT),
    ("V-ARCH-POSITIVE-BACKGROUND_JOB", pred_V_ARCH_POSITIVE_BACKGROUND_JOB),
    ("V-ARCH-NO-STRUCTURAL-DETECTOR", pred_V_ARCH_NO_STRUCTURAL_DETECTOR),
]


# -- plan 02-04 Task 1: freshness by fingerprint (D-05, audit G4) -------------------
# A cache is evidence about the tree as it was when produced. The reader judges it fresh
# with a cheap fingerprint (root listing plus root manifest stats) and a re-stat of the
# evidence files, and reads STALE (every trait UNJUDGED `stale`) when any of them moved.

def _edit_file(path, text):
    """Rewrite `path` and set an explicit, distinct mtime: a coarse filesystem timestamp
    must never be what hides a change (RESEARCH F6)."""
    before = os.stat(path)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 7_000_000_000))


def pred_V_ARCH_STALE_MANIFEST():
    """Builds and produces its own fixtures, so a drill that mutates the fingerprint
    reaches producer and reader alike."""
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state, repo = new_state(), make_repo("prisma_marker_react")
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        return False, "produce outcome=%r reason=%r" % (res.get("outcome"), res.get("reason"))
    problems = []
    before = ar.read_traits(repo, state_dir=state)
    wm0 = _wm(ar.resolve(WM_ES, repo, state_dir=state))
    if before["cache"]["state"] != ar.CACHE_FRESH or wm0 is None or wm0["strength"] != ar.Strength.REQUIRED:
        problems.append("PRECONDITION: before the edit cache=%s WORLD_MUTATION=%s" % (
            before["cache"]["state"], wm0 and wm0["strength"]))
    # Same filename, different size, distinct mtime: only a root-manifest stat can see this.
    _edit_file(os.path.join(repo, "package.json"),
               json.dumps({"name": "fixture", "dependencies": {"react": "^18.0.0", "stripe": "^14.0.0"}}))
    after = ar.read_traits(repo, state_dir=state)
    subject = ar.resolve(WM_ES, repo, state_dir=state)
    wm1 = _wm(subject)
    reasons = sorted({r["reason"] for r in after["traits"].values()})
    if after["cache"]["state"] != ar.CACHE_STALE:
        problems.append("STALE-MANIFEST-NOT-DETECTED: after the edit cache=%s (want STALE)" % after["cache"]["state"])
    if not (set(after["traits"]) == set(ar.TRAITS)
            and all(r["state"] == ar.UNJUDGED and r["fact_state"] == ar.UNKNOWN
                    for r in after["traits"].values()) and reasons == ["stale"]):
        problems.append("STALE-TRAITS-NOT-UNJUDGED: states=%s reasons=%s" % (
            sorted({r["state"] for r in after["traits"].values()}), reasons))
    last_known = (after["cache"].get("last_known") or {})
    if not (set(last_known) == set(ar.TRAITS) and last_known["persistent"]["state"] == ar.PRESENT):
        problems.append("LAST-KNOWN-MISSING: %s" % sorted(last_known))
    if wm1 is None or not (wm1["strength"] == ar.Strength.CONDITIONAL and wm1["basis"] == "intent"):
        problems.append("STALE-STILL-REQUIRED: WORLD_MUTATION=%s" % ((wm1 and (wm1["strength"], wm1["basis"])),))
    # Control: a separate fixture with no edit is FRESH and REQUIRED.
    state_c, repo_c = new_state(), make_repo("prisma_marker_react")
    ts.produce(repo_c, state_dir=state_c)
    ctrl = ar.read_traits(repo_c, state_dir=state_c)
    wmc = _wm(ar.resolve(WM_ES, repo_c, state_dir=state_c))
    if ctrl["cache"]["state"] != ar.CACHE_FRESH or wmc is None or wmc["strength"] != ar.Strength.REQUIRED:
        problems.append("CONTROL: unedited fixture cache=%s WORLD_MUTATION=%s" % (
            ctrl["cache"]["state"], wmc and wmc["strength"]))
    return not problems, "; ".join(problems) or \
        "root package.json edited -> STALE, ten traits UNJUDGED/stale, last_known kept, WORLD_MUTATION REQUIRED -> %s/%s; control FRESH/REQUIRED" % (
            wm1["strength"], wm1["basis"])


GATES += [
    ("V-ARCH-STALE-MANIFEST", pred_V_ARCH_STALE_MANIFEST),
]


# -- plan 02-04 Task 2: the reader contract --------------------------------------------

def _stored_doc(repo, state):
    with open(ar.cache_path(repo, state_dir=state), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _produce_fixture(kind):
    """-> (state, repo): the fixture produced into a fresh state dir. Raises on failure."""
    state, repo = new_state(), make_repo(kind)
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        raise RuntimeError("produce(%s) outcome=%r reason=%r" % (kind, res.get("outcome"), res.get("reason")))
    return state, repo


_SCHEMA_REL = os.path.join("prisma", "schema.prisma")


def pred_V_ARCH_STALE_EVIDENCE_FILE():
    problems = []
    # (a) an evidence file edited in place: no directory listing moves, only its stat does.
    state, repo = _produce_fixture("persistent_prisma")
    _edit_file(os.path.join(repo, _SCHEMA_REL), "model Subscription {\n  id Int @id\n  name String\n}\n")
    edited = ar.read_traits(repo, state_dir=state)
    if edited["cache"]["state"] != ar.CACHE_STALE or "prisma/schema.prisma" not in edited["cache"]["reason"]:
        problems.append("EDIT-NOT-DETECTED: evidence file edited, cache=%s reason=%s" % (
            edited["cache"]["state"], edited["cache"]["reason"]))
    # (b) an evidence file deleted.
    state_b, repo_b = _produce_fixture("persistent_prisma")
    os.remove(os.path.join(repo_b, _SCHEMA_REL))
    deleted = ar.read_traits(repo_b, state_dir=state_b)
    if deleted["cache"]["state"] != ar.CACHE_STALE:
        problems.append("DELETE-NOT-DETECTED: evidence file deleted, cache=%s" % deleted["cache"]["state"])
    # (c) control: an untouched fixture is FRESH.
    state_c, repo_c = _produce_fixture("persistent_prisma")
    ctrl = ar.read_traits(repo_c, state_dir=state_c)
    if ctrl["cache"]["state"] != ar.CACHE_FRESH:
        problems.append("CONTROL: untouched fixture cache=%s" % ctrl["cache"]["state"])
    # (d) a data file (a database a program rewrites) is WEAK evidence by NAME: its content
    # says nothing the judgment uses, and re-stat'ing it would pin the cache STALE on every
    # repository that holds a live database. The walk saw it (precondition), the evidence
    # list does not hold it, and an edit leaves the cache FRESH.
    state_d, repo_d = new_state(), make_repo("ephemeral")
    os.makedirs(os.path.join(repo_d, "data"))
    data_file = os.path.join(repo_d, "data", "app.sqlite")
    with open(data_file, "wb") as fh:
        fh.write(b"SQLite format 3\x00" + b"\x00" * 64)
    ts.produce(repo_d, state_dir=state_d)
    doc_d = _stored_doc(repo_d, state_d)
    persistent_d = doc_d["traits"]["persistent"]
    listed = [e["path"] for e in doc_d["fingerprint"]["evidence_files"]]
    if not (persistent_d["state"] == ar.WEAK and "data/app.sqlite" in persistent_d["evidence"]):
        problems.append("PRECONDITION: the walk did not see the data file: persistent=%s %s" % (
            persistent_d["state"], persistent_d["evidence"]))
    _edit_file(data_file, "rewritten by the program under test")
    live = ar.read_traits(repo_d, state_dir=state_d)
    if "data/app.sqlite" in listed or live["cache"]["state"] != ar.CACHE_FRESH:
        problems.append("VOLATILE-DATA-FILE-STALES-CACHE: listed=%s cache=%s" % (
            "data/app.sqlite" in listed, live["cache"]["state"]))
    return not problems, "; ".join(problems) or \
        "edit and delete of prisma/schema.prisma -> STALE; untouched control FRESH; a rewritten data file stays FRESH (not listed among %d evidence files)" % len(listed)


def pred_V_ARCH_STALE_AGE():
    problems = []
    bound = getattr(ar, "TRAIT_MAX_AGE_S", None)
    if bound != 7 * 24 * 3600:
        problems.append("CONSTANT: TRAIT_MAX_AGE_S=%r (want 604800)" % (bound,))
    bound = 7 * 24 * 3600
    state, repo = _produce_fixture("persistent_prisma")
    produced_at = _stored_doc(repo, state)["produced_at"]
    over = ar.read_traits(repo, state_dir=state, now=produced_at + bound + 1)
    under = ar.read_traits(repo, state_dir=state, now=produced_at + bound - 60)
    if over["cache"]["state"] != ar.CACHE_STALE or "age" not in over["cache"]["reason"]:
        problems.append("AGE-NOT-DETECTED: now = produced_at + bound + 1 gave cache=%s reason=%s" % (
            over["cache"]["state"], over["cache"]["reason"]))
    elif not all(r["state"] == ar.UNJUDGED and r["reason"] == "stale" for r in over["traits"].values()):
        problems.append("AGE-TRAITS-NOT-UNJUDGED")
    if under["cache"]["state"] != ar.CACHE_FRESH:
        problems.append("AGE-TOO-EAGER: now = produced_at + bound - 60 gave cache=%s" % under["cache"]["state"])
    return not problems, "; ".join(problems) or \
        "bound=%d s: +1 s over reads STALE (%s), 60 s under reads FRESH" % (bound, over["cache"]["reason"])


def pred_V_ARCH_STALE_DEEP_BLINDSPOT():
    """Pitfall 4, pinned so nobody claims more than is true: the prompt-path reader does
    not see a new deep module."""
    state, repo = _produce_fixture("persistent_prisma")
    stored = _stored_doc(repo, state)["fingerprint"]
    deep = os.path.join(repo, "src", "a", "b", "c")
    os.makedirs(deep)
    with open(os.path.join(deep, "new_module.py"), "w", encoding="utf-8") as fh:
        fh.write("VALUE = 1\n")
    read = ar.read_traits(repo, state_dir=state)
    fp1_same = ar.fingerprint(repo, 1) == stored["fp1"]
    fp2_moved = ar.fingerprint(repo, 2) != stored["fp2"]
    ok = read["cache"]["state"] == ar.CACHE_FRESH and fp1_same and fp2_moved
    return ok, ("cache=%s fp1_unchanged=%s fp2_moved=%s -- documented bound: a module added below the root "
                "(src/a/b/c/new_module.py) is not an evidence file and not in the depth-1 fingerprint, so "
                "the reader stays FRESH; it is caught by the age backstop (TRAIT_MAX_AGE_S) and by the "
                "producer's depth-2 check on its next run" % (read["cache"]["state"], fp1_same, fp2_moved))


def pred_V_ARCH_MISS_UNJUDGED():
    """Pitfall 2: every way the cache can be unusable reads all ten traits UNJUDGED with a
    named cause, never ABSENT and never a shorter dict. Builds and produces its own fixture."""
    state, repo = _produce_fixture("persistent_prisma")
    path = ar.cache_path(repo, state_dir=state)
    with open(path, "rb") as fh:
        base_bytes = fh.read()
    max_bytes = getattr(ar, "CACHE_MAX_BYTES", 256 * 1024)
    problems = []
    if max_bytes != 256 * 1024:
        problems.append("CONSTANT: CACHE_MAX_BYTES=%r (want 262144)" % (getattr(ar, "CACHE_MAX_BYTES", None),))

    def variant(mutate):
        doc = json.loads(base_bytes.decode("utf-8"))
        mutate(doc)
        return json.dumps(doc).encode("utf-8")

    def drop_trait(doc):
        del doc["traits"]["ui"]

    def set_state(doc):
        doc["traits"]["persistent"]["state"] = "MAYBE"

    def foreign_key(doc):
        doc["repo_key"] = "another-repository-key"

    def pad(doc):
        doc["pad"] = "x" * (max_bytes + 10)

    def no_produced_at(doc):
        del doc["produced_at"]

    def traversal(doc):
        # A forged evidence path that climbs out of the repository: the reader would stat it.
        doc["fingerprint"]["evidence_files"][0]["path"] = "../outside.txt"

    cases = [
        ("no-file", None, ar.CACHE_MISSING, "no-cache"),
        ("non-json", b"\x00\xffnot json", ar.CACHE_MALFORMED, "cache-malformed"),
        ("other-schema", variant(lambda d: d.__setitem__("schema", "ucep-traits/9")), ar.CACHE_MALFORMED, "cache-malformed"),
        ("trait-missing", variant(drop_trait), ar.CACHE_MALFORMED, "cache-malformed"),
        ("state-MAYBE", variant(set_state), ar.CACHE_MALFORMED, "cache-malformed"),
        ("repo-key-mismatch", variant(foreign_key), ar.CACHE_MALFORMED, "cache-malformed"),
        ("oversize", variant(pad), ar.CACHE_MALFORMED, "cache-malformed"),
        ("produced-at-missing", variant(no_produced_at), ar.CACHE_MALFORMED, "cache-malformed"),
        ("evidence-path-traversal", variant(traversal), ar.CACHE_MALFORMED, "cache-malformed"),
    ]
    # Control: the unmodified document reads FRESH, so each case fails for its own change.
    ctrl = ar.read_traits(repo, state_dir=state)
    if ctrl["cache"]["state"] != ar.CACHE_FRESH:
        problems.append("CONTROL: the unmodified document reads %s" % ctrl["cache"]["state"])
    for label, payload, want_state, cause in cases:
        if payload is None:
            os.remove(path)
        else:
            with open(path, "wb") as fh:
                fh.write(payload)
        res = ar.read_traits(repo, state_dir=state)
        traits = res["traits"]
        if res["cache"]["state"] != want_state:
            # The document was accepted (or refused for another reason): not a miss at all.
            problems.append("MISS-NOT-REFUSED[%s]: cache=%s want=%s" % (label, res["cache"]["state"], want_state))
            continue
        absent = sorted(t for t, r in traits.items() if r["state"] == ar.ABSENT)
        if absent:
            problems.append("READ-ABSENT[%s]: a refused cache answered ABSENT for %s" % (label, absent))
            continue
        shape_ok = (set(traits) == set(ar.TRAITS)
                    and all(r["state"] == ar.UNJUDGED and r["fact_state"] == ar.UNKNOWN and r["reason"] == cause
                            for r in traits.values()))
        if not shape_ok:
            problems.append("MISS-NOT-UNJUDGED[%s]: traits=%d reasons=%s" % (
                label, len(traits), sorted({r["reason"] for r in traits.values()})))
    return not problems, "; ".join(problems) or \
        "%d unusable shapes (no file, non-JSON, other schema, missing trait, state MAYBE, foreign repo_key, > %d bytes, no produced_at, evidence path climbing out of the repo): ten UNJUDGED each with its cause, none ABSENT; control FRESH" % (
            len(cases), max_bytes)


def pred_V_ARCH_KEY_NORMALIZATION():
    problems = []
    state, repo = _produce_fixture("persistent_prisma")
    canonical = ar.subject_root(repo)
    expected = ar.cache_path(canonical, state_dir=state)
    spellings = {
        "canonical": canonical,
        "forward-slash": canonical.replace("\\", "/"),
        "trailing-separator": canonical + os.sep,
        "subdirectory": os.path.join(canonical, "src"),
        "dot-dot": os.path.join(canonical, "src", ".."),
    }
    for label, variant in (("upper-case", canonical.upper()), ("lower-case", canonical.lower())):
        if os.path.isdir(variant):          # only where the filesystem really folds case
            spellings[label] = variant
    if os.name == "nt" and len(canonical) > 2 and canonical[1] == ":":
        spellings["git-bash"] = "/" + canonical[0].lower() + "/" + canonical[3:].replace("\\", "/")
    for label, spelling in spellings.items():
        got = ar.cache_path(spelling, state_dir=state)
        fresh = ar.read_traits(spelling, state_dir=state)["cache"]["state"]
        if got is None or os.path.normcase(got) != os.path.normcase(expected) or fresh != ar.CACHE_FRESH:
            problems.append("KEY-DIFFERS[%s]: %r -> cache_path=%s read=%s" % (label, spelling, got, fresh))
    files_before = sorted(os.listdir(state))
    for label, bad in (("relative", "src"), ("missing-absolute", os.path.join(_HOME, "no-such-repo-directory"))):
        path = ar.cache_path(bad, state_dir=state)
        res = ar.read_traits(bad, state_dir=state)
        causes = {r["reason"] for r in res["traits"].values()}
        if not (path is None and res["cache"]["state"] == ar.CACHE_UNRESOLVABLE
                and res["cache"]["reason"] == "unresolvable-root" and causes == {"unresolvable-root"}):
            problems.append("INVENTED-KEY[%s]: cache_path=%s cache=%s causes=%s" % (
                label, path, res["cache"]["state"], sorted(causes)))
    if sorted(os.listdir(state)) != files_before:
        problems.append("a lookup created a file: %s -> %s" % (files_before, sorted(os.listdir(state))))
    return not problems, "; ".join(problems) or \
        "%d spellings of one repo (%s) share one cache file and read FRESH; relative and missing paths invent no key" % (
            len(spellings), ", ".join(sorted(spellings)))


_SAFE_CACHE_NAME = re.compile(r"^traits_[A-Za-z0-9-]+\.json\Z")


def pred_V_ARCH_CACHE_PATH_SAFE():
    """T-02-02, run LAST so it sees every cache this file produced: the filename comes
    from the repo key only, in the state directory it was given, with nothing else left."""
    problems, swept = [], 0
    state = new_state()
    awkward_parent = tempfile.mkdtemp(prefix="carch-repo-")
    _TEMP_DIRS.append(awkward_parent)
    awkward = os.path.join(awkward_parent, "we ird&name;..%$")
    os.makedirs(os.path.join(awkward, ".git"))
    roots = [make_repo("persistent_prisma"), make_repo("ephemeral"), awkward]
    for root in roots:
        p = ar.cache_path(root, state_dir=state)
        if p is None or not _SAFE_CACHE_NAME.match(os.path.basename(p)) \
                or os.path.normcase(os.path.dirname(p)) != os.path.normcase(state):
            problems.append("UNSAFE-PATH: %r -> %r" % (root, p))
    state_root = os.path.join(_HOME, ".claude", "state")
    for dirpath, _dirs, files in os.walk(state_root):
        for fn in files:
            if not fn.startswith(("traits_", ".traits_")):
                continue
            swept += 1
            if fn == "traits_production.jsonl":
                continue
            if not _SAFE_CACHE_NAME.match(fn):
                problems.append("UNSAFE-FILE: %s" % os.path.join(dirpath, fn))
    if swept == 0:
        problems.append("CONTROL: the sweep found no cache file, so it checked nothing")
    return not problems, "; ".join(problems) or \
        "%d awkward roots map to safe names inside the given state dir; %d produced files swept, all `traits_<key>.json`, no stray temp file" % (
            len(roots), swept)


def pred_V_ARCH_CACHE_OUTSIDE_REPO():
    """Pitfall 6: the cache lives in the per-user state dir; producing, skipping, reading and
    resolving leave the scanned repository byte-identical and put no cache in the worktree."""
    problems = []
    kinds = ("persistent_prisma", "ephemeral", "external_npm", "zero_manifest",
             "prisma_marker_react", "pip_fastapi")
    for kind in kinds:
        state, repo = new_state(), make_repo(kind)
        before = listing(repo)
        ts.produce(repo, state_dir=state)
        ts.produce(repo, state_dir=state)
        ar.resolve(WM_ES, repo, state_dir=state)
        ar.read_traits(repo, state_dir=state)
        after = listing(repo)
        if before != after:
            problems.append("REPO-CHANGED[%s]: %d -> %d entries" % (kind, len(before), len(after)))
    stray = [p for p in glob.glob(os.path.join(_PP_ROOT, "**", "traits_*.json"), recursive=True)
             if os.sep + ".git" + os.sep not in p]
    if stray:
        problems.append("CACHE-IN-WORKTREE: %s" % stray[:3])
    return not problems, "; ".join(problems) or \
        "%d fixture repos byte-identical across produce x2, resolve and read; no traits_*.json under the worktree" % len(kinds)


def _p95(values):
    s = sorted(values)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)]


def pred_V_ARCH_READ_ONLY():
    """G4: the prompt-path reader walks nothing, scans nothing, produces nothing and creates
    nothing. Counters are installed only around the resolve loop, after this predicate's own
    produce calls, so a producer-side effect can never be what turns it red."""
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    state_f, repo_f = _produce_fixture("persistent_prisma")            # fresh
    state_s, repo_s = _produce_fixture("prisma_marker_react")          # stale after the edit
    _edit_file(os.path.join(repo_s, "package.json"),
               json.dumps({"name": "fixture", "dependencies": {"react": "^18.0.0", "stripe": "^14.0.0"}}))
    state_m, repo_m = new_state(), make_repo("persistent_prisma")      # missing: never produced
    cases = [(repo_f, state_f, "fresh"), (repo_s, state_s, "stale"), (repo_m, state_m, "missing")]
    before = listing(_HOME)
    real_walk, real_scan, real_produce = os.walk, ts.scan, ts.produce
    walk_c, scan_c, prod_c = Counting(real_walk), Counting(real_scan), Counting(real_produce)
    os.walk, ts.scan, ts.produce = walk_c, scan_c, prod_c
    ms, seen = [], {}
    try:
        for i in range(20):
            repo, state, label = cases[i % 3]
            t0 = time.perf_counter()
            subject = ar.resolve(WM_ES, repo, state_dir=state)
            ms.append((time.perf_counter() - t0) * 1000.0)
            seen.setdefault(label, set()).add(subject["cache"]["state"])
        counts = (walk_c.calls, scan_c.calls, prod_c.calls)
    finally:
        os.walk, ts.scan, ts.produce = real_walk, real_scan, real_produce
    after = listing(_HOME)
    # Control: the same counters DO see a walk, a scan and a produce when one happens.
    cw, cs, cp = Counting(real_walk), Counting(real_scan), Counting(real_produce)
    os.walk, ts.scan, ts.produce = cw, cs, cp
    try:
        list(os.walk(repo_m))
        ts.scan(repo_m)
        ts.produce(repo_m, state_dir=new_state())
        control = (cw.calls, cs.calls, cp.calls)
    finally:
        os.walk, ts.scan, ts.produce = real_walk, real_scan, real_produce
    problems = []
    if counts[0] > 0:
        problems.append("READER-WALKED: os.walk calls=%d during 20 resolve calls" % counts[0])
    if counts[1] > 0:
        problems.append("READER-SCANNED: ts.scan calls=%d" % counts[1])
    if counts[2] > 0:
        problems.append("READER-PRODUCED: ts.produce calls=%d" % counts[2])
    if before != after:
        problems.append("READER-WROTE: _HOME listing changed (%d -> %d paths)" % (len(before), len(after)))
    if seen != {"fresh": {ar.CACHE_FRESH}, "stale": {ar.CACHE_STALE}, "missing": {ar.CACHE_MISSING}}:
        problems.append("BRANCHES-NOT-REACHED: %s" % {k: sorted(v) for k, v in seen.items()})
    if not (control[0] >= 1 and control[1] == 2 and control[2] == 1):
        problems.append("CONTROL: the counters did not see a deliberate walk/scan/produce: %s" % (control,))
    return not problems, "; ".join(problems) or \
        "walk=%d scan=%d produce=%d over 20 resolve calls (fresh, stale, missing); _HOME unchanged (%d paths); median=%.2f ms p95=%.2f ms; control saw walk=%d scan=%d produce=%d" % (
            counts[0], counts[1], counts[2], len(after), statistics.median(ms), _p95(ms),
            control[0], control[1], control[2])


def pred_V_ARCH_PRODUCER_SKIP():
    problems = []
    original = ts._walk
    walks = Counting(original)
    ts._walk = walks
    try:
        state, repo = new_state(), make_repo("persistent_prisma")
        first = ts.produce(repo, state_dir=state)
        path = ar.cache_path(repo, state_dir=state)
        with open(path, "rb") as fh:
            bytes1 = fh.read()
        mtime1 = os.stat(path).st_mtime_ns
        walks.calls = 0
        second = ts.produce(repo, state_dir=state)
        skip_walks = walks.calls
        with open(path, "rb") as fh:
            bytes2 = fh.read()
        mtime2 = os.stat(path).st_mtime_ns
        walks.calls = 0
        forced = ts.produce(repo, state_dir=state, force=True)
        force_walks = walks.calls
        produced_at = _stored_doc(repo, state)["produced_at"]
        walks.calls = 0
        aged = ts.produce(repo, state_dir=state, now=produced_at + ts.SKIP_WINDOW_S + 1)
        aged_walks = walks.calls
        # A moved root manifest (fp2 moves) and a moved evidence file each force a rewalk, each
        # with a skip control immediately before the edit.
        state_b, repo_b = new_state(), make_repo("persistent_prisma")
        ts.produce(repo_b, state_dir=state_b)
        ctrl_b = ts.produce(repo_b, state_dir=state_b)
        _edit_file(os.path.join(repo_b, "package.json"),
                   json.dumps({"name": "fixture", "dependencies": {"@prisma/client": "^5.0.0", "zod": "^3.0.0"}}))
        after_manifest = ts.produce(repo_b, state_dir=state_b)
        state_c, repo_c = new_state(), make_repo("persistent_prisma")
        ts.produce(repo_c, state_dir=state_c)
        ctrl_c = ts.produce(repo_c, state_dir=state_c)
        _edit_file(os.path.join(repo_c, _SCHEMA_REL), "model Subscription {\n  id Int @id\n  note String\n}\n")
        after_evidence = ts.produce(repo_c, state_dir=state_c)
    finally:
        ts._walk = original
    if first.get("outcome") != ts.WRITTEN:
        problems.append("first produce outcome=%r" % first.get("outcome"))
    if second.get("outcome") != ts.SKIPPED or skip_walks != 0 or mtime1 != mtime2 or bytes1 != bytes2:
        problems.append("SKIP-FAILED: outcome=%r walks=%d mtime_same=%s bytes_same=%s" % (
            second.get("outcome"), skip_walks, mtime1 == mtime2, bytes1 == bytes2))
    if forced.get("outcome") != ts.WRITTEN or force_walks != 1:
        problems.append("FORCE-FAILED: outcome=%r walks=%d" % (forced.get("outcome"), force_walks))
    if aged.get("outcome") != ts.WRITTEN or aged_walks != 1:
        problems.append("AGE-NOT-REWALKED: outcome=%r walks=%d" % (aged.get("outcome"), aged_walks))
    if ctrl_b.get("outcome") != ts.SKIPPED or after_manifest.get("outcome") != ts.WRITTEN:
        problems.append("MANIFEST-EDIT-NOT-REWALKED: control=%r after_edit=%r" % (
            ctrl_b.get("outcome"), after_manifest.get("outcome")))
    if ctrl_c.get("outcome") != ts.SKIPPED or after_evidence.get("outcome") != ts.WRITTEN:
        problems.append("EVIDENCE-EDIT-NOT-REWALKED: control=%r after_edit=%r" % (
            ctrl_c.get("outcome"), after_evidence.get("outcome")))
    if ts.SKIP_WINDOW_S != 24 * 3600:
        problems.append("CONSTANT: SKIP_WINDOW_S=%r" % ts.SKIP_WINDOW_S)
    return not problems, "; ".join(problems) or \
        "second produce SKIPPED (0 walks, file bytes and mtime unchanged); force and age rewalk once; edited root manifest and edited evidence file rewalk after a SKIPPED control"


def pred_V_ARCH_MANIFEST_NAMES_COVER():
    names = set(ar.MANIFEST_NAMES)
    parsed = {k.lower() for k in ts.PARSERS}
    missing = sorted(parsed - names)
    markers = ("schema.prisma", "docker-compose.yml", "compose.yaml", "fly.toml", "vercel.json",
               "plugin.yml", "dockerfile")
    missing_markers = [m for m in markers if m not in names]
    not_lower = sorted(n for n in names if n != n.lower())
    control = bool({"definitely-not-a-manifest.txt"} - names)       # the comparison can answer "missing"
    ok = not missing and not missing_markers and not not_lower and control
    return ok, "parsers missing=%s markers missing=%s not lower-case=%s control=%s (%d names)" % (
        missing, missing_markers, not_lower, control, len(names))


# -- plan 02-04 Task 2: reader drills (RESEARCH drills 2, 3, 4) ----------------------------
# Same four conditions as the 02-02 drills: the mutated predicate goes RED, the counting wrapper
# was reached, the red evidence names the sub-assertion under test, and after the restore the
# same predicate is GREEN on real code.

def pred_V_ARCH_DRILL_ABSENT_ON_MISS():
    """RESEARCH drill 2: a reader whose miss path answers ABSENT must turn the miss gate red."""
    original = ar.unjudged_reading

    def absent_on_miss(cause):
        return ar.reading(ar.ABSENT, ar.OBSERVED, [], cause)

    counter = Counting(absent_on_miss)
    ar.unjudged_reading = counter
    try:
        ok_m, ev_m = pred_V_ARCH_MISS_UNJUDGED()
    finally:
        ar.unjudged_reading = original
    restored_is_original = ar.unjudged_reading is original
    ok_r, _ev_r = pred_V_ARCH_MISS_UNJUDGED()
    _drill_report("absent-on-miss", [("V-ARCH-MISS-UNJUDGED", ok_m, ev_m)])
    named = "READ-ABSENT" in ev_m
    ok = ok_m is False and counter.calls > 0 and named and restored_is_original and ok_r is True
    return ok, "mutated ok=%s calls=%d named_sub_assertion=%s restored ok=%s | %s" % (
        ok_m, counter.calls, named, ok_r, ev_m)


def pred_V_ARCH_DRILL_READER_SCAN():
    """RESEARCH drill 3: a reader that walks, however little, must turn the read-only gate red."""
    original = ar.fingerprint

    def scanning(root, depth=1):
        for _item in os.walk(root):       # pull one item: the reader just walked
            break
        return original(root, depth)

    counter = Counting(scanning)
    ar.fingerprint = counter
    try:
        ok_m, ev_m = pred_V_ARCH_READ_ONLY()
    finally:
        ar.fingerprint = original
    restored_is_original = ar.fingerprint is original
    ok_r, _ev_r = pred_V_ARCH_READ_ONLY()
    _drill_report("reader-scan", [("V-ARCH-READ-ONLY", ok_m, ev_m)])
    named = "READER-WALKED" in ev_m
    ok = ok_m is False and counter.calls > 0 and named and restored_is_original and ok_r is True
    return ok, "mutated ok=%s calls=%d named_sub_assertion=%s restored ok=%s | %s" % (
        ok_m, counter.calls, named, ok_r, ev_m)


def pred_V_ARCH_DRILL_FP_IGNORES_MANIFEST():
    """RESEARCH drill 4: a fingerprint that ignores manifests must turn the stale-manifest gate
    red. The root manifest there is not an evidence file, so only the fingerprint can see it."""
    original_names, original_fp = ar.MANIFEST_NAMES, ar.fingerprint
    counter = Counting(original_fp)
    ar.MANIFEST_NAMES = frozenset()
    ar.fingerprint = counter
    try:
        ok_m, ev_m = pred_V_ARCH_STALE_MANIFEST()
    finally:
        ar.MANIFEST_NAMES, ar.fingerprint = original_names, original_fp
    restored = ar.MANIFEST_NAMES is original_names and ar.fingerprint is original_fp
    ok_r, _ev_r = pred_V_ARCH_STALE_MANIFEST()
    _drill_report("fp-ignores-manifest", [("V-ARCH-STALE-MANIFEST", ok_m, ev_m)])
    named = "STALE-MANIFEST-NOT-DETECTED" in ev_m
    ok = ok_m is False and counter.calls > 0 and named and restored and ok_r is True
    return ok, "mutated ok=%s calls=%d named_sub_assertion=%s restored ok=%s | %s" % (
        ok_m, counter.calls, named, ok_r, ev_m)


GATES += [
    ("V-ARCH-STALE-EVIDENCE-FILE", pred_V_ARCH_STALE_EVIDENCE_FILE),
    ("V-ARCH-STALE-AGE", pred_V_ARCH_STALE_AGE),
    ("V-ARCH-STALE-DEEP-BLINDSPOT", pred_V_ARCH_STALE_DEEP_BLINDSPOT),
    ("V-ARCH-MISS-UNJUDGED", pred_V_ARCH_MISS_UNJUDGED),
    ("V-ARCH-KEY-NORMALIZATION", pred_V_ARCH_KEY_NORMALIZATION),
    ("V-ARCH-CACHE-OUTSIDE-REPO", pred_V_ARCH_CACHE_OUTSIDE_REPO),
    ("V-ARCH-READ-ONLY", pred_V_ARCH_READ_ONLY),
    ("V-ARCH-PRODUCER-SKIP", pred_V_ARCH_PRODUCER_SKIP),
    ("V-ARCH-MANIFEST-NAMES-COVER", pred_V_ARCH_MANIFEST_NAMES_COVER),
    ("V-ARCH-DRILL-ABSENT-ON-MISS", pred_V_ARCH_DRILL_ABSENT_ON_MISS),
    ("V-ARCH-DRILL-READER-SCAN", pred_V_ARCH_DRILL_READER_SCAN),
    ("V-ARCH-DRILL-FP-IGNORES-MANIFEST", pred_V_ARCH_DRILL_FP_IGNORES_MANIFEST),
]


# -- plan 02-04 Task 3: the out-of-band producer CLI -------------------------------------
# `tools/capability_traits.py` is the entry point a scheduled task will host (Owner step O-1).
# Everything here runs inside the temp HOME: the subprocess environment pins HOME, USERPROFILE
# and CLAUDE_STATE_DIR, and `--all` is only ever driven with an explicit fixture list, never
# against the estate.

_CLI_PATH = os.path.join(_PP_ROOT, "tools", "capability_traits.py")
_LEDGER = os.path.join(STATE, "traits_production.jsonl")


def _cli_env():
    return dict(os.environ, HOME=_HOME, USERPROFILE=_HOME,
                CLAUDE_STATE_DIR=os.path.join(_HOME, ".claude", "state"), PYTHONIOENCODING="utf-8")


def _cli(*args):
    return subprocess.run([sys.executable, _CLI_PATH, *args], capture_output=True, text=True,
                          encoding="utf-8", env=_cli_env(), timeout=120)


def _ledger_rows():
    if not os.path.isfile(_LEDGER):
        return []
    with open(_LEDGER, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def pred_V_ARCH_CLI_ONE():
    problems = []
    repo = make_repo("external_npm")
    rows0 = len(_ledger_rows())
    first = _cli(repo)
    path = ar.cache_path(repo, state_dir=STATE)
    if first.returncode != 0 or "WRITTEN" not in first.stdout or not os.path.isfile(path):
        problems.append("FIRST-RUN: rc=%s written_in_stdout=%s cache_exists=%s stderr=%s" % (
            first.returncode, "WRITTEN" in first.stdout, os.path.isfile(path), first.stderr[-200:]))
    rows1 = _ledger_rows()
    if len(rows1) != rows0 + 1 or rows1[-1].get("mode") != "one":
        problems.append("LEDGER-AFTER-FIRST: rows %d -> %d last=%s" % (rows0, len(rows1), rows1[-1:] ))
    second = _cli(repo)
    if second.returncode != 0 or "SKIPPED" not in second.stdout or len(_ledger_rows()) != rows0 + 2:
        problems.append("SECOND-RUN: rc=%s skipped_in_stdout=%s rows=%d (want %d)" % (
            second.returncode, "SKIPPED" in second.stdout, len(_ledger_rows()), rows0 + 2))
    forced = _cli(repo, "--force")
    if forced.returncode != 0 or "WRITTEN" not in forced.stdout or len(_ledger_rows()) != rows0 + 3:
        problems.append("FORCE-RUN: rc=%s written_in_stdout=%s rows=%d (want %d)" % (
            forced.returncode, "WRITTEN" in forced.stdout, len(_ledger_rows()), rows0 + 3))
    last = (_ledger_rows() or [{}])[-1]
    if not {"ts", "mode", "projects", "outcomes", "truncated"} <= set(last):
        problems.append("LEDGER-ROW-SHAPE: %s" % sorted(last))
    return not problems, "; ".join(problems) or \
        "WRITTEN (cache file exists, ledger +1 mode=one), then SKIPPED (+1), then --force WRITTEN (+1); row keys %s" % sorted(last)


def pred_V_ARCH_CLI_SHOW():
    problems = []
    repo = make_repo("external_npm")
    ts.produce(repo, state_dir=STATE)
    rows0, listing0 = len(_ledger_rows()), sorted(os.listdir(STATE))
    shown = _cli("--show", repo)
    lines = shown.stdout.splitlines()
    named = [t for t in ar.TRAITS if any(l.strip().startswith(t + " ") for l in lines)]
    if shown.returncode != 0 or "FRESH" not in shown.stdout or named != list(ar.TRAITS):
        problems.append("SHOW-FRESH: rc=%s fresh_in_stdout=%s traits_named=%d stderr=%s" % (
            shown.returncode, "FRESH" in shown.stdout, len(named), shown.stderr[-200:]))
    never = make_repo("external_npm")                         # never produced
    shown2 = _cli("--show", never)
    lines2 = shown2.stdout.splitlines()
    unjudged = [l for l in lines2 if l.strip().split(" ")[0] in ar.TRAITS and "UNJUDGED" in l]
    if shown2.returncode != 0 or "NO_CACHE" not in shown2.stdout or len(unjudged) != 10:
        problems.append("SHOW-NO-CACHE: rc=%s no_cache_in_stdout=%s unjudged_lines=%d" % (
            shown2.returncode, "NO_CACHE" in shown2.stdout, len(unjudged)))
    if len(_ledger_rows()) != rows0 or sorted(os.listdir(STATE)) != listing0:
        problems.append("SHOW-WROTE: --show changed the ledger or the state dir")
    return not problems, "; ".join(problems) or \
        "--show prints FRESH with all ten traits for a produced repo, NO_CACHE with ten UNJUDGED lines for a never-produced one, writes nothing"


def pred_V_ARCH_CLI_UNRESOLVABLE():
    problems = []
    before = sorted(os.listdir(STATE)) if os.path.isdir(STATE) else []
    rows_before = len(_ledger_rows())
    for label, arg in (("relative", "src"), ("missing-absolute", os.path.join(_HOME, "no-such-repo-directory"))):
        res = _cli(arg)
        # rc 2 alone is also what the interpreter returns for a missing script, so the CLI's
        # own word for the refusal must be in its output.
        if res.returncode != 2 or "UNRESOLVABLE" not in res.stdout:
            problems.append("EXIT-NOT-2[%s]: rc=%s unresolvable_in_stdout=%s stderr=%s" % (
                label, res.returncode, "UNRESOLVABLE" in res.stdout, res.stderr[-100:]))
    bogus = _cli("--no-such-flag")
    if bogus.returncode != 2 or "usage" not in (bogus.stdout + bogus.stderr).lower():
        problems.append("UNKNOWN-ARGUMENT: rc=%s usage_printed=%s" % (
            bogus.returncode, "usage" in (bogus.stdout + bogus.stderr).lower()))
    after = sorted(os.listdir(STATE)) if os.path.isdir(STATE) else []
    if after != before or len(_ledger_rows()) != rows_before:
        problems.append("WROTE-ON-UNRESOLVABLE: state dir %s -> %s, ledger rows %d -> %d" % (
            before, after, rows_before, len(_ledger_rows())))
    return not problems, "; ".join(problems) or \
        "relative path, missing path and an unknown flag each exit 2 with nothing written (state dir and ledger unchanged)"


def pred_V_ARCH_CLI_ALL_INJECTED():
    """`--all` driven in-process over three fixtures, one of which fails. `find_repos` is
    replaced by a counting stub so a wiring mistake can never enumerate the real estate."""
    try:
        from tools import capability_traits
    except Exception as exc:  # noqa: BLE001 -- a RED run fails on the predicate, never crashes
        return False, "import tools.capability_traits failed: %s: %s" % (type(exc).__name__, exc)
    problems = []
    repos = [make_repo("persistent_prisma"), make_repo("ephemeral"), make_repo("external_npm")]
    victim = os.path.normcase(os.path.abspath(ar.subject_root(repos[1])))
    real_scan = ts.scan

    def scan_or_raise(root, **kw):
        if os.path.normcase(os.path.abspath(root)) == victim:
            raise RuntimeError("injected scan failure")
        return real_scan(root, **kw)

    scan_counter = Counting(scan_or_raise)
    # The CLI imports the TOP-LEVEL module `family_scan` (a sibling import, as
    # tools/tower_capsule.py does), a different object from `tools.family_scan`.
    tools_dir = os.path.join(_PP_ROOT, "tools")
    saved_path = list(sys.path)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import family_scan                                       # the same module object the CLI imports
    real_find = family_scan.find_repos
    bound_name = hasattr(capability_traits, "find_repos")
    real_bound = getattr(capability_traits, "find_repos", None)
    find_counter = Counting(lambda: [])
    family_scan.find_repos = find_counter
    if bound_name:
        capability_traits.find_repos = find_counter
    ts.scan = scan_counter
    rows0 = len(_ledger_rows())
    import contextlib
    import io
    printed = io.StringIO()               # the CLI prints one line per repository; keep it out of the gate log
    try:
        with contextlib.redirect_stdout(printed):
            rc = capability_traits.produce_all(repos)
        rows = _ledger_rows()
        enumerated = find_counter.calls
        # Positive control: with the stub standing in for the estate, produce_all(None) must
        # reach it exactly once, so a counter that cannot see the enumeration proves nothing.
        find_counter.calls = 0
        with contextlib.redirect_stdout(io.StringIO()):
            capability_traits.produce_all(None)
        control_calls = find_counter.calls
    finally:
        ts.scan = real_scan
        family_scan.find_repos = real_find
        if bound_name:
            capability_traits.find_repos = real_bound
        sys.path[:] = saved_path
    if rc != 1:
        problems.append("EXIT-CODE: produce_all returned %r (want 1, one scan failed)" % rc)
    new_rows = rows[rows0:rows0 + 1]
    row = new_rows[0] if new_rows else {}
    if len(rows) != rows0 + 1 or row.get("mode") != "all" or row.get("projects") != 3 \
            or row.get("outcomes") != {"WRITTEN": 2, "FAILED": 1}:
        problems.append("LEDGER-ROW: rows %d -> %d row=%s" % (rows0, len(rows), row))
    if enumerated != 0:
        problems.append("ENUMERATED-THE-ESTATE: find_repos called %d times for an explicit list" % enumerated)
    if control_calls != 1:
        problems.append("CONTROL: produce_all(None) reached the find_repos stub %d times (want 1)" % control_calls)
    if scan_counter.calls < 3:
        problems.append("INJECTION-NOT-REACHED: ts.scan wrapper called %d times (want >= 3)" % scan_counter.calls)
    return not problems, "; ".join(problems) or \
        "produce_all([3 fixtures]) -> rc=1, ledger row mode=all projects=3 with %d written and %d scan-failed, find_repos calls=0 for the explicit list; control produce_all(None) reached the stub %d time" % (
            row["outcomes"]["WRITTEN"], row["outcomes"]["FAILED"], control_calls)


GATES += [
    ("V-ARCH-CLI-ONE", pred_V_ARCH_CLI_ONE),
    ("V-ARCH-CLI-SHOW", pred_V_ARCH_CLI_SHOW),
    ("V-ARCH-CLI-UNRESOLVABLE", pred_V_ARCH_CLI_UNRESOLVABLE),
    ("V-ARCH-CLI-ALL-INJECTED", pred_V_ARCH_CLI_ALL_INJECTED),
]

# -- plan 02-05 Task 1: a trait transition is a different compiled subject (D-07) ------
# The subject `signature` is what Phase 8's challenge 3 will attack: adding persistent
# structure to a repository must show up first as STALE to the reader and then, after the
# producer runs, as a REQUIRED archetype and a different signature.

def _add_prisma(repo):
    """ephemeral -> persistent: a prisma schema file plus the client dependency, with an
    explicit distinct mtime on the edited manifest (RESEARCH F6)."""
    os.makedirs(os.path.join(repo, "prisma"))
    with open(os.path.join(repo, _SCHEMA_REL), "w", encoding="utf-8") as fh:
        fh.write("model Subscription {\n  id Int @id\n}\n")
    _edit_file(os.path.join(repo, "package.json"),
               json.dumps({"name": "fixture", "dependencies": {"react": "^18.0.0", "@prisma/client": "^5.0.0"}}))


def _sig(subject):
    return subject.get("signature")


def pred_V_ARCH_TRANSITION_PERSISTENT():
    if ar is None or ts is None:
        return False, "module import failed: ar=%s ts=%s" % (_AR_ERR, _TS_ERR)
    problems = []
    state, repo = _produce_fixture("ephemeral")
    f1 = _stored_doc(repo, state)["fingerprint"]["fp1"]
    before = {lang: ar.resolve(p, repo, state_dir=state) for lang, p in (("es", WM_ES), ("en", WM_EN))}
    for lang, subj in before.items():
        wm = _wm(subj)
        if wm is None or not (wm["strength"] == ar.Strength.CONDITIONAL and wm["basis"] == "intent"):
            problems.append("PRECONDITION[%s]: ephemeral WORLD_MUTATION=%s (want CONDITIONAL/intent)" % (
                lang, wm and (wm["strength"], wm["basis"])))
    s1 = _sig(before["es"])
    _add_prisma(repo)
    seen = ar.read_traits(repo, state_dir=state)
    if seen["cache"]["state"] != ar.CACHE_STALE:
        problems.append("TRANSITION-NOT-VISIBLE-TO-READER: before re-producing cache=%s (want STALE)" % seen["cache"]["state"])
    res = ts.produce(repo, state_dir=state)
    if res.get("outcome") != ts.WRITTEN:
        problems.append("REPRODUCE: outcome=%r reason=%r (the fingerprint changed, so no skip)" % (
            res.get("outcome"), res.get("reason")))
    f2 = _stored_doc(repo, state)["fingerprint"]["fp1"]
    after = {lang: ar.resolve(p, repo, state_dir=state) for lang, p in (("es", WM_ES), ("en", WM_EN))}
    for lang, subj in after.items():
        wm = _wm(subj)
        if wm is None or not (wm["strength"] == ar.Strength.REQUIRED and wm["basis"] == "structural+intent"):
            problems.append("PERSISTENT-NOT-REQUIRED[%s]: WORLD_MUTATION=%s (want REQUIRED/structural+intent)" % (
                lang, wm and (wm["strength"], wm["basis"])))
    s2 = _sig(after["es"])
    if not (isinstance(s1, str) and isinstance(s2, str) and len(s1) == 16 and len(s2) == 16):
        problems.append("SIGNATURE-MISSING: s1=%r s2=%r" % (s1, s2))
    elif s1 == s2:
        problems.append("SIGNATURE-UNCHANGED: ephemeral and persistent both sign %s" % s1)
    if f1 == f2:
        problems.append("FP1-UNCHANGED: stored fp1 is %s before and after" % f1)
    # Determinism: a repeat resolve of the same state, then the same final structure in a
    # different directory (no path, timestamp or evidence text may be inside the signature).
    again = _sig(ar.resolve(WM_ES, repo, state_dir=state))
    if again != s2:
        problems.append("SIGNATURE-NOT-REPEATABLE: %s then %s" % (s2, again))
    state2, repo2 = _produce_fixture("ephemeral")
    _add_prisma(repo2)
    ts.produce(repo2, state_dir=state2)
    twin = _sig(ar.resolve(WM_ES, repo2, state_dir=state2))
    if os.path.normcase(repo2) == os.path.normcase(repo):
        problems.append("PRECONDITION: the twin is the same directory")
    if twin != s2:
        problems.append("SIGNATURE-NOT-HOST-INDEPENDENT: same structure in two directories signs %s and %s" % (s2, twin))
    return not problems, "; ".join(problems) or \
        "CONDITIONAL/intent->REQUIRED/structural+intent sig=%s->%s fp1=%s->%s STALE seen; twin dir %s" % (
            s1, s2, f1, f2, "equal" if twin == s2 else "DIFFERS")


GATES += [
    ("V-ARCH-TRANSITION-PERSISTENT", pred_V_ARCH_TRANSITION_PERSISTENT),
]

# Runs after every other gate, so its sweep sees every cache file this process produced.
FINAL_GATES = [
    ("V-ARCH-CACHE-PATH-SAFE", pred_V_ARCH_CACHE_PATH_SAFE),
]

# A literal, enforced by the exit code (01-REVIEW IN-01): a count that satisfies
# itself would let a dropped gate read as green.
EXPECTED = 56


def main() -> int:
    try:
        for name, pred in GATES + FINAL_GATES:
            run_gate(name, pred)
        print("CAPABILITY_ARCHETYPES_PASS=%d/%d  threshold=%d/%d" % (
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
