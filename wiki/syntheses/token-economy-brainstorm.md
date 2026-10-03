---
type: synthesis
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research, 2026-10-02-token-economy-external-research-2, 2026-10-02-token-economy-internal-inventory]
---

# Token economy, wave 2: deep measurements and a ranked idea catalogue

Owner asked for "next level research and massive brainstorming" on token saving (Owner,
2026-10-02). Builds on [[token-economy-levers]]. Wave 2 added: a second external survey
([[2026-10-02-token-economy-external-research-2]]) and six new zero-quota transcript instruments in
`wiki/tools/` (`token_economy_deep`, `_listings`, `_coldstart`, `_coldstart_bydir`,
`_prefix_stability`, `_ttl_net`; each with a `.2026-10-02.out`). Same caveats as wave 1: USD is a
list-price estimate, not the weekly meter; bounds overlap.

## 1. What the new instruments found (7 d, main thread unless noted)

| # | finding | number | instrument |
|---|---|---|---|
| F1 | **Session starts share almost no cache.** Main first calls write 85 % of their context fresh (subagents 91 %). Reading instead of writing would cost ~$1,028 less (12.4 %). | median first-call read 2,494 tok; mean written 109k | `_coldstart` |
| F2 | The 2.5k-read sessions are **worktree / mission directories** (~550 sessions: `wt_keosdtk_home` 253, `orca-dws-wt` 156, ...). Interactive project dirs share ~32k (tools + system prompt) and still write ~80-95k each. | `_coldstart_bydir` |
| F3 | Tool definitions were byte-identical in 673/673 same-dir session pairs within 1 h; system-prompt sections almost always too. The break is in what follows (instructions, listings, git/env context), not the tool list. | `_prefix_stability` |
| F4 | **73 % of mid-session prefix rebuilds come back from idle > 1 h** (cache expired): 224 of 307, ~$541. Model switches 36 (~$88), compaction 31 (~$38), unexplained ≤ 5 min gaps 16. | `_deep` [P] |
| F5 | **A 5 min TTL would cost MORE**: cheaper writes save ~$795, but 1,327 calls arriving 5-60 min after the previous one would miss (~$2,056). Net +$1,262. Wave 1's "TTL 9.6 %" bound is refuted. | `_ttl_net` |
| F6 | **280 of 319 listed skills were never invoked** in 7 d (39 invoked, 336 invocations; `kclear` alone 113). Listing deltas are re-injected mid-session 875 times (median 5.4k chars). | `_coldstart` [K], `_listings` |
| F7 | Thinking = 27.6 % of output tokens (≈ 3.6 % of spend); effort is already `medium` on 98 % of calls. | `_deep` [T] |
| F8 | 30 % of Read calls re-read a path already read in the same transcript. | `_deep` [S] |
| F9 | ~20 model calls per human prompt (mean 20.4; p50 7, p90 60, max 475); ~1.1 tool uses per call, i.e. almost no batching. | `_deep` [H] |
| F10 | Transcript records are not what the model sees: `hook_success` (1.85 MB record, +864 tok measured), `prompt_snapshot` and `hook_cancelled` are UI records with fitted reach 0. Hook `additionalContext` does reach the model (~0.43 tok/char). | `_deep` [C] + direct check |

Growth attribution by kind (fitted, R² 0.20, so rough): the model's own tool-call inputs (Edit/Write
bodies) 11 %, Read results 11 %, PowerShell 6 %, hook additionalContext 4 %, Grep 3 %, plus ~317
tok per call of injection the transcript does not record (9 %). Listing/instructions attachments
are confounded with start-of-session content and are not attributable by this method.

**Correction to my own first pass:** the uncalibrated table (before the fit) ranked hook outputs
and prompt snapshots at ~45 % of re-read cost. They are not sent. Recorded so nobody repeats it.

## 2. Lateral pass (lateral-thinking skill)

**First principles.** Spend = Σ calls × (context × read price) + Σ births × (prefix × write
price) + Σ rebuilds + output. Three multiplicands, each a lever family:
- **C, number of calls**: 20 per prompt, 1.1 tools per call.
- **M, mean context per call**: floor ~114k + growth (main p50 305k).
- **P, price mix**: writes at 2× input vs reads at 0.05×; every cold start and every rebuild moves
  tokens from the 0.05× column to the 2× column (a 40× gap).

The P family was under-weighted in wave 1. A token written instead of read costs 40× more, so
cold starts (F1) and idle rebuilds (F4) are the cheapest reachable money per unit of effort.

**Constraint removal.**

| constraint | if it did not exist | what becomes possible |
|---|---|---|
| "a session's context is its transcript" | context compiled from durable state per epoch | goal-spine briefs are 0.7-3 KB ([[goal-spine]]); rollover capsule |
| "a resumed session must rebuild its old context" | after a > 1 h idle the cache is cold anyway | **idle-return rollover**: start fresh from a capsule instead of rewriting 300k |
| "every session writes its prefix" | sessions in a dir share a byte-stable prefix | cold start becomes a read: up to ~$1,028 / 7 d |
| "every skill is described every call" | only invoked skills are described | `skillOverrides: name-only` for the 280 never invoked |
| "the model runs every loop" | scripts and schedulers run deterministic loops | gates in the goal-spine sweep (zero-LLM), test-summary scripts |
| "one tool per call" (partly PP's own Windows caps) | independent reads batched | fewer calls per prompt; conflicts with the bridge-reliability caps |

**Inversion: how to guarantee maximum spend, and whether PP does it.**
1. Huge always-loaded prefix: yes (floor ~114k).
2. Leave sessions idle > 1 h, then continue them: yes, 224 rebuilds.
3. Start many sessions that cannot share a cache: yes, 85-91 % of first calls written.
4. Re-read whole files: yes, 30 % re-reads, PDFs and images read whole.
5. One tool per call: yes, 1.1 tools per call.
6. Use the top model for mechanical work: yes, 86 % Opus.
7. Inject advisory text every prompt and every tool call: yes (tower baseline, GK-12 graph
   advisory on Grep, skill advisor on Write, cross-project baseline on PowerShell).
8. Switch model mid-session: 36 rebuilds.

Each "yes" inverts into one idea below.

```
[lateral-thinking audit]
domain: system-design
ratings: reframing=3 inversion=5 analogy=3 constraint-removal=5 first-principles=5
applied: first-principles, constraint-removal, inversion
non-obvious-candidates: price-mix (write->read) levers outrank floor trimming per unit effort; idle-return rollover (cache already cold, so a fresh epoch is free); byte-stable session-start prefix for worktree/mission epochs; hide never-invoked skills; refute 5m TTL; PP's Windows batching caps raise call count
```

## 3. Idea catalogue

Status of each idea: NEW (this wave) or W1 (in [[token-economy-levers]]). Bound = upper bound over
the 7 d window as a share of est. spend; "?" = unmeasured. Owner: who would build it.

### A. Price mix: move tokens from write to read

| id | idea | bound | evidence | effort | owner |
|---|---|---:|---|---|---|
| A1 | **Idle-return rollover**: on a > 1 h gap with context well above floor, start fresh from the capsule instead of rewriting | ≤ 6.5 % (the $541 rewrite; net of floor ~60 % of it) + smaller later reads | measured F4 | S-M | rollover owner (SPEC-ECON-ROLLOVER): proposal, this mission's S6 |
| A2 | **Byte-stable start for worktree / mission epochs** (~550 sessions sharing 2.5k instead of 32k): find what differs (likely per-epoch text in the system prompt) and move it to the first user message | ~1.5 % | measured F2 | S | Ralph / `gsd_epoch` owner |
| A3 | **Share the post-system prefix across sessions** (~80-95k per start): `--exclude-dynamic-system-prompt-sections` (CLI 2.1.288 has it), stable listings, no per-session text before CLAUDE.md | ≤ ~10 % | doc tier A ("improves prompt-cache reuse"); feasibility UNKNOWN | experiment first | none → [[cold-start-cache-sharing]] |
| A4 | Stop mid-session model switches (find the source: advisor model, `opusplan`, skill `model:` frontmatter) | ~1 % | measured F4 | S | none |
| A5 | Keep the 1 h TTL; do NOT set `CLAUDE_CODE_PROMPT_CACHE_TTL=5m` | avoids +15 % | measured F5 | none | — |
| A6 | Compact while the cache is warm, never after a break (doc: warm compaction costs a fraction) | ? | doc tier A | S | rollover owner |

### B. Mean context: floor and growth

| id | idea | bound | evidence | effort | owner |
|---|---|---:|---|---|---|
| B1 | `skillOverrides: "name-only"` for the 280 skills never invoked in 7 d; keep full descriptions for the 39 used | ~1.5-2 % (≈ -5k tok/call) | measured F6; doc tier A | S, Owner step (settings.json, HR-001) | none → [[hide-unused-skills]] |
| B2 | Floor diet: CLAUDE.md + rules (44.7k movable) | 6.3-12.6 % | W1 | M | [[always-loaded-prefix-audit]] |
| B3 | **Per-prompt / per-tool advisory diet**: dedupe hook additionalContext per session (tower baseline every prompt, GK-12 on every Grep, skill advisor on Write, cross-project baseline on PowerShell) | ~2-4 % | fit F10 (~$202 re-read) | S | PP hooks: none → [[hook-injection-diet]] |
| B4 | Cap main context: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` / `--autocompact` exists (doc tier A); or the rollover wall at 150-200k | 7.4-8.8 % | W1 + doc | S (env) | rollover owner / CCP C6 |
| B5 | PostToolUse `updatedToolOutput` to trim tool results (field documented; per-tool scope UNKNOWN) | part of ~20 % tool-result growth | doc tier A | M, verify scope first | [[tool-output-at-source]] |
| B6 | PreToolUse `updatedInput` to pipe verbose PowerShell (pytest, git log) through filters: PS-native RTK | part of PS 6 % | doc tier A; PP gap | M | [[rtk-powershell-gap]] |
| B7 | Hard caps: `BASH_MAX_OUTPUT_LENGTH` (30k default), `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | ? | doc tier A | S | none |
| B8 | Read discipline: 30 % re-reads; page PDFs; contact sheets instead of frame-by-frame images | ~2-3 % | measured F8, top items | S | anti-thrash hook (LIVE, unchanged-only) |
| B9 | Big pastes into files, read the needed part (top single items are 19-24 Mtok of pasted text re-read) | ? | measured (top items) | behaviour | Owner |
| B10 | Fix failing MCP servers: 665 mid-session deferred-tool deltas; 5 servers failed in this session | ~1 % | measured `_listings` | S | Owner (MCP config) |
| B11 | Hide unused agents from the listing (62 agents, ~15 types used) | ~1 % | ACV measurements | S | ACV |
| B12 | MEMORY.md index trim (15.7 KB ≈ 4k tok every call) | ~1 % | W1 audit | S | memory owner |
| B13 | Identify the ~317 tok/call the transcript does not record | up to ~9 % of re-read | fit F10 | S (investigate) | none |

### C. Number of calls

| id | idea | bound | evidence | effort | owner |
|---|---|---:|---|---|---|
| C1 | Batch independent reads into one call where the Windows bridge allows (1.1 tools/call today) | ? large | measured F9 | M; conflicts with the ≤ 4 parallel-read doctrine | Owner decision |
| C2 | Developer-designed skills that stop repeat retrieval, script regeneration, test re-runs | 7.9-41.7 % of task cost in one study | tier A (single) | M | PP skills |
| C3 | Deterministic loops in scripts (goal-spine gates, test summaries), the model sees only failures | ? | Agentless / code-exec (W1) | M | goal spine (LIVE) |
| C4 | Plan with Opus, execute with Sonnet for strong-model workloads (~30 % cost, -0.4 to -2 pp) | ~? | snippet tier A, open models | M | CCP C4 |
| C5 | `/rewind` instead of continuing a failed path (reuses an earlier cache entry) | ? | doc tier A | behaviour | Owner |

### D. Output and model mix

| id | idea | bound | owner |
|---|---|---:|---|
| D1 | Subagents to Sonnet / Haiku; custom `Explore` with `model: haiku` (built-in Explore runs on Opus on a subscription) | 3.8 % | CCP C4 |
| D2 | `--effort low` for mechanical subagents (executor, code-fixer) | ≤ ~2 % | CCP C4 |

### E. Instruments (enable everything above)

| id | idea | why |
|---|---|---|
| E1 | **Meter calibration**: one controlled before/after of the weekly % against transcript tokens | every bound here is USD, not the meter (unknown cache-read weight) |
| E2 | Fold the six wave-2 instruments into the CCP usage index as typed reports | they are one-off scripts today; a lever without a recurring meter regresses silently |
| E3 | A/B on the same task for any lever (runs vary ~2× on identical tasks) | wave-2 external research, tier A |

## 4. Recommended next steps (cheapest money first)

1. **A1 idle-return rollover**: sent as this mission's S6 proposal to the rollover owner
   (`vault/proposals/2026-10-03_idle-return-rollover.md`). **Correction 2026-10-03:** a fresh
   epoch is not free. `/kclear` after the gap needs a model turn on the cold context, because the
   handoff must be less than 30 min old (`tools/rollover.py:403` @ `20d0e66`). That turn is the rewrite. Only
   a pre-call UserPromptSubmit block with a handoff-less capsule avoids it, and that weakens
   SAFE_TO_FORGET.
2. **B1 hide never-invoked skills**: Owner step in settings.json; measurable next week by
   `_coldstart` [K] and floor probe.
3. **B3 advisory diet**: PP-owned hooks, smallest code change.
4. **A3 cold-start experiment** (4 small calls: two sessions per arm, with and without
   `--exclude-dynamic-system-prompt-sections`): decides whether a ~10 % lever exists. Waits for an
   Owner go (it uses quota before the 2026-10-07 reset).
5. **E1 meter calibration**: so the ranking can switch from USD to the weekly limit.

Not recommended: a 5 min TTL (F5); LSP / code-graph tools as a token saver (+6 % to +118 % tokens
in a controlled study, [[2026-10-02-token-economy-external-research-2]]).

## Disagreements

- **TTL.** [[token-economy-levers]] listed "1 h → 5 m TTL, ≤ 9.6 %, not reachable". Both halves
  were wrong: it is reachable (`CLAUDE_CODE_PROMPT_CACHE_TTL`, doc tier A), and it would cost
  more (F5). This page supersedes that row.
- **Code intelligence.** Claude Code's costs doc says code-intelligence plugins reduce reads
  (qualitative); a controlled study measured LSP using +6 % to +118 % tokens. Evidence favours the
  study for localisation tasks.
