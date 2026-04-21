"""
Python daemon dumper — subprocess launcher + httpx probe matrix.

Launches a uvicorn/FastAPI subprocess from the target repo, waits for the
health endpoint, then runs the action script's HTTP steps and records each
response. Captures stdout/stderr tail from the daemon.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .base import ActionScript, Dumper, DumperError, EvidenceBundle, HTTPResponse

logger = logging.getLogger(__name__)


class PythonDaemonDumper(Dumper):
    runtime_class = "python_daemon"

    def __init__(self, repo_path: Path, config: dict[str, Any], run_id: str) -> None:
        super().__init__(repo_path, config, run_id)
        self._proc: subprocess.Popen[bytes] | None = None
        self._out_dir: Path | None = None
        self._action_name: str = ""
        self._responses: list[HTTPResponse] = []
        self._base_url: str = ""

    def launch(self) -> None:
        self._out_dir = Path(tempfile.mkdtemp(prefix=f"sqa-py-{self.run_id}-"))
        self._launched = True
        logger.info("PythonDaemonDumper out_dir=%s", self._out_dir)

    def _start_daemon(self, action: ActionScript) -> None:
        if self._out_dir is None:
            raise DumperError("PythonDaemonDumper: _out_dir not initialized")

        launch_cmd_str = action.setup.get("launch_cmd")
        if not launch_cmd_str:
            raise DumperError("python_daemon action script missing setup.launch_cmd")
        self._base_url = action.setup.get("base_url", "http://127.0.0.1:8000")

        stdout_file = open(self._out_dir / "daemon.stdout", "wb")
        stderr_file = open(self._out_dir / "daemon.stderr", "wb")

        logger.info("Launching daemon: %s (cwd=%s)", launch_cmd_str, self.repo_path)
        self._proc = subprocess.Popen(
            launch_cmd_str,
            shell=True,
            cwd=str(self.repo_path),
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
        )

        wait_s = int(self.config.get("uvicorn_startup_wait_seconds", 5))
        time.sleep(wait_s)

        if self._proc.poll() is not None:
            raise DumperError(
                f"Daemon exited immediately with code {self._proc.returncode}. "
                f"Check {self._out_dir}/daemon.stderr"
            )

    def trigger(self, action: ActionScript) -> None:
        self._action_name = action.name
        self._start_daemon(action)

        try:
            import httpx  # type: ignore
        except ImportError as exc:
            raise DumperError("httpx not installed") from exc

        timeout = float(self.config.get("probe_timeout_seconds", 10))
        client = httpx.Client(base_url=self._base_url, timeout=timeout)

        try:
            for step in action.steps:
                if step.kind != "http":
                    logger.warning("python_daemon: non-http step ignored: %s", step.kind)
                    continue
                method = (step.extra.get("method") or "GET").upper()
                path = step.target or "/"
                body = step.extra.get("json")

                t0 = time.monotonic()
                try:
                    resp = client.request(method, path, json=body)
                except Exception as exc:
                    logger.error("HTTP probe failed: %s %s: %s", method, path, exc)
                    self._responses.append(
                        HTTPResponse(
                            url=f"{self._base_url}{path}",
                            method=method,
                            status=0,
                            duration_ms=int((time.monotonic() - t0) * 1000),
                            body_excerpt=f"PROBE_ERROR: {exc}",
                        )
                    )
                    continue
                duration_ms = int((time.monotonic() - t0) * 1000)
                body_text = resp.text[:8192]
                self._responses.append(
                    HTTPResponse(
                        url=str(resp.url),
                        method=method,
                        status=resp.status_code,
                        duration_ms=duration_ms,
                        body_excerpt=body_text,
                    )
                )
        finally:
            client.close()

    def capture(self) -> EvidenceBundle:
        if self._out_dir is None:
            raise DumperError("PythonDaemonDumper.capture() before trigger()")

        stdout_path = self._out_dir / "daemon.stdout"
        stderr_path = self._out_dir / "daemon.stderr"
        log_excerpts: dict[str, str] = {}
        if stdout_path.exists():
            log_excerpts["stdout"] = stdout_path.read_bytes()[-16_000:].decode("utf-8", "replace")
        if stderr_path.exists():
            log_excerpts["stderr"] = stderr_path.read_bytes()[-16_000:].decode("utf-8", "replace")

        exit_code = self._proc.returncode if self._proc and self._proc.poll() is not None else None

        return EvidenceBundle(
            run_id=self.run_id,
            runtime_class=self.runtime_class,
            action_script_name=self._action_name,
            screenshots=[],
            log_excerpts=log_excerpts,
            http_responses=self._responses,
            exit_code=exit_code,
            stdout=log_excerpts.get("stdout", ""),
            stderr=log_excerpts.get("stderr", ""),
            metadata={"base_url": self._base_url, "out_dir": str(self._out_dir)},
        )

    def teardown(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            logger.info("Killing daemon pid=%d", self._proc.pid)
            try:
                if os.name == "nt":
                    self._proc.terminate()
                else:
                    os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
                try:
                    self._proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name == "nt":
                        self._proc.kill()
                    else:
                        os.killpg(os.getpgid(self._proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                logger.debug("Daemon already exited before teardown")
            except Exception:
                logger.exception("Daemon teardown failed")
        self._launched = False
