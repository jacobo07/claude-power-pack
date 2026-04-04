"""
OmniCapture Receiver — VPS-resident telemetry ingestion service.
Accepts telemetry via REST (batch) and WebSocket (streaming).
Designed to run as a systemd service on KobiiClaw VPS.

Usage:
    python receiver.py                    # Start with default config
    python receiver.py --config /path/to/config.json
    python receiver.py --port 9876        # Override port
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Any

try:
    from aiohttp import web
except ImportError:
    print("ERROR: aiohttp required. Install: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

from auth import AuthManager
from schema_validator import validate_event, enrich_event
from storage import TieredStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("omnicapture")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "host": "127.0.0.1",
        "port": 9876,
        "api_keys": {},
        "storage": {"base_dir": "/opt/kobiiclaw/omnicapture/data"},
        "rate_limits": {"global_per_min": 1000},
    }


# ---------------------------------------------------------------------------
# Request Helpers
# ---------------------------------------------------------------------------

def extract_api_key(request: web.Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def parse_since(since_str: str) -> int:
    """Parse since parameter (5m, 1h, 24h, 7d) to seconds."""
    if not since_str:
        return 300  # default 5 minutes

    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = since_str[-1].lower()
    if unit in multipliers:
        try:
            return int(since_str[:-1]) * multipliers[unit]
        except ValueError:
            pass
    return 300


# ---------------------------------------------------------------------------
# HTTP Handlers
# ---------------------------------------------------------------------------

async def handle_health(request: web.Request) -> web.Response:
    """GET /api/v1/health — Health check endpoint."""
    app = request.app
    storage: TieredStorage = app["storage"]
    stats = storage.get_storage_stats()
    return web.json_response({
        "status": "healthy",
        "version": "1.0.0",
        "storage": stats,
        "ws_connections": len(app.get("ws_clients", [])),
    })


async def handle_ingest(request: web.Request) -> web.Response:
    """POST /api/v1/ingest — Batch event ingestion."""
    app = request.app
    auth_mgr: AuthManager = app["auth"]
    storage: TieredStorage = app["storage"]

    # Authenticate
    api_key = extract_api_key(request)
    if not api_key:
        return web.json_response({"error": "Missing Authorization header"}, status=401)

    is_valid, key_name, allowed_projects = auth_mgr.authenticate(api_key)
    if not is_valid:
        return web.json_response({"error": "Invalid API key"}, status=403)

    # Parse body
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    events = body.get("events", [])
    if not isinstance(events, list):
        return web.json_response({"error": "events must be an array"}, status=400)

    max_events = app["config"].get("storage", {}).get("max_events_per_ingest", 500)
    if len(events) > max_events:
        return web.json_response(
            {"error": f"Too many events. Max {max_events} per request."},
            status=413,
        )

    # Rate limit
    is_allowed, retry_after = auth_mgr.check_rate_limit(api_key, len(events))
    if not is_allowed:
        return web.json_response(
            {"error": "Rate limit exceeded", "retry_after": round(retry_after, 1)},
            status=429,
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    # Validate and store
    accepted = 0
    rejected = 0
    errors_list: list[str] = []

    for i, event in enumerate(events):
        is_event_valid, event_errors = validate_event(event)
        if not is_event_valid:
            rejected += 1
            errors_list.append(f"event[{i}]: {'; '.join(event_errors)}")
            continue

        # Determine project_id from event or default from key
        project_id = event.get("project_id")
        if not project_id and allowed_projects:
            project_id = next(iter(allowed_projects))

        if project_id and not auth_mgr.is_project_allowed(api_key, project_id):
            rejected += 1
            errors_list.append(f"event[{i}]: not authorized for project {project_id}")
            continue

        enriched = enrich_event(event, project_id or "unknown")
        storage.write_event(enriched)
        accepted += 1

    logger.info(f"Ingest from {key_name}: {accepted} accepted, {rejected} rejected")

    return web.json_response({
        "accepted": accepted,
        "rejected": rejected,
        "errors": errors_list[:20],  # Cap error list
    })


async def handle_query(request: web.Request) -> web.Response:
    """GET /api/v1/query — Query events with filters."""
    app = request.app
    auth_mgr: AuthManager = app["auth"]
    storage: TieredStorage = app["storage"]

    api_key = extract_api_key(request)
    if not api_key:
        return web.json_response({"error": "Missing Authorization header"}, status=401)

    is_valid, _, allowed_projects = auth_mgr.authenticate(api_key)
    if not is_valid:
        return web.json_response({"error": "Invalid API key"}, status=403)

    # Parse query params
    project_id = request.query.get("project_id")
    if not project_id:
        return web.json_response({"error": "project_id required"}, status=400)

    if not auth_mgr.is_project_allowed(api_key, project_id):
        return web.json_response({"error": f"Not authorized for project {project_id}"}, status=403)

    since = parse_since(request.query.get("since", "5m"))
    limit = min(int(request.query.get("limit", "50")), 500)
    category = request.query.get("category")

    severity_param = request.query.get("severity")
    severity = set(severity_param.split(",")) if severity_param else None

    events = storage.query(
        project_id=project_id,
        since_seconds=since,
        severity=severity,
        category=category,
        limit=limit,
    )

    return web.json_response({
        "events": events,
        "total": len(events),
        "truncated": len(events) >= limit,
    })


async def handle_query_summary(request: web.Request) -> web.Response:
    """GET /api/v1/query/summary — Aggregated telemetry summary."""
    app = request.app
    auth_mgr: AuthManager = app["auth"]
    storage: TieredStorage = app["storage"]

    api_key = extract_api_key(request)
    if not api_key:
        return web.json_response({"error": "Missing Authorization header"}, status=401)

    is_valid, _, _ = auth_mgr.authenticate(api_key)
    if not is_valid:
        return web.json_response({"error": "Invalid API key"}, status=403)

    project_id = request.query.get("project_id")
    if not project_id:
        return web.json_response({"error": "project_id required"}, status=400)

    if not auth_mgr.is_project_allowed(api_key, project_id):
        return web.json_response({"error": f"Not authorized for project {project_id}"}, status=403)

    since = parse_since(request.query.get("since", "1h"))
    summary = storage.get_summary(project_id, since_seconds=since)

    return web.json_response(summary)


async def handle_projects(request: web.Request) -> web.Response:
    """GET /api/v1/projects — List projects visible to this API key."""
    app = request.app
    auth_mgr: AuthManager = app["auth"]
    storage: TieredStorage = app["storage"]

    api_key = extract_api_key(request)
    if not api_key:
        return web.json_response({"error": "Missing Authorization header"}, status=401)

    is_valid, _, allowed_projects = auth_mgr.authenticate(api_key)
    if not is_valid:
        return web.json_response({"error": "Invalid API key"}, status=403)

    projects = []
    for pid in (allowed_projects or set()):
        summary = storage.get_summary(pid, since_seconds=86400)
        projects.append({
            "id": pid,
            "event_count_24h": summary["total_events"],
            "error_count_24h": summary["error_count"],
            "crash_count_24h": summary["crash_count"],
        })

    return web.json_response({"projects": projects})


# ---------------------------------------------------------------------------
# WebSocket Handler
# ---------------------------------------------------------------------------

async def handle_stream(request: web.Request) -> web.WebSocketResponse:
    """WS /api/v1/stream — Real-time event streaming."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    app = request.app
    auth_mgr: AuthManager = app["auth"]
    storage: TieredStorage = app["storage"]

    # First message must be auth
    authenticated = False
    api_key = None
    allowed_projects: set[str] = set()

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except json.JSONDecodeError:
                await ws.send_json({"status": "error", "reason": "Invalid JSON"})
                continue

            # Auth handshake
            if not authenticated:
                api_key = data.get("auth")
                if not api_key:
                    await ws.send_json({"status": "error", "reason": "First message must contain auth key"})
                    await ws.close()
                    break

                is_valid, key_name, projects = auth_mgr.authenticate(api_key)
                if not is_valid:
                    await ws.send_json({"status": "error", "reason": "Invalid API key"})
                    await ws.close()
                    break

                authenticated = True
                allowed_projects = projects or set()
                app.setdefault("ws_clients", []).append(ws)
                await ws.send_json({"status": "ok", "message": f"Authenticated as {key_name}"})
                logger.info(f"WS client connected: {key_name}")
                continue

            # Process event
            is_valid_event, errors = validate_event(data)
            if not is_valid_event:
                await ws.send_json({"status": "error", "reason": "; ".join(errors)})
                continue

            # Rate limit
            is_allowed, retry_after = auth_mgr.check_rate_limit(api_key, 1)
            if not is_allowed:
                await ws.send_json({"status": "error", "reason": "Rate limited", "retry_after": round(retry_after, 1)})
                continue

            project_id = data.get("project_id")
            if not project_id and allowed_projects:
                project_id = next(iter(allowed_projects))

            enriched = enrich_event(data, project_id or "unknown")
            storage.write_event(enriched)
            await ws.send_json({"status": "ok", "event_id": enriched["event_id"]})

        elif msg.type in (web.WSMsgType.ERROR, web.WSMsgType.CLOSE):
            break

    # Cleanup
    clients = app.get("ws_clients", [])
    if ws in clients:
        clients.remove(ws)
    logger.info("WS client disconnected")

    return ws


# ---------------------------------------------------------------------------
# Application Setup
# ---------------------------------------------------------------------------

def create_app(config: dict[str, Any]) -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()

    # Initialize components
    app["config"] = config
    app["auth"] = AuthManager(config.get("rate_limits", {}))
    # Merge api_keys into rate_limits for AuthManager
    rate_config = {**config.get("rate_limits", {}), "api_keys": config.get("api_keys", {})}
    app["auth"] = AuthManager(rate_config)
    app["storage"] = TieredStorage(config.get("storage", {}))

    # Routes
    app.router.add_get("/api/v1/health", handle_health)
    app.router.add_post("/api/v1/ingest", handle_ingest)
    app.router.add_get("/api/v1/query", handle_query)
    app.router.add_get("/api/v1/query/summary", handle_query_summary)
    app.router.add_get("/api/v1/projects", handle_projects)
    app.router.add_get("/api/v1/stream", handle_stream)

    return app


def main():
    parser = argparse.ArgumentParser(description="OmniCapture Receiver")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Config file path")
    parser.add_argument("--host", type=str, help="Override bind host")
    parser.add_argument("--port", type=int, help="Override bind port")
    args = parser.parse_args()

    config = load_config(args.config)
    host = args.host or config.get("host", "127.0.0.1")
    port = args.port or config.get("port", 9876)

    app = create_app(config)

    # Graceful shutdown on SIGTERM/SIGINT (Zero-Crash safeguard)
    def _handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        raise web.GracefulExit()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info(f"OmniCapture Receiver v1.0.0 starting on {host}:{port}")
    web.run_app(app, host=host, port=port, print=None)


if __name__ == "__main__":
    main()
