# Unit U1 — packet-builder credential-content false positive (backlog D33 item 2)

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Background
`vault/programs/cognitive-economy/gen2/evidence/tranche/S5-receipt.md` (lines 3-4, 23, 46) records that the vendored
packet builder BLOCKED `tools/floor_regression_gate.py`, `tools/test_floor_regression_gate.py` and `tools/cep_gen2.py`
as credential-content. None of them holds a credential. `governance/KNOWN_FALSE_POSITIVES.md` does not mention them.
Nobody has checked whether it still fires today.

## Task
1. Find the builder and the filter that produced "credential-content" (Grep for that string; read the S5 receipt for
   which builder). Run that filter today on the three files and record, per file, BLOCKED or ADMITTED with the
   matching rule/pattern and the matched text (quote at most 40 chars, never a whole line).
2. If none is blocked today: write the receipt saying so (with the evidence from step 1) and stop. That is a valid outcome.
3. If any is blocked: fix the matching rule as narrowly as possible (the smallest change that admits these files).
   Add a test file `tools/test_credential_filter_fp.py` (V-* gate style, prints `CFP_PASS=n/n`) with:
   - each real blocked file as an ADMITTED control (read from disk, not copied into the test);
   - a real-shape fake key (built at runtime by string concatenation so the test file itself carries no key-shaped
     literal) that must still be BLOCKED;
   - a mutant check: with your fix reverted in memory, at least one admitted control goes back to BLOCKED.
   Add one entry to `governance/KNOWN_FALSE_POSITIVES.md` naming the rule, the files and the fix.
4. If the matching rule lives in a hook file (anything under `hooks/` or `~/.claude/hooks/`), do NOT edit it: write
   the receipt with the rule location and the proposed change, and stop.

## Done
- `python tools/test_floor_regression_gate.py` still exits 0; if you wrote it, `python tools/test_credential_filter_fp.py` exits 0.
- Commit with a pathspec (only files you changed): `git commit -m "<msg>" -- <files>`.
- Receipt `vault/programs/factory-tranche-b/U1-receipt.md`: per-file verdict today, what you changed (or why
  nothing), test output lines, and `COMMITS: <hash>` reachable from HEAD (or `COMMITS: none` for outcome 2 or 4).
