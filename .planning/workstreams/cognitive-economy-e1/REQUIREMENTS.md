# Requirements: cognitive-economy-e1

- [x] **E1-BANK**: 11 judgement tasks, one per rule, validated without model calls and frozen before any counted run.
- [x] **E1-RUNNER**: the ADDENDUM-E1 stopping contract implemented as code, every stop branch driven by a test.
- [x] **E1-RUNS**: counted pairs on GEX44 until a contract stop, committed pair by pair.
- [x] **E1-REPORT**: per-rule decisions with run ids, spend and limits; nothing written under `~/.claude`.

## Traceability

| requirement | phase | status |
|---|---|---|
| E1-BANK | 1 | Complete |
| E1-RUNNER | 2 | Complete |
| E1-RUNS | 3 | Complete |
| E1-REPORT | 4 | Complete |
