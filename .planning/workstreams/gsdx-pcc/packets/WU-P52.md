# WU-P52 -- GSD X PCC wave 5.2 (trust core): N01 N02 N05 N16 N17 N19 D11 N23 + done-gate registry: PLAN, then EXECUTE, then compile WU-P6

Mission: the id on your rehydration card (write it in the receipt). Follows WU-P51 (Phase 5 closed, cross-platform; see `packets/WU-P51-receipt.md`).
Authority: Owner, 2026-10-14 chat, "Aprobar 175M" for `.planning/workstreams/gsdx-pcc/CONTINUATION-PLAN-2026-10-14.md` (the plan of record).
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.

## Never
- Write the main checkout `C:\Users\User\.claude\skills\claude-power-pack`, `io-chatgpt-plugin`, `io-ucg`, or anything
  under `C:\Users\User\.claude`. Never push. Never arm a mission. Never ssh to another host.
- Start wave 6 / Phase 6 work. Your successor is armed by the chain from the packet YOU compile (Part C).
- Run `/gsd-discuss-phase` or end a turn on a question. A decision reserved to the Owner goes into STATE.md as
  `OWNER DECISION NEEDED` (question, options, your pick); then continue with other runnable work.
- Weaken a gate, mark UNKNOWN as PASS, let a builder certify its own work, drop a red branch to save calls, or label
  Linux evidence as portability evidence (portability = the same claim observed on two planes against the same `modules/` tree).
- Run `tools/test_gsd_x_goal_mutation.py` on the laptop. Use `tools/test_gsd_x_goal_mutation_hermetic.py` (it mutates a
  disposable copy and leaves the live tree sha-unchanged) or `tools/mutation_drill.py` (isolated copy + control).
  A drill killed for memory is NOT retried: mark it UNRUN, record it, and list it for the coordinator's Linux run.
- Re-litigate STATE.md Decisions or the resolved semantics of Phases 2-5 (their VERIFICATION files).

## Start (first 3 calls)
1. `node ~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set gsdx-pcc --raw --cwd .`
2. `git status --short; git log --oneline -5` (the repository wins over this packet).
3. Read CONTINUATION-PLAN-2026-10-14.md sections 2, 4, 5, 6, 7; DENOMINATOR.md; `phases/05-*/05-CROSS-PLATFORM.md`;
   STATE.md. Do not reread the 2111-line dataset end to end: open only the section numbers a row cites.
If `phases/05-2-*/` plans already exist, skip straight to the first plan with no SUMMARY.

## Scope (plan section 5, row 5.2) -- the whole of it, nothing from wave 6
- N01 revocation: a revoked authority keeps its certificate invalid with the certificate bytes UNCHANGED.
- N02 lineage: a certificate carries its derivation lineage.
- N05 authority monotonicity: inherited authority greater than the original is refused.
- N16 certificate forgery: at least 8 distinct forgery attacks, each refused (list them in the plan; each has a control that is admitted).
- N17 canonical environment equivalence: repair audit A4, `modules/gsd_x/goal/proof.py:347`. Environment drift invalidates.
- N19 platform vs portability semantics: PLATFORM = one plane, PORTABILITY = same claim on two planes with the same
  `modules/` tree. Make it a checked field of the certificate/receipt, not prose.
- D11 wiring (audit A2).
- N23 ledger seed.
- `tools/gsdx_pcc_done.py` as a question registry (plan section 7): the ~40 questions, each mapped to a V-gate id +
  evidence file + plane. It exits 1 while any question is OPEN, UNKNOWN, or single-plane where portability is claimed.
The trust core changes the certificate schema every later wave emits: one migration now, not five later.

## Inputs from WU-P51 you must account for
- The Linux liveness gate is RED and host-dependent: `python modules/liveness/reachability.py` is exit 0 on the laptop
  and exit 1 on GEX44 (2 offenders: `cognitive_os/hibernate_runner`, `session_resilience/snapshot_versioning`), because the
  scan seeds from the live `~/.claude` install. The done-gate registry and N19 must treat a green liveness as PLATFORM
  proof of the installed host, never portability proof. Do not declare those two modules in the registry to silence it.
- The Linux semantics run failed 2 gates (46/48) on a Windows-only `GIT_CANDIDATES[0]` in a TEST; fixed in `b30b3f88`.
  New tests you write must not index `GIT_CANDIDATES[0]`; use the first existing candidate.
- The coordinator runs the Linux leg of N17 (the env-equivalence pair) on GEX44; list exactly what to run in your receipt.

## Concurrent writers and the shared tree
Other sessions may write in the same checkout.
- Commit isolation is file-granular: pathspec commits take the whole file, so two writers in one file means one commit
  carries the other's hunks. Prefer NEW files; commit early; before committing a file you did not create, `git diff` it.
- The shared `.git/COMMIT_EDITMSG` race is NOT closed by pathspec: after every commit run `git log -1 --format=%s` and
  compare it with the first line of your message file; if it differs, `git commit --amend -F <msgfile>`.
- A repo-wide test, lint or type-check run is INCONCLUSIVE if the set of dirty paths moved during it. Bracket a wide run
  with `git status --short` before and after and say so in the log if it moved.
- Never rebase while a reviewer agent is reading the worktree.

## Part A -- plan (budget: finish by ~25 % of need, i.e. ~4.5M processed)
Write into `phases/05-2-trust-core/` (create it; the GSD phase id for this wave is `5.2`), committing each artifact as it lands
(the breaker refuses 25 calls without an edit or commit): `05-2-CONTEXT.md` (scope above; every gray area decided with a
one-line reason; the RED list verbatim from the Scope bullets), `05-2-RESEARCH.md` <= 25 KB (premise-verify every
function/module the plans touch with file:line, HR-PREMISE-001; reuse `proof.py`, the certificate and PCC event seams,
no new stores), 4-6 `05-2-0N-PLAN.md` (RED-first tasks, named gates, files, done criteria) and `05-2-VALIDATION.md`.
One `gsd-plan-checker` agent (Sonnet, solo in its message, bounded, "Prefer Read/Grep/Glob; avoid Bash, use PowerShell",
findings to `05-2-PLAN-CHECK.md`). Fix blockers in place; one iteration only.

## Part B -- execute
Plans in order, INLINE with PowerShell, RED first, ONE suite per call, logs under the phase dir, `05-2-0N-SUMMARY.md`,
commit by pathspec (`git add -- <paths>; git commit -F <msgfile> -- <paths>`, message file UTF-8 no BOM, ends with
`Co-Authored-By: Claude Sonnet <noreply@anthropic.com>`; verify `git log -1 --format=%s`). Update DENOMINATOR rows only
with evidence. Every drill: spec JSON under the phase dir `drills/`, run via `tools/mutation_drill.py`, one per call.
At the end re-run the Phase 2-5 suites once each (semantics 48/48, replay 28/28, frontier 40/40, invalidation 26/26,
judge_validate 11/11, hermetic 5/5) and `python modules/liveness/reachability.py` (exit 0 on the laptop; declare a new
test tool if the gate requires it). Then `05-2-VERIFICATION.md` (every gate labelled with its plane), STATE.md updated,
commit.

## Budget
Envelope `route-P52.json`: target 18M, warn 21M, stop 24M, 127 calls. The binding number is NOT the stop. Measured
2026-10-14: the goal-budget gate locks the session at its admitted need = calls x ~118K x 1.2 = 127 x 141.6K = **17.98M**.
Plan the work to fit 17.98M. **Write the receipt at ~80 % of need (~14.4M processed)**, whatever is unfinished, then
commit. At SESSION BUDGET warn: commit what is verified and go straight to Part C and the receipt. Read burn only from
`~/.claude/state/session-budget-<your sid>.state.json` (`tokens`, `calls`). Never `run_in_background` for a check you
need this turn; pass `timeout: 600000` on long PowerShell calls; never poll an output file.
Gap recorded: plan section 6 counts 150 calls for this wave; 127 is what the admission rule allows at the 18M target.
If the scope proves larger, do not overrun: mark the unfinished item PARTIAL in the receipt so the coordinator recompiles the remaining frontier.

## Done-gate for this unit (deterministic)
- Every named RED turns green: revoked authority stays invalid with unchanged bytes; inherited > original refused;
  >= 8 forgery attacks refused each with an admitted control; environment drift invalidates.
- `python tools/gsdx_pcc_done.py` exists, runs, and exits 1 while any question is OPEN/UNKNOWN/single-plane-portability
  (assert that it exits 1 today and that a seeded all-closed registry exits 0).
- `05-2-VERIFICATION.md` frontmatter `status: passed`, every `05-2-0N-SUMMARY.md` present, Phase 2-5 suites green.
- `git status --short` clean except `vault/progress.md` and `LEARNINGS_PENDING.md`.

## Receipt
Write `packets/WU-P52-receipt.md` (<= 25 lines). Line 2 is exactly `Status: DONE` or `Status: PARTIAL -- <blocker>`. Then:
mission id; plans with commit ids; gate lines verbatim with plane; DENOMINATOR rows moved; drills with verdict and plane;
items for the coordinator's Linux run; measured burn (tokens, calls, tokens/call) at end of Part A and at the end;
the WU-P6 route numbers and their derivation; open points. Commit it.

## Part C -- compile the successor (wave 6, W5 mutant farm)
Write `packets/WU-P6.md` and `packets/route-P6.json`, modelled exactly on this packet (Never list, Start, Scope, Inputs,
Concurrent writers, Part A plan, Part B execute, Budget, Done-gate, Receipt, Part C compile for wave 7).
- Scope = plan section 5 row 6: D18, D19, R04, R11 + N09 (farm level), N13 OBSERVE start, N14, N15, N18 (exec).
- Route: start from plan section 6 (target 21M, cutoff 29M, 175 calls). Re-derive with THIS unit's measured tokens/call:
  choose calls with calls x tokens/call x 1.2 <= target <= the plan cutoff, tell the WU-P6 worker to write its receipt at
  ~80 % of need, and record any gap to the plan's 175 calls. Never exceed the plan's cutoff.
- Route JSON shape: `{"unit":"gsdx-pcc-P6","envelope":{"target":T,"warn":W,"stop":S,"calls":C},"workers":[{"name":"gsdx-pcc-p6","profile":"top-level-worker","calls":C,"packet":7500}]}`.
- Successor duty: WU-P6's own Part C compiles WU-P7 the same way, and so on down the chain to WU-P11.
Commit both files. Then end with exactly one line:
`HANDOFF NOTE: WU-P52 done -- WU-P6 (mutant farm) compiled` or `HANDOFF NOTE: WU-P52 PARTIAL -- <next plan id> -- <blocker>`.
After that commit, end the session: no further work in this unit.
