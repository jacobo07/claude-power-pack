# CCR v4 stage 3 -- A4 evidence: epoch economics and elasticity

Every number is measured on the **Linux plane GEX44, host 2.1.296**. Sources: the A3 corpus (`stage3/a3/corpus.json`, usage projections in `ccr-s3-data/pack/sessions`), and the Lobby Ralph-epoch transcripts 2026-09-22..26 (`ccr-s3-data/lobby-transcripts`, which were only read). The projections carry no text, so nothing here is derived from PP transcript text.

    D=/home/kobii/missions/ccr-s3-data; A=vault/programs/ccr/stage3/a4
    python3 tools/ccr_breakeven.py capsules-pp --corpus vault/programs/ccr/stage3/a3/corpus.json --root . --out $A/capsules-pp.json
    python3 tools/ccr_breakeven.py capsules-lobby --transcripts $D/lobby-transcripts --repo $D/a4-work/lobby-repo --work $D/a4-work/transcript-copies --out $A/capsules-lobby.json
    python3 tools/ccr_breakeven.py fit --corpus vault/programs/ccr/stage3/a3/corpus.json --pack $D/pack --lobby $D/lobby-transcripts --caps-pp $A/capsules-pp.json --caps-lobby $A/capsules-lobby.json --out $A/breakeven.json
    python3 tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime --json $A/estate-gate-before.json

`$D/a4-work/lobby-repo` is a copy of `lobby-repo` with `git init` and one snapshot commit (2f28a89b).

## 1. Weighted break-even per class

**Weights:** read 0.1, write 1.25, input 1, output 5.

**Model** (tools/ccr_breakeven.py). At a call with context `ctx`, continuing reads `ctx` on every later call. A rotation instead pays the following once:
- `rotate_once = 1.25*(floor + capsule)`, the capsule plus floor write
- `+ rehydration` (the measured weighted cost of calls 1..3 of a fresh class session, plus 3 reads of the capsule)
- `+ first-call overhead` (the measured uncached input plus output of call 0)

After a rotation, each call reads `floor + capsule + R`, where R is the context the 3 rehydration calls add. Growth after the decision costs the same in both futures, so it cancels out.

- `k*(ctx) = rotate_once / (0.1*(ctx - floor - capsule - R))` is the number of calls a rotation needs to pay itself back.
- **Decision rule:** rotate iff `carry = ctx - floor - capsule - R >= X*` **and** `E[remaining calls | call i] > k*(ctx)`.
  - `X* = sqrt(2*rotate_once*g/0.1)` is the renewal-optimal carry for a per-call growth g.
  - `E[remaining]` is the median remaining length of the train sessions that outlived call i.

**Why X*:** the first rule I tried was the greedy "rotate iff E[remaining] > k*". It **lost 22.3 % on Lobby held-out**: it rotated every ~15 calls, because each rotation's saving only lasts until the next rotation. The X* term fixes this. A regression test pins it (V-CCRBE-04).

**Fit and split:** each class is fit on train (the earliest 70 % by first ts, as in A3) and replayed on held-out. Sessions with fewer than 5 calls are excluded, as in E1.

**Capsules are MEASURED** with `tools/ccr_continuation.py`, not assumed to be 8k:
- PP: 119 capsules, built on this clone. Obligation = packet title, and `<packet>-receipt.md` is added when it exists. Projections have no note text, so a worst-case inline predecessor note slot of 901 tokens is added. "Used" = p50 + note slot.
- Lobby: 102 capsules. They were built at calls 40/80/120 of every session with at least 41 calls, using `--repo` on the git-init copy and `--transcript` on a copy cut at that call. 100 of them inline the note and 2 reference it.

| class | n train/held | capsule tok p50 / p80 / max (n) | capsule used | floor | R | g/call | rehydration | first-call | rotate_once | X* | **ctx\*** (rotate at) | k* at ctx* | k* at ctx 100k / 200k / 300k |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| bounded-code | 55/24 | 261 / 283 / 564 (80) | 1,162 | 17,783 | 6,824 | 2,141 | 19,801 | 497 | 44,328 | 43,568 | **69,337** | 10.2 | 6.0 / 2.5 / 1.6 |
| long-textual | 18/7 | 262 / 286 / 348 (25) | 1,163 | 17,402 | 6,641 | 2,324 | 19,878 | 492 | 43,924 | 45,186 | **70,392** | 9.7 | 5.9 / 2.5 / 1.6 |
| generic | 7/3 | 261 / 290 / 302 (11) | 1,162 | 17,188 | 7,164 | 2,222 | 17,412 | 852 | 41,551 | 42,967 | **68,481** | 9.7 | 5.6 / 2.4 / 1.5 |
| lookup | 1/1 (LOW) | 166 / 169 / 169 (3) | 1,067 | 17,591 | 2,114 | 531 | 11,753 | 447 | 35,842 | 19,508 | **40,280** | 18.4 | 4.5 / 2.0 / 1.3 |
| lobby | 36/15 | 226 / 247 / 405 (102) | 226 | 206,186 | 10,388 | 2,264 | 85,853 | 1,905 | 345,839 | 125,138 | **341,938** | 27.6 | -- / -- / 41.6 (ctx below floor+capsule+R: never pays) |

**Held-out replay** (weighted cost, saving vs A, rotations in brackets). C300 rotates when the simulated ctx reaches 300k, i.e. the gsd continuation ceiling at call grain. K40 is E1's arm D.

| class | n held | A cost | C300 | K40 | **BE (this rule)** | same replay under E1 assumptions (capsule 8k, no rehydration, no overhead): C300 / K40 / BE |
|---|---:|---:|---|---|---|---|
| bounded-code | 24 | 7,594,962 | 0.0 % (0) | 0.38 % (3) | **+3.99 %** (8) | 0.0 / 0.86 / 4.93 % |
| long-textual | 7 | 2,233,458 | 0.0 % (0) | 0.0 % (0) | **-0.64 %** (2) | 0.0 / 0.0 / 1.51 % |
| generic | 3 | 804,957 | 0.0 % (0) | 0.0 % (0) | 0.0 % (0) | 0.0 / 0.0 / 2.63 % |
| lookup | 1 | 25,419 | 0 | 0 | 0 | 0 |
| lobby | 15 | 48,132,600 | 2.28 % (20) | 1.54 % (22) | **+5.47 %** (12) | 5.73 / 5.46 / 7.89 % |

### Reading

- **Capsules are 30-50x smaller than E1's assumed 8k.** They run 164-564 tokens, or 1,162 with the note slot, so the capsule write is not what makes rotation expensive.
- **Floor and rehydration are what make it expensive.**
  - On Lobby the floor is 206k (the first call of a Ralph epoch), so one rotation costs 346k weighted. Rotating pays only past ctx ≈ 342k, and only when about 28 or more calls remain.
  - On PP work units the floor is about 18k, so rotating pays from ctx ≈ 69-70k with about 10 calls left.
- **The 300k ceiling never fires on PP held-out units** (0 rotations), while break-even would rotate them at about 70k.
- **BE beats C300 and K40 on bounded-code (+4.0 %) and Lobby (+5.5 %).** No class reaches E1's 15 % bar.
  - E1's +21.1 % for Lobby came from a different corpus: the laptop's live Lobby project dir, with a different floor mix.
  - Under E1's own assumptions on this corpus, K40 gives only +5.5 %. The two results do not contradict each other.
- **lookup is LOW**: n train 1. Only the 3 apr canaries survive the 5-call minimum, and the V1 streams are excluded.

## 2. Observe-only wiring

**gsd_mission rotation path (applied and tested):**
- `gsd_epoch.decide_turn_end` records `evidence.shadow_breakeven` = {would, cls, calls, k_star, x_star, carry, remaining, rule} beside the ceiling's decision.
  - The class comes from the WU packet via `ccr_pgo.classify`.
  - The call count comes from distinct message ids in the transcript.
  - The model file is `stage3/a4/breakeven.json`, or the path in env `CPP_CCR_BREAKEVEN`.
  - The shadow never raises and never decides.
- `record_cause` persists it into the `launch_cause` ledger row.
- `gsd_mission` copies it into `row.turn_end.shadow_breakeven`.
- Tests: `test_gsd_epoch_breakeven_shadow.py` **6/6**. It covers a disagreement being recorded while the ceiling still says continue, the ceiling's decision being unchanged at 310k, an unmeasured context, never raising, and the ledger row.
- `test_gsd_mission.py` **MC_PASS=230/230**, `test_gsd_epoch.py` 92/92, `test_gsd_epoch_context_budget.py` 6/6.

**Mod (`rotate_advice` in carryAdvice): NOT applied to `mods/`.**
- The edit to `mods/cpp-cognitive-runtime/hooks/policy.ts` was refused by the harness as a sensitive file, and I did not route around that.
- The change is delivered as `stage3/a4/ccr-mod-a4.patch` (228 lines, policy.ts + register.ts + policy.test.ts; `git apply --check` OK).
- It was validated on a scratch copy (`ccr-s3-data/a4-work/mod-patched`): `claude plugin test` **30 pass / 0 fail** (26 existing + 4 new).
- What it adds:
  - `parseBreakevenModel`, `rotateAdvice` and `expectedRemaining`.
  - `carryAdvice(floor, ctx, imageTok, be?)` returns `rotateAdvice`.
  - register.ts reads `<stateDir>/pgo/<unit class>.breakeven.json` (exported by `ccr_breakeven.py export`; files in `stage3/a4/pgo/`). It emits a `rotate_advice` receipt (`applied: false`) on the first call and whenever the verdict flips. The ratio rule and the advice file are unchanged.
- The real mod still passes its 26 tests unchanged.

## 3. Elasticity

**Estate V-gate** (`tools/ccr_estate_gate.py`):
- It feeds `decideUnitAttachment` / `decideUnitSection` the host's real 25 instruction files (160,848 bytes, plus 20k skill/agent/memory listings), then the same estate at 10x.
- Bound: unit out-bytes ≤ KERNEL_CHARS 8000 (register.ts reads the kernel up to 8000 chars). The kernel itself is 2,970.

| mod | policy sha256 | out 1x (instr/skills/agents/memory) | out 10x | verdict |
|---|---|---|---|---|
| `mods/cpp-cognitive-runtime` (as committed) | cd640ac46f8dc4e7 | 6,452 / 0 / 0 / 0 | **35,927** / 0 / 0 / 0 | **FAIL** (slope 0.0204 out-byte per estate byte) |
| patched copy (`ccr-mod-a4.patch`) | 74895721fcb57776 | 6,452 / 0 / 0 / 0 | **3,646** / 0 / 0 / 0 | **PASS** |

- Skills, agents and memory were already elastic: they are dropped at any size. The instruction index was not: it adds one line per file.
- The patch keeps one line per file while the whole text fits within 8000. Past that, it names files by directory (with count and chars, "Glob it for the names"), and collapses to parent directories until the text fits. Every file stays one Glob + Read away.
- The real host estate (1x) is byte-identical before and after the patch.
- Outputs: `stage3/a4/estate-gate-before.json` and `estate-gate-after.json`.

**History elasticity** (replayed Lobby transcripts, model-facing ctx at fixed call 120):
- 22 sessions are longer than 120 calls. The median floor is 212,020.
- Carry (as recorded): p50 ctx **503,776**, which is 2,431 tok/call above the floor.
- Capsule (break-even rotations, measured capsule): p50 ctx **264,394**, which is 436 tok/call above the floor.
- Ratio 0.525. The history slope falls 5.6x.

## 4. One-Read invalidation

M1 capsule refs already carried sha256, but inlined receipt facts did not. Now every inlined fact block's header carries `path=<posix> sha256=<hex>`.
- `ccr_continuation.fingerprints(capsule)` returns {path: sha}.
- `reuse(capsule, path)` answers `fingerprint-match` (reuse without a re-read), `source-changed: raw read required`, `not-in-capsule` or `source-missing`.

Test `V_CCRCONT_07_one_read_invalidation` checks the following:
1. Both an inlined fact and a ref are fingerprinted, and both are reused.
2. Editing the receipt invalidates its fact, while the untouched source stays valid.
3. A rebuilt capsule (raw read) is valid again and carries the new fact.
4. Unknown and deleted sources are refused.

`test_ccr_continuation.py` 7/7 (V-CCRCONT-01 flat-under-history still holds).

## Tests run (all exit 0)

- `test_ccr_breakeven` 7/7
- `test_ccr_continuation` 7/7
- `test_ccr_epoch_econ` 3/3
- `test_gsd_epoch_breakeven_shadow` 6/6
- `test_gsd_epoch_context_budget` 6/6
- `test_gsd_epoch` 92/92
- `test_gsd_mission` 230/230
- `test_gsd_mission_ccr_contract` 5/5
- `test_ccr_pgo` 16/16
- real mod `claude plugin test` 26/26
- patched copy 30/30
- estate gate: FAIL on the real mod, PASS on the patch
