#!/usr/bin/env python3
"""DAIF-07 obligation extractor — lifts open obligations out of a real session transcript.

Implements the object of DAIF-07 Part II, the taxonomy of Part III (kind determines
closure semantics), the intake gate of Part IV 4.6 (a candidate must name a closure
condition, an owner, and an origin, or it is refused as a wish and the refusal is
recorded), and the de-duplication rule of 4.4 (identical candidates collapse to ONE
obligation carrying N source pointers, never N obligations).

Honest positioning, stated because the corpus forbids the flattering version:
DAIF-07 Part IV names capture-at-creation as the primary path and calls detection after
the fact ARCHAEOLOGY. This module is archaeology. It runs over residue, it recovers the
sentence and not always the meaning, and every obligation it produces carries
intake='archaeology' so that no consumer mistakes it for a CIR-5 object compiled at t=0.
Its value is that the estate has no CIR-5 compiler today and the alternative to reading
the residue is reading nothing.

Fail-open: an unparseable line, an unreadable file, or a turn with an unexpected shape is
skipped, never raised.

CLI:
  python modules/daif/obligation_extractor.py <session.jsonl> [--out obligation_report.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# DAIF-07 Part III — the kinds. Each carries its own closure semantics and its own
# default done-gate shape. A ledger with one undifferentiated kind certifies nothing.
# ---------------------------------------------------------------------------

# (kind, pattern, closure_condition, done_gate)
KIND_RULES: list[tuple[str, str, str, str]] = [
    (
        "pending_verification",
        r"\b(?:not (?:yet )?(?:verified|measured|proven|observed)|sin verificar|"
        r"queda por verificar|needs? (?:to be )?verif\w+|pendiente de verificar|"
        r"remains? (?:unverified|unproven)|no (?:se )?ha verificado)\b",
        "the claim is observed to hold by an executed gate, not asserted",
        "an observed run of the named gate emits its verdict",
    ),
    (
        "pending_test",
        r"\b(?:tests? (?:are |is )?(?:still )?pending|test not (?:yet )?run|suite not run|"
        r"sin test|falta(?:n)? (?:el )?test|no tests? (?:were|was) (?:run|executed)|"
        r"tests? pendientes?)\b",
        "the test exists and a green run is reconciled against a known-good baseline",
        "pytest / the V-gate runner exits 0 against the recorded baseline",
    ),
    (
        "open_decision",
        r"\b(?:owner (?:must|has to) (?:decide|choose)|owner-gated|awaiting (?:the )?owner|"
        r"open question|needs? a decision|decision (?:is )?(?:still )?open|"
        r"queda por decidir|decidir(?:á|a)? el owner|pendiente de decisi(?:ó|o)n)\b",
        "an authored decision object carrying question, options, choice, justification, authority",
        "the decision record exists and names its authority",
    ),
    (
        "deferred_work",
        r"\b(?:deferred to|left for (?:a |the )?(?:next|later|follow)|next sprint|"
        r"in a follow-?up|out of scope for (?:this|the current)|no tocar en este sprint|"
        r"pr(?:ó|o)ximo sprint|queda pendiente|se pospone|postponed)\b",
        "the deferred item is either done under its own kind or explicitly abandoned with a record",
        "the underlying kind's done-gate, or an authored abandonment",
    ),
    (
        "promise",
        r"(?:\b(?:I|we)\s+will\s+(?!not\b)|\bI'?ll\s+(?!not\b)|\bvoy a\s+|\bvamos a\s+)"
        r"(?:\w+\s+){2,}",
        "the promised artifact exists and its own done-gate observes it",
        "the named artifact is on disk and its gate emits a verdict",
    ),
    (
        "task",
        r"\b(?:next step|siguiente paso|remaining work|still (?:to do|missing)|"
        r"falta(?:n)? (?:por )?(?:implementar|construir|escribir|a(?:ñ|n)adir)|"
        r"needs? (?:to be )?(?:implemented|wired|built|written))\b",
        "the change exists on disk and its done-gate observes it",
        "the artifact exists and the suite covering it exits 0",
    ),
]

# Markers of discharge. A subject that reappears later under one of these is closed and is
# NOT an open obligation. This is a coarse resolver, and it is recorded as such.
DISCHARGE_RE = re.compile(
    r"\b(?:done|sealed|shipped|committed|passed|green|exit 0|verified|resolved|"
    r"listo|hecho|sellado|cerrado|completado)\b",
    re.IGNORECASE,
)

# DAIF-07 2.8 / 4.6 — the wish clause. A candidate whose object is a sentiment with no
# checkable subject names no closure condition and is refused at intake.
WISH_RE = re.compile(
    r"\b(?:keep an eye|be careful|at some point|somewhere down the line|"
    r"ten(?:er)? cuidado|alg(?:ú|u)n d(?:í|i)a|estar(?:í|i)a bien)\b",
    re.IGNORECASE,
)

# A kind pattern alone is not enough. Prose ABOUT verification is not a commitment TO verify,
# and a corpus that discusses obligations is not a session that incurs them. A candidate must
# also carry a commitment frame — a person, a deontic, or a pendency — which is the grammatical
# trace of someone taking something on. DAIF-07 3.7 holds that softness of phrasing is no
# measure of the reality of the work; the ABSENCE of any commitment frame is different, and is
# evidence the sentence describes rather than commits.
COMMITMENT_FRAME_RE = re.compile(
    r"(?:\b(?:I|we|you|let'?s|I'?ll|we'?ll)\b|\b(?:must|should|need(?:s)? to|have to|has to|"
    r"will)\b|\b(?:pending|deferred|remaining|next)\b|"
    r"\b(?:hay que|falta|faltan|queda|quedan|pendiente|voy a|vamos a|debe|debemos|no tocar)\b)",
    re.IGNORECASE,
)

MIN_SUBJECT_WORDS = 4
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;:\n])\s+")


@dataclass
class Obligation:
    """DAIF-07 Part II. Every slot is present; unknown is spelled, never absent (DAIF-01 2.6)."""

    identifier: str
    kind: str
    origin: str                       # the source unit it arose from — session + turn
    source: list[str]                 # the exact pointers; de-dup keeps ALL of them (4.4)
    owner: str
    authority: str
    scope: str
    text: str
    closure_condition: str            # 2.7 — without this it is a wish, not an obligation
    done_gate: str
    evidence: list[str] = field(default_factory=list)
    priority: str = "unknown"
    risk: str = "unknown"
    impact: str = "unknown"
    dependencies: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    consumers: list[str] = field(default_factory=list)
    state: str = "active"
    lifecycle_stage: str = "live"
    born_ts: str = "unknown"          # the age triple (2.6) — recorded at write time,
    last_activity_ts: str = "unknown" # because age cannot be reconstructed by archaeology
    deferral_count: int = 0
    expiry: str = "unknown"
    escalation_path: str = "owner_queue"
    abandonment_risk: str = "unknown"
    supersedes: str = "unknown"
    intake: str = "archaeology"       # never 'cir-5' — this extractor runs over residue
    confidence: str = "low"           # DAIF-01 2.4 — an unqualified claim is trusted least

    def resumption_context(self) -> dict[str, Any]:
        """DAIF-07 12.3 — the five elements. Survival is CLOSEABILITY, not a surviving name."""
        return {
            "what": self.text,
            "why": self.origin,
            "what_closes_it": self.closure_condition,
            "depends_on": self.dependencies + self.blockers,
            "evidence_lives": self.source + self.evidence,
        }

    def is_closeable(self) -> bool:
        """12.5 clause two — an obligation that survives with an empty closure condition is LOST."""
        rc = self.resumption_context()
        return bool(rc["what"].strip()) and bool(rc["why"].strip()) and \
            bool(rc["what_closes_it"].strip()) and bool(rc["evidence_lives"])


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def _subject_key(text: str) -> str:
    """Stable, content-independent handle (2.2). Keyed on the normalized subject so that a
    reworded obligation is still the same obligation."""
    words = [w for w in _norm(text).split() if len(w) > 3][:12]
    return hashlib.sha256(" ".join(words).encode("utf-8")).hexdigest()[:12]


def _iter_turns(path: Path) -> Iterable[dict[str, Any]]:
    """Yield {role, text, ts, uuid} per turn. Fail-open on every line."""
    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(rec, dict) or rec.get("type") not in ("user", "assistant"):
            continue
        msg = rec.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        chunks: list[str] = []
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for block in content:
                # tool_result bodies are machine residue, not commitments — never scanned.
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text")
                    if isinstance(t, str):
                        chunks.append(t)
        if not chunks:
            continue
        yield {
            "role": rec.get("type"),
            "text": "\n".join(chunks),
            "ts": str(rec.get("timestamp") or "unknown"),
            "uuid": str(rec.get("uuid") or "unknown"),
        }


def _classify(sentence: str) -> tuple[str, str, str] | None:
    for kind, pattern, closure, gate in KIND_RULES:
        if re.search(pattern, sentence, re.IGNORECASE):
            return kind, closure, gate
    return None


def extract_obligations(session_path: str | Path) -> tuple[list[Obligation], dict[str, Any]]:
    """Return (open obligations, intake report). Never raises on a malformed session."""
    path = Path(session_path)
    session_id = path.stem
    candidates: dict[str, Obligation] = {}
    refused_wishes = 0
    refused_no_subject = 0
    refused_no_frame = 0
    scanned_turns = 0
    discharged_keys: set[str] = set()
    discharge_sentences: list[str] = []

    for turn in _iter_turns(path):
        scanned_turns += 1
        for sentence in _SENTENCE_SPLIT.split(turn["text"]):
            sentence = sentence.strip()
            if not (12 <= len(sentence) <= 600):
                continue
            if DISCHARGE_RE.search(sentence):
                discharge_sentences.append(_norm(sentence))
            hit = _classify(sentence)
            if hit is None:
                continue
            kind, closure, gate = hit
            if WISH_RE.search(sentence):
                refused_wishes += 1          # 4.6 — the refusal is itself recorded
                continue
            if not COMMITMENT_FRAME_RE.search(sentence):
                refused_no_frame += 1
                continue
            if len(sentence.split()) < MIN_SUBJECT_WORDS:
                refused_no_subject += 1
                continue

            key = _subject_key(sentence)
            pointer = f"{session_id}#{turn['uuid']}"
            existing = candidates.get(key)
            if existing is not None:
                # 4.4 — one obligation, N source pointers. Never N obligations.
                if pointer not in existing.source:
                    existing.source.append(pointer)
                existing.last_activity_ts = turn["ts"]
                existing.deferral_count += 1
                continue
            candidates[key] = Obligation(
                identifier=f"OB-{key}",
                kind=kind,
                origin=f"session:{session_id} turn:{turn['uuid']} role:{turn['role']}",
                source=[pointer],
                owner="agent" if turn["role"] == "assistant" else "owner",
                authority="owner",
                scope="project",
                text=sentence,
                closure_condition=closure,
                done_gate=gate,
                born_ts=turn["ts"],
                last_activity_ts=turn["ts"],
            )

    # Coarse discharge resolution: an obligation whose subject words later reappear in a
    # sentence carrying a discharge marker is treated as closed and dropped from the OPEN set.
    for key, ob in candidates.items():
        subject = {w for w in _norm(ob.text).split() if len(w) > 4}
        if not subject:
            continue
        for later in discharge_sentences:
            later_words = set(later.split())
            if len(subject & later_words) >= max(3, len(subject) // 2):
                discharged_keys.add(key)
                break

    open_obligations = [ob for k, ob in candidates.items() if k not in discharged_keys]
    open_obligations.sort(key=lambda o: (o.kind, o.identifier))

    report = {
        "session_id": session_id,
        "session_path": str(path),
        "turns_scanned": scanned_turns,
        "candidates": len(candidates),
        "open": len(open_obligations),
        "discharged": len(discharged_keys),
        "refused_as_wish": refused_wishes,
        "refused_no_commitment_frame": refused_no_frame,
        "refused_no_subject": refused_no_subject,
        "intake": "archaeology",
        "by_kind": {k: sum(1 for o in open_obligations if o.kind == k)
                    for k in sorted({o.kind for o in open_obligations})},
    }
    return open_obligations, report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DAIF-07 obligation extractor")
    ap.add_argument("session", help="path to a Claude Code session .jsonl")
    ap.add_argument("--out", default=None, help="write obligation_report.json here")
    args = ap.parse_args(argv)

    obligations, report = extract_obligations(args.session)
    payload = {"report": report, "obligations": [asdict(o) for o in obligations]}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    for o in obligations[:20]:
        print(f"  [{o.kind}] {o.identifier}  {o.text[:100]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
