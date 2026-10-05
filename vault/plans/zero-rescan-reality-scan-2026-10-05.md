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

Run 2 (session 7cf90b36, task bnc29t9k6, 9.6 GB free at start): STOPPED BY ME at 1097 s, not completed -- its 1500 s cap
would have killed it and the Owner chose to keep the laptop browser-usable (option A). Its line reads `killed=False`
because the stop was external; the facts are: 28.63 GB read without finishing (~3.1x the 9.17 GB unique corpus, i.e.
`--until auto` makes several full passes), peak 156 MB, min free 1.56 GB. Scanner memory is not the constraint; wall
time and bytes re-read are.

Run 3 (task bfvivsg5j, launched 2026-10-05 ~10:57): owner-bundle rows 4-10 in their exact authorized commands
(population, d KME-L, d CPP-D-W7, e, f, g, h, i, kme_replay rank), sequential, BelowNormal priority, watchdog floor 0.6
GB free, cap 3 h per step, stop after a failed population step. One `STEP <id> exit= killed= wall_s= cpu_s= peak_ws_MB=
read_GB= min_free_GB=` line per step in the session scratchpad `ic_rows_4_10.summary`. The population step is this
mission's champion baseline.
Result: population killed by the watchdog at 93 s (free 0.48 GB, scanner 50 MB, 1.39 GB read); later steps not run.
Host at that moment: 28 claude processes 10.1 GB, Brave 7.6 GB, Cursor 5.1 GB of 31.3 GB.

Run 4 (task bwb1d2crm): same steps, watchdog switched to Available MBytes and PAUSE (NtSuspendProcess below 0.5 GB,
resume above 1.0 GB, mechanism tested on a dummy process) instead of kill. Claude Code's own low-memory reaper killed the
runner while the session was idle; no step line written, no orphan scanner left (verified), Available 0.63 GB after.
Not restarted: the harness says not to without the Owner. Conclusion: on this laptop at the current load the D-I + L
runs cannot complete; they need either other apps/panes closed or the GEX44 option (B), which copies the corpus.

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

## Rescan recurrence across the estate (2026-10-05, session 7cf90b36)

Method: grep of every `*.py` iterating `*.jsonl` (119 files name the projects dir; most are single-session lookups or
stat-only), 25 candidates classified by a read-only subagent (scope / read depth / incremental / trigger, file:line cited),
the automatic one re-verified by me. Table: session scratchpad `scan-recurrence.md` (session-local, not durable).

| class | count |
|---|---|
| ALL_PROJECTS + full-content parse + no cache | 14 (4 of them mtime-windowed, not whole-corpus) |
| of those, automatic | **1**: `tools/sovereign_miner.py`, scheduled task PP-Sovereign-Miner daily 03:00 (verified: Ready, last run 2026-10-05 03:00 result 0; `json.loads` every line `:104`, recursive glob over PROJECTS_DIR `:164`; docstring still says 1.6 GB) |
| of those, manual / effectively manual | 13 (kme_token_audit, kme_pillars, token_ground_truth, tis_observed.iter_calls, skill_invocations, skill_invocation_channels, store_consult, merger, measure_command_surface, co_12_telemetry, token_corpus_audit, conversation_quality_audit, by_entrypoint) |
| already incremental | usage_index (`:438-455` size+mtime_ns+offset), tis_observed.calls_from (offset) |
| frequent automatic readers | tail/metadata only: session_active (every 5 min x2 tasks), scheduler, cpc_os snapshot (2 min + SessionStart), pp_eval nightly (stat) |

Wired-but-dead / UNKNOWN: merger is spawned only via `tools/vault_refresh_all.py`, which does not exist (verified
`Test-Path` False) -> never runs from the vault-heartbeat Stop hook; `commands/cpp-resume-sovereign.md:93` is stale.
budget_monitor -> iter_calls documented as SessionStart hook (`register_global_hooks.py:37`) but no live registration found
(UNKNOWN). pm_04_auction default -> token_ground_truth: automatic? UNKNOWN. `rename_sessions.py --all --apply` daily 04:00:
read depth UNKNOWN.

Reading for the ROI gate: automatic full-corpus recurrence is ~1/day (the miner), not a per-session cost. The rescan
burden is concentrated in MANUAL measurement tools (13), each re-parsing the corpus per invocation, and kme_pillars
`--until auto` / bundle rows multiply that per run.

## Open, not acted on

- GEX44 copy of the PP transcript folders at `/home/kobii/kme-l-corpus` (932 MB, chmod 700): delete needs the Owner's go
  (destructive; superseded by the data-locality rule).
- Next: per-subcommand rescan count (bundle rows 4-10 = up to 9 full-corpus scans), does the walk follow the junction,
  recurrence across the estate, then the ROI gate and the inline plan + Q&A (ULTRA phase 2 stop).
