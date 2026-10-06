# WU2 packet (from WU1)
Task: zero-model wake check on an EXISTING scheduled task per post-E1 Phase 2 in vault/plans/post-e1-meta-work-2026-10-06.md. Cap 0.4M processed, <=8 calls realistic (fresh worker costs ~100k+/call). Never borrow; write a receipt AS YOU GO.
Facts from WU1:
- Scheduled tasks are defined in tools/install_sprint1_daemons.py DAEMONS (name, tool, args, time). PP-Vault-Summarize = tools/vault_summarize.py --check at 02:00 (pythonw, zero model). Registration changes are Owner actions: do not re-register.
- Gate CLI now has --admit-cwd; organic floor check: python tools/floor_regression_gate.py --check --reference vault/programs/incremental-cognition/floor/reference.json --project-dir <proj dir> --chars-only --admit-cwd -> exit 1 (MATERIAL_RISE, total ref 188147 now 225830) at WU1 time; exit 2 = UNKNOWN, never green.
- Test suite tools/test_floor_regression_gate.py was 60/61 (see WU1-receipt.md for the failing gate; pre-existing vs mine unverified).
- WU1 wiring of --check into vault_summarize.py NOT done (AUTHORIZATION_BOUND / budget). Do not assume it exists.
Wait test required: dormant task runs 0 model calls; a fixture flip wakes it (both poles).
Env: PowerShell tool only for shell; git -C with C:\Program Files\Git\cmd\git.exe; pathspec commits only; never push/reset/stash.
Use `python tools/cep_gen2.py --status` for ledger state. Log page faults.