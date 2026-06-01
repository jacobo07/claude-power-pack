"""Registry corruption recovery -- backs up the broken file and
returns an empty registry. Caller (typically a SessionStart hook)
re-registers active panes from runtime state."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from .registry import DEFAULT_REGISTRY_PATH, PaneRegistry


def recover_corrupt_registry(
    path: Path | None = None,
) -> tuple[PaneRegistry, bool]:
    """Returns (registry, recovered_flag). When the file parses
    cleanly: returns the live registry and False. When it doesn't:
    backs up the broken file to <path>.corrupt-<ts>.bak (best effort)
    and returns an empty registry + True."""
    p = path or DEFAULT_REGISTRY_PATH
    if not p.is_file():
        return PaneRegistry(_path=p), False
    try:
        json.loads(p.read_text(encoding="utf-8"))
        return PaneRegistry.load(p), False
    except (OSError, json.JSONDecodeError):
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        backup = p.with_suffix(f".corrupt-{ts}.bak")
        try:
            shutil.copy2(p, backup)
        except OSError:
            pass
        return PaneRegistry(_path=p), True
