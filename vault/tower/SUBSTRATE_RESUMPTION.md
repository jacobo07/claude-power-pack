# RESUMPTION — Constitutive Baseline Substrate (Power Pack side)

Repo: claude-power-pack · Worktree `C:\Users\User\Apps\pp-cbr-wt` · Branch
`tower/constitutive-substrate` · Base `6fdf032` (live `feature/knowledge-acquisition`;
`modules/tower` exists on no other branch, `main` included). Read this, then continue at
the first unsealed wave.

## Thesis
The ratchet already has an owner (`modules/tower/baselines.py`, spec
`docs/superpowers/specs/2026-09-24-family-baselines-design.md`), but only slices S1–S3
were live: no working promote/revert, no runnable checks, no injection bound, no
done-gate. This branch finishes the substrate so KobiiCraft's executor pane
(`kc-diffint-wt`, its W14 "constitutional ratchet") has something real to promote into.
It writes NO real generation: rule content belongs to W14 and to the Owner.

## Scope boundary (Owner ruling 2026-09-25)
`kc-diffint-wt` (branch `kseip/diff-integrity-v1`) owns the whole SkyParty programme,
W0–W14. This pane: Power Pack machinery P0–P7 only, report-only, no production writes,
no edits to `gsd_x/goal`, `kseip/goal-spine`, `fusion_*`, or any KobiiCraft file.

## SEALED
| commit | wave | what is now true |
|---|---|---|
| `9a8b243` | P1 | generation publish is create-if-absent (private temp + `os.link`); a positioned two-writer race had BOTH report success and one generation vanish. 16/16, drill caught. |
| `fe3530b` | P2 | `modules/tower/checks.py` grammar: file/glob/regex evaluated (only kinds that can PASS); registry/test DELEGATED; prose/empty named; instrument failures separate. 22/22, 3 drills. Real B0s: 60 entries, 31 prose, 29 empty, 0 runnable. |
| `24d851b` | P3 | `modules/tower/select.py`: deterministic bounded injection, nothing lost, every deferred entry named. 15/15, 3 drills. |
| `e2f642a` | P4 | `ratchet.py` promote/revert/verify_chain + CLI review/verify/revert; parent SHA anchoring (TAMPERED); duplicate ids refused. Code-review HIGH (same-rung check swap) folded in as CHECK_CHANGED. 21/21, 6 drills. |
| `27fd70d` | P4 | glob hits confined by realpath (junction escape). 23/23, drill caught a real escape. |
| `df524e0` | P5+P6 | `donegate.py` report-only S6: per-entry verdicts stamped `judged_under` + SHA-256, deferred entries still judged. Severing drill: finding vanishes and would_block flips True->False. 10/10, 4 drills. |
| (this) | P7 | `vault/tower/HANDOFF_W14_CONSTITUTIVE.md`: substrate API, narrowed C1–C7, corrections, goal-spine contract, 3 spec readings for the Owner. |

**STATUS: COMPLETE, MERGED** as `a85a009` into `feature/knowledge-acquisition` on
2026-09-25 (Owner-approved). Post-merge on the live checkout: 8 tower suites green
(121 gates), 4 family chains OK, dirty-path set identical before/after (491, 0 moved).

## MEASURED FACTS
- The prose checks are mostly repo-generic (placeholders, "grep for…"). A family entry
  cannot name one repo's path, so converting them would be invention. The runner reports
  them UNRUNNABLE_PROSE; that is the honest state, not a bug to paper over.
- `class` C|D is undefined in the spec (9 of 60 entries are C). Not used for ranking.
- Spec reading taken in P3 (Owner to confirm): the 8/1,400 ceiling bounds the prompt,
  not the constitution; the done-gate judges every applicable entry.

## NEXT
1. Owner decides the merge into `feature/knowledge-acquisition` (bracket the live
   checkout's dirty-path set before and after; none of its 492 dirty paths touched
   `modules/tower`, `tools/family_baseline.py` or `vault/tower` at 2026-09-25).
2. Relay `HANDOFF_W14_CONSTITUTIVE.md` to `kc-diffint-wt` before it starts W9/W12/W14.
3. Owner confirms or rejects the 3 spec readings (HANDOFF §5).

## NOT PROVEN
No real generation was written (B0s untouched). No goal has consumed the done-gate
(goal-spine is unmerged and not edited here). Only the synthetic web fixture and the
real kobiicraft_mode B0 were judged. The newest generation has no child to anchor it.

## Harness
`python tools/test_<name>.py` from the worktree root (PowerShell, absolute python.exe).
Drills: session scratchpad `mutate.py <file> <old.txt> <new.txt> <test> <expect>`;
exit 0 = caught + SHA-256 restore verified, 1 = survived, 2 = harness failed.
