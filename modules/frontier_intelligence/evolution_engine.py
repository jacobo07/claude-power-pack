#!/usr/bin/env python3
"""evolution_engine.py -- FIOS IV-1 Dataset Evolution Engine.

The one genuinely-new FIOS responsibility: it does not CREATE datasets, it makes the
EXISTING knowledge_base evolve. It scans every dataset, computes cheap deterministic
health signals, and PROPOSES typed mutations for the Owner -- it NEVER applies one.

Mutation kinds (the spec's taxonomy):
  compress    -- oversized dataset with low unique-token density (prose bloat).
  split       -- one dataset spanning too many distinct topics (a family in a file).
  merge       -- two datasets whose titles/topics overlap heavily (a duplicate pair).
  reinforce   -- a dataset below the family depth floor (thin, under-developed).
  deprecate   -- a dataset flagged deprecated/superseded/obsolete in its own body.
  abstract    -- many sibling datasets sharing a pattern that wants a parent doctrine.
  specialize  -- a dataset trying to be general where a scoped child is warranted.

Owner-gated (T-FIOS-EVOLUTION-LOCK-001): the output is a proposal ledger
`pending_mutations.md`; nothing mutates a sealed dataset. This mirrors the
cdio-standards-librarian and graphify agents (propose, never auto-apply).

Anti-duplication: FD-06 mutates ASSETS, GK-07 detects GRAPH drift, the
cdio-librarian evolves CDIO STANDARDS only -- none proposes whole-knowledge_base
dataset mutations. This is that missing scope, and nothing more. Fail-open ABSOLUTE.
"""
from __future__ import annotations

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

_KB_DIR = _PP_ROOT / "vault" / "knowledge_base"
# Health thresholds (named + documented -- a dataset outside a band is a candidate,
# never an auto-action). Word counts are per-file (datasets are multi-Part).
_REINFORCE_WORDS = 400             # below this a dataset is thin (under-developed)
_COMPRESS_WORDS = 6000             # above this AND low density -> prose bloat
_LOW_DENSITY = 0.28                # unique-tokens / total-tokens; below = repetitive
_SPLIT_HEADINGS = 12               # a file with more top-level topics than this may be a family
_MERGE_TITLE_OVERLAP = 0.6         # Jaccard over title tokens flags a near-duplicate pair
_DEPRECATE_MARKERS = ("deprecated", "superseded", "obsolete", "do not use",
                      "replaced by", "no longer")
_DEPRECATE_HEAD_CHARS = 600        # a real deprecation is announced in the top banner
_STOP = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
         "this", "that", "with", "it", "as", "by", "at", "de", "la", "el", "los"}


@dataclass
class MutationProposal:
    target: str                    # dataset path (repo-relative)
    kind: str                      # compress|split|merge|reinforce|deprecate|abstract|specialize
    reason: str                    # the signal, with its measured value
    evidence: str                  # the concrete number that triggered it
    partner: str = ""              # for merge: the other dataset


def _tokens(s: str) -> list:
    return [w for w in re.findall(r"[a-z0-9]{3,}", (s or "").lower()) if w not in _STOP]


def _title_tokens(path: Path) -> set:
    return set(_tokens(path.stem.replace("_", " ").replace("-", " ")))


@dataclass
class _Doc:
    path: Path
    rel: str
    words: int
    density: float
    headings: int
    body_low: str
    title_toks: set


def _scan_one(md: Path, kb_dir: Path) -> _Doc | None:
    try:
        text = md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    toks = _tokens(text)
    words = len(toks)
    density = round(len(set(toks)) / words, 3) if words else 0.0
    headings = len(re.findall(r"(?m)^##\s+\S", text))
    try:
        rel = str(md.relative_to(kb_dir.parent))
    except ValueError:
        rel = md.name
    return _Doc(md, rel, words, density, headings, text.lower(), _title_tokens(md))


def scan(kb_dir: Path | None = None) -> list:
    """Propose mutations across every knowledge_base dataset. Read-only; returns a
    list[MutationProposal]. Fail-open -> [] on any error."""
    proposals: list = []
    try:
        base = kb_dir or _KB_DIR
        if not base.is_dir():
            return []
        docs = []
        for md in sorted(base.rglob("*.md")):
            if md.name.upper().startswith("INDEX") or "_INDEX" in md.name.upper():
                continue                       # indexes are navigation, not datasets
            d = _scan_one(md, base)
            if d is not None:
                docs.append(d)
        # Per-doc signals.
        for d in docs:
            if 0 < d.words < _REINFORCE_WORDS:
                proposals.append(MutationProposal(
                    d.rel, "reinforce",
                    f"below the depth floor ({d.words} < {_REINFORCE_WORDS} words)",
                    f"words={d.words}"))
            if d.words > _COMPRESS_WORDS and d.density < _LOW_DENSITY:
                proposals.append(MutationProposal(
                    d.rel, "compress",
                    f"oversized with low density ({d.words} words, density {d.density})",
                    f"words={d.words} density={d.density}"))
            if d.headings > _SPLIT_HEADINGS:
                proposals.append(MutationProposal(
                    d.rel, "split",
                    f"spans many topics ({d.headings} top-level sections)",
                    f"headings={d.headings}"))
            # Deprecate fires only on a STATUS-BANNER marker near the top (a real
            # deprecation is announced up front), not on the phrase buried in prose
            # -- that avoids false positives on datasets that merely discuss "no
            # longer"/"superseded" descriptively.
            head = d.body_low[:_DEPRECATE_HEAD_CHARS]
            if any(m in head for m in _DEPRECATE_MARKERS):
                hit = next(m for m in _DEPRECATE_MARKERS if m in head)
                proposals.append(MutationProposal(
                    d.rel, "deprecate",
                    f"status banner marks obsolete (contains {hit!r})", f"marker={hit!r}"))
        # Pairwise merge signal (title-token Jaccard). O(n^2) but n is small and this
        # runs on demand, not on the hot path.
        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                a, b = docs[i], docs[j]
                if not a.title_toks or not b.title_toks:
                    continue
                inter = len(a.title_toks & b.title_toks)
                union = len(a.title_toks | b.title_toks) or 1
                jac = inter / union
                if jac >= _MERGE_TITLE_OVERLAP:
                    proposals.append(MutationProposal(
                        a.rel, "merge",
                        f"near-duplicate title with {b.rel} (overlap {round(jac, 2)})",
                        f"jaccard={round(jac, 2)}", partner=b.rel))
        return proposals
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return proposals


def write_pending(proposals: list, *, out_dir=None,
                  now: datetime | None = None) -> Path | None:
    """Write proposals to pending_mutations.md (Owner review queue). NEVER mutates a
    dataset. Fail-open -> None. Owner promotes a proposal by hand -- LOCK-001."""
    try:
        base = Path(out_dir) if out_dir else (_KB_DIR / "frontier_intelligence_os")
        base.mkdir(parents=True, exist_ok=True)
        p = base / "pending_mutations.md"
        ts = (now or datetime.now(timezone.utc)).isoformat()
        lines = ["# FIOS Dataset Evolution -- pending mutations (Owner-gated)", "",
                 f"> Generado {ts}. NADA se aplica automaticamente "
                 "(T-FIOS-EVOLUTION-LOCK-001). El Owner promueve a mano.", "",
                 f"**{len(proposals)} propuesta(s).**", ""]
        if proposals:
            lines += ["| target | mutation | reason | evidence |", "|---|---|---|---|"]
            for m in proposals:
                tgt = m.target + (f"  +  {m.partner}" if m.partner else "")
                lines.append(f"| `{tgt}` | **{m.kind}** | {m.reason} | {m.evidence} |")
        else:
            lines.append("*(sin propuestas -- el knowledge_base esta sano)*")
        lines.append("")
        p.write_text("\n".join(lines), encoding="utf-8")
        return p
    except OSError:
        return None


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="FIOS Dataset Evolution -- propose, never apply")
    ap.add_argument("--kb-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--write", action="store_true", help="write pending_mutations.md")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    props = scan(Path(args.kb_dir) if args.kb_dir else None)
    if args.json:
        print(json.dumps([asdict(m) for m in props], ensure_ascii=False, indent=2))
    else:
        print(f"FIOS Evolution: {len(props)} mutation proposal(s) "
              "(NONE auto-applied -- Owner-gated).")
        for m in props[:20]:
            print(f"  {m.kind:9} {m.target}  --  {m.reason}")
    if args.write:
        p = write_pending(props, out_dir=Path(args.out_dir) if args.out_dir else None)
        print(f"pending_mutations written: {p}" if p else "write failed (fail-open)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
