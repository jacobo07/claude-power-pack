#!/usr/bin/env python3
"""token_irr.py -- FIOS III-2 Token IRR Calculator (merges III-3 Balance Sheet).

Treats the frontier token as R&D CAPITAL, not operational cost, and computes the
investment return of a frontier session in NUMBERS (never adjectives):

  immediate_roi     -- assets produced per 1k frontier tokens spent.
  reuse_multiplier  -- how many future frontier calls each deposit is expected to
                       retire (deterministic/portable deposits retire the most).
  compound_roi      -- immediate_roi carried over the horizon by the reuse multiplier.
  payback_tokens    -- frontier tokens the deposits must retire to repay the spend.
  frontier_dependence_index (FDI) -- fraction of deposits still `frontier-only`
                       (0 = fully distilled, 1 = wholly model-bound). THE central metric.

And the balance sheet (III-3): ASSETS = deposits by destination; LIABILITIES =
frontier-only deposits + DUP debt. Net = assets that outlive the model.

Anti-duplication (the boundary the whole stack guards, FD-07 Invariant 1): this
computes NO parallel dependence number -- it READS the FD-07 deposits ledger and
CO-12's `fd_metrics` / `opus_avoided_count`, and FEEDS its IRR back to CO-12 via
`record_signal`. CO-12 remains the single instrument; this is one more producer.

Fail-open ABSOLUTE: any error -> a benign zeroed report, never an exception.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Expected future frontier calls each portability class retires. A deterministic
# recipe needs no model ever again (highest reuse); a frontier-only deposit retires
# nothing until it is downgraded (reuse 0). Calibratable, honest defaults.
_REUSE_BY_PORTABILITY = {
    "deterministic": 8.0, "small-model": 4.0, "mid-model": 2.0, "frontier-only": 0.0,
}
_DEFAULT_REUSE = 1.0               # unknown target -> conservative single reuse


def _deposits(repo: str, *, state_dir=None) -> list:
    try:
        from modules.fable_distillation.fd_07_flywheel import _load_deposits
        return _load_deposits(repo, state_dir)
    except Exception:  # noqa: BLE001 -- fail-open
        return []


@dataclass
class IRRReport:
    repo: str
    tokens_spent: int
    assets: int                       # non-DUP deposits (the R&D output)
    immediate_roi: float              # assets per 1k tokens
    reuse_multiplier: float           # avg future calls retired per asset
    compound_roi: float               # immediate_roi * reuse_multiplier
    payback_tokens: float             # tokens the reuse must retire to break even
    frontier_dependence_index: float  # frontier-only / total deposits (0..1)
    balance_sheet: dict = field(default_factory=dict)
    measured: bool = False
    note: str = ""


def _reuse_multiplier(deposits: list) -> float:
    if not deposits:
        return 0.0
    total = 0.0
    for d in deposits:
        total += _REUSE_BY_PORTABILITY.get(
            str(d.get("portability_target", "")), _DEFAULT_REUSE)
    return round(total / len(deposits), 3)


def _balance_sheet(deposits: list) -> dict:
    """III-3: assets by destination vs the frontier-dependence + DUP liabilities."""
    assets = {}
    frontier_only = 0
    for d in deposits:
        dest = str(d.get("destination", "unknown"))
        assets[dest] = assets.get(dest, 0) + 1
        if d.get("portability_target") == "frontier-only":
            frontier_only += 1
    return {
        "assets_by_type": assets,
        "assets_total": len(deposits),
        "liabilities": {
            "frontier_only_deposits": frontier_only,
            "frontier_dependence_index": (round(frontier_only / len(deposits), 3)
                                          if deposits else 0.0),
        },
        "net_portable_assets": len(deposits) - frontier_only,
    }


def compute_irr(repo: str, tokens_spent: int, *, state_dir=None,
                deposits=None) -> IRRReport:
    """Compute the frontier-token IRR for a repo's accumulated deposits. `deposits`
    may be supplied for a hermetic test; otherwise read from the FD-07 ledger.
    Fail-open -> a zeroed, honest report."""
    try:
        deps = deposits if deposits is not None else _deposits(repo, state_dir=state_dir)
        n = len(deps)
        tokens_spent = max(int(tokens_spent or 0), 0)
        immediate = round(n / (tokens_spent / 1000.0), 3) if tokens_spent else 0.0
        reuse = _reuse_multiplier(deps)
        compound = round(immediate * reuse, 3)
        # Payback: the spend is repaid once the deposits retire an equal number of
        # future frontier calls. Expressed in the same token unit (avg call ~ spend/n).
        avg_call = (tokens_spent / n) if n else 0.0
        retired_calls = sum(_REUSE_BY_PORTABILITY.get(
            str(d.get("portability_target", "")), _DEFAULT_REUSE) for d in deps)
        payback = round(max(tokens_spent - retired_calls * avg_call, 0.0), 1)
        bsheet = _balance_sheet(deps)
        return IRRReport(
            repo=repo or "(repo)", tokens_spent=tokens_spent, assets=n,
            immediate_roi=immediate, reuse_multiplier=reuse, compound_roi=compound,
            payback_tokens=payback,
            frontier_dependence_index=bsheet["liabilities"]["frontier_dependence_index"],
            balance_sheet=bsheet, measured=bool(n),
            note=("no deposits yet -- IRR is 0 until a frontier session deposits"
                  if not n else f"{n} asset(s), reuse x{reuse}"))
    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE
        return IRRReport(repo=repo, tokens_spent=0, assets=0, immediate_roi=0.0,
                         reuse_multiplier=0.0, compound_roi=0.0, payback_tokens=0.0,
                         frontier_dependence_index=0.0, measured=False,
                         note=f"irr error (fail-open): {e}")


def record_irr(report: IRRReport, *, state_dir=None) -> bool:
    """Feed the IRR to CO-12 (the single instrument) as one producer signal. NEVER
    a parallel accountant -- CO-12 owns the corpus; this appends to it. Fail-open."""
    try:
        from modules.cognitive_os.co_12_telemetry import record_signal
        return record_signal("fios_token_irr", {
            "repo": report.repo, "assets": report.assets,
            "immediate_roi": report.immediate_roi,
            "reuse_multiplier": report.reuse_multiplier,
            "compound_roi": report.compound_roi,
            "frontier_dependence_index": report.frontier_dependence_index,
        }, state_dir=state_dir)
    except Exception:  # noqa: BLE001 -- a telemetry write never breaks the caller
        return False


# --------------------------------------------------------------------------- #
# Stop-hook entry (rides the Stop-chain, same shape as fd_07_flywheel.main).
# --------------------------------------------------------------------------- #
def _is_frontier_session() -> bool:
    """kclaude exports PP_FRONTIER_SESSION=1 for a frontier (Opus) launch. Absent
    -> the Stop entry is a silent no-op (the IRR of frontier tokens is only
    meaningful in a frontier session -- same cadence gate as the FD-07 flywheel)."""
    return str(os.environ.get("PP_FRONTIER_SESSION", "")).strip() in ("1", "true", "yes")


def _stop_line(rep: "IRRReport") -> str:
    """The one-line IRR readout the Stop emits (honest: never a fake token number)."""
    if not rep.assets:
        return "FIOS IRR: 0 assets tracked -- populate the FD-07 ledger for a real IRR"
    net = rep.balance_sheet.get("net_portable_assets", 0)
    tok = f"{rep.tokens_spent} tok" if rep.tokens_spent else "tokens unmeasured"
    return (f"FIOS IRR: {rep.assets} assets / {tok} / immediate {rep.immediate_roi}/1k "
            f"/ reuse x{rep.reuse_multiplier} / FDI {rep.frontier_dependence_index} "
            f"/ net portable {net}")


def stop_entry() -> int:
    """Stop-chain entry: read the Stop JSON on stdin, gate on a frontier session,
    compute the repo's Token IRR, feed it to CO-12, emit a systemMessage. ALWAYS
    exit 0 -- an IRR readout never blocks session close. Fail-open ABSOLUTE."""
    raw = ""
    try:
        raw = sys.stdin.read()
    except OSError:
        raw = ""
    try:
        data = json.loads(raw or "{}")
    except (json.JSONDecodeError, ValueError):
        data = {}
    if not _is_frontier_session():
        try:
            sys.stdout.write("{}")          # bare session -> silent no-op
        except OSError:
            pass
        return 0
    try:
        cwd = data.get("cwd") or os.getcwd()
        try:                                 # optional honest token source; else 0
            tokens = int(os.environ.get("PP_SESSION_TOKENS", "0") or 0)
        except (TypeError, ValueError):
            tokens = 0
        rep = compute_irr(cwd, tokens)
        record_irr(rep)                      # feed CO-12 (one producer, never a fork)
        msg = _stop_line(rep)
        try:                                 # D2: nudge a non-PP repo with 0 deposits
            from modules.fable_distillation.federated_ledger import fdi_advisory
            adv = fdi_advisory(cwd)
            if adv:
                msg = msg + " | " + adv
        except Exception:  # noqa: BLE001 -- fail-open: the advisory never blocks Stop
            pass
        sys.stdout.write(json.dumps({"systemMessage": msg}))
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE: never block Stop
        try:
            sys.stdout.write("{}")
        except OSError:
            pass
    return 0


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="FIOS Token IRR -- frontier tokens as R&D capital")
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--tokens", type=int, default=0, help="frontier tokens spent")
    ap.add_argument("--record", action="store_true", help="feed the IRR to CO-12")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rep = compute_irr(args.repo, args.tokens)
    if args.record:
        record_irr(rep)
    if args.json:
        print(json.dumps(asdict(rep), ensure_ascii=False, indent=2))
    else:
        print(f"Token IRR [{rep.repo}]  assets={rep.assets}  "
              f"immediate_roi={rep.immediate_roi}/1k  reuse=x{rep.reuse_multiplier}  "
              f"compound={rep.compound_roi}  FDI={rep.frontier_dependence_index}")
        print(f"  balance: {rep.balance_sheet.get('net_portable_assets', 0)} portable "
              f"/ {rep.assets} total  ({rep.note})")
    return 0


if __name__ == "__main__":
    # A human CLI passes args (--repo/--tokens/--record/--json); the Stop-chain
    # dispatcher invokes this bare (no args) with the Stop JSON on stdin. Disambiguate
    # on argv so one file serves both without a glue module (mirrors fd_07_flywheel).
    raise SystemExit(main() if len(sys.argv) > 1 else stop_entry())
