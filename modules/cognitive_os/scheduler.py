#!/usr/bin/env python3
"""scheduler.py -- CO-08: hard hot-session cap (the 48h-burn systemic fix).

Where repo_coordinator (W4) DETECTS a second same-repo pane and the parallel-burn
pattern but only ADVISES, this promotes those detectors into an admission gate
with a real cap. The cap governs two coupled limits (CO-08 dataset, Part I.2):

  * GLOBAL hot-session cap (HOT_CAP=2) -- the TCO doctrine "max 2 active; a 3rd
    frees one first".
  * SAME-REPO hot cap (SAME_REPO_CAP=1) -- the literal burn pattern was multiple
    hot panes on the SAME repo re-deriving overlapping context; gated hardest.

A NEW session is REFUSED when launching it would exceed EITHER limit. The refusal
has no bypass flag (CO-08 III.4 / CO-00 II.4): it can only be SATISFIED -- resume
the existing session, /compact-or-close the longest hot session to free a slot,
or run the work as bounded subagents in the existing session (CO-09). RESUMING an
already-hot session consumes no new slot -> always proceeds. Fail-open ABSOLUTE:
any error -> proceed (never block a launch on a kernel bug).

"Hot" is defined from GROUND TRUTH, accurately and cheaply (this was empirically
calibrated 2026-06-30): a session is hot iff its transcript holds a real TURN
whose own timestamp is within HOT_WINDOW_MIN. File mtime alone over-counts
(background hooks bump mtimes -> 45 false positives observed); pane_map
lastActivity under-counts (stale -> 0). So the gate:
  1. stat-filters to mtime-recent transcripts (cheap; mtime>=T is implied by any
     turn at T, so this pre-filter is lossless),
  2. TAIL-reads each (last ~16KB) for the most-recent turn timestamp (~4ms total),
  3. DEDUPES by session id -- one session that spans several working dirs (each
     getting its own project transcript) is ONE hot session, not several.

Pure core: decide(hot, cwd, is_new, ...) -- unit-testable, no I/O. Each `hot`
item is {sid, encs:[encoded-project-dirs]} OR {cwd, sid} (single cwd); decide
normalizes both. I/O: gather_hot_sessions() + admit().
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Cap defaults (CO-08 I.2). Env-tunable, never unbounded.
HOT_CAP = int(os.environ.get("PP_HOT_SESSION_CAP", "2"))
SAME_REPO_CAP = int(os.environ.get("PP_SAME_REPO_HOT_CAP", "1"))
# "Hot" recency window. 120min mirrors repo_coordinator's max_age_hours=2.
HOT_WINDOW_MIN = float(os.environ.get("PP_HOT_WINDOW_MIN", "120"))
# Tail bytes read per transcript to find the most-recent turn timestamp.
_TAIL_BYTES = 16384


@dataclass
class CapVerdict:
    verdict: str                       # "proceed" | "refuse"
    reasons: list = field(default_factory=list)
    satisfy: list = field(default_factory=list)
    hot_count: int = 0                 # distinct global hot sessions
    same_repo_count: int = 0           # distinct hot sessions on this cwd
    cap: int = HOT_CAP
    source: str = ""                   # proceed | refuse | error


def _enc(cwd: str) -> str:
    """Claude Code's project-dir encoder: non-alnum -> '-'."""
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")


def _item_encs(item: dict) -> list:
    """Encoded-project-dir set for a hot item, accepting both shapes:
    {encs:[...]} (real gather) or {cwd:...} (injected test item)."""
    encs = item.get("encs")
    if encs:
        return list(encs)
    return [_enc(item.get("cwd", ""))]


def decide(hot, cwd, *, is_new=True,
           cap: int = HOT_CAP, same_repo_cap: int = SAME_REPO_CAP) -> CapVerdict:
    """Pure cap decision. `hot` = distinct currently-hot sessions (the
    about-to-launch one is NOT in it). Resuming -> proceed."""
    same_enc = _enc(cwd)
    same_repo = [h for h in hot if same_enc in _item_encs(h)]
    n_global = len(hot)
    n_same = len(same_repo)

    if not is_new:
        return CapVerdict("proceed", ["resume -- no new hot slot consumed"],
                          [], n_global, n_same, cap, "proceed")

    reasons: list[str] = []
    satisfy: list[str] = []

    if n_same >= same_repo_cap:
        reasons.append(
            f"{n_same} hot session(s) already on this repo "
            f"({Path(cwd).name or cwd}); same-repo cap is {same_repo_cap}")
        sid = same_repo[0].get("sid")
        satisfy.append(
            "resume the existing session"
            + (f" (--resume {sid})" if sid else "")
            + " instead of a 2nd hot pane")
        satisfy.append("or run the extra work as bounded subagents in it (CO-09)")

    if n_global + 1 > cap:
        reasons.append(
            f"{n_global} hot sessions already active; global cap is {cap} "
            f"(a new pane would make {n_global + 1})")
        satisfy.append(
            "free a slot first: /compact or close the longest-running hot session")

    if reasons:
        return CapVerdict("refuse", reasons, satisfy, n_global, n_same, cap,
                          "refuse")
    return CapVerdict("proceed", ["under cap"], [], n_global, n_same, cap,
                      "proceed")


def _last_turn_within(path: Path, start: datetime,
                      tail_bytes: int = _TAIL_BYTES) -> bool:
    """True iff the transcript's most-recent timestamped turn is >= start.
    Tail-reads only the last `tail_bytes` (the newest turns are at EOF), so this
    is O(tail) per file, not O(file). The most-recent turn dominates 'hot'."""
    try:
        sz = path.stat().st_size
        with path.open("rb") as fh:
            if sz > tail_bytes:
                fh.seek(sz - tail_bytes)
            chunk = fh.read().decode("utf-8", "replace")
    except OSError:
        return False
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
    return last is not None and last >= start


def gather_hot_sessions(proj_base=None, now: datetime | None = None,
                        window_min: float = HOT_WINDOW_MIN,
                        exclude_sid: str | None = None,
                        tail_bytes: int = _TAIL_BYTES) -> list:
    """Distinct currently-hot sessions across ALL project dirs, from ground
    truth (a real turn within `window_min`). Deduped by sid: a session spanning
    several working dirs is ONE entry whose `encs` lists every project dir it
    appears under. Fail-open -> []."""
    try:
        now = now or datetime.now(timezone.utc)
        start = now - timedelta(minutes=window_min)
        cutoff = start.timestamp()
        base = Path(proj_base) if proj_base else (
            Path.home() / ".claude" / "projects")
        if not base.is_dir():
            return []
        by_sid: dict[str, dict] = {}
        for sub in base.iterdir():
            if not sub.is_dir():
                continue
            for jf in sub.glob("*.jsonl"):
                if "subagent" in str(jf).lower():
                    continue
                try:
                    if jf.stat().st_mtime < cutoff:      # cheap lossless prefilter
                        continue
                except OSError:
                    continue
                sid = jf.stem
                if exclude_sid and sid == exclude_sid:
                    continue
                if not _last_turn_within(jf, start, tail_bytes):
                    continue
                entry = by_sid.setdefault(sid, {"sid": sid, "encs": []})
                if sub.name not in entry["encs"]:
                    entry["encs"].append(sub.name)
        return list(by_sid.values())
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def admit(cwd: str, *, is_new: bool = True, proj_base=None,
          now: datetime | None = None, exclude_sid: str | None = None,
          cap: int = HOT_CAP, same_repo_cap: int = SAME_REPO_CAP,
          window_min: float = HOT_WINDOW_MIN,
          gather_fn=None) -> CapVerdict:
    """I/O composition: gather hot sessions, then decide. Fail-open -> proceed."""
    try:
        hot = (gather_fn or gather_hot_sessions)(
            proj_base=proj_base, now=now, window_min=window_min,
            exclude_sid=exclude_sid)
        return decide(hot, cwd, is_new=is_new, cap=cap,
                      same_repo_cap=same_repo_cap)
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return CapVerdict("proceed", ["cap check errored -- fail-open"], [],
                          0, 0, cap, "error")


def format_refusal(v: CapVerdict) -> str:
    """Owner-facing refusal block (ASCII). Empty string when proceeding."""
    if v.verdict != "refuse":
        return ""
    head = (f"PP CO-08: hot-session cap reached -- new pane refused "
            f"({v.hot_count} hot, cap {v.cap}).")
    why = "\n".join(f"  - {r}" for r in v.reasons)
    how = "\n".join(f"  > {s}" for s in v.satisfy)
    return (f"{head}\n{why}\nSatisfy (no bypass -- only these make it fit):\n"
            f"{how}")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--is-new", choices=("true", "false"), default="true")
    ap.add_argument("--proj-base", default=None)
    ap.add_argument("--exclude-sid", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    v = admit(args.cwd or os.getcwd(), is_new=(args.is_new == "true"),
              proj_base=args.proj_base, exclude_sid=args.exclude_sid)
    if args.json:
        print(json.dumps({
            "verdict": v.verdict, "reasons": v.reasons, "satisfy": v.satisfy,
            "hot_count": v.hot_count, "same_repo_count": v.same_repo_count,
            "cap": v.cap, "source": v.source}))
    elif v.verdict == "refuse":
        print(format_refusal(v))
    else:
        print(f"# proceed ({v.hot_count} hot, cap {v.cap}, "
              f"same-repo {v.same_repo_count})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
