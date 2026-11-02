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
