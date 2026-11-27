#!/usr/bin/env python3
"""check_evidence.py -- phase-local checker for 01-EVIDENCE.md (perf-construction, Phase 1).

A verification fixture, NOT a product module: standard library only, registered
nowhere, written only inside the phase directory. It exists because no existing
owner parses a markdown status table or resolves path:line citations
(tools/claim_evidence.py certifies a command's JSON values; tools/evidence_bundle.py
runs V-gate commands into receipts). The BUILD-reason is recorded in 01-EVIDENCE.md.

    python3 -I check_evidence.py EVIDENCE.md --repo REPO_ROOT --stage STAGE
            [--require-judged P01,P03,...] [--selftest]

STAGE is cumulative and ordered: tracer < pids < owners < d1 < final.
Prints one `FAIL: V-EVD-n: message` line per violation and a last line
`CHECK_EVIDENCE stage=<stage> violations=<n>`; exit 0 only when n is 0.

--selftest builds in-memory mutants of the evidence text and requires the SAME
stage to reject each one with the violation code that mutant is designed to
trip. A self-test that exercises nothing (fewer than 4 mutants run) fails.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

STAGES = ["tracer", "pids", "owners", "d1", "final"]
HEADINGS = [
    "## 1. P-id table (P01-P40)",
    "## 2. Owners (UCR-CIF, Constitutive Baseline Ratchet)",
    "## 3. D1 decision",
    "## 4. Unavailable inputs",
    "## 5. Searches (instrument records)",
    "## 6. Code-reading observations not mapped to a P-id",
    "## 7. LAPTOP-ONLY procedures",
    "## 8. Phase verdict",
]
STATUSES = [
    "CONFIRMED_ACTIVE", "HISTORICAL_FIXED", "PARTIALLY_FIXED", "SUPERSEDED",
    "FALSIFIED", "UNKNOWN", "NOT_APPLICABLE", "LAPTOP-ONLY",
]
PID_HEADER = "| P-id | Definition source | Status | Evidence | Owner file | Consumed by |"
SEARCH_HEADER = "| ID | Command | Exit | Hits | Positive control | Control hits |"
PENDING = ("UNSURVEYED", "UNREAD")
D1_OPTIONS = ["EXTEND trace_context", "EXTEND capability_runtime", "BUILD", "UNDECIDED"]
PIDS = [f"P{n:02d}" for n in range(1, 41)]

CITE_RE = re.compile(
    r"(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_./\-]+\.[A-Za-z][A-Za-z0-9]*):(\d+)(?:-(\d+))?(?![A-Za-z0-9_])")
SID_RE = re.compile(r"\bS-\d{2,}\b")
LPID_RE = re.compile(r"\bLP-\d{2,}\b")
PIPE_RE = re.compile(r"(?<!\\)\|")


def stage_ge(stage: str, other: str) -> bool:
    return STAGES.index(stage) >= STAGES.index(other)


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in PIPE_RE.split(s)]


class Doc:
    def __init__(self, text: str):
        self.text = text
        self.lines = text.splitlines()
        self.head_idx: list[int | None] = []
        pos = 0
        for h in HEADINGS:
            found = None
            for i in range(pos, len(self.lines)):
                if self.lines[i].strip() == h:
                    found = i
                    break
            self.head_idx.append(found)
            if found is not None:
                pos = found + 1
        self.heading_ok = all(i is not None for i in self.head_idx)
        self.sections: dict[int, list[str]] = {}
        order = [(i, k + 1) for k, i in enumerate(self.head_idx) if i is not None]
        for j, (i, sec) in enumerate(order):
            end = order[j + 1][0] if j + 1 < len(order) else len(self.lines)
            self.sections[sec] = self.lines[i + 1:end]
        first = min((i for i in self.head_idx if i is not None), default=len(self.lines))
        self.header_block = self.lines[:first]

    def table(self, sec: int, header: str) -> list[list[str]]:
        rows: list[list[str]] = []
        inside = False
        for ln in self.sections.get(sec, []):
            if not inside:
                if ln.strip() == header:
                    inside = True
                continue
            if not ln.strip().startswith("|"):
                if ln.strip() == "":
                    continue
                break
            cells = split_row(ln)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
        return rows

    def table_present(self, sec: int, header: str) -> bool:
        return any(ln.strip() == header for ln in self.sections.get(sec, []))


class Repo:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self._lc: dict[str, int | None] = {}

    def line_count(self, rel: str) -> int | None:
        if rel in self._lc:
            return self._lc[rel]
        n: int | None = None
        try:
            if rel.startswith("/") or ".." in Path(rel).parts:
                n = None
            else:
                p = (self.root / rel).resolve()
                if (p == self.root or self.root in p.parents) and p.is_file():
                    n = len(p.read_bytes().decode("utf-8", "replace").splitlines())
        except OSError:
            n = None
        self._lc[rel] = n
        return n

    def exists(self, rel: str) -> bool:
        try:
            if rel.startswith("/") or ".." in Path(rel).parts:
                return False
            p = (self.root / rel).resolve()
            return (p == self.root or self.root in p.parents) and p.exists()
        except OSError:
            return False

    def resolves(self, path: str, a: int, b: int | None) -> bool:
        n = self.line_count(path)
        if n is None:
            return False
        end = a if b is None else b
        return 1 <= a <= end <= n


def citations(text: str) -> list[tuple[str, int, int | None, str]]:
    out = []
    for m in CITE_RE.finditer(text):
        a = int(m.group(2))
        b = int(m.group(3)) if m.group(3) else None
        out.append((m.group(1), a, b, m.group(0)))
    return out


def resolving(repo: Repo, text: str) -> tuple[int, list[str]]:
    ok, bad = 0, []
    for path, a, b, raw in citations(text):
        if repo.resolves(path, a, b):
            ok += 1
        else:
            bad.append(raw)
    return ok, bad


def closed_sections(stage: str) -> set[int]:
    return {
        "tracer": set(), "pids": {1}, "owners": {1, 2}, "d1": {1, 2, 3},
        "final": {1, 2, 3, 4, 5, 6, 7, 8},
    }[stage]


def check(text: str, repo: Repo, stage: str, require_judged: list[str]) -> list[tuple[str, str]]:
    v: list[tuple[str, str]] = []

    def fail(code: str, msg: str) -> None:
        v.append((code, msg))

    doc = Doc(text)

    # V-EVD-1
    for h, i in zip(HEADINGS, doc.head_idx):
        if i is None:
            fail("V-EVD-1", f"heading missing or out of order: {h}")
    present = [ln.strip() for ln in doc.lines if ln.startswith("## ")]
    if doc.heading_ok and present != HEADINGS:
        fail("V-EVD-1", "unexpected extra or reordered level-2 heading")

    # ---- section 5 (parsed first: other checks cite S ids)
    s_ids: dict[str, list[str]] = {}
    if not doc.table_present(5, SEARCH_HEADER):
        fail("V-EVD-1", "section 5 table header missing or not exact")
    for cells in doc.table(5, SEARCH_HEADER):
        if len(cells) != 6:
            fail("V-EVD-9", f"section 5 row has {len(cells)} cells, need 6: {cells[:1]}")
            continue
        sid, _cmd, exit_c, hits_c, _pc, ctl = cells
        if not re.fullmatch(r"S-\d{2,}", sid):
            fail("V-EVD-9", f"search id malformed: {sid!r}")
            continue
        if sid in s_ids:
            fail("V-EVD-9", f"search id reused: {sid}")
        s_ids[sid] = cells
        if not re.fullmatch(r"-?\d+", exit_c) or not re.fullmatch(r"\d+", hits_c):
            fail("V-EVD-9", f"{sid}: Exit and Hits must be integers (got {exit_c!r}, {hits_c!r})")
            continue
        if int(hits_c) == 0:
            if not re.fullmatch(r"\d+", ctl) or int(ctl) < 1:
                fail("V-EVD-9", f"{sid}: zero-hit search needs Control hits >= 1 (got {ctl!r})")
        else:
            if not (ctl == "n/a" or re.fullmatch(r"\d+", ctl)):
                fail("V-EVD-9", f"{sid}: Control hits must be an integer or n/a (got {ctl!r})")

    # ---- section 7 LP ids
    lp_ok: set[str] = set()
    for ln in doc.sections.get(7, []):
        ids = LPID_RE.findall(ln)
        if ids and "procedure:" in ln and "falsifier:" in ln:
            lp_ok.update(ids[:1])

    # ---- section 1
    rows: dict[str, list[str]] = {}
    if not doc.table_present(1, PID_HEADER):
        fail("V-EVD-1", "section 1 table header missing or not exact")
    seen: list[str] = []
    for cells in doc.table(1, PID_HEADER):
        if len(cells) != 6:
            fail("V-EVD-2", f"section 1 row has {len(cells)} cells, need 6: {cells[:1]}")
            continue
        pid = cells[0]
        seen.append(pid)
        if pid in rows:
            fail("V-EVD-2", f"{pid} appears more than once")
        rows[pid] = cells
    for pid in PIDS:
        if pid not in rows:
            fail("V-EVD-2", f"{pid} missing from section 1")
    for pid in seen:
        if pid not in PIDS:
            fail("V-EVD-2", f"unexpected id in section 1: {pid!r}")

    judged_count = 0
    for pid in PIDS:
        if pid not in rows:
            continue
        _, definition, status, evidence, _owner, _cons = rows[pid]
        # V-EVD-3
        if status not in STATUSES:
            fail("V-EVD-3", f"{pid}: status {status!r} is not one of the eight allowed terms")
        undefined = definition.startswith("DEFINITION_NOT_FOUND") or definition.startswith("UNSURVEYED")
        # V-EVD-4
        if definition.startswith("UNSURVEYED"):
            if stage != "tracer":
                fail("V-EVD-4", f"{pid}: UNSURVEYED definition is only accepted at stage tracer")
        elif not definition.startswith("DEFINITION_NOT_FOUND"):
            ok, bad = resolving(repo, definition)
            if ok < 1:
                fail("V-EVD-4", f"{pid}: definition cell has no resolving citation and is not DEFINITION_NOT_FOUND")
        # V-EVD-5
        if undefined and status != "UNKNOWN":
            fail("V-EVD-5", f"{pid}: definition not found on this host but status is {status} (no invention)")
        if status != "UNKNOWN" and status in STATUSES:
            judged_count += 1
            if status == "LAPTOP-ONLY":
                ids = LPID_RE.findall(evidence)
                if not any(i in lp_ok for i in ids):
                    fail("V-EVD-6", f"{pid}: LAPTOP-ONLY needs an LP-nn defined in section 7 with procedure: and falsifier:")
            else:
                ok, _bad = resolving(repo, evidence)
                if ok < 1:
                    fail("V-EVD-6", f"{pid}: status {status} has no resolving citation in the Evidence cell")
        # V-EVD-8
        if stage_ge(stage, "pids"):
            if status == "UNKNOWN":
                ids = [i for i in SID_RE.findall(evidence) if i in s_ids]
                if not ids:
                    fail("V-EVD-8", f"{pid}: UNKNOWN row cites no existing S-nn search id")
    if stage == "tracer" and judged_count < 1:
        fail("V-EVD-6", "tracer needs at least one row with a status other than UNKNOWN")

    # V-EVD-7: every citation outside section-5 command cells must resolve
    scan: list[tuple[str, str]] = [("header", ln) for ln in doc.header_block]
    for sec in (1, 2, 3, 4, 6, 7, 8):
        scan += [(f"section {sec}", ln) for ln in doc.sections.get(sec, [])]
    for ln in doc.sections.get(5, []):
        if ln.strip().startswith("|") and ln.strip() != SEARCH_HEADER:
            cells = split_row(ln)
            if len(cells) == 6:
                cells[1] = ""
                ln = " | ".join(cells)
        scan.append(("section 5", ln))
    for where, ln in scan:
        for path, a, b, raw in citations(ln):
            if not repo.resolves(path, a, b):
                fail("V-EVD-7", f"{where}: citation does not resolve: {raw}")

    # pending tokens in closed sections
    for sec in sorted(closed_sections(stage)):
        for ln in doc.sections.get(sec, []):
            for tok in PENDING:
                if re.search(rf"\b{tok}\b", ln):
                    fail("V-EVD-8", f"section {sec}: pending token {tok} in a closed section")
                    break
    if stage == "final":
        for ln in doc.header_block:
            for tok in PENDING:
                if re.search(rf"\b{tok}\b", ln):
                    fail("V-EVD-13", f"header: pending token {tok} at stage final")

    # V-EVD-10
    for pid in require_judged:
        if pid not in rows:
            fail("V-EVD-10", f"{pid}: required-judged id has no row")
        elif rows[pid][2] == "UNKNOWN":
            fail("V-EVD-10", f"{pid}: required to be judged but status is UNKNOWN")

    # key lines for the tracer; V-EVD-11..14 for later stages
    sec2 = doc.sections.get(2, [])
    sec3 = doc.sections.get(3, [])
    sec4 = doc.sections.get(4, [])
    ucr = [ln for ln in sec2 if ln.startswith("UCR-CIF owner:")]
    rat = [ln for ln in sec2 if ln.startswith("Constitutive Baseline Ratchet owner:")]
    d1l = [ln for ln in sec3 if ln.startswith("D1 decision:")]
    ite = [ln for ln in sec4 if "iteracion-avanzada-universal.txt" in ln]
    if stage == "tracer":
        if not ucr:
            fail("V-EVD-11", "tracer: section 2 lacks a 'UCR-CIF owner:' line")
        if not d1l:
            fail("V-EVD-12", "tracer: section 3 lacks a 'D1 decision:' line")
        if not ite:
            fail("V-EVD-13", "tracer: section 4 lacks a line naming iteracion-avanzada-universal.txt")

    if stage_ge(stage, "owners"):
        for label, lines in (("UCR-CIF owner:", ucr), ("Constitutive Baseline Ratchet owner:", rat)):
            if not lines:
                fail("V-EVD-11", f"section 2 lacks a '{label}' line")
                continue
            val = lines[0][len(label):].strip().replace("`", "")
            m = re.match(r"^(\S+)\s*\(basis:\s*(NAME_IN_HEADER|NAME_IN_SPEC|FUNCTION_ONLY)\)", val)
            if m:
                if not repo.exists(m.group(1)):
                    fail("V-EVD-11", f"{label} path does not exist: {m.group(1)}")
            elif val.startswith("NOT FOUND"):
                ids = [i for i in SID_RE.findall(val) if i in s_ids]
                if not ids:
                    fail("V-EVD-11", f"{label} NOT FOUND must cite an existing S-nn search id")
            else:
                fail("V-EVD-11", f"{label} value must be 'PATH (basis: ...)' or 'NOT FOUND ... S-nn' (got {val[:60]!r})")

    if stage_ge(stage, "d1"):
        if not d1l:
            fail("V-EVD-12", "section 3 lacks a 'D1 decision:' line")
        else:
            val = d1l[0][len("D1 decision:"):].strip().replace("`", "")
            hit = [o for o in D1_OPTIONS if val == o or val.startswith(o + " ") or val.startswith(o + ".")
                   or val.startswith(o + "(")]
            # EXTEND trace_context must not shadow EXTEND capability_runtime etc.: exact-prefix match above.
            if len(hit) != 1:
                fail("V-EVD-12", f"D1 decision must be exactly one of {D1_OPTIONS} (got {val[:50]!r})")
            reason = [ln for ln in sec3 if ln.startswith("D1 reason:")]
            fals = [ln for ln in sec3 if ln.startswith("Falsifier:")]
            if not reason or not reason[0][len("D1 reason:"):].strip():
                fail("V-EVD-12", "section 3 lacks a non-empty 'D1 reason:' line")
            if not fals or not fals[0][len("Falsifier:"):].strip():
                fail("V-EVD-12", "section 3 lacks a non-empty 'Falsifier:' line")
            sec3_text = "\n".join(sec3)
            ids = {i for i in SID_RE.findall(sec3_text) if i in s_ids}
            if len(ids) < 2:
                fail("V-EVD-12", "section 3 must cite at least two distinct existing S-nn ids")
            if hit == ["BUILD"]:
                r = reason[0] if reason else ""
                if "EXTEND fails" not in r or "CONNECT fails" not in r:
                    fail("V-EVD-12", "BUILD needs 'EXTEND fails' and 'CONNECT fails' in D1 reason")

    if stage == "final":
        unav = [ln for ln in ite if "UNAVAILABLE" in ln and any(i in s_ids for i in SID_RE.findall(ln))]
        if not unav:
            fail("V-EVD-13", "section 4 must say UNAVAILABLE for iteracion-avanzada-universal.txt and cite an existing S-nn")
        sec8 = "\n".join(doc.sections.get(8, []))
        m = re.search(r"Phase 1 verdict:\s*(COMPLETE_WITH_UNKNOWNS|COMPLETE|BLOCKED)\b", sec8)
        if not m:
            fail("V-EVD-14", "section 8 lacks 'Phase 1 verdict:' with COMPLETE, COMPLETE_WITH_UNKNOWNS or BLOCKED")
        counts = {s: sum(1 for r in rows.values() if r[2] == s) for s in STATUSES}
        sc = re.search(r"Status counts:(.*)", sec8)
        if not sc:
            fail("V-EVD-14", "section 8 lacks a 'Status counts:' line")
        else:
            pairs = re.findall(r"([A-Z][A-Z_\-]+)\s*=\s*(\d+)", sc.group(1))
            got = {k: int(n) for k, n in pairs}
            if sorted(got) != sorted(STATUSES) or len(pairs) != 8:
                fail("V-EVD-14", "'Status counts:' must list exactly the eight status terms")
            else:
                if sum(got.values()) != 40:
                    fail("V-EVD-14", f"status counts sum to {sum(got.values())}, need 40")
                for s in STATUSES:
                    if got[s] != counts[s]:
                        fail("V-EVD-14", f"status count for {s} is {got[s]} but the table has {counts[s]}")
        if m and m.group(1) == "COMPLETE" and counts["UNKNOWN"] > 0:
            fail("V-EVD-14", "verdict is plain COMPLETE while UNKNOWN rows exist (UNKNOWN is never PASS)")
    return v


# --------------------------------------------------------------------------- selftest
def _replace_cell(line: str, idx: int, new: str) -> str:
    cells = split_row(line)
    cells[idx] = new
    return "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"


def _row_lines(text: str, header: str) -> list[int]:
    lines = text.splitlines()
    out, inside = [], False
    for i, ln in enumerate(lines):
        if not inside:
            if ln.strip() == header:
                inside = True
            continue
        if not ln.strip().startswith("|"):
            if ln.strip() == "":
                continue
            break
        cells = split_row(ln)
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        out.append(i)
    return out


def mutants(text: str, stage: str) -> list[tuple[str, str, str | None]]:
    """(name, expected V-EVD code, mutated text or None when not applicable)."""
    lines = text.splitlines()
    nl = "\n"
    out: list[tuple[str, str, str | None]] = []
    p_rows = _row_lines(text, PID_HEADER)

    def with_lines(new: list[str]) -> str:
        return nl.join(new) + nl

    judged = [i for i in p_rows if split_row(lines[i])[2] not in ("UNKNOWN",)]
    # (a) invalid status on a judged row
    if judged:
        l2 = list(lines)
        l2[judged[0]] = _replace_cell(l2[judged[0]], 2, "MAYBE_FIXED")
        out.append(("a_invalid_status", "V-EVD-3", with_lines(l2)))
    else:
        out.append(("a_invalid_status", "V-EVD-3", None))
    # (b) a resolving citation pushed past EOF
    done = False
    for i in judged:
        cells = split_row(lines[i])
        m = CITE_RE.search(cells[3])
        if m:
            cells[3] = cells[3][:m.start(2)] + "99999" + cells[3][m.end(2):]
            l2 = list(lines)
            l2[i] = "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"
            out.append(("b_bad_line_number", "V-EVD-6", with_lines(l2)))
            done = True
            break
    if not done:
        out.append(("b_bad_line_number", "V-EVD-6", None))
    # (c) invented status on an undefined row
    done = False
    for i in p_rows:
        cells = split_row(lines[i])
        if cells[1].startswith(("DEFINITION_NOT_FOUND", "UNSURVEYED")):
            l2 = list(lines)
            l2[i] = _replace_cell(l2[i], 2, "CONFIRMED_ACTIVE")
            out.append(("c_invented_status", "V-EVD-5", with_lines(l2)))
            done = True
            break
    if not done:
        out.append(("c_invented_status", "V-EVD-5", None))
    # (d) delete a row
    if len(p_rows) > 20:
        l2 = [ln for j, ln in enumerate(lines) if j != p_rows[19]]
        out.append(("d_row_deleted", "V-EVD-2", with_lines(l2)))
    else:
        out.append(("d_row_deleted", "V-EVD-2", None))
    # (e) zero-hit search with a zero control
    s_rows = _row_lines(text, SEARCH_HEADER)
    done = False
    for i in s_rows:
        cells = split_row(lines[i])
        if len(cells) == 6 and cells[3] == "0":
            l2 = list(lines)
            l2[i] = _replace_cell(l2[i], 5, "0")
            out.append(("e_zero_hit_zero_control", "V-EVD-9", with_lines(l2)))
            done = True
            break
    if not done:
        out.append(("e_zero_hit_zero_control", "V-EVD-9", None))
    # (f) ratchet owner replaced by a path that does not exist
    if stage_ge(stage, "owners"):
        l2 = list(lines)
        idx = next((j for j, ln in enumerate(l2) if ln.startswith("Constitutive Baseline Ratchet owner:")), None)
        if idx is not None:
            if "NOT FOUND" in l2[idx]:
                l2[idx] = "Constitutive Baseline Ratchet owner: NOT FOUND (S-99)"
            else:
                l2[idx] = "Constitutive Baseline Ratchet owner: no/such/path_zzz.py (basis: FUNCTION_ONLY)"
            out.append(("f_ratchet_path_missing", "V-EVD-11", with_lines(l2)))
        else:
            out.append(("f_ratchet_path_missing", "V-EVD-11", None))
    else:
        out.append(("f_ratchet_path_missing", "V-EVD-11", None))
    # (g) invalid D1 decision
    if stage_ge(stage, "d1"):
        l2 = list(lines)
        idx = next((j for j, ln in enumerate(l2) if ln.startswith("D1 decision:")), None)
        if idx is not None:
            l2[idx] = "D1 decision: MAYBE_EXTEND"
            out.append(("g_invalid_d1", "V-EVD-12", with_lines(l2)))
        else:
            out.append(("g_invalid_d1", "V-EVD-12", None))
    else:
        out.append(("g_invalid_d1", "V-EVD-12", None))
    # (h) plain COMPLETE while an UNKNOWN row exists
    has_unknown = any(split_row(lines[i])[2] == "UNKNOWN" for i in p_rows)
    if stage == "final" and has_unknown:
        l2 = [re.sub(r"Phase 1 verdict:\s*\S+", "Phase 1 verdict: COMPLETE", ln) for ln in lines]
        out.append(("h_complete_with_unknown", "V-EVD-14", with_lines(l2)))
    else:
        out.append(("h_complete_with_unknown", "V-EVD-14", None))
    return out


def run_selftest(text: str, repo: Repo, stage: str, require: list[str]) -> int:
    base = check(text, repo, stage, require)
    if base:
        print("SELFTEST base text is not clean; mutants cannot be judged")
        print("SELFTEST executed=0 accepted_mutants=0")
        return 1
    executed = accepted = 0
    for name, code, mut in mutants(text, stage):
        if mut is None:
            print(f"SELFTEST mutant={name} rejected=not_applicable")
            continue
        got = check(mut, repo, stage, require)
        hit = any(c == code or (name == "b_bad_line_number" and c in ("V-EVD-4", "V-EVD-6", "V-EVD-7")) for c, _ in got)
        executed += 1
        if hit:
            print(f"SELFTEST mutant={name} rejected=yes")
        else:
            accepted += 1
            print(f"SELFTEST mutant={name} rejected=no")
    print(f"SELFTEST executed={executed} accepted_mutants={accepted}")
    return 1 if (accepted > 0 or executed < 4) else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("evidence")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--stage", choices=STAGES, required=True)
    ap.add_argument("--require-judged", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    text = Path(a.evidence).read_text(encoding="utf-8")
    repo = Repo(a.repo)
    req = [x.strip() for x in a.require_judged.split(",") if x.strip()]
    viol = check(text, repo, a.stage, req)
    for code, msg in viol:
        print(f"FAIL: {code}: {msg}")
    print(f"CHECK_EVIDENCE stage={a.stage} violations={len(viol)}")
    rc = 0 if not viol else 1
    if a.selftest:
        rc = max(rc, run_selftest(text, repo, a.stage, req))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
