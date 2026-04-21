"""
Web runtime dumper — Playwright (chromium headless).

Launches a target Next.js/Electron/static web app, navigates per the action
script, captures screenshot + console log + network HAR.

Playwright's sync API is used from a child process to keep the async/sync
boundary clean (Mistake #34 — no asyncio.run() in library code).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .base import ActionScript, Dumper, DumperError, EvidenceBundle, HTTPResponse

logger = logging.getLogger(__name__)


class WebDumper(Dumper):
    runtime_class = "web"

    def __init__(self, repo_path: Path, config: dict[str, Any], run_id: str) -> None:
        super().__init__(repo_path, config, run_id)
        self._out_dir: Path | None = None
        self._bundle_data: dict[str, Any] = {}
        self._action_name: str = ""

    def launch(self) -> None:
        self._out_dir = Path(tempfile.mkdtemp(prefix=f"sqa-web-{self.run_id}-"))
        self._launched = True
        logger.info("WebDumper launched, out_dir=%s", self._out_dir)

    def trigger(self, action: ActionScript) -> None:
        if not self._launched or self._out_dir is None:
            raise DumperError("WebDumper.trigger() called before launch()")

        self._action_name = action.name
        target_url = action.setup.get("url")
        if not target_url:
            raise DumperError("Web action script missing setup.url")

        script_path = self._out_dir / "playwright_run.py"
        script_path.write_text(_PLAYWRIGHT_WORKER, encoding="utf-8")

        action_json = self._out_dir / "action.json"
        action_json.write_text(action.model_dump_json(), encoding="utf-8")

        cache_dir = os.path.expanduser(
            self.config.get("playwright_cache_dir", "~/.cache/sleepless-qa-playwright")
        )
        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = cache_dir

        cmd = [
            sys.executable,
            str(script_path),
            "--action", str(action_json),
            "--out", str(self._out_dir),
        ]
        timeout = int(self.config.get("subprocess_timeout_seconds", 600))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            logger.error("Playwright worker timed out: %s", exc)
            raise DumperError(f"Playwright timeout after {timeout}s") from exc

        self._bundle_data = {
            "exit_code": result.returncode,
            "stdout": result.stdout[-16_000:],
            "stderr": result.stderr[-16_000:],
        }

        bundle_json = self._out_dir / "bundle.json"
        if bundle_json.exists():
            try:
                self._bundle_data.update(json.loads(bundle_json.read_text(encoding="utf-8")))
            except json.JSONDecodeError as exc:
                logger.warning("bundle.json parse failed: %s", exc)

    def capture(self) -> EvidenceBundle:
        if self._out_dir is None:
            raise DumperError("WebDumper.capture() before trigger()")

        screenshots = sorted(self._out_dir.glob("*.png"))
        console_log = (self._out_dir / "console.log")
        har_file = (self._out_dir / "network.har")

        log_excerpts: dict[str, str] = {}
        if console_log.exists():
            log_excerpts["console"] = console_log.read_text(encoding="utf-8", errors="replace")[-16_000:]
        if har_file.exists():
            log_excerpts["har_path"] = str(har_file)

        http_responses = [
            HTTPResponse(**r) for r in self._bundle_data.get("http_responses", [])
        ]

        return EvidenceBundle(
            run_id=self.run_id,
            runtime_class=self.runtime_class,
            action_script_name=self._action_name,
            screenshots=screenshots,
            log_excerpts=log_excerpts,
            http_responses=http_responses,
            exit_code=self._bundle_data.get("exit_code"),
            stdout=self._bundle_data.get("stdout", ""),
            stderr=self._bundle_data.get("stderr", ""),
            metadata={"out_dir": str(self._out_dir)},
        )

    def teardown(self) -> None:
        # Intentionally do NOT rm -rf the out_dir — evidence is archived.
        # TTL cleanup is handled by a separate job.
        self._launched = False


# Worker script executed in a subprocess. Keeps Playwright's sync API isolated.
_PLAYWRIGHT_WORKER = r'''
"""Playwright worker — runs in its own process."""
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    action = json.loads(Path(args.action).read_text(encoding="utf-8"))

    console_lines: list[str] = []
    http_responses: list[dict] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed", file=sys.stderr)
        return 2

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_har_path=str(out_dir / "network.har"),
        )
        page = context.new_page()
        page.on("console", lambda msg: console_lines.append(f"[{msg.type}] {msg.text}"))
        page.on("response", lambda resp: http_responses.append({
            "url": resp.url,
            "method": resp.request.method,
            "status": resp.status,
            "duration_ms": 0,
            "body_excerpt": "",
        }))

        setup = action.get("setup", {})
        url = setup.get("url")
        if not url:
            print("ERROR: no setup.url", file=sys.stderr)
            return 3

        page.goto(url, wait_until="domcontentloaded", timeout=15_000)
        page.screenshot(path=str(out_dir / "01_initial.png"))

        for i, step in enumerate(action.get("steps", []), start=2):
            kind = step.get("kind")
            target = step.get("target") or ""
            value = step.get("value") or ""
            timeout = int(step.get("timeout_ms", 5000))
            try:
                if kind == "navigate":
                    page.goto(target, wait_until="domcontentloaded", timeout=timeout)
                elif kind == "click":
                    page.click(target, timeout=timeout)
                elif kind == "type":
                    page.fill(target, value, timeout=timeout)
                elif kind == "wait":
                    page.wait_for_selector(target, timeout=timeout)
                elif kind == "custom":
                    page.evaluate(value)
                else:
                    console_lines.append(f"[warn] unknown step kind: {kind}")
            except Exception as exc:
                console_lines.append(f"[step_error] step {i} ({kind}): {exc}")
            page.screenshot(path=str(out_dir / f"{i:02d}_{kind}.png"))

        browser.close()

    (out_dir / "console.log").write_text("\n".join(console_lines), encoding="utf-8")
    (out_dir / "bundle.json").write_text(
        json.dumps({"http_responses": http_responses}, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
