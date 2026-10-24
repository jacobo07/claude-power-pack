# Phase 3 verification — PASSED (DEFER autopsy INCONCLUSIVE, recorded)
- Gates: `python3 tools/test_s3_admission.py` S3_PASS=11/11 (CRLF/BOM equal, content change still differs, legacy raw digest matches, backoff 300/600/1200/1800 cap, kill switch; two mutants — no-normalise, no-backoff — go red).
- Replay (this host ledger, 6074 rows): m-9d00610493fc 53 identical `relay_held` NO_PHASES over 4.73 h; same cadence through the new backoff asks GSD 12 times (-77%). OK is still observed at the first ask past next_check (V-MC-GSD-BLOCK-CLEARS-ON-OK-AND-PROCEEDS).
- Trade-off: a roadmap fixed mid-window is noticed up to 1800 s later; accepted, kill switch exists.
- DEFER autopsy: 0 DEFER/RECOMPILE verdicts in this host's 65 mission records or ledger/cognitive-admission. The 231 DEFER/none are laptop-plane; false-defer rate is UNMEASURED here (LAPTOP-ONLY), not zero and not PASS.
