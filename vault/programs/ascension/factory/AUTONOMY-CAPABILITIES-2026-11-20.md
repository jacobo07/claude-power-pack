# Ascension: capabilities that remove stalls (investigation 2026-11-20, pane 8949bcc6)

Question (Owner): which capabilities would let the reconstruction keep going, without stopping, until every function
is rebuilt? Method: measure what stalled the work (GEX44 ledger, autopilot.log, owner_queue, last 7 days; plus a
catalogue of the RESUMPTION_FILE history) and inventory what already exists on GEX44. Measured = observed today with
the command named; projected = labelled.

## Measured on GEX44 (2026-11-20 ~01:55Z, last 7 days)
- Day cap: 974 `budget wait` ticks = ~81 lane-hours parked waiting for the next UTC day (autopilot.log). Spend
  ~471-492M/day on 11-16..11-19 against DAY_CAP 500M.
- Overhead tokens (not worker): plan 248M, judge 88M, lever design 18M = 354M in 7 days (ledger kinds).
- Report progress in the week: only `factory_match` rows (WSR 9,121, MKWLIB 5,389, MKW 3,819), 0 tokens.
- Host: 20 cores, load ~9-10, 28-39% CPU idle (vmstat), 46 GB RAM available.
- Owner queue (7 days): judge INCONCLUSIVE/DISAGREE, policy refusals (S26C profile, "fresh" asks, no rival), EVO
  research stops, CHECKPOINT_ON_BRANCH; many "NOTICE (no action needed)".

## Already on GEX44, unused or under-used
- decomp-permuter (`/home/kobii/tools/decomp-permuter`, own venv): no lane runs it.
- Donor decomps with Matching SDK/NW4R/MSL source: petari 2,023 Matching objects (RVL_SDK + nw4r), ogws 474,
  xenoblade (RVL_SDK), ss 494, tp 787.
- WSR `tools/m3a` donor pipeline (ogws_compile, donor_match with negative control, donor_tu): 2,563 ogws functions
  match WSR byte-for-byte (1,197 unique; negative control 2,513/2,513 missed), yet only 16 TUs were applied because
  application required a contiguous TU run (392 TUs not contiguous: newer library versions).
- Ghidra headless (`/opt/ksr-decomp/ghidra_12.1.2_PUBLIC`), dtk 1.8.3, objdiff-cli, wibo, all compilers.

## Stall catalogue from the history (RESUMPTION_FILE, all ~1,000 lines; sub-agent review, 2 citations re-checked)
Hours: "stated" = written in the file; "est." = timestamp subtraction, order of magnitude only.

| # | Class | Incidents | Lane-hours | Still recurs? |
|---|---|---|---|---|
| 1 | Autopilot park / hold / re-judge defects | ~16 | est. ~110 (one event ~80: 7/8 lanes parked 11-17 00:07Z-12:47Z) | yes, a new defect per day 11-14..11-18 |
| 2 | Day cap / research cap / cost-hold waits | ~14 | est. ~30 history; **81 measured in the last 7 days** | yes, caps raised by hand |
| 3 | Policy refusals of plans | ~12 named; 111 of 348 plans | est. ~16 | yes (S26C 67, asks-fresh 47, no rival 16, >10M 14) |
| 4 | Judge / gate defects (bare-run, pinned pools, pre-existing red) | ~18 | est. >=10 | yes (11-19 MKW S204M, MKWLIB S207L) |
| 5 | Worktree / git hygiene | ~9 | stated 13.05 | yes, new cause each time (today: dtk rewrites symbols.txt) |
| 6 | Permission / host prompts | ~5 | stated 3.5 + unknown | workaround only (`claude stop`) |
| 7 | Owner-only gates | ~16 | est. >=9 | by design; `close` still needs `!` commands |
| 8 | Context wall / session death / unwoken worker | ~9 | stated 4.2 | mostly fixed; notices go to "no channel configured" |
| 9-11 | Tooling gaps, pane collisions, instrument failures | ~35 | mostly tokens | partly |
| 12 | Method yield plateau | programme-wide | ~1.89B tokens, 141 gens, 5 CERT+MATCH | mitigated only where the factory runs |

## Capabilities, ranked by functions reconstructed per stall removed
1. **Factory lane (deterministic, cron on GEX44, 0 tokens).** sweep -> carve -> scratch build -> gate (binary hash
   unchanged, 0 lost, lane clean, HEAD guard) -> apply in a hold/park window -> advance the MATCH snapshot -> ledger.
   Today every factory step needs an agent session; this removes the session (class 8), the day cap (class 2: no
   tokens) and the plateau (class 12) for the deterministic share. Uses the 28-39% idle CPU.
2. **Standing authorization for 0-token deterministic applications** under exactly those gates, modelled on the
   existing standing authorization for known-boundary sources (brief.md). Removes the per-application Owner gate
   (class 7) for this class only; anything with tokens, rulings or a gate change stays the Owner's.
3. **Cross-game transfer + TARGET_AMBIGUOUS by address** (generalized port_ksr): 3,541 transfer-ready functions,
   6,799 never attempted (leverage census). Plugs into (1) as a stage.
4. **Function-level donor transfer** from petari (2,023 Matching objects), ogws, xenoblade, ss, tp: m3a already proved
   2,563 WSR functions byte-identical but applied 16 TUs because a TU had to be contiguous; per-function units remove
   that condition. Open problem: compiling one function out of its donor TU. Shared SDK = 12-91% of each game's bytes.
5. **Permuter on the >=90% band** (decomp-permuter installed, unused): ~5,000 functions, CPU only, as a stage of (1).
6. **Budget re-route:** day cap by cost (RF proposal, unapplied); model generations only on what (1)-(5) leave;
   cut the 354M/week planning/judging overhead. Owner decision.
7. **Lane hygiene self-heal:** lane builds never dirty tracked files (dtk `--no-update` in lane builds or commit the
   refinement in-window); arm/relaunch auto-restores a build-dirtied file with a saved patch (class 5).
8. **Notification channel** for owner_queue QUESTION lines (push notification / mail draft): today "no channel
   configured", so Owner gates wait until a pane reads the file (classes 7, 8).
9. **Owner-turn proof without a transcript copy** (S162R needs two `!` commands because the session-file guard blocks
   the copy): a sanctioned, Owner-run one-step command. Owner decision on the mechanism.
10. **Gate contract check** before a generation is judged: every pinned gate must run bare (class 4).

## DTK: what we need that it does not cover (measured 2026-11-20 on GEX44)
| # | Gap | Evidence | Fix | Status |
|---|---|---|---|---|
| D1 | RSO modules (FIFA's 6.3 MB game code) | dtk 1.8.3 `rso` = info/make only; `rso info` on fifaf.code.rso: "failed to fill whole buffer" | (a) **dtk v1.9.0 (15-Nov) adds full RSO/SEL support** (modules in config.yml, split, rebuild, `dol config`), v1.9.1 current; (b) FIFA ships the RSO split in 5 files: `factory/fifa-rso/rso_join.py` tiles them at the header's own offsets (each part = its span exactly, 8 trailing zero bytes) -> fifaf.rso 13,127,288 B sha1 ba8fcf0d; dtk 1.9.1 reads it: 17 sections, code 0x6297BC, **31,462 exports with real C++ names** (24,482 in code), SEL 593 exports | DONE: join + read; split in progress |
| D2 | Overlapping functions abort the whole split | dtk 1.9.1 on FIFA: `Overlapping functions 0:0x390840-0:0x390C70 -> 0:0x3909B4` (hand-written video IDCT `IDct10_GC`, two entry points) | a `type:label` seed does NOT help (25 identical failures); two adjacent functions -> "Unpaired epilogue 0x390C64"; **module `skip_cfa_ranges: [{start: .text:0x390840, end: .text:0x390C70}]` resolves it** | DONE |
| D7 | RSO `_ctors`/`_dtors` exports break dtk 1.9.1 | next error: "Multiple symbols with name _ctors" (an export + dtk's own); renaming the exports in an analysis-only copy needs their ELF name hash re-patched (export table stores it); then "Split auto_fn_1_40870_text .ctors (0x0..0x4) ends within symbol '_ctorX' (0x0..0x608)": the export gets the whole section as size and a symbols.txt label seed (at `.section2`, the load-time name) does not override it (same error twice -> stopped) | patch dtk (export at a ctors/dtors section start = label, or skip it) -- needs a Rust toolchain on GEX44 (none today), or drop the two entries from the analysis copy's export table | OPEN: main.dol part already analysed (4,194 fns, 841 named) |
| D3 | Map-derived split does not round-trip | TENNIS: dtk wrote splits.txt with two `.rodata` (DOL .data6 unnamed in the map), then refused its own file "Multiple sections with name .rodata" | rename the second to `.rodata2` + move its 2,379 symbols | DONE (tn-f2) |
| D4 | Map-derived split relinks with .ctors/.dtors order wrong | TENNIS relink same size, all data sections identical, but .ctors 208 B, .dtors 8 B, 2 refs in .init/.text (+8 B shift) differ; same with dtk 1.9.1 | give .ctors/.dtors ownership from the map to units, or split TENNIS without the map (WIIPARTY's auto-split relinks byte-identical) | OPEN: blocks TENNIS's `main.dol: OK` gate |
| D5 | Lane builds rewrite tracked symbols.txt | template rule `dtk dol split $in $out_dir` (project.py:1494) has no `--no-update`; WIIPARTY: 684 lines | `--no-update` for lane builds, or commit the refinement in-window | OPEN (patch saved) |
| D6 | Version pin | lanes on dtk 1.8.3 (2-Mar); 1.9.x also fixes .ctors/.dtors unit ownership in RELs, extab search across gaps, quick_analysis of new modules | upgrade per lane in a window, gate = main.dol OK + 0 lost | proposal |
| -- | Not DTK (m2c producer) | WIIPARTY m2c failures: 145 "Unable to determine jump table" = `bctr` through a function pointer; 111 "Cannot find branch target" = tail call `b fn_X` out of the single-function input; dtk asm correct in both samples | producer: declare call targets as functions; mark pointer `bctr` as a call | proposal |
