---
status: APPROVED 2026-11-03 (Owner "y" on the general Reconstruction Factory plan)
covers: [reconstruction-factory, recon-general, recon-public-gate, synthetic-corpus, maturity-parity]
owner: modules/reconstruction_factory (port of the private recon_fabric engine)
budget: 50M worker tokens (low 35M / high 80M), model USD $0 (+$10 ceiling for one real LLM-fix lane check)
---

# Reconstruction Factory (general) — spec

## Goal
A game-agnostic program-reconstruction engine in this public repo with the SAME MATURITY as the private engine
(`modules/recon_fabric` on branch t1/campaign of the private factory), and ZERO content derived from any
commercial binary. Maturity is measured by a parity matrix, never asserted.

## Source of the port (read-only)
`/home/kobii/missions/t1-campaign/modules/recon_fabric/*.py` and `tools/test_recon_fabric*.py`, `tools/test_om_*.py`.
Read the CODE only. Never copy, open into this tree, summarise into docs, or paste: anything under `evidence/`,
`.local/`, `modules/recon_fabric/fixtures/`, any `.dol/.elf/.gz` blob, any m2c/objdiff output of the private target,
any `fn_80xxxxxx` address list, sha pins of the private binary, or held-out manifests (H, H2).

## Shape
- `modules/reconstruction_factory/`: the ported engine. Every path, binary, toolchain command, function list and
  flag string comes from a project manifest `recon.toml` (schema documented and validated; unknown key = refusal).
  Mechanisms to port (parity rows): exact certification (judge + cert contract, independent vs corroborating
  evidence, UNDERDETERMINED_TOOLCHAIN), fingerprint / causal diff / residual, search / search_plan / permute,
  Build Twin + toolchain discrimination, Object Model (vtables, vptr installs, prototype propagation, this-call),
  om_skeleton generator, Method Graph + Strategy Genome + supercompiled trajectories, Negative Search Memory,
  atoms/claims (WROS), maturity contract, CBR + Construction Return, held-out law (sealed set, release gate),
  frontier projection (counts once), invalidation, provenance.
- Wave scripts that only served one private wave (g4_*, ascension_s9/s10b/s11 tools, sweeps) are NOT ported;
  each is listed in the parity matrix as NOT_PORTED with a reason.
- Toolchains: adapters behind one interface. Public tests use GCC PowerPC (`powerpc-eabi-gcc` devkitPPC,
  `powerpc-linux-gnu-gcc`). An mwcc adapter may exist but is never shipped with a compiler binary and never
  required by a test. m2c and objdiff are external pinned dependencies (install doc + version check), not vendored.
- `fixtures/synthetic/`: ~60 ORIGINAL C/C++ functions written for this repo (plain C, structs, loops, switch,
  float, C++ classes with inheritance, virtual calls, ctors/dtors), compiled by the public toolchain into the target
  objects. Includes positive controls, negative controls, mutants, and a sealed synthetic held-out set used only
  through the release gate.
- `tools/recon_public_gate.py`: scans the tree (or a commit range) for derived content: `fn_80[0-9a-f]{6}` from the
  private target, private binary names/hashes/game titles, PowerPC disassembly not produced from fixtures/synthetic,
  `.dol/.elf/.iso/.wbfs` and opaque `.gz` blobs, `evidence/`, `.local/`. Exit 0 = clean. Driven at both poles in its
  own test (a planted violation per class is caught).
- `vault/programs/reconstruction-factory/PARITY.md` (+ `.json`): one row per private gate/mechanism -> public gate,
  status GREEN / GAP(reason) / NOT_PORTED(reason), with the command that proves it.

## Acceptance
1. `python tools/test_reconstruction_factory.py` (V-RF-*) green on the synthetic corpus, end to end: lift ->
   skeleton -> compile -> diff -> search -> certify, including at least one C++ virtual-call function certified exact
   and one negative control refused.
2. Every ported mechanism has a gate driven at both poles; drills (`--drills`) turn each named gate red.
3. PARITY.json has no unexplained row; GREEN covers every mechanism listed under Shape.
4. `python tools/recon_public_gate.py` exits 0 on the branch, and its test proves each class is caught.
5. `python modules/liveness/reachability.py`: the new module is reachable or declared.
6. Branch `recon-factory/general` starts at public main 70c2fde4 and contains only this work.

## Never
- Never commit derived content (above). Never push (the coordinator pushes after the gate). Never touch t1 or gen3.
- Never weaken a gate to reach parity: a mechanism that cannot be shown on the synthetic corpus is a GAP row.

## Rollback
Delete the branch; nothing else consumes it.
