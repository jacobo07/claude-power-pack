# RESUMPTION_FILE: ctx-rent-a2

Regenerated 2026-10-23 from durable state; updated after the GEX44 residual worker was collected.
**Coherence anchor:** HEAD contains 512188e6 "F5 reads the rollover ledger where rollover.py writes it". If it does not, this file is stale: re-derive before acting.

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Other writers are active, so commit by pathspec only. Goal `ctx-rent-a2`. Plan `vault/plans/context-rent-a2-2026-10-11.md`.
Residual plan `vault/plans/incremental-kernel-residual-2026-10-23.md` (aa97ebf8), Owner `y residual`, then option 1.

**Economics (read `goal-status`; every key carries `scope`).**
- Programme 60,000,000; lease L2 cap 30,000,000.
- Settled 19,522,634; programme_executable 40,477,366 (after the GEX44 worker b27d5705 settled at 1,600,603 measured).
- The b8ff709c correction is APPLIED (approval 3384afb6). This pane (36d35fab) is tombstoned; its own spend is unbooked.

**Residual plan.** R1-R5 SEALED: 7eafc2b0, 2259ca87, c6657844, 7f255a13, fa840b3c, 426a12eb (cpp_fsck), 512188e6.
R6 PENDING: the UKDL entry RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION is in `vault/salvage/residual-fsck-ukdl-entry.patch`
(worker commit 83d58547). It was not applied because `ukdl-universal.md` carries ~1,355 uncommitted lines of another writer.

**Live `python tools/cpp_fsck.py` (2026-10-23):** exit 1. stranded_lease FINDING (old LEAKED/RESERVED reserves across
many goals), worktree_without_lifecycle FINDING (dirty worktrees with no lifecycle row), capsule_without_disposition
FINDING (36 PENDING capsules 2026-09-28..10-20), stale_resumption UNKNOWN (econ-contain has no anchor),
parked_chain_polled UNKNOWN (needs --chain/--tick-log), denominators PASS. Repairs are printed per finding; none applied.

**Slices.** A and B SEALED. Next in plan order: H (econ-succession S1 canary), then C+F, I, D+E+G, J, K, L.

**Next 3 actions.**
1. When `ukdl-universal.md` is clean in `git status`, `git apply vault/salvage/residual-fsck-ukdl-entry.patch` and commit it by pathspec (R6).
2. Ask the Owner before settling the stranded reserves fsck lists: each settle moves another goal's books.
3. Check whether slice H is still live before reading `vault/programs/econ-succession/RESUMPTION_FILE.md`; compact MEMORY.md (+4.2K).

**Start.** Bind your session to ctx-rent-a2, run `python tools/cpp_fsck.py`, then action 1.
