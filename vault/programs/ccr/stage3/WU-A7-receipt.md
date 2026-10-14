# A7 receipt
Status: DONE_WITH_LIMITS

Unit: WU-A7, main interactive authority and canary (goal ccr). Linux plane GEX44, host 2.1.296, branch mission/ccr-s3, base 7d2af6e6.

**Limit: processed-token budget.**
- Budget 3,000,000. Measured 3,199,878 over 43 calls when this receipt was written; final about 3.65M (see K7).
- Over budget, under the 4,500,000 breaker.
- The work is complete; the overrun is the only limit.

## Done-check
`vault/programs/ccr/evidence-v4-stage3-A7.md` contains:
- the shadow table (section 1);
- the main-lean policy with its gate, rollback and validation (section 2);
- the canary command, the prediction, the read-out command and the state CANARY_PENDING (section 3).

## Results
**Shadow:**
- 52 interactive main sessions, 50 with a projection.
- Unit closure would drop 1,765,034 skill-listing bytes, 2,540,644 agent-listing bytes and 261,255 MCP-instruction bytes.
- 19/50 sessions later used a Skill (14 calls) or an Agent (43 calls). MCP tool uses: 0.
- So dropping is rejected for main sessions.

**Policy:**
- Main-lean = name-only skill and agent listings plus MCP server headings, with the page fault (new kind `mcp`) bringing descriptions back.
- Opt-in `CCR_MAIN_CANARY=1`, interactive sessions only, no unit.
- On real 2.1.296 text: 314/314 skill names and 70/70 agent types kept; 29,998 -> 7,778 and 26,065 -> 1,521 chars.
- Estimated 3.8% of main-loop processed tokens over the laptop sessions, with the chars/4 assumption.

**Tests:**
- plugin test 38/38;
- validate passed;
- test_ccr_main_shadow 11/11;
- test_ccr_release 20/20;
- estate gate PASS.

**Canary:** CANARY_PENDING. Prediction: about 12.7k tokens off the first call, about 11% of the laptop baseline median of 112,591.

**Observed, not acted on:**
- The SDD-OS prompt hook reported the plan `vault/plans/ccr-v4-stage3-2026-10-13.md` as `NOT_READY` (status:proposed, no V-gate). I proceeded on the packet's Owner approval ("approve stage 3 + main canary"). The plan's readiness keys are for the coordinator.
- The scratch dir `/tmp/a7val` holds the real-listing check (listing text of this host's estate, no secrets). It is left in place.

## Files
- mods/cpp-cognitive-runtime/hooks/policy.ts, register.ts, policy.test.ts
- tools/ccr_main_shadow.py, tools/test_ccr_main_shadow.py
- vault/programs/ccr/evidence-v4-stage3-A7.md, this receipt

## K7: estimate vs actual processed tokens, every session of this unit
| session | estimate | actual processed |
|---|---:|---:|
| A7 worker 05d0d13f (Opus, GEX44) | 3,000,000 (packet budget) | 3,199,878 over 43 calls at receipt-writing time. The commit and verify calls add about 4 x 115k, so expected final is about 3.66M |
| canary / probe sessions | 0 | 0. No model-calling probe was run; the canary is the Owner's pane |
| **total** | 3,000,000 | ~3.66M (over budget by ~0.66M, under the 4.5M breaker) |

## LAPTOP_APPLY
Prerequisite: bring the A7 commit on GEX44 `mission/ccr-s3` to laptop `ccr/v4` (worktree `.claude\worktrees\ccr`) the same way A2-A6 were brought over. Then, in PowerShell:

    Set-Location C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr
    claude plugin test mods/cpp-cognitive-runtime        # expect 38 pass, 0 fail
    claude plugin validate mods/cpp-cognitive-runtime    # expect "Validation passed"; env reads CCR_MAIN_CANARY, CCR_PIXEL_GC, CCR_WORK_UNIT
    python tools/test_ccr_main_shadow.py                  # expect CCR_PASS=11/11
    python tools/test_ccr_release.py                      # expect CCR_PASS=20/20
    python tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime   # expect PASS
    # Guarded release (A1 rule): only if no Madzia driver (python.exe with kobiimii in its CommandLine) is running
    $madzia = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*kobiimii*' }
    if ($madzia) { "SKIP release: Madzia driver running, pid(s) $($madzia.ProcessId -join ',')" } else { python tools/ccr_release.py release }
    python tools/ccr_release.py status --sessions

Record the output of the last two commands. If the release was skipped, record the skip line and the pids, and do not open the canary pane: an old release ignores the variable.

**Owner's canary pane** (a new PowerShell pane, after the release):

    $env:CCR_MAIN_CANARY='1'; claude

The status line should read `... canary:enforce`. Work in it normally.

**Read the result afterwards** (from the worktree):

    python tools/ccr_main_shadow.py --canary $env:USERPROFILE\.claude\ccr\state\receipts

Record:
- `state` (expect CANARY_RAN);
- for each canary session: `releaseId`, `withheld`, `predicted_first_call_tok` vs `measured_first_call_tok`, `faults`, `spawns`, `errors`;
- the Owner's note on any skill or agent the session failed to find.

**Rollback**, any one of:
- close the pane, or `Remove-Item Env:CCR_MAIN_CANARY` and restart `claude`;
- `python tools/ccr_release.py rollback`;
- `python tools/ccr_release.py off`.

## Text for RESUMPTION_FILE (coordinator)
A7 DONE_WITH_LIMITS on GEX44 (limit: budget 3.0M, actual ~3.66M processed), committed on mission/ccr-s3.
- Shadow over 52 interactive laptop sessions: unit closure's listing drop would have hit a later-used Skill or Agent in 19/50 sessions. Rejected for main.
- Main-lean canary instead: name-only skill and agent listings plus MCP headings, page fault kind `mcp`. Opt-in `CCR_MAIN_CANARY=1`, interactive only. 38/38 plugin tests, 11/11 shadow tests.
- Canary state: CANARY_PENDING.
- Next: LAPTOP_APPLY merge + guarded release, then the Owner opens a pane with `$env:CCR_MAIN_CANARY='1'; claude` and the coordinator reads `python tools/ccr_main_shadow.py --canary $env:USERPROFILE\.claude\ccr\state\receipts`.
- Next candidate after the read: instructions -> kernel + index on main (>= 7.27M bytes in the shadow).
