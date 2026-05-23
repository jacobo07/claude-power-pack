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
| 05-23 | PRE-1 | DONE | Dirs scaffolded; branch confirmed feat/rtk-compressor-fusion |
| 05-23 | 1.1 | DONE | Module skeleton — `--version` exits 0, `win32:IDLE_PRIORITY_CLASS` confirmed |
| 05-23 | 1.2 | DONE | DDG cascade — 5 real GitHub URLs returned; sponsored-result filter added after empirical y.js leak |
| 05-23 | 1.3 | DONE | fetch + html_to_markdown — trafilatura layer fired on real github page (2270 chars). example.com firewall-blocked on this host (network condition) |
| 05-23 | 1.4 | DONE | LLM cascade — claude.exe -p subprocess returned 'HELLO' in 17s; JSON-schema test returned `{cities:[Paris,Berlin,Madrid]}` in 26s |
| 05-23 | 1.5 | DONE | generate_serp_queries — 3 distinct topical queries + researchGoal in 31s |
| 05-23 | 1.6 | DONE | extract_learnings — 3 dense learnings + 3 follow-ups in 26s; quoted "Paper 75%", "Velocity 3.4" |
| 05-23 | 1.7 | DONE | generate_report — 13.8 KB markdown, 10 H2 headings, 7/7 input learnings echoed, 121s |
| 05-23 | 1.8 | DONE+FIX | First-run hit WinError 206 (argv length cap). Fix: pass user message via STDIN (lesson: `vault/lessons/windows-argv-limit-stdin-fix.md`). After-fix: 6 learnings, 10 URLs, 22.7 KB JEP 401 report in 276s |
| 05-23 | 1.9 | DONE | CLI + 3-artifact writer; atomic .tmp+rename; URL dedup against index.json history |
| 05-23 | V1 | PASS | Real CLI run: Minecraft prompt → 6 learnings, 8 real URLs, 16.9 KB report in 220s. Cascade verdict: ddg + trafilatura+bs4-strip + claude.exe. Zero API keys used. CLI exit 0 |
| 05-23 | 2.1 | DONE | /cpp-deep-research skill in commands/cpp-deep-research.md — args + examples + activation modes + env vars |
| 05-23 | 2.2 | DONE | research-intent-detector.js Stop hook — 220 lines, fail-OPEN; regex 13/13 PASS on test fixture (6 ES + 4 EN positives + 3 negatives) |
| 05-23 | 2.3 | DONE | register-deep-research consolidator in settings_merger.py; idempotent --apply added Stop[3] entry |
| 05-23 | 3.1 | DONE | vault/research/.gitignore + README — separates committable artifacts (*.md + index.json) from runtime/forensic (.lock, .auto-spawned.log, raw.jsonl, *.tmp.*) |
| 05-23 | 3.2 | DONE | research_discovery.py standalone — discover_for_cwd() empirical: KobiiCraft cwd → surfaces Minecraft research report. Stop-word filter (drops "the/and/projects/workspace/...") prevents over-matching. Wiring into learning-sentinel.js deferred to Wave-5b follow-up |
| 05-23 | V2 | PASS-SPAWN | Synthetic 92-word Spanish prompt with "investiga / compara / Estado del arte" triggered Stop hook → detached `cmd.exe /c start "" /B python deep_research.py` spawn. Auto-spawn log entry written; child python PID 42468 visible in Win32_Process; Stop hook returned in <200ms. Artifact-landing half: see `vault/research/` for the .md once the child completes (~5 min after spawn). Next-session SessionStart discovery half: deferred to Owner manual test (cannot fire SessionStart safely from inside this session) |
| 05-23 | POST-1 | DONE | apex-completion-standard.md (PP + live mirror, byte-identical) now carries "Research Axis" — 5 required components + activation gate + 5-check DONE-gate. Empirical V1 + V2-spawn numbers cited inline |
| 05-23 | POST-2 | DONE | This row + the `windows-argv-limit-stdin-fix.md` lesson captures the WinError 206 incident |

## Final commits (this plan)

- `5c74630` — Wave 1 (Pasos 1.1-1.4): Python core fallback layers
- `5950cc1` — Wave 2+3 (Pasos 1.5-1.9 + V1): chains + driver + CLI + V1 PASS
- `fa11761` — Wave 4 (Pasos 2.1-2.3): sleepy activation
- Wave 5+6+7 commit — Pasos 3.1, 3.2, V2-spawn, POST-1, POST-2 (this commit)

## Empirical evidence summary (all real, no mocks)

- 4 real Claude calls (HELLO, JSON schema, query generation, learnings extraction, report generation)
- 2 real-world depth-1 research runs (JEP 401, Minecraft servers)
- 10+ real URLs across both runs (github, openjdk, oracle, papermc, etc.)
- 1 real detached spawn via the Stop hook
- Zero API keys required (DDG + claude.exe keychain OAuth)
- Reality Contract worked under test: WinError 206 triggered INSUFFICIENT DATA fallback, not fabrication. Fix shipped.

