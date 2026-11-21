---
covers: [ascension, factory, m2c, objdiff, mkw, wsr, ksr, fifa, wiiparty, tennis, materialize]
status: F1 measured, F2-F4 open
owner_go: "go ahead with everything" (Owner, 2026-11-19, pane 81dcf473)
---
# Ascension reconstruction factory (deterministic, no model call)

## Why
Measured 2026-11-19: Ascension LLM generations certify ~2 functions per 1M processed tokens. KSR's 8,687 certificates
came from a deterministic pipeline instead (decomp_work/b8d1db7edd42: Ghidra bounds -> m2c lift of every function ->
mwcceppc under wibo, per-object flag arm -> byte identity), 25% of all functions in 710 s. It had run on ONE binary.

## F1: generalised runner (DONE, measured)
`/home/kobii/agora/factory/factory.py` (laptop copy: pane 81dcf473 scratchpad). Reuses read-only: the pinned m2c
producer + venv (/opt/ksr-decomp), t1-campaign `repair.transform_v5` + `toolchain_sd.retype`, `cv1.objdiff_pct`, KSR
wibo/objdiff. Per dtk-template repo: corpus from symbols.txt -> m2c over dtk asm -> 2 flag arms -> objdiff vs the
function's own dtk target object -> one arm per object (KSR rule; FLAGS_SPLIT certifies nothing).
Output: <out>/{corpus.jsonl, m2c/, sweep.jsonl, matched.tsv, summary.json}. A row in matched.tsv is PROVISIONAL_MATCH.

Measured (GEX44, nice 10):
| run | functions | L1 | compile | 100% object-consistent | >=90% near | new vs lane reports | wall |
|---|---|---|---|---|---|---|---|
| mkw-main-pilot400 | 400 | 366 | 103 | 49 | 17 | - | 29 s |
| mkw-main-full | 9,086 | 8,222 | 2,719 | 1,213 | 451 | 1,111 new (592 >8 B, 36,692 B) | 10 min |
| mkw-staticr-full | 17,232 | 16,003 | 7,228 | 4,078 | 1,299 | 2,989 new (1,278 >8 B, 96,152 B) | 10.5 min |
| wsr-main-full (Wii/1.0) | 34,148 | 30,375 | 19,023 | 8,647 | 2,463 | 8,586 new (3,851 >8 B, 232,104 B) | 39 min |

Totals 2026-11-19: 12,686 new PROVISIONAL_MATCH (MKW 4,100 vs its report's 3,922; WSR 8,586 vs its report's 136),
0 model tokens, ~1 h CPU at nice 10. Not yet counted by any report (F2). TARGET_AMBIGUOUS (WSR 5,249, StaticR 1,550)
= a name in more than one target object; recoverable by keying the target on address instead of name.

Largest loss: L1 -> compile (8,222 -> 2,719 on MKW). Next yield lever = compile repair (types/headers, C++ this-calls),
not more search.

## F2: materialize into the product tree (MKW, MKWLIB, WSR DONE 2026-11-19)
Route used: `factory/carve.py` = one unit per function for matches in dtk `auto_*` objects (the MKW lane's own
`auto_tu` shape), `Object(NonMatching, "factory/<sym>.c", cflags=[chosen arm])`, split = the function's exact .text
range. `factory/materialize.py` (greedy multi-function unit with per-step byte check) stays for named units (not run).
MKW result (lane/mkw 8234f1c, fast-forwarded while the lane was PARKED, rebuilt in the lane): report.json matched
3,922 -> 7,723 (+3,801; 1,044 main + 2,739 StaticR carved), matched code 7.36% -> 9.43%, 0 functions lost by
unit::name, main.dol OK, StaticR.rel OK, no split unit removed or changed (255 -> 1,319 and 2,034 -> 4,773 units).
total_functions 26,639 -> 27,057: carving auto objects changes objdiff's enumeration; use matched code % for trend.
Autopilot MATCH snapshot match/MKW.json advanced 3,904 -> 7,723 under cron.lock (ledger kind `factory_match`, 0
tokens), so no generation is credited for factory work; side effect: S204M's 18 pending functions are in it too.
MKWLIB (mkw-lib cb3faf0, same binary as MKW): report 2,043 -> 7,408 (5.96% -> 8.96%), 0 lost, main.dol OK, StaticR.rel
OK; snapshot match/MKWLIB.json 2,019 -> 7,408. WSR (wsr-decomp 1f4f821): report 136 -> 8,722 (code 3.64%), 0 lost,
main.dol OK; snapshot match/WSR.json -> 8,722.

### Lane merge KSR -> WSR (DONE 2026-11-19, `factory/port_ksr.py`)
KSR (t1-campaign) and WSR target the same main.dol (sha1 7752caae). port_ksr.py takes each KSR certificate WSR lacks,
recompiles it against WSR's own target object and admits it only at objdiff 100%: 645 candidates -> 535 MATCH, 96
NO_COMPILE, 14 NO_MATCH (those 110 stay counted in KSR only). Scratch first (8,722 -> 9,257, code 3.88%, 0 lost,
main.dol OK), then lane commit 483a94f, lane rebuild main.dol OK, report 9,257, snapshot match/WSR.json 8,722 -> 9,257
(backup `WSR.json.bak-81dc-port-20261119T192111Z`; checked: snapshot == lane report set, 0 lost vs backup).
Autopilot lanes 8 -> 5 (Owner "go ahead to both", 2026-11-19): KSR, MKWLIB, FIFATC set `status PARKED,
park_kind merged, merged_into WSR/MKW/FIFA` under cron.lock (state.json CAS e6bc2729, backup
`state.json.bak-8949-merge-20261119T220016Z`, ledger kind `owner_park`). No worker was alive in any of the three; their
missions were left as they were. `park_kind merged` is never auto-lifted (only `budget` is). Undo = restore the backup.

### Original F2 plan
Goal: each PROVISIONAL_MATCH counted by the lane's own `ninja build/<GAME>/report.json` (the autopilot MATCH class).
- Per target object with >=1 match: one source file holding its matched functions (prelude + transformed lift), compiled
  with that object's chosen arm; unit declared in configure.py as `Object(NonMatching, ...)` with those cflags and the
  game's mw_version; the split entry must exist in splits.txt (auto_* objects need a named split first).
- Done-gate: ninja report.json before/after; matched_functions rises by the materialized count and no previously
  matched function is lost; `main.dol: OK` still builds where the lane builds; a planted wrong source is refused.
- Ownership: a lane's product repo is written only between generations (lane PARKED or under a hold), in its own commit,
  never while its worker runs (concurrent-writers rule).

## F3: the other binaries (OPEN)
FIFA/FIFATC (b8637681, RSO, 24,482 named fns), WIIPARTY (f8f46694, monolithic DOL, no symbols), TENNIS
(SportsPackEP.dol) have no dtk-template build. Each needs a dtk split (config.yml + symbols/splits; Ghidra bounds via
ExportL1.java where no symbols exist) before F1 runs. MKWLIB = MKW binary: share MKW's run, do not run twice.

**2026-11-19 (pane 8949bcc6), measured.** Scratch repos of symlinks under /home/kobii/agora/factory/ (no lane repo
written): WIIPARTY `wp-repo` reuses the S51W dtk split (build/s51w/supp01, relinked main.dol sha1 93b41984 = orig,
7,416 fns, 284 objects); TENNIS `tn-repo` = new `dtk dol split` of fabric-tools/in/SportsPackEP.dol WITH its
SportsPackEP.map (14,885 fns, 560 map-derived objects; 10 data/bss sections not in the map, no relink checked yet);
FIFA `fifa-repo` = main.dol only (4,194 fns, 46 objects): the game is the 7.5 MB split RSO and dtk 1.8.3 cannot read
it (`rso info`: "failed to fill whole buffer"; rso has only info/make) -> needs an RSO->ELF converter. Pilots, 400
fns, seed 20261119, factory.py as is: WIIPARTY 106 (26.5%), TENNIS 95 (23.8%), FIFA main.dol 68 (17%); compiler
version barely moves it (Wii/1.0, 1.1, 0x4201_127 within 1). Full base sweeps queued (wp-main-full, tn-main-full).

**Compile-failure lever (typegen/, measured).** Funnel per 400: m2c L1 ~90% -> compiles 51-61% -> 100% 17-27%.
mwcc errors of the non-compiling lifts (errclass.py): untyped member access (10149), `?` declarations (10121),
void*/int conversions (10209/10377/10499). Variant `typegen/factory_vs2.py` = m2c `--valid-syntax` + m2c_macros.h +
`#pragma gcc_extensions on` in the prelude (front-end only; certification flag arms unchanged):

| pilot 400 | compiles | 100% any arm | union with base | >=90% not 100 |
|---|---|---|---|---|
| WIIPARTY base -> vs2 | 205 -> 301 | 106 -> 121 | 123 (+16%) | 26 -> 59 |
| TENNIS base -> vs2 | 243 -> 328 | 95 -> 108 | 111 (+17%) | 53 -> 84 |

Compiling is no longer the bottleneck (84-92% of lifts compile); the bottleneck is now codegen identity: of the
compiled, ~37% are byte-identical, and the >=90% band (15-21% of the sample) is the next lever (permuter / model on
near misses). Second cost: the one-arm-per-object rule over dtk auto objects drops a FLAGS_SPLIT object whole
(WIIPARTY vs2 121 -> 91 counted, TENNIS 108 -> 99); with carve.py's one-unit-per-function product layout the rule's
premise (one TU, one flag set) may not hold -- an Owner certification question, not changed here.

**Owner ruling 2026-11-19 ("y", pane 8949bcc6): a one-function unit certifies with the flag arm it matched.** The
one-arm-per-object rule stays for multi-function units (materialize.py, real TUs); carve.py units take the arm per
row of matched.tsv (it already did). Full WIIPARTY base sweep (wp-main-full, 7,404 fns, 39 min): L1 6,578, compile
3,703, 100% any arm 1,644, object-consistent 1,205 (2 FLAGS_SPLIT objects cost 439), >=90% 594.
**WIIPARTY F2 DONE.** New dtk-template project (configure.py + tools/ from wsr-decomp, config.libs empty, orig at
orig/SUPP01/sys/main.dol, build.sha1 93b41984; baseline main.dol OK, report 0 fns). Run dir wp-main-full-perfn
(matched.tsv = 1,644 rows, one per function, `dol` arm first). carve.py -> 1,644 units; scratch wp-f2 faf7699; lane
wiiparty-decomp fast-forwarded 370ec95 -> faf7699 while S163W sat on its cost-breaker hold (no worker alive, lane
clean, HEAD guard), lane rebuild main.dol OK, report **0 -> 1,642 at 100 of 8,751 (code 2.71%)**, same set as
scratch, 0 lost. 2 carved functions do not reach 100 in the project build (open). DEBT: a lane build makes dtk rewrite
config/SUPP01/symbols.txt (684 data-string size refinements); restored to keep the lane clean (patch
factory/wp-lane-symbols-dtk-20261119T231339Z.patch) -- commit it in a window or every build re-dirties the lane.
WIIPARTY has no `match_report` in lanes.json, so the autopilot's MATCH class cannot see this progress (Owner decision).

## Leverage census 2026-11-20 (pane 8949bcc6, measured, 0 tokens; `factory/pareto/pareto.py`, `pareto2.py`)
Per function of each game's dtk TARGET objects: size and a reloc-masked body hash (a word touched by a relocation
keeps only its opcode). Matched = the game's own report (WSR, MKW, WIIPARTY) or a pilot matched.tsv (TENNIS, FIFA).
- Size Pareto (all 5 games alike): top 10% of functions = 50-61% of code bytes; functions >=256 B = 68-80% of bytes
  and match 0-7%; matches live in <128 B. The one-shot factory is structurally a small-function machine.
- Shared library code: identical masked bodies (>=16 B) present in another game cover WSR 21%, MKW 12%, WIIPARTY 70%,
  TENNIS 44%, FIFA main.dol 91% of bytes (~6,000 groups; 4,785 in >=3 games, 1,599 in all 5). Names where known:
  TRK, NWC24, NHTTP, RFL, Bluetooth (bta/btm), GX, MSL (`__kernel_rem_pio2`), i.e. the RVL SDK and its libraries,
  linked identically into every game. Solve once, apply to every game holding the body.
- Transfer-ready now (unmatched body == a MATCHED body in another game): WSR 776, MKW 373, WIIPARTY 240, TENNIS 1,676,
  FIFA 476 = 3,541 functions (port_ksr verified 535/645 = 83% for the same-binary case; cross-game unmeasured).
- Never attempted: TARGET_AMBIGUOUS (target_index keys by name) WSR 5,249 + MKW StaticR 1,550.
- Compile lever on MKW (pilot 400, main): compiles 99 -> 241, 100% 47 -> 76, >=90% 16 -> 52 (vs2 vs base).
- Near misses already measured (>=90%, not 100): WSR 2,463, MKW 1,299+451, MKWLIB 1,431+451, WIIPARTY 594.

## F5: factory lane (Owner ruling 2026-11-20, pane 5a77ca0e: lane + standing authorization)
covers: [factory-lane, standing-authorization, carve-vs2, perfn]
**PRD.** Every factory step so far needed an agent session (stall classes 2, 7, 8, 12 in
`vault/programs/ascension/factory/AUTONOMY-CAPABILITIES-2026-11-20.md`). F5 runs the deterministic share alone: a cron
job on GEX44, 0 tokens, that applies already-measured factory matches to a lane in a window and advances the MATCH
snapshot, with no Owner turn per application (standing authorization, brief.md section of the same date).
**Arch.** `/home/kobii/agora/factory/lane.py tick` (cron hourly, `flock -n factory.lock`, nice 10, kill switch
`~/.claude/state/factory-lane.ready`). Config `factory/lanes_factory.json`: per lane {lane, repo, game, scratch, report,
binaries (ninja "X: OK" names), runs: [{run, producer, lib, compiler}]}. Per lane per tick:
1. PREPARE (no lock): scratch = shared clone at lane HEAD; for each run: `perfn.py` (any-arm per function, dol first;
   reproduces the F2 list byte for byte) -> `carve.py --producer --lib` (skips units already present, so a vs2 run adds
   only its new functions). Nothing carved -> done.
2. GATE (scratch): configure + ninja: every binary line `OK`; report: lost == 0 vs the lane's report at the same HEAD,
   gained > 0; tracked files the build dirtied (symbols.txt, D5) restored. Commit in scratch (src/factory*,
   configure.py, splits). Fail -> owner_queue NOTICE with the log, scratch left for inspection, no retry until the run
   set or the lane HEAD changes.
3. APPLY (under the autopilot's `cron.lock`, so no tick can arm during it): lane HEAD == scratch base, lane tracked-clean,
   autopilot state status != RUNNING (a park/wait/stop window). ff the lane to the scratch commit; lane configure +
   ninja + report; binaries OK; lost == 0 vs match/<LANE>.json (else `git reset --hard <base>` of the lane, NOTICE);
   snapshot advanced (backup `.bak-factory-<ts>`), ledger `factory_match` (tokens 0), owner_queue NOTICE.
**Standing authorization scope.** Only 0-token deterministic applications under exactly these gates. Out of scope (stay
the Owner's): anything spending tokens, a ruling, a gate or certification-rule change, a lane config change, dtk version
changes, producer changes not already measured.
**AC.** (a) perfn reproduces wp-main-full-perfn (DONE 2026-11-20: dol-first identical, ksr-first differs 1,357);
(b) carve vs2 union on WIIPARTY carves 2,100 - 1,644 = 456 (DONE, 456); (c) a dry tick on a lane with nothing new
carves 0 and touches nothing; (d) a RUNNING lane is never applied; (e) a forced lost != 0 is refused (negative control).
**Status 2026-11-20 11:30Z (pane 5a77ca0e).** LIVE: cron `*/10` (`flock -n factory.lock`, `python3 -I lane.py tick`, log
`factory/lane.log`), ready file present, config = WIIPARTY only (base + vs2 runs). Tick 1 GATED scratch `eb9e76f` on
faf7699 (carved 456, report 1,642 -> 2,097 at 100, code 2.71 -> 3.99%, 0 lost, main.dol OK) and waits: WIIPARTY RUNNING
S163W (AC d observed at 11:15, 11:20, 11:29). AC (e): `lane.py selftest` 4/4 (verdict arithmetic from both poles); the
live apply-refusal path is not yet exercised. AC (c) not yet observed (needs a post-apply tick). pp-code-reviewer: APPROVE
with notes; MEDIUM F1 (exception after ff -> reset + NOTICE + re-raise) and F2 (failed git diff is not clean), LOW F3
(duplicate unit name in one batch), F4 (`--producer=X`) fixed and redeployed (backups `*.bak-5a77-review`). Open
note: carve/perfn failures now NOTICE once; the `links` symlinks share the lane's build/tools and build/compilers.
Brief section "Factory lane: standing Owner authorization" live (brief.md f3c695ce -> dc99cea2, policy_check [] as phase
and as fact, negative control caught). Laptop mirrors: `vault/programs/ascension/factory/{lane,perfn,carve}.py`,
`lanes_factory.json`, `autopilot/brief.md`.
**Rollback.** Remove the cron line; delete the ready file; each application is one ff commit (`git reset --hard` to the
`base` in its ledger row) + the snapshot backup.

## F6: twin transfer (S2; Owner "y" 2026-11-21, pane 3581ade8)
covers: [twin-transfer, s2, speed-s2]
**PRD.** The census found 3,541 unmatched functions whose reloc-masked body equals a function MATCHED in another game
(WSR 776, MKW 373, WIIPARTY 240, TENNIS 1,676, FIFA 476). Solving one body once and copying its source should cost one
compile + one objdiff per function, 0 tokens. port_ksr did this for the SAME binary (535/645 = 83%); cross-game is
unmeasured, and F6 measures it before any lane depends on it.
**Premises (verified 2026-11-21 11:18Z).** `factory/pareto/shared_bodies.json` (1.0 MB, Nov 20) maps masked hash ->
[[game, name, size], ...] (`pareto2.py` reads it). A matched.tsv row is `<obj>:<ADDR>\t<arm>`: it names the arm, not
the source file. Carved donor sources exist as one-function units `src/factory/<sym>.c` with their cflags and
mw_version in the lane's configure.py (carve.py, port_ksr.py). Hand-written multi-function TUs (the MKW public decomp)
are NOT one-function sources.
**Arch.** New `factory/twin.py --lane L --repo SCRATCH [--limit N]`, built on port_ksr's verify-then-carve shape:
1. CANDIDATES: f unmatched in L's report; its masked group has a member d MATCHED in game D != L.
2. DONOR SOURCE: d's one-function unit in D's lane repo (`src/factory/<d>.c` + cflags + mw_version). A donor that is
   only a matched.tsv row or a multi-function TU -> state `NO_DONOR_SRC` (counted; phase 2 below).
3. RENAME: masking hides relocation TARGETS, and D's source names D's symbols. Walk the relocations of d (D's target
   object) and f (L's target object) at the same offsets. Each pair gives a map D-symbol -> L-symbol, and the source's
   identifiers are rewritten by that map, including d -> f itself. A target pair that disagrees across sites, or a
   symbol with no pair -> `RENAME_UNRESOLVED`.
4. VERIFY: compile in a private empty cwd (wibo cost scales with cwd entries) with D's flags under L's compiler first,
   then L's lane arms. MATCH only on objdiff 100% vs L's OWN target object (port_ksr.compile_pct). Address outside every
   existing split.
5. CARVE: same unit shape as port_ksr (`src/factory/<f>.c`, header naming donor game + symbol + hash, Object(NonMatching,
   cflags, mw_version)). Writes only in SCRATCH, plus `<repo>/factory_twin.jsonl` with one row per candidate and its state.
6. GATE + APPLY: exactly F5 steps 2-3 (binaries OK, lost == 0, gained > 0, apply in a window under cron.lock +
   `factory-apply-<L>.lock`, snapshot + ledger `factory_match`).
**Phase 2 (only if phase 1 MATCH rate warrants it).** Donors without a one-function unit: re-lift d with D's producer
(matched.tsv arm) or extract the function + its context from the TU. Measured separately.
Prior art to adapt (verified 2026-11-21; see `research/GITHUB-RESOURCES-2026-11-21.md` §1b):
- Ketbome/decomp-skills `dk.py cmd_twins` (MIT) does both steps 3 and phase 2 for MIPS/splat projects:
  - ordered symbol signature, zip rename map with a consistency refusal;
  - TU body extraction, transitive copy of declarations and types, prototype rebinding by cast;
  - `__asm__` aliasing, revert on no match.
- F6 ports its logic to PPC dtk relocations, with the MIT notice. Our gate stays objdiff 100% vs the lane's own target
  plus the F5 binary gate.
**Authority.** The F5 standing authorization covers applying under its gates only producers "already measured". twin.py is
a new producer, so the first apply per lane and adding a `twin` run to lanes_factory.json (a lane config change) need
the Owner's "y" on the pilot numbers.
**AC.** (a) Census: per lane, how many of the 3,541 have a one-function donor (states before any compile).
(b) Pilot WIIPARTY (240) + WSR (776): counts per state. MATCH rows recompiled in a second fresh cwd give the same bytes.
(c) Negative control: one deliberately crossed rename (two callees swapped) must not reach 100 and must be refused. Same
for a donor with a different masked hash.
(d) Same-binary control: KSR donors -> WSR reproduce >= the 535 port_ksr matched (ported units excluded from candidates).
(e) Scratch gate: binaries OK, 0 lost, gained == carved MATCH count.
**AC (a) MEASURED 2026-11-21 (pane 3581ade8, read-only `twin_census.py` over shared_bodies.json, which is built from the
Nov 20 reports, and the LIVE reports: WSR 10,653 / MKW 9,320 / WIIPARTY 2,134 at 100).** Unmatched receivers:
WSR: 600 with a one-function donor (40,944 B), 318 whose donor is matched only inside a TU, 360 with no matched twin.
MKW: 263 (18,172 B), 30 TU-only, 290 none. WIIPARTY: 4 (252 B), 203 TU-only, 133 none.
So phase 1 = **867** functions. Phase 2 (TU donors) = 551. A further WSR 4,338 / MKW 2,826 / WIIPARTY 3,719 have twins
only in TENNIS/FIFA, which have no lane repo. Their match state was not read, so this is NOT a transfer count. The
census's 3,541 shrank because the factory has matched many of them since.
**Rollback.** twin.py writes only in a scratch clone. Each lane apply is one ff commit (`git reset --hard <base>`) plus
the snapshot backup.

## F4: cross-lane index (OPEN)
One certified-source pool per binary (KSR+WSR, MKW+MKWLIB, FIFA+FIFATC) and a masked-byte index across binaries
(SDK/NW4R/EGG), consulted by the planner before any generation; the model works only on the residual (LF1 near misses).

## Rollback
F1 writes only under /home/kobii/agora/factory/. Delete the run dir to undo. F2 commits are per-lane and revertible.
