# A probe's outcome letter is not a fidelity verdict

Measured 2026-10-19 on Two Builders TB-FINISH (Phase 25).

## What happened
The worker records each Dolphin probe as outcome A, B or C. That letter answers the
probe's own causal question ("did the UV rewrite reach the screen?"). I reported the
letters to the Owner as results. The independent audit of the same 42 captures
(`vault/tower/sources/ttb-fidelity-v3/TTB_Run_Audit_Tracker_v3.csv`) read F2A, F3A, F3B
and F3C as FAIL_VISUAL, F4B as PARTIAL, nine as UNVERIFIED and F6C as having no run;
none had hardware evidence or Owner approval. F3B was "A" and a multicolour malformed model
at the same time, and both were true.

## Pattern
Two different questions share one status field. A causal outcome is not a fidelity state;
reading one as the other hides the visual failures behind a green letter.

## Rule that enforces it
Family `game_mod_fidelity` (B0, entry `gmf-no-pass-by-resemblance`) plus
`modules/tower/evidence.py`: a claim whose source is not evidence is refused by name, stills
cap at DOLPHIN_LOAD, behaviour needs a video, WII_TESTED needs hardware plus logs,
OWNER_APPROVED needs a decision file, PASS needs both. Gate: `python tools/test_tower_fidelity.py`
(22 gates, two mutants verified red).

## Not yet generalised
One project, one session. Treat as a PROCESS RULE candidate for UKDL, not a hard rule, until
a second project shows it.
