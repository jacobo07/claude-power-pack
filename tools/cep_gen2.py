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


# processed = input + cache_write + cache_read + output, deduplicated by message id.
BUDGET_UNITS = {"processed"}


def _fixture(root: Path) -> dict:
    (root / "ev.md").write_text("evidence\n", encoding="utf-8")
    return {"budget_tokens": {"unit": "processed", "authorization_boundary": 100, "spent_measured": 10},
            "work_units": {
                "A": {"terminal": "IMPLEMENTED_AND_VERIFIED", "evidence": [{"path": "ev.md", "command": "x"}]},
                "B": {"terminal": "MERGED_INTO_EXISTING_OWNER", "evidence": [{"path": "ev.md"}],
                      "not_before": "2999-01-01T00:00:00Z"}}}


MUTANTS = {
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "final"))
