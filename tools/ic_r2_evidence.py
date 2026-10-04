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
    if not all(isinstance(w, dict) for w in wanted):
        raise TypeError(f"frozen.consumes[{pid}] holds an entry that is not an object")
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
    frozen = led.get("frozen") or {}
    pillars = frozen.get("pillars") or [] if isinstance(frozen, dict) else UNREADABLE
    if not isinstance(pillars, list):      # a ledger of the wrong shape is unreadable, not "no prediction"
        return UNREADABLE
    for p in pillars:
        if isinstance(p, dict) and p.get("id") == pillar:
            return p.get("predicted")
    return None


def ready_when(flags) -> bool:
    """Ready only when there is at least one pillar and every one is ready."""
    flags = list(flags)
    return bool(flags) and all(flags)


def valid_terminal(terminal) -> bool:
    """True only for a str naming one of ce.TERMINALS; rejects "", 0, False, {} and an unknown name (an unhashable
    value must not raise on the set test)."""
    return isinstance(terminal, str) and terminal in ce.TERMINALS


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
        if not valid_terminal(terminal):
            lines.append(f"OPEN {ref}#{pillar} at {short}: terminal {terminal!r} is not a known terminal "
                         f"(owner predicted {predicted})")
            flags.append(False)
            continue
        lines.append(f"READY {ref}#{pillar} at {short}: {terminal}")
        flags.append(True)
        rows.append({"kind": "owner_ledger", "ref": ref, "commit": full_commit(sha), "pillar": pillar,
                     "terminal": terminal})
    return (rows if ready_when(flags) else []), lines


def roundtrip_problems(pid: str, wanted, rows, owners) -> list:
    """What R2 itself says about a program ledger holding exactly `rows` as pid's owner_ledger evidence."""
    synthetic = {
        "frozen": {"consumes": {pid: [{"ledger": ref, "pillar": p} for ref, p in wanted]}},
        "state": {pid: {"terminal": "MERGED_INTO_EXISTING_OWNER", "evidence": list(rows)}},
    }
    return icp.check_consumed(synthetic, owners)


def needs_lines(led: dict, pid: str) -> list:
    """The OTHER evidence kinds the CE clause L4 demands for pid's own frozen prediction (derived, not listed)."""
    entry = next((p for p in (led.get("frozen") or {}).get("pillars") or [] if p.get("id") == pid), None)
    if not entry:
        return []
    predicted = entry.get("predicted")
    kinds = (ce.REQUIRED_KINDS.get(predicted) or [()])[0]
    out = []
    for kind in kinds:
        head = f"NEEDS {pid} {predicted}: {kind}"
        if kind == "owner":
            out.append(f"{head} (one of {', '.join(entry.get('owner') or [])})")
        elif kind == "handoff":
            out.append(f"{head} ({icp.PROGRAM_DIR}handoffs/{pid}.md naming [{pid}] and one owner, "
                       f"committed after the freeze)")
        else:
            out.append(head)
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ic_r2_evidence.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--pillar", required=True, help="the consuming program pillar (a key of frozen.consumes)")
    ap.add_argument("--commit", default="HEAD", help="the commit at which to read the owner ledgers (default HEAD)")
    return ap


def _open_pillars(wanted, lines) -> list:
    return [p for ref, p in wanted if not any(x.startswith(f"READY {ref}#{p} ") for x in lines)]


def _consume_keys(led) -> list:
    """The frozen.consumes keys, or [] when the ledger's shape cannot say (never raises)."""
    frozen = led.get("frozen") if isinstance(led, dict) else None
    consumes = frozen.get("consumes") if isinstance(frozen, dict) else None
    return sorted(str(k) for k in consumes) if isinstance(consumes, dict) else []


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    pid = args.pillar
    try:
        led = json.loads((icp.REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:        # ValueError covers JSONDecodeError and UnicodeDecodeError
        print(f"ICR2_COULD_NOT_RUN ledger unreadable: {exc}")
        return 2
    if not isinstance(led, dict):
        print(f"ICR2_COULD_NOT_RUN ledger is not a JSON object (got {type(led).__name__})")
        return 2
    try:
        wanted = consumed(led, pid)
    except (KeyError, TypeError, AttributeError):
        print(f"ICR2_COULD_NOT_RUN pillar {pid} consumes no owner (frozen.consumes keys: {_consume_keys(led)})")
        return 2
    sha = resolve_commit(args.commit)
    if sha is None:
        print(f"ICR2_COULD_NOT_RUN commit {args.commit} does not resolve")
        return 2
    try:
        return _run(led, pid, sha, wanted)
    except Exception as exc:  # noqa: BLE001 -- exit 1 means "not ready"; an uncaught traceback must not borrow it
        print(f"ICR2_COULD_NOT_RUN unexpected {exc.__class__.__name__}: {exc}")
        return 2


def _run(led: dict, pid: str, sha: str, wanted) -> int:
    owners = icp.OwnerLedgers()
    rows, lines = owner_rows(pid, sha, wanted, owners)
    if rows:
        problems = roundtrip_problems(pid, wanted, rows, owners)
        if problems:      # the rows as printed must pass R2 as pasted; otherwise nothing is printed
            print(f"ICR2_COULD_NOT_RUN rows fail R2: {problems[0]}")
            return 2
    for x in lines:
        print(x)
    if rows:
        print("ROWS")
        print(json.dumps(rows, indent=1))
        for x in needs_lines(led, pid):
            print(x)
        print(f"ICR2_READY={pid} commit={sha}")
        return 0
    print(f"ICR2_READY=NO pillar={pid} commit={sha} open={_open_pillars(wanted, lines)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
