#!/usr/bin/env python3
"""Sweep Enforcer CLI (P3) -- seal a prevention rule only after it sweeps.

  Sweep and attempt to seal:
    python tools/rule_sweep.py --rule U-27 \
        --title "loaders must skip _-prefixed keys" \
        --site 'def load_\\w+\\(' --fix 'startswith\\("_"\\)' \
        --include '**/*.py'

  Sweep only, no seal (see the governed sites):
    python tools/rule_sweep.py --site '...' --fix '...' --dry

Exit 0 = ACCEPTED (rule may be written to UKDL / HARD-RULES).
Exit 1 = REJECTED (gaps remain, or no sweep was run).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.sweep_enforcer import SweepSpec, seal, sweep  # noqa: E402

LEDGER = PP_ROOT / "vault" / "sweeps" / "sweeps.jsonl"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="A prevention rule is not sealable until it has been "
                    "swept across every site matching its pattern (U-2).")
    p.add_argument("--site", required=True,
                   help="regex for every site the rule governs")
    p.add_argument("--fix", required=True,
                   help="regex for what a compliant site looks like")
    p.add_argument("--include", default="**/*.py")
    p.add_argument("--root", default=str(PP_ROOT))
    p.add_argument("--window", type=int, default=40,
                   help="lines after a site match in which compliance "
                        "may live (the enclosing block)")
    p.add_argument("--rule", default="", metavar="RULE_ID")
    p.add_argument("--title", default="")
    p.add_argument("--dry", action="store_true",
                   help="sweep and report; do not attempt a seal")
    a = p.parse_args(argv)

    spec = SweepSpec(site_pattern=a.site, fix_pattern=a.fix,
                     include=a.include, window_lines=a.window)
    res = sweep(spec, Path(a.root))

    print("=== SWEEP ===")
    print(f"command : {res.command}")
    print(f"audited : {len(res.sites)} site(s)")
    print(f"patched : {len(res.patched)}")
    print(f"gaps    : {len(res.gaps)}")
    for s in res.sites:
        mark = "ok  " if s.compliant else "GAP "
        print(f"  [{mark}] {s}  {s.text}")

    if a.dry:
        print("\n[dry] no seal attempted.")
        return 0

    if not a.rule:
        p.error("--rule is required unless --dry")

    v = seal(a.rule, a.title, res)
    print(f"\n=== SEAL: {v.verdict.value} ===")
    print(v.reason)
    if v.collapse_proposal:
        print(f"\n--- COLLAPSE PROPOSAL ---\n{v.collapse_proposal}")

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry = {"rule_id": a.rule, "title": a.title,
             "verdict": v.verdict.value, **res.as_dict()}
    # Atomic: read -> compose -> os.replace. Append mode would make this
    # tool violate the very rule class it exists to enforce (HR-4 / U-25),
    # and its own first sweep caught it doing exactly that.
    old = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else ""
    tmp = LEDGER.with_suffix(LEDGER.suffix + ".tmp")
    tmp.write_text(old + json.dumps(entry, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, LEDGER)
    print(f"\nsweep recorded: {LEDGER}")
    return 0 if v.sealed else 1


if __name__ == "__main__":
    raise SystemExit(main())
