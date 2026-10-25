---
phase: 08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate
plan: 03
completed: 2026-10-25
status: complete
---

# 08-03 summary: master gate

`tools/s9_done_gate.py` collects each acceptance suite under a dirty-path bracket, binds the result to the sha256 of the git blobs under
`HEAD:tools`, `HEAD:hooks` and `HEAD:modules` (its own two files excluded), and judges the stored evidence. It never re-runs a suite when judging.

- Gates: `python3 tools/test_s9_done_gate.py` prints `S9_PASS=43/43`. They cover the suite rules, the seal-check instrument (control roots in temp dirs),
  one control per mission-judge gate, 12 mutants of the judge each killed by its mapped probe with a no-op control, the report, and the cited residuals.
- Evidence: `08-DONE-GATE.json` (18 suites collected on a clean tree). Rendered report: `08-REPORT.md` (`python3 tools/s9_done_gate.py report`).
- Mission verdict: **NOT_DONE**. One cause: `test_cpp_gsd_long_routing` is red outside the known set (V-ROUTE-LIVE-COMMAND-IS-REPO-COMMAND finds no
  `cpp-gsd-long.md` under the HOME the test builds; 8 of 9 gates pass). With that suite green the judge returns DONE_WITH_RESIDUALS. No host file was edited.
- Residuals: red-team BREACH 8 and 12, UNMEASURED claims 1, 2, 3, 5, 15, milestones S1-S5 and S7 MET_WITH_UNMEASURED, LAPTOP-ONLY items,
  4 legacy PLAN files without frontmatter, and W1-W5 plus the epoch_compacted rows quoted verbatim.
- The known red V-MSPEND-HOLD-PLAN-NONE did not reproduce on this host (test_mission_spend 46/46); V-AMCR-ONE-RESOLVER-INVENTORY did (38 gates, 1 red).
- Live S1 context rotation: 7 of 17 observed epochs of m-3d5f0a27e41d.
- `blocker_compiler decisions` emits one item: the claim-15 question. The held UKDL section was applied to ukdl-universal.md and the patch deleted (71c26db4).
- Close: `python3 tools/s9_done_gate.py seal-check --expect 8` returns PENDING_VERIFIER (exit 2) until `08-VERIFICATION.md` passes.
