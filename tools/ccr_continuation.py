"""CCR M1: tiny continuation capsule + resume-rent meter (stdlib).

Extends the mission-card idea (tools/gsd_mission.py card, tools/mission_capsule.py):
same intent (bounded rehydration text), no second persistent format -- this emits
plain text built only from certified state + next obligation.
Over-budget items become refs (path + sha256), never truncated mid-item.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import os
import shutil
import subprocess
import sys
from pathlib import Path

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"

BUDGET_TOKENS = 8000          # E1 receipt names no budget -> default
TOK_PER_CHAR = 0.585          # B5 calibration
MAX_DIRTY = 40
NOTE_ITEM_CHARS = 1500        # predecessor note beyond this becomes a ref
FACT_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(status|verdicts?)(?:\*\*)?\s*:", re.I)


def budget_chars(tokens: int = BUDGET_TOKENS) -> int:
    return int(tokens / TOK_PER_CHAR)


def est_tokens(nchars: int) -> int:
    return int(round(nchars * TOK_PER_CHAR))


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _git(repo, *args) -> str:
    try:
        r = subprocess.run([GIT, "-C", str(repo), *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def head_sha(repo) -> str:
    return _git(repo, "rev-parse", "HEAD").strip() or "unknown"


def dirty_paths(repo) -> tuple[list[str], int]:
    names = []
    for ln in _git(repo, "status", "--porcelain").splitlines():
        if len(ln) > 3:
            names.append(ln[3:].strip().strip('"'))
    return names[:MAX_DIRTY], max(0, len(names) - MAX_DIRTY)


def receipt_facts(path) -> list[str]:
    out = []
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if FACT_RE.match(ln):
            out.append(ln.strip())
    return out


def _text_of(msg) -> str:
    c = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def last_assistant_text(transcript) -> str:
    """Last assistant text block; streams the file, keeps O(1) state."""
    last = ""
    with open(transcript, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if '"assistant"' not in ln:
                continue
            try:
                o = json.loads(ln)
            except ValueError:
                continue
            if o.get("type") == "assistant":
                t = _text_of(o.get("message")).strip()
                if t:
                    last = t
            elif o.get("role") == "assistant":
                t = _text_of(o).strip()
                if t:
                    last = t
    return last


def last_call_ctx(transcript) -> int:
    """Input-side tokens of the final assistant call (input + cache read + cache create)."""
    ctx = 0
    with open(transcript, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if '"usage"' not in ln or '"assistant"' not in ln:
                continue
            try:
                o = json.loads(ln)
            except ValueError:
                continue
            u = (o.get("message") or {}).get("usage") if o.get("type") == "assistant" else None
            if isinstance(u, dict):
                ctx = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                       + u.get("cache_creation_input_tokens", 0))
    return ctx


def _ref(label: str, path) -> str:
    return f"REF {label}: {Path(path).as_posix()} sha256={sha256_file(path)}"


def build(repo, obligation: str, receipts=(), transcript=None, budget_tokens: int = BUDGET_TOKENS) -> str:
    cap = budget_chars(budget_tokens)
    head = [f"# CCR continuation capsule",
            f"HEAD: {head_sha(repo)}",
            f"NEXT OBLIGATION: {obligation}"]
    dirty, more = dirty_paths(repo)
    dl = "DIRTY (names only): " + (", ".join(dirty) if dirty else "none")
    if more:
        dl += f" (+{more} more)"
    head.append(dl)
    lines = list(head)
    used = sum(len(x) + 1 for x in lines)

    def add(item: str, ref_item: str) -> None:
        nonlocal used
        for cand in (item, ref_item):
            if used + len(cand) + 1 <= cap:
                lines.append(cand)
                used += len(cand) + 1
                return
        # nothing fits: drop silently-but-visibly is forbidden; fail loud
        raise ValueError("capsule budget cannot hold even a ref; raise budget")

    lines.append("CERTIFIED FACTS (receipt Status/verdict rows):")
    used += len(lines[-1]) + 1
    for r in receipts:
        facts = receipt_facts(r)
        ref = _ref("receipt", r)
        if facts:
            # whole receipt's facts or its ref -- atomic per receipt; the header fingerprints the source (One-Read)
            blk = "\n".join([f"[{Path(r).name}] path={Path(r).as_posix()} sha256={sha256_file(r)}"] + facts)
            if used + len(blk) + 1 + 600 <= cap:   # keep 600 chars slack for note/refs
                lines.append(blk)
                used += len(blk) + 1
                continue
        lines.append(ref)
        used += len(ref) + 1
    if transcript:
        note = last_assistant_text(transcript)
        if note and len(note) <= NOTE_ITEM_CHARS:
            add("PREDECESSOR NOTE (CLAIM, unverified): " + note,
                _ref("predecessor note (CLAIM)", transcript))
        else:
            add(_ref("predecessor note (CLAIM, too long to inline)", transcript),
                _ref("predecessor", transcript))
    out = "\n".join(lines) + "\n"
    if len(out) > cap:
        raise ValueError(f"capsule {len(out)} chars exceeds budget {cap}")
    return out


# One-Read (A4): every certified fact and every ref in a capsule names its source by path and sha256. A
# successor reuses the fact without re-reading the source while the source still hashes the same; once the
# source changes, the fact is invalid and a raw read of the source is the valid way back.
FP_RE = re.compile(r"(?:^\[[^\]]+\] path=|^REF [^:]+: )(?P<path>\S+) sha256=(?P<sha>[0-9a-f]{64})\s*$", re.M)


def fingerprints(text: str) -> dict[str, str]:
    """{source path: sha256} for every fingerprinted fact block and ref in a capsule."""
    return {m["path"]: m["sha"] for m in FP_RE.finditer(text)}


def reuse(text: str, path) -> dict:
    """May the capsule's fact about `path` be used without re-reading `path`?"""
    want = fingerprints(text).get(Path(path).as_posix())
    if want is None:
        return {"reuse": False, "reason": "not-in-capsule"}
    try:
        now = sha256_file(path)
    except OSError:
        return {"reuse": False, "reason": "source-missing"}
    return {"reuse": now == want, "reason": "fingerprint-match" if now == want else "source-changed: raw read required",
            "sha256": now}


def rent(text: str) -> dict:
    b = len(text.encode("utf-8"))
    return {"bytes": b, "chars": len(text), "est_tokens": est_tokens(len(text))}


def check_budget(text: str, budget_tokens: int = BUDGET_TOKENS) -> bool:
    return len(text) <= budget_chars(budget_tokens)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ccr_continuation")
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("--repo", required=True)
    b.add_argument("--obligation", required=True)
    b.add_argument("--receipt", action="append", default=[])
    b.add_argument("--transcript")
    b.add_argument("--budget-tokens", type=int, default=BUDGET_TOKENS)
    r = sp.add_parser("rent")
    r.add_argument("--capsule", required=True)
    r.add_argument("--budget-tokens", type=int, default=BUDGET_TOKENS)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(build(a.repo, a.obligation, a.receipt, a.transcript, a.budget_tokens))
        return 0
    txt = Path(a.capsule).read_text(encoding="utf-8")
    d = rent(txt)
    d["within_budget"] = check_budget(txt, a.budget_tokens)
    print(json.dumps(d))
    return 0 if d["within_budget"] else 1


if __name__ == "__main__":
    sys.exit(main())
