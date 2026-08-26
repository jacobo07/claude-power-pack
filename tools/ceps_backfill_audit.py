#!/usr/bin/env python3
"""Classify historical CEPS events against the semantic admission rules.

The admission gate added on 2026-08-26 refuses vacuous failure claims at
write time. It cannot reach what was already written: 73 events accrued
while the producer classified text rather than failure, and three of them
are demonstrably not failures at all.

This tool CLASSIFIES. It never purges and never rewrites `root_cause`,
`category` or `ts` -- institutional history stays readable exactly as it
was recorded, because a store that quietly edits its own past cannot be
used to audit anything, including this repair. Each event gains:

    admission_status : "valid" | "invalid" | "identity_suspect"
    admission_note   : why, in one line
    admission_rev    : the rule generation that judged it

Idempotent: re-running re-judges from the ORIGINAL fields, so a rule
change moves a verdict and a re-run never compounds.

    --check   report only, exit 1 if any unjudged event remains
    --apply   write verdicts back
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

# ADMISSION_REV is imported, never re-declared: two copies of a rule
# generation drift, and the one that drifts is the one nobody re-runs.
from tools.ceps import ADMISSION_REV, is_vacuous_failure_claim  # noqa: E402

EVENTS = PP / "vault" / "ceps" / "events.jsonl"
SENTINEL = "[Tool result missing due to internal error]"

# Navigation prefixes are not failing tools. Kept in sync with the
# producer's NAV_PREFIXES by the V-CEPS-BACKFILL-NAV-PARITY gate.
NAV = {"cd", "chdir", "pushd", "popd", "set-location", "sl",
       "export", "set", "source", ".", "env", "call"}


def judge(event: dict) -> tuple[str, str]:
    """Return (status, note) for one event, from its original fields."""
    root = str(event.get("root_cause", ""))
    subsystem = str(event.get("subsystem", ""))

    if is_vacuous_failure_claim(root):
        return ("invalid",
                "vacuous failure claim: asserts that nothing failed")

    if root.strip() == SENTINEL:
        # Cannot be distinguished retrospectively: the stored snippet is
        # identical whether the frame really dropped or the tool merely
        # printed the literal. Recorded honestly as unknown-leaning-bad
        # rather than guessed in either direction.
        return ("identity_suspect",
                "sentinel snippet: quoted-vs-experienced is unrecoverable "
                "from the stored record")

    tail = subsystem.split(":", 1)[1] if ":" in subsystem else ""
    if tail.lower() in NAV:
        return ("identity_suspect",
                f"subsystem '{subsystem}' is a navigation prefix, not the "
                "failing tool; the failure may be real, the KEY is not")

    return ("valid", "")


def load() -> list[dict]:
    rows = []
    if not EVENTS.exists():
        return rows
    for line in EVENTS.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    rows = load()
    if not rows:
        print("CEPS_BACKFILL: no events -- nothing to classify")
        return 0

    verdicts = collections.Counter()
    changed = 0
    for e in rows:
        status, note = judge(e)
        verdicts[status] += 1
        if e.get("admission_status") != status or \
                e.get("admission_rev") != ADMISSION_REV:
            changed += 1
        e["admission_status"] = status
        e["admission_note"] = note
        e["admission_rev"] = ADMISSION_REV

    print(f"CEPS_BACKFILL: {len(rows)} events")
    for k in ("valid", "identity_suspect", "invalid"):
        print(f"  {k:18s} {verdicts[k]}")
    for e in rows:
        if e["admission_status"] != "valid":
            print(f"    {e.get('ts')} | {e.get('category')} | "
                  f"{e.get('subsystem')} | {e['admission_status']} | "
                  f"{str(e.get('root_cause'))[:44]}")

    if args.apply:
        body = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in rows)
        EVENTS.write_text(body, encoding="utf-8", newline="\n")
        print(f"APPLIED: {changed} verdicts written (rev {ADMISSION_REV})")
        return 0

    if args.check and changed:
        print(f"UNJUDGED: {changed} events lack a current verdict "
              f"-- run with --apply")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
