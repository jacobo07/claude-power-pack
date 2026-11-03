# Reconstruction Factory (general) -- workstream STATE

Mission m-a9d8915ae366, branch recon-factory/general (base 70c2fde4). Spec: vault/specs/reconstruction-factory-general.md.

## Done (committed)
- Unit 1: fixtures/synthetic (68 fns: 60 dev + 8 held-out, recon.toml), elf.py, manifest.py (strict), toolchain.py (gcc-ppc, mwcc, external_status).
- Unit 2: tools/recon_public_gate.py + tools/test_recon_public_gate.py (11 gates, drills 11/11 red), gatekit.py (Kit, patched).
- Unit 3a: judge.py (exact compare, masked bytes, reloc rows, data check, pct).

## Decisions
- Toolchain: devkitPPC powerpc-eabi-gcc/g++ (/opt/devkitpro/devkitPPC/bin) has a C++ front end; powerpc-linux-gnu-gcc has none (C only). m2c/objdiff are not installed: lift = fixture skeletons (GAP row: m2c adapter unexercised).
- Corpus is compiled at test time into temp dirs; no objects committed. Targets = ref sources compiled with the manifest recipe (o0, a few o1).
- Gate denylist is SHA-256 hashed tokens (built-in floor + --deny-file/RECON_GATE_DENY); Owner should extend with the full private list's hashes (GAP).
- Gates use gatekit.Kit; `--drills` sabotages one instrument per gate and requires RED.

## Done since (epoch 2)
- 3b-3e committed: core.py, certify.py (ELF+objdump independent, controls, UNDERDETERMINED_TOOLCHAIN, held-out refusal), fingerprint/causal_diff/residual, operators/search/search_plan/permute, build_twin, tools/rf_gen_corpus.py (skeleton/mutants/seal), tools/test_reconstruction_factory.py (16 V-RF gates, drills 16/16 red).
- Step 4 IN PROGRESS (uncommitted -> committed in the handoff commit): om.py (tables/installs/vcalls/registry/propagate/root_methods/field_accesses), om_skeleton.py (class_decls, method_to_vslot, vslot_to_method), rf_shape_area added to corpus (defines Shape vtable), operators commute_call_add/assign_via_tmp/tmp_assign_inline, search/permute accept extra={name: sites(text)} context operators.
- Finding: a raw vptr slot call compiles BYTE-IDENTICAL to the method call, so OM skeletons are lift(inverse-op(ref)); rf_gen_corpus.lifted_skeleton does this.

## Done since (epoch 3)
- Step 4 closed: V-RF-OM-* gates (registry, propagation, this-call, decls, virtual-call pipeline) + drills. rf_call_area/rf_total_area have NO committed skeleton (raw slot form compiles byte-identical); V-RF-OM-VCALL lifts the ref with method_to_vslot at test time.
- Step 5a committed: nsm.py (SOUND: only deterministic refutations; NO_GAIN is advisory -- pruning on no-gain made rf_collatz unsolvable; run memo), method_graph.py (prior + supercompiled macros + expand), genome.py. search() takes nsm/prior; search_plan prior weight x3. Gates V-RF-NSM/METHOD-GRAPH/GENOME.
- Step 5b (this commit): atoms.py, claims.py (ClaimStore; from_certificate(fn, cert, world)), invalidation.py (sequence diff, member-vs-type ids, include lines stripped; ground truth = recompile with edited header). Gates V-RF-ATOMS/CLAIMS/INVALIDATION.

## Next (in order)
5c  maturity.py (executable-predicate rubric, hashed contract, verify red when rubric edited), cbr.py (Birth dispositions INHERITED/ADAPTED/ALREADY_SATISFIED/NOT_APPLICABLE/CONFLICT/UNKNOWN per DISCOVERED input + Construction Return kinds), heldout.py (release gate over fixtures/synthetic/heldout.seal.json; certify already refuses unreleased), frontier.py (projection counts each function once), provenance. Gates + drills for each. Private references: t1 modules/recon_fabric/{maturity,cbr,frontier,provenance_cxx}.py (CODE ONLY).
6   PARITY.md/.json under vault/programs/reconstruction-factory/ (one row per mechanism: GREEN/GAP/NOT_PORTED, with proving command; wave scripts g4_*, ascension s9/s10b/s11, sweeps = NOT_PORTED), declare modules/reconstruction_factory in vault/liveness/reachability_registry.json and run python modules/liveness/reachability.py, then checkpoint CHECKPOINT_COMPLETE "recon general ready for public gate" with --residual GAP rows: m2c/objdiff adapters unexercised; mwcc adapter unexercised; denylist hashes need Owner's full list; 22 functions without operator-reachable skeleton; virtual-method return types default s32; field layout from this-call evidence only.
Tokens: steps 1-3 green. Epoch 3 ended at context wall (~177k) after step 5b.

## Done since (epoch 4)
- Step 5c committed: heldout.py (seal verify, leak scan, one-way release bound to a solver freeze), maturity.py (rubric contract frozen in maturity.contract.json), cbr.py (birth: one disposition per DISCOVERED input; return kinds with evidence), frontier.py (union counting, greedy plan, shuffle control), provenance.py (E0/E2/E3/NONE from the object). Gates V-RF-HELDOUT-RELEASE/PROVENANCE/FRONTIER/MATURITY/CBR, drills 32/32 red.
- FINDING (real): the leak scan caught generated skeletons and mutants of the 8 sealed functions in the dev tree. Generator no longer emits them; files removed. Seal unchanged.
- Decision: search/search_plan take nsm/prior by injection (no import), so maturity anchors for them are greps, not import edges.
- Decision: maturity anchor 10 of every dimension = OWNER_ACCEPTANCE.json (absent on purpose); the engine never self-grades to 10.
