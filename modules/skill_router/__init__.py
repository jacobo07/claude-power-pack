"""Skill Router -- PP Sleepy Skills (frontend pilot).

Sleepy-by-default skill activation: the JIT loader (UserPromptSubmit)
injects a pointer card for the most relevant general skill ONLY when the
prompt's intent clears a confidence threshold. Apollo modules keep their
existing trigger path; this router covers the general skill library.

Public API: build_index, get_frontend_skills, load_cached_index,
classify_domain, SkillEntry.
"""
from .skill_index import (
    SkillEntry,
    build_index,
    classify_domain,
    get_frontend_skills,
    load_cached_index,
)
from .intent_classifier import IntentResult, classify_intent

__all__ = [
    "SkillEntry",
    "build_index",
    "classify_domain",
    "get_frontend_skills",
    "load_cached_index",
    "IntentResult",
    "classify_intent",
]
