"""Amendment A1 gate: C15 (receipts + two-strike freeze) and C16 (A1 spend <= cap, UNKNOWN fails).

`--obligation C15|C16` judges the real gen2 ledger and exits 1 unless it is provably fine.
No argument runs a hermetic selftest on temp fixtures (never the real ledger), including one mutant.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import cep_gen2  # noqa: E402

LEDGER = REPO / cep_gen2.LEDGER_REL
passes = fails = 0


def _ok(tag: str, ev: str = "") -> None:
    global passes
    passes += 1
    print(f"  ok   {tag} {ev}")


def _fail(tag: str, diag: str = "") -> None:
    global fails
    fails += 1
    print(f"  FAIL {tag} {diag}")


def c15(led: dict, root: Path) -> list:
    """A tranche is started when its completion_plan entry is an object with started=true; a bare integer is an
    unspent budget. Started + unfrozen needs a receipt passing check_receipt."""
    a1 = led.get("a1")
    if not isinstance(a1, dict):
        return ["C15 ledger has no a1 block"]
    frozen = set(a1.get("frozen") or [])
    tr = (led.get("completion_plan") or {}).get("tranches") or {}
    out = []
    for tid, t in tr.items():
        if tid == "reserve" or tid in frozen or not (isinstance(t, dict) and t.get("started")):
            continue
        out.extend(cep_gen2.check_receipt(tid, t.get("receipt"), root))
    limit = a1.get("strike_limit")
    if not cep_gen2._pos_int(limit):
        out.append(f"C15 strike_limit {limit!r} is not a positive integer")
        return out
    for fam, d in (a1.get("families") or {}).items():
        strikes = (d or {}).get("strikes")
        if not isinstance(strikes, int) or isinstance(strikes, bool):
            out.append(f"C15 family {fam} strikes {strikes!r} is not an integer (unknown never passes)")
        elif strikes >= limit:
            live = [x for x in (d.get("tranches") or []) if x not in frozen]
            if live or not d.get("tranches"):
                out.append(f"C15 family {fam} at {strikes} strikes: unfrozen/undeclared tranches {live or 'none declared'}")
    return out


def c16(led: dict) -> list:
    a1 = led.get("a1")
    spent, cap = (a1 or {}).get("spent"), (a1 or {}).get("cap")
    if not isinstance(a1, dict) or not cep_gen2._pos_int(cap):
        return ["C16 ledger a1.cap missing or not a positive integer"]
    if not isinstance(spent, int) or isinstance(spent, bool):  # MUT-NULL
        return [f"C16 a1.spent {spent!r} is UNKNOWN: unmeasured never passes"]
    return [] if spent <= cap else [f"C16 a1.spent {spent:,} exceeds cap {cap:,}"]


def _measurement_receipt(root: Path, tid: str) -> str:
    (root / "ev.md").write_text("evidence\n", encoding="utf-8")
    rel = f"{tid}-receipt.json"
    (root / rel).write_text(json.dumps({"kind": "measurement", "work_unit": tid, "cost": {"unit": "processed", "value": 10},
                                         "decision_value": "floor for T3 economics"}), encoding="utf-8")
    return rel


def _base(root: Path) -> dict:
    return {"a1": {"cap": 100, "spent": 50, "frozen": ["T2"], "strike_limit": 2,
                   "families": {"fam": {"strikes": 0, "tranches": ["T2"]}}},
            "completion_plan": {"tranches": {"T0": {"started": True, "receipt": _measurement_receipt(root, "T0")},
                                             "T2": {"started": True}, "T3": 6, "reserve": 1}}}


def selftest_cases(c16_fn=c16) -> list:
    """Returns [(tag, passed)]; c16_fn is injectable so the mutant can swap the null handling."""
    res = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = _base(root)
        res.append(("V-A1-C15-valid-receipt-passes", not c15(base, root)))
        d = copy.deepcopy(base)
        d["completion_plan"]["tranches"]["T0"].pop("receipt")
        res.append(("V-A1-C15-missing-receipt-fails", bool(c15(d, root))))
        d = copy.deepcopy(base)
        d["completion_plan"]["tranches"]["T0"]["receipt"] = "nope.json"
        res.append(("V-A1-C15-unreadable-receipt-fails", bool(c15(d, root))))
        d = copy.deepcopy(base)
        d["a1"]["families"]["fam"]["strikes"] = 2
        d["a1"]["frozen"] = []
        d["completion_plan"]["tranches"]["T2"]["receipt"] = _measurement_receipt(root, "T2")
        res.append(("V-A1-C15-two-strikes-unfrozen-fails", bool(c15(d, root))))
        d["a1"]["frozen"] = ["T2"]
        res.append(("V-A1-C15-two-strikes-frozen-passes", not c15(d, root)))
        d = copy.deepcopy(base)
        d["a1"]["families"]["fam"]["strikes"] = None
        res.append(("V-A1-C15-unknown-strikes-fails", bool(c15(d, root))))
        for tag, spent, want in (("under-cap-passes", 50, True), ("at-cap-passes", 100, True),
                                 ("over-cap-fails", 101, False), ("null-fails", None, False)):
            d = copy.deepcopy(base)
            d["a1"]["spent"] = spent
            res.append((f"V-A1-C16-{tag}", (not c16_fn(d)) == want))
        d = copy.deepcopy(base)
        d.pop("a1")
        res.append(("V-A1-C16-absent-fails", bool(c16_fn(d))))
    return res


def mutant_null_as_zero_goes_red() -> bool:
    """Load a copy of this file with C16 treating null spend as 0; True when its selftest goes red."""
    src = Path(__file__).read_text(encoding="utf-8").splitlines(keepends=True)
    hits = [i for i, l in enumerate(src) if l.rstrip().endswith("# MUT-NULL") and l.strip().startswith("if ")]
    if len(hits) != 1:
        return False
    i = hits[0]
    ind = src[i][: len(src[i]) - len(src[i].lstrip())]
    src[i] = ind + "spent = 0 if spent is None else spent\n" + ind + "if False:\n"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "test_ce_a1_mut.py"
        p.write_text("".join(src), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("test_ce_a1_mut", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return not all(ok for _, ok in m.selftest_cases(m.c16))


def selftest() -> int:
    for tag, ok in selftest_cases():
        (_ok if ok else _fail)(tag)
    red = mutant_null_as_zero_goes_red()
    (_ok if red else _fail)("V-A1-MUT-null-as-zero", "killed" if red else "SURVIVED")
    print(f"CE_A1_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


def obligation(oid: str) -> int:
    try:
        led = json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{oid} ledger unreadable: {exc}")
        return 1
    if oid not in ("C15", "C16"):
        print(f"unknown obligation {oid!r}")
        return 1
    out = c15(led, REPO) if oid == "C15" else c16(led)
    for x in out:
        print(x)
    print(f"{oid}={'FAIL' if out else 'PASS'}")
    return 1 if out else 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--obligation":
        sys.exit(obligation(sys.argv[2]))
    if len(sys.argv) == 1:
        sys.exit(selftest())
    print("usage: test_ce_a1.py [--obligation C15|C16]")
    sys.exit(2)
