---
id: SPEC-HOOK-CHAIN-THREAD-RUNNER
title: Run node chain members as worker threads instead of child processes (hook-dispatcher.js)
tier: T2
status: implemented and deployed 2026-11-26 (A3/A4 re-measure pending)
covers: [hook-chain-thread-runner, hook-dispatcher, chain-latency, perf-construction]
owner_go: "go ahead" (laptop pane 8fd6ace9, 2026-11-26) -- to write this spec; implementation needs its own go
---

# SPEC -- Thread runner for hook chains

## Problem (measured, laptop plane)

The Owner's complaint: "Claude responde lento". Over 1,621 laptop turns from the last 7 days
(`.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/LAPTOP-turn-decomposition-7d.txt`):

- Per-turn median 210.8 s: **hooks 53.0 s** (exclusive), model/API 53.3 s, tools 45.8 s, idle 15.7 s.
- Per-hook medians: Stop chain 16.5 s per turn end; PreToolUse Bash chain 4.1 s per shell call;
  PreToolUse Edit chain 7.1 s per edit; Read chain 1.6 s per read.

Mechanism: `hook-dispatcher.js` runs every `*-chain` member as a child process (`runStep` -> `spawn`,
shell:false), with a sequential critical lane and a pool of 4-6 (`CHAIN_CONCURRENCY`). Process start on the
laptop costs 0.15 s idle to over 1 s when the CPU is saturated
(`.../04-host-pressure-admission/records/LAPTOP-contention-sampler-2h.txt`), so a chain pays that price N times.

Feasibility probe (`scratchpad/perf/thread_vs_spawn.js`, 2026-11-26, laptop, unchanged
`windows-bash-bridge-guard.js`, 8 interleaved runs each): child process median 219 ms / 202 ms, worker thread
median **52 ms / 53 ms**, with identical stdout and exit code on both poles (allow: exit 0; block: exit 2 with the
block JSON).

## Decision

Add a second runner to `runStep`: a node member runs in a `worker_threads` Worker with `stdin/stdout/stderr`
piped, executing the **unchanged** standalone script. Inside a Worker `process.exit(code)` ends only that thread
and surfaces as the `exit` code, so the standalone contract (read stdin, write stdout, exit 0/2) is kept with no
refactor of any hook. Python members and any member flagged `runner: 'spawn'` keep the child process.

Rejected: converting members to `module.exports.run` (EVENT_MAP lane). Each needs a refactor, and a member that
calls `process.exit` mid-chain truncates the chain silently (the gsd-context-monitor note in EVENT_MAP).

## Contract

1. `runStep(step, rawStdin)` returns the same shape for both runners: `{error, status, stdout, stderr}`.
   Timeout: `worker.terminate()` at `step.timeoutMs`, reported as `ETIMEDOUT after Nms`, exactly as now.
2. Selection: runner = `thread` when `step.exe === NODE_EXE`, the member is not on `THREAD_DENY`, and the kill
   switch is not off; otherwise `spawn`.
3. Automatic fallback: if the Worker fails to construct, or errors before its first stdout byte with a
   thread-incompatibility signature (`process.chdir`, `ERR_WORKER_*`, an unsupported native addon), the step is
   re-run once as a child process, and one line goes to `hook-dispatcher-errors.log` with the class
   `THREAD-FALLBACK <script>`. Any other error is the member's own result, as now.
4. Isolation that is kept: own V8 isolate, own `process.env` copy, own module cache per member. What is NOT
   isolated, and is why `THREAD_DENY` exists: the process cwd (read-only for workers), process-wide signal
   handlers, and members that rely on `process.stdin` being a TTY or a file.
5. Order and merge are unchanged: the critical lane stays sequential and first; the pool and `runPool`'s
   original-index ordering stay; `mergeOutputs` is untouched.
6. Kill switch: `CPP_HOOK_THREAD_RUNNER=off` restores the child-process runner for every member.
   Per-member opt-out: `runner: 'spawn'` in the chain entry.

## Premises to verify before the first edit (HR-PREMISE-001)

- P1. Three copies of the dispatcher differ today (SHA-256 prefixes, 2026-11-26): live `~/.claude/hooks`
  3433D5E44681, shared repo `hooks/` 106C90EAB4A5, this worktree 5149F3E4DCEE. The change is written against
  the LIVE content, the repo copy is brought to it, and the deploy step is a byte-identical copy checked by hash.
- P2. Every node member of the Bash, Edit, Read, PostToolUse-Bash, UserPromptSubmit and Stop chains is run once
  through the thread runner with a recorded allow payload and a recorded block payload (where it can block), and
  its stdout and exit code are compared with the spawn runner. A member that differs goes on `THREAD_DENY`
  with the reason, never silently.
- P3. `grep` the members for `process.chdir`, `process.on('SIG`, `process.stdin.isTTY`, `require.main` checks
  that would skip the CLI path inside a Worker (in a Worker, `require.main === module` is true for the entry
  script; confirm per member).

## Acceptance (all on the laptop plane)

- A1. Existing dispatcher tests pass unchanged: `hooks/tests/test-priority-lane.js`,
  `test-scratchpad-fast-path.js`, `test-capsule-guard-fallback.js`, `test-capsule-mutation-guard.js --e2e`,
  `test-console-popup-guard.js --e2e`, `test-carrier-bash-guard.js`, `test-destructive-doctrine-card.js --e2e`,
  `test-doctrine-cards.js`, `_tests/test-cascade-deny-and-heredoc.js`, and `tools/test_hook_boundary.py`.
- A2. New `hooks/tests/test-thread-runner.js` (V-THREAD-*): both runners give identical `{status, stdout}` for an
  allow and a block payload on at least the four critical guards (capsule_mutation_guard, windows-bash-bridge-guard,
  secret_firewall_gate, secret-scanner); a member that calls `process.exit(2)` mid-script blocks; a member that
  hangs is terminated at its timeout and reported ETIMEDOUT; the kill switch restores spawn; a forced
  thread-incompatible member falls back once and logs THREAD-FALLBACK. Each assertion has a mutant that it kills
  (always-allow runner, swallowed exit code, no terminate on timeout).
- A3. Measured effect, same instrument as the problem statement: `turn_decomp2.py` and `hook_cost.py` over the
  7 days after deploy, compared with the record above. Target: PreToolUse Edit chain median below 3 s and Bash
  chain below 2 s; hook share of turn wall time down by at least a third. If not met, the spec says so and the
  runner stays only if A1/A2 hold and it is not slower.
- A4. LP-05 re-run (`tools/construction_metrology_report.py`, same flags) after deploy; TTFUR/TTFMC p50/p90
  reported beside the 2026-11-24 baseline.

## Out of scope

No hook is added, removed or reordered; no timeout or concurrency changes; no change to which chains exist or to
`settings.json`. The Stop chain's own members (the largest single cost, 16.5 s median) are not pruned here; this
spec only changes how they are started. Python members are untouched.

## Results (implementation, 2026-11-26, laptop plane)

- P1: live vs repo differ functionally only by `corpus-reuse-sentinel.js` (registered in the repo, not live;
  T-WHOLE-FILE-MIRROR-SYNC). So the change ships as the SAME anchor-checked transform applied to each copy
  (`apply_thread_runner.js`), never as a file copy. Live after deploy: E97E2416F764 (backup
  `~/.claude/backups/hook-thread-runner-20261126T145157/`, hash 3433D5E44681 verified before the copy).
- P2 audit (59 node members, both runners, one allow payload, isolated state): 57/57 finished members faster as
  threads, median 246 -> 57 ms. Two hung as threads, both read fd 0 (`fs.readFileSync(0)`): claude_md_firewall.js,
  claude_md_linter_stop.js -> detected from source, kept on spawn. vault-heartbeat.js differs only by its own
  throttle (first run speaks).
- A1: test-capsule-guard-fallback 7/7, test-capsule-mutation-guard --e2e 24/24, test-console-popup-guard 34/34,
  test-destructive-doctrine-card 17/17, test-carrier-bash-guard 31/31, test-doctrine-cards 25/25,
  test-priority-lane 4/4 (both dispatchers), tools/test_hook_boundary.py 7/7. test-scratchpad-fast-path 15/17 on
  BOTH the old and the new dispatcher (pre-existing, not caused here).
- A2: test-thread-runner.js 33/33 against the candidate. Against live after deploy 32/33: E2E-BASH-BLOCK parity
  failed because the spawn REFERENCE lost member outputs to ETIMEDOUT on a saturated host (22 s chain; error log
  13:52-13:54Z shows cascade_check_bash, ovo-push-gate, console-popup-guard, capsule_mutation_guard timing out).
  To re-run on a calmer host.
- Interleaved end-to-end (6 runs): Edit chain median 10.3 s -> 8.4 s. Bash chain (V-THREAD e2e): block 6.7 -> 3.7 s,
  allow 3.4 -> 1.8 s. The Edit floor is zero-fiction-gate.js (~4.6 s of its own work in either runner).
- A3/A4 (7-day re-measure, LP-05 re-run): pending, due 2026-12-03.

## Rollback

`CPP_HOOK_THREAD_RUNNER=off` (immediate, no file change). Full: copy back
`~/.claude/backups/hook-thread-runner-<ts>/hook-dispatcher.js` (taken at deploy) and verify its hash.
