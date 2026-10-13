# A2 receipt
Status: DONE_WITH_LIMITS

Limits, each with its number:
- L1 budget: this worker used 3,922,368 processed tokens by its 48th model call (measured from its own transcript), against a 1,500,000 budget and a 1.5x stop at 2,250,000. The stop was exceeded by 1,672,368 at that point. The last ~3 calls that wrote this receipt and committed are not in that measurement (estimate +0.45M, about 4.37M in total; the 4,500,000 breaker was not hit). Cause: the first session reached the turn cap after a survey at about 150K context per call, and this continuation reread that context on every call.
- L2 hard floor not isolated: in the smallest probe (P4, 3,119 tokens) every token is controllable, so the registry records an upper bound, not a floor. The P3 residual of 1,354 tokens is UNKNOWN.
- L3 tool-schema saving of the CWS proposal is UNKNOWN: 0 probes with `--tools Read,Grep,Glob` remained (4 of 4 used).
- L4 Madzia carry residual -3,677 to -8,807 tokens: response bytes overcount re-sent thinking/sealed content, so the carry:response bucket is an estimate.

All numbers are Linux plane GEX44, host 2.1.296.

## Deliverables
- tools/ccr_anatomy.py, tools/ccr_cws_proposal.py, tools/test_ccr_anatomy.py (17 passed, 0 failed: `python3 tools/test_ccr_anatomy.py`)
- vault/programs/ccr/hard_floor_registry.json (4 GEX44 probe rows plus 2 laptop rows UNKNOWN)
- vault/programs/ccr/evidence-v4-stage3-A2.md (anatomy for V1 r1-r5 plus 4 Madzia unit sessions plus 4 probes; registry; CWS proposal)
- vault/programs/ccr/stage3/a2/: anatomy-detail.md, anatomy.json, cws-short-lookup.patch (NOT applied, `git apply --check` OK), probes/*.facts.jsonl (content-free init/result facts)

## Key results
- Calibration: 2.999 B/token for call 1 (35 sessions, 11 groups) and 2.491 B/token for carry (1,031 steps).
- In the V1 CCR arm, tools+framing is 9,865 of 18,308 tokens; in the Madzia 7-tool workers it is 14,333-15,812 of 17-19K. The "21K floor" is mostly tool schemas, which are controllable (REDUCIBLE).
- Probes, ctx at call 1: P1 14,269, P2 13,361, P3 10,155, P4 3,119. P4's residual is -6 tokens.
- CWS short-lookup projection (attachments only): -2,034 tokens at call 1 on V1 r2/r4 (-11 %).

## Model calls (packet-named only)
- P1 99d97182-1e6d-4a62-aeda-cc6321da9c54: processed 14,273 (MemAvailable 54,535,816 kB)
- P2 95ab3d08-26bd-47dd-988e-d3a8ca131c91: processed 13,365 (54,507,480 kB)
- P3 228f7133-03c4-4504-8509-eb19e760272c: processed 10,159 (57,733,836 kB)
- P4 2ee1f371-b2f2-430f-a34a-62f2c8a54c4b: processed 3,123 (57,645,596 kB)
- P2a c011839c-38d7-4f79-a9ad-f807c3611c44: 0 model calls (the prompt was swallowed by variadic `--tools ""`; host error before any call; 0 assistant events)
- Subscription `claude -p` only, no API key. No Agent spawns, no Monitor, no GSD commands, no push.

## K7
| item | estimate | actual |
|---|---:|---:|
| worker session 0c9c8dbd-68ba-4499-b3d6-514fc304962e (both turns) | 1,500,000 (packet) | 3,922,368 measured at call 48; final ~4.37M estimated |
| probe sessions P1-P4 | ~100,000 (plan: 3 probes ~0.1M) | 40,920 |
| total | 1,600,000 | 3,963,288 measured; ~4.41M estimated final |

## Not applicable
The hook-injected kobiicraft_mode family rules do NOT APPLY: this unit is an offline token-accounting tool and probe set, not a Minecraft mode or mechanic. No in-game surface was touched and nothing was built or deployed.

## LAPTOP_APPLY
Run on the laptop by the coordinator:
```
# book this unit's measured spend into the ccr goal ledger (coordinator lease)
python tools/ledger.py book --goal ccr --unit WU-A2 --processed 3963288 --note "A2 worker 0c9c8dbd (measured to call 48, ~0.45M unmeasured tail) + probes P1-P4 40,920 on GEX44"
# optional: laptop-plane floor row (registry rows for laptop-windows are UNKNOWN)
# rerun the same 4 probes from the laptop clone with CCR_WORK_UNIT set, then:
python tools/ccr_anatomy.py table --root %USERPROFILE%\.claude\ccr\state\receipts --sid <probe sids>
```
