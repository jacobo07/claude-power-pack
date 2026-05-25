#!/usr/bin/env python3
"""M15 -- CEPS auto-test stub generator + stale-stub audit.

Reads `vault/ceps/events.jsonl`, filters to events with
`auto_test_eligible=true` (categories: regression, security, drift),
and writes a SKIP-by-default pytest stub for each at
`tests/ceps_generated/test_<sig[:12]>.py`.

Why skip-by-default: per plan P6, failing-by-default stubs would break
the 29 baseline tests immediately. SKIP keeps them visible but non-
blocking. The 7-day stale audit (subcommand `audit`) emits WARN rows
to flag stubs that have been pending resolution longer than the
threshold -- WARN, not FAIL, so the Auto-Testing Gate is never broken
by stale stubs alone.

Usage:
    python tools/ceps_test_gen.py generate
    python tools/ceps_test_gen.py audit [--stale-days N]
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
EVENTS_PATH = PP_ROOT / "vault" / "ceps" / "events.jsonl"
STUB_DIR = PP_ROOT / "tests" / "ceps_generated"
STALE_DAYS_DEFAULT = 7

STUB_TEMPLATE = '''"""Auto-generated CEPS regression stub.

Pattern signature: {sig}
Category:         {category}
Subsystem:        {subsystem}
Generated:        {ts}
Prevention rule:  {rule}

Status: skip-pending. Replace the assertion below with a real check
that reproduces the root cause and now passes against the fix. Once
the assertion is real, remove the @pytest.mark.skip decorator -- the
test will run as part of the normal pytest suite.

Reality contract: empty body skip-marker is acceptable for up to 7
days from the `Generated` timestamp above. After that, `tools/
ceps_test_gen.py audit` flags it WARN.
"""
import pytest


@pytest.mark.skip(reason="ceps-stub-pending: {rule_short}")
def test_ceps_{sig_short}_regression():
    # Root cause to encode:
    # {root_cause_short}
    # Fill the assertion with a check that fails before the fix and
    # passes after. Then drop the @pytest.mark.skip decorator above.
    assert False, "ceps stub awaiting real assertion"
'''


def _short(text: str, n: int = 80) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "..."


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_events(events_path: Path) -> list:
    if not events_path.is_file():
        return []
    out = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _stub_path(sig: str) -> Path:
    return STUB_DIR / f"test_{sig[:12]}.py"


def _safe_ident(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def _relpath(p: Path) -> Path:
    """relative_to(PP_ROOT) when possible, else absolute. Avoids
    ValueError when STUB_DIR is monkeypatched to a tmpdir outside the
    PP repo (M16 full-cycle test pattern)."""
    try:
        return p.relative_to(PP_ROOT)
    except ValueError:
        return p


def cmd_generate(args) -> int:
    events_path = Path(args.events) if args.events else EVENTS_PATH
    events = _load_events(events_path)
    eligible = [e for e in events if e.get("auto_test_eligible")]
    if not eligible:
        print("no auto_test_eligible events found")
        return 0
    written = 0
    skipped = 0
    for ev in eligible:
        sig = ev.get("pattern_signature", "")
        if not sig:
            continue
        stub = _stub_path(sig)
        if stub.exists() and not args.force:
            skipped += 1
            continue
        body = STUB_TEMPLATE.format(
            sig=sig,
            sig_short=_safe_ident(sig[:12]),
            category=ev.get("category", "?"),
            subsystem=ev.get("subsystem", "?"),
            ts=ev.get("ts", ""),
            rule=ev.get("prevention_rule", ""),
            rule_short=_short(ev.get("prevention_rule", ""), 100).replace('"', "'"),
            root_cause_short=_short(ev.get("root_cause", ""), 200),
        )
        _atomic_write(stub, body)
        written += 1
        print(f"wrote {_relpath(stub)}")
    print(f"\nwritten={written}  skipped(existing)={skipped}  "
          f"total_eligible={len(eligible)}")
    return 0


# 7-day stale audit. WARN-only, never FAIL the Auto-Testing Gate.
_GENERATED_RX = re.compile(r"^Generated:\s+(\S+)", re.M)


def cmd_audit(args) -> int:
    stale_days = args.stale_days or STALE_DAYS_DEFAULT
    cutoff = time.time() - stale_days * 86400
    stubs = sorted(STUB_DIR.glob("test_*.py")) if STUB_DIR.is_dir() else []
    if not stubs:
        print("no stubs found")
        return 0
    warns = 0
    for stub in stubs:
        body = stub.read_text(encoding="utf-8", errors="replace")
        m = _GENERATED_RX.search(body)
        if not m:
            continue
        ts_str = m.group(1).strip()
        try:
            ts_epoch = time.mktime(time.strptime(ts_str[:19],
                                                  "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            continue
        age_days = (time.time() - ts_epoch) / 86400.0
        if ts_epoch < cutoff:
            warns += 1
            print(f"WARN  {_relpath(stub)}  age={age_days:.1f}d "
                  f"(stale threshold {stale_days}d)")
        else:
            print(f"OK    {_relpath(stub)}  age={age_days:.1f}d")
    print(f"\nWARN count: {warns}/{len(stubs)}  (gate impact: 0 -- "
          "stale stubs are advisory only)")
    return 0


def main(argv: list) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate",
                       help="materialize SKIP stubs for eligible events")
    g.add_argument("--events", help="override events.jsonl path")
    g.add_argument("--force", action="store_true",
                   help="overwrite existing stubs")
    g.set_defaults(func=cmd_generate)
    a = sub.add_parser("audit", help="warn on stubs older than N days")
    a.add_argument("--stale-days", type=int, default=STALE_DAYS_DEFAULT,
                   help=f"stale threshold (default {STALE_DAYS_DEFAULT})")
    a.set_defaults(func=cmd_audit)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
