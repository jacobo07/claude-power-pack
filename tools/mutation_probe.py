"""Mutation probe -- does this suite CATCH a defect, or only describe one?

G1 asks whether a suite contains text that looks like a failure expectation. Two
corrections later (D-001, D-002) it still cannot answer the question it was built
for. The proof is on record: tools/test_ias_c2_opportunity_cost.py gained six
assertions that feed bad input and require the rejection, read from branches in
the module, and G1 did not move -- because they are spelled `is None` and `== 0`.
A criterion satisfied by spelling and not by rigor is not a measure of rigor.

This asks the question directly. Break the module, run the suite, and see whether
it goes red:

    surviving mutant  the module was changed and the suite still passed. Whatever
                      that line does, nothing observes it.
    killed mutant     the suite noticed. That is coverage, demonstrated.

A suite that kills nothing is vacuous IN FACT, whatever its text looks like, and
that verdict cannot be earned by rewording an assertion.

    python tools/mutation_probe.py --suite tools/test_x.py --module modules/y/z.py

LIMIT, stated because omitting it would let a KILLS_ALL read as proof of a
correct suite: killing a mutant shows the suite is sensitive to that line, not
that its expected values are right. A suite asserting `count == 5` where the
true answer is 4 kills the mutant and is still wrong. Mutation bounds
sensitivity from below; it does not certify the oracle. `V-MUT-LIMIT` asserts
this blind spot exists rather than pretending it does not.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Sampled, not exhaustive: a full operator set on a 200-line module is hundreds of
# suite runs. The cap keeps a probe interactive; SAMPLED is reported so a partial
# sweep is never read as a complete one.
DEFAULT_MAX_MUTANTS = 10
# A suite that has not finished by here is neither killed nor survived. Reported
# as TIMEOUT rather than folded into either, since collapsing them would let a
# hang read as coverage.
SUITE_TIMEOUT_S = 180

_CMP_SWAP = {ast.Lt: ast.GtE, ast.Gt: ast.LtE, ast.LtE: ast.Gt, ast.GtE: ast.Lt,
             ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot,
             ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}


class _Mutator(ast.NodeTransformer):
    """Applies exactly the target-th mutation, counting candidates in walk order."""

    def __init__(self, target: int) -> None:
        self.target = target
        self.seen = 0
        self.description = ""

    def _hit(self, label: str) -> bool:
        fired = self.seen == self.target
        if fired:
            self.description = label
        self.seen += 1
        return fired

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if len(node.ops) == 1 and type(node.ops[0]) in _CMP_SWAP:
            old = type(node.ops[0])
            if self._hit(f"line {node.lineno}: {old.__name__} -> "
                         f"{_CMP_SWAP[old].__name__}"):
                node.ops = [_CMP_SWAP[old]()]
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        flipped = "or" if isinstance(node.op, ast.And) else "and"
        if self._hit(f"line {node.lineno}: boolop -> {flipped}"):
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool):
            if self._hit(f"line {node.lineno}: {node.value} -> {not node.value}"):
                return ast.Constant(value=not node.value)
        elif isinstance(node.value, int):
            if self._hit(f"line {node.lineno}: {node.value} -> {node.value + 1}"):
                return ast.Constant(value=node.value + 1)
        return node


def count_candidates(src: str) -> int:
    m = _Mutator(-1)
    m.visit(ast.parse(src))
    return m.seen


def mutate(src: str, index: int) -> tuple[str, str]:
    m = _Mutator(index)
    tree = m.visit(ast.parse(src))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree), m.description


def _run(suite: Path) -> int:
    # PYTHONDONTWRITEBYTECODE is not decoration. CPython invalidates a .pyc on
    # (mtime, size), and `==` -> `!=` is length-preserving: two mutants written in
    # the same second with identical size let the child import the PREVIOUS
    # mutant's bytecode and report SURVIVED for a line that is in fact covered.
    # Observed on the first real run of this probe -- a plausible, wrong result
    # from the instrument built to catch plausible, wrong results.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, str(suite)], cwd=str(REPO_ROOT),
                          capture_output=True, text=True, timeout=SUITE_TIMEOUT_S,
                          env=env)
    return proc.returncode


def _purge_cache(module: Path) -> None:
    """Drop any .pyc already on disk for this module, for the same reason."""
    cache = module.parent / "__pycache__"
    if not cache.is_dir():
        return
    for pyc in cache.glob(f"{module.stem}.*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass


def probe(suite: Path, module: Path, max_mutants: int = DEFAULT_MAX_MUTANTS) -> dict:
    """Break `module` one edit at a time; report which edits `suite` notices."""
    original = module.read_text(encoding="utf-8-sig")
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
    result: dict = {"suite": suite.name, "module": module.name,
                    "killed": [], "survived": [], "errors": []}

    try:
        if _run(suite) != 0:
            result["verdict"] = "UNMEASURABLE"
            result["reason"] = ("the suite does not pass before mutation, so a red "
                                "run proves nothing about the mutant")
            return result
    except subprocess.TimeoutExpired:
        result["verdict"] = "UNMEASURABLE"
        result["reason"] = f"the clean suite exceeded {SUITE_TIMEOUT_S}s"
        return result

    total = count_candidates(original)
    if total == 0:
        result["verdict"] = "UNMEASURABLE"
        result["reason"] = "no mutable construct in the module"
        return result

    # Evenly spaced rather than the first N, so a sample is not biased to the
    # module's import block.
    step = max(1, total // max_mutants)
    picks = list(range(0, total, step))[:max_mutants]
    result["candidates"] = total
    result["sampled"] = len(picks)

    try:
        for i in picks:
            try:
                mutated, label = mutate(original, i)
            except (SyntaxError, ValueError) as exc:
                result["errors"].append(f"mutant {i}: unparseable ({exc})")
                continue
            if mutated == ast.unparse(ast.parse(original)):
                continue                      # a no-op edit is not a mutant
            module.write_text(mutated, encoding="utf-8")
            _purge_cache(module)
            try:
                (result["killed"] if _run(suite) != 0
                 else result["survived"]).append(label)
            except subprocess.TimeoutExpired:
                result["errors"].append(f"{label}: TIMEOUT")
    finally:
        module.write_text(original, encoding="utf-8", newline="")
        _purge_cache(module)
        restored = hashlib.sha256(
            module.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
        result["restored_intact"] = restored == digest

    k, s = len(result["killed"]), len(result["survived"])
    if k + s == 0:
        result["verdict"] = "UNMEASURABLE"
        result["reason"] = "every sampled mutation failed to build"
    elif k == 0:
        result["verdict"] = "KILLS_NOTHING"
        result["reason"] = (f"{s} mutant(s) survived and none was caught. The suite "
                            "passes whether or not the module works.")
    elif s == 0:
        result["verdict"] = "KILLS_ALL"
        result["reason"] = f"all {k} sampled mutant(s) were caught"
    else:
        result["verdict"] = "PARTIAL"
        result["reason"] = f"{k} caught, {s} survived unnoticed"
    return result


def render(res: dict) -> str:
    lines = [f"MUTATION_PROBE suite={res['suite']} module={res['module']}",
             f"  verdict={res['verdict']}  {res.get('reason', '')}"]
    if "candidates" in res:
        lines.append(f"  mutable constructs={res['candidates']} "
                     f"sampled={res['sampled']} "
                     f"killed={len(res['killed'])} survived={len(res['survived'])}")
    for label in res["survived"]:
        lines.append(f"  SURVIVED  {label}")
    for label in res["errors"]:
        lines.append(f"  ERROR     {label}")
    if "restored_intact" in res and not res["restored_intact"]:
        lines.append("  WARNING   the module was NOT restored byte-identical; "
                     "run `git checkout -- <module>`")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Does this suite catch a real defect?")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--max", type=int, default=DEFAULT_MAX_MUTANTS)
    args = ap.parse_args(argv)

    suite, module = REPO_ROOT / args.suite, REPO_ROOT / args.module
    for p in (suite, module):
        if not p.is_file():
            print(f"no such file: {p}")
            return 2

    res = probe(suite, module, args.max)
    print(render(res))
    # KILLS_NOTHING is the only exit-1 condition. PARTIAL is information, not a
    # build break: a partially-covered module is the normal state and failing on
    # it would pressure someone into deleting the surviving branch.
    return 1 if res["verdict"] == "KILLS_NOTHING" else 0


if __name__ == "__main__":
    sys.exit(main())
