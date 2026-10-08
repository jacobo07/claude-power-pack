"""V-ADMIT-EXPECTED-*: the expected-completion tiers of tools/route_admission.py (spec E1).

Canaries 1-3 replay T1 and T2 against the REAL calibrated floor table; canary 4 and the mutation drills
use hermetic floor tables / a temp copy of the module. Every drill asserts the mutation was applied
(a replace that matched nothing would leave the drill vacuously red-free)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import route_admission as ra  # noqa: E402

M = 1_000_000
T1_ACTUAL, T2_ACTUAL = 11_135_030, 4_090_547
passes = fails = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global passes, fails
    if ok:
        passes += 1
        print(f"PASS {name} {detail}".rstrip())
    else:
        fails += 1
        print(f"FAIL {name} {detail}".rstrip())


def route(calls: int, packet: int, target: int, warn: int, stop: int, profile: str = "top-level-worker") -> dict:
    return {"envelope": {"target": target, "warn": warn, "stop": stop},
            "workers": [{"name": "w", "profile": profile, "calls": calls, "packet": packet}]}


def table(**profiles) -> dict:
    return {"default_min_calls": 3, "profiles": {k: dict(v) for k, v in profiles.items()}}


def field(value, n=10, basis="measured:fixture"):
    return {"value": value, "n": n, "basis": basis, "provenance": "fixture"}


def scenario(mod) -> dict:
    """The four properties the drills attack, measured on whatever module `mod` is."""
    base = {"floor": 100_000, "write": True, "n": 9}
    lo = table(a={**base, "growth_per_call": field(1000), "calls_err": field(0.1)})
    hi = table(a={**base, "growth_per_call": field(5000), "calls_err": field(0.1)})
    r = route(20, 0, 5 * M, 6 * M, 9 * M, "a")
    e_lo, e_hi = mod.admit(r, lo)["forecast"]["expected"], mod.admit(r, hi)["forecast"]["expected"]
    no_g = table(a={**base, "calls_err": field(0.1)}, b={**base, "growth_per_call": field(1000), "calls_err": field(0.1)})
    unk = mod.admit(r, no_g)
    low = table(a={**base, "growth_per_call": field(5000, n=2), "calls_err": field(0.5, n=2)})
    # expected fits the target, safety (30 calls) exceeds stop: LOW must WATCH, an OK-confidence twin must refuse
    rl = route(20, 0, 3 * M, 3 * M, 4 * M, "a")
    ok_tbl = table(a={**base, "growth_per_call": field(5000), "calls_err": field(0.5)})
    fc = mod.admit(r, hi)["forecast"]
    return {"growth_matters": e_hi > e_lo,
            "unknown_g_escalates": unk["challenger"]["verdict"] == ra.ESCALATE if "challenger" in unk else False,
            "lower_bound_is_not_expected": fc["expected"] > fc["lower_bound"],
            "low_never_refuses": mod.admit(rl, low)["challenger"]["verdict"] == ra.WATCHED,
            "ok_confidence_refuses": mod.admit(rl, ok_tbl)["challenger"]["verdict"] == ra.ESCALATE}


def mutant(src: str, old: str, new: str, tag: str):
    assert old in src, f"mutation {tag} matched nothing"
    path = Path(tempfile.mkdtemp(prefix="admit_mut_")) / f"ra_mut_{tag}.py"
    path.write_text(src.replace(old, new, 1), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"ra_mut_{tag}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    real = ra.load_floors(HERE.parent / "vault" / "config" / "route-floors.json")
    top = real["profiles"][ra.TOP_LEVEL]
    check("V-ADMIT-EXPECTED-CALIBRATED", all(k in top for k in ("growth_per_call", "calls_err"))
          and all(top[k].get("provenance") and top[k].get("n") for k in ("growth_per_call", "calls_err")),
          f"g={top['growth_per_call']['value']} n={top['growth_per_call']['n']} "
          f"calls_err={top['calls_err']['value']} n={top['calls_err']['n']}")
    check("V-ADMIT-EXPECTED-NO-SAMPLE-NO-FIELD", "growth_per_call" not in real["profiles"]["slim-t2"]
          and "growth_per_call" not in real["profiles"]["Explore"], "profiles with no samples carry no g")

    # canary 1: T1 replay -- 48 planned calls, actual 65 calls / 11,135,030
    t1 = ra.admit(route(48, 1100, 8 * M, int(9.6 * M), 16 * M), real)
    fc = t1["forecast"]
    err = (fc["safety"] - T1_ACTUAL) / T1_ACTUAL
    check("V-ADMIT-EXPECTED-C1-CHAMPION", t1["champion"]["verdict"] == ra.ADMISSIBLE and t1["champion"]["need_with_margin"] == 6_447_456,
          f"champion {t1['champion']['verdict']} at {t1['champion']['need_with_margin']:,}")
    check("V-ADMIT-EXPECTED-C1-CHALLENGER-WATCHED", t1["challenger"]["verdict"] == ra.WATCHED, str(t1["challenger"]))
    check("V-ADMIT-EXPECTED-C1-SAFETY-WITHIN-15PCT", abs(err) <= 0.15,
          f"safety {fc['safety']:,} vs actual {T1_ACTUAL:,} = {err:+.1%}; expected {fc['expected']:,}")

    # canary 2: T2 replay -- 36 planned, 27 metered, actual 4,090,547. Stated, not tuned.
    t2 = ra.admit(route(36, 770, 5 * M, 5 * M, 10 * M), real)
    at27 = ra.admit(route(27, 770, 5 * M, 5 * M, 10 * M), real)["forecast"]["expected"]
    e36 = t2["forecast"]["expected"]
    check("V-ADMIT-EXPECTED-C2-REPORTED", isinstance(e36, int) and t2["challenger"]["verdict"] == ra.RECOMPILE,
          f"planned-36 expected {e36:,} vs actual {T2_ACTUAL:,} = {(e36 - T2_ACTUAL) / T2_ACTUAL:+.1%} "
          f"(call-count error); at the metered 27 calls expected {at27:,} = {(at27 - T2_ACTUAL) / T2_ACTUAL:+.1%} "
          f"(model error); challenger {t2['challenger']['verdict']}, cap {t2['max_calls_per_process']} calls")
    check("V-ADMIT-EXPECTED-C2-MODEL-ERROR-BOUNDED", abs(at27 - T2_ACTUAL) / T2_ACTUAL <= 0.15)

    # canary 3: lower bound labelled, present, and still refuses an impossible route
    imp = ra.admit(route(200, 1100, 8 * M, 8 * M, 16 * M), real)
    check("V-ADMIT-EXPECTED-C3-LOWER-BOUND-LABELLED", "lower_bound" in fc and "expected" in fc
          and fc["lower_bound"] == t1["need"] and fc["expected"] > fc["lower_bound"],
          f"lower_bound {fc['lower_bound']:,} < expected {fc['expected']:,}")
    check("V-ADMIT-EXPECTED-C3-IMPOSSIBLE-REFUSED", imp["challenger"]["verdict"] in (ra.RECOMPILE, ra.ESCALATE)
          and imp["forecast"]["lower_bound"] > 8 * M, f"{imp['challenger']['verdict']} lower {imp['forecast']['lower_bound']:,}")
    tiny = ra.admit(route(48, 1100, 200_000, 200_000, 400_000), real)
    check("V-ADMIT-EXPECTED-C3-UNHOLDABLE-ESCALATES", tiny["challenger"]["verdict"] == ra.ESCALATE, str(tiny["challenger"]["reasons"]))
    ctl = ra.admit(route(10, 1100, 8 * M, 8 * M, 16 * M), real)
    check("V-ADMIT-EXPECTED-C3-CONTROL-ADMITS", ctl["challenger"]["verdict"] == ra.ADMISSIBLE, str(ctl["challenger"]))

    # canary 4: same F, different g -> different expected AND different verdict; absent g -> ESCALATE
    base = {"floor": 100_000, "write": True, "n": 9}
    pair = table(calm={**base, "growth_per_call": field(1000), "calls_err": field(0.1)},
                 steep={**base, "growth_per_call": field(9000), "calls_err": field(0.1)})
    r4 = lambda p: route(25, 0, 3 * M, 4 * M, 8 * M, p)  # noqa: E731
    calm, steep = ra.admit(r4("calm"), pair), ra.admit(r4("steep"), pair)
    check("V-ADMIT-EXPECTED-C4-G-CHANGES-EXPECTED", calm["forecast"]["expected"] != steep["forecast"]["expected"]
          and calm["forecast"]["lower_bound"] == steep["forecast"]["lower_bound"],
          f"{calm['forecast']['expected']:,} vs {steep['forecast']['expected']:,}")
    check("V-ADMIT-EXPECTED-C4-G-CHANGES-VERDICT", calm["challenger"]["verdict"] != steep["challenger"]["verdict"],
          f"{calm['challenger']['verdict']} vs {steep['challenger']['verdict']}")
    nog = table(calm={**base, "growth_per_call": field(1000), "calls_err": field(0.1)}, bare=dict(base))
    nob = ra.admit(r4("bare"), nog)
    check("V-ADMIT-EXPECTED-C4-ABSENT-G-ESCALATES", nob["challenger"]["verdict"] == ra.ESCALATE
          and nob["forecast"]["expected"] is None and "absent is not zero" in nob["challenger"]["reasons"][0])
    noe = table(x={**base, "growth_per_call": field(1000)})
    check("V-ADMIT-EXPECTED-C4-ABSENT-CALLS-ERR-ESCALATES", ra.admit(r4("x"), noe)["challenger"]["verdict"] == ra.ESCALATE)
    leg = ra.admit(r4("calm"), table(calm=base))
    check("V-ADMIT-EXPECTED-LEGACY-TABLE-CHAMPION-STANDS", leg["forecast"]["available"] is False
          and "challenger" not in leg and leg["verdict"] == leg["champion"]["verdict"])

    # confidence = weakest input; LOW (n < 5) can only WATCH
    lowt = table(a={**base, "growth_per_call": field(1000, n=7), "calls_err": field(0.1, n=2, basis="estimated")})
    lc = ra.admit(route(20, 0, 5 * M, 6 * M, 9 * M, "a"), lowt)["forecast"]
    check("V-ADMIT-EXPECTED-CONFIDENCE-WEAKEST", lc["confidence"] == {"level": "LOW", "n": 2} and lc["basis"] == "estimated", str(lc["confidence"]))

    # mutation drills: each must turn its own property red while the original has all green
    sc = scenario(ra)
    check("V-ADMIT-EXPECTED-DRILL-BASELINE-GREEN", all(sc.values()), str(sc))
    src = (HERE / "route_admission.py").read_text(encoding="utf-8")
    drills = [("growth", "growth_matters", "g * calls * (calls - 1) / 2", "0 * calls * (calls - 1) / 2"),
              ("unkg", "unknown_g_escalates", 'g, err = _calibrated(prof, "growth_per_call"), _calibrated(prof, "calls_err")',
               'g, err = (_calibrated(prof, "growth_per_call") or (0.0, 9, "measured")), _calibrated(prof, "calls_err")'),
              ("lbexp", "lower_bound_is_not_expected", "out.update(expected=expected,", "out.update(expected=lower,"),
              ("lowref", "low_never_refuses", "        if low:\n", "        if False:\n")]
    for tag, prop, old, new in drills:
        try:
            got = scenario(mutant(src, old, new, tag))[prop]
        except Exception as exc:  # a mutant that crashes is also detected, but say so
            got, tag = False, f"{tag}(crashed: {type(exc).__name__})"
        check(f"V-ADMIT-EXPECTED-DRILL-{tag.split('(')[0].upper()}-RED", got is False, f"{prop} -> {got}")

    # the kill switch of the old path and the CLI stay: the result still carries the champion's keys
    check("V-ADMIT-EXPECTED-KEYS-KEPT", all(k in t1 for k in ("need", "need_with_margin", "max_calls_single_worker", "route_sha256", "calls")),
          "need/need_with_margin/max_calls_single_worker kept; max_calls_per_process="
          f"{t1['max_calls_per_process']}")

    print(f"ADMIT_EXPECTED_PASS={passes}/{passes + fails}  threshold=all")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
