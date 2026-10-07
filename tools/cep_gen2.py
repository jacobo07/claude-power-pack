"""Cognitive Economy generation 2 (TOK-18 v2) verifier.

Reached through `python tools/test_cognitive_economy_program.py --generation 2 --final|--status|--selftest`.
Generation 1's ledger and gate are not read or changed here.

A work unit is closed only by a terminal from the generation-1 vocabulary plus evidence files that exist and
are non-empty. IMPLEMENTED_AND_VERIFIED also needs a command that produced the evidence. A saving labelled
realized needs its measuring command and its displacement. Spend over the authorization boundary needs an
Owner extension. A Tier-3 unit cannot be IMPLEMENTED before its not_before instant.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER_REL = "vault/programs/cognitive-economy/gen2/ledger.json"
TERMINALS = {
    "IMPLEMENTED_AND_VERIFIED", "MERGED_INTO_EXISTING_OWNER",
    "FALSIFIED_OR_REJECTED_BY_EVIDENCE", "DEFERRED_STRONGER_OWNER",
    "AUTHORIZATION_BOUND", "EXTERNAL_BLOCKED", "RESEARCH_INSUFFICIENT_EVIDENCE",
    "DEFERRED_BY_OWNER_QUOTA",
}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def check(led: dict, root: Path, now: dt.datetime | None = None) -> list:
    now = now or _now()
    fails = []
    wus = led.get("work_units") or {}
    if not wus:
        fails.append("ledger has no work units")
    for wid, wu in wus.items():
        term = wu.get("terminal")
        if not term:
            fails.append(f"{wid} open: no terminal")
            continue
        if term not in TERMINALS:
            fails.append(f"{wid} unknown terminal {term!r}")
        ev = wu.get("evidence") or []
        if not ev:
            fails.append(f"{wid} {term} without evidence")
        for e in ev:
            p = root / e.get("path", "")
            if not e.get("path") or not p.is_file() or p.stat().st_size == 0:
                fails.append(f"{wid} evidence missing or empty: {e.get('path')!r}")
        if term == "IMPLEMENTED_AND_VERIFIED" and not any(e.get("command") for e in ev):
            fails.append(f"{wid} IMPLEMENTED_AND_VERIFIED without the command that verified it")
        nb = wu.get("not_before")
        if nb and term == "IMPLEMENTED_AND_VERIFIED" and now < dt.datetime.fromisoformat(nb.replace("Z", "+00:00")):
            fails.append(f"{wid} IMPLEMENTED before its not_before {nb}")
        s = wu.get("saving")
        if s and s.get("label") == "realized" and not (s.get("measured_by") and "displacement" in s):
            fails.append(f"{wid} realized saving without measuring command and displacement")
        if wu.get("experiment"):
            fails.extend(check_receipt(wid, wu.get("receipt"), root))
    b = led.get("budget_tokens") or {}
    # A budget whose unit can be read two ways is not a gate (processed vs weighted differed ~6x in this estate).
    if b and b.get("unit") not in BUDGET_UNITS:
        fails.append(f"budget_tokens unit {b.get('unit')!r} is not one of {sorted(BUDGET_UNITS)}")
    spent, cap = b.get("spent_measured"), b.get("authorization_boundary")
    if spent is not None and cap is not None and spent > cap and not b.get("owner_extension"):
        fails.append(f"spend {spent:,} over boundary {cap:,} without an Owner extension")
    fails.extend(check_obligations(led, root)[1])
    return fails


# Scope conservation (D3, optional). ledger.obligations_declared (bool) + ledger.obligations [{id, source, terminal, evidence|execution}].
# Absent / false / null -> UNASSESSED (never PASS by vacuity, never FAIL). True -> every obligation needs a valid terminal and
# an execution mapping or evidence: EXECUTE needs `execution`; SATISFIED needs `evidence`; the rest need either.
OBL_TERMINALS = {"SATISFIED", "EXECUTE", "REUSE", "MERGED", "OWNED_ELSEWHERE", "CONDITIONAL", "SUPERSEDED", "OWNER_REMOVED"}


def check_obligations(led: dict, root: Path) -> tuple:
    """Return (status, fails); status is UNASSESSED, PASS or FAIL."""
    decl = led.get("obligations_declared")
    if decl is None or decl is False:
        return "UNASSESSED", []
    if decl is not True:
        return "FAIL", [f"obligations_declared must be a bool, got {decl!r}"]
    obs = led.get("obligations")
    if not isinstance(obs, list) or not obs:
        return "FAIL", ["obligations_declared is true but the obligations list is empty or missing (a vacuous pass)"]
    fails, ids = [], set()
    for k, o in enumerate(obs):
        if not isinstance(o, dict):
            fails.append(f"obligation #{k} is not an object")
            continue
        oid = o.get("id")
        tag = f"obligation {oid!r}" if oid else f"obligation #{k}"
        if not oid:
            fails.append(f"{tag} has no id")
        elif oid in ids:
            fails.append(f"{tag} duplicate id")
        ids.add(oid)
        if not o.get("source"):
            fails.append(f"{tag} has no source")
        term = o.get("terminal")
        if not term:
            fails.append(f"{tag} open: no terminal")
        elif term not in OBL_TERMINALS:
            fails.append(f"{tag} unknown terminal {term!r}")
        ev, ex = o.get("evidence") or [], o.get("execution")
        has_ex = bool(ex)
        if not isinstance(ev, list):
            fails.append(f"{tag} evidence must be a list")
            ev = []
        for e in ev:
            p = root / (e.get("path", "") if isinstance(e, dict) else "")
            if not isinstance(e, dict) or not e.get("path") or not p.is_file() or p.stat().st_size == 0:
                fails.append(f"{tag} evidence missing or empty: {e.get('path') if isinstance(e, dict) else e!r}")
        if not ev and not has_ex:
            fails.append(f"{tag} has neither an execution mapping nor evidence")
        elif term == "EXECUTE" and not has_ex:
            fails.append(f"{tag} EXECUTE without an execution mapping")
        elif term == "SATISFIED" and not ev:
            fails.append(f"{tag} SATISFIED without evidence")
    return ("FAIL" if fails else "PASS"), fails


# Experiment receipt (B1, post-E1 plan Phase 1). A work unit with `experiment: true` and a terminal is a CLOSED experiment;
# it needs `receipt`, a path to a JSON receipt. The receipt states cost, measured saving, forecast, payback, and the estimates
# it supersedes. Every derived number is recomputed here, so a receipt cannot carry arithmetic its own inputs contradict.
PAYBACK_STATES = {"PAID_BACK", "NOT_YET", "UNKNOWN"}


def _pos_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def check_receipt(wid: str, rel, root: Path) -> list:
    if not rel:
        return [f"{wid} closed experiment without a receipt"]
    p = root / rel
    try:
        r = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{wid} receipt unreadable {rel!r}: {exc}"]
    if not isinstance(r, dict):
        return [f"{wid} receipt {rel!r} is not an object"]
    f = []
    if r.get("work_unit") != wid:
        f.append(f"{wid} receipt names work unit {r.get('work_unit')!r}")
    cost, sav, fc, pb = (r.get(k) if isinstance(r.get(k), dict) else {} for k in ("cost", "saving", "forecast", "payback"))
    if cost.get("unit") not in BUDGET_UNITS or not _pos_int(cost.get("value")):
        f.append(f"{wid} receipt cost needs unit 'processed' and a positive integer value")
    per = sav.get("per_call")
    if not _pos_int(per) or not sav.get("measured_by"):
        f.append(f"{wid} receipt saving needs a positive integer per_call and the command that measured it")
    if sav.get("label") not in {"realized", "upper_bound", "unknown"}:
        f.append(f"{wid} receipt saving label {sav.get('label')!r} is not realized/upper_bound/unknown")
    for e in [sav.get("evidence")] + list(r.get("evidence") or []):
        q = root / (e or "")
        if not e or not q.is_file() or q.stat().st_size == 0:
            f.append(f"{wid} receipt evidence missing or empty: {e!r}")
    if not r.get("evidence"):
        f.append(f"{wid} receipt lists no evidence")
    if not isinstance(r.get("supersedes"), list):
        f.append(f"{wid} receipt supersedes must be a list (empty when nothing was forecast)")
    if f:
        return f
    fv = fc.get("per_call")
    if fv is not None:
        if not _pos_int(fv) or not fc.get("derivation"):
            f.append(f"{wid} receipt forecast needs a positive integer per_call and its derivation")
        else:
            want = round(100.0 * (per - fv) / fv, 1)
            got = (r.get("calibration") or {}).get("error_pct")
            if not isinstance(got, (int, float)) or abs(got - want) > 0.1:
                f.append(f"{wid} receipt calibration error_pct {got!r} != {want} recomputed from forecast and saving")
    be = -(-cost["value"] // per)
    if pb.get("break_even_calls") != be:
        f.append(f"{wid} receipt break_even_calls {pb.get('break_even_calls')!r} != ceil(cost/per_call) = {be}")
    if not pb.get("activated_at") or not pb.get("coverage"):
        f.append(f"{wid} receipt payback needs activated_at and coverage")
    obs, state = pb.get("calls_observed"), pb.get("state")
    want_state = "UNKNOWN" if obs is None else ("PAID_BACK" if isinstance(obs, int) and obs >= be else "NOT_YET")
    if state not in PAYBACK_STATES or state != want_state:
        f.append(f"{wid} receipt payback state {state!r} != {want_state} for calls_observed={obs!r}")
    return f


# processed = input + cache_write + cache_read + output, deduplicated by message id.
BUDGET_UNITS = {"processed"}


RECEIPT_FIXTURE = {"work_unit": "C", "cost": {"unit": "processed", "value": 1000},
                   "saving": {"per_call": 30, "label": "upper_bound", "measured_by": "x", "evidence": "ev.md"},
                   "forecast": {"per_call": 40, "derivation": "bytes x tokens/byte"},
                   "calibration": {"error_pct": -25.0},
                   "payback": {"activated_at": "2026-01-01T00:00:00Z", "coverage": "fixture",
                               "break_even_calls": 34, "calls_observed": 34, "state": "PAID_BACK"},
                   "supersedes": [], "evidence": ["ev.md"]}


def _write_receipt(root: Path, mutate=None) -> None:
    r = copy.deepcopy(RECEIPT_FIXTURE)
    if mutate:
        mutate(r)
    (root / "receipt.json").write_text(json.dumps(r), encoding="utf-8")


def _fixture(root: Path) -> dict:
    (root / "ev.md").write_text("evidence\n", encoding="utf-8")
    _write_receipt(root)
    return {"budget_tokens": {"unit": "processed", "authorization_boundary": 100, "spent_measured": 10},
            "work_units": {
                "A": {"terminal": "IMPLEMENTED_AND_VERIFIED", "evidence": [{"path": "ev.md", "command": "x"}]},
                "B": {"terminal": "MERGED_INTO_EXISTING_OWNER", "evidence": [{"path": "ev.md"}],
                      "not_before": "2999-01-01T00:00:00Z"},
                "C": {"terminal": "IMPLEMENTED_AND_VERIFIED", "experiment": True, "receipt": "receipt.json",
                      "evidence": [{"path": "ev.md", "command": "x"}]}}}


# Each rewrites the fixture receipt on disk; the ledger dict is left unchanged.
RECEIPT_MUTANTS = {
    "receipt-wrong-break-even": lambda r: r["payback"].update(break_even_calls=33),
    "receipt-paid-back-too-early": lambda r: r["payback"].update(calls_observed=33),
    "receipt-unknown-claimed-paid": lambda r: r["payback"].update(calls_observed=None),
    "receipt-calibration-drift": lambda r: r["calibration"].update(error_pct=-20.0),
    "receipt-forecast-without-derivation": lambda r: r["forecast"].pop("derivation"),
    "receipt-weighted-cost": lambda r: r["cost"].update(unit="weighted"),
    "receipt-saving-without-command": lambda r: r["saving"].pop("measured_by"),
    "receipt-missing-evidence": lambda r: r.update(evidence=["nope.md"]),
    "receipt-other-unit": lambda r: r.update(work_unit="A"),
    "receipt-no-supersedes": lambda r: r.pop("supersedes"),
}


MUTANTS = {
    "experiment-without-receipt": lambda d: d["work_units"]["C"].pop("receipt"),
    "experiment-receipt-unreadable": lambda d: d["work_units"]["C"].update(receipt="nope.json"),
    "open-unit": lambda d: d["work_units"]["A"].update(terminal=None),
    "unknown-terminal": lambda d: d["work_units"]["A"].update(terminal="DONE"),
    "no-evidence": lambda d: d["work_units"]["B"].update(evidence=[]),
    "missing-evidence-file": lambda d: d["work_units"]["B"].update(evidence=[{"path": "nope.md"}]),
    "implemented-without-command": lambda d: d["work_units"]["A"].update(evidence=[{"path": "ev.md"}]),
    "premature-tier3": lambda d: d["work_units"]["B"].update(terminal="IMPLEMENTED_AND_VERIFIED",
                                                            evidence=[{"path": "ev.md", "command": "x"}]),
    "realized-without-displacement": lambda d: d["work_units"]["A"].update(
        saving={"label": "realized", "measured_by": "cmd"}),
    "over-budget": lambda d: d["budget_tokens"].update(spent_measured=101),
    "untyped-budget": lambda d: d["budget_tokens"].pop("unit"),
    "weighted-budget": lambda d: d["budget_tokens"].update(unit="weighted"),
    "empty-ledger": lambda d: d.update(work_units={}),
}


def selftest(verbose=True) -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = _fixture(root)
        clean = check(base, root)
        ok &= not clean
        if verbose:
            print(f"  {'ok' if not clean else 'FAIL'}   V-CEP2-CLEAN (positive control green) {clean or ''}")
        for name, mutate in MUTANTS.items():
            d = copy.deepcopy(base)
            mutate(d)
            killed = bool(check(d, root))
            ok &= killed
            if verbose:
                print(f"  {'ok' if killed else 'FAIL'}   V-CEP2-MUT-{name} {'killed' if killed else 'SURVIVED'}")
        for name, mutate in RECEIPT_MUTANTS.items():
            _write_receipt(root, mutate)
            killed = bool(check(copy.deepcopy(base), root))
            _write_receipt(root)
            ok &= killed
            if verbose:
                print(f"  {'ok' if killed else 'FAIL'}   V-CEP2-MUT-{name} {'killed' if killed else 'SURVIVED'}")
    return ok


def main(mode: str) -> int:
    if mode == "selftest":
        ok = selftest()
        print(f"CEP2_SELFTEST={'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    try:
        led = json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"CEP2_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
        return 2
    fails = check(led, REPO)
    if mode == "status":
        open_ = [w for w, u in led.get("work_units", {}).items() if not u.get("terminal")]
        print(json.dumps({"open": open_, "violations": fails}, indent=1, ensure_ascii=False))
        return 1 if fails else 0
    if not selftest(verbose=False):
        fails.insert(0, "S0 selftest failed: the verifier cannot be trusted")
    print(f"CEP2_OBLIGATIONS={check_obligations(led, REPO)[0]}")
    for x in fails:
        print("  FAIL", x)
    print(f"CEP2_VERDICT={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
    return 0 if not fails else 1


TRANCHE_DIR = "vault/programs/cognitive-economy/gen2/evidence/tranche"
TRANCHE_STATES = {"PASS", "FAIL", "WAITING", "BLOCKED", "BLOCKED_BY_OWNERSHIP", "UNDECIDED"}


def tranche(name: str, root: Path = REPO) -> int:
    """`--tranche <name>`: judge <name>-results.json (written by tools/tranche_driver.py). Existing modes untouched.
    Computed clauses: receipts, violations (owned ledger units only), spend. Extra clauses are printed as given;
    only PASS is green, so WAITING/BLOCKED/UNDECIDED keep the tranche red."""
    import re
    d = root / TRANCHE_DIR
    # re-run files <name><letter>-results.json: the latest verdict per step wins, but EVERY attempt's spend counts,
    # so a failed attempt can never drop out of the total by being superseded.
    files = [d / f"{name}-results.json"] + sorted(d.glob(f"{name}[a-z]-results.json"))
    try:
        rs = [json.loads(f.read_text(encoding="utf-8")) for f in files]
        man = json.loads((d / f"{name}-tranche.json").read_text(encoding="utf-8")) \
            if (d / f"{name}-tranche.json").is_file() else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"CEP2_TRANCHE=COULD_NOT_RUN results unreadable: {exc}")
        return 2
    r = {"steps": {}, "clauses": {}, "owned_units": [], "cap": man.get("cap", rs[0].get("cap", 4_500_000))}
    attempt_spends = []
    for x in rs:
        r["steps"].update(x.get("steps") or {})
        r["clauses"].update(x.get("clauses") or {})
        r["owned_units"] += [u for u in x.get("owned_units") or [] if u not in r["owned_units"]]
        attempt_spends += [s.get("spend") for s in (x.get("steps") or {}).values() if s.get("sid")]
    coord = man.get("coordinator")
    if coord:  # a model coordinator metered live from its transcript, minus its reading when the tranche began
        try:
            sys.path.insert(0, str(REPO / "tools"))
            from tranche_driver import spend as _spend
            now = _spend(coord["sid"])
            r["coordinator_spend"] = now - int(coord["baseline"]) if isinstance(now, int) else None
        except (ImportError, KeyError, TypeError, ValueError):
            r["coordinator_spend"] = None
    else:
        r["coordinator_spend"] = rs[0].get("coordinator_spend")
    steps = r["steps"]
    has = lambda s: bool(s.get("receipt")) and (root / s["receipt"]).is_file()
    for k, s in steps.items():
        print(f"STEP {k} {s.get('verdict')} receipt={has(s)}")
    cl = {}
    miss = [k for k, s in steps.items() if s.get("verdict") == "PASS" and not has(s)]
    cl["receipts"] = ("PASS" if steps and not miss else "FAIL", "missing:" + ",".join(miss) if miss else f"{len(steps)} steps")
    owned = r.get("owned_units") or []
    if not owned:
        cl["violations"] = ("UNDECIDED", "no owned ledger units declared")
    else:
        try:
            led = json.loads((root / LEDGER_REL).read_text(encoding="utf-8"))
            v = [x for x in check(led, root) if any(re.search(rf"\b{re.escape(u)}\b", x) for u in owned)]
            cl["violations"] = ("PASS" if not v else "FAIL", f"{len(v)} on {owned}")
        except (OSError, json.JSONDecodeError) as exc:
            cl["violations"] = ("FAIL", f"ledger unreadable: {exc}")
    nums = [r.get("coordinator_spend")] + attempt_spends
    cap = r["cap"]
    if any(not isinstance(n, int) for n in nums):
        cl["spend"] = ("FAIL", "unknown spend (unmeasured is never green)")
    else:
        cl["spend"] = ("PASS" if sum(nums) <= cap else "FAIL", f"total={sum(nums):,} cap={cap:,}")
    for k, c in (r.get("clauses") or {}).items():
        st, ev = c.get("status"), c.get("evidence") or ""
        if st not in TRANCHE_STATES or (st == "PASS" and not (ev and (root / ev).is_file())):
            st = "FAIL"
        cl[k] = (st, ev)
    for k, (st, ev) in cl.items():
        print(f"CLAUSE {k} {st} {ev}")
    green = sum(st == "PASS" for st, _ in cl.values())
    print(f"CEP2_TRANCHE={'PASS' if green == len(cl) else 'FAIL'} clauses={len(cl)} green={green}")
    return 0 if green == len(cl) else 1


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--tranche":
        sys.exit(tranche(sys.argv[2]))
    sys.exit(main(sys.argv[1].lstrip("-") if len(sys.argv) > 1 else "final"))
