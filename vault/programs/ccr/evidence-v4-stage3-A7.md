# CCR v4 Stage 3 -- A7 evidence: main interactive authority and canary

Unit WU-A7, goal ccr. Branch mission/ccr-s3 on GEX44, base 7d2af6e6. Inputs are the laptop receipts and usage projections in the pack (`ccr-s3-data/pack`), which are content-free. Numbers taken from them are labelled "laptop projection". Numbers measured on this host are labelled "Linux plane GEX44, host 2.1.296".

## 1. Offline shadow: what unit closure would do to interactive main sessions

Tool: `tools/ccr_main_shadow.py <pack>`; tests: `tools/test_ccr_main_shadow.py`, CCR_PASS=11/11.

Scope:
- Every receipt file whose start receipt says `interactive: true` and has no Work Unit: 52 sessions.
- 50 of them have a usage projection, and 41 of those 50 have main-loop listing receipts.
- Main-loop processed tokens over the 50: 1,234,720,984 (laptop projection).

A "later use" is a main-loop (non-sidechain) `Skill`, `Agent` or `mcp__*` tool_use in the projection after the first dropped listing.

| attachment | sessions | events | bytes | unit closure | main-lean saves (bytes) | main-lean est. processed tok | later uses (sessions) |
|---|---:|---:|---:|---|---:|---:|---|
| skill_listing | 42 | 82 | 1,765,034 | drop 1,765,034 | 1,307,890 | 16,687,382 | 14 (12) |
| agent_listing_delta | 42 | 80 | 2,540,644 | drop 2,540,644 | 2,393,287 | 28,393,639 | 43 (14) |
| mcp_instructions_delta | 42 | 97 | 261,255 | drop 261,255 | 234,084 | 2,131,679 | 0 (0) |
| instructions | 42 | 85 | 7,945,868 | replace, saves >= 7,265,868 | kept (not in canary) | - | n/a |

**Regression risk under drop:** 19 of 50 sessions later used a capability whose listing unit closure drops.
- Skill uses (14): gsd-plan-phase 3, cpp-gsd-long 3, plugin-authoring 2, kclear 2, and others.
- Agent uses (43): gsd-executor 11, general-purpose 10, pp-code-reviewer 7, gsd-plan-checker 6, gsd-planner 5, and others.
- MCP tool uses: 0 in all 50 sessions.

**Verdict:** dropping the skill and agent listings in main sessions is rejected. In 38% of sessions (19/50), the model later picked a skill or agent by name.

**How the lean columns were computed:**
- Name-only ratios come from running the real `decideMainLeanAttachment` on real 2.1.296 listing text from this host's estate (transcript d5e49ddf). Linux plane GEX44, host 2.1.296:
  - skills: 29,998 -> 7,778 chars, 314/314 names kept;
  - agents: 26,065 -> 1,521 chars, 70/70 types kept;
  - MCP: 1,893 -> 197 chars.
- Applying those ratios to laptop bytes assumes the laptop listings have the same shape. The per-event sizes match closely: skills 30,063 laptop vs 29,998 here; agents 27,315 vs 26,065.
- Tokens are chars/4. This is an assumption, not a fit.
- "Processed" counts cache reads at full weight. At the billing weight (0.1 per cache read) the saving is smaller.
- On that basis, main-lean on these sessions is about 47.2M of 1,234.7M processed (3.8%).

## 2. Policy: main-lean canary

The code is in `mods/cpp-cognitive-runtime/hooks/policy.ts` (main-lean section) and `register.ts`.

**When it runs** (`mainCanaryMode`):
- Opt-in: `CCR_MAIN_CANARY=1`, read once at `session.start`.
- Only on `isInteractive === true` sessions with no Work Unit.
- Off when `modes.main` is off, which includes the OFF file.
- On a build outside COMPAT it runs as shadow: receipts only.
- Any other value of the variable (`0`, `true`, unset) means off.

**What it changes** (`decideMainLeanAttachment`):
- `skill_listing` and `agent_listing_delta`: each `- name: description` line becomes `- name`. Every name is kept, including plugin-scoped `plugin:skill` names. Other lines are kept unchanged.
- `mcp_instructions_delta`: becomes the server headings. The MCP tools themselves are untouched.
- Each compacted text ends with a hint: load `mcp__cpp-cognitive-runtime__page` with ToolSearch and call it with kind `skills`, `agents` or `mcp`.
- The page tool gained kind `mcp`, which returns the matching server's block. Agent and MCP deltas now accumulate for paging instead of only the last one being kept.
- If no line can be compacted, or the compacted text would be no shorter, the stock text is kept.
- `instructions` are not touched in this canary. It is the biggest line in the table (>= 7.27M bytes), so it is the candidate for a later canary once this one is read.

**Version truth:**
- The start receipt carries `canary`.
- `policyGen` moves only when the canary runs (enforce and shadow give different ids). With the canary off the id is unchanged (`acce69838866` test pin).
- The status line shows `canary:<mode>`.
- Each canary attach receipt carries `canary`, `bytes`, `out`, `lean`, `action`, `applied`.

**Rollback:** any one of these turns the canary off:
- unset the variable and start a new `claude`;
- `python tools/ccr_release.py rollback`;
- `python tools/ccr_release.py off`.

**Validation** (Linux plane GEX44, host 2.1.296, `~/.local/bin/claude`):
- `claude plugin test mods/cpp-cognitive-runtime`: 38 pass, 0 fail. That includes 5 new canary/lean tests; there were 33 at A1.
- `claude plugin validate`: passed. Env reads are CCR_MAIN_CANARY, CCR_PIXEL_GC and CCR_WORK_UNIT, with no env writes.
- `tools/test_ccr_release.py`: CCR_PASS=20/20.
- `tools/ccr_estate_gate.py`: PASS.
- Real-listing run: the 314/70 names result above.

## 3. Canary

**Prediction for one canary session**, from typical laptop first events (skills 30,063, agents 27,315, MCP 3,144 chars):
- About 50.8k chars withheld at the first call, which is about 12.7k tokens.
- That is about 11% of the baseline median first-call ctx. The baseline is 112,591 tokens over 18 compatible interactive sessions (laptop projection).
- The saving rides every later call.

**Launch** (Owner, new PowerShell pane):

    $env:CCR_MAIN_CANARY='1'; claude

Expected status line: `CCR 0.1.0 sub:enforce main:shadow canary:enforce`.

**Read afterwards** (laptop, repo root):

    python tools/ccr_main_shadow.py --canary $env:USERPROFILE\.claude\ccr\state\receipts

The output gives:
- `state`;
- per canary session: `withheld`, `predicted_first_call_tok`, `measured_first_call_tok` (baseline median minus the canary's first ctx; n is small and prompts differ), `faults` (page calls, meaning the model needed a description), `spawns` and `errors`.

A capability failure, such as a skill or agent the model did not find, is not visible in content-free receipts beyond faults. The Owner's account of the session is the other half of the read.

**State: CANARY_PENDING.** No canary session exists. The host loads plugins per process, so the canary needs an Owner-opened pane on the laptop. `--canary` over the pack's receipts returns `CANARY_PENDING`.
