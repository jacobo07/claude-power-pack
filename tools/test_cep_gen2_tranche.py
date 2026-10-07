"""V-CEP2-TRANCHE-* gates for `cep_gen2.py --tranche`: a green control and every red branch."""
import contextlib, copy, io, json, re, sys, tempfile, types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cep_gen2 as cg  # noqa: E402

passes = fails = 0


def run(root, results, ledger=None):
    d = root / cg.TRANCHE_DIR
    d.mkdir(parents=True, exist_ok=True)
    f = d / "t-results.json"
    f.unlink(missing_ok=True)
    if results is not None:
        f.write_text(json.dumps(results), encoding="utf-8")
    if ledger is not None:
        (root / cg.LEDGER_REL).parent.mkdir(parents=True, exist_ok=True)
        (root / cg.LEDGER_REL).write_text(json.dumps(ledger), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cg.tranche("t", root)
    return rc, buf.getvalue()


def gate(name, ok, ev=""):
    global passes, fails
    passes += bool(ok); fails += not ok
    print(f"  {'ok' if ok else 'FAIL'}   {name} {ev if not ok else ''}")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    base = cg._fixture(root)
    (root / "r.md").write_text("receipt\n", encoding="utf-8")
    good = {"steps": {"S1": {"verdict": "PASS", "receipt": "r.md", "sid": "x", "spend": 100}},
            "coordinator_spend": 100, "cap": 1000, "owned_units": ["A"],
            "clauses": {"c1": {"status": "PASS", "evidence": "r.md"}}}
    rc, out = run(root, good, base); gate("V-CEP2-TRANCHE-GREEN-CONTROL", rc == 0 and "CEP2_TRANCHE=PASS" in out, out)
    r = copy.deepcopy(good); r["steps"]["S1"]["receipt"] = "nope.md"
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-MISSING-RECEIPT", rc == 1 and "CLAUSE receipts FAIL" in out, out)
    r = copy.deepcopy(good); r["steps"]["S1"]["spend"] = 2000
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-OVER-CAP", rc == 1 and "CLAUSE spend FAIL" in out, out)
    r = copy.deepcopy(good); r["steps"]["S1"]["spend"] = None
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-UNKNOWN-SPEND", rc == 1 and "unknown spend" in out, out)
    r = copy.deepcopy(good); r["clauses"]["c1"]["status"] = "WAITING"
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-WAITING-NOT-GREEN", rc == 1 and "CLAUSE c1 WAITING" in out, out)
    r = copy.deepcopy(good); r["clauses"]["c1"]["evidence"] = "nope.md"
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-PASS-WITHOUT-EVIDENCE", rc == 1 and "CLAUSE c1 FAIL" in out, out)
    r = copy.deepcopy(good); r["owned_units"] = []
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-NO-OWNED-UNDECIDED", rc == 1 and "violations UNDECIDED" in out, out)
    bad = copy.deepcopy(base); cg.MUTANTS["open-unit"](bad)
    rc, out = run(root, good, bad); gate("V-CEP2-TRANCHE-OWNED-VIOLATION", rc == 1 and "CLAUSE violations FAIL" in out, out)
    rc, out = run(root, None); gate("V-CEP2-TRANCHE-MISSING-FILE", rc == 2 and "COULD_NOT_RUN" in out, out)
    # re-run file: S1 failed (spend 300) then passed on re-run (spend 200). Verdict follows the re-run; spend counts both.
    d = root / cg.TRANCHE_DIR
    first = copy.deepcopy(good); first["steps"]["S1"].update(verdict="FAIL", spend=300)
    rerun = {"steps": {"S1": {"verdict": "PASS", "receipt": "r.md", "sid": "y", "spend": 200}}, "coordinator_spend": 0}
    (d / "tb-results.json").write_text(json.dumps(rerun), encoding="utf-8")
    rc, out = run(root, first, base)
    gate("V-CEP2-TRANCHE-RERUN-SUPERSEDES-VERDICT", rc == 0 and "STEP S1 PASS" in out, out)
    gate("V-CEP2-TRANCHE-RERUN-KEEPS-FAILED-SPEND", "total=600" in out, out)  # coord 100 + 300 + 200
    big = copy.deepcopy(rerun); big["steps"]["S1"]["spend"] = 700
    (d / "tb-results.json").write_text(json.dumps(big), encoding="utf-8")
    rc, out = run(root, first, base)
    gate("V-CEP2-TRANCHE-RERUN-OVER-CAP", rc == 1 and "CLAUSE spend FAIL" in out, out)  # 100+300+700 > 1000
    # manifest: cap comes from it; a coordinator whose transcript cannot be found is unknown, never 0.
    (d / "tb-results.json").write_text(json.dumps(rerun), encoding="utf-8")
    (d / "t-tranche.json").write_text(json.dumps({"cap": 550}), encoding="utf-8")
    rc, out = run(root, first, base)
    gate("V-CEP2-TRANCHE-MANIFEST-CAP", rc == 1 and "cap=550" in out, out)
    (d / "t-tranche.json").write_text(json.dumps({"cap": 10_000, "coordinator": {"sid": "no-such-session",
                                                                                 "baseline": 0}}), encoding="utf-8")
    rc, out = run(root, first, base)
    gate("V-CEP2-TRANCHE-MANIFEST-COORD-UNKNOWN", rc == 1 and "unknown spend" in out, out)
    (d / "t-tranche.json").unlink(); (d / "tb-results.json").unlink()
    # E1: NOT_APPLICABLE only for an explicit owned_units: [] WITH a reason; a missing key stays UNDECIDED.
    na = copy.deepcopy(good); na["owned_units"] = []; na["owned_units_reason"] = "tranche touches no ledger unit"
    rc, out = run(root, na)
    gate("V-CEP2-TRANCHE-EXPLICIT-EMPTY-NA", rc == 0 and "CLAUSE violations NOT_APPLICABLE" in out
         and "CEP2_TRANCHE=PASS" in out, out)
    r = copy.deepcopy(na); r.pop("owned_units_reason")
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-EMPTY-NO-REASON-UNDECIDED", rc == 1 and "violations UNDECIDED" in out, out)
    r = copy.deepcopy(na); r.pop("owned_units")
    rc, out = run(root, r)
    gate("V-CEP2-TRANCHE-MISSING-KEY-WITH-REASON-UNDECIDED", rc == 1 and "violations UNDECIDED" in out, out)
    r = copy.deepcopy(good); r.pop("owned_units")
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-MISSING-KEY-UNDECIDED", rc == 1 and "violations UNDECIDED" in out, out)
    (d / "t-tranche.json").write_text(json.dumps({"cap": 1000, "owned_units": [], "owned_units_reason": "none"}),
                                      encoding="utf-8")
    rc, out = run(root, r)
    gate("V-CEP2-TRANCHE-MANIFEST-EXPLICIT-EMPTY-NA", rc == 0 and "violations NOT_APPLICABLE" in out, out)
    (d / "t-tranche.json").unlink()
    r = copy.deepcopy(good); r["clauses"]["c1"]["status"] = "NOT_APPLICABLE"
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-EXTRA-NA-GREEN", rc == 0 and "CLAUSE c1 NOT_APPLICABLE" in out, out)
    r["clauses"]["c1"]["evidence"] = "nope.md"
    rc, out = run(root, r); gate("V-CEP2-TRANCHE-EXTRA-NA-WITHOUT-EVIDENCE", rc == 1 and "CLAUSE c1 FAIL" in out, out)
    # E1: a frozen coordinator `final` is reproducible while the (fake) transcript keeps growing; live says so.
    calls = {"n": 0}

    def fake_spend(sid):
        calls["n"] += 1
        return 1000 * calls["n"]

    def tot(o):
        m = re.search(r"total=([\d,]+)", o)
        return m.group(1) if m else None

    saved = sys.modules.get("tranche_driver")
    sys.modules["tranche_driver"] = types.SimpleNamespace(spend=fake_spend)
    try:
        (d / "t-tranche.json").write_text(json.dumps({"cap": 10 ** 9, "coordinator": {"sid": "fake", "baseline": 0}}),
                                          encoding="utf-8")
        _, o1 = run(root, good, base); _, o2 = run(root, good, base)
        gate("V-CEP2-TRANCHE-LIVE-COORD-GROWS-AND-SAYS-SO", bool(tot(o1)) and tot(o1) != tot(o2)
             and "coordinator=LIVE (not reproducible)" in o1, o1 + o2)
        (d / "t-tranche.json").write_text(json.dumps({"cap": 10 ** 9, "coordinator": {"sid": "fake", "baseline": 100,
                                                                                     "final": 500}}), encoding="utf-8")
        n0 = calls["n"]
        rc1, o1 = run(root, good, base); rc2, o2 = run(root, good, base)
        gate("V-CEP2-TRANCHE-FROZEN-COORD-REPRODUCIBLE", rc1 == rc2 == 0 and tot(o1) == tot(o2) == "500"
             and "coordinator=FROZEN" in o1 and calls["n"] == n0, o1 + o2)
    finally:
        if saved is None:
            sys.modules.pop("tranche_driver", None)
        else:
            sys.modules["tranche_driver"] = saved
        (d / "t-tranche.json").unlink(missing_ok=True)

print(f"CEP2_TRANCHE_TEST_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
