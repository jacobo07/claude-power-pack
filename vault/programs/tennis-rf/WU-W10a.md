# WU-W10a -- Tennis capsule profile, part 1: one profile through the six Resort-hardwired modules (zero jobs)

Common brief: `PROGRAMME.md`. Owner 2026-10-11: "si" to W3b option (a), a real Tennis oracle, so that W8/W9 report
compile-verified rates instead of UNKNOWN. Read `WU-W3b-receipt.md` first; it lists every blocker with its line.

Facts (W3b, verify each with one read before relying on it):
- `capsule_build.resolve_units` (l.251-320) derives units from the Resort ledger and refuses on SEALED_SET_MISMATCH /
  DONOR_COUNT / MODEL_SET_MISMATCH / UNIT_COUNT. `resolve_targets` needs census + EXPECTED_TARGETS 2685.
- Resort paths are hardwired in capsule_build.py:40-42, candidate.py:46-49, pack_inputs.py:22, reproduce.py:35,
  propagate.py:125, and sda_stub.py:91,113 (default arg candidate.ASM_DIR).
- Tennis inputs: split/asm/obj under `wst_tennis/step0/split_sports/out/`, DOL
  `step0/disc/files/EU/sys/sports/SportsPackEP.dol`, candidates `wst_tennis/w3/tennis_fns.json`.

Steps:
1. RED first: a new `gex44/test_tennis_profile.py` (gate style), with these gates:
   a. `profile("resort")` returns exactly today's constants (the Resort default is byte-identical);
   b. `profile("tennis")` resolves every path to an existing Tennis file or dir;
   c. a Tennis capsule built from a 3-donor set (the W3b ids) passes `resolve_units` with Tennis counts, while the
      same set under the Resort profile still refuses;
   d. entity ids are `tns:<addr>` and never collide with Resort ids.
2. Add ONE profile dict (split, asm, obj, dol, L0, ids, expected counts, sealed set, F root) and a `--profile`
   argument, default `resort`, then thread it through the six modules. Remove no Resort constant; route it
   through `profile("resort")`.
3. Re-run every suite you touched: test_candidate, test_custody, test_reproduce, test_fanout_preconditions, and
   capsule_build's own tests. Resort must stay exactly as green as before; the two test_candidate failures W1 found
   (V-CAND-OPERANDS-NORMALISED, V-SDA-PRECHECK-REAL) were already there before this unit. Run with
   `C:\Program Files\Git\cmd` on PATH (the EOL gate shells out to git).
4. Build the Tennis capsule locally (no send, no certify) for the 3 W3b donors plus the 12 W5a functions (W5a
   receipt and `evidence/w5a/`). Write its manifest path and sha256 into the receipt.
5. Mutation drill on an isolated copy: make `profile("tennis")` fall back to a Resort path, and make the Resort
   default change. Each must go RED.
Do NOT touch match.py, custody or CURRENT_CAPSULE: that is W10b. Zero GEX44 jobs, zero local compiles.
If the unit is too big, use the continuation rule in PROGRAMME.md step 4 (id W10a-b).
Receipt (write it to vault/programs/tennis-rf/WU-W10a-receipt.md, Status line per PROGRAMME.md step 3; the chain
reads only that file): commits, the per-suite counts before/after, the capsule manifest path + sha256, drill result.
