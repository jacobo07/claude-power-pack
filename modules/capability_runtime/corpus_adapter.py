#!/usr/bin/env python3
"""corpus_adapter.py -- the corpus-to-capability writer (UCEIMR residue R1).

`seed_capability_contracts.py` says it in its own docstring: the capability
layer "shipped as a reader with no writer", and the seeder that fixed that
seeds "from capabilities THIS repo actually has" -- an INTROSPECTIVE producer.
It is the only writer of a contract.

So the estate could acquire evidence (crawl_os / AKOS / autoresearch), rank
capabilities (applicability), specialize them (derivatives), audit overlap
(d2a) and score portfolios -- and there was no path from a mined corpus to a
proposal. That gap is the whole thesis of the UCEIMR brief: convert sources
into CAPABILITIES, not into knowledge. This module is that path and nothing
more.

  evidence (existing stores)
    -> claim extraction        (what capability does the author ASSUME?)
    -> d2a.run()               (overlap audit -- the real filter)
    -> CapabilityProposal      (propose-only, no owner, cannot be activated)
    -> [Owner approves]        -> CapabilityContract -> save_contract()

Three boundaries this module does NOT cross:

  HR-UCEIMR-02  It ACQUIRES NOTHING. It reads what CrawlOS/AKOS/autoresearch
                already wrote to disk. No fetch, no download, no transcription.
  HR-UCEIMR-03  Every proposal passes the d2a overlap audit before it is
                surfaced. A proposal an existing owner already covers is
                dropped WITH the parent named, never silently.
  propose-only  A CapabilityProposal carries no owner, so it CANNOT become a
                contract by accident: `CapabilityContract.validate()` rejects
                an empty owner (HR-APA-018). Only `approve()` -- which demands
                an Owner-supplied owner -- can produce a real contract. A miner
                that admits its own capabilities is a gate that grades itself.

Extraction is lexical and deterministic, and is a SURFACER, not a judge: it
proposes sentences in which an author assumes a capability. The overlap audit
filters and the Owner decides. Stating that plainly is the point -- an
extractor sold as an oracle would be the `research theater` failure mode the
brief itself names.

Stdlib-only. Fail-open at every read boundary; fail-closed on approve.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, save_contract,
)

PROPOSALS_DIR = _PP_ROOT / "vault" / "capability_runtime" / "proposals"

# Bounds. A miner over an on-disk corpus must never run unbounded.
_MAX_FILE_BYTES = 2_000_000
_MAX_FILES = 400
_MAX_SENTENCES_PER_UNIT = 400
_MAX_CLAIMS_PER_UNIT = 3
_MIN_CLAIM_CHARS = 30
_MAX_CLAIM_CHARS = 400

# Coverage at or above this means an existing owner already holds the ground.
# Same floor d2a uses for its own self-duplication filter, deliberately: two
# different thresholds for "is this already owned" would drift apart.
OWNED_COVERAGE_PCT = 50

# A capability is a VERB the author applies to an object. These are the verbs
# that denote one; a sentence without one describes a fact, not a capability.
_CAPABILITY_VERBS = (
    "compare", "compares", "comparing", "track", "tracks", "tracking",
    "measure", "measures", "measuring", "detect", "detects", "detecting",
    "monitor", "monitors", "monitoring", "automate", "automates", "automating",
    "validate", "validates", "verify", "verifies", "score", "scores",
    "scoring", "rank", "ranks", "ranking", "audit", "audits", "auditing",
    "benchmark", "benchmarks", "predict", "predicts", "classify", "classifies",
    "extract", "extracts", "extracting", "aggregate", "aggregates",
    "correlate", "correlates", "simulate", "simulates", "replay", "replays",
    "cross-reference", "cross-check", "deduplicate", "prioritize",
    "prioritise", "forecast", "attribute", "reconcile", "instrument",
    # Spanish -- the corpora on disk are bilingual.
    "comparo", "comparar", "mido", "medir", "detecto", "detectar",
    "monitorizo", "automatizo", "automatizar", "verifico", "verificar",
    "puntuo", "clasificar", "clasifico", "extraigo", "extraer", "priorizo",
)
# Habitual / prescriptive markers -- the author states this as standing practice.
_HABITUAL = (
    "always", "every time", "i use", "i always", "you should", "you need to",
    "you have to", "the key is", "make sure", "never ", "we always",
    "the first thing", "rule of thumb", "best practice",
    "siempre", "cada vez", "lo primero", "hay que", "tienes que", "nunca ",
)
_SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")
_WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_-]+")
# Markdown / code furniture. A bullet, heading, quote, table row, link or code
# span is a note ABOUT work; a capability claim is prose BY an author.
_STRUCT_PREFIX = ("- ", "* ", "> ", "#", "|", "```", "1.", "2.", "3.", "4.")
_STRUCT_INLINE = ("](", "```", "**", "`", "|---", "<http")


def _is_structural(s: str) -> bool:
    t = s.strip()
    return (t.startswith(_STRUCT_PREFIX)
            or any(tok in t for tok in _STRUCT_INLINE))


@dataclass
class EvidenceUnit:
    """One addressable piece of already-acquired external evidence."""
    source_kind: str          # "akos" | "research"
    source_ref: str           # path or brief coordinate -- the lineage anchor
    title: str
    text: str
    domain: str = ""


@dataclass
class CapabilityProposal:
    """A mined capability, pre-approval. Deliberately NOT a contract: it has no
    owner, so it cannot be activated, ranked as live, or saved by accident."""
    proposal_id: str
    name: str
    claim: str                # the sentence in which the author assumed it
    sovereign_question: str
    # lineage -- source -> evidence -> claim -> proposal (traceable, HR-01)
    source_kind: str
    source_ref: str
    source_title: str
    # overlap audit
    disposition: str          # "CANDIDATE" | "OWNED"
    parent_id: str = ""
    parent_name: str = ""
    coverage_pct: int = 0
    recommended_operation: str = ""
    recommended_artifact: str = ""
    triggers: list = field(default_factory=list)
    mined_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def lineage(self) -> list:
        """The genealogy the brief demands: no capability without a traceable
        path back to the source that produced it."""
        return [f"{self.source_kind}:{self.source_ref}",
                f"evidence:{self.source_title}",
                f"claim:{self.claim[:60]}",
                f"proposal:{self.proposal_id}"]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(p: Path) -> str:
    try:
        if not p.is_file() or p.stat().st_size > _MAX_FILE_BYTES:
            return ""
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Evidence intake -- reuse only. Acquires nothing (HR-UCEIMR-02).
# ---------------------------------------------------------------------------
def evidence_from_akos(brief_path=None) -> list:
    """Every unit in the AKOS brief -- not the six the JIT injector selects.
    The injector picks for a prompt; mining wants the corpus. Fail-open -> []."""
    out: list = []
    try:
        from modules.akos_knowledge.akos import find_brief, parse_brief
        p = Path(brief_path) if brief_path else find_brief(_PP_ROOT)
        if p is None:
            return out
        for u in parse_brief(_read(Path(p))):
            body = f"{u.title}. {u.snippet}".strip()
            if len(body) < _MIN_CLAIM_CHARS:
                continue
            out.append(EvidenceUnit(
                source_kind="akos",
                source_ref=f"{Path(p).name}#{u.domain}.{u.index}",
                title=u.title, text=body, domain=u.domain))
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return out
    return out


def evidence_from_research(research_dir=None) -> list:
    """autoresearch / crawl writeback already on disk. Fail-open -> []."""
    out: list = []
    try:
        base = Path(research_dir) if research_dir else _PP_ROOT / "vault" / "research"
        paths = sorted(base.glob("*.md"))[:_MAX_FILES]
    except OSError:
        return out
    for p in paths:
        text = _read(p)
        if len(text) < _MIN_CLAIM_CHARS:
            continue
        title = p.stem
        for line in text.split("\n", 40)[:40]:
            if line.startswith("# "):
                title = line[2:].strip() or title
                break
        out.append(EvidenceUnit(source_kind="research", source_ref=str(
            p.relative_to(_PP_ROOT)) if str(p).startswith(str(_PP_ROOT)) else str(p),
            title=title, text=text))
    return out


def evidence_from_corpus(corpus_dir) -> list:
    """Authored external text (transcripts, articles, threads) at FULL length.

    Measured 2026-08-04: the two stores above yield zero capability claims.
    AKOS persists a ~220-char lead per unit -- enough to route a prompt, far
    too little to mine -- and `vault/research/` holds the estate's OWN notes,
    which are markdown ABOUT work rather than an author's standing practice.
    `enricher.py` fetches transcripts with yt-dlp at runtime and never writes
    them down, so nothing on disk carries the text mining needs.

    That is a real upstream gap, not a reason to loosen the extractor until it
    manufactures proposals. This entry point is the honest answer: point the
    miner at authored corpus wherever it lands, today or later.

    Fail-open -> [].
    """
    out: list = []
    try:
        base = Path(corpus_dir)
        paths = sorted([q for pat in ("*.txt", "*.md", "*.vtt")
                        for q in base.glob(pat)])[:_MAX_FILES]
    except (OSError, TypeError):
        return out
    for p in paths:
        text = _read(p)
        if len(text) < _MIN_CLAIM_CHARS:
            continue
        out.append(EvidenceUnit(source_kind="corpus", source_ref=str(p),
                                title=p.stem, text=text))
    return out


def load_evidence(brief_path=None, research_dir=None, corpus_dir=None) -> list:
    units = evidence_from_akos(brief_path) + evidence_from_research(research_dir)
    if corpus_dir:
        units += evidence_from_corpus(corpus_dir)
    return units


# ---------------------------------------------------------------------------
# Claim extraction -- a surfacer, not a judge.
# ---------------------------------------------------------------------------
def extract_claims(unit: EvidenceUnit) -> list:
    """Sentences in which the author ASSUMES a standing capability.

    Three conditions, all required. Measured on the real corpus (138 units):
    verb-plus-object alone yielded 176 claims of which almost none were
    capability assumptions -- they were markdown fragments from the estate's
    own notes. Precision, not recall, is what makes this surface usable: a
    miner that floods the Owner with 148 proposals has produced capability
    inflation, which is the failure mode DS14 of the source brief names.

      1. STRUCTURE  -- authored prose, not a bullet / heading / quote / code
                       line. Those are notes ABOUT work, not claims BY an
                       author.
      2. VERB       -- a capability verb. A sentence without one states a
                       fact, not a capability.
      3. HABITUAL   -- a standing-practice marker ("I always", "you need to",
                       "siempre"). This is the actual UCEIMR signal: the
                       author treats the capability as a given. Without it a
                       capability verb is just narration.
    """
    claims: list = []
    try:
        sentences = _SENT_SPLIT.split(unit.text or "")[:_MAX_SENTENCES_PER_UNIT]
    except Exception:  # noqa: BLE001
        return claims
    for raw in sentences:
        s = " ".join(str(raw).split())
        if not (_MIN_CLAIM_CHARS <= len(s) <= _MAX_CLAIM_CHARS):
            continue
        if _is_structural(s):
            continue
        low = s.lower()
        words = _WORD.findall(low)
        if not words:
            continue
        if not any(v in words or v in low for v in _CAPABILITY_VERBS):
            continue
        if not any(m in low for m in _HABITUAL):
            continue
        # Object test: content words beyond the verb itself.
        content = [w for w in words if w not in _CAPABILITY_VERBS and len(w) > 3]
        if len(content) < 3:
            continue
        claims.append(s)
        if len(claims) >= _MAX_CLAIMS_PER_UNIT:
            break
    return claims


def _name_for(claim: str) -> str:
    words = _WORD.findall(claim)
    verb = next((w for w in words if w.lower() in _CAPABILITY_VERBS), "")
    objs = [w for w in words if len(w) > 4 and w.lower() not in _CAPABILITY_VERBS]
    parts = ([verb.capitalize()] if verb else []) + [w.lower() for w in objs[:3]]
    return " ".join(parts).strip() or (claim[:40] + "...")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return (s[:48] or "capability")


# ---------------------------------------------------------------------------
# The pipeline.
# ---------------------------------------------------------------------------
def mine_unit(unit: EvidenceUnit) -> list:
    """One evidence unit -> zero or more overlap-audited proposals."""
    from modules.duplicate_to_advantage.d2a_engine import Proposal, run

    out: list = []
    for claim in extract_claims(unit):
        name = _name_for(claim)
        try:
            v = run(Proposal(description=claim, name=name))
            dupe = v.dupe
            rec_op = v.recommended.operation if v.recommended else ""
            rec_art = v.contract.artifact if v.contract else ""
        except Exception:  # noqa: BLE001 -- an audit failure must not lose the
            # claim silently; surface it as UNAUDITED rather than as a candidate.
            out.append(CapabilityProposal(
                proposal_id=f"{_slug(name)}__{_slug(unit.source_ref)[:16]}",
                name=name, claim=claim,
                sovereign_question=f"Can this estate {name.lower()}?",
                source_kind=unit.source_kind, source_ref=unit.source_ref,
                source_title=unit.title, disposition="UNAUDITED",
                mined_at=_now()))
            continue
        # Three outcomes, not two. `deferred` means d2a's plausibility floor
        # CAPPED coverage: a parent's vocabulary matched but precision was too
        # low to name it. Reading that cap as "genuinely new" is exactly the
        # defect d2a already sealed (V-D2A-FAMILY-DEFER-NOT-KEEP) -- a
        # 45%-capped candidate is UNKNOWN ownership, never novelty.
        if bool(dupe.parent_id) and dupe.coverage_pct >= OWNED_COVERAGE_PCT:
            disposition = "OWNED"
        elif getattr(dupe, "deferred", False):
            disposition = "DEFER"
        else:
            disposition = "CANDIDATE"
        out.append(CapabilityProposal(
            proposal_id=f"{_slug(name)}__{_slug(unit.source_ref)[:16]}",
            name=name, claim=claim,
            sovereign_question=f"Can this estate {name.lower()}?",
            source_kind=unit.source_kind, source_ref=unit.source_ref,
            source_title=unit.title,
            disposition=disposition,
            parent_id=dupe.parent_id, parent_name=dupe.parent_name,
            coverage_pct=dupe.coverage_pct,
            recommended_operation=rec_op, recommended_artifact=rec_art,
            triggers=sorted({w.lower() for w in _WORD.findall(name)
                             if len(w) > 4})[:6],
            mined_at=_now()))
    return out


def mine(units=None, *, limit: int = 0, brief_path=None,
         research_dir=None, corpus_dir=None) -> list:
    """Mine evidence into overlap-audited capability proposals, strongest
    novelty first. Fail-open: a bad unit is skipped, never fatal."""
    src = (units if units is not None
           else load_evidence(brief_path, research_dir, corpus_dir))
    out: list = []
    seen = set()
    for u in src:
        try:
            for p in mine_unit(u):
                if p.proposal_id in seen:
                    continue
                seen.add(p.proposal_id)
                out.append(p)
        except Exception:  # noqa: BLE001
            continue
    # CANDIDATE first, then DEFER (unknown ownership), then OWNED; within each,
    # least-covered first -- the least owned claim is the most informative one
    # to show the Owner.
    rank = {"CANDIDATE": 0, "DEFER": 1, "UNAUDITED": 2, "OWNED": 3}
    out.sort(key=lambda p: (rank.get(p.disposition, 4), p.coverage_pct, p.name))
    return out[:limit] if limit and limit > 0 else out


def save_proposal(p: CapabilityProposal, proposals_dir=None) -> Path:
    base = Path(proposals_dir) if proposals_dir is not None else PROPOSALS_DIR
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{p.proposal_id}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(p.to_dict(), indent=2, ensure_ascii=False),
                   encoding="utf-8")
    tmp.replace(path)
    return path


def load_proposals(proposals_dir=None) -> list:
    base = Path(proposals_dir) if proposals_dir is not None else PROPOSALS_DIR
    out: list = []
    try:
        paths = sorted(base.glob("*.json"))
    except OSError:
        return out
    known = set(CapabilityProposal.__dataclass_fields__)
    for p in paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
            out.append(CapabilityProposal(**{k: v for k, v in d.items()
                                             if k in known}))
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    return out


def approve(p: CapabilityProposal, owner: str, *, consumers=None,
            contracts_dir=None, save: bool = True):
    """Owner-gated promotion: proposal -> CapabilityContract.

    Fail-CLOSED. An OWNED proposal is refused outright (HR-UCEIMR-03 -- the
    overlap audit already named a parent), a DEFER is refused because its
    ownership is UNKNOWN rather than absent, and an empty owner or consumer set
    is refused by the contract's own HR-APA-018 / HR-APA-006 validation. There
    is deliberately no auto-approve path: the miner may not admit its own
    capabilities.
    """
    if p.disposition == "OWNED":
        raise ContractError(
            f"HR-UCEIMR-03 {p.proposal_id}: already owned by "
            f"{p.parent_id} at {p.coverage_pct}% -- extend that owner instead")
    if p.disposition == "DEFER":
        raise ContractError(
            f"HR-UCEIMR-03 {p.proposal_id}: ownership UNKNOWN -- d2a capped "
            f"coverage at {p.coverage_pct}% against {p.parent_id or 'a parent'} "
            "without confidently naming it. Resolve ownership before approving")
    if not str(owner).strip():
        raise ContractError(
            f"HR-APA-018 {p.proposal_id}: approval requires an owner")
    cons = [c for c in (consumers or []) if str(c).strip()] or ["Owner"]
    c = CapabilityContract(
        id=p.proposal_id, name=p.name, owner=str(owner).strip(),
        sovereign_question=p.sovereign_question,
        scope=[p.name.lower()],
        non_scope=([f"the ground {p.parent_id} already owns"]
                   if p.parent_id else []),
        triggers=p.triggers or [w.lower() for w in _WORD.findall(p.name)][:4],
        inputs=[f"{p.source_kind} evidence"],
        outputs=[f"{p.name} verdict"], consumers=cons,
        maturity="experimental",
        retirement_condition=(
            f"the claim behind it is contradicted, or {p.parent_id or 'an owner'} "
            "absorbs this ground"),
        parent=p.parent_id or "",
    )
    if save:
        save_contract(c, contracts_dir)
    return c


def render(proposals: list, *, show: int = 12) -> str:
    lines = []
    counts: dict = {}
    for p in proposals:
        counts[p.disposition] = counts.get(p.disposition, 0) + 1
    lines.append(f"mined {len(proposals)} claim(s): "
                 + (", ".join(f"{n} {k}" for k, n in sorted(counts.items()))
                    or "none"))
    for p in proposals[:show]:
        tag = (f"{p.disposition} ({p.parent_id} {p.coverage_pct}%)"
               if p.parent_id else p.disposition)
        lines.append(f"  [{tag}] {p.name}")
        lines.append(f"      claim:   {p.claim[:110]}")
        lines.append(f"      lineage: {' -> '.join(p.lineage())}")
    if len(proposals) > show:
        lines.append(f"  ... {len(proposals) - show} more (not truncated on disk)")
    lines.append("propose-only: nothing is activated until "
                 "`--approve <id> --owner <path>`")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Mine already-acquired evidence into capability proposals")
    ap.add_argument("--mine", action="store_true", help="run the miner")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--brief", default=None)
    ap.add_argument("--research-dir", default=None)
    ap.add_argument("--corpus-dir", default=None,
                    help="authored external text (.txt/.md/.vtt) to mine")
    ap.add_argument("--proposals-dir", default=None)
    ap.add_argument("--save", action="store_true", help="persist proposals")
    ap.add_argument("--list", action="store_true", help="list saved proposals")
    ap.add_argument("--approve", default="", metavar="PROPOSAL_ID")
    ap.add_argument("--owner", default="", help="required with --approve")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.approve:
        by_id = {p.proposal_id: p for p in load_proposals(args.proposals_dir)}
        p = by_id.get(args.approve)
        if p is None:
            print(f"no such proposal: {args.approve}")
            return 1
        try:
            c = approve(p, args.owner)
        except ContractError as e:
            print(f"REFUSED: {e}")
            return 1
        print(f"approved -> contract {c.id} (owner={c.owner})")
        return 0

    if args.list:
        ps = load_proposals(args.proposals_dir)
        print(render(ps) if ps else "no saved proposals")
        return 0

    ps = mine(limit=args.limit, brief_path=args.brief,
              research_dir=args.research_dir, corpus_dir=args.corpus_dir)
    if args.save:
        for p in ps:
            save_proposal(p, args.proposals_dir)
    if args.json:
        print(json.dumps([p.to_dict() for p in ps], indent=2,
                         ensure_ascii=False))
    else:
        print(render(ps))
    return 0


__all__ = [
    "EvidenceUnit", "CapabilityProposal", "PROPOSALS_DIR",
    "OWNED_COVERAGE_PCT", "evidence_from_akos", "evidence_from_research",
    "load_evidence", "extract_claims", "mine_unit", "mine", "approve",
    "save_proposal", "load_proposals", "render",
]

if __name__ == "__main__":
    raise SystemExit(main())
