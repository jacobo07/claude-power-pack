"""Shared canonical state model + dimension extractors for Session Resilience OS.

A *state description* is the single JSON-serializable structure every system in
the family operates on: G3 versions it, G4 scores two of them against each other,
G1 produces its editor portion, G2 produces its window portion. Keeping ONE
canonical shape (and ONE canonicalization) is what lets deltas be small (G3) and
verdicts be deterministic (G4).

Schema (schema_version 1) -- a plain dict:
  {
    "schema_version": 1,
    "captured_at": "<iso8601>",
    "windows": [
      {
        "window_id": "<stable id, never a PID>",
        "workspace_path": "<abs path>",
        "foreground": true|false,
        "terminals": [
          {"pane_id": "..", "cwd": "..", "conversation_id": ".."|null}
        ],
        "editor": {
          "tabs":   [{"path": "..", "group": 0, "order": 0,
                      "pinned": false, "preview": false}],
          "focus":  {"window_id": "..", "group": 0, "path": ".."}|null,
          "scroll": {"<path>": 0.0..1.0},   # fraction of document
          "panels": {"<region>": {"visible": bool, "size": int|null}},
          "splits": {"groups": int, "layout": ".."}
        }
      }
    ]
  }

Nothing here touches a live editor or process -- it is pure data + pure functions,
so it is fully unit-testable. Dimension extractors normalize a description into a
comparable value per recovery dimension; acceptance (G4) compares reference vs
observed extractions, and G3 diffs canonical forms.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA_VERSION = 1

# Every Owner-perceptible recovery dimension. Acceptance criteria reference these.
DIMENSIONS = (
    "windows",        # window count + workspace bindings + foreground
    "terminals",      # per-window terminal panes (cwd)
    "conversations",  # pane -> conversation mapping
    "editor_tabs",    # set of open editor documents per window
    "editor_order",   # ordered tab sequence per group
    "focus",          # which window/group/tab holds focus
    "scroll",         # per-document scroll position (approximate by nature)
)

# Default scroll match tolerance (fraction). Scroll restore is host-approximate
# (revealRange), so exact equality would be dishonest; tolerant match is the
# contract Dataset 01 documents.
DEFAULT_SCROLL_TOLERANCE = 0.03


def canonical(obj: Any) -> Any:
    """Recursively produce a canonically-ordered structure for stable hashing /
    diffing. Dict keys sorted; lists preserved (order can itself be state)."""
    if isinstance(obj, dict):
        return {k: canonical(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [canonical(x) for x in obj]
    return obj


def canonical_json(desc: dict) -> str:
    return json.dumps(canonical(desc), separators=(",", ":"), ensure_ascii=False)


def state_hash(desc: dict) -> str:
    return hashlib.sha256(canonical_json(desc).encode("utf-8")).hexdigest()


def _windows(desc: dict) -> list[dict]:
    return list(desc.get("windows") or [])


# --- Dimension extractors: description -> comparable normalized value ---------

def extract_windows(desc: dict) -> list[tuple[str, str, bool]]:
    """(window_id, workspace_path, foreground) sorted by window_id."""
    out = [
        (str(w.get("window_id")), str(w.get("workspace_path")), bool(w.get("foreground")))
        for w in _windows(desc)
    ]
    return sorted(out, key=lambda t: t[0])


def extract_terminals(desc: dict) -> list[tuple[str, str]]:
    """(window_id, cwd) for every terminal pane, sorted -- the working board."""
    out: list[tuple[str, str]] = []
    for w in _windows(desc):
        wid = str(w.get("window_id"))
        for t in (w.get("terminals") or []):
            out.append((wid, str(t.get("cwd"))))
    return sorted(out)


def extract_conversations(desc: dict) -> list[tuple[str, str, str]]:
    """(window_id, pane_id, conversation_id) -- the pane->conversation mapping."""
    out: list[tuple[str, str, str]] = []
    for w in _windows(desc):
        wid = str(w.get("window_id"))
        for t in (w.get("terminals") or []):
            out.append((wid, str(t.get("pane_id")), str(t.get("conversation_id"))))
    return sorted(out)


def extract_editor_tabs(desc: dict) -> list[tuple[str, str]]:
    """(window_id, path) set of open editor documents, sorted."""
    out: list[tuple[str, str]] = []
    for w in _windows(desc):
        wid = str(w.get("window_id"))
        for tab in ((w.get("editor") or {}).get("tabs") or []):
            out.append((wid, str(tab.get("path"))))
    return sorted(out)


def extract_editor_order(desc: dict) -> list[tuple[str, int, list[str]]]:
    """(window_id, group, [paths in tab order]) -- order IS state, not sorted."""
    out: list[tuple[str, int, list[str]]] = []
    for w in _windows(desc):
        wid = str(w.get("window_id"))
        groups: dict[int, list[tuple[int, str]]] = {}
        for tab in ((w.get("editor") or {}).get("tabs") or []):
            g = int(tab.get("group", 0))
            groups.setdefault(g, []).append((int(tab.get("order", 0)), str(tab.get("path"))))
        for g in sorted(groups):
            ordered = [p for _, p in sorted(groups[g], key=lambda x: x[0])]
            out.append((wid, g, ordered))
    return sorted(out, key=lambda t: (t[0], t[1]))


def extract_focus(desc: dict) -> list[tuple[str, Any]]:
    """(window_id, focus-descriptor-tuple|None) sorted by window_id."""
    out: list[tuple[str, Any]] = []
    for w in _windows(desc):
        wid = str(w.get("window_id"))
        f = (w.get("editor") or {}).get("focus")
        if f:
            out.append((wid, (int(f.get("group", 0)), str(f.get("path")))))
        else:
            out.append((wid, None))
    return sorted(out, key=lambda t: t[0])


def extract_scroll(desc: dict) -> dict[str, float]:
    """{ "<window_id>::<path>": fraction } -- compared with tolerance by G4."""
    out: dict[str, float] = {}
    for w in _windows(desc):
        wid = str(w.get("window_id"))
        for path, frac in ((w.get("editor") or {}).get("scroll") or {}).items():
            try:
                out[f"{wid}::{path}"] = float(frac)
            except (TypeError, ValueError):
                continue
    return out


EXTRACTORS = {
    "windows": extract_windows,
    "terminals": extract_terminals,
    "conversations": extract_conversations,
    "editor_tabs": extract_editor_tabs,
    "editor_order": extract_editor_order,
    "focus": extract_focus,
    "scroll": extract_scroll,
}
