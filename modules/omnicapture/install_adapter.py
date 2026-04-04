"""
OmniCapture — Adapter Installer.
Generates adapter scaffolding for a target project.

Usage:
    python install_adapter.py --type python --project /path/to/project
    python install_adapter.py --type react_native --project /path/to/project
    python install_adapter.py --type minecraft --project /path/to/project
    python install_adapter.py --type wii_cpp --project /path/to/project
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = MODULE_DIR / "adapters" / "templates"

ADAPTER_TYPES = {"python", "react_native", "minecraft", "wii_cpp"}


def install_python_adapter(project_path: Path) -> list[str]:
    """Generate Python adapter files in the target project."""
    adapter_dir = project_path / "omnicapture"
    adapter_dir.mkdir(exist_ok=True)

    files_created = []

    # __init__.py
    init_content = '''"""OmniCapture Python Adapter — Runtime telemetry for Python applications."""
from .decorators import capture_errors, capture_performance
from .client import OmniCaptureClient

__all__ = ["capture_errors", "capture_performance", "OmniCaptureClient"]
'''
    _write(adapter_dir / "__init__.py", init_content, files_created)

    # client.py
    client_content = '''"""OmniCapture HTTP client — buffers and ships events to VPS."""
import json
import os
import time
import threading
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_FLUSH_INTERVAL = 30  # seconds
_BUFFER_MAX = 100     # events


class OmniCaptureClient:
    """Thread-safe telemetry client with local buffering and batch upload."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        project_id: str | None = None,
        source_type: str = "python",
    ):
        self.endpoint = endpoint or os.environ.get("OMNICAPTURE_ENDPOINT", "https://localhost:9877")
        self.api_key = api_key or os.environ.get("OMNICAPTURE_API_KEY", "")
        self.project_id = project_id or os.environ.get("OMNICAPTURE_PROJECT", "unknown")
        self.source_type = source_type

        self._buffer: list[dict] = []
        self._lock = threading.Lock()
        self._fallback_path = Path("/tmp/omnicapture_buffer.jsonl")

        # Start background flusher
        self._timer: threading.Timer | None = None
        self._start_flusher()

    def emit(self, event: dict[str, Any]) -> None:
        """Buffer a telemetry event for batch upload."""
        event.setdefault("event_id", str(uuid.uuid4()))
        event.setdefault("project_id", self.project_id)
        event.setdefault("source_type", self.source_type)
        event.setdefault("timestamp_iso", datetime.now(timezone.utc).isoformat())
        event.setdefault("timestamp_epoch_ms", int(time.time() * 1000))
        event.setdefault("environment", os.environ.get("OMNICAPTURE_ENV", "development"))
        event.setdefault("hostname", os.uname().nodename if hasattr(os, "uname") else "unknown")

        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= _BUFFER_MAX:
                self._flush_locked()

    def flush(self) -> None:
        """Force flush the buffer."""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        """Flush buffer to VPS. Must be called with self._lock held."""
        if not self._buffer:
            return

        events = self._buffer[:]
        self._buffer.clear()

        if not self.api_key:
            self._write_fallback(events)
            return

        try:
            payload = json.dumps({"events": events}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/api/v1/ingest",
                data=payload,
                method="POST",
            )
            req.add_header("Authorization", f"Bearer {self.api_key}")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=5) as resp:
                pass  # Success — events accepted

        except Exception:
            # VPS unreachable — write to local fallback
            self._write_fallback(events)

    def _write_fallback(self, events: list[dict]) -> None:
        """Write events to local JSONL fallback file."""
        try:
            with open(self._fallback_path, "a", encoding="utf-8") as f:
                for event in events:
                    f.write(json.dumps(event, ensure_ascii=False) + "\\n")
        except OSError:
            pass  # Last resort — silently drop

    def _start_flusher(self) -> None:
        """Start periodic flush timer."""
        def _tick():
            self.flush()
            self._start_flusher()

        self._timer = threading.Timer(_FLUSH_INTERVAL, _tick)
        self._timer.daemon = True
        self._timer.start()
'''
    _write(adapter_dir / "client.py", client_content, files_created)

    # decorators.py
    decorators_content = '''"""OmniCapture decorators — capture errors and performance from functions."""
import functools
import traceback
import time
from typing import Any, Callable
from .client import OmniCaptureClient

_client: OmniCaptureClient | None = None


def _get_client() -> OmniCaptureClient:
    global _client
    if _client is None:
        _client = OmniCaptureClient()
    return _client


def capture_errors(func: Callable) -> Callable:
    """Decorator: catches unhandled exceptions, ships traceback to VPS, re-raises."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _get_client().emit({
                "category": "error",
                "severity": "ERROR",
                "payload": {
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "stacktrace": traceback.format_exc().splitlines(),
                    "function": func.__qualname__,
                    "module": func.__module__,
                },
            })
            raise
    return wrapper


def capture_performance(threshold_ms: float = 200.0) -> Callable:
    """Decorator factory: logs execution time if over threshold."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if elapsed_ms > threshold_ms:
                    _get_client().emit({
                        "category": "performance",
                        "severity": "WARNING",
                        "payload": {
                            "metric_name": "function_execution_ms",
                            "value": round(elapsed_ms, 2),
                            "tags": {
                                "function": func.__qualname__,
                                "module": func.__module__,
                                "threshold_ms": threshold_ms,
                            },
                        },
                    })
            return result
        return wrapper
    return decorator
'''
    _write(adapter_dir / "decorators.py", decorators_content, files_created)

    # middleware.py
    middleware_content = '''"""OmniCapture ASGI middleware — auto-captures request errors and slow requests."""
import time
import traceback
from typing import Any
from .client import OmniCaptureClient

_client: OmniCaptureClient | None = None


def _get_client() -> OmniCaptureClient:
    global _client
    if _client is None:
        _client = OmniCaptureClient()
    return _client


class OmniCaptureMiddleware:
    """
    ASGI middleware for FastAPI/Starlette.
    Auto-captures: unhandled exceptions (500s), slow requests (>threshold).

    Usage:
        from omnicapture.middleware import OmniCaptureMiddleware
        app.add_middleware(OmniCaptureMiddleware, slow_threshold_ms=500)
    """

    def __init__(self, app: Any, slow_threshold_ms: float = 500.0):
        self.app = app
        self.slow_threshold_ms = slow_threshold_ms

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 200

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            _get_client().emit({
                "category": "error",
                "severity": "ERROR",
                "payload": {
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "stacktrace": traceback.format_exc().splitlines(),
                    "context": {
                        "path": scope.get("path", "?"),
                        "method": scope.get("method", "?"),
                    },
                },
            })
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            path = scope.get("path", "?")
            method = scope.get("method", "?")

            if elapsed_ms > self.slow_threshold_ms:
                _get_client().emit({
                    "category": "performance",
                    "severity": "WARNING",
                    "payload": {
                        "metric_name": "http_request_ms",
                        "value": round(elapsed_ms, 2),
                        "tags": {"path": path, "method": method, "status": status_code},
                    },
                })

            if status_code >= 500:
                _get_client().emit({
                    "category": "error",
                    "severity": "ERROR",
                    "payload": {
                        "error_type": f"HTTP_{status_code}",
                        "message": f"{method} {path} returned {status_code}",
                        "context": {"latency_ms": round(elapsed_ms, 2)},
                    },
                })
'''
    _write(adapter_dir / "middleware.py", middleware_content, files_created)

    # interceptors.py
    interceptors_content = '''"""OmniCapture interceptors — capture DB queries and HTTP client calls."""
import time
from typing import Any
from .client import OmniCaptureClient

_client: OmniCaptureClient | None = None


def _get_client() -> OmniCaptureClient:
    global _client
    if _client is None:
        _client = OmniCaptureClient()
    return _client


def patch_sqlalchemy(engine: Any, slow_threshold_ms: float = 200.0) -> None:
    """
    Patch SQLAlchemy engine to capture slow/failed queries.

    Usage:
        from omnicapture.interceptors import patch_sqlalchemy
        patch_sqlalchemy(engine, slow_threshold_ms=200)
    """
    from sqlalchemy import event as sa_event

    @sa_event.listens_for(engine, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("omnicapture_start", time.perf_counter())

    @sa_event.listens_for(engine, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):
        start = conn.info.pop("omnicapture_start", None)
        if start is None:
            return
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > slow_threshold_ms:
            _get_client().emit({
                "category": "performance",
                "severity": "WARNING",
                "payload": {
                    "metric_name": "db_query_time_ms",
                    "value": round(elapsed_ms, 2),
                    "tags": {"query": statement[:200], "db": str(engine.url.database)},
                },
            })

    @sa_event.listens_for(engine, "handle_error")
    def _error(exception_context):
        _get_client().emit({
            "category": "error",
            "severity": "ERROR",
            "payload": {
                "error_type": type(exception_context.original_exception).__name__,
                "message": str(exception_context.original_exception),
                "context": {
                    "statement": str(exception_context.statement)[:200] if exception_context.statement else None,
                },
            },
        })


def patch_httpx(client: Any) -> None:
    """
    Wrap httpx.AsyncClient or httpx.Client to capture failed/slow requests.

    Usage:
        import httpx
        from omnicapture.interceptors import patch_httpx
        client = httpx.AsyncClient()
        patch_httpx(client)
    """
    original_send = client.send

    async def _patched_send(request, **kwargs):
        start = time.perf_counter()
        try:
            response = await original_send(request, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if response.status_code >= 400:
                _get_client().emit({
                    "category": "network",
                    "severity": "WARNING" if response.status_code < 500 else "ERROR",
                    "payload": {
                        "url": str(request.url)[:200],
                        "method": request.method,
                        "status_code": response.status_code,
                        "latency_ms": round(elapsed_ms, 2),
                        "response_body_preview": response.text[:500] if hasattr(response, "text") else "",
                    },
                })
            return response

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            _get_client().emit({
                "category": "network",
                "severity": "ERROR",
                "payload": {
                    "url": str(request.url)[:200],
                    "method": request.method,
                    "status_code": 0,
                    "latency_ms": round(elapsed_ms, 2),
                    "error_type": type(e).__name__,
                    "message": str(e),
                },
            })
            raise

    client.send = _patched_send
'''
    _write(adapter_dir / "interceptors.py", interceptors_content, files_created)

    return files_created


def install_react_native_adapter(project_path: Path) -> list[str]:
    """Generate React Native adapter files."""
    adapter_dir = project_path / "omnicapture"
    adapter_dir.mkdir(exist_ok=True)
    files_created = []

    # index.ts
    index_content = '''/**
 * OmniCapture React Native Adapter
 * Runtime telemetry for Expo/React Native applications.
 */
export { OmniCaptureClient } from "./client";
export { installNetworkInterceptor } from "./networkInterceptor";
export { OmniCaptureErrorBoundary } from "./errorBoundary";
export { startMetricsCollection } from "./metricsCollector";

import { OmniCaptureClient } from "./client";
import { installNetworkInterceptor } from "./networkInterceptor";

/**
 * Initialize OmniCapture with a single call.
 * Call this in your app's entry point (App.tsx or index.ts).
 */
export function initOmniCapture(config: {
  endpoint: string;
  apiKey: string;
  projectId: string;
}) {
  const client = new OmniCaptureClient(config);
  installNetworkInterceptor(client);
  return client;
}
'''
    _write(adapter_dir / "index.ts", index_content, files_created)

    # client.ts
    client_ts = '''/**
 * OmniCapture fetch-based HTTP client for React Native.
 * Zero external dependencies. Buffers events and batch-uploads.
 */

const FLUSH_INTERVAL_MS = 60_000; // 60 seconds
const BUFFER_MAX = 50;

export interface UTSEvent {
  event_id?: string;
  project_id?: string;
  source_type?: string;
  category: "error" | "performance" | "state_dump" | "network" | "crash" | "custom";
  severity: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL" | "FATAL";
  timestamp_iso?: string;
  environment?: string;
  payload: Record<string, unknown>;
  fingerprint?: string;
}

export class OmniCaptureClient {
  private endpoint: string;
  private apiKey: string;
  private projectId: string;
  private buffer: UTSEvent[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;

  constructor(config: { endpoint: string; apiKey: string; projectId: string }) {
    this.endpoint = config.endpoint;
    this.apiKey = config.apiKey;
    this.projectId = config.projectId;
    this.timer = setInterval(() => this.flush(), FLUSH_INTERVAL_MS);
  }

  emit(event: UTSEvent): void {
    event.event_id = event.event_id ?? crypto.randomUUID();
    event.project_id = this.projectId;
    event.source_type = "react_native";
    event.timestamp_iso = event.timestamp_iso ?? new Date().toISOString();
    event.environment = event.environment ?? __DEV__ ? "development" : "production";

    this.buffer.push(event);
    if (this.buffer.length >= BUFFER_MAX) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const events = [...this.buffer];
    this.buffer = [];

    try {
      await fetch(`${this.endpoint}/api/v1/ingest`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ events }),
      });
    } catch {
      // VPS unreachable — re-buffer (up to limit)
      this.buffer = [...events.slice(-BUFFER_MAX), ...this.buffer].slice(0, BUFFER_MAX * 2);
    }
  }

  destroy(): void {
    if (this.timer) clearInterval(this.timer);
    this.flush();
  }
}
'''
    _write(adapter_dir / "client.ts", client_ts, files_created)

    # networkInterceptor.ts
    network_ts = '''/**
 * OmniCapture Network Interceptor for React Native.
 * Patches global.fetch to capture failed requests (Supabase, Whisper, etc).
 */
import type { OmniCaptureClient } from "./client";

export function installNetworkInterceptor(client: OmniCaptureClient): void {
  const originalFetch = global.fetch;

  global.fetch = async function patchedFetch(
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    const method = init?.method ?? "GET";
    const start = Date.now();

    try {
      const response = await originalFetch(input, init);
      const latency = Date.now() - start;

      if (!response.ok) {
        let bodyPreview = "";
        try {
          bodyPreview = await response.clone().text();
          bodyPreview = bodyPreview.slice(0, 500);
        } catch {}

        client.emit({
          category: "network",
          severity: response.status >= 500 ? "ERROR" : "WARNING",
          payload: {
            url: url.slice(0, 200),
            method,
            status_code: response.status,
            latency_ms: latency,
            response_body_preview: bodyPreview,
          },
        });
      }

      return response;
    } catch (error) {
      const latency = Date.now() - start;
      client.emit({
        category: "network",
        severity: "ERROR",
        payload: {
          url: url.slice(0, 200),
          method,
          status_code: 0,
          latency_ms: latency,
          error_type: (error as Error).name,
          message: (error as Error).message,
        },
      });
      throw error;
    }
  };
}
'''
    _write(adapter_dir / "networkInterceptor.ts", network_ts, files_created)

    # errorBoundary.tsx
    error_boundary = '''/**
 * OmniCapture React Error Boundary.
 * Captures component crashes and ships them to VPS.
 */
import React, { Component, type ReactNode, type ErrorInfo } from "react";
import type { OmniCaptureClient } from "./client";

interface Props {
  client: OmniCaptureClient;
  fallback?: ReactNode;
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class OmniCaptureErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.client.emit({
      category: "crash",
      severity: "FATAL",
      payload: {
        signal: "REACT_ERROR_BOUNDARY",
        exit_code: 1,
        error_type: error.name,
        message: error.message,
        stacktrace: error.stack?.split("\\n") ?? [],
        component_stack: info.componentStack ?? "",
      },
    });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return this.props.fallback ?? null;
    }
    return this.props.children;
  }
}
'''
    _write(adapter_dir / "errorBoundary.tsx", error_boundary, files_created)

    # metricsCollector.ts
    metrics_ts = '''/**
 * OmniCapture Metrics Collector for React Native.
 * Monitors JS thread frame drops via requestAnimationFrame.
 */
import type { OmniCaptureClient } from "./client";

const TARGET_FRAME_MS = 16.67; // 60fps
const REPORT_INTERVAL_MS = 30_000; // Report every 30s

export function startMetricsCollection(client: OmniCaptureClient): () => void {
  let frameDrops = 0;
  let totalFrames = 0;
  let lastTimestamp = 0;
  let rafId: number;
  let intervalId: ReturnType<typeof setInterval>;

  function onFrame(timestamp: number): void {
    if (lastTimestamp > 0) {
      const delta = timestamp - lastTimestamp;
      totalFrames++;
      if (delta > TARGET_FRAME_MS * 1.5) {
        frameDrops++;
      }
    }
    lastTimestamp = timestamp;
    rafId = requestAnimationFrame(onFrame);
  }

  rafId = requestAnimationFrame(onFrame);

  intervalId = setInterval(() => {
    if (totalFrames > 0) {
      const dropPct = (frameDrops / totalFrames) * 100;
      if (dropPct > 5) {
        client.emit({
          category: "performance",
          severity: dropPct > 20 ? "ERROR" : "WARNING",
          payload: {
            metric_name: "js_frame_drop_pct",
            value: Math.round(dropPct * 100) / 100,
            tags: {
              total_frames: totalFrames,
              dropped_frames: frameDrops,
              window_ms: REPORT_INTERVAL_MS,
            },
          },
        });
      }
    }
    frameDrops = 0;
    totalFrames = 0;
  }, REPORT_INTERVAL_MS);

  // Return cleanup function
  return () => {
    cancelAnimationFrame(rafId);
    clearInterval(intervalId);
  };
}
'''
    _write(adapter_dir / "metricsCollector.ts", metrics_ts, files_created)

    return files_created


def install_wii_cpp_adapter(project_path: Path) -> list[str]:
    """Generate Wii/C++ adapter files."""
    adapter_dir = project_path / "omnicapture"
    adapter_dir.mkdir(exist_ok=True)
    files_created = []

    # dolphin_watcher.py
    watcher_content = '''"""
OmniCapture Dolphin Watcher — Monitors Dolphin emulator logs for errors/crashes.

Usage:
    python dolphin_watcher.py --dolphin-log /path/to/Dolphin.log
    python dolphin_watcher.py --follow  # Tail mode
"""
import re
import time
import json
import os
import sys
import signal
import atexit
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Import shared client pattern (or use standalone HTTP)
import urllib.request

# ── Graceful Shutdown (Zero-Crash) ──────────────────────────────────
_running = True

def _shutdown(signum, frame):
    global _running
    _running = False
    sys.stderr.write("dolphin_watcher: received signal, shutting down\\n")
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)
atexit.register(lambda: sys.stderr.write("dolphin_watcher: clean exit\\n"))

VPS_ENDPOINT = os.environ.get("OMNICAPTURE_ENDPOINT", "https://localhost:9877")
API_KEY = os.environ.get("OMNICAPTURE_API_KEY", "")
PROJECT_ID = os.environ.get("OMNICAPTURE_PROJECT", "wii-homebrew")

# Dolphin error patterns
PATTERNS = [
    (r"OSREPORT:\\s*(.+)", "WARNING", "osreport"),
    (r"Panic:\\s*(.+)", "CRITICAL", "panic"),
    (r"DSP:\\s*(.+error.+)", "ERROR", "dsp_error"),
    (r"VI:\\s*(.+error.+)", "ERROR", "vi_error"),
    (r"HLE:\\s*(.+unimplemented.+)", "WARNING", "hle_unimplemented"),
    (r"(SIGSEGV|SIGABRT|Segmentation fault)", "FATAL", "crash_signal"),
    (r"Exception:\\s*(.+)", "ERROR", "exception"),
]

COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), sev, tag) for p, sev, tag in PATTERNS]


def parse_line(line: str) -> dict | None:
    """Parse a Dolphin log line for known error patterns."""
    for pattern, severity, tag in COMPILED_PATTERNS:
        match = pattern.search(line)
        if match:
            return {
                "category": "crash" if severity == "FATAL" else "error",
                "severity": severity,
                "source_type": "wii_cpp",
                "project_id": PROJECT_ID,
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
                "payload": {
                    "error_type": tag,
                    "message": match.group(1) if match.lastindex else match.group(0),
                    "raw_line": line.strip()[:500],
                    "signal": match.group(0) if severity == "FATAL" else None,
                    "exit_code": 139 if "SIGSEGV" in line else 134 if "SIGABRT" in line else None,
                },
            }
    return None


def ship_event(event: dict) -> None:
    """Send a single event to VPS."""
    if not API_KEY:
        print(json.dumps(event), file=sys.stderr)  # Fallback to stderr (never pollute stdout/TTY)
        return

    try:
        payload = json.dumps({"events": [event]}).encode("utf-8")
        req = urllib.request.Request(
            f"{VPS_ENDPOINT}/api/v1/ingest",
            data=payload,
            method="POST",
        )
        req.add_header("Authorization", f"Bearer {API_KEY}")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Failed to ship event: {e}", file=sys.stderr)


def watch_log(log_path: str, follow: bool = False) -> None:
    """Watch a Dolphin log file for errors."""
    path = Path(log_path)
    if not path.exists():
        print(f"Log file not found: {path}", file=sys.stderr)
        return

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        if follow:
            f.seek(0, 2)  # Start at end
        while _running:
            line = f.readline()
            if not line:
                if not follow:
                    break
                time.sleep(0.5)
                continue

            event = parse_line(line)
            if event:
                ship_event(event)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OmniCapture Dolphin Watcher")
    parser.add_argument("--dolphin-log", required=True, help="Path to Dolphin log file")
    parser.add_argument("--follow", action="store_true", help="Tail mode (watch continuously)")
    args = parser.parse_args()
    watch_log(args.dolphin_log, follow=args.follow)
'''
    _write(adapter_dir / "dolphin_watcher.py", watcher_content, files_created)

    return files_created


def install_minecraft_adapter(project_path: Path) -> list[str]:
    """Generate Minecraft adapter migration guide."""
    adapter_dir = project_path / "omnicapture"
    adapter_dir.mkdir(exist_ok=True)
    files_created = []

    migration_content = '''# OmniCapture — Minecraft Adapter Migration Guide

## From KobiiCapture V2.0 to OmniCapture

### Phase 1: Parallel Run (2 weeks)
Keep existing JSONL writers active while adding OmniCapture push.

### Java Changes (KobiCore)

Add `OmniCaptureAdapter.java` to the capture module:

```java
package com.kobicraft.core.modules.capture;

import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONObject;

public class OmniCaptureAdapter {
    private final String endpoint;
    private final String apiKey;
    private final String projectId;
    private final BlockingQueue<JSONObject> buffer = new LinkedBlockingQueue<>(200);
    private final ScheduledExecutorService flusher;

    public OmniCaptureAdapter(String endpoint, String apiKey, String projectId) {
        this.endpoint = endpoint;
        this.apiKey = apiKey;
        this.projectId = projectId;
        this.flusher = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "OmniCapture-Flusher");
            t.setDaemon(true);
            return t;
        });
        this.flusher.scheduleAtFixedRate(this::flush, 10, 10, TimeUnit.SECONDS);
    }

    public void emit(String category, String severity, JSONObject payload) {
        JSONObject event = new JSONObject();
        event.put("event_id", UUID.randomUUID().toString());
        event.put("project_id", projectId);
        event.put("source_type", "minecraft");
        event.put("category", category);
        event.put("severity", severity);
        event.put("timestamp_iso", java.time.Instant.now().toString());
        event.put("timestamp_epoch_ms", System.currentTimeMillis());
        event.put("payload", payload);
        buffer.offer(event);  // Non-blocking, drops if full
    }

    private void flush() {
        if (buffer.isEmpty()) return;
        JSONArray events = new JSONArray();
        JSONObject event;
        while ((event = buffer.poll()) != null && events.length() < 200) {
            events.put(event);
        }
        try {
            URL url = new URL(endpoint + "/api/v1/ingest");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Authorization", "Bearer " + apiKey);
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            JSONObject body = new JSONObject();
            body.put("events", events);
            conn.getOutputStream().write(body.toString().getBytes(StandardCharsets.UTF_8));
            conn.getResponseCode();  // Trigger send
            conn.disconnect();
        } catch (Exception ignored) {
            // VPS unreachable — events dropped (already in local JSONL via legacy writer)
        }
    }

    public void shutdown() {
        flush();
        flusher.shutdown();
    }
}
```

### Wire into existing components:

1. **LogWatcher.java** — In the `publish()` method, after writing to TelemetryWriter, also call:
   `omniAdapter.emit("error", severity, payload);`

2. **GUIDumper.java** — After writing JSON dump, also call:
   `omniAdapter.emit("state_dump", "INFO", dumpPayload);`

3. **ChatSentimentCapture.java** — After writing to sentiment.jsonl, also call:
   `omniAdapter.emit("custom", "INFO", sentimentPayload);`

### Phase 2: After 2-week parallel run
- Compare event counts between legacy JSONL and VPS
- If matching: disable legacy TelemetryWriter local writes
- Remove capture_ingest.py SFTP pull from kobiiclaw.py step 5e
'''
    _write(adapter_dir / "MIGRATION.md", migration_content, files_created)

    return files_created


def _write(filepath: Path, content: str, files_list: list[str]) -> None:
    """Write content to file and track it."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    files_list.append(str(filepath))


def main():
    parser = argparse.ArgumentParser(description="OmniCapture Adapter Installer")
    parser.add_argument("--type", required=True, choices=sorted(ADAPTER_TYPES), help="Adapter type")
    parser.add_argument("--project", required=True, type=Path, help="Target project path")
    args = parser.parse_args()

    project_path = args.project.resolve()
    if not project_path.exists():
        print(f"ERROR: Project path does not exist: {project_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Installing OmniCapture {args.type} adapter in {project_path}/omnicapture/")

    installers = {
        "python": install_python_adapter,
        "react_native": install_react_native_adapter,
        "wii_cpp": install_wii_cpp_adapter,
        "minecraft": install_minecraft_adapter,
    }

    files = installers[args.type](project_path)

    print(f"\nCreated {len(files)} files:")
    for f in files:
        print(f"  {f}")
    print(f"\nNext steps:")
    print(f"  1. Set OMNICAPTURE_API_KEY environment variable")
    print(f"  2. Set OMNICAPTURE_ENDPOINT to your VPS URL")
    print(f"  3. Wire the adapter into your application entry point")
    print(f"  4. Test: trigger a known error, verify it appears in VPS within 30s")


if __name__ == "__main__":
    main()
