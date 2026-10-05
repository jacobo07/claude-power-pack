# Zero-rescan mission (KME-L raw-history scan) -- reality scan, measurement phase (2026-10-05)

> **SUPERSEDED 2026-10-05** by `vault/plans/autonomous-optimization-2026-10-05.md` (APPROVED by the Owner the same
> day; `covers: zero-rescan`, this file is its parent). The ROI gate and the build decision belong there: P1 =
> usage_index v5, P2 = KME-L challenger that must reproduce the 7 KME-L files and "may lose to plain scoping". This
> file stays the measurement record; nothing below is rewritten. Handoff of what it adds: the section at the end.

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

Run 5 -- GEX44 (Owner chose B, 2026-10-05: a COPY, originals stay on the laptop; this overrides the brief's
data-locality rule for this run; CostaLuz not excluded). Repo bundle at 61909502 cloned to
`/home/kobii/missions/zero-rescan-run`. Corpus copied to `/home/kobii/kme-corpus/projects` (chmod 700): first stream
reaped by Claude Code's low-memory reaper at 7.9 GB; resumed by a size-keyed delta (bsdtar died `(null)` on a live file
after 218 s; the remainder sent with a snapshotting Python tarfile stream). Final parity: 10,577 files / 9.50 GB both
sides, 3 files differing = live transcripts still growing (after the frozen `--until auto` cut). The 3 laptop junctions
are recreated as relative symlinks. Runner `/home/kobii/missions/gex44_ic_rows.sh` (nohup setsid, cap 4 h/step, rchar +
VmHWM per step), START 2026-10-05T12:13:26+02:00; summary `/home/kobii/missions/zero-rescan-out/summary.txt`.
Note: Linux `rchar` counts page-cache hits, comparable to Windows ReadTransferCount, not to disk reads.

Run 5 result (GEX44): `STEP r4-population exit=3 killed=no wall_s=869 peak_rss_MB=184 read_GB=101.53` -> population gate
STOP, rows 4-10 not run. **Champion baseline measured: one population run = 869 s, 101.5 GB read (~10.7x the 9.5 GB
corpus; `until_located.scans` = 10 full scans), 184 MB RSS.** Drift reconciled to the unit: frozen 102 / 34,871 calls /
11,549,646,300 cache_read = KobiiCraft-Core-Files (101 / 34,870 / 11,549,645,760) + `kme-wt-arena2` (1 / 1 / 540).
The measured extras are exactly: `_archived` 1 session / 649 calls / 271,001,260 cache_read (dir dates from 2026-03-31,
so not new data) + ONE PP session counted twice via the `mcp-video-analyzer` junction alias (128 calls / 34,065,113 x2).
34,871+649+128+128 = 35,776 and the cache_read sum match exactly. So the drift is scan SCOPE (alias + _archived), not
corpus change; `--until` cannot fix it (`not_found`). Owner decision needed before D-I: re-scope to the frozen projects
vs re-investigate the freeze's scope.

Run 6 (GEX44, Owner option 1: KME-L steps with `--project-filter "KobiiCraft-Core-Files|kme-wt-arena2"`, CPP-D-W7
unfiltered as authorized), 20:09:57 -> 20:14:12 (4 min 15 s for all 9 steps):

| step | exit | wall_s | read_GB | peak_rss_MB |
|---|---|---|---|---|
| r4-population | 0 (match exact) | 24 | 2.83 | 99 |
| r4-d-kmel | 0 | 26 | 2.85 | 159 |
| r4-d-w7 | 3 (referenced, coverage 1.1206 -> materiality UNMEASURED, not terminal) | 54 | 10.04 | 169 |
| r5-e / r6-f / r7-g | 0 / 0 / 0 | 24 / 24 / 28 | 2.77 / 2.73 / 2.85 | 106 / 99 / 114 |
| r8-h / r9-i / r10-l-rank | 0 / 0 / 0 | 24 / 25 / 26 | 2.65 / 2.80 / 2.82 | 110 / 99 / 104 |

Files (measured on plane gex44, copied back, committed with this entry): `measurements/{D-KME-L,E-KME-L,F-KME-L,G-KME-L,
H-KME-L,I-KME-L,L-KME-L,D-CPP-D-W7}-2026-10-05.md`; the seven KME-L files carry `population_match: exact` and
`terminal_evidence: true`. W7's 12 % over-coverage is plausibly the same junction alias (UNVERIFIED); D-KME-L says
`second_workload_required: false`. Not yet done: writing pillar terminals into the IC ledger / owner-bundle rows.

ROI reading: the same population answer cost 869 s / 101.5 GB unscoped (10 locator scans of everything) and 24 s /
2.83 GB scoped (one pass over the one project that holds the population). Most of the rescan cost was scope, not parsing:
a project-scoped walk gives ~36x, before any index exists.

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

## Handoff to autonomous-optimization (2026-10-05, session 7cf90b36)

Facts this record adds after that plan's approval snapshot (laptop HEAD 7ea78fa3):

- **IC gen1 state moved** (its P0 "reconcile IC gen1 state"): `d2e4edef` writes terminals D, E (FALSIFIED), F (MERGED,
  handoff F), G, H, L (RESEARCH_INSUFFICIENT); I stays OPEN (consumes SC B, which has no terminal). H's pre-registered
  "verification below materiality" check FAILED (5.1 %, 97 % verifier subagents). Handoffs F, I: `92ea26f8`.
- **Verifier defect fixed in IC, latent in SC**: the IC wrapper never rebound `REQS_REL` / `REQ_ROW`, so X2 judged IC
  pillars against CE's REQUIREMENTS rows; fixed in `d2e4edef` with mutants. `tools/test_skill_capability_program.py`
  does not rebind them either (unverified there, not touched). A gen2 wrapper must bind all seven globals.
- **Equivalence oracle for P2**: the 7 KME-L files were produced on plane gex44 with `--project-filter
  "KobiiCraft-Core-Files|kme-wt-arena2"`; unscoped, the population drifts by exactly `_archived` (1 session) + the
  mcp-video-analyzer junction alias (one PP session x2). P1's dedup must make the unscoped walk equal the scoped one.
- **Per-step cost, scoped** (all 9 rows in 4 min 15 s): 24-28 s and 2.65-2.85 GB each; CPP-D-W7 54 s / 10.04 GB and
  referenced at coverage 1.12 (not terminal), plausibly the same alias.
- **GEX44 state**: corpus copy `/home/kobii/kme-corpus/projects` (9.50 GB, 10,577 files, 3 relative symlinks
  recreating the laptop junctions, Owner option B, CostaLuz included); repo clone `/home/kobii/missions/zero-rescan-run`
  at 61909502; runner + outputs `zero-rescan-out{,2}`. The older `/home/kobii/kme-l-corpus` (1.2 GB) is redundant.
  Neither is deleted: both need the Owner's go, and the gen2 run on GEX44 may want the full copy.
- **Laptop memory**: the low-memory reaper killed two background jobs this session; laptop runs of whole-corpus work
  are not reliable at the current load.
