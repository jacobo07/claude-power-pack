---
id: PLAN-K-RESIDENT-PREFIX
date: 2026-10-05
status: APPROVED 2026-10-05 (Owner: "K-local now, rest after reset (Recommended)"; connectors "Budget as account floor (Recommended)")
covers: [ic-pillar-k, resident-prefix, startup-floor, sessionstart-attribution, deferred-tools-budget]
parents: [vault/plans/incremental-cognition-rearm-2026-10-05.md]
defers_to: vault/plans/cognitive-microkernel-brief-2026-10-04.md (steps 11-18, after the weekly quota reset)
done_gate: python tools/test_floor_regression_gate.py exit 0 AND one real K probe passing the strengthened gate for the right reason, reference 2026-10-03 preserved
---

# Pillar K -- resident prefix governance (K-local slice)

The inline ULTRA-PLAN approved in session c59ad762 is the authority; this file keeps its decisions and order.
Ledger of the programme: `vault/programs/incremental-cognition/ledger.json`. K evidence: `evidence/K-reference.md`,
`evidence/K-prg.md` (f4d0b2e7).

## Owner decisions 2026-10-05
- Do NOT reset the 2026-10-03 reference (c77535d4...) to make K green; it stays the historical champion.
- K-local (commits 0-10) now, interactively, ~1-2 probes. Steps 11-18 (host floor, capability / rule / project
  scaling, cold-start canary, discoverability, KV/UKDL/CBR at scale) merge into the deferred cognitive-microkernel
  brief and run under /cpp-gsd-long after the quota reset.
- Deferred-tools growth (+41 claude.ai Gmail 30 / Google Drive 11 names) is budgeted as host/account floor if the
  host cannot scope connectors per session.

## Measured attribution (probe fa7e93cb vs reference 8f983bc6, same cwd, same prompt digest)
- SessionStart +6,436 = one element produced by `hook-dispatcher.js` -> `hooks/session_start_hub.js` (the
  superpowers hypothesis is FALSIFIED: its 3,405-char element is in both windows, same sha). Sections:
  rule-stub re-injection 2,985 (`learning-sentinel.js:442-466`, duplicate of the rules layer), 18-rule
  "delivered by file" pointer 1,046 (`:475`; claims ~148 KB, the file is 30,431 bytes), OWNER_QUEUE 1,536
  (`modules/owner_queue`), recovery verdict 608 (`tools/recovery_epoch_gate.py`), AutoResearch digest 261 (hub ~957).
- Deferred tools +3,378: names only (~37 chars each), 72 -> 113 names; all 41 added are claude.ai connectors.
- UNRESOLVED: whether the reference's dispatcher output `{"continue":true}` was a legitimately empty hub or a
  fail-open (commit 1 decides). Why the gate's correlator left the element unattributed (commit 2).

## Order of work (micro-commits; HEAD re-read before each; pathspec only)
0. This file. 1. Reference comparability of the SessionStart component. 2. Gate: producer provenance for composite
hook output + tests. 3. Resident-rent table from transcripts on disk (per-prompt injections counted per turn).
4. Retire the duplicate rule-stub re-injection (consumer check first). 5. Scope OWNER_QUEUE / recovery / AutoResearch
to the consumer that needs them. 6. Replace or justify the 18-rule pointer (and its false size claim). 7. Deploy
live + one K probe. 8. Deferred tools: host scoping test, else account-floor budget. 9. K champion / accepted
baseline / regression-debt + per-component budgets in the gate, tests. 10. Close K-local.

## Execution log (step, commit, calls, result)
