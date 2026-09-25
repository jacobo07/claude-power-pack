"""Constitutive baseline generations per system family.

Spec: docs/superpowers/specs/2026-09-24-family-baselines-design.md §3.2-§3.4.

A generation is `vault/tower/baselines/<family>/B<n>.json`, IMMUTABLE once
written: a promotion writes B<n+1>, a revert writes B<n+2>. Nothing is edited
in place, so "what did the baseline say when this mission ran" always has an
answer -- the same reason the Tower supersedes instead of overwriting.

Every entry carries an origin (file + line). `verify_origin` re-reads that line:
an entry whose citation does not exist is not evidence of anything, and B0 is
built only from entries that verify.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
BASELINES_DIR = os.path.join(_PP_ROOT, "vault", "tower", "baselines")

VERIFIED = "VERIFIED"            # file exists, line exists, shares vocabulary
WEAK = "WEAK"                    # line exists, but little shared vocabulary
LINE_MISSING = "LINE_MISSING"    # file shorter than the cited line
FILE_MISSING = "FILE_MISSING"
MALFORMED = "MALFORMED"          # entry lacks the fields a citation needs

REQUIRED = ("id", "requirement", "why", "origin", "class")
_GEN = re.compile(r"^B(\d+)\.json$")
_STOP = {"that", "this", "with", "from", "must", "every", "have", "before",
         "never", "when", "into", "than", "then", "they", "their", "what", "which"}


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{4,}", (s or "").lower()) if w not in _STOP}


MOVED = "MOVED"                  # quoted text exists, at another line
QUOTE_MISSING = "QUOTE_MISSING"  # quoted text no longer in the file


def _squash(s: str) -> str:
    return " ".join(str(s or "").split())


def locate_quote(path: str, quote: str) -> int:
    """1-indexed line holding `quote` (whitespace-insensitive), or 0."""
    q = _squash(quote)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for n, text in enumerate(fh.read().splitlines(), 1):
            if q and q in _squash(text):
                return n
    return 0


def verify_origin(entry: dict, window: int = 3) -> str:
    """Re-read the cited line.

    WITH `origin.quote` the answer is exact: the quote on the cited line is
    VERIFIED, elsewhere in the file MOVED, nowhere QUOTE_MISSING.

    WITHOUT a quote (a candidate not yet anchored) it falls back to shared
    vocabulary within `window` lines -- and that fallback is weak by
    construction: measured 2026-09-24, CLAUDE.md gained a section above a cited
    line and an entry about motion FLOORS passed as VERIFIED against a line about
    DECLARING, because the window found shared words. So B0 stores the quote,
    and the fallback is only ever used to admit a candidate, never to re-verify
    a stored entry.
    """
    try:
        if any(k not in entry for k in REQUIRED):
            return MALFORMED
        o = entry["origin"] or {}
        path, line = o.get("file"), int(o.get("line") or 0)
        if not path or line < 1:
            return MALFORMED
        if not os.path.isfile(path):
            return FILE_MISSING
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        if o.get("quote"):
            if line <= len(lines) and _squash(o["quote"]) in _squash(lines[line - 1]):
                return VERIFIED
            return MOVED if locate_quote(path, o["quote"]) else QUOTE_MISSING
        if line > len(lines):
            return LINE_MISSING
        ctx = " ".join(lines[max(0, line - 1 - window): line + window])
        shared = _tokens(entry["requirement"] + " " + entry["why"]) & _tokens(ctx)
        return VERIFIED if len(shared) >= 2 else WEAK
    except Exception:  # noqa: BLE001
        return MALFORMED


def _family_dir(family: str, root: str | None = None) -> str:
    return os.path.join(root or BASELINES_DIR, family)


def generations(family: str, root: str | None = None) -> list:
    d = _family_dir(family, root)
    if not os.path.isdir(d):
        return []
    return sorted(int(m.group(1)) for m in (_GEN.match(f) for f in os.listdir(d)) if m)


def load_generation(family: str, n: int, root: str | None = None) -> dict:
    with open(os.path.join(_family_dir(family, root), "B%d.json" % n), "r",
              encoding="utf-8") as fh:
        return json.load(fh)


def latest(family: str, root: str | None = None) -> dict | None:
    gens = generations(family, root)
    return load_generation(family, gens[-1], root) if gens else None


def active_entries(family: str, root: str | None = None) -> list:
    """Entries of the newest generation that are not reverted."""
    g = latest(family, root)
    if not g:
        return []
    return [e for e in g.get("entries", []) if e.get("status") != "reverted"]


def write_generation(family: str, entries: list, reason: str,
                     root: str | None = None) -> str:
    """Write B<n+1>. Refuses to overwrite: a generation is a record.

    Publication is create-if-absent in ONE step. The earlier shape checked that
    B<n> did not exist, wrote a shared `B<n>.json.tmp`, then `os.replace`d it:
    two writers that both passed the check both reported success and the later
    one silently replaced the earlier (measured 2026-09-25, positioned race,
    V-BGEN-RACE-ONE-WINNER). Each writer now owns a private temp file and
    publishes with a hard link, which the OS refuses when the target exists, so
    the loser gets FileExistsError and the winner's bytes are never touched.
    """
    d = _family_dir(family, root)
    os.makedirs(d, exist_ok=True)
    gens = generations(family, root)
    n = gens[-1] + 1 if gens else 0
    path = os.path.join(d, "B%d.json" % n)
    doc = {"family": family, "generation": n, "parent": gens[-1] if gens else None,
           "created_at": time.time(), "reason": reason, "entries": entries}
    fd, tmp = tempfile.mkstemp(prefix=".B%d." % n, suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        try:
            os.link(tmp, path)
        except FileExistsError:
            raise
        except OSError:
            # A filesystem without hard links: fall back to an exclusive create.
            # Still refuses an existing target; loses only atomicity of content.
            with open(tmp, "rb") as src, \
                    os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY), "wb") as dst:
                dst.write(src.read())
    finally:
        # Only "already gone" is benign; any other failure leaves residue that
        # V-BGEN-RACE-ONE-WINNER reports, so it must stay loud.
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
    return path
