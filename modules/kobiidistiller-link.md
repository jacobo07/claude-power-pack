---
name: kobiidistiller-link
description: Pointer to the canonical KobiiDistillerOS at kobicraft_content_intelligence/distiller/ in the KobiiCraft repo. Use when Power Pack users need to destill a raw dataset into a structured Knowledge Vault following the Owner-ratified 22-section Mother Prompt v1.2 schema.
---

# KobiiDistillerOS — canonical pointer (v220000)

**Canonical implementation** lives at `kobicraft_content_intelligence/distiller/` in the KobiiCraft repo. The Power Pack carries this pointer only — there is no in-Pack code copy of the engine.

The Power Pack DOES own a separate operator-UX layer at `tools/distiller/` driven by the `/cpp-distill` slash command. That layer is a thin wrapper for in-session destillation invocation; the heavy lifting (orchestrator, kernel gates, emitter, UKDL bridge) all happens in the canonical KobiiCraft codebase.

## Source of truth

```
<KobiiCraft repo>/kobicraft_content_intelligence/distiller/
├── core/orchestrator.py      # IRE 3-6 (DRY_RUN default + LIVE Anthropic)
├── core/prompt_madre.py      # 22-section Owner-ratified spec
├── ingestor/text_ingestor.py # IRE 1-2 (text modality)
├── kernel/                   # vMAX-NULL-ERROR gates: placeholder, ROI, Hawkins, vaccine_synth
├── emitter/                  # IRE 7: Markdown + UKDL ledger
├── data_contracts/           # Pydantic v2 models
├── cli/                      # python -m ... text|status|verify
└── tests/test_pipeline_e2e   # DRY_RUN end-to-end coverage
```

Companion: `<KobiiCraft repo>/kobicraft_content_intelligence/api/routers/distiller.py` (FastAPI router serving `/api/distiller/*`).

Sealed doctrine: `<KobiiCraft repo>/docs/KOBII_PHILOSOPHY/KOBIIDISTILLER_OS_v1.md` (v220000 reset).

## Install

```bash
cd <KobiiCraft repo>/kobicraft_content_intelligence
pip install -r requirements.txt   # FastAPI + Pydantic v2 + Typer + anthropic (optional)
python -m kobicraft_content_intelligence.distiller.cli --help
```

The `distiller_backend` setting (env or `.env`) picks Anthropic (default), OpenAI, or `auto`. `distiller_dry_run` defaults `true` — no token spend until the Owner explicitly flips it.

## When to use this pointer in a Power Pack session

- The Owner hands over a raw dataset (text dump, transcript, spec, gameplay log) and wants 22 destilled sections in a Knowledge Vault.
- The Owner asks about `/api/distiller/*` HTTP endpoints, `distiller text` / `status` / `verify` CLI commands, or the per-section ROI block + Cierre patrimonial + Comentario del Oráculo contract.
- The Owner references "the 22-section Mother Prompt v1.2 schema" or `Conocimiento Negativo & Cosecha Latente` (section 22).

## When NOT to use this pointer

- The Owner wants the `/cpp-distill` slash command workflow — that's the Power Pack's own `tools/distiller/` + `parts/sleepy/distiller.md` UX, separate surface.
- Whisper transcription / vision-to-data extraction — explicitly **reserved** for a future v-series. Non-text modalities raise `RuntimeError` in the canonical ingestor.
- Audit-trail edits to the Power Pack schema at `tools/distiller/schema.json` — that's spec authoring, distinct from invoking the engine.

## Pillar 3 contract (v1.2 — 2026-05-15)

All 22 section titles are Owner-ratified verbatim. **v1.2 materializes every section — zero gap markers.** The DRY_RUN synthesizer (`orchestrator._build_section_body`) deterministically emits the canonical 3-tanda × 3-parte skeleton (`### Tanda T1/T2/T3` × `#### Parte I/II/III`) for all 22 sections from the dataset's real distilled content — zero tokens, zero fabrication, zero placeholders. `prompt_madre.is_gap_section()` is False for every v1.2 section. (The pre-v1.2 claim that §14-16 were gap-marked is **retired** — see `vault/knowledge_base/session_lessons.md`, 2026-05-15 Verdict-B root cause: a stale doctrine that oversold the engine.)

## Power Pack wiring

`tools/distiller/run.py distill <source>` is the operator entrypoint. It subprocesses this engine with explicit `cwd` + `PYTHONPATH`, DRY_RUN by default, then chains the Power Pack validator. The engine root is a **cross-repo dependency** resolved from `$KOBII_DISTILLER_ENGINE_ROOT` (no hardcoded path — Mistake #36). If unset/invalid, `distill` fails LOUD (exit 3) and never silently falls back to in-session LLM materialization (Mistake #37).

## Historical note (v200000 → v210000 → v220000)

An earlier Python package at `kobiicraft_distiller_os/` (commits `565f462` + `0f91917`) shipped a 19-section schema with author-inferred titles. v220000 audit determined the Owner had ratified a parallel 22-section v1.2 spec elsewhere; the in-repo `kobicraft_content_intelligence/distiller/` codebase aligned with that spec. The 19-section package retired. This pointer was rewritten at v220000 to redirect at the canonical 22-section codebase.

See `vault/audits/verdicts.jsonl` for the v220000 verdict row + audit trail.
