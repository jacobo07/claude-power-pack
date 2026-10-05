# Pillar K -- second real probe after the K-local fixes (deploy + check)

Session c59ad762, 2026-10-05, laptop, HEAD b526915a. Within the Owner's K-local approval ("~1-2 probes").

## Deploy
- `hooks/learning-sentinel.js` (6063b55f) copied to `~/.claude/hooks/learning-sentinel.js`: live sha256[:12]
  7CFF5EF41BB7 -> 82A0622DD94B (= canonical). Pre-deploy copy in the session scratchpad `deploy-backup/`, and the
  previous version is 6063b55f^. Live `test-global-rule-inheritance.js` deployed the same way: all passed.
- `hooks/session_start_hub.js` (b526915a) is run by the dispatcher from this checkout
  (`../skills/claude-power-pack/hooks/session_start_hub.js`): live on commit.

## Check

    python tools/floor_regression_gate.py --check --probe --cwd C:\Users\User\Apps\listing-probe\champion
    PROBE ... session=6eba7a1f-7d66-49eb-b125-9e554800308d label=floor-gate-20261005T213736Z cost_usd=0.2432796
    FLOOR total_chars ref=188147 now=163070 delta=-25077
    LAYER other:deferred_tools_delta scope=unattributed ref=5116 now=8494 delta=+3378
    LAYER rules scope=universal ref=63625 now=35605 delta=-28020
    LAYER system_prompt scope=unattributed ref=6998 now=6575 delta=-423
    RISE other:deferred_tools_delta scope=unattributed delta=+3378 unit=chars rules=universal_1k
    TOKENS status=measured ref=87739 now=80241 delta=-7498
    FLOOR verdict=MATERIAL_RISE exit=1 reason=material_rise

## What this probe proves, and what it does not

- **Rule de-duplication: CONFIRMED at the model boundary.** The dispatcher emits every member that settled before
  its deadline (`hook-dispatcher.js` ~756, "whatever has settled is EMITTED"). learning-sentinel settled (it is not
  in the abandonment line below) and contributed nothing; the pre-fix version always emitted the rule stubs and the
  18-rule pointer (4,031 chars in fa7e93cb).
- **Hub scoping (OWNER_QUEUE / recovery / AutoResearch): INCONCLUSIVE.** The hub did not deliver at all:

      2026-10-05T21:37:48.854Z [SessionStart-chain] CHAIN-DEADLINE-ABANDONED after 4000ms Error: still running:
      ../skills/claude-power-pack/hooks/session_start_hub.js; host free=3382MB/32061MB (10.5%)

  and the dispatcher's `hook_success` row carries stdout `{"continue":true}` (durationMs 11,394). This is the same
  fail-open as the 2026-10-03 reference. The SessionStart layer's "no delta" is therefore NOT a saving, and is not
  claimed as one. The hub's headless scoping stays proven only by `tools/test_hub_owner_facing.js` (8/8) until a
  probe whose hub settles.
- **Tokens 83,115 -> 80,241 (-2,874)** against the previous probe: includes the confirmed rule de-dup AND the hub's
  absence, so it is not attributed to the K fixes as a whole.

## New defect exposed (fed to commit 9)

The startup floor's SessionStart component depends on host RAM: of the four laptop session starts examined
(2026-10-03 and 2026-10-05), three abandoned the hub at the 4,000 ms chain deadline (13:34:37Z 10-03 reference, 20:41:10Z, 21:37:48Z). A gate
that reads an abandoned window will report a failure as a saving and a recovery as a regression. K must recognise a
degraded window and refuse to certify from it.
