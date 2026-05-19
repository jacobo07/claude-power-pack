---
name: cpp-distill
description: "Atomic-ingest + 22-section distillation + IRE-Stage-7 materialization. Reads a raw dataset, applies the Mother Prompt verbatim, writes Tier_N/Seccion_N.md across 22 sections with Tandas & Partes structural layer + ROI blocks, then validates. Subcommands: ingest (default) / check."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# /cpp-distill — KobiiDistillerOS (v1.2 Sovereign Sealing)

Project-agnostic distillation pipeline. Takes a single source file (text, markdown, dump), runs it through the **Atomic Ingestor** (size cap + placeholder rejection + secret redaction + chunking), drives the **Distillation Engine** in-session against the **Mother Prompt** at `parts/sleepy/distiller.md`, and **Materializes** the result as 22 section files following the verbatim dataset markers.

The driver is the running Claude session itself (no external API). Tokens are spent against your active Power-Pack context; the Mother Prompt is the only compression layer.

---

## Invocation

```
/cpp-distill distill <source-file> [--global] [--live]   # zero-token deterministic engine (DEFAULT)
/cpp-distill <source-file> [--global] [--force] [--scope-only]   # in-session LLM driver
/cpp-distill check <path>
```

Underlying CLI surface (used by the in-session driver and CI):

```
python tools/distiller/run.py distill <source> [--global] [--live]
python tools/distiller/run.py ingest <source> [--global] [--force] [--scope-only] [--verify]
python tools/distiller/run.py check <output-dir>
python tools/distiller/run.py <source> ...      # back-compat → ingest
```

Arguments:

- `<source-file>` — absolute or CWD-relative path to the raw input.
- `--global` — write outputs under `~/.claude/knowledge_vault/distilled/<source-stem>/` instead of `./.knowledge_vault/distilled/<source-stem>/`.
- `--force` — override the 1 MB hard input cap (slow / costly; the cap is there to stop accidental whole-repo dumps).
- `--scope-only` — emit only the `READY.md` orchestration manifest; do not write any Tier_N section files. Useful for dry-runs.
- `--live` — (`distill` only) opt into LIVE Anthropic mode. Default is DRY_RUN: the canonical engine's deterministic synthesizer materializes all 22 Tandas/Partes sections with **zero token spend**.
- `check <path>` — walk an existing output directory and run the validator. Wraps `validate.py`; same exit codes.

### `distill` — deterministic engine (preferred)

`run.py distill` subprocesses the canonical KobiiCraft engine
(`kobicraft_content_intelligence.distiller.cli`) with explicit `cwd` +
`PYTHONPATH`, then chains the validator. It is a **cross-repo dependency**:
the engine root must be exported as `KOBII_DISTILLER_ENGINE_ROOT` (the
KobiiCraft repo root). If unset/invalid, `distill` exits **3** with a precise
remediation message and **never** silently falls back to the in-session LLM
path (loud-degradation rule — Mistake #37). DRY_RUN needs no API key.

If no argument is passed, AskUserQuestion: **"Which file do you want to distill? Provide an absolute path or a path relative to the current project."**

---

## Step 1 — Pre-flight (Atomic Ingestor)

Always run the ingestor first. Never feed raw input to the distillation step.

```bash
python tools/distiller/ingest.py <source-file> [--force]
```

The ingestor:

- Asserts size ≤ 1 MB unless `--force` is set.
- Aborts (exit 2) if the input contains literal placeholder tokens outside Markdown code fences (`TODO`, `FIXME`, `HACK`, `PLACEHOLDER`, `Coming Soon`, `<TU_URL_REAL>`, `raise NotImplementedError`, etc.). The Reality Contract is enforced at input as well as output. Meta-discourse inputs (documents that name the forbidden tokens) can be wrapped in backticks to demote the mention to a documented enumeration rather than a violation.
- Redacts secrets in-place (Discord webhook URLs, SSH private-key blocks, SSH key paths `~/.ssh/<name>`, `kobicraft_*` token patterns, AWS access keys, GitHub PATs, Bearer JWTs, generic `api_key=...` patterns) and replaces them with `[REDACTED:<type>]`. The original file is never modified; the redacted output is written to a sidecar.
- Chunks the source on `^## ` headings, falling back to 50 KB blocks.
- Emits a sidecar `<source-stem>.ingest.json` next to the raw input with `{size_bytes, chunks: [...], redactions: [...]}`.

A lightweight `--scan-only` mode runs gates 2+3 over an arbitrary input file (e.g. for Reality-Contract probes against documentation) and exits 0/2 with a JSON summary; no sidecar is written.

If the ingestor exits non-zero, abort the slash-command run and surface the exit code + message to the operator.

## Step 2 — Resolve output root

Compute:

```
stem = basename(source-file) without extension
default = ./.knowledge_vault/distilled/<stem>/
global  = ~/.claude/knowledge_vault/distilled/<stem>/
output_root = global if --global else default
```

Create `output_root/Tier_1/`, `output_root/Tier_2/`, `output_root/Tier_3/`. The schema assigns sections to tiers — see `tools/distiller/schema.json#tier_layout`.

## Step 3 — Load the Mother Prompt

Read `parts/sleepy/distiller.md` (lazy-loaded; do NOT inline at session start). The Mother Prompt defines:

- The 22 section titles (verbatim from the dataset).
- The Tandas & Partes structural contract (T1 Baseline / T2 Chase-Gain / T3 Síntesis × Parte I Narrativa / II Estructura / III ROI).
- The mandatory per-section blocks (`🧮 Calculadora de ROI`, `🏁 Cierre patrimonial`, `🦅 Comentario del Oráculo`).
- The tier-end markers (`-- FIN DE TIER 1 --` after §7, `-- FIN DE TIER 2 --` after §13, `-- FIN DE TIER 3 --` after §22).
- The dataset-final marker (`-- FIN DE DATASET v1.2 --`).
- The canonical `🧨 KILL-SWITCH` marker (lives inside §16 T3).

## Step 4 — Materialize (IRE Stage 7)

For each section N (1..22), use the Mother Prompt to draft a markdown file at `output_root/Tier_<T>/Seccion_<N>.md`. Every section MUST contain:

1. A heading `## N. <SECTION_TITLE>` (titles from `schema.json#section_titles`).
2. Tandas & Partes body: every section declares all three depth-tandas (T1 / T2 / T3) and all three orthogonal partes (I / II / III) per tanda. Validator exit 1 if any marker is missing.
3. A `🧮 Calculadora de ROI` block with all required fields (`Tipo`, `ROI Temporal`, `ROI Riesgo`, `Escenario`, `Explicación`).
4. A `🏁 Cierre patrimonial` closing line.
5. A `🦅 Comentario del Oráculo` aside (1–3 sentences).

After the last section of a tier, append the tier-end marker. After the very last section (§22), append `-- FIN DE DATASET v1.2 --`.

Use the `Write` tool sequentially (one file per call) — bulk parallel writes drop payloads under the current harness.

## Step 5 — Validate

```bash
python tools/distiller/run.py check <output_root>
# or directly:
python tools/distiller/validate.py <output_root>
```

Validator exit codes:

- `0` — pass (every section has its blocks, every tier has its marker, no forbidden tokens, no leaked secrets, voice gate clean).
- `1` — missing-marker (section heading, Tanda or Parte marker, ROI block, tier-end, or final marker absent).
- `2` — forbidden-token (`TODO` / `FIXME` / `Coming Soon` / etc. slipped through outside code fences).
- `3` — redaction-violation (a secret pattern present in output — should never happen post-ingestor; if it does, abort everything and audit).
- `4` — schema-parse error (`schema.json` itself is malformed).
- `5` — voice-gate violation (`schema.voice_gate.mode == "enforcing"`; corporate blacklist hit AND zero nostalgic anchor hits across the aggregated output; global scope).

If exit ≠ 0, surface the validator output verbatim and STOP. Do not auto-fix and re-run — the operator decides.

## Step 6 — Visual eyeball (first-run mandate)

On the FIRST `/cpp-distill` invocation against any source file, after validator passes, open `output_root/Tier_1/Seccion_1.md` and compare against `fixtures/expected/Tier_1/Seccion_1.md`. Confirm structural parity (heading + Tandas/Partes shape + ROI block + closing markers). If a discrepancy exists, treat as failure and re-iterate via the universal iteration protocol at `~\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-visual.txt`.

Subsequent runs skip the eyeball step unless the operator passes `--review`.

---

## Reality Contract (vMAX-NULL-ERROR)

- Zero placeholders in output. Validator exit code 2 = hard stop.
- Zero leaked secrets. Validator exit code 3 = audit incident.
- Empty buttons / 401-style stub responses / `Coming Soon` blocks are treated as forbidden tokens — the schema regex catches them at validate time.
- Voice gate enforcing (exit 5): blacklist of corporate vocabulary AND nostalgic anchors aggregated globally. If your output is ALL corporate AND zero Refugio / MCPE / 2014 / Helsinki / etc., the validator hard-fails.
- Snowball: every operator-correction round-trip is appended to `vault/knowledge_base/session_lessons.md` with date + symptom + root cause + fix + vaccine.

## Out of scope (future cycle)

Whisper audio ingestion · vision/video DNA · the "Concilio de 22 Agentes" parallel swarm · ROI Predictor pre-gate · Helsinki Live-Feed wiring · external Claude/Gemini API drivers. Each is a separate `/ultra` cycle.

## Reference

Born of `/ultra plan kobiidistilleros-genesis` (2026-05-14). v1.2 Sovereign Sealing landed by `/ultra plan` — 22-section singularity with Tandas & Partes structural layer. Snowball ledger: `vault/knowledge_base/session_lessons.md`.
