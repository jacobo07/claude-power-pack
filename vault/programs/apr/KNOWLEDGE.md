
## A6 -- canary: only the Status-less unit gets a seal.json (APR-6, OBSERVED, cause unverified)
- C2/C3 closed by the worker + gate passed have `.gate.json` only. Evidence: PRODUCTION-REALITY.md F1.

## A7 -- refusal.json cited by the row disappears (APR-6, OBSERVED, cause unverified): F2.

## A8 -- mission layer says "no receipt" about a closed receipt; second worker renewed (APR-6, OBSERVED)
- m-2e61e0a0aa10 and renewal m-7a5265092233 both HALTED "no receipt" while WU-C2-receipt.md (Status: DONE, 17:30:05)
  was on disk and the chain advanced. ~77k tokens of a duplicate worker. Likely the residual path of the receipt check
  (receipt older than mission start / residual packet) -- not verified. Open: next task. Status: OBSERVED, unfixed.

## A9 -- `gsdx_chain.py status` under Git Bash: "Could not determine home directory" (APR-6)
- Python Path.home() needs USERPROFILE/HOME; the harness bash lacked them. Works under PowerShell. Workaround, not a code fault.

## A10 -- APR4 self-review was not independent (APR-4 receipt): 1 HIGH (empty acceptance sealed vacuously) fixed 9da3e13f.
opped_without_done`.
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

## A11 -- an edited packet froze APR7 for 28 h with no alert (coordinator, 2026-10-13)
- Cause: the coordinator amended WU-APR7.md (3e3df8ab) 2 min after the chain admitted it; every sweep pass refused the
  launch ("the packet changed since it was admitted: admit it again"), the mission halted at 24 h with 0 spend and no
  session, the steward cannot settle a session-less mission, so the chain sat at wait_steward (SILENT) from 10-12 20:31.
- No alert reached the Owner: neither the repeated launch refusal nor the wait_steward silence surfaced.
- Recovery: residual packet written by the coordinator + manual arm-chain (m-8fda4d378172), identical to the chain's _arm.
- Lessons: never edit a packet after it is armed (append a new unit or a residual instead); a never-launched mission must
  not wait on a steward; a launch refused on consecutive passes must alert. Folded into WU-APR7.md.residual.md item 7.