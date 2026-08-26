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


def _prune_index(bad_ids: list[str]) -> int:
    """Drop judged-bad events from the FTS5 sidecar.

    The JSONL is not the only reader-facing copy. `ceps.propagate()` queries
    `ceps_patterns_fts` and returns its prevention rules as live advisories,
    so filtering the two cascade readers left the corrupt events reaching a
    THIRD consumer by a path nobody had looked at. A verdict honoured in one
    representation and ignored in another is not a verdict.

    Fail-open: the JSONL classification is the record of truth, and a
    missing or locked sidecar must never fail the audit.
    """
    if not bad_ids:
        return 0
    try:
        import sqlite3  # noqa: PLC0415

        from tools.ceps import DB_PATH  # noqa: PLC0415
        if not Path(DB_PATH).exists():
            return 0
        conn = sqlite3.connect(str(DB_PATH))
        try:
            total = 0
            for i in range(0, len(bad_ids), 400):
                chunk = bad_ids[i:i + 400]
                marks = ",".join("?" * len(chunk))
                cur = conn.execute(
                    f"DELETE FROM ceps_patterns_fts WHERE id IN ({marks})",
                    chunk)
                if cur.rowcount and cur.rowcount > 0:
                    total += cur.rowcount
            conn.commit()
            return total
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"  (FTS prune skipped: {type(exc).__name__}: {exc})")
        return 0


def load() -> list[dict | str]:
    """Every line, in order. A line that will not parse is kept AS TEXT.

    An earlier version dropped unparseable lines and then rebuilt the whole
    file from what survived, which deleted them permanently and silently --
    a torn write, a stray CRLF or a mid-file BOM would have been erased by
    the tool whose docstring promises it never purges. Preserving the raw
    line costs nothing and keeps the promise literally true.
    """
    out: list[dict | str] = []
    if not EVENTS.exists():
        return out
    for line in EVENTS.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            out.append(json.loads(stripped))
        except Exception:  # noqa: BLE001
            out.append(stripped)   # unreadable, not unwanted
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    items = load()
    if not items:
        print("CEPS_BACKFILL: no events -- nothing to classify")
        return 0

    rows = [e for e in items if isinstance(e, dict)]
    unreadable = [e for e in items if not isinstance(e, dict)]

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
    if unreadable:
        print(f"  {'unreadable':18s} {len(unreadable)}  "
              "(preserved verbatim, not judged, NOT dropped)")
    for e in rows:
        if e["admission_status"] != "valid":
            print(f"    {e.get('ts')} | {e.get('category')} | "
                  f"{e.get('subsystem')} | {e['admission_status']} | "
                  f"{str(e.get('root_cause'))[:44]}")

    if args.apply:
        # Read-modify-write against a log another process APPENDS to. The
        # producer opens it in "a" mode with no lock, so an event captured
        # between load() and this write would be erased by the rewrite.
        # Cheapest correct answer: notice and refuse. Losing an event is
        # worse than deferring a re-judgement that is idempotent anyway.
        if len(load()) != len(items):
            print("APPLY SKIPPED: the event log grew while this ran "
                  "(a producer appended). Nothing written; re-run.")
            return 0

        body = "".join(
            (json.dumps(e, ensure_ascii=False) if isinstance(e, dict) else e)
            + "\n" for e in items)
        # Atomic. A truncating write of 55KB that is interrupted -- by the
        # 30s budget this runs under as an umbrella row, or by anything else
        # -- would leave the event log half-written. This repo already knows
        # the pattern; the first version of this tool simply did not use it.
        tmp = EVENTS.with_suffix(".jsonl.tmp")
        try:
            tmp.write_text(body, encoding="utf-8", newline="\n")
            tmp.replace(EVENTS)
        except OSError as exc:
            print(f"APPLY FAILED (event log untouched): {exc}")
            return 2
        pruned = _prune_index([e["id"] for e in rows
                               if e["admission_status"] != "valid"
                               and e.get("id")])
        print(f"APPLIED: {changed} verdicts written (rev {ADMISSION_REV}); "
              f"{len(unreadable)} unreadable line(s) preserved; "
              f"{pruned} FTS row(s) pruned")
        return 0

    if args.check and changed:
        print(f"UNJUDGED: {changed} events lack a current verdict "
              f"-- run with --apply")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
