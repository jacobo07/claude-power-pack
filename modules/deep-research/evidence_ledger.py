#!/usr/bin/env python3
"""evidence_ledger.py — claim-level evidence for deep_research (DRX U1).

WHY THIS MODULE EXISTS
----------------------
Up to v0.3.0 a learning's `evidence` was a sentence the extractor WROTE, and its
`supporting_sources` was a number the extractor REPORTED. Neither pointed at a
place in a document, so "VERIFIED" meant "the model said two sources agreed".
The epistemic caps in research_engines.cap_epistemic could only check the
arithmetic of a self-report, never the report itself.

This module makes the claim checkable against the bytes the model actually read:

  * SourceSnapshot  every page text handed to the extractor is stored once,
                    content-addressed by SHA-256, exactly as the model saw it.
  * EvidenceSpan    a quote is accepted only if it occurs VERBATIM (modulo
                    whitespace, case, typographic quotes/dashes and markdown
                    emphasis) in the snapshot of the source it names. The span
                    keeps the character offsets into the ORIGINAL text, so an
                    auditor can re-locate it without trusting this code.
  * Lineage         sources whose text is substantially the same document
                    (syndication, scraped copies, identical press release) are
                    one lineage. Corroboration counts lineages, never URLs.
  * Claim           the extractor's label is capped, DEGRADE-ONLY, by what the
                    verified spans can carry.

No fuzzy matching. A near-match that is accepted is exactly the failure this
module exists to remove; a correct quote that is rejected costs one demotion,
which is visible in the ledger and recoverable. The asymmetry is deliberate.

Pure Python, stdlib only, no network, no LLM. `audit_ledger` re-verifies a
written ledger from disk, independently of the process that produced it.

    python evidence_ledger.py audit <ledger.json>
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

__version__ = "1.0.0"

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from research_engines import (  # noqa: E402
    EPI_DERIVED,
    EPI_HYPOTHESIS,
    EPI_OBSERVED,
    EPI_REJECTED,
    EPI_VERIFIED,
    EPISTEMIC_RANK,
    normalize_epistemic,
)

# A quote shorter than this (after normalisation) matches too many places to
# prove anything: "the model" occurs in every page about models.
MIN_QUOTE_CHARS = 20
# A "quote" longer than this is the extractor pasting a page, not citing it.
MAX_QUOTE_CHARS = 600
# Corroboration needs this many DISTINCT lineages among verified spans.
MIN_LINEAGES_FOR_VERIFIED = 2
# Two snapshots are one lineage when this share of the smaller one's shingles
# also occurs in the other (containment, not Jaccard: a short press release
# embedded in a longer article is still a copy of it).
LINEAGE_CONTAINMENT = 0.6
SHINGLE_WORDS = 8
# Two verified quotes from different sources that normalise to the same text
# and are at least this long are treated as a shared origin.
SHARED_QUOTE_MIN_CHARS = 60

_TRANSLATE = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "−": "-", " ": " ",
    " ": " ", " ": " ", "…": "...",
}
_SKIP = set("*_`#>")


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_exact(path: Path) -> str:
    """Read a snapshot without newline translation (the inverse of the write)."""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalise `text` for matching and return (normalised, index_map).

    index_map[k] is the index in `text` of the character that produced
    normalised[k]. Whitespace runs collapse to one space; markdown emphasis
    characters are dropped; case is folded with lower() per character so the
    map stays exact even where lowering changes length.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = True
    for i, ch in enumerate(text):
        if ch in _SKIP:
            continue
        rep = _TRANSLATE.get(ch, ch)
        for c in rep:
            if c.isspace():
                if prev_space:
                    continue
                out.append(" ")
                idx.append(i)
                prev_space = True
                continue
            for lc in c.lower():
                out.append(lc)
                idx.append(i)
            prev_space = False
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def normalize(text: str) -> str:
    return normalize_with_map(text)[0]


def locate_quote(snapshot: str, quote: str) -> tuple[int, int] | None:
    """Return (start, end) offsets of `quote` in the ORIGINAL `snapshot`, or None.

    Exact match after normalisation only. The first occurrence wins; the span
    stores its own text, so which occurrence was chosen never changes what an
    auditor reads.
    """
    nq = normalize(quote).strip()
    if not nq:
        return None
    ns, imap = normalize_with_map(snapshot)
    pos = ns.find(nq)
    if pos < 0:
        return None
    start = imap[pos]
    end = imap[pos + len(nq) - 1] + 1
    return start, end


_NUM_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")


def numbers_in(text: str) -> set[str]:
    """Number tokens that carry information (commas stripped, trailing % kept).

    Integers below 10 are ignored: sources write them as words ("three runs")
    and the claim restates them as digits, so demanding a digit match would
    demote correct claims for spelling.
    """
    found: set[str] = set()
    for m in _NUM_RE.finditer(text or ""):
        tok = m.group(0).replace(",", "").rstrip(".")
        bare = tok.rstrip("%")
        try:
            val = float(bare)
        except ValueError:
            continue
        if "." not in bare and val < 10:
            continue
        found.add(tok)
    return found


def _shingles(text: str, k: int = SHINGLE_WORDS) -> set[int]:
    words = re.findall(r"\w+", normalize(text))
    if len(words) < k:
        return {hash(" ".join(words))} if words else set()
    return {hash(" ".join(words[i:i + k])) for i in range(len(words) - k + 1)}


class EvidenceLedger:
    """Per-run registry of snapshots, spans and claims. JSON-serialisable."""

    def __init__(self, run_id: str, snapshot_dir: Path) -> None:
        self.run_id = run_id
        self.snapshot_dir = Path(snapshot_dir)
        self.sources: dict[str, dict[str, Any]] = {}
        self.spans: dict[str, dict[str, Any]] = {}
        self.claims: list[dict[str, Any]] = []
        self._by_sha: dict[str, str] = {}
        self._text_cache: dict[str, str] = {}
        self._shingle_cache: dict[str, set[int]] = {}
        self._lineage: dict[str, str] | None = None

    # -- sources --------------------------------------------------------------

    def add_source(self, url: str, text: str, family: str = "UNKNOWN",
                   quality: str = "LOW", injection_flags: list[str] | None = None,
                   retrieved_at: str | None = None) -> str:
        """Register the exact text the extractor will read. Returns source_id.

        Identical text from a second URL is NOT a second source: the URL is
        recorded as an alias of the first, which is the cheapest and strongest
        independence fact available.
        """
        digest = sha256_text(text)
        if digest in self._by_sha:
            sid = self._by_sha[digest]
            aliases = self.sources[sid].setdefault("aliases", [])
            if url != self.sources[sid]["url"] and url not in aliases:
                aliases.append(url)
            return sid
        sid = f"S{len(self.sources) + 1}"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        snap = self.snapshot_dir / f"{digest}.txt"
        if not snap.exists():
            tmp = snap.with_suffix(f".tmp.{os.getpid()}")
            tmp.write_text(text, encoding="utf-8", newline="")
            os.replace(tmp, snap)
        self.sources[sid] = {
            "source_id": sid,
            "url": url,
            "aliases": [],
            "sha256": digest,
            "chars": len(text),
            "snapshot": snap.name,
            "retrieved_at": retrieved_at or now_iso(),
            "family": family,
            "quality": quality,
            "injection_flags": list(injection_flags or []),
        }
        self._by_sha[digest] = sid
        self._text_cache[sid] = text
        self._lineage = None
        return sid

    def source_text(self, sid: str) -> str:
        if sid not in self._text_cache:
            src = self.sources[sid]
            # newline="" : snapshots are byte-exact; read_text() would turn \r\n
            # into \n, break the SHA-256 and shift every span offset on resume.
            self._text_cache[sid] = _read_exact(self.snapshot_dir / src["snapshot"])
        return self._text_cache[sid]

    # -- lineage --------------------------------------------------------------

    def lineages(self) -> dict[str, str]:
        """source_id -> lineage root id (union-find over near-duplicate text)."""
        if self._lineage is not None:
            return self._lineage
        parent = {sid: sid for sid in self.sources}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        ids = sorted(self.sources, key=lambda s: int(s[1:]))
        for sid in ids:
            if sid not in self._shingle_cache:
                self._shingle_cache[sid] = _shingles(self.source_text(sid))
        for i, a in enumerate(ids):
            sa = self._shingle_cache[a]
            for b in ids[i + 1:]:
                sb = self._shingle_cache[b]
                if not sa or not sb:
                    continue
                inter = len(sa & sb)
                if inter / min(len(sa), len(sb)) >= LINEAGE_CONTAINMENT:
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        parent[max(ra, rb, key=lambda s: int(s[1:]))] = min(
                            ra, rb, key=lambda s: int(s[1:]))
        self._lineage = {sid: find(sid) for sid in ids}
        return self._lineage

    # -- claims ---------------------------------------------------------------

    def _add_span(self, sid: str, start: int, end: int) -> str:
        text = self.source_text(sid)[start:end]
        span_id = f"E{len(self.spans) + 1}"
        self.spans[span_id] = {
            "span_id": span_id,
            "source_id": sid,
            "start": start,
            "end": end,
            "text": text,
            "sha256": sha256_text(text),
        }
        return span_id

    def verify_claim(self, claim_text: str, level: str,
                     quotes: list[dict[str, Any]] | None,
                     meta: dict[str, Any] | None = None) -> dict[str, Any]:
        """Verify a claim's quotes and cap its label. Appends and returns the record.

        `level` is the label AFTER research_engines.cap_epistemic; this only ever
        lowers it. Rules, in order:
          * a quote naming an unknown source, too short, too long, or not found
            verbatim in that source's snapshot is REJECTED (kept, with reason);
          * no verified span at all -> at most HYPOTHESIS (REJECTED stays);
          * VERIFIED needs >= 2 distinct lineages among verified spans;
          * OBSERVED needs every informative number in the claim to occur in a
            verified span.
        """
        verified: list[str] = []
        rejected: list[dict[str, str]] = []
        reattributed: list[dict[str, str]] = []
        for q in quotes or []:
            if not isinstance(q, dict):
                rejected.append({"quote": str(q)[:200], "reason": "malformed quote entry"})
                continue
            sid = str(q.get("source_id") or "").strip().upper()
            quote = str(q.get("quote") or "")
            nq = normalize(quote)
            if sid not in self.sources:
                rejected.append({"source_id": sid, "quote": quote[:200],
                                 "reason": "unknown source id"})
                continue
            if len(nq) < MIN_QUOTE_CHARS:
                rejected.append({"source_id": sid, "quote": quote[:200],
                                 "reason": f"shorter than {MIN_QUOTE_CHARS} chars"})
                continue
            if len(nq) > MAX_QUOTE_CHARS:
                rejected.append({"source_id": sid, "quote": quote[:200],
                                 "reason": f"longer than {MAX_QUOTE_CHARS} chars"})
                continue
            loc = locate_quote(self.source_text(sid), quote)
            if loc is None:
                # RE-ATTRIBUTION (2026-11-11, first real runs: 6 of 9 rejected
                # quotes were verbatim in ANOTHER snapshot of the same run, 0 were
                # absent from all). The quote is still required verbatim in a
                # hashed snapshot; only the pointer the extractor named is
                # corrected, and the correction is recorded, so the report cites
                # the page that actually says it instead of the wrong URL.
                found = self._find_elsewhere(quote, exclude=sid)
                if found is None:
                    rejected.append({"source_id": sid, "quote": quote[:200],
                                     "reason": "not found verbatim in snapshot"})
                    continue
                other, loc = found
                reattributed.append({"cited": sid, "found": other,
                                     "quote": quote[:200]})
                sid = other
            verified.append(self._add_span(sid, *loc))

        lineage = self.lineages()
        roots: set[str] = set()
        seen_quotes: dict[str, str] = {}
        for span_id in verified:
            span = self.spans[span_id]
            root = lineage.get(span["source_id"], span["source_id"])
            nq = normalize(span["text"])
            if len(nq) >= SHARED_QUOTE_MIN_CHARS and nq in seen_quotes:
                root = seen_quotes[nq]
            seen_quotes.setdefault(nq, root)
            roots.add(root)

        claimed = normalize_epistemic(level)
        final = claimed
        reasons: list[str] = []
        if claimed != EPI_REJECTED:
            if not verified:
                if EPISTEMIC_RANK[final] > EPISTEMIC_RANK[EPI_HYPOTHESIS]:
                    final = EPI_HYPOTHESIS
                    reasons.append("no quote verified in any snapshot")
            else:
                span_text = " ".join(self.spans[s]["text"] for s in verified)
                missing = sorted(n for n in numbers_in(claim_text)
                                 if n not in numbers_in(span_text))
                if final == EPI_VERIFIED and len(roots) < MIN_LINEAGES_FOR_VERIFIED:
                    final = EPI_OBSERVED if not missing and numbers_in(claim_text) else EPI_DERIVED
                    reasons.append(f"VERIFIED needs {MIN_LINEAGES_FOR_VERIFIED} independent "
                                   f"lineages, verified spans cover {len(roots)}")
                if final == EPI_OBSERVED and (missing or not numbers_in(span_text)):
                    final = EPI_DERIVED
                    reasons.append("OBSERVED number(s) absent from verified spans: "
                                   + (", ".join(missing) if missing else "spans carry no figure"))
        # No min() over EPISTEMIC_RANK here, on purpose. That scale ranks
        # OBSERVED above VERIFIED (the Owner's ladder), so min(OBSERVED,
        # VERIFIED) would hand a demoted claim its old label back -- caught by
        # V-DRX-COPIES-ARE-ONE-LINEAGE. The moves above are the only ones
        # allowed: VERIFIED->OBSERVED|DERIVED, OBSERVED->DERIVED, any->HYPOTHESIS.
        record = {
            "claim_id": f"C{len(self.claims) + 1}",
            "text": claim_text,
            "epistemic_in": claimed,
            "epistemic": final,
            "ledger_capped": final != claimed,
            "ledger_reason": "; ".join(reasons),
            "spans": verified,
            "source_ids": sorted({self.spans[s]["source_id"] for s in verified},
                                 key=lambda s: int(s[1:])),
            "independent_lineages": len(roots),
            "rejected_quotes": rejected,
            "reattributed_quotes": reattributed,
            # None until the caller says whether the claim entered the corpus
            # (the relevance gate and the 3-per-query cap drop some after
            # verification). Unknown is reported as unknown, never as kept.
            "persisted": None,
        }
        if meta:
            record["meta"] = meta
        self.claims.append(record)
        return record

    def _find_elsewhere(self, quote: str, exclude: str) -> tuple[str, tuple[int, int]] | None:
        """First other snapshot (by id) that contains `quote` verbatim, or None."""
        for sid in sorted(self.sources, key=lambda x: int(x[1:])):
            if sid == exclude:
                continue
            loc = locate_quote(self.source_text(sid), quote)
            if loc is not None:
                return sid, loc
        return None

    def mark_persisted(self, claim_id: str, persisted: bool) -> None:
        for c in self.claims:
            if c["claim_id"] == claim_id:
                c["persisted"] = bool(persisted)
                return
        raise KeyError(claim_id)

    # -- reporting / persistence ----------------------------------------------

    def summary(self) -> dict[str, Any]:
        total = len(self.claims)
        with_span = sum(1 for c in self.claims if c["spans"])
        kept = [c for c in self.claims if c.get("persisted") is True]
        kept_span = sum(1 for c in kept if c["spans"])
        quotes_offered = sum(len(c["spans"]) + len(c["rejected_quotes"]) for c in self.claims)
        quotes_rejected = sum(len(c["rejected_quotes"]) for c in self.claims)
        lineage = self.lineages()
        return {
            "sources": len(self.sources),
            "lineages": len(set(lineage.values())),
            "duplicate_url_aliases": sum(len(s["aliases"]) for s in self.sources.values()),
            "sources_with_injection_flags": sum(1 for s in self.sources.values()
                                                if s["injection_flags"]),
            "claims": total,
            "claims_with_verified_span": with_span,
            "verified_span_rate": round(with_span / total, 3) if total else None,
            "quotes_offered": quotes_offered,
            "quotes_rejected": quotes_rejected,
            "ledger_capped": sum(1 for c in self.claims if c["ledger_capped"]),
            "quotes_reattributed": sum(len(c.get("reattributed_quotes", []))
                                       for c in self.claims),
            "claims_persisted": len(kept),
            "persisted_with_verified_span": kept_span,
            "persisted_verified_span_rate": round(kept_span / len(kept), 3) if kept else None,
        }

    def to_dict(self) -> dict[str, Any]:
        lineage = self.lineages()
        return {
            "schema": "drx-evidence-ledger/1",
            "module_version": __version__,
            "run_id": self.run_id,
            "snapshot_dir": str(self.snapshot_dir),
            "sources": [dict(s, lineage=lineage.get(sid, sid))
                        for sid, s in sorted(self.sources.items(),
                                             key=lambda kv: int(kv[0][1:]))],
            "spans": list(self.spans.values()),
            "claims": self.claims,
            "summary": self.summary(),
        }

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
        tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1),
                       encoding="utf-8")
        os.replace(tmp, path)
        return path

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceLedger":
        led = cls(data["run_id"], Path(data["snapshot_dir"]))
        for s in data.get("sources", []):
            s = dict(s)
            s.pop("lineage", None)
            led.sources[s["source_id"]] = s
            led._by_sha[s["sha256"]] = s["source_id"]
        for sp in data.get("spans", []):
            led.spans[sp["span_id"]] = sp
        led.claims = list(data.get("claims", []))
        return led

    @classmethod
    def load(cls, path: Path) -> "EvidenceLedger":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def audit_ledger(path: Path) -> dict[str, Any]:
    """Re-verify a written ledger from disk without trusting its producer.

    Checks: each snapshot exists and still hashes to its recorded SHA-256; each
    span's text is exactly snapshot[start:end] and hashes to its recorded hash;
    each claim's spans exist; no claim above HYPOTHESIS lacks a verified span.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    snap_dir = Path(data["snapshot_dir"])
    failures: list[str] = []
    texts: dict[str, str] = {}
    for s in data.get("sources", []):
        p = snap_dir / s["snapshot"]
        if not p.exists():
            failures.append(f"{s['source_id']}: snapshot missing ({p.name})")
            continue
        t = _read_exact(p)
        if sha256_text(t) != s["sha256"]:
            failures.append(f"{s['source_id']}: snapshot hash mismatch")
            continue
        texts[s["source_id"]] = t
    spans = {sp["span_id"]: sp for sp in data.get("spans", [])}
    for sp in spans.values():
        t = texts.get(sp["source_id"])
        if t is None:
            failures.append(f"{sp['span_id']}: source {sp['source_id']} unreadable")
            continue
        piece = t[sp["start"]:sp["end"]]
        if piece != sp["text"] or sha256_text(piece) != sp["sha256"]:
            failures.append(f"{sp['span_id']}: span text does not match snapshot offsets")
    for c in data.get("claims", []):
        for sid in c.get("spans", []):
            if sid not in spans:
                failures.append(f"{c['claim_id']}: cites missing span {sid}")
        lvl = normalize_epistemic(c.get("epistemic"))
        if (not c.get("spans") and lvl != EPI_REJECTED
                and EPISTEMIC_RANK[lvl] > EPISTEMIC_RANK[EPI_HYPOTHESIS]):
            failures.append(f"{c['claim_id']}: {lvl} with no verified span")
    return {"ok": not failures, "failures": failures,
            "sources": len(data.get("sources", [])), "spans": len(spans),
            "claims": len(data.get("claims", []))}


def render_evidence_md(ledger: EvidenceLedger, max_claims: int = 60) -> str:
    """Deterministic '## Evidence ledger' section: no LLM touches this text."""
    s = ledger.summary()
    lines = [
        "## Evidence ledger",
        "",
        f"- **Claims:** {s['claims']} · with a verified quote: "
        f"{s['claims_with_verified_span']} (rate {s['verified_span_rate']})",
        f"- **Quotes:** {s['quotes_offered']} offered, {s['quotes_rejected']} rejected "
        f"(not verbatim / unknown source / length)",
        f"- **Sources:** {s['sources']} snapshots in {s['lineages']} independent lineage(s); "
        f"{s['duplicate_url_aliases']} URL(s) were byte-identical copies",
        f"- **Labels lowered by the ledger:** {s['ledger_capped']}",
        f"- **Sources with instruction-like text (treated as data):** "
        f"{s['sources_with_injection_flags']}",
        "",
    ]
    for c in ledger.claims[:max_claims]:
        lines.append(f"**{c['claim_id']}** [{c['epistemic']}] {c['text']}")
        for sp_id in c["spans"]:
            sp = ledger.spans[sp_id]
            src = ledger.sources[sp["source_id"]]
            quote = sp["text"].replace("\n", " ").strip()
            if len(quote) > 280:
                quote = quote[:277] + "..."
            lines.append(f"  - {sp['source_id']} <{src['url']}> chars "
                         f"{sp['start']}-{sp['end']}: \"{quote}\"")
        if not c["spans"]:
            lines.append("  - _no verified quote_")
        for ra in c.get("reattributed_quotes", []):
            lines.append(f"  - _extractor cited {ra['cited']}; quote found verbatim in "
                         f"{ra['found']} (citation corrected)_")
        if c["ledger_reason"]:
            lines.append(f"  - _ledger: {c['ledger_reason']}_")
        lines.append("")
    if len(ledger.claims) > max_claims:
        lines.append(f"_{len(ledger.claims) - max_claims} more claim(s) in the ledger JSON._")
    return "\n".join(lines).rstrip() + "\n"


def _main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "audit":
        res = audit_ledger(Path(argv[1]))
        print(json.dumps(res, indent=1))
        return 0 if res["ok"] else 1
    print(f"evidence_ledger {__version__}\nusage: python evidence_ledger.py audit <ledger.json>")
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
