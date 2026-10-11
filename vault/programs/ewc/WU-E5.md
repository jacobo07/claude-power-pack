# WU-E5 -- Fault matrix, hook boundary, liveness, TOKEN BUDGET standard, independent review (M9, M11, M12)

Common brief: `PROGRAMME.md`. Read E1-E4 receipts + `PREMISES.md` first. Route M (20 calls). cwd `C:\Users\User\Apps\wt_ewc`.

Steps:
1. M9 fault matrix in `tools/test_ewc.py` (one V-EWC-FM-* gate per row, real hooks, temp state dirs). Rows not
   already covered by E1-E4: RED with internal fix; AMBER actionable; INFO warning (no obligation); subjective-only;
   missing evidence; missing commit; unconsumed child; explicit next action; review finding; failed test;
   Production Reality missing; human preference; irreversible; outward-facing without authorization; provider/resource
   block; token budget exhausted; iteration budget exhausted; same repair fails 3x (STALLED); next action only in the
   ledger after rotation; Goal Spine unreadable; obligation write fails; evaluator throws; completion unknown; one
   optional warning left after all required gates pass (must STOP_COMPLETE, not loop); out-of-scope opportunity (no
   obligation); two independent obligations; one blocking another (AFTER_DEP is not NOW); child result arriving during
   evaluation. Expected verdict per row written in the gate name's evidence string.
2. Hook boundary: extend `tools/test_hook_boundary.py` (or its sibling per PREMISES e) so the incident fixture goes
   node -> dispatcher Stop-chain -> merged JSON `decision`, proving the dispatcher keeps the block (in enforce mode)
   and that shadow mode never emits one. Plus `hooks/tests/test-matcher-liveness.js` stays green.
3. Liveness: `python modules/liveness/reachability.py` exit 0; every new module wired or declared.
4. M11 TOKEN BUDGET standard: add a mandatory TOKEN BUDGET section to the canonical plan template (path from
   WU-E1-receipt): measured / estimated / unknown labels; context used; planning, implementation, review, Production
   Reality, rotation, Agent Teams costs; model routing; rotation / downgrade / pause triggers; and the line "price
   units with `tools/route_admission.py admit` before writing this table" (KNOWLEDGE K1). If a plan-lint gate exists,
   make it require the section; if none exists, do not invent one -- record the gap.
5. M12 independent review: dispatch ONE `pp-code-reviewer` agent (solo in its message, bounded prompt with a write-
   as-you-go findings file `vault/programs/ewc/REVIEW-E5.md`), scope = `git -C <wt> diff 696ce37a..HEAD`. Then ONE
   `woz` agent the same way on the hook changes only. Ask both to hunt: Stop paths bypassing the gate, warnings not
   compiled, human-gate overuse, infinite loops, budget escapes, child-result loss, rotation loss, false COMPLETE.
   Fix every HIGH/CRITICAL; record MEDIUM/LOW dispositions. A reviewer that ran no checks cannot approve.
6. Re-run the full touched set + `python tools/test_hook_boundary.py` + `node hooks/tests/run-all.js`.
Receipt: matrix pass count N/N, review verdicts + each finding's disposition, plan-template commit.
