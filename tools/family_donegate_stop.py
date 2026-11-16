#!/usr/bin/env python3
"""Stop hook: run the family done-gate on the session's repo and BLOCK a turn that left a VIOLATED baseline entry.

Until 2026-11-16 the family block told the builder "run /family-done-gate before calling it done" and nothing ran it
(LAPTOP_STEPS 3, campaign 1): enforcement depended on the model remembering. This closes that gap with the owner's
own judge (modules.tower.donegate), on the event where "done" is claimed: the end of the turn.

Policy (Owner "go ahead, corrige todo", 2026-11-16 -- the blocking decision spec §7 kept for the Owner):
  * acts only in a session that RECEIVED a family block (a `kind: family` row for this session id in
    ~/.claude/state/tower/consumption.jsonl): a session that never built a family member is never judged;
  * judges every family that session was shown, against the payload's cwd;
  * blocks ONLY on VIOLATED (an evaluable check that failed). UNJUDGED prose rules never block -- a gate that blocks
    on what it cannot judge blocks every turn, and a gate that blocks every turn gets switched off;
  * `NO APLICA: <entry-id>: <reason>` lines in the turn's last assistant message are honoured (a reason is required);
  * blocks at most once per (session, family, violated set) and never when `stop_hook_active` is set: one block,
    one chance to fix, no loop;
  * every judgement is a row in ~/.claude/state/tower/donegate_stop.jsonl -- the evidence that it ran, block or not.
Fail-open: any error prints nothing and exits 0 (a Stop hook must never cost the user their turn), but the error is
ledgered. Kill switch: CPP_FAMILY_DONEGATE=off.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

TAIL_BYTES = 2_000_000
NA_RX = re.compile(r"NO APLICA:\s*`?\[?([a-z0-9_]+-[a-z0-9-]+)\]?`?\s*[:\-]\s*(\S.{2,})", re.I)


def _state_dir() -> Path:
    d = Path(os.environ.get("CPP_TOWER_STATE_DIR") or (Path.home() / ".claude" / "state" / "tower"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _tail_lines(path: Path, limit: int = TAIL_BYTES) -> list:
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - limit))
            data = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    lines = data.splitlines()
    return lines[1:] if size > limit else lines      # the first line of a cut window is partial


def families_shown(sid: str) -> list:
    out = []
    for line in _tail_lines(_state_dir() / "consumption.jsonl"):
        if sid not in line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("kind") == "family" and row.get("sid") == sid and row.get("family") not in out:
            out.append(row["family"])
    return out


def last_assistant_text(transcript: str) -> str:
    if not transcript or not os.path.isfile(transcript):
        return ""
    for line in reversed(_tail_lines(Path(transcript), 600_000)):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        msg = row.get("message") if isinstance(row, dict) else None
        if row.get("type") != "assistant" or not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        texts = [c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text"]
        if texts:
            return "\n".join(texts)
    return ""


def not_applicable(text: str) -> dict:
    return {m.group(1): m.group(2).strip() for m in NA_RX.finditer(text or "")}


def _ledger(row: dict) -> None:
    try:
        with open(_state_dir() / "donegate_stop.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(row, ts=time.time()), ensure_ascii=False) + "\n")
    except OSError:
        pass


def decide(payload: dict) -> dict | None:
    """The hook's whole decision, pure enough to test: returns the Stop output dict, or None for silence."""
    from modules.tower import donegate as dg
    sid = str(payload.get("session_id") or payload.get("sessionId") or "")
    cwd = str(payload.get("cwd") or "")
    if not sid or not cwd or not os.path.isdir(cwd):
        return None
    fams = families_shown(sid)
    if not fams:
        return None
    # A family is attached by classifying the PROMPT, so the session may be standing in a repo that is no member of
    # it; judging there blocks on entries that cannot apply (review of bb4db9f4, M2). Skip only a repo PROVEN out:
    # UNJUDGED (no marker route, cut walk, failed delegate) is not OUT, and is still judged.
    from modules.tower import families as fm
    membership = fm.repo_family_report(cwd, [f for f in fm.load_families() if f.id in fams])
    member = set(membership["in"]) | set(membership["unjudged"])
    na = not_applicable(last_assistant_text(str(payload.get("transcript_path") or "")))
    problems = []
    for fam in fams:
        if fam not in member:
            _ledger({"sid": sid, "family": fam, "repo": cwd, "decision": "skipped",
                     "why": "repo proven outside the family (no repo marker)"})
            continue
        rep = dg.judge(fam, cwd, not_applicable=na)
        violated = [x for x in rep.get("entries", []) if x["verdict"] == dg.VIOLATED]
        _ledger({"sid": sid, "family": fam, "repo": cwd, "judged_under": rep.get("judged_under"),
                 "violated": [x["entry_id"] for x in violated], "na": sorted(na),
                 "verdicts": {x["entry_id"]: x["verdict"] for x in rep.get("entries", [])}})
        if violated:
            problems.append((fam, rep.get("judged_under"), violated))
    if not problems:
        return None
    key = hashlib.sha256(json.dumps([[f, sorted(x["entry_id"] for x in v)] for f, _, v in problems]).encode()
                         ).hexdigest()[:16]
    seen = _state_dir() / ("donegate-stop-%s.seen" % re.sub(r"[^A-Za-z0-9_-]", "_", sid)[:80])
    already = seen.read_text().split() if seen.exists() else []
    if payload.get("stop_hook_active") or key in already:
        _ledger({"sid": sid, "decision": "not_blocked", "why": "already blocked once for this set" if key in already
                 else "stop_hook_active", "key": key})
        return None
    seen.write_text(" ".join(already + [key]))
    lines = ["Family done-gate: this turn leaves baseline entries VIOLATED in %s. Fix them, or write "
             "`NO APLICA: <entry-id>: <reason>` for an entry that does not apply, before calling it done." % cwd]
    for fam, stamp, violated in problems:
        for x in violated:
            lines.append("- [%s/%s] %s -- %s" % (stamp, x["entry_id"], x.get("requirement") or "", x.get("detail") or ""))
    _ledger({"sid": sid, "decision": "block", "key": key})
    return {"decision": "block", "reason": "\n".join(lines)}


def main() -> int:
    if os.environ.get("CPP_FAMILY_DONEGATE", "").strip().lower() in ("off", "0", "false"):
        return 0
    try:
        raw = sys.stdin.read().lstrip("﻿")
        payload = json.loads(raw) if raw.strip() else {}
        out = decide(payload if isinstance(payload, dict) else {})
        if out:
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 -- fail-open, but never silently
        _ledger({"decision": "error", "error": "%s: %s" % (type(exc).__name__, exc)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
