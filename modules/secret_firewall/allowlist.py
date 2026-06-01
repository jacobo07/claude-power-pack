"""Owner-managed allowlist by sha256(value). Absent by default."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ALLOWLIST_PATH = (
    Path(__file__).resolve().parents[2]
    / "vault" / "secret_firewall" / "allowlist.json"
)


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def is_allowed(raw_value: str) -> bool:
    if not ALLOWLIST_PATH.is_file():
        return False
    try:
        data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return _hash(raw_value) in set(data.get("allowed_hashes", []))
