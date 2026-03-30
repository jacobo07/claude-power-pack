#!/usr/bin/env python3
"""
Nightcrawler v2 -- Autoresearch orchestrator.

Runs the research pipeline sequentially:
  1. rss_sniffer.py    -- poll RSS feeds from config
  2. youtube_firehose.py -- poll YouTube channels from config
  3. cross_signal_bus.py -- cross-project signal correlation + digest

Features:
  - Lockfile-based throttle to enforce min_interval_hours
  - Config-driven (reads config.json)
  - Batch digest generation
  - Optional Telegram notification
  - Appends run metadata to nightcrawler_runs.jsonl
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [nightcrawler] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
BASE_DIR = Path.home() / ".claude" / "autoresearch-triggers"
LOCKFILE = BASE_DIR / "nightcrawler.lock"
RUNS_LOG = BASE_DIR / "nightcrawler_runs.jsonl"
CONFIG_PATH = MODULE_DIR / "config.json"


def load_config() -> dict:
    """Load config.json from module directory."""
    if not CONFIG_PATH.exists():
        logger.error("Config not found: %s", CONFIG_PATH)
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Lockfile throttle
# ---------------------------------------------------------------------------

def check_lockfile(min_interval_hours: float) -> bool:
    """
    Return True if enough time has passed since the last run.
    Returns True (allow) if lockfile is missing or stale.
    """
    if not LOCKFILE.exists():
        return True
    try:
        data = json.loads(LOCKFILE.read_text(encoding="utf-8"))
        last_run = data.get("last_run_epoch", 0)
        elapsed_hours = (time.time() - last_run) / 3600
        if elapsed_hours < min_interval_hours:
            logger.info(
                "Throttled: %.1fh since last run (min %.1fh)",
                elapsed_hours,
                min_interval_hours,
            )
            return False
        return True
    except (json.JSONDecodeError, ValueError):
        logger.warning("Corrupt lockfile, allowing run")
        return True


def update_lockfile() -> None:
    """Write current timestamp to lockfile."""
    LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_run_epoch": time.time(),
        "last_run_iso": datetime.now(timezone.utc).isoformat(),
    }
    LOCKFILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.debug("Lockfile updated")


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def run_step(script_name: str) -> dict:
    """
    Run a pipeline script and capture result.
    Returns dict with status, duration, and any errors.
    """
    script_path = MODULE_DIR / script_name
    if not script_path.exists():
        logger.error("Script not found: %s", script_path)
        return {"script": script_name, "status": "missing", "duration_s": 0, "error": "file not found"}

    logger.info("Running %s ...", script_name)
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per step
            cwd=str(MODULE_DIR),
        )
        duration = round(time.time() - start, 2)
        if result.returncode != 0:
            logger.warning(
                "%s exited with code %d: %s",
                script_name,
                result.returncode,
                result.stderr[:500] if result.stderr else "(no stderr)",
            )
            return {
                "script": script_name,
                "status": "error",
                "exit_code": result.returncode,
                "duration_s": duration,
                "error": result.stderr[:500] if result.stderr else None,
            }
        logger.info("%s completed in %.1fs", script_name, duration)
        return {"script": script_name, "status": "ok", "duration_s": duration}
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start, 2)
        logger.error("%s timed out after %.1fs", script_name, duration)
        return {"script": script_name, "status": "timeout", "duration_s": duration}
    except Exception as exc:
        duration = round(time.time() - start, 2)
        logger.error("%s failed: %s", script_name, exc)
        return {"script": script_name, "status": "exception", "duration_s": duration, "error": str(exc)}


# ---------------------------------------------------------------------------
# Telegram notification
# ---------------------------------------------------------------------------

def send_telegram_digest(config: dict, digest_path: Path) -> None:
    """Send digest summary via Telegram if enabled."""
    tg = config.get("telegram", {})
    if not tg.get("enabled", False):
        logger.debug("Telegram disabled, skipping notification")
        return

    bot_token = os.environ.get(tg.get("bot_token_env", "TELEGRAM_BOT_TOKEN"))
    chat_id = os.environ.get(tg.get("chat_id_env", "TELEGRAM_CHAT_ID"))

    if not bot_token or not chat_id:
        logger.warning("Telegram env vars not set, skipping notification")
        return

    if not digest_path.exists():
        logger.warning("No digest file to send: %s", digest_path)
        return

    try:
        import httpx  # noqa: delayed import to avoid hard dep if telegram disabled

        digest_text = digest_path.read_text(encoding="utf-8")
        # Truncate for Telegram's 4096 char limit
        if len(digest_text) > 4000:
            digest_text = digest_text[:3950] + "\n\n... (truncated)"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"Nightcrawler Digest\n\n{digest_text}",
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram notification sent")
            else:
                logger.warning("Telegram API returned %d: %s", resp.status_code, resp.text[:200])
    except ImportError:
        logger.warning("httpx not installed, cannot send Telegram notification")
    except Exception as exc:
        logger.warning("Telegram send failed: %s", exc)


# ---------------------------------------------------------------------------
# Run log
# ---------------------------------------------------------------------------

def append_run_log(run_record: dict) -> None:
    """Append a run record to nightcrawler_runs.jsonl."""
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(run_record) + "\n")
    logger.debug("Run record appended to %s", RUNS_LOG)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PIPELINE_STEPS = [
    "rss_sniffer.py",
    "youtube_firehose.py",
    "cross_signal_bus.py",
]


def main() -> None:
    logger.info("=== Nightcrawler v2 starting ===")
    config = load_config()

    # Throttle check
    min_interval = config.get("throttle", {}).get("min_interval_hours", 6)
    if not check_lockfile(min_interval):
        logger.info("Exiting due to throttle")
        return

    BASE_DIR.mkdir(parents=True, exist_ok=True)

    run_start = time.time()
    run_iso = datetime.now(timezone.utc).isoformat()
    step_results: list[dict] = []

    # Run pipeline sequentially
    for step_name in PIPELINE_STEPS:
        result = run_step(step_name)
        step_results.append(result)

    run_duration = round(time.time() - run_start, 2)

    # Update lockfile after successful run
    update_lockfile()

    # Check for digest
    digest_path = BASE_DIR / "latest_digest.md"
    if digest_path.exists():
        send_telegram_digest(config, digest_path)

    # Build run record
    all_ok = all(r.get("status") == "ok" for r in step_results)
    run_record = {
        "timestamp": run_iso,
        "duration_s": run_duration,
        "status": "ok" if all_ok else "partial",
        "steps": step_results,
    }
    append_run_log(run_record)

    logger.info(
        "=== Nightcrawler v2 complete (%.1fs, %s) ===",
        run_duration,
        "all OK" if all_ok else "some errors",
    )


if __name__ == "__main__":
    main()
