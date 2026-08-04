#!/usr/bin/env python3
"""retirement.py -- the retirement-condition evaluator (UCEIMR residue R2).

`contract.py:115` defines `retirement_condition`, and every seeded contract
populates it -- `duplicate_detection.json`: "proposals stop measuring
majority-owned across three consecutive audits". Nothing read it.

That is the sealed `feedback_orphan_field_dead_recovery_path` shape: a field
defined and consumed with no evaluator is dead by starvation, and the registry
reads as healthy while a capability that should have been retired stays live.
It is also, exactly, DS10's `RETIRED_BY_EVIDENCE` from the UCEIMR brief:
negative learning as a first-class operation, not an afterthought.

Two rules govern the design.

  A free-text condition is NOT auto-evaluable, and pretending otherwise would
  be worse than the gap. So evaluation runs through a PROBE REGISTRY: a
  condition with a deterministic probe is measured against real repository
  state; a condition without one is reported UNEVALUABLE and is never
  silently counted as ACTIVE. `feedback_zero_cannot_fall` -- an unrecognized
  idiom must not read as a pass.

  Retirement is PROPOSE-ONLY. This module never deletes, edits or deactivates
  a contract. A capability that retires itself is a gate that grades itself
  (`sqi_scs_c93`); the Owner retires, the evaluator only shows the evidence.

Stdlib-only. Fail-open per contract: a probe that raises yields UNEVALUABLE
for that one contract and never aborts the sweep.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import load_contracts  # noqa: E402

RETIREMENT_LOG = _PP_ROOT / "vault" / "capability_runtime" / "retirement_log.json"
STALE_AFTER_DAYS = 30

# Statuses. UNEVALUABLE is a first-class outcome, never a synonym for ACTIVE.
RETIRED = "RETIRED_BY_EVIDENCE"
ACTIVE = "ACTIVE"
NEVER = "NEVER"
UNEVALUABLE = "UNEVALUABLE"
NO_CONDITION = "NO_CONDITION"

_NEVER_RE = re.compile(r"^\s*never\b", re.I)
_FM_KEY = re.compile(r"^([a-z_]+):\s*(.+?)\s*$", re.I)


@dataclass
class RetirementVerdict:
    contract_id: str
    status: str
    condition: str
    evidence: str
    probe: str = ""
    evaluated_at: str = ""

    @property
    def retires(self) -> bool:
        return self.status == RETIRED

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Probes. Each returns (met, evidence): met=True means the condition the
# contract named has COME TRUE and the capability should be retired.
# ---------------------------------------------------------------------------
def _audit_frontmatter(root: Path) -> list:
    """Every corpus audit in vault/plans that declares a verdict, newest first.

    Discovered, never curated (`PR-COVERAGE-BY-CONSTRUCTION-001`): the set is
    every plan file carrying a `verdict:` front-matter key, not a hand-kept
    list of audits someone remembered.
    """
    out = []
    try:
        paths = sorted((root / "vault" / "plans").glob("*.md"))
    except OSError:
        return out
    for p in paths:
        try:
            if p.stat().st_size > 2_000_000:
                continue
            head = p.read_text(encoding="utf-8-sig", errors="replace")[:4000]
        except OSError:
            continue
        if not head.startswith("---"):
            continue
        block = head.split("---", 2)[1] if head.count("---") >= 2 else ""
        fm = {}
        for line in block.split("\n"):
            m = _FM_KEY.match(line)
            if m:
                fm.setdefault(m.group(1).lower(), m.group(2))
        if "verdict" not in fm:
            continue
        out.append({"file": p.name, "date": fm.get("date", ""),
                    "verdict": fm.get("verdict", "")})
    out.sort(key=lambda r: (r["date"], r["file"]), reverse=True)
    return out


def probe_duplicate_detection(root: Path):
    """"proposals stop measuring majority-owned across three consecutive audits"

    Retires only when the three most recent verdict-bearing audits are all
    NOT majority-owned. Fewer than three audits is insufficient evidence --
    reported as unmet with the count, never as a pass.
    """
    audits = _audit_frontmatter(root)
    if len(audits) < 3:
        return False, (f"only {len(audits)} verdict-bearing audit(s) on disk -- "
                       "three consecutive are required to retire")
    last3 = audits[:3]
    majority = [a for a in last3 if "majority" in a["verdict"].lower()]
    names = ", ".join(f"{a['file']}={a['verdict'].split()[0]}" for a in last3)
    if majority:
        return False, (f"{len(majority)} of the last 3 audits still measure "
                       f"majority-owned ({names})")
    return True, f"3 consecutive audits without a majority-owned verdict ({names})"


def probe_liveness_reachability(root: Path):
    """"every module is registered at creation time by construction"

    Retires only when the liveness gate reports zero unreachable/undeclared
    modules -- i.e. the registry can no longer catch anything.
    """
    try:
        from modules.liveness.reachability import gate as liveness_gate
        _ok, _rows, offenders = liveness_gate()
    except Exception as e:  # noqa: BLE001
        return None, f"liveness gate unavailable ({type(e).__name__})"
    n = len(offenders or [])
    if n:
        return False, f"liveness still names {n} unreachable/undeclared module(s)"
    return True, "liveness gate reports zero offenders -- registration is by construction"


# id -> (probe, human description). A contract absent here is UNEVALUABLE,
# which is a visible debt, not a silent pass.
PROBES = {
    "duplicate_detection": (probe_duplicate_detection,
                            "3 most recent corpus audits vs majority-owned"),
    "liveness_reachability": (probe_liveness_reachability,
                              "liveness gate offender count"),
}


# ---------------------------------------------------------------------------
# Evaluation.
# ---------------------------------------------------------------------------
def evaluate_contract(c, root=None) -> RetirementVerdict:
    """One contract's retirement condition against real repository state."""
    root = Path(root) if root is not None else _PP_ROOT
    cond = (getattr(c, "retirement_condition", "") or "").strip()
    cid = getattr(c, "id", "?")
    stamp = _iso(_now())
    if not cond:
        return RetirementVerdict(cid, NO_CONDITION, "",
                                 "no retirement condition declared -- a "
                                 "capability with no exit is dogma",
                                 evaluated_at=stamp)
    if _NEVER_RE.match(cond):
        return RetirementVerdict(cid, NEVER, cond,
                                 "declared permanent by contract",
                                 evaluated_at=stamp)
    entry = PROBES.get(cid)
    if entry is None:
        return RetirementVerdict(
            cid, UNEVALUABLE, cond,
            "no deterministic probe registered for this condition -- "
            "it cannot be measured, and is NOT counted as active",
            evaluated_at=stamp)
    probe, desc = entry
    try:
        met, evidence = probe(root)
    except Exception as e:  # noqa: BLE001 -- fail-open per contract
        return RetirementVerdict(cid, UNEVALUABLE, cond,
                                 f"probe raised {type(e).__name__}", desc, stamp)
    if met is None:
        return RetirementVerdict(cid, UNEVALUABLE, cond, evidence, desc, stamp)
    return RetirementVerdict(cid, RETIRED if met else ACTIVE, cond,
                             evidence, desc, stamp)


def evaluate_all(contracts=None, contracts_dir=None, root=None) -> list:
    """Every contract, retiring ones first. Fail-open -> []."""
    try:
        cs = contracts if contracts is not None else load_contracts(contracts_dir)
    except Exception:  # noqa: BLE001
        return []
    order = {RETIRED: 0, UNEVALUABLE: 1, NO_CONDITION: 2, ACTIVE: 3, NEVER: 4}
    out = [evaluate_contract(c, root) for c in cs]
    return sorted(out, key=lambda v: (order.get(v.status, 5), v.contract_id))


# ---------------------------------------------------------------------------
# Staleness probe -- a condition nobody has measured in N days is a debt.
# ---------------------------------------------------------------------------
def load_log(log_path=None) -> dict:
    p = Path(log_path) if log_path is not None else RETIREMENT_LOG
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001 -- fail-open
        return {}


def record_evaluation(verdicts: list, log_path=None) -> Path:
    """Persist last-evaluated stamps. Atomic; never raises on a bad entry."""
    p = Path(log_path) if log_path is not None else RETIREMENT_LOG
    log = load_log(p)
    for v in verdicts:
        log[v.contract_id] = {"evaluated_at": v.evaluated_at,
                              "status": v.status, "probe": v.probe}
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(log, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(p)
    return p


def stale(contracts=None, contracts_dir=None, log_path=None,
          days: int = STALE_AFTER_DAYS, now=None) -> list:
    """Contract ids whose retirement condition has not been evaluated within
    `days`. A contract never evaluated is stale by definition -- absence of a
    record is the strongest staleness signal there is."""
    try:
        cs = contracts if contracts is not None else load_contracts(contracts_dir)
    except Exception:  # noqa: BLE001
        return []
    log = load_log(log_path)
    cutoff = (now or _now()) - timedelta(days=max(0, days))
    out = []
    for c in cs:
        cid = getattr(c, "id", "")
        rec = log.get(cid)
        if not isinstance(rec, dict) or not rec.get("evaluated_at"):
            out.append(cid)
            continue
        try:
            when = datetime.strptime(rec["evaluated_at"], "%Y-%m-%dT%H:%M:%SZ")
            when = when.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            out.append(cid)
            continue
        if when < cutoff:
            out.append(cid)
    return sorted(out)


def render(verdicts: list, stale_ids=None) -> str:
    counts: dict = {}
    for v in verdicts:
        counts[v.status] = counts.get(v.status, 0) + 1
    lines = [" ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no contracts"]
    for v in verdicts:
        lines.append(f"  [{v.status}] {v.contract_id}")
        lines.append(f"      condition: {v.condition[:100]}")
        lines.append(f"      evidence:  {v.evidence[:110]}")
    if stale_ids:
        lines.append(f"  STALE (>{STALE_AFTER_DAYS}d unevaluated): "
                     f"{', '.join(stale_ids)}")
    retiring = [v.contract_id for v in verdicts if v.retires]
    lines.append(f"propose-only: {len(retiring)} retirement proposal(s)"
                 + (f" -> {', '.join(retiring)}" if retiring else "")
                 + " -- nothing was deleted or deactivated")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Evaluate capability retirement conditions (propose-only)")
    ap.add_argument("--contracts-dir", default=None)
    ap.add_argument("--log", default=None)
    ap.add_argument("--stale-days", type=int, default=STALE_AFTER_DAYS)
    ap.add_argument("--record", action="store_true",
                    help="persist last-evaluated stamps")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when any capability is proposed for retirement")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    verdicts = evaluate_all(contracts_dir=args.contracts_dir)
    stale_ids = stale(contracts_dir=args.contracts_dir, log_path=args.log,
                      days=args.stale_days)
    if args.record:
        record_evaluation(verdicts, args.log)
    if args.json:
        print(json.dumps({"verdicts": [v.to_dict() for v in verdicts],
                          "stale": stale_ids}, indent=2))
    else:
        print(render(verdicts, stale_ids))
    if args.strict and any(v.retires for v in verdicts):
        return 1
    return 0


__all__ = [
    "RetirementVerdict", "PROBES", "RETIRED", "ACTIVE", "NEVER", "UNEVALUABLE",
    "NO_CONDITION", "RETIREMENT_LOG", "STALE_AFTER_DAYS",
    "probe_duplicate_detection", "probe_liveness_reachability",
    "evaluate_contract", "evaluate_all", "stale", "load_log",
    "record_evaluation", "render",
]

if __name__ == "__main__":
    raise SystemExit(main())
