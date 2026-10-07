---
covers: [cr4-closure, tranche-gate-truth, hard-rules-authority, coordinator-enforcement, ukdl-staging, savings-probe]
status: PROPOSED (awaiting one Owner approval)
source: fresh read-only planner session 0e59c062-1009-4b97-8d63-6e74a0708bcb, 21 tool calls, 1,220,273 processed
---

# Planner packet: context-runtime-4 closure and failure-class fixes

The scan was read-only and used 21 tool calls; nothing was modified. The most important finding is that **context-runtime-4 cannot be closed green by fixing the violations clause**. The spend clause fails on its own, and the coordinator's reading keeps growing every time the gate is re-run.

## 1. Reality scan

| Claim | Status | Evidence |
|---|---|---|
| The listed commits exist (ea728742, 1059ff1e, 7f42e43e, 4625c0e7, 2ea65ca2, 3893ac84, 5386f35e, 13f2f708, 968ed5a0) | CURRENT | `git log -1` resolved every hash; HEAD is 02d2f3c0 |
| Tranche FAIL is caused by violations being UNDECIDED | **WRONG (partial)** | The gate printed `violations UNDECIDED` **and** `spend FAIL total=5,297,362 cap=3,500,000`, then `CEP2_TRANCHE=FAIL clauses=3 green=1` |
| Coordinator spent ~18.4M (tranche 3) | CURRENT as history | NEXT-SESSION.md:19 |
| Coordinator overspent in tranche 4 | CURRENT, derived | R1 592,688 + R2 1,442,476 = 2,035,164, so the coordinator accounts for **3,262,198** against a 0.7M allowance (tranche.json:3) |
| R2 cut ~605 tokens per call | ESTIMATED (chars/4) | R2-receipt.md:43; the receipt says "live probe: PENDING" |
| 22 rules exist on only one side | CURRENT as a claim, not enumerated | R2-receipt.md:12-14 names HR-SECRET/CASCADE/OUTPUT (mirror only) and HR-REVIVAL/PANE-MAP (archive only). I did not enumerate all 22 |
| Global `~/.claude/CLAUDE.md` is ~39.8k chars | **STALE** | Now **40,117**, over the 40.0k warning (NEXT-SESSION.md:10 recorded 39,809) |
| Project CLAUDE.md is ~33.4k chars | **STALE** | Now 33,774, which is +387 since R2 reported 33,387 |
| "Coordinator stays under 6 calls" is enforced | **WRONG** (it is narrative only) | The guard is opt-in: `session_budget_guard.js:169` returns null when no envelope exists. No `session-budget-e6e0eca7…json` exists. `tranche_driver.py:92` declares workers only |
| The UKDL file carries another writer's uncommitted hunks | **WRONG framing** | All 905 added lines are machine-generated CEPS entries (`- [tooling/powershell:s] ceps_…`), written by `ceps.py:500 _atomic_append(UKDL_PATH…)`. They are not a concurrent human session |

**Hidden defects:**
- **D1 – coordinator metering never stops.** `cep_gen2.py:338` computes `now − baseline` against a session that is still alive. Every re-run of the gate raises the total, so the verdict cannot be reproduced. Even running this gate counts.
- **D2 – two different caps.** results.json has cap 2,800,000; the manifest has 3,500,000. The manifest wins (`cep_gen2.py:326`), so this is benign but confusing.
- **D3 – receipt hash is not the branch hash (PLAUSIBLE).** The R2 receipt names `cd859053`, while the branch carries `7f42e43e`. This looks like a cherry-pick rewriting the hash. 1059ff1e shows the same pattern.
- **D4 – stray test files.** Seven untracked `vault/hard_rules/auto_*.md` files plus test side effects into the UKDL file. This is the non-hermetic `test_hard_rules.py` already listed as debt in R2-receipt.md:54.
- **D5 – no call counts in results.** Driver results store spend and seconds, but no physical call count and no semantic boundaries (`tranche_driver.py:111`).
- **D6 – no goal resolver.** There is no current-goal resolver: `goal/log.py:100` exposes only `goals_root()`, and logs are keyed by `(repo, goal_id)` at line 141. NEXT-SESSION.md:28 says "ask the Owner for the goal id."
- **D7 – unclear HARD RULES authority.** `writer.py:4` calls the archive "canonical," but rule ids are allocated from the CLAUDE.md block (`get_current_rules(claude_md)`, lines 108/122). In practice the mirror is the id authority, which contradicts the docstring.

## 2. Owners

| Workstream | Existing owner | What happens |
|---|---|---|
| A | `tools/cep_gen2.py::tranche` (310-376) | **Decision:** the tranche left out a required declaration, and the gate also has a gap. A missing `owned_units` key must stay UNDECIDED. Add NOT_APPLICABLE only for an *explicit* `owned_units: []` with a written reason in the manifest. Freeze the coordinator reading (D1) |
| B | `modules/hard_rules/writer.py` + `tools/test_hard_rules_mirror.py` | EXTEND |
| C | `writer.py::stub_reason` (272) | EXTEND the classifier from "stub" to five labels: obsolete/stub/mechanical/duplicate/judgmental |
| D | `wiki/tools/listing_floor_probe.py` | Use as-is (see the epoch 5 note) |
| E/F/G | `tools/mission_spend.py session-declare` + `hooks/session_budget_guard.js` + `tools/tranche_driver.py` | EXTEND: declare the coordinator too |
| H/I | Guard closeout path (140-160 already allows writing `RESUMPTION_FILE`/handoffs and points to `/kclear`) + `/kclear` | EXTEND the trip message. `closer-guard.js` is untouched. Ralph and the context watchdog were not verified in this scan |
| J | `modules/gsd_x/goal/log.py` | EXTEND with a resolver. Deferred until the floor gate is green |
| K | `tools/ceps.py` draft set (852-928, already has a terminal "resolved" transition) | CONNECT `distribute()` to drafts instead of the tracked UKDL file |
| L/M | No measurement owner. The Owner previously REJECTED the global CLAUDE.md item (NEXT-SESSION.md:10) | Report only |
| P/Q/R/S | UKDL + CEPS drafts + `tools/router_freshness_gate.py` | CONNECT only |

**NEW: none.** HR-NOVELTY-001 is not triggered.

## 3. Plan

The coordinator only launches, cherry-picks and gates. Every epoch below is a worker packet run with `tranche_driver.py --root <worktree>`. Token estimates are based on R1 (0.59M) and R2 (1.44M) measured.

**E0 – Close tranche 4 truthfully** (EXECUTION, deterministic, 0 workers)
- Commit a receipt stating that tranche 4 is FAIL on spend, with coordinator spend frozen at the reading taken at commit time. Do not re-baseline anything.
- 1 boundary, 2 calls, ~0.1M.

**E1 – Gate truth (A + D1)** (EXECUTION)
- Add `NOT_APPLICABLE` to `TRANCHE_STATES`. It is allowed only for an explicit empty declaration with a reason; a missing key stays UNDECIDED.
- Add a manifest field `coordinator.final` that freezes the reading.
- The spend clause becomes FAIL if the manifest's coordinator has no declaration file.
- Extend the existing `--tranche` test (currently 14/14). Mutations:
  - Treat a missing key as NOT_APPLICABLE: the test must go red.
  - Drop the freeze and grow the transcript: the test must go red.
- Rollback: revert one commit.
- 1 packet, ~25 calls, ~1.0M.

**E2 – Coordinator enforcement and receipts (E/F/G + D5)** (EXECUTION)
- The driver runs `session-declare` for the coordinator sid from the manifest before the first packet: `--calls-estimate 6`, allowance taken from the manifest.
- The driver writes `calls` (via `mission_spend.session_tokens`, which already counts tool_use blocks) and `boundaries` (packet ids) into results.
- Test: a V-DRIVER case shows an undeclared coordinator being refused.
- Mutations:
  - Skip the declare step: the test must go red.
  - Drop `calls` from results: the test must go red.
- 1 packet, ~30 calls, ~1.2M.

**E3 – HARD RULES single authority (B + D7 + R2 debt)** (PLAN, then EXECUTION)
- Merge the union of both sides into the archive, losing nothing, and record per-rule provenance (archive-only / mirror-only / both).
- The mirror becomes a generated projection, and id allocation moves to the archive.
- `append_hard_rule` refuses entries where `stub_reason` is non-null.
- Drift check added to `test_hard_rules_mirror.py`. Mutation: delete one rule from the mirror only, and the test must go red.
- Make `test_hard_rules.py` hermetic using a temporary root (D4).
- 1 packet, ~35 calls, ~1.5M.

**E4 – UKDL staging (K)** (EXECUTION)
- CEPS `distribute()` goes to drafts. The existing 905 lines go through draft review and are never discarded automatically.
- Test: `distribute` leaves the tracked UKDL bytes unchanged. Mutation: restore the direct append, and the test must go red.
- ~0.8M.

**E5 – Live savings probe (D)** (EXECUTION, model work)
- `--pair` cannot isolate a CLAUDE.md change, because CLAUDE.md loads in both the ON and OFF runs.
- Cheapest valid A/B: two ON probes with the same prompt, one with the cwd at 7f42e43e^ and one at 7f42e43e. Each probe costs about 105K first-call tokens (S1-receipt.md:22).
- Cost: ~0.25M.
- Until this runs, the 605-token figure stays labeled ESTIMATED.

**E6 – Hot-prefix classification and rent ranking (C, L/M)** (deterministic report)
- Use the five-label classifier from E3 across the HARD RULES and both CLAUDE.md files. Rent = estimated tokens × calls; the call counts come from transcripts.
- Mechanical retirement candidate: mirror-block entries already enforced by registered hooks (HR-SECRET-001 by the `secret_firewall` hook). This counts as a saving only if the rule stays enforced mechanically, so moving text elsewhere does not count.
- ~0.6M. The output is a decision list for the Owner.

**E7 – Budget-edge handoff and goal resolver (H/I, J)** (EXECUTION)
- Change the trip message so the pane writes `RESUMPTION_FILE` and ends on a `/kresume` instruction instead of asking the Owner.
- Add `current_goal(repo)` to `goal/log.py`: exactly one non-terminal goal returns its id; zero or several returns UNDECIDED.
- J stays deferred until the floor gate is green.
- ~0.8M.

**P/Q/R/S** are folded into E4 (lessons go through CEPS drafts and are promoted by `router_freshness_gate`). There is no new CI.

## 4. Master done-gate

| Command | Expected | Evidence level |
|---|---|---|
| `python tools/cep_gen2.py --tranche context-runtime-4` | `FAIL` with the spend total frozen; two runs one hour apart print the same total | MEASURED |
| `python tools/cep_gen2.py --tranche context-runtime-5` | `PASS`, with every clause PASS or a declared NOT_APPLICABLE | MEASURED |
| `--tranche` test suite | All pass; the 2 mutations go red | MEASURED, both poles |
| `python tools/test_tranche_driver.py` (V-DRIVER) | All pass, including the undeclared-coordinator refusal | MEASURED |
| `python tools/test_hard_rules_mirror.py`, `test_hard_rules.py`, `verify_hard_rules.py` | Exit 0; drift mutation red; `git status` clean after the run | MEASURED |
| `test_session_budget_guard.py` | Parity holds | MEASURED |
| CEPS draft test | Tracked UKDL bytes unchanged | MEASURED |
| E5 probe rows | Both rows present, delta reported, or the result is labeled ESTIMATED | MEASURED or ESTIMATED |
| `python modules/liveness/reachability.py` | Exit 0 | MEASURED |
| `node ~/.claude/hooks/tests/run-all.js` | `closer-guard` unchanged and green | MEASURED |

## 5. Total envelope and Owner authority

**Envelope:** about 6.2M for workers (E1–E7) plus a coordinator cap of 0.5M, declared through E2 before any packet runs. Total ≈ **6.7M**, against tranche 4's actual 5.3M.

**Owner authority needed:**
1. Accept tranche 4 closing as **FAIL** (not re-baselined).
2. The 6.7M cap for tranche 5.
3. ~0.25M of model spend for the E5 probe.
4. Any edit to `~/.claude/CLAUDE.md` coming out of E6. It is now over 40k, but it was previously rejected, and HR-001 applies to writes under `~/.claude`.
5. What to do with the 905 pending CEPS lines in the UKDL file: promote through drafts, or discard them yourself.

Separately, the context7 server needs authorizing via `/mcp` (other MCP servers failed to connect). This plan does not use either.

Short approval form: **"go 1-4, 5=drafts"**.
