#!/usr/bin/env python
"""test_contribution_verdict.py -- pillar E verdict gate (skill-capability, SC-E, decisions D-01/D-02).

    python3 tools/test_contribution_verdict.py                   # check (default mode)
    python3 tools/test_contribution_verdict.py --jsonl PATH      # verdict clauses on one rows file only
    python3 tools/test_contribution_verdict.py --jsonl P --regrade R   # same, with a regrade file
    python3 tools/test_contribution_verdict.py --drills          # print the in-process mutant drills
    python3 tools/test_contribution_verdict.py --json            # derived figures as one JSON object
    python3 tools/test_contribution_verdict.py --write-evidence  # render the D-SESSIONS measurement file

What it reads: the committed paired delivery benchmark of the cognitive-resource-os P3 ablation
(results-delivery.jsonl, arms N0/R/P/C) joined by run_id with results-delivery-regrade.jsonl, and
the frozen D-SESSIONS denominator of vault/programs/skill-capability/ledger.json (read only, never
written). Nothing is typed in: the per-arm counts, the separation bound and the verdict are
recomputed from the rows on every run. In the default mode only the rows whose run_id is in the
blob at ROWS_PIN_COMMIT are used; the P3 jsonl is append-only and owned by another workstream.

Authoritative grade: a run's regrade row when one exists, else its stored grade. Three provenance
clauses justify that choice (V-CT-AUTH-COMMIT, -GRADER, -AUDIT); the verdict needs all three. Only an
exact `PASS` passes, so `FAIL-SWALLOW-REPAIRED` is a failure. A row is measured only when
`valid is True` and its grade is a non-empty string; any other row is UNMEASURED and left out of
every count. An arm with no measured row is UNMEASURED, never a zero rate.

Fisher: two-sided exact test over the 2x2 tables with the observed margins (hypergeometric, computed
with math.comb and fractions.Fraction, no float, no scipy). p = the sum of the probabilities of every
table whose probability is <= the observed table's probability (minimum-likelihood method, exact
comparison). "Separates" means p <= ALPHA = 1/20.

Bound: the budget is D-SESSIONS.new_benchmark_cap minus the session counts stated by phases 1-6
(read from their committed SUMMARYs and evidence files). It covers the equal allocations
k = 1..budget//2 per arm (D-01) and every allocation n1 + n2 <= budget, n1, n2 >= 1. Claude's
discretion (recorded here): a "cannot separate" claim must hold for the most favourable FRESH design, so
the verdict floor is the minimum separable effect over ALL allocations, which is never above the
equal-allocation floor. Unstated phases can only lower the true budget, and the floor never falls
as the budget shrinks (by construction: a smaller budget's allocations are a subset of a larger
one's, so its floor is a minimum over fewer tables; V-CT-BOUND prints that it holds and the
bound-floors-fall drill proves only its comparator, not the property), so the stated budget is the
most favourable one. Design space: fresh allocations only. Topping up the committed arms with new
sessions of the same protocol is a different design; its floor is rendered beside the bound (and in
--json as `topup`) with the verdict each committed effect gets against it, and it does not move the
verdict floor (07-REVIEW IN-03).

Verdict: NOT_SEPARABLE when every clause is ok (the largest committed effect is below the floor);
SEPARABLE when V-CT-SEPARATION fails and every other clause is ok (per D-01: record an [E]
owner-bundle line and run no sessions); INCONCLUSIVE otherwise.

Output lines: `  ok   V-CT-X <evidence>` / `  FAIL V-CT-X <diagnostic>` / `  INCONCLUSIVE V-CT-X <why>`,
then `verdict: <V>`, last line `CT_PASS=<passed>/<total>`. Exit codes: 0 pass, 1 fail, inconclusive
or separable, 2 could not run. INCONCLUSIVE is never a pass; a git failure is INCONCLUSIVE, never a
guessed hash. `--json` exits 1 unless the verdict is NOT_SEPARABLE.

Committed sources only: the audit, the residency plan, p3_runner.py, the phase SUMMARYs, the
evidence files and the ledger's frozen object are read as their HEAD blobs (`git show HEAD:<path>`).
An edit to a cited line, or a new phase 1-6 SUMMARY with a session statement, makes
V-CT-EVIDENCE-CURRENT go red. That is the intended signal: re-render, and re-pin state.E's sha256
in the same commit.

The planes: the rows are laptop fresh-session readings (derived from their Windows transcript paths);
this script's derivation is host-independent and runs no session.
"""
from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3_REL = ".planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/"
ROWS_REL = P3_REL + "results-delivery.jsonl"
REGRADE_REL = P3_REL + "results-delivery-regrade.jsonl"
DELIVERY_REL = P3_REL + "p3_delivery.py"
RUNNER_REL = P3_REL + "p3_runner.py"
AUDIT_REL = "vault/audits/cwst-representation-verdict-2026-10-03.md"
RESIDENCY_REL = "vault/plans/skill-residency-program-2026-10-03.md"
REQ_REL = ".planning/workstreams/skill-capability/REQUIREMENTS.md"
PHASES_REL = ".planning/workstreams/skill-capability/phases/"
EVIDENCE_DIR_REL = "vault/programs/skill-capability/evidence/"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = EVIDENCE_DIR_REL + "E-contribution.md"
SELF_REL = "tools/test_contribution_verdict.py"

ALPHA = Fraction(1, 20)
CONTROL_ARM = "N0"
TREATMENT_ARMS = ("R", "P", "C")
ARM_ORDER = (CONTROL_ARM,) + TREATMENT_ARMS
PASS_GRADE = "PASS"
LAPTOP_PREFIX = "C:\\Users\\User\\"
THIS_PHASE = 7
# D-01: this phase runs no fresh session (a statement about this phase, not a measurement).
FRESH_SESSIONS_THIS_PHASE = 0
NEEDED_K_MAX = 40
# The commit that brought results-delivery.jsonl to its 8 rows (appended the 2 C rows).
ROWS_PIN_COMMIT = "123c96cc"

# Plan-time exact pins (07-01 interfaces): (a, n1, b, n2) -> two-sided p.
FISHER_PINS = (((4, 4, 0, 4), Fraction(1, 35)), ((5, 5, 0, 5), Fraction(1, 126)),
               ((4, 5, 0, 5), Fraction(1, 21)), ((3, 5, 0, 5), Fraction(1, 6)),
               ((2, 2, 0, 2), Fraction(1, 3)), ((1, 2, 0, 2), Fraction(1)),
               ((3, 4, 0, 5), Fraction(1, 21)), ((10, 10, 5, 10), Fraction(21, 646)))
# Review-time pins for the necessary session figures (07-REVIEW WR-01, recomputed independently with
# factorial-form fractions): effect -> (smallest n1 + n2 that separates it, its allocations, equal k).
# 3/6 vs 0/9 has effect 1/2 and p = 4/91; 2/2 vs 0/5 has effect 1 and p = 1/21 (2/2 vs 0/4 = 1/15 and
# 3/3 vs 0/3 = 1/10 do not separate, so 7 is the smallest total for effect 1).
NEEDED_PINS = ((Fraction(1, 2), 15, ((6, 9), (9, 6)), 10),
               (Fraction(1), 7, ((2, 5), (3, 4), (4, 3), (5, 2)), 4))

# Session-count phrasings used by phases 1-6 (three at plan time, a fourth found at execution in F).
# Each is anchored (no digit, letter, '/' or '.' before the statement) and refuses a statement opened by
# "of " ("2 of 10 fresh sessions were consumed"), "if " or "would " (a conditional), which are not a
# phase's own count (07-REVIEW IN-01).
_SESSION_GUARD = r"(?<![\w/.])(?<!\bof )(?<!\bif )(?<!\bwould )"
SESSION_RES = (re.compile(_SESSION_GUARD + r"(\d+) fresh sessions? were consumed", re.I),
               re.compile(_SESSION_GUARD + r"consumed this phase: (\d+) fresh sessions?", re.I),
               re.compile(_SESSION_GUARD + r"fresh sessions consumed in this phase: (\d+)(?![\w/]|\.\d)", re.I),
               re.compile(_SESSION_GUARD + r"this phase consumed (\d+) fresh sessions?", re.I))
SUMMARY_PATH_RE = re.compile(r"^" + re.escape(PHASES_REL) + r"(\d{2})-[^/]+/[^/]+-SUMMARY\.md$")
EVIDENCE_PATH_RE = re.compile(r"^" + re.escape(EVIDENCE_DIR_REL) + r"([A-Z])-[^/]+\.md$")
TRACE_RE = re.compile(r"^\| SC-([A-Z]) \| Phase (\d+) \|", re.M)
RUNNER_RES = (re.compile(r'^RUNS = Path\(r"C:\\[^"]*"\)', re.M), re.compile(r'^CLAUDE = r"C:\\[^"]*"', re.M))


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
    """(smallest |a/n1 - b/n2| over the tables with p <= ALPHA, ((a, b, p) attaining it)) or None."""
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


def _floor_over(allocs, budget):
    floor, at = None, []
    for key in sorted(allocs):
        ms = allocs[key]
        if ms is None or key[0] + key[1] > budget:
            continue
        if floor is None or ms[0] < floor:
            floor, at = ms[0], [key]
        elif ms[0] == floor:
            at.append(key)
    return floor, at


def bound(budget: int) -> dict:
    """Equal and all-allocation separation floors for a session budget, plus the floor per smaller budget."""
    equal = [(k, min_separable(k, k)) for k in range(1, budget // 2 + 1)]
    allocs = {}
    for n1 in range(1, budget):
        for n2 in range(1, budget - n1 + 1):
            allocs[(n1, n2)] = min_separable(n1, n2)
    floor, floor_at = _floor_over(allocs, budget)
    eq_floor = None
    for _, ms in equal:
        if ms is not None and (eq_floor is None or ms[0] < eq_floor):
            eq_floor = ms[0]
    floors = {bb: _floor_over(allocs, bb)[0] for bb in range(2, budget + 1)}
    return {"budget": budget, "equal": equal, "allocs": allocs, "floor": floor,
            "floor_at": floor_at, "equal_floor": eq_floor, "floors": floors}


def topup_floor(counts, budget):
    """Design space beyond fresh allocations (07-REVIEW IN-03): top up the committed control and one
    committed treatment arm with x + y <= budget new sessions of the same protocol. Returns
    (floor, [(control total, treatment total)...]) over every measured treatment arm, or (None, [])."""
    ctl = (counts or {}).get(CONTROL_ARM)
    if not ctl or ctl["n"] == 0 or not _is_int(budget) or budget < 0:
        return None, []
    allocs = {}
    for arm in TREATMENT_ARMS:
        c = counts.get(arm)
        if not c or c["n"] == 0:
            continue
        for x in range(budget + 1):
            for y in range(budget - x + 1):
                key = (ctl["n"] + x, c["n"] + y)
                if key not in allocs:
                    allocs[key] = min_separable(*key)
    return _floor_over(allocs, 10 ** 9) if allocs else (None, [])


def floors_monotone(floors) -> list:
    """Budgets at which the floor FALLS as the budget shrinks (None = nothing separates = infinite)."""
    inf = Fraction(10 ** 9)
    keys = sorted(floors)
    return [(lo, hi) for lo, hi in zip(keys, keys[1:])
            if (floors[lo] if floors[lo] is not None else inf) < (floors[hi] if floors[hi] is not None else inf)]


def needed_k(effect):
    """Smallest equal k <= NEEDED_K_MAX whose floor <= effect; None for a zero effect (a table with
    a == b at equal k is the modal table, p = 1) or when no k up to the cap is enough."""
    if effect is None or effect <= 0:
        return None
    for k in range(1, NEEDED_K_MAX + 1):
        ms = min_separable(k, k)
        if ms is not None and ms[0] <= effect:
            return k
    return None


def needed_total(effect):
    """(smallest n1 + n2 over ALL allocations whose floor <= effect, [(n1, n2) attaining it]), the same
    most-favourable-design rule as the verdict floor. Searched up to 2 x needed_k(effect), where (k, k)
    always qualifies, so the answer is never above the equal one. None when needed_k is None."""
    k = needed_k(effect)
    if k is None:
        return None
    for tot in range(2, 2 * k + 1):
        hits = []
        for n1 in range(1, tot):
            ms = min_separable(n1, tot - n1)
            if ms is not None and ms[0] <= effect:
                hits.append((n1, tot - n1))
        if hits:
            return tot, hits
    return None


def needed_text(effect) -> str:
    """'smallest total T sessions (n1 vs n2 or ...); equal allocation k per arm (2k sessions)'."""
    nt, k = needed_total(effect), needed_k(effect)
    if nt is None or k is None:
        return f"no design up to {NEEDED_K_MAX} per arm separates it"
    alloc = " or ".join(f"{a} vs {b}" for a, b in nt[1])
    return f"smallest total {nt[0]} sessions ({alloc}); equal allocation {k} per arm ({2 * k} sessions)"


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
    """(rows, refusal): exactly one is None. Refuses bad JSON, a missing run_id, a duplicate run_id."""
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


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _find_line(text, pattern):
    """(1-based line, matched text) of the first regex match, or (None, None)."""
    if text is None:
        return None, None
    m = re.search(pattern, text)
    return (None, None) if not m else (_line_of(text, m.start()), _collapse(m.group(0)))


# --------------------------------------------------------------------------- pins and static texts (git)


def _parse_blob(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def add_commit(rel, git=_git):
    """Full hash of the commit that added rel, or None when git fails or answers empty."""
    rc, out = git("log", "--diff-filter=A", "--format=%H", "--", rel)
    hashes = out.split() if rc == 0 else []
    return hashes[-1] if hashes else None


def pin_info(git=_git) -> dict:
    """Both pins, their ancestry and their blobs. Any git failure is recorded as `error`, never guessed."""
    info = {"rows_commit": ROWS_PIN_COMMIT, "regrade_commit": None, "error": None,
            "rows_blob": None, "regrade_blob": None, "rows_sha": None, "regrade_sha": None}
    info["regrade_commit"] = add_commit(REGRADE_REL, git)
    if not info["regrade_commit"]:
        info["error"] = f"git log --diff-filter=A -- {REGRADE_REL} failed or was empty"
        return info
    for ref in (ROWS_PIN_COMMIT, info["regrade_commit"]):
        rc, _ = git("merge-base", "--is-ancestor", ref, "HEAD")
        if rc != 0:
            info["error"] = f"pin {ref[:8]} is not an ancestor of HEAD (git rc {rc})"
            return info
    for key, ref, rel in (("rows", ROWS_PIN_COMMIT, ROWS_REL), ("regrade", info["regrade_commit"], REGRADE_REL)):
        text = git_text(f"{ref}:{rel}", git)
        if text is None:
            info["error"] = f"git show {ref[:8]}:{rel} failed"
            return info
        try:
            info[key + "_blob"] = _parse_blob(text)
        except ValueError as exc:
            info["error"] = f"blob {ref[:8]}:{rel} is not JSON lines ({exc})"
            return info
        info[key + "_sha"] = lf_sha(text)
    return info


def session_sources(git=_git):
    """(sources, refusal). Committed phase 1-6 SUMMARYs and evidence/<P>-*.md files whose pillar maps to
    a phase below 7, each as its HEAD blob. Phase 7 files and E-contribution.md are never scanned."""
    req = git_text(f"HEAD:{REQ_REL}", git)
    if req is None:
        return None, f"git show HEAD:{REQ_REL} failed"
    phase_of = {p: int(n) for p, n in TRACE_RE.findall(req)}
    if not phase_of:
        return None, f"{REQ_REL} has no traceability rows"
    rc, out = git("ls-tree", "-r", "--name-only", "HEAD", "--", PHASES_REL, EVIDENCE_DIR_REL)
    if rc != 0:
        return None, f"git ls-tree HEAD failed (rc {rc})"
    sources = []
    for path in sorted(out.split()):
        m, e = SUMMARY_PATH_RE.match(path), EVIDENCE_PATH_RE.match(path)
        if m:
            phase = int(m.group(1))
        elif e and path != EVIDENCE_REL:
            if e.group(1) not in phase_of:
                sources.append({"path": path, "phase": None, "text": git_text(f"HEAD:{path}", git)})
                continue
            phase = phase_of[e.group(1)]
        else:
            continue
        if phase >= THIS_PHASE:
            continue
        text = git_text(f"HEAD:{path}", git)
        if text is None:
            return None, f"git show HEAD:{path} failed"
        sources.append({"path": path, "phase": phase, "text": text})
    return sources, None


def static(git=_git) -> dict:
    """Every committed text the verdict and the render cite. None marks a git failure."""
    st = {"info": pin_info(git)}
    rc_commit = add_commit(REGRADE_REL, git)
    st["regrade_commit"] = rc_commit
    msg = None
    if rc_commit:
        rc, out = git("log", "-1", "--format=%s%n%b", rc_commit)
        msg = out if rc == 0 and out.strip() else None
    st["commit_msg"] = msg
    st["grader"] = git_text(f"{rc_commit}:{DELIVERY_REL}", git) if rc_commit else None
    st["delivery_head"] = git_text(f"HEAD:{DELIVERY_REL}", git)
    st["audit"] = git_text(f"HEAD:{AUDIT_REL}", git)
    st["residency"] = git_text(f"HEAD:{RESIDENCY_REL}", git)
    st["runner"] = git_text(f"HEAD:{RUNNER_REL}", git)
    st["sessions_src"], st["sessions_refusal"] = session_sources(git)
    return st


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
    """[(arm, effect, p)] for every measured treatment arm against the control. An UNMEASURED control
    (absent or 0 measured rows) gives no pair, so max_effect is None, never a 0/0 rate (07-REVIEW WR-03)."""
    ctl = (counts or {}).get(CONTROL_ARM)
    if not ctl or ctl["n"] == 0:
        return []
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


CFIXED_RE = re.compile(r"^\s*(\d+)/(\d+) PASS\b")


def c_fixed_frozen(arm_c, counts, b):
    """The frozen D-CARD.arm_c figure ("a/n PASS ...", no committed row) judged by the SAME verdict rule as
    the committed rows: its effect against the committed control, separation_verdict against the budget
    floor, and the equal k it would need. None when the figure does not parse or nothing is measured."""
    m = CFIXED_RE.match(arm_c) if isinstance(arm_c, str) else None
    ctl = (counts or {}).get(CONTROL_ARM)
    if m is None or not ctl or ctl["n"] == 0 or b is None:
        return None
    a, n = int(m.group(1)), int(m.group(2))
    if n < 1 or a > n:
        return None
    eff = abs(Fraction(a, n) - rate(ctl))
    return {"passes": a, "n": n, "control": ctl, "effect": eff, "verdict": separation_verdict(eff, b["floor"]),
            "needed_k": needed_k(eff), "p_rows": fisher_two_sided(a, n, ctl["passes"], ctl["n"])}


def consumption(rows) -> dict:
    """Per arm, from the rows' delivery / card_rows fields. A row is measured for consumption only when
    valid is True and delivery.state is MEASURED with boolean skill fields; otherwise UNMEASURED."""
    out = {}
    for r in rows:
        arm = r.get("arm") if isinstance(r.get("arm"), str) else "?"
        a = out.setdefault(arm, {"n": 0, "unmeasured": 0, "listing": Counter(), "invoked": 0,
                                 "before_commit": 0, "card_rows": Counter(), "consumed": 0, "contradictions": []})
        d = r.get("delivery")
        if (r.get("valid") is not True or not isinstance(d, dict) or d.get("state") != "MEASURED"
                or not isinstance(d.get("skill_invoked"), bool) or not isinstance(d.get("skill_before_commit"), bool)):
            a["unmeasured"] += 1
            continue
        a["n"] += 1
        a["listing"][str(d.get("listing"))] += 1
        a["invoked"] += d["skill_invoked"]
        a["before_commit"] += d["skill_before_commit"]
        cards = r.get("card_rows") if isinstance(r.get("card_rows"), list) else []
        for c in cards:
            a["card_rows"][str(c)] += 1
        if d["skill_before_commit"] and not d["skill_invoked"]:
            a["contradictions"].append(r["run_id"])
        a["consumed"] += d["skill_invoked"] or any(str(c).startswith("deny") for c in cards)
    return out


def session_statements(sources) -> dict:
    """{phase: {"figures": {n}, "where": [(path, line, n)]}} plus unattributed statements under None."""
    out = {}
    for src in sources:
        text = src["text"] or ""
        seen = set()
        for rx in SESSION_RES:
            for m in rx.finditer(text):
                key = (_line_of(text, m.start()), int(m.group(1)))
                if key in seen:
                    continue
                seen.add(key)
                ph = out.setdefault(src["phase"], {"figures": set(), "where": []})
                ph["figures"].add(key[1])
                ph["where"].append((src["path"], key[0], key[1]))
    return out


def sessions_budget(st, cap):
    """(per-phase statements, consumed_stated, remaining, refusal)."""
    if st.get("sessions_src") is None:
        return None, None, None, st.get("sessions_refusal") or "session sources unreadable"
    stm = session_statements(st["sessions_src"])
    if None in stm:
        w = stm[None]["where"][0]
        return stm, None, None, f"a session statement in {w[0]}:{w[1]} maps to no phase (no traceability row)"
    conflicts = [p for p, v in stm.items() if len(v["figures"]) > 1]
    if conflicts:
        p = conflicts[0]
        return stm, None, None, f"phase {p} states different figures {sorted(stm[p]['figures'])}"
    consumed = sum(next(iter(v["figures"])) for v in stm.values())
    remaining = cap - consumed
    if remaining < 0:
        return stm, consumed, remaining, f"budget overdrawn: stated {consumed} > new_benchmark_cap {cap}"
    return stm, consumed, remaining, None


def runner_constants(text):
    """[(line, text)] of the p3_runner.py Windows constants, by regex."""
    out = []
    for rx in RUNNER_RES:
        m = rx.search(text or "")
        if m:
            out.append((_line_of(text, m.start()), m.group(0)))
    return out


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


def clause_sessions(stm, consumed, remaining, refusal, runner):
    if refusal:
        return "INCONCLUSIVE", refusal
    if len(runner) != len(RUNNER_RES):
        return "INCONCLUSIVE", f"the p3_runner.py Windows constants backing this phase's 0 were not found in HEAD:{RUNNER_REL}"
    per = ", ".join(f"phase {p} {next(iter(v['figures']))}" for p, v in sorted(stm.items())) or "none"
    unstated = [str(p) for p in range(1, THIS_PHASE) if p not in stm]
    return "ok", (f"stated: {per}; not stated: phase {', '.join(unstated) or 'none'}; consumed_stated {consumed}, "
                  f"remaining {remaining}; this phase {FRESH_SESSIONS_THIS_PHASE} (p3_runner.py lines "
                  f"{', '.join(str(ln) for ln, _ in runner)} are Windows paths)")


def clause_bound(b, remaining, refusal, floors=None):
    if refusal:
        return "INCONCLUSIVE", f"no budget: {refusal}"
    if b is None:
        return "INCONCLUSIVE", f"budget {remaining!r} is not an int >= 0"
    falls = floors_monotone(floors if floors is not None else b["floors"])
    if falls:
        return "FAIL", f"the floor falls as the budget shrinks between budgets {falls[0]}"
    k5 = dict(b["equal"]).get(5)
    k5t = f"; equal k=5 floor {frac(k5[0])}" if k5 else ""
    at = ",".join(f"({n1},{n2})" for n1, n2 in b["floor_at"])
    return "ok", (f"budget {b['budget']} sessions: all-allocation floor {frac(b['floor'])} "
                  f"({points(b['floor'])} points) attained at {at or 'none'}{k5t}; floors non-increasing in the "
                  f"budget over 2..{b['budget']} (by construction: subset minimum)")


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


def clause_grades_agree(rows, grades, b, ok_sources):
    """D-01: the verdict must not depend on which grade source is authoritative."""
    if not ok_sources:
        return "INCONCLUSIVE", "sources refused; no comparison"
    if b is None:
        return "INCONCLUSIVE", "no bound; no floor"
    auth, stored = arm_counts(grades, rows), arm_counts(stored_grades(rows), rows)
    if stored[CONTROL_ARM]["n"] == 0 or max_effect(stored) is None:
        return "INCONCLUSIVE", "the stored grades leave the control or every treatment arm UNMEASURED"
    ea, es = max_effect(auth), max_effect(stored)
    va, vs = separation_verdict(ea, b["floor"]), separation_verdict(es, b["floor"])
    if va == vs:
        return "ok", f"both grade sources give {va}: authoritative effect {frac(ea)}, stored effect {frac(es)}"
    return "INCONCLUSIVE", (f"grade source decides the verdict: authoritative effect {frac(ea)} -> {va}, "
                            f"stored effect {frac(es)} -> {vs}")


def clause_auth_commit(msg, commit):
    if not commit or msg is None:
        return "INCONCLUSIVE", f"could not read the commit that added {REGRADE_REL} (git failed or empty)"
    subject, _, body = msg.partition("\n")
    if "6/6 swallow" not in subject:
        return "FAIL", f"subject of {commit[:8]} lacks '6/6 swallow': {subject[:80]!r}"
    if "reflog-aware grader" not in _collapse(body):
        return "FAIL", f"body of {commit[:8]} does not name the reflog-aware grader"
    return "ok", f"{commit[:8]} added the regrade file; subject has '6/6 swallow', body names the reflog-aware grader"


def clause_auth_grader(src, commit):
    if not commit or src is None:
        return "INCONCLUSIVE", f"could not read {DELIVERY_REL} at the regrade add commit (git failed)"
    n = src.count("FAIL-SWALLOW-REPAIRED")
    if n == 0:
        return "FAIL", f"{DELIVERY_REL} at {commit[:8]} has no FAIL-SWALLOW-REPAIRED label"
    return "ok", f"{DELIVERY_REL} at {commit[:8]} carries FAIL-SWALLOW-REPAIRED ({n} occurrences)"


def clause_auth_audit(text):
    if text is None:
        return "INCONCLUSIVE", f"git show HEAD:{AUDIT_REL} failed"
    if "regrades FAIL-SWALLOW-REPAIRED" not in _collapse(text):
        return "FAIL", f"{AUDIT_REL} does not say the P run regrades FAIL-SWALLOW-REPAIRED"
    line, _ = _find_line(text, r"regrades\s+FAIL-SWALLOW-REPAIRED")
    return "ok", f"{AUDIT_REL} line {line}: P r1 stored PASS regrades FAIL-SWALLOW-REPAIRED"


def clause_consumption(cons):
    bad = [rid for a in cons.values() for rid in a["contradictions"]]
    if bad:
        return "FAIL", f"skill_before_commit true while skill_invoked false (contradiction): {bad}"
    n = sum(a["n"] for a in cons.values())
    if n == 0:
        return "INCONCLUSIVE", "UNMEASURED: no row carries a measured delivery"
    consumed = sum(a["consumed"] for a in cons.values())
    unm = sum(a["unmeasured"] for a in cons.values())
    per = "; ".join(f"{arm} invoked {a['invoked']} of {a['n']}" for arm, a in sorted(cons.items()) if a["n"])
    return "ok", f"consumed in {consumed} of {n} measured rows ({unm} UNMEASURED); {per}"


def verdict_of(results) -> str:
    st = {name: status for name, status, _ in results}
    if all(s == "ok" for s in st.values()):
        return "NOT_SEPARABLE"
    if st.get("V-CT-SEPARATION") == "FAIL" and all(s == "ok" for n, s in st.items() if n != "V-CT-SEPARATION"):
        return "SEPARABLE"
    return "INCONCLUSIVE"


def evaluate_core(rows, refusal, regrade_rows, cap, st, fisher_fn=fisher_two_sided, floors=None,
                  verdict_only=False):
    """Pure clauses over one rows set and one set of committed texts. Returns (results, ctx)."""
    grades, grade_refusal = (None, None) if refusal else authoritative(rows, regrade_rows)
    counts = arm_counts(grades, rows) if grades is not None else None
    results = [("V-CT-SOURCES",) + clause_sources(rows, refusal, grades or {}, grade_refusal,
                                                   counts or {CONTROL_ARM: {"n": 0}})]
    ok_sources = results[0][1] == "ok"
    results.append(("V-CT-FISHER-PINS",) + clause_fisher_pins(fisher_fn))
    if not _is_int(cap) or cap <= 0:
        stm, consumed, remaining, srefusal = None, None, None, f"new_benchmark_cap {cap!r} is not an int > 0"
    else:
        stm, consumed, remaining, srefusal = sessions_budget(st, cap)
    runner = runner_constants(st.get("runner"))
    results.append(("V-CT-SESSIONS",) + clause_sessions(stm, consumed, remaining, srefusal, runner))
    b = bound(remaining) if srefusal is None and _is_int(remaining) and remaining >= 0 else None
    results.append(("V-CT-BOUND",) + clause_bound(b, remaining, srefusal, floors))
    results.append(("V-CT-SEPARATION",) + clause_separation(counts, b, ok_sources))
    results.append(("V-CT-GRADES-AGREE",) + clause_grades_agree(rows, grades, b, ok_sources))
    cons = consumption(rows if rows else [])
    if not verdict_only:
        results.append(("V-CT-AUTH-COMMIT",) + clause_auth_commit(st.get("commit_msg"), st.get("regrade_commit")))
        results.append(("V-CT-AUTH-GRADER",) + clause_auth_grader(st.get("grader"), st.get("regrade_commit")))
        results.append(("V-CT-AUTH-AUDIT",) + clause_auth_audit(st.get("audit")))
        results.append(("V-CT-CONSUMPTION",) + clause_consumption(cons))
    return results, {"grades": grades, "counts": counts, "bound": b, "sessions": stm, "consumed": consumed,
                     "remaining": remaining, "runner": runner, "consumption": cons}


# --------------------------------------------------------------------------- rows-pinned / evidence-current


def pinned_split(rows, info):
    """(rows inside the pinned run_id set, rows outside it). Without a blob every row is outside."""
    ids = {r["run_id"] for r in (info.get("rows_blob") or [])}
    return [r for r in rows if r["run_id"] in ids], [r for r in rows if r["run_id"] not in ids]


def pinned_regrade_split(regrade_rows, info):
    """(regrade rows whose run_id is in the pinned ROW set, the others). The P3 jsonls are append-only and
    owned by another workstream: a regrade row for an appended run is outside the pin, like its run, and
    must not reach the join (07-REVIEW WR-02). A new regrade row for a PINNED run stays inside and makes
    V-CT-ROWS-PINNED fail, because it would change a pinned run's grade."""
    ids = {r["run_id"] for r in (info.get("rows_blob") or [])}
    inside = [g for g in regrade_rows if isinstance(g, dict) and g.get("run_id") in ids]
    return inside, [g for g in regrade_rows if not (isinstance(g, dict) and g.get("run_id") in ids)]


def clause_rows_pinned(rows, regrade_rows, info, regrade_outside=()):
    if info.get("error"):
        return "INCONCLUSIVE", info["error"]
    blob = {r["run_id"]: r for r in info["rows_blob"]}
    wt = {r["run_id"]: r for r in rows}
    missing = sorted(set(blob) - set(wt))
    if missing:
        return "FAIL", f"pinned run_ids absent from the working tree: {missing}"
    diff = sorted(rid for rid in blob if wt[rid] != blob[rid])
    if diff:
        return "FAIL", f"pinned rows differ from the blob at {ROWS_PIN_COMMIT}: {diff}"
    gb = sorted(json.dumps(g, sort_keys=True) for g in info["regrade_blob"])
    gw = sorted(json.dumps(g, sort_keys=True) for g in regrade_rows)
    if gb != gw:
        return "FAIL", f"regrade rows differ from the blob at {info['regrade_commit'][:8]}"
    orphans = sorted(str(g.get("run_id") if isinstance(g, dict) else g) for g in regrade_outside
                     if not (isinstance(g, dict) and g.get("run_id") in wt))
    if orphans:
        return "FAIL", f"regrade rows outside the pinned set name no row in the working tree: {orphans}"
    outside = len(rows) - len(blob)
    return "ok", (f"{len(blob)} rows equal the blob at {ROWS_PIN_COMMIT} (LF sha256 {info['rows_sha'][:12]}), "
                  f"{len(gb)} regrade rows equal the blob at {info['regrade_commit'][:8]} (LF sha256 "
                  f"{info['regrade_sha'][:12]}); both pins are ancestors of HEAD; {outside} rows and "
                  f"{len(regrade_outside)} regrade rows outside the pinned set")


def clause_evidence_current(wt_text, head_text, rendered):
    if wt_text is None:
        return "FAIL", f"{EVIDENCE_REL} absent from the working tree; re-render with --write-evidence"
    if head_text is None:
        return "FAIL", f"{EVIDENCE_REL} absent at HEAD; re-render with --write-evidence and commit it"
    want = rendered.replace("\r\n", "\n")
    for where, text in (("working tree", wt_text), ("HEAD", head_text)):
        if text.replace("\r\n", "\n") != want:
            return "FAIL", f"{EVIDENCE_REL} at {where} differs from a fresh render; re-render with --write-evidence"
    return "ok", f"working tree and HEAD both equal a fresh render (LF sha256 {lf_sha(want)[:12]})"


def clause_rows_pinned_drill(rows, regrade_rows, info):
    """Text drill: one pinned row's wall_s changed must FAIL."""
    rows = copy.deepcopy(rows)
    rows[0]["wall_s"] = (rows[0].get("wall_s") or 0) + 1
    return clause_rows_pinned(rows, regrade_rows, info)


def clause_evidence_current_drill(rendered):
    """Text drill: one digit of the rendered text changed must FAIL."""
    m = re.search(r"\d", rendered)
    mutated = rendered[:m.start()] + str((int(m.group(0)) + 1) % 10) + rendered[m.end():]
    return clause_evidence_current(mutated, rendered, rendered)


# --------------------------------------------------------------------------- drills


def _fisher_doubled_one_sided(a, n1, b, n2):
    """A wrong implementation for the drill: 2 x the smaller one-sided tail."""
    s, total = a + b, comb(n1 + n2, a + b)
    xs = range(max(0, s - n2), min(n1, s) + 1)
    pr = {x: Fraction(comb(n1, x) * comb(n2, s - x), total) for x in xs}
    up = sum((pr[x] for x in xs if x >= a), Fraction(0))
    lo = sum((pr[x] for x in xs if x <= a), Fraction(0))
    return min(Fraction(1), 2 * min(up, lo))


def _fisher_one_sided(a, n1, b, n2):
    """A wrong implementation for the drill: the upper tail only."""
    s, total = a + b, comb(n1 + n2, a + b)
    xs = range(max(0, s - n2), min(n1, s) + 1)
    return sum((Fraction(comb(n1, x) * comb(n2, s - x), total) for x in xs if x >= a), Fraction(0))


def _git_fails_log(*args):
    """A failing git for the drill: every `git log` call fails, everything else is real."""
    return (128, "") if args and args[0] == "log" else _git(*args)


def _template(rows, arm):
    return next(r for r in rows if r.get("arm") == arm)


def _fab(rows, spec):
    """Fabricated rows from deep copies of real rows: only run_id / arm / rep / grade / valid change."""
    out = []
    for arm, grades in spec:
        for i, g in enumerate(grades, 1):
            r = copy.deepcopy(_template(rows, arm if any(x.get("arm") == arm for x in rows) else "P"))
            r.update({"run_id": f"X-{arm}-r{i}", "arm": arm, "rep": i, "grade": g, "valid": True})
            out.append(r)
    return out


F, P_ = "FAIL-SWALLOW", "PASS"


def _with_text(st, path_suffix, old, new):
    """A copy of st whose session source ending in path_suffix has `old` replaced by `new` (must occur)."""
    st = dict(st)
    srcs = []
    for s in st["sessions_src"]:
        s = dict(s)
        if s["path"].endswith(path_suffix):
            if old not in s["text"]:
                raise ValueError(f"drill anchor {old!r} not in {s['path']}")
            s["text"] = s["text"].replace(old, new)
        srcs.append(s)
    st["sessions_src"] = srcs
    return st


def _drill_specs():
    """(name, mutate(inp) -> inp, {clause: status}, verdict, check). inp keys: rows, regrade, st, fn, floors."""
    def upd(**kw):
        def mut(inp):
            out = dict(inp)
            out.update({k: (v(inp) if callable(v) else v) for k, v in kw.items()})
            return out
        return mut

    def rows_with(fn):
        def f(inp):
            rows = copy.deepcopy(inp["rows"])
            fn(rows)
            return rows
        return f

    def set_invalid_p(rows):
        for r in rows:
            if r.get("arm") == "P":
                r["valid"] = False

    def set_c_empty(rows):
        next(r for r in rows if r.get("arm") == "C")["grade"] = ""

    def set_contradiction(rows):
        rows[0]["delivery"]["skill_before_commit"] = True

    def drop_delivery(rows):
        del rows[0]["delivery"]

    def st_text(key, old, new):
        def f(inp):
            st = dict(inp["st"])
            st[key] = (st[key] or "").replace(old, new)
            return st
        return f

    def falling(inp):
        fl = dict(bound(inp["remaining"])["floors"])
        top = max(fl)
        fl[top - 1] = fl[top] / 2
        return fl

    def unmeasured(arm):
        def chk(inp, ctx, results):
            t = count_text(ctx["counts"][arm]) if ctx["counts"] else "no counts"
            joined = " ".join(x[2] for x in results)
            good = t.startswith("UNMEASURED") and "0/0" not in joined and f"{arm} 0 of" not in joined
            return good, f"{arm} {t}"
        return chk

    def p_out(inp, ctx, results):
        good, note = unmeasured("P")(inp, ctx, results)
        used = [a for a, _, _ in pairs(ctx["counts"])]
        return good and used == ["R", "C"], f"{note}; pairs from {','.join(used)}"

    def c_n1(inp, ctx, results):
        n = ctx["counts"]["C"]["n"]
        return n == 1, f"C measured n {n}"

    def remaining_is(n):
        def chk(inp, ctx, results):
            return ctx["remaining"] == n, f"remaining {ctx['remaining']}"
        return chk

    def cons_unmeasured(inp, ctx, results):
        c = ctx["consumption"]
        n, unm = sum(a["n"] for a in c.values()), sum(a["unmeasured"] for a in c.values())
        return n == 7 and unm == 1, f"consumption measured {n}, UNMEASURED {unm}"

    def set_n0_null(rows):
        for r in rows:
            if r.get("arm") == CONTROL_ARM:
                r["grade"] = None

    def render_refuses(inp, ctx, results):
        """WR-03: stored control UNMEASURED while the regrade grades it -> the render refuses with a reason
        (no ZeroDivisionError), and the stored effect is None, never a 0/0 rate."""
        stored = arm_counts(stored_grades(inp["rows"]), inp["rows"])
        if inp.get("fro") is None:
            return False, "no frozen ledger passed to the drill"
        try:
            text, why = _render_or_none({"rows": inp["rows"], "regrade": inp["regrade"], "st": inp["st"],
                                         "outside": []}, inp["fro"])
        except ArithmeticError as exc:
            return False, f"render raised {type(exc).__name__}"
        good = text is None and why is not None and why.startswith("UNMEASURED") and max_effect(stored) is None
        return good, f"render refused: {(why or 'it rendered')[:60]}"

    def set_c_pass(rows):
        for r in rows:
            if r.get("arm") == "C":
                r["grade"] = PASS_GRADE

    def c_fixed_rule(inp, ctx, results):
        """CR-01: the frozen-figure judgement (c_fixed_frozen) must agree with the verdict on real rows."""
        eff = max_effect(ctx["counts"])
        cf = c_fixed_frozen("2/2 PASS", ctx["counts"], ctx["bound"])
        good = eff == 1 and needed_k(eff) == 4 and cf is not None and cf["verdict"] == "SEPARABLE"
        return good, (f"effect {frac(eff)}, needed equal k {needed_k(eff)}, frozen-figure judgement "
                      f"{cf['verdict'] if cf else 'none'}")

    inc3 = {"V-CT-SOURCES": "INCONCLUSIVE", "V-CT-SEPARATION": "INCONCLUSIVE", "V-CT-GRADES-AGREE": "INCONCLUSIVE"}
    inc_budget = {"V-CT-SESSIONS": "INCONCLUSIVE", "V-CT-BOUND": "INCONCLUSIVE",
                  "V-CT-SEPARATION": "INCONCLUSIVE", "V-CT-GRADES-AGREE": "INCONCLUSIVE"}
    c_rel = EVIDENCE_DIR_REL + "C-delivery.md"
    s22 = "02-listing-floor/02-02-SUMMARY.md"
    sep_rows = upd(rows=lambda i: _fab(i["rows"], [("P", [P_] * 5), ("N0", [F] * 5)]), regrade=[])
    return [
        ("clean", upd(), {}, "NOT_SEPARABLE", None),
        ("sep-P5of5-vs-N0-0of5", sep_rows, {"V-CT-SEPARATION": "FAIL"}, "SEPARABLE", None),
        ("edge-P3of4-vs-N0-0of5", upd(rows=lambda i: _fab(i["rows"], [("P", [P_] * 3 + [F]), ("N0", [F] * 5)]),
                                      regrade=[]), {"V-CT-SEPARATION": "FAIL"}, "SEPARABLE", None),
        ("edge-P3of5-vs-N0-0of5", upd(rows=lambda i: _fab(i["rows"], [("P", [P_] * 3 + [F] * 2), ("N0", [F] * 5)]),
                                      regrade=[]), {}, "NOT_SEPARABLE", None),
        ("c-fixed-2of2-pass", upd(rows=rows_with(set_c_pass)), {"V-CT-SEPARATION": "FAIL"}, "SEPARABLE",
         c_fixed_rule),
        ("no-N0-rows", upd(rows=lambda i: [r for r in i["rows"] if r.get("arm") != CONTROL_ARM],
                           regrade=lambda i: [g for g in i["regrade"] if not g["run_id"].startswith("D-cwst-N0-")]),
         inc3, "INCONCLUSIVE", unmeasured(CONTROL_ARM)),
        ("P-rows-invalid", upd(rows=rows_with(set_invalid_p)), {}, "NOT_SEPARABLE", p_out),
        ("C-r1-grade-empty", upd(rows=rows_with(set_c_empty)), {}, "NOT_SEPARABLE", c_n1),
        ("N0-stored-null-regraded", upd(rows=rows_with(set_n0_null)), {"V-CT-GRADES-AGREE": "INCONCLUSIVE"},
         "INCONCLUSIVE", render_refuses),
        ("regrade-unknown-run_id", upd(regrade=lambda i: list(i["regrade"]) + [{"run_id": "X-ghost-r1", "grade": F}]),
         inc3, "INCONCLUSIVE", None),
        ("grade-sources-disagree", upd(rows=lambda i: _fab(i["rows"], [("P", [P_] * 5), ("N0", [F] * 5)]),
                                       regrade=[{"run_id": f"X-P-r{k}", "grade": F} for k in (1, 2, 3)]),
         {"V-CT-GRADES-AGREE": "INCONCLUSIVE"}, "INCONCLUSIVE", None),
        ("fisher-doubled-one-sided", upd(fn=lambda i: _fisher_doubled_one_sided), {"V-CT-FISHER-PINS": "FAIL"},
         "INCONCLUSIVE", None),
        ("fisher-one-sided", upd(fn=lambda i: _fisher_one_sided), {"V-CT-FISHER-PINS": "FAIL"}, "INCONCLUSIVE", None),
        ("auth-commit-no-reflog-grader", upd(st=st_text("commit_msg", "reflog-aware grader", "history grader")),
         {"V-CT-AUTH-COMMIT": "FAIL"}, "INCONCLUSIVE", None),
        ("auth-grader-no-label", upd(st=st_text("grader", "FAIL-SWALLOW-REPAIRED", "FAIL-SWALLOW")),
         {"V-CT-AUTH-GRADER": "FAIL"}, "INCONCLUSIVE", None),
        ("auth-audit-no-regrade", upd(st=st_text("audit", "regrades FAIL-SWALLOW-REPAIRED", "stays PASS")),
         {"V-CT-AUTH-AUDIT": "FAIL"}, "INCONCLUSIVE", None),
        ("git-log-fails", upd(st=lambda i: static(_git_fails_log)),
         {"V-CT-AUTH-COMMIT": "INCONCLUSIVE", "V-CT-AUTH-GRADER": "INCONCLUSIVE"}, "INCONCLUSIVE", None),
        ("sessions-11-overdrawn", upd(st=lambda i: _with_text(i["st"], c_rel, "- 0 fresh sessions were consumed",
                                                              "- 11 fresh sessions were consumed")),
         inc_budget, "INCONCLUSIVE", None),
        ("sessions-3-consumed", upd(st=lambda i: _with_text(i["st"], c_rel, "- 0 fresh sessions were consumed",
                                                            "- 3 fresh sessions were consumed")),
         {}, "NOT_SEPARABLE", remaining_is(7)),
        ("sessions-conflict-in-phase", upd(st=lambda i: _with_text(i["st"], s22, "consumed this phase: 0 fresh",
                                                                   "consumed this phase: 2 fresh")),
         inc_budget, "INCONCLUSIVE", None),
        ("sessions-conditional-and-n-of-m", upd(st=lambda i: _with_text(
            i["st"], c_rel, "- 0 fresh sessions were consumed",
            "- 0 fresh sessions were consumed\n2 of 10 fresh sessions were consumed. If this phase consumed 3 fresh "
            "sessions, the cap is exceeded; it would consume 4 fresh sessions.")), {}, "NOT_SEPARABLE",
         remaining_is(10)),
        ("bound-floors-fall", upd(floors=falling), {"V-CT-BOUND": "FAIL"}, "INCONCLUSIVE", None),
        ("consumption-contradiction", upd(rows=rows_with(set_contradiction)), {"V-CT-CONSUMPTION": "FAIL"},
         "INCONCLUSIVE", None),
        ("consumption-delivery-missing", upd(rows=rows_with(drop_delivery)), {}, "NOT_SEPARABLE", cons_unmeasured),
    ]


PURE_CLAUSES = ("V-CT-SOURCES", "V-CT-FISHER-PINS", "V-CT-SESSIONS", "V-CT-BOUND", "V-CT-SEPARATION",
                "V-CT-GRADES-AGREE", "V-CT-AUTH-COMMIT", "V-CT-AUTH-GRADER", "V-CT-AUTH-AUDIT", "V-CT-CONSUMPTION")


def drills(rows, regrade_rows, cap, st, remaining, text_drills=None, fro=None) -> list:
    """[(name, observed, good)]. Each mutant declares its FULL non-ok clause set; every other evaluated
    clause must stay ok and the verdict must match. The clean case is the positive control."""
    out = []
    base = {"rows": rows, "regrade": regrade_rows, "st": st, "fn": fisher_two_sided, "floors": None,
            "remaining": remaining, "fro": fro}
    for name, mut, want, want_v, chk in _drill_specs():
        try:
            inp = mut(base)
        except ValueError as exc:
            out.append((name, f"mutant could not be built ({exc})", False))
            continue
        results, ctx = evaluate_core(inp["rows"], None, inp["regrade"], cap, inp["st"], inp["fn"], inp["floors"])
        stt = {n: s for n, s, _ in results}
        missing = [c for c in PURE_CLAUSES if c not in stt]
        wrong = [f"{c}={stt[c]}(want {want.get(c, 'ok')})" for c in stt if stt[c] != want.get(c, "ok")]
        v = verdict_of(results)
        good = not missing and not wrong and v == want_v
        note = ""
        if chk is not None and ctx["counts"] is not None:
            cg, note = chk(inp, ctx, results)
            good = good and cg
        moved = ",".join(f"{c} {stt[c]}" for c in stt if stt[c] != "ok") or "all ok"
        obs = f"{moved} verdict {v}" + (f" ({note})" if note else "")
        if missing:
            obs += f" MISSING {','.join(missing)}"
        if wrong:
            obs += f" WRONG {';'.join(wrong)}"
        out.append((name, obs, good))
    for name, fn in (text_drills or {}).items():
        status, text = fn()
        out.append((name, f"{status} {text[:80]}", status == "FAIL"))
    return out


# --------------------------------------------------------------------------- render


def sessions_host(rows) -> str:
    ts = [((r.get("metrics") or {}).get("transcript")) for r in rows]
    if ts and all(isinstance(t, str) and t.startswith(LAPTOP_PREFIX) for t in ts):
        return "laptop"
    return "host unknown"


def _counter_text(c: Counter) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted(c.items())) or "-"


def render(rows, regrade_rows, fro, st, outside=(), regrade_outside=()) -> str:
    denoms = fro["denominators"]
    ds = denoms["D-SESSIONS"]
    cap = ds["new_benchmark_cap"]
    info = st["info"]
    results, ctx = evaluate_core(rows, None, regrade_rows, cap, st)
    grades, counts, b = ctx["grades"], ctx["counts"], ctx["bound"]
    if grades is None or b is None:
        raise ValueError("sources or budget refused; nothing to render")
    if info.get("error"):
        raise ValueError(f"pins unreadable: {info['error']}")
    if st.get("commit_msg") is None:
        raise ValueError("regrade add commit message unreadable")
    stored = arm_counts(stored_grades(rows), rows)
    regrade = {g["run_id"]: g["grade"] for g in regrade_rows}
    rule = next(p["rule"] for p in fro["pillars"] if p["id"] == "E")
    commit8 = st["regrade_commit"][:8]
    e_auth, e_stored = max_effect(counts), max_effect(stored)
    for which, e in (("authoritative", e_auth), ("stored", e_stored)):
        if e is None:
            raise ValueError(f"UNMEASURED: the {which} grades leave {CONTROL_ARM} or every treatment arm with 0 "
                             f"measured rows; the evidence states both grade sources, so nothing is rendered")
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
    L.append("## Sources")
    L.append("")
    L.append(f"- rows: `{ROWS_REL}`, the run_id set of its blob at {info['rows_commit']} (the commit that brought it "
             f"to {len(info['rows_blob'])} rows), LF sha256 `{info['rows_sha']}`")
    L.append(f"- regrade: `{REGRADE_REL}`, blob at its add commit {info['regrade_commit'][:8]} "
             f"({len(info['regrade_blob'])} rows), LF sha256 `{info['regrade_sha']}`")
    L.append("- Rows outside the pinned set (not used by the verdict): " + (
        "; ".join(f"{r['run_id']} / {r.get('arm')} / {r.get('grade')}" for r in outside) if outside else "none"))
    L.append("- Regrade rows outside the pinned set (not joined): " + (
        "; ".join(f"{g.get('run_id')} / {g.get('grade')}" for g in regrade_outside) if regrade_outside else "none"))
    L.append("")
    L.append("## Grade authority (why the regrade row wins)")
    L.append("")
    subject = st["commit_msg"].partition("\n")[0]
    _, phrase = _find_line(st["commit_msg"], r"P-r1's amend hid a swallow[^;]*?reflog-aware grader")
    L.append(f"- commit {commit8} added the regrade file; subject: \"{subject}\"; body: \"{phrase}\"")
    gl = [_line_of(st["grader"], m.start()) for m in re.finditer("FAIL-SWALLOW-REPAIRED", st["grader"])]
    L.append(f"- `{DELIVERY_REL}` at {commit8} carries `FAIL-SWALLOW-REPAIRED` on lines {', '.join(map(str, gl))}")
    al, aq = _find_line(st["audit"], r"r1 stored PASS = swallow \+ `--amend`, regrades\s+FAIL-SWALLOW-REPAIRED")
    L.append(f"- `{AUDIT_REL}` line {al}: \"{aq}\"")
    rl, rq = _find_line(st["residency"], r"P-r1 stored PASS = amended shape, regrades\s+FAIL-SWALLOW-REPAIRED")
    L.append(f"- `{RESIDENCY_REL}` line {rl}: \"{rq}\"")
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
    L.append(f"Largest effect against {CONTROL_ARM}: authoritative {frac(e_auth)} ({points(e_auth)} points), "
             f"stored {frac(e_stored)} ({points(e_stored)} points).")
    L.append("")
    L.append(f"## Pairs against {CONTROL_ARM} (authoritative grades, two-sided Fisher exact)")
    L.append("")
    L.append("| arm | effect | points | p | p (4 dp) |")
    L.append("|---|---|---|---|---|")
    for a, e, p in pairs(counts):
        L.append(f"| {a} | {frac(e)} | {points(e)} | {frac(p)} | {dec4(p)} |")
    L.append("")
    L.append("## Sessions (D-SESSIONS)")
    L.append("")
    L.append(f"- frozen D-SESSIONS: new_benchmark_cap {cap}; listing family remaining {ds['listing_family_remaining']} "
             f"of {ds['listing_family_total']}")
    stm = ctx["sessions"]
    for ph in range(1, THIS_PHASE):
        if ph in stm:
            where = "; ".join(f"{p}:{ln}" for p, ln, _ in stm[ph]["where"])
            L.append(f"- phase {ph}: {next(iter(stm[ph]['figures']))} ({where})")
        else:
            L.append(f"- phase {ph}: not stated")
    L.append(f"- consumed_stated {ctx['consumed']}; remaining {ctx['remaining']} (the budget of the bound below)")
    rc = "; ".join(f"line {ln} `{t}`" for ln, t in ctx["runner"])
    L.append(f"- this phase ({THIS_PHASE}): {FRESH_SESSIONS_THIS_PHASE} sessions; this script runs no session. "
             f"`{RUNNER_REL}` at HEAD sets {rc}, so the benchmark cannot run on a POSIX host as committed.")
    L.append("- Unstated phases can only lower the true remaining budget, and a lower budget never lowers the floor "
             "(by construction: a smaller budget's allocations are a subset of a larger one's), so NOT_SEPARABLE at "
             "the stated budget implies NOT_SEPARABLE at the true one.")
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
    L.append(f"Floor: {frac(b['floor'])} ({points(b['floor'])} points), attained at {at}; "
             f"equal-allocation floor {frac(b['equal_floor'])} ({points(b['equal_floor'])} points).")
    L.append("")
    L.append("Floor per budget (non-increasing in the budget by construction, a subset minimum): " + ", ".join(
        f"{bb}: {frac(f)}" for bb, f in sorted(b["floors"].items())))
    L.append("")
    tf, tat = topup_floor(counts, b["budget"])
    if tf is not None:
        tv = ", ".join(f"the {w} effect {frac(e)} gives {separation_verdict(e, tf)}"
                       for w, e in (("authoritative", e_auth), ("stored", e_stored)))
        L.append(f"Design space: the floor above is taken over fresh allocations. Topping up the committed arms "
                 f"({CONTROL_ARM} and a treatment arm, as measured) with up to {b['budget']} new sessions of the same "
                 f"protocol gives floor {frac(tf)} ({points(tf)} points) at "
                 f"{', '.join(f'{a} vs {t}' for a, t in tat)} ({CONTROL_ARM} total vs treatment total); against it "
                 f"{tv}.")
        L.append("")
    L.append(f"verdict: {verdict_of(results)} (largest committed effect {frac(e_auth)}, floor {frac(b['floor'])}; "
             f"under the stored grades {frac(e_stored)}, also {separation_verdict(e_stored, b['floor'])})")
    L.append("")
    L.append("## Result consumption (from the rows' `delivery` and `card_rows` fields)")
    L.append("")
    L.append("| arm | n | listing | skill invoked | skill before the protected commit | card_rows |")
    L.append("|---|---|---|---|---|---|")
    cons = ctx["consumption"]
    for a in arms_of(rows):
        c = cons.get(a)
        if c is None:
            continue
        if c["n"] == 0:
            L.append(f"| {a} | UNMEASURED (0 measured rows) | - | - | - | - |")
            continue
        L.append(f"| {a} | {c['n']} | {_counter_text(c['listing'])} | {c['invoked']} of {c['n']} | "
                 f"{c['before_commit']} of {c['n']} | {_counter_text(c['card_rows'])} |")
    L.append("")
    nc = sum(c["n"] for c in cons.values())
    L.append(f"The delivered capability's output was consumed (a Skill invocation, or a card deny reaching the "
             f"agent) in {sum(c['consumed'] for c in cons.values())} of {nc} measured rows; "
             f"{sum(c['unmeasured'] for c in cons.values())} rows UNMEASURED for consumption.")
    L.append("")
    L.append("n < 5 per arm: no rate estimated, only counts.")
    L.append("")
    L.append("## Figures not derivable from the committed rows (cited, not used by the verdict)")
    L.append("")
    arm_c = denoms.get("D-CARD", {}).get("arm_c")
    cl, cq = _find_line(st["audit"], r"\|[^\n]*C card, fixed[^\n]*")
    L.append(f"- C card fixed, deny mode: frozen `D-CARD.arm_c` = \"{arm_c}\"; `{AUDIT_REL}` line {cl}: \"{cq}\" "
             f"-- no committed row holds it (the {len(info['rows_blob'])} pinned rows hold only the pre-fix C arm); "
             f"not used by the verdict.")
    cf = c_fixed_frozen(arm_c, counts, b)
    if cf is None:
        L.append("  - `D-CARD.arm_c` states no `a/n PASS` figure against a measured control; nothing to judge.")
    else:
        can = ("the budget could separate an effect of this size" if cf["verdict"] == "SEPARABLE"
               else "the budget could not separate it")
        L.append(f"  - judged by the verdict rule used for the committed rows: {cf['passes']}/{cf['n']} PASS against "
                 f"{CONTROL_ARM} {cf['control']['passes']}/{cf['control']['n']} is an effect of {frac(cf['effect'])} "
                 f"({points(cf['effect'])} points), floor {frac(b['floor'])}, so {cf['verdict']}: {can} "
                 f"({needed_text(cf['effect'])}, against new_benchmark_cap {cap}). "
                 f"Rows like these, judged as committed rows, would give the verdict {cf['verdict']}.")
        L.append(f"  - fisher_two_sided({cf['passes']}, {cf['n']}, {cf['control']['passes']}, {cf['control']['n']}) = "
                 f"{frac(cf['p_rows'])}: whether these few rows are significant on their own, which is not what "
                 f"pillar E asks (it asks whether the budget can separate an effect of this size).")
    sl, sq = _find_line(st["residency"], r"\d+/\d+ sessions used")
    L.append(f"- \"{sq}\" (`{RESIDENCY_REL}` line {sl}): the skill-residency program's own budget, not D-SESSIONS; "
             f"not used by the verdict.")
    _, bq = _find_line(st["commit_msg"], r"R loaded the full body \([^)]*\)")
    L.append(f"- \"{bq}\" (commit {commit8} message): no row field records it; not used by the verdict.")
    L.append("")
    L.append("## What a separating benchmark would need (necessary condition, not a power calculation)")
    L.append("")
    for label, eff in (("authoritative effect", e_auth), ("stored-grade effect", e_stored)):
        if eff == 0:
            L.append(f"- {label} 0: no n separates a zero effect.")
        else:
            L.append(f"- {label} {frac(eff)}: {needed_text(eff)}, against new_benchmark_cap {cap}.")
    L.append("- The smallest total is taken over every allocation n1 + n2 (the same most-favourable-design rule as "
             "the floor); the equal allocation is shown beside it.")
    L.append("- This is only the smallest design in which such a table could separate at all; a powered design "
             "(a stated chance of separating when the effect is real) needs more sessions than this.")
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
    dl, _ = _find_line(st["delivery_head"], r"python p3_delivery\.py run --arm")
    L.append(f"(host laptop; shape from the `{DELIVERY_REL}` docstring line {dl}; per-run settings such as arm C's "
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


def default_inputs(git=_git):
    """Working-tree rows and regrade rows restricted to the pinned run_id set, the committed texts.
    When the pins are unreadable no row is judged: the rows cannot be restricted to the pinned set, so
    the verdict clauses read INCONCLUSIVE instead of judging every working-tree row (07-REVIEW WR-04)."""
    rows, refusal = load_rows(REPO / ROWS_REL)
    reg, rrefusal = load_rows(REPO / REGRADE_REL)
    st = static(git)
    rows = rows or []
    reg = reg or []
    if st["info"].get("error"):
        inside, outside, reg_in, reg_out = [], rows, [], reg
        refusal = refusal or rrefusal or (f"pins unreadable ({st['info']['error']}); the rows cannot be "
                                          f"restricted to the pinned set, so none is judged")
    else:
        inside, outside = pinned_split(rows, st["info"])
        reg_in, reg_out = pinned_regrade_split(reg, st["info"])
    return {"rows": inside, "all_rows": rows, "outside": outside, "refusal": refusal or rrefusal,
            "regrade": reg_in, "regrade_outside": reg_out, "st": st}


def _read_wt(rel):
    try:
        return (REPO / rel).read_text(encoding="utf-8")
    except OSError:
        return None


def _render_or_none(inp, fro):
    try:
        return render(inp["rows"], inp["regrade"], fro, inp["st"], inp["outside"],
                      inp.get("regrade_outside", ())), None
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        return None, str(exc)


def run_drills(inp, fro, cap, rendered, remaining, nested=False):
    """(status, why, [(name, observed, good)]). status "refused" when the real sources, the pins, the budget
    or the render are unavailable: the drills did not run, which is INCONCLUSIVE, never FAIL (WR-04)."""
    why = (inp["refusal"] and f"sources refused: {inp['refusal']}") or (
        inp["st"]["info"].get("error") and f"pins unreadable: {inp['st']['info']['error']}") or (
        remaining is None and "no session budget") or (rendered is None and "the evidence could not be rendered")
    if why:
        return "refused", why, []
    if nested:
        return "refused", "nested drill run (a drill re-entered the default path with readable sources)", []
    text_drills = {
        "rows-pinned-wall_s-changed": lambda: clause_rows_pinned_drill(inp["all_rows"], inp["regrade"],
                                                                       inp["st"]["info"]),
        "evidence-one-digit-changed": lambda: clause_evidence_current_drill(rendered),
    }
    all_reg = list(inp["regrade"]) + list(inp.get("regrade_outside", ()))
    return "ran", None, (drills(inp["rows"], inp["regrade"], cap, inp["st"], remaining, text_drills, fro)
                         + [needed_pins_drill()] + append_drills(inp["all_rows"], all_reg, cap, inp["st"])
                         + [git_fails_end_to_end_drill(fro, cap)])


def git_fails_end_to_end_drill(fro, cap):
    """WR-04: the whole default path with a git whose every `git log` fails. Required: V-CT-DRILLS reads
    INCONCLUSIVE "drills not run: ... pins unreadable ...", the verdict clauses read INCONCLUSIVE (no unpinned row is
    judged), no clause reads FAIL, and the verdict is INCONCLUSIVE."""
    inp = default_inputs(_git_fails_log)
    results, _ = default_results(inp, fro, cap, nested=True)
    st = {n: (s, t) for n, s, t in results}
    dr = st.get("V-CT-DRILLS", ("missing", ""))
    fails = [n for n, (s, _) in st.items() if s == "FAIL"]
    verdict_inc = all(st[c][0] == "INCONCLUSIVE" for c in ("V-CT-SOURCES", "V-CT-SEPARATION", "V-CT-GRADES-AGREE"))
    good = (dr[0] == "INCONCLUSIVE" and dr[1].startswith("drills not run: ") and "pins unreadable" in dr[1]
            and not fails and verdict_inc
            and verdict_of(results) == "INCONCLUSIVE")
    return ("git-log-fails-end-to-end", f"V-CT-DRILLS {dr[0]}, FAIL lines {fails or 'none'}, verdict clauses "
                                        f"{'INCONCLUSIVE' if verdict_inc else 'judged'}, verdict {verdict_of(results)}",
            good)


def append_drills(all_rows, all_reg, cap, st):
    """WR-02: the owning workstream appends one run and its regrade row (as 713b02a7 did for N0/R/P):
    every clause must stay ok. A regrade row naming no row at all must still make V-CT-ROWS-PINNED fail."""
    info, out = st["info"], []
    base_out = len(pinned_regrade_split(all_reg, info)[1])
    new = copy.deepcopy(all_rows[0])
    new.update(run_id="X-appended-C-r3", arm="C", rep=3, grade=PASS_GRADE)
    cases = (("append-row-and-regrade", all_rows + [new],
              all_reg + [{"run_id": new["run_id"], "regraded_by": "reflog-aware grader", "grade": PASS_GRADE}], "ok"),
             ("regrade-orphan-outside-pin", all_rows, all_reg + [{"run_id": "X-ghost-r9", "grade": PASS_GRADE}],
              "FAIL"))
    for name, rows2, reg2, want in cases:
        inside, outside = pinned_split(rows2, info)
        reg_in, reg_out = pinned_regrade_split(reg2, info)
        results, _ = evaluate_core(inside, None, reg_in, cap, st)
        rp = clause_rows_pinned(rows2, reg_in, info, reg_out)
        bad = [f"{n} {s_}" for n, s_, _ in results if s_ != "ok"]
        good = not bad and verdict_of(results) == "NOT_SEPARABLE" and rp[0] == want and len(reg_out) == base_out + 1
        out.append((name, f"{'verdict clauses all ok' if not bad else ','.join(bad)}, verdict {verdict_of(results)}; "
                          f"V-CT-ROWS-PINNED {rp[0]} (want {want}); outside: {len(outside)} rows, "
                          f"{len(reg_out)} regrade rows", good))
    return out


def needed_pins_drill():
    """WR-01 pin: needed_total reproduces NEEDED_PINS, and an equal-allocation-only answer (2 x needed_k)
    would differ from the pin for 1/2 (the pin can tell the two rules apart)."""
    bad, notes = [], []
    for eff, tot, at, k in NEEDED_PINS:
        got, gk = needed_total(eff), needed_k(eff)
        if got is None or got[0] != tot or tuple(got[1]) != at or gk != k:
            bad.append(f"{frac(eff)}: needed_total {got}, needed_k {gk}, pinned {tot} {at} k {k}")
        notes.append(f"{frac(eff)} -> total {tot} {'/'.join(f'({a},{b})' for a, b in at)}, equal {2 * k}")
    half = NEEDED_PINS[0]
    if 2 * half[3] == half[1]:
        bad.append("pin cannot tell the equal-only rule from the all-allocation rule")
    # IN-03 pin (reviewer's factorial-form recomputation): 2 + 2 committed rows topped up within 10 sessions.
    tf, tat = topup_floor({CONTROL_ARM: {"n": 2, "passes": 0}, "P": {"n": 2, "passes": 0}}, 10)
    want_at = [(5, 7), (5, 8), (5, 9), (7, 5), (8, 5), (9, 5)]
    if tf != Fraction(3, 5) or tat != want_at:
        bad.append(f"topup 2+2 within 10: floor {frac(tf)} at {tat}, pinned 3/5 at {want_at}")
    notes.append("topup 2+2 within 10 -> 3/5")
    obs = ("pins reproduced: " + "; ".join(notes)) if not bad else "WRONG " + "; ".join(bad)
    return ("needed-total-pins", obs, not bad)


def default_results(inp, fro, cap, nested=False):
    results, ctx = evaluate_core(inp["rows"], inp["refusal"], inp["regrade"], cap, inp["st"])
    results.append(("V-CT-ROWS-PINNED",) + clause_rows_pinned(inp["all_rows"], inp["regrade"], inp["st"]["info"],
                                                             inp.get("regrade_outside", ())))
    rendered, why = _render_or_none(inp, fro)
    if rendered is None:
        results.append(("V-CT-EVIDENCE-CURRENT", "INCONCLUSIVE", f"cannot render: {why}"))
    else:
        results.append(("V-CT-EVIDENCE-CURRENT",) + clause_evidence_current(
            _read_wt(EVIDENCE_REL), git_text(f"HEAD:{EVIDENCE_REL}"), rendered))
    status, why, d = run_drills(inp, fro, cap, rendered, ctx["remaining"], nested)
    subs = "".join(f"\n    drill {n}: {o}{'' if g else ' <-- WRONG'}" for n, o, g in d)
    if status == "refused":
        results.append(("V-CT-DRILLS", "INCONCLUSIVE", f"drills not run: {why}"))
    elif all(g for *_, g in d):
        results.append(("V-CT-DRILLS", "ok", f"{len(d)} drills, clean case all ok, each mutant moved exactly "
                                             f"its declared clauses" + subs))
    else:
        results.append(("V-CT-DRILLS", "FAIL", "a drill did not behave as required" + subs))
    return results, ctx


def derived_json(inp, fro, cap) -> dict:
    results, ctx = default_results(inp, fro, cap)
    rows, b, st = inp["rows"], ctx["bound"], inp["st"]
    counts = ctx["counts"] or {}
    stored = arm_counts(stored_grades(rows), rows)
    out = {"verdict": verdict_of(results),
           "clauses": {n: s for n, s, _ in results},
           "arms": {a: {"authoritative": counts.get(a), "stored": stored.get(a)} for a in arms_of(rows)},
           "effects": {k: ("UNMEASURED" if e is None else frac(e))
                       for k, e in (("authoritative", max_effect(counts)), ("stored", max_effect(stored)))},
           "max_n2_effect_p": frac(fisher_two_sided(2, 2, 0, 2)),
           "alpha": frac(ALPHA)}
    if b is not None:
        out["floors"] = {"all_allocation": frac(b["floor"]), "all_allocation_at": [list(k) for k in b["floor_at"]],
                         "equal_allocation": frac(b["equal_floor"]),
                         "equal": {str(k): (frac(ms[0]) if ms else None) for k, ms in b["equal"]},
                         "per_budget": {str(k): frac(v) for k, v in sorted(b["floors"].items())}}
    ds = fro["denominators"]["D-SESSIONS"]
    out["budget"] = {"new_benchmark_cap": cap, "consumed_stated": ctx["consumed"], "remaining": ctx["remaining"],
                     "this_phase": FRESH_SESSIONS_THIS_PHASE,
                     "listing_family_remaining": ds["listing_family_remaining"],
                     "listing_family_total": ds["listing_family_total"]}
    stm = ctx["sessions"] or {}
    out["sessions"] = {str(p): ({"figure": next(iter(stm[p]["figures"])),
                                 "where": [f"{w[0]}:{w[1]}" for w in stm[p]["where"]]} if p in stm else "not stated")
                       for p in range(1, THIS_PHASE)}
    out["consumption"] = {a: {"n": c["n"], "unmeasured": c["unmeasured"], "listing": dict(c["listing"]),
                              "skill_invoked": c["invoked"], "skill_before_commit": c["before_commit"],
                              "card_rows": dict(c["card_rows"]), "consumed": c["consumed"]}
                          for a, c in sorted(ctx["consumption"].items())}
    ea, es = max_effect(counts) if counts else None, max_effect(stored)
    out["needed_k"] = {"authoritative": needed_k(ea), "stored": needed_k(es)}
    if b is not None:
        tf, tat = topup_floor(ctx["counts"], b["budget"])
        out["topup"] = None if tf is None else {
            "floor": frac(tf), "at": [list(k) for k in tat],
            "authoritative_verdict": None if ea is None else separation_verdict(ea, tf),
            "stored_verdict": None if es is None else separation_verdict(es, tf)}

    def _nt(e):
        nt = needed_total(e)
        return None if nt is None else {"total": nt[0], "at": [list(x) for x in nt[1]]}
    out["needed_total"] = {"authoritative": _nt(ea), "stored": _nt(es)}
    cf = c_fixed_frozen(fro["denominators"].get("D-CARD", {}).get("arm_c"), ctx["counts"], b)
    out["c_fixed_frozen"] = None if cf is None else {
        "passes": cf["passes"], "n": cf["n"], "control": f"{cf['control']['passes']}/{cf['control']['n']}",
        "effect": frac(cf["effect"]), "verdict": cf["verdict"], "needed_k": cf["needed_k"],
        "needed_total": _nt(cf["effect"]), "p_rows": frac(cf["p_rows"]), "committed_row": False}
    info = st["info"]
    out["pins"] = {"rows_commit": info["rows_commit"], "rows_blob_sha256": info["rows_sha"],
                   "regrade_add_commit": st["regrade_commit"], "regrade_blob_sha256": info["regrade_sha"]}
    out["sessions_host"] = sessions_host(rows)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jsonl", help="evaluate the verdict clauses on this rows file only")
    ap.add_argument("--regrade", help="regrade file joined to --jsonl (default under --jsonl: none)")
    ap.add_argument("--drills", action="store_true", help="print the in-process mutant drills")
    ap.add_argument("--json", action="store_true", help="print the derived figures as JSON")
    ap.add_argument("--write-evidence", action="store_true", help=f"render {EVIDENCE_REL}")
    args = ap.parse_args(argv)
    try:
        fro = frozen()
        cap = fro["denominators"]["D-SESSIONS"]["new_benchmark_cap"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"CT_VERDICT=COULD_NOT_RUN frozen ledger unreadable: {exc}")
        return 2
    if args.jsonl:
        rows, refusal = load_rows(args.jsonl)
        reg, rref = (load_rows(args.regrade) if args.regrade else ([], None))
        print(f"  (rows {args.jsonl}; regrade {args.regrade or 'none: stored grades only'})")
        results, _ = evaluate_core(rows or [], refusal or rref, reg or [], cap, static(), verdict_only=True)
        return emit(results)
    inp = default_inputs()
    if args.json:
        dj = derived_json(inp, fro, cap)
        print(json.dumps(dj, indent=1, sort_keys=True))
        return 0 if dj["verdict"] == "NOT_SEPARABLE" else 1
    if args.drills:
        rendered, _ = _render_or_none(inp, fro)
        _, ctx = evaluate_core(inp["rows"], inp["refusal"], inp["regrade"], cap, inp["st"])
        status, why, d = run_drills(inp, fro, cap, rendered, ctx["remaining"])
        if status == "refused":
            print(f"  INCONCLUSIVE drills not run: {why}")
            return 1
        for name, obs, good in d:
            print(f"    drill {name}: {obs}{'' if good else ' <-- WRONG'}")
        return 0 if all(g for *_, g in d) else 1
    if args.write_evidence:
        if inp["refusal"]:
            print(f"cannot render: {inp['refusal']}")
            return 1
        text, why = _render_or_none(inp, fro)
        if text is None:
            print(f"cannot render: {why}")
            return 1
        out = REPO / EVIDENCE_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {EVIDENCE_REL} ({len(text)} chars)")
        return 0
    results, _ = default_results(inp, fro, cap)
    return emit(results)


if __name__ == "__main__":
    sys.exit(main())
