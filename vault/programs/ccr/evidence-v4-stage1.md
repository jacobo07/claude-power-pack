# CCR v4 Stage 1 evidence (2026-10-12)

Measured in session e10a9f08. The plan of record is `vault/plans/ccr-v4-boundary-cost-2026-10-12.md`.

## B5: Tool Output Projection (provider-measured)
- Host seam: on 2.1.296 a `tool.call` hook can `await next(e)` and return its own `{ result }`, which core maps
  with the tool's mapper. Projection is therefore a mod capability, not a HOST_LIMITATION.
- Canary: haiku, same prompt, an M4-shaped listing of 600 paths and 19,018 chars. modes.project is off in one arm and enforce in the other.
  | arm | floor (call 1 ctx) | carry into call 2 | answer |
  |---|---|---|---|
  | off | 68,140 | 12,136 | 5 (correct) |
  | enforce | 68,140 | 2,733 | 5 (correct) |
  The carried tool output fell 77 % at answer parity. Receipt: kind listing, 19,018 -> 2,948 chars, and the full output was written
  to the mod state dir. Calibration: 9,403 tok / 16,070 chars = 0.585 tok/char on a path listing.
- Gates: `claude plugin test` 23/23 and `claude plugin validate` passes. The elasticity test keeps the model-facing
  result <= 8,000 chars from 10 to 10,000 attempts while the raw result grows ~1000x.

## B1: M4 runs-tree listing (already fixed upstream, now measured)
`tools/ccr_carry_fit.py` and the per-result scan over the worker streams in `runs/madzia_p2r4_20261011`:
| attempt | call-2 listing | processed |
|---|---|---|
| a5 | `Get-ChildItem runs/madzia_p2r4_20261011 -Recurse`, 22,506 chars, rides 30 calls | 1,902,729 |
| a6 | predecessor folder only | 1,479,906 |
| a7 | predecessor folder only, 1,270 chars | 739,315 |
| a8 | predecessor folder only (call 1), 2,789 chars | 926,409 |
The driver ContextImage now names exact predecessor refs ("Best so far: p4p2a7 ..."). The recursive dump left
the path between a5 and a6 through the previous owner's driver change. B5 now catches the same class on any shell
listing, so a regression no longer reaches the model.

## B3: what the 0.73M "invisible" carry was
The fit runs over provider ctx deltas: 190 steps across a3-a8, abs residual 13.1 %, verdict PLAUSIBLE. Rates are tool_result 0.501,
assistant_text 0.59, tool_input 0.445 tok/char, thinking signature 0.305 tok/char, and ~594 tok per image.
| attempt | carry | tool_result | tool_input | thinking (sig) | images | residual |
|---|---|---|---|---|---|---|
| a3 | 2,936,541 | 33.4 % | 10.4 % | **40.8 %** | 13.2 % | 1.2 % |
| a4 | 1,602,240 | 53.2 % | 7.1 % | 30.0 % | 9.0 % | 0.4 % |
| a5 | 1,330,889 | 64.9 % | 6.9 % | 18.9 % | 11.4 % | -2.5 % |
| a6 | 910,281 | 28.7 % | 12.5 % | 33.3 % | 12.8 % | 11.3 % |
| a7 | 322,679 | 45.7 % | 15.0 % | 29.2 % | 12.3 % | -3.0 % |
| a8 | 448,309 | 52.0 % | 16.0 % | 21.8 % | 14.2 % | -5.0 % |
- Ablation: dropping the thinking kind makes the fit IMPLAUSIBLE (assistant_text and tool_input rates hit 1.0 and 0.83). Abs residual rises from 13.1 % to
  30.9 %, and a3's residual from 1.2 % to 26.4 %. The mass is real, and it rides in thinking blocks whose text the stream shows
  empty while their signatures carry the size.
- Classification: the residual is CARRIED THINKING within one `-p` turn (the worker's whole tool loop is one turn, so
  every thinking block rides every later call). For a3 it is 1.20M, so the earlier 0.73M estimate was low. Whether
  it bought novelty or reconstruction cannot be read from content (none is stored). That stays UNKNOWN, and the observable
  lever is epoch/turn structure, not introspection.
- Instrument limit, found by its own red-pole test: mass that rides every step alike cannot be identified by a
  no-intercept positive fit. It inflates a per-step kind's rate instead of the residual. The tool therefore reports a rate
  plausibility verdict, and a fit is only read as attribution when the verdict is PLAUSIBLE.

## B4/B6: contract, Work-Class model, intra-epoch governor
- `tools/ccr_pgo.py` builds the class model from real transcripts. Held-out (train a3-a6, test a7-a8): error with floor and length
  known is 15 % for the worker and 6.6 % for the reviewer (gate < 25 %). Class-only error before launch is 93 % for the worker,
  because training straddles the M4 fix (regime change, so retrain), and 32 % for the reviewer. All actuals fall within the class P80.
- Offline anomaly: the post-fix model (a6-a8) applied to a5 flags the call-2 step at 11,213 tok = 3.1x P95. Riding 30 calls
  that is 336,390 tok, which is the measured M4 0.30-0.34M.
- Live unit canary (haiku, `bounded-code-worker` unit, class model from a6-a8): the contract receipt has forecast P50 865K / P80
  1.12M and verdict ADMIT. With projection off, the call-2 step of 12,399 tok is flagged as an anomaly (3.42x P95, costIfRides 334,773). With the unit default (projection on),
  the step is 2,890 and there is no anomaly. Both answered 5.
- Enforcement status: the contract and anomaly are receipts plus a driver advice file (`advice/<sid>.anomaly.json`, verdict INCIDENT).
  Nothing refuses a model call yet. The pre-launch refusal point is the driver or `gsd_mission` launch admission (Stage 2 bridge).

## B2: provider elasticity of the M4 lookup (haiku, unit session, answer 5 in all 6 runs)
| estate | off: call-2 step | CCR default: call-2 step |
|---|---|---|
| 12 attempts, 1.9K chars | 2,096 | 2,485 |
| 120 attempts, 19K chars | 12,376 (anomaly) | 3,316 (projected) |
| 1,200 attempts, 190K chars | 2,362 (host persisted) | 2,386 (host persisted) |
The host already persists outputs above ~30K chars. The unguarded band was ~8K-30K chars, where M4's listing sat, and
B5 closes it. With CCR the step stays within 2.4K-3.3K across 100x estate growth.

## D1: Lobby re-reads (One-Read GO/NO-GO)
`tools/ccr_reread_audit.py` over all 575 KobiiCraft sessions: 53,286 unique calls (ids unique across files), 18.4B processed.
Read results carry 46 % of processed, but unchanged re-reads are 2.40 % (same session) and 2.21 % (later session), so NO_GO
(CE F rule 3 %). G1/H1 are NO_WORK. The historical "2,044 boundaries / 755M" does not describe this corpus (avg ctx 345K/call).

## U3: non-convergence (replay of the longest KobiiCraft Ralph missions, epoch = one `launched` event)
| mission | epochs run | commits per epoch | T5 breaker would halt at |
|---|---|---|---|
| m-1d270cd85220 (control, 137 commits) | 26 | `CC..CCCCCCC...............` | 14 (never during progress) |
| m-5d5949f39e9f | 48 | `CC....` then 46 empty | 5 |
| m-215a3e3ecd0a, m-700d11f14a20, m-dc815cfccbe3 (24 epochs), m-edc3f0192d3f, m-5cfc29313ebd, m-62c08be815a8 (48) | 24-48 | none at all | 3 |
These missions ran 2026-09-25/26, before T5 shipped the breaker (2026-09-27; their records carry no `progress` field).
The current `NO_PROGRESS_EPOCHS=3` halts the zero-progress lineages at ~6 % of their epochs and never during progress.
The docs-only-commit-resets-the-stall hypothesis is REJECTED: no epoch in these lineages was docs-only. U3 = ALREADY_DONE.

## Rent rank for the Madzia work class (a6-a8, after the M4 fix)
tool results 29-52 % > thinking 22-33 % > tool inputs 12-16 % > images 12-14 % of carry. Floor rent is 34-56 % of
processed. Next levers: B5 enforce in Work Unit sessions for tool text, then turn/epoch structure for thinking (E1), then
tool inputs (scripts written once and then re-sent as text).
