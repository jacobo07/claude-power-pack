# `tools/distiller/` — KobiiDistillerOS pipeline (v1.2 Sovereign Sealing)

Atomic ingestion → **22-section** distillation → IRE-Stage-7 materialization. Project-agnostic. Driven in-session by the running Claude Code agent against the Mother Prompt at `parts/sleepy/distiller.md`.

## Layout

```
tools/distiller/
├── schema.json     # 22-section contract + Tandas & Partes spec + ROI fields + forbidden tokens + redaction regexes + voice gate
├── ingest.py       # size cap + placeholder reject + secret redaction + chunking + --scan-only
├── validate.py     # walks output dir; enforces schema + Tandas/Partes + global voice gate
├── run.py          # orchestrator with subcommands: `ingest` / `check` (positional back-compat preserved)
├── cli_help.txt    # --help text rendered by run.py
└── README.md       # this file
```

Companions outside this directory:

- `commands/distill.md` — slash-command spec (`/cpp-distill`).
- `parts/sleepy/distiller.md` — the Mother Prompt (lazy-loaded by the slash command).
- `fixtures/raw_sample.txt` — canonical Owner-provided dataset; meta-mentions of forbidden tokens are backtick-wrapped to demote them from violations to documented enumerations.
- `fixtures/expected/Tier_1/Seccion_1.md` — golden Sección 1 used for first-run visual eyeball.
- `fixtures/expected/ingest_sample.json` — golden ingestor sidecar (9 chunks, 1 ssh_key_path redaction).

## CLI surface

```
/cpp-distill <source-file> [--global] [--force] [--scope-only] [--review]
/cpp-distill check <output-dir>
```

The slash command (the agent-side entry) is the canonical UX. The Python tools are callable directly as a fallback / for CI:

```
python tools/distiller/ingest.py <source-file> [--force] [-o <path>]
python tools/distiller/ingest.py <source-file> --scan-only
python tools/distiller/validate.py <output-dir>
python tools/distiller/run.py ingest <source-file> [--global] [--force] [--scope-only] [--verify]
python tools/distiller/run.py check <output-dir>
python tools/distiller/run.py <source-file> ...     # back-compat → ingest
```

## Output layout

Default (`./.knowledge_vault/distilled/<source-stem>/`) or `--global` (`~/.claude/knowledge_vault/distilled/<source-stem>/`):

```
<output_root>/
├── READY.md             # orchestrator manifest: chunks + Mother Prompt + <<INSTRUCTION TO CLAUDE>>
├── Tier_1/
│   ├── Seccion_1.md
│   ├── ...
│   └── Seccion_7.md     # ends with `-- FIN DE TIER 1 --`
├── Tier_2/
│   ├── Seccion_8.md
│   ├── ...
│   └── Seccion_13.md    # ends with `-- FIN DE TIER 2 --`
└── Tier_3/
    ├── Seccion_14.md
    ├── ...
    └── Seccion_22.md    # ends with `-- FIN DE TIER 3 --` + `-- FIN DE DATASET v1.2 --`
```

The tier layout is declared in `schema.json#tier_layout` — the validator reads it, not this README.

## Tandas & Partes structural layer

Every materialized section MUST partition into three depth-tandas × three orthogonal partes:

| Tanda | Label | Purpose |
|-------|-------|---------|
| T1 | Baseline (esenciales) | Minimum viable signal — what a reader at first contact needs to act today |
| T2 | Chase-Gain (ampliación) | Snowball-effect / rapid-scaling vectors built on top of T1 |
| T3 | Síntesis & Ventaja Estructural | Compounding advantage and irreversible moat |

| Parte | Label | Purpose |
|-------|-------|---------|
| I | Narrativa | Why this exists; human-anchored story; Refugio-voice context |
| II | Estructura | Shape, framework, schematic, operational mechanic |
| III | ROI | tiempo / dinero / riesgo of applying it |

The validator enforces both marker regexes (`tanda_heading_regex`, `parte_heading_regex` from `schema.tandas_partes_spec`) per section file. A section missing any of the three tandas or three partes fails exit 1.

## Exit codes (validator)

| Code | Meaning                                                                                                |
|------|--------------------------------------------------------------------------------------------------------|
| 0    | pass — every block present, structural markers present, no forbidden tokens, no leaked secrets, voice gate clean |
| 1    | missing-marker — section heading, Tanda or Parte marker, ROI block, tier-end, or final marker absent   |
| 2    | forbidden-token — `TODO` / `FIXME` / `Coming Soon` / etc. slipped in (code-fence-aware)                |
| 3    | redaction-violation — a secret pattern surfaced in output (audit incident)                             |
| 4    | schema-parse error — `schema.json` itself is malformed                                                 |
| 5    | voice-gate violation — `mode == "enforcing"`; blacklist hit AND zero anchor hits (global scope)        |

## Adversarial gates (ingestor)

- **Size cap.** Hard 1 MB. `--force` overrides; the override is logged.
- **Placeholder reject.** Same forbidden-token list the validator uses. Caught at input so it never reaches the LLM context. Code-fence-aware (meta-discourse inputs can wrap mentions in backticks).
- **Secret redaction.** Discord webhooks, SSH private-key blocks, SSH key paths (`~/.ssh/<name>`), `kobicraft_*` tokens, AWS keys, GitHub PATs, Bearer JWTs, generic `api_key=…` patterns. Replaced with `[REDACTED:<type>]`. The original file is never mutated; the redacted source is written to the sidecar.
- **Chunking.** Splits on `^## ` headings, falls back to 50 KB blocks. Chunk boundaries are recorded in the sidecar so distillation can address chunks individually.
- **--scan-only.** Runs gates 2+3 only; prints JSON summary; exits 0 if clean / 2 if dirty. No sidecar written. Used to probe arbitrary documentation files (e.g. the Mother Prompt itself before commit).

## Voice gate (v1.2)

`schema.voice_gate.mode == "enforcing"`. Validator aggregates all materialized section bodies (global scope per `voice_gate.scope`) and scans for two lists:

- **blacklist_candidates** — corporate-vocabulary tokens (`KPI`, `synergy`, `stakeholder`, `roadmap`, `paradigm shift`, etc.).
- **anchors_candidates** — nostalgic / Refugio-voice tokens (`Refugio`, `MCPE`, `2014`, `cabaña`, `linterna`, `Helsinki`, `KobiiCraft`, `Andorra`, etc.).

Exit 5 fires iff ≥1 blacklist hit AND 0 anchor hits across the entire output. Strict Mode (Q2.a Sovereign Sealing).

## Snowball

Every operator-correction round-trip lands as a `## YYYY-MM-DD — <title>` entry in `vault/knowledge_base/session_lessons.md`. Pattern: symptom → root cause → fix → vaccine.

## Status

| Phase | Status | Files |
|-------|--------|-------|
| 0     | done   | hook-utils.js + kobiiclaw-autoresearch.js patched; Snowball logged |
| A     | done   | commands/distill.md + schema.json v1.2.1 + this README |
| B     | done   | parts/sleepy/distiller.md (22 sections, full rewrite); fixtures/raw_sample.txt |
| C     | done   | validate.py (voice gate + Tandas/Partes); ingest.py (--scan-only); fixtures/expected/Tier_1/Seccion_1.md |
| D     | done   | run.py argparse subcommands (ingest/check) + back-compat shim |
| E     | done   | Snowball entries + three-part verification |
