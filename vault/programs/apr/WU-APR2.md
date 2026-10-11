# WU-APR2 -- Machine seal, false-DONE refusal, residual recovery classes

Common brief: `PROGRAMME.md` (read it first). Route M. cwd `C:\Users\User\Apps\wt_apr`.
Files you own: `tools/gsdx_chain.py`, `tools/receipt_judge.py`, `tools/test_gsdx_chain.py`, a new
`tools/test_apr_seal.py` if you prefer a separate suite.

Steps:
1. Read `tools/gsdx_chain.py` whole (it is ~250 lines) and `tools/receipt_judge.py`. Read `chain.json` of
   `vault/programs/ewc/` as the real shape.
2. Schema (optional, per unit): `"acceptance": {"gates": [[argv...], ...], "cwd": <path, default unit cwd or chain
   root>, "require_commit": true|false, "files": [paths that must exist], "timeout_s": int}`. Absent => behaviour
   unchanged (test it on a chain with no acceptance anywhere: every existing V-CHAIN-* stays green).
3. Finalizer (zero model, in `tick`, BEFORE `decide`; `decide` stays pure and reads the files it leaves):
   for each unit with `acceptance` that is not yet sealed, whose missions are all terminal (or which has none and a
   receipt exists):
   - receipt NOT closed (judge: UNREADABLE / None / STUB) AND evidence passes -> write `<receipt>.seal.json`
     `{unit, verdict:"DONE", sealed_by:"gsdx_chain.finalize", receipt_status, receipt_sha256 (null if absent),
     gates:[{argv, rc, tail}], commits (since the unit's first mission created_at, via git -C), at}`. The worker's
     receipt bytes are never modified (provenance). This is the K5 auto-repair.
   - receipt says DONE AND evidence fails -> write `<receipt>.refusal.json` (same fields, verdict "FALSE_DONE").
   - Cache by (receipt sha256, HEAD of the gate cwd): never re-run gates for an unchanged pair (each tick is every
     10 min; gates must not run 6x/hour on nothing new). Timeout -> refusal with reason "gate timeout", not a crash.
   - require_commit: at least one commit in the gate cwd since the unit's first mission was created.
4. `decide`: a unit is done if (status in accept) and no refusal for the current receipt sha, OR a seal exists for the
   current receipt sha (or for an absent receipt). A refusal makes the unit not done; its missions are terminal, so
   it flows into the residual path with `receipt: "FALSE_DONE"`.
5. Residual recovery classes: the residual row carries `class` in {UNCLOSED_RECEIPT, FALSE_DONE, NO_RECEIPT,
   WORKER_STOPPED} and the refusal/seal evidence path; the steward's residual packet is still the packet armed.
   Strategy change: if the latest two residual attempts of the unit end with the same refusal fingerprint
   (sha256 of gate argv+rc+tail) the next arm must climb a rung; at the top rung with the same fingerprint emit
   `{"action":"human_gate","unit","why":"same failure on every rung","evidence":[paths]}` -- never another arm.
   FALSE_DONE has no steward: its mission ended COMPLETED with a closed receipt, and the steward acts only on
   HALTED/BLOCKED missions without one, so `_residual` would sit at `wait_steward` forever. The finalizer therefore
   writes `<packet>.residual.md` itself for FALSE_DONE (base packet text + a `## Residual` section citing the refusal
   file and the failing gate tails, naming the latest mission id), and `_residual` accepts it for that class without
   `steward.done`. Test that exact deadlock (RED today: wait_steward forever).
   Expose `try_seal(packet) -> {"sealed": bool, ...}` (finalizer for the one unit that owns the packet, found via the
   chain files) for APR-3 to call before a halt-continue renewal.
6. RED first: E2-shaped fixture (receipt without Status, commit present, gate `python -c "exit(0)"`) -> today
   `stopped_without_done`, after -> `arm` of the successor with a seal file on disk. False-DONE fixture (receipt
   `Status: DONE`, gate exits 1) -> today `arm` successor (the bug), after -> no successor, refusal on disk.
   Controls: no-acceptance chain unchanged; DONE + passing gate arms; unchanged receipt => gates not re-run (count
   invocations with an injected runner); gate timeout => refusal not crash; human_gate after repeated fingerprint.
7. Run `tools/test_gsdx_chain.py`, `tools/test_receipt_judge.py`, `tools/test_halt_continues.py`,
   `tools/test_mission_steward.py`.
Receipt: per-step PROVEN/NOT_PROVEN with counts; the seal/refusal schema; RED evidence (old code result per fixture).
