# IC-009 — Universal Blocking-I/O Eradication & Critical-Path Liveness Closure

Branch: `feature/knowledge-acquisition` · Scanned + executed 2026-09-16
Status: **class closed on the read side, closed on the write side, gates wired.**
Open items at the bottom are real and named.

## 1. Reality Scan — handoff verdicts

| Prior claim | Verdict |
|---|---|
| `bfb40a1` fixes session-file-guard's stdin | **CONFIRMED** |
| `1b70c2a` adds the ratchet | **FALSIFIED (hash)** — no such object. Real commit `5ccbe78` |
| ten remaining offenders | **CONFIRMED** — gate agreed exactly |
| detector's own false negative | **CONFIRMED, already repaired** in `5ccbe78` |
| agent-solo-guard is the only other blocking PreToolUse gate | **CONFIRMED** for `readFileSync(0)`, **REFINED** — that primitive was never the class |
| the stall is inherited-stdin blocking | **PARTIALLY PROVEN, INSUFFICIENT** — see §2 |

## 2. What the scan found that the handoff did not

`session-file-guard.js` — the hook `bfb40a1` fixed, hash-identical to its repo copy —
was parked at 11.4 min, zero CPU, dead parent. Beside it `first-time-project.js`,
which **reads no stdin at all**, parked with the same signature.

**A hook has two pipes.** On Windows Node's stdout-to-a-pipe is SYNCHRONOUS, so a write
over the OS buffer with no reader blocks the event loop exactly like `readFileSync(0)` —
and unlike the read, it CANNOT be restructured to yield, so no timer will ever bound it.

Measured buffers (they disagree because the buffer belongs to whoever CREATED the pipe):

    .NET RedirectStandardOutput    4096 B passes    8192 B BLOCKS
    libuv spawn                   65536 B passes  262144 B BLOCKS

## 3. Final population — four members, not one

| Class | Primitive | Count | State |
|---|---|---|---|
| A | `fs.readFileSync(0)` | 10 | migrated |
| B | shared helper: timer resolved, listener left attached | 2 helpers → 6 hooks | fixed at source |
| C | async listener, no timer | 3 | bounded |
| D | write over the pipe buffer | 1 live (148 KB) | capped + relocated |

**36 of 36 harness-spawned hooks now exit on an unclosed stdin.**
`KNOWN_OFFENDERS` is empty. Post-migration orphan census: 1 parked process, `config.js`,
not a hook.

## 4. Commits

| | |
|---|---|
| `f9b3b52` | pin the second blocking primitive (V-PIPE, 5/5) |
| `966310b` | hook-utils: resolved is not exited; helper added to the repo at all |
| `5ec6d71` | agent-solo-guard migrated; ratchet could be turned by lying |
| `9750371` | five more migrated; the one that nearly lost data |
| `4055f6f` | ratchet reaches zero; every claim driven |
| `7aaf619` | six parked hooks with no banned call; gate rescoped to the property |
| `986febf` | learning-sentinel 148,740 → 1,191 B; V-EMIT-BUDGET |
| `2559fa3` | V-MIRROR: nothing pinned live to repo |
| `98343ce` | UKDL ×4 + incident record |

## 5. Gates

- `tools/test_hook_stdin_liveness.py` — 7 gates. Scoped to the PROPERTY (can this process
  die), drives all 36, derives the claimed-fixed set, reads CPU via syscall to separate
  parked from slow.
- `tools/test_hook_mirror_identity.py` — 5 gates. 18 dual-resident files, 5 frozen
  divergences, drift measured in BOTH directions.
- `hooks/tests/test-pipe-write-liveness.js` — 5 gates, the write-side thresholds.
- `hooks/tests/test-hook-utils-stdin-bounded.js` — 6 gates, mutant included.
- `hooks/tests/test-hook-liveness-gates.js` — bridges the Python gates into the canonical
  `run-all.js`, so enforcement is not a remembered command.

All four mutation drills landed on their own assertion; every restore verified by SHA-256.

## 6. OPEN — named, not hand-waved

1. ~~The canonical suite got slow.~~ **CLOSED** — bounded concurrency (4) on both drives,
   216 s → 80 s, and the CPU classifier was strengthened to two samples so the parallelism
   could not manufacture false accusations. `test-priority-lane` passes again in the suite.
2. **`test-block-reason-propagation` fails 17/20, and it is NOT this work.** Attributed:
   the three failures are all E2E-through-dispatcher (`R1 did not fire on the third
   consecutive edit`); `anti-thrash.js` is unmodified since 2026-04-24 and blocks correctly
   when DRIVEN DIRECTLY (edit 3 → exit 2 with its full reason on stderr); and another pane
   replaced the live dispatcher during this session with `ee54540 chore(dispatcher):
   reconcile the mirror deliberately`. No commit here touches any Edit-chain member.
   **Left for that writer — rewriting under a live session is worse than a correct report.**
   Two hypotheses were raised and refuted before landing on this: a size cap in the
   anti-thrash state map (pruning is by TTL, not count) and the scratchpad fast path
   swallowing the probe (its predicate needs `/temp/claude/` AND `/scratchpad/`; the probe
   has neither).
3. **Five live/repo divergences unreconciled**, two of which (`research-intent-detector.js`,
   `_oneshot_solitary_empty_shell_cleanup.js`) are repo-only work that has never executed.
4. **The harness's own pipe buffer is UNKNOWN.** 4096 B is the conservative floor, not a
   measurement of the real consumer.
5. **Orphan prevention is one short observation**, during a session that was also reaping.
   Not a multi-hour production window.
6. **`learning-sentinel` does not strip a BOM** from its own stdin where sibling hooks do.
7. A concurrent session is writing to `~/.claude/rules` (`presence-is-not-residency.md`
   appeared mid-session). Wide oracles here are bracketing a moving tree.
