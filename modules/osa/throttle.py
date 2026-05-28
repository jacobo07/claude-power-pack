"""OSA throttle gate: budget + cooldown + cache for claude -p calls.

Sleepy-by-default discipline. Reads vault/osa/config.json so the
daily budget can be tuned without code changes. Falls back to safe
defaults if the config file is missing.

State lives in vault/osa/budget_<YYYY-MM-DD>.json (atomic write,
JSON line, no daemon). One file per UTC date, naturally rotating.

Sealed 2026-05-28.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PP_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PP_ROOT / "vault" / "osa" / "config.json"
BUDGET_DIR = PP_ROOT / "vault" / "osa"

DEFAULT_CONFIG = {
    "max_daily_calls": 150,
    "cooldown_minutes": 30,
    "cache_ttl_minutes": 60,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


def _load_throttle_config() -> dict:
    """Returns the throttle section of vault/osa/config.json or defaults."""
    if not CONFIG_PATH.is_file():
        return dict(DEFAULT_CONFIG)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(DEFAULT_CONFIG)
    section = data.get("throttle") if isinstance(data, dict) else None
    if not isinstance(section, dict):
        return dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    for k in ("max_daily_calls", "cooldown_minutes", "cache_ttl_minutes"):
        v = section.get(k)
        if isinstance(v, int) and v > 0:
            merged[k] = v
    return merged


def _budget_file() -> Path:
    BUDGET_DIR.mkdir(parents=True, exist_ok=True)
    return BUDGET_DIR / f"budget_{date.today().isoformat()}.json"


def _load_budget() -> dict:
    f = _budget_file()
    if not f.exists():
        return {
            "date": str(date.today()),
            "calls": 0,
            "last_run_iso": "",
            "cache": {},
        }
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {
            "date": str(date.today()),
            "calls": 0,
            "last_run_iso": "",
            "cache": {},
        }


def _atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON atomically: tmp + os.replace, Windows-safe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _save_budget(b: dict) -> None:
    _atomic_write_json(_budget_file(), b)


def _minutes_since(iso: str) -> int | None:
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return int((_utc_now() - d).total_seconds() // 60)
    except ValueError:
        return None


def check(project: str = "global") -> str:
    """Returns: GO | CACHE_HIT:<min> | COOLDOWN:<min> | BUDGET_EXHAUSTED.

    Order of precedence: cache-hit beats budget; budget beats cooldown.
    Fail-open on any storage error -- a throttle that errors must let
    the action through, never silently block real work.
    """
    try:
        cfg = _load_throttle_config()
        b = _load_budget()
        cache_entry = (b.get("cache") or {}).get(project) or {}
        age = _minutes_since(cache_entry.get("ts", ""))
        if age is not None and age < cfg["cache_ttl_minutes"]:
            return f"CACHE_HIT:{age}"
        if b.get("calls", 0) >= cfg["max_daily_calls"]:
            return "BUDGET_EXHAUSTED"
        elapsed = _minutes_since(b.get("last_run_iso", ""))
        if elapsed is not None and elapsed < cfg["cooldown_minutes"]:
            return f"COOLDOWN:{cfg['cooldown_minutes'] - elapsed}"
        return "GO"
    except Exception:
        return "GO"


def consume(project: str = "global", summary: str = "") -> dict:
    """Records a single invocation, updates cache, returns new state.

    Fail-open: returns {"ok": False, "reason": ...} on storage error,
    never raises. Callers should not block on a write failure.
    """
    try:
        b = _load_budget()
        b["calls"] = int(b.get("calls", 0)) + 1
        now = _iso_now()
        b["last_run_iso"] = now
        b.setdefault("cache", {})[project] = {
            "ts": now,
            "summary": (summary or "")[:240],
        }
        _save_budget(b)
        return {"ok": True, "calls": b["calls"], "last_run_iso": now}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}


def status() -> dict:
    """Returns: {date, daily_calls, remaining, max_daily, last_run, cooldown_min, cache_ttl_min}."""
    cfg = _load_throttle_config()
    b = _load_budget()
    return {
        "date": b.get("date", str(date.today())),
        "daily_calls": int(b.get("calls", 0)),
        "remaining": max(0, cfg["max_daily_calls"] - int(b.get("calls", 0))),
        "max_daily": cfg["max_daily_calls"],
        "cooldown_min": cfg["cooldown_minutes"],
        "cache_ttl_min": cfg["cache_ttl_minutes"],
        "last_run": b.get("last_run_iso") or "never",
        "cached_projects": sorted((b.get("cache") or {}).keys()),
    }


def reset_today() -> None:
    """Test helper. Truncates today's budget file."""
    _save_budget({
        "date": str(date.today()),
        "calls": 0,
        "last_run_iso": "",
        "cache": {},
    })


def runway_days() -> float | None:
    """Best-effort runway lookup from tools/budget_monitor.py.

    Returns None when monitor is unconfigured / stale / errored.
    """
    import subprocess
    monitor = PP_ROOT / "tools" / "budget_monitor.py"
    if not monitor.is_file():
        return None
    try:
        r = subprocess.run(
            [sys.executable, str(monitor), "--quiet"],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    for line in (r.stdout or "").splitlines():
        low = line.lower()
        if "runway" in low and "day" in low:
            for tok in line.replace(":", " ").split():
                try:
                    return float(tok)
                except ValueError:
                    continue
    return None


def _main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OSA throttle gate")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("--check")
    sub.add_parser("--consume")
    sub.add_parser("--status")
    sub.add_parser("--reset")
    ap.add_argument("--project", default="global")
    args, _extra = ap.parse_known_args(argv)
    # support both `--check` (no subcommand) and bare arg form
    cmd = args.cmd
    if cmd is None:
        for a in (argv if argv is not None else sys.argv[1:]):
            if a in {"--check", "--consume", "--status", "--reset"}:
                cmd = a
                break
    cmd = cmd or "--check"
    if cmd == "--check":
        print(check(args.project))
    elif cmd == "--consume":
        result = consume(args.project)
        print(json.dumps(result))
    elif cmd == "--status":
        print(json.dumps(status(), indent=2))
    elif cmd == "--reset":
        reset_today()
        print("RESET")
    else:
        ap.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
