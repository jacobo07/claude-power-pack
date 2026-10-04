---
phase: 04-re-derivation-admission-proof-reuse-and-tool-schema-residency
plan: 01
status: complete
commits: [36db0ff8, 8f7b6caf, ae816022, 73d97127, 950e2f84]
requirements: [CE-F, CE-G, CE-K, CE-P, CE-C]
---

# Plan 04-01 Summary

- K: KSR `ctx_dead.py` replicated by a campaign copy on the CPP corpus (original untouched, manifest committed
  before measuring in 36db0ff8). Largest dead class 2.67 % < 3 % -> FALSIFIED_OR_REJECTED_BY_EVIDENCE.
- F: identical re-reads (path, offset, limit, sha256) across sibling subagents = 1.8793 % of D-W7 weighted
  (1,124 re-reads) < 3 % -> FALSIFIED_OR_REJECTED_BY_EVIDENCE.
- G: F measured exactly the identity boundary G's rule names and found no recurrence >= 3 % -> FALSIFIED.
- P: verification carriage (test/gate results 0.3041 + issuing tool_use 0.1966) = 0.5007 % < 3 % -> FALSIFIED.
- C (tool half): ToolSearch-loaded schema carriage 0.0020 % < 3 %; lazy loading already exists in the harness.
  C's terminal (DEFERRED_STRONGER_OWNER, skills/agents to their owners) was written in phase 7.
- Sources: `evidence/K-tool-output-admission.md`, `evidence/F-G-P-C-carriage.md`. SUMMARY written by epoch 4.
