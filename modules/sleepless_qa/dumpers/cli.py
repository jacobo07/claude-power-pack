"""
Generic CLI dumper — subprocess with captured stdout/stderr + exit code.

For tools that accept arguments and exit. NOT for long-running daemons — use
python_daemon for those.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .base import ActionScript, Dumper, DumperError, EvidenceBundle

logger = logging.getLogger(__name__)


class CLIDumper(Dumper):
    runtime_class = "cli"

    def __init__(self, repo_path: Path, config: dict[str, Any], run_id: str) -> None:
        super().__init__(repo_path, config, run_id)
        self._out_dir: Path | None = None
        self._action_name: str = ""
        self._result: subprocess.CompletedProcess[str] | None = None

    def launch(self) -> None:
        self._out_dir = Path(tempfile.mkdtemp(prefix=f"sqa-cli-{self.run_id}-"))
        self._launched = True

    def trigger(self, action: ActionScript) -> None:
        if self._out_dir is None:
            raise DumperError("CLIDumper.trigger() before launch()")
        self._action_name = action.name

        invocation = action.setup.get("command")
        if not invocation:
            raise DumperError("cli action script missing setup.command")

        timeout = int(self.config.get("default_timeout_seconds", 60))
        logger.info("Running CLI: %s (cwd=%s)", invocation, self.repo_path)
        try:
            self._result = subprocess.run(
                invocation,
                shell=True,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise DumperError(f"CLI timeout after {timeout}s: {invocation}") from exc

        (self._out_dir / "stdout.txt").write_text(
            self._result.stdout or "", encoding="utf-8"
        )
        (self._out_dir / "stderr.txt").write_text(
            self._result.stderr or "", encoding="utf-8"
        )

    def capture(self) -> EvidenceBundle:
        if self._result is None or self._out_dir is None:
            raise DumperError("CLIDumper.capture() before trigger()")
        return EvidenceBundle(
            run_id=self.run_id,
            runtime_class=self.runtime_class,
            action_script_name=self._action_name,
            screenshots=[],
            log_excerpts={
                "stdout": (self._result.stdout or "")[-16_000:],
                "stderr": (self._result.stderr or "")[-16_000:],
            },
            http_responses=[],
            exit_code=self._result.returncode,
            stdout=(self._result.stdout or "")[-16_000:],
            stderr=(self._result.stderr or "")[-16_000:],
            metadata={"out_dir": str(self._out_dir)},
        )

    def teardown(self) -> None:
        self._launched = False
