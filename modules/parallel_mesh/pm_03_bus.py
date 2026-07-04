#!/usr/bin/env python3
"""pm_03_bus.py -- PM-03: Shared Findings Bus (+ Redundancy Tax).

A pane pays real tokens to reach a reusable conclusion ("this function is dead",
"the real signature is X", "this test is flaky because Z"). The Bus publishes
that finding once so no other pane re-derives it. The Redundancy Tax is the
enforcement edge: before reasoning about a topic, a pane consults the Bus; a hit
returns the existing finding for ZERO new model tokens; only a miss justifies
spending, and the miss is published back so the mesh pays it once.

Parent CO-05 (registry.py): a finding is a CO-05-style asset with a freshness
anchor, stored append-only in JSONL. This module mirrors registry.py's proven
shape (JSONL, file-hash anchor, fail-open) rather than inventing a new store.

Honest (CO-10): the Bus is an append-only JSONL FILE PER REPO on disk, read at
pane boundaries -- not IPC, not a live event stream. JSONL (not a single rewritten
JSON object) is deliberate: concurrent publishers append lines safely, whereas a
single JSON object rewritten on every publish races and clobbers. Fail-open
ABSOLUTE: any error -> the consult misses (reason normally); publish is best-effort.

Storage: ~/.claude/state/parallel_mesh/findings_bus_<enc-repo>.jsonl

Hub wiring (Owner-side, HR-001 -- documented, not auto-edited into the live hook):
  SessionStart  -> `python -m modules.parallel_mesh.pm_03_bus --repo <cwd> --digest`
                   injects the repo's bus digest as light context.
  Stop (end)    -> call publish_session_findings(cwd, <new findings>) to commit
                   this session's discoveries (the Cross-Pane Commit Protocol).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))


def _enc(repo: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", repo or "")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _default_state_dir() -> Path:
    return Path.home() / ".claude" / "state" / "parallel_mesh"


def file_hash(path) -> str | None:
    """Short sha256 of a file (the freshness anchor), or None if unreadable."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


@dataclass
class Finding:
    repo: str
    topic: str
    claim: str                       # the reusable conclusion
    evidence: str = ""               # file:line or command that proved it
    sid: str = ""                    # publishing pane
    anchor: dict = field(default_factory=lambda: {"type": "none"})
    ts: str = ""

    @property
    def identity(self) -> str:
        """Dedup key: normalized topic + claim. Two findings with the same
        conclusion about the same topic are one finding, not near-duplicates."""
        raw = f"{_norm(self.topic)}|{_norm(self.claim)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_json(d: dict) -> "Finding":
        return Finding(
            repo=str(d.get("repo", "")), topic=str(d.get("topic", "")),
            claim=str(d.get("claim", "")), evidence=str(d.get("evidence", "")),
            sid=str(d.get("sid", "")),
            anchor=d.get("anchor") or {"type": "none"},
            ts=str(d.get("ts", "")))


def is_fresh(f: Finding, *, hash_fn=file_hash) -> bool:
    """A finding is FRESH only if its anchor still matches source. A 'none' anchor
    is not auto-fresh -- it is a lead, verify-before-trust (mirrors CO-05)."""
    a = f.anchor or {}
    if a.get("type") == "file" and a.get("path"):
        cur = hash_fn(a["path"])
        return cur is not None and cur == a.get("hash")
    return False


class FindingsBus:
    """Append-only JSONL bus, one file per repo. Publish appends; load reads."""

    def __init__(self, state_dir=None):
        self.state_dir = Path(state_dir) if state_dir else _default_state_dir()

    def path_for(self, repo: str) -> Path:
        return self.state_dir / f"findings_bus_{_enc(repo)}.jsonl"

    def load(self, repo: str) -> list:
        """All findings for a repo (fail-open -> [])."""
        p = self.path_for(repo)
        if not p.is_file():
            return []
        out = []
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(Finding.from_json(json.loads(line)))
                except (json.JSONDecodeError, ValueError):
                    continue
        except OSError:
            return []
        return out

    def publish(self, repo: str, topic: str, claim: str, *, evidence: str = "",
                sid: str = "", anchor=None, now: datetime | None = None,
                dedup: bool = True) -> Finding:
        """Append a finding. With dedup (default), an identical existing finding
        (same identity) is returned WITHOUT a second append -- the bus is not a
        log. Best-effort I/O: an append error still returns the Finding object."""
        now = now or datetime.now(timezone.utc)
        f = Finding(repo=repo, topic=topic, claim=claim, evidence=evidence,
                    sid=sid, anchor=anchor or {"type": "none"}, ts=now.isoformat())
        if dedup:
            for existing in self.load(repo):
                if existing.identity == f.identity:
                    return existing
        try:
            p = self.path_for(repo)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(f.to_json(), ensure_ascii=False) + "\n")
        except OSError:
            pass
        return f

    def query(self, repo: str, topic: str) -> list:
        """Findings matching a topic (normalized), newest first. Fail-open -> []."""
        try:
            nt = _norm(topic)
            hits = [f for f in self.load(repo) if _norm(f.topic) == nt]
            hits.sort(key=lambda f: f.ts, reverse=True)
            return hits
        except Exception:  # noqa: BLE001 -- fail-open
            return []

    def lookup(self, repo: str, topic: str, claim: str | None = None):
        """Best matching finding for a topic (and claim, if given), or None."""
        hits = self.query(repo, topic)
        if not hits:
            return None
        if claim is None:
            return hits[0]
        nc = _norm(claim)
        for f in hits:
            if _norm(f.claim) == nc:
                return f
        return None


class BusIndex:
    """Lightweight derived index over a repo's bus: topic -> findings + a compact
    digest for SessionStart light-context injection."""

    def __init__(self, bus: FindingsBus, repo: str):
        self.repo = repo
        self._by_topic: dict = {}
        for f in bus.load(repo):
            self._by_topic.setdefault(_norm(f.topic), []).append(f)

    def topics(self) -> list:
        return sorted(self._by_topic.keys())

    def by_topic(self, topic: str) -> list:
        return list(self._by_topic.get(_norm(topic), []))

    def digest(self, *, max_topics: int = 40, max_claim_chars: int = 120) -> str:
        """Compact markdown digest -- what SessionStart injects so a pane consults
        before reasoning. Bounded so the bus never becomes its own context cost."""
        if not self._by_topic:
            return f"# Findings Bus ({self.repo}): empty"
        lines = [f"# Findings Bus ({self.repo}) -- consult before reasoning:"]
        for topic in self.topics()[:max_topics]:
            fs = self._by_topic[topic]
            newest = max(fs, key=lambda f: f.ts)
            claim = newest.claim.strip().replace("\n", " ")[:max_claim_chars]
            lines.append(f"- **{topic}** ({len(fs)}): {claim}")
        return "\n".join(lines)


class RedundancyTax:
    """The consume-before-reason gate. `consult` answers 'does this conclusion
    already exist?'; `reason_or_reuse` enforces it -- a hit reuses (0 new tokens),
    a miss reasons and publishes the result back."""

    def __init__(self, bus: FindingsBus | None = None):
        self.bus = bus or FindingsBus()

    def consult(self, repo: str, topic: str, claim: str | None = None):
        """Returns (hit: bool, finding: Finding|None, trust: str). trust is
        'fresh' (anchor matches), 'lead' (unanchored/stale -> verify), or 'none'."""
        f = self.bus.lookup(repo, topic, claim)
        if f is None:
            return (False, None, "none")
        return (True, f, "fresh" if is_fresh(f) else "lead")

    def reason_or_reuse(self, repo: str, topic: str, reason_fn, *,
                        claim: str | None = None, sid: str = "",
                        evidence: str = "", anchor=None,
                        now: datetime | None = None):
        """If the bus already holds the conclusion -> reuse it, reason_fn is NEVER
        called (0 new tokens). Else call reason_fn() to derive the claim, publish
        it, and return it. Returns (claim, reused: bool, trust: str)."""
        hit, f, trust = self.consult(repo, topic, claim)
        if hit and f is not None:
            return (f.claim, True, trust)
        derived = reason_fn()
        pub = self.bus.publish(repo, topic, str(derived), evidence=evidence,
                               sid=sid, anchor=anchor, now=now)
        return (pub.claim, False, "fresh" if is_fresh(pub) else "lead")


def publish_session_findings(repo: str, findings, *, sid: str = "",
                             now: datetime | None = None, state_dir=None) -> int:
    """Cross-Pane Commit Protocol (Stop-hook side): publish this session's new
    findings to the bus at close. `findings` is an iterable of dicts with at least
    topic + claim. Returns the count published. Fail-open -> 0."""
    try:
        bus = FindingsBus(state_dir=state_dir)
        n = 0
        for d in findings or []:
            topic = (d or {}).get("topic")
            claim = (d or {}).get("claim")
            if not topic or not claim:
                continue
            bus.publish(repo, topic, claim, evidence=(d.get("evidence") or ""),
                        sid=sid or (d.get("sid") or ""),
                        anchor=d.get("anchor"), now=now)
            n += 1
        return n
    except Exception:  # noqa: BLE001 -- fail-open
        return 0


def _staging_path(repo: str, sid: str, state_dir=None) -> Path:
    """Per-session staging file the agent appends findings to during work; the Stop
    hook drains it into the bus. One file per (repo, sid) so concurrent panes never
    collide."""
    d = Path(state_dir) if state_dir else _default_state_dir()
    return d / f"session_findings_staging_{_enc(repo)}_{_enc(sid)}.jsonl"


def stage_finding(repo: str, sid: str, topic: str, claim: str, *,
                  evidence: str = "", state_dir=None) -> bool:
    """Producer side: append ONE reusable conclusion to this session's staging file
    the moment it is reached. Drained to the bus at Stop by drain_staging_findings.
    Fail-open -> False (a staging write must never break the agent's work)."""
    try:
        if not topic or not claim:
            return False
        p = _staging_path(repo, sid, state_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"topic": topic, "claim": claim,
                                 "evidence": evidence}, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def drain_staging_findings(repo: str, sid: str, *, now: datetime | None = None,
                           state_dir=None) -> int:
    """Stop side (Cross-Pane Commit): publish every staged finding to the bus, then
    clear the staging file. Returns the count published. Fail-open -> 0, and the
    staging file is cleared ONLY after a publish attempt (never lose findings on a
    read error). Cheap to call every turn-end: no staging file -> 0, no bus write."""
    try:
        p = _staging_path(repo, sid, state_dir)
        if not p.is_file():
            return 0
        findings = []
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                findings.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
        n = publish_session_findings(repo, findings, sid=sid, now=now,
                                     state_dir=state_dir)
        try:
            p.unlink()
        except OSError:
            pass
        return n
    except Exception:  # noqa: BLE001 -- fail-open
        return 0


def load_context_digest(repo: str, *, state_dir=None, max_topics: int = 40) -> str:
    """SessionStart side: the compact bus digest a launching pane consults."""
    try:
        return BusIndex(FindingsBus(state_dir=state_dir), repo).digest(
            max_topics=max_topics)
    except Exception:  # noqa: BLE001 -- fail-open
        return f"# Findings Bus ({repo}): unavailable"


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--repo", default=None)
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--topic", default="")
    ap.add_argument("--claim", default="")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--sid", default="")
    ap.add_argument("--query", action="store_true")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--stage", action="store_true",
                    help="append a finding to this session's staging file")
    ap.add_argument("--drain", action="store_true",
                    help="Stop side: publish staged findings to the bus + clear")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = args.repo or os.getcwd()
    bus = FindingsBus()
    if args.stage:
        ok = stage_finding(repo, args.sid, args.topic, args.claim,
                           evidence=args.evidence)
        print(f"# staged={ok} topic={args.topic!r}")
        return 0
    if args.drain:
        n = drain_staging_findings(repo, args.sid)
        print(f"# drained {n} finding(s) to the bus")
        return 0
    if args.publish:
        f = bus.publish(repo, args.topic, args.claim, evidence=args.evidence,
                        sid=args.sid)
        print(json.dumps(f.to_json()) if args.json
              else f"# published [{f.identity}] topic={f.topic!r}")
        return 0
    if args.query:
        hits = bus.query(repo, args.topic)
        if args.json:
            print(json.dumps([h.to_json() for h in hits]))
        else:
            for h in hits:
                print(f"[{h.identity}] {h.claim[:100]}  (sid={h.sid})")
        return 0
    # default: the SessionStart digest
    print(load_context_digest(repo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
