#!/usr/bin/env python3
"""usea_outcome_contrast.py -- does the constitution change engineering OUTCOMES?

Phases I-III proved USEA exists, inherits across domains, and withholds itself
from work that does not need it. None of that is the question the programme is
for. The question is whether a session that carries the constitution produces
BETTER SOFTWARE than the same session without it -- and every earlier answer was
mechanistic: USEA tells you to verify more, USEA verifies more, therefore USEA is
better. That reasoning is circular and it was never evidence.

This instrument breaks the circle by holding everything constant except the
doctrine, and grading the ARTIFACT rather than the reasoning.

    control    = claude -p, sonnet, tools on, hooks off, temp cwd
    treatment  = the same invocation + parts/core.md appended to the system prompt

One variable. The payload is the exact bytes the always-read layer delivers, not
a paraphrase of them, because a paraphrase measures my summary and not the
artefact under test.

Grading is a HIDDEN EXECUTABLE ORACLE. Each task ships a checker the session
never sees, run against whatever the session left on disk when it exited. That is
the first-serious-attempt metric: not the first code generated, but the state at
declared-ready, after the session has finished whatever internal validation it
chose to do. A session is free to iterate privately; it is graded on what it
hands over.

WHY A SIBLING OF fd_04_contrast AND NOT AN EXTENSION OF IT
    fd_04_contrast varies the MODEL and scores TEXT against a regex rubric, to
    find which judgments retire to a cheaper substrate. This varies the DOCTRINE
    and scores ARTEFACTS by running them, which needs tools enabled and a real
    working directory. Same isolation recipe -- deliberately copied, not
    re-invented -- and the same absolute never-a-ratio control discipline. Folding
    the two together would bind doctrine-efficacy to the FD-04 deposits ledger,
    which answers a different question.

CONTROL DISCIPLINE (the part that makes the numbers mean anything)
    Before a single session is spent, every task proves BOTH POLES of its oracle
    are reachable: a known-good reference implementation must PASS and the naive
    implementation the task is designed to trap must FAIL. An oracle that cannot
    fail reports a clean green for a broken arm, and an oracle that cannot pass
    makes a working arm look broken. A task failing either control is discarded
    rather than run -- spending sessions against an instrument that cannot
    discriminate is how a benchmark produces confident noise.

    Plus a leakage check: the string "LAW II" or "LAW IX" appearing in a CONTROL
    transcript means the arms were not separated and the run is void. The control
    has no channel through which it could have seen those words.

WHAT THIS CANNOT SHOW
    The effect is measured on one model (sonnet, held constant so the variable
    stays the doctrine). Four tasks is a portfolio, not a sample. A result here
    is directional evidence about artefact quality; it is not a statistical claim
    and must never be reported as one.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parent.parent
CORE_MD = _PP_ROOT / "parts" / "core.md"

_CLI_TIMEOUT_S = 900
_MAX_BUDGET_USD = "1.50"
_LEAK_MARKERS = ("LAW II", "LAW IX", "strength_ladder", "architectural_truth")


# --------------------------------------------------------------------------- #
# Substrate runner -- isolation recipe copied from fd_04_contrast.ask_model.
# --------------------------------------------------------------------------- #
def run_session(prompt: str, workdir: Path, *, doctrine: str | None,
                model: str = "sonnet", timeout: int = _CLI_TIMEOUT_S) -> dict:
    """One session, one working directory. Never raises: a dead child is a
    recorded failure, never a silent pass."""
    settings = workdir / "_contrast_settings.json"
    settings.write_text(json.dumps({"hooks": {}, "disableAllHooks": True}),
                        encoding="utf-8")
    cmd = [shutil.which("claude") or "claude", "-p", prompt,
           "--model", model,
           "--settings", str(settings),
           "--permission-mode", "acceptEdits",
           "--output-format", "json",
           "--max-budget-usd", _MAX_BUDGET_USD]
    if doctrine:
        cmd += ["--append-system-prompt", doctrine]
    env = {**os.environ, "PP_FRONTIER_SESSION": "0"}
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              cwd=str(workdir), env=env,
                              stdin=subprocess.DEVNULL, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "note": f"timeout after {timeout}s",
                "wall_s": round(time.time() - t0, 1)}
    except Exception as e:  # noqa: BLE001 -- a broken child proves nothing
        return {"ok": False, "note": f"{type(e).__name__}: {e}",
                "wall_s": round(time.time() - t0, 1)}
    meta = {}
    try:
        meta = json.loads(proc.stdout or "{}")
    except Exception:
        pass
    settings.unlink(missing_ok=True)
    return {"ok": proc.returncode == 0,
            "rc": proc.returncode,
            "wall_s": round(time.time() - t0, 1),
            "cost_usd": meta.get("total_cost_usd"),
            "turns": meta.get("num_turns"),
            "permission_denials": len(meta.get("permission_denials") or []),
            "result_text": str(meta.get("result", ""))[:20_000],
            "stderr": (proc.stderr or "")[:600]}


def _run_py(workdir: Path, source: str, timeout: int = 120) -> subprocess.CompletedProcess:
    """Execute a probe script inside the task directory. The probe is written at
    grading time, so no session ever saw it."""
    probe = workdir / "_oracle_probe.py"
    probe.write_text(source, encoding="utf-8")
    try:
        return subprocess.run([sys.executable, str(probe)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, cwd=str(workdir), check=False)
    finally:
        probe.unlink(missing_ok=True)


def _verdict(cp: subprocess.CompletedProcess) -> tuple[bool, str]:
    tail = ((cp.stdout or "") + (cp.stderr or "")).strip().replace("\n", " | ")
    return cp.returncode == 0, tail[-400:]


# =========================================================================== #
# TASK A -- durable configuration write. Trap: LAW II's "exit 0 != external
# effect durable". A direct open(path,'w') returns success having destroyed the
# previous contents; the call reports done and the data is gone.
# =========================================================================== #
A_PROMPT = (
    "Create a file `store.py` in this directory containing a function "
    "`save_config(path, data)` that writes the dictionary `data` to `path` as "
    "JSON.\n\n"
    "This runs on a machine that can lose power at any instant, and other "
    "processes read `path` continuously. A reader must NEVER observe a "
    "truncated, partial, or corrupt file, and an interrupted write must leave "
    "the previous contents intact.\n\n"
    "Write only `store.py`. Do not create tests or other files."
)

A_PROBE = r'''
import json, os, sys
sys.path.insert(0, ".")

opened_for_write, renamed_to = [], []
def _audit(event, args):
    if event == "open":
        path, mode = args[0], args[1]
        if isinstance(path, str) and isinstance(mode, str) and any(
                c in mode for c in "wa+x"):
            opened_for_write.append(os.path.abspath(path))
    elif event == "os.rename":
        try:
            renamed_to.append(os.path.abspath(args[1]))
        except Exception:
            pass
sys.addaudithook(_audit)

from store import save_config

TARGET = os.path.abspath("cfg.json")
fails = []

# 1. basic correctness -- it must actually work when nothing goes wrong.
save_config(TARGET, {"ok": 1, "name": "alpha"})
try:
    got = json.load(open(TARGET, encoding="utf-8"))
except Exception as e:
    got = None
    fails.append("round-trip unreadable: %s" % e)
if got is not None and got != {"ok": 1, "name": "alpha"}:
    fails.append("round-trip mismatch: %r" % (got,))

# 2. an interrupted write must not destroy the previous contents. json.dump
#    streams, so a value that fails to serialize part-way leaves a truncated
#    file behind -- unless the write went somewhere else first.
opened_for_write.clear(); renamed_to.clear()
try:
    save_config(TARGET, {"big": "x" * 4000, "boom": {1, 2, 3}})
except Exception:
    pass
try:
    survived = json.load(open(TARGET, encoding="utf-8"))
except Exception as e:
    survived = None
    fails.append("previous contents destroyed by a failed write (%s)" % type(e).__name__)
if survived is not None and survived != {"ok": 1, "name": "alpha"}:
    fails.append("previous contents changed by a failed write: %r" % (survived,))

# 3. the target must be replaced, never written through. This is what makes a
#    concurrent reader safe; probes 1-2 alone pass a serialize-then-write
#    implementation that is still torn by a crash mid-write.
opened_for_write.clear(); renamed_to.clear()
save_config(TARGET, {"ok": 2})
if TARGET in opened_for_write:
    fails.append("target opened for writing directly (not replaced atomically)")
if TARGET not in renamed_to:
    fails.append("no atomic rename/replace landed on the target")

print("FAILS:" + ("; ".join(fails) if fails else "none"))
sys.exit(1 if fails else 0)
'''

A_REFERENCE = '''
import json, os, tempfile
def save_config(path, data):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
'''

A_NAIVE = '''
import json
def save_config(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
'''


# =========================================================================== #
# TASK B -- cross-process counter. Trap: read-modify-write loses updates under
# real concurrency, and a single-process test never shows it.
# =========================================================================== #
B_PROMPT = (
    "Create a file `counter.py` in this directory containing a function "
    "`increment(path)` that increases an integer counter stored as JSON in the "
    "file at `path` by one, creating it at 0 if absent, and returns the new "
    "value.\n\n"
    "Many SEPARATE OPERATING-SYSTEM PROCESSES on this machine call "
    "`increment(path)` on the same file at the same time. Every single call must "
    "be reflected in the final total -- no increment may be lost.\n\n"
    "Write only `counter.py`. Do not create tests or other files."
)

B_PROBE = r'''
import json, os, subprocess, sys
WORKERS, EACH = 8, 25
worker = "_b_worker.py"
with open(worker, "w", encoding="utf-8") as f:
    f.write(
        "import sys\n"
        "sys.path.insert(0, '.')\n"
        "from counter import increment\n"
        "for _ in range(%d):\n"
        "    increment('ctr.json')\n" % EACH)
if os.path.exists("ctr.json"):
    os.remove("ctr.json")
procs = [subprocess.Popen([sys.executable, worker],
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
         for _ in range(WORKERS)]
errs = []
for p in procs:
    _, e = p.communicate(timeout=180)
    if p.returncode != 0:
        errs.append((e or b"").decode("utf-8", "replace")[-200:])
expected = WORKERS * EACH
fails = []
if errs:
    fails.append("%d/%d workers crashed: %s" % (len(errs), WORKERS, errs[0]))
try:
    raw = json.load(open("ctr.json", encoding="utf-8"))
    final = raw if isinstance(raw, int) else (
        raw.get("count") if isinstance(raw, dict) and len(raw) == 1
        else list(raw.values())[0] if isinstance(raw, dict) else raw)
except Exception as e:
    final = None
    fails.append("counter file unreadable: %s" % e)
if final != expected:
    fails.append("lost updates: final=%r expected=%d" % (final, expected))
print("FAILS:" + ("; ".join(fails) if fails else "none"))
sys.exit(1 if fails else 0)
'''

B_REFERENCE = '''
import json, os, time
def increment(path):
    lock = str(path) + ".lock"
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            break
        except FileExistsError:
            time.sleep(0.001)
        except PermissionError:
            # Windows only, and the reason this reference failed its own
            # control at 4/8 workers: a lock file whose holder has just
            # unlinked it sits in DELETE_PENDING, and every further open of
            # that name answers ACCESS_DENIED rather than EEXIST until the
            # last handle closes. An O_EXCL spin that catches only
            # FileExistsError therefore dies under exactly the contention it
            # was written to survive.
            time.sleep(0.001)
    try:
        try:
            with open(path, encoding="utf-8") as f:
                value = json.load(f)
        except (OSError, ValueError):
            value = 0
        value = int(value) + 1
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(value, f)
        os.replace(tmp, path)
        return value
    finally:
        os.close(fd)
        try:
            os.unlink(lock)
        except OSError:
            pass
'''

B_NAIVE = '''
import json, os
def increment(path):
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)
    except (OSError, ValueError):
        value = 0
    value = int(value) + 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f)
    return value
'''


# =========================================================================== #
# TASK C -- unfamiliar dependency with a lying README. Trap: believe the
# documentation instead of reading the source. The repo's own HR-PREMISE-001 was
# born from exactly this, and core.md answers it with "never assume file/class/
# endpoint exists" plus "read before edit".
# =========================================================================== #
C_PROMPT = (
    "This directory contains a local package `vendorlib`. Create a file "
    "`search.py` containing a function `top_names(q, n)` that uses `vendorlib` "
    "to search for `q` and returns a list of the names of the first `n` "
    "results, in order. If there are fewer than `n` results, return all of "
    "them.\n\n"
    "Write only `search.py`. Do not modify `vendorlib`."
)

# The real module. Keyword-only `limit`, a dict return with the rows under
# "items", and each row keyed "label" rather than "name".
C_VENDOR_INIT = '''"""vendorlib -- minimal local search client."""

_ROWS = [
    {"label": "alpha", "score": 9},
    {"label": "bravo", "score": 8},
    {"label": "charlie", "score": 7},
    {"label": "delta", "score": 6},
    {"label": "echo", "score": 5},
]


def fetch(query, *, limit=None, retries=3):
    """Return {"items": [...], "cursor": str|None}. `limit` is keyword-only."""
    if not isinstance(query, str):
        raise TypeError("query must be str")
    rows = [r for r in _ROWS if query.lower() in r["label"]] or list(_ROWS)
    if limit is not None:
        rows = rows[:limit]
    return {"items": rows, "cursor": None}
'''

# The decoy. Plausible, prominent, and two versions out of date.
C_VENDOR_README = '''# vendorlib

Tiny search client.

## Usage

    import vendorlib
    results = vendorlib.fetch("alpha", 10)
    for r in results:
        print(r["name"])

`fetch(query, count)` returns a **list** of result dicts, each with a `name`
and a `score` key. Raises `LookupError` when nothing matches.
'''

C_PROBE = r'''
import sys
sys.path.insert(0, ".")
from search import top_names
fails = []
try:
    got = top_names("a", 2)
except Exception as e:
    got = None
    fails.append("top_names raised %s: %s" % (type(e).__name__, e))
if got is not None:
    if not isinstance(got, list):
        fails.append("expected a list, got %r" % (type(got).__name__,))
    elif got != ["alpha", "bravo"]:
        fails.append("wrong result: %r (expected ['alpha', 'bravo'])" % (got,))
try:
    few = top_names("delta", 5)
    if few != ["delta"]:
        fails.append("short-result case wrong: %r (expected ['delta'])" % (few,))
except Exception as e:
    fails.append("short-result case raised %s: %s" % (type(e).__name__, e))
print("FAILS:" + ("; ".join(fails) if fails else "none"))
sys.exit(1 if fails else 0)
'''

C_REFERENCE = '''
import vendorlib
def top_names(q, n):
    out = vendorlib.fetch(q, limit=n)
    return [row["label"] for row in out["items"]][:n]
'''

# Exactly what the README tells you to write.
C_NAIVE = '''
import vendorlib
def top_names(q, n):
    results = vendorlib.fetch(q, n)
    return [r["name"] for r in results][:n]
'''


# =========================================================================== #
# TASK D -- a one-line typo. There is no trap. This task exists to measure the
# COST of carrying the doctrine on work that does not need it: if the treatment
# arm spends materially more, or touches anything it was not asked to touch,
# that is evidence AGAINST the constitution and is reported as such.
# =========================================================================== #
D_PROMPT = (
    "In `greet.py`, the docstring of `greet` contains the misspelling "
    "'Retrun'. Fix that one typo. Change nothing else."
)

D_ORIGINAL = '''"""Greeting helpers."""


def greet(name):
    """Retrun a friendly greeting for the given name."""
    return "Hello, " + name + "!"


def farewell(name):
    """Return a parting message for the given name."""
    return "Goodbye, " + name + "."
'''
D_FIXED = D_ORIGINAL.replace("Retrun", "Return")

D_PROBE = r'''
import sys, pathlib
EXPECTED = __EXPECTED__
fails = []
p = pathlib.Path("greet.py")
if not p.exists():
    fails.append("greet.py is gone")
else:
    actual = p.read_text(encoding="utf-8")
    if actual != EXPECTED:
        if "Retrun" in actual:
            fails.append("typo not fixed")
        else:
            fails.append("typo fixed but the file was otherwise modified "
                         "(%d chars vs %d expected)" % (len(actual), len(EXPECTED)))
extra = sorted(q.name for q in pathlib.Path(".").iterdir()
               if q.name not in ("greet.py",) and not q.name.startswith("_"))
if extra:
    fails.append("unrequested files created: %s" % (extra,))
print("FAILS:" + ("; ".join(fails) if fails else "none"))
sys.exit(1 if fails else 0)
'''.replace("__EXPECTED__", repr(D_FIXED))


# --------------------------------------------------------------------------- #
# Task table.
# --------------------------------------------------------------------------- #
def _scaffold_none(_d: Path) -> None:
    pass


def _scaffold_c(d: Path) -> None:
    pkg = d / "vendorlib"
    pkg.mkdir(exist_ok=True)
    (pkg / "__init__.py").write_text(C_VENDOR_INIT, encoding="utf-8")
    (d / "README.md").write_text(C_VENDOR_README, encoding="utf-8")


def _scaffold_d(d: Path) -> None:
    (d / "greet.py").write_text(D_ORIGINAL, encoding="utf-8")


TASKS = {
    "A": {"domain": "persistence / durable write", "prompt": A_PROMPT,
          "probe": A_PROBE, "scaffold": _scaffold_none, "artifact": "store.py",
          "reference": A_REFERENCE, "naive": A_NAIVE,
          "criterion": "writes via a temporary file and atomically replaces the "
                       "target; an interrupted write leaves prior contents intact"},
    "B": {"domain": "concurrency / lost update", "prompt": B_PROMPT,
          "probe": B_PROBE, "scaffold": _scaffold_none, "artifact": "counter.py",
          "reference": B_REFERENCE, "naive": B_NAIVE,
          "criterion": "8 concurrent OS processes x 25 increments == 200"},
    "C": {"domain": "unfamiliar dependency / hidden contract", "prompt": C_PROMPT,
          "probe": C_PROBE, "scaffold": _scaffold_c, "artifact": "search.py",
          "reference": C_REFERENCE, "naive": C_NAIVE,
          "criterion": "works against the real vendorlib signature, not the "
                       "signature its README documents"},
    "D": {"domain": "trivial / restraint control", "prompt": D_PROMPT,
          "probe": D_PROBE, "scaffold": _scaffold_d, "artifact": "greet.py",
          "reference": D_FIXED, "naive": D_ORIGINAL,
          "criterion": "the typo is fixed and NOTHING else in the tree changed"},
}


# --------------------------------------------------------------------------- #
# Controls -- both poles reachable, or the task is not run at all.
# --------------------------------------------------------------------------- #
def controls_hold(key: str) -> dict:
    task = TASKS[key]
    out = {}
    for pole, body in (("positive", task["reference"]), ("negative", task["naive"])):
        d = Path(tempfile.mkdtemp(prefix=f"usea_ctl_{key}_{pole}_"))
        try:
            task["scaffold"](d)
            (d / task["artifact"]).write_text(body, encoding="utf-8")
            ok, tail = _verdict(_run_py(d, task["probe"]))
            out[pole] = {"oracle_pass": ok, "detail": tail}
        finally:
            shutil.rmtree(d, ignore_errors=True)
    out["ok"] = (out["positive"]["oracle_pass"] is True
                 and out["negative"]["oracle_pass"] is False)
    return out


# --------------------------------------------------------------------------- #
# One arm of one task.
# --------------------------------------------------------------------------- #
def run_arm(key: str, arm: str, doctrine: str, *, model: str, trial: int) -> dict:
    task = TASKS[key]
    d = Path(tempfile.mkdtemp(prefix=f"usea_{key}_{arm}_{trial}_"))
    try:
        task["scaffold"](d)
        before = {p.name for p in d.iterdir()}
        session = run_session(task["prompt"], d,
                              doctrine=(doctrine if arm == "treatment" else None),
                              model=model)
        after = {p.name for p in d.iterdir() if not p.name.startswith("_")}
        produced = (d / task["artifact"]).exists()
        if produced:
            ok, tail = _verdict(_run_py(d, task["probe"]))
        else:
            ok, tail = False, f"{task['artifact']} was never created"
        # Keep the artefact. The working directory is destroyed below, and
        # without this a PASS/FAIL is a number nobody can interrogate -- the
        # whole point of grading artefacts rather than reasoning is that the
        # artefact can be read afterwards and the difference pointed at.
        artifact_src = ""
        if produced:
            try:
                artifact_src = (d / task["artifact"]).read_text(
                    encoding="utf-8", errors="replace")[:8000]
            except OSError:
                pass
        leaked = [m for m in _LEAK_MARKERS
                  if arm == "control" and m in session.get("result_text", "")]
        return {"task": key, "arm": arm, "trial": trial,
                "oracle_pass": ok, "oracle_detail": tail,
                "artifact_produced": produced,
                "artifact_source": artifact_src,
                "files_added": sorted(after - before),
                "session_ok": session.get("ok"),
                "cost_usd": session.get("cost_usd"),
                "turns": session.get("turns"),
                "wall_s": session.get("wall_s"),
                "permission_denials": session.get("permission_denials"),
                "leak_markers": leaked,
                "note": session.get("note", "") or session.get("stderr", "")[:200]}
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="USEA doctrine outcome contrast")
    ap.add_argument("--tasks", nargs="*", default=sorted(TASKS))
    ap.add_argument("--arms", nargs="*", default=["control", "treatment"])
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--controls-only", action="store_true",
                    help="validate every oracle without spending a session")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    if not CORE_MD.exists():
        print(f"treatment payload missing: {CORE_MD}", file=sys.stderr)
        return 3
    doctrine = CORE_MD.read_text(encoding="utf-8")

    print(f"treatment payload: {CORE_MD} "
          f"({len(doctrine.encode('utf-8'))} bytes utf-8)")
    print("=== CONTROLS (both poles must be reachable) ===")
    controls, runnable = {}, []
    for key in args.tasks:
        c = controls_hold(key)
        controls[key] = c
        flag = "OK  " if c["ok"] else "VOID"
        print(f"  {flag} {key}  reference={c['positive']['oracle_pass']} "
              f"naive={c['negative']['oracle_pass']}  ({TASKS[key]['domain']})")
        if not c["ok"]:
            print(f"       positive: {c['positive']['detail']}")
            print(f"       negative: {c['negative']['detail']}")
        else:
            runnable.append(key)

    report = {"model": args.model, "trials": args.trials,
              "payload_bytes": len(doctrine.encode("utf-8")),
              "controls": controls, "runs": []}

    if args.controls_only:
        _emit(report, args.out)
        return 0 if len(runnable) == len(args.tasks) else 1

    print("\n=== ARMS ===")
    for trial in range(1, args.trials + 1):
        for key in runnable:
            for arm in args.arms:
                r = run_arm(key, arm, doctrine, model=args.model, trial=trial)
                report["runs"].append(r)
                print(f"  {key} t{trial} {arm:<9} oracle="
                      f"{'PASS' if r['oracle_pass'] else 'FAIL'}  "
                      f"${r['cost_usd']}  turns={r['turns']}  "
                      f"{r['wall_s']}s  files={r['files_added']}")
                if not r["oracle_pass"]:
                    print(f"      -> {r['oracle_detail'][:220]}")
                if r["leak_markers"]:
                    print(f"      !! LEAK in control arm: {r['leak_markers']}")

    _summarise(report)
    _emit(report, args.out)
    leaked = any(r["leak_markers"] for r in report["runs"])
    return 1 if leaked else 0


def _summarise(report: dict) -> None:
    print("\n=== SUMMARY ===")
    runs = report["runs"]
    for arm in ("control", "treatment"):
        sub = [r for r in runs if r["arm"] == arm]
        if not sub:
            continue
        passed = sum(1 for r in sub if r["oracle_pass"])
        cost = sum(r["cost_usd"] or 0 for r in sub)
        turns = sum(r["turns"] or 0 for r in sub)
        print(f"  {arm:<9} first-attempt oracle {passed}/{len(sub)}   "
              f"total ${cost:.2f}   turns {turns}")
    print("  per task:")
    for key in sorted({r["task"] for r in runs}):
        row = {r["arm"]: r for r in runs if r["task"] == key}
        c, t = row.get("control"), row.get("treatment")
        fmt = lambda r: ("PASS" if r["oracle_pass"] else "FAIL") if r else "-"
        cost = lambda r: f"${r['cost_usd']:.2f}" if r and r["cost_usd"] else "-"
        print(f"    {key} {TASKS[key]['domain']:<38} "
              f"control={fmt(c):<4} {cost(c):<7} "
              f"treatment={fmt(t):<4} {cost(t)}")
    if any(r["leak_markers"] for r in runs):
        print("  RUN VOID: doctrine markers found in a control transcript.")


def _emit(report: dict, out: str | None) -> None:
    if out:
        Path(out).write_text(json.dumps(report, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        print(f"\nreport -> {out}")


if __name__ == "__main__":
    sys.exit(main())
