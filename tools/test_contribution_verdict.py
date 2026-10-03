#!/usr/bin/env python
"""test_contribution_verdict.py -- pillar E verdict gate (skill-capability, SC-E, decisions D-01/D-02).

    python3 tools/test_contribution_verdict.py                   # check (default mode)
    python3 tools/test_contribution_verdict.py --jsonl PATH      # verdict clauses on one rows file only
    python3 tools/test_contribution_verdict.py --jsonl P --regrade R   # same, with a regrade file
    python3 tools/test_contribution_verdict.py --write-evidence  # render the D-SESSIONS measurement file

What it reads: the committed paired delivery benchmark of the cognitive-resource-os P3 ablation
(results-delivery.jsonl, arms N0/R/P/C) joined by run_id with results-delivery-regrade.jsonl, and
the frozen D-SESSIONS denominator of vault/programs/skill-capability/ledger.json (read only, never
written). Nothing is typed in: the per-arm counts, the separation bound and the verdict are
recomputed from the rows on every run.

Authoritative grade: a run's regrade row when one exists, else its stored grade. Only an exact
`PASS` passes, so `FAIL-SWALLOW-REPAIRED` is a failure. A row is measured only when `valid is True`
and its grade is a non-empty string; any other row is UNMEASURED and left out of every count. An arm
with no measured row is UNMEASURED, never a zero rate.

Fisher: two-sided exact test over the 2x2 tables with the observed margins (hypergeometric, computed
with math.comb and fractions.Fraction, no float, no scipy). p = the sum of the probabilities of every
table whose probability is <= the observed table's probability (minimum-likelihood method, exact
comparison). "Separates" means p <= ALPHA = 1/20.

Bound: for the remaining D-SESSIONS budget, the equal allocations k = 1..budget//2 per arm (D-01)
and every allocation n1 + n2 <= budget, n1, n2 >= 1. Claude's discretion (recorded here): a "cannot
separate" claim must hold for the most favourable design, so the verdict floor is the minimum
separable effect over ALL allocations, which is never above the equal-allocation floor.

Verdict: NOT_SEPARABLE when every clause is ok (the largest committed effect is below the floor);
SEPARABLE when V-CT-SEPARATION fails and every other clause is ok (per D-01: record an [E]
owner-bundle line and run no sessions); INCONCLUSIVE otherwise.

Output lines: `  ok   V-CT-X <evidence>` / `  FAIL V-CT-X <diagnostic>` / `  INCONCLUSIVE V-CT-X <why>`,
then `verdict: <V>`, last line `CT_PASS=<passed>/<total>`. Exit codes: 0 pass, 1 fail, inconclusive
or separable, 2 could not run. INCONCLUSIVE is never a pass.

The planes: the rows are laptop fresh-session readings (derived from their Windows transcript paths);
this script's derivation is host-independent and runs no session.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3_REL = ".planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/"
ROWS_REL = P3_REL + "results-delivery.jsonl"
REGRADE_REL = P3_REL + "results-delivery-regrade.jsonl"
DELIVERY_REL = P3_REL + "p3_delivery.py"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = "vault/programs/skill-capability/evidence/E-contribution.md"
SELF_REL = "tools/test_contribution_verdict.py"

ALPHA = Fraction(1, 20)
CONTROL_ARM = "N0"
TREATMENT_ARMS = ("R", "P", "C")
ARM_ORDER = (CONTROL_ARM,) + TREATMENT_ARMS
PASS_GRADE = "PASS"
LAPTOP_PREFIX = "C:\\Users\\User\\"
# D-01: this phase runs no fresh session (a statement about this phase, not a measurement).
FRESH_SESSIONS_THIS_PHASE = 0

# Plan-time exact pins (07-01 interfaces): (a, n1, b, n2) -> two-sided p.
FISHER_PINS = (((4, 4, 0, 4), Fraction(1, 35)), ((5, 5, 0, 5), Fraction(1, 126)),
               ((4, 5, 0, 5), Fraction(1, 21)), ((3, 5, 0, 5), Fraction(1, 6)),
               ((2, 2, 0, 2), Fraction(1, 3)), ((1, 2, 0, 2), Fraction(1)),
               ((3, 4, 0, 5), Fraction(1, 21)), ((10, 10, 5, 10), Fraction(21, 646)))


# --------------------------------------------------------------------------- exact arithmetic


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


@functools.lru_cache(maxsize=None)
def fisher_two_sided(a: int, n1: int, b: int, n2: int) -> Fraction:
    """Two-sided Fisher exact p, minimum-likelihood method, exact Fractions."""
    if not all(_is_int(v) for v in (a, n1, b, n2)):
        raise ValueError("counts must be ints")
    if n1 < 1 or n2 < 1 or not 0 <= a <= n1 or not 0 <= b <= n2:
        raise ValueError(f"invalid table a={a} n1={n1} b={b} n2={n2}")
    s = a + b
    total = comb(n1 + n2, s)
    probs = [Fraction(comb(n1, x) * comb(n2, s - x), total)
             for x in range(max(0, s - n2), min(n1, s) + 1)]
    obs = Fraction(comb(n1, a) * comb(n2, b), total)
    return sum((p for p in probs if p <= obs), Fraction(0))


@functools.lru_cache(maxsize=None)
def min_separable(n1: int, n2: int):
    """(smallest |a/n1 - b/n2| over the tables with p <= ALPHA, [(a, b, p) attaining it]) or None."""
    best, hits = None, []
    for a in range(n1 + 1):
        for b in range(n2 + 1):
            p = fisher_two_sided(a, n1, b, n2)
            if p > ALPHA:
                continue
            e = abs(Fraction(a, n1) - Fraction(b, n2))
            if best is None or e < best:
                best, hits = e, [(a, b, p)]
            elif e == best:
                hits.append((a, b, p))
    return None if best is None else (best, tuple(hits))


def bound(budget: int) -> dict:
    """Equal and all-allocation separation floors for a session budget."""
    equal = [(k, min_separable(k, k)) for k in range(1, budget // 2 + 1)]
    allocs = {}
    for n1 in range(1, budget):
        for n2 in range(1, budget - n1 + 1):
            allocs[(n1, n2)] = min_separable(n1, n2)
    floor, floor_at = None, []
    for key in sorted(allocs):
        ms = allocs[key]
        if ms is None:
            continue
        if floor is None or ms[0] < floor:
            floor, floor_at = ms[0], [key]
        elif ms[0] == floor:
            floor_at.append(key)
    eq_floor = None
    for _, ms in equal:
        if ms is not None and (eq_floor is None or ms[0] < eq_floor):
            eq_floor = ms[0]
    return {"budget": budget, "equal": equal, "allocs": allocs, "floor": floor,
            "floor_at": floor_at, "equal_floor": eq_floor}


def frac(x) -> str:
    if x is None:
        return "none"
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def points(x) -> str:
    return "none" if x is None else frac(Fraction(x) * 100)


def dec4(p: Fraction) -> str:
    """Half-up 4-decimal text of an exact fraction (display only, never compared)."""
    q = (p.numerator * 20000 + p.denominator) // (2 * p.denominator)
    return f"{q // 10000}.{q % 10000:04d}"


# --------------------------------------------------------------------------- sources


def load_rows(path):
    """(rows, refusal): exactly one is None. Refuses bad JSON, a missing run_id/arm, a duplicate run_id."""
    rows, seen = [], set()
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        return None, f"{path}: {exc}"
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            return None, f"{path}:{n} is not JSON ({exc})"
        if not isinstance(row, dict) or not isinstance(row.get("run_id"), str) or not row["run_id"]:
            return None, f"{path}:{n} has no run_id"
        if row["run_id"] in seen:
            return None, f"{path}:{n} duplicate run_id {row['run_id']}"
        seen.add(row["run_id"])
        rows.append(row)
    return rows, None


def _git(*args):
    """(rc, stdout). rc 127 when git is missing. Argv list only, never a shell."""
    git = shutil.which("git")
    if not git:
        return 127, ""
    r = subprocess.run([git, "-C", str(REPO), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout


def git_text(rev_path: str, git=_git):
    rc, out = git("show", rev_path)
    return out if rc == 0 else None


def frozen(git=_git) -> dict:
    """The frozen object of the ledger, read from its HEAD blob. Read only."""
    text = git_text(f"HEAD:{LEDGER_REL}", git)
    if text is None:
        raise OSError(f"git show HEAD:{LEDGER_REL} failed")
    return json.loads(text)["frozen"]


def lf_sha(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- joins and counts


def authoritative(rows, regrade_rows):
    """({run_id: (grade, source)}, refusal). source 'regrade' when a regrade row exists, else 'stored'."""
    by_id = {r["run_id"]: r for r in rows}
    regrade = {}
    for g in regrade_rows:
        rid = g.get("run_id") if isinstance(g, dict) else None
        if rid not in by_id:
            return None, f"regrade run_id {rid!r} is absent from the rows"
        if rid in regrade:
            return None, f"regrade run_id {rid} appears twice"
        if not isinstance(g.get("grade"), str):
            return None, f"regrade row {rid} has no string grade"
        regrade[rid] = g["grade"]
    out = {}
    for r in rows:
        if r["run_id"] in regrade:
            out[r["run_id"]] = (regrade[r["run_id"]], "regrade")
        else:
            out[r["run_id"]] = (r.get("grade"), "stored")
    return out, None


def stored_grades(rows):
    return {r["run_id"]: (r.get("grade"), "stored") for r in rows}


def is_measured(row, grade) -> bool:
    return row.get("valid") is True and isinstance(grade, str) and grade != ""


def arms_of(rows):
    seen = {r.get("arm") for r in rows if isinstance(r.get("arm"), str)}
    return list(ARM_ORDER) + sorted(seen - set(ARM_ORDER))


def arm_counts(grades, rows) -> dict:
    """Per arm: measured n and passes. n == 0 means UNMEASURED."""
    out = {a: {"n": 0, "passes": 0} for a in arms_of(rows)}
    for r in rows:
        arm = r.get("arm")
        if not isinstance(arm, str):
            continue
        grade = grades.get(r["run_id"], (None, None))[0]
        if not is_measured(r, grade):
            continue
        out[arm]["n"] += 1
        out[arm]["passes"] += grade == PASS_GRADE
    return out


def count_text(c) -> str:
    return "UNMEASURED (0 measured rows)" if c["n"] == 0 else f"{c['passes']} of {c['n']}"


def rate(c) -> Fraction:
    return Fraction(c["passes"], c["n"])


def pairs(counts):
    """[(arm, effect, p)] for every measured treatment arm against the control. Control must be measured."""
    ctl = counts[CONTROL_ARM]
    out = []
    for arm in TREATMENT_ARMS:
        c = counts.get(arm)
        if not c or c["n"] == 0:
            continue
        out.append((arm, abs(rate(c) - rate(ctl)), fisher_two_sided(c["passes"], c["n"], ctl["passes"], ctl["n"])))
    return out


def max_effect(counts):
    ps = pairs(counts)
    return max(e for _, e, _ in ps) if ps else None


# --------------------------------------------------------------------------- clauses


def clause_sources(rows, refusal, grades, grade_refusal, counts):
    if refusal:
        return "INCONCLUSIVE", refusal
    if grade_refusal:
        return "INCONCLUSIVE", grade_refusal
    if not rows:
        return "INCONCLUSIVE", "no rows"
    if counts[CONTROL_ARM]["n"] == 0:
        return "INCONCLUSIVE", f"control arm {CONTROL_ARM} UNMEASURED (0 measured rows)"
    measured_t = [a for a in TREATMENT_ARMS if counts.get(a, {"n": 0})["n"] > 0]
    if not measured_t:
        return "INCONCLUSIVE", "no treatment arm is measured"
    n_regrade = sum(1 for g, s in grades.values() if s == "regrade")
    per = ", ".join(f"{a} {count_text(counts[a])}" for a in arms_of(rows))
    return "ok", f"{len(rows)} rows, {n_regrade} joined to a regrade row; measured passes: {per}"


def clause_fisher_pins(fn=fisher_two_sided):
    bad = []
    for (a, n1, b, n2), want in FISHER_PINS:
        try:
            got, mirror = fn(a, n1, b, n2), fn(b, n2, a, n1)
        except (ValueError, ZeroDivisionError) as exc:
            return "FAIL", f"{a}/{n1} vs {b}/{n2} raised {exc}"
        if got != want:
            bad.append(f"{a}/{n1} vs {b}/{n2} = {frac(got)}, pinned {frac(want)}")
        elif mirror != got:
            bad.append(f"{a}/{n1} vs {b}/{n2} not symmetric ({frac(got)} vs {frac(mirror)})")
    if bad:
        return "FAIL", "; ".join(bad)
    return "ok", f"{len(FISHER_PINS)} exact pins reproduced, each symmetric (e.g. 3/4 vs 0/5 = 1/21, 1/2 vs 0/2 = 1)"


def clause_bound(b):
    if b is None:
        return "INCONCLUSIVE", "no budget"
    k5 = dict(b["equal"]).get(5)
    k5t = f"; equal k=5 floor {frac(k5[0])}" if k5 else ""
    at = ",".join(f"({n1},{n2})" for n1, n2 in b["floor_at"])
    return "ok", (f"budget {b['budget']} sessions: all-allocation floor {frac(b['floor'])} "
                  f"({points(b['floor'])} points) first at {at or 'none'}{k5t}")


def separation_verdict(effect, floor) -> str:
    return "NOT_SEPARABLE" if floor is None or effect < floor else "SEPARABLE"


def clause_separation(counts, b, ok_sources):
    if not ok_sources:
        return "INCONCLUSIVE", "sources refused; no effect computed"
    if b is None:
        return "INCONCLUSIVE", "no bound; no floor"
    effect = max_effect(counts)
    per = ", ".join(f"{a} vs {CONTROL_ARM} {frac(e)} (p={frac(p)})" for a, e, p in pairs(counts))
    if separation_verdict(effect, b["floor"]) == "NOT_SEPARABLE":
        return "ok", (f"NOT_SEPARABLE: the largest committed effect {frac(effect)} is below the smallest effect "
                      f"any allocation within {b['budget']} sessions can separate ({frac(b['floor'])}); {per}")
    return "FAIL", (f"SEPARABLE: the budget could separate an effect of this size ({frac(effect)} >= "
                    f"{frac(b['floor'])}); per D-01 record an [E] owner-bundle line and run no sessions; {per}")


def verdict_of(results) -> str:
    st = {name: status for name, status, _ in results}
    if all(s == "ok" for s in st.values()):
        return "NOT_SEPARABLE"
    if st.get("V-CT-SEPARATION") == "FAIL" and all(s == "ok" for n, s in st.items() if n != "V-CT-SEPARATION"):
        return "SEPARABLE"
    return "INCONCLUSIVE"


def evaluate_core(rows, refusal, regrade_rows, budget):
    """Pure clauses over one rows set. Returns (results, ctx)."""
    grades, grade_refusal = (None, None) if refusal else authoritative(rows, regrade_rows)
    counts = arm_counts(grades, rows) if grades is not None else None
    results = [("V-CT-SOURCES",) + clause_sources(rows, refusal, grades or {}, grade_refusal,
                                                   counts or {CONTROL_ARM: {"n": 0}})]
    ok_sources = results[0][1] == "ok"
    results.append(("V-CT-FISHER-PINS",) + clause_fisher_pins())
    b = bound(budget) if _is_int(budget) and budget > 0 else None
    results.append(("V-CT-BOUND",) + (clause_bound(b) if b else ("INCONCLUSIVE", f"budget {budget!r} is not an int > 0")))
    results.append(("V-CT-SEPARATION",) + clause_separation(counts, b, ok_sources))
    return results, {"grades": grades, "counts": counts, "bound": b}


# --------------------------------------------------------------------------- render


def sessions_host(rows) -> str:
    ts = [((r.get("metrics") or {}).get("transcript")) for r in rows]
    if ts and all(isinstance(t, str) and t.startswith(LAPTOP_PREFIX) for t in ts):
        return "laptop"
    return "host unknown"


def render(rows, regrade_rows, fro) -> str:
    denoms = fro["denominators"]
    budget = denoms["D-SESSIONS"]["new_benchmark_cap"]
    results, ctx = evaluate_core(rows, None, regrade_rows, budget)
    grades, counts, b = ctx["grades"], ctx["counts"], ctx["bound"]
    if grades is None or b is None:
        raise ValueError("sources or budget refused; nothing to render")
    stored = arm_counts(stored_grades(rows), rows)
    regrade = {g["run_id"]: g["grade"] for g in regrade_rows}
    rule = next(p["rule"] for p in fro["pillars"] if p["id"] == "E")
    L = []
    L.append("# [E] contribution + result consumption -- D-SESSIONS measurement")
    L.append("")
    L.append(f"Planes: sessions host `{sessions_host(rows)}` (derived: every row's `metrics.transcript` starts with "
             f"`{LAPTOP_PREFIX}`); derivation host-independent (this file is rendered from committed rows by "
             f"`{SELF_REL}`, nothing typed in). Sessions consumed by this phase: {FRESH_SESSIONS_THIS_PHASE}.")
    L.append("")
    L.append("Frozen pillar E rule (ledger `frozen.pillars[E].rule`):")
    L.append("")
    L.append(f"> {rule}")
    L.append("")
    L.append("## Rows (authoritative grade = regrade row when one exists, else stored grade)")
    L.append("")
    L.append("| run_id | arm | rep | valid | stored grade | regrade grade | authoritative | source |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        g, src = grades[r["run_id"]]
        L.append(f"| {r['run_id']} | {r.get('arm')} | {r.get('rep')} | {r.get('valid')} | {r.get('grade') or '-'} | "
                 f"{regrade.get(r['run_id'], '-')} | {g or 'UNMEASURED'} | {src} |")
    L.append("")
    L.append("## Arms (passes = exact `PASS`)")
    L.append("")
    L.append("| arm | measured n | passes (authoritative) | passes (stored) |")
    L.append("|---|---|---|---|")
    for a in arms_of(rows):
        c, s = counts[a], stored[a]
        L.append(f"| {a} | {c['n']} | {count_text(c)} | {count_text(s)} |")
    L.append("")
    L.append(f"## Pairs against {CONTROL_ARM} (authoritative grades, two-sided Fisher exact)")
    L.append("")
    L.append("| arm | effect | points | p | p (4 dp) |")
    L.append("|---|---|---|---|---|")
    for a, e, p in pairs(counts):
        L.append(f"| {a} | {frac(e)} | {points(e)} | {frac(p)} | {dec4(p)} |")
    L.append("")
    L.append(f"## Separation bound (alpha {frac(ALPHA)}, budget {b['budget']} sessions)")
    L.append("")
    L.append("Equal allocation (k sessions per arm):")
    L.append("")
    L.append("| k | floor | points | attaining tables (a/k vs b/k, p) |")
    L.append("|---|---|---|---|")
    for k, ms in b["equal"]:
        if ms is None:
            L.append(f"| {k} | none | none | no table separates |")
        else:
            t = "; ".join(f"{a}/{k} vs {bb}/{k} p={frac(p)}" for a, bb, p in ms[1])
            L.append(f"| {k} | {frac(ms[0])} | {points(ms[0])} | {t} |")
    L.append("")
    sep = {k: v for k, v in b["allocs"].items() if v is not None}
    L.append(f"All allocations n1 + n2 <= {b['budget']} (n1, n2 >= 1): {len(b['allocs'])} allocations, "
             f"{len(b['allocs']) - len(sep)} separate nothing; those that separate:")
    L.append("")
    L.append("| n1 | n2 | floor | points | attaining tables (a/n1 vs b/n2, p) |")
    L.append("|---|---|---|---|---|")
    for (n1, n2), ms in sorted(sep.items()):
        t = "; ".join(f"{a}/{n1} vs {bb}/{n2} p={frac(p)}" for a, bb, p in ms[1])
        L.append(f"| {n1} | {n2} | {frac(ms[0])} | {points(ms[0])} | {t} |")
    L.append("")
    at = ", ".join(f"({n1},{n2})" for n1, n2 in b["floor_at"])
    L.append(f"Floor: {frac(b['floor'])} ({points(b['floor'])} points), first attained at {at}; "
             f"equal-allocation floor {frac(b['equal_floor'])} ({points(b['equal_floor'])} points).")
    L.append("")
    L.append(f"verdict: {verdict_of(results)} (largest committed effect {frac(max_effect(counts))}, "
             f"floor {frac(b['floor'])})")
    L.append("")
    L.append("## Commands")
    L.append("")
    reps = {}
    for r in rows:
        if isinstance(r.get("arm"), str) and _is_int(r.get("rep")):
            reps[r["arm"]] = max(reps.get(r["arm"], 0), r["rep"])
    for a in arms_of(rows):
        if a in reps:
            L.append(f"command: python {DELIVERY_REL} run --arm {a} --reps {reps[a]}")
    L.append("")
    L.append(f"(host laptop; shape from the `{DELIVERY_REL}` docstring line 6; per-run settings such as arm C's "
             "`--settings` card attachment are not recorded in the rows)")
    L.append("")
    L.append(f"command: python3 {SELF_REL}")
    L.append(f"command: python3 {SELF_REL} --write-evidence")
    L.append("")
    L.append("(`python` on the laptop, `python3` on gex44; the first renders nothing, it checks)")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- main


def emit(results) -> int:
    passed = 0
    for name, status, text in results:
        print(f"  {status:<4} {name} {text}")
        passed += status == "ok"
    print(f"verdict: {verdict_of(results)}")
    print(f"CT_PASS={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def default_rows():
    rows, refusal = load_rows(REPO / ROWS_REL)
    reg, rrefusal = load_rows(REPO / REGRADE_REL)
    return rows, refusal or rrefusal, reg or []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jsonl", help="evaluate the verdict clauses on this rows file only")
    ap.add_argument("--regrade", help="regrade file joined to --jsonl (default under --jsonl: none)")
    ap.add_argument("--write-evidence", action="store_true", help=f"render {EVIDENCE_REL}")
    args = ap.parse_args(argv)
    try:
        fro = frozen()
        budget = fro["denominators"]["D-SESSIONS"]["new_benchmark_cap"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"CT_VERDICT=COULD_NOT_RUN frozen ledger unreadable: {exc}")
        return 2
    if args.jsonl:
        rows, refusal = load_rows(args.jsonl)
        reg, rref = (load_rows(args.regrade) if args.regrade else ([], None))
        print(f"  (rows {args.jsonl}; regrade {args.regrade or 'none: stored grades only'})")
        results, _ = evaluate_core(rows, refusal or rref, reg or [], budget)
        return emit(results)
    rows, refusal, reg = default_rows()
    if args.write_evidence:
        if refusal:
            print(f"cannot render: {refusal}")
            return 1
        try:
            text = render(rows, reg, fro)
        except ValueError as exc:
            print(f"cannot render: {exc}")
            return 1
        out = REPO / EVIDENCE_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {EVIDENCE_REL} ({len(text)} chars)")
        return 0
    results, _ = evaluate_core(rows, refusal, reg, budget)
    return emit(results)


if __name__ == "__main__":
    sys.exit(main())
