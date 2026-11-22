---
covers: [self-improve, analyze-transcripts, unattended, self_improve_unattended]
tier: T3
status: BUILT 2026-11-22 (Owner "y"); PP-SelfImprove registered, daily 04:30
date: 2026-11-22
---

## As built (supersedes the sections below where they differ)

- **Fixed core = guard AND driver.** `tools/self_improve_guard.py` (policy) and `tools/self_improve_unattended.py`
  (git, merge, revert, admission calls) are both pinned in `vault/self_improve/guard.sha256`: if the loop could edit
  the driver it could stop calling the guard. What the loop improves about itself lives in
  `tools/self_improve_policy.py` (keys, trend, ranking, prompt, tuning, report) and in its live parameters
  `~/.claude/state/self-improve/params.json` (seeded from `vault/self_improve/params.json`, clamped by the guard).
- **The agent has no shell** (Read/Write/Edit/Glob/Grep, model sonnet). The driver runs every test: the new test
  must FAIL on the old code, pass on the branch, and the MERGED tree must pass it plus the regression block.
- **Landing** = `merge-tree --write-tree` + `commit-tree`, then `checkout <new> -- <paths>` on clean paths and a
  compare-and-swap `update-ref`; never the shared index as a whole. A dirty path -> PENDING_MERGE, retried daily.
- **Rectify attribution:** a red gate at HEAD reverts only if the same gate passes at HEAD-without-the-change;
  red both ways is someone else's breakage and the change is kept.
- **Host-stall days** suppress hook-latency and hook-timeout candidates (they are victims of host load).
- **Liveness:** the reachability scan covers `modules/` only; these files are in `tools/` and reached by the
  scheduled task, so no registry entry applies.
- **Agent sandbox (review H1, 2026-11-22):** `--allowed-tools` only pre-approves; it does not remove tools, and
  the child loaded the Owner's settings (blanket Bash/PowerShell allows). The agent now runs with `--restricted
  --strict-mcp-config --disable-slash-commands --tools Read,Write,Edit,Glob,Grep`. Proven with a real `claude -p`
  (haiku) in a temp dir: no shell tool, a write outside the cwd blocked, a write inside allowed.
- **Executed agent code (review H2):** the driver runs the agent's test and code. Residual risk, mitigated, not
  removed: a diff may not ADD subprocess/os.system/sockets/http/ctypes/eval/exec/importlib/absolute or home paths/
  child_process/fs writes/process.env; the core, its pin, `~/.claude/settings*.json` and `~/.gitconfig` are
  fingerprinted around every agent run and gate run, and a change stops the cycle and writes the `OFF` switch.
  There is no OS-level sandbox for those test runs.
- **Judges are untouchable:** the regression suites, `tools/analyze_transcripts.py`, `tools/transcript_events.py`;
  measurement (keys, snapshots, rates) is in the pinned driver, not in the policy module.
- **Rectify robustness:** a red gate re-runs once; a timeout is inconclusive (never a revert); no gate verdict below
  20% free RAM; one change's error never stops the others; the ledger is saved right after every landing/revert.
- **Landing branches** are listed in the guard (`main`, `feature/knowledge-acquisition`); any other checked-out
  branch -> PENDING_MERGE. Per-gate timeout 900 s (the loop's own suite took 315-398 s on the loaded host).
- **Gate:** `python tools/test_self_improve_unattended.py` -> 52/52 (5 mutation drills). Real cycles
  2026-11-22: 39-41 candidates / 188-191 sessions observed; apply and rectify gates refused at 9.2-14.4% free RAM.
  The live agent + merge path has NOT yet run on the real repo: its first real apply needs >= 20% free RAM.

# Self-improve, fully autonomous: apply, verify, rectify, tune itself

Owner, 2026-11-22: "necesito que sea self-improvement autonomo" -> "deberia ser 100% autonomo y rectificar si hay
alguna que ha aceptado y ha sido contraproducente y mejorarse a si mismo". Supersedes the "propose, Owner merges"
draft of the same day. The Owner is informed, never asked.

## Daily loop (`PP-SelfImprove`, 04:30, after compound 02:30 and self-eval 03:30)

1. **Observe** (deterministic). `analyze_transcripts.py --all-projects --days 1 --json` -> local snapshot
   `~/.claude/state/self-improve/<date>.json`. Candidates keyed `kind+subject`, rate per session (not raw count),
   classed NEW / RISING / STEADY / FALLING / RESOLVED against a 7-day baseline.
2. **Rectify first** (deterministic; before any new change). For every APPLIED change:
   - its gate or the regression block is RED -> `git revert` now (reason `REGRESSED_GATE`);
   - after >= 3 days and >= 10 sessions in scope, its target rate is >= 1.5x baseline and +5 absolute -> revert
     (`COUNTERPRODUCTIVE`); rate fell below 0.7x -> `VALIDATED`; otherwise keep measuring to day 14, then `NO_EFFECT`
     (kept, noted). A reverted key is not retried with the same approach; a second revert on a key retires it.
3. **Apply** (model, at most 1 per day). Top eligible candidate -> `claude -p` in a NEW worktree on `si/<date>-<slug>`:
   failing test first, fix, the candidate's gate. The DRIVER then re-runs that gate AND the regression block in the
   worktree. Both green -> merge into the main checkout's current branch (refused, and retried next day, if any
   touched path is dirty there: other panes' work is never overwritten). Red or no diff -> worktree discarded,
   reason recorded.
4. **Improve itself** (deterministic). Its own track record (applied, validated, reverted, red, no-effect, cost)
   tunes its own parameters in `vault/self_improve/params.json`, inside fixed bounds: ranking weights, the minimum
   score, the measurement window, which kinds it attempts (a kind with >= 2 reverts and 0 validations is benched for
   30 days). Its own non-core code (ranking, trend, prompt, reporting) is an eligible target like any other file.
5. **Report.** SessionStart line + `/self-improve` (what was applied, validated, reverted, and why). Push stays the
   ovo-push-gate's decision.

## The fixed core (the only thing it cannot change)

`tools/self_improve_guard.py` holds: the edit allowlist, the kill switch, the spend/RAM/lock admission, the
never-push/never-force rule, the rectify thresholds' floor, and the parameter bounds. The driver checks its sha256
against `vault/self_improve/guard.sha256` on every run and stops if they differ; every change to the guard is
outside its own allowlist. Reason: a loop that can rewrite its own brakes is unbounded, not autonomous, and the
mission constraint "No desactives controles de seguridad" stays in force.

## Eligibility (guard-enforced)

- target inside this repo under `tools/`, `hooks/` (non-blocking hooks only), `modules/`, `commands/`; never
  `~/.claude` live files, settings, `rules/`, HARD_RULES, sealed UKDL, governance, blocking guards/gates, the guard.
- kind code-fixable: not `host-stall`, not a correction awaiting `/ceps`.
- `model_spend_gate.refusal(...)` is None; host free RAM >= 20%; no compound/self-eval lock held.

## Never-do

never push, force or rebase; never edit the main checkout except by a merge of a green branch or a revert; the prompt
carries only structured candidate fields, never transcript excerpts (untrusted data, local only); receipts carry
counts and refs only; the agent's "done" is never evidence.

## Files

NEW `tools/self_improve_guard.py`, `tools/self_improve_unattended.py`, `tools/test_self_improve_unattended.py`
(V-SIU-*), `vault/self_improve/params.json`, `vault/self_improve/guard.sha256`, `commands/self-improve.md`
(+ live copy). Liveness: `SCHEDULED` in `vault/liveness/reachability_registry.json`.

## Acceptance (V-SIU-*, each negative gate with a mutation drill)

trend classes; rectify: red gate -> revert, counterproductive -> revert, validated kept, too-few-sessions waits;
second revert retires the key; host-stall / out-of-allowlist / guard-file target never eligible; tampered guard hash
-> stop; spend refusal / low RAM / held lock -> zero spawns; driver gate overrides an agent that claims success;
dirty touched path -> no merge; parameter tuning stays inside bounds; no excerpt in the prompt (canary); no push in
any spawned command; kill switch. Then ONE real `--once` run inspected before the task is registered.

## Rollback

`CPP_SELF_IMPROVE=off` (instant); `Unregister-ScheduledTask PP-SelfImprove`; each applied change is one merge commit,
revertible alone; all files are additive.
