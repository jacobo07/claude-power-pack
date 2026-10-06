# WU-1R -- repair packet: close EDD Phase 1 (2 wrong rows + 28 UNKNOWN)

Owner approved 2026-10-07. Fresh worker, no parent transcript. This file is your whole scope, budget and done-gate.
Do NOT run GSD commands, do NOT spawn agents, do NOT rescan the repository broadly, do NOT touch rows not listed.

## Where
`cd /home/kobii/missions/edd/.claude/worktrees/edd-run` (branch `mission/edd-run`). Pathspec commits only. Never push.

## Inputs
1. `.planning/workstreams/edd/OWNERSHIP_MATRIX.md` -- the rows to repair (read only those rows + the header).
2. `.planning/workstreams/edd/canary/dossier/dossier.md` -- read ONLY the `### C-NN` sections of the rows below.
3. PAGE as needed: `canary/dossier/refs.jsonl` (grep it by `"concept": "C-NN"`), a file range (<= 80 lines),
   `git grep -n -i -E '<terms>' -- modules tools hooks commands vault/specs governance` with YOUR OWN synonyms.

## Rows
A. Wrong in an independent sample (fix them):
- C-15 OWNERSHIP CLOSURE: currently UNDER_ANOTHER_NAME -> tools/usea_ownership_audit.py. Wrong concept: the mission
  means lifecycle ownership of PRODUCT resources/state (owner, birth, transfer, destruction, restoration, no
  survival past owner scope), not architectural authority between modules. Find a real owner or reclassify.
- C-54 PRODUCTION REALITY GATE: ALREADY_IMPLEMENTED contradicts its own note (mission-path production_reality is a
  self-declared string, closure.py:230). Re-judge; PARTIAL unless you can show both paths enforce it.
B. UNKNOWN (settle each): C-01 C-03 C-06 C-07 C-12 C-13 C-14 C-17 C-18 C-19 C-21 C-23 C-24 C-26 C-27 C-31 C-36 C-40
   C-43 C-47 C-49 C-50 C-56 C-58 C-65 C-66 C-77 C-80.

## Rules of judgment
- A dossier candidate is a vocabulary match, not an owner. Cite a line only after reading that it DOES the concept.
- DATASET_ONLY is an ABSENCE claim: it needs the search that could have found it. Put in the note the terms you
  searched (at least 2 synonyms beyond the title words) and the pathspec; "no hits" without the search is not allowed.
- NOT_A_SYSTEM is for process instructions of the mission prompt; name the existing rule/doc that already carries it.
- If after paging you still cannot decide, keep the row as is and write `UNRESOLVABLE: <one-line reason>` in the
  note. Silent UNKNOWN is not allowed.
- Row format unchanged: `| C-NN | title | STATUS | producer path:line | consumer path:line | evidence / note |`.

## Budget
At most 20 model calls. Batch: settle 4-6 rows per turn, independent reads in one turn. Token estimate 3M; the
breaker parks you at 6M; commit after every ~10 rows (a stall of 1.5M without a tree change also parks you).

## Outputs and done
1. Edit the listed rows in place in OWNERSHIP_MATRIX.md; commit.
2. `.planning/workstreams/edd/canary/RECEIPT-1R.json`:
   `{"mission_id": "<from your card>", "rows": {"C-NN": {"from": "<old status>", "to": "<new status>", "basis": "path:line or search terms"}}, "unresolvable": ["C-NN"], "boundaries": [{"n": 1, "reason": "PAGE|AMBIGUITY|PROOF_FAILURE|RECOVERY", "purpose": "<=12 words"}]}`
   All 30 rows must appear under "rows".
3. Run `python3 tools/edd_canary_gate.py` -- it must still print EDD_CANARY_GATE=13/13 (it checks the matrix
   structure and that cited lines resolve). Commit matrix + RECEIPT-1R.json, end with `HANDOFF NOTE:` and one line:
   rows by new status, unresolvable count, gate line. Do not wait for anything.
