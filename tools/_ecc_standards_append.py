#!/usr/bin/env python3
"""M16 -- atomic append of:

  (a) SCS v6 clause C14 (ECC-UQF-Active-by-default) to
      knowledge_vault/core/skill-completion-standard.md
  (b) Apex axis v6 (ECC Universal Quality Framework) to
      knowledge_vault/core/apex-completion-standard.md

On BOTH loose + PP mirrors. SCS C6 atomic-write. Idempotent on marker.

Source attribution: ECC absorption from github.com/affaan-m/ecc
under MIT License (c) 2026 Affaan Mustafa.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP_SCS = Path("knowledge_vault/core/skill-completion-standard.md")
LOOSE_SCS = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/skill-completion-standard.md"))
PP_APEX = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE_APEX = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

C14_MARKER = "### C14 -- ECC-UQF-Active-by-default (sealed v6, 2026-05-27)"
C14_BODY = """

### C14 -- ECC-UQF-Active-by-default (sealed v6, 2026-05-27)

Every new PP feature is complete only when it is auditable against
the absorbed ECC quality baseline. Three obligations:

1. **UQF audit runs.** `python tools/uqf_audit.py <module>` returns
   a score (0-100) without crashing on the module's source file.
   The score is recorded; no minimum threshold is enforced at v1
   baseline. Future cycles raise the floor empirically.
2. **At least one ECC principle applied where applicable.** If the
   feature emits code-review findings, it goes through
   `modules.code_review.run_full_review` (Pre-Report Gate + FP
   filter + Proof Triad demotion). If the feature is an agent
   prompt, the 6-rule Prompt Defense Baseline is present in the
   prompt body.
3. **No detected anti-pattern that is blocking.** If
   `modules.uqf.anti_patterns.run_all` reports a hit in
   `detect_bare_except` or `detect_silent_pass_in_except` AND the
   hit is in NEW code (not pre-existing), the finding is a BLOCK
   and must be resolved or explicitly waived with a comment + test.

Without (1)+(2)+(3): the feature is not SCS-complete on the
ECC-UQF axis.

Source: ECC (github.com/affaan-m/ecc) v2.0.0-rc.1 under MIT
License (c) 2026 Affaan Mustafa.
"""

APEX_MARKER = "## ECC Universal Quality Framework Axis v6 (sealed 2026-05-27)"
APEX_BODY = """

## ECC Universal Quality Framework Axis v6 (sealed 2026-05-27) -- absorbed-baseline DONE

The eighth Apex DONE axis. A PP install is Apex-complete on this
axis iff the ECC-absorbed quality framework is **active**, not just
documented. Distinct from the prior axes: this one is the assertion
that PP applies a competitor's hard-won doctrine internally, not as
inspiration but as importable runtime infrastructure.

### Six required components (all six must be present)

1. **Principle registry** -- `modules/uqf/principles/__init__.py`
   with `register`, `get_all`, and at least 9 `Principle` subclasses
   loaded (P01 through P09 + Error Never Silent). Each principle
   declares its `domains` and carries `source = "ECC/Affaan Mustafa MIT"`
   where applicable.
2. **Audit pipeline** -- `modules/uqf/auditor.py::UQFAuditor` with
   `audit_file`, `audit_code_str`, `audit_prompt`, `scan_all`.
   Returns `AuditReport` with 0-100 score, passed/failed lists,
   anti-pattern hits, fix hints, source attributions.
3. **Anti-pattern detectors** -- `modules/uqf/anti_patterns.py`
   with at least 7 AST-based detectors (bare_except,
   silent_pass_in_except, missing_type_hints, magic_numbers,
   mutable_defaults, god_function, hardcoded_paths).
4. **Code-review helpers** -- `modules/code_review/__init__.py`
   exposing `pre_report_gate`, `filter_false_positives`,
   `validate_high_critical`, `derive_verdict`, `run_full_review`.
   Importable; the pipeline drops FPs, demotes HIGH/CRITICAL
   without triad, computes verdict.
5. **Rules taxonomy** -- `rules/common/` (>=5 files),
   `rules/python/` (>=4 files), `rules/elixir/` (>=4 files), each
   with ECC MIT attribution footer. Cross-language base + 2 piloted
   languages.
6. **Verify probes** -- `tools/verify_uqf.py` returning UQF_PROBE
   = 5/5 + `tools/verify_rules.py` returning RULES_PROBE = 5/5,
   both rows in `tools/verify_spp.py`.

### Six-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the ECC-UQF axis iff:

1. `tools/test_uqf.py` exit 0 with UQF_PASS = 15/15.
2. `tools/verify_uqf.py` exit 0 with UQF_PROBE = 5/5.
3. `tools/verify_rules.py` exit 0 with RULES_PROBE = 5/5.
4. `tools/uqf_audit.py --scan-all` returns a real table with at
   least 4 PP modules audited and scores in 0-100 (no crash).
5. `modules/code_review/__init__.py` runs the full pipeline
   without error on a synthetic mixed-severity findings list.
6. `CLAUDE.md` contains the 6-rule Prompt Defense Baseline (P09)
   AND the Code Review Doctrine section.

Missing any of 1-6 = NOT Apex-complete on the ECC-UQF axis.

### Empirical baseline (2026-05-27)

- 9 principles registered, all with `source="ECC/Affaan Mustafa MIT"`.
- `uqf_audit.py --scan-all` baseline:
    modules/monitoring/monitor.py 80% (OK)
    tools/tco_compact_gate.py    40% (WARN)
    tools/ceps.py                20% (FAIL silent passes)
    tools/tis.py                 20% (FAIL silent passes)
    tools/jit_skill_loader.py    20% (FAIL silent passes)
  The low scores reflect honest deuda -- PP fail-open patterns
  flagged by ErrorNeverSilent. Each is documented and threshold
  is 0% baseline at v1; future cycles raise it.
- verify_spp.py now has 12 rows; 10/12 STRICT OK (2 pre-existing
  Pane-N apex drift FAILs continue, unchanged by this cycle).
- 17 rule files written with ECC MIT attribution footer.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C14
  (ECC-UQF-Active-by-default).
- `vault/knowledge_base/ecc-reverse-engineering.md` -- full
  technical analysis.
- `vault/knowledge_base/ecc-universal-baseline.md` -- 12-principle
  reference catalog.
- `rules/common/code-review.md` -- absorbed Pre-Report Gate +
  Common False Positives + Proof Triad + Severity Table.

### Asymmetric complement to PP-native axes

This axis is the FIRST one where PP imports an external system's
doctrine. The prior 7 axes (Concurrency, Async-Audit, Zero-Drift,
Context-Pressure, Session-Safety, Skill-Completion, TIS, TCO,
Monitoring) are PP-native. ECC is in the same niche but emphasizes
different things (61 agents, 246 skills, multi-harness distribution,
industrial test corpus). PP -> ECC absorption is one-way for this
axis; PP retains its own axes intact.

Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa.
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
    ok &= append_section(PP_SCS, C14_MARKER, C14_BODY)
    ok &= append_section(LOOSE_SCS, C14_MARKER, C14_BODY)
    ok &= append_section(PP_APEX, APEX_MARKER, APEX_BODY)
    ok &= append_section(LOOSE_APEX, APEX_MARKER, APEX_BODY)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
