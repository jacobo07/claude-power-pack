# APR production reality -- canary judged (WU-APR6, 2026-10-11)
Sources: `~/.claude/state/gsdx-chain.jsonl` rows 899-961 (goal apr), `gsd-mission-<id>.json`, `gsd-autorun-ledger.jsonl`,
`apr-canary/*.seal.json|gate.json`, `git log` in wt_apr, `python tools/gsdx_chain.py status --chain vault/programs/apr-canary/chain.json`
(run under PowerShell; under Git Bash it dies "Could not determine home directory", HOME unset -> see KNOWLEDGE A9).

## Verdict per EXPECTED row
| # | Expected | Observed (quoted) | Verdict |
|---|---|---|---|
| 1 | C1 armed; receipt without Status | row 899 16:55:31 `arm C1 ... mission_id m-e9f113b4634f trigger watchdog`; WU-C1-receipt.md = "# C1 receipt / PROVEN: canary/c1.txt = ok" (no Status); commit e0b767ae 17:03:39 | PASS |
| 2 | C1 sealed by finalizer, NO renewal, C2 armed trigger event | WU-C1-receipt.md.seal.json `"sealed_by": "gsdx_chain.finalize", "receipt_status": "UNREADABLE", "verdict": "DONE"`; mission m-e9f113b4634f HALTED "receipt not closed (status UNREADAB..." with no successor; row 914 17:06:58 `arm C2 ... m-a38d4cdacdaf trigger event` | PASS |
| 3 | C2 attempt 1: Status DONE only -> FALSE_DONE refusal + residual | row 927 17:18:08 `class FALSE_DONE, residual 1, finalized refused "missing files: ['canary/c2.txt']", packet WU-C2.md.residual.md` | PASS (row). Refusal file cited by row (`WU-C2-receipt.md.refusal.json`) is NOT on disk now -> F2 |
| 4 | ONE residual arm of C2, creates c2.txt, sealed DONE | residual mission m-2e61e0a0aa10 armed 927 (only one chain arm of C2: rows 914, 927). Commit b05c01f4 17:29:56; WU-C2-receipt.md Status: DONE, gate.json passed:true. No `*.seal.json` for C2 -> F1. A second mission on the same residual packet, m-7a5265092233, exists (halt-continue renewal of m-2e61, ledger `mission_renewed successor m-7a5265092233 renewal 1`, NOT a chain arm) -> F3 | PARTIAL (advance correct; artifacts/mission layer deviate, see F1-F3) |
| 5 | C3 armed trigger event; DONE; chain complete | row 959 17:43:25 `arm C3 ... m-715cdc4ca1b5 trigger event`; mission COMPLETED; commit da2fd7eb 17:48:48; status: `"decision": "complete"`, units C1/C2/C3 done:true | PASS (no seal.json for C3, F1) |

## Forbidden list
- Duplicate arm of same unit+attempt: PASS. Chain arm rows: C1 x1, C2 x2 (attempt 1 row 914, residual row 927), C3 x1.
- human_gate: PASS (`grep -c human_gate gsdx-chain.jsonl` = 0; status `"human_gate": null`).
- C1 renewal: PASS (no successor of m-e9f113b4634f; mission file has no renewed_as).
- 2nd residual: PASS at chain level (residuals max 1). Mission-layer renewal m-7a52 exists (F3).
- Coordinator sent nothing: PASS on evidence available. Every chain arm row has trigger `watchdog` (C1) or `event` (C2, C2r, C3); all 4 chain
  missions have `mode: ralph`; no arm rows with another trigger. Absence of a pane message is not provable from these files alone (UNPROVEN: pane transcript not audited).
- Wall time: first arm 16:55:31 -> last commit 17:48:48 -> `complete` row 17:53:28 = 58 min (< 90 target, < 3 h bound). Sources: rows 899, 961 / git log.
- Progression not dependent on watchdog: C2 and C3 arms were `trigger: event` (rows 914, 927, 959). C1 arm was watchdog because C1 was the first unit.

## Residual noise
`residual_exhausted APR5` rows every ~10 min (895..961) from the apr programme chain (APR5 unit sealed BLOCKED_HUMAN originally, closed by coordinator) -- alert-once logic held? Not checked: finding F4.

## Findings (mismatch = finding)
- F1 only C1 has `.seal.json`; C2/C3 have only `.gate.json` (passed:true). Cause not verified (hypothesis: seal is written only by the finalizer path for Status-less/refused receipts, not when the worker closed DONE and the gate passes). Unproven; consequence: "sealed DONE" in EXPECTED rows 4/5 is evidenced by gate.json + receipt Status, not a seal file.
- F2 refusal.json cited by row 927 absent from disk afterwards (hypothesis: removed on successful seal/gate). Unverified.
- F3 the residual worker of C2 ran twice at mission layer: m-2e61e0a0aa10 (HALTED "no receipt", 157,195 tokens) then renewal m-7a5265092233 (HALTED "no receipt", 77,704 tokens), while WU-C2-receipt.md (Status: DONE, 17:30:05) existed and the chain advanced. The mission layer said "no receipt" about a file the chain accepted: a second reading of the same fact (UKDL one-parser). Cost ~77k tokens extra. NOT fixed here (needs a mission-layer test; see REPORT next task).
- F4 apr programme chain re-emits `residual_exhausted APR5` ten-minutely; silence-alert dedupe not verified.
