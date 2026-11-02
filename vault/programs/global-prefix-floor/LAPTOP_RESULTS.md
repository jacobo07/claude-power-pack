# GPF-L2 laptop results (2026-11-02, plane DESKTOP-PMT5BS8, claude --model haiku, interactive ConPTY, PP root, CCR canary enforce)

## Why GPF-L2 was not applied as written
GPF-L2 (LAPTOP_STEPS.md) copied the GEX44-derived `global-CLAUDE.diet.md` over the laptop's `~/.claude/CLAUDE.md`. The two
source files differ on 140 lines. The laptop has sections GEX44 lacks: Windows Execution, Background Process Hygiene, the
Windows host probe. Copying would have deleted them. 3 of the 5 rules it stubs do not exist on the laptop (already skills, see
`skill-rule-index.md`). Instead, the diet was recompiled from the laptop's own file: `diet/global-CLAUDE.laptop.diet.md`
(19,289 -> 7,930 B; original in `diet/global-CLAUDE.laptop.original.md`). The 2 laptop rules (`common/code-review.md`,
`python/testing.md`) become 2-line stubs pointing at `~/.claude/skills/claude-power-pack/rules/...`.
Out of scope: the repo `CLAUDE.md`. Its laptop working copy (23,197 B) carries another pane's uncommitted edit, so the worker's
9,724 B version (a46ae9a3, GEX44) must not be landed over it until that edit is committed.

## Floor (call-1, N=4/arm, CTCT then TCTC) -> gpf-l2-laptop.json
control 78,236 / 78,231 / 78,530 / 78,571 (spread 0.43%) | diet 71,723 / 72,007 / 72,008 / 72,053
**delta -6,444 tokens per call-1 (-8.2%), MEASURED.**

## Quality (l6 Work Unit, 3 pairs CTC / TCT) -> gpf-l2-quality.json
correct C 3/3, T 3/3; page faults 0; repairs 0. processed/task: C 402,793 / 401,956 / 407,291; T 348,467 / 407,769 / 347,817
(mean -35,996, noisy: one T run took 8 calls).

## Applied live 2026-11-02 16:07 local
Backup `~/.claude/backups/gpf-apply-20261102T160717/` (CLAUDE.md, rules/common/code-review.md, rules/python/testing.md); the
live files were hash-checked equal to the measured original first. Post-apply live probe: call-1 **72,059** (gpf-l2-post-apply.json).
Revert: copy those three backup files back over `~/.claude/`.

## Driver defects fixed (Error -> Immunity)
1. `l5_canary_driver.run` / `l6.run` read the pty with a blocking `read()`: once the pane went quiet, the deadline was never
   checked (a probe hung 12 min). Fixed in l5 with a reader thread. GPF quality_run uses the same pattern.
2. Both found the probe's transcript as "newest transcript with the same cwd". With another pane active in the PP root
   (09664f88), that measures someone else's session. Fixed: `run(arm, session_id=True)` passes `--session-id` and reads that
   transcript only.
3. `l6_quality_driver.py` imports `p3_canary`, which no longer exists (vanished temp worktree,
   T-LAPTOP-TEMP-WORKTREE-FILES-VANISH-001). GPF aliases it to l5 (same three functions).

# GPF-L1 (ctx-rent-x Phase 4 successor smoke) -- 2026-11-02 ~16:15-16:31 local, live release, diet applied
Driver `gpf_successor_smoke.py`: predecessor pane (pinned sid, `--permission-mode plan`, isolated empty CPP_ROLLOVER_STATE_DIR)
-> "reply OK" -> `rollover.py seal` into that dir -> `/clear` -> `/kresume` in the same pane. Recompute from the session ids below
(transcripts under `~/.claude/projects/C--Users-User--claude-skills-claude-power-pack/`, receipts under `~/.claude/ccr/state/receipts/576459d4/`).

| run | CCR_MAIN_CANARY | predecessor | successor | seal | CCR receipts after /clear | frontier receipt |
|---|---|---|---|---|---|---|
| S1 | default (enforce) | eac88636 | 1698fe36 | capsule + latest pointer written; verdict REFUSED (test goal not registered, no /kclear handoff) | under the PREDECESSOR sid: `successor marker:true mode:"off" canary:"enforce"` | **none** |
| S2 | 0 | e2700fe9 | ffbb61ce | same | `end` at /clear, then **no receipt at all** for the successor | **none** |

**CR-11 / CR-14: FAIL (MEASURED, n=1 per arm), not UNKNOWN.** On the live release a `/clear` -> `/kresume` successor never
resolves the capsule frontier:
- canary on (the default since L8): `register.ts:124` sets `mode = canary === 'off' ? successorCanaryMode(...) : 'off'`. With
  the main canary enforcing, the successor mode is always off, so `successor` stays false and `resolveFrontier` (line 134)
  never runs. The L8 default-on flip structurally disabled the successor frontier path. Its L8 smoke checked start receipts
  only, so it could not see this.
- canary off: the plugin records `end` at /clear and nothing for the successor session (lifecycle cause not isolated).
- The other pane seen in the window (`fd4ffce8`, a real /kresume) shows the same `marker:true mode:"off"`: this hits real
  successors, not just the probe.
Also: after /clear the canary-on plugin keeps writing under the predecessor's sid, so any consumer that keys successor
receipts by the new transcript id finds nothing.

**CR-15 fresh-start cost: PARTIAL (MEASURED bootstrap, no correct resume).** Successor call-1 75,239 (S1) / 75,844 (S2);
/kresume turn 2 calls 150,770 processed (S1) / 3 calls 232,175 (S2); 0 Reads, 0 rereads, 0 page faults. Both successors
correctly refused the test capsule ("no resumable capsule"), so time-to-first-correct-action is unmeasured. That needs a real
/kclear-sealed capsule.
**CR-16, CR-29:** blocked by the frontier defect (breakeven inputs and fresh-agent recovery both need a working frontier).
**CR-09 / CR-10 / CR-13 (Phase 5 Safe-to-Forget in main):** not a measurement gap. `register.ts` projectShell enforces only
in Work Unit sessions and shadows in main; the Phase 5 extension to main was never built. These stay UNKNOWN as UNBUILT.

## Fix attempt 2026-11-02 16:42 -> ROLLED BACK 16:51 (HR-2: no green smoke)
Commit 83069706: `policy.successorMode` (a successor activates under the main canary and keeps its mode) plus
`register.ts` restoring the launch canary at /clear. plugin test 29/0 (was 28/0); mutation drill with the old gate -> 28/1,
killed; test_ccr_release 24/24. Released `0.1.0-39151f03` (source_commit 83069706).
Smoke S3 (predecessor 6988bac6, successor 1a16ffc5): start receipt `releaseId 0.1.0-39151f03 canary enforce`, then `end` at /clear
and **no receipt of any kind** for the successor conversation, in any receipt file; the successor transcript carries no capsule
text. The fix is therefore UNPROVEN live, and HR-2 forbids leaving it active: `ccr_release.py rollback` -> active
`0.1.0-265d3d55` (source e8d29ffb) at 16:51:16. Panes launched 16:42-16:51 keep 39151f03 until they restart.
~~New open defect: plugin silent after /clear~~ **RETRACTED (harness artifact, not a CCR defect).** Diagnosed with
`--debug-file` (S4): after /clear the plugin received `prompt.attachment` x19 (so the successor decision ran and its receipts were
buffered), but no `turn.complete` or `session.end`, so the buffer was never flushed. Cause: the probe ran `--permission-mode plan`.
The successor called `ExitPlanMode` at 17:46:11, and the dialog held the turn open. At the 360 s timeout the driver typed
`/exit`+Enter **into that dialog, approving the plan** (17:51:44; the model then ran `rollover.py resume`, exit 4, nothing claimed),
and the pane was terminated 15 s later, before any flush. S1 was fast only because its successor never called ExitPlanMode.
Harness fixed: no plan mode (`auto` + `--disallowedTools Write Edit NotebookEdit`), `/exit` typed only after `end_turn`, receipts
read after exit.

## Clean A/B with the fixed harness (2026-11-02 18:55-18:58) -> fix RE-RELEASED and KEPT LIVE
| run | release | after /clear -> /kresume | frontier receipt |
|---|---|---|---|
| S5 | 0.1.0-265d3d55 (old, e8d29ffb) | `successor marker:true mode:"off" canary:"enforce"` | **none** |
| S6 | 0.1.0-39151f03 (fix, 83069706) | `successor marker:true mode:"enforce" canary:"enforce"` | **`basis:"capsule"`**, sha 60b039fb..., 33 bytes |
Both turns completed (19 s / 31 s), successor call-1 73,734 / 73,660, 2 calls each, 0 rereads.
**HR-2: green smoke from the same commit -> 0.1.0-39151f03 stays active** (released 18:57:05; the rollback path was exercised
for real at 16:51). **CR-11 / CR-14: PASS (MEASURED, n=1 per arm, clean A/B).** CR-15: bootstrap measured (~73.7K call-1, 2 calls,
~148K processed per /kresume turn); time-to-first-correct-action still needs a real /kclear-sealed capsule (the test capsule is
REFUSED by design, so the successor correctly stops). CR-16, CR-29: unblocked, not yet run.

## CR-29 / CR-15 real /kclear probe (2026-11-02, laptop, `gpf_cr29_kclear.py`, receipts `gpf-cr29.json`)
K1, K2, K3 all **ABORTED SAFELY at the folder-trust dialog** before any prompt was typed. K3 recorded the raw screen: "Yes, I
trust this folder" with default "No, exit", so the dialog is real, not a false match. Trust is not inherited from the trusted
`%TEMP%` entry. The agent-side fix (merge `hasTrustDialogAccepted` into `~/.claude.json`) was **DENIED by the auto-mode
classifier (Self-Modification)**. That is the HR-001 class, so it was not worked around. Shipped in 90eb6263: the driver reuses a fixed,
marker-gated root `%TEMP%/gpf-cr29-probe` once trusted, and `gpf_cr29_owner_trust.py` is the Owner-run half.
**CR-29, CR-15 (time-to-first-correct-action): UNKNOWN, Owner gate.** `done_gate.py` now reads CR-11/14/15/29 from these
receipt files (latest measured run decides; aborted runs stay UNKNOWN), drilled at both poles (`tools/test_done_gate.py` 19/19).
### K4 (Owner trusted `%TEMP%/gpf-cr29-probe`, 2026-11-02 19:27; run 18:28-18:31 UTC)
Real /kclear -> /clear -> /kresume, fresh successor 7aa6cd09, no predecessor transcript. Ledger: `reset_gate SAFE_TO_FORGET`,
`successor_claimed refresh=CONTINUE`, 3x `resume_failed wrong=[next]`, then `resume_certified`.
**CR-29: PASS (MEASURED, n=1).** done.txt == `RESUMED-K4-6186fd` (the exact token). **CR-15: PASS (MEASURED, n=1).** 91 s
from /kresume to the correct file. Successor call-1 62,073, 12 calls, 813,369 processed, 4 Reads, 1 reread, 0 page faults.
Findings (open debt, n=1):
- **Lossy capsule obligation.** The predecessor's handoff paraphrased the goal, and the sealed obligation reads "...with the
  RESUMED-K4 token": it dropped the `-6186fd` suffix and added an "Owner go-ahead" the goal file never asked for. The certify
  exam keys `next` on that paraphrase, so the successor failed it 3 times. It recovered only because the capsule also points
  at the goal file, which it read and followed. The goal pointer did the recovery; the obligation text was a hazard.
- **Frontier basis `unreadable`** on a real /kclear capsule, against `capsule` for the synthetic S6 capsule. CR-11 is PASS
  only on the synthetic path, and the real path needs its own investigation (CCR `register.ts` frontier reader vs the
  /kclear capsule schema).
- **Instrument fixed:** the driver read the verdict from `final[-300:]`, which had cut it to `_TO_FORGET`. It now reads
  `ledger_facts()` from the isolated ledger. K4's ledger fields were backfilled from its own `state_dir` and labelled.
### K5 -- both capsule fixes live (2026-11-02, same trusted root, working-tree tools)
Fixes (CCR_CAPSULE_DEFECTS_SCOPE.md): `session_checkpoint.seal_capsule` now writes `latest/<repo-key>.json`, and `compile_capsule`
lets a NAMED goal file's verbatim Next items win over the /kclear model summary (kept as `obligations_stated`).
Gates: `tools/test_rollover_obligations.py` 8/8; on HEAD code 6 FAIL + 2 controls PASS (red pole proven). 24 rollover/kresume/
capsule suites green except 2 that fail identically on HEAD/host state (V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT, V-HUB-REGISTERED).
Review (pp-code-reviewer): APPROVE, one LOW design note (a stale named goal file now beats an accurate pending list; intended).
| | K4 (before) | K5 (fixed) |
|---|---|---|
| failed certify attempts | 3 (`wrong=[next]`) | **0** |
| frontier receipt | `unreadable`, capsule/sha null | **`capsule`**, sha 46b9b6dc... |
| seconds to correct done.txt | 91 | **51** |
| successor calls / processed | 12 / 813,369 | **6 / 378,691 (-53%)** |
**CR-29 PASS, CR-15 PASS 51 s (MEASURED, n=1).** CR-11 now also holds on a real /kclear capsule, not only the synthetic one.