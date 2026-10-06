# WU4 receipt (TOK-18 gen2, learning writeback from receipts only)
STATUS: DONE (UKDL written as candidates file, not into ukdl-universal.md)
- Inputs: WU1-receipt.md, WU2-receipt.md + orchestrator facts. No transcripts read.
- Outputs: LEARNINGS.md, ukdl-candidates.md, WU4-receipt.md, 4-line close under ## Spend of the tranche plan.
- UKDL: 4 candidates, 0 skipped as exact duplicate (grep counts in candidates file); ukdl-universal.md had 661 uncommitted lines from another writer, so not touched.
- Initial context: first assistant row of newest *.jsonl (subagents/agent-a9c7e71164283c367.jsonl): input 2 + cache_creation 74009 + cache_read 22448 = 96,459.
- Calls used: 3 (receipts+grep, write+commit, verify).
- Page faults beyond packet: 0.
- Debt: WU2 processed total not in receipt; duplicate grep first pass truncated at 25 hits (counts in file are the second pass); per-call 100k prefix means this unit cost ~0.3M.