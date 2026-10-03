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


GATES = [
    ("V-ARCH-HERMETIC-HOME", pred_V_ARCH_HERMETIC_HOME),
    ("V-ARCH-TRACER-PRODUCE", pred_V_ARCH_TRACER_PRODUCE),
    ("V-ARCH-TRACER-WORLD_MUTATION", pred_V_ARCH_TRACER_WORLD_MUTATION),
    ("V-ARCH-TRACER-MISS", pred_V_ARCH_TRACER_MISS),
    ("V-ARCH-LIVENESS-DECLARED", pred_V_ARCH_LIVENESS_DECLARED),
]

# A literal, enforced by the exit code (01-REVIEW IN-01): a count that satisfies
# itself would let a dropped gate read as green.
EXPECTED = 5


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
