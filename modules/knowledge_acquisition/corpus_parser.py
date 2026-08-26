"""Parse the EVA corpus markdown files into prompts + already-captured answers.

THE HAZARD THIS FILE EXISTS TO DEFEAT
-------------------------------------
In `EVA_2000_Prompts_...md` the prompt marker is a bare `N.` at line start.
That same shape occurs inside EVA's own answers as ordinary numbered lists. A
raw scan of the file yields 2,011 markers for 2,000 prompts, and the surplus
ids repeat (1, 2, 3, 1, 1, 2, 3, 5). A parser that trusts the regex fragments
answers and mis-assigns provenance across the whole corpus -- silently, with
no error, producing a registry that looks complete and is wrong.

Two defences, both required:

1. Column-zero + monotonic walk. A real prompt marker starts at column 0 and
   continues the sequence 1, 2, 3, ... exactly. A list item inside an answer is
   either indented or restarts the count, so it fails one of the two tests.
2. Fail-closed count assertion. The caller declares how many prompts the
   corpus contains. A parse that does not land on that number raises, rather
   than ingesting a plausible-looking partial corpus.

Defence 2 is the one that matters. Defence 1 is a heuristic and heuristics
drift; the assertion is what makes drift loud.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import ConversationMode, canonical_hash

#: A body shorter than this is trailing noise (a stray line, a header echo),
#: not a captured answer. The shortest real answer measured in the corpus is
#: 1,080 chars; the longest non-answer fragment is far below 200.
MIN_ANSWER_CHARS = 200

_H_RX = re.compile(r"^(#{1,6})\s+(.*)$")
#: Column-zero only. `.strip()` here would re-admit every indented list item.
_NUMERIC_RX = re.compile(r"^(\d{1,4})\.\s+(\S.*)$")
#: Prefix may contain digits (`SF30-001`), so the character class cannot be
#: letters-only -- `[A-Z]{2,8}` silently matches nothing on `SF30` and the
#: whole family parses as zero prompts.
_PREFIXED_RX = re.compile(r"^([A-Z][A-Z0-9]{1,9}-\d{2,5})\.\s+(\S.*)$")


class CorpusParseError(Exception):
    """Ingestion refused. Never downgrade this to a warning."""


@dataclass(frozen=True)
class ParsedPrompt:
    external_id: str
    ordinal: int
    question: str
    family: str
    inline_answer: str | None  # answer already present in the source document

    @property
    def prompt_id(self) -> str:
        return canonical_hash(self.question)


@dataclass
class ParseResult:
    corpus_id: str
    source_path: Path
    prompts: list[ParsedPrompt] = field(default_factory=list)
    rejected_markers: list[tuple[int, str]] = field(default_factory=list)

    @property
    def answered(self) -> list[ParsedPrompt]:
        return [p for p in self.prompts if p.inline_answer]

    @property
    def bare(self) -> list[ParsedPrompt]:
        return [p for p in self.prompts if not p.inline_answer]


def _sections(lines: list[str]) -> dict[int, str]:
    """Map line number -> nearest preceding level-2 header (the family)."""
    out: dict[int, str] = {}
    current = "(unsectioned)"
    for i, line in enumerate(lines):
        m = _H_RX.match(line)
        if m and len(m.group(1)) == 2:
            current = m.group(2).strip()
        out[i] = current
    return out


def _walk_numeric(lines: list[str]) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    """Accept only markers that continue the sequence 1, 2, 3, ... exactly."""
    accepted: list[tuple[int, str, str]] = []
    rejected: list[tuple[int, str]] = []
    expected = 1
    for i, line in enumerate(lines):
        m = _NUMERIC_RX.match(line)
        if not m:
            continue
        n = int(m.group(1))
        if n == expected:
            accepted.append((i, str(n), m.group(2).strip()))
            expected += 1
        else:
            rejected.append((i, line[:100]))
    return accepted, rejected


def _walk_prefixed(lines: list[str]) -> tuple[list[tuple[int, str, str]], list[tuple[int, str]]]:
    """Prefixed ids (SF30-001) are unambiguous, but still must not repeat."""
    accepted: list[tuple[int, str, str]] = []
    rejected: list[tuple[int, str]] = []
    seen: set[str] = set()
    last = 0
    for i, line in enumerate(lines):
        m = _PREFIXED_RX.match(line)
        if not m:
            continue
        ext = m.group(1)
        n = int(ext.rsplit("-", 1)[1])
        if ext in seen or n <= last:
            rejected.append((i, line[:100]))
            continue
        seen.add(ext)
        last = n
        accepted.append((i, ext, m.group(2).strip()))
    return accepted, rejected


def parse_corpus(
    path: Path,
    corpus_id: str,
    expected_count: int,
    conversation_mode: ConversationMode = ConversationMode.ISOLATED,
) -> ParseResult:
    """Parse one corpus file. Raises CorpusParseError unless the count matches.

    `expected_count` is not advisory. It is the contract between the Owner's
    understanding of the corpus and what actually got ingested.
    """
    if not path.exists():
        raise CorpusParseError(f"corpus file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="strict")
    lines = text.splitlines()
    families = _sections(lines)

    prefixed, rej_p = _walk_prefixed(lines)
    numeric, rej_n = _walk_numeric(lines)

    # Whichever scheme the document actually uses will dominate by an order of
    # magnitude; picking the larger avoids hardcoding a per-file format.
    if len(prefixed) >= len(numeric):
        markers, rejected = prefixed, rej_p
    else:
        markers, rejected = numeric, rej_n

    if not markers:
        raise CorpusParseError(f"{path.name}: no prompt markers matched")

    # Level-2 headers terminate an answer body just as a next prompt does.
    h2_lines = [i for i, l in enumerate(lines) if (m := _H_RX.match(l)) and len(m.group(1)) == 2]

    result = ParseResult(corpus_id=corpus_id, source_path=path, rejected_markers=rejected)

    for idx, (lineno, ext_id, question) in enumerate(markers):
        next_marker = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        next_h2 = next((h for h in h2_lines if h > lineno), len(lines))
        end = min(next_marker, next_h2)

        body = "\n".join(lines[lineno + 1 : end]).strip()
        answer = body if len(body) >= MIN_ANSWER_CHARS else None

        result.prompts.append(
            ParsedPrompt(
                external_id=ext_id,
                ordinal=idx + 1,
                question=question,
                family=families.get(lineno, "(unsectioned)"),
                inline_answer=answer,
            )
        )

    found = len(result.prompts)
    if found != expected_count:
        raise CorpusParseError(
            f"{path.name}: parsed {found} prompts, expected {expected_count}. "
            f"Ingestion refused -- a partial corpus would look complete. "
            f"({len(rejected)} markers rejected by the disambiguation walk; "
            f"re-check MIN_ANSWER_CHARS and the marker regex against the source.)"
        )

    ids = {p.prompt_id for p in result.prompts}
    if len(ids) != found:
        dupes = found - len(ids)
        raise CorpusParseError(
            f"{path.name}: {dupes} prompts share a canonical hash with another. "
            f"Identity would collide and answers would overwrite each other."
        )

    _ = conversation_mode  # applied by the registry at ingest time
    return result
