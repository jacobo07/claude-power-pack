#!/usr/bin/env python3
"""research_quality.py — prompt builders + deterministic quality gates for
deep_research (Claude Power Pack).

WHY THIS MODULE EXISTS
----------------------
deep_research v0.1.0 shipped the n8n-derived prompts byte-for-byte, with a
code comment declaring them untouchable IP. Three defects followed directly
from that decision, all observed in production output on 2026-07-13:

  1. QUERY SOUP. generate_serp_queries asked for "SERP queries", so the LLM
     returned concatenated technical terms:
         "data mesh product contract semantic layer composable insight
          envelope schema versioning"
     That is a keyword pile, not a question. A human researching this would
     ask "how do data teams stop a schema change from silently breaking
     dashboards" — and get better sources.

  2. CODE IN LEARNINGS. extract_learnings asked to be "as detailed and
     information dense as possible", with no prohibition. The LLM returned
     CLI invocations, YAML fragments and identifiers as if they were the
     insight ("datacontract lint --old ...@main --new ..."). The consumer of
     these learnings is a founder/operator, not a data engineer.

  3. NO RELEVANCE GATE. Every learning was persisted regardless of whether
     anyone in this org could act on it. Irrelevant learnings persisted into
     the vault poison every downstream run that reads them back as context.

This module owns the corrected prompts and the gates that ENFORCE them.
A prompt is a request; a gate is a guarantee. Both are required: the prompt
raises the odds, the gate makes the contract true even when the LLM ignores
the prompt.

DESIGN CONTRACT
---------------
* Every function here is PURE (no network, no LLM, no disk) except
  `log_discarded`, which appends JSONL. That makes the whole quality layer
  unit-testable offline — see test_research_quality.py.
* The code gate is deterministic and therefore CANNOT fail open. The
  relevance gate needs an LLM and therefore CAN be unavailable; its
  unavailability is recorded, never silently ignored (see RELEVANCE_UNRATED).
"""
from __future__ import annotations

import json as _json
import re
from pathlib import Path
from typing import Any

__version__ = "1.0.0"


# =========================================================================
# PART 1 — QUERY GENERATION: natural-language questions, not keyword soup
# =========================================================================

SERP_QUERY_PROMPT = """\
Given the following research topic, generate the search questions a founder \
or operator would actually type into Google, or ask a domain expert over \
coffee.

Return a maximum of {breadth} questions. Return fewer if the topic is \
already clear. Each question must be unique — not a rephrasing of another.

WHAT A GOOD QUESTION LOOKS LIKE:
  - "how do data teams stop a schema change from silently breaking dashboards"
  - "que problemas resuelven los contratos de datos en equipos distribuidos"
  - "what actually goes wrong when two teams define the same metric differently"
  - "how much notice do downstream consumers need before a breaking change"

WHAT IS FORBIDDEN (these produce bad search results, not just ugly ones):
  - Concatenated technical terms with no grammar. BANNED:
    "data mesh product contract semantic layer schema versioning"
  - Tool names or product names used AS the query ("datacontract CLI",
    "Confluent Schema Registry setup")
  - Command-line syntax, flags, file extensions, code, or field names
  - Any string a human would not say out loud

RULES:
  - Write a real question, in grammatical Spanish or English, with the \
function words present ("how", "why", "what happens when", "como", "que", \
"por que", "cuando").
  - Aim at the PROBLEM and its consequences, not at the vocabulary of the \
solution. The vocabulary is what we are trying to discover.
  - The `researchGoal` field explains what you expect to learn and why it \
matters to someone running a business.

<topic>{prompt}</topic>

{learnings_block}"""


# Function words. Their presence is the cheapest reliable signal that a
# string is a sentence and not a pile of nouns. Deliberately small — a
# larger list buys nothing and risks matching a technical term.
_STOPWORDS = frozenset("""
a al algo an and are as at be by can como con cual cuales cuando cuanto de
del do does donde el en es for from ha hacen hacer hay how i in into is
it la las le lo los mas me my no o of on or para pero por porque que quien se
should si sin sobre son su than that the their them there these they this to
un una uno vs was we what when where which who why will with y you
""".split())

# Interrogative / problem-framing markers. Any one of these is sufficient
# proof the LLM wrote a question rather than a keyword pile.
_QUESTION_MARKERS = frozenset("""
como cómo cual cuál cuales cuáles cuando cuándo cuanto cuánto donde dónde por
porque qué que quien quién
can does do how is should what when where which who why
""".split())

# Syntax that must never appear in a search query typed by a human.
_QUERY_BANNED_SYNTAX: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("command-line flag", re.compile(r"(?:^|\s)--?[A-Za-z][\w-]*")),
    ("code fence or backtick", re.compile(r"`")),
    ("search operator", re.compile(r"\b(?:site|filetype|inurl|intitle):")),
    ("file extension", re.compile(r"\.(?:py|js|ts|ex|exs|ya?ml|json|sh|sql)\b")),
    ("code punctuation", re.compile(r"[{}<>|]|\(\)|=>|::")),
)

# A question shorter than this cannot carry a real research intent.
_MIN_QUERY_WORDS = 5
# Below this ratio of function words, and with no interrogative marker, the
# string is a noun pile. Calibrated against the observed bug: the 11-word
# "data mesh product contract semantic layer composable insight envelope
# schema versioning" scores 0.0 — there is not one function word in it.
_MIN_STOPWORD_RATIO = 0.15


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", text.lower(), re.UNICODE)


def is_natural_question(query: str) -> tuple[bool, str]:
    """True iff `query` reads as a question a human would ask.

    Returns (ok, reason). `reason` is empty on success and names the exact
    defect on failure, so the caller can put it in a corrective re-ask and
    in the run metadata.
    """
    q = (query or "").strip()
    if not q:
        return False, "empty query"

    for label, pattern in _QUERY_BANNED_SYNTAX:
        if pattern.search(q):
            return False, f"contains {label} — not something a human types"

    words = _words(q)
    if len(words) < _MIN_QUERY_WORDS:
        return False, (
            f"only {len(words)} words — too short to carry a research "
            f"question (minimum {_MIN_QUERY_WORDS})"
        )

    if any(w in _QUESTION_MARKERS for w in words):
        return True, ""

    stopword_count = sum(1 for w in words if w in _STOPWORDS)
    ratio = stopword_count / len(words)
    if ratio < _MIN_STOPWORD_RATIO:
        return False, (
            f"keyword soup: {len(words)} words, {stopword_count} function "
            f"words (ratio {ratio:.2f} < {_MIN_STOPWORD_RATIO}), no "
            f"interrogative marker — this is a pile of terms, not a question"
        )
    return True, ""


def build_serp_query_prompt(prompt: str, breadth: int,
                            learnings: list[str] | None = None) -> str:
    """Assemble the query-generation user message."""
    learnings = learnings or []
    if learnings:
        block = (
            "These are the learnings already collected. Use them to ask "
            "SHARPER questions — do not re-ask what is already answered:\n"
            + "\n".join(f"- {ln}" for ln in learnings)
        )
    else:
        block = ""
    return SERP_QUERY_PROMPT.format(
        prompt=prompt, breadth=breadth, learnings_block=block
    )


def build_query_correction_prompt(rejected: list[tuple[str, str]],
                                  breadth: int) -> str:
    """Assemble the single corrective re-ask after a keyword-soup rejection.

    Bounded to ONE retry by the caller (Anti-Antipattern Regla 12: a second
    identical failure is a pivot, never a third attempt).
    """
    listing = "\n".join(
        f'  - "{q}"  -> REJECTED: {why}' for q, why in rejected
    )
    return (
        "Your previous queries were rejected by the quality gate because "
        "they are not questions a human would ask:\n\n"
        f"{listing}\n\n"
        f"Rewrite them. Return at most {breadth} questions. Each one must be "
        "a grammatical question in Spanish or English, aimed at the PROBLEM "
        "and its business consequences, containing function words "
        "(how / why / what happens when / como / que / por que). No "
        "concatenated term piles. No tool names as the query. No code, "
        "flags, or file extensions."
    )


# =========================================================================
# PART 2 — LEARNINGS: prose insights, never code
# =========================================================================

LEARNINGS_PROMPT = """\
Given the following contents from a search for <query>{query}</query>, \
extract what a founder or operator should LEARN from them.

Return a maximum of 3 learnings. Return fewer if the contents are thin. Each \
learning must be unique — not a restatement of another.

THE READER: someone who runs a business. They decide where money, people and \
attention go. They are intelligent but they are NOT going to run a command, \
edit a config file, or read a schema. If a learning cannot change a decision \
they make, it is not a learning — it is trivia.

FORBIDDEN IN EVERY LEARNING (a learning containing any of these is discarded \
by an automated gate, so writing one wastes the slot):
  - Code in any language. No YAML, no JSON, no SQL, no shell, no Python.
  - Command-line invocations, flags, or CLI tool syntax.
  - Configuration fragments, schema definitions, or field names \
(order_id, null_rate, PT1H).
  - A tool name presented AS the insight ("use datacontract lint"). Naming a \
tool as evidence of who does what is fine; naming it as the takeaway is not.
  - Implementation steps. WHAT changes and WHY it matters, never HOW to type it.

REQUIRED IN EVERY LEARNING:
  - A complete, self-contained insight, written in plain prose, 1 to 3 \
sentences. No bullets inside a learning.
  - Actionable by a business operator with no prior technical context.
  - The concrete numbers, metrics, dates and named entities (companies, \
people, products) whenever the contents provide them — these are what make a \
learning worth more than an opinion.
  - The CONSEQUENCE, not just the fact. "Teams that skip X lose Y" beats \
"X exists".

GOOD: "Organisations running distributed data teams report that a single \
unannounced schema change can feed wrong revenue numbers to marketing for two \
weeks before anyone notices, because the failure is silent — nothing crashes, \
the dashboard simply lies."

BAD: "Use datacontract lint in CI to check breaking changes before merge."

<contents>
{contents_block}
</contents>"""


# Deterministic code detector. Each entry is (human reason, pattern).
# Calibrated to the observed bug output on 2026-07-13, and deliberately kept
# TIGHT: a false discard destroys a good learning, so every pattern here must
# be something that essentially never appears in business prose. Patterns
# considered and REJECTED for false-positive risk: camelCase (iPhone, eBay),
# bare parentheses (SLA(s)), the word "python" alone (Python 3.11 in prose).
_CODE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("backtick / code fence", re.compile(r"`")),
    ("command-line flag", re.compile(r"(?:^|\s)--[A-Za-z][\w-]*")),
    (
        # A tool name followed by a FLAG or a real SUBCOMMAND. The second
        # token is what separates code from prose: "dbt run" is an
        # invocation, "dbt ya existe" is a Spanish sentence that happens to
        # name a tool. The first version of this rule matched tool +
        # any-lowercase-word and ate exactly that sentence on the 2026-07-13
        # live run (see discarded_learnings.jsonl). Naming a tool as evidence
        # is prose; invoking it is code.
        "CLI tool invocation",
        re.compile(
            r"\b(?:npm|npx|pnpm|pip|pytest|python3?|docker|kubectl|terraform"
            r"|gcloud|mix|dbt|buf|datacontract|helm|psql|curl|wget|ssh"
            r"|chmod|grep|sed|awk)\s+"
            r"(?:-{1,2}\w"
            r"|(?:install|uninstall|run|test|build|exec|compose|apply|start"
            r"|stop|init|add|remove|update|upgrade|deps|lint|breaking"
            r"|migrate|seed|serve|publish|deploy|plan|destroy|config"
            r"|create|delete|describe|list)\b)"
        ),
    ),
    (
        "git subcommand",
        re.compile(
            r"\bgit\s+(?:commit|push|pull|rebase|merge|clone|checkout|reset"
            r"|log|diff|add|status)\b"
        ),
    ),
    (
        "config / schema key-value pair",
        re.compile(
            r"\b[\w.-]+:\s*(?:PT\d|\[|\{|<|v?\d+\.\d+\.\d+|\"|')"
            r"|\bapiVersion\b|\bkind:\s*[A-Z]"
        ),
    ),
    ("ISO-8601 duration literal", re.compile(r"\bPT\d+[HMS]\b")),
    (
        "file path or extension",
        re.compile(r"\.(?:py|js|ts|tsx|ex|exs|ya?ml|json|sh|ps1|sql|toml)\b"),
    ),
    ("code operator", re.compile(r"=>|::|\|\||&&|!==|===")),
    ("SQL fragment", re.compile(r"\bSELECT\b[\s\S]{0,80}?\bFROM\b", re.I)),
    ("markup tag", re.compile(r"<\/?[A-Za-z][\w-]*\s*\/?>")),
)


# A single snake_case token is not code. "A payments company renamed
# transaction_amount to amount and silently produced NULL revenue across 14
# dashboards" is a business anecdote whose whole point IS the field name —
# discarding it destroys the learning. TWO OR MORE distinct identifiers means
# the learning has stopped telling a story and started describing a schema
# (customer_id / user_id / order_id). Threshold calibrated on the 2026-07-13
# live run, which discarded that exact anecdote as a false positive.
_SNAKE_CASE = re.compile(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b")
_SNAKE_CASE_LIMIT = 2


def find_code_in_learning(learning: str) -> str | None:
    """Return a human reason if `learning` carries code, else None.

    This is the HARD gate behind the doctrine "a learning never contains
    code". It is deterministic: it does not depend on an LLM, a network, or
    a config file, so it cannot fail open.

    Calibration bias: a FALSE POSITIVE here destroys a good learning, which
    is worse than letting a marginal one through — the prompt is the first
    line of defence and it already asks for prose. So every rule must be a
    shape that essentially never occurs in business writing.
    """
    text = learning or ""
    for reason, pattern in _CODE_PATTERNS:
        m = pattern.search(text)
        if m:
            snippet = m.group(0).strip()
            return f"{reason}: {snippet!r}"

    identifiers = sorted(set(_SNAKE_CASE.findall(text)))
    if len(identifiers) >= _SNAKE_CASE_LIMIT:
        return (
            f"schema field names ({len(identifiers)} identifiers): "
            f"{', '.join(identifiers[:4])}"
        )
    return None


def build_learnings_prompt(query: str, contents_block: str) -> str:
    """Assemble the learnings-extraction user message."""
    return LEARNINGS_PROMPT.format(query=query, contents_block=contents_block)


# =========================================================================
# PART 3 — RELEVANCE: only what an operator can act on gets persisted
# =========================================================================

RELEVANCE_HIGH = "HIGH_RELEVANCE"
RELEVANCE_MEDIUM = "MEDIUM_RELEVANCE"
RELEVANCE_LOW = "LOW_RELEVANCE"
RELEVANCE_DISCARD = "DISCARD"
# Assigned when the relevance LLM is unavailable. Never silently treated as
# a pass: the caller records it in run metadata so the Owner sees that the
# judgment layer was down for that run.
RELEVANCE_UNRATED = "UNRATED"

RELEVANCE_LEVELS = (
    RELEVANCE_HIGH, RELEVANCE_MEDIUM, RELEVANCE_LOW, RELEVANCE_DISCARD,
)
# Doctrine: only HIGH and MEDIUM reach the vault. Better to lose a valid
# learning than to persist an irrelevant one — an irrelevant learning is not
# neutral, it is read back as context by every later run.
KEEP_LEVELS = frozenset({RELEVANCE_HIGH, RELEVANCE_MEDIUM})

DEFAULT_OPERATOR_CONTEXT = (
    "A founder/operator running a business. They decide on product, "
    "distribution, go-to-market, pricing, hiring and operations. They are "
    "not a data engineer and will not run a command or edit a config file."
)

RELEVANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ratings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "relevance": {
                        "type": "string",
                        "enum": list(RELEVANCE_LEVELS),
                    },
                    "reason": {"type": "string"},
                },
                "required": ["index", "relevance", "reason"],
            },
        }
    },
    "required": ["ratings"],
}


def build_relevance_prompt(learnings: list[str],
                           operator_context: str | None = None) -> str:
    """Assemble the relevance-rating user message."""
    context = operator_context or DEFAULT_OPERATOR_CONTEXT
    listing = "\n".join(
        f"[{i}] {ln}" for i, ln in enumerate(learnings)
    )
    return (
        "Rate each learning below for whether it is worth persisting into "
        "the operator's permanent knowledge base.\n\n"
        f"WHO WILL READ IT:\n{context}\n\n"
        "ASK THESE THREE QUESTIONS OF EVERY LEARNING:\n"
        "  1. Could this operator ACT on it within the next 30 days?\n"
        "  2. Does it improve a decision about business, product, "
        "distribution or operations?\n"
        "  3. Does it transfer beyond the narrow technical domain it came "
        "from — would it still matter to a company of a different size or "
        "in a different sector?\n\n"
        "RATING SCALE:\n"
        f"  {RELEVANCE_HIGH}   — yes to all three. Acts on it, changes a "
        "decision, transfers.\n"
        f"  {RELEVANCE_MEDIUM} — yes to 2 of 3. Useful, not urgent.\n"
        f"  {RELEVANCE_LOW}    — yes to at most 1. Interesting but the "
        "operator cannot use it. Applies only to enterprise data "
        "infrastructure teams, or is pure background.\n"
        f"  {RELEVANCE_DISCARD}        — noise, vendor marketing, a "
        "restatement of a definition, or an implementation detail.\n\n"
        "Be strict. A learning that is merely TRUE is not a learning. "
        "Persisting an irrelevant one is worse than losing a valid one, "
        "because the knowledge base is read back as context on every future "
        "run. When genuinely torn between two levels, pick the LOWER one.\n\n"
        "`reason` must be one sentence naming which of the three questions "
        "failed, or why it passed all three.\n\n"
        f"<learnings>\n{listing}\n</learnings>"
    )


def parse_relevance_ratings(response: dict[str, Any],
                            learning_count: int) -> dict[int, dict[str, str]]:
    """Normalise the LLM's rating payload into {index: {relevance, reason}}.

    An index the LLM failed to rate, or rated with a level outside the scale,
    is left out of the returned map. The caller treats a missing index as
    unrated (kept, but flagged) rather than as an implicit pass or fail —
    a malformed LLM response must never silently mutate the corpus.
    """
    out: dict[int, dict[str, str]] = {}
    for row in (response.get("ratings") or []):
        if not isinstance(row, dict):
            continue
        try:
            idx = int(row.get("index"))
        except (TypeError, ValueError):
            continue
        if not 0 <= idx < learning_count:
            continue
        level = str(row.get("relevance") or "").strip().upper()
        if level not in RELEVANCE_LEVELS:
            continue
        out[idx] = {
            "relevance": level,
            "reason": str(row.get("reason") or "").strip(),
        }
    return out


def log_discarded(rows: list[dict[str, Any]], path: Path) -> None:
    """Append discarded learnings to a JSONL audit trail.

    The discard log is the feedback loop: it is how the Owner sees WHAT the
    gates are throwing away and WHY, and therefore how the gates get tuned.
    A gate that discards silently is indistinguishable from a bug.
    """
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(_json.dumps(row, ensure_ascii=False) + "\n")
