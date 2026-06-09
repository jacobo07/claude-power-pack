#!/usr/bin/env python3
"""ADS doc updater (D3).

Refreshes ONLY the AUTO block of an existing doc, preserving the OWNER
block byte-for-byte. The Changelog is append-only: a new dated entry is
prepended to its AUTO block rather than overwriting history.

Splice safety (audit gap #7): a splice happens ONLY when the file has
EXACTLY ONE balanced AUTO marker pair (open before close, one of each).
On zero / multiple / unbalanced markers the file is left UNTOUCHED and a
diagnostic reason is returned -- never a best-effort overwrite that could
eat the OWNER block.

stdlib-only. Public API: update_docs, splice_block, extract_block.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.ads.detector import ModuleChange, module_slug
from modules.ads.doc_generator import (
    AUTO_CLOSE,
    AUTO_OPEN,
    DOC_TYPES,
    build_docs,
    write_docs,
)


def extract_block(text: str, open_m: str, close_m: str) -> tuple[str | None, str]:
    """Return (inner, reason). inner is None when not exactly-one-balanced."""
    n_open = text.count(open_m)
    n_close = text.count(close_m)
    if n_open == 0 and n_close == 0:
        return None, "no markers"
    if n_open != 1 or n_close != 1:
        return None, f"unbalanced markers (open={n_open}, close={n_close})"
    i = text.index(open_m) + len(open_m)
    j = text.index(close_m)
    if j < i:
        return None, "close marker precedes open marker"
    return text[i:j], "ok"


def splice_block(text: str, open_m: str, close_m: str,
                 new_inner: str) -> tuple[str | None, str]:
    """Replace the content between markers. Returns (new_text|None, reason)."""
    inner, reason = extract_block(text, open_m, close_m)
    if inner is None:
        return None, reason
    i = text.index(open_m) + len(open_m)
    j = text.index(close_m)
    return text[:i] + new_inner + text[j:], "ok"


def _changelog_entry(change: ModuleChange, ts: str) -> str:
    line = (f"- {ts} — {change.change_type.value.lower()} "
            f"(+{change.added}/-{change.deleted}, {change.pct}%)")
    if change.rename_from:
        line += f" — renamed from `{change.rename_from}`"
    return line


def update_docs(key: str, repo: str | Path, change: ModuleChange,
                now: str, is_package: bool | None = None) -> dict[str, str]:
    """Update the four docs for `key`. Returns {doc_type: status}.

    status in {created, updated, skipped:<reason>}. A doc that does not yet
    exist is freshly generated (created); an existing one has only its AUTO
    block refreshed (updated) unless its markers are malformed (skipped).
    """
    repo = Path(repo).resolve()
    slug = module_slug(key)
    status: dict[str, str] = {}

    # Any doc missing -> regenerate the whole set fresh, then continue so the
    # AUTO refresh / changelog append still run against the freshly written
    # files (idempotent).
    missing = [d for d in DOC_TYPES
               if not (repo / "docs" / d / f"{slug}.md").exists()]
    if missing:
        write_docs(key, repo, now, is_package)
        for d in missing:
            status[d] = "created"

    fresh = build_docs(key, repo, now, is_package)

    for doc_type in DOC_TYPES:
        path = repo / "docs" / doc_type / f"{slug}.md"
        existing = path.read_text(encoding="utf-8", errors="replace")

        if doc_type == "changelog":
            cur_inner, reason = extract_block(existing, AUTO_OPEN, AUTO_CLOSE)
            if cur_inner is None:
                status.setdefault(doc_type, f"skipped:{reason}")
                continue
            entry = _changelog_entry(change, now)
            # Prepend the new entry directly under the auto-note line.
            lines = cur_inner.splitlines()
            insert_at = next((idx + 1 for idx, ln in enumerate(lines)
                              if ln.strip() == ""), len(lines))
            lines.insert(insert_at, entry)
            new_text, reason = splice_block(
                existing, AUTO_OPEN, AUTO_CLOSE, "\n".join(lines))
            if new_text is None:
                status.setdefault(doc_type, f"skipped:{reason}")
                continue
            path.write_text(new_text, encoding="utf-8")
            status.setdefault(doc_type, "updated")
            continue

        # Non-changelog: replace AUTO inner with the freshly-built AUTO inner.
        new_inner, _ = extract_block(fresh[doc_type], AUTO_OPEN, AUTO_CLOSE)
        if new_inner is None:
            status.setdefault(doc_type, "skipped:fresh-build-malformed")
            continue
        new_text, reason = splice_block(
            existing, AUTO_OPEN, AUTO_CLOSE, new_inner)
        if new_text is None:
            status.setdefault(doc_type, f"skipped:{reason}")
            continue
        path.write_text(new_text, encoding="utf-8")
        status.setdefault(doc_type, "updated")

    return status


__all__ = ["update_docs", "splice_block", "extract_block"]
