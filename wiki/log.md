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
