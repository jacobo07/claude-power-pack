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

## 2. Full pytest suite

### 2a. pytest availability and install (GEX44)

legitimacy_checkpoint: approved
api_key_recheck: UNSET

Approved by the Owner on 2026-09-30 (answer `y` to: install pytest 9.1.1, pluggy 1.6.0 and iniconfig 2.3.0 into the
job-scratch venv), relayed by a laptop session driving GEX44 over ssh. This supersedes the 2026-09-28 orchestrator
rejection, which was recorded here before.

Pin re-verification against the PyPI JSON API (fetched 2026-09-30, `timeout 30 curl -sS https://pypi.org/pypi/<name>/<version>/json`):

```
pytest 9.1.1 wheel=pytest-9.1.1-py3-none-any.whl pypi_sha256=37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c match=True
pluggy 1.6.0 wheel=pluggy-1.6.0-py3-none-any.whl pypi_sha256=e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746 match=True
iniconfig 2.3.0 wheel=iniconfig-2.3.0-py3-none-any.whl pypi_sha256=f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12 match=True
PINS_OK
```

pip_install_rc: 0
pytest_version: pytest 9.1.1
venv_base_prefix: /usr

Sanity line (python, base_prefix, packaging, pygments, pluggy): `3.12.3 /usr 24.0 2.17.2 1.6.0`

The interpreter is the host's python3 3.12 plus three pytest-dev wheels, which is why it stands in for `python3` in
ROADMAP criterion 2.

Provenance note. The venv directory already existed when this run started: commit 016c19f (2026-09-28 22:20 +0200)
records a pytest 9.1.1 run in this same job-scratch venv that ended rc=3 (INTERNALERROR at collection, no esprima),
but no approval or install record for it was ever written to this file. pip therefore reported the three
requirements as already satisfied and installed nothing new. Because `--require-hashes` does not re-check an already
installed distribution, the installed files were verified directly: the three wheels were downloaded again with
`pip download --require-hashes --no-deps --only-binary :all:` (rc 0) and every file listed in each wheel's RECORD was
hashed in the venv's site-packages: iniconfig 9/9, pluggy 13/13, pytest 88/88 files match, 0 mismatches.

### 2b. Dirty-set bracket (GEX44)

Before:

```
?? .planning/active-workstream
?? .planning/workstreams/cognitive-resource-os/config.json
?? .planning/workstreams/cognitive-resource-os/state.json
```

After:

```
?? .planning/active-workstream
?? .planning/workstreams/cognitive-resource-os/config.json
?? .planning/workstreams/cognitive-resource-os/state.json
```

suite_moved_lines: 0

### 2c. Run (GEX44)

suite_command: timeout 1800 /home/kobii/.claude/jobs/a293bedf/tmp/cro-p01/pytest-venv/bin/python -m pytest tests/ -q --tb=line
suite_cwd: /home/kobii/missions/cognitive-resource-os/.claude/worktrees/cro-gex44
suite_head: 016c19f

Host load immediately before the run (GEX44):

```
== loadavg
0.57 0.67 0.68 4/972 1584475
== free -m
               total        used        free      shared  buff/cache   available
Mem:           64081       14126        1479         315       49628       49955
Swap:          16366         142       16224
```

suite_rc: 0
suite_wall_s: 3.2
suite_summary: 194 passed, 4 skipped in 2.98s
suite_failing_ids: none
suite_verdict: PASS

The suite ran at HEAD 016c19f, which differs from 784e446 outside `.planning/` (see section 4, deviation). One of the
4 skips is tests/test_cascade_populator.py, which since 016c19f skips when esprima is absent; esprima is not importable
by the venv interpreter (`ModuleNotFoundError: No module named 'esprima'`).

### 2d. tools/test_tco.py V-BASELINE-INTACT corroboration (GEX44)

tco_rc: 0
tco_v_baseline_intact: PASS  V-BASELINE-INTACT              rc=0 last='194 passed, 4 skipped in 2.86s'
tco_pass_line: TCO_PASS=14/14  threshold=14/14
tco_moved_lines: 0

FAIL lines: none

## 3. Failure classification

No failure in the suite or in test_tco; no classification needed; no scratch worktree created.

class_counts: ENVIRONMENT=0 ATTRIBUTABLE=0 PRE-EXISTING=0 UNCLASSIFIED=0

## 4. Phase verdict (CRO-01)

inputs: gates_verdict=PASS, suite_verdict=PASS
phase_verdict: PASS

v_baseline_intact_gex44: PASS (suite_wall_s=3.2, bound 1800 s, GEX44)
v_baseline_intact_laptop: INCONCLUSIVE (pytest tests/ exceeded 180 s, host ~630 MB free; RESUMPTION section 2)
tco_v_baseline_intact_gex44: PASS  V-BASELINE-INTACT              rc=0 last='194 passed, 4 skipped in 2.86s'

Constraints honoured:
- no push
- commits by explicit pathspec only
- ANTHROPIC_API_KEY UNSET (section 0; rechecked UNSET at suite run)
- no edit under ~/.claude config or /home/kobii/.claude/skills/claude-power-pack
- no other mission's directory used
- pytest only in job scratch (/home/kobii/.claude/jobs/a293bedf/tmp/cro-p01/pytest-venv)
- no refusal recorded

Deviation (recorded, not hidden): the plan's check `git diff --name-only 784e446 HEAD -- . ':(exclude).planning'`
does not print nothing. It lists vault/knowledge_base/ukdl-cognitive-resource-os.md and
vault/plans/cognitive-resource-os-RESUMPTION.md (Phase 5 commits 471c749, c34511a, 9044735, both in the section 1b
owned set) and tests/test_cascade_populator.py (016c19f, a peer-owned test outside the owned set). The last one
changes what this instrument collects: without it, collection aborted with INTERNALERROR on this host. This verdict
is therefore about HEAD 016c19f, not about 784e446.

next: Phase 5 follow-up: push 016c19f with the branch (it is local-only, ahead 1), and state in RESUMPTION/UKDL that
V-BASELINE-INTACT on GEX44 is PASS at 016c19f. No ATTRIBUTABLE failures.
