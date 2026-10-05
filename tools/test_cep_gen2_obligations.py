"""D3 tests: obligations section of tools/cep_gen2.py (scope conservation). Run: python tools/test_cep_gen2_obligations.py
Green cases, red cases, and mutants of the checker that the case table must catch (vacuous pass, missing terminal accepted,
unassessed turned into a verdict)."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cep_gen2 as cep  # noqa: E402

OK = {"id": "O1", "source": "MISSION.md#3", "terminal": "SATISFIED", "evidence": [{"path": "ev.md"}]}


def obl(**kw):
    d = copy.deepcopy(OK)
    for k, v in kw.items():
        if v is None:
            d.pop(k, None)
        else:
            d[k] = v
    return d


def led(decl=True, obs=None):
    d = {"budget_tokens": {"unit": "processed", "authorization_boundary": 100, "spent_measured": 10},
         "work_units": {"A": {"terminal": "IMPLEMENTED_AND_VERIFIED", "evidence": [{"path": "ev.md", "command": "x"}]}}}
    if decl is not ...:
        d["obligations_declared"] = decl
    if obs is not None:
        d["obligations"] = obs
    return d


def cases(root):
    """(name, ledger, expected_status). Expected FAIL cases must also add a failure to cep.check()."""
    all_terms = [obl(id=f"T{i}", terminal=t, evidence=[{"path": "ev.md"}], execution="W-x" if t == "EXECUTE" else None) for i, t in enumerate(sorted(cep.OBL_TERMINALS))]
    return [
        ("green-absent", led(decl=...), "UNASSESSED"),
        ("green-false", led(False, [obl(terminal=None)]), "UNASSESSED"),
        ("green-null", led(None, None), "UNASSESSED"),
        ("green-all-terminals", led(True, all_terms), "PASS"),
        ("green-execute-with-mapping-only", led(True, [obl(terminal="EXECUTE", evidence=None, execution="W5")]), "PASS"),
        ("red-declared-empty", led(True, []), "FAIL"),
        ("red-declared-missing-list", led(True, None), "FAIL"),
        ("red-missing-terminal", led(True, [obl(terminal=None)]), "FAIL"),
        ("red-unknown-terminal", led(True, [obl(terminal="DONE")]), "FAIL"),
        ("red-no-id", led(True, [obl(id=None)]), "FAIL"),
        ("red-duplicate-id", led(True, [obl(), obl()]), "FAIL"),
        ("red-no-source", led(True, [obl(source=None)]), "FAIL"),
        ("red-no-evidence-no-execution", led(True, [obl(evidence=None)]), "FAIL"),
        ("red-execute-without-mapping", led(True, [obl(terminal="EXECUTE")]), "FAIL"),
        ("red-satisfied-with-only-mapping", led(True, [obl(evidence=None, execution="W5")]), "FAIL"),
        ("red-evidence-file-missing", led(True, [obl(evidence=[{"path": "nope.md"}])]), "FAIL"),
        ("red-declared-not-bool", led("yes", [obl()]), "FAIL"),
    ]


def run(fn, root):
    """Names of cases where fn disagrees with the expected status."""
    bad = []
    for name, l, want in cases(root):
        try:
            got = fn(l, root)[0]
        except Exception as exc:  # a checker that raises is a failed case, not a crash of the harness
            got = f"RAISED {exc!r}"
        if got != want:
            bad.append(f"{name}: want {want} got {got}")
    return bad


def mutants(orig):
    def vacuous(l, root):
        if l.get("obligations_declared") is True and not l.get("obligations"):
            return "PASS", []
        return orig(l, root)

    def missing_terminal_ok(l, root):
        l = copy.deepcopy(l)
        for o in l.get("obligations") or []:
            if isinstance(o, dict) and not o.get("terminal"):
                o["terminal"] = "SATISFIED"
        return orig(l, root)

    def unknown_terminal_ok(l, root):
        l = copy.deepcopy(l)
        for o in l.get("obligations") or []:
            if isinstance(o, dict) and o.get("terminal") not in cep.OBL_TERMINALS and o.get("terminal"):
                o["terminal"] = "SATISFIED"
        return orig(l, root)

    def absent_is_pass(l, root):
        st, f = orig(l, root)
        return ("PASS", []) if st == "UNASSESSED" else (st, f)

    def absent_is_fail(l, root):
        st, f = orig(l, root)
        return ("FAIL", ["absent"]) if st == "UNASSESSED" else (st, f)

    def no_evidence_ok(l, root):
        l = copy.deepcopy(l)
        for o in l.get("obligations") or []:
            if isinstance(o, dict) and not o.get("evidence") and not o.get("execution"):
                o["execution"] = "x"
        return orig(l, root)

    return {"vacuous-pass": vacuous, "missing-terminal-accepted": missing_terminal_ok, "unknown-terminal-accepted": unknown_terminal_ok,
            "unassessed-becomes-pass": absent_is_pass, "unassessed-becomes-fail": absent_is_fail}


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ev.md").write_text("evidence\n", encoding="utf-8")
        bad = run(cep.check_obligations, root)
        ok &= not bad
        print(f"  {'ok' if not bad else 'FAIL'}   V-OBL-CASES ({len(cases(root))} cases) {bad or ''}")
        for name, fn in mutants(cep.check_obligations).items():
            killed = bool(run(fn, root))
            ok &= killed
            print(f"  {'ok' if killed else 'FAIL'}   V-OBL-MUT-{name} {'killed' if killed else 'SURVIVED'}")
        # integration: check() adds failures only when declared and invalid; absent leaves existing behaviour byte-identical
        base = led(decl=...)
        same = cep.check(base, root) == []
        ok &= same
        print(f"  {'ok' if same else 'FAIL'}   V-OBL-INTEGRATION-absent-no-change")
        cf = led(True, [obl(terminal=None)])
        added = any("obligation" in x for x in cep.check(cf, root))
        ok &= added
        print(f"  {'ok' if added else 'FAIL'}   V-OBL-INTEGRATION-declared-invalid-fails-check")
        cg = led(True, [obl()])
        clean = cep.check(cg, root) == []
        ok &= clean
        print(f"  {'ok' if clean else 'FAIL'}   V-OBL-INTEGRATION-declared-valid-passes-check")
    live = json.loads((cep.REPO / cep.LEDGER_REL).read_text(encoding="utf-8"))
    st = cep.check_obligations(live, cep.REPO)[0]
    live_ok = live.get("obligations_declared") is not True and st == "UNASSESSED"
    ok &= live_ok
    print(f"  {'ok' if live_ok else 'FAIL'}   V-OBL-LIVE-LEDGER-unassessed (status {st}, declared={live.get('obligations_declared')!r})")
    print(f"OBL_TEST={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
