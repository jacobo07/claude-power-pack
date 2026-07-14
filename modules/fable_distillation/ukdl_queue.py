#!/usr/bin/env python3
"""ukdl_queue.py -- close the write-only candidate queue (T-UKDL-CANDIDATES-WRITE-ONLY-001).

The candidates ledger already carries a `status` field. That was never the defect.
The defect is that the field is a CONSTANT the producer stamps at write time
("candidate -- Owner promotes to ukdl-universal.md") and which no producer anywhere
can ever change. A field nobody can transition is not state -- it is decoration, and
a queue whose state cannot move is a write-only queue no matter how many status
fields it has.

Proof it was lying: on 2026-07-14 all three candidates had been promoted into
ukdl-universal.md, and all three rows still read "candidate".

This module is the missing transition producer. Following the ledger discipline the
repo already uses (fd04 proofs are a SIBLING of deposits, never a rewrite), a
transition is APPENDED to `ukdl_transitions_<repo>.jsonl` and the effective status is
DERIVED as the latest transition per fingerprint -- pending when there is none. Rows
are never mutated, so the queue's history stays auditable.

Promotion is fail-CLOSED on the one lie that matters: a promotion naming a rule that
does not exist in the target archive is REFUSED. A pointer to a rule nobody wrote is
the orphan-field trap wearing a promotion's clothes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_07_flywheel import (  # noqa: E402
    _append_jsonl, _state_dir)

STATUSES = ("pending", "under_review", "promoted", "rejected")
_TERMINAL = ("promoted", "rejected")
_ARCHIVE = _PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
_RULE_ID_RE = re.compile(r"^(HR|PR|T)-[A-Z0-9-]+$")
_CLAIM_SNIP = 160   # chars of a claim kept in a listing row (the queue is a queue,
                    # not a reader -- the full claim stays in the candidates ledger)


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _enc(repo: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", repo or "")


def _candidates_path(repo: str, state_dir=None) -> Path:
    return _state_dir(state_dir) / f"ukdl_candidates_{_enc(repo)}.jsonl"


def _transitions_path(repo: str, state_dir=None) -> Path:
    return _state_dir(state_dir) / f"ukdl_transitions_{_enc(repo)}.jsonl"


def _read_jsonl(path: Path) -> list:
    if not path.is_file():
        return []
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
    except OSError:
        return []
    return out


def _latest_by_fp(records: list) -> dict:
    out: dict = {}
    for r in records:
        fp = r.get("fingerprint")
        if fp:
            out[fp] = r
    return out


# --------------------------------------------------------------------------- #
# Derived state -- the producer's constant string is normalised to `pending`.
# --------------------------------------------------------------------------- #
def status_of(repo: str, fingerprint: str, state_dir=None) -> dict:
    t = _latest_by_fp(_read_jsonl(_transitions_path(repo, state_dir))).get(fingerprint)
    if not t:
        return {"fingerprint": fingerprint, "status": "pending",
                "promoted_to": "", "reviewed_at": "", "reviewed_by": ""}
    return {"fingerprint": fingerprint, "status": t.get("status", "pending"),
            "promoted_to": t.get("promoted_to", ""),
            "reviewed_at": t.get("reviewed_at", ""),
            "reviewed_by": t.get("reviewed_by", ""),
            "note": t.get("note", "")}


def candidates(repo: str, state_dir=None) -> list:
    """Every candidate with its DERIVED status. Fail-open on read."""
    out = []
    for c in _read_jsonl(_candidates_path(repo, state_dir)):
        fp = c.get("fingerprint")
        if not fp:
            continue
        st = status_of(repo, fp, state_dir)
        out.append({**{k: c.get(k) for k in ("fingerprint", "kind", "portability",
                                             "sid", "ts")},
                    "claim": (c.get("claim") or "")[:_CLAIM_SNIP],
                    **{k: st[k] for k in ("status", "promoted_to", "reviewed_at",
                                          "reviewed_by")}})
    return out


def pending(repo: str, state_dir=None) -> list:
    """Candidates awaiting an Owner decision -- the surfacing the queue never had."""
    return [c for c in candidates(repo, state_dir)
            if c["status"] not in _TERMINAL]


# --------------------------------------------------------------------------- #
# Transitions -- the producers the field never had.
# --------------------------------------------------------------------------- #
def _rule_exists(rule_id: str, archive: Path | None = None) -> bool:
    p = archive or _ARCHIVE
    try:
        return bool(re.search(rf"(?m)^#+\s*{re.escape(rule_id)}\b",
                              p.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        return False


def _is_candidate(repo: str, fingerprint: str, state_dir) -> bool:
    return any(c.get("fingerprint") == fingerprint
               for c in _read_jsonl(_candidates_path(repo, state_dir)))


def _transition(repo: str, fingerprint: str, status: str, *, promoted_to: str = "",
                reviewed_by: str = "owner", note: str = "", state_dir=None,
                now: datetime | None = None, archive: Path | None = None) -> dict:
    try:
        if status not in STATUSES:
            return {"ok": False, "note": f"status must be one of {STATUSES}"}
        if not _is_candidate(repo, fingerprint, state_dir):
            return {"ok": False,
                    "note": "not in the candidates ledger -- a transition only "
                            "moves a candidate that exists"}
        if status == "promoted":
            if not _RULE_ID_RE.match(promoted_to or ""):
                return {"ok": False,
                        "note": "promotion requires promoted_to = a rule id "
                                "(HR-* / PR-* / T-*)"}
            if not _rule_exists(promoted_to, archive):
                return {"ok": False,
                        "note": f"{promoted_to} is not a heading in the archive -- "
                                "refusing to promote to a rule nobody wrote"}
        rec = {"fingerprint": fingerprint, "status": status,
               "promoted_to": promoted_to if status == "promoted" else "",
               "reviewed_at": _now(now).isoformat(), "reviewed_by": reviewed_by,
               "note": note}
        _append_jsonl(_transitions_path(repo, state_dir), rec)
        return {"ok": True, **rec}
    except Exception as e:  # noqa: BLE001 -- fail-closed: an error never transitions
        return {"ok": False, "note": f"{type(e).__name__}: {e}"}


def promote(repo: str, fingerprint: str, rule_id: str, *, reviewed_by: str = "owner",
            note: str = "", state_dir=None, now=None, archive=None) -> dict:
    return _transition(repo, fingerprint, "promoted", promoted_to=rule_id,
                       reviewed_by=reviewed_by, note=note, state_dir=state_dir,
                       now=now, archive=archive)


def reject(repo: str, fingerprint: str, *, reason: str, reviewed_by: str = "owner",
           state_dir=None, now=None) -> dict:
    if not (reason or "").strip():
        return {"ok": False, "note": "a rejection without a reason is a deletion"}
    return _transition(repo, fingerprint, "rejected", reviewed_by=reviewed_by,
                       note=reason.strip(), state_dir=state_dir, now=now)


def under_review(repo: str, fingerprint: str, *, reviewed_by: str = "owner",
                 note: str = "", state_dir=None, now=None) -> dict:
    return _transition(repo, fingerprint, "under_review", reviewed_by=reviewed_by,
                       note=note, state_dir=state_dir, now=now)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="UKDL candidate queue -- status + promotion")
    ap.add_argument("--repo", default=str(_PP_ROOT))
    ap.add_argument("--state-dir", default=None)
    ap.add_argument("--list", action="store_true", help="every candidate + derived status")
    ap.add_argument("--pending", action="store_true", help="candidates awaiting a decision")
    ap.add_argument("--promote", metavar="FINGERPRINT")
    ap.add_argument("--rule-id", default="")
    ap.add_argument("--reject", metavar="FINGERPRINT")
    ap.add_argument("--reason", default="")
    ap.add_argument("--under-review", metavar="FINGERPRINT")
    ap.add_argument("--by", default="owner")
    ap.add_argument("--note", default="")
    args = ap.parse_args(argv)

    if args.promote:
        r = promote(args.repo, args.promote, args.rule_id, reviewed_by=args.by,
                    note=args.note, state_dir=args.state_dir)
    elif args.reject:
        r = reject(args.repo, args.reject, reason=args.reason, reviewed_by=args.by,
                   state_dir=args.state_dir)
    elif args.under_review:
        r = under_review(args.repo, args.under_review, reviewed_by=args.by,
                         note=args.note, state_dir=args.state_dir)
    elif args.pending:
        r = pending(args.repo, args.state_dir)
    elif args.list:
        r = candidates(args.repo, args.state_dir)
    else:
        ap.print_help()
        return 0
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if not isinstance(r, dict) or r.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
