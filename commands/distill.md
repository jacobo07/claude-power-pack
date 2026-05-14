---
name: cpp-distill
description: "Atomic-ingest + 19-section distillation + IRE-Stage-7 materialization. Reads a raw dataset, applies the Mother Prompt verbatim, writes Tier_N/Seccion_N.md across 19 sections with ROI blocks, then validates."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# /cpp-distill — KobiiDistillerOS Genesis

Project-agnostic distillation pipeline. Takes a single source file (text, markdown, dump), runs it through the **Atomic Ingestor** (size cap + placeholder rejection + secret redaction + chunking), drives the **Distillation Engine** in-session against the **Mother Prompt** at `parts/sleepy/distiller.md`, and **Materializes** the result as 19 section files following the verbatim dataset markers.

The driver is the running Claude session itself (no external API). Tokens are spent against your active Power-Pack context; the Mother Prompt is the only compression layer.

---

## Invocation

```
/cpp-distill <source-file> [--global] [--force] [--scope-only]
```

- `<source-file>` — absolute or CWD-relative path to the raw input.
- `--global` — write outputs under `~/.claude/knowledge_vault/distilled/<source-stem>/` instead of `./.knowledge_vault/distilled/<source-stem>/`.
- `--force` — override the 1 MB hard input cap (slow / costly; the cap is there to stop accidental whole-repo dumps).
- `--scope-only` — emit only the `READY.md` orchestration manifest; do not write any Tier_N section files. Useful for dry-runs.

If no argument is passed, AskUserQuestion: **"Which file do you want to distill? Provide an absolute path or a path relative to the current project."**

---

## Step 1 — Pre-flight (Atomic Ingestor)

Always run the ingestor first. Never feed raw input to the distillation step.

```bash
python tools/distiller/ingest.py <source-file> [--force]
```

The ingestor:
- Asserts size ≤ 1 MB unless `--force` is set.
- Aborts (exit ≠ 0) if the input contains literal placeholder tokens: `TODO`, `FIXME`, `HACK`, `PLACEHOLDER`, `Coming Soon`, `<TU_URL_REAL>`, `raise NotImplementedError`, `pass # TODO`. The Reality Contract is enforced at input as well as output.
- Redacts secrets in-place (Discord webhook URLs, SSH private-key blocks, SSH key paths matching `~/.ssh/<name>`, `kobicraft_*` token patterns, AWS access keys, GitHub PATs, Bearer JWTs) and replaces them with `[REDACTED:<type>]`. The original file is never modified; the redacted output is written to a sidecar.
- Chunks the source on `^## ` headings, falling back to 50 KB blocks.
- Emits a sidecar `<source-stem>.ingest.json` next to the raw input with `{size_bytes, chunks: [...], redactions: [...]}`.

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
- Section numbering and titles (verbatim from the dataset).
- The mandatory per-section blocks (`🧮 Calculadora de ROI`, `🏁 Cierre patrimonial`, `🦅 Comentario del Oráculo`).
- The tier-end markers (`-- FIN DE TIER 1 --`, etc.).
- The dataset-final marker (`-- FIN DE DATASET v1.0 --`).

If the Mother Prompt contains the line `<<AWAITING OWNER VERBATIM>>` anywhere, halt immediately with:
> *"The Mother Prompt is still a scaffold — Owner must paste the verbatim template before /cpp-distill can run end-to-end. Sections 1–6 are inferred and safe to draft, but 7–19 will refuse to materialize until the gap-marker is removed."*

## Step 4 — Materialize (IRE Stage 7)

For each section N (1..19), use the Mother Prompt to draft a markdown file at `output_root/Tier_<T>/Seccion_<N>.md`. Every section MUST contain:
1. A heading `## N. <SECTION_TITLE>` (titles from `schema.json#section_titles`).
2. Body content distilled from the ingestor's chunks. No filler. No `TODO`. No placeholder UI / button / endpoint references.
3. A `🧮 Calculadora de ROI` block with all required fields (`Tipo`, `ROI Temporal`, `ROI Riesgo`, `Escenario`, `Explicación`).
4. A `🏁 Cierre patrimonial` closing line.
5. A `🦅 Comentario del Oráculo` aside (1–3 sentences).

After the last section of a tier, append the tier-end marker. After the very last section, append `-- FIN DE DATASET v1.0 --`.

Use the `Write` tool sequentially (one file per call) — bulk parallel writes drop payloads under the current harness.

## Step 5 — Validate

```bash
python tools/distiller/validate.py <output_root>
```

Validator exit codes:
- `0` — pass (every section has its blocks, every tier has its marker, no forbidden tokens, no leaked secrets)
- `1` — missing-marker (section heading, ROI block, tier-end, or final marker)
- `2` — forbidden-token (`TODO` / `FIXME` / etc. slipped through)
- `3` — redaction-violation (a secret pattern present in output — should never happen post-ingestor; if it does, abort everything and audit)
- `4` — schema-parse error (`schema.json` itself is malformed)

If exit ≠ 0, surface the validator output verbatim and STOP. Do not auto-fix and re-run — the operator decides.

## Step 6 — Visual eyeball (first-run mandate)

On the FIRST `/cpp-distill` invocation against any source file, after validator passes, open `output_root/Tier_1/Seccion_1.md` and compare against `fixtures/expected/Seccion_1.md`. Confirm structural parity (heading + ROI block + closing markers). If a discrepancy exists, treat as failure and re-iterate via the universal iteration protocol at `C:\Users\kobig\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-visual.txt`.

Subsequent runs skip the eyeball step unless the operator passes `--review`.

---

## Reality Contract (vMAX-NULL-ERROR)

- Zero placeholders in output. Validator exit code 2 = hard stop.
- Zero leaked secrets. Validator exit code 3 = audit incident.
- Empty buttons / 401-style stub responses / `Coming Soon` blocks are treated as forbidden tokens — the schema regex catches them at validate time.
- Snowball: every operator-correction round-trip is appended to `vault/knowledge_base/session_lessons.md` with date + symptom + root cause + fix + vaccine.

## Out of scope (future cycle)

Whisper audio ingestion · vision/video DNA · the "Concilio de 19 Agentes" parallel swarm · ROI Predictor pre-gate · Helsinki Live-Feed wiring · external Claude/Gemini API drivers. Each is a separate `/ultra` cycle.

## Reference

Born of `/ultra plan kobiidistilleros-genesis` (2026-05-14). Dataset: `Dataset KobiiDistillerOS 1.txt`. Snowball ledger: `vault/knowledge_base/session_lessons.md`.
