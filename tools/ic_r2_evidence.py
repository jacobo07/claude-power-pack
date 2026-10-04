#!/usr/bin/env python3
"""ic_r2_evidence.py -- print the R2 owner_ledger evidence rows for a consuming pillar (J, M, ...).

    python3 tools/ic_r2_evidence.py --pillar J [--commit HEAD]

READ-ONLY: it writes no file, no git ref and no index entry. The program ledger is read from
`icp.REPO / ce.LEDGER_REL`; every owner ledger is read with git at the resolved commit, through the same
reader R2 itself uses (test_incremental_cognition_program.OwnerLedgers), so the terminal printed here is the
terminal R2 will see.

The consumed owner pillars are DISCOVERED from the ledger's `frozen.consumes[P]`, never listed here.
A pasteable row is printed only when EVERY consumed pillar has a terminal at the resolved commit and that
commit is an ancestor of HEAD; otherwise one line per pillar says why it is not ready and no row is printed.

Exit codes: 0 ready (rows printed), 1 not ready, 2 could not run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_incremental_cognition_program as icp  # noqa: E402

ce = icp.ce
UNREADABLE = "UNREADABLE"
FULL_SHA = re.compile(r"[0-9a-f]{40}")


def consumed(led: dict, pid: str) -> list:
    """[(owner ledger ref, owner pillar)] in file order from frozen.consumes[pid]; KeyError when pid consumes nothing."""
    wanted = ((led.get("frozen") or {})["consumes"])[pid]
    return [(w.get("ledger"), w.get("pillar")) for w in wanted]


def resolve_commit(spec: str):
    """The 40-hex commit `spec` names in the repository, or None."""
    spec = (spec or "").strip()
    if not spec or spec.startswith("-"):
        return None
    r = ce._git("rev-parse", "--verify", "--quiet", spec + "^{commit}")
    out = r.stdout.strip()
    return out if r.returncode == 0 and FULL_SHA.fullmatch(out) else None


def full_commit(sha: str) -> str:
    """The commit field of a printed row: the full 40-hex sha, never an abbreviation."""
    return sha


def predicted_at(sha: str, ref: str, pillar: str):
    """The owner's frozen prediction for `pillar` at `sha`; UNREADABLE when git or the JSON fails."""
    r = ce._git("show", f"{sha}:{ref}")
    if r.returncode != 0:
        return UNREADABLE
    try:
        led = json.loads(r.stdout.lstrip("﻿"))
    except json.JSONDecodeError:
        return UNREADABLE
    if not isinstance(led, dict):
        return UNREADABLE
    for p in (led.get("frozen") or {}).get("pillars") or []:
        if isinstance(p, dict) and p.get("id") == pillar:
            return p.get("predicted")
    return None


def ready_when(flags) -> bool:
    """Ready only when there is at least one pillar and every one is ready."""
    flags = list(flags)
    return bool(flags) and all(flags)


def owner_rows(pid: str, sha: str, wanted, owners):
    """(rows, lines) for the consumed pairs `wanted` at commit `sha`. Rows only when every pair is READY."""
    short = sha[:8]
    if not owners.reachable(sha):
        return [], [f"UNREACHABLE {short}: not an ancestor of HEAD"]
    rows, lines, flags = [], [], []
    for ref, pillar in wanted:
        predicted = predicted_at(sha, ref, pillar)
        if predicted == UNREADABLE:
            lines.append(f"{UNREADABLE} {ref} at {short}: ledger or pillar {pillar} cannot be read")
            flags.append(False)
            continue
        terminal = owners.terminal_at(sha, ref, pillar)
        if terminal is None:
            lines.append(f"OPEN {ref}#{pillar} at {short}: no terminal (owner predicted {predicted})")
            flags.append(False)
            continue
        lines.append(f"READY {ref}#{pillar} at {short}: {terminal}")
        flags.append(True)
        rows.append({"kind": "owner_ledger", "ref": ref, "commit": full_commit(sha), "pillar": pillar,
                     "terminal": terminal})
    return (rows if ready_when(flags) else []), lines


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ic_r2_evidence.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--pillar", required=True, help="the consuming program pillar (a key of frozen.consumes)")
    ap.add_argument("--commit", default="HEAD", help="the commit at which to read the owner ledgers (default HEAD)")
    return ap


def _open_pillars(wanted, lines) -> list:
    return [p for ref, p in wanted if not any(x.startswith(f"READY {ref}#{p} ") for x in lines)]


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    pid = args.pillar
    try:
        led = json.loads((icp.REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ICR2_COULD_NOT_RUN ledger unreadable: {exc}")
        return 2
    try:
        wanted = consumed(led, pid)
    except (KeyError, TypeError):
        keys = sorted(((led.get("frozen") or {}).get("consumes") or {}).keys())
        print(f"ICR2_COULD_NOT_RUN pillar {pid} consumes no owner (frozen.consumes keys: {keys})")
        return 2
    sha = resolve_commit(args.commit)
    if sha is None:
        print(f"ICR2_COULD_NOT_RUN commit {args.commit} does not resolve")
        return 2
    rows, lines = owner_rows(pid, sha, wanted, icp.OwnerLedgers())
    for x in lines:
        print(x)
    if rows:
        print("ROWS")
        print(json.dumps(rows, indent=1))
        print(f"ICR2_READY={pid} commit={sha}")
        return 0
    print(f"ICR2_READY=NO pillar={pid} commit={sha} open={_open_pillars(wanted, lines)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
