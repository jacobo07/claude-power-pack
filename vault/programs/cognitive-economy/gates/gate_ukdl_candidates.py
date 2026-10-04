#!/usr/bin/env python
"""gate_ukdl_candidates.py -- pillar R. Format gate over the campaign's UKDL / CBR review.

Reads `vault/programs/cognitive-economy/ukdl-candidates.md`. Every candidate is a block

    ### UC-NN <title>
    - level: hard | process | trap
    - verdict: promote | reject | keep-candidate
    - cbr: EXPERIMENTAL | CANDIDATE | VALIDATED | ESTABLISHED
    - evidence: <repo-relative path>[, <path> ...]
    - reason: <why this verdict>

and the gate requires: at least one block; unique ids; every field present and in its set; every
evidence path an existing file; a non-empty reason; and every `promote` named as `[R] UC-NN` in the
owner bundle, because promotion INTO ukdl-universal.md is an Owner item (audit G10), never the
campaign's.

Each run also drives its own red branch: the real file must pass AND five mutants of it (dropped
evidence, unknown verdict, duplicate id, promote missing from the bundle, empty reason) must each
fail. A gate whose mutants pass is reported as FAIL, not as a pass.

    python vault/programs/cognitive-economy/gates/gate_ukdl_candidates.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PROG = REPO / "vault/programs/cognitive-economy"
CANDIDATES = PROG / "ukdl-candidates.md"
BUNDLE = PROG / "owner-bundle.md"
FIELDS = {
    "level": {"hard", "process", "trap"},
    "verdict": {"promote", "reject", "keep-candidate"},
    "cbr": {"EXPERIMENTAL", "CANDIDATE", "VALIDATED", "ESTABLISHED"},
}
HEAD = re.compile(r"^### (UC-\d+)\b", re.M)
FIELD = re.compile(r"^- (level|verdict|cbr|evidence|reason):[ \t]*(.*)$", re.M)


def problems(text: str, bundle: str) -> list:
    out = []
    heads = list(HEAD.finditer(text))
    if not heads:
        return ["no UC-NN candidate block"]
    ids = [m.group(1) for m in heads]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"{dup}: duplicate id")
    for k, m in enumerate(heads):
        uid = m.group(1)
        body = text[m.end(): heads[k + 1].start() if k + 1 < len(heads) else len(text)]
        got = {f: v.strip() for f, v in FIELD.findall(body)}
        for f, allowed in FIELDS.items():
            if got.get(f) not in allowed:
                out.append(f"{uid}: {f} {got.get(f)!r} not in {sorted(allowed)}")
        refs = [r.strip().strip("`") for r in (got.get("evidence") or "").split(",") if r.strip()]
        if not refs:
            out.append(f"{uid}: no evidence")
        for r in refs:
            if ".." in r or not (REPO / r).is_file():
                out.append(f"{uid}: evidence {r!r} is not a file in this repo")
        if not got.get("reason"):
            out.append(f"{uid}: empty reason")
        if got.get("verdict") == "promote" and f"[R] {uid}" not in bundle:
            out.append(f"{uid}: promote without an owner-bundle line naming [R] {uid}")
    return out


def mutants(text: str, bundle: str) -> dict:
    first = HEAD.search(text).group(1)
    promoted = re.search(r"^### (UC-\d+)\b[^#]*?^- verdict: promote", text, re.M | re.S)
    return {
        "dropped-evidence": (re.sub(r"^- evidence:.*$", "- evidence:", text, count=1, flags=re.M), bundle),
        "unknown-verdict": (re.sub(r"^- verdict:.*$", "- verdict: maybe", text, count=1, flags=re.M), bundle),
        "duplicate-id": (text + f"\n### {first} copy\n", bundle),
        "promote-not-in-bundle": (text, bundle.replace(f"[R] {promoted.group(1)}", "[R] gone"))
        if promoted else (text + "\n### UC-99 x\n- level: trap\n- verdict: promote\n- cbr: EXPERIMENTAL\n"
                                 "- evidence: vault/programs/cognitive-economy/ledger.json\n- reason: r\n", bundle),
        "empty-reason": (re.sub(r"^- reason:.*$", "- reason:", text, count=1, flags=re.M), bundle),
    }


def main() -> int:
    text = CANDIDATES.read_text(encoding="utf-8")
    bundle = BUNDLE.read_text(encoding="utf-8")
    fails = problems(text, bundle)
    for p in fails:
        print(f"  FAIL {p}")
    n = len(HEAD.findall(text))
    for name, (t, b) in mutants(text, bundle).items():
        caught = bool(problems(t, b))
        print(f"  {'ok  ' if caught else 'FAIL'} mutant {name} {'caught' if caught else 'PASSED (gate is blind)'}")
        if not caught:
            fails.append(f"mutant {name} passed")
    print(f"GATE_UKDL_CANDIDATES={'PASS' if not fails else 'FAIL'} candidates={n} failures={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
