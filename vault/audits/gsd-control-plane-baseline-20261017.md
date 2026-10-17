---
covers: [gsd-control-plane, epoch-amplification, continuation-race, economic-ledger, two-builders-tb-full]
status: BEFORE-BASELINE + first root cause (2026-10-17, pane dc5a2a29). Numbers are measured on GEX44 unless marked.
---
# GSD X control plane: before-baseline and the continuation race

Subject: Ralph mission `m-80fd126a23cc` (Two Builders TB-FULL), 16:09-19:01 UTC 2026-10-17, GEX44 PP install code_id 7688c481f358.
Accounting unit: processed tokens, `mission_spend._file_tokens` over every main + subagent transcript under
`~/.claude/projects/-home-kobii-missions-tb-m2*` modified after arming. Freshness: live file mtimes; PARTIAL (excludes the
planning pane on the laptop).

## Measured (before)
| Metric | Value | Source |
|---|---|---|
| Processed tokens, 2 h 25 min | 45.7M (main 34.3M, 7 subagent files 11.4M); 51.3M at 19:02 | `_file_tokens` |
| Epochs / fresh worker sessions | 8 / 7 | `gsd_epoch.py epochs` |
| Epoch start causes | LAUNCH_RETRY 1, CONTEXT_ROTATION 1, PROCESS_RECOVERY 1 (operator), CONTINUATION_FAILED 4 | same |
| Context at the first call of a main session | 84-87k tokens (subagent 58-60k) | transcripts |
| Calls per main session | 104, 60, 112, 45, 36, 15, 83 | transcripts |
| Mean processed tokens per main call | ~73k (cost = calls x context, the prefix is re-read every call) | derived |
| Bootstrap-only epochs | epoch 7: 0.9M, 15 calls, 42 s of work | transcript 426a939e |
| Verified product events in the window | P40-P43 (4 runs), CHG decoder+writer+350-file census, build receipt | git log |
| Owner decision delivery | blocked 17:00-17:07 on a question already answered; cleared only by commit + stop + supervise | ledger |

## Root cause of the epoch churn (CONFIRMED, reproduced)
`gsd_epoch.continue_worker` wakes the owner with `claude --bg --resume <full sid> <prompt>`, after `gsd_mission.stop_owner`.
The host lists an idle worker as `state: done`, `status: idle`, with NO pid. `stop_owner` read `done` as finished, skipped
`claude stop`, and returned "stopped; no pid to wait on". The resume then hit a session that was still alive and the host
answered: `session X is already running in the background, so this started a copy as Y`. The copy was stopped, the
continuation was logged `continuation_failed`, and 4 minutes later "start ack overdue" launched a FRESH worker (new 86k prefix,
state re-read). 4 of 7 continuations failed this way (ledger rows 50, 62, 81, 93); the other 3 succeeded when the stop happened to win.
Reproduction on GEX44 (claude 2.1.302): resume of an alive session -> copy; stop + 3 s + full id -> `woke session`.
Short 8-char id also forks a copy (CLI note), but PP passes the full id, so that was not the cause here.

Fix: PP `705218e0` (`stop_owner` treats `status in idle/busy/waiting` as running, stops it, waits until the host stops listing it;
injected stop runners never poll the real host). Mirrored to the GEX44 install (backup `gsd_mission.py.bak-stopowner-*`).
Proof: V-MC-STOP-IDLE-NOPID-STOPS-AND-WAITS, -UNRELEASED-REFUSES, V-MC-STOP-GONE-NOPID-NO-EXTRA-STOP (MC 233/233); real consumer:
3 x real stop + resume on GEX44, all `woke session`, 0 copies, host released in 1.5 s. The pid-less branch is unit-proven only.

## Falsified / corrected
- `gsd_mission.py status` is side-effect free (seq 66, epoch 8, 121 ledger rows identical before and after). Canary A green.
- `hold` is NOT "park without consequence": a held mission whose owner finishes its turn settles to terminal HALTED with the
  hold kept (`hold_settled`). Resuming means arming a new mission (m-7e268fc1a6d9 for TB-FULL). Hold only a mission you mean to end.
- `mission_dirs(work_dir=<worktree>)` returns [] when workers run in the main cwd: a work_dir meter is blind (matches the old
  "goal meter used=0"). Not yet fixed.
- Lean launch (measured, `claude -p`, haiku): default 68.5k; `--disable-slash-commands` 62.7k; `--setting-sources project,local`
  45.4k (-34%). That flag also drops user skills (`gsd-autonomous`) and the mission hooks, so it is not a drop-in; the floor is
  ~45k of system prompt + tools. Defer until a reprofile shows the prefix dominates.
- First-call composition (chars): skill listing 69k, agent listing 57k (95 agent files on GEX44), hook-injected context 21k,
  file attachment 14k, global CLAUDE.md 25k + rules 36k.

## Open
Owner decision as a durable mission event; one authoritative ledger with freshness + worktree-aware meter and cap enforcement;
operational events (gex44_jobs.jsonl) out of the source tree; claim-granular completion; Proof Horizon; worker-lifetime policy.
