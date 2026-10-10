# C2a-fix receipt (2026-10-10)

- Mission id: not visible to this session (no rehydration card in context); goal `cp50-c2`, worktree wt_cp50_c2. Supersedes C2a m-e6ea9c26d377.
- Calls used: 6 of 6 (Read, Edit, PowerShell run, Write, PowerShell git, final message).
- Fix: `_stage_and_seal` in `tools/wros/binary/decomp/gex44/capsule_build.py` now writes `units/TARGETS.jsonl` before `scan_tree` when `targets is not None`, so targets enter the capsule id. Nothing else edited. Staged in wt_cp50_c2, not committed there (snapshot gate); durable form is the patch `vault/backlog/2026-10-10_cp50-c2a-fix.patch`.
- ARM_A_DRILL=8/8
- BENCH_DRILL=8/8 (all PASS; run with `python -I`)
- ARM_A_PREPARED job=C:\Users\User\Apps\recon_work\recon_factory\gex44\jobs\candidate-20261010T151142Z capsule=cap1-ba8a3cfe2822 units=50 functions=5 no_unit=none
- Capsule id: cap1-ba8a3cfe2822. Manifest sha256: not captured (no call left to read it; compute from the job dir's manifest).
- Units n=50; functions with no unit: none.
- Nothing sent (no stage.py send, ssh, scp), no paid/model call, G0_HOLDOUT.json not read, no mission armed, nothing pushed.
- Open points: manifest sha256 and mission id to be filled by C2b/coordinator.

HANDOFF NOTE: C2a done -- C2b may send C:\Users\User\Apps\recon_work\recon_factory\gex44\jobs\candidate-20261010T151142Z
