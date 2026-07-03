#!/usr/bin/env python3
"""process_governor.py -- FASE A Resource Governor for Transparent Process Hibernation.

Decides which LIVE claude.exe panes should HIBERNATE: be killed to reclaim RAM,
then transparently rehydrated on the next keystroke by the kclaude wrapper
(kclaude.ps1 park-and-resume). This is the process-layer sibling of CO-07/CO-08:

  * CO-08 scheduler.py  -- tells us which SESSIONS are HOT (a real transcript turn
                           within a window). This module INVERTS that: a pane that
                           is NOT hot AND idle past the threshold is a candidate.
  * CO-07 hibernation.py -- stores + integrity-verifies the frozen CONTEXT before
                           any kill (store-then-destroy). We REUSE it as the anchor
                           gate: a pane with no restorable anchor is never killed.

It EXTENDS both; it never reimplements them. The pure core -- ``decide`` / ``plan``
-- takes fully-resolved ``PaneProc`` records and is deterministic + unit-testable
with zero I/O. The Windows process scan (``scan_panes``) is a thin CIM adapter.

Never-hibernate invariants (fail-SAFE, in priority order):
  1. foreground pane            -- the Owner is looking at it
  2. a pane running /loop       -- a live autonomous loop must not be killed
  3. a HOT pane                 -- a real turn within HOT_WINDOW (CO-08 ground truth)
  4. idle age UNKNOWN           -- cannot prove it is idle -> keep (fail-safe)
  5. no resume anchor           -- hibernation.hibernate would REFUSE anyway
  6. not wakeable (raw pane)    -- FASE A does not reap non-rehydratable panes
                                   (Owner decision: "idle>15min + not-hot", no reap)

The worst outcome this module can produce is a MISSED ECONOMY (a pane that could
have hibernated stays alive), NEVER a killed pane that cannot be rehydrated and
NEVER a lost session. Fail-open ABSOLUTE: any error -> the pane is KEPT.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Default idle threshold (minutes). Owner-approved FASE A default (STOP #1).
IDLE_THRESHOLD_MIN = 15.0
# Tail bytes read per transcript to find the most-recent turn timestamp.
# Mirrors scheduler._TAIL_BYTES (proven cheap: newest turns live at EOF).
_TAIL_BYTES = 16384

# Wrapper kinds that can transparently rehydrate a killed pane. A pane launched
# with no kclaude wrapper ("none") cannot self-resume on a keystroke, so FASE A
# leaves it alive (reap is a deferred, separately-gated economy).
WAKEABLE_KINDS = frozenset({"ps1", "bat", "cmd"})

HIBERNATE = "hibernate"
KEEP = "keep"


@dataclass
class PaneProc:
    """A fully-resolved live claude.exe pane. Produced by scan_panes(); consumed
    by the pure decide(). ``wrapper_pid`` is the flag KEY the wrapper reads
    (kclaude.ps1 checks %TEMP%\\claude-hibernate-<wrapper_pid>.flag)."""
    pid: int                       # the claude.exe process id (the kill target)
    wrapper_pid: int               # parent kclaude wrapper pid (the flag key)
    sid: str | None = None         # session id (for --resume)
    cwd: str | None = None
    ws_mb: float = 0.0             # working-set MB (measured reclaim)
    idle_min: float | None = None  # minutes since last transcript turn (None=unknown)
    is_foreground: bool = False
    is_loop: bool = False
    wrapper_kind: str = "none"     # ps1 | bat | cmd | none
    has_anchor: bool = True        # a resume anchor (transcript .jsonl) exists
    transcript_path: str | None = None


@dataclass
class HibernateDecision:
    verdict: str                   # "hibernate" | "keep"
    pane: PaneProc
    reasons: list = field(default_factory=list)
    reclaim_mb: float = 0.0
    wakeable: bool = False


@dataclass
class GovernorPlan:
    decisions: list = field(default_factory=list)
    hibernate_count: int = 0
    keep_count: int = 0
    reclaim_mb: float = 0.0
    scanned: int = 0

    def hibernate_targets(self) -> list:
        return [d for d in self.decisions if d.verdict == HIBERNATE]


def decide(pane: PaneProc, *, idle_threshold_min: float = IDLE_THRESHOLD_MIN
           ) -> HibernateDecision:
    """Pure, deterministic hibernate/keep decision for one pane. Fail-safe: any
    never-hibernate invariant -> KEEP with the reason. Only a pane that clears
    EVERY invariant is a hibernate target."""
    wakeable = pane.wrapper_kind in WAKEABLE_KINDS
    reasons: list[str] = []

    if not pane.sid:
        reasons.append("no session id resolved -- cannot --resume (fail-safe keep)")
    if pane.is_foreground:
        reasons.append("foreground pane (Owner is looking at it)")
    if pane.is_loop:
        reasons.append("/loop running -- never kill a live autonomous loop")
    if pane.idle_min is None:
        reasons.append("idle age unknown -- cannot prove idle (fail-safe keep)")
    elif pane.idle_min < idle_threshold_min:
        reasons.append(
            f"active {pane.idle_min:.1f}min ago < {idle_threshold_min:.0f}min "
            f"threshold (hot)")
    if not pane.has_anchor:
        reasons.append("no resume anchor -- hibernation would REFUSE (fail-safe)")
    if not wakeable:
        reasons.append(
            f"wrapper '{pane.wrapper_kind}' cannot rehydrate -- reap deferred "
            f"(FASE A keeps it)")

    if reasons:
        return HibernateDecision(KEEP, pane, reasons, 0.0, wakeable)
    return HibernateDecision(
        HIBERNATE, pane,
        [f"idle {pane.idle_min:.1f}min, not hot/foreground/loop, anchor OK, "
         f"wakeable via {pane.wrapper_kind}"],
        pane.ws_mb, wakeable)


def plan(panes, *, idle_threshold_min: float = IDLE_THRESHOLD_MIN) -> GovernorPlan:
    """Decide across a set of panes and summarize the reclaim. Pure."""
    decisions = [decide(p, idle_threshold_min=idle_threshold_min)
                 for p in (panes or [])]
    hib = [d for d in decisions if d.verdict == HIBERNATE]
    return GovernorPlan(
        decisions=decisions,
        hibernate_count=len(hib),
        keep_count=len(decisions) - len(hib),
        reclaim_mb=round(sum(d.reclaim_mb for d in hib), 1),
        scanned=len(decisions))


# --- idle age reader (isolated; mirrors scheduler's proven tail pattern) ------
# Kept local rather than refactoring the sealed CO-08 scheduler: scheduler exposes
# a boolean "within window"; we need the actual AGE. Same tail-read discipline.

def last_turn_age_min(transcript_path, now: datetime | None = None,
                      tail_bytes: int = _TAIL_BYTES) -> float | None:
    """Minutes since the transcript's most-recent timestamped turn, or None if it
    cannot be read/parsed (treated as UNKNOWN -> fail-safe keep upstream)."""
    now = now or datetime.now(timezone.utc)
    try:
        p = Path(transcript_path)
        sz = p.stat().st_size
        with p.open("rb") as fh:
            if sz > tail_bytes:
                fh.seek(sz - tail_bytes)
            chunk = fh.read().decode("utf-8", "replace")
    except OSError:
        return None
    last = None
    for line in chunk.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = e.get("timestamp")
        if isinstance(ts, str) and len(ts) >= 19:
            try:
                d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                last = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    if last is None:
        return None
    return max(0.0, (now - last).total_seconds() / 60.0)


def hot_sids(proj_base=None, now: datetime | None = None,
             window_min: float | None = None) -> set:
    """Authoritative HOT session-id set from CO-08 scheduler (single source of
    truth for 'hot'). Fail-open -> empty set (nothing proven hot)."""
    try:
        from modules.cognitive_os import scheduler
        wm = window_min if window_min is not None else scheduler.HOT_WINDOW_MIN
        hot = scheduler.gather_hot_sessions(
            proj_base=proj_base, now=now, window_min=wm)
        return {h.get("sid") for h in hot if h.get("sid")}
    except Exception:  # noqa: BLE001 -- fail-open
        return set()


def anchor_exists(sid, cwd, transcript_path, proj_base=None) -> bool:
    """Reuse CO-07's exact anchor definition so the governor's has_anchor matches
    what hibernation.hibernate() will actually accept. Fail-open -> False (keep)."""
    try:
        from modules.cognitive_os import hibernation
        return hibernation._default_anchor_exists(  # noqa: SLF001 -- shared anchor def
            sid, cwd, transcript_path, proj_base)
    except Exception:  # noqa: BLE001
        return False


def _enc(cwd: str) -> str:
    """Claude Code's project-dir encoder (non-alnum -> '-'). Matches scheduler."""
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")


def enrich_panes(raw, *, now: datetime | None = None, proj_base=None) -> list:
    """Turn RAW scan records (from scan_panes.ps1) into fully-resolved PaneProc:
    derive the transcript path from (cwd, sid), read idle age + anchor from it,
    and read the per-pane idle age from its transcript tail.

    Idle age (minutes since the last turn) is the SOLE hotness signal here, at the
    15-min hibernation granularity -- deliberately NOT the CO-08 120-min launch-cap
    hot set, which would force-keep every pane active in the last 2h and defeat
    hibernation of the 20-119-min-idle panes that are exactly the targets.

    Raw record keys: pid, wrapper_pid, ws_mb, wrapper_kind, sid, cwd,
    is_foreground, is_loop. Fail-open per pane: any parse issue -> conservative
    (idle unknown / no anchor -> the governor keeps it)."""
    base = Path(proj_base) if proj_base else (Path.home() / ".claude" / "projects")
    panes: list[PaneProc] = []
    for r in (raw or []):
        sid = r.get("sid")
        cwd = r.get("cwd")
        tp = str(base / _enc(cwd) / f"{sid}.jsonl") if (sid and cwd) else None
        idle = last_turn_age_min(tp, now=now) if tp else None
        anchor = anchor_exists(sid, cwd, tp, proj_base) if sid else False
        try:
            panes.append(PaneProc(
                pid=int(r.get("pid", 0)),
                wrapper_pid=int(r.get("wrapper_pid", 0)),
                sid=sid, cwd=cwd, ws_mb=float(r.get("ws_mb", 0.0)),
                idle_min=idle,
                is_foreground=bool(r.get("is_foreground", False)),
                is_loop=bool(r.get("is_loop", False)),
                wrapper_kind=r.get("wrapper_kind", "none"),
                has_anchor=anchor, transcript_path=tp))
        except (ValueError, TypeError):
            continue
    return panes


def format_plan(gp: GovernorPlan) -> str:
    """ASCII Owner-facing summary of a governor plan."""
    lines = [f"# Resource Governor -- {gp.scanned} pane(s) scanned"]
    for d in gp.decisions:
        tag = "HIBERNATE" if d.verdict == HIBERNATE else "keep     "
        sid = (d.pane.sid or "?")[:8]
        head = (f"  [{tag}] pid={d.pane.pid} sid={sid} "
                f"ws={d.pane.ws_mb:.0f}MB")
        lines.append(head)
        for r in d.reasons:
            lines.append(f"             - {r}")
    lines.append(
        f"# hibernate {gp.hibernate_count} / keep {gp.keep_count} "
        f"-> reclaim ~{gp.reclaim_mb:.0f}MB")
    return "\n".join(lines)


def main(argv=None) -> int:  # pragma: no cover - thin CLI; scan is Windows-only
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--idle-min", type=float, default=IDLE_THRESHOLD_MIN)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--panes-json", default=None,
                    help="path to a JSON list of pre-enriched PaneProc dicts")
    ap.add_argument("--from-scan", default=None,
                    help="path to a RAW scan_panes.ps1 JSON array; enriched here")
    ap.add_argument("--proj-base", default=None)
    args = ap.parse_args(argv)

    panes: list[PaneProc] = []
    if args.from_scan and Path(args.from_scan).is_file():
        try:
            raw = json.loads(Path(args.from_scan).read_text(encoding="utf-8-sig"))
            panes = enrich_panes(raw, proj_base=args.proj_base)
        except (ValueError, OSError, TypeError):
            pass
    elif args.panes_json and Path(args.panes_json).is_file():
        try:
            raw = json.loads(Path(args.panes_json).read_text(encoding="utf-8-sig"))
            for r in raw:
                panes.append(PaneProc(
                    pid=int(r.get("pid", 0)),
                    wrapper_pid=int(r.get("wrapper_pid", 0)),
                    sid=r.get("sid"), cwd=r.get("cwd"),
                    ws_mb=float(r.get("ws_mb", 0.0)),
                    idle_min=r.get("idle_min"),
                    is_foreground=bool(r.get("is_foreground", False)),
                    is_loop=bool(r.get("is_loop", False)),
                    wrapper_kind=r.get("wrapper_kind", "none"),
                    has_anchor=bool(r.get("has_anchor", True)),
                    transcript_path=r.get("transcript_path")))
        except (ValueError, OSError, TypeError):
            pass

    gp = plan(panes, idle_threshold_min=args.idle_min)
    if args.json:
        print(json.dumps({
            "hibernate_count": gp.hibernate_count, "keep_count": gp.keep_count,
            "reclaim_mb": gp.reclaim_mb, "scanned": gp.scanned,
            "targets": [{"pid": d.pane.pid, "wrapper_pid": d.pane.wrapper_pid,
                         "sid": d.pane.sid, "cwd": d.pane.cwd,
                         "ws_mb": d.pane.ws_mb} for d in gp.hibernate_targets()]}))
    else:
        print(format_plan(gp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
