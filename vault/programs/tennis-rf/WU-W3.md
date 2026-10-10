# WU-W3 -- Tennis onboarding, minimal for measurement (<= 1 GEX44 job)

Common brief: `PROGRAMME.md`. Plan section 5 (W3). Needs W2 DONE. Iterate after step 2 (compiler fingerprint).

Goal: the factory can compile and judge Tennis functions with the same oracle it uses for Resort, proven by an A/A.
1. Reuse step0-3 (`wst_tennis\step0..3`): DTK split of SportsPackEP.dol, `.fn` list, shape hashes, Tennis units
   (6 DTK objects, 1,797 functions). Do not redo them.
2. Compiler fingerprint (PLAN mode, bounded to 1 decision note `TENNIS-TOOLCHAIN.md`): which mwcc build and flag set
   produced SportsPackEP (Wii Sports 2006) vs the Resort pins (2009). Evidence: code-gen idioms on functions whose
   Resort shape matches exactly (step0: 408), SDK version strings (step1 anchors), known decomp-community facts only if
   cited. Output: candidate compiler + flags with confidence; UNKNOWN is acceptable and must be stated.
3. Run the existing m2c producer over a stratified sample of 60 Tennis functions (no compile): record per function
   unresolved-type count, unk-field count, size, Resort-shape match (exact/loose/none), call fan-in/out.
4. Tennis A/A: pick 2-3 functions whose exact Resort-shape counterpart is already SRC PROVEN in the factory
   (levels.jsonl), transfer that source, build one certified job (W2 certificate), send it as Tennis job 1
   (record in JOBS.md first), judge it. PASS = the oracle reproduces at least one Tennis object byte-exact, or a named
   refusal that W5 must route around (e.g. compiler mismatch).
Receipt: toolchain note, the 60-row sample table path, A/A job id and verdict, commits.
