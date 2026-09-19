#!/usr/bin/env python3
"""ucr_cif_adjudicate.py -- turn owner PROPOSALS into authoritative dispositions.

`disposition_ledger` generates candidates lexically and says so: its
`disposition` field has always been authoritative and has always been empty,
while `proposed_disposition` carried a candidate. This is the step between them,
and it is deliberately NOT more scoring -- it runs the structural adjudicator in
`modules/ucr_cif/ownership_evidence.py`, whose signals cannot be won by saying a
word more often.

  VERIFY   -> writes `disposition` (EXTEND_EXISTING_OWNER) with its evidence
  REJECT   -> writes nothing, and records that THIS candidate is wrong, so a
              false owner is not re-proposed forever
  ABSTAIN  -> writes nothing; the row stays open with a typed reason

Coverage is never improved by resolving an ABSTAIN toward the convenient answer.
A run that verifies few rows and abstains on many is the honest outcome when the
evidence is thin, and it is reported as such.

Re-runnable: adjudication is a pure function of repository state plus the
ledger, so a second run over an unchanged estate produces the same verdicts and
rewrites the same values. Rows already carrying an authoritative disposition are
left alone unless --reverify is given.

CLI
  python tools/ucr_cif_adjudicate.py                 # report only
  python tools/ucr_cif_adjudicate.py --apply         # write dispositions
  python tools/ucr_cif_adjudicate.py --limit 400     # sample, for a fast look
  python tools/ucr_cif_adjudicate.py --owner modules/governance-overlay
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.ucr_cif.ownership_evidence import (  # noqa: E402
    adjudicate, build_structural_index,
)

LEDGER = _PP_ROOT / "vault" / "ucr_cif" / "disposition_ledger.json"
ADJUDICATOR = "ucr-cif-w3:structural"


def _terms_of(row: dict) -> list:
    """The terms a row is about. `evidence_terms` is what the lexical proposer
    actually matched on, so adjudicating those is adjudicating ITS claim rather
    than a different one of our choosing."""
    terms = list(row.get("evidence_terms") or [])
    name = str(row.get("name") or "")
    if name:
        terms.append(name)
    return terms


def run(rows, index, *, owner_filter=None, limit=None, reverify=False) -> dict:
    counts = Counter(r["proposed_owner"] for r in rows if r.get("proposed_owner"))
    verdicts = []
    seen = 0
    for row in rows:
        cand = row.get("proposed_owner")
        if not cand:
            continue
        if owner_filter and cand != owner_filter:
            continue
        if row.get("disposition") and not reverify:
            continue
        if limit is not None and seen >= limit:
            break
        seen += 1
        verdicts.append(adjudicate(row.get("uid", "?"), cand, _terms_of(row),
                                   index, counts))
    return {"verdicts": verdicts, "considered": seen,
            "proposal_counts": counts}


def apply_verdicts(rows, verdicts) -> int:
    by_uid = {r.get("uid"): r for r in rows}
    written = 0
    for v in verdicts:
        row = by_uid.get(v.unit_uid)
        if row is None:
            continue
        if v.verdict == "VERIFY":
            row["disposition"] = "EXTEND_EXISTING_OWNER"
            row["disposition_reason"] = v.reason
            row["reviewed_by"] = ADJUDICATOR
            written += 1
        elif v.verdict == "REJECT":
            # No disposition -- but the candidate is recorded as refuted, which
            # is a different and more useful state than "still unresolved".
            row["disposition_reason"] = f"candidate rejected: {v.reason}"
            row["reviewed_by"] = ADJUDICATOR
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reverify", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--owner", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    ledger = json.loads(LEDGER.read_text(encoding="utf-8-sig"))
    rows = ledger["rows"]

    index = build_structural_index()
    if index["files_seen"] < 200 or len(index["owners"]) < 20:
        print(f"HARNESS-FAILED: structural index saw only "
              f"{index['files_seen']} files / {len(index['owners'])} owners -- "
              "refusing to adjudicate against an empty population",
              file=sys.stderr)
        return 2

    out = run(rows, index, owner_filter=args.owner, limit=args.limit,
              reverify=args.reverify)
    tally = Counter(v.verdict for v in out["verdicts"])

    print(f"structural index: {index['files_seen']} files, "
          f"{len(index['owners'])} owners")
    print(f"rows considered : {out['considered']}")
    for verdict in ("VERIFY", "REJECT", "ABSTAIN"):
        n = tally.get(verdict, 0)
        pct = 100 * n / max(out["considered"], 1)
        print(f"  {verdict:8s} {n:5d}  ({pct:5.1f}%)")

    per_owner = Counter()
    for v in out["verdicts"]:
        per_owner[(v.candidate, v.verdict)] += 1
    print("\nthe two measured volume winners:")
    for owner in ("modules/governance-overlay",
                  "agents/oneshot-architect-auditor.md"):
        line = "  ".join(f"{verdict}={per_owner[(owner, verdict)]}"
                         for verdict in ("VERIFY", "REJECT", "ABSTAIN"))
        print(f"  {owner}: {line}")

    if args.apply:
        written = apply_verdicts(rows, out["verdicts"])
        ledger["adjudication"] = {
            "adjudicator": ADJUDICATOR,
            "considered": out["considered"],
            "verify": tally.get("VERIFY", 0),
            "reject": tally.get("REJECT", 0),
            "abstain": tally.get("ABSTAIN", 0),
        }
        # MATCH THE PRODUCER'S FORMAT (disposition_ledger.py:332 writes
        # `indent=1, ensure_ascii=False`). Writing indent=2 reformatted all
        # 58,000 lines of an institutional artifact so that a 996-row change
        # was indistinguishable from a rewrite -- the diff is evidence, and a
        # formatter that launders it destroys the evidence.
        LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        print(f"\nAPPLIED: {written} authoritative disposition(s) written")

    if args.json:
        print(json.dumps([v.to_dict() for v in out["verdicts"][:50]], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
