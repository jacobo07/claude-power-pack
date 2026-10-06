"""Incremental Cognition generation 2 (IC-gen2, autonomous-optimization) judge.

Reached through `python3 tools/test_incremental_cognition_program.py --generation 2 --status|--final|--selftest`.
Spec of record: vault/specs/autonomous-optimization.md. Generation 1's ledger, its `frozen` object and its
FROZEN_AT are read here only to be compared with, never written.

What it judges: vault/programs/incremental-cognition/gen2/ledger.json (pillars M reopened, O, P, Q, R). The
clauses are CE's own (tools/test_cognitive_economy_program.py L1-L9, X1-X3): they are reused, not
reimplemented (AO-01, no parallel verifier). CE reads seven module globals at call time, so every judgement
runs inside `bound()`, which snapshots those globals, points them at gen2, and restores all seven in a
`finally`. Nothing is rebound at import time, so a gen1 run of the same process is unaffected, and CE's own
selftest (which hardcodes the A-T fixtures) is never run under the gen2 binding.

On top of CE's clauses, the gen2-only rules G2-* (each killed by a mutant in `selftest`) pin what CE cannot
see: the ledger identity (G2-B1), gen1's pre-registration still equal to its pinned copy (G2-GEN1), the M
reopening quoting gen1 faithfully (G2-REOPEN), denominators and materiality equal to gen1's (G2-DENOM), the
predicted terminals and the pre-registered allowed loss of P (G2-PRED), and a READY spec (G2-SPEC).

Modes: status | final | selftest. Exit codes: 0 pass, 1 fail, 2 could not run. An unreadable or invalid
ledger is COULD_NOT_RUN, never a pass.
"""
from __future__ import annotations

import contextlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO))
import test_cognitive_economy_program as ce  # noqa: E402

GEN2_DIR = "vault/programs/incremental-cognition/gen2/"
LEDGER_REL = GEN2_DIR + "ledger.json"
FROZEN_AT_REL = GEN2_DIR + "FROZEN_AT"
HANDOFF_DIR = GEN2_DIR + "handoffs/"
PILLARS = ["M", "O", "P", "Q", "R"]
REQS_REL = ".planning/workstreams/autonomous-optimization/REQUIREMENTS.md"
REQ_ROW = re.compile(r"^\|\s*AOP-([MOPQR])\s*\|[^|\n]*\|([^|\n]*)\|\s*$", re.M)
SELF_REL = "tools/test_incremental_cognition_program.py"

_GLOBALS = ("SELF_REL", "LEDGER_REL", "FROZEN_AT_REL", "HANDOFF_DIR", "PILLARS", "REQS_REL", "REQ_ROW")


def snapshot_bindings() -> dict:
    """The seven CE globals as they are now (REQ_ROW as its pattern string), for the restore check."""
    out = {}
    for k in _GLOBALS:
        v = getattr(ce, k)
        out[k] = v.pattern if k == "REQ_ROW" else list(v) if k == "PILLARS" else v
    return out


@contextlib.contextmanager
def bound():
    """Point the seven CE globals at generation 2 for the duration of one judgement, then restore them."""
    saved = {k: getattr(ce, k) for k in _GLOBALS}
    try:
        ce.SELF_REL, ce.LEDGER_REL, ce.FROZEN_AT_REL = SELF_REL, LEDGER_REL, FROZEN_AT_REL
        ce.HANDOFF_DIR, ce.PILLARS = HANDOFF_DIR, list(PILLARS)
        ce.REQS_REL, ce.REQ_ROW = REQS_REL, REQ_ROW
        yield
    finally:
        for k, v in saved.items():
            setattr(ce, k, v)


def load_ledger() -> dict:
    """The gen2 ledger (OSError / JSONDecodeError reach the caller)."""
    return json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))


def g2_problems(led: dict, res) -> list:
    """The gen2-only rules (filled by Task 2)."""
    return []


def problems(led: dict, res=None, final: bool = False) -> list:
    """CE's clauses under the gen2 binding plus the G2 rules. Empty = pass."""
    with bound():
        res = res if res is not None else ce.Resolver()
        out = ce.check_ledger(led, res, final=final, run_gates=final)
        if not final:
            out += ce.check_disposition(led, res)  # `final` already includes it
        out += g2_problems(led, res)
    return out


def main(mode: str) -> int:
    if mode not in ("status", "final"):
        print(f"ICP_GEN2_VERDICT=COULD_NOT_RUN unknown mode {mode!r} (status|final)")
        return 2
    try:
        led = load_ledger()
        if not isinstance(led, dict):
            raise ValueError("ledger is not a JSON object")
    except (OSError, ValueError) as exc:  # JSONDecodeError is a ValueError
        print(f"ICP_GEN2_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
        return 2
    fails = problems(led, None, final=(mode == "final"))
    if mode == "status":
        state = led.get("state") or {}
        open_ = [p for p in PILLARS if not (state.get(p) or {}).get("terminal")]
        print(json.dumps({"open": open_, "closed": [p for p in PILLARS if p not in open_], "violations": fails},
                         ensure_ascii=False))
        return 1 if fails else 0
    for x in fails:
        print("  FAIL", x)
    print(f"ICP_GEN2_VERDICT={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1].lstrip("-") if len(sys.argv) > 1 else "final"))
