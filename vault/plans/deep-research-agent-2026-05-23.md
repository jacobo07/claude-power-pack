---
title: Deep Research Agent — ULTRA PLAN
date_started: 2026-05-23
status: ACCEPTED — execution in progress
branch: feat/rtk-compressor-fusion
spec: vault/specs/deep-research-agent.md
forbidden_runtimes: n8n (per feedback_no_n8n_ever)
defaults_at_accept:
  clarifying_step: opt-in via --clarify
  llm_model: env CLAUDEPP_RESEARCH_MODEL (default Sonnet)
  auto_spawn_threshold: verb match + 80 words
---

# Deep Research Agent — Execution Plan

## Objective

Build the Deep Research Agent as a native PP module that runs in the
background and produces real research reports while the Owner is away.
Auto-activation when prompt signals research intent. Output to
`vault/research/<ts>_<slug>.md`. The source-material is an n8n workflow;
the deliverable is pure Python (n8n is forbidden).

## Reality contract (the hard floor)

A research report exists in `vault/research/` or it does not. Timestamps
do not lie. Sources are real URLs or they are not. Fabricated content
without real search = bug, not feature. Empty SERP + no API keys =
`CEILING.md` + abort, never invented results.

## The 19 Pasos (clickable mirror lives in chat transcript)

| # | Paso | Component |
|---|---|---|
| PRE-1 | Scaffold dirs + branch confirm | preparation |
| 1.1 | Module skeleton + ctypes priority drop | core |
| 1.2 | Web search cascade (DDG → Brave → Apify) | core |
| 1.3 | Page fetch + HTML→markdown | core |
| 1.4 | LLM cascade (claude.exe → claude-api) | core |
| 1.5 | generate_serp_queries (verbatim prompt) | core |
| 1.6 | extract_learnings (verbatim prompt) | core |
| 1.7 | generate_report (verbatim prompt) | core |
| 1.8 | Recursive driver + governance wiring | core |
| 1.9 | CLI + 3-artifact writer | core |
| 2.1 | commands/cpp-deep-research.md skill | sleepy |
| 2.2 | hooks/research-intent-detector.js Stop hook | sleepy |
| 2.3 | register-deep-research consolidator | sleepy |
| 3.1 | vault/research/ + gitignore | vault |
| 3.2 | SessionStart auto-discovery | vault |
| V1 | Foreground real-network run | verify |
| V2 | Sleepy spawn + discovery | verify |
| POST-1 | apex-completion-standard.md Research Axis | seal |
| POST-2 | Iteration capture | seal |

## Iteration loop

Per Owner template
(`Downloads/Promptsss/Prompts pa iterar/Universal/iteracion-avanzada-universal.txt`):
any done-gate failure → row in
`vault/knowledge_base/session_lessons.md` + cross-ref in
`vault/knowledge_base/ukdl-universal.md`. POST-2 enforces this.

## Status log

| Date  | Paso | Result | Notes |
|-------|------|--------|-------|
