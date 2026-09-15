# Observation Surface Closure — plan, 2026-08-27

Branch `frontier28/session-2026-08-26`, worktree `wt-clean`, base `14a4658`.
Read-only reconnaissance done before this file was written. Every number below
was measured today, not carried from the previous session's report.

## 0. Verified starting state

| Claim (prior report) | Verified today |
|---|---|
| 11 commits, pushed, head `14a4658` | TRUE — `origin/frontier28/session-2026-08-26` = `14a4658` |
| tree clean, concurrent work preserved | TRUE — main worktree is on `feature/knowledge-acquisition`, 200+ dirty files, untouched |
| five `Bash`-only registrations | TRUE — unchanged |
| canonical/live dispatcher divergence | TRUE — exactly one: `session_delta_stop.js` in canonical only |
| "zero PowerShell events in CEPS" | **FALSE, and worse than reported** — 2 exist, both injected by `test_capture_liveness.py` into the PRODUCTION store |

## 1. The measurement that governs the mission

Independent of the event store, from 98 session transcripts (789 MB, since 2026-08-16,
the window `fires.jsonl` covers):

```
PowerShell  11126  29.2%      Bash   3618   9.5%
COMMAND TOOLS: Bash 3618 + PowerShell 11126 = 14744
PowerShell share of command traffic ............ 75.5%
CEPS observation coverage of command surface ... 24.5%
errored tool_results in window ................. 3399
CEPS fires in window ...........................    84
```

The instrument observes the minority surface. This is a denominator measured from a
source the instrument does not control, per §7.

## 2. Owners — zero new systems (§3, §63, HR-NOVELTY-001)

| Need | Existing owner | Action |
|---|---|---|
| observation coverage | `tools/capture_liveness.py` | EXTEND |
| sensor health verdicts | same file's `verdict` field | EXTEND |
| event trust state | `ceps.py` `admission_status` | ALREADY EXISTS |
| data regime version | `ceps.py` `ADMISSION_REV = 1` | BUMP to 2 |
| predictor maturity | `predictive.py` `SUBSTRATE_*` | ALREADY HONEST |
| settings.json migration | `tools/migrate_*.py` pattern | REUSE pattern |

Nothing in this plan creates a new system, dataset family, or authority.

## 3. Defects found in reconnaissance

1. **Coverage is unmeasurable by the gate that exists to measure it.**
   `capture_liveness.py` computes `registered` as `marker in cmd` — presence of the
   basename anywhere in settings.json. Its own producer table says the bridge covers
   "Bash/PowerShell". Registration presence ≠ registration coverage, so a producer bound
   to the wrong surface reads as wired.
2. **`bench_all.py:332` records `category='bench_all'`**, which is not in
   `VALID_CATEGORIES`. All 41 attempts rejected. The benchmark named `ceps_record_ms`
   has therefore only ever measured the REJECTION path.
3. **Test writes reach the production store.** `test_capture_liveness.py` feeds
   synthetic Bash/PowerShell/Read payloads through the real bridge; 4 fires and 2 events
   landed in production. Rejections carry `origin`; events do not, so the contamination
   is unrecoverable after the fact.
4. **The bridge's code already handles PowerShell** (`COMMAND_TOOLS`, repaired
   2026-08-14) while its registration does not. Correct logic, wrong address.

## 4. Per-registration matcher disposition (§10 — no bulk change)

| Registration | Disposition | Reason |
|---|---|---|
| `bug-hunter-ceps-bridge.js` | **WIDEN** | code explicitly handles PowerShell; 75.5% of subject unobserved |
| `osa_deploy_detector.js` | evaluate | deploys run through PowerShell on this host |
| `bug-hunter-learning.js` | evaluate | SCOPED producer, no-op outside InfinityOps |
| `tty-restore.js` | likely KEEP | may be intentionally narrow; PowerShell does not mangle the TTY the same way |
| `hook-dispatcher.js --event=PreToolUse-Bash-chain` | **KEEP unless proven** | widening adds a gate chain to 11k PowerShell calls (§100) |

## 5. Workstreams and modes (§64 — smallest mode that preserves correctness)

- **A. Coverage gate** — EXECUTION. Extend `capture_liveness.py` with declared-vs-matched
  surface coverage; fail on divergence. Owner known, local, reversible.
- **B. Contamination boundary** — EXECUTION. `origin` on events; `ADMISSION_REV` 2.
- **C. bench_all category** — EXECUTION. Concrete defect, one line, gated.
- **D. Matcher widening** — PLAN-GATED. Written as an idempotent, backup-first,
  dry-run-default migration in the existing `tools/migrate_*.py` idiom. `--apply`
  runs only under the approval this plan carries (HR-001: the PP half ships either way).
- **E. Dispatcher reconciliation** — EXECUTION for the parity gate; the live-copy write
  is Owner-side.
- **F. Adversarial falsification** — mandatory before done.

## 6. Stop conditions

Stop only for: the live `~/.claude/hooks/` write (denied to this agent), and any
finding that turns out to require an Owner policy choice. Everything else proceeds
without asking.

## 7. Done-gates

CEPS: coverage measured, gap either closed or named by a FAILING gate; a real
PowerShell failure recorded end-to-end; a benign PowerShell success not recorded;
no duplicate capture; test writes distinguishable from organic ones.
Umbrella: every red attributed. No maturity claim beyond evidence.
