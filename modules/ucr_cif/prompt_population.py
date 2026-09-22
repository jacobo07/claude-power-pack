"""UCR-CIF W7 -- the real prompt population, and the activation funnel.

The reach question cannot be answered from synthetic prompts: a hand-made
set can only express the states its author already believes in, and the
author here also wrote the thing being measured. So the population is the
estate's OWN `UserPromptSubmit` history -- the exact pair the live signal
sees, `(prompt text, cwd)` -- replayed through the REAL
`classify_tier` / `check_spec_gate` / `sdd_tier.evaluate`, never through a
model of them.

PRIVACY BOUNDARY (Owner decision 4, capture=C; brief sec. IX).
Prompt text is read from disk, held transiently in memory, classified, and
DISCARDED. It is never returned by the public API, never written to any
artifact, and never rendered. What survives is derived and typed: a digest
for dedup, a length bucket, the tier verdict, the gate action, the owner
PATHS routed (already public repository paths), a semantic class and a
coarse date. No text, no absolute host path, no session content. A caller
that wants the text has the transcript; the institution inherits the
lesson, not the evidence payload.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
It does not decide relevance. Whether an owner SHOULD have been shown is
ground truth and must not be answered by any component of the trigger it
is grading; that lives in `reach_ground_truth`.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

PP_ROOT = Path(__file__).resolve().parents[2]

#: Where Claude Code keeps this host's session transcripts.
TRANSCRIPT_ROOT = Path(os.path.expanduser("~/.claude/projects"))

#: Prefixes that mark machine-authored text inside a `user` record. These
#: are not prompts: they are reminders, command echoes, tool output and
#: interrupt markers that the harness files under the user's role. Counting
#: them would inflate the denominator with text no human ever typed.
_NOT_A_PROMPT = (
    "<system-reminder>", "<local-command-stdout>", "<command-name>",
    "<command-message>", "<command-args>", "[Request interrupted",
    "Caveat: The messages below were generated",
    "<local-command-caveat>", "API Error", "<bash-stdout>",
    "<user-prompt-submit-hook>",
)

#: Reporting-only semantic classes. NOT a routing input and never consulted
#: by any gate -- they exist so the funnel can be read per kind of work
#: instead of as one average. Ordered: first match wins, most specific
#: first. Derived from the estate's own vocabulary rather than invented.
_SEMANTIC_CLASSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("investigation", ("audit", "investigate", "analyse", "analyze",
                       "measure", "why does", "why is", "diagnose",
                       "forensic", "explain")),
    ("repair", ("fix", "bug", "broken", "error", "fails", "failing",
                "crash", "regression", "repair")),
    ("refactor", ("refactor", "rename", "clean up", "simplify",
                  "deduplicate", "restructure")),
    ("extend", ("extend", "add to", "improve", "enhance", "widen",
                "expand", "continue")),
    ("create", ("create", "build", "implement", "new ", "scaffold",
                "bootstrap", "from scratch", "design")),
    ("integrate", ("integrate", "wire", "connect", "hook up", "absorb")),
    ("verify", ("test", "verify", "validate", "prove", "gate", "check")),
    ("document", ("document", "readme", "write up", "changelog",
                  "handoff", "summar")),
    ("deploy", ("deploy", "ship", "release", "publish", "commit",
                "push")),
)

_SLASH = re.compile(r"^\s*/[a-z0-9][\w:-]*", re.IGNORECASE)


@dataclass
class DerivedCase:
    """One replayed `UserPromptSubmit`, with no prompt text in it."""

    prompt_sha: str
    n_chars: int
    length_bucket: str
    date: str                      # YYYY-MM-DD, coarse on purpose
    session_sha: str
    cwd_group_id: str
    cwd_name: str
    semantic_class: str
    is_slash_command: bool
    # --- funnel stages, each from the REAL production function ---
    tier: int = -1
    tier_size: str = ""
    tier_signal: str = ""          # the keyword that decided the tier
    reached_tier2: bool = False
    cwd_spec_present: bool | None = None
    gate_action: str = ""
    selector_consulted: bool = False
    owners_routed: list[str] = field(default_factory=list)
    #: W10. The ranked owner names BEFORE `[:MAX_OWNERS]`. Carried so rank
    #: quality and cap survival can be read as two effects rather than one:
    #: `owners_routed` is what the agent saw, this is what the ranking
    #: actually decided, and an eviction is the difference between them.
    precap_owners: list[str] = field(default_factory=list)
    owner_units: int = 0
    signal_emitted: bool = False
    signal_named_owners: bool = False
    miss_layer: str = ""
    # --- independent relevance oracle (see reach_ground_truth) ---
    #: POST-HOC label from the engineer's own later commits. Never derived
    #: from the trigger or the selector.
    gt_label: str = ""
    gt_owner_hits: list[str] = field(default_factory=list)
    error: str | None = None


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def _bucket(n: int) -> str:
    for edge, label in ((80, "xs"), (300, "s"), (1200, "m"),
                        (5000, "l")):
        if n < edge:
            return label
    return "xl"


def semantic_class(text: str) -> str:
    """Coarse intent family, for reading the funnel per kind of work.

    Scores every class and takes the strongest, rather than returning the
    first table entry that matches. Measured 2026-09-21: first-match-wins
    put 100 of 127 Tier>=2 prompts into `investigation`, because its
    needles ("explain", "analyse", "measure", "why is") appear somewhere in
    almost any long prompt and it happened to sit first. A classifier whose
    answer is decided by table order is reporting its own layout.

    Ties break on table order, which is specific-before-general, so the
    ordering still carries meaning -- it is just no longer sufficient on
    its own.
    """
    low = text.lower()
    best_name, best_score, best_rank = "unclassified", 0, len(_SEMANTIC_CLASSES)
    for rank, (name, needles) in enumerate(_SEMANTIC_CLASSES):
        score = sum(1 for n in needles if n in low)
        if score > best_score or (score == best_score and score > 0
                                  and rank < best_rank):
            best_name, best_score, best_rank = name, score, rank
    return best_name


def _user_text(obj: dict) -> str | None:
    """Return the human-authored text of a `user` record, or None.

    Returns None -- rather than an empty string -- for every machine-filed
    record, so 'no human text' and 'a human typed nothing' stay different
    facts at the call site.
    """
    if obj.get("type") != "user" or obj.get("isMeta"):
        return None
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None
    content = msg.get("content")
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
    text = "\n".join(p for p in parts if p).strip()
    if not text:
        return None
    if text.startswith(_NOT_A_PROMPT):
        return None
    return text


def iter_sessions(root: Path = TRANSCRIPT_ROOT,
                  limit: int | None = None,
                  seed: int = 20260921) -> list[Path]:
    """Sample session transcripts, reproducibly.

    Sampled without replacement from the whole store rather than taking the
    newest N: the newest sessions are this mission's own, and a population
    made of them would measure UCR-CIF work and call it ordinary
    engineering.
    """
    if not root.exists():
        return []
    files = sorted(root.glob("*/*.jsonl"))
    if limit is None or limit >= len(files):
        return files
    rng = random.Random(seed)
    return sorted(rng.sample(files, limit))


def iter_prompts(sessions: list[Path]) -> Iterator[tuple[str, str, str, str]]:
    """Yield `(text, cwd, session_id, timestamp)` for real user prompts.

    Streams line by line. The full store is 3.5 GB on this host and must
    never be materialised -- not into a list, and certainly not into model
    context.
    """
    for path in sessions:
        try:
            handle = path.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                if '"type":"user"' not in line and '"type": "user"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, TypeError):
                    continue
                text = _user_text(obj)
                if text is None:
                    continue
                yield (text, obj.get("cwd") or "",
                       str(obj.get("sessionId") or path.stem),
                       str(obj.get("timestamp") or ""))


__all__ = [
    "TRANSCRIPT_ROOT", "DerivedCase", "iter_prompts", "iter_sessions",
    "semantic_class",
]
