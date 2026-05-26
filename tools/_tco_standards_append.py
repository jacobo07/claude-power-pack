#!/usr/bin/env python3
"""M8 -- atomic append of:

  (a) SCS v5 clause C13 (Cost-Awareness-by-default) to
      knowledge_vault/core/skill-completion-standard.md
  (b) Apex axis v5 (Token Cost Optimizer v1) to
      knowledge_vault/core/apex-completion-standard.md

On BOTH loose + PP mirrors. SCS C6 atomic-write. Idempotent on marker.
Fails open if a mirror is missing -- documents and continues.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP_SCS  = Path("knowledge_vault/core/skill-completion-standard.md")
LOOSE_SCS = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/skill-completion-standard.md"))
PP_APEX = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE_APEX = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

C13_MARKER = "### C13 -- Cost-Awareness-by-default (sealed v5, 2026-05-26)"
C13_BODY = """

### C13 -- Cost-Awareness-by-default (sealed v5, 2026-05-26)

A feature that calls a Claude model OR injects context into the prompt
pipeline is complete only when its cost is visible AND its model
routing is auditable. The TCO substrate enforces this.

**Three obligations:**

1. **Compact-gate respected.** Before spawning subagents or
   continuing long loops, the author has checked
   `python tools/tco_compact_gate.py` and acted on its
   `should_compact` recommendation (threshold 70% per
   `vault/config/model-routing.json`).
2. **Routed by intent.** Subagents whose task_type maps to
   `subagent_explore`, `test_runner`, `doc_generation`,
   `commit_push_pr`, or `single_file_lookup` use Sonnet or Haiku per
   `model-routing.json`. Opus is reserved for `arch_decision`,
   `code_review_final`, and `iteration_on_error`. Audit visible in
   `tools/tis_report.py --by-skill` (rec_model vs actual_model).
3. **Cost projection emitted.** `tools/tis_report.py
   --cost-projection` runs cleanly on the session log and reports an
   honest `estimated_savings_pct` (never silent zero) plus
   `top_3_routing_opportunities` (empty list with explicit reason is
   acceptable; missing field is not).

If any of the three is missing, the feature is NOT SCS-complete on
the Cost-Awareness axis. The Reality Contract forbids silent zeros
and unmeasured cost.
"""

APEX_MARKER = "## Token Cost Optimizer (TCO) Axis v1 (sealed 2026-05-26)"
APEX_BODY = """

## Token Cost Optimizer (TCO) Axis v1 (sealed 2026-05-26) -- cost-discipline baseline

A new PP feature that consumes Claude model output is complete only
when its activity is cost-visible AND its model routing is auditable.
Until 2026-05-26 there was no live model-routing recommendation on
the trigger matrix; this axis closes that gap as the seventh standard
DONE axis alongside Concurrency, Async-Audit, Zero-Drift Mirror,
Context-Pressure, Session-Safety, Skill-Completion, and TIS.

### Five required components (all five must be present for Apex-complete)

1. **Compact Gate** -- `tools/tco_compact_gate.py` reads the active
   TIS session log and emits a 70% context-pct warning + governor
   warnings for >100k session tokens or >2h session duration.
   Stdlib-only, fail-open.
2. **Model Routing config** -- `vault/config/model-routing.json` with
   `default_model`, `>=7 rules`, and a `skill_to_task_type` map.
   Authoritative source for routing decisions; consumed by both the
   gate CLI and `tis_report.py --by-skill` audit column.
3. **Cost-projection CLI** -- `tools/tis_report.py --cost-projection`
   reads the active session log + the routing JSON + the pricing JSON
   and emits `actual_total_cost_usd`, `optimized_total_cost_usd`,
   `estimated_savings_pct` (with explicit reason field), and
   `top_3_routing_opportunities`. Honest zeros enforced
   (NO_DATA / NO_LLM_ENTRIES / ZERO_ACTUAL_COST reasons).
4. **JIT routing inject** -- `tools/jit_skill_loader.py` heuristically
   infers task_type from prompt keywords and appends a one-line
   "TCO router: recommended model X" advisory to additionalContext.
   Decorator pattern over `run()`; fail-open.
5. **verify_spp probe** -- `tools/verify_tco.py` 5-check probe + a
   row in `tools/verify_spp.py::rows_spec`. Confirms the substrate
   is alive from cold state and that CLAUDE.md anchors are present.

### Five-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the TCO Axis iff:

1. `tools/test_tco.py` exit 0 with TCO_PASS=8/8.
2. `tools/verify_tco.py` exit 0 with TCO_PROBE=5/5.
3. `tools/tco_compact_gate.py --route subagent_explore` emits a
   string containing 'sonnet'.
4. `tools/tis_report.py --cost-projection` emits a field
   `estimated_savings_pct: N%` with explicit reason (never silent).
5. `~/CLAUDE.md` contains the 'Session Cost Discipline' section AND
   references `tco_compact_gate`.

Missing any of 1-5 = NOT Apex-complete on the TCO Axis.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C13 (Cost-
  Awareness-by-default): the per-skill obligation derived from this
  axis.
- `tools/tco_compact_gate.py`, `tools/verify_tco.py`,
  `tools/test_tco.py`: the substrate.
- `vault/config/model-routing.json`,
  `vault/pricing/anthropic_2026-05.json`: the configuration.
- Sister modules: `tis_report.py` (--cost-projection, --by-skill
  audit), `jit_skill_loader.py` (TCO router inject). TCO is the
  policy + tooling layer; TIS is the measurement substrate. They
  are complementary.

### Empirical proofs (2026-05-26)

- M2 `tco_compact_gate.py` emitted real governor warning at session
  duration 11172s > 7200s threshold on the active session.
- M5 V-* gates 8/8: COMPACT-OK / COMPACT-WARN at 73% / COMPACT-HARD /
  ROUTE-SONNET / ROUTE-OPUS / ROUTE-DEFAULT / PROJECTION /
  BASELINE-INTACT.
- M3 `--cost-projection` produced honest `-400%` reading with explicit
  "actual cheaper than recommended" reason for the synthetic
  tis-self-probe entry. No silent zero.
- M3b JIT router inject: prompt "design the schema" routed to
  `arch_decision -> opus`; prompt "explore the codebase" routed to
  `subagent_explore -> sonnet`; neutral prompt did not inject.
- M6 verify_tco.py TCO_PROBE 5/5 in <1s.
"""


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_section(target: Path, marker: str, body: str) -> bool:
    if not target.is_file():
        print(f"missing (skip): {target}", file=sys.stderr)
        return False
    raw = target.read_text(encoding="utf-8")
    if marker in raw:
        print(f"already present (idempotent skip): {target}")
        return True
    if not raw.endswith("\n"):
        raw += "\n"
    _atomic_write(target, raw + body)
    print(f"appended: {target} (bytes={target.stat().st_size})")
    return True


def main() -> int:
    ok = True
    ok &= append_section(PP_SCS,  C13_MARKER, C13_BODY)
    ok &= append_section(LOOSE_SCS, C13_MARKER, C13_BODY)
    ok &= append_section(PP_APEX, APEX_MARKER, APEX_BODY)
    ok &= append_section(LOOSE_APEX, APEX_MARKER, APEX_BODY)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
