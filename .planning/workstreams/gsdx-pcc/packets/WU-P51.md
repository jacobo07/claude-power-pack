# WU-P51 -- GSD X PCC wave 5.1: close Phase 5 cross-platform, make the goal mutation suite hermetic, compile WU-P52

Mission: the id on your rehydration card (write it in the receipt). Follows m-ee676522b2fd (Phase 5, 46d470e1).
Authority: Owner, 2026-10-14 chat, "Aprobar 175M" for the PCC continuation plan
`.planning/workstreams/gsdx-pcc/CONTINUATION-PLAN-2026-10-14.md` (read it: it is the campaign's plan of record).
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.

## Already done by the coordinator (do not redo)
`d057770f`: Linux plane (GEX44, Linux 6.8, Python 3.12.3), clone at 46d470e1. d3 MUTANT KILLED (control valid).
`tools/test_gsd_x_goal_mutation.py` 58/58 in 70 s, disposable clone left clean.
Log: `phases/05-*/logs/05-linux-gex44.log`.

## Never
- Write the main checkout `C:\Users\User\.claude\skills\claude-power-pack`, `io-chatgpt-plugin`, `io-ucg`, or anything
  under `C:\Users\User\.claude`. Never push. Never arm a mission. Never ssh to another host.
- Start Phase 6 / wave 5.2 work. Your successor is armed by the chain from the packet YOU compile (Part C).
- Run `/gsd-discuss-phase` or end a turn on a question. A decision reserved to the Owner goes into STATE.md as
  `OWNER DECISION NEEDED` (question, options, your pick); then continue with other runnable work.
- Weaken a gate, mark UNKNOWN as PASS, or label Linux evidence as portability evidence.
- Run the CURRENT `tools/test_gsd_x_goal_mutation.py` on this laptop. It mutates LIVE files, and a kill left
  `judge.py` mutated in Phase 4.

## Start (first 3 calls)
1. `node ~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set gsdx-pcc --raw --cwd .`
2. `git status --short; git log --oneline -5` (the repository wins over this packet).
3. Read CONTINUATION-PLAN-2026-10-14.md sections 2, 5, 6 and 7; `tools/test_gsd_x_goal_mutation.py:360-530`;
   `tools/mutation_drill.py`; `tools/gsdx_reality_baseline.py` (its `--in-copy` path).

## Part A -- hermetic goal mutation suite (audit A7)
Goal: the same 58 mutants, the same anchors, the same gates, the same outcome vocabulary (CAUGHT / INVALID / ...).
The suite must mutate a disposable copy of the candidate, never the live tree.
1. RED first: write `tools/test_gsd_x_goal_mutation_hermetic.py` (summary line `GSDX_MUTATION_HERMETIC_PASS=n/m`). It
   records sha256 of every live target before and after, and simulates an interrupted run (kill the child mid-mutant).
   Today's suite must FAIL it: the live target moves, or depends on the journal restore. Commit the RED log.
2. Fix with the smallest change that reuses existing substrate (mutation_drill's isolated copy, or
   gsdx_reality_baseline's in-copy runner). Do not build a third copy mechanism. Keep the journal/restore path only
   if the copy still needs it, and say why in the SUMMARY.
3. GREEN: the hermetic suite passes. The ported mutation suite reads 58/58 on this laptop IN A COPY, live sha
   unchanged. If RAM kills the run, mark it UNRUN, do not retry it, and record it. The Linux 58/58 already exists.
4. UKDL: evaluate a Trap/Process rule ("a mutation suite that edits the live tree and restores it is one kill away
   from shipping a mutant"). Add it to `vault/knowledge_base/ukdl-universal.md` in THIS worktree if it is not
   already covered (grep first).

## Part B -- Phase 5 cross-platform closure receipt
Write `phases/05-*/05-CROSS-PLATFORM.md`: one row per Phase 5 claim (D15, D16, D17, R05, drills d1-d10, goal
mutation suite). Each row gives plane(s) observed, candidate, toolchain, and whether it is PLATFORM proof or
PORTABILITY proof, with the reason. d3 may be re-attempted ONCE on the laptop (one call, `tools/mutation_drill.py`,
isolated copy) if free RAM >= 4 GB. If it is killed, keep it Linux-only and do not retry.
Update DENOMINATOR D15 evidence and STATE.md: Phase 5 status = CLOSED, with planes named.

## Part C -- compile the successor (wave 5.2, trust core)
Write `packets/WU-P52.md` and `packets/route-P52.json`, modelled exactly on this packet and on `WU-P5.md`:
Never list, Start, Part A plan (PLAN MODE: CONTEXT, RESEARCH <= 25 KB, 4-6 PLANs, one gsd-plan-checker), Part B
execute, Budget, Done-gate, Receipt, Part C successor compile for wave 6.
- Scope = plan section 5, row 5.2: N01 revocation, N02 lineage, N05 authority monotonicity, N16 certificate forgery
  (>= 8 attacks), N17 canonical environment equivalence (repair audit A4, `proof.py:347`), N19 platform vs
  portability semantics, D11 wiring (audit A2), N23 ledger seed. Plus `tools/gsdx_pcc_done.py` as a question
  registry (plan section 7) that exits 1 while any question is OPEN.
- Successor duty: WU-P52's own Part C compiles WU-P6 the same way, and so on down the chain to WU-P11.
- Route: start from plan section 6 (target 18M, stop 24M, 150 calls). Re-derive with THIS unit's measured
  tokens/call (`~/.claude/state/session-budget-<sid>.state.json`). calls x measured per-call must be <= target.
  Never exceed the plan's cutoff; if the derivation needs more, cap at the cutoff and record the gap in the receipt.
- Route JSON shape: `{"unit":"gsdx-pcc-P52","envelope":{"target":T,"warn":W,"stop":S,"calls":C},"workers":[{"name":"gsdx-pcc-p52","profile":"top-level-worker","calls":C,"packet":7500}]}`.
Commit both files.

## Execution rules
INLINE with PowerShell. One suite per call; logs under the phase dir. Commit by pathspec
(`git add -- <paths>; git commit -F <msgfile> -- <paths>`, message file UTF-8 no BOM, ends with
`Co-Authored-By: Claude Sonnet <noreply@anthropic.com>`; verify `git log -1 --format=%s`).
Liveness: `python modules/liveness/reachability.py` exit 0 at the end (declare a new test tool if the gate requires it).

## Budget
Envelope `route-P51.json`: target 5.5M, warn 6.3M, stop 7M, 45 calls. At SESSION BUDGET warn: commit what is
verified, then go straight to Part C and the receipt. Read burn only from
`~/.claude/state/session-budget-<your sid>.state.json`. Never `run_in_background` for a check you need this turn.
Pass `timeout: 600000` on long PowerShell calls.

## Done-gate for this unit (deterministic)
- `GSDX_MUTATION_HERMETIC_PASS=n/n` in a committed log.
- `05-CROSS-PLATFORM.md` committed.
- `packets/WU-P52.md` and `packets/route-P52.json` committed.
- Phase 2-5 suites still green: semantics 48/48, replay 28/28, frontier 40/40, invalidation 26/26, judge_validate
  11/11. Run each once at the end.
- `git status --short` clean except `vault/progress.md` and `LEARNINGS_PENDING.md`.

## Receipt
Write `packets/WU-P51-receipt.md` (<= 25 lines). The first line after the title is `Status: DONE` (or
`Status: PARTIAL -- <blocker>`). Then: mission id; commits; gate lines verbatim with plane; DENOMINATOR rows moved;
measured burn (tokens, calls, tokens/call); the WU-P52 route numbers and how they were derived; open points.
Commit it. End with exactly one line:
`HANDOFF NOTE: WU-P51 done -- WU-P52 (trust core) compiled` or `HANDOFF NOTE: WU-P51 PARTIAL -- <blocker>`.
After that commit, end the session.
</content>
</invoke>
