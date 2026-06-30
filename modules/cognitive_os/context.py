#!/usr/bin/env python3
"""context.py -- CO-00: effective-context estimate + bands + the 60% ceiling.

The root law: the effective context of any session never exceeds 60%, defended
PROJECTIVELY from the 45-55% action band. This module supplies the kernel's single
effective-context read, composing the existing sensors (CO-00 I.4) -- it does NOT
invent a new one:

  PRIMARY  -- the statusline bridge `<TEMP>/claude-ctx-<sid>.json` written by the
              statusline on every render: {used_pct, remaining_percentage,
              timestamp}. The closest thing to a host ground-truth context %.
              Trusted ONLY when fresh (timestamp within STALE_S); a stale bridge
              is the documented failure mode (CO-00 III.3) -- empirically the
              bridge files on this host were ~3h old, so freshness is load-bearing.
  SECONDARY -- the live transcript jsonl size (the same proxy context_monitor uses:
              16MB COMPACT / 24MB KCLEAR). Used when the bridge is stale/missing,
              with the pct reported as None (unknown) and confidence low. RAM is
              deliberately NOT probed here (it spawns PowerShell ~600ms) -- the
              launch path must stay fast; ram_guard is a tie-breaker elsewhere.

Honesty rule: a stale/missing signal yields band UNKNOWN, never a fabricated GREEN
(CO-00 anti-pattern "optimistic measurement").

Bands (CO-00 I.2): GREEN <=45, AMBER 45-55 (action band), RED 55-60 (pre-ceiling),
BREACH >60 (incident). resume_advisory() returns the honest rung-2 advisory for a
RED/BREACH resume target -- a *block* on resume is counterproductive (a session
must be opened to be /compact-ed), so the resume case is advisory; the true rung-3
block lives in the cap (CO-08) and loop admission (CO-09).
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

GREEN, AMBER, RED, BREACH, UNKNOWN = "GREEN", "AMBER", "RED", "BREACH", "UNKNOWN"

# CO-00 I.2 band edges (effective context %).
GREEN_MAX = 45.0
AMBER_MAX = 55.0
CEILING = 60.0
# Bridge freshness: the statusline re-renders every turn, so a live session's
# bridge is seconds old; >15min means the session is not actively rendering and
# the % is not a current read.
STALE_S = 900.0
# Secondary jsonl-size bands (MB), mirroring context_monitor COMPACT/KCLEAR.
JSONL_AMBER_MB = 16.0
JSONL_RED_MB = 24.0
_BYTES_PER_MB = 1024 * 1024


@dataclass
class ContextEstimate:
    pct: float | None          # effective context % (None == unknown exact)
    band: str                  # GREEN | AMBER | RED | BREACH | UNKNOWN
    source: str                # statusline | jsonl | unknown
    confidence: str            # high | low | unknown
    stale: bool = False        # bridge present but stale (surfaced, not hidden)


def band_of(pct) -> str:
    if pct is None:
        return UNKNOWN
    if pct <= GREEN_MAX:
        return GREEN
    if pct <= AMBER_MAX:
        return AMBER
    if pct <= CEILING:
        return RED
    return BREACH


def _enc(cwd: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")


def _read_bridge(sid: str, temp_dir) -> dict | None:
    p = Path(temp_dir or tempfile.gettempdir()) / f"claude-ctx-{sid}.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))   # BOM-tolerant
    except (OSError, ValueError):
        return None


def _jsonl_mb(sid: str, cwd: str | None, proj_base) -> float | None:
    if not cwd:
        return None
    base = Path(proj_base) if proj_base else (Path.home() / ".claude" / "projects")
    p = base / _enc(cwd) / f"{sid}.jsonl"
    try:
        return round(p.stat().st_size / _BYTES_PER_MB, 2) if p.is_file() else None
    except OSError:
        return None


def _band_from_mb(mb: float) -> str:
    if mb >= JSONL_RED_MB:
        return RED
    if mb >= JSONL_AMBER_MB:
        return AMBER
    return GREEN


def effective_context(sid: str, cwd: str | None = None, *, now: float | None = None,
                      temp_dir=None, proj_base=None,
                      bridge_fn=None, jsonl_fn=None) -> ContextEstimate:
    """Single effective-context read: fresh statusline bridge primary, jsonl-size
    secondary, honest UNKNOWN otherwise. Fail-open -> UNKNOWN (never fabricated)."""
    try:
        now = now if now is not None else time.time()
        bridge = (bridge_fn or _read_bridge)(sid, temp_dir)
        if isinstance(bridge, dict):
            up = bridge.get("used_pct")
            ts = bridge.get("timestamp")
            if isinstance(up, (int, float)):
                fresh = isinstance(ts, (int, float)) and (now - ts) < STALE_S
                if fresh:
                    return ContextEstimate(float(up), band_of(up),
                                           "statusline", "high", False)
                # stale -> do not trust as current; fall through to secondary,
                # remembering the stale bridge for honest surfacing.
                stale = True
            else:
                stale = False
        else:
            stale = False

        mb = (jsonl_fn or _jsonl_mb)(sid, cwd, proj_base)
        if isinstance(mb, (int, float)):
            return ContextEstimate(None, _band_from_mb(mb), "jsonl", "low", stale)
        return ContextEstimate(None, UNKNOWN, "unknown", "unknown", stale)
    except Exception:  # noqa: BLE001 -- fail-open, never fabricate GREEN
        return ContextEstimate(None, UNKNOWN, "unknown", "unknown", False)


@dataclass
class ResumeAdvisory:
    band: str
    advise: bool                 # True when the resume target is RED/BREACH
    message: str | None = None   # ready-to-print advisory (ASCII), or None
    confidence: str = "unknown"


def resume_advisory(sid: str, cwd: str | None = None, *, now: float | None = None,
                    temp_dir=None, proj_base=None,
                    estimate_fn=None) -> ResumeAdvisory:
    """Honest rung-2 advisory for resuming a session near/over the ceiling. A
    block is NOT used (a session must be opened to be /compact-ed); instead the
    Owner is warned and offered the recovery-class choice. Fail-open -> no advice."""
    try:
        est = (estimate_fn or effective_context)(
            sid, cwd, now=now, temp_dir=temp_dir, proj_base=proj_base)
        if est.band not in (RED, BREACH):
            return ResumeAdvisory(est.band, False, None, est.confidence)
        pct = f"{est.pct:.0f}%" if est.pct is not None else f"~{est.band}"
        why = ("ALREADY OVER the 60% ceiling" if est.band == BREACH
               else "in the 55-60% pre-ceiling band")
        msg = (f"PP CO-00: the session you are resuming is {why} "
               f"(effective context {pct}, {est.source}/{est.confidence}). "
               f"Recovery-class entry recommended: resume and /compact "
               f"immediately, or start a fresh session that inherits a "
               f"checkpoint. A session should not keep working past 60%.")
        return ResumeAdvisory(est.band, True, msg, est.confidence)
    except Exception:  # noqa: BLE001 -- fail-open
        return ResumeAdvisory(UNKNOWN, False, None, "unknown")


def current_context_pct(sid: str, cwd: str | None = None, **kw):
    """Convenience for CO-09 loop admission: the start_context_pct of a loop is
    the launching session's effective context now. Returns a float or None
    (unknown). CO-09 treats None conservatively (no projection blocks on it)."""
    return effective_context(sid, cwd, **kw).pct


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--sid", required=True)
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    est = effective_context(args.sid, args.cwd)
    adv = resume_advisory(args.sid, args.cwd)
    if args.json:
        print(json.dumps({"pct": est.pct, "band": est.band, "source": est.source,
                          "confidence": est.confidence, "stale": est.stale,
                          "resume_advise": adv.advise, "message": adv.message}))
    else:
        print(f"effective context: {est.band} "
              f"(pct={est.pct}, {est.source}/{est.confidence}"
              f"{', STALE bridge' if est.stale else ''})")
        if adv.message:
            print(adv.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
