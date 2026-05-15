"""Hawkins gate — pre-emit gate #3.

Scores a Tier artifact's Markdown body on the Hawkins Map of Consciousness
(20-700+) by counting keyword occurrences across the canonical
EMOTION_TO_HAWKINS table and returning the weighted Hawkins value.

A score < 200 (Coraje) fails the gate. The orchestrator's Reality Contract
targets ≥ 350 (Aceptación) average over a DistillResult.

**Self-contained**: this module vendors the Hawkins doctrine (the table +
the weighted-score math) as plain Python. It does NOT import from
`kobicraft_content_intelligence.consciousness` or any project-side
data_contract — the kernel must keep dep direction sane (PP never depends
on a consumer repo).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

COURAGE_FLOOR: Final[int] = 200
ACCEPTANCE_TARGET: Final[int] = 350

# Canonical Hawkins doctrine — emotion keyword -> (level_name, hawkins_value).
# Mirror of `consciousness/hawkins_mapper.py:EMOTION_TO_HAWKINS` (v220000).
EMOTION_TO_HAWKINS: Final[dict[str, tuple[str, int]]] = {
    "shame": ("shame", 20),
    "guilt": ("guilt", 30),
    "apathy": ("apathy", 50),
    "grief": ("grief", 75),
    "fear": ("fear", 100),
    "desire": ("desire", 125),
    "anger": ("anger", 150),
    "pride": ("pride", 175),
    "courage": ("courage", 200),
    "neutrality": ("neutrality", 250),
    "willingness": ("willingness", 310),
    "acceptance": ("acceptance", 350),
    "reason": ("reason", 400),
    "love": ("love", 500),
    "joy": ("joy", 540),
    "peace": ("peace", 600),
    "nostalgia": ("willingness", 310),
    "excitement": ("joy", 540),
}

# Spanish-friendly synonyms that map onto canonical EMOTION_TO_HAWKINS keys.
_SPANISH_SYNONYMS: Final[dict[str, str]] = {
    # Lower band (negatives) — present for accurate detection of cynical text.
    "verguenza": "shame", "vergüenza": "shame",
    "culpa": "guilt",
    "apatia": "apathy", "apatía": "apathy",
    "duelo": "grief", "tristeza": "grief",
    "miedo": "fear", "panico": "fear", "pánico": "fear",
    "deseo": "desire", "codicia": "desire",
    "ira": "anger", "enfado": "anger", "rabia": "anger",
    "orgullo": "pride", "soberbia": "pride",
    # Upper band (positives) — what KobiiDistillerOS aims for.
    "coraje": "courage", "valentia": "courage", "valentía": "courage",
    "neutralidad": "neutrality",
    "voluntad": "willingness", "disposicion": "willingness", "disposición": "willingness",
    "aceptacion": "acceptance", "aceptación": "acceptance",
    "razon": "reason", "razón": "reason", "lucidez": "reason",
    "amor": "love", "afecto": "love", "cariño": "love",
    "alegria": "joy", "alegría": "joy", "gozo": "joy",
    "paz": "peace", "serenidad": "peace", "calma": "peace",
    "nostalgia": "nostalgia", "hogar": "nostalgia", "refugio": "nostalgia",
    "ilusion": "excitement", "ilusión": "excitement", "emocion": "excitement",
}


@dataclass(slots=True, frozen=True)
class _EmotionSignal:
    """Internal detection record — one canonical emotion + its confidence."""

    emotion: str
    confidence: float


@dataclass(slots=True, frozen=True)
class _ConsciousnessLevel:
    """Internal scoring record — a Hawkins level name + value + presence score."""

    level: str
    hawkins_value: int
    score: float


def _scan_emotion_signals(text: str) -> list[_EmotionSignal]:
    """Count keyword occurrences and emit one signal per detected canonical emotion."""
    lowered = text.lower()
    counts: dict[str, int] = {}

    for emotion_key in EMOTION_TO_HAWKINS:
        pattern = r"\b" + re.escape(emotion_key) + r"\b"
        hits = len(re.findall(pattern, lowered))
        if hits:
            counts[emotion_key] = counts.get(emotion_key, 0) + hits

    for es_word, canonical in _SPANISH_SYNONYMS.items():
        pattern = r"\b" + re.escape(es_word) + r"\b"
        hits = len(re.findall(pattern, lowered))
        if hits:
            counts[canonical] = counts.get(canonical, 0) + hits

    if not counts:
        return []

    total = sum(counts.values())
    signals: list[_EmotionSignal] = []
    for emotion, n in counts.items():
        share = n / total
        confidence = min(0.5 + share * 0.5, 0.95)
        signals.append(_EmotionSignal(emotion=emotion, confidence=confidence))
    return signals


def _map_signals_to_levels(signals: list[_EmotionSignal]) -> list[_ConsciousnessLevel]:
    """Dedup signals by Hawkins level, summing confidence (cap at 1.0)."""
    level_scores: dict[str, float] = {}
    level_values: dict[str, int] = {}
    for sig in signals:
        mapping = EMOTION_TO_HAWKINS.get(sig.emotion)
        if mapping is None:
            continue
        level_name, hawkins_value = mapping
        level_scores[level_name] = min(level_scores.get(level_name, 0.0) + sig.confidence, 1.0)
        level_values[level_name] = hawkins_value
    levels = [
        _ConsciousnessLevel(level=name, hawkins_value=level_values[name], score=round(score, 4))
        for name, score in level_scores.items()
    ]
    levels.sort(key=lambda lv: lv.hawkins_value, reverse=True)
    return levels


def _weighted_score(levels: list[_ConsciousnessLevel]) -> float:
    """Weighted-average Hawkins value across levels, capped at 1000."""
    if not levels:
        return 0.0
    total_weight = sum(lv.score for lv in levels)
    if total_weight == 0:
        return 0.0
    weighted = sum(lv.score * lv.hawkins_value for lv in levels)
    result = weighted / total_weight
    return round(min(result, 1000.0), 2)


def evaluate(text: str) -> int:
    """Return the weighted Hawkins score (0-1000) for the given Markdown body."""
    signals = _scan_emotion_signals(text)
    if not signals:
        # No detectable emotion content: treat as neutral baseline (Coraje floor).
        return COURAGE_FLOOR
    levels = _map_signals_to_levels(signals)
    return int(round(_weighted_score(levels)))


def passes(text: str, floor: int = COURAGE_FLOOR) -> bool:
    """True if the text scores at or above the given Hawkins floor."""
    return evaluate(text) >= floor


__all__ = [
    "COURAGE_FLOOR",
    "ACCEPTANCE_TARGET",
    "EMOTION_TO_HAWKINS",
    "evaluate",
    "passes",
]
