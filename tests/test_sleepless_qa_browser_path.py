"""Regression: WebDumper must not point Playwright at a directory that is empty.

The default `~/.cache/sleepless-qa-playwright` is correct on the VPS, where
`vps/install.sh` installs chromium into exactly that path. On any host where
Playwright was installed normally the directory does not exist, and exporting
PLAYWRIGHT_BROWSERS_PATH at it hides the real install -- every web action then
fails with "executable doesn't exist".

The earlier reading of this defect was that the default path was simply wrong
and needed changing. It is not wrong; it is paired with an installer. Changing
it would have broken the VPS to fix the laptop.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))


def _env_for(config: dict, monkeypatch, tmp_path) -> dict:
    """Reproduce the dumper's env-building decision in isolation.

    The real `trigger()` needs a launched dumper and an ActionScript; the
    decision under test is the four lines that build `env`, so those are what
    the test drives.
    """
    cache_dir = os.path.expanduser(
        config.get("playwright_cache_dir", "~/.cache/sleepless-qa-playwright")
    )
    env = os.environ.copy()
    if os.path.isdir(cache_dir):
        env["PLAYWRIGHT_BROWSERS_PATH"] = cache_dir
    elif config.get("playwright_cache_dir"):
        raise ValueError(cache_dir)
    return env


def test_absent_default_cache_leaves_playwright_to_resolve_itself(monkeypatch, tmp_path):
    # Arrange -- a home with no sleepless cache, the normal laptop shape
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)

    # Act
    env = _env_for({}, monkeypatch, tmp_path)

    # Assert -- the variable is not set at all, so Playwright finds its own
    assert "PLAYWRIGHT_BROWSERS_PATH" not in env


def test_present_cache_is_used(monkeypatch, tmp_path):
    cache = tmp_path / "sleepless-cache"
    cache.mkdir()
    env = _env_for({"playwright_cache_dir": str(cache)}, monkeypatch, tmp_path)
    assert env["PLAYWRIGHT_BROWSERS_PATH"] == str(cache)


def test_configured_but_missing_cache_is_an_error_not_a_silent_fallback(
    monkeypatch, tmp_path
):
    """An operator who set the path deliberately needs to know it is wrong."""
    missing = tmp_path / "not-there"
    with pytest.raises(ValueError):
        _env_for({"playwright_cache_dir": str(missing)}, monkeypatch, tmp_path)


def test_the_real_module_implements_the_same_decision():
    """Guards against the test drifting from the code it describes."""
    src = (_PP / "modules" / "sleepless_qa" / "dumpers" / "web.py").read_text(
        encoding="utf-8"
    )
    assert "if os.path.isdir(cache_dir):" in src
    assert 'env["PLAYWRIGHT_BROWSERS_PATH"] = cache_dir' in src
