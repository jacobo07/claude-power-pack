# kpp-distiller-kernel

**KobiiDistillerOS kernel** — the schema-driven contract + 3 pre-emit gates
(anti-scaffold guard · ROI parser · Hawkins scorer), packaged as a real
pip-installable Python module so it can be the **Single Source of Truth**
for any KobiiCraft project that needs the v1.2 distillation contract.

Born from ULTRA-PLAN v230000 — THE GREAT UNIFICATION
(2026-05-15, Owner-ratified Opt D Hybrid Kernel-Only).

## What it is (and what it is not)

**Is**: the *contract* surface + the three pure, testable gates that
every Tier artifact must pass before it ships:

| Module | Purpose |
|---|---|
| `kpp_distiller_kernel.contract` | Loads `schema.json` (v1.2.1, 22 sections × Tandas/Partes) and re-exports `SECTION_TITLES`, `TIER_SECTIONS`, every marker, `GAP_MARKER`, `is_gap_section`, `tier_of`. |
| `kpp_distiller_kernel.placeholder_guard` | Pure scan over Markdown text → `list[Violation]` of scaffold-token matches. Honors backtick / code-fence stripping and the canonical gap-marker whitelist. |
| `kpp_distiller_kernel.roi_calculator` | Parses the canonical `🧮 Calculadora de ROI` block (5 fields) → `ROICalc` Pydantic v2 model. Raises `ROIParseError` if malformed. |
| `kpp_distiller_kernel.hawkins_gate` | Self-contained Hawkins Map-of-Consciousness scorer (EN+ES synonym table). Returns the weighted Hawkins value (0-1000). |
| `kpp_distiller_kernel.gate_runner` | `run_all_gates(artifact, hawkins_floor=200) → GateVerdict`. Mutates the artifact's `gate_*` fields per the kernel contract. |

**Is not**: the orchestrator, the FastAPI router, the LIVE LLM caller, the
ingestor, the emitter, the vaccine synthesizer, or the CLI. Those are
**orchestrator-layer concerns** and live in the project repo that consumes
this kernel.

## Install (editable)

```bash
# repo venv (the consumer)
pip install -e /path/to/claude-power-pack/kpp-distiller-kernel
```

Editable install = source edits in PP propagate to the next Python run in
the repo without a re-install. That is the "auto-sync engine" the
unification mandate asked for; the mechanism is `pip`'s own `-e`.

## Usage

```python
from kpp_distiller_kernel import (
    Violation, ROICalc, ROIParseError, GateVerdict,
    run_all_gates, scan_placeholders, parse_roi, evaluate_hawkins,
    SECTION_TITLES, TIER_SECTIONS, ROI_BLOCK_MARKER, CIERRE_MARKER,
    ORACLE_MARKER, KILL_SWITCH_MARKER, DATASET_FINAL_MARKER,
    GAP_MARKER, TIER_END_MARKERS, is_gap_section, tier_of,
)
```

The KobiiCraft repo re-exports these symbols at the legacy paths
(`kobicraft_content_intelligence.distiller.kernel.*`) so existing consumers
work byte-identical — no code rewires required.

## Schema source

`schema.json` is shipped as package data and is the **canonical** schema
file. The PP also keeps a copy at `tools/distiller/schema.json` for the
in-session `/cpp-distill` slash command, kept aligned by the
`scripts/check_kernel_drift.py` guard in the consumer repo.

## Versioning

- `kpp-distiller-kernel` package version: `0.1.0` (v230000 birth).
- Schema version it pins: `1.2.1`.

A mismatch between the loaded schema's `version` field and the kernel's
`SCHEMA_VERSION` constant raises loudly at import — no silent drift.

## Provenance

- Doctrine: `~/.claude/CLAUDE.md` "Documentation contract (KobiiDistillerOS v1.2 Sovereign Sealing)".
- Audit chain: `docs/audit/KOBIIDISTILLER_RETRO_AUDIT_v220000.md` (in the consumer repo).
- Governance: ceiling v5.5 (Owner-ratified hard-block commit gate); ceiling v5.4 sealed.
