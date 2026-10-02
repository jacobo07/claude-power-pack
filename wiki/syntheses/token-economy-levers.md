---
type: synthesis
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research, 2026-10-02-token-economy-internal-inventory, 2026-10-02-state-centric-reality-scan]
---

# Token economy: where the spend goes and which levers move it

Question: how can PP spend far fewer tokens without losing quality? (Owner, 2026-10-02: "expand
the research on token saving ... massive evolution").

Method: 7 days of transcripts through the CCP usage index, cut by category, thread, model and
prompt kind (`wiki/tools/token_economy_cuts.py`, `token_economy_cuts2.py`); upper-bound
counterfactuals per lever (`token_economy_levers.py`); outputs pinned in the `.2026-10-02.out`
files next to them @ `fd27800`. External evidence and an internal mechanism inventory came from two
read-only research agents ([[2026-10-02-token-economy-external-research]],
[[2026-10-02-token-economy-internal-inventory]]).

## Caveats that bound every number below

- **USD is an estimate, not the meter.** List prices from `vault/pricing/anthropic_2026-09.json`.
  Transcript usage does not reconcile with the weekly meter (week A 75 % = $8,041, week B 90 % =
  $2,275), and 2-3 accounts write to the same store ([[2026-10-02-token-economy-internal-inventory]],
  "Where the tokens go"). How the subscription meter weighs cache reads is undocumented
  ([[2026-10-02-token-economy-external-research]], Q1). A lever's share of USD is therefore an
  ordering signal, not a promised share of the weekly limit.
- **Lever bounds overlap and are not additive.** A smaller floor also shrinks every cap and every
  cold call.
- **Upper bounds, not savings.** Each counterfactual assumes the change costs nothing else (no
  extra calls, no quality loss).
- **Price table check (done).** Opus 5.5 reads cache at $0.20/MTok = 0.05× its $4 input; Sonnet 5
  at $0.20 = 0.1× its $2 input. Both match the documented multipliers (external Q1), so equal
  absolute cache-read prices are real, not a table bug. `claude-sonnet-5-5` has no row and is
  priced by family fallback to `claude-sonnet-5` (`tools/usage_index.py:516-528` @ `3b07419`):
  the Sonnet routing figure rests on that fallback.

## Where the money went (7 d to 2026-10-02T20:48Z, 76,126 calls, est. $8,312)

| cut | share | note |
|---|---:|---|
| cache read | 53.9 % | 22.1 B tokens |
| cache write | 33.1 % | 61.8 % of written tokens on the 1 h TTL (2× input price) |
| output | 13.0 % | includes thinking |
| main thread | 72.1 % | context p50 305k, p90 468k |
| subagents | 27.9 % | context p50 238k |
| Opus 5.5 | 85.7 % | |
| first call of each transcript | 13.2 % | 37.8 % of all cache writes; first-call ctx p50 114k |
| mid-session prefix rebuilds | 8.1 % | 358 later calls writing > 50k |
| one-call `sdk-cli` transcripts | 4.9 % | 508 transcripts, ~$0.80 each |

Sessions are flat: top-10 sessions 14.2 %, median session $1.0. No single runaway explains the
spend; the shape is many sessions each carrying a large prefix.

Interpretation: **the bill is the prefix times the number of calls.** Cache read and cache write
together are 87 %; both scale with how big the context is when a call is made and how often a new
context is born.

## Levers, ranked

Rank = share (upper bound) × evidence tier × whether PP can act on it. Tier A = official or
controlled study with numbers; B = practitioner with numbers; C = opinion
(external research's grading).

| # | lever | bound (7 d) | evidence | PP can act? | owner |
|---|---|---:|---|---|---|
| 1 | Smaller always-loaded floor (-20k / -40k tok per call) | 6.3 % / 12.6 % | A (costs doc); floor attribution measured | yes | [[always-loaded-prefix-audit]] (IDEA, Owner-gated); CMV / CRO |
| 2 | Cap main-thread context at 150-200k (fresh epoch at the wall) | 7.4-8.8 % | A/B (JetBrains, OpenHands: bounded context = linear cost) | yes | rollover (SPEC-ECON-ROLLOVER, CCP C6) |
| 3 | Shrink tool output at its source | share of growth: tool results 78.4 % | A (JetBrains masking 52 % cheaper, +2.6 % solve; context editing -84 %) | partly (harness owns masking) | **none for the main thread** → [[tool-output-at-source]] |
| 4 | Find why prefixes rebuild mid-session | 8.1 % | A (invalidation hierarchy in caching doc) | yes, once attributed | **none** → [[mid-session-prefix-rebuilds]] |
| 5 | 1 h → 5 m cache TTL | 9.6 % | A (97.8 % of inter-call gaps ≤ 5 min) | **no**: harness picks the TTL by plan | outside PP |
| 6 | Cheaper floor for one-shot `claude -p` calls | ≤ 4.9 % | measured | yes | **none** → [[sdk-probe-floor]] |
| 7 | Subagents to Sonnet 5.5 | 3.8 % | A (costs doc recommends) | yes | CCP C4 (PLANNED, waits for quota) |
| 8 | RTK compression for PowerShell | ≤ PowerShell's 25-26 % of growth × unknown ratio | measured on one Bash command only (80 %) | yes, with a PS-native rewriter | **none** → [[rtk-powershell-gap]] |
| 9 | Fewer cold births (fan-out, concurrency) | part of the 13.2 % cold share | A (multi-agent ~15× tokens) | yes | CCP C2/C3/C7 |
| 10 | Lower effort / thinking on routine steps | part of the 13 % output | A (thinking billed as output) | yes | none; Owner preference |

Notes per lever:

1. **Floor.** Movable parts measured in a neutral cwd: CLAUDE.md + rules 44.7k, skills listing
   6.5k, hooks 4.8k, MCP 2.0k, plugins 1.4k; harness + tool schemas 34.5k are not movable
   ([[2026-10-02-token-economy-internal-inventory]], floor rows). So -40k means removing most of
   CLAUDE.md + rules; -20k is within reach of the rule→skill moves already started. Quality risk:
   six of the nine moved rules have no ablation, and moved rules auto-invoke 0/8.
2. **Context cap.** Main-thread p50 305k against a measured first-call p50 114k: two thirds of the
   resident context is growth. A cap pays a new first call per crossing (891 crossings at 150k);
   the bound already nets that. The rollover machinery exists and is LIVE; the economic trigger's
   production effect is UNMEASURED.
3. **Tool output.** The largest single growth source is `Read` (56.5 % of growth), then
   PowerShell (26 %). The external evidence says hiding old tool output is as good as summarising
   and cheaper. Claude Code exposes no per-session masking switch, so PP's reachable form is at
   the source: page reads, filter command output, keep verbose work in a subagent that returns a
   path.
4. **Prefix rebuilds.** 358 calls rebuilt > 50k of prefix mid-session. Documented causes: tool
   definition changes, idle > TTL, compaction, toggled features. Not attributed yet.
5. **TTL.** Largest clean bound, not reachable: on a subscription the harness uses 1 h (external
   Q1). Recorded so nobody re-derives it.
6. **One-shot calls.** `modules/deep-research/deep_research.py:795-805` @ `3b07419` runs every
   research LLM step as `claude -p` with tools disabled but the full project prefix; each pays a
   cold ~114k first call to produce a short answer.
7. **Model routing.** Small because cache reads cost the same on both models; the saving is on
   writes and output only.
8. **RTK.** `modules/rtk-core/rtk-rewrite.js:106-110` @ `3b07419` passes every non-Bash tool
   through, while the global CLAUDE.md mandates PowerShell for git, python and node.

## What is owned, and by whom

The Cognitive Control Plane owns the burn monitor, fan-out ledger, spawn admission, agent floor
and model policy, in-agent growth and rollover observation (CCP plan, cited in
[[2026-10-02-state-centric-reality-scan]]). This mission does not edit those surfaces. Unowned
levers got an improvement page each: [[tool-output-at-source]], [[mid-session-prefix-rebuilds]],
[[sdk-probe-floor]], [[rtk-powershell-gap]].

## Disagreements

- **Masking vs summarising.** OpenHands reports summarising keeps quality at ~2× lower per-turn
  cost; JetBrains finds masking as good, cheaper, and that summaries lengthen runs 13-15 %.
  Evidence favours masking first ([[2026-10-02-token-economy-external-research]], Q4).
- **Compaction vs caching.** Context editing cuts tokens 84 % in a vendor eval; TokenPilot
  (single preprint) shows any eviction rewrites the prefix and breaks the cache. Unresolved; it
  argues for compaction at deliberate boundaries (which is what rollover does), not continuously.
- **PowerShell compression size.** PowerShell is 25-26 % of context growth, yet CMV dropped a
  PowerShell tee as ≤ 4.5 % of tool rent ([[2026-10-02-token-economy-internal-inventory]], RTK
  row). Different measures (growth vs rent of one technique); unresolved until a PS compressor is
  measured on real calls.

## Open questions

- What does the weekly meter charge per cache-read token? Needs an Owner-side before/after.
- Which accounts write to the transcript store? (RCA §15; Owner-checkable only.)
- Does a smaller floor change quality? The six unablated rule moves are the test bed.

Related: [[lean-always-loaded-context]], [[goal-spine-connect-not-build]] (briefs compiled from
durable state are 0.7-3 KB, against a 114k cold floor).
