"""Cognitive OS -- the PP's cognitive-economy kernel (datasets CO-00..CO-10).

Sealed as architecture under SCS C61 (vault/knowledge_base/cognitive_os/). This
package is the *live* implementation of that architecture, built faithfully and
incrementally (anti-monolith waves). Every module here is fail-open: a kernel
that errors must never block a working launch (CO-00 III.4 fail-open contract).

Modules:
  scheduler   -- CO-08 hot-session cap verdict (advisory-only consumer; see its STATUS).
  economics   -- CO-01 Work-Units-per-MTok metric (verifiable work / compute).
  loop_budget -- CO-09 loop & subagent admission budget.
  (router, context projection, ... land in later waves.)
"""
