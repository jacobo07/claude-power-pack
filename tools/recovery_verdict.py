#!/usr/bin/env python3
"""recovery_verdict.py -- the live surface that makes the recovery arbiter judge.

`session_resilience/acceptance.py` (G4) scores a restored session against the state it
was meant to reproduce and returns RECOVERED / PARTIAL / FAILED. It shipped with tests,
was never called by any hook, command or task, and so has never judged a single real
recovery. That is why an incomplete restore is silently accepted: nothing scores it.

This tool is the missing producer. It reads two pane_map payloads -- the topology PP
recorded BEFORE the interruption (reference) and the one live NOW (observed) -- lifts
both into the canonical description `models` expects, and asks the arbiter for a verdict.

HONEST SCOPE. pane_map records terminals and their conversations; it knows nothing about
editor tabs, tab order, focus or scroll. Those dimensions are therefore declared
UNMEASURABLE-BY-THIS-SOURCE and excluded from the denominator via the arbiter's own
capability-aware path -- reported, never assumed passing. A verdict that silently scored
four dimensions it cannot see would be the fake recovery this whole effort exists to end.

What it CAN prove is exactly what keeps failing:
  - windows        -- did every repo window come back?
  - terminals      -- did every pane come back, in the right cwd?
  - conversations  -- did each pane come back on ITS OWN session, or did N panes collapse
                      onto one? ("only one recovered session per pane")

Exit 0 = RECOVERED. Exit 3 = PARTIAL/FAILED (a real, reportable shortfall). Exit 2 = the
verdict could not be computed -- held, never silently passed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.session_resilience import acceptance, epoch, models  # noqa: E402

# The dimensions a pane_map can actually witness. The rest are excluded from the
# denominator rather than scored as passes.
OBSERVABLE = frozenset({"windows", "terminals", "conversations"})

STATE_DIR = Path.home() / ".claude" / "state"
HISTORY_DIR = STATE_DIR / "pane_map_history"
RECEIPTS_DIR = _ROOT / "vault" / "recovery"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def to_description(payload: dict) -> dict:
    """pane_map -> the canonical description in models' schema.

    One window per repo (that is what a Cursor window is here); one terminal per pane.
    `pane_id` is the pane's own session id, and `conversation_id` is the same value --
    which is precisely the point: if a restore collapses three panes onto one session,
    three distinct pane->conversation triples become one, and the conversations dimension
    misses. That collapse is the "only one recovered session per pane" symptom, and this
    is where it becomes measurable.
    """
    windows: dict[str, dict] = {}
    for pane in payload.get("panes") or []:
        repo = str(pane.get("repo") or "")
        cwd = str(pane.get("cwd") or "")
        sid = str(pane.get("sessionId") or "")
        w = windows.setdefault(repo, {
            "window_id": repo,
            "workspace_path": cwd,
            "foreground": False,
            "terminals": [],
            "editor": {},
        })
        w["terminals"].append({"cwd": cwd, "pane_id": sid, "conversation_id": sid})
    return {"schema": models.SCHEMA_VERSION, "windows": list(windows.values())}


def _live_only(payload: dict) -> dict:
    """Observed state = the panes that actually came back, not the ones merely listed.

    pane_map enumerates every recent pane; a restore is judged on what is LIVE. Trusting
    the full list would score a dead pane as recovered -- the map is not the territory.
    """
    panes = [p for p in (payload.get("panes") or []) if p.get("live")]
    return {**payload, "panes": panes}


def newest_snapshot() -> Path | None:
    """The freshest snapshot on disk. NOT a valid reference after an interruption:
    the 5-minute snapshotter keeps running once the panes come back, so within
    ~20 minutes this file records the DAMAGE, and scoring the damage against
    itself always returns RECOVERED. Only used when no epoch is open (a routine
    check with nothing to recover from)."""
    if not HISTORY_DIR.is_dir():
        return None
    snaps = sorted(HISTORY_DIR.glob("pane_map_*.json"))
    return snaps[-1] if snaps else None


def resolve_reference() -> tuple[Path | None, dict | None, str]:
    """The reference this verdict must be scored against.

    When an epoch is OPEN, the reference is the snapshot PINNED at the interruption
    boundary -- the last topology recorded while the session was still alive. It is
    frozen: it cannot advance as the panes trickle back, so a loss stays visible.
    An open epoch whose pinned snapshot is missing yields no reference at all, and
    the caller HOLDS -- a recovery is never declared complete against a reference
    that does not exist.
    """
    ep = epoch.read_epoch(STATE_DIR)
    if ep and ep.get("status") == epoch.OPEN:
        pinned = epoch.reference_path(STATE_DIR, ep)
        return pinned, ep, "pinned"
    return newest_snapshot(), ep, "newest"


# Kept for callers/tests that predate the epoch.
latest_reference = newest_snapshot


def verdict(reference: dict, observed: dict) -> tuple[acceptance.GateDecision,
                                                      acceptance.Scorecard, list[str]]:
    criteria = acceptance.AcceptanceCriteria(required=frozenset(OBSERVABLE))
    card = acceptance.score_recovery(reference, observed, criteria)
    decision = acceptance.acceptance_gate(card, criteria, host_capabilities=OBSERVABLE)
    _, missing = acceptance.classify(card, criteria, host_capabilities=OBSERVABLE)
    return decision, card, missing


def summarize(reference: dict, observed: dict) -> dict[str, str]:
    """Per-dimension shortfall in numbers a human can act on.

    The arbiter's `detail` is the full expected-vs-actual tuple list -- 20k characters
    for 68 panes. A verdict nobody can read is a verdict nobody acts on, so the counts
    and the first few missing panes carry the message; the receipt keeps the rest.
    """
    out: dict[str, str] = {}
    for dim in sorted(OBSERVABLE):
        ref = set(models.EXTRACTORS[dim](reference))
        obs = set(models.EXTRACTORS[dim](observed))
        lost = sorted(ref - obs)
        line = f"{len(obs)}/{len(ref)} recovered"
        if lost:
            shown = ", ".join(str(x[0]) if isinstance(x, tuple) else str(x) for x in lost[:4])
            line += f"; {len(lost)} missing ({shown}{', ...' if len(lost) > 4 else ''})"
        out[dim] = line
    return out


def _receipt(decision, card, missing: list[str], ref_path: Path, now: datetime,
             summary: dict[str, str]) -> Path:
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    path = RECEIPTS_DIR / f"recovery_{stamp}.md"
    lines = [
        f"# Recovery verdict -- {decision.verdict}",
        "",
        f"- when: {now.isoformat()}",
        f"- reference: {ref_path.name}",
        f"- observed: live panes in ~/.claude/state/pane_map.json",
        f"- reason: {decision.reason}",
        "",
        "## Dimensions",
        "",
        "| dimension | matched | detail |",
        "|---|---|---|",
    ]
    for name, res in sorted(card.dimensions.items()):
        lines.append(f"| {name} | {'yes' if res.matched else 'NO'} | "
                     f"{summary.get(name, res.detail)} |")
    lines += [
        "",
        "## Not witnessed by this source (excluded from the denominator, not passed)",
        "",
        "- " + ", ".join(sorted(set(models.DIMENSIONS) - OBSERVABLE)),
    ]
    if missing:
        lines += ["", "## Shortfalls", ""] + [f"- {m}" for m in missing]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Judge the last workspace restore.")
    ap.add_argument("--reference", help="pane_map snapshot to compare against")
    ap.add_argument("--observed", help="pane_map payload to score (default: the live one)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-receipt", action="store_true")
    args = ap.parse_args(argv)

    ep, source = None, "explicit"
    if args.reference:
        ref_path = Path(args.reference)
    else:
        ref_path, ep, source = resolve_reference()
    obs_path = Path(args.observed) if args.observed else STATE_DIR / "pane_map.json"

    if ref_path is None or not ref_path.is_file():
        if ep and ep.get("status") == epoch.OPEN:
            print("HELD: an interruption is open "
                  f"(since {ep.get('interrupted_at')}) but its pinned reference "
                  f"({ep.get('reference_file')}) is not on disk. A recovery cannot be "
                  "declared complete against a reference that does not exist.")
        else:
            print("HELD: no pre-interruption snapshot to compare against "
                  "(~/.claude/state/pane_map_history is empty). A recovery cannot be "
                  "declared complete against a reference that does not exist.")
        return 2
    if not obs_path.is_file():
        print(f"HELD: no observed pane_map at {obs_path}")
        return 2

    try:
        # BOTH sides are live-filtered. Scoring every pane the map has ever seen against
        # the ones alive now does not ask "did the restore work?" -- it asks "is anything
        # that ever existed still running?", which no restore could ever satisfy. The
        # question is: of the panes that were ALIVE, how many are alive again?
        reference = to_description(_live_only(_read_json(ref_path)))
        observed = to_description(_live_only(_read_json(obs_path)))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"HELD: cannot read a pane_map ({exc.__class__.__name__}: {exc})")
        return 2

    decision, card, missing = verdict(reference, observed)
    summary = summarize(reference, observed)
    now = datetime.now(timezone.utc)

    # A verdict scored against an open epoch is the judgment OF that recovery, so it
    # belongs on the epoch: RECOVERED closes it, a shortfall keeps it open and keeps
    # surfacing until it is really recovered or the Owner dismisses it.
    if source == "pinned" and not args.observed:
        epoch.record_verdict(STATE_DIR, decision.verdict, missing)

    if args.json:
        print(json.dumps({
            "verdict": decision.verdict,
            "allow_complete": decision.allow_complete,
            "reason": decision.reason,
            "reference": ref_path.name,
            "reference_source": source,
            "interrupted_at": (ep or {}).get("interrupted_at"),
            "dimensions": {k: {"matched": v.matched, "summary": summary.get(k, "")}
                           for k, v in card.dimensions.items()},
        }, indent=2))
    else:
        if source == "pinned":
            print(f"interruption at {(ep or {}).get('interrupted_at')} "
                  f"-- scored against the topology pinned before it ({ref_path.name})")
        elif source == "newest":
            print(f"no open interruption -- scored against the newest snapshot "
                  f"({ref_path.name}); this cannot witness a loss, it is a routine check")
        print(f"{decision.verdict} -- {decision.reason}")
        for name, res in sorted(card.dimensions.items()):
            print(f"  {'ok  ' if res.matched else 'MISS'} {name}: {summary.get(name, '')}")

    if not args.no_receipt:
        path = _receipt(decision, card, missing, ref_path, now, summary)
        print(f"receipt: {path}")

    return 0 if decision.allow_complete else 3


if __name__ == "__main__":
    raise SystemExit(main())
