"""providers.py -- the live adapters that take the kernel off the bench (DRK-01 II).

Each adapter converts a REAL sealed-module output into the contract
decision_kernel.review_decision already consumes. Every signature here was read
from source before a line was written (HR-PREMISE-001); the three premises that
did not survive that check are recorded in
vault/plans/drk-wiring-proactive-2026-07-11.md.

Contracts produced:
  precedent  -> {"verdict": "COLLISION"|"WARNING"|"CLEAR", "on_veto": bool, "sources": [...]}
  placement  -> {"operation": <D2A op>, "coverage": int}
  evidence   -> {evidence_index: acis_level_int}   (ONLY for fingerprint-bearing items)
  tier       -> {"tier": 0..3, "size": "S".."XL"}
  route      -> {"route_class": str, "model": str, "max_budget": float}

Fail-open is absolute: an adapter that cannot answer returns None (or {}), never
raises, never guesses. A provider that is slow is abandoned at its own budget --
a review must not stall on an index scan.

Stdlib only. No hardcoded absolute paths.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import time
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]

# Per-adapter wall-clock budgets (seconds). A provider that overruns is dropped,
# not waited on.
BUDGET_PRECEDENT = 3.0
BUDGET_PLACEMENT = 5.0

# An FD deposit fingerprint as it appears in an Evidence.source string.
_FINGERPRINT_RE = re.compile(r"\b(?:fp|fingerprint|deposit)[:=]\s*([0-9a-f]{6,64})\b",
                             re.IGNORECASE)


def _ensure_pp_on_path() -> None:
    if str(PP_ROOT) not in sys.path:
        sys.path.insert(0, str(PP_ROOT))


# --------------------------------------------------------------------------- #
# 1. precedent -- modules/arch-decision/arch_check.py
#
# The package directory is HYPHENATED ("arch-decision"), so it is not importable
# by `import modules.arch_decision`. It is loaded from its file path. It also
# exposes no library entrypoint -- main() prints JSON -- so the verdict is
# composed from its real public functions.
# --------------------------------------------------------------------------- #
def _load_arch_check():
    path = PP_ROOT / "modules" / "arch-decision" / "arch_check.py"
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_drk_arch_check", path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 -- fail-open: a broken provider is silence
        return None


def precedent_for(text: str, *, budget: float = BUDGET_PRECEDENT) -> dict | None:
    """arch-decision precedent-collision verdict for a decision STATEMENT.

    Returns the kernel's precedent contract, or None when the provider cannot
    answer (index absent, module unreadable, empty text). None means "no
    precedent signal", never "no collision" -- the kernel treats an absent
    provider as an absent input, not as a CLEAR.

    TWO CALIBRATION FACTS, measured against the real index (531 sources), not
    assumed. Both were found by submitting THIS wiring decision to the kernel and
    watching it reject itself:

    1. arch_check's score rises monotonically with input LENGTH (body-token
       matches score 0.5 each up to a cap, entity hits 5 each). The same decision
       scored 1.50 as a 28-word statement and 4.05 as a 78-word statement+problem+
       rationale blob -- approaching the 4.5 COLLISION floor purely by growing.
       Feed it the STATEMENT ONLY: a prompt-sized intent, the input shape its
       thresholds were calibrated on. Feeding it a concatenated blob turns "this
       is a big decision" into "this collides with everything", which is the
       always-reject bias (T-DECISION-AUTHORITY-CAPTURE-001), not a precedent.

    2. 86% of the index (459/531) is veto-class. So "a veto source appears in the
       top 3" is true almost always and carries NO information. `on_veto` must
       therefore mirror arch_check's OWN collision condition -- a veto source
       scoring at or above the COLLISION floor -- or the kernel's
       REJECT-on-precedent-collision fires on noise.
    """
    if not (text or "").strip():
        return None
    mod = _load_arch_check()
    if mod is None:
        return None
    try:
        index = mod.load_index()
        vocab = mod.load_vocab()
        if not index or not vocab:
            return None  # index not built -> no signal (NOT a CLEAR)
        signals = mod.extract_signals(text, vocab)
        deadline = time.monotonic() + budget
        sources = index.get("sources", [])
        if not isinstance(sources, list) or not sources:
            return None
        top = mod.rank_sources(sources, signals, deadline)
        verdict = mod.decide_verdict(top, signals)
        floor = getattr(mod, "COLLISION_FLOOR", 4.5)
        on_veto = any(
            s.get("_score", 0) >= floor
            and (bool(s.get("is_veto")) or s.get("class") == "veto")
            for s in top[:3])
        return {
            "verdict": verdict,
            "on_veto": on_veto,
            "sources": [{"path": s.get("path", ""), "title": s.get("title", ""),
                         "score": round(s.get("_score", 0), 2)} for s in top[:3]],
        }
    except Exception:  # noqa: BLE001 -- fail-open
        return None


# --------------------------------------------------------------------------- #
# 2. placement -- modules/duplicate_to_advantage/d2a_engine.py
# --------------------------------------------------------------------------- #
def placement_for(statement: str, *, name: str = "",
                  budget: float = BUDGET_PLACEMENT) -> dict | None:
    """D2A capability-placement operation for a build decision.

    Only meaningful for is_build_decision objects. Returns the kernel's placement
    contract; None when D2A has no recommendation. Note: most D2A operations
    (DEEPEN, CONNECT, GENERALIZE...) are NOT verdicts -- the kernel maps only the
    placement-bearing ones (CONSOLIDATE / KEEP_LOCAL / REMOVE / RETIRE /
    DO_NOT_BUILD) and ignores the rest. That is intended: a DEEPEN is a shape of
    build, not a judgment on whether to build.
    """
    if not (statement or "").strip():
        return None
    _ensure_pp_on_path()
    started = time.monotonic()
    try:
        from modules.duplicate_to_advantage.d2a_engine import Proposal, run
        v = run(Proposal(description=statement, name=name))
    except Exception:  # noqa: BLE001 -- fail-open
        return None
    if time.monotonic() - started > budget:
        return None  # overran its budget -- drop the signal rather than stall
    try:
        rec = getattr(v, "recommended", None)
        dupe = getattr(v, "dupe", None)
        if rec is None:
            return None
        return {
            "operation": getattr(rec, "operation", "") or "",
            "coverage": getattr(dupe, "coverage_pct", 0) if dupe else 0,
            "parent": getattr(dupe, "parent_name", "") if dupe else "",
        }
    except Exception:  # noqa: BLE001 -- fail-open
        return None


# --------------------------------------------------------------------------- #
# 3. evidence -- modules/fable_distillation/epistemic_ladder.py
#
# SEMANTIC LIMIT (verified at source, not assumed): epistemic_level() is keyed by
# an FD *deposit fingerprint* and returns "E0" for any fingerprint it has never
# seen. It cannot level free-text evidence. So this adapter levels ONLY evidence
# whose `source` names a real fingerprint, and returns nothing for the rest --
# leaving the caller's acis_level untouched. Assigning a level to unfingerprinted
# evidence would be the DRK inventing epistemic status, which is precisely what
# the ACIS No-Autopromotion invariant forbids.
# --------------------------------------------------------------------------- #
def _fingerprint_of(source: str) -> str | None:
    m = _FINGERPRINT_RE.search(source or "")
    return m.group(1) if m else None


def evidence_levels_for(evidence: list, *, repo: str = "claude-power-pack",
                        state_dir=None) -> dict:
    """{index_in_evidence_list: acis_level_int} for fingerprint-bearing items.

    Returns {} when nothing can be levelled -- the honest answer, not a zero.
    """
    if not evidence:
        return {}
    _ensure_pp_on_path()
    try:
        from modules.fable_distillation.epistemic_ladder import epistemic_level
    except Exception:  # noqa: BLE001 -- fail-open
        return {}
    out: dict[int, int] = {}
    for i, ev in enumerate(evidence):
        fp = _fingerprint_of(getattr(ev, "source", "") or "")
        if not fp:
            continue  # unfingerprinted -> ACIS has nothing to say. Leave it.
        try:
            level = epistemic_level(fp, repo, state_dir=state_dir)
        except Exception:  # noqa: BLE001 -- fail-open per item
            continue
        m = re.fullmatch(r"E([0-7])", str(level or ""))
        if m:
            out[i] = int(m.group(1))
    return out


def apply_evidence_levels(obj) -> int:
    """Write resolved ACIS levels onto the object's evidence items in place.

    Returns the number of items levelled. Only fingerprint-bearing items are
    touched; an item the ladder cannot speak to keeps whatever the author gave it.
    """
    try:
        levels = evidence_levels_for(list(obj.evidence))
    except Exception:  # noqa: BLE001 -- fail-open
        return 0
    n = 0
    for i, lvl in levels.items():
        try:
            obj.evidence[i].acis_level = lvl
            n += 1
        except (IndexError, AttributeError):
            continue
    return n


# --------------------------------------------------------------------------- #
# 4. tier -- modules/spec_gate/gate.py  (advisory tier-raiser)
# --------------------------------------------------------------------------- #
def tier_for(statement: str) -> dict | None:
    if not (statement or "").strip():
        return None
    _ensure_pp_on_path()
    try:
        from modules.spec_gate.gate import classify_tier
        r = classify_tier(statement)
        return {"tier": int(getattr(r, "tier", 0)),
                "size": getattr(r, "size", ""),
                "requires_spec": bool(getattr(r, "requires_spec", False)),
                "reason": getattr(r, "reason", "")}
    except Exception:  # noqa: BLE001 -- fail-open
        return None


# --------------------------------------------------------------------------- #
# 5. routing -- modules/cost_collapse/router.py  (the review's own cost, CO-03)
# --------------------------------------------------------------------------- #
def route_for(statement: str) -> dict | None:
    if not (statement or "").strip():
        return None
    _ensure_pp_on_path()
    try:
        from modules.cost_collapse.router import route
        r = route(statement)
        rc = getattr(r, "route_class", None)
        return {"route_class": getattr(rc, "name", str(rc)),
                "model": getattr(r, "model", ""),
                "max_budget": float(getattr(r, "max_budget", 0.0))}
    except Exception:  # noqa: BLE001 -- fail-open
        return None


# --------------------------------------------------------------------------- #
# resolve_all -- one call, every provider, each independently fail-open.
# --------------------------------------------------------------------------- #
def resolve_all(obj) -> dict:
    """Resolve every live provider for a DecisionObject.

    A provider that fails contributes None and is named in `failed` -- the review
    proceeds on the rest. This is the fail-open guarantee the kernel depends on:
    losing a provider degrades the review, it does not stop it.
    """
    # The STATEMENT alone goes to every text provider. All three (arch_check,
    # classify_tier, route) are calibrated on prompt-sized intent; a concatenated
    # statement+problem+rationale blob inflates arch_check's length-sensitive
    # score toward a false COLLISION (see precedent_for). The statement IS the
    # decision; the rationale is only the argument for it.
    statement = getattr(obj, "statement", "") or ""
    out: dict = {"precedent": None, "placement": None, "tier": None,
                 "route": None, "levelled": 0, "failed": []}
    for key, fn in (
        ("precedent", lambda: precedent_for(statement)),
        ("tier", lambda: tier_for(statement)),
        ("route", lambda: route_for(statement)),
    ):
        try:
            out[key] = fn()
        except Exception:  # noqa: BLE001 -- fail-open per provider
            out["failed"].append(key)
    if getattr(obj, "is_build_decision", False):
        try:
            out["placement"] = placement_for(
                getattr(obj, "statement", ""), name=getattr(obj, "id", ""))
        except Exception:  # noqa: BLE001 -- fail-open
            out["failed"].append("placement")
    try:
        out["levelled"] = apply_evidence_levels(obj)
    except Exception:  # noqa: BLE001 -- fail-open
        out["failed"].append("evidence")
    for key in ("precedent", "tier", "route"):
        if out[key] is None and key not in out["failed"]:
            out["failed"].append(f"{key}:no-signal")
    return out
