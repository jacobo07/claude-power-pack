# Zero-rescan mission (KME-L raw-history scan) -- reality scan, measurement phase (2026-10-05)

Owner brief: the pasted /ultra-plan "KME-L / zero-rescan" mission (2026-10-05). Mode: ULTRA-PLAN, measurement-first,
NO build before the ROI gate. Data locality: move compute to the data; do NOT replicate raw transcripts to GEX44.

## Measured (laptop, read-only census of ~/.claude/projects, 164 s, hashes only, no text read)

| measure | value |
|---|---|
| jsonl paths seen by a link-following walk | 4,368 files, 10.11 GB |
| unique realpaths | 4,007 files, 9.23 GB |
| unique contents (sha256) | 3,884, 9.17 GB (123 duplicate groups, 0.06 GB) |
| linked project dirs | 3: `C--Users-User-Apps-mcp-video-analyzer` -> the PP project dir (0.88 GB / 359 files double-counted by any link-following walk); `...TUA-X-CW-UGC-SYSTEM` (kobig) -> TUA-X-CW-UGC-SYSTEM; `...provisional--recovered-transcripts` -> provisional |
| project dirs with jsonl | 233 |
| dirs named kme/mapengine (KME_PATH) | 1 dir, 1 file, 0.78 MB -> KME-L's 102 sessions are almost all content-classified (KME_STRONG) elsewhere |
| CostaLuz dirs with jsonl | 1 dir, 22 files, 99 MB |
| largest | KobiiCraft Core Files 2.84 GB / 991; Orca-X 0.96; PP 0.88 (x2 via junction); TUA-X 0.67; KobiiSports 0.59 |

KME-L frozen denominator (`vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`): 102 active
sessions, 34,871 calls; classifier `wiki/tools/kme_token_audit.py:10-11,236-241` (KME_PATH by dir/cwd name, KME_STRONG by
>= 30 % KME tool calls). GEX44 test: PP folders alone reproduce 1 session / 128 calls (exit 3, drifted) -> the KME
population needs content classification across other repos.

## Champion result (task b2c7dhmyw)

INCONCLUSIVE: the watchdog killed it at 100.9 s after 2.97 GB read (~1/3 of the corpus), host free RAM 1.19 GB; the
process peaked at only 61 MB, so host pressure (other panes), not the scanner. Re-run when free RAM is >= 4 GB.

## In flight at seal

- Champion baseline: `kme_pillars.py population --denominator KME-L --until auto --expand --root ~/.claude/projects` on the
  laptop under a memory watchdog (kill < 1.2 GB free, 1500 s cap); script `scratchpad/champion_run.ps1`, background task
  b2c7dhmyw; prints `CHAMPION exit= killed= wall_s= cpu_s= peak_ws_MB= read_GB= min_free_GB=`.
- Ownership sweep subagent (read-only, 12 capabilities incl. how kme_pillars walks the root and whether subcommands rescan)
  writing `scratchpad/ownership-sweep.md`.
- The scratchpad of session 7f072421 is session-local: re-run the census (`corpus_census.py`, recreated from this table's
  method) rather than relying on it.

## Ownership sweep (subagent, read-only, ~55 tool calls; unverified by me beyond citations -- re-check before building)

- EXTEND, do not build: `tools/usage_index.py` is LIVE (sqlite `~/.claude/state/usage_index/index.sqlite`, schema v4:
  files/calls/quota/prompts/spawns/subagents/meta; per-file byte-offset cursor, skip on unchanged size+mtime_ns, junction
  aliases via `tis_observed.store_identity`; MONITOR_FAILURE after 7200 s stale; CLI refresh/window/burn/replay/holdout;
  caller `modules/wrapper/cost_gate.py:189-198`). Lacks: tool calls/results, compactions, cwd, project attribution,
  content-hash key. Parent plan `vault/plans/cognitive-control-plane-2026-10-02.md` (G7 "One parser").
- Champion mechanics: `kme_pillars.scan()` :1629-1648 rescans every run, no cache; `--expand` lists every dir under the
  root, only `--project-filter` narrows; `kme_token_audit.scan_project` :212-230 json-parses every line of every jsonl,
  classify after full parse; `--until auto` does several scans; `all` runs every pillar in one scan; it never reads usage_index.
- Duplicates: ~10 independent transcript parsers (token_ground_truth, token_corpus_audit, session_autopsy, token_autopsy,
  conversation_quality_audit, skill_invocations, CE turns/context_lifetime, ksr_archaeology scripts, kme_token_audit);
  12+ projects-dir globs; 3 freshness vocabularies (tis_observed / usage_index / kme_pillars). Content-addressed transcript
  cache: ABSENT. FIOS: engines only (CONNECT). Cognitive Economy: closed, consumes the index; pillar F reread FALSIFIED 1.88 %.
- Not read within the bound: `modules/cognitive_os/co_12_telemetry.py`, `scheduler.py`, session-continuity, session_guard.

## Open, not acted on

- GEX44 copy of the PP transcript folders at `/home/kobii/kme-l-corpus` (932 MB, chmod 700): delete needs the Owner's go
  (destructive; superseded by the data-locality rule).
- Next: per-subcommand rescan count (bundle rows 4-10 = up to 9 full-corpus scans), does the walk follow the junction,
  recurrence across the estate, then the ROI gate and the inline plan + Q&A (ULTRA phase 2 stop).
