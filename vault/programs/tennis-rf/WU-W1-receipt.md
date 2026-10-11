# WU-W1 receipt

Status: DONE

The worker (m-a2577ad5897d, renewal of m-5d849041fbec) did the work but wrote this receipt into
`wt_tennis_rf/RESUMPTION_FILE.md`, not here. The coordinator moved it here after re-running the
new gate.

- Commit: `fa8aaf0` in `C:\Users\User\Apps\recon_work\wt_tennis_rf` (8 files, +254/-8).
- Invariant: CURRENT_CAPSULE must equal capsule X at send time. `stage.send` refuses with
  CAPSULE_NOT_CURRENT (exit 16) before any job is created.
- Source lint (`source_lint.py`) is wired into `candidate.build_units`. Custody verdicts get their
  own miss class. Stderr keeps 2 KB head + 2 KB tail.
- Step 5 gate: a fresh worktree with `core.autocrlf=true` checked `.ksr_vault` out as CRLF, and the
  hook hashes worktree bytes against LF snapshots. Fixed with `.gitattributes`
  `.ksr_vault/** text eol=lf`. The commit passed the hook without `--no-verify`.
- Root cause: `vault/programs/tennis-rf/ROOT-CAUSE-C2B.md`.

## Tests

| Suite | Result | Source |
|---|---|---|
| `test_fanout_preconditions` | 29/29 | Re-run by the coordinator, 2026-10-11 11:2x, git on PATH (the EOL gate shells out to `git`). |
| `test_custody` | 69/69 | Worker |
| `test_reproduce` | 56/56 | Worker |
| Mutation drill | 5/5 mutants RED | Worker |

- `test_candidate` (worker): 39 PASS, 2 FAIL (V-CAND-OPERANDS-NORMALISED, V-SDA-PRECHECK-REAL),
  plus a crash on a missing 03-CONTEXT.md. The worker reports the same result on clean `3c86ae2`,
  so these failures were already there.
- `test_arm_a.py` does not exist.

## Limits

- Without git on PATH, `V-VAULT-EOL-PINNED-LF` fails instead of skipping. It never passes falsely.
