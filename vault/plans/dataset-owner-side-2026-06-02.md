# Dataset BUCKET-B Owner-Side Items -- Resolution (2026-06-02)

Decision record for the 3 "Owner-side" items surfaced when the BUCKET-B
"~12 gaps" plan was falsified (SCS C29 / BL-DATASET-INVENTORY). PASO-1
read every named module before building; the plan's mechanisms were
wrong for 2 of 3 and the 3rd had no substrate.

## Item 1 -- budget_monitor.py -> RESOLVED (shipped)

Plan wanted a new `register_dataset_signals.py`. Reality: `budget_monitor.py`
documents its own activation ("Owner registers as a SessionStart hook")
and a registration tool already exists (`register_global_hooks.py`, the
C18 pattern). **Built**: added it as **H11** (SessionStart, `--quiet`) to
the existing register tool + reported in `check_hook_status.py`. One
registration source of truth, no fork. Commit 5706b7c.

Owner activation (one-time): `python tools/register_global_hooks.py`.

## Item 2 -- session_cost_estimator.py -> RESOLVED (shipped)

Plan wanted it wired to SessionStart. Reality: it is a manual `--tier 1-5`
diagnostic that prints a ~50-line report -- firing that every session
with a hardcoded tier is wrong. **Built**: exposed as the `/cost-estimate`
slash command (correct mechanism, sibling of `/cost-autopsy`). Commit
5706b7c.

## Item 3 -- ukdl_sync -> SKIPPED (Owner decision D4, 2026-06-02)

Plan wanted to sync the PP UKDL to "active projects' vaults". PASO-1
found there are exactly TWO `ukdl-universal.md` files on the host: the PP
source (`vault/knowledge_base/ukdl-universal.md`) and the global
(`~/.claude/knowledge_vault/core/ukdl-universal.md`). **No sibling-repo
ukdl vaults exist.** The cross-repo sync the plan imagined has no targets;
a tool for it would be orphan machinery.

Owner chose **D4 -- Skip**. Rationale: the only other ukdl is the global
one, already fed through existing PP vault flow; D2/D3 (append/full sync
to other repos) have no substrate; D1 (read-only diff) judged not worth
the file. No `ukdl_sync.py` / `ukdl_diff.py` built.

Re-litigation guard: if a future session sees "ukdl_sync" in a gap list,
this is the closed decision -- do not rebuild without a NEW destination
repo actually maintaining a ukdl vault.

## Gate state

`python tools/test_dataset_build.py` -> 47/47 (44 + V-CMD-COST-ESTIMATE
+ V-REG-BUDGET-MONITOR + V-CHECK-BUDGET-MONITOR). `pytest tests/` 43.
Cross-ref SCS C28 / C29.
