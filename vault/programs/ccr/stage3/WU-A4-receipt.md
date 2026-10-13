# A4 receipt
Status: DONE_WITH_LIMITS

Limits, each with its number:
- **L1, budget overrun.** This unit processed 6,102,046 tokens at the moment this receipt was written (64 calls). The budget was 3,000,000, with a stop at 4,500,000. The overrun was noticed only when K7 was measured. The remaining calls (this receipt and the commit) add roughly 0.5M more.
- **L2, mod change not applied.** 1 edit to `mods/cpp-cognitive-runtime/hooks/policy.ts` was refused as a sensitive file. The `rotate_advice` wiring and the bounded instruction index ship as `vault/programs/ccr/stage3/a4/ccr-mod-a4.patch`, validated on a scratch copy (30/30 tests, estate gate PASS). Until it is applied, the real mod fails the estate gate (35,927 > 8,000 bytes at 10x).

All numbers: Linux plane GEX44, host 2.1.296. Evidence: `vault/programs/ccr/evidence-v4-stage3-A4.md`.

## Done-check
- **k\* per class:**
  - bounded-code: ctx* 69,337, k* 10.2
  - long-textual: 70,392, k* 9.7
  - generic: 68,481, k* 9.7
  - lookup (LOW, n 1): 40,280, k* 18.4
  - lobby: 341,938, k* 27.6
- **Decision rule:** rotate iff carry ≥ X* = sqrt(2·rotate_once·g/0.1) and E[remaining] > k*.
- **Measured capsules:** 164-564 tokens (PP n 119, Lobby n 102).
- **Held-out replay, BE vs the 300k rule:**
  - bounded-code +3.99 % vs 0.0 %
  - lobby +5.47 % vs +2.28 %
  - long-textual -0.64 %
  - No class reaches 15 %.
- **Elasticity gate output:**
  - Estate gate: real mod FAIL (10x → 35,927 bytes); patch PASS (10x → 3,646 bytes).
  - History at call 120 (Lobby, n 22): carry 503,776 vs capsule 264,394 (ratio 0.525).
- **Invalidation test:** `V_CCRCONT_07_one_read_invalidation` passes (fingerprinted facts and refs; an edit invalidates; a rebuild revalidates).
- **gsd shadow:** `test_gsd_epoch_breakeven_shadow` 6/6. `tools/test_gsd_mission.py` MC_PASS=230/230.

## Files
- **Added:**
  - tools/ccr_breakeven.py and tools/test_ccr_breakeven.py
  - tools/ccr_estate_gate.py
  - tools/test_gsd_epoch_breakeven_shadow.py
  - vault/programs/ccr/stage3/a4/: breakeven.json, capsules-pp.json, capsules-lobby.json, estate-gate-before.json, estate-gate-after.json, ccr-mod-a4.patch, pgo/bounded-code-worker.breakeven.json, pgo/read-only-reviewer.breakeven.json
  - the evidence file
- **Changed:**
  - tools/ccr_continuation.py and its test (fingerprints)
  - tools/gsd_epoch.py (shadow, ledger field)
  - tools/gsd_mission.py (row.turn_end.shadow_breakeven)
- **Choice:** read-only-reviewer is mapped to the long-textual fit.

## K7
| item | estimate | actual |
|---|---:|---:|
| this worker session d37c61fb (~/.claude/projects/-home-kobii-missions-ccr-s3) | 1,500,000 (plan) / 3,000,000 (packet budget) | 6,102,046 processed at receipt time (64 calls; final ≈ 6.6M after the receipt and commit calls) |
| canary / probe sessions | 0 | 0 (no model calls, so no RAM admission needed) |
| **total** | 3,000,000 | **≥ 6,102,046** |

## LAPTOP_APPLY
Run from the laptop clone after merging mission/ccr-s3:

    git apply vault/programs/ccr/stage3/a4/ccr-mod-a4.patch
    claude plugin test mods/cpp-cognitive-runtime          # expect 30 pass
    python tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime   # expect PASS on the laptop estate
    copy vault/programs/ccr/stage3/a4/pgo/*.breakeven.json  %USERPROFILE%\.claude\ccr\state\pgo\
    git commit -- mods/cpp-cognitive-runtime/hooks/policy.ts mods/cpp-cognitive-runtime/hooks/register.ts mods/cpp-cognitive-runtime/hooks/policy.test.ts

The release of the mod (`tools/ccr_release.py`) stays with the coordinator. The advice is observe-only, and nothing in it enforces rotation.
