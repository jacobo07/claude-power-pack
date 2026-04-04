"""
Zero-Crash Telemetry Receiver — VPS-resident anonymous crash data collector.

Collects anonymized crash reports from Claude Power Pack users (opt-in).
Runs as a lightweight HTTP service alongside OmniCapture on KobiiClaw VPS.

Usage:
    python crash_receiver.py                   # Default: port 9879
    python crash_receiver.py --port 9879
    python crash_receiver.py --config config.json

What it collects (anonymized):
    - Hook failure patterns (which gates fail)
    - TTY corruption events (platform, frequency)
    - Quality gate pass/fail rates
    - Process sandbox trigger rates

What it NEVER collects:
    - Code content
    - File paths (hashed only)
    - User identity (session UUID hash only)
    - API keys or secrets

Part of Claude Power Pack — Zero-Crash Environment module.
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from aiohttp import web
except ImportError:
    print("ERROR: aiohttp required. Install: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("zero-crash")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PORT = 9879
DATA_DIR = Path("/opt/kobiiclaw/zero-crash/data")
RETENTION_DAYS = 90  # Premium: 90 days, Free: 7 days

FREE_RETENTION_DAYS = 7
PREMIUM_RETENTION_DAYS = 90


def load_config(path: Path | None = None) -> dict[str, Any]:
    if path and path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "port": DEFAULT_PORT,
        "data_dir": str(DATA_DIR),
        "max_batch_size": 100,
        "rate_limit_per_minute": 60,
    }


# ---------------------------------------------------------------------------
# Storage (append-only JSONL per day)
# ---------------------------------------------------------------------------

class CrashStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._counts: dict[str, int] = {}

    def _today_file(self) -> Path:
        return self.data_dir / f"crashes_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"

    def append(self, events: list[dict]) -> int:
        filepath = self._today_file()
        count = 0
        with open(filepath, "a", encoding="utf-8") as f:
            for event in events:
                # Enforce anonymization: strip any field that could identify users
                safe_event = {
                    "session_hash": str(event.get("session_hash", ""))[:16],
                    "gate": str(event.get("gate", "unknown"))[:32],
                    "passed": bool(event.get("passed", True)),
                    "platform": str(event.get("platform", "unknown"))[:16],
                    "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "enforce_mode": bool(event.get("enforce_mode", False)),
                    "event_type": str(event.get("event_type", "gate_result"))[:32],
                    "received_at": datetime.now(timezone.utc).isoformat(),
                }
                f.write(json.dumps(safe_event) + "\n")
                count += 1

                # Track counts for dashboard
                gate = safe_event["gate"]
                self._counts[gate] = self._counts.get(gate, 0) + 1

        return count

    def get_stats(self) -> dict:
        """Return aggregated stats for dashboard."""
        total_events = 0
        gate_stats: dict[str, dict] = {}
        platform_stats: dict[str, int] = {}

        for filepath in sorted(self.data_dir.glob("crashes_*.jsonl"))[-7:]:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        total_events += 1

                        gate = event.get("gate", "unknown")
                        if gate not in gate_stats:
                            gate_stats[gate] = {"total": 0, "passed": 0, "failed": 0}
                        gate_stats[gate]["total"] += 1
                        if event.get("passed"):
                            gate_stats[gate]["passed"] += 1
                        else:
                            gate_stats[gate]["failed"] += 1

                        platform = event.get("platform", "unknown")
                        platform_stats[platform] = platform_stats.get(platform, 0) + 1
                    except json.JSONDecodeError:
                        continue

        return {
            "total_events_7d": total_events,
            "gates": gate_stats,
            "platforms": platform_stats,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def cleanup_old_files(self, retention_days: int = FREE_RETENTION_DAYS) -> int:
        """Remove files older than retention period."""
        cutoff = time.time() - (retention_days * 86400)
        removed = 0
        for filepath in self.data_dir.glob("crashes_*.jsonl"):
            if filepath.stat().st_mtime < cutoff:
                filepath.unlink()
                removed += 1
        return removed


# ---------------------------------------------------------------------------
# Rate Limiter (simple token bucket)
# ---------------------------------------------------------------------------

class RateLimiter:
    def __init__(self, max_per_minute: int = 60):
        self.max_per_minute = max_per_minute
        self._requests: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []

        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if now - t < 60]

        if len(self._requests[key]) >= self.max_per_minute:
            return False

        self._requests[key].append(now)
        return True


# ---------------------------------------------------------------------------
# HTTP Handlers
# ---------------------------------------------------------------------------

async def handle_report(request: web.Request) -> web.Response:
    """POST /api/v1/zero-crash/report — Receive crash telemetry."""
    store: CrashStore = request.app["store"]
    limiter: RateLimiter = request.app["limiter"]

    # Rate limit by IP
    client_ip = request.remote or "unknown"
    if not limiter.allow(client_ip):
        return web.json_response({"error": "rate limited"}, status=429)

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "invalid JSON"}, status=400)

    # Accept single event or batch
    events = body if isinstance(body, list) else [body]

    # Enforce max batch size
    max_batch = request.app["config"].get("max_batch_size", 100)
    if len(events) > max_batch:
        events = events[:max_batch]

    count = store.append(events)
    logger.info(f"Received {count} crash event(s) from {client_ip}")

    return web.json_response({"accepted": count})


async def handle_stats(request: web.Request) -> web.Response:
    """GET /api/v1/zero-crash/stats — Return aggregated dashboard data."""
    store: CrashStore = request.app["store"]
    stats = store.get_stats()
    return web.json_response(stats)


async def handle_health(request: web.Request) -> web.Response:
    """GET /health — Health check."""
    return web.json_response({"status": "ok", "service": "zero-crash-receiver", "version": "1.0.0"})


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(config: dict) -> web.Application:
    app = web.Application()

    data_dir = Path(config.get("data_dir", str(DATA_DIR)))
    app["store"] = CrashStore(data_dir)
    app["limiter"] = RateLimiter(config.get("rate_limit_per_minute", 60))
    app["config"] = config

    app.router.add_post("/api/v1/zero-crash/report", handle_report)
    app.router.add_get("/api/v1/zero-crash/stats", handle_stats)
    app.router.add_get("/health", handle_health)

    return app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Zero-Crash Telemetry Receiver")
    parser.add_argument("--config", type=Path, help="Config file path")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Listen port")
    args = parser.parse_args()

    config = load_config(args.config)
    port = args.port or config.get("port", DEFAULT_PORT)

    app = create_app(config)

    # Graceful shutdown
    def _handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        raise web.GracefulExit()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info(f"Zero-Crash Receiver v1.0.0 starting on 0.0.0.0:{port}")
    web.run_app(app, host="0.0.0.0", port=port, print=None)


if __name__ == "__main__":
    main()
