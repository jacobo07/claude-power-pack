# P5 receipt -- recon-factory Phase 5 (FAILED LEASE: nothing built)
Mission: m-6d6bb4cef637 | worker session 13f4a97d | written by the main pane: the worker's own receipt Write was refused by
the session budget breaker (17 tool calls > 1.5 x estimate 10).
Spend (control plane, message-id dedup): 11 calls, 1,412,234 processed (5,622 out). Route target 1.35M, stop 1.65M: over
target, under stop, zero output.
Files: none in the recon work tree; no commit there (HEAD still 2ca5ee3).

Root cause (main pane, not the worker): the packet named `full/closure_census.py` as if it existed and gave no source for
the six numbers. Phase 1 RESEARCH lists it as "(new)"; KEOS_RECON_FACTORY_PLAN.md:22-23 says the M0 census script "was
scratch and is unversioned". The worker spent its budget searching for a premise the packet should have pinned
(HR-PREMISE-001; compiled grammar requires a dossier, P5 shipped without one).

Located afterwards (for the re-lease dossier):
- M0 = Island Hopper closure, commit aa1d82c (2026-10-01): 1,131 Pln functions, DIRECT 541 / CHEAP 302 / FAMILY 148 /
  TRIVIAL 115 / FRONTIER 25; blockers CLASS 588, SDA 330, CXX 94.
- Evidence: .ksr_vault/frontier/island_hopper/M0_CLOSURE_CENSUS.md (method, 175 lines) and M0_closure.json (output).
  Present in the KSR main checkout; ABSENT on disk in the recon work tree (read with `git show aa1d82c:<path>`).

Mission state: BLOCKED (surface only, no relaunch planned). Re-lease needs a new Owner go.
HANDOFF NOTE: P5 blocker -- packet premise unpinned; re-lease with a zero-model M0 dossier.
