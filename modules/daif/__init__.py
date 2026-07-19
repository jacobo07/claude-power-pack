"""DAIF runtime — the executable half of the D2A Institutional Fabric corpus.

The corpus in vault/knowledge_base/d2a_fabric/ specifies. This package runs.
Nothing here narrates; every module produces an object the corpus defined.
"""
from __future__ import annotations

__all__ = ["obligation_extractor", "constraint_extractor", "decision_extractor",
          "session_continuity_compiler", "two_arm_trial", "resume_reader"]
