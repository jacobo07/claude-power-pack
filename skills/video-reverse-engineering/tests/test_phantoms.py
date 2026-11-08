"""Regressions from the first real render: a shape read as text, and a stray text row standing in for a layer."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vre.judge import match_rows  # noqa: E402
from vre.text import is_readable  # noqa: E402

SHOTS = [{"index": 0, "start": 0, "end": 59}]


def test_block_glyph_and_empty_are_not_text():
    assert not is_readable("█")
    assert not is_readable("")
    assert not is_readable(None)
    assert not is_readable("  ▪ ")


def test_letters_and_digits_are_text():
    assert is_readable("Hello")
    assert is_readable("42")
    assert is_readable("$9")


def test_stray_text_row_does_not_stand_in_for_a_missing_layer():
    ref = [{"element": "s0.layer#0", "property": "x", "start": 35, "source": "layer"}]
    cand = [{"element": "s0.text#1", "property": "x", "start": 44, "source": "text"}]
    pairs, missing = match_rows(ref, cand, SHOTS, 12)
    assert pairs == [] and len(missing) == 1  # old code paired them and asked for a -9 frame shift


def test_same_source_still_pairs():
    ref = [{"element": "s0.layer#0", "property": "x", "start": 35, "source": "layer"}]
    cand = [{"element": "s0.layer#3", "property": "x", "start": 37, "source": "layer"}]
    pairs, missing = match_rows(ref, cand, SHOTS, 12)
    assert len(pairs) == 1 and not missing
