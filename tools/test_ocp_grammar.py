"""V-OCP-GRAMMAR-* gates for modules/provider_routing/capital_grammar.py. Run: python tools/test_ocp_grammar.py

Pure and hermetic. Every refusal is paired with a control where the same shape is admitted. Prints
OCP_GRAMMAR_PASS=n/m, exit 1 on any failure.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from modules.provider_routing import capital_grammar as g  # noqa: E402

M = 1_000_000
GATES: list = []


def gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


def op(text):
    r = g.parse_intent(text)
    return (r["op"], r["value"]) if r else None


@gate("V-OCP-GRAMMAR-ADD-ALIASES")
def _():
    for t in ("subelo por 70M", "sube por 70M", "incrementa 70M", "suma 70M", "add 70M", "raise by 70M",
              "plus 70M", "increase by 70M", "ADD +70M", "Súbelo por 70M."):
        assert op(t) == ("ADD", 70 * M), t


@gate("V-OCP-GRAMMAR-SET-ALIASES")
def _():
    for t in ("subelo a 70M", "sube a 70M", "pon el tope en 70M", "set to 70M", "raise to 70M", "SET total 70M"):
        assert op(t) == ("SET", 70 * M), t
    r = g.parse_intent("modify econ-safex to 102M")
    assert (r["op"], r["value"], r["goal"]) == ("SET", 102 * M, "econ-safex")


@gate("V-OCP-GRAMMAR-ADD-IS-NOT-SET")
def _():
    assert op("subelo por 70M") != op("subelo a 70M")  # the control for the pair above


@gate("V-OCP-GRAMMAR-KEEP-STOP")
def _():
    assert op("keep") == ("KEEP", None) and op("mantener") == ("KEEP", None)
    for t in ("stop", "para", "cierra el goal"):
        assert op(t) == ("STOP", None), t
    r = g.parse_intent("revoke econ-safex")
    assert (r["op"], r["goal"]) == ("STOP", "econ-safex")


@gate("V-OCP-GRAMMAR-UNITS")
def _():
    assert op("add 1.5M") == ("ADD", 1_500_000)
    assert op("add 250k") == ("ADD", 250_000)
    assert op("add 70,000,000") == ("ADD", 70 * M)
    assert op("add 70_000_000") == ("ADD", 70 * M)
    assert op("add 5000") == ("ADD", 5000)


@gate("V-OCP-GRAMMAR-AMBIGUOUS-OFFERS-CHOICE")
def _():
    for t in ("subelo 70M", "70M"):
        r = g.parse_intent(t)
        assert r["op"] == "CLARIFY" and r["value"] == 70 * M, t
        assert r["choices"] == ["ADD +70000000", "SET total 70000000"], r["choices"]
    assert g.parse_intent("2") is None and g.parse_intent("1") is None  # menu answers are not capital


@gate("V-OCP-GRAMMAR-REJECTS-BAD-AMOUNTS")
def _():
    for t, why in (("add 0M", "positive"), ("add 5", "unit"), ("add 1.5", "decimal"),
                   ("add 1.2.3M", "malformed"), ("add 999999M", "ceiling"), ("subelo a 0", "positive")):
        r = g.parse_intent(t)
        assert r and r["op"] == "INVALID" and why in r["reason"], (t, r)
    assert g.parse_intent("add -5M") is None  # a minus sign is not in the grammar at all


@gate("V-OCP-GRAMMAR-NEGATION")
def _():
    for t in ("don't add 70M", "do not subelo por 70M", "no subas a 70M", "never stop", "can't keep"):
        assert g.parse_intent(t) is None, t
    assert op("add 70M") == ("ADD", 70 * M)  # same shape without the negation is admitted


@gate("V-OCP-GRAMMAR-WHOLE-MESSAGE-ONLY")
def _():
    for t in ("please add 70M to the thing", "add 70M and then delete everything", "tell me how to stop",
              "can you keep going", "hello", "", "   "):
        assert g.parse_intent(t) is None, t
    assert g.parse_intent(None) is None and g.parse_intent(42) is None


@gate("V-OCP-GRAMMAR-NO-MODEL-NO-IO")
def _():
    src = (REPO / "modules" / "provider_routing" / "capital_grammar.py").read_text(encoding="utf-8")
    for banned in ("anthropic", "subprocess", "open(", "requests", "urllib", "socket", "os.environ"):
        assert banned not in src, banned


def main() -> int:
    ok = 0
    for name, fn in GATES:
        try:
            fn()
            ok += 1
            print(f"PASS {name}")
        except Exception:
            print(f"FAIL {name}\n{traceback.format_exc(limit=2)}")
    print(f"OCP_GRAMMAR_PASS={ok}/{len(GATES)}")
    return 0 if ok == len(GATES) else 1


if __name__ == "__main__":
    sys.exit(main())
