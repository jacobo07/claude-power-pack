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
import json
import os
import re
import shutil
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

# A literal, enforced by the exit code (01-REVIEW IN-01): a count that satisfies
# itself would let a dropped gate read as green.
EXPECTED = 37


def main() -> int:
    try:
        for name, pred in GATES:
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
