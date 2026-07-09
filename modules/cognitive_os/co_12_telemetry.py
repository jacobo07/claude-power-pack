#!/usr/bin/env python3
"""co_12_telemetry.py -- CO-12 Cognitive Readiness Telemetry: the instrument layer.

The CO-12 dataset (SCS C74) specifies adoption-rate metrics, each naming its data
source and whether the instrument exists or is pending. This module wires the
instruments that can produce REAL data now, and exposes the producer-side sink for
the ones whose call site is not yet on the live path -- honestly reading `unknown`
(never a faked 0/100) for those.

Three signals from the C73/C74 handoff:

  loop-boundedness  -- CORPUS-DERIVED, real data now. Classifies every session in
                       ~/.claude/projects by transcript entry count: a session far
                       above the threshold ran long without a reset (the 10h-hung
                       pattern). Read-only over the same corpus C68/C69/C70 read;
                       no live-path dependency. This is the "wired with real data"
                       signal the reality contract requires.
  opus-avoided      -- PRODUCER-SIDE sink. CO-03 router.route() computes whether a
                       task resolved below Opus; when a caller passes the sink, the
                       event is recorded. Honest: route() is not guaranteed on the
                       live model-selection path (CO-10 residual), so the live count
                       is 0 until a caller wires the sink -- reported as such, not faked.
  dedup-hit         -- INSTRUMENT-PENDING. PM-03's consume side is wired (Hook 13,
                       SCS C73), but RedundancyTax.reason_or_reuse (the hit producer)
                       is agent-driven and not on the live path. Reported pending;
                       the datum is never invented (reality contract).

Fail-open ABSOLUTE everywhere: any error -> the signal is unknown/empty, never an
exception that could disturb a caller (a telemetry layer must never break work).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# A session whose transcript holds more entries than this ran long without a
# reset (/compact or /clear start a fresh transcript). Env-tunable; a proxy, not
# a wall-clock measure -- named honestly (CO-12 metric §II.5 limitation).
UNBOUNDED_ENTRY_THRESHOLD = int(os.environ.get("PP_CO12_UNBOUNDED_ENTRIES", "800"))
# Display bounds (not behavioral): how many unbounded sessions to keep/show and
# how far to truncate a session id for the report.
_TOP_UNBOUNDED_DEFAULT = 10
_REPORT_TOP_SHOWN = 5
_SID_DISPLAY_LEN = 12


def _default_state_dir() -> Path:
    return Path.home() / ".claude" / "state" / "co12_readiness"


def _default_proj_base() -> Path:
    return Path.home() / ".claude" / "projects"


# --------------------------------------------------------------------------- #
# Producer-side signal sink (opus-avoided, and any future producer signal).
# --------------------------------------------------------------------------- #
def record_signal(kind: str, payload: dict, *, state_dir=None,
                  now: datetime | None = None) -> bool:
    """Append one telemetry signal as a JSONL line. Fail-open -> False on any
    error (the caller's work must never break on a telemetry write)."""
    try:
        now = now or datetime.now(timezone.utc)
        d = Path(state_dir) if state_dir else _default_state_dir()
        d.mkdir(parents=True, exist_ok=True)
        rec = {"kind": str(kind), "ts": now.isoformat()}
        rec.update(payload or {})
        with (d / "signals.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return False


def load_signals(*, state_dir=None) -> list:
    """All recorded signals (fail-open -> [])."""
    try:
        p = (Path(state_dir) if state_dir else _default_state_dir()) / "signals.jsonl"
        if not p.is_file():
            return []
        out = []
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
        return out
    except OSError:
        return []


# --------------------------------------------------------------------------- #
# opus-avoided classifier (over a CO-03 RouteDecision or an equivalent dict).
# --------------------------------------------------------------------------- #
def classify_opus_avoided(decision) -> dict:
    """Given a CO-03 route decision, report whether the cascade resolved BELOW
    Opus (opus was avoided) and whether it was an explicit budget-pressure
    demotion. Accepts a RouteDecision-like object or a dict. Fail-open."""
    try:
        rung = getattr(decision, "rung", None)
        notes = getattr(decision, "notes", None)
        if rung is None and isinstance(decision, dict):
            rung = decision.get("rung")
            notes = decision.get("notes")
        rung = str(rung or "").lower()
        notes = notes or []
        avoided = rung in ("vault", "asset", "deterministic", "haiku", "sonnet")
        demoted = any("budget pressure" in str(n).lower() for n in notes)
        return {"opus_avoided": avoided, "demoted": demoted, "rung": rung}
    except Exception:  # noqa: BLE001
        return {"opus_avoided": False, "demoted": False, "rung": ""}


def opus_avoided_count(*, state_dir=None) -> dict:
    """Aggregate recorded opus-avoided signals. Honest: if no route decision was
    ever recorded, the count is 0 with adopted=0 opportunities (unknown adoption),
    NOT a claim that Opus was never avoidable."""
    sigs = [s for s in load_signals(state_dir=state_dir)
            if s.get("kind") == "opus_avoided"]
    avoided = sum(1 for s in sigs if s.get("opus_avoided"))
    demoted = sum(1 for s in sigs if s.get("demoted"))
    return {"opportunities": len(sigs), "opus_avoided": avoided,
            "demotions": demoted}


def route_and_record(task: str, *, sink_state_dir=None, now=None, **route_kw) -> dict:
    """Wire opus-avoided: route a task via CO-03 and RECORD whether Opus was
    avoided. Returns the classification. This is the producer call site a live
    caller uses instead of bare router.route() so the signal accrues real data
    without smearing I/O into the router. Fail-open: any error still returns a
    benign classification and never disturbs the caller."""
    try:
        from modules.cognitive_os.router import route as _route
        decision = _route(task, **route_kw)
        cls = classify_opus_avoided(decision)
        record_signal("opus_avoided", cls, state_dir=sink_state_dir, now=now)
        return cls
    except Exception:  # noqa: BLE001 -- fail-open
        return {"opus_avoided": False, "demoted": False, "rung": ""}


# --------------------------------------------------------------------------- #
# loop-boundedness (CORPUS-DERIVED -- the real-data signal).
# --------------------------------------------------------------------------- #
_SID_RE = re.compile(r"^[0-9a-fA-F-]{8,}$")


def _count_entries(path: Path) -> int:
    """Cheap transcript entry count = newline count (each JSONL line is one
    event). Fail-open -> 0."""
    try:
        n = 0
        with path.open("rb") as fh:
            for _ in fh:
                n += 1
        return n
    except OSError:
        return 0


def loop_boundedness(proj_base=None, *,
                     threshold: int = UNBOUNDED_ENTRY_THRESHOLD,
                     top: int = _TOP_UNBOUNDED_DEFAULT) -> dict:
    """Classify every session transcript as bounded / unbounded by entry count.
    Unbounded = ran far past a reset (the 10h-hung pattern). Real data from the
    live corpus. Fail-open -> an empty, honest report."""
    try:
        base = Path(proj_base) if proj_base else _default_proj_base()
        if not base.is_dir():
            return {"sessions": 0, "bounded": 0, "unbounded": 0,
                    "threshold": threshold, "top_unbounded": [],
                    "note": "no projects dir"}
        rows = []
        for sub in base.iterdir():
            if not sub.is_dir():
                continue
            for jf in sub.glob("*.jsonl"):
                if "subagent" in jf.name.lower():
                    continue
                if not _SID_RE.match(jf.stem):
                    continue  # only real session transcripts (uuid-like stem)
                rows.append((jf.stem, _count_entries(jf)))
        unbounded = [(sid, n) for sid, n in rows if n > threshold]
        unbounded.sort(key=lambda r: r[1], reverse=True)
        return {
            "sessions": len(rows),
            "bounded": len(rows) - len(unbounded),
            "unbounded": len(unbounded),
            "threshold": threshold,
            "top_unbounded": [{"sid": s[:_SID_DISPLAY_LEN], "entries": n}
                              for s, n in unbounded[:top]],
        }
    except Exception:  # noqa: BLE001 -- fail-open
        return {"sessions": 0, "bounded": 0, "unbounded": 0,
                "threshold": threshold, "top_unbounded": [], "note": "error"}


# --------------------------------------------------------------------------- #
# Readiness report -- honest composite (real signals + pending markers).
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Fable Advantage Distillation (FD) loop metrics -- REUSED, not re-invented.
# --------------------------------------------------------------------------- #
def fd_metrics(*, state_dir=None) -> dict:
    """FD suite loop metrics, computed from the fd_* signals the FD-00 admission
    gate and the FD-07 flywheel emit into the SAME signals.jsonl this module owns.
    This is the anti-duplication boundary the suite guards (FD-07 I.4, Invariant 1):
    CO-12 is the single dependence instrument; FD feeds it, never forks it. No
    separate dependence NUMBER is computed here -- the ground truth is opus_avoided
    + loop_boundedness above; FD adds the admission/deposit/portability signals that
    move them. instrument-pending until the loop runs on live frontier sessions."""
    sigs = load_signals(state_dir=state_dir)
    admitted = [s for s in sigs if s.get("kind") == "fd_frontier_call_admitted"]
    declined = [s for s in sigs if s.get("kind") == "fd_admission_declined"]
    deposits = [s for s in sigs if s.get("kind") == "fd_delta_deposited"]
    turns = [s for s in sigs if s.get("kind") == "fd_flywheel_turn"]
    total_adm = len(admitted) + len(declined)
    processed = sum(int(t.get("processed", 0) or 0) for t in turns)
    dep_count = len(deposits)
    frontier_only = sum(1 for d in deposits
                        if d.get("portability_target") == "frontier-only")
    proven = sum(1 for d in deposits if d.get("portability_proven"))
    measured = bool(admitted or declined or deposits or turns)
    return {
        "fd_sessions_count": len(turns),
        "fd_frontier_calls_admitted": len(admitted),
        "fd_admissions_declined": len(declined),
        # rejection rate: fraction of admission decisions the gate sent below frontier.
        "fd_rejection_rate": (round(len(declined) / total_adm, 3)
                              if total_adm else None),
        "fd_deltas_extracted": processed,
        "fd_assets_written": dep_count,
        "fd_portability_frontier_only": frontier_only,
        "fd_portability_proven": proven,
        # portability slope proxy: 1 - frontier_only/total; rises only on FD-04-
        # proven downgrades in v2 (portability_proven), never on estimates.
        "fd_portability_slope_proxy": (round(1 - frontier_only / dep_count, 3)
                                       if dep_count else None),
        "fd_dependence_reduction": "reuses opus_avoided + loop_boundedness (FD feeds "
                                   "them; no separate number -- Invariant 1)",
        "status": ("live" if measured else
                   "instrument-pending -- no fd_* signal yet (accrues on live "
                   "frontier sessions via the FD-07 Stop hook + FD-00 gate)"),
        "measured": measured,
    }


def readiness_report(proj_base=None, *, state_dir=None) -> dict:
    """The CO-12 readiness surface. Real signals carry values; pending
    instruments read 'instrument-pending', never a faked number."""
    loop = loop_boundedness(proj_base)
    opus = opus_avoided_count(state_dir=state_dir)
    opus_status = ("live" if opus["opportunities"] > 0
                   else "wired; 0 opportunities recorded "
                        "(route() not yet on the live path)")
    # CDIO design-review metrics. Lazy import: modules.cdio.telemetry imports
    # this module at load, so we resolve it at call time to avoid a cycle.
    try:
        from modules.cdio import telemetry as _cdio_tel
        cdio = _cdio_tel.cdio_readiness(state_dir=state_dir)
    except Exception:  # noqa: BLE001 -- fail-open: telemetry never breaks the report
        cdio = {"design_reviews_count": 0, "avg_design_quality_score": None,
                "critical_issues_caught": 0, "antipatterns_prevented": 0,
                "measured": False}
    fd = fd_metrics(state_dir=state_dir)
    pending = ["dedup_hit"]
    if not fd.get("measured"):
        pending.append("fd_distillation")
    return {
        "loop_boundedness": loop,          # REAL data now
        "opus_avoided": {**opus, "status": opus_status},
        "cdio": cdio,                      # REAL data once reviews record
        "fd_distillation": fd,             # REAL data once the FD loop runs live
        "dedup_hit": {"status": "instrument-pending",
                      "reason": "PM-03 consume wired (Hook 13, C73); "
                                "RedundancyTax hit-producer is agent-driven, "
                                "not on the live path -- datum not invented"},
        "instruments_pending": pending,
    }


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.loop:
        out = loop_boundedness()
    else:
        out = readiness_report()
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        lb = out.get("loop_boundedness", out)
        print(f"loop-boundedness: {lb.get('sessions')} sessions, "
              f"{lb.get('bounded')} bounded, {lb.get('unbounded')} unbounded "
              f"(threshold {lb.get('threshold')} entries)")
        for r in lb.get("top_unbounded", [])[:_REPORT_TOP_SHOWN]:
            print(f"  UNBOUNDED {r['sid']}: {r['entries']} entries")
        if "opus_avoided" in out:
            oa = out["opus_avoided"]
            print(f"opus-avoided: {oa['opus_avoided']}/{oa['opportunities']} "
                  f"({oa['status']})")
            print(f"dedup-hit: {out['dedup_hit']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
