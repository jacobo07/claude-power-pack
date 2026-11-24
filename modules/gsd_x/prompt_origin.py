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
    "another claude session sent a message",          # subagent / peer hand-back, as the transcript renders it
    "<agent-message",                                 # the same hand-back as the hook RECEIVES it (live, 2026-11-22)
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


# ------------------------------------------------------------------ mentions vs requests (T3-CT W3)
# A keyword router reads a word, not a request. Measured 2026-11-22/23: the design router (web) and AKOS grounding
# fired on two 80-103k Owner amendments that only LISTED "website" among artifact types (2e3b8dd4 L2008) or DISCUSSED
# those very false positives (218d8162 L659). Owner text is still the input; what is dropped is a match that the
# surrounding words show to be a mention: quoted, inside talk about routing, or a bare item of an unrelated list.
# Consumers: modules/cdio/design_route.classify, hooks/creative_grounding.js (JS twin, parity V-POP-*).

QUOTES = {'"': '"', "'": "'", "`": "`", "“": "”", "‘": "’", "«": "»"}
META_WINDOW = 200   # chars each side searched for router-talk signals
META_MIN = 2        # distinct signals needed: one stray "false positive" in a web brief must not mute the route
META_RX = re.compile(
    r"false[ -]positives?|falsos? positivos?|\bmatched\b|\bdetector\b|design[ -]rout(?:e|er|ing)|\brouters?\b"
    r"|\bincidental(?:ly)?\b|\bnouns?\b|\bverbs?\b|\bclassifier\b|\btriggered\b|\bfired\b",
    re.I)
LIST_SEP = re.compile(r"[;,\n|•·]")
LIST_FILLER = re.compile(r"^(?:[-*+>\s\d.)]|and\b|or\b|y\b|o\b|e\.g\.|etc\.?|the\b|a\b|an\b|un[ao]?\b|el\b|la\b)+", re.I)
LIST_SPAN = 400     # chars each side searched for sibling items
SHORT_ITEM = 4      # words; a sibling longer than this is prose, not a list item


def _quoted(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    return before in QUOTES and after == QUOTES[before]


def meta_signals(text: str, start: int, end: int) -> list:
    """Distinct router-talk signal FAMILIES within META_WINDOW of a span ("router"/"routers" is one signal)."""
    win = text[max(0, start - META_WINDOW):end + META_WINDOW]
    return sorted({signal_family(m.group(0)) for m in META_RX.finditer(win)})


def signal_family(s: str) -> str:
    """One concept, one signal: lower-case, '-' as ' ', a plural 's' dropped (review of W3, MEDIUM-1)."""
    s = s.lower().replace("-", " ")
    return s[:-1] if s.endswith("s") else s


def _words(s: str) -> list:
    return re.findall(r"[^\W_]+", s)


def _bare(item: str, match: str, request_rx=None) -> bool:
    rest = item.replace(match, " ", 1).strip()
    rest = LIST_FILLER.sub("", rest).strip(" :.!?")
    # "write ads, emails, blog posts": an item that also holds a request word heads a request, it is not a list item.
    if request_rx is not None and request_rx.search(rest):
        return False
    return len(_words(rest)) <= 1


def list_item(text: str, start: int, end: int, same_kind=None, request_rx=None) -> bool:
    """True when the span is a bare item of a list whose sibling items are mostly NOT of the same kind."""
    lo, hi = max(0, start - LIST_SPAN), min(len(text), end + LIST_SPAN)
    left = LIST_SEP.split(text[lo:start])
    right = LIST_SEP.split(text[end:hi])
    item = left[-1] + text[start:end] + right[0]
    if not _bare(item, text[start:end], request_rx):
        return False
    # A line ending in ':' heads the list ("Pages:"); it is not one of its items.
    keep = lambda s: bool(s) and not s.endswith(":")  # noqa: E731
    near = ([s.strip() for s in reversed(left[:-1]) if keep(s.strip())][:2]
            + [s.strip() for s in right[1:] if keep(s.strip())][:2])
    sib = [s for s in near if len(_words(s)) <= SHORT_ITEM]
    if len(sib) < 2:
        return False
    if same_kind is None:
        return True
    kin = sum(1 for s in sib if same_kind.search(s))
    return kin * 2 < len(sib)


def mention_reason(text: str, start: int, end: int, same_kind=None, request_rx=None) -> str:
    """'' when the span reads as a request; else why it is a mention: quoted | meta | list."""
    if _quoted(text, start, end):
        return "quoted"
    if len(meta_signals(text, start, end)) >= META_MIN:
        return "meta"
    if list_item(text, start, end, same_kind, request_rx):
        return "list"
    return ""


def live_matches(rx, text: str, same_kind=None, request_rx=None) -> list:
    """The matches of `rx` in `text` that are not mentions (see mention_reason)."""
    return [m for m in rx.finditer(text or "")
            if not mention_reason(text, m.start(), m.end(), same_kind, request_rx)]
