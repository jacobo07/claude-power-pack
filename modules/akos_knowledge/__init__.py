"""AKOS Knowledge integration — makes generated AKOS briefs LIVE.

The AKOS engine (external, in the AKOS/ repo) writes a static, domain-
partitioned Markdown brief into each project at
``<repo>/knowledge/AKOS_KNOWLEDGE_BRIEF.md``. Those briefs already exist on
disk across ~15 repos but nothing consumed them — knowledge muerto.

This module is the CONSUMPTION substrate: a single parser + domain resolver +
selector, imported by both live consumers so there is exactly one parse path:

  * A1 — tools/jit_skill_loader.py (_akos_knowledge_inject): session-start
    injection of domain-matched units into UserPromptSubmit context.
  * A2 — modules/frontier_intelligence/question_harvester.py (_from_akos):
    a 6th candidate-question source for the FIOS frontier pipeline.

Everything here is deterministic, bounded, and fail-open ABSOLUTE (any error
-> empty result, never an exception that could disturb the caller).
"""
from modules.akos_knowledge.akos import (
    AkosUnit,
    find_brief,
    load_domain_map,
    parse_brief,
    resolve_domains,
    select_units,
    units_for_cwd,
)

__all__ = [
    "AkosUnit",
    "find_brief",
    "load_domain_map",
    "parse_brief",
    "resolve_domains",
    "select_units",
    "units_for_cwd",
]
