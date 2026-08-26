"""Tests for modules/knowledge_acquisition — Phase 0 (identity, state, parser).

Hermetic by default: the parser tests build their own fixtures. The two tests
that touch the real 2,200-prompt corpus skip cleanly when it is absent, so CI
on another machine stays green without the Owner's Downloads folder.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.knowledge_acquisition.corpus_parser import (
    CorpusParseError,
    parse_corpus,
)
from modules.knowledge_acquisition.models import (
    IllegalTransition,
    JobState,
    assert_transition,
    canonical_hash,
    canonicalize,
    content_hash,
)

# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------


def test_canonicalize_collapses_whitespace_variants():
    # Arrange — the same question as it survives a round-trip through a chat UI
    a = "¿Qué  casos\treales\nconoce EVA?"
    b = "¿Qué casos reales conoce EVA?"

    # Act
    ca, cb = canonicalize(a), canonicalize(b)

    # Assert
    assert ca == cb
    assert canonical_hash(a) == canonical_hash(b)


def test_canonicalize_folds_typographic_unicode():
    # Arrange — NFKC folds the non-breaking space a word processor inserts
    nbsp = "Cual es el AOV?"
    plain = "Cual es el AOV?"

    # Act / Assert
    assert canonical_hash(nbsp) == canonical_hash(plain)


def test_identity_is_position_independent():
    # Arrange — renumbering the corpus must not change any id
    q = "¿Cuál es el CAC objetivo?"

    # Act / Assert
    assert canonical_hash(q) == canonical_hash(q)
    assert canonical_hash(q) != canonical_hash(q + " Y el LTV?")


def test_content_hash_does_not_canonicalize():
    # Arrange — two materially different captures must not collide
    a = "line one\n\nline two"
    b = "line one line two"

    # Act / Assert — canonical_hash folds these; content_hash must not
    assert canonical_hash(a) == canonical_hash(b)
    assert content_hash(a) != content_hash(b)


# --------------------------------------------------------------------------
# State machine
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "current,target",
    [
        (JobState.PENDING, JobState.RUNNING),
        (JobState.RUNNING, JobState.COMPLETE),
        (JobState.RUNNING, JobState.FAILED),
        (JobState.RUNNING, JobState.NEEDS_HUMAN),
        (JobState.FAILED, JobState.PENDING),
        (JobState.NEEDS_HUMAN, JobState.PENDING),
    ],
)
def test_legal_transitions_are_allowed(current, target):
    assert_transition(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target",
    [
        (JobState.PENDING, JobState.COMPLETE),   # cannot skip execution
        (JobState.COMPLETE, JobState.PENDING),   # cannot re-ask an answered prompt
        (JobState.COMPLETE, JobState.RUNNING),
        (JobState.FAILED, JobState.COMPLETE),    # only a real run may complete
        (JobState.NEEDS_HUMAN, JobState.COMPLETE),
    ],
)
def test_illegal_transitions_are_refused(current, target):
    with pytest.raises(IllegalTransition):
        assert_transition(current, target)


def test_complete_is_terminal():
    # A captured answer can never be dragged back into the work set.
    for target in JobState:
        with pytest.raises(IllegalTransition):
            assert_transition(JobState.COMPLETE, target)


# --------------------------------------------------------------------------
# Parser — the numbered-list ambiguity
# --------------------------------------------------------------------------


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_parser_rejects_numbered_list_items_inside_answers(tmp_path):
    # Arrange — answer to prompt 1 contains its own "1." / "2." list at col 0,
    # which is exactly the shape that yielded 2,011 markers for 2,000 prompts.
    src = _write(
        tmp_path,
        "c.md",
        "## Fam A\n"
        "1. Primera pregunta?\n"
        "\n"
        "Respuesta larga. " + ("x" * 300) + "\n"
        "1. item de lista dentro de la respuesta\n"
        "2. otro item de lista\n"
        "\n"
        "2. Segunda pregunta?\n"
        "\n"
        "3. Tercera pregunta?\n",
    )

    # Act
    result = parse_corpus(src, "C", expected_count=3)

    # Assert — three prompts, and the two list items were rejected, not ingested
    assert [p.external_id for p in result.prompts] == ["1", "2", "3"]
    assert len(result.rejected_markers) == 2


def test_parser_fails_closed_on_count_mismatch(tmp_path):
    # Arrange — a corpus that is one prompt short of what the caller declared
    src = _write(tmp_path, "c.md", "## Fam\n1. Uno?\n\n2. Dos?\n")

    # Act / Assert — must refuse, not ingest a plausible partial corpus
    with pytest.raises(CorpusParseError, match="parsed 2 prompts, expected 3"):
        parse_corpus(src, "C", expected_count=3)


def test_parser_refuses_colliding_identities(tmp_path):
    # Arrange — the same question twice produces one canonical hash for two rows
    src = _write(tmp_path, "c.md", "## Fam\n1. Misma pregunta?\n\n2. Misma pregunta?\n")

    # Act / Assert
    with pytest.raises(CorpusParseError, match="canonical hash"):
        parse_corpus(src, "C", expected_count=2)


def test_parser_handles_digit_bearing_id_prefix(tmp_path):
    # Arrange — `SF30-001`: a letters-only prefix class matches none of these,
    # which silently parsed the whole 200-prompt family as zero.
    src = _write(
        tmp_path,
        "c.md",
        "## Fam\nSF30-001. Primera?\n\nSF30-002. Segunda?\n",
    )

    # Act
    result = parse_corpus(src, "SF30", expected_count=2)

    # Assert
    assert [p.external_id for p in result.prompts] == ["SF30-001", "SF30-002"]


def test_parser_separates_answered_from_bare(tmp_path):
    # Arrange — prompt 1 already has EVA's answer inline; prompt 2 does not
    src = _write(
        tmp_path,
        "c.md",
        "## Fam\n1. Con respuesta?\n\n" + ("y" * 400) + "\n\n2. Sin respuesta?\n",
    )

    # Act
    result = parse_corpus(src, "C", expected_count=2)

    # Assert — an already-answered prompt must never re-enter the work set
    assert len(result.answered) == 1
    assert len(result.bare) == 1
    assert result.answered[0].external_id == "1"


def test_parser_assigns_family_from_level_two_headers(tmp_path):
    # Arrange
    src = _write(tmp_path, "c.md", "## Alpha\n1. Uno?\n\n## Beta\n2. Dos?\n")

    # Act
    result = parse_corpus(src, "C", expected_count=2)

    # Assert
    assert result.prompts[0].family == "Alpha"
    assert result.prompts[1].family == "Beta"


# --------------------------------------------------------------------------
# Real corpus — skipped when the source files are not on this machine
# --------------------------------------------------------------------------

_DOWNLOADS = Path.home() / "Downloads"
_SF30 = _DOWNLOADS / "EVA_PRE_200_Six_Figure_First_30_Day_Launch_Reverse_Engineering.md"
_CWOPS = _DOWNLOADS / "EVA_2000_Prompts_CommonWealth_Ops_Brand_001.md"

_needs_corpus = pytest.mark.skipif(
    not (_SF30.exists() and _CWOPS.exists()),
    reason="real EVA corpus not present on this machine",
)


@_needs_corpus
def test_real_sf30_corpus_parses_to_declared_size():
    # Act
    result = parse_corpus(_SF30, "SF30", expected_count=200)

    # Assert — measured ground truth 2026-08-26
    assert len(result.prompts) == 200
    assert len(result.answered) == 17
    assert [p.external_id for p in result.answered] == [
        f"SF30-{i:03d}" for i in range(1, 18)
    ]


@_needs_corpus
def test_real_cwops_corpus_parses_to_declared_size():
    # Act
    result = parse_corpus(_CWOPS, "CWOPS2000", expected_count=2000)

    # Assert — 5 answered, and the surplus list-item markers were rejected
    assert len(result.prompts) == 2000
    assert len(result.answered) == 5
    assert len(result.rejected_markers) == 5


@_needs_corpus
def test_real_corpus_ids_are_stable_across_parses():
    # Arrange / Act — resume correctness depends entirely on this
    a = parse_corpus(_SF30, "SF30", expected_count=200)
    b = parse_corpus(_SF30, "SF30", expected_count=200)

    # Assert
    assert [p.prompt_id for p in a.prompts] == [p.prompt_id for p in b.prompts]
