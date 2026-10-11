# W3 receipt
Status: DONE

Slice done: steps 1-3. Step 4 (A/A job) moved to continuation W3b (chain.json: W3b after W3, W5a now after W3b). Zero GEX44 jobs sent, JOBS.md untouched.
Commits: PP only (see git log of vault/programs/tennis-rf); no code changed in wt_tennis_rf.

- PROVEN (step 1, reused): 6 units, 1,797 fns, 408 exact / 166 loose Resort shape (re-derived by evidence/w3/analyze.py, same counts).
- PROVEN (step 2): `TENNIS-TOOLCHAIN.md`. Premise corrected: SportsPackEP is SDK build 0x4302_145 dated Dec 2009 (not 2006), same build id as Resort (Feb-Mar 2009). Candidate = Resort pin mwcceppc f54d5644, flags UNKNOWN, confidence medium-low.
- PROVEN (step 3): `evidence/w3/sample60_table.md` (60 rows: 15 exact, 15 loose, 30 none, size-stratified). m2c: 48 L1 / 12 fail (jump-table 'bctr' and M2C_ERROR); unresolved `?` types sum 142, unk fields sum 763 over the 48 (the 1,310-insn fn alone: 25 / 360). Command: m2c_producer.py (factory venv) over wst_tennis/step0 split; no compile.
- PROVEN: 179 of 408 exact-shape Tennis fns have a SRC PROVEN Resort donor, all 1-2 insns (so A/A cannot test the compiler).
- NOT_PROVEN: the A/A (step 4). Blocker named: capsule_build.py:40,45 / candidate.py:49-53 / match.py are Resort-hardwired; needs a Tennis capsule + judge (W3b step 2-3).
- Next unit must know: W3b packet lists 3 candidate pairs; compiler mismatch is undetectable by trivial bodies; keep Resort drills green when parametrising.