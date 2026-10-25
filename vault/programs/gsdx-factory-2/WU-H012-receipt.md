Status: DONE_WITH_LIMITS -- H0, H1, H2 built, tested and mutation-killed on branch `h012-econ`; coverage table has UNKNOWN rows (no runtime subagent probe); not yet landed on feature/knowledge-acquisition (next step below).

## Where it lives
Worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\h012-econ`, branch `h012-econ` (from 7bed6a6f). Land with a pathspec cherry-pick onto feature/knowledge-acquisition; the shared checkout was not edited. Nothing was pushed; no settings.json edit; no capital request.

## Commits
- 56a401bd feat(session_budget_guard): pre-boundary ceiling denies when processed+next+closeout would cross stop (H0)
- H1+H2 commit: see `git log h012-econ` (subject `feat(econ): exact_push ... + unit_econ ...`).

## H0 -- pre-boundary ceiling
- `judge()` denies when processed + next + closeout_calls x next > stop (next = max(last call, mean of last 3)); `CPP_PREBOUNDARY=off` restores the old comparison; a receipt write is still admitted after a pre-boundary deny, other writes are not.
- RED before the fix (earlier worker): replay admitted 3,106,574 > stop 3,000,000, 5 of 9 gates red. GREEN: `PREB_PASS=9/9` (replay admits 2,301,533, denies at gated call 18; control with the switch off admits 3,106,574).
- Mutation drill (`python tools/mutation_drill.py --spec <json>`; the earlier note that the spec is positional was wrong): `st.tokens + next + reserve > budget.stop` -> `false`: **MUTANT KILLED gate=V-PREB-REPLAY-CEILING**, `PREB_PASS=4/9`.
- Existing suites: `ADMIT_PASS=12/12` (session_budget_admission); `GOAL_PASS=59/59` (goal_budget_admission, earlier run); `SBG_PASS=21/22` -- only `V-SBG-LATENCY` (>50 ms) fails, and it fails identically on the unmodified main checkout (host load).
- UNKNOWN: the packet quotes 4.31M for transcript 4f881648; it measures 7,955,580 processed over 50 unique ids. The replay still binds stop at 3M; the 4.31M figure is not reproduced.

## H1 -- exact-subject push (`tools/exact_push.py`, `tools/test_exact_push.py`)
- `XPUSH_PASS=10/10` against temp local bare repos: tip B with A's receipt refused and remote untouched; `push --sha A` leaves remote == A with B unpublished; rescan B then push B -> remote == B; re-sealed receipts with a different remote URL / ref / policy hash refused; a credential in a MID-range commit -> BLOCK, push refused, value not echoed; control: a non-credential MEDIUM pattern is admitted; policy object is named `secrets-only` and its hash moves with it.
- Mutation: `if want != r["sha"]:` -> `if False:` : **MUTANT KILLED gate=V-XPUSH-TIP-MOVED** (`XPUSH_PASS=8/10`; the mutant published B's receipt-mate unguarded).
- Design: patterns come from `modules/secret_firewall/detector.py` (no regex fork); blocked on CRITICAL only (anthropic/openai/github_pat/aws/private_key/connection_string) plus path names (.env*, *.pem, *.key, id_rsa*, id_ed25519*); lower severities are advisory. Owner allowlist (`allowlist.py`) is deliberately NOT applied: the scan is stricter than the live firewall. Push re-verifies seal, policy hash, subject, remote URL, remote tip == base, and re-scans the range before `git push R S:refs/heads/REF` (no force), then reads the remote back.
- Not wired: `ovo-push-gate.js` is untouched (not weakened). Adopting exact_push as the push path is a separate step (the gate still keys on its TTL).

## H2 -- unit telemetry (`tools/unit_econ.py`, `tools/test_unit_econ.py`)
- `UECON_PASS=8/8`. Counting reuses `mission_spend.session_tokens` as the cross-check (sum of per-call list must equal it; exit 1 otherwise). Mutation: `if mid in seen:` -> `if False:` : **MUTANT KILLED gate=V-UECON-DEDUPE** (`UECON_PASS=3/8`).
- Output on THIS unit's own transcript (residual run only, taken before the final commit; the earlier worker's 5.7M is in a different session):
  calls 26, processed 3,359,935, first-call CWS 71,988 (cache_read 31,868), avg/p50/p80/peak per call 129,228 / 123,161 / 141,730 / 152,839, forecast 4,600,000, amplification 0.73, value deposit none supplied, measurement tax 0.054 s, count agrees with mission_spend: true.

## Coverage table (does a path reach the pre-boundary guard?)
| Path | Class | Basis |
|---|---|---|
| Parent session tool call, envelope declared | RUNTIME_GUARDED | `session_budget_guard.js` PreToolUse; V-PREB replay |
| Worker launched by `arm-chain` / respawn with a session id and admitted wu_packet | RUNTIME_GUARDED | `gsd_mission._declare_worker_envelope` -> `mission_spend.declare` writes `session-budget-<sid>.json` (called at gsd_mission.py:1025, 1421, 3880); read from code, no live arm run |
| Same, but sid unknown at launch, no wu_packet, or verdict not launchable | UNAVAILABLE (silent no-op) | early `return` at gsd_mission.py:3475; undeclared session is unguarded (guard line "no envelope, no guard") |
| Subagent (Agent tool) calls, SESSION envelope | UNKNOWN (code suggests not counted) | session-mode `advance()` reads only `event.transcript_path`; the `<sid>/subagents/*.jsonl` sweep exists only in goal mode (guard line ~352). No runtime probe run |
| Subagent calls, GOAL mode | RUNTIME_GUARDED | measured over parent + `subagents/*.jsonl`, fails closed |
| Budget wording in prompts, model routing | MODEL_POLICY_ONLY | not machine-checked |
| Post-hoc spend accounting (`unit_econ`, `mission_spend`) | OBSERVED | measures after the fact |

## UNKNOWNs / bugs
- Subagent coverage under a session envelope: UNKNOWN at runtime; a cheap real probe (spawn one subagent in an enveloped session and read the state file) was not run.
- 4.31M vs 7.96M transcript mismatch (above).
- V-SBG-LATENCY fails on host load, pre-existing.
- Bug: none in product code. Doc note: the receipt of the first worker said the drill takes the spec positionally; `--spec` is required.

## Next
Cherry-pick the H0 and H1+H2 commits onto feature/knowledge-acquisition (pathspec), re-run the three suites there, then decide wiring of `exact_push.py` as the push path. H3 not started.
