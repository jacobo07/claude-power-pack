"""V-TLEDGER-* gates: genesis-task-ledger MERGED into the Goal Spine's own closure evidence.

The Task Ledger's two differentials, in the canonical owner (modules/gsd_x/goal), never in a
parallel ledger:
  artifact binding  already there: convergence.evaluate pins tree, revision and gate files
  attribution       each SATISFIED row now names the epoch/provider/handle that produced its
                    verdict (driven through the real sweep._apply_verdicts)
  reviewer!=worker  by construction: the ONLY production caller of convergence.satisfy is
                    sweep._apply_verdicts, which takes verdicts solely from a gate receipt. An
                    AST ratchet pins that set, resolving each module's own import aliases (a
                    receiver matched by name missed an alias once -- instrument-before-claim).

Liveness is NOT claimed here: the Goal Spine engine has no live invoker yet (vault/liveness
registry: gsd_x/goal is PLANNED, wired by UWCP S6).
"""
from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from modules.gsd_x.goal import contract as gc     # noqa: E402
from modules.gsd_x.goal import convergence as cv  # noqa: E402
from modules.gsd_x.goal import log as gl          # noqa: E402
from modules.gsd_x.goal import sweep as sw        # noqa: E402

TARGET_MODULE = "modules.gsd_x.goal.convergence"
EXPECTED_CALLERS = {("modules/gsd_x/goal/sweep.py", "_apply_verdicts")}
PIN = (("tools/gate.py", "1" * 64),)
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


# ---------------------------------------------------------------- structural sweep
def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def _aliases(tree: ast.AST, modname: str) -> tuple[set[str], set[str]]:
    """Names this module bound to the convergence MODULE, and names bound to its satisfy FUNCTION."""
    mods, funcs = set(), set()
    pkg = modname.rsplit(".", 1)[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == TARGET_MODULE:
                    mods.add(a.asname or a.name)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = pkg.split(".")
                base = ".".join(parts[:len(parts) - node.level + 1] + ([node.module] if node.module else []))
            for a in node.names:
                full = f"{base}.{a.name}" if base else a.name
                if full == TARGET_MODULE:
                    mods.add(a.asname or a.name)
                elif base == TARGET_MODULE and a.name == "satisfy":
                    funcs.add(a.asname or a.name)
    return mods, funcs


def callers(source: str, relpath: str, modname: str) -> set[tuple[str, str]]:
    tree = ast.parse(source)
    mods, funcs = _aliases(tree, modname)
    if modname == TARGET_MODULE:
        funcs.add("satisfy")
    found = set()

    def visit(node, scope):
        for child in ast.iter_child_nodes(node):
            s = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else scope
            if isinstance(child, ast.Call):
                f = child.func
                if (isinstance(f, ast.Attribute) and f.attr == "satisfy" and isinstance(f.value, ast.Name)
                        and f.value.id in mods) or (isinstance(f, ast.Name) and f.id in funcs):
                    found.add((relpath, scope))
            visit(child, s)
    visit(tree, "<module>")
    return found


def production_callers() -> tuple[set, int]:
    out, scanned = set(), 0
    for base in ("modules", "tools"):
        for p in (ROOT / base).rglob("*.py"):
            rel = p.relative_to(ROOT).as_posix()
            if p.name.startswith("test_") or "/tests/" in rel or "__pycache__" in rel:
                continue
            try:
                src = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            scanned += 1
            try:
                out |= callers(src, rel, _module_name(p))
            except SyntaxError:
                continue
    return out, scanned


# ---------------------------------------------------------------- behaviour through the sweep
def fresh(base: Path):
    lg = gl.GoalLog("b" * 40, "g-ledger", base=base)
    gc.declare(lg, "goal ledger", ["it works"], [], {"paths": ["src"]})
    s = gc.project(lg)
    cv.accept_obligation(lg, s, "ob-outcome", cv.OUTCOME, "x", "python tools/gate.py", PIN, "t", gate_class="unit")
    return lg


def receipt(state, tree="t" * 40, pin=PIN):
    return SimpleNamespace(verdicts=[{"gate": "tools/gate.py", "exit_status": 0, "observed": "3 passed",
                                      "tree_hash": tree, "revision": state.revision, "gate_class": "unit",
                                      "gate_pin": [list(p) for p in pin]}])


def main() -> int:
    base = Path(tempfile.mkdtemp(prefix="tledger-"))
    lg = fresh(base)
    record = SimpleNamespace(epoch_id="ep-7", provider="gate", handle="run-42", spec={"obligation": "ob-outcome"})

    bad = sw._apply_verdicts(lg, receipt(gc.project(lg), pin=(("tools/other.py", "2" * 64),)), record, "sweep")
    o = cv.project_convergence(gc.project(lg)).obligations["ob-outcome"]
    check("V-TLEDGER-REFUSED-NO-SOURCE", o.disposition != cv.SATISFIED and o.verdict_source is None,
          f"a verdict from an unpinned gate satisfies nothing and attributes nothing: {bad}")

    out = sw._apply_verdicts(lg, receipt(gc.project(lg)), record, "sweep")
    o = cv.project_convergence(gc.project(lg)).obligations["ob-outcome"]
    check("V-TLEDGER-SATISFIED", o.disposition == cv.SATISFIED, str(out))
    check("V-TLEDGER-ATTRIBUTED", o.verdict_source == {"epoch": "ep-7", "provider": "gate", "handle": "run-42"},
          f"the ledger row names what produced the verdict: {o.verdict_source}")
    check("V-TLEDGER-ARTIFACT-BOUND", (o.verdict or {}).get("tree_hash") == "t" * 40
          and (o.verdict or {}).get("gate_pin") == [list(p) for p in PIN], "tree and gate files pinned on the row")

    # A meaningful revision, then an explicit carry: the old proof AND its attribution must go.
    gc.revise(lg, gc.project(lg).last_seq + 1, "goal ledger v2", ["it works", "and it is attributed"],
              [], {"paths": ["src"]}, actor="t")
    cv.carry_obligation(lg, gc.project(lg), "ob-outcome", "same meaning", "t")
    o2 = cv.project_convergence(gc.project(lg)).obligations["ob-outcome"]
    check("V-TLEDGER-CARRY-CLEARS", o2.verdict_source is None and o2.disposition == cv.ACCEPTED,
          "a carried obligation loses its old proof AND its old attribution")

    found, scanned = production_callers()
    check("V-TLEDGER-FLOOR", scanned > 200 and len(found) >= 1, f"{scanned} production modules scanned, {len(found)} caller(s)")
    check("V-TLEDGER-ONLY-SWEEP", found == EXPECTED_CALLERS,
          f"production callers of convergence.satisfy: {sorted(found)}")
    stale = EXPECTED_CALLERS - found
    check("V-TLEDGER-NO-STALE", not stale, f"expected callers no longer found: {sorted(stale)}")

    synthetic = ("from modules.gsd_x.goal import convergence as conv\n"
                 "from modules.gsd_x.goal.convergence import satisfy as sat\n"
                 "def worker_claims(log, s, v):\n    conv.satisfy(log, s, 'ob', v, 'worker')\n"
                 "def other(log, s, v):\n    sat(log, s, 'ob', v, 'worker')\n")
    red = callers(synthetic, "modules/fake/worker.py", "modules.fake.worker")
    check("V-TLEDGER-RED-DRILL", red == {("modules/fake/worker.py", "worker_claims"), ("modules/fake/worker.py", "other")},
          f"an aliased module call and an aliased function import are both caught: {sorted(red)}")
    decoy = callers("from modules.gsd_x.mission import closure as cl\ndef f(o, v):\n    cl.satisfy(o, v)\n",
                    "modules/fake/decoy.py", "modules.fake.decoy")
    check("V-TLEDGER-DECOY", not decoy, "mission.closure.satisfy is a different function and is not counted")
    print(f"TLEDGER_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
