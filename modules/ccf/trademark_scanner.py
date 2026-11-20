"""Trademark Collision Scanner (CCF component #7).

HONEST SCOPE (per vault/plans/CCF_ARCHITECTURE.md §7): this is a first-pass
filter -- phrase/keyword pattern matching against a small, hand-maintained
corpus of well-known marks' shape descriptors. It is NOT a trained visual-
similarity model and NOT a legal trademark-clearance system. Its job is to
catch the specific failure class that CCF-F01 (the Airbnb Belo case)
demonstrated: an icon description that is effectively a textual re-description
of a known mark, even when that mark is never named. Coverage grows via
CCF_KNOWLEDGE_SYSTEMS.md's Trademark Risk Corpus, not by claiming completeness
here.

Verdict semantics: BLOCK halts the concept before it reaches any showcase.
WARN requires an explicit recorded human acknowledgment before the concept
may proceed. PASS still logs the corpus version consulted, so a later corpus
update can retroactively re-flag it (`cpp creative audit`).
"""
from __future__ import annotations

import difflib
import re

BLOCK_THRESHOLD = 0.60
WARN_THRESHOLD = 0.35
CORPUS_VERSION = "1.1"

# Seed entries. Airbnb is mandatory -- it is the founding failure case
# (CCF-F01) this component exists to catch. Additional entries are common
# geometric-mark examples to keep the corpus from being a single-entry gate.
KNOWN_MARKS = {
    "Airbnb": {
        "keywords": ["loop", "ring"],
        "phrases": [
            "a continuous line that loops back on itself",
            "a continuous rounded line that loops back on itself",
            "single continuous loop shape",
        ],
    },
    "Nike": {
        "keywords": ["swoosh", "curve"],
        "phrases": ["a single swoosh curve", "a checkmark-like swoosh"],
    },
    "Apple": {
        "keywords": ["bite", "leaf"],
        "phrases": ["an apple silhouette with a bite taken out and a leaf"],
    },
}


# BCAP2-07 (BR-16): paraphrase recall. Phrase similarity alone scored a literal "check-shaped swoosh"
# PASS. Each known mark lists independent signature GROUPS of whole-word tokens; two distinct groups matched
# is a BLOCK-level signal (one group alone is too common to act on). Still a first-pass filter, not clearance.
SIGNATURES = {
    "Nike": [{"swoosh", "swish", "tick", "checkmark", "check"}, {"curved", "curve", "wing", "sweeping"}],
    "Apple": [{"apple"}, {"bite", "bitten", "leaf"}],
    "Airbnb": [{"loop", "looping", "ring"}, {"continuous", "single-line", "monoline"}, {"pin", "heart", "belo"}],
    "McDonalds": [{"arches", "arch"}, {"golden", "double-arch"}],
    "Target": [{"bullseye", "concentric"}, {"red", "circles", "rings"}],
    "Mercedes": [{"three-pointed", "tri-pointed"}, {"star", "circle", "ring"}],
    "Adidas": [{"stripes", "three-stripe"}, {"diagonal", "mountain", "triangle"}],
    "Twitter": [{"bird", "songbird"}, {"blue", "flying", "perched"}],
}
SIGNATURE_BLOCK = 0.65


def _signature_score(icon_description: str):
    words = set(re.findall(r"[a-z][a-z-]*", (icon_description or "").lower()))
    best, best_mark = 0.0, None
    for mark, groups in SIGNATURES.items():
        hit = sum(1 for g in groups if words & g)
        score = SIGNATURE_BLOCK if hit >= 2 else 0.0
        if score > best:
            best, best_mark = score, mark
    return best, best_mark


def _phrase_similarity(icon_description: str, phrases: list) -> float:
    normalized = icon_description.lower()
    if not phrases:
        return 0.0
    return max(difflib.SequenceMatcher(None, normalized, phrase).ratio() for phrase in phrases)


def scan(concept_id: str, icon_description: str, semantic_avoid: list = None) -> dict:
    """Score one concept's icon description against the known-marks corpus.

    `semantic_avoid` is the list produced by prompt_compiler.extract_semantic_avoid
    -- reused here rather than re-derived, so the scanner sees exactly what the
    Prompt Compiler tagged.
    """
    semantic_avoid = semantic_avoid or []
    keyword_tags = set(semantic_avoid[1:]) if semantic_avoid else set()

    best_score = 0.0
    best_mark = None
    for mark, data in KNOWN_MARKS.items():
        phrase_score = _phrase_similarity(icon_description or "", data["phrases"])
        keyword_overlap = len(keyword_tags & set(data["keywords"]))
        keyword_bonus = min(keyword_overlap * 0.15, 0.3)
        score = min(phrase_score + keyword_bonus, 1.0)
        if score > best_score:
            best_score = score
            best_mark = mark

    sig_score, sig_mark = _signature_score(icon_description)
    if sig_score > best_score:
        best_score, best_mark = sig_score, sig_mark

    if best_score >= BLOCK_THRESHOLD:
        verdict = "BLOCK"
        justification = (
            f"Icon description scores {best_score:.2f} phrase/keyword similarity against "
            f"the known mark '{best_mark}' (threshold {BLOCK_THRESHOLD}). First-pass filter "
            f"only -- not a legal clearance. Respecify the icon direction or add an explicit "
            f"named ban before retrying."
        )
    elif best_score >= WARN_THRESHOLD:
        verdict = "WARN"
        justification = (
            f"Icon description scores {best_score:.2f} similarity against '{best_mark}' "
            f"(threshold {WARN_THRESHOLD}). Below the auto-block line but flagged for human "
            f"review -- proceeding requires an explicit recorded acknowledgment."
        )
    else:
        verdict = "PASS"
        justification = (
            f"No known mark in the corpus (v{CORPUS_VERSION}) scored above {WARN_THRESHOLD}; "
            f"highest was {best_score:.2f} against '{best_mark}'." if best_mark else
            f"No known mark in the corpus (v{CORPUS_VERSION}) matched."
        )

    return {
        "concept_id": concept_id,
        "risk_score": round(best_score, 3),
        "verdict": verdict,
        "justification": justification,
        "nearest_known_mark": best_mark if best_score >= WARN_THRESHOLD else None,
        "corpus_version": CORPUS_VERSION,
    }
