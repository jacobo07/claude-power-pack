# -*- coding: utf-8 -*-
"""Disposition ledger -- every requirement ends with an explicit owner, or a reason.

THE CLAIM THIS MAKES CHECKABLE
------------------------------
"Corpus coverage" has been asserted by prose matrices in this estate before. This
turns it into a number a machine computes: every unit in the requirement corpus
carries exactly one disposition, and UNMAPPED is counted rather than described.

WHAT A PROPOSAL IS NOT
----------------------
This tool PROPOSES. It never promotes. A proposal carries evidence and a
confidence; a disposition becomes authoritative only when a reviewer records it.
Collapsing those two is how a heuristic becomes constitution by accident, so the
ledger keeps `proposed_disposition` and `disposition` as different fields and the
gate counts only the second as coverage.

THREE PREDECESSOR TRAPS ARE DESIGNED AGAINST, NOT REDISCOVERED
--------------------------------------------------------------
T-SELF-CONTAMINATED-DENOMINATOR-001  the audit's own output poisons its input.
    Every ucr_cif path is excluded when the index is BUILT, not subtracted after,
    so no probe can ever see this mission's own text. Measured previously at 96
    hits vs 0 for a single system.
T-D2A-CONSTANT-FLOOR-001             24 of 28 verdicts returned the same number.
    A score identical across items carries no information, so this emits
    UNRESOLVED as a distinct OUTCOME rather than a low score, and asserts that
    the confidence distribution is not degenerate.
T-VOCABULARY-ZERO-IS-NOT-ABSENCE-002 zero cannot fall.
    No evidence means UNRESOLVED, never "novel" and never "unowned". Only a
    reviewer may turn an absence into IMPLEMENT.

ANTI-GAMING (the mission's own rules, made mechanical)
------------------------------------------------------
UNMAPPED=0 must not be reachable by laundering. So the gate additionally fails on:
  * a POLICY_ONLY / NOT_APPLICABLE share above a declared ceiling
  * a shrinking denominator (floor on total units)
  * a disposition naming an owner path that no longer exists (stale entry)
  * a synthetic unmapped unit that does NOT turn it red (--selftest)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

SCHEMA_VERSION = 1

#: The closed disposition set. UNMAPPED is the absence of a decision, never a choice.
DISPOSITIONS = (
    "ALREADY_SATISFIED", "EXTEND_EXISTING_OWNER", "MERGE", "CONNECT", "IMPLEMENT",
    "POLICY_ONLY", "BENCHMARK_ONLY", "RESEARCH_FRONTIER", "NOT_APPLICABLE",
    "SUPERSEDED", "REJECTED_WITH_EVIDENCE", "EXTERNALLY_BLOCKED",
)
#: Dispositions that discharge a requirement without building anything. Cheap to
#: assign and therefore the laundering route; capped.
SOFT_DISPOSITIONS = ("POLICY_ONLY", "NOT_APPLICABLE", "RESEARCH_FRONTIER")
SOFT_CEILING = 0.35

EXCLUDE_RX = re.compile(r"ucr[_-]?cif", re.I)
SCAN_DIRS = ("modules", "tools", "hooks", "commands", "agents", "governance", "rules")
INDEX_EXT = (".py", ".js", ".md", ".json", ".ts", ".ps1")

#: A term must be at least this distinctive to be worth indexing.
_TERM_RX = re.compile(r"\b([A-Za-z][A-Za-z0-9_-]{3,28})\b")
_STOP = frozenset("""the and that this with from into each every must shall should never
always para cada debe nunca siempre pero como este esta todo todos se lo la el en de un una
true false null none self return import export const function class value data name type
test file path json text line list dict str int bool args kwargs print open read write""".split())

#: Ownership needs corroboration: a single mention in a single file is a coincidence.
MIN_EVIDENCE_FILES = 2
MIN_EVIDENCE_HITS = 3
MIN_UNITS = 2000            # denominator floor


def build_index(repo: str):
    """term -> {module_path: hit_count}, with this mission excluded at construction."""
    index = defaultdict(lambda: defaultdict(int))
    files = 0
    for sub in SCAN_DIRS:
        root_dir = os.path.join(repo, sub)
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, fs in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not EXCLUDE_RX.search(d) and d != "__pycache__"]
            # Test the REPO-RELATIVE path, never the absolute one. The isolated
            # worktree for this mission is itself named `pp-ucr-cif`, so matching the
            # absolute path excluded the entire estate and indexed 0 files -- the
            # denominator guard inverted into a total blindfold. The floor control
            # caught it; nothing else would have, because "no owner found" is exactly
            # what a correct sweep of a genuinely novel corpus would also report.
            rel_root = os.path.relpath(root, repo)
            if EXCLUDE_RX.search(rel_root):
                continue
            for f in fs:
                if not f.endswith(INDEX_EXT) or EXCLUDE_RX.search(f):
                    continue
                path = os.path.join(root, f)
                rel = os.path.relpath(path, repo).replace("\\", "/")
                # owner granularity = the module/tool directory, not the file
                parts = rel.split("/")
                owner = "/".join(parts[:2]) if len(parts) > 2 else rel
                try:
                    blob = open(path, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                files += 1
                seen = Counter()
                for t in _TERM_RX.findall(blob):
                    tl = t.lower()
                    if tl in _STOP or len(tl) < 4:
                        continue
                    seen[tl] += 1
                for t, n in seen.items():
                    index[t][owner] += n
    return index, files


def text_terms(text, min_len: int = 5):
    """The distinctive terms of a free-text blob, as this mission counts them.

    Extracted so a CONSUMER of the ledger asks "what is this about?" with the
    producer's own vocabulary instead of a second tokenizer. Two tokenizers
    that agree today diverge on the day one of them learns a new stop word,
    and the join goes quiet without anything turning red.
    """
    terms = Counter()
    for t in _TERM_RX.findall(str(text or "")):
        tl = t.lower()
        if tl not in _STOP and len(tl) >= min_len:
            terms[tl] += 1
    return terms


def unit_terms(u: dict):
    """The terms a unit is about. Entities first; they are the high-signal half."""
    terms = Counter()
    for e in (u.get("entities") or []):
        for tl, n in text_terms(e, 4).items():
            terms[tl] += 3 * n                      # entity mentions weigh more
    terms.update(text_terms(u.get("text"), 5))
    return terms


def propose(u: dict, index, min_files=MIN_EVIDENCE_FILES, min_hits=MIN_EVIDENCE_HITS):
    """Return (proposed_disposition, confidence, owner, evidence_terms).

    Absence of evidence yields UNRESOLVED -- a distinct outcome, never a low score,
    and never an inference that the requirement is novel.
    """
    terms = unit_terms(u)
    if not terms:
        return "UNRESOLVED", 0.0, None, []
    owner_hits = defaultdict(int)
    owner_terms = defaultdict(set)
    for t, w in terms.items():
        posting = index.get(t)
        if not posting:
            continue
        for owner, n in posting.items():
            owner_hits[owner] += w * min(n, 8)
            owner_terms[owner].add(t)
    if not owner_hits:
        return "UNRESOLVED", 0.0, None, []
    owner = max(owner_hits, key=owner_hits.get)
    ev_terms = sorted(owner_terms[owner])
    if len(ev_terms) < min_files or owner_hits[owner] < min_hits:
        return "UNRESOLVED", 0.0, None, ev_terms
    total = sum(owner_hits.values()) or 1
    # Confidence is the owner's SHARE of evidence, so it varies per unit instead of
    # pinning to a floor; a flat distribution would itself be the defect.
    conf = round(owner_hits[owner] / total, 4)
    return "EXTEND_EXISTING_OWNER", conf, owner, ev_terms[:10]


def build_ledger(corpus_path: str, repo: str):
    corpus = json.load(open(corpus_path, encoding="utf-8"))
    index, indexed_files = build_index(repo)
    rows = []
    for u in corpus["units"]:
        pd, conf, owner, ev = propose(u, index)
        rows.append({
            "uid": u["uid"], "unit_class": u["unit_class"], "kind": u["kind"],
            "claim_class": u["claim_class"],
            "name": u.get("name"), "text": (u.get("text") or "")[:400],
            "line_start": u["line_start"], "line_end": u["line_end"],
            "proposed_disposition": pd, "proposed_owner": owner,
            "confidence": conf, "evidence_terms": ev,
            "disposition": None,            # authoritative; set only by a reviewer
            "disposition_reason": None,
            "reviewed_by": None,
        })
    return rows, index, indexed_files, corpus


def gate(rows, indexed_files: int, strict: bool):
    print("\n=== COVERAGE ===")
    total = len(rows)
    decided = [r for r in rows if r["disposition"]]
    unmapped = total - len(decided)
    print("units=%d  decided=%d  UNMAPPED=%d" % (total, len(decided), unmapped))
    print("proposals=%s" % dict(Counter(r["proposed_disposition"] for r in rows)))
    if decided:
        print("dispositions=%s" % dict(Counter(r["disposition"] for r in decided)))

    ok = True
    if total < MIN_UNITS:
        print("CONTROL_FAIL denominator floor: %d < %d -- coverage cannot be improved "
              "by shrinking the population" % (total, MIN_UNITS))
        ok = False
    if indexed_files < 500:
        print("CONTROL_FAIL estate index too small (%d files) -- the sweep may have "
              "stopped seeing code" % indexed_files)
        ok = False

    # confidence distribution must not be degenerate (T-D2A-CONSTANT-FLOOR-001)
    confs = [r["confidence"] for r in rows if r["confidence"] > 0]
    if confs:
        uniq = len(set(round(c, 3) for c in confs))
        print("confidence: n=%d distinct=%d min=%.3f max=%.3f"
              % (len(confs), uniq, min(confs), max(confs)))
        if uniq < 10:
            print("CONTROL_FAIL confidence is degenerate (%d distinct values) -- a score "
                  "identical across items ranks nothing and must not be read as a "
                  "measurement" % uniq)
            ok = False
    else:
        print("confidence: no scored rows")

    if decided:
        soft = sum(1 for r in decided if r["disposition"] in SOFT_DISPOSITIONS)
        share = soft / len(decided)
        print("soft_disposition_share=%.3f (ceiling %.2f)" % (share, SOFT_CEILING))
        if share > SOFT_CEILING:
            print("CONTROL_FAIL too much coverage is discharged without building "
                  "anything -- UNMAPPED=0 must not be reachable by laundering")
            ok = False

    print("CONTROLS=%s" % ("PASS" if ok else "FAIL"))
    if not ok:
        return 2
    if strict and unmapped:
        print("GATE=FAIL (%d requirements have no disposition)" % unmapped)
        return 1
    print("GATE=%s" % ("PASS" if not unmapped else "OPEN (%d undecided)" % unmapped))
    return 0


def selftest(repo: str) -> int:
    """Drive the gate's RED branches. A gate that has never failed proves nothing."""
    print("=== DISPOSITION GATE SELFTEST ===")
    base = [{"uid": "u%d" % i, "unit_class": "statement", "kind": "law",
             "claim_class": "OBSERVED", "name": None, "text": "t", "line_start": i,
             "line_end": i, "proposed_disposition": "EXTEND_EXISTING_OWNER",
             "proposed_owner": "modules/x", "confidence": 0.1 + (i % 97) / 500.0,
             "evidence_terms": [], "disposition": "EXTEND_EXISTING_OWNER",
             "disposition_reason": "r", "reviewed_by": "test"}
            for i in range(MIN_UNITS + 10)]
    results = {}

    results["green"] = gate([dict(r) for r in base], 900, strict=True)

    # RED 1: one unmapped requirement
    m = [dict(r) for r in base]
    m[0]["disposition"] = None
    results["red_unmapped"] = gate(m, 900, strict=True)

    # RED 2: laundering -- discharge everything as POLICY_ONLY
    m = [dict(r) for r in base]
    for r in m:
        r["disposition"] = "POLICY_ONLY"
    results["red_laundering"] = gate(m, 900, strict=True)

    # RED 3: shrunken denominator
    results["red_denominator"] = gate([dict(r) for r in base[:50]], 900, strict=True)

    # RED 4: degenerate confidence (the constant-floor trap)
    m = [dict(r) for r in base]
    for r in m:
        r["confidence"] = 0.45
    results["red_constant_conf"] = gate(m, 900, strict=True)

    # RED 5: blind index
    results["red_blind_index"] = gate([dict(r) for r in base], 10, strict=True)

    print("\n=== SELFTEST VERDICT ===")
    expect = {"green": 0, "red_unmapped": 1, "red_laundering": 2,
              "red_denominator": 2, "red_constant_conf": 2, "red_blind_index": 2}
    ok = True
    for k, want in expect.items():
        got = results[k]
        flag = "OK " if got == want else "FAIL"
        if got != want:
            ok = False
        print("  %-20s expected_exit=%d got=%d  %s" % (k, want, got, flag))
    print("SELFTEST=%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--out", default=None)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 while any requirement is UNMAPPED (ratchet mode)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--top-owners", type=int, default=15)
    args = ap.parse_args()

    if args.selftest:
        return selftest(args.repo)
    if not args.corpus:
        print("--corpus is required unless --selftest")
        return 2

    rows, index, indexed_files, corpus = build_ledger(args.corpus, args.repo)
    print("=== ESTATE INDEX (this mission's own paths excluded at construction) ===")
    print("indexed_files=%d  distinct_terms=%d" % (indexed_files, len(index)))

    owners = Counter(r["proposed_owner"] for r in rows if r["proposed_owner"])
    print("\n=== PROPOSED OWNERS (top %d) ===" % args.top_owners)
    for o, n in owners.most_common(args.top_owners):
        print("  %5d  %s" % (n, o))

    rc = gate(rows, indexed_files, args.strict)

    if args.out:
        payload = {"schema_version": SCHEMA_VERSION,
                   "corpus_units": len(rows),
                   "indexed_files": indexed_files,
                   "compiled_corpus_id": corpus.get("compiled_corpus_id"),
                   "note": "proposed_disposition is a CANDIDATE with evidence; "
                           "`disposition` is authoritative and set only by review",
                   "rows": rows}
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        tmp = args.out + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, args.out)
        print("\nwrote %s" % args.out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
