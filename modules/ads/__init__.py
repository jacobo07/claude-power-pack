"""ADS -- Auto-Documentation System (BL-ADS-001).

Stop-hook-driven, zero-touch documentation. On each turn the detector
diffs the active repo's working tree, classifies which modules were
created / updated / minor-touched, and the generator/updater write
docs/{prd,arch,constitution,changelog}/<slug>.md into that repo --
preserving Owner-authored sections. Fail-open, no-spam, cross-repo.

Public API (built incrementally per the ULTRA plan):
  * detector: ChangeType, ModuleChange, resolve_git, detect_changes
"""
from .detector import (
    ChangeType,
    ModuleChange,
    detect_changes,
    module_slug,
    resolve_git,
)
from .doc_generator import DOC_TYPES, build_docs, write_docs
from .doc_updater import extract_block, splice_block, update_docs

__all__ = [
    "ChangeType",
    "ModuleChange",
    "detect_changes",
    "module_slug",
    "resolve_git",
    "DOC_TYPES",
    "build_docs",
    "write_docs",
    "update_docs",
    "splice_block",
    "extract_block",
]
