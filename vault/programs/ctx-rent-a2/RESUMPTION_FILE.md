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
R6 SEALED AS A SEPARATE FILE (Owner "y", 2026-10-24): the UKDL entry RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION is in
`vault/knowledge_base/ukdl-recomputation-without-causal-invalidation.md`. The patch (worker commit 83d58547) stopped applying
because `ukdl-universal.md` carries ~1,500 uncommitted lines of another writer. Merging the entry into UKDL is left for later.

**Live `python tools/cpp_fsck.py` (2026-10-24):** exit 1. stranded_lease: none. All 71 reserves plus 3 that leaked
later are settled with Owner consent (cp50-c1 c021de1c booked at its one-call transcript, 215,716).
Those settles over-charged 14,795,560 of pre-binding history across 13 sessions in 9 goals, because a booked pane was
capped only at mark + holds. The fix is 7ea946df (gates V-MSPEND-SETTLE-BOOKED-EXCLUDES-PREBIND-*). The 13
Owner-approved correction packets are APPLIED in `~/.claude/state/capital-authority/corrections.jsonl`, and all 13
marks were re-read equal to the packet values. worktree_without_lifecycle FINDING (dirty worktrees with no lifecycle row), capsule_without_disposition
FINDING (36 PENDING capsules 2026-09-28..10-20), stale_resumption UNKNOWN (econ-contain has no anchor),
parked_chain_polled UNKNOWN (needs --chain/--tick-log), denominators PASS. Repairs are printed per finding; none applied.

**Slices.** A and B SEALED. Next in plan order: H (econ-succession S1 canary), then C+F, I, D+E+G, J, K, L.

**Next 3 actions.**
1. When `ukdl-universal.md` is clean in `git status`, append the entry from the separate file into it, then delete that file and the salvage patch in the same commit.
2. cp50-c1's lease reads -6,250,345 (used 7,750,345 vs cap 1,500,000). That was mostly there before the settles; ask the Owner whether to investigate it.
3. Check whether slice H is still live before reading `vault/programs/econ-succession/RESUMPTION_FILE.md`; compact MEMORY.md (+4.2K).

**Start.** Bind your session to ctx-rent-a2, run `python tools/cpp_fsck.py`, then action 1.
