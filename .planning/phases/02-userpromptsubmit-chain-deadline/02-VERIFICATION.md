---
status: passed
phase: 02-userpromptsubmit-chain-deadline
date: 2026-09-21
must_haves_verified: 4
must_haves_total: 4
---

# Phase 2 Verification — UserPromptSubmit chain deadline

**Dir contents at verification time:** only `02-SUMMARY.md` (no PLAN, no CONTEXT).
Confirmed via `Glob` — this is a genuine structural gap in the phase's paper
trail (work landed ahead of its GSD scaffolding, matching the pattern STATE.md
records for Phase 4), not a fabrication concern by itself.

## Central-question framing

Unlike Phase 1, `02-SUMMARY.md` carries **no frontmatter at all** — it does not
self-declare a `verification_status`. Every load-bearing number in it was
independently re-derived against the production file it claims to instrument
(`hooks/hook-dispatcher.js`) and against the live harness config
(`~/.claude/settings.json`), not accepted from prose.

## Per-claim table

| Claim | Verdict | File read | Evidence |
|---|---|---|---|
| Deadline clock starts at `runChain()`, measured via `process.uptime()` at that instant | VERIFIED | `hooks/hook-dispatcher.js:792-800` | `const chainStart = Date.now(); ... const startupMs = Math.round(process.uptime() * 1000);` — comment block explicitly states "The harness's cap starts at PROCESS SPAWN. This clock starts HERE." |
| Measurement instrument is the dispatcher's existing `CLAUDE_DISPATCH_DEBUG` stderr line, format `startup=<ms> deadline=<ms> runnable=N/M` | VERIFIED | `hooks/hook-dispatcher.js:835-844` | `if (process.env.CLAUDE_DISPATCH_DEBUG) { process.stderr.write('[dispatch] ' + event + ... + ' startup=' + startupMs + 'ms' + ' deadline=' + (CHAIN_DEADLINE_MS[event]\|\|0) + 'ms' + ' runnable=' + runnable.length + '/' + chain.length ...)` — byte-for-byte matches the SUMMARY's described output shape (`config_invalid=0`, `runnable=6/6`). |
| `UserPromptSubmit-chain` deadline is 11,500 ms; comment records its own origin measurement `15,173 -> 6,595` | VERIFIED | `hooks/hook-dispatcher.js:688-690` | `'UserPromptSubmit-chain': 11500, // settings.json timeout 15 s; measured 15,173 -> 6,595` |
| Harness cap is 15,000 ms (`15 s`) | VERIFIED | `C:\Users\User\.claude\settings.json:568-578` | UserPromptSubmit hooks entry invoking `hook-dispatcher.js --event=UserPromptSubmit-chain` carries `"timeout": 15` (seconds) — matches the SUMMARY's `harness cap 15,000 ms` row exactly. |
| `UserPromptSubmit-chain` concurrency is 4 (so a 6-step chain runs in two lanes, not serially) | VERIFIED | `hooks/hook-dispatcher.js:582-588` | `'UserPromptSubmit-chain': 4, // ... this chain overran the harness ceiling on an ORDINARY prompt` |
| `CONFIG INVALID` recovery path exists and matches the discarded-reading story (space-form `--event UserPromptSubmit` triggers it) | VERIFIED | `hooks/hook-dispatcher.js:1060,1413` | `'POWER PACK CONFIG INVALID: hook-dispatcher was invoked WITHOUT --event= '` / `` `POWER PACK CONFIG INVALID: hook-dispatcher has no chain named '${event}'.\n` `` — confirms the fail-safe behavior the SUMMARY cites for the discarded batch. |
| Startup: spawn → deadline clock measured at 42 ms median, n=5 (38, 42, 42, 52, 65) | UNVERIFIABLE (re-derivability) | — | No script or log file in the repo reproduces this run; the only record of the raw n=5 samples is the prose table in `02-SUMMARY.md` itself. The **mechanism** that would produce these numbers is verified (rows above); the **specific numbers** are a one-off manual measurement with no persisted artifact. Not the same as a false claim — see below. |
| Free RAM 4,965 → 4,984 MB of 32,061 (15.5 % free) | UNVERIFIABLE (point-in-time reading) | — | `hookPressure()`-equivalent capability exists in the dispatcher (`hostPressure()`, `hooks/hook-dispatcher.js:699-710`, reads `os.freemem()`/`os.totalmem()`), so the mechanism to produce this class of reading is real, but the specific figure is inherently a point-in-time observation with no persisted log to re-check post hoc. |
| "Neither the cap nor the clock is the defect" | VERIFIED (as a conclusion drawn correctly from verified inputs) | `hooks/hook-dispatcher.js:688-710,792-800` | The 42 ms startup figure is measured **before any chain step runs** (`process.uptime()` taken at `runChain()` entry, prior to `runPool`/`runStep`), so it is not contaminated by the synthetic-payload caveat that affects total chain time. The arithmetic (42 ms ≪ 11,500 ms deadline ≪ 15,000 ms cap) is internally consistent and correctly scoped. |
| "Total chain wall time is a lower bound (synthetic payload)" self-caveat | VERIFIED as an honest, doctrinally-correct limitation | `02-SUMMARY.md:54-61` | This project's own `~/.claude/rules/instrument-before-claim.md` states "a probe drives the subject with an input, and an input that cannot reach the expensive path measures startup, not the chain." The SUMMARY applies this rule to itself and explicitly declines to claim the total-time number answers the worst-case question — it only claims the **startup-gap** number does, which is the literal quantity the roadmap asked to measure ("the gap between the chain starting and its deadline clock starting"). This is the correct, self-limiting application of the rule, not a violation of it. |
| No measuring script exists in the repo for this exact procedure (dispatcher invoked directly with `--event=UserPromptSubmit-chain`, real chain, `CLAUDE_DISPATCH_DEBUG=1`) | CONFIRMED ABSENT | Repo-wide grep | `tools/measure_hook_event.py` exists but measures a **different** thing (per-hook subprocess timing enumerated from `settings.json`, summed serially) — it does not exercise `runChain()`'s pooled/deadline logic or read `CLAUDE_DISPATCH_DEBUG` output. No other script matches. The n=5 run was evidently an ad-hoc manual invocation, not a checked-in instrument. |

## Was the done-criterion actually met, or is it structurally unanswerable?

The roadmap's literal ask is: *"Measure the gap between the chain starting and
its deadline clock starting... and say whether the cap or the clock is the
defect."* That gap **is** the startup figure, and the startup figure is
measured before any hook body runs — so it cannot be invalidated by the
synthetic-payload objection the way the *total* chain time can. The
done-criterion ("one bounded run with the interval measured and reported in
milliseconds, against a recorded free-RAM figure, with the cause named rather
than guessed") is met on its own terms. The SUMMARY does not overclaim beyond
this: it explicitly declines to certify the *total* time as a worst case, which
is the correct scope-limiting move rather than a failure to meet the
done-criterion.

## UNVERIFIABLE items — what would close them

- **Raw n=5 sample log.** Would be closed by a checked-in output capture
  (e.g. `_logs/upsc-startup-<timestamp>.log`) of five `CLAUDE_DISPATCH_DEBUG=1`
  runs, per this project's own `python-testing`/instrument doctrine of
  preferring durable artifacts over prose medians.
- **Free-RAM figure.** Inherently a point-in-time OS reading; would be closed
  by the same log file carrying `hostPressure()`'s own stderr line alongside
  each `startup=`/`deadline=` sample, which the dispatcher already supports.
- **Reusable instrument.** No `tools/measure_chain_deadline.py`-shaped script
  exists; `tools/measure_hook_event.py` is a sibling tool for a different
  question and should not be read as covering this one.

## What this phase does NOT establish

- **Worst-case total chain time under a real transcript**, explicitly
  disclaimed by the SUMMARY itself: the probe used a synthetic session id and
  empty `transcript_path`, so `jit_skill_loader` (the historical 11.4 s
  straggler) did not do its real work. The 19.4 s / 17.1 s failure mode is
  addressed by `CHAIN_DEADLINE_MS` + `CHAIN_CONCURRENCY` (both present and
  correct in code), not re-tested end to end under load by this phase.
- **Re-derivability by a third party without re-running a manual command.**
  No script or raw-data file persists the measurement; only this repo's
  verified *mechanism* (the debug line, the deadline constant, the settings.json
  timeout) can be checked after the fact.
- **A PLAN or CONTEXT artifact for this phase.** None exists; the phase's only
  paper trail is the SUMMARY itself, cross-checked here against `STATE.md`,
  `ROADMAP.md` and the dispatcher source.
- **Requirement traceability** — no `REQUIREMENTS.md` exists in this project;
  n/a, not a gap.

## Verdict

**passed, 4/4 must-haves verified.** The two "UNVERIFIABLE" rows above are
re-derivability limitations on a legitimate one-off measurement, not evidence
of a fabricated or contradicted claim — every artifact the SUMMARY's causal
reasoning depends on (the clock's placement, the debug line's format, the
deadline constant and its origin measurement, the harness's real 15 s timeout,
the chain's real concurrency) was read directly from the production files and
matches exactly.
