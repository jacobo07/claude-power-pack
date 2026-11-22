"""Which part of a UserPromptSubmit prompt the Owner wrote.

Text reaches UserPromptSubmit without the Owner typing it: subagent hand-backs, compaction summaries, task
notifications, loaded skill bodies. Measured 2026-11-22 over the design router's live prompts.jsonl (106 routes):
~54 fired on such text (efaae877). The same day the web_surface family baseline fired on a subagent hand-back that
said "hero" and armed a turn-end done-gate on a tooling repo (CDIO tranche 2). One rule, every prompt consumer that
can arm a gate: classify the Owner's words, not the envelope. Owner-typed and pasted text is never filtered.

Consumers: tools/design_route_prompt.py (design router), modules/gsd_x/cli.py (family baselines).
"""
from __future__ import annotations

import re

MACHINE_PREFIXES = (
    "another claude session sent a message",          # subagent / peer hand-back
    "this session is being continued from a previous conversation",  # compaction summary
    "<task-notification>",                            # background task completion
    "base directory for this skill",                  # a loaded skill's body
    "userpromptsubmit hook additional context",       # hook output echoed as a turn
    "caveat: the messages below were generated",      # local-command transcript
)
_LEADING_REMINDERS = re.compile(r"(?s)^\s*(?:<system-reminder[^>]*>.*?</system-reminder>\s*)+")


def owner_text(prompt: str) -> str:
    """The part of a prompt the Owner wrote, or '' when the whole turn is machine-originated."""
    rest = _LEADING_REMINDERS.sub("", prompt or "").lstrip(" \t\r\n\"'")
    low = rest[:200].lower()
    if not rest or any(low.startswith(p) for p in MACHINE_PREFIXES):
        return ""
    return rest


def is_machine_turn(prompt: str) -> bool:
    return bool((prompt or "").strip()) and owner_text(prompt) == ""
