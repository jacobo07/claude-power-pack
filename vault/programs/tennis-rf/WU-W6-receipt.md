# W6 receipt
Status: DONE

Commits: PP only (evidence/w6/ledger.py, evidence/w6/test_ledger.py, measure/causal-ledger.json, this receipt). Zero GEX44 jobs, zero compiles, no code in wt_tennis_rf.
Command: `python -I evidence/w6/ledger.py measure/causal-ledger.json`; tests `python -m pytest evidence/w6/test_ledger.py` 5/5 (written RED first).
Scope: 18 worker sessions of W1-W5b (mission records whose wu_packet is under vault/programs/tennis-rf/, de-duplicated by session; no subagent transcripts exist). Excluded: W6 itself (running) and m-ea05f64a68b3 (W1, no session recorded). session_autopsy.py has no role classifier (context rent only), so roles live in ledger.py reusing the tis_observed counting rule (message.id+requestId).

Category table (321 calls, 13,086,143 processed tokens; transcript sum == the harness's mission token sum per session, 18/18 equal):
| category | calls | tokens | share |
|---|---|---|---|
| SEARCH | 85 | 3,707,126 | 28.3 % |
| CONTROL | 73 | 2,894,518 | 22.1 % |
| READ | 79 | 2,820,160 | 21.6 % |
| PROOF | 23 | 1,088,966 | 8.3 % |
| RECEIPT | 18 | 924,487 | 7.1 % |
| IMPLEMENT | 14 | 868,621 | 6.6 % |
| STARTUP | 18 | 308,314 | 2.4 % |
| REREAD | 6 | 269,188 | 2.1 % |
| UNATTRIBUTED | 2 | 85,986 | 0.7 % |
| RECOVERY | 2 | 63,513 | 0.5 % |
| REPAIR | 1 | 55,264 | 0.4 % |
| SEMANTIC | 0 | 0 | 0 % |
Buckets: tax (STARTUP+REREAD+CONTROL+RECOVERY) 27.0 %; exploration (READ+SEARCH) 49.9 %; work (IMPLEMENT+PROOF+REPAIR+RECEIPT) 22.5 %; semantic 0 %.
Per-unit tables: measure/causal-ledger.json `units`.

- PROVEN: unattributed share 0.66 % (>= 95 % attributed: 99.34 %); no transcript gap versus mission records.
- PROVEN: no Tennis model-semantic inference exists in W1-W5b (SEMANTIC = 0; W5a/W5b closed 0 functions). All spend is architecture/tooling/exploration.
- Derived: context duplication factor 14.06 (processed / new tokens); startup tax: first calls 2.4 %, floor rent (first-call context re-read on later calls) 41.6 % of all tokens; 70 failed/hook-blocked tool calls (mostly Bash-bridge guard refusals); raw-binary page-fault rate 1/3 (2 reads, 1 re-read of disassembly-like paths: tiny sample, shell reads only by gc/cat).
- UNKNOWN: tokens per verified function (0 verified; semantic vs tax split given in the json: semantic 0, tax 3.54 M); model displacement rate (no verified/layer-closed denominator); LLM invocation density per function (same).
- Limits: roles are regex rules on tool names/commands (SEARCH matches `find`/`grep` words anywhere in a shell command; PROOF matches any `.py` run), so category edges are approximate; totals and unattributed are exact. SEMANTIC needs a tool-less reasoning call before a source edit, which never occurred.
- Next unit must know: ~50 % of spend is exploration and 27 % tax, 42 % is pure floor rent, while ~0 % is semantic: reforecast should price Tennis A/B as floor-rent x calls, not tokens per function. Calls ~16.
