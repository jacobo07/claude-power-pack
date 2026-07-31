#!/usr/bin/env python3
"""align.py -- OSR-3: align two executions and locate the EARLIEST divergence.

The distinction this module exists to make. `tools/replay_harness.py` compares
one run against recorded expectations and emits MATCH / DIFF / SHIM_ERROR /
SKIPPED per event; it never aligns two live traces, so it cannot answer the
question that actually matters during a regression hunt: *the first difference
a human sees is rarely the first difference that happened.*

Two indices, never one:

  T1 -- the earliest divergence on an INTERNAL event (a command dispatched, a
        registry populated, a resource mounted). The candidate cause.
  T2 -- the earliest divergence on an OBSERVABLE event (a rendered frame, an
        emitted response). The symptom.

Their separation is the finding. `causal_distance = T2 - T1` counts how many
events the failure travelled before becoming visible; a distance greater than
zero means every investigation that starts at the symptom starts in the wrong
place. This module locates the position and stops. CRAIF owns the investigation
that follows -- candidates, evidence sufficiency, closure -- and this module
never opens one.

(The source document routed this output to a system called KADOS. That system
does not exist in this repository: one mention, inside a plan file. The bridge
is to CRAIF.)
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Sequence

MISSING = "MISSING_IN_BUILD"
EXTRA = "EXTRA_IN_BUILD"
REORDERED = "REORDERED"
PAYLOAD_DIFF = "PAYLOAD_DIFF"
ALIGNED = "ALIGNED"

INTERNAL = "internal"
OBSERVABLE = "observable"

_DEFAULT_VOLATILE = ("ts", "iso_ts", "timestamp", "duration_ms", "session_id", "trace_id")


def normalize(event: dict[str, Any], volatile: Sequence[str] = _DEFAULT_VOLATILE) -> str:
    """A stable comparison key for one event.

    Volatile fields are dropped rather than compared, because a timestamp
    difference between two runs is not a divergence and treating it as one
    makes every alignment diverge at index 0 -- which is the same as having no
    instrument at all.
    """
    payload = {
        k: v for k, v in (event.get("payload") or {}).items()
        if k not in volatile
    }
    return json.dumps(
        {"kind": event.get("kind"), "payload": payload},
        sort_keys=True,
        ensure_ascii=False,
    )


def align(
    reference: Iterable[dict[str, Any]],
    build: Iterable[dict[str, Any]],
    volatile: Sequence[str] = _DEFAULT_VOLATILE,
    lookahead: int = 8,
) -> dict[str, Any]:
    """Align two ordered traces and report the earliest divergence per layer.

    `lookahead` bounds the search for a reordered match. Unbounded search would
    let a trace with many repeated events pair an early reference event with a
    much later build event and report a clean alignment that never happened.
    """
    ref = list(reference)
    got = list(build)
    if not ref or not got:
        return {
            "verdict": "UNMEASURED",
            "reason": "one or both traces are empty",
            "divergences": [],
        }

    ref_keys = [normalize(e, volatile) for e in ref]
    got_keys = [normalize(e, volatile) for e in got]

    divergences: list[dict[str, Any]] = []
    i = j = 0
    while i < len(ref) and j < len(got):
        if ref_keys[i] == got_keys[j]:
            i += 1
            j += 1
            continue

        # Same event kind, different payload: a value diverged, not the flow.
        if ref[i].get("kind") == got[j].get("kind"):
            divergences.append(_record(PAYLOAD_DIFF, i, j, ref[i], got[j]))
            i += 1
            j += 1
            continue

        # The reference's next event appears further along the build: the build
        # emitted something extra (or ran the two out of order).
        ahead_in_build = _find(ref_keys[i], got_keys, j + 1, j + 1 + lookahead)
        ahead_in_ref = _find(got_keys[j], ref_keys, i + 1, i + 1 + lookahead)
        if ahead_in_build is not None and (ahead_in_ref is None or ahead_in_build - j <= ahead_in_ref - i):
            for k in range(j, ahead_in_build):
                divergences.append(_record(EXTRA, i, k, None, got[k]))
            j = ahead_in_build
        elif ahead_in_ref is not None:
            for k in range(i, ahead_in_ref):
                divergences.append(_record(MISSING, k, j, ref[k], None))
            i = ahead_in_ref
        else:
            divergences.append(_record(REORDERED, i, j, ref[i], got[j]))
            i += 1
            j += 1

    for k in range(i, len(ref)):
        divergences.append(_record(MISSING, k, len(got), ref[k], None))
    for k in range(j, len(got)):
        divergences.append(_record(EXTRA, len(ref), k, None, got[k]))

    return _summarize(divergences, len(ref), len(got))


def _summarize(divergences: list[dict[str, Any]], ref_len: int, got_len: int) -> dict[str, Any]:
    if not divergences:
        return {
            "verdict": ALIGNED,
            "reference_events": ref_len,
            "build_events": got_len,
            "divergences": [],
            "t1_internal": None,
            "t2_observable": None,
            "causal_distance": None,
        }

    t1 = next((d for d in divergences if d["layer"] == INTERNAL), None)
    t2 = next((d for d in divergences if d["layer"] == OBSERVABLE), None)
    distance = None
    if t1 is not None and t2 is not None:
        distance = t2["reference_index"] - t1["reference_index"]

    return {
        "verdict": "DIVERGED",
        "reference_events": ref_len,
        "build_events": got_len,
        "divergences": divergences,
        "earliest": divergences[0],
        "t1_internal": t1,
        "t2_observable": t2,
        "causal_distance": distance,
    }


def craif_record(alignment: dict[str, Any], mission: str) -> dict[str, Any]:
    """Shape the alignment as an investigation INPUT for CRAIF.

    Deliberately carries no hypothesis, no ranking and no suspected cause. This
    module knows *where* the executions parted; asserting *why* would be the
    generator grading its own output, which CLAE Part XVI names as the
    self-verification limit.
    """
    t1 = alignment.get("t1_internal")
    t2 = alignment.get("t2_observable")
    return {
        "mission": mission,
        "producer": "osr.align",
        "consumer": "craif",
        "verdict": alignment.get("verdict"),
        "investigate_from": (t1 or t2 or alignment.get("earliest") or {}).get("reference_index"),
        "symptom_at": (t2 or {}).get("reference_index"),
        "causal_distance": alignment.get("causal_distance"),
        "divergence_count": len(alignment.get("divergences", [])),
        "note": (
            "Start at investigate_from, not symptom_at. A non-zero causal_distance "
            "means the visible failure is downstream of where the executions parted."
        ),
    }


def _record(
    kind: str,
    ref_index: int,
    build_index: int,
    ref_event: dict[str, Any] | None,
    build_event: dict[str, Any] | None,
) -> dict[str, Any]:
    source = ref_event or build_event or {}
    return {
        "divergence": kind,
        "layer": source.get("layer", OBSERVABLE),
        "event_kind": source.get("kind"),
        "reference_index": ref_index,
        "build_index": build_index,
        "reference_event_id": (ref_event or {}).get("event_id"),
        "build_event_id": (build_event or {}).get("event_id"),
    }


def _find(needle: str, haystack: Sequence[str], start: int, stop: int) -> int | None:
    for idx in range(start, min(stop, len(haystack))):
        if haystack[idx] == needle:
            return idx
    return None
