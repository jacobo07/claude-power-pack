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
import shutil
import sys
import tempfile
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
]

# A literal, enforced by the exit code (01-REVIEW IN-01): a count that satisfies
# itself would let a dropped gate read as green.
EXPECTED = 14


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
