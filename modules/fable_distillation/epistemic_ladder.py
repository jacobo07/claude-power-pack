#!/usr/bin/env python3
"""epistemic_ladder.py -- ACIS-00 derived epistemic level (E0-E7).

The level of a claim is NOT stored; it is DERIVED by reading four artifacts that
already exist -- the FD-07 deposits ledger, the FD-04 proofs ledger, the sealed
UKDL corpus, and the Hard-Rule archive. This module writes nothing, stores
nothing, and emits no new signal (ACIS single-accountant discipline: FD feeds
CO-12, ACIS reads the pipeline, neither forks it).

The No-Autopromotion Invariant (ACIS-00 I.2) is enforced by construction: the
producer of a claim can never certify its level. A deposit -- however confident,
however many probes passed -- caps at E3 unless an artifact authored by a
DIFFERENT actor references it: an Owner-promoted UKDL rule (E4/E5) or a sealed
Hard Rule (E6). Today no sealed rule carries a deposit ref, so every live deposit
resolves to E2 or E3 -- which is the invariant working, not a bug: nothing
autopromotes.

Ladder (ACIS-00 Part I):
  E0 intuition · E1 observation · E2 hypothesis+mechanism (a deposit) ·
  E3 repeated/transferred evidence (a PROVEN probe or attestation) ·
  E4 operational rule (Owner UKDL rule references it) ·
  E5 portable law (E4 + a cross-model proof target) ·
  E6 constitutional invariant (a Hard Rule references it) ·
  E7 meta-generative law (the router itself -- never derived per-claim).

Fail-open ABSOLUTE on every read: an unreadable artifact degrades the level
downward (never upward -- an error must never inflate a claim), never raises.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_04_prover import (  # noqa: E402
    _proofs_path, _read_jsonl, _latest_by_fp)
from modules.fable_distillation.fd_07_flywheel import _load_deposits  # noqa: E402

_CROSS_MODEL = ("mid-model", "small-model")
_UKDL = _PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
_HARD_RULES = _PP_ROOT / "vault" / "hard_rules" / "HARD_RULES.md"


def _refs_for(deposit: dict) -> list:
    """The tokens by which an Owner-authored rule can cite this deposit: its
    fingerprint and the question_ref that paid for it. A rule in the sealed
    corpus containing one of these is the E4+ referent (No-Autopromotion: the
    Owner wrote that rule, not the deposit's producer)."""
    out = []
    for k in ("fingerprint", "question_ref"):
        v = str(deposit.get(k, "") or "").strip()
        if v:
            out.append(v)
    return out


def _corpus_cites(refs: list, path: Path) -> bool:
    """True iff the sealed corpus at `path` cites any ref. Fail-open -> False
    (an unreadable corpus can never RAISE a level -- errors degrade downward)."""
    if not refs:
        return False
    try:
        if not path.is_file():
            return False
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False
    return any(r in text for r in refs)


def _proof_targets(repo: str, fingerprint: str, state_dir=None) -> set:
    """achieved_target set of this fingerprint's PROVEN proof records (empty if
    none / unreadable). Fail-open -> empty (no proof can be inferred on error)."""
    try:
        rec = _latest_by_fp(_read_jsonl(_proofs_path(repo, state_dir))).get(fingerprint)
        if rec and rec.get("verdict") == "PROVEN":
            return {str(rec.get("achieved_target", "") or "")}
    except Exception:  # noqa: BLE001 -- fail-open
        pass
    return set()


def epistemic_level(fingerprint: str, repo: str, *, state_dir=None) -> str:
    """Derive the E-level of a deposited claim. Reads deposits + proofs + UKDL +
    Hard Rules; writes nothing. Caps at E3 without an Owner-authored referent
    (the No-Autopromotion Invariant). Returns 'E0'..'E6' ('E7' is the router, never
    a per-claim result). Fail-open -> the lowest level the evidence proves."""
    try:
        deposits = {d.get("fingerprint"): d for d in _load_deposits(repo, state_dir)}
        dep = deposits.get(fingerprint)
        if dep is None:
            return "E0"                         # no deposit -> at most an intuition
        # E2 floor: a deposit is a hypothesis with a mechanism (its claim).
        level = "E2" if str(dep.get("claim", "") or "").strip() else "E1"
        targets = _proof_targets(repo, fingerprint, state_dir)
        proven = bool(targets)
        if proven:
            level = "E3"                         # repeated/transferred evidence
        refs = _refs_for(dep)
        # E6: a Hard Rule (constitutional kill-switch) cites this claim.
        if _corpus_cites(refs, _HARD_RULES) or (
                _corpus_cites(refs, _UKDL) and _hardrule_cites(refs)):
            return "E6"
        # E4/E5: an Owner-promoted UKDL rule cites this claim.
        if _corpus_cites(refs, _UKDL):
            # E5 iff the promotion is backed by a cross-model portability proof.
            if proven and (targets & set(_CROSS_MODEL)):
                return "E5"
            return "E4"
        return level                             # capped at E3 -- no rule referent
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE: never inflate on error
        return "E0"


def _hardrule_cites(refs: list) -> bool:
    """A HR-* block inside ukdl-universal.md (the inline Hard-Rule mirror) citing a
    ref. Kept distinct from a plain PR/T citation so a UKDL mention alone is E4,
    not E6."""
    if not refs:
        return False
    try:
        if not _UKDL.is_file():
            return False
        text = _UKDL.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False
    for m in re.finditer(r"^#+\s*HR-[A-Z0-9-]+.*$", text, re.MULTILINE):
        block = text[m.start():m.start() + 1200]
        if any(r in block for r in refs):
            return True
    return False


def theory_maturity(repo: str, *, state_dir=None) -> dict:
    """Derived count of deposited claims by E-level -- the Theory Maturity metric.
    Zero new state, zero new signal: a projection over the deposits ledger. A
    stack whose deposits cluster at E2 has many unproven hypotheses; one that
    climbs to E3+ is converting hypotheses into evidenced capital."""
    counts = {f"E{i}": 0 for i in range(7)}
    try:
        for d in _load_deposits(repo, state_dir):
            fp = d.get("fingerprint")
            if fp:
                counts[epistemic_level(fp, repo, state_dir=state_dir)] += 1
    except Exception:  # noqa: BLE001 -- fail-open
        pass
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="ACIS-00 derived epistemic level (reads the pipeline, writes nothing)")
    ap.add_argument("--repo", default=str(_PP_ROOT))
    ap.add_argument("--level", metavar="FINGERPRINT",
                    help="print the derived E-level of one deposited claim")
    ap.add_argument("--maturity", action="store_true",
                    help="print the Theory Maturity distribution (counts by E-level)")
    args = ap.parse_args(argv)
    if args.level:
        print(epistemic_level(args.level, args.repo))
        return 0
    if args.maturity:
        m = theory_maturity(args.repo)
        print("  ".join(f"{k}={v}" for k, v in m.items()))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
