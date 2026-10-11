# WU-W3b -- Tennis A/A job (continuation of W3 step 4; <= 1 GEX44 job)

Common brief: `PROGRAMME.md`. W3 receipt: `WU-W3-receipt.md`. Evidence so far: `evidence/w3/`, `TENNIS-TOOLCHAIN.md`.
Goal: Tennis job 1 = a certified A/A that proves the oracle reproduces at least one Tennis object byte-exact, or a named refusal.

Finding that makes this a build task: the capsule/judge chain is Resort-hardwired. `gex44/capsule_build.py:40,45` (SPLIT=certify_855e4ffe,
SEALED = 5 Resort ids), `candidate.py:49-53` (SPLIT_OUT, ASM_DIR, OBJ_DIR, L0_PATH), judge `match.py` reads the Resort retail DOL words.
Steps:
1. Candidates (already computed, `wst_tennis/w3/tennis_fns.json`): Tennis fns with exact Resort shape AND a SRC PROVEN donor, 179 of them,
   all 1-2 insns. Pick 3 distinct donor ids, e.g. fn_80209DD8 (donor main:80012E88), fn_802029B0 (donor main:801C333C), fn_802047D0
   (donor main:8010C960). Check each donor's source_text in the registry (levels.py SRC evidence bundle_sha256 -> src bundle).
2. Tennis target objects: from `wst_tennis/step0/split_sports/out/obj` (or re-run dtk on the .s units; read-only on SportsPackEP).
   Build a Tennis capsule (new entity ids `tns:<addr>`, own manifest) WITHOUT altering the Resort capsule or sealed set; parametrise
   SPLIT/ASM_DIR/OBJ_DIR/DOL by a module argument, default Resort (existing drills must stay green).
3. Judge: match.py needs the Tennis DOL words (`step0/disc/files/EU/sys/sports/SportsPackEP.dol`) and Tennis DTK operands. Prove it with a local
   judge control on the Tennis object pair BEFORE spending a job (positive: donor source object vs target; negative: one flipped word).
4. `stage.py build` -> `stage.py certify <tag>` (W2) -> record JOBS.md row 1 -> `stage.py send` -> wait -> judge. CURRENT_CAPSULE must equal
   the Tennis capsule or send refuses (W1 guard); document how you register it without disturbing the Resort CURRENT.
   Toolchain caveat: compiler is the Resort pin; a trivial-body A/A cannot detect a compiler mismatch (TENNIS-TOOLCHAIN.md).
5. If no safe parametrisation exists in this unit's budget, write a named refusal (what blocks the Tennis capsule) and stop with DONE:
   PASS = oracle reproduces one Tennis object byte-exact OR a named refusal W5 must route around.
Zero local compiles. Max 1 GEX44 job. Receipt `WU-W3b-receipt.md` (Status line per PROGRAMME.md), then commit.