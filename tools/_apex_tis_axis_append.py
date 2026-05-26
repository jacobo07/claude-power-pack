#!/usr/bin/env python3
"""M9 -- atomic append of `Token Intelligence (TIS) Axis v1 (sealed
2026-05-26)` section to apex-completion-standard.md on both loose and
PP mirrors. SCS C6 atomic-write + idempotent on marker.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

PP = Path("knowledge_vault/core/apex-completion-standard.md")
LOOSE = Path(os.path.expanduser(
    "~/.claude/knowledge_vault/core/apex-completion-standard.md"))

MARKER = "## Token Intelligence (TIS) Axis v1 (sealed 2026-05-26)"
AXIS = """

## Token Intelligence (TIS) Axis v1 (sealed 2026-05-26) -- cost-visibility baseline

A new PP feature that calls a Claude model OR injects context into the
prompt pipeline is complete only when its activity is visible in the
TIS log AND its handoff summarizer can produce a real
`recommended_action`. Until 2026-05-26 there was no cost telemetry on
the trigger matrix; this axis closes that gap as the sixth standard
DONE axis alongside Concurrency, Async-Audit, Zero-Drift Mirror,
Context-Pressure, Session-Safety, and Skill-Completion.

### Five required components (all five must be present for Apex-complete)

1. **Logger** -- `tools/tis.py` (`TokenEvent` dataclass +
   `append_log` + `read_log` + `get_session_id`). Stdlib only;
   atomic-write for the session id sidecar. JSONL append-only to
   `vault/token_logs/YYYY-MM-DD.jsonl`.
2. **Analytics CLI** -- `tools/tis_report.py` with four flags:
   `--summary`, `--by-skill`, `--cache-ratio`, `--since`. ASCII
   tables, stdlib only. `PRICING` constant for Sonnet 4.6 / Opus 4.7 /
   Haiku 4.5 (extensible).
3. **Handoff summarizer** -- `tools/tis_handoff.py` reads the active
   session log and emits a `<context_summary>` block with
   `top_3_expensive_calls`, `compression_candidates`,
   `estimated_savings_next_session_tokens`, `recommended_action`.
   Honest fallback: `INSUFFICIENT_TELEMETRY` / `NO_CANDIDATES_DETECTED`
   are explicit reasons -- never silent zero (Reality Contract).
4. **JIT hook** -- `tools/jit_skill_loader.py::_tis_log_call` decorator
   wraps `run()` and records a per-call event. Fail-open on any
   internal error.
5. **verify_spp probe** -- `tools/verify_tis.py` 4-check probe + a
   row in `tools/verify_spp.py::rows_spec`. Confirms the system is
   alive from cold state.

### Five-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the Token Intelligence Axis iff:

1. `tools/test_tis_core.py` exit 0 with TIS_CORE_PASS=6/6.
2. `tools/test_tis_e2e.py` exit 0 with E2E_PASS=4/4.
3. `tools/verify_tis.py` exit 0 with TIS_PROBE=4/4.
4. `tools/tis_report.py --summary` returns at least one row of real
   data (no synthetic-only sessions).
5. `tools/tis_handoff.py` writes a `vault/token_logs/handoff_*.md`
   with a real, non-empty `recommended_action`.

Missing any of 1-5 = NOT Apex-complete on the TIS Axis.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C11 (Token-
  Intelligence-by-default): the per-skill obligation derived from
  this axis.
- `tools/tis.py`, `tools/tis_report.py`, `tools/tis_handoff.py`,
  `tools/verify_tis.py`, `tools/test_tis_core.py`,
  `tools/test_tis_e2e.py`: the substrate.
- Sister modules: `modules/token-optimizer/token_autopsy.py`
  (post-mortem parser of `~/.claude/projects/` session JSONL). TIS
  is the live per-skill logger; token_autopsy is the forensic
  cross-session parser. They are complementary.

### Empirical proofs (2026-05-26)

- M1 self-probe: round-trip preserved `input_tokens=100`.
- M2 V-TIS-* 6/6: APPEND / IDEMPOTENT / SCHEMA / SESSION / PERSIST / NONZERO.
- M3 hook fires on real `jit_skill_loader.run()`: captured
  `input_tokens=12 / output_tokens=157 / call_label=jit-context-injected`
  on an LT trigger prompt.
- M4 `--summary` / `--by-skill` / `--cache-ratio` / `--since`: all
  4 flags emit non-empty tables with real data.
- M5 handoff emits `<context_summary>` with honest
  `NO_CANDIDATES_DETECTED` when applicable.
- M6 E2E 4/4: 3 mock dispatches -> `tis_report` non-empty ->
  `tis_handoff` detects compression candidate on repeated call_label.
- M7 verify_spp row `tis-probe` PASS in <1s.
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


def append_axis(target: Path) -> bool:
    if not target.is_file():
        print(f"missing: {target}", file=sys.stderr)
        return False
    body = target.read_text(encoding="utf-8")
    if MARKER in body:
        print(f"TIS axis already present in {target} (idempotent skip)")
        return True
    if not body.endswith("\n"):
        body += "\n"
    _atomic_write(target, body + AXIS)
    print(f"TIS axis appended to {target} (bytes={target.stat().st_size})")
    return True


def main() -> int:
    ok = True
    ok &= append_axis(PP)
    ok &= append_axis(LOOSE)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
