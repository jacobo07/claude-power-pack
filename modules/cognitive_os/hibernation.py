#!/usr/bin/env python3
"""hibernation.py -- CO-07: Session Hibernation & Dedup.

A session that is idle, expensive, or waiting should not hold live context. CO-07
lets a session FREEZE -> serialize -> compress -> store -> destroy its active
context, then RESTORE on demand, integrity-verified. Hibernation is how the kernel
keeps the number of HOT sessions low (the lever CO-08 enforces) WITHOUT losing any
session's work.

The cardinal safety rule (CO-07 I.3), inherited from the Session Safety Contract +
the deploy doctrine (HR-005 backup-before-write): **never destroy live context
before the archive is stored AND verified.** Ordering: freeze -> compress -> store
-> VERIFY store -> only then free the hot slot. If any step before verify fails,
the session stays HOT (fail-open toward keeping it alive). The worst case is a
missed economy (a session that should have hibernated stays hot), NEVER a lost
session. A `.jsonl` transcript is never destroyed -- the archive references it; the
live record is sacred.

Restore is complete ONLY on a G4-style RECOVERED verdict; a corrupt archive or a
vanished resume anchor yields FAILED (never a silently-wrong restore); a moved cwd
yields PARTIAL with the missing dimension enumerated. EXTEND of snapshot_versioning
(G3 serialization) + restore_guard dedup; the genuinely new steps are real
compression + voluntary destroy-and-restore as an economy move.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

DEFAULT_ARCHIVE = _PP_ROOT / "vault" / "cognitive_os" / "hibernation.jsonl"


@dataclass
class HibernationResult:
    ok: bool                           # True only when store is verified
    verdict: str                       # HIBERNATED | REFUSED
    reason: str
    archive_id: str | None = None
    hot_slot_freed: bool = False       # True only when it is safe to free


@dataclass
class RestoreResult:
    verdict: str                       # RECOVERED | PARTIAL | FAILED
    reason: str
    state: dict | None = None
    missing: list = field(default_factory=list)


def _enc(cwd: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")


def _pack(state: dict) -> tuple:
    """Compress + integrity-anchor the frozen state. (b64-zlib blob, hash)."""
    raw = json.dumps(state, sort_keys=True, ensure_ascii=False).encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()[:16]
    blob = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
    return blob, h


def _unpack(blob: str, expected_hash: str):
    """Decompress + verify integrity. None on corruption (never serve wrong)."""
    try:
        raw = zlib.decompress(base64.b64decode(blob))
    except (zlib.error, ValueError, TypeError):
        return None
    if hashlib.sha256(raw).hexdigest()[:16] != expected_hash:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _default_anchor_exists(sid, cwd, transcript_path, proj_base=None) -> bool:
    """The resume anchor: a transcript .jsonl on disk (SCS C28 anchor)."""
    if transcript_path and Path(transcript_path).is_file():
        return True
    if sid and cwd:
        base = Path(proj_base) if proj_base else (
            Path.home() / ".claude" / "projects")
        return (base / _enc(cwd) / f"{sid}.jsonl").is_file()
    return False


def _append(path, rec) -> bool:
    try:
        p = Path(path) if path else DEFAULT_ARCHIVE
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def _find_archive(archive_id, path):
    p = Path(path) if path else DEFAULT_ARCHIVE
    if not p.is_file():
        return None
    found = None
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("archive_id") == archive_id:
                found = rec               # last write wins
    except OSError:
        return None
    return found


def hibernate(sid: str, cwd: str, *, task: str = "", transcript_path=None,
              now: datetime | None = None, registry_path=None,
              anchor_exists_fn=None, proj_base=None) -> HibernationResult:
    """Freeze + compress + store + VERIFY, then signal the hot slot may be freed.
    Refuses (session stays hot) if the resume anchor is missing or store fails."""
    now = now or datetime.now(timezone.utc)
    anchor_ok = (anchor_exists_fn or _default_anchor_exists)(
        sid, cwd, transcript_path, proj_base)
    if not anchor_ok:
        return HibernationResult(
            False, "REFUSED",
            "resume anchor (transcript) missing -- session stays HOT (fail-open)")

    state = {"sid": sid, "cwd": cwd, "task": task,
             "transcript_path": str(transcript_path) if transcript_path else None,
             "ts": now.isoformat()}
    blob, h = _pack(state)
    archive_id = f"{sid}@{now.isoformat()}"
    rec = {"archive_id": archive_id, "sid": sid, "cwd": cwd, "ts": now.isoformat(),
           "blob": blob, "anchor_hash": h, "hibernated": True}

    if not _append(registry_path, rec):
        return HibernationResult(False, "REFUSED",
                                 "store failed -- session stays HOT")
    # VERIFY store before declaring it safe to free the slot (store-then-destroy).
    back = _find_archive(archive_id, registry_path)
    if not back or _unpack(back.get("blob", ""), back.get("anchor_hash", "")) is None:
        return HibernationResult(False, "REFUSED",
                                 "store verify failed -- session stays HOT")
    return HibernationResult(True, "HIBERNATED",
                             "stored + verified -- hot slot may be freed",
                             archive_id, True)


def restore(archive_id: str, *, registry_path=None, anchor_exists_fn=None,
            proj_base=None) -> RestoreResult:
    """Decompress + integrity-check + re-verify the anchor -> a G4-style verdict."""
    rec = _find_archive(archive_id, registry_path)
    if not rec:
        return RestoreResult("FAILED", "archive not found", None, ["archive"])
    state = _unpack(rec.get("blob", ""), rec.get("anchor_hash", ""))
    if state is None:
        return RestoreResult("FAILED",
                             "archive integrity check failed (corrupt) -- "
                             "never restored silently wrong", None, ["integrity"])
    anchor_ok = (anchor_exists_fn or _default_anchor_exists)(
        state.get("sid"), state.get("cwd"), state.get("transcript_path"), proj_base)
    if not anchor_ok:
        return RestoreResult("FAILED", "resume anchor (transcript) gone",
                             state, ["transcript"])
    missing = []
    if state.get("cwd") and not Path(state["cwd"]).exists():
        missing.append("cwd")
    if missing:
        return RestoreResult("PARTIAL", f"restored with missing: {missing}",
                             state, missing)
    return RestoreResult("RECOVERED", "anchor intact + integrity verified", state, [])


def un_gated_duplicate(live_sids, hibernated_sids):
    """Dedup helper: live sessions that are NOT hibernated (candidates to keep
    hot or fold). Hibernated sessions never count toward the CO-08 cap."""
    h = set(hibernated_sids or ())
    return [s for s in (live_sids or ()) if s not in h]


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--registry", default=None)
    args = ap.parse_args(argv)
    p = Path(args.registry) if args.registry else DEFAULT_ARCHIVE
    if args.list and p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    print(f"{r.get('archive_id')}  sid={r.get('sid')}")
                except json.JSONDecodeError:
                    pass
    else:
        print("# no hibernation archive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
