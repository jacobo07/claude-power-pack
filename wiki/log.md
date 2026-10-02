# PP Wiki — Log

Append-only. Newest at the bottom. `grep "^## \[" log.md` lists every entry.

## [2026-09-30] init | Wiki created
- touched: [[CLAUDE]], [[index]], [[log]], [[overview]]
- notes: Owner choices — topic: Claude Power Pack and how to improve it; location: `wiki/` in the PP
  repo; ingest: one source at a time, discussed; language: terse English (lowest token cost that
  stays readable).
- raw: saved `raw/2026-09-30-karpathy-llm-wiki.md` (the pattern's original gist). Not yet ingested.

## [2026-09-30] ingest | Karpathy — LLM Wiki (gist)
- touched: [[2026-09-30-karpathy-llm-wiki]], [[llm-wiki-pattern]], [[compounding-vs-rederived-knowledge]],
  [[measure-knowledge-store-consultation]], [[overview]], [[index]]
- notes: Owner approved takeaways as proposed. Store paths verified to exist @ `8574446`; consultation not measured.

## [2026-09-30] query | Do sessions consult PP's knowledge stores?
- touched: [[measure-knowledge-store-consultation]]
- notes: `tools/store_consult.py 30 560`; 3015 transcripts, 246,755 tool calls, full scan; the wiki's own
  writes served as a check that the counter works. PORTFOLIO_LEARNINGS read 2× in 30 days.

## [2026-09-30] ingest | Playlist "$ Datasets: Vibe Coding" (4 videos)
- touched: [[2026-09-30-yt-9uojngzcjo]], [[2026-09-30-yt-91b_v-woaws]], [[2026-09-30-yt-i10xtuixfey]],
  [[2026-09-30-yt-pffo4jysptw]], [[lean-always-loaded-context]], [[always-loaded-prefix-audit]]
- notes: transcripts from YouTube auto-captions via yt-dlp; 91B_v-wOaws only had a Spanish auto-dub.
  Owner: the two app-growth videos kept as short decision guides, marked off-topic.

## [2026-09-30] ingest | system_prompts_leaks @ b632b67
- touched: [[2026-09-30-system-prompts-leaks]], [[compact-instructions-section]], [[always-loaded-prefix-audit]]
- notes: stored as a manifest plus cited files only (compact.md). Treated as reported, not official.

## [2026-09-30] query | Always-loaded prefix size; PORTFOLIO_LEARNINGS fate
- touched: [[always-loaded-prefix-audit]], [[portfolio-learnings]], [[overview]]
- notes: 167,206 bytes loaded every session in this repo. Global CLAUDE.md: 39,810 chars / 292 lines.
  PORTFOLIO_LEARNINGS recommendation awaits Owner.

## [2026-09-30] schema | tools/ folder, large-source manifests, lint skip-list
- touched: [[CLAUDE]]

## [2026-09-30] apply | PORTFOLIO_LEARNINGS frozen; Compact Instructions added
- touched: [[portfolio-learnings]], [[compact-instructions-section]]
- notes: Owner "y". Edited PP `CLAUDE.md` (obligation → pointer to wiki; new `## Compact Instructions`)
  and `knowledge/PORTFOLIO_LEARNINGS.md` (header, LRN-03 duplicate → LRN-11). Found an uncommitted
  2026-07-30 entry in the ledger (another session's work); corrected the component page. Compact
  Instructions not yet verified: needs a test compaction.

## [2026-10-01] query | SDD-OS technical gaps vs engineer-grade instruction
- touched: [[sdd-os-gap-analysis]], [[sdd-os]], [[2026-10-01-sdd-external-research]],
  [[2026-10-01-sdd-internal-inventory]], [[overview]], [[index]]
- notes: two research subagents (external web, internal read-only audit). I verified 2 of 3
  load-bearing papers against their abstracts (the third is a pilot study with unverified numbers).
  Reproduced the binder and tier defects with `tools/sdd_probe.py`, including a no-spec control.
  Score: 0 met / 18 partial / 15 missing. Fixes ranked; none approved.

## [2026-10-01] query | Constitutive Baseline Ratchet: gaps and full potential
- touched: [[cbr-gap-analysis]], [[constitutive-baseline-ratchet]], [[2026-10-01-cbr-external-research]],
  [[2026-10-01-cbr-internal-inventory]], [[overview]], [[index]]
- notes: two research subagents (external web ~33 sources, internal read-only audit @ 298975d).
  Verified 3 load-bearing external claims (OpenSSF confirmed; agent-memory claim weaker than stated;
  Infer snippet-only). Corrected the audit's "47/47 identical capsules" to 43/47. `tools/cbr_probe.py`
  reproduced 9 defects with controls and REFUTED one hypothesis (newest-generation edit is caught).
  Score: 2 met / 15 partial / 15 missing. Fixes ranked; none approved.

## [2026-10-01] query | Maturity transfer pilot: KobiiCraft → KobiiSports Resort
- touched: [[maturity-transfer]], [[maturity-transfer-pilot-kobiicraft-ksr]],
  [[2026-10-01-kobiicraft-capability-harvest]], [[2026-10-01-ksr-maturity-profile]], [[index]]
- notes: Owner asked whether a mature system can raise others' maturity "and not only lessons".
  Two blind read-only agents, shared taxonomy (L1-L5 + LG, 14 traits). Verified in source: KSR
  save zeroes and overwrites on any failed load (main.cpp:1443-1565); KC codifies the inverse
  (world_persistence_gate.py:7-16); KC CI skips its missing praxis guard. 50 KC capabilities:
  12 → 6 ranked proposals, 11 second-tier, 4 product questions, 7 present/shared, 16 not
  transferable. Diff not blind; 19/24 gap coverage is interpretation. Nothing changed in either repo.

## [2026-10-01] query | Maturity transfer pilot: Owner decisions recorded
- touched: [[maturity-transfer-pilot-kobiicraft-ksr]]
- notes: Owner accepted P1 and both reverse CI items. Landed as backlog rows only: KSR-B-073
  (KSR `5345ca1`) and KobiiCraft P1 "CI gates that cannot fire" (KC `61cd4448`). P2-P6 undecided.

## [2026-10-02] ingest | State-centric reality scan; goal spine connected; G-001 converged
- touched: [[2026-10-02-state-centric-reality-scan]], [[goal-spine]], [[goal-spine-connect-not-build]],
  [[verdict-pinned-to-what-runs]], [[spec-acceptance-as-goal-obligations]], [[mutation-anchor-rot]],
  [[overview]], [[index]]
- notes: Owner directed "use the research we did for the wiki" (Owner, 2026-10-02). Goal spine was
  built and unreachable; connected via PP-GoalSweep (c4c45b7..738ed40). G-001 judge PASS 20:44Z incl.
  live production bot gate. Overview point 7 added; next step proposed from SDD/CBR gap rows.
## [2026-10-02] query | Token economy: where the spend goes, levers ranked
- touched: [[token-economy-levers]], [[2026-10-02-token-economy-external-research]],
  [[2026-10-02-token-economy-internal-inventory]], [[tool-output-at-source]],
  [[mid-session-prefix-rebuilds]], [[sdk-probe-floor]], [[rtk-powershell-gap]],
  [[always-loaded-prefix-audit]], [[overview]], [[index]]
- notes: Owner asked to expand token-saving research (Owner, 2026-10-02). 7 d usage-index cuts
  (est. $8,312; cache 87 %, main 72 %, Opus 86 %) + upper-bound levers (`wiki/tools/token_economy_*`
  @ fd27800); two research agents (raw @ 3b07419). Verified the price table matches documented cache
  multipliers; sonnet-5-5 priced by family fallback. Four unowned levers filed as IDEA. USD is not
  the meter; bounds overlap. Nothing changed outside wiki/.