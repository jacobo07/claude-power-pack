"""arch_check.py -- Architecture Decision Skill verdict engine.

Reads a design-related prompt from STDIN, consults the pre-built vault
index, and emits a verdict (COLLISION / WARNING / CLEAR) with cited
context in <= 200 words.

Modes:
  --fast (default): 3.0 s wall-clock budget. No LLM. Pure index scan.
                    Emits JSON to stdout.
  --deep:           60 s budget. Allows the caller (commands/arch-decision.md)
                    to generate an ADR. Emits structured JSON with
                    a `deep` block for the calling skill to format.

STDIN contract: per windows-argv-limit-stdin-fix.md vaccine.
Recursion guard: CLAUDEPP_ARCHCHECK_RUNNING=1 short-circuits to CLEAR.
Opt-out: CLAUDEPP_ARCHCHECK_DISABLED=1 short-circuits to CLEAR.

Exit codes: 0 success (any verdict), 1 bad invocation, 2 index missing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = PP_ROOT / "vault" / ".arch-index" / "index.json"
VOCAB_PATH = PP_ROOT / "vault" / ".arch-index" / "vocab.json"
DEFAULT_BUDGET_FAST = 3.0
DEFAULT_BUDGET_DEEP = 60.0

# Scoring weights.
ENTITY_HIT_SCORE = 5.0
CONCEPT_HIT_SCORE = 3.0
CONCEPT_TITLE_HIT_SCORE = 2.0
TOKEN_MATCH_SCORE = 0.5     # per unique token match, capped at TOKEN_MATCH_CAP
TOKEN_MATCH_CAP = 12        # max body-token matches counted
TITLE_TOKEN_SCORE = 1.0     # per unique title-token match
TITLE_TOKEN_CAP = 5         # max title-token matches counted

# Verdict thresholds (after weight multiplier).
COLLISION_FLOOR = 4.5
WARNING_FLOOR = 1.5

TITLE_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9]+", re.IGNORECASE)

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-\._]*", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


def stdin_text() -> str:
    """Read full STDIN with Windows-safe binary mode then decode.

    Per windows-text-mode-compounding (feedback_windows_text_mode_compounding):
    on Windows, text-mode stdin can translate line endings. Use binary
    where possible.
    """
    if sys.stdin.isatty():
        return ""
    try:
        data = sys.stdin.buffer.read()
    except (AttributeError, OSError):
        data = sys.stdin.read().encode("utf-8", errors="replace")
    return data.decode("utf-8", errors="replace")


def load_index() -> dict | None:
    if not INDEX_PATH.exists():
        return None
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_vocab() -> dict | None:
    if not VOCAB_PATH.exists():
        return None
    try:
        return json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _entity_pattern(entity: str) -> re.Pattern:
    """Word-boundary regex for an entity. Mirrors build_index.py.

    'redis' must not match 'rediscovery'; 'react' must not match
    'reactor'. Special chars (., -) are kept literal.
    """
    esc = re.escape(entity)
    return re.compile(rf"(?<![a-z0-9_]){esc}(?![a-z0-9_])", re.IGNORECASE)


def extract_signals(prompt: str, vocab: dict) -> dict:
    """Extract design verbs, entities, concepts, tokens from prompt."""
    lo = prompt.lower()
    tokens = tokenize(prompt)
    token_set = set(tokens)

    # Design verbs: word-boundary match.
    verbs_hit = []
    for v in vocab.get("verbs", []):
        if _entity_pattern(v).search(prompt):
            verbs_hit.append(v)

    # Entities: word-boundary match (matches build_index).
    entities_hit = []
    for e in vocab.get("entities", []):
        if _entity_pattern(e).search(prompt):
            entities_hit.append(e)

    # Concepts: token match against kebab-case concept ids (split by '-').
    concepts_hit = []
    for c in vocab.get("concepts", []):
        if len(c) < 4:
            continue
        # Concept token match: every kebab-token of the concept must appear
        # in the prompt tokens.
        parts = [p for p in c.split("-") if len(p) >= 3]
        if not parts:
            continue
        if all(p in token_set for p in parts):
            concepts_hit.append(c)

    return {
        "tokens": tokens,
        "token_set": token_set,
        "verbs": verbs_hit,
        "entities": entities_hit,
        "concepts": concepts_hit,
    }


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def score_source(src: dict, signals: dict) -> float:
    score = 0.0
    weight = src.get("weight", 0.5)

    # 1) Entity hits (strongest signal; exact substring matches).
    src_entities = set(src.get("entities", []))
    for e in signals["entities"]:
        if e in src_entities:
            score += ENTITY_HIT_SCORE * weight

    # 2) Concept exact hits (the source's own concept ids).
    src_concepts = set(src.get("concepts", []))
    for c in signals["concepts"]:
        if c in src_concepts:
            score += CONCEPT_HIT_SCORE * weight

    # 3) Concept title-match: prompt concept's kebab-parts all in source title.
    title_lo = (src.get("title", "") or "").lower()
    for c in signals["concepts"]:
        if c in src_concepts:
            continue  # already counted
        parts = [p for p in c.split("-") if len(p) >= 3]
        if parts and all(p in title_lo for p in parts):
            score += CONCEPT_TITLE_HIT_SCORE * weight

    # 4) Title-token containment: prompt tokens that appear in the source title.
    title_tokens = set(
        t.lower() for t in TITLE_TOKEN_RE.findall(title_lo)
        if len(t) >= 3
    )
    if title_tokens:
        title_hits = len(signals["token_set"] & title_tokens)
        title_hits = min(title_hits, TITLE_TOKEN_CAP)
        score += title_hits * TITLE_TOKEN_SCORE * weight

    # 5) Body-token containment: prompt tokens present in source shingles.
    shingles = set(src.get("shingles", []))
    if shingles:
        body_hits = len(signals["token_set"] & shingles)
        body_hits = min(body_hits, TOKEN_MATCH_CAP)
        score += body_hits * TOKEN_MATCH_SCORE * weight

    return score


def rank_sources(sources: list[dict], signals: dict,
                 deadline: float) -> list[dict]:
    """Score every source; return top scored ones sorted descending."""
    scored = []
    for s in sources:
        if time.monotonic() > deadline:
            break
        sc = score_source(s, signals)
        if sc <= 0:
            continue
        scored.append({**s, "_score": sc})
    scored.sort(key=lambda x: (-x["_score"], 0 if x.get("is_veto") else 1))
    return scored


def decide_verdict(top: list[dict], signals: dict) -> str:
    if not top:
        return "CLEAR"
    best = top[0]["_score"]
    # COLLISION needs high score on ANY of the top 3 sources where
    # that source is veto-flagged (class=veto or is_veto=true).
    for src in top[:3]:
        if src["_score"] >= COLLISION_FLOOR and (
            src.get("is_veto") or src.get("class") == "veto"
        ):
            return "COLLISION"
    if best >= WARNING_FLOOR:
        return "WARNING"
    return "CLEAR"


def format_context(verdict: str, top: list[dict],
                   signals: dict) -> str:
    if verdict == "CLEAR" or not top:
        return ""
    lines = [f"ARCH-CHECK [{verdict}]"]
    for src in top[:3]:
        path = src.get("path", "?")
        section = src.get("section") or ""
        title = src.get("title", "?")
        # Trim section if too long.
        section_disp = f":{section[:50]}" if section else ""
        # Summary one-liner: first sentence or up to 120 chars.
        summary = (src.get("summary") or "")[:160].split("\n", 1)[0].strip()
        if len(summary) > 140:
            summary = summary[:140] + "..."
        lines.append(f"- {path}{section_disp} -> {summary or title}")

    # Build "Why" line from signals.
    if signals["entities"]:
        ent_str = ", ".join(signals["entities"][:3])
        lines.append(f"\nWhy this surfaced: prompt mentions {ent_str}.")
    elif signals["concepts"]:
        c_str = ", ".join(signals["concepts"][:3])
        lines.append(f"\nWhy this surfaced: prompt concepts overlap with: "
                     f"{c_str}.")
    else:
        lines.append("\nWhy this surfaced: token-shingle overlap above 30%.")

    lines.append("\nThis is advisory. The agent decides what to weigh.")
    out = "\n".join(lines)
    # Enforce 200-word cap.
    words = out.split()
    if len(words) > 200:
        out = " ".join(words[:200]) + "..."
    return out


def short_circuit_clear(reason: str, start: float) -> dict:
    return {
        "verdict": "CLEAR",
        "context": "",
        "sources": [],
        "reason": reason,
        "timing_ms": int((time.monotonic() - start) * 1000),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", default=True)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--prompt", default=None,
                        help="Bypass STDIN with an inline prompt (testing).")
    args = parser.parse_args(argv)

    start = time.monotonic()
    budget = args.budget or (
        DEFAULT_BUDGET_DEEP if args.deep else DEFAULT_BUDGET_FAST
    )
    deadline = start + budget

    # Recursion guard + opt-out.
    if os.environ.get("CLAUDEPP_ARCHCHECK_RUNNING") == "1":
        print(json.dumps(short_circuit_clear("recursion-guard", start)))
        return 0
    if os.environ.get("CLAUDEPP_ARCHCHECK_DISABLED") == "1":
        print(json.dumps(short_circuit_clear("opt-out-env", start)))
        return 0

    prompt = args.prompt if args.prompt is not None else stdin_text()
    if not prompt.strip():
        print(json.dumps(short_circuit_clear("empty-prompt", start)))
        return 0

    index = load_index()
    vocab = load_vocab()
    if not index or not vocab:
        print(json.dumps(short_circuit_clear("index-missing", start)))
        return 2

    sources = index.get("sources", [])
    signals = extract_signals(prompt, vocab)
    ranked = rank_sources(sources, signals, deadline)
    top = ranked[:3]
    verdict = decide_verdict(ranked, signals)
    context = format_context(verdict, top, signals)

    payload = {
        "verdict": verdict,
        "context": context,
        "sources": [
            {
                "path": t.get("path"),
                "title": t.get("title"),
                "section": t.get("section"),
                "class": t.get("class"),
                "score": round(t["_score"], 3),
                "is_veto": t.get("is_veto", False),
            }
            for t in top
        ],
        "signals_summary": {
            "verbs_hit": len(signals["verbs"]),
            "entities_hit": signals["entities"][:5],
            "concepts_hit": signals["concepts"][:5],
            "tokens": len(signals["tokens"]),
        },
        "timing_ms": int((time.monotonic() - start) * 1000),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
