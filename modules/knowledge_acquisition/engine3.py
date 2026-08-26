"""Bridge to the deep-research quality engine. Re-exports, never reimplements.

WHY A BRIDGE AND NOT AN IMPORT
------------------------------
`modules/deep-research/` has a hyphen, so it is not an importable package. The
in-repo convention (see `deep-research/classify_sources.py:38`) is to put the
directory on sys.path and import bare. That convention is followed here rather
than invented around, so there is exactly one way this dependency is resolved.

WHY A BRIDGE AT ALL
-------------------
The epistemic vocabulary, the deterministic demotion caps and the measurable-
datum test already exist and are tested. Re-deriving any of them here would
create a second scale that drifts from the first -- the precise failure the
Duplicate-to-Advantage audit exists to prevent. This module is the seam, and it
is deliberately thin: no logic lives here.

FAILURE POSTURE
---------------
Import failure raises, loudly, at import time. It is NOT softened into a local
fallback: a silent reimplementation of `cap_epistemic` would grade answers on a
scale nobody reviewed. The caller that must not die -- the acquisition runner --
guards the assessment call itself and records the answer unrated. Durability is
protected at the integration point, not by faking the dependency.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parents[1] / "deep-research"
_ENGINE_PATH = _ENGINE_DIR / "research_engines.py"
_QUALITY_PATH = _ENGINE_DIR / "research_quality.py"


def _load(name: str, path: Path):
    if not path.is_file():
        raise ImportError(
            f"knowledge_acquisition depends on {path} and it is not there. "
            f"This module deliberately has no local fallback: grading answers "
            f"on a privately reimplemented scale is worse than not grading "
            f"them."
        )
    if str(_ENGINE_DIR) not in sys.path:
        sys.path.insert(0, str(_ENGINE_DIR))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not build an import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


_engines = _load("kacq_research_engines", _ENGINE_PATH)
_quality = _load("kacq_research_quality", _QUALITY_PATH)

# -- epistemic scale (research_engines.py:684-706) --------------------------
EPI_OBSERVED = _engines.EPI_OBSERVED
EPI_VERIFIED = _engines.EPI_VERIFIED
EPI_DERIVED = _engines.EPI_DERIVED
EPI_HYPOTHESIS = _engines.EPI_HYPOTHESIS
EPI_REJECTED = _engines.EPI_REJECTED
EPISTEMIC_LEVELS = _engines.EPISTEMIC_LEVELS
EPISTEMIC_RANK = _engines.EPISTEMIC_RANK
EPISTEMIC_DEFAULT = _engines.EPISTEMIC_DEFAULT

# -- coverage vocabulary (research_engines.py:586-615) ----------------------
# Supplied by this module's caller, never forked. `UNCLASSIFIED` is the honest
# baseline for one unverifiable expert source; `VENDOR_ONLY` is reserved for a
# claim the source's own declared boundary makes unsourced.
COVERAGE_COVERED = _engines.COVERAGE_COVERED
COVERAGE_THIN = _engines.COVERAGE_THIN
COVERAGE_UNCLASSIFIED = _engines.COVERAGE_UNCLASSIFIED
COVERAGE_VENDOR_ONLY = _engines.COVERAGE_VENDOR_ONLY

# -- the gates themselves ---------------------------------------------------
cap_epistemic = _engines.cap_epistemic
normalize_epistemic = _engines.normalize_epistemic
has_measurable_datum = _engines.has_measurable_datum

# -- unrated: the judgment layer was down, and that is never a pass ---------
# (research_quality.py:377-392). Adopted rather than redefined so a reader of
# either module sees the same token mean the same thing.
UNRATED = _quality.RELEVANCE_UNRATED

__all__ = [
    "EPI_OBSERVED", "EPI_VERIFIED", "EPI_DERIVED", "EPI_HYPOTHESIS",
    "EPI_REJECTED", "EPISTEMIC_LEVELS", "EPISTEMIC_RANK", "EPISTEMIC_DEFAULT",
    "COVERAGE_COVERED", "COVERAGE_THIN", "COVERAGE_UNCLASSIFIED",
    "COVERAGE_VENDOR_ONLY", "cap_epistemic", "normalize_epistemic",
    "has_measurable_datum", "UNRATED",
]
