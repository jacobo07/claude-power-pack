# Phase 5 Evidence: Compile-out of compound steps 7 and 8

Plan (inline): build `compound/steps78.py` and `gates/gate_compound78.py`; prove on temp copies; Owner-bundle the
live apply; ledger row L. Done out of roadmap order (phases 3-6 depend only on phase 1) while phase 3's extraction
ran in the background.

| Pillar | Terminal | Key evidence |
|---|---|---|
| L | IMPLEMENTED_AND_VERIFIED | `gate_compound78.py` PASS 6/6 on temp copies (224 real learning files, real marker); red under `--break-rollback`; live state sha256 unchanged |

Verifier: `CEP_PILLAR_L=PASS`. Full PRG: `vault/programs/cognitive-economy/evidence/L-prg.md`.

Success criteria: (1) module with mkdir mutex at `compound-learnings.json.lock`, backup, sibling tmp + rename,
marker unlink, rollback on unlink failure, case-sensitive keys -- met; (2) gate on a TEMP copy, red branch driven,
live sha256 identical -- met; (3) live apply + call-site switch in the Owner bundle as `[L]` -- met; (4) `--pillar L`
PASS -- met.

## Product Delta

- `/cpp-compound`'s stalling tail is a tested function with a CLI; switching to it is one Owner decision.

## Intelligence Delta

- The live state file is unreadable by PowerShell `ConvertFrom-Json` (case-variant project-id pair), so any
  PowerShell-side step 7 fails before it starts. A Python or Node implementation is not a preference, it is required.
