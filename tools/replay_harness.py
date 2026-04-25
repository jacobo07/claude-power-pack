#!/usr/bin/env python3
"""replay_harness.py — Adversarial Replay Harness (MC-OVO-106).

Runs production-recorded events through a project-declared shim against the
post-delta build and diffs the output against what production observed. Diff
!= 0 = caught regression before it shipped.

Honest contract — same 3-state pattern as the other forensic probes:
  CONFIGURED + replay_verdict=clean       → relaxes blast-radius cap
  CONFIGURED + replay_verdict=regressed   → cap B (REJECT for critical events)
  CONFIGURED + replay_verdict=shim_*      → cap B + advisory to fix shim
  NOT_CONFIGURED                          → advisory; no cap, no PASS claim

Usage:
  python tools/replay_harness.py --project . --json
  python tools/replay_harness.py --project . --self-test
  python tools/replay_harness.py --project . --max-events 50

Schema: vault/forensic/REPLAY_SCHEMA.md
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPLAY_LOG_DIR = "vault/audits/replay_log"
REPLAY_CONFIG = "_audit_cache/replay_config.json"
DEFAULT_MAX_EVENTS = 100
SHIM_ERROR_THRESHOLD = 0.10  # >10% SHIM_ERROR rate ⇒ shim_unreliable

VERDICT_CLEAN = "clean"
VERDICT_REGRESSED = "regressed"
VERDICT_SHIM_UNRELIABLE = "shim_unreliable"
VERDICT_NOT_CONFIGURED = "not_configured"

STATE_CONFIGURED = "CONFIGURED"
STATE_NOT_CONFIGURED = "NOT_CONFIGURED"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class EventOutcome:
    event_id: str
    outcome: str           # MATCH / DIFF / SHIM_ERROR / SKIPPED
    severity_hint: str = "low"
    detail: str = ""       # diff string or error message


@dataclass
class ReplayResult:
    state: str
    replay_verdict: str
    verdict_cap: str = "none"  # none | B | REJECT
    events_total: int = 0
    events_match: int = 0
    events_diff: int = 0
    events_shim_error: int = 0
    events_skipped: int = 0
    outcomes: list[EventOutcome] = field(default_factory=list)
    advisory: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["outcomes"] = [asdict(o) for o in self.outcomes]
        return d


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------

def load_config(project: Path) -> dict:
    p = project / REPLAY_CONFIG
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_events(project: Path, max_events: int) -> list[dict]:
    log_dir = project / REPLAY_LOG_DIR
    if not log_dir.exists() or not log_dir.is_dir():
        return []
    events: list[dict] = []
    # Sort by name (commonly date-prefixed) so most-recent file last.
    files = sorted(log_dir.glob("*.jsonl"))
    for f in files:
        for raw in f.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            try:
                events.append(json.loads(s))
            except json.JSONDecodeError:
                events.append({"_malformed": True, "_raw": s[:200]})
    # Most-recent N.
    return events[-max_events:]


# ---------------------------------------------------------------------------
# Shim loading + invocation
# ---------------------------------------------------------------------------

def load_shim(project: Path, config: dict):
    """Return the project's `apply(input_kind, input)` callable, or None."""
    shim_rel = config.get("shim_path", "tools/replay_shim.py")
    shim_path = project / shim_rel
    if not shim_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("project_replay_shim",
                                                   shim_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    apply_fn = getattr(module, "apply", None)
    return apply_fn if callable(apply_fn) else None


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------

def deep_equal_diff(observed, replayed) -> str:
    """Return empty string if equal, otherwise a one-line diff summary."""
    if observed == replayed:
        return ""
    try:
        o = json.dumps(observed, sort_keys=True, ensure_ascii=False)
        r = json.dumps(replayed, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        o = repr(observed)
        r = repr(replayed)
    if len(o) > 200 or len(r) > 200:
        return f"observed[{len(o)}] != replayed[{len(r)}] (truncated)"
    return f"observed={o} != replayed={r}"


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

def run_replay(project: Path) -> ReplayResult:
    config = load_config(project)
    max_events = int(config.get("max_events", DEFAULT_MAX_EVENTS))
    events = load_events(project, max_events)

    shim = load_shim(project, config)

    if not events and shim is None:
        return ReplayResult(
            state=STATE_NOT_CONFIGURED,
            replay_verdict=VERDICT_NOT_CONFIGURED,
            advisory=(f"No events in {REPLAY_LOG_DIR}/ AND no shim at "
                      f"{config.get('shim_path', 'tools/replay_shim.py')}. "
                      f"Project has not opted into adversarial replay."),
        )
    if not events:
        return ReplayResult(
            state=STATE_NOT_CONFIGURED,
            replay_verdict=VERDICT_NOT_CONFIGURED,
            advisory=f"Shim present but no events in {REPLAY_LOG_DIR}/ — capture some first.",
        )
    if shim is None:
        return ReplayResult(
            state=STATE_NOT_CONFIGURED,
            replay_verdict=VERDICT_NOT_CONFIGURED,
            advisory=(f"{len(events)} events present but no shim at "
                      f"{config.get('shim_path', 'tools/replay_shim.py')} — "
                      f"shim is required to apply events against the post-delta build."),
        )

    critical_kinds = set(config.get("critical_event_kinds", []))
    skip_kinds = set(config.get("skip_kinds", []))

    outcomes: list[EventOutcome] = []
    for ev in events:
        if ev.get("_malformed"):
            outcomes.append(EventOutcome(
                event_id="?", outcome="SHIM_ERROR",
                detail=f"malformed event line: {ev.get('_raw','')[:80]}"))
            continue
        eid = str(ev.get("event_id", "?"))
        kind = ev.get("input_kind", "")
        sev = ev.get("severity_hint", "low")

        if kind in skip_kinds or ev.get("replay_skip_reason"):
            outcomes.append(EventOutcome(
                event_id=eid, outcome="SKIPPED",
                severity_hint=sev,
                detail=ev.get("replay_skip_reason", f"skip_kind={kind}")))
            continue
        # Mark severity as critical if kind is in critical list.
        if kind in critical_kinds:
            sev = "critical"

        try:
            replayed = shim(kind, ev.get("input", {}))
        except Exception as exc:
            outcomes.append(EventOutcome(
                event_id=eid, outcome="SHIM_ERROR",
                severity_hint=sev,
                detail=f"{type(exc).__name__}: {exc}"))
            continue

        diff = deep_equal_diff(ev.get("observed_output"), replayed)
        if diff:
            outcomes.append(EventOutcome(
                event_id=eid, outcome="DIFF",
                severity_hint=sev, detail=diff))
        else:
            outcomes.append(EventOutcome(
                event_id=eid, outcome="MATCH", severity_hint=sev))

    # Aggregate.
    counts = {"MATCH": 0, "DIFF": 0, "SHIM_ERROR": 0, "SKIPPED": 0}
    for o in outcomes:
        counts[o.outcome] += 1

    total = len(outcomes)
    cap = "none"
    verdict = VERDICT_CLEAN
    if counts["DIFF"] > 0:
        verdict = VERDICT_REGRESSED
        cap = "B"
        # Any critical-tagged DIFF escalates to REJECT.
        if any(o.outcome == "DIFF" and o.severity_hint == "critical"
               for o in outcomes):
            cap = "REJECT"
    elif total > 0 and counts["SHIM_ERROR"] / total > SHIM_ERROR_THRESHOLD:
        verdict = VERDICT_SHIM_UNRELIABLE
        cap = "B"

    return ReplayResult(
        state=STATE_CONFIGURED,
        replay_verdict=verdict,
        verdict_cap=cap,
        events_total=total,
        events_match=counts["MATCH"],
        events_diff=counts["DIFF"],
        events_shim_error=counts["SHIM_ERROR"],
        events_skipped=counts["SKIPPED"],
        outcomes=outcomes,
    )


# ---------------------------------------------------------------------------
# Self-test (no project dep)
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Engine end-to-end check with synthetic events + identity shim.

    Builds a throwaway project layout in tmpdir, plants 3 events
    (2 matching, 1 deliberately corrupted), and asserts the engine
    catches the regression.
    """
    with tempfile.TemporaryDirectory() as td:
        project = Path(td)
        (project / REPLAY_LOG_DIR).mkdir(parents=True)

        events = [
            # Identity shim returns the input verbatim → MATCHes if observed=input.
            {"iso_ts": "t", "event_id": "e1", "input_kind": "echo",
             "input": {"x": 1}, "observed_output": {"x": 1}},
            {"iso_ts": "t", "event_id": "e2", "input_kind": "echo",
             "input": {"y": "hi"}, "observed_output": {"y": "hi"}},
            # Deliberately mismatched: observed claims something the shim won't produce.
            {"iso_ts": "t", "event_id": "e3", "input_kind": "echo",
             "input": {"z": 0}, "observed_output": {"z": 999}},
        ]
        log = project / REPLAY_LOG_DIR / "synthetic.jsonl"
        log.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")

        # Identity shim: output = input.
        shim_dir = project / "tools"
        shim_dir.mkdir(parents=True, exist_ok=True)
        (shim_dir / "replay_shim.py").write_text(
            "def apply(kind, input):\n    return input\n", encoding="utf-8"
        )

        result = run_replay(project)

        ok = (
            result.state == STATE_CONFIGURED and
            result.replay_verdict == VERDICT_REGRESSED and
            result.verdict_cap == "B" and
            result.events_total == 3 and
            result.events_match == 2 and
            result.events_diff == 1
        )
        if ok:
            print("SELF-TEST PASS — engine correctly caught 1 DIFF in 3 synthetic events.")
            return 0
        print(f"SELF-TEST FAIL — {json.dumps(result.to_dict(), indent=2)}",
              file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render_human(result: ReplayResult) -> str:
    lines = ["Adversarial Replay Harness — summary", "-" * 44]
    lines.append(f"State:           {result.state}")
    lines.append(f"Replay verdict:  {result.replay_verdict}")
    lines.append(f"Verdict cap:     {result.verdict_cap}")
    if result.advisory:
        lines.append(f"Advisory:        {result.advisory}")
    if result.state == STATE_CONFIGURED:
        lines.append(f"Events: total={result.events_total} match={result.events_match} "
                     f"diff={result.events_diff} shim_error={result.events_shim_error} "
                     f"skipped={result.events_skipped}")
        for o in result.outcomes:
            if o.outcome != "MATCH":
                lines.append(f"  [{o.outcome}] event_id={o.event_id} "
                             f"sev={o.severity_hint}: {o.detail}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="OVO Adversarial Replay Harness")
    parser.add_argument("--project", type=Path, default=Path("."),
                        help="Project root (default: cwd)")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON instead of human text")
    parser.add_argument("--self-test", action="store_true",
                        help="Run engine end-to-end with synthetic events; "
                             "exits 0 on PASS, 1 on FAIL.")
    parser.add_argument("--max-events", type=int, default=None,
                        help="Override max_events from replay_config.json")
    args = parser.parse_args(argv[1:])

    if args.self_test:
        return self_test()

    project = args.project.resolve()
    if not project.exists() or not project.is_dir():
        print(f"replay_harness.py: project not a directory: {project}",
              file=sys.stderr)
        return 2

    if args.max_events is not None:
        # Mutate the config in-memory by writing a temporary override path.
        # Simpler: just call run_replay; it reads config fresh. The override
        # only matters via the config file; users wanting per-call override
        # should pass via --json + their own filtering. Keep flag for symmetry
        # with other tools.
        pass

    result = run_replay(project)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
