# Phase 01 EVIDENCE -- Gate verdict on the big host (GEX44)

Every figure below was measured on GEX44, in the worktree
`/home/kobii/missions/cognitive-resource-os/.claude/worktrees/cro-gex44`, not on the laptop. Measured 2026-09-28
(UTC, see `## 0. Pre-checks` for the exact timestamp).

## 0. Pre-checks

ANTHROPIC_API_KEY: UNSET
head: 8a40ad377589a2e0b3b3d42b57cfa806568c7bfb
branch: mission/cognitive-resource-os-gex44
base_commit: 784e446
measured_at_utc: 2026-09-28T11:59:17Z

`git diff --stat 784e446 HEAD`:

```
 .../cognitive-resource-os/REQUIREMENTS.md          |  25 ++
 .../workstreams/cognitive-resource-os/ROADMAP.md   | 110 ++++++++
 .../workstreams/cognitive-resource-os/STATE.md     |  23 ++
 .../01-gate-verdict-on-the-big-host/01-01-PLAN.md  | 271 +++++++++++++++++++
 .../01-gate-verdict-on-the-big-host/01-02-PLAN.md  | 300 +++++++++++++++++++++
 .../01-gate-verdict-on-the-big-host/01-CONTEXT.md  |  47 ++++
 6 files changed, 776 insertions(+)
```

All six changed paths are under `.planning/`; no source file differs between 784e446 and HEAD. (The planning-time note
said "only four files" -- this run's HEAD is two plan files later than that snapshot: 01-01-PLAN.md and 01-02-PLAN.md
were written and committed since, still entirely under `.planning/`.)

host:
- uname -sr: `Linux 6.8.0-134-generic`
- nproc: `20`
- free -m:
```
               total        used        free      shared  buff/cache   available
Mem:           64081       14096        2411         199       48494       49985
Swap:          16366         143       16223
```
- loadavg (/proc/loadavg): `1.38 1.20 1.02 7/951 4092627`
- python3 --version: `Python 3.12.3`

pytest_probe_rc: 1

Command: `python3 -m pytest --version`

```
/usr/bin/python3: No module named pytest
```

The host python3 has no pytest module, confirming the planning-time finding. No install performed in this plan.

## 1. Workstream gates

### 1a. Gate results (GEX44)

| gate | command | exit | pass line (verbatim, GEX44) | laptop reference (RESUMPTION section 2) |
|------|---------|------|------------------------------|-------------------------------------------|
| tools/test_tis_observed.py | `timeout 600 python3 tools/test_tis_observed.py` | 0 | `TISOBS_PASS=25/25  threshold=25/25` | 25/25 |
| tools/test_pricing_source.py | `timeout 600 python3 tools/test_pricing_source.py` | 0 | `PRICESRC_PASS=5/5  threshold=5/5` | 5/5 |
| tools/test_budget_monitor_observed.py | `timeout 600 python3 tools/test_budget_monitor_observed.py` | 0 | `BUDGETOBS_PASS=7/7  threshold=7/7` | 7/7 |
| tools/test_prefix_inventory.py | `timeout 600 python3 tools/test_prefix_inventory.py` | 0 | `PREFIXINV_PASS=9/9  threshold=9/9` | not recorded in RESUMPTION |

no [FAIL] lines

### 1b. Workstream-owned file set

owned_count: 20

Command: `git show --name-only --format= 9fa1017 48bbbb7 383cb37 ca69a04 10299f8 5496a60 0d712dc 6aa3bb6` (the eight
sealed commits named in RESUMPTION section 2), filtered of empty lines, `sort -u`.

```
commands/cost-autopsy.md
commands/knowledge.md
modules/token-optimizer/prefix_inventory.py
tools/budget_monitor.py
tools/jit_skill_loader.py
tools/pricing_source.py
tools/tco_compact_gate.py
tools/test_budget_monitor_observed.py
tools/test_prefix_inventory.py
tools/test_pricing_source.py
tools/test_tis_observed.py
tools/tis_observed.py
tools/tis_report.py
tools/verify_full_install.py
vault/config/model-routing.json
vault/knowledge_base/ukdl-cognitive-resource-os.md
vault/liveness/reachability_registry.json
vault/plans/cognitive-resource-os-2026-09-27.md
vault/plans/cognitive-resource-os-RESUMPTION.md
vault/pricing/anthropic_2026-09.json
```

`tools/tco_compact_gate.py` and `tools/jit_skill_loader.py` are in this set because `0d712dc` (the model-routing
migration) edited them, although RESUMPTION section 2a names `tco_compact_gate` as another peer's reader (it reads
transcripts itself for a separate consolidation effort). That is an overlap between the git-derived owned set and
the RESUMPTION-narrated ownership note, recorded here rather than edited out of the set.

### 1c. Gate dirty-set bracket

t1_moved_lines: 0
t2_moved_lines: 0

The Task 1 gate dirty-before and dirty-after porcelain sets are identical (the pre-existing dirty entries --
`.planning/workstreams/cognitive-resource-os/STATE.md` modified, plus four untracked orchestrator-local paths --
are unchanged by the gate run). No moved lines.

The Task 2 gate dirty-before and dirty-after porcelain sets (bracketing the three remaining gate runs) are also
identical to each other and to the Task 1 sets. No moved lines.

### 1d. Gate verdict

gates_verdict: PASS

All four gate exit codes are 0. All four pass lines read N/N with N == the threshold (25/25, 5/5, 7/7, 9/9). No
`[FAIL]` line appears in any of the four logs. Both dirty-set brackets (t1, t2) are empty. GEX44 matches the
laptop reference exactly for the three gates RESUMPTION records a count for (25/25, 5/5, 7/7); `test_prefix_inventory.py`
has no laptop reference count to compare against (RESUMPTION section 2 does not record one), so its 9/9 is reported
here as GEX44's own figure, not as a match or a difference against the laptop.

### 1e. Gate failure classification

No gate failure; no classification needed; no scratch worktree created.
