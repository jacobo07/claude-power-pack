#!/usr/bin/env python3
"""recall_roi.py -- D3: measure KB recall ROI so eviction becomes evidence-based.

The knowledge base is write-optimized and never GC'd: injection cost is paid on every
prompt (the JIT loader put a 13.4 KB spec into a strategy prompt this session), but
whether an injected item ever earned its keep is unmeasured. Dead knowledge is
indistinguishable from load-bearing knowledge, so nothing can be retired safely and
the KB (and its token tax) grows monotonically.

REUSE, NOT FORK: the JIT loader ALREADY records every injection to
vault/telemetry/jit_usage_<sid>.jsonl (module / bytes / spec_path / session_id / ts).
D3 does not add a parallel producer -- it READS that existing log (closing the
write->read loop the loader's producer left open) and turns it into two things:

  1. co12_metrics()          -- kb_injection_count + distinct lessons/sessions +
                                ceps_recurrence, surfaced through CO-12's readiness
                                report (the single instrument; recall_roi feeds it,
                                never forks a parallel accountant).
  2. retirement_candidates() -- KB items (vault/specs/*.md) never injected in the
                                window. FIRM once the corpus spans >= window_days;
                                PROVISIONAL while it is shorter (never used in N days
                                of real data, but not yet the full 90-day proof).

Fail-open ABSOLUTE: any error -> empty/benign result, never an exception.
"""
from __future__ import annotations

import glob
import json
import os
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
_SECONDS_PER_DAY = 86400.0
DEFAULT_WINDOW_DAYS = float(os.environ.get("PP_RECALL_RETIRE_DAYS", "90"))


def _telemetry_dir(td=None) -> Path:
    return Path(td) if td else (_PP_ROOT / "vault" / "telemetry")


def _specs_dir() -> Path:
    return _PP_ROOT / "vault" / "specs"


def _lesson_key(row: dict):
    """The identity of the injected KB item. A spec injection carries spec_path;
    a module injection carries its module name."""
    if row.get("module") == "__spec__" and row.get("spec_path"):
        return Path(str(row["spec_path"])).name          # spec basename
    m = row.get("module")
    return m if m and m != "__spec__" else None


def _read_usage(td=None) -> list:
    rows = []
    try:
        for fp in glob.glob(str(_telemetry_dir(td) / "jit_usage_*.jsonl")):
            try:
                for line in Path(fp).read_text(encoding="utf-8", errors="replace").split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        continue
            except OSError:
                continue
    except OSError:
        return []
    return rows


def injection_stats(td=None, *, now=None) -> dict:
    """Per-lesson injection aggregation from the JIT usage log. Fail-open."""
    try:
        rows = _read_usage(td)
        now = now if now is not None else time.time()
        per = {}
        all_ts = []
        for r in rows:
            key = _lesson_key(r)
            if not key:
                continue
            ts = r.get("ts")
            try:
                ts = float(ts) if ts is not None else None
            except (TypeError, ValueError):
                ts = None
            if ts is not None:
                all_ts.append(ts)
            d = per.setdefault(key, {"count": 0, "bytes": 0, "sessions": set(),
                                     "first_ts": None, "last_ts": None})
            d["count"] += 1
            try:
                d["bytes"] += int(r.get("bytes", 0) or 0)
            except (TypeError, ValueError):
                pass
            sid = r.get("session_id")
            if sid:
                d["sessions"].add(sid)
            if ts is not None:
                d["first_ts"] = ts if d["first_ts"] is None else min(d["first_ts"], ts)
                d["last_ts"] = ts if d["last_ts"] is None else max(d["last_ts"], ts)
        corpus_span = ((now - min(all_ts)) / _SECONDS_PER_DAY) if all_ts else 0.0
        # normalize sessions set -> count for a JSON-safe view
        per_out = {k: {"count": v["count"], "bytes": v["bytes"],
                       "sessions": len(v["sessions"]), "last_ts": v["last_ts"]}
                   for k, v in per.items()}
        return {"per_lesson": per_out, "raw": per,
                "total_injections": sum(v["count"] for v in per.values()),
                "distinct_lessons": len(per),
                "distinct_sessions": len({s for v in per.values() for s in v["sessions"]}),
                "corpus_span_days": round(corpus_span, 1)}
    except Exception:  # noqa: BLE001 -- fail-open
        return {"per_lesson": {}, "raw": {}, "total_injections": 0,
                "distinct_lessons": 0, "distinct_sessions": 0, "corpus_span_days": 0.0}


def ceps_recurrence(ceps_path=None) -> dict:
    """Recurrent CEPS concepts (an error pattern that has fired more than once).
    Prefer distinct-session recurrence when the events carry a session id; CEPS
    events do not, so fall back to per-signature occurrence count (>= 2 = recurrent).
    Best-effort, fail-open -> {}."""
    try:
        candidates = ([Path(ceps_path)] if ceps_path else
                      [_PP_ROOT / "vault" / "ceps" / "events.jsonl",
                       Path.home() / ".claude" / "state" / "ceps" / "events.jsonl",
                       _PP_ROOT / "modules" / "cascade_prevention" / "events.jsonl"])
        path = next((p for p in candidates if p.is_file()), None)
        if not path:
            return {}
        counts, sessions = {}, {}
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            concept = (ev.get("pattern_signature") or ev.get("category")
                       or ev.get("signature") or ev.get("pattern"))
            if not concept:
                continue
            concept = str(concept)
            counts[concept] = counts.get(concept, 0) + 1
            sid = ev.get("session_id") or ev.get("sid")
            if sid:
                sessions.setdefault(concept, set()).add(str(sid))
        if any(sessions.values()):
            return {c: len(s) for c, s in sessions.items() if len(s) >= 2}
        return {c: n for c, n in counts.items() if n >= 2}
    except Exception:  # noqa: BLE001 -- fail-open
        return {}


def kb_injection_count(td=None, *, now=None) -> dict:
    s = injection_stats(td, now=now)
    return {"total_injections": s["total_injections"],
            "distinct_lessons": s["distinct_lessons"],
            "distinct_sessions": s["distinct_sessions"],
            "corpus_span_days": s["corpus_span_days"]}


def co12_metrics(td=None, *, ceps_path=None, now=None) -> dict:
    """The recall-ROI slice CO-12's readiness_report surfaces (single instrument)."""
    kc = kb_injection_count(td, now=now)
    rec = ceps_recurrence(ceps_path)
    measured = kc["total_injections"] > 0
    return {
        "kb_injection_count": kc["total_injections"],
        "distinct_lessons": kc["distinct_lessons"],
        "distinct_sessions": kc["distinct_sessions"],
        "corpus_span_days": kc["corpus_span_days"],
        "ceps_recurrent_concepts": len(rec),
        "status": ("live" if measured else
                   "instrument-pending -- no jit_usage rows yet"),
        "measured": measured,
    }


def retirement_candidates(kb_items=None, td=None, *, window_days=DEFAULT_WINDOW_DAYS,
                          now=None) -> dict:
    """KB items never injected in the window. FIRM once the corpus spans >=
    window_days; PROVISIONAL while shorter (never used in the whole corpus but not
    yet the full proof). Fail-open."""
    try:
        now = now if now is not None else time.time()
        stats = injection_stats(td, now=now)
        raw = stats["raw"]
        inv = list(kb_items) if kb_items is not None else [
            p.name for p in sorted(_specs_dir().glob("*.md"))]
        cutoff = now - window_days * _SECONDS_PER_DAY
        recent = {k for k, v in raw.items()
                  if v.get("last_ts") is not None and v["last_ts"] >= cutoff}
        ever = {k for k, v in raw.items() if v.get("count", 0) > 0}
        span = stats["corpus_span_days"]
        sufficient = span >= window_days
        firm, provisional = [], []
        for item in inv:
            if item in recent:
                continue
            if sufficient:
                firm.append(item)
            elif item not in ever:
                provisional.append(item)
        return {"firm": firm, "provisional": provisional,
                "meta": {"corpus_span_days": span, "window_days": window_days,
                         "sufficient_history": sufficient, "tracked": len(inv),
                         "injected_ever": len([i for i in inv if i in ever])}}
    except Exception:  # noqa: BLE001 -- fail-open
        return {"firm": [], "provisional": [], "meta": {"error": True}}


def write_retirement_report(kb_items=None, td=None, *, out_path=None,
                            window_days=DEFAULT_WINDOW_DAYS, now=None) -> Path:
    r = retirement_candidates(kb_items, td, window_days=window_days, now=now)
    m = r["meta"]
    lines = [
        "# RETIREMENT_CANDIDATES -- KB recall-ROI (D3)", "",
        f"Corpus span {m.get('corpus_span_days')}d over a {m.get('window_days')}d window "
        f"| {m.get('tracked')} KB items tracked, {m.get('injected_ever')} ever injected.",
        "",
        ("Retirement is evidence-based: an item never injected in the window is a "
         "candidate. FIRM requires the corpus to span the full window; PROVISIONAL "
         "means never injected in the (shorter) corpus so far -- a lead, not yet proof."),
        "",
    ]
    if r["firm"]:
        lines += ["## FIRM candidates (never injected in the full window)", ""]
        lines += [f"- {c}" for c in r["firm"]] + [""]
    if r["provisional"]:
        lines += [f"## PROVISIONAL candidates (never injected in {m.get('corpus_span_days')}d so far)", ""]
        lines += [f"- {c}" for c in r["provisional"]] + [""]
    if not r["firm"] and not r["provisional"]:
        lines += ["## Candidates", "",
                  "(none -- every tracked KB item was injected within the window)", ""]
    out = Path(out_path) if out_path else (_PP_ROOT / "vault" / "audits" / "RETIREMENT_CANDIDATES.md")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="D3 Recall-ROI Instrumentation")
    ap.add_argument("--metrics", action="store_true", help="CO-12 recall-roi slice")
    ap.add_argument("--report", action="store_true", help="write RETIREMENT_CANDIDATES.md")
    ap.add_argument("--window-days", type=float, default=DEFAULT_WINDOW_DAYS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.metrics or not args.report:
        m = co12_metrics()
        print(json.dumps(m, indent=2) if args.json else
              f"kb_injection_count={m['kb_injection_count']} lessons={m['distinct_lessons']} "
              f"sessions={m['distinct_sessions']} span={m['corpus_span_days']}d "
              f"ceps_recurrent={m['ceps_recurrent_concepts']}")
    if args.report:
        r = retirement_candidates(window_days=args.window_days)
        p = write_retirement_report(window_days=args.window_days)
        print(f"wrote {p}: firm={len(r['firm'])} provisional={len(r['provisional'])} "
              f"(span {r['meta'].get('corpus_span_days')}d)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
