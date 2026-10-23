# RESUMPTION_FILE: ctx-rent-a2

Regenerated 2026-10-23 from durable state. The 2026-10-11 version, which asked for Slice B, was STALE.
**Coherence anchor:** HEAD contains 2259ca87 "status labels its denominators". If it does not, this file is stale: re-derive before acting.

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Other writers are active, so commit by pathspec only. Goal `ctx-rent-a2`. Plan `vault/plans/context-rent-a2-2026-10-11.md`.
Residual plan `vault/plans/incremental-kernel-residual-2026-10-23.md` (aa97ebf8), Owner `y residual`, then option 1.

**Economics (read `goal-status`; every key now carries `scope`).**
- Programme 60,000,000. The Owner raised it from 30M on 2026-10-23.
- Lease L2 has a cap of 30,000,000.
- Settled 18,943,657 across the goal, so programme_executable was 41,056,343 at regeneration.
- The residual plan's own hard stop is 5.0M. The raise does not widen it.
- Pending Owner correction packet `correct-ctx-rent-a2-b8ff709c-2026-10-23.json`. It lowers the b8ff709c mark from 6,867,353 to 5,845,727 (pre-binding 1,021,626 charged twice). The root cause is fixed in 7eafc2b0.

**Slices.**
- A: SEALED (4de21ba8).
- B: SEALED, receipt `SLICE-B-RECEIPT.md`. Call-1 floor fell from 122,093 to 106,769.
- Next in plan order: H (econ-succession S1 canary), then C+F, I, D+E+G, J, K, L.

**Next 3 actions.**
1. Check whether H is still live before reading `vault/programs/econ-succession/RESUMPTION_FILE.md`. Later economics work (owner-control-plane, ccr) may have superseded econ-succession.
2. Compact MEMORY.md (+4.2K regrowth since Slice A).
3. Residual R5 (cpp_fsck) + R6 (knowledge) run as a GEX44 worker. It was launched 2026-10-23 at about 16:45 local, pid 2483351, clone `~/missions/residual-fsck`, branch `mission/residual-fsck` (base 34d3f4a7), brief `vault/plans/residual-fsck-gex44-brief.md`, sonnet, max-turns 45.
   When `RESULT.md` exists there:
   - `git fetch ssh://gex44/home/kobii/missions/residual-fsck mission/residual-fsck`, then cherry-pick by pathspec.
   - Rerun `tools/test_cpp_fsck.py` on the laptop, then `python tools/cpp_fsck.py` against live state.
   - Settle the spend into ctx-rent-a2 with `--measured` from `~/missions/residual-fsck.out.json` usage.
   R1-R4 are SEALED: 7eafc2b0, 2259ca87, c6657844, 7f255a13, fa840b3c. The b8ff709c correction was APPLIED (approval 3384afb6).

**Start.** Bind your session to ctx-rent-a2, then run action 1.
