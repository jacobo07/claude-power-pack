"""G1 -- UI / Editor State Persistence Layer (Python-feasible half).

The editor surface (tabs, order, focus, scroll, panels, splits) is what makes a
crash *feel* different from a Reload Window. CAPTURE and APPLY of that surface can
only happen inside the editor host (extension JS: vscode.window.tabGroups /
TextEditor.visibleRanges / showTextDocument / revealRange) -- Python cannot touch
the UI, and scroll restore is host-APPROXIMATE. That extension half is specified
in vault/knowledge_base/session_resilience/G1_EXTENSION_CAPTURE_SPEC.md and its
visual "indistinguishable from Reload Window" gate is Owner-run (SCS C50).

This module is the Python-feasible, fully-testable half:
  * the canonical editor manifest model (the shape the extension produces),
  * the UI State Diff Adapter (canonical form so G3 deltas stay small),
  * capability-aware unrestorable marking (what the host cannot restore is
    dropped+reported, and excluded from G4's equivalence denominator),
  * the glue that turns captured editor state into the canonical description
    G2 embeds per window and G3 versions / G4 scores.

Eight dataset entities (session_resilience_01): 7 are capture/apply (extension JS,
see the spec) -- Editor Tab Inventory, Tab Ordering, Active Focus, Scroll & Cursor
Position, Panel Layout, Editor Split Topology, Pinned & Preview Classifier. The
8th, the UI State Diff Adapter, plus the manifest model and capability marking,
live here in Python.
"""
from __future__ import annotations

from . import models

# Editor properties the host may or may not be able to restore. On current Cursor
# all are attempted; scroll restore is approximate (handled by G4's tolerance).
# A host/version that genuinely cannot restore a property drops it from this set,
# and capability-aware acceptance (G4) then excludes it from the denominator.
DEFAULT_HOST_CAPABILITIES = frozenset({"tabs", "focus", "scroll", "panels", "splits"})

_EDITOR_KEYS = ("tabs", "focus", "scroll", "panels", "splits")


# --- Manifest model (the shape the extension capture must produce) ----------

def build_editor(
    tabs: list[dict] | None = None,
    focus: dict | None = None,
    scroll: dict | None = None,
    panels: dict | None = None,
    splits: dict | None = None,
) -> dict:
    """Assemble one window's editor manifest in the canonical shape (models.py).
    ``tabs`` items: {path, group, order, pinned, preview}. Pure data -- the
    extension fills these from the live editor; tests pass synthetic values."""
    return {
        "tabs": list(tabs or []),
        "focus": focus,
        "scroll": dict(scroll or {}),
        "panels": dict(panels or {}),
        "splits": dict(splits or {}),
    }


def validate_editor(editor: dict) -> tuple[bool, str]:
    """Internal validity before a manifest is offered for restore: the focus
    target must be an open tab, and every scrolled document must be an open tab."""
    tab_paths = {str(t.get("path")) for t in (editor.get("tabs") or [])}
    focus = editor.get("focus")
    if focus and str(focus.get("path")) not in tab_paths:
        return False, f"focus target {focus.get('path')!r} not among open tabs"
    for path in (editor.get("scroll") or {}):
        if str(path) not in tab_paths:
            return False, f"scroll for {path!r} which is not an open tab"
    return True, "valid"


# --- Entity 8: UI State Diff Adapter ----------------------------------------

def canonical_editor(editor: dict) -> dict:
    """Stable, canonically-ordered form so a single UI change yields a small,
    legible delta when G3 diffs it (rather than whole-state churn)."""
    return models.canonical(editor)


def _leaves(obj, prefix=()):
    if isinstance(obj, dict):
        for k in obj:
            yield from _leaves(obj[k], prefix + (k,))
    else:
        yield prefix, obj


def editor_change_count(prev: dict, cur: dict) -> int:
    """How many canonical leaves changed -- proves the diff adapter keeps a
    small change small (the cheap-delta contract G3 relies on)."""
    a = dict(_leaves(canonical_editor(prev)))
    b = dict(_leaves(canonical_editor(cur)))
    changed = sum(1 for k in b if a.get(k, object()) != b[k])
    changed += sum(1 for k in a if k not in b)
    return changed


# --- Capability-aware unrestorable marking ----------------------------------

def mark_unrestorable(
    editor: dict, capabilities: frozenset[str] = DEFAULT_HOST_CAPABILITIES
) -> tuple[dict, list[str]]:
    """Return (restorable_editor, unrestorable_report). A property the host
    cannot restore is dropped from the restorable manifest and named in the
    report -- never silently kept-and-failed, never silently dropped."""
    restorable: dict = {}
    report: list[str] = []
    for key in _EDITOR_KEYS:
        if key not in editor:
            continue
        if key in capabilities:
            restorable[key] = editor[key]
        else:
            report.append(f"{key}: host cannot restore (known limitation)")
    return restorable, report


def g4_host_capabilities(
    editor_caps: frozenset[str] = DEFAULT_HOST_CAPABILITIES,
) -> frozenset[str]:
    """Translate editor capability flags into the G4 dimension set, so the
    arbiter excludes host-unrestorable dimensions from equivalence. Window /
    terminal / conversation dimensions are always restorable (CETTG/G2)."""
    dims = {"windows", "terminals", "conversations"}
    if "tabs" in editor_caps:
        dims |= {"editor_tabs", "editor_order"}
    if "focus" in editor_caps:
        dims.add("focus")
    if "scroll" in editor_caps:
        dims.add("scroll")
    return frozenset(dims)
