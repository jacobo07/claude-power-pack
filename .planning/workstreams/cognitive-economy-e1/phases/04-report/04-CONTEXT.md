# Phase 4: Report -- context (discuss skipped, unattended; decisions derived from ADDENDUM-E1 and the Phase 2 code)

- The report is RENDERED from `e1/results.jsonl` by code (`e1/e1_report.py`), never hand-written, so every number
  and run id in it has one source. It is planned and tested while Phase 3 runs (no model call, no write to e1's
  git index while the runner owns it).
- Decisions are the stop record's `final_decisions`, cross-checked against an independent
  `e1_contract.replay` + `final_decisions` of the same records; any mismatch, a missing stop record, or a record
  set replay refuses -> no report (exit 1). Tokens never decide (clause 4).
- Contents (ROADMAP Phase 4): one row per rule (13: 11 E1 + 2 R2 carried by reference) with decision, basis and
  the pair's run ids; positive control (A/B first-call context, delta); counted spend vs the 17M cap; mean
  measured first-call delta over valid pairs; per-run table (validity + reasons, grade, first-call, total and
  output tokens); bank-access audit per run (hits listed and the pair named; unreadable/absent evidence is
  NOT AUDITED, never "clean"); the "Known limits" section of ADDENDUM-E1 quoted verbatim; the proposed move list
  for the Owner (relocation candidates + R2 carried, empty on harm or positive-control stop) with HR-001 stated.
- Ceiling wording: every valid pair A-pass/B-pass -> "no loss observed at n=1 per rule", never "no effect".
- The report writes one file, refuses any output path under `~/.claude`, and changes nothing there.
