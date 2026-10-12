"""CCR v4 D1: how much of a corpus's processed tokens is model-facing re-reads of UNCHANGED content.

For every Read tool call: (session, path, range) and a hash of the content the model received. A read is a
re-read when the same (path, range, content hash) was already delivered earlier in the SAME session (the content is
unchanged, so the second copy bought nothing new) or in an earlier session of the corpus (cross-session; a receipt
could have answered it). The rent of a delivered copy is its tokens times the calls it then rode in its session.

    python tools/ccr_reread_audit.py <dir-with-session-jsonl> [--limit N] [--json]

Share = re-read rent / processed tokens (input + cache read + cache write over all calls). The CE F rule makes
One-Read GO only at >= 3 %. Tokens per char come from the B3 fit (0.50 on tool results).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

TOK_PER_CHAR = 0.50  # tool_result rate fitted in tools/ccr_carry_fit.py over Madzia a3-a8
GO_SHARE = 0.03      # CE F rule


def _content_text(c) -> str:
    if isinstance(c, str):
        return c
    return "".join(x.get("text", "") for x in c or [] if isinstance(x, dict) and x.get("type") == "text")


def audit_session(path: Path) -> dict:
    calls: list[int] = []
    seen_ids: set[str] = set()
    reads: dict[str, tuple] = {}
    delivered: list[tuple[int, tuple, int]] = []  # (call index when delivered, key, chars)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"assistant"' not in line and '"tool_result"' not in line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue  # torn line: nothing to count
            msg = ev.get("message") or {}
            if ev.get("type") == "assistant":
                mid = msg.get("id")
                if mid and mid not in seen_ids:
                    seen_ids.add(mid)
                    u = msg.get("usage") or {}
                    calls.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Read":
                        i = b.get("input") or {}
                        reads[b.get("id")] = (str(i.get("file_path", "")).lower().replace("\\", "/"), i.get("offset"), i.get("limit"))
            elif ev.get("type") == "user":
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in reads and not b.get("is_error"):
                        text = _content_text(b.get("content"))
                        h = hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:16]
                        delivered.append((len(calls), reads[b.get("tool_use_id")] + (h,), len(text)))
    return {"calls": calls, "delivered": delivered}


def audit(root: Path, limit: int | None) -> dict:
    files = sorted(root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if limit:
        files = files[-limit:]
    processed = 0
    reads = 0
    read_rent = 0.0
    same = {"n": 0, "rent": 0.0}
    cross = {"n": 0, "rent": 0.0}
    corpus_seen: set[tuple] = set()
    for f in files:
        s = audit_session(f)
        n = len(s["calls"])
        processed += sum(s["calls"])
        session_seen: set[tuple] = set()
        for at, key, chars in s["delivered"]:
            rides = max(0, n - at)
            rent = chars * TOK_PER_CHAR * rides
            reads += 1
            read_rent += rent
            if key in session_seen:
                same["n"] += 1
                same["rent"] += rent
            elif key in corpus_seen:
                cross["n"] += 1
                cross["rent"] += rent
            session_seen.add(key)
        corpus_seen |= session_seen
    share_same = same["rent"] / processed if processed else None
    share_cross = cross["rent"] / processed if processed else None
    return {"sessions": len(files), "processed": processed, "reads": reads, "read_rent": round(read_rent),
            "read_rent_share": round(read_rent / processed, 4) if processed else None,
            "same_session_rereads": same["n"], "same_session_rent": round(same["rent"]), "same_session_share": share_same and round(share_same, 4),
            "cross_session_rereads": cross["n"], "cross_session_rent": round(cross["rent"]), "cross_session_share": share_cross and round(share_cross, 4),
            "verdict_same": None if share_same is None else ("GO" if share_same >= GO_SHARE else "NO_GO"),
            "note": "cross-session re-reads ride a different context; they are avoidable only by a receipt the new session consults"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = audit(Path(a.root), a.limit)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
