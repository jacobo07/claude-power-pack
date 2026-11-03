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

## Next (in order)
4  Add V-RF-OM-* gates to tools/test_reconstruction_factory.py: registry grades (Shape/CircleShape/RectShape VTABLE with kinds), a CANDIDATE case (single-kind), prototype propagation (override flags), field_accesses on rf_circle_ctor == [(0,'stw'),(8,'stw')], class_decls compiles, virtual-call pipeline: OM skeleton (rf_call_area, rf_total_area, rf_scale_all) -> search(extra={'vslot_to_method': ...}) -> certify; drills. Check whether skeletons for rf_total_area/rf_scale_all now exist (regen printed 48 skeletons; rf_scale_all new) and V-RF-SEARCH (which uses plain search) still passes: virtual-call skeletons need extra=; V-RF-SEARCH currently passes for 48? verify.
5  method_graph, genome, nsm (refuted_operator(fn,cls,op)/record(fn,cls,op,why) is the interface search_plan expects), atoms, claims, maturity, cbr, heldout (release gate over heldout.seal.json), frontier, invalidation, provenance.
6  PARITY.md/json, liveness (modules/liveness/reachability.py: declare modules/reconstruction_factory in vault/liveness/reachability_registry.json), CHECKPOINT_COMPLETE with --residual GAP rows: m2c/objdiff adapters unexercised; denylist hash coverage; 22 functions without operator-reachable skeleton; return types of virtual methods default to s32; field layout only from this-call evidence; mwcc adapter unexercised.
Tokens: steps 1-3 green (moratorium satisfied). ~4M used at handoff of epoch 2 (context wall).
