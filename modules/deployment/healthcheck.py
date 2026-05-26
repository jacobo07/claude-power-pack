"""Healthcheck helpers -- tcp / http / curl-grep.

Each kind returns a dict with shape:
  { "ok": bool, "attempts": int, "evidence": str, "kind": str }

The healthcheck is the receipt. A deploy without a passing healthcheck
is, by the Reality Contract in the spec, NOT a deploy. The dispatcher
in deploy.py refuses to write a vault/deploys/<ts>_*.md report unless
the healthcheck has run -- success or fail. Silent masking is forbidden.
"""

from __future__ import annotations

import json
import socket
import subprocess
import time
from typing import Any


def _truncate(text: str, limit: int = 500) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def check_tcp(
    target: str,
    port: int,
    retries: int = 6,
    delay_sec: int = 10,
    connect_timeout: float = 5.0,
) -> dict[str, Any]:
    """TCP-level reachability. Used for ports without an HTTP layer
    to interrogate -- e.g., Minecraft on 25565. Pure socket; no
    external binary. Each retry pauses delay_sec.
    """
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            with socket.create_connection((target, port), timeout=connect_timeout):
                return {
                    "ok": True,
                    "attempts": attempt,
                    "evidence": f"tcp connect to {target}:{port} succeeded on attempt {attempt}",
                    "kind": "tcp",
                }
        except (OSError, socket.timeout) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(delay_sec)
    return {
        "ok": False,
        "attempts": retries,
        "evidence": f"tcp connect to {target}:{port} failed all {retries} attempts; last error: {last_error}",
        "kind": "tcp",
    }


def check_http(
    url: str,
    retries: int = 6,
    delay_sec: int = 10,
    expect_status: int = 200,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """HTTP-level liveness via curl CLI (universal on Windows + Unix).
    """
    last_evidence = ""
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-fsS",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    "--max-time",
                    str(int(timeout)),
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
                check=False,
            )
            code = (result.stdout or "").strip()
            if code == str(expect_status):
                return {
                    "ok": True,
                    "attempts": attempt,
                    "evidence": f"curl {url} returned HTTP {code} on attempt {attempt}",
                    "kind": "http",
                }
            last_evidence = (
                f"attempt {attempt}: curl returned code='{code}', stderr={_truncate(result.stderr)}"
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            last_evidence = f"attempt {attempt}: {type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(delay_sec)
    return {
        "ok": False,
        "attempts": retries,
        "evidence": _truncate(last_evidence),
        "kind": "http",
    }


def check_curl_grep(
    url: str,
    grep_pattern: str,
    retries: int = 24,
    delay_sec: int = 15,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """§77-style content verification. HTTP 200 is insufficient because
    a stale build still returns 200. Verify the live page literally
    contains the expected regex pattern. Used by InfinityOps
    deploy-vps.yml (24 attempts x 15s = ~6 minute window for the
    Next.js rebuild).
    """
    import re as _re

    pattern = _re.compile(grep_pattern, _re.IGNORECASE)
    last_evidence = ""
    for attempt in range(1, retries + 1):
        try:
            # text=False -> capture stdout as raw bytes, decode UTF-8
            # explicitly. text=True on Windows decodes with locale
            # (cp1252) which mangles UTF-8 bytes (e.g. "brújula"
            # 0xC3 0xBA -> "brÃºjula"), breaking any non-ASCII grep
            # pattern in the live page. Monitoring Axis L1 (2026-05-26).
            result = subprocess.run(
                ["curl", "-fsS", "--max-time", str(int(timeout)), url],
                capture_output=True,
                timeout=timeout + 5,
                check=False,
            )
            body = (result.stdout or b"").decode("utf-8", errors="replace")
            if pattern.search(body):
                return {
                    "ok": True,
                    "attempts": attempt,
                    "evidence": f"curl {url} contained pattern '{grep_pattern}' on attempt {attempt}",
                    "kind": "curl-grep",
                }
            stderr_text = (result.stderr or b"").decode("utf-8", errors="replace")
            last_evidence = (
                f"attempt {attempt}: pattern '{grep_pattern}' not found; "
                f"body_len={len(body)} stderr={_truncate(stderr_text)}"
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            last_evidence = f"attempt {attempt}: {type(exc).__name__}: {exc}"
        if attempt < retries:
            time.sleep(delay_sec)
    return {
        "ok": False,
        "attempts": retries,
        "evidence": _truncate(last_evidence),
        "kind": "curl-grep",
    }


def run_healthcheck(spec: dict[str, Any]) -> dict[str, Any]:
    """Dispatch on spec['kind']. Unknown kind -> ok=False, evidence
    describes the gap.
    """
    kind = (spec or {}).get("kind", "").lower()
    retries = int(spec.get("retries", 6))
    delay_sec = int(spec.get("delay_sec", 10))
    if kind == "tcp":
        return check_tcp(
            target=str(spec["target"]),
            port=int(spec["port"]),
            retries=retries,
            delay_sec=delay_sec,
        )
    if kind == "http":
        return check_http(
            url=str(spec["url"]),
            retries=retries,
            delay_sec=delay_sec,
            expect_status=int(spec.get("expect_status", 200)),
        )
    if kind == "curl-grep":
        return check_curl_grep(
            url=str(spec["url"]),
            grep_pattern=str(spec["grep_pattern"]),
            retries=retries,
            delay_sec=delay_sec,
        )
    return {
        "ok": False,
        "attempts": 0,
        "evidence": f"unknown healthcheck kind: {kind!r}; expected one of tcp / http / curl-grep",
        "kind": kind,
    }


if __name__ == "__main__":
    import sys

    spec = json.loads(sys.stdin.read())
    print(json.dumps(run_healthcheck(spec), indent=2))
