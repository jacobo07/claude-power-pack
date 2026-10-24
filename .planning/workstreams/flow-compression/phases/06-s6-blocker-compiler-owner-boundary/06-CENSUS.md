# Phase 6 census (blocker taxonomy evidence)

Ledger: `/home/kobii/.claude/state/gsd-autorun-ledger.jsonl`
Rows read: 6249 (census date 2026-10-24)

## Populations (rows per event)

| event | rows |
| --- | --- |
| mission_blocked | 55 |
| blocked_intent | 8 |
| owner_hold_set | 56 |
| recovery_owner_boundary | 5 |

## Class to evidence

| class | rows | rules that fired | example reasons |
| --- | --- | --- | --- |
| HOST_GATE | 9 | host_wait_gate x9 | host: waiting for input needed; host: waiting for permission prompt; host: waiting for permission prompt; host needs: approve Write: /home/kobii/missions/autonomous-optimization/.claude/wor |
| COMMAND_REQUEST | 9 | intent_ask x9 | host lists session blocked (no waitingFor); host needs: request too large — /compact or trim · Autocompact is thrashing:; host lists session blocked (no waitingFor); host needs: run /clear; host lists session blocked (no waitingFor); host needs: Complete the 6 checks in 04-UAT.md (operator /ql/ops look, wrapp |
| DECISION_REQUEST | 12 | intent_ask x12 | host lists session blocked (no waitingFor); host needs: Reply "approve all 8", name the subset, or say "keep all"; host lists session blocked (no waitingFor); host needs: 1) decide on push gate; 2) compute floor patch-id on laptop; 3) ; host lists session blocked (no waitingFor); host needs: choose (a) port E1–E3 admission + E4a contract to GEX44 live as  |
| RESOURCE_REQUEST | 1 | intent_ask x1 | host lists session blocked (no waitingFor); host needs: Supply target images (kitten reshape, Jacobo hair) or a new offl |
| PUBLISH_BOUNDARY | 5 | autonomy_outward x5 | host lists session blocked (no waitingFor); host needs: From the laptop: push feat/wsctx-m2 to GitHub, open the PR using; host lists session blocked (no waitingFor); host needs: Open PR with ql-lifecycle-w2-PR_BODY.md (confirm migration 0015 ; host lists session blocked (no waitingFor); host needs: On laptop: open PR from ql-lifecycle-w2-PR_BODY.md, then run /gs |
| CAPITAL_EXHAUSTED | 16 | amr_wait_capital_exhausted x3, authority_trip x3, capital_text x10 | host lists session blocked (no waitingFor); host needs: approve ~3M more budget to finish (judge P39 frames, write resul; host lists session blocked (no waitingFor); host needs: Owner: do you want to grant another budget allowance for the Pha; Owner reviewing tranche-3 scope (red team as falsification + leak/meter fixes) |
| COST_HOLD_RECOVERING | 13 | cost_hold x13 | cost breaker: 1,958,619 processed since the work tree last changed (stall budget 1,500,000); semantic progress is not ke; cost breaker: 4,082,017 processed since the work tree last changed (stall budget 4,000,000); semantic progress is not ke; cost breaker: processed 2,397,234 > 1.25 x estimate 1,600,000; explain the variance and recompute the remaining work bef |
| PROVIDER_LIMIT | 3 | provider_limit_text x3 | host lists session blocked (no waitingFor); host needs: rate limited — wait and retry · You've hit your weekly limit · r; GEX44 account weekly limit until 2026-10-21 19:00 Europe/Berlin (worker a3937ee7 got the limit message on turn 1); resum |
| WAIT_RESOURCE | 0 | (none observed) | - |
| GSD_HOLD | 1 | gsd_hold x1 | gsd NO_PHASES on 2 consecutive passes (300 s): GSD parses 0 phases from ROADMAP.md (headings must be GSD phases) -- no r |
| CAPSULE_NOT_CERTIFIED | 0 | (none observed) | - |
| CAPSULE_SEAL_REFUSED | 2 | capsule_seal_refused x2 | capsule-v2 seal impossible for mission-m-c474d0bfc3e6-e3: recovery REFUSED: obligations: no open item found in the goal ; capsule-v2 seal impossible for mission-m-ce29fdac4224-e2: recovery REFUSED: obligations: no open item found in the goal  |
| SETUP_HOLD | 16 | setup_text x16 | canary: envelope before first launch; canary2: envelope before first launch; WU-1R: envelope before launch |
| OWNER_PARK | 24 | owner_park x24 | E1 ALL_DECIDED at 9787a946 (merged into feature/knowledge-acquisition as 223612e9 on the laptop); work complete, no reru; Owner y 2026-10-06 ~20:30Z: Orca P4 compiled-execution canary (CPP spec vault/specs/orca-p4-compiled-execution-canary.md; Owner y 2026-10-07: compiled-execution canary (vault/specs/edd-compiled-execution-canary.md); stop unbounded GSD grammar |
| UNKNOWN | 5 | no_rule_matched x5 | host lists session blocked (no waitingFor); host needs: dispatch gsd-executor to run tools/test_kme_challenger.py + wiki; host lists session blocked (no waitingFor); host needs: open this session to continue setup; host lists session blocked (no waitingFor); host needs: arm a new TB-FULL mission epoch under the R-REFC packet, or tell |

Compiled rows: 116; UNKNOWN residual: 5.

## UNKNOWN residual (distinct reasons)

- x1: host lists session blocked (no waitingFor); host needs: dispatch gsd-executor to run tools/test_kme_challenger.py + wiki/tools/kme_pillars.py with WR-01/02/03 d
- x1: host lists session blocked (no waitingFor); host needs: open this session to continue setup
- x1: host lists session blocked (no waitingFor); host needs: arm a new TB-FULL mission epoch under the R-REFC packet, or tell me to build the growth step interactive
- x1: host lists session blocked (no waitingFor); host needs: say so if you want the in-play probe launched (uses a ledger slot and a Dolphin run)
- x1: host lists session blocked (no waitingFor); host needs: run `/gsd-autonomous --from 20` from the p17-growth worktree

A class with zero observed rows is allowed only when it is already a named hold kind in code (CAPSULE_NOT_CERTIFIED, CAPSULE_SEAL_REFUSED, GSD_HOLD, WAIT_RESOURCE).

