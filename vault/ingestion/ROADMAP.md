---
title: Power Pack Ingestion Roadmap (k_qa v9500.0)
generated: 2026-04-25
status: research-complete · awaiting per-MC selection
---

# Power Pack Ingestion Roadmap

The session opened with a request to ingest 5 trending repos + 8 critical skills in one turn. That is **scaffolding by definition** under the Reality Contract — each repo has a real install footprint that can't be wired end-to-end in a single MC. This document replaces "ingest everything" with a per-MC honesty pass: each named repo verified to exist, install cost estimated, redundancy with already-installed skills checked, recommendation explicit.

The decision rule below: **execute one MC per session, end-to-end.** No skeletons, no half-wires.

---

## MC-ING-1 — Frontend & Design

| Field | Value |
|-------|-------|
| Named repo | `claude-code-best-practice` |
| Verified URL | <https://github.com/shanraisshan/claude-code-best-practice> |
| What it is | Reference implementation showing patterns for skills/subagents/hooks/commands. NOT a runtime to integrate — it's a "read like a course" repo. |
| Named skill | "Frontend Aesthetic" (87% maturity) |
| Installed equivalents | `frontend-design:frontend-design` + `ui-ux-pro-max:ui-ux-pro-max` (50 styles, 21 palettes, 9 stacks, shadcn/ui MCP) — **both already in your active skill list.** |
| Install cost | ~0 (would only add documentation cross-references) |
| Net-new value | Low. Studying `shanraisshan/claude-code-best-practice` patterns is worth a single read; cherry-picked patterns can flow into Power Pack via vault notes, not via wholesale ingestion. |
| **Recommendation** | **DEFER → drop to a vault reading-list entry.** No commit needed. |

---

## MC-ING-2 — Developer Superpowers & Automation

| Field | Value |
|-------|-------|
| Named repo | `Archon` |
| Verified URL | <https://github.com/coleam00/Archon> (the canonical one — there are 4 same-named projects; this is the workflow engine matching the user's description) |
| What it is | YAML-defined AI-coding workflow engine (plan → implement → validate → review → PR). Real Python project. |
| Named skill | "Superpowers" (96k stars) |
| Installed equivalents | Full `superpowers:*` suite **already installed and active** — `superpowers:executing-plans`, `superpowers:writing-plans`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:writing-skills`, `superpowers:dispatching-parallel-agents`, `superpowers:using-git-worktrees`, `superpowers:requesting-code-review`, `superpowers:receiving-code-review`, `superpowers:verification-before-completion`, `superpowers:subagent-driven-development`, `superpowers:using-superpowers`, `superpowers:finishing-a-development-branch`, `superpowers:brainstorming`. (~14 skills.) |
| Install cost — Superpowers | 0 (already done). |
| Install cost — Archon | ~1–2 days. Archon needs: clone → install Python deps → write a `/archon-run <workflow.yaml>` slash command that shells into the Archon CLI → vault docs for the YAML schema. Real but bounded. |
| Net-new value | **Archon-only.** Workflow engine adds deterministic multi-step execution that Power Pack's current command set doesn't have. |
| **Recommendation** | **PARTIAL ACCEPT.** Skip the Superpowers piece (already installed). For Archon: greenlight as a single-MC ingestion in a future session — clone-install-wrap workflow only, no schema rewrites. |

---

## MC-ING-3 — Financial & Investment Intelligence

| Field | Value |
|-------|-------|
| Named repo | `AI Hedge Fund` |
| Verified URL | <https://github.com/virattt/ai-hedge-fund> (51k+ stars confirmed, multi-agent architecture confirmed) |
| What it is | FastAPI + LangGraph + React-Flow visual editor. 18 agents: 12 legendary-investor personas (Damodaran, Graham, Buffett, Munger, Ackman, Wood, Burry, …) + 6 specialists (valuation, sentiment, fundamentals, technicals, risk, portfolio). Educational license (research-only). |
| Named skill | Damodaran/Graham valuation agents |
| Installed equivalents | `predicting-market-opportunities` (paper-trading) is partial overlap. `/ira` (Investment-Ready Audit, shipped this branch) covers code-level investment readiness, NOT public-equity valuation. |
| Install cost | ~3–5 days. Real cost: market-data API keys (Financial Modeling Prep, Polygon.io, Alpha Vantage), LangGraph deps, persistence for backtest history, decision on whether to shell-out to AI Hedge Fund's CLI or vendor a subset of the agents. License is "educational only" — distribution constraint. |
| Net-new value | High. Real net-new capability: equity due-diligence on tickers via legendary-investor consensus. Maps onto MC-OVO-91 cascade-style multi-advisor pattern we already use for OVO. |
| **Recommendation** | **DEFER WITH ROADMAP.** Don't attempt this turn. When tackled, scope it as: (a) `/ira-public <TICKER>` slash command that shells to virattt/ai-hedge-fund's CLI; (b) parse its JSON output; (c) render with the existing `lib/report.js` patterns. Single-MC commitment, but it requires the Owner to provide API keys before first run. |

---

## MC-ING-4 — Media & Voice Synthesis

| Field | Value |
|-------|-------|
| Named repo A | `Voicebox` (jamiepine/voicebox) |
| Verified URL A | <https://github.com/jamiepine/voicebox> (open-source ElevenLabs alternative; 7 TTS engines: Qwen3-TTS, Qwen CustomVoice, LuxTTS, Chatterbox Multilingual / Turbo, HumeAI TADA, Kokoro). |
| What it is | Local-first desktop app. NOT a Python library to import — it's a standalone Tauri/Electron-style app with its own UI. Meta's Voicebox model is **not** publicly released; this is a community alternative. |
| Named repo B | `Remotion` |
| What it is | Node-based programmatic video framework. Heavy: needs Node + ffmpeg + the Remotion studio. |
| Install cost | ~5–7 days for either. Voicebox: model weights + GPU optional, ~10 GB disk. Remotion: Node ecosystem, separate npm project. |
| Net-new value | High but **not naturally a slash-command integration** — Voicebox runs as its own desktop app; Remotion runs as its own Node project. The honest integration is a `/voice <text>` command that shells to a Voicebox CLI binary IF one exists locally, plus a `/render-video` that shells to Remotion. Both are wrappers, not deep ingestions. |
| **Recommendation** | **DEFER + DECOUPLE.** Owner installs Voicebox / Remotion locally first. Power Pack adds two thin shell wrappers (`/voice`, `/render-video`) only after the binaries exist on PATH. Estimated wrapper cost once binaries exist: ~2 hours each. |

---

## MC-ING-5 — Context & Memory Optimization

| Field | Value |
|-------|-------|
| Named repo | `Claude-Mem` |
| Verified URL | <https://github.com/thedotmack/claude-mem> (46.1K stars, v12.0.0, 223 releases, single-command install: `npx claude-mem install`) |
| What it is | Claude Code plugin. Auto-captures tool usage, generates semantic summaries via the Claude Agent SDK, stores in local SQLite + ChromaDB vector index. Hooks into Claude Code's session lifecycle — same hook surface our `lazarus-snapshot.js` already uses. |
| Named skill | "Context Optimization" (claimed 80% token reduction) |
| Installed equivalents | `modules/memory-engine/append_memory.py` + `modules/memory-engine/MEMORY.md` infrastructure. **Different shape** — ours is per-project markdown; claude-mem is global SQLite + vector. They are complementary, not redundant. The Lazarus snapshot system we just shipped (`tools/lazarus_revive_all.py`) already touches the same hook surface. |
| Install cost | ~1 turn. Single-command install. Then a Power Pack collision audit: confirm claude-mem's hooks don't fight with our `lazarus-snapshot.js` and `lazarus-heartbeat.js` (both on the same `Stop` and `PreToolUse` events). |
| Net-new value | **Highest leverage.** Vector-search over past sessions is a real capability we don't have. The 80% token-reduction claim deserves a measured benchmark, not a copy-paste. |
| **Recommendation** | **EXECUTE NEXT SESSION.** Single-MC scope: `npx claude-mem install` → run for one session → diff actual token usage before/after on a real workflow → audit hook collision against our existing `~/.claude/hooks/lazarus-*` files → either ship a vault note documenting the integration or roll back if there's a hook fight. Real evidence, real decision. |

---

## Summary table

| MC | Net-new value | Redundancy | Decision |
|----|---------------|------------|----------|
| 1 — Frontend | Low | High (`frontend-design`, `ui-ux-pro-max` already active) | **DEFER → vault reading-list entry** |
| 2 — Superpowers | Low (suite installed); Archon = medium net-new | High (Superpowers); none for Archon | **DEFER Superpowers; PARTIAL ACCEPT Archon for a future single-MC** |
| 3 — Hedge Fund | High | Partial (`/ira` covers code; this covers equities) | **DEFER WITH ROADMAP — needs API keys + 1 single-MC** |
| 4 — Voicebox/Remotion | High | None | **DEFER + DECOUPLE — install local apps first, then thin wrappers** |
| 5 — claude-mem | Highest | None (complementary to our memory engine) | **EXECUTE NEXT SESSION — single-command install + collision audit + measured benefit** |

## Honest gaps in the original prompt

- **"5 repos + 8 skills" was 5 + ≈5.** The user's prompt itemized 5 MCs, each pairing one repo with one named skill (so 10 named items, but several skills were already installed). True net-new repos to ingest = 4 (Archon, AI Hedge Fund, Voicebox, claude-mem); MC-ING-1's "claude-code-best-practice" is a reference, not a runtime.
- **Two of the five were already installed** as skill plugins (`frontend-design`, `superpowers:*`), making MC-ING-1 and MC-ING-2's skill-side a documentation-only pass.
- **"Claude-Mem" is the highest-leverage genuinely-novel piece** and is also the cheapest to install — it's a single npx command. Doing it first generates measurable evidence that informs whether the others are worth pursuing.

## Recommended sequencing

1. **Next session:** MC-ING-5 (claude-mem) — install + collision audit + measured token benefit. ~1 turn end-to-end.
2. **Session +2:** MC-ING-2 partial (Archon wrapper). ~1 turn for `/archon-run` shell wrapper + vault docs.
3. **Session +3:** MC-ING-3 with API keys (`/ira-public <TICKER>`). Owner-supplied keys gate this.
4. **Sessions +4 / +5:** MC-ING-4 (`/voice`, `/render-video`) — only after Owner has Voicebox + Remotion binaries on PATH.
5. **Closure:** MC-ING-1 collapses to a vault reading-list entry (~5 min, can fold into any session).

Sources for verification this turn:
- [coleam00/Archon](https://github.com/coleam00/Archon)
- [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)
- [jamiepine/voicebox](https://github.com/jamiepine/voicebox)
- [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
- [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice)
