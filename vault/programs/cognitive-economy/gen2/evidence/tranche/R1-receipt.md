# R1 receipt -- review of S5 commits 599bd751 + c7ca71d8 (tranche context-runtime-4)
VERDICT: ACCEPT. No defect found. Every check passed, and two notes (N1, N2) are recorded below without blocking.
Scope: read-only review. S5 was not re-run beyond its own test, and no S5 code was changed.

## Commits under review
- 599bd751 `feat(wu3): offline dependency packets for WU1/WU2 + V-WU3 gates (11/11)`: A tools/wu3_packets.py (197), A tools/test_wu3_packets.py (85).
- c7ca71d8 `docs(s5): WU3 offline packet receipt`: M vault/programs/cognitive-economy/gen2/evidence/tranche/S5-receipt.md (+54/-5).
All three files were read in full.

## Checks
1. **Writes outside the repo or outside the listed files.** None in S5 code. wu3_packets.py only reads (`read_text`, `stat`, `is_file`) and calls git read-only (`show`, `rev-parse`, `hash-object` without `-w`, wu3_packets.py:47-63). test_wu3_packets.py creates one empty `tempfile.TemporaryDirectory` (test:69), which it uses only as a non-existent root for the DEOPT judge and then removes automatically. The vendored builder tools/source_packet.py (not S5's file) does write at :119-124 (mkdir + `{digest}.txt/.json`) and :198 (`--out`). Those are pre-existing paths that S5 reaches through `sp.build`. After the test run `git status --short` showed only `?? .pp-capabilities` (created 2026-10-07 14:09:55, 311 B), so no tracked file was modified. See N2.
2. **Network or subprocess calls not in the receipt.** No network: no urlopen, requests, socket or http in the S5 files. The only subprocess is git at wu3_packets.py:47-49. It is read-only and backs the receipt's "Critical pages = .py files the unit's own commits changed" and "drift=none (worktree blob == last unit commit blob)". The receipt implies these calls but does not name git explicitly (N1).
3. **Secrets.** A grep of all three files for `sk-|ghp_|AKIA|BEGIN .*PRIVATE|password|token\s*=|api[_-]?key` returned 0 hits.
4. **Deleted or overwritten files that are not S5's.** None. 599bd751 only adds files. c7ca71d8's 5 deleted lines are S5's own earlier BLOCKED receipt (from 97a8cd1a, "S1/S3/S5 BLOCKED by permission"), replaced by the offline result. That text remains in git history.
5. **Gates that cannot fail.** Each of the 11 V-WU3 gates has a red branch:
   - ORACLE: red on an empty unit or a shared critical page.
   - PRIVATE-NONEMPTY: red on an empty private set.
   - EXCLUDE-WU1/-WU2: red if the packet is empty or contains a page private to the other unit.
   - EXCLUDE-CONTROL: red if the union packet drops a private page. This is the negative pole.
   - ADMIT-CONTROL: red on any WU2 fault.
   - WU1-NO-SILENT-PASS: red if the judge says ADMIT for an included page that is redacted, or says non-ADMIT when every page is included. It is a consistency check against `included()`, so it is the weakest gate, but it is not a tautology: `judge` also rejects `redactedLines` and `included` does not.
   - MUTANT-PAGE and MUTANT-DEOPT: red unless exactly the cut page faults with the expected class.
   - TRUNCATED-IS-FAULT: red if a default-limit packet ADMITs.
   - UNJUDGED-DEOPT: red if a builder failure is not DEOPT.
   - In `judge` (wu3_packets.py:128-142), ADMIT is reachable only when no required page faults.

## Test run
Command: `python tools/test_wu3_packets.py` (Python312, cwd = worktree). Exit code **0**.
```
PASS V-WU3-ORACLE WU1=['tools/floor_regression_gate.py', 'tools/test_floor_regression_gate.py'] WU2=['tools/test_wake_check.py', 'tools/vault_summarize.py', 'tools/wake_check.py']
PASS V-WU3-PRIVATE-NONEMPTY
PASS V-WU3-EXCLUDE-WU1
PASS V-WU3-EXCLUDE-WU2
PASS V-WU3-EXCLUDE-CONTROL union packet leaks [test_floor_regression_gate, test_wake_check, vault_summarize, wake_check]
PASS V-WU3-ADMIT-CONTROL WU2 judge=ADMIT faults=[]
PASS V-WU3-WU1-NO-SILENT-PASS WU1 judge=DEOPT faults=[floor_regression_gate.py blocked, test_floor_regression_gate.py blocked]
PASS V-WU3-MUTANT-PAGE judge=PAGE faults=[('tools/wake_check.py', 'PAGE', 'not-in-packet')]
PASS V-WU3-MUTANT-DEOPT judge=DEOPT faults=[('tools/wake_check.py', 'DEOPT', 'absent-from-disk')]
PASS V-WU3-TRUNCATED-IS-FAULT judge=PAGE faults=[('tools/vault_summarize.py', 'PAGE', 'truncated')]
PASS V-WU3-UNJUDGED-DEOPT judge=DEOPT
WU3_PASS=11/11  threshold=11/11
```
These results match the claims in S5-receipt.md: WU2 ADMIT, WU1 DEOPT (blocked), and 11/11.

## Notes (not defects)
- N1: The receipt does not name the read-only git subprocess or the builder's cache writes. Both are implied by its method section, and neither changes a tracked file.
- N2: The origin of `.pp-capabilities` was not measured. It could come from a session hook or from the builder. It is not part of either S5 commit and was left untouched.
- N3: GIT is hardcoded to a Windows path (wu3_packets.py:36), so the tool is host-specific. The header of S5-receipt.md says "context-runtime-3" while this tranche is context-runtime-4. Both are cosmetic.

COMMITS: d5636e78 (receipt) + this follow-up commit that records the hash
