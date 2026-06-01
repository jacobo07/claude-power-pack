"""Audit log for firewall hits -- only metadata, never raw values."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from .detector import Hit

AUDIT_PATH = (
    Path(__file__).resolve().parents[2]
    / "vault" / "secret_firewall" / "audit.jsonl"
)


def report(source: str, hits: Iterable[Hit]) -> None:
    hits_list = list(hits)
    if not hits_list:
        return
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": source,
        "hits": [
            {
                "pattern_name": h.pattern_name,
                "severity": h.severity.name,
                "line_no": h.line_no,
            }
            for h in hits_list
        ],
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
