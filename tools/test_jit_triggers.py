#!/usr/bin/env python3
"""V-gates for the JIT loader's trigger vocabulary (tools/jit_skill_loader.py).

A trigger is an admission gate on context. Every byte it admits is spent whether
or not the task needed it, so the gate must be shown to REFUSE on the words that
are not evidence, not merely to fire on the words that are.

Founding measurement (2026-07-27): replayed over 2,513 real user prompts, the
graphql_ops trigger fired 85 times, and 76 of those matched only on a generic
engineering word -- "InitConfig resolver (Code node)" pulling in two Apollo
GraphQL skills at full depth.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "jit_skill_loader_under_test", _ROOT / "tools" / "jit_skill_loader.py")
_JIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_JIT)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"[OK] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {diag}")


def _rx(name: str) -> re.Pattern:
    for tname, rx, _mods, _prio in _JIT.TRIGGERS:
        if tname == name:
            return rx
    raise KeyError(name)


# Real prompt fragments, taken verbatim from the transcripts that fired the old
# trigger. None of them is about GraphQL.
FALSE_POSITIVES = [
    "Created InitConfig resolver (Code node)",
    "Updated the InitConfig resolver with three-tier priority",
    "the path resolver returns an absolute path",
    "this mutation of the config file is not idempotent",
    "cancel the subscription before the daemon exits",
    "a state mutation without a lock is the bug",
]

# Genuine GraphQL, which must still fire.
TRUE_POSITIVES = [
    "add a field to schema.graphql",
    "load the queries from ops.gql",
    "we use graphql for the public API",
    "type Mutation { addUser(name: String): User }",
    "query GetUser($id: ID!) { user(id: $id) { name } }",
    "mutation AddUser($n: String) { add(name: $n) { id } }",
    "const typeDefs = `type Query { me: User }`",
    "Subscription { messageAdded { id } }",
]


def main() -> int:
    rx = _rx("graphql_ops")

    # V-JIT-TRIGGER-REFUSES: the negative pole, and the whole point of the fix.
    fired = [p for p in FALSE_POSITIVES if rx.search(p)]
    if not fired:
        _ok("V-JIT-TRIGGER-REFUSES",
            f"{len(FALSE_POSITIVES)}/{len(FALSE_POSITIVES)} generic-word prompts refused")
    else:
        _fail("V-JIT-TRIGGER-REFUSES", f"still fires on: {fired}")

    # V-JIT-TRIGGER-ADMITS: refusing everything would be a cheaper bug, not a fix.
    missed = [p for p in TRUE_POSITIVES if not rx.search(p)]
    if not missed:
        _ok("V-JIT-TRIGGER-ADMITS",
            f"{len(TRUE_POSITIVES)}/{len(TRUE_POSITIVES)} real GraphQL prompts admitted")
    else:
        _fail("V-JIT-TRIGGER-ADMITS", f"missed real GraphQL: {missed}")

    # V-JIT-TRIGGER-FSFALLBACK: a real project that names none of the vocabulary is
    # still caught by the .graphql/.gql walk, which is what makes the narrowing safe.
    src = _JIT.__file__ and Path(_JIT.__file__).read_text(encoding="utf-8")
    if 'name == "graphql_ops"' in src and "fs_has" in src:
        _ok("V-JIT-TRIGGER-FSFALLBACK", "FS-walk fallback still guards the narrowed regex")
    else:
        _fail("V-JIT-TRIGGER-FSFALLBACK", "narrowing the regex removed its safety net")

    # V-JIT-TRIGGER-SKIPDIRS: test fixtures must never classify the repo (2026-06-08).
    if {"tests", "fixtures"} <= set(_JIT.SKIP_DIRS):
        _ok("V-JIT-TRIGGER-SKIPDIRS", "tests/ and fixtures/ excluded from the walk")
    else:
        _fail("V-JIT-TRIGGER-SKIPDIRS", "fixture dirs can drive runtime injection again")

    total = _passes + _fails
    print(f"JIT_TRIGGER_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
