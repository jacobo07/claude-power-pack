"""Test fixture for spec compiled-grammar-default law 2 (no envelope, no launch).

A lifecycle gate that launches a mission is not testing admission, so every mission it creates gets a
token estimate far above anything a fixture spends. Admission itself is judged in test_grammar_default.py,
which does not use this module.
"""
from __future__ import annotations

BIG_ESTIMATE = 10_000_000_000


def bound_missions(gm, estimate: int = BIG_ESTIMATE) -> None:
    """Wrap gm.create so each mission it prepares carries `estimate` as its token_estimate."""
    if getattr(gm.create, "_envelope_fixture", False):
        return
    original = gm.create

    def create(*args, **kwargs):
        rec = original(*args, **kwargs)
        rec["token_estimate"] = estimate
        gm._write(gm.mission_path(rec["mission_id"]), rec)
        return rec

    create._envelope_fixture = True
    gm.create = create
