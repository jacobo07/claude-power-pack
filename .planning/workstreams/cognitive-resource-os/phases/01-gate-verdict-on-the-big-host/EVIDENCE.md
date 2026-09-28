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

no [FAIL] lines

### 1c. Gate dirty-set bracket

t1_moved_lines: 0

The Task 1 gate dirty-before and dirty-after porcelain sets are identical (the pre-existing dirty entries --
`.planning/workstreams/cognitive-resource-os/STATE.md` modified, plus four untracked orchestrator-local paths --
are unchanged by the gate run). No moved lines.
