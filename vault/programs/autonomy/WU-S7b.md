# WU-S7b -- Autonomy Convergence unit S7b (continuation of S7)

Read `vault/programs/autonomy/PROGRAMME.md` first. Done in S7: `tools/autonomy_gates.py` (8 invariant V-gates + spend
agreement gate + reflex coverage counter 8/8), `tools/test_autonomy_gates.py` (25/25 with mutation drill), programme_status
shows interactive_processed. Remaining:

1. Wire `autonomy_gates.run_all` to LIVE state (build the state dict from programme_status + mission_spend goal-status) as a
   CLI `python tools/autonomy_gates.py --live`; a test that the live spend_agreement gate compares programme_status and goal-status.
2. Reflex: `gsd_mission release` of a held mission must re-admit from the recorded route when packet + route sha are intact
   (same rule as A3 readmit_for_relay), so the sweep does not log `not admitted (verdict none)` forever. Test it, with a red branch
   (sha changed -> no readmit).
3. Reflex: breaker-halted unit with handoff -> verify R1 (604eb054) covers it; add a test asserting the chain does not return
   stopped_without_done when a residual exists, or fix it.
4. Attribution: interactive pane whose cwd enters a goal root is charged role=interactive, not to the goal's productive spend;
   show it apart in programme-spend (already measured as interactive_processed) -- check the goal ledger charge path, not only the view.
5. Record compiled patterns (manual re-arm -> chain, manual landing -> land_worktree) in the receipt.

Receipt: `vault/programs/autonomy/WU-S7b-receipt.md`.
