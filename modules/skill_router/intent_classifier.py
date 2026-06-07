#!/usr/bin/env python3
"""Intent Classifier -- PP Sleepy Skills (skill_router).

Decides whether a prompt should wake a general skill, and which one(s).
Token-efficient: pure pattern matching + scoring, NO LLM call. Runs on
the UserPromptSubmit hot path (via jit_skill_loader), so it must be fast
and must NOT read skill files itself -- the candidate pool of
``SkillEntry`` is passed in by the caller (from a cached index).

Scoring (per domain, word-boundary matched):
  * any negative signal present  -> domain disqualified (hard veto)
  * >=1 strong signal            -> 0.85
  * >=2 medium signals           -> 0.65
  * exactly 1 medium signal      -> 0.45  (detected, but below wakeup)

A prompt wakes a skill iff confidence >= WAKEUP_THRESHOLD (0.6) AND at
least one candidate skill in the matched domain exists. Context above
CONTEXT_SLEEP_PCT forces every skill asleep (token austerity).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .skill_index import SkillEntry

WAKEUP_THRESHOLD = 0.6
CONTEXT_SLEEP_PCT = 0.75
MAX_SKILLS = 2

# Per-domain intent signals. Tuned for EN + ES (Owner works bilingual).
INTENT_SIGNALS: dict[str, dict[str, tuple[str, ...]]] = {
    "frontend": {
        "strong": (
            "landing page", "react component", "vue component",
            "svelte component", "build a component", "create a component",
            "make it responsive", "tailwind", "shadcn", "framer motion",
            "css animation", "build me a", "create a form", "add styling",
            "make it look", "web page", "html page", "dashboard",
            "artifact", "frontend", "wireframe", "mockup",
            "design system", "hero section", "style the page",
            # ES
            "página de aterrizaje", "componente react", "haz una web",
            "diseña una", "interfaz de usuario",
        ),
        "medium": (
            "button", "form", "layout", "component", "page", "visual",
            "card", "modal", "navbar", "sidebar", "responsive", "css",
            "html", "ui", "ux", "styling", "design", "palette",
            "typography", "animation",
            # ES
            "botón", "formulario", "diseño", "pantalla",
        ),
        "negative": (
            "backend", "database", "sql", "jwt", "api endpoint",
            "deploy", "docker", "kubernetes", "server", "auth token",
            "migration", "webhook", "terraform", "nginx",
            "graphql resolver", "genserver", "stored procedure",
        ),
    },
    "spec": {
        # Large-task / system-build language. These phrases inherently
        # signal L/XL work where a spec (PRD / arch decision / one-shot
        # contract) should precede code. Kept deliberately narrow so
        # small fixes never trip the spec domain.
        "strong": (
            "build a complete", "build a full", "implement a complete",
            "create a system", "design the architecture",
            "write a prd", "prd for", "spec for", "requirements for",
            "architecture for", "refactor the entire", "redesign the",
            "full implementation", "from scratch", "end to end",
            "entire system", "whole system",
            # SDD-OS triggers (PARTE I sec. 4) -- spec-first work.
            "spec-driven", "cross-repo", "for any repo", "new os",
            "universal framework",
            # ES
            "sistema completo", "desde cero", "arquitectura de",
            "implementacion completa", "para cualquier repo",
        ),
        "medium": (
            "architecture", "pipeline", "roadmap", "prd",
            "requirements", "specification", "blueprint",
            # SDD-OS vocabulary -- two of these together wake the domain.
            "framework", "universal", "platform", "governance",
            "standard",
        ),
        "negative": (
            "fix a bug", "fix this", "fix the", "add a test",
            "format", "rename", "comment", "lint", "typo",
            "small change", "quick fix", "one line",
        ),
    },
}


@dataclass
class IntentResult:
    domain: str
    confidence: float
    matching_skills: list[SkillEntry] = field(default_factory=list)
    reasoning: str = ""

    @property
    def should_wakeup(self) -> bool:
        return (self.confidence >= WAKEUP_THRESHOLD
                and bool(self.matching_skills))


def _present(token: str, text: str) -> bool:
    """Word-boundary presence test -- 'form' must not match 'perform'."""
    return re.search(r"\b" + re.escape(token) + r"\b", text) is not None


def _matches(tokens: tuple[str, ...], text: str) -> list[str]:
    return [t for t in tokens if _present(t, text)]


def _rank_skills(prompt_lower: str, candidates: list[SkillEntry]
                 ) -> list[SkillEntry]:
    """Rank domain candidates by prompt relevance: count of the skill's
    curated keywords present in the prompt, plus a bonus if the skill
    name itself is mentioned."""
    def relevance(skill: SkillEntry) -> tuple[int, int]:
        kw_hits = sum(1 for k in skill.keywords if _present(k, prompt_lower))
        name_bonus = 1 if _present(skill.name.lower(), prompt_lower) else 0
        # Secondary sort key: more curated keywords overall = richer skill.
        return (kw_hits + name_bonus, len(skill.keywords))
    return sorted(candidates, key=relevance, reverse=True)


def classify_intent(prompt: str,
                    available_skills: list[SkillEntry],
                    context_pct: float = 0.0) -> IntentResult:
    """Classify prompt intent and select skills to wake (if any).

    Args:
        prompt: the user's prompt text.
        available_skills: candidate SkillEntry pool (from a cached
            index); this function never reads disk.
        context_pct: fraction of context window used (0.0-1.0). Above
            CONTEXT_SLEEP_PCT, all skills are forced asleep.
    """
    if context_pct > CONTEXT_SLEEP_PCT:
        return IntentResult(
            domain="none", confidence=0.0,
            reasoning=f"context at {context_pct:.0%} -- sleepy mode "
                      f"forced (>{CONTEXT_SLEEP_PCT:.0%})")

    text = (prompt or "").lower()
    if not text.strip():
        return IntentResult(domain="none", confidence=0.0,
                            reasoning="empty prompt")

    best_domain = "none"
    best_score = 0.0
    best_reason = "no domain signal detected"

    for domain, signals in INTENT_SIGNALS.items():
        if _matches(signals.get("negative", ()), text):
            continue  # hard veto
        strong = _matches(signals.get("strong", ()), text)
        if strong:
            score, reason = 0.85, f"strong: {strong[:2]}"
        else:
            medium = _matches(signals.get("medium", ()), text)
            if len(medium) >= 2:
                score, reason = 0.65, f"medium x{len(medium)}: {medium[:3]}"
            elif len(medium) == 1:
                score, reason = 0.45, f"weak: {medium}"
            else:
                continue
        if score > best_score:
            best_score, best_domain, best_reason = score, domain, reason

    if best_domain == "none" or best_score < 0.45:
        return IntentResult(domain="none", confidence=best_score,
                            reasoning=best_reason)

    domain_candidates = [s for s in available_skills
                         if s.domain == best_domain]
    selected = _rank_skills(text, domain_candidates)[:MAX_SKILLS]

    return IntentResult(domain=best_domain, confidence=best_score,
                        matching_skills=selected, reasoning=best_reason)
