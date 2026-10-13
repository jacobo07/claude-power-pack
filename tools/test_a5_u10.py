#!/usr/bin/env python3
"""A5 U10 tests (AAA, hermetic, read-only on the repo)."""
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(W / "tools"))
import a5_u10_budget as b  # noqa: E402  (import does not re-run the compile; main is guarded)

MD = (b.A / "DWS-BUDGET-FINAL.md").read_text()
HIST = 6_501_959_646
KS = [k / 10 for k in range(1, 10)]


def refuse_hist_multiple(figure: float) -> None:
    """Checker: a 'new expected' equal to HIST x k (k = 0.1..0.9) is a percentage, not a compile."""
    for k in KS:
        if abs(figure - HIST * k) <= 1.0:
            raise ValueError(f"PERCENTAGE_OF_HISTORICAL k={k}")


def unsourced_rows(md: str) -> list[str]:
    return [ln for ln in md.splitlines()
            if (ln.startswith("- ") or ln.startswith("|")) and re.search(r"\d", ln) and "[src:" not in ln
            and "src:" not in ln]


def raises(fn, *a) -> bool:
    try:
        fn(*a)
    except ValueError:
        return True
    return False


def t_sections():
    assert b.sections_ok(MD) == []
    heads = re.findall(r"^## (.+)$", MD, flags=re.M)
    assert [h for h in heads if h in b.SECTIONS] == b.SECTIONS


def t_sections_mutant():
    swapped = MD.replace("## Confidence", "## Zzz")
    assert b.sections_ok(swapped) == ["Confidence"]


def t_decision():
    assert MD.rstrip("\n").splitlines()[-4:] == b.DECISION


def t_decision_mutant():
    assert (MD + "\nextra").rstrip("\n").splitlines()[-4:] != b.DECISION


def t_sources():
    assert unsourced_rows(MD) == []


def t_sources_mutant():
    assert unsourced_rows(MD + "\n- Total 12345 tokens\n") == ["- Total 12345 tokens"]


def t_not_historical():
    R = b.compile_all()
    assert R["scen"]["expected"]["HISTORICAL_PROFILE"] is False
    assert R["hist"]["HISTORICAL_PROFILE_FLAG"] == "HISTORICAL_PROFILE"
    assert R["hist"]["candidate"]["tokens"] == HIST


def t_doc_flag():
    assert "HISTORICAL_PROFILE = False" in MD


def t_mutant_refused():
    for k in KS:
        assert raises(refuse_hist_multiple, round(HIST * k)), k


def t_control_admits():
    R = b.compile_all()
    for s in ("lower", "expected", "p90", "ceiling"):
        refuse_hist_multiple(R["scen"][s]["total"])
    m = re.search(r"expected (\d[\d,]*) ", MD)
    assert m and int(m.group(1).replace(",", "")) == R["scen"]["expected"]["total"]


TESTS = [t_sections, t_sections_mutant, t_decision, t_decision_mutant, t_sources, t_sources_mutant,
         t_not_historical, t_doc_flag, t_mutant_refused, t_control_admits]
# compile_all() reads the GEX44 DWS checkout and a5/data/, neither of which is in the public repo.
NEEDS_COMPILE = {t_not_historical, t_control_admits}
COMPILE_INPUTS = [b.DWS / "config/dws-completion-matrix.jsonc", b.A / "data/calls.jsonl.gz",
                  b.A / "data/counterfactual.json"]

if __name__ == "__main__":
    missing = [str(p) for p in COMPILE_INPUTS if not p.exists()]
    ok = skipped = 0
    for t in TESTS:
        if t in NEEDS_COMPILE and missing:
            skipped += 1
            print("SKIP", t.__name__, "compile inputs absent:", missing[0])
            continue
        try:
            t()
            ok += 1
        except Exception as e:  # noqa: BLE001
            print("FAIL", t.__name__, repr(e))
    print(f"A5_U10_PASS={ok}/{len(TESTS) - skipped} SKIPPED={skipped}")
    sys.exit(0 if ok == len(TESTS) - skipped else 1)
