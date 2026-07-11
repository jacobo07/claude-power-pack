#!/usr/bin/env python3
"""question_harvester.py -- FIOS I-4 Candidate-Question Harvester (FD-02's intake).

Session #1 exposed the pipeline's one empty stage: the compiler RANKS candidate
questions (FD-00 admission + FD-02 leverage axes) but nothing GENERATES them --
SESSION_ZERO_2026-07-10T162015Z shipped with 0 candidates. This module fills that
stage deterministically: it mines candidate questions from state the stack
ALREADY records, so a frontier session never launches with an empty portfolio
(PR-HARVEST-BEFORE-FRONTIER-001).

It COMPOSES, never re-implements (FD-07 I.4 anti-duplication):
  - FD-07 deposits ledger (`_load_deposits`) -- every unproven-portability deposit
    becomes an FD-04 downgrade-test question (Session #1's 7 deposits are Session
    #2's agenda by construction).
  - D4 OWNER_QUEUE (`owner_queue.pending`) -- every stale residual becomes a
    "retire the class, not the instance" architecture question.
  - CO-12 `fd_metrics` -- an instrument-pending loop metric becomes an
    instrumentation-design question.
  - UKDL (`ukdl-universal.md`) -- a trap with no covering PR/HR id becomes a
    hardening question.
  - Vault honest-residual markers -- a declared "Honest residual" becomes a
    permanent-closure question.

Every harvested question carries `source_ref` (auditable provenance),
`expected_asset` (what permanent form the answer must take: hard_rule |
benchmark | asset | dataset_part) and a stable `fingerprint` the session tags
its PM-03 findings with, so FD-07 deposits link back to the question that paid
for them (per-question ROI, read by CO-12/token_irr -- no new metric).

The harvester only PROPOSES: the FD-00 gate remains the sole admission arbiter
(a harvested question the floor already covers is DECLINE'd there, correctly).
Deterministic, zero-model. Fail-open ABSOLUTE: any source error -> that source
contributes nothing; harvest() never raises.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

_MAX_PER_SOURCE = 6            # bounded portfolio: quality over volume (FD-02)
_SNIP_CLAIM = 90               # deposit-claim snippet inside a question
_SNIP_ACTION = 80              # owner-queue action snippet
_SNIP_TITLE = 60               # trap-title snippet
_SNIP_LINE = 70                # residual-line snippet
_MAX_RESIDUAL_FILES = 150      # bounded vault scan
_MAX_FILE_BYTES = 200_000      # skip pathological files
_FP_HEX_LEN = 12               # question fingerprint hex length
_MIN_ID_TOKEN_LEN = 3          # trap/rule id stem-token floor
# Honest-residual markers (the exact vocabulary the SCS notes use).
_RESIDUAL_RE = re.compile(r"(?i)honest residual|owner-side pending|instrument-pending")
# UKDL header ids, e.g. "### UKDL TRAP T-<NAME>-001 -- title" and PR-/HR- rule ids.
_TRAP_HDR_RE = re.compile(r"^#{2,4}\s+UKDL TRAP\s+(T-[A-Z0-9-]+)\s*(?:--|—)?\s*(.*)$")
_RULE_ID_RE = re.compile(r"\b(?:PR|HR)-[A-Z0-9-]+\b")
_GENERIC_ID_TOKENS = {"UKDL", "TRAP", "PR", "HR", "T", "001", "002", "003"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def question_fingerprint(text: str) -> str:
    """Stable ref the session tags PM-03 findings with (FD-07 `question_ref`)."""
    return "q:" + hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()[:_FP_HEX_LEN]


@dataclass
class HarvestedQuestion:
    text: str
    source: str            # deposits | owner_queue | co12 | ukdl_trap | honest_residual
    source_ref: str        # auditable provenance (deposit fp / row id / trap id / file)
    expected_asset: str    # hard_rule | benchmark | asset | dataset_part
    depends_on: str = ""   # fingerprint of a prerequisite question, if any
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = question_fingerprint(self.text)


def _snip(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:n].rstrip()


# --------------------------------------------------------------------------- #
# Source 1 -- FD-07 deposits: unproven portability -> FD-04 downgrade question.
# --------------------------------------------------------------------------- #
def _from_deposits(repo: str, *, state_dir=None, cap: int = _MAX_PER_SOURCE) -> list:
    try:
        from modules.fable_distillation.fd_07_flywheel import _load_deposits
        try:  # FD-04 join surface: a proven deposit stops generating questions
            from modules.fable_distillation.fd_04_prover import proven_fingerprints
            proven = proven_fingerprints(repo, state_dir)
        except Exception:  # noqa: BLE001 -- fail-open: behave as pre-FD-04
            proven = set()
        out = []
        for d in _load_deposits(repo, state_dir):
            if d.get("portability_proven") or d.get("fingerprint") in proven:
                continue
            claim = _snip(d.get("claim", ""), _SNIP_CLAIM)
            if not claim:
                continue
            out.append(HarvestedQuestion(
                text=(f"Critique the deposited claim '{claim}': under what edge "
                      f"case does it fail, and design the deterministic checklist "
                      f"that reproduces it without a frontier model?"),
                source="deposits",
                source_ref=f"deposit:{d.get('fingerprint', '?')}",
                expected_asset="benchmark"))
            if len(out) >= cap:
                break
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Source 2 -- OWNER_QUEUE residuals: retire the class, not the instance.
# --------------------------------------------------------------------------- #
def _from_owner_queue(*, oq_state_dir=None, cap: int = _MAX_PER_SOURCE) -> list:
    try:
        from modules.owner_queue.owner_queue import pending
        out = []
        for r in pending(oq_state_dir):
            action = _snip(r.get("action", ""), _SNIP_ACTION)
            if not action:
                continue
            out.append(HarvestedQuestion(
                text=(f"Design the permanent system or always-applied general rule "
                      f"that eliminates the entire class of residual '{action}' so "
                      f"it never recurs -- which reusable pattern retires it?"),
                source="owner_queue",
                source_ref=f"owner_queue:{r.get('id', '?')}",
                expected_asset="asset"))
            if len(out) >= cap:
                break
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Source 3 -- CO-12 fd loop metrics: instrument-pending -> instrumentation design.
# --------------------------------------------------------------------------- #
def _from_co12(*, co12_state_dir=None, cap: int = _MAX_PER_SOURCE) -> list:
    try:
        from modules.cognitive_os.co_12_telemetry import fd_metrics
        fd = fd_metrics(state_dir=co12_state_dir)
        out = []
        if not fd.get("measured"):
            out.append(HarvestedQuestion(
                text=("Design the minimal deterministic instrumentation that turns "
                      "the FD loop metrics from instrument-pending into measured -- "
                      "what invariant should each signal verify, and what is the "
                      "general rule for wiring a new one?"),
                source="co12", source_ref="co12:fd_metrics.status",
                expected_asset="benchmark"))
        elif (fd.get("fd_assets_written") or 0) > 0 and not fd.get("fd_portability_proven"):
            out.append(HarvestedQuestion(
                text=("Critique why zero deposits have proven portability: design "
                      "the downgrade-test harness that moves the slope, and under "
                      "what edge case would it lie?"),
                source="co12", source_ref="co12:fd_portability_proven=0",
                expected_asset="benchmark"))
        return out[:cap]
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Source 4 -- UKDL traps with no covering PR/HR rule -> hardening question.
# --------------------------------------------------------------------------- #
def _id_tokens(ident: str) -> set:
    return {t for t in re.split(r"[-_]", (ident or "").upper())
            if len(t) >= _MIN_ID_TOKEN_LEN and t not in _GENERIC_ID_TOKENS}


def _from_ukdl(*, kb_file=None, cap: int = _MAX_PER_SOURCE) -> list:
    try:
        p = Path(kb_file) if kb_file else (
            _PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md")
        if not p.is_file():
            return []
        traps, rule_ids = [], set()
        for ln in p.read_text(encoding="utf-8-sig", errors="replace").split("\n"):
            m = _TRAP_HDR_RE.match(ln.strip())
            if m:
                traps.append((m.group(1), _snip(m.group(2), _SNIP_TITLE)))
            rule_ids.update(_RULE_ID_RE.findall(ln))
        rule_tok = set()
        for rid in rule_ids:
            rule_tok |= _id_tokens(rid)
        out = []
        for tid, title in traps:
            if _id_tokens(tid) & rule_tok:
                continue                     # a PR/HR shares the trap's stem -> covered
            out.append(HarvestedQuestion(
                text=(f"What always/never rule would structurally prevent trap "
                      f"{tid} ('{title}') at design time, and under what edge case "
                      f"does the current mitigation break?"),
                source="ukdl_trap", source_ref=f"ukdl:{tid}",
                expected_asset="hard_rule"))
            if len(out) >= cap:
                break
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Source 5 -- vault honest-residual markers -> permanent-closure question.
# --------------------------------------------------------------------------- #
def _from_residuals(*, vault_dirs=None, cap: int = _MAX_PER_SOURCE) -> list:
    try:
        dirs = [Path(d) for d in (vault_dirs or (
            _PP_ROOT / "vault" / "knowledge_base", _PP_ROOT / "vault" / "lessons"))]
        out, scanned = [], 0
        for base in dirs:
            if not base.is_dir():
                continue
            for md in sorted(base.glob("*.md")):
                scanned += 1
                if scanned > _MAX_RESIDUAL_FILES or len(out) >= cap:
                    return out
                try:
                    if md.stat().st_size > _MAX_FILE_BYTES:
                        continue
                    text = md.read_text(encoding="utf-8-sig", errors="replace")
                except OSError:
                    continue
                for ln in text.split("\n"):
                    if _RESIDUAL_RE.search(ln):
                        out.append(HarvestedQuestion(
                            text=(f"Architect the permanent closure of the declared "
                                  f"honest residual in {md.name}: "
                                  f"'{_snip(ln, _SNIP_LINE)}' -- what design retires "
                                  f"the manual step for every future session?"),
                            source="honest_residual",
                            source_ref=f"residual:{md.name}",
                            expected_asset="dataset_part"))
                        break                # one question per file, bounded
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Source 6 -- AKOS brief units: domain-matched insight -> operationalize-as-rule.
# The AKOS knowledge store is a 6th natural intake: a domain-relevant unit
# becomes a "how do I apply X to this project" question whose answer must take
# a permanent form (process rule / hard rule). Composes the shared parser
# (modules.akos_knowledge) -- never re-implements brief parsing.
# --------------------------------------------------------------------------- #
def _from_akos(repo: str, *, cap: int = _MAX_PER_SOURCE) -> list:
    try:
        from modules.akos_knowledge.akos import units_for_cwd
        _brief, _domains, units = units_for_cwd(repo or ".")
        out = []
        for u in units:
            title = _snip(re.sub(r"^\d+\s*-\s*", "", getattr(u, "title", "")),
                          _SNIP_TITLE)
            if not title:
                continue
            dom = getattr(u, "domain", "")
            out.append(HarvestedQuestion(
                text=(f"How would you operationalize the AKOS {dom} insight "
                      f"'{title}' as a permanent process rule or hard rule for "
                      f"this project -- what concrete always/never encodes it, "
                      f"and under what edge case would it mislead?"),
                source="akos",
                source_ref=f"akos:{dom}:{title[:40]}",
                expected_asset="hard_rule"))
            if len(out) >= cap:
                break
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# Harvest -- all sources, fingerprint-deduped, bounded.
# --------------------------------------------------------------------------- #
def harvest(repo: str, *, state_dir=None, oq_state_dir=None, co12_state_dir=None,
            kb_file=None, vault_dirs=None,
            max_per_source: int = _MAX_PER_SOURCE) -> list:
    """Mine candidate questions from the five existing sources. Deterministic,
    bounded (max_per_source each), deduped by fingerprint across sources.
    Fail-open ABSOLUTE -> [] (a harvester must never block the session it feeds)."""
    try:
        batches = (
            _from_deposits(repo, state_dir=state_dir, cap=max_per_source),
            _from_owner_queue(oq_state_dir=oq_state_dir, cap=max_per_source),
            _from_co12(co12_state_dir=co12_state_dir, cap=max_per_source),
            _from_ukdl(kb_file=kb_file, cap=max_per_source),
            _from_residuals(vault_dirs=vault_dirs, cap=max_per_source),
            _from_akos(repo, cap=max_per_source),
        )
        seen, out = set(), []
        for batch in batches:
            for q in batch:
                if q.fingerprint in seen:
                    continue
                seen.add(q.fingerprint)
                out.append(q)
        return out
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return []


def as_declaration_questions(questions) -> list:
    """The dict form `SessionDeclaration.candidate_questions` accepts (the compiler
    preserves source_ref/expected_asset/depends_on through ranking)."""
    return [asdict(q) for q in (questions or [])]


def main(argv=None) -> int:
    import argparse
    import os
    ap = argparse.ArgumentParser(
        description="FIOS question harvester -- stack state -> candidate questions")
    ap.add_argument("--repo", default="")
    ap.add_argument("--max-per-source", type=int, default=_MAX_PER_SOURCE)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    qs = harvest(args.repo or os.getcwd(), max_per_source=args.max_per_source)
    if args.json:
        print(json.dumps(as_declaration_questions(qs), ensure_ascii=False, indent=2))
    else:
        for q in qs:
            print(f"  [{q.source}] {q.fingerprint} ({q.expected_asset}) {q.text[:100]}")
        print(f"harvested={len(qs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
