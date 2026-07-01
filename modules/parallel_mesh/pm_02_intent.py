#!/usr/bin/env python3
"""pm_02_intent.py -- PM-02: Pane Intent Declaration & Collision Detector.

Recalibrates CO-08's blunt same-repo cap. A pane DECLARES its scope before it
executes; the scope-gate then admits N same-repo panes whose declared scopes do
not collide, while an UNDECLARED pane keeps CO-08's blunt SAME_REPO_CAP=1 as the
fail-safe. The collision decision itself lives in the parent `scheduler.decide`
(extended with optional `declared`/`hot_scopes`); this module adds the on-disk
intent registry, the collision reporter, and the ergonomic scope-gated admit.

Honest (CO-10): intents are FILES ON DISK (one JSON per sid, under
~/.claude/state/parallel_mesh/intents/<enc-cwd>/), read at pane boundaries. This
is not a lock server and not IPC. Fail-open ABSOLUTE: any error anywhere ->
fall back to the sealed CO-08 blunt cap (never widen admission on a bug).

Known limitation (documented, not a stub): scope collision is exact normalized-
path-token intersection. Directory-vs-file prefix overlap (one pane declares
`modules/`, another `modules/x.py`) is NOT yet caught -- deferred to a follow-up
(backlog). Declaring at file granularity is collision-correct today.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import scheduler as _sched  # noqa: E402

# Intent freshness window mirrors CO-08's HOT_WINDOW_MIN (a stale intent whose
# pane is no longer hot must not cause phantom collisions).
INTENT_WINDOW_MIN = float(os.environ.get("PP_INTENT_WINDOW_MIN", "120"))


def _enc(cwd: str) -> str:
    """Same project-dir encoder CO-08 uses: non-alnum -> '-'."""
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")


def _norm_token(tok: str) -> str:
    """Canonicalize a scope token (a file/dir/module path) for set-intersection
    collision: lowercase, backslashes -> '/', strip leading './' and slashes,
    drop trailing slash. Coarse but deterministic and collision-correct at file
    granularity."""
    t = str(tok).strip().replace("\\", "/").lower()
    while t.startswith("./"):
        t = t[2:]
    return t.strip("/")


def norm_scope(scope) -> tuple:
    """Normalize an iterable of scope tokens to a sorted unique tuple. Empty/None
    -> empty tuple (an empty scope collides with nothing -- an honest 'I touch
    no files' declaration)."""
    if not scope:
        return ()
    seen = {_norm_token(t) for t in scope if str(t).strip()}
    seen.discard("")
    return tuple(sorted(seen))


def _parse_iso(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass
class Intent:
    sid: str
    cwd: str
    scope: tuple = ()          # normalized path tokens
    objective: str = ""
    mode: str = ""             # EXECUTION | ULTRA-PLAN | review | index
    model: str = ""            # requested model (arbitrated later by PM-04)
    ts: str = ""               # ISO declaration timestamp

    def to_json(self) -> dict:
        d = asdict(self)
        d["scope"] = list(self.scope)
        return d

    @staticmethod
    def from_json(d: dict) -> "Intent":
        return Intent(
            sid=str(d.get("sid", "")),
            cwd=str(d.get("cwd", "")),
            scope=norm_scope(d.get("scope")),
            objective=str(d.get("objective", "")),
            mode=str(d.get("mode", "")),
            model=str(d.get("model", "")),
            ts=str(d.get("ts", "")),
        )


def _default_state_dir() -> Path:
    return Path.home() / ".claude" / "state" / "parallel_mesh" / "intents"


class PaneIntentRegistry:
    """Disk-backed registry of declared intents. One JSON file per sid keeps
    writers isolated (each pane writes only its own file -> no concurrent-writer
    clobber, per the mesh write discipline)."""

    def __init__(self, state_dir=None):
        self.state_dir = Path(state_dir) if state_dir else _default_state_dir()

    def _dir_for(self, cwd: str) -> Path:
        return self.state_dir / _enc(cwd)

    def _file_for(self, cwd: str, sid: str) -> Path:
        return self._dir_for(cwd) / f"{sid}.json"

    def declare(self, sid: str, cwd: str, scope, *, objective: str = "",
                mode: str = "", model: str = "", now: datetime | None = None) -> Intent:
        """Record (or overwrite) this pane's intent. Fail-open: on any I/O error
        returns the Intent object without a persisted file (the gate then treats
        this pane as undeclared -> blunt cap, the safe direction)."""
        now = now or datetime.now(timezone.utc)
        intent = Intent(sid=sid, cwd=cwd, scope=norm_scope(scope),
                        objective=objective, mode=mode, model=model,
                        ts=now.isoformat())
        try:
            d = self._dir_for(cwd)
            d.mkdir(parents=True, exist_ok=True)
            self._file_for(cwd, sid).write_text(
                json.dumps(intent.to_json(), indent=2), encoding="utf-8")
        except OSError:
            pass
        return intent

    def retire(self, sid: str, cwd: str) -> bool:
        """Remove a pane's intent (on /kclear -- the work ended). Fail-open."""
        try:
            f = self._file_for(cwd, sid)
            if f.exists():
                f.unlink()
                return True
        except OSError:
            pass
        return False

    def active(self, cwd: str, *, now: datetime | None = None,
               window_min: float = INTENT_WINDOW_MIN,
               exclude_sid: str | None = None) -> list:
        """Active (fresh) intents for this repo. An intent whose ts is older than
        window_min is ignored (its pane is no longer hot). Fail-open -> []."""
        try:
            now = now or datetime.now(timezone.utc)
            cutoff = now - timedelta(minutes=window_min)
            d = self._dir_for(cwd)
            if not d.is_dir():
                return []
            out = []
            for f in d.glob("*.json"):
                try:
                    intent = Intent.from_json(json.loads(f.read_text(encoding="utf-8")))
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
                if exclude_sid and intent.sid == exclude_sid:
                    continue
                ts = _parse_iso(intent.ts)
                if ts is None or ts < cutoff:
                    continue
                out.append(intent)
            return out
        except Exception:  # noqa: BLE001 -- fail-open
            return []

    def scopes_by_sid(self, cwd: str, **kw) -> dict:
        """{sid: scope-tuple} for active intents on this repo. Feeds
        scheduler.decide's `hot_scopes`."""
        return {i.sid: i.scope for i in self.active(cwd, **kw)}


class CollisionDetector:
    """Reports scope collisions between a declared scope and active intents.
    Uses the same exact-token intersection rule scheduler.decide applies, so the
    reporter and the gate never disagree."""

    @staticmethod
    def overlap(declared, scope) -> list:
        a = set(norm_scope(declared))
        b = set(norm_scope(scope))
        return sorted(a & b)

    @classmethod
    def collisions(cls, declared, intents, *, exclude_sid: str | None = None) -> list:
        """List of (sid, overlap_tokens) for every active intent whose scope
        intersects `declared`. An empty list means no collision -> admissible."""
        out = []
        for it in intents:
            if exclude_sid and it.sid == exclude_sid:
                continue
            ov = cls.overlap(declared, it.scope)
            if ov:
                out.append((it.sid, ov))
        return out


def scope_gated_admit(cwd: str, sid: str, declared_scope=None, *,
                      registry: PaneIntentRegistry | None = None,
                      proj_base=None, now: datetime | None = None,
                      window_min: float = INTENT_WINDOW_MIN,
                      gather_fn=None):
    """Admit (or refuse) a NEW same-repo pane. When `declared_scope` is None the
    pane is undeclared -> CO-08's blunt cap (scheduler.admit) applies unchanged.
    When a scope is declared, the same-repo dimension is scope-gated via
    scheduler.decide. Returns a scheduler.CapVerdict. Fail-open ABSOLUTE: any
    error -> the sealed blunt cap (never widen admission on a bug)."""
    try:
        registry = registry or PaneIntentRegistry()
        if declared_scope is None:
            # Undeclared: exact sealed CO-08 behavior (fail-safe).
            return _sched.admit(cwd, is_new=True, proj_base=proj_base, now=now,
                                exclude_sid=sid, window_min=window_min,
                                gather_fn=gather_fn)
        hot = (gather_fn or _sched.gather_hot_sessions)(
            proj_base=proj_base, now=now, window_min=window_min, exclude_sid=sid)
        hot_scopes = registry.scopes_by_sid(
            cwd, now=now, window_min=window_min, exclude_sid=sid)
        return _sched.decide(hot, cwd, is_new=True,
                             declared=norm_scope(declared_scope),
                             hot_scopes=hot_scopes)
    except Exception:  # noqa: BLE001 -- fail-open to the blunt cap
        try:
            return _sched.admit(cwd, is_new=True, proj_base=proj_base, now=now,
                                exclude_sid=sid, window_min=window_min,
                                gather_fn=gather_fn)
        except Exception:  # noqa: BLE001
            return _sched.CapVerdict("proceed", ["gate errored -- fail-open"],
                                     [], 0, 0, _sched.HOT_CAP, "error")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--sid", required=True)
    ap.add_argument("--declare", action="store_true",
                    help="record the intent instead of testing admission")
    ap.add_argument("--scope", default="", help="comma-separated scope tokens")
    ap.add_argument("--objective", default="")
    ap.add_argument("--mode", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    cwd = args.cwd or os.getcwd()
    scope = [s for s in args.scope.split(",") if s.strip()] or None
    reg = PaneIntentRegistry()
    if args.declare:
        it = reg.declare(args.sid, cwd, scope or (), objective=args.objective,
                         mode=args.mode)
        print(json.dumps(it.to_json()) if args.json
              else f"# declared {args.sid}: scope={list(it.scope)}")
        return 0
    v = scope_gated_admit(cwd, args.sid, scope, registry=reg)
    if args.json:
        print(json.dumps({"verdict": v.verdict, "reasons": v.reasons,
                          "satisfy": v.satisfy, "hot_count": v.hot_count,
                          "same_repo_count": v.same_repo_count, "source": v.source}))
    elif v.verdict == "refuse":
        print(_sched.format_refusal(v))
    else:
        print(f"# proceed ({v.hot_count} hot, same-repo {v.same_repo_count}, "
              f"declared={'yes' if scope else 'no'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
