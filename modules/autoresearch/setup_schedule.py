#!/usr/bin/env python3
"""
Cross-platform scheduler for autoresearch nightcrawler.

- Windows: creates scheduled tasks via schtasks /create
- Unix/macOS: installs crontab entries

Usage:
    python setup_schedule.py                # install schedule from config.json
    python setup_schedule.py --uninstall    # remove scheduled tasks
    python setup_schedule.py --status       # show current schedule status
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"
TASK_NAME_PREFIX = "AutoResearch_Nightcrawler"


def load_config() -> dict:
    """Load config.json from the module directory."""
    if not CONFIG_PATH.exists():
        logger.error("Config not found at %s", CONFIG_PATH)
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _python_exe() -> str:
    """Return the path to the current Python interpreter."""
    return sys.executable


def _nightcrawler_path() -> str:
    """Return the absolute path to nightcrawler.py."""
    return str(MODULE_DIR / "nightcrawler.py")


# ---------------------------------------------------------------------------
# Windows: schtasks
# ---------------------------------------------------------------------------

def _install_windows(times: list[str]) -> None:
    """Create Windows scheduled tasks for each run time."""
    python = _python_exe()
    script = _nightcrawler_path()

    for i, t in enumerate(times):
        task_name = f"{TASK_NAME_PREFIX}_{i}"
        cmd = (
            f'schtasks /create /tn "{task_name}" '
            f'/tr "\"{python}\" \"{script}\"" '
            f"/sc daily /st {t} /f"
        )
        logger.info("Creating task: %s at %s", task_name, t)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Failed to create task %s: %s", task_name, result.stderr.strip())
        else:
            logger.info("Task created: %s", task_name)


def _uninstall_windows(times: list[str]) -> None:
    """Remove Windows scheduled tasks."""
    for i in range(len(times)):
        task_name = f"{TASK_NAME_PREFIX}_{i}"
        cmd = f'schtasks /delete /tn "{task_name}" /f'
        logger.info("Removing task: %s", task_name)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("Could not remove %s (may not exist): %s", task_name, result.stderr.strip())
        else:
            logger.info("Task removed: %s", task_name)


def _status_windows(times: list[str]) -> None:
    """Show status of Windows scheduled tasks."""
    for i in range(len(times)):
        task_name = f"{TASK_NAME_PREFIX}_{i}"
        cmd = f'schtasks /query /tn "{task_name}" /fo LIST'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("=== %s ===\n%s", task_name, result.stdout.strip())
        else:
            logger.info("Task %s: not found", task_name)


# ---------------------------------------------------------------------------
# Unix/macOS: crontab
# ---------------------------------------------------------------------------

CRON_MARKER_START = "# >>> AutoResearch Nightcrawler START >>>"
CRON_MARKER_END = "# <<< AutoResearch Nightcrawler END <<<"


def _get_existing_crontab() -> str:
    """Read current user crontab."""
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout


def _set_crontab(content: str) -> None:
    """Write new crontab content."""
    proc = subprocess.run(
        ["crontab", "-"],
        input=content,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        logger.error("Failed to set crontab: %s", proc.stderr.strip())
        sys.exit(1)


def _strip_autoresearch_block(crontab: str) -> str:
    """Remove existing autoresearch block from crontab text."""
    lines = crontab.splitlines()
    result: list[str] = []
    inside_block = False
    for line in lines:
        if line.strip() == CRON_MARKER_START:
            inside_block = True
            continue
        if line.strip() == CRON_MARKER_END:
            inside_block = False
            continue
        if not inside_block:
            result.append(line)
    return "\n".join(result).strip()


def _install_unix(times: list[str]) -> None:
    """Install crontab entries for each run time."""
    python = _python_exe()
    script = _nightcrawler_path()

    existing = _get_existing_crontab()
    cleaned = _strip_autoresearch_block(existing)

    cron_lines = [CRON_MARKER_START]
    for t in times:
        hour, minute = t.split(":")
        cron_lines.append(
            f"{int(minute)} {int(hour)} * * * {python} {script} >> ~/.claude/autoresearch-triggers/cron.log 2>&1"
        )
    cron_lines.append(CRON_MARKER_END)

    new_crontab = cleaned + "\n" + "\n".join(cron_lines) + "\n"
    _set_crontab(new_crontab)
    logger.info("Installed %d cron entries", len(times))


def _uninstall_unix() -> None:
    """Remove autoresearch crontab entries."""
    existing = _get_existing_crontab()
    cleaned = _strip_autoresearch_block(existing)
    _set_crontab(cleaned + "\n" if cleaned else "")
    logger.info("Removed autoresearch cron entries")


def _status_unix() -> None:
    """Show autoresearch crontab entries."""
    existing = _get_existing_crontab()
    inside = False
    found = False
    for line in existing.splitlines():
        if line.strip() == CRON_MARKER_START:
            inside = True
            found = True
            continue
        if line.strip() == CRON_MARKER_END:
            inside = False
            continue
        if inside:
            logger.info("  %s", line)
    if not found:
        logger.info("No autoresearch schedule installed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Manage autoresearch schedule")
    parser.add_argument("--uninstall", action="store_true", help="Remove scheduled tasks")
    parser.add_argument("--status", action="store_true", help="Show schedule status")
    args = parser.parse_args()

    config = load_config()
    times = config.get("schedule", {}).get("times", ["02:00", "14:00"])
    is_windows = platform.system() == "Windows"

    if args.status:
        logger.info("Platform: %s", platform.system())
        logger.info("Configured times: %s", times)
        if is_windows:
            _status_windows(times)
        else:
            _status_unix()
        return

    if args.uninstall:
        logger.info("Uninstalling autoresearch schedule...")
        if is_windows:
            _uninstall_windows(times)
        else:
            _uninstall_unix()
        logger.info("Done.")
        return

    # Install
    logger.info("Installing autoresearch schedule...")
    logger.info("Platform: %s", platform.system())
    logger.info("Times: %s", times)
    if is_windows:
        _install_windows(times)
    else:
        _install_unix(times)
    logger.info("Done. Run with --status to verify.")


if __name__ == "__main__":
    main()
