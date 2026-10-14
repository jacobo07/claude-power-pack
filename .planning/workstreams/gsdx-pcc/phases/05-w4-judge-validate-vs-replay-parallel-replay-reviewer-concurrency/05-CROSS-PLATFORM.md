---
phase: 5
workstream: gsdx-pcc
status: CLOSED
closed: 2026-10-14
---

# Phase 5 cross-platform closure (wave 5.1)

PLATFORM proof = observed on one plane; says nothing about the other. PORTABILITY proof = the same claim observed
on two planes against the same candidate content. Candidate content here is the `modules/` tree: git tree
`dd6c4ba3` at both `46d470e1` (Linux leg) and `fdc0c18b` (Windows legs of 5.1). `git diff 46d470e1 HEAD -- modules`
is empty; only `tools/` changed (the hermetic gate and the suite's copy wrapper).

Toolchains: **Windows** = Windows 11 10.0.26200, Python 3.12.10, laptop (hermetic temp roots / disposable copies).
**Linux** = GEX44, Linux 6.8.0-134, Python 3.12.3, git 2.43.0, disposable clone `~/missions/pcc-p5-linux` at
`46d470e1` (log `logs/05-linux-gex44.log`, coordinator 7c5ac907).

| Claim | Windows observation | Linux observation | Proof kind | Reason |
|---|---|---|---|---|
| D15 judge VALIDATE re-derives (`GSDX_JUDGE_VALIDATE_PASS=11/11`) | 970ea212 / 73179700 `logs/05-01-green.log` | not run | PLATFORM (Windows) | one plane |
| D15 drill d1, d2 | KILLED, isolated copy, control valid | not run | PLATFORM (Windows) | one plane |
| D15 drill d3 (`V-JV-WEAKENED-GATE-REFUSED`) | KILLED at fdc0c18b, `logs/05-51-d3-windows.log` (first try at 970ea212 was reaped, UNRUN) | KILLED at 46d470e1, `logs/05-linux-gex44.log`, control valid | **PORTABILITY** | two planes, same `modules/` tree, same drill spec and gate |
| D16 parallel replay (`GSDX_REPLAY_PARALLEL_PASS=14/14`), d4, d5 | 0f1b2aba, KILLED | not run | PLATFORM (Windows) | one plane; parallelism is scheduler-dependent, so not inferable |
| D17 reviewer concurrency (`GSDX_REVIEW_PASS=12/12`), d8-d10 | 73179700, KILLED | not run | PLATFORM (Windows) | one plane |
| R05 A->B->A (`EVB_ABA_PASS=10/10`), d6, d7 | 8e62abdb, KILLED | not run | PLATFORM (Windows) | one plane; the stat journal's mtime/inode behaviour is filesystem-specific (known residual limit) |
| Goal mutation suite, 58 mutants | 58/58 CAUGHT in a disposable copy at fdc0c18b, live sha unchanged: `GSDX_MUTATION_HERMETIC_PASS=5/5` (`logs/05-51-hermetic-GREEN.log`) | 58/58 CAUGHT at 46d470e1 (in-place suite inside a disposable clone) | **PORTABILITY** for the mutant verdicts (same `modules/` tree, same 58 anchors); the *entry point* differs (Windows ran the new copy wrapper, Linux the old in-place suite) and is not claimed portable | two planes, identical mutated tree |
| Goal mutation suite hermetic (A7) | `GSDX_MUTATION_HERMETIC_PASS=5/5`; RED was 3/5 (`logs/05-51-hermetic-RED.log`) | not run | PLATFORM (Windows) | the hard-kill leg is `taskkill /T /F`; the POSIX `killpg` branch is unexercised |
| Phases 2-4 regression suites, semantics (`GSDX_PCC_SEMANTICS_PASS`) | 48/48 | **46/48 first, then 48/48** after a test-side fix: `V-PCC-EXPORT-RESTORE-ROUNDTRIP` and `V-PCC-ADDITIVE-ONLY` raised `FileNotFoundError: C:\Program Files\Git\cmd\git.exe` because the test indexed `GIT_CANDIDATES[0]`; the product `_git` falls back to `git`. Test now picks the first existing candidate (`_usable_git`), assertions unchanged. `logs/05-51-linux-pcc_semantics.log` | PORTABILITY (after fix) | two planes, same `modules/` tree; the Windows run predates the test edit, but the edit selects the same executable there |
| replay (`GSDX_PCC_REPLAY_PASS`) | 28/28 | 28/28 `logs/05-51-linux-pcc_replay.log` | PORTABILITY | two planes, same tree |
| frontier (`GSDX_FRONTIER_PASS`) | 40/40 | 40/40 `logs/05-51-linux-frontier.log` | PORTABILITY | two planes, same tree |
| invalidation (`GSDX_INVALIDATION_PASS`) | 26/26 | 26/26 `logs/05-51-linux-invalidation.log` | PORTABILITY | two planes, same tree |
| judge validate (`GSDX_JUDGE_VALIDATE_PASS`) | 11/11 | 11/11 `logs/05-51-linux-judge_validate.log` | PORTABILITY | two planes, same tree |
| Hermetic gate POSIX kill leg (`GSDX_MUTATION_HERMETIC_PASS`) | 5/5 (`taskkill /T /F` leg) | 5/5, hard kill via `os.killpg(SIGKILL)` at 21.1 s, entry tree byte-identical, 58/58 CAUGHT in the copy (`logs/05-51-linux-mutation_hermetic.log`) | PORTABILITY of the gate's outcome; each plane exercised its own kill branch | two planes, same gate, different kill mechanism by design |
| Liveness (`modules/liveness/reachability.py`) | exit 0, REACHABLE 312, offenders 0 (`logs/05-05-liveness-green.log`) | **exit 1**, REACHABLE 310, offenders 2: `cognitive_os/hibernate_runner`, `session_resilience/snapshot_versioning` (`logs/05-51-linux-liveness.log`). Same result at HEAD with the WU-P51 edits stashed | NOT PORTABLE (RED on Linux) | the scan seeds from the live `~/.claude` install; GEX44's install has no reference to either module (grep of hooks/settings/commands is empty), so the 2-module gap matches the 312 vs 310 difference. Not declared in the registry: that would assert a status the laptop does not have. Carried to N19 |

## Not claimed
No Phase 5 claim other than d3 and the mutation verdicts is portability evidence. Linux evidence is never relabelled
as Windows evidence or the reverse. The Linux mutation run used the pre-A7 in-place suite; it is valid evidence about
the 58 mutants, not about the hermetic wrapper.

## Findings from the Linux regression pass
1. **Semantics suite was not Linux-clean** (test-side Windows-ism, fixed, see the row above). Product code was already portable.
2. **Liveness gate is host-dependent**: exit 0 on the laptop, exit 1 on GEX44, for the same repo content. Root cause is inferred from the seed logic (`reachability.py`, `_is_installed_root`) and the grep above, not from the laptop's hook files, which are not on this host. It means a green liveness gate is PLATFORM proof of the installed laptop, never portability proof.

## Disposition
Phase 5 status: **CLOSED** (Windows plane complete; Linux plane: d3 and the 58-mutant verdicts; the rest named above
as single-plane). The open Linux gaps (D16, D17, R05, D15 gates) are carried to wave 5.2's N19 platform-vs-portability
semantics rather than silently promoted.
