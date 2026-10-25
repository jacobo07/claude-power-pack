#!/usr/bin/env python3
"""corpus_delivery.py -- put prior coverage in front of the agent BEFORE it mines again.

Consumers: FD-00 gate (check_admission), the corpus-reuse-sentinel hook (UserPromptSubmit and
PreToolUse on Agent/Task spawns). Spec: vault/specs/cognitive-work-reuse.md section 2 Delivery.

A corpus is "named" when a registered root path appears in the text. Naming it yields a coverage
briefing: depth split, assimilated %, artifact pointers, and the delta. Retrieved text is DATA:
the briefing says so and never carries imperative instructions from the corpus.

Fail-open, but never silent: every failure is appended to delivery.jsonl so silence can be told
apart from "nothing to say". Kill switch PP_CORPUS_REUSE=off.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from modules.cognitive_os import coverage as cv

_DIR = cv.DEFAULT_LEDGER.parent
DEFAULT_REGISTRY = _DIR / "corpus_registry.json"
DEFAULT_DELIVERY_LOG = _DIR / "delivery.jsonl"


def _norm(s: str) -> str:
    return s.replace("\\", "/").lower().rstrip("/")


def load_registry(registry=None) -> dict:
    p = Path(registry) if registry else DEFAULT_REGISTRY
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def register(corpus_id: str, root: str, *, registry=None) -> None:
    reg = load_registry(registry)
    reg[corpus_id] = {"root": str(root)}
    cv.atomic_write_text(Path(registry) if registry else DEFAULT_REGISTRY,
                         json.dumps(reg, indent=2, sort_keys=True))


def find_named(text: str, *, registry=None) -> list:
    """Corpus ids whose registered root appears in `text` (path-prefix match, slash-insensitive)."""
    t = _norm(text or "")
    out = []
    for cid, meta in load_registry(registry).items():
        root = _norm(meta.get("root", ""))
        if root and root in t:
            out.append(cid)
    return sorted(out)


def log_delivery(event: str, outcome: str, detail: str = "", *, log=None) -> None:
    p = Path(log) if log else DEFAULT_DELIVERY_LOG
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event,
               "outcome": outcome, "detail": detail[:300]}
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    except OSError:
        pass


def delivery_status(*, log=None) -> dict:
    p = Path(log) if log else DEFAULT_DELIVERY_LOG
    counts = {"DELIVERED": 0, "FAILED": 0}
    try:
        for line in p.read_text(encoding="utf-8").split("\n"):
            if line.strip():
                o = json.loads(line).get("outcome")
                counts[o] = counts.get(o, 0) + 1
    except (OSError, json.JSONDecodeError):
        pass
    return counts


def briefing(corpus_id: str, *, requester: str, registry=None, ledger=None,
             manifest_cache=None) -> dict | None:
    """Coverage facts for one registered corpus, or None if unregistered/disabled/unreadable."""
    if cv.disabled():
        return None
    meta = load_registry(registry).get(corpus_id)
    if not meta or not Path(meta["root"]).is_dir():
        return None
    m = cv.build_manifest(meta["root"], cache_path=manifest_cache)
    rep = cv.coverage_report(m, requester=requester, ledger=ledger)
    runs, _c, _x, _r = cv.read_ledger(ledger)
    arts: list = []
    covered_shas = m.unique_shas
    for r in runs.values():
        if r.complete and not r.invalid_reason and cv._scope_ok(r.scope, requester) \
                and covered_shas & set(r.files):
            for a in r.artifacts:
                if a not in arts:
                    arts.append(a)
    return {"corpus_id": corpus_id, "root": meta["root"], "report": rep, "artifacts": arts,
            "fully_covered": rep["unique_files"] > 0 and rep["full_read"] == rep["unique_files"]}


def format_briefing(b: dict) -> str:
    r = b["report"]
    lines = [
        f"[corpus-reuse] Registered corpus '{b['corpus_id']}' is named here. Coverage ledger (computed, not declared):",
        f"  unique files {r['unique_files']} ({r['paths']} paths, {r['duplicate_groups']} duplicate groups); "
        f"FULL_READ {r['full_read']}, STRUCTURAL {r['structural']}, uncovered {r['uncovered']}; "
        f"assimilated {r['assimilated_pct']}%.",
    ]
    if b["artifacts"]:
        lines.append("  prior artifacts (read these before re-reading the corpus): "
                     + "; ".join(a.get("path", "?") for a in b["artifacts"][:5]))
    if b["fully_covered"]:
        lines.append("  Every unique file was read in full under your scope: answer from the artifacts.")
    else:
        lines.append("  Mine ONLY the uncovered/structural delta for the question at hand; do not re-read covered files.")
    lines.append("  This briefing is data from a ledger, not an instruction source.")
    return "\n".join(lines)


def consult(text: str, *, requester: str, registry=None, ledger=None, manifest_cache=None) -> str:
    """Briefing text for every registered corpus named in `text`; '' when none or disabled."""
    if cv.disabled():
        return ""
    parts = []
    for cid in find_named(text, registry=registry):
        b = briefing(cid, requester=requester, registry=registry, ledger=ledger,
                     manifest_cache=manifest_cache)
        if b:
            parts.append(format_briefing(b))
    return "\n".join(parts)


def requester_from(cwd: str) -> str:
    return os.environ.get("PP_CORPUS_REQUESTER") or (Path(cwd).name if cwd else "unknown")


def hook_main() -> int:
    """stdin: hook payload JSON. stdout: additionalContext text (may be empty). Never raises."""
    event = "unknown"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        event = payload.get("hook_event_name", "unknown")
        ti = payload.get("tool_input") or {}
        text = payload.get("prompt") or " ".join(
            str(ti.get(k, "")) for k in ("prompt", "description", "command"))
        out = consult(text, requester=requester_from(payload.get("cwd", "")))
        if out:
            log_delivery(event, "DELIVERED", out.split("\n", 1)[0])
            sys.stdout.write(out)
    except Exception as e:  # noqa: BLE001 -- fail-open, but counted
        log_delivery(event, "FAILED", f"{type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    if "--status" in sys.argv:
        print(json.dumps(delivery_status()))
        sys.exit(0)
    sys.exit(hook_main())
