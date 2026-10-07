done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_grammar_default.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-CC1 -- land G1 of the compiled grammar on the live base, close F1/F2 (cost-collapse T1)

Spec (binding): `vault/specs/cost-collapse.md` (program law, tranche table) and `vault/specs/compiled-grammar-default.md`
(laws 1-4, 7). Fresh worker, no parent transcript. This file is your scope, budget and done-gate.

## 0. Where you work
- The work tree above, branch `cost-collapse/main`. It already exists: do NOT create another worktree, do NOT edit the
  main checkout `C:\Users\User\.claude\skills\claude-power-pack` (another mission writes there) or
  `C:\Users\User\Apps\pp-gsdx-pcc`. No GSD commands, no Agents. Pathspec commits with a message file; never push.
- Windows host: PowerShell tool for git/python; git = `C:\Program Files\Git\cmd\git.exe`; python = the absolute path in
  `done_gate:`; `$env:PYTHONIOENCODING='utf-8'`. Redirect test output to a log; read only `_PASS=` and FAIL lines.

## 1. Fix the 8 red V-GRAMMAR gates (measured 33/41 at f9da4dad)
Red: NO-ENVELOPE-REFUSED-SWEEP, NO-ENVELOPE-REFUSED-CONTINUE, NO-ENVELOPE-REFUSED-RENEWAL, RENEWAL-ENVELOPE-LAUNCHES,
UNBOUNDED-ADMITTED-AND-LEDGERED (`OSError WinError 193` at launch), PACKET-GATE-COMPLETES-CONTINUE,
PACKET-GATE-REAL-HANG-NOT-PASS, MUTATION-CONTROL-UNMUTATED-COPY-GREEN (follows the others).
Classify each before fixing: (a) a launch path on this newer base that bypasses the launch-boundary admission
(law 1: the check lives INSIDE the launch function every path calls); (b) Windows portability in the test harness
(fake launcher not a PE file -> use `sys.executable` + a .py shim or a .cmd; `python3` in fixture gates ->
`sys.executable`). Fix (a) in `tools/gsd_mission.py`, (b) in the test. Never weaken an assertion to pass.

## 2. Close G1 review findings F1 and F2 (WU-G2b.md section 1, verbatim requirements)
F1: packet sha256 differs from the one recorded at `envelope --wu-packet` -> gate NOT judged + ledger
`packet_gate_drift`; record without sha256 -> not judged. F2: the gate runs in the packet's `work_tree:` when inside
the record's repo (a worktree of the same repo is admitted; a sibling clone of a different repo, a relative path or a
missing dir is refused + `packet_gate_unanswered`); no line -> effective_workdir, else work_dir, else cwd.
New gates V-GRAMMAR-F1-* / V-GRAMMAR-F2-* with both poles, plus one mutation check each (copy module, revert hunk,
import copy, assert red). Windows paths in fixtures.

## 3. No regressions
`tools/test_gsd_mission_envelope.py` stays 55/55. `tools/test_gsd_mission.py`: record its pass line before your
first edit and after; no new red. Commit after each section.

## 4. Chain (last act)
Write `vault/specs/cost-collapse.RECEIPT-T1.json` (commits, gate lines before/after, processed tokens if known).
Then write `vault/specs/packets/WU-CC2.md` for tranche T2 from the spec table (same header shape: `done_gate:` with
the absolute python and the new test file, `work_tree:` this tree), commit both, and arm it:
`<python> C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py arm --cwd C:\Users\User\Apps\pp-cost-collapse --command "Execute the work unit in the wu_packet" --workstream cost-collapse --no-launch`
then `... envelope --mission <id> --wu-packet vault/specs/packets/WU-CC2.md --token-estimate 5M --model sonnet --autocompact 250k`.
If your own gate is not green, do NOT arm T2: write the receipt with the red lines and end.

## Budget
At most 50 model calls; token estimate 8M (breaker parks at 16M). Keep context lean: no whole-file reads of
gsd_mission.py (it is >3000 lines) -- Grep for the function, read only that range. End with `HANDOFF NOTE:` and one line.
</content>
</invoke>
