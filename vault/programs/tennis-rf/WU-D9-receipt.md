# WU-D9 receipt

Status: BLOCKED_HUMAN

Gate: ADMITTED. fn_802128D4 (6/8 insns, bool idiom) and fn_8032CF78 (3 insns, sda21 vs @ha/@l) are PARTIAL, <=16 insns.

Done: variants generated (`evidence/d28/d9/gen_variants.py`), 31 variants + 3 donor controls at O4p only (O2 dropped: 65 units projected OUT 36.6 MB > 20 MB budget). Build candidate-20261014T160717Z, FIT=OK, CERTIFY=READY (inputs_hash c2e43d028547c4c17f97fae45fce46dadab321615937ecf3f21aa8ab73c927d4). JOBS.md row 7 written before send.

Blocker: `stage.py send` returned `SEND=CAP_REACHED` (phase 1: 4 queue adds already recorded, cap 4). Not bypassed.
Owner: raise/clear the phase-1 queue-add cap (or approve a cap override) for D28 Ph9 job 7, then run
`KSR_CAPSULE_PROFILE=tennis MATCH_ACCEL_GEX44=C:\Users\User\Apps\recon_work\wst_tennis\w10\F python stage.py send candidate-20261014T160717Z` (cwd tools\wros\binary\decomp\gex44), then repatriate.py <job>, candidate.py judge <job>, write synthesis.json.

synthesis.json: not produced (no results).

## Plan delta
Ph9 is admitted but unexecuted; O2 variant arm dropped for OUT budget (re-add in a later job if O4p yields no MATCH).