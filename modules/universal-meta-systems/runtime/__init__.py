"""Universal Meta-Systems Runtime.

Interprets the read-only meta-systems corpus (SHA 45dd1f9) and, given a repo's
noun-map, emits a concrete, noun-substituted, gate-checked execution plan per
meta-system. It NEVER reimplements a meta-system and NEVER writes to the corpus:
the logic lives in the corpus datasets; this package parses and applies it.

Design (approved 2026-07-10, Option C deflated):
  corpus_parser  -- PART V/VI/VII of a dataset -> MetaSystemSpec (structured).
  noun_map       -- load/validate .pp_meta_systems.json; generic fail-open;
                    propose candidate nouns from CLAUDE.md (propose-never-build).
  executor       -- MetaSystemSpec + NounMap -> ExecutionPlan (R-CORE).
  loop           -- executor x7 in the corpus loop order + stop conditions.
  runtime        -- CLI (list/show/apply/loop/audit); audit == executor(MS-6).

Constraints: corpus read-only; interpreter never reimplements; the noun-map is
the single point of variability.
"""

__all__ = [
    "corpus_parser",
    "noun_map",
    "executor",
    "loop",
    "runtime",
]

# Corpus loop order (from index.md): the closed loop the seven coexist in.
LOOP_ORDER = ["MS-6", "MS-2", "MS-1", "MS-0", "MS-3", "MS-4", "MS-5"]

# The pinned, read-only corpus commit this runtime is written against.
CORPUS_PINNED_SHA = "45dd1f9"
