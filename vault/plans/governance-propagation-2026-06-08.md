# PP Governance Propagation — Plan (approved 2026-06-08, SCS C43)

## Goal
Make PP governance (SDD-OS tiers, PRD/spec requirement, setup-scan) fire in ANY
repo automatically — not just security. Cross-repo, no per-repo config.

## FASE -1 finding (corrects the prompt's premise)
The cross-repo rail ALREADY exists: `tools/jit_skill_loader.py` (UserPromptSubmit
hook) runs in any cwd and feeds `modules/pp_agents/proactive_dispatcher.dispatch`
the real `prompt`+`cwd` via `_pp_proactive_inject`. All 11 signals already fire
cross-repo (incl. `pp-spec-guardian`). The gap is only: (a) `classify_tier`
exists but no signal calls it; (b) `scanner.scan` is cross-repo but `/scan-repo`
only prints — no persisted registry to ask "is this repo scanned?".

So: compose existing cwd-aware primitives (`spec_gate.classify_tier`,
`check_spec_gate`, `setup_os.scanner.scan`). Do not rebuild.

## Decision (Owner-approved)
`sdd_tier` TAKES the spec-governance slot in the dispatcher (richer than
`spec_compliance`: tier + spec). `spec_compliance.py` and its unit tests stay
intact; only the dispatch line swaps. No double advisories.

## Deliverables
- G1 `signals/sdd_tier.py` — classify_tier + check_spec_gate; advisory only if
  tier >= 2 AND no spec; silent for Tier 0-1.
- G2 `signals/setup_scan.py` — `setup_os/registry.has_profile(cwd)`; missing ->
  advisory `/scan-repo`; silent if present.
- G3 register G1+G2 in `proactive_dispatcher` (swap spec slot -> sdd_tier; add
  setup_scan). Throttle: sdd_tier 5 min, setup_scan 24 h.
- G4 `/scan-repo --save` -> `setup_os/registry.save_profile(cwd, scan(cwd))`;
  central store at `vault/setup_os/profiles/<slug>_<pathhash>.json` (in PP repo,
  never the scanned repo).
- G5 one-time scan + save: KobiiCraft, CostaLuz, WhisprFlow.
- G6 `tools/test_governance_propagation.py` (7 V-gates incl. cross-repo from a
  /tmp dir), SCS C43, push (REMOTE_DELTA 0 0).

## Done-gate
"build user auth" (any repo) -> Tier 2 advisory; "fix typo" -> silence;
/scan-repo in KobiiCraft -> real KobiiCraft profile; 3 repo profiles saved;
test 7/7 hermetic; pytest no regression; SCS C43 sealed; REMOTE_DELTA 0 0.
