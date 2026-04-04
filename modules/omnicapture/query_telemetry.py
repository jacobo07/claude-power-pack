"""
OmniCapture — Query Telemetry CLI.
Claude Code invokes this tool to read runtime telemetry from the VPS.

Output is formatted as human-readable text optimized for Claude's context window.

Usage:
    python query_telemetry.py --project kobiicraft --since 5m
    python query_telemetry.py --project kobiicraft --summary
    python query_telemetry.py --project kobiicraft --category crash --limit 10
    python query_telemetry.py --project kobiicraft --since 5m --severity ERROR,CRITICAL
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_api_key(config: dict, project_id: str | None = None) -> str | None:
    """Resolve API key from config -> project mapping -> env var."""
    # Project-specific key
    if project_id and project_id in config.get("project_mapping", {}):
        env_var = config["project_mapping"][project_id].get("api_key_env")
        if env_var:
            key = os.environ.get(env_var)
            if key:
                return key

    # Global fallback
    global_env = config.get("api_key_env", "OMNICAPTURE_API_KEY")
    return os.environ.get(global_env)


def api_request(endpoint: str, api_key: str, config: dict) -> dict[str, Any] | None:
    """Make a GET request to the VPS API."""
    base_url = config.get("vps_endpoint", "https://localhost:9877")
    url = f"{base_url}{endpoint}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: HTTP {e.code} from VPS: {body}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"ERROR: VPS unreachable at {base_url}: {e.reason}", file=sys.stderr)
        print("NOTE: Runtime telemetry not available — static verification only.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error querying VPS: {e}", file=sys.stderr)
        return None


def format_summary(data: dict[str, Any]) -> str:
    """Format summary response for Claude consumption."""
    lines = []
    project = data.get("project_id", "unknown")
    since = data.get("since_seconds", 3600)
    since_label = f"{since // 60}m" if since < 3600 else f"{since // 3600}h"

    lines.append(f"=== OmniCapture: {project} (last {since_label}) ===")
    lines.append(f"TOTAL: {data.get('total_events', 0)} events")
    lines.append(f"ERRORS: {data.get('error_count', 0)} | WARNINGS: {data.get('warning_count', 0)} | CRASHES: {data.get('crash_count', 0)}")

    p99 = data.get("p99_latency_ms", 0)
    if p99 > 0:
        lines.append(f"P99 LATENCY: {p99}ms")

    # Top errors
    top_errors = data.get("top_errors", [])
    if top_errors:
        lines.append("")
        lines.append("TOP ERRORS:")
        for err in top_errors[:5]:
            count = err.get("count", 0)
            error_type = err.get("error_type", "Unknown")
            message = err.get("message", "")[:120]
            fp = err.get("fingerprint", "")[:8]
            lines.append(f"  [{count}x] {error_type}: {message} (fp:{fp})")

    # Severity breakdown
    breakdown = data.get("severity_breakdown", {})
    if breakdown:
        lines.append("")
        parts = [f"{k}={v}" for k, v in sorted(breakdown.items())]
        lines.append(f"SEVERITY: {', '.join(parts)}")

    # Governance verdict
    lines.append("")
    error_count = data.get("error_count", 0)
    crash_count = data.get("crash_count", 0)
    if error_count > 0 or crash_count > 0:
        lines.append("GOVERNANCE: BLOCK — Unresolved runtime errors. Fix before claiming completion.")
    else:
        lines.append("GOVERNANCE: PASS — No runtime errors detected.")

    return "\n".join(lines)


def format_events(data: dict[str, Any]) -> str:
    """Format event list response for Claude consumption."""
    lines = []
    events = data.get("events", [])
    total = data.get("total", 0)
    truncated = data.get("truncated", False)

    lines.append(f"=== OmniCapture: {total} events {'(truncated)' if truncated else ''} ===")
    lines.append("")

    for event in events:
        severity = event.get("severity", "?")
        timestamp = event.get("timestamp_iso", "?")
        # Extract just time portion
        time_part = timestamp[11:19] if len(timestamp) > 19 else timestamp
        category = event.get("category", "?")
        payload = event.get("payload", {})

        if category == "error":
            error_type = payload.get("error_type", "Unknown")
            message = payload.get("message", "")[:150]
            lines.append(f"[{severity}] {time_part} {error_type}: {message}")
            stacktrace = payload.get("stacktrace", [])
            for frame in stacktrace[:3]:
                lines.append(f"  {frame}")
            context = payload.get("context", {})
            if context:
                lines.append(f"  Context: {json.dumps(context)}")
            fp = event.get("fingerprint", "")[:8]
            lines.append(f"  Fingerprint: {fp}")

        elif category == "crash":
            sig = payload.get("signal", "?")
            code = payload.get("exit_code", "?")
            lines.append(f"[{severity}] {time_part} CRASH: {sig} (exit {code})")

        elif category == "network":
            url = payload.get("url", "?")[:80]
            status = payload.get("status_code", "?")
            latency = payload.get("latency_ms", "?")
            lines.append(f"[{severity}] {time_part} HTTP {status} {url} ({latency}ms)")

        elif category == "performance":
            metric = payload.get("metric_name", "?")
            value = payload.get("value", "?")
            lines.append(f"[{severity}] {time_part} {metric}: {value}")

        elif category == "state_dump":
            dump_type = payload.get("dump_type", "?")
            lines.append(f"[{severity}] {time_part} STATE_DUMP: {dump_type}")

        else:
            lines.append(f"[{severity}] {time_part} {category}: {json.dumps(payload)[:120]}")

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="OmniCapture Telemetry Query")
    parser.add_argument("--project", required=True, help="Project ID to query")
    parser.add_argument("--since", default=None, help="Time window (5m, 1h, 24h, 7d)")
    parser.add_argument("--severity", default=None, help="Comma-separated severities (ERROR,CRITICAL)")
    parser.add_argument("--category", default=None, help="Event category filter (error, crash, network, performance)")
    parser.add_argument("--limit", type=int, default=None, help="Max events to return")
    parser.add_argument("--summary", action="store_true", help="Show aggregated summary instead of events")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    config = load_config()
    api_key = get_api_key(config, args.project)

    if not api_key:
        env_var = config.get("api_key_env", "OMNICAPTURE_API_KEY")
        project_env = config.get("project_mapping", {}).get(args.project, {}).get("api_key_env", "")
        print(f"ERROR: No API key found. Set {project_env or env_var} environment variable.", file=sys.stderr)
        print("NOTE: Runtime telemetry not available — static verification only.", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        since = args.since or config.get("query_defaults", {}).get("since", "1h")
        endpoint = f"/api/v1/query/summary?project_id={args.project}&since={since}"
        data = api_request(endpoint, api_key, config)
        if data:
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print(format_summary(data))
    else:
        defaults = config.get("query_defaults", {})
        since = args.since or defaults.get("since", "5m")
        limit = args.limit or defaults.get("limit", 50)
        severity = args.severity or defaults.get("severity", "")

        endpoint = f"/api/v1/query?project_id={args.project}&since={since}&limit={limit}"
        if severity:
            endpoint += f"&severity={severity}"
        if args.category:
            endpoint += f"&category={args.category}"

        data = api_request(endpoint, api_key, config)
        if data:
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print(format_events(data))


if __name__ == "__main__":
    main()
