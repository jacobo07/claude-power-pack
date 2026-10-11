# APR knowledge log (APR-6 promotes candidates; append one entry per bug/failure)

## A1 -- Three receipt parsers, one file, three answers: the root cause of EWC K5 (coordinator, 2026-10-11)
- Symptom: EWC E2 halted `stopped_without_done receipt=UNREADABLE` with its work committed (25f83975, 56/56).
- Trigger: E2's renewal m-4d2ca58231cd (renewed_from m-5b373f3a9b72, which had HALTED "no receipt") wrote a receipt
  with every step PROVEN and no `Status:` line.
- Root cause: `gsd_mission._receipt_present` -> present (not stub/partial) -> mission COMPLETED, halt-continue skipped;
  `gsdx_chain.receipt_status` -> UNREADABLE -> unit not done; `gsd_mission.receipt_complete` -> not done. With every
  mission terminal and `max_residuals 0`, `_residual` returned `stopped_without_done` each tick. The steward also
  skipped the mission (`mission_steward.py:138` returned on "receipt file exists").
- Failed defenses: halt-continue (the recovery that DID work for the first E2 stop) was switched off by the permissive
  parser; the chain had no evidence but model text; no alert on a repeated `stopped_without_done`.
- Fix (APR-1, 6932f9b9 in wt_apr, 741479f3 live): `tools/receipt_judge.py` is the only reading; an unclosed receipt
  halts the mission with the reason and gets the bounded renewal; the steward acts on it, never rewriting the file.
- Proof: `V-APR-K5-UNCLOSED-RECEIPT-RENEWS` FAIL against HEAD's gsd_mission (state COMPLETED = the incident), PASS
  after (HALTED "receipt not closed (status UNREADABLE)", one successor). Differential over 47 receipts on disk: no
  DONE verdict and no chain status changed; 27 Status-less receipts no longer count as closed (intended).
- Universal lesson (UKDL candidate, process rule): one parser per lifecycle fact; a second reading of the same file is
  a split brain waiting for the input where they disagree. Epistemic status: MEASURED.

## A2 -- 27 historical receipts carry no Status line (coordinator, 2026-10-11)
- Symptom: the differential found 27 `*-receipt.md` (cognitive-economy gen2/gen3/gen4, presence) with no status.
- Impact: before APR-1 each one counted as "present" to the mission layer. They belong to finished programmes, so
  no live behaviour changes; a future worker writing that shape is now renewed (bounded) instead of COMPLETED.
- Lesson: the receipt contract was a convention in each programme's brief, never checked by the code that read it.
  Epistemic status: MEASURED (scratchpad receipt_diff.py, two runs).

## A3 -- an inline `Status: DONE` is a real receipt shape (coordinator, 2026-10-11)
- Symptom: a first line-start-only judge flipped P2a / P3a / P7G0 from DONE to UNREADABLE.
- Fix: line-leading match first, then the first word-bounded `Status:` anywhere. Caught by the differential before
  commit, not after. Lesson: run a parser change against the real corpus, not only fixtures. Epistemic status: MEASURED.

## A4 -- recorded spend fell between two ticks (coordinator, 2026-10-11, UNEXPLAINED)
- Symptom: ewc chain rows show `used` 3,214,753 (11:03) then 2,726,500 (11:14) then 3,476,500.
- Hypothesis: settlement at transcript-measured spend replaced larger open reservations. Not verified; APR-3's
  reforecast reads these numbers and must cite which ledger field it uses. Epistemic status: OBSERVED, cause UNKNOWN.

## A5 -- the E1 route was priced at 12 calls and used 21 (from EWC K3)
- The growth estimator priced S at 1,266,053 (12 calls, 29 physical). E1 (premises + fixtures + RED test) tripped at
  21. One data point: the global estimator is not changed; APR-3 makes the CURRENT programme reforecast from measured
  unit spend. Epistemic status: MEASURED (one programme).
