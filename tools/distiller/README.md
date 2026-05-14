# `tools/distiller/` — KobiiDistillerOS pipeline

Atomic ingestion → 19-section distillation → IRE-Stage-7 materialization. Project-agnostic. Driven in-session by the running Claude Code agent against the Mother Prompt at `parts/sleepy/distiller.md`.

## Layout

```
tools/distiller/
├── schema.json     # markers + ROI fields + forbidden tokens + redaction regexes
├── ingest.py       # Phase C: size cap + placeholder reject + secret redaction + chunking
├── validate.py     # Phase B.2: walks output dir, enforces schema
├── run.py          # Phase D: orchestrator, emits READY.md, calls ingest + validate
├── cli_help.txt    # --help text rendered by run.py
└── README.md       # this file
```

Companions outside this directory:
- `commands/distill.md` — slash command spec (`/cpp-distill`)
- `parts/sleepy/distiller.md` — the Mother Prompt (lazy-loaded by the slash command)
- `fixtures/raw_sample.txt` — canonical Owner-provided dataset, treated as ground truth
- `fixtures/expected/Seccion_1.md` — golden Sección 1 used for Phase A visual eyeball
- `fixtures/expected/ingest_sample.json` — golden ingestor sidecar with expected redactions

## CLI surface

```
/cpp-distill <source-file> [--global] [--force] [--scope-only] [--review]
```

The slash command (the agent-side entry) is the canonical UX. The Python tools are callable directly as a fallback / for CI:

```
python tools/distiller/ingest.py <source-file> [--force] [-o <output-dir>]
python tools/distiller/validate.py <output-dir>
python tools/distiller/run.py <source-file> [--global] [--force] [--scope-only]
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
    └── Seccion_19.md    # ends with `-- FIN DE TIER 3 --` + `-- FIN DE DATASET v1.0 --`
```

The tier layout is declared in `schema.json#tier_layout` — the validator reads it, not this README.

## Exit codes (validator)

| Code | Meaning                                                          |
|------|------------------------------------------------------------------|
| 0    | pass — every block present, no forbidden tokens, no leaked secrets |
| 1    | missing-marker — section heading, ROI block, tier-end, or final marker absent |
| 2    | forbidden-token — `TODO` / `FIXME` / `Coming Soon` / etc. slipped in |
| 3    | redaction-violation — a secret pattern surfaced in output (audit incident) |
| 4    | schema-parse error — `schema.json` itself is malformed             |

## Adversarial gates (Phase C ingestor)

- **Size cap.** Hard 1 MB. `--force` overrides; the override is logged.
- **Placeholder reject.** Same forbidden-token list the validator uses. Caught at input so it never reaches the LLM context.
- **Secret redaction.** Discord webhooks, SSH private-key blocks, SSH key paths (`~/.ssh/<name>`), `kobicraft_*` tokens, AWS keys, GitHub PATs, Bearer JWTs, generic `api_key=…` patterns. Replaced with `[REDACTED:<type>]`. The original file is never mutated; the redacted source is written to the sidecar.
- **Chunking.** Splits on `^## ` headings, falls back to 50 KB blocks. Chunk boundaries are recorded in the sidecar so distillation can address chunks individually.

## Mother Prompt gap-marker (Phase B.1)

`parts/sleepy/distiller.md` ships with Sections 1–6 inferred from the dataset and Sections 7–19 marked `<<AWAITING OWNER VERBATIM — Q1.a>>`. This is **not** a placeholder per the Reality Contract — it is a typed expectation declaring the bind point. `run.py` will halt with a friendly explanation rather than materialize gap-marked sections.

When the Owner pastes the verbatim Mother Prompt, the gap-marker is removed and the full 19 sections become resolvable.

## Snowball

Every operator-correction round-trip lands as a `## YYYY-MM-DD — <title>` entry in `vault/knowledge_base/session_lessons.md`. Pattern: symptom → root cause → fix → vaccine.

## Status (2026-05-14)

| Phase | Status      | Files                                                                    |
|-------|-------------|--------------------------------------------------------------------------|
| 0     | done        | hook-utils.js + kobiiclaw-autoresearch.js patched; Snowball logged       |
| A     | in progress | commands/distill.md + tools/distiller/schema.json + this README          |
| B.1   | pending     | parts/sleepy/distiller.md scaffold + fixtures/raw_sample.txt             |
| B.2   | pending     | tools/distiller/validate.py + fixtures/expected/Seccion_1.md             |
| C     | pending     | tools/distiller/ingest.py + fixtures/expected/ingest_sample.json         |
| D     | pending     | tools/distiller/run.py + cli_help.txt + SKILLBANK.md + INDEX.md edits    |
