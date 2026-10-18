---
title: Continue-here session transfer is proved on the target, not by the product
tier: execution
date: 2026-10-18
source: Orca repo docs/dws/live-2026-10-18-row-70-resume-evidence.md (r70r5 and mutant r70m, session transfer 3987e6c4fa, harness 55f1d7fbb6)
status: LESSON -- UKDL entry T-SESSION-TRANSFER-NEEDS-AN-INDEPENDENT-READ-BACK-001
---

# Continue-here session transfer is proved on the target, not by the product

## Evidence
- r70r5 passed: a word told only on the laptop was answered by the resumed session on GEX44 (HWF70R_RESUMED_ANSWER pelican2e5e, question did not contain it).
- Independent instrument: stat on GEX44 of the transcript file gave XFER_BYTES=583529.
- Mutant r70m: 	ransferOne returned copied/present without writing. The product still showed esume/provider-session-present, the GEX44 stat answered No such file or directory, and the spec went red at the XFER_BYTES assertion.

## Lesson
The product's own status is the thing under test; it cannot also be the witness. Read the bytes on the target with a tool the product does not use, and keep a mutant that makes the product lie so the witness is shown able to fail.