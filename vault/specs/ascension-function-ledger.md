# Spec: Ascension per-function ledger (D43 step 1; Owner "rec" 2026-11-20, pane 5a77ca0e)
covers: [function-ledger, d43-step1, target-pinning, padded-tag]

## PRD
The self-certifying loop (backlog D43, `vault/programs/ascension/research/SYNTHESIS-2026-11-20.md`) needs one record of
every function of every Ascension binary: what it is, which methods were tried on it with what result, and its current
state, so a method ladder can pick "the cheapest untried method for this failure class" without anyone re-researching.
Step 1 is observation only: it reads what exists and changes no lane, no autopilot, no factory behaviour.

## Arch
`/home/kobii/agora/factory/ledger.py` (mirror `vault/programs/ascension/factory/ledger.py`), SQLite
`factory/ledger/ledger.db`, stdlib only.
- **Identity** `fid = <binary>:<module>:<ADDR>`; binary = the game image (RMCP01 = MKW+MKWLIB, RZTP01 = WSR+KSR, SUPP01,
  TENNIS, FIFA), so lanes that share a binary share rows.
- **Discovery, not enrolment** (PR-COVERAGE-BY-CONSTRUCTION-001): every `*/sweep.jsonl` under factory/ (depth <= 3) is a
  run; a run whose summary names no known binary is reported UNMAPPED, never skipped in silence.
- **Tables**: `function(fid, binary, module, addr, name, size)` from every corpus.jsonl; `attempt(fid, run, producer,
  arm, compiler, state, compiles, pct, target_obj, target_sha256, target_ok)` one row per (run, function, arm);
  `lift(fid, run, m2c_state)` from m2c/results.tsv; `cert(fid, lane, source)` from the autopilot MATCH snapshots
  (`match/<LANE>.json`), names mapped to addresses through the binary's corpora (unmapped names counted, not dropped).
- **Target pinning** (atlas defect: 416 rows pointed at rebuilt objects): at ingest each target object is hashed and
  the function name looked up in it now; `target_ok = 0` when the name is gone. Old sweep rows carry no hash, so their
  `target_sha256` is the hash observed at ingest and `target_ok` says whether it still holds the function: absent is
  never read as unchanged.
- **State per function** (best wins): CERT > MATCH (a factory run at 100, any arm) > NEAR99 > NEAR95 > NEAR90 > COMPILES
  (<90) > NO_COMPILE > LIFT_FAIL > TARGET_AMBIGUOUS/NO_TARGET > UNATTEMPTED. Attempts with target_ok = 0 do not set a
  state above COMPILES (their % describes a vanished object).
- **PADDED** (Owner ruling): column `padded` on attempt/cert, default NULL = not assessed; detection is a later step.
- `ledger.py build` (idempotent rebuild), `ledger.py report` (per binary: functions and bytes by state, methods tried,
  drift count, unmapped certs), `ledger.py fn <fid|name>` (history of one function).

## AC
(a) For the four atlas runs, per-run state counts from the ledger equal `research/census.json` (instrument check).
(b) Per binary, the state counts sum to the function count. (c) Two builds give identical reports. (d) Negative
control: a synthetic attempt whose target object lacks the symbol is marked target_ok = 0 and cannot raise the state.
(e) Every discovered run is mapped or listed UNMAPPED.

## Rollback
Delete `factory/ledger/` and `factory/ledger.py`. Nothing reads it yet.
