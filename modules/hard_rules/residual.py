#!/usr/bin/env python3
"""residual.py -- the residual-move compiler (PR-PROHIBITIONS-DO-NOT-CONFLICT-001).

The frontier judgment this implements: Hard Rules are prohibitions, and prohibitions
cannot contradict one another -- they can only jointly shrink the set of legal moves.
So there is no precedence to compute. A "conflict" is the appearance of an empty legal
set, and it appears for exactly one reason: no move has been declared legal under every
possible join, so the agent picks by recency.

This compiler declares one. Given the rules fired on an action, it takes the JOIN of
their prohibitions over a fixed move universe and returns the surviving moves. The
RESIDUAL move -- halt the guarded frontier, write a block artifact naming every fired
rule and each rule's unblock phrase, close with an active Owner-actionable statement --
is the constitutional guarantee: it must survive every join, and the compiler asserts
that rather than assuming it.

Where this compiler REFUSES, on purpose:

  * A fired rule that is a MANDATE, not a prohibition. Mandates CAN genuinely conflict
    (do X / never X), and the whole argument depends on the corpus being prohibitions.
    A compiler that quietly treated a mandate as a prohibition would manufacture a
    resolution that does not exist. Verdict UNSAFE_JOIN, and it names the rule.
  * A fired rule whose forbidden object cannot be determined. Verdict UNDECIDABLE
    (fail-closed). Guessing the scope of a STOP is how the recency bug got in.
  * A rule that forbids the residual itself. Verdict NO_RESIDUAL -- the seam the
    frontier answer named against its own design, surfaced rather than hidden.

The output is never "the Hard Rules conflict". That sentence is the bug.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# The move universe. A prohibition forbids one or more of these classes; the residual
# is a member, which is what makes "legal under every join" a checkable claim rather
# than a slogan.
RESIDUAL = "RESIDUAL"
MOVES = (
    "PROCEED_ON_GUARDED_OBJECT",
    "COMMIT",
    "DEPLOY",
    "DISPATCH_SUBAGENT",
    "DESTRUCTIVE_FS_OP",
    "ROTATE_CREDENTIAL",
    "INSTALL_PLUGIN",
    "EMIT_UNREDACTED",
    # The anti-waiting doctrine's forbidden object. Naming it as a move class is the
    # whole point of the scope corollary: that doctrine binds the FORM of the closing
    # emission, not the state of being blocked -- so it removes one move and leaves the
    # residual (an ACTIVE closer) untouched. Read as "you may not proceed", it looked
    # like a deadlock; read as what its trigger actually names, it is not.
    "CLOSE_WITH_PASSIVE_WAIT",
    RESIDUAL,
)

# A rule's ACTION is a STOP plus a ritual. The STOP is a prohibition; the ritual is a
# PRECONDITION of acting, never an unconditional obligation to act. A rule is a mandate
# only when it obliges an act with no guarded act to refrain from.
_PROHIBITIVE = re.compile(
    r"\b(never|do not|don't|refuse|stop|forbidden|prohibited|must not|cannot|"
    r"can't|no\b|before|without|halt|block|deny)\b", re.I)
_MANDATORY_ONLY = re.compile(
    r"\b(always (?:immediately )?(?:rotate|delete|deploy|push|install)|"
    r"you must (?:rotate|delete|deploy|push|install))\b", re.I)

PROHIBITION = "PROHIBITION"
MANDATE = "MANDATE"
UNKNOWN = "UNKNOWN"


@dataclass
class FiredRule:
    rule_id: str
    trigger: str = ""
    stop: str = ""
    exception: str = ""
    forbids: list = field(default_factory=list)   # explicit move classes, when declared
    kind: str = ""                                # explicit override, when declared


def classify(rule: FiredRule) -> str:
    """PROHIBITION / MANDATE / UNKNOWN. Explicit declaration always wins over prose."""
    if rule.kind in (PROHIBITION, MANDATE):
        return rule.kind
    text = f"{rule.trigger} {rule.stop}"
    if _MANDATORY_ONLY.search(text) and not _PROHIBITIVE.search(text):
        return MANDATE
    if _PROHIBITIVE.search(text):
        return PROHIBITION
    return UNKNOWN


def compile_residual(fired: list, universe=MOVES) -> dict:
    """Join the prohibitions of every fired rule and return the surviving moves."""
    if not fired:
        return {"verdict": "NO_RULES_FIRED", "legal": list(universe),
                "residual": RESIDUAL, "fired": [],
                "reason": "nothing fired -- the unguarded path is legal"}

    kinds = {r.rule_id: classify(r) for r in fired}
    mandates = [rid for rid, k in kinds.items() if k == MANDATE]
    if mandates:
        return {"verdict": "UNSAFE_JOIN", "legal": [], "residual": RESIDUAL,
                "fired": list(kinds),
                "reason": f"mandate(s) fired: {mandates}. Mandates can genuinely "
                          "conflict; the prohibition join does not apply and this "
                          "compiler refuses to manufacture a resolution."}
    unknown = [r.rule_id for r in fired
               if kinds[r.rule_id] == UNKNOWN or not r.forbids]
    if unknown:
        return {"verdict": "UNDECIDABLE", "legal": [], "residual": RESIDUAL,
                "fired": list(kinds),
                "reason": f"forbidden object undeterminable for {unknown}. A STOP "
                          "binds exactly the object its TRIGGER names; guessing that "
                          "scope is the recency bug. Declare `forbids` on the rule."}

    forbidden = set()
    for r in fired:
        forbidden |= {m for m in r.forbids if m in universe}
    legal = [m for m in universe if m not in forbidden]

    if RESIDUAL not in legal:
        offenders = [r.rule_id for r in fired if RESIDUAL in r.forbids]
        return {"verdict": "NO_RESIDUAL", "legal": legal, "residual": None,
                "fired": list(kinds), "offenders": offenders,
                "reason": f"{offenders} forbid the residual itself. The constitutional "
                          "guarantee is broken -- this is the seam the design named "
                          "against itself, and it escalates rather than resolving."}

    return {"verdict": "RESIDUAL_AVAILABLE",
            "legal": legal, "residual": RESIDUAL, "fired": list(kinds),
            "forbidden": sorted(forbidden),
            "unblock": {r.rule_id: (r.exception or "(no declared exception)")
                        for r in fired},
            "reason": "prohibitions joined; the residual survives. Halt the guarded "
                      "frontier, write the block artifact naming every fired rule and "
                      "its unblock phrase, and close with the Owner's single next move."}


def gate_new_rule(rule: FiredRule) -> dict:
    """The ONLY check rule-addition needs: does this rule forbid the residual?

    Local, one rule at a time -- no global re-ranking, which is what keeps rules
    addable by the bug that caused them.
    """
    if RESIDUAL in (rule.forbids or []):
        return {"admitted": False,
                "reason": "a rule may not forbid the residual move -- it is the one "
                          "move guaranteed legal under every join"}
    return {"admitted": True}


def classify_empty_class(class_name: str, rules: list, rejects: list) -> dict:
    """An empty trigger class is a router-completeness bug, never a conflict.

    Rules were written and are inert on a schema failure -> FAIL_CLOSED (that is the
    disarmed kill switch this repo already lived through). No rule was ever written and
    no incident ever occurred -> FAIL_OPEN plus a visible Owner-queue entry, because
    fail-closed on a virgin class contradicts the founding rule that a prohibition
    requires an incident.
    """
    if rules:
        return {"class": class_name, "verdict": "POPULATED", "rules": len(rules)}
    if rejects:
        return {"class": class_name, "verdict": "FAIL_CLOSED",
                "rejects": len(rejects),
                "reason": "rules exist for this class and are INERT on a schema "
                          "failure -- proceeding would re-run the disarmed kill switch"}
    return {"class": class_name, "verdict": "FAIL_OPEN_WITH_QUEUE",
            "reason": "virgin class -- no rule, no incident. A prohibition requires an "
                      "incident, so proceed, but surface it in the Owner queue."}


# --------------------------------------------------------------------------- #
# Corpus audit -- test the frontier premise instead of assuming it.
# --------------------------------------------------------------------------- #
def audit_corpus() -> dict:
    """Is every real Hard Rule actually a prohibition? Measure, do not assume."""
    from modules.rule_compiler.parser import load_corpus
    counts = {PROHIBITION: [], MANDATE: [], UNKNOWN: []}
    for r in load_corpus():
        fr = FiredRule(rule_id=r.rule_id, trigger=r.trigger, stop=r.stop)
        counts[classify(fr)].append(r.rule_id)
    return {"total": sum(len(v) for v in counts.values()),
            "prohibition": len(counts[PROHIBITION]),
            "mandate": len(counts[MANDATE]),
            "unknown": len(counts[UNKNOWN]),
            "mandates": counts[MANDATE], "unknowns": counts[UNKNOWN][:10]}


def load_cases(path: str) -> list:
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    return json.loads(raw.lstrip("﻿"))


def run_case(case: dict) -> dict:
    fired = [FiredRule(**r) for r in case.get("fired", [])]
    out = compile_residual(fired)
    exp = case.get("expect_verdict")
    return {"case": case.get("id"), "expected": exp, **out,
            "matches_expectation": (exp is None or out["verdict"] == exp)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Residual-move compiler")
    ap.add_argument("--cases", default=str(_PP_ROOT / "vault" / "hard_rules" /
                                           "conflict_cases.json"))
    ap.add_argument("--audit-corpus", action="store_true")
    args = ap.parse_args(argv)

    if args.audit_corpus:
        print(json.dumps(audit_corpus(), ensure_ascii=False, indent=2))
        return 0
    rows = [run_case(c) for c in load_cases(args.cases)]
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0 if all(r["matches_expectation"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
