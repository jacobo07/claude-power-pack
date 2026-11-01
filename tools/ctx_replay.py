"""Counterfactual replay (ctx-rent-x W6): X -> X-prime for the A7 main-lean lever over this host's transcripts.

X       = processed input actually billed (input + cache_read + cache_creation, per unique assistant message.id).
X-prime = X minus `delta` per INTERACTIVE top-level call, `delta` being the measured call-1 saving of the live
          CCR_MAIN_CANARY arm (laptop L5: 20,795 tokens), clamped to that call's own input. Subagent and worker
          sessions are not touched (the canary is interactive-only). Every figure here is an ESTIMATE (counterfactual);
          the live arms in main-canary-quality.json are the MEASURED ones. The two are never added together.
Only the floor lever is priced: Safe-to-Forget (Phase 5) is not built, so no content-removal saving is claimed.
Quality of a counterfactual is UNKNOWN by construction (nothing was re-run); it is reported as such.
Corpus class is a first-user-text / shape heuristic (APPROX), first match wins.
Usage: ctx_replay.py --since ISO --until ISO [--delta N] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctx_rent as cx  # noqa: E402

DELTA_L5 = 20795   # MEASURED laptop call-1 saving, enforce vs shadow (STATE D2)
LARGE_CTX = 400_000
CLASS_ORDER = ("mission_worker", "kresume_successor", "ksr_style", "debugging", "coherent_large_context", "long_repo", "sparse", "other")


def first_user_text(path: Path, limit: int = 4000) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            m = e.get("message")
            if e.get("type") == "user" and isinstance(m, dict):
                c = m.get("content")
                if isinstance(c, list):
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                if isinstance(c, str) and c.strip():
                    return c[:limit]
    return ""


def classify(text: str, calls: int, peak: int, is_worker: bool) -> str:
    if is_worker:
        return "mission_worker"
    if re.search(r"kresume", text, re.I):
        return "kresume_successor"
    if re.search(r"\b(KSR|KME)\b", text):
        return "ksr_style"
    if re.search(r"\b(debug|bug|error|traceback|fails?|failing|broken|regression)\b", text, re.I):
        return "debugging"
    if peak >= LARGE_CTX:
        return "coherent_large_context"
    if calls >= 150:
        return "long_repo"
    if calls <= 10:
        return "sparse"
    return "other"


def prime(inputs: list[int], delta: int) -> int:
    """X-prime for one interactive session: each call loses min(delta, its own input)."""
    return sum(i - min(delta, i) for i in inputs)


def replay(projects: Path, since: str, until: str, delta: int, worker_kind: dict[str, str], plane: str) -> dict:
    lo = time.mktime(time.strptime(since[:10], "%Y-%m-%d")) - 86400
    rows: dict[str, dict] = {}
    for p in projects.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < lo:
                continue
        except OSError:
            continue
        inputs = [ev[3] for ev in cx.events(p) if ev[0] == "call" and since <= ev[2] < until]
        if not inputs:
            continue
        sub, sid = "subagents" in p.parts, p.stem
        worker = sid in worker_kind
        if sub:
            cls, interactive = "subagent", False
        else:
            cls = classify(first_user_text(p), len(inputs), max(inputs), worker)
            interactive = not worker
        x = sum(inputs)
        xp = prime(inputs, delta) if interactive else x
        r = rows.setdefault(cls, {"sessions": 0, "calls": 0, "X": 0, "X_prime": 0, "interactive": interactive})
        r["sessions"] += 1
        r["calls"] += len(inputs)
        r["X"] += x
        r["X_prime"] += xp
    tot = {"X": 0, "X_prime": 0, "calls": 0, "sessions": 0}
    for c, r in rows.items():
        r["saving_pct"] = round(100 * (r["X"] - r["X_prime"]) / r["X"], 2) if r["X"] else None
        r["quality"] = "UNKNOWN (counterfactual, nothing re-run)"
        for k in tot:
            tot[k] += r[k]
    tot["saving_pct"] = round(100 * (tot["X"] - tot["X_prime"]) / tot["X"], 2) if tot["X"] else None
    return {"plane": plane, "label": "ESTIMATE (counterfactual)", "lever": "A7 main-lean floor, interactive top-level only",
            "delta_per_call": delta, "delta_source": "MEASURED laptop L5 call-1, applied here as an assumption",
            "since": since, "until": until, "classes": {c: rows[c] for c in CLASS_ORDER + ("subagent",) if c in rows}, "total": tot,
            "caveat": "class by first-user-text heuristic (APPROX); other-host delta; cache pricing ignored (processed tokens only)"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", required=True)
    ap.add_argument("--delta", type=int, default=DELTA_L5)
    ap.add_argument("--projects", type=Path, default=cx.PROJECTS)
    ap.add_argument("--plane", default=socket.gethostname())
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    doc = replay(a.projects, a.since, a.until, a.delta, cx._worker_kinds(), a.plane)
    if a.out:
        a.out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
