#!/usr/bin/env python
"""Replay the existing rollover policy on MEASURED inputs (plan ccp-s16). Read-only.

`tools/rollover.py::decide` is the single rollover policy. This tool never decides on its own and
never clears anything: it measures what `decide` currently assumes, so the assumption can be
replaced by evidence later, in rollover.py, by its owner.

    python tools/rollover_replay.py fresh-cost [--json] [--min-samples N]

fresh-cost: what a fresh epoch actually cost, from sessions that took over a sealed capsule and
passed the resume exam. `decide` prices a fresh epoch as floor + capsule chars / 4; a successor
also pays the calls it spends re-orienting before it changes anything. Measured per certified
successor: its first-call context, and how many calls (and how much context) it carried before
its first mutation (Write / Edit / NotebookEdit, or a `git commit` command). "Calls to first
mutation" includes genuine work, so as a rehydration cost it is an UPPER bound.

Joins: `resume_certified` rows carry only the PREDECESSOR (`rollover.py` ledger call in certify);
the successor is `successor_claimed.claimant`. A certified capsule with no claim row is reported,
never measured. Torn ledger rows (concurrent appends interleave) are counted, never guessed.
Calls are counted by `tis_observed._calls_in` (one API call once); context by `_context_of`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import rollover  # noqa: E402  (single owner: ledger location, transcript rows, transcript lookup)
import tis_observed as tis  # noqa: E402  (single owner: call identity and context size)

MIN_SAMPLES = 5
MUTATING_TOOLS = ("Write", "Edit", "NotebookEdit")
# `commit` must be git's subcommand: an executable spelled git / git.exe or a variable holding it,
# then only options (-C path, -c k=v, --flag[=v]) before `commit`.
_COMMIT_RE = re.compile(
    r"""(?:\bgit(?:\.exe)?['"]?|\$\w+)\s+(?:(?:-C|-c)\s+(?:'[^']*'|"[^"]*"|\S+)\s+|--?[\w-]+(?:=\S+)?\s+)*commit\b""",
    re.I)


def is_commit_command(command: str) -> bool:
    return bool(_COMMIT_RE.search(command or ""))


def read_ledger(path: Path) -> tuple[list[dict], int]:
    """(rows, torn): a line that is not a JSON object is torn, counted, never repaired."""
    rows, torn = [], 0
    if not Path(path).is_file():
        return rows, torn
    for line in Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            torn += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            torn += 1
    return rows, torn


def _mutating_message_ids(transcript: Path) -> set:
    ids = set()
    for row in rollover._rows(transcript):
        msg = row.get("message")
        if not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
            continue
        for b in msg["content"]:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            inp = b.get("input") or {}
            if b.get("name") in MUTATING_TOOLS or is_commit_command(str(inp.get("command") or "")):
                ids.add(msg.get("id"))
    return ids


def session_trace(transcript: Path) -> dict:
    """Per-call context, and the 1-based index of the first call that mutated."""
    calls, *_ = tis._calls_in(Path(transcript))
    ctx = [tis._context_of(c["usage"]) for c in calls]
    muts = _mutating_message_ids(transcript)
    first = next((i + 1 for i, c in enumerate(calls) if c["key"][0] in muts), None)
    return {"calls": len(calls), "ctx": ctx, "first_mutation": first}


def _dist(values: list, min_samples: int) -> dict:
    v = sorted(values)
    if len(v) < min_samples:
        return {"n": len(v), "p10": None, "p50": None, "p90": None}
    pick = lambda q: v[min(len(v) - 1, int(q * len(v)))]
    return {"n": len(v), "p10": pick(0.10), "p50": v[len(v) // 2], "p90": pick(0.90)}


def fresh_cost(ledger_path: Optional[Path] = None, find: Optional[Callable] = None,
               min_samples: int = MIN_SAMPLES) -> dict:
    ledger_path = Path(ledger_path or rollover.STATE_DIR / "rollover-ledger.jsonl")
    find = find or rollover._find_transcript
    rows, torn = read_ledger(ledger_path)
    claimant = {r["session_id"]: r["claimant"] for r in rows
                if r.get("event") == "successor_claimed" and r.get("session_id") and r.get("claimant")}
    certified = [r["session_id"] for r in rows if r.get("event") == "resume_certified" and r.get("session_id")]
    samples, missing_claim, missing_transcript, no_mutation = [], [], [], 0
    for pred in dict.fromkeys(certified):
        succ = claimant.get(pred)
        if not succ:
            missing_claim.append(pred)
            continue
        t = find(succ)
        if not t or not Path(t).is_file():
            missing_transcript.append(succ)
            continue
        tr = session_trace(Path(t))
        if not tr["ctx"]:
            missing_transcript.append(succ)
            continue
        fm = tr["first_mutation"]
        no_mutation += fm is None
        samples.append({"predecessor": pred, "successor": succ, "first_ctx": tr["ctx"][0],
                        "calls_to_first_mutation": fm,
                        "ctx_at_first_mutation": tr["ctx"][fm - 1] if fm else None,
                        "carried_before_first_mutation": sum(tr["ctx"][:fm - 1]) if fm else None})
    measured = [s for s in samples if s["calls_to_first_mutation"]]
    first = _dist([s["first_ctx"] for s in samples], min_samples)
    return {
        "verdict": "MEASURED" if first["p50"] is not None else "INSUFFICIENT_EVIDENCE",
        "ledger": str(ledger_path), "torn_rows": torn, "certified": len(dict.fromkeys(certified)),
        "missing_claim": missing_claim, "missing_transcript": missing_transcript,
        "no_mutation": no_mutation, "first_ctx": first,
        "calls_to_first_mutation": _dist([s["calls_to_first_mutation"] for s in measured], min_samples),
        "carried_before_first_mutation": _dist([s["carried_before_first_mutation"] for s in measured],
                                               min_samples),
        "bound": "calls before the first mutation include real work: an UPPER bound on rehydration",
        "decide_assumes": "fresh = floor + capsule chars / 4 (rollover.decide), no rehydration term",
        "samples": samples,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    fc = sub.add_parser("fresh-cost")
    fc.add_argument("--json", action="store_true")
    fc.add_argument("--min-samples", type=int, default=MIN_SAMPLES)
    a = ap.parse_args(argv)
    res = fresh_cost(min_samples=a.min_samples)
    if a.json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"fresh-cost: {res['verdict']}  certified {res['certified']}, measured {len(res['samples'])}, "
          f"no claim {len(res['missing_claim'])}, no transcript {len(res['missing_transcript'])}, "
          f"never mutated {res['no_mutation']}, torn ledger rows {res['torn_rows']}")
    for k in ("first_ctx", "calls_to_first_mutation", "carried_before_first_mutation"):
        d = res[k]
        print(f"  {k}: n={d['n']} p10={d['p10']} p50={d['p50']} p90={d['p90']}")
    print(f"  {res['bound']}\n  decide assumes: {res['decide_assumes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
