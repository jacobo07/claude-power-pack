---
covers: [pp-self-eval, self-eval, ablation, eval-harness, layer-ablation, gap-1]
status: APPROVED-DECISIONS  # Owner answers 2026-09-30, see §2
tier: T2
---

# PP Self-Eval — automatic, standing measurement of whether Power Pack helps

Gap 1 of `vault/audits/se-capability-gaps-2026-09-30.md`. Generalises the one-off P3
ablation (`.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/`) into a
system that runs by itself.

## 1. Problem

PP loads ~140k tokens of context into every session and runs dozens of hooks, and none of
it is measured for effect on outcomes. P3 measured one slice once and found no loss when
three rule files left the prefix (−27k tokens/session). Its own report names why it could
not have found a loss: **every task passed in both arms** (ceiling) — the task set had no
power. A standing eval must (a) run without anyone starting it and (b) use tasks that can fail.

## 2. Owner decisions (2026-09-30, do not re-litigate)

| decision | answer |
|---|---|
| trigger | on change to a layer (queued) + nightly slot + weekly full baseline |
| budget | ≤ 16 model runs per night; stop at first usage-limit signal, resume next night |
| layers | always-loaded context, hooks, skills |
| action | report + propose to OWNER_QUEUE; never applies a change itself |

Standing constraint (memory `feedback-experiments-on-subscription-quota-not-paid`): model
calls run on subscription quota via `claude -p` (OAuth). Never `--bare` (needs an API key),
never the paid SDK.

## 3. Architecture

`modules/pp_eval/` (library) + `tools/pp_eval.py` (CLI) + a scheduled task.

```
harvest ─▶ bank (hidden) ─▶ calibrate ─▶ schedule ─▶ run arms ─▶ grade ─▶ verdict ─▶ report + OWNER_QUEUE
                                              ▲
                          layer fingerprints ─┘ (change detection)
```

### 3.1 Harvester (no model calls)
Mines real bug-fix commits from configured repos (default: PP + repos listed in
`~/.claude/state/pp-eval/repos.json`). A candidate = commit whose diff touches ≥ 1 source
file AND adds/changes ≥ 1 test file, subject matches fix/bug/repair vocabulary.
**Validated** only if, in a fresh worktree: the fix commit's test FAILS at the parent and
PASSES at the fix, within 120 s, deterministically (run twice). Task record: repo, parent,
fix, test paths, test command, subject.

### 3.2 Bank (hidden)
`~/.claude/state/pp-eval/bank.json` — outside every worktree an agent sees. The agent gets
the parent tree **without** the fix's test files, and the prompt = the commit subject plus
the test's name (what must work, not how). After the session, the fix's tests are copied in
and run as the grade. Bank-access audit over the stream-json tool inputs (P3 practice).

### 3.3 Calibration (fixes P3's ceiling)
Amended 2026-09-30 before S3: parking tasks that always pass in arm A would hide the very
signal a LOSS is (A passes, B fails). So no task is parked. A task is **discriminating**
when its VALID history (any layer, any arm) holds at least one pass and one fail. The
weekly baseline (arm A over the whole bank) discovers difficulty; layer nights prefer
discriminating tasks, then the least-run ones. The ceiling defence moves into the verdict:
`NO_LOSS` needs ≥ 4 discriminating tasks among those compared, else `INSUFFICIENT (ceiling)`.

### 3.4 Layers and arms
| layer | arm A | arm B | positive control (must hold or the run is VOID) |
|---|---|---|---|
| context | as-is | `--settings {"claudeMdExcludes": [...rules, CLAUDE.md files]}` | first-call input tokens B < A by ≥ the excluded bytes/4 × 0.5 |
| hooks | as-is | `--settings {"disableAllHooks": true}` | `--include-hook-events`: A > 0 hook events, B = 0 |
| skills | as-is | `--disable-slash-commands` | stream shows no Skill tool call in B |

All runs: `--no-session-persistence --output-format stream-json --include-hook-events`, the
session's default model, fresh worktree under `C:\Users\User\Apps\pp-eval-runs\`, deleted
after grading. Env `CLAUDEPP_EVAL_CHILD=1` marks children.

### 3.5 Change detection
Fingerprint per layer = sha256 over the sorted (path, sha256) of its files
(context: `~/.claude/rules/**`, `~/.claude/CLAUDE.md`, PP `CLAUDE.md`, memory index;
hooks: `~/.claude/hooks/**` + settings hook blocks; skills: `~/.claude/skills/*/SKILL.md`).
A layer whose fingerprint differs from its last evaluated one is queued first. Covers
edits made outside git, which a commit hook would miss.

### 3.6 Scheduler
Windows scheduled task, nightly 03:30, hidden launch (wscript + `hidden_launch.vbs`, per
memory `feedback_scheduled_task_zero_flash_wscript`). Each night: acquire a kernel lock
(same mechanism as `gsd_mission._Lock`) → skip if free RAM < 6 GB or an interactive claude
session wrote to its transcript in the last 15 min → harvest if the bank is short (no model
calls, so it runs even under the quota ceiling) → quota ceiling → pick work (changed layers first; Sunday
= baseline) → run ≤ 16 → stop early on a usage-limit / rate-limit signal in the stream
(recorded `DEFERRED_QUOTA`, never retried the same night).

**Quota ceiling (amended 2026-09-30).** The first probe measured the Owner's 7-day window at
93 %. The night never starts while the last observed utilization is ≥ 0.80 (7-day) or ≥ 0.50
(5-hour) and its reset time has not passed, and it stops after any run whose
`rate_limit_event` crosses those levels. No probe call is spent to learn this: each run's
own stream carries it, and the ledger keeps the latest reading with its reset time.
Thresholds: `~/.claude/state/pp-eval/config.json`.

### 3.7 Verdict (per layer and layer fingerprint, paired by task × replicate)
Only VALID rows recorded under the layer's CURRENT fingerprint are compared.
- `LOSS` — some task passes in A and fails in B in 2 of 2 replicates (the layer helps).
- `HARM` — some task fails in A and passes in B in 2 of 2 replicates (the layer hurts).
- `NO_LOSS` — ≥ 4 tasks with 2 complete pairs, B passes every pair A passes, ≥ 4 of them
  discriminating (§3.3), and for the context layer every pair's first-call context is at
  least 1,000 tokens lower in B.
- `INSUFFICIENT` — anything else, with the reason (too few pairs, ceiling, context control).
Secondary (never a tie-breaker): context tokens, wall time, turns. Only aggregates are
reported; P3 measured A/A spread up to 1.7× per task.

### 3.8 Output
State, not repo (amended 2026-09-30: nightly writes must not dirty a shared tree):
`~/.claude/state/pp-eval/runs.jsonl` (one row per run, fsync'd), `nights.jsonl` (one row per
night incl. skip reasons), `REPORT.md` (regenerated from the ledger alone). `NO_LOSS` and
`HARM` are actionable and go to `modules.owner_queue` (SessionStart digest); `LOSS` is
reported only. Registered `SCHEDULED` in `vault/liveness/reachability_registry.json`.

## 4. Acceptance criteria
1. `tools/test_pp_eval.py` passes with a fake `claude` binary (no model calls): harvester
   validates a synthetic fix commit and rejects a non-failing one; arms build the right
   flags; each positive control can VOID a run; verdict table returns all three outcomes;
   the quota signal stops the night; the lock refuses a second instance.
2. Each guard is mutation-drilled (break it, the gate goes red).
3. Harvest over PP produces ≥ 8 validated tasks (reported number, not assumed).
4. Scheduled task registered and its first night leaves ≥ 1 ledger row or a recorded
   skip reason. Observed, not assumed.

## 5. Never-do
- Never modify rules, hooks, skills or settings — propose only.
- Never run in the Owner's working tree; never leave a worktree behind.
- Never call the paid API or `--bare`.
- Never count a VOID run toward a verdict; never report `NO_LOSS` without ≥ 4 active tasks.

## 5b. Known limits (stated, not engineered around)
- **Arm-A children run the real hooks, and hooks write shared state** (CEPS events, session
  logs, learning markers, graph writeback). Silencing them would change the thing measured.
  Children carry `CLAUDEPP_EVAL_CHILD=1` and `--no-session-persistence`, so they are
  identifiable and never appear in `/resume`; hooks do not read that variable today.
- **The context arm removes global context only.** The task repo's own CLAUDE.md stays in both
  arms; for tasks harvested from PP itself that file is PP context and is not ablated.
- **Tasks come from repos whose tests read their own tree.** Tests that import the LIVE
  install by absolute path pass at the parent and are rejected by validation, by design.
- One host, one model at a time, subscription quota only.

## 6. Rollback
Unregister the scheduled task (`schtasks /Delete /TN PP-SelfEval /F`); the module is
inert without it. Ledger and bank are data only.

## 7. Slices
S1 harvester + validator · S2 runner/arms/grade with fake-claude tests · S3 fingerprints +
scheduler + lock + quota stop · S4 verdict + report + OWNER_QUEUE · S5 install task, observe
first night.
