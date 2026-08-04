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
# Distinct from UNEVALUABLE on purpose: UNEVALUABLE is a probe DEBT this repo
# can pay, EXTERNAL is a condition no repository probe could ever settle.
# Collapsing the two would leave the debt count unable to fall honestly.
EXTERNAL = "EXTERNAL"

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
        # Only verdicts that MEASURE OWNERSHIP count. Other plans carry a
        # `verdict:` key too (a sprint outcome, a wiring result); letting those
        # into the window would let an unrelated document silently "reset" the
        # majority-owned streak this condition is about.
        vtext = fm.get("verdict", "")
        # The vocabulary must cover BOTH poles of the measurement, or the
        # filter itself becomes the zero that cannot fall: "MAJORITY_OWNED"
        # would be counted while "GENUINELY_NEW_DATASET" -- the verdict that
        # would actually retire this capability -- silently would not.
        if not any(tok in vtext.upper() for tok in
                   ("OWNED", "NOVEL", "DUPLICATE", "GENUINELY", "NEW_DATASET")):
            continue
        out.append({"file": p.name, "date": fm.get("date", ""),
                    "verdict": vtext})
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
        # gate() -> (passed, OFFENDERS, rows). Order matters: unpacking rows
        # into offenders reports the whole unit inventory as unreachable (339
        # instead of 1) and the condition could then never be met.
        _ok, offenders, _rows = liveness_gate()
    except Exception as e:  # noqa: BLE001
        return None, f"liveness gate unavailable ({type(e).__name__})"
    n = len(offenders or [])
    if n:
        return False, f"liveness still names {n} unreachable/undeclared module(s)"
    return True, "liveness gate reports zero offenders -- registration is by construction"


def _jsonl_records(path: Path, limit: int = 5000) -> list:
    """Bounded JSONL read. Fail-open -> []."""
    out = []
    try:
        if not path.is_file() or path.stat().st_size > 8_000_000:
            return out
        for i, line in enumerate(path.read_text(encoding="utf-8-sig",
                                                errors="replace").splitlines()):
            if i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    except OSError:
        return out
    return out


_SPEC_OMISSION = ("spec omission", "without a spec", "sin spec", "no spec",
                  "spec_gate", "spec gate", "missing spec", "spec first")
# A zero must be earned against a corpus large enough for the absence to mean
# something. Below this, the probe returns UNEVALUABLE rather than retiring.
_MIN_INCIDENT_SAMPLE = 200


def probe_spec_depth_selection(root: Path):
    """"spec omission stops appearing in the incident record"

    Retires only when the incident record is NON-EMPTY and carries no
    spec-omission entry. An empty or unreadable record proves nothing and
    returns UNEVALUABLE -- absence of evidence is not evidence of absence,
    and a silent zero must never retire a guard.
    """
    recs = (_jsonl_records(root / "vault" / "osa" / "never_again_log.jsonl")
            + _jsonl_records(root / "vault" / "ceps" / "events.jsonl"))
    if not recs:
        return None, "incident record empty or unreadable -- cannot conclude"
    if len(recs) < _MIN_INCIDENT_SAMPLE:
        # A zero over a tiny denominator is not evidence of extinction, it is
        # evidence of a small corpus -- and a gate bounded by its own
        # vocabulary reads an unfamiliar idiom as 0 (feedback_zero_cannot_fall).
        # Refuse to retire a live guard on that.
        return None, (f"only {len(recs)} incident record(s); "
                      f"{_MIN_INCIDENT_SAMPLE} required before a zero can "
                      "retire a guard")
    hits = [r for r in recs
            if any(tok in json.dumps(r, ensure_ascii=False).lower()
                   for tok in _SPEC_OMISSION)]
    if hits:
        return False, (f"{len(hits)} spec-omission entr(ies) still in an "
                       f"incident record of {len(recs)}")
    return True, f"0 spec-omission entries across {len(recs)} incident records"


def probe_cascade_prevention(root: Path):
    """"the recorded chain set goes two years without a new member"."""
    recs = _jsonl_records(root / "vault" / "ceps" / "events.jsonl")
    if not recs:
        return None, "CEPS event log empty or unreadable -- cannot conclude"
    stamps = []
    for r in recs:
        for key in ("ts", "timestamp", "time", "created_at", "date"):
            val = r.get(key)
            if not val:
                continue
            try:
                stamps.append(datetime.fromisoformat(
                    str(val).replace("Z", "+00:00")))
            except ValueError:
                continue
            break
    if not stamps:
        return None, f"{len(recs)} CEPS events carry no parsable timestamp"
    newest = max(stamps)
    if newest.tzinfo is None:
        newest = newest.replace(tzinfo=timezone.utc)
    age_days = (_now() - newest).days
    if age_days >= 730:
        return True, f"newest recorded chain member is {age_days} days old"
    return False, (f"chain set gained a member {age_days} days ago "
                   f"({len(recs)} events) -- two years not elapsed")


def probe_architecture_reconstruction(root: Path):
    """"the repo carries a maintained architecture contract verified in CI"."""
    ci = root / ".github" / "workflows"
    try:
        flows = sorted(ci.glob("*.y*ml")) if ci.is_dir() else []
    except OSError:
        flows = []
    if not flows:
        return False, ("no CI workflow directory -- nothing verifies an "
                       "architecture contract")
    named = []
    for f in flows[:40]:
        try:
            body = f.read_text(encoding="utf-8-sig", errors="replace")[:20000]
        except OSError:
            continue
        if any(tok in body.lower()
               for tok in ("architecture", "arch_contract", "contract_fabric")):
            named.append(f.name)
    if named:
        return True, f"CI verifies an architecture contract ({', '.join(named[:3])})"
    return False, (f"{len(flows)} CI workflow(s), none referencing an "
                   "architecture contract")


# Conditions that depend on facts OUTSIDE this repository. These are not a
# probe debt -- no probe can exist here, and filing them under UNEVALUABLE
# would conflate "we owe a measurement" with "this repo cannot measure it",
# so the debt count could never fall for the right reason. Retiring one needs
# an Owner attestation, not a scanner.
EXTERNAL_CONDITIONS = {
    "cost_routing": ("model pricing is a market fact; no repository signal "
                     "can observe convergence"),
    "premise_verification": ("editor/toolchain symbol verification is a "
                             "property of the toolchain, not of this repo"),
}

# id -> (probe, human description). A contract absent from BOTH this registry
# and EXTERNAL_CONDITIONS is UNEVALUABLE: a visible debt, never a silent pass.
PROBES = {
    "duplicate_detection": (probe_duplicate_detection,
                            "3 most recent corpus audits vs majority-owned"),
    "liveness_reachability": (probe_liveness_reachability,
                              "liveness gate offender count"),
    "spec_depth_selection": (probe_spec_depth_selection,
                             "spec-omission entries in the incident record"),
    "cascade_prevention": (probe_cascade_prevention,
                           "age of the newest recorded chain member"),
    "architecture_reconstruction": (probe_architecture_reconstruction,
                                    "CI verification of an architecture contract"),
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
    if cid in EXTERNAL_CONDITIONS:
        return RetirementVerdict(
            cid, EXTERNAL, cond,
            f"depends on facts outside this repo: {EXTERNAL_CONDITIONS[cid]}. "
            "Retiring it needs an Owner attestation, not a scanner",
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
    order = {RETIRED: 0, UNEVALUABLE: 1, NO_CONDITION: 2, ACTIVE: 3,
             EXTERNAL: 4, NEVER: 5}
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
