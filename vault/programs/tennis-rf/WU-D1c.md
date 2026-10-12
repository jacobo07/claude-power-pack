# WU-D1c -- Ph1c deterministic-first gate (laptop plane, PP code, global for every chain)

Common brief: `D28-BRIEF.md`. Plan section 4 "Deterministic-first", MDG 4. Regression case: P1P2 (37 turns,
`factor.py` written on the last turn and never run; `evidence/p1p2/receipt.md`, KNOWLEDGE-TRFC K-TRFC-04).

Design (implement exactly this, smallest code that does it):
1. WU packet front matter (YAML between `---` lines at the top, optional): `class:` one of DETERMINISTIC,
   SEARCH, MODEL, OWNER_REQUIRED (absent = MODEL, today's behaviour) and `pre:` a list of shell commands
   (string each) with optional `pre_timeout_s` (default 600, max 900).
2. `tools/gsdx_chain.py tick` (zero model) runs a unit's `pre` commands BEFORE it arms that unit, once per packet
   sha: outputs (rc, last 4 KB stdout/stderr, seconds) go to `<packet>.pre.json`; a non-zero rc stops the unit as
   `pre_failed` (silent decision row, no arm). For class DETERMINISTIC, if after `pre` the unit's receipt exists and
   `receipt_judge` says DONE, the unit closes with NO worker (decision row `closed_deterministic`). A MODEL/SEARCH
   unit's worker gets the `.pre.json` path in its card/packet so it reads results instead of recomputing them.
3. `receipt_judge`: a DETERMINISTIC unit whose ledger shows model calls > 0 and whose receipt has no typed
   `UNKNOWN`/`CONFLICT` line = `CLAIM_EVIDENCE_DIVERGENCE`-style typed failure `DETERMINISTIC_USED_MODEL`.

Steps:
1. Read `tools/gsdx_chain.py` (tick path, the arm call) and `tools/receipt_judge.py`; `tools/test_gsdx_chain.py` is
   the harness to extend. Tests first (RED): front matter absent = unchanged decisions (control); pre rc 0 then
   arm; pre rc 1 = `pre_failed`, no arm; DETERMINISTIC with DONE receipt after pre = closed without arm; pre runs
   once per sha (second tick does not rerun); timeout honoured; DETERMINISTIC_USED_MODEL typed failure.
2. The tick is LIVE (PP-TrfChain-Tick runs this checkout every 10 min, including for YOUR successor). Develop the
   new logic in a new module `tools/chain_pre.py` and call it from gsdx_chain in ONE small hunk; run the suites
   before that hunk lands; commit tests + module + hunk in one pathspec commit. `CPP_CHAIN_PRE=off` = kill switch.
3. Mutation drills on isolated copies (`tools/mutation_drill.py --spec`): at least the arm-skip on pre failure and
   the deterministic close; both must be KILLED.
4. Regression replay: a fixture packet shaped like P1P2 (class DETERMINISTIC, pre = a python one-liner that writes a
   DONE receipt) closes without a worker in a temp chain (`--chain <tmp> --dry-run` where possible).
5. Run `test_gsdx_chain.py`, `test_receipt_judge.py` (if present), `test_claim_evidence.py`, `test_apr_seal.py`.
Done-check: suites green with counts in the receipt, drills KILLED, kill switch tested.
Receipt: `WU-D1c-receipt.md`.
