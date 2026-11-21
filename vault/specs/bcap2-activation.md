---
covers: [bcap2-activation, ccf-creative-checks, brand-truth, territories, visual-dna, provider-policy, identity-set, critique, techniques, floor-guard]
tier: T2
owner_decision: "Owner 2026-11-20 'rec' (pane adcdff7b): write the activation spec for BI-08..14 + floor_guard"
status: "PROVEN 2026-11-21 -- slice A 37ee0072 (AC1-AC6), AC7 04d510df+fe7c84ab, slice B (a) e15f415d report-only. Measured: test_ccf 16 passed, test_asc_ccf PASS, test_bcap2_brand PASS, test_bcap2_activation V-BCAP2-ACT PASS, done_gate BCAP2_DONE_GATE PASS; reachability shows creative_checks + the 7 modules REACHABLE (its exit 1 is 57 non-BCAP-2 offenders owned by other panes)"
---
# BCAP-2 activation: make the absorbed checks run on the real path

## Problem (measured 2026-11-20 on feature/knowledge-acquisition 48416891)
BCAP-2 closed with every item PARTIALLY_PROVEN and none ACTIVATED. Seven CCF modules pass `tools/test_bcap2_brand.py`
but are declared LIBRARY: `modules/ccf/cli.py` (`init`, `compile`, `generate`, `select`, `package`) calls none of them,
so a CCF run today behaves exactly as before BCAP-2. Same for `modules/sqi/floor_guard.py` (diff-scoped test-weakening
guard): nothing in the commit or done path invokes it. A gate that is never reached is indistinguishable from none
(Liveness Standard).

| module | public API | natural call site |
|---|---|---|
| brand_truth (BI-08) | `intake(brief_id, items)` | `init --brief` / `compile` |
| territories (BI-09) | `check_territories(concepts, narrow_brief)` | `generate`, after the concept loop |
| techniques (BI-10) | `check_hypothesis(h)`, `summarize(hs)` | `generate`, per concept |
| identity_set (BI-11) | `validate_set(s, mode, original)` | `generate` (when an identity set is declared) |
| visual_dna (BI-12) | `validate(dna)`, `tokens_for(dna, project_tokens)` | `compile` / `package` |
| provider_policy (BI-13) | `route(intent)`, `plan_call(model, fallback, n, imports)` | `generate`, BEFORE `adapter.generate` |
| critique (BI-14) | `build_critique`, `qualifies`, `approve(critiques, id, actor)` | `select` |

## Falsifiers already in hand (why this is not "just call them")
1. `config_schema.CONCEPT_REQUIRED_FIELDS` = id, font, colours, bg, wordmark, avoid, icon. No `mechanism`,
   `brand_fact`, `hypothesis`, identity axes or critique instruments exist in any current config. Enforced,
   `check_territories` returns FAIL for every existing project ("missing mechanism or brand_fact").
2. `provider_policy.route` with `deterministic_possible` absent returns DETERMINISTIC_VECTOR. Enforced before
   `adapter.generate`, it stops every image generation of every current project.
3. `critique.approve` needs >=2 qualifying critiques and a human actor; no project records critiques, so enforced it
   blocks every `select`.
4. `config_schema.validate_config` ignores unknown keys, so new optional fields and a top-level `creative_checks` key are
   backward compatible (no schema version bump needed).

## Design
**One rule: absent is UNASSESSED, never FAIL; a check enforces only where the project declares it.**
- New `modules/ccf/creative_checks.py`: `run(stage, config, spec, **ctx) -> {check: {status, detail}}` with status in
  PASS | FAIL | NARROW_BRIEF_EXCEPTION | UNASSESSED (+ the module's own verdict kept verbatim). It calls the seven
  modules; it never repairs input and never calls a provider.
- `cli.py` calls it at the sites in the table and writes `<project>/ccf/creative_checks.json` (one record per stage,
  with the module versions/sha). One summary line per run, e.g. `creative checks: territories UNASSESSED (0/3 declared)`.
- Enforcement is opt-in per check: `config["creative_checks"] = {"territories": "enforce", ...}` (default `report`).
  In `enforce`, FAIL returns EXIT_GATE_BLOCKED at that stage; for provider_policy it is decided BEFORE the provider call
  (same rule as the trademark BLOCK, ASC-04 D4). UNASSESSED under `enforce` is also a block: the project asked for the
  check and did not supply its inputs.
- Dry-run prints the report and persists nothing (current dry-run contract).
- Liveness: the seven modules move from LIBRARY to reachable through `cli.py`; `--baseline` after the change.

### floor_guard (slice B, separate, needs an Owner pick)
`floor_guard.run(repo, base)` judges a diff for weakened constraints. Candidate consumers, one to choose:
(a) `vault/programs/bcap-2/done_gate.py` and the PP done path (report only);
(b) a PreToolUse/commit hook in `~/.claude` (HR-001 territory: global config, Owner-run step);
(c) `tools/test_*` gates that already diff the tree. Slice A does not depend on it.

## Acceptance criteria (each driven from both poles)
- AC1 every existing CCF fixture/project (`modules/ccf/test_ccf.py`, `tools/test_asc_ccf.py`, test_bcap2_brand) still
  passes byte-for-byte: no exit code, prompt, scan or artifact changes in `report` mode.
- AC2 a config with no new fields yields 7x UNASSESSED in creative_checks.json and exit unchanged.
- AC3 per check, `enforce` + a FAIL input returns EXIT_GATE_BLOCKED at the right stage; `enforce` + a PASS input passes;
  `enforce` + absent input blocks with "inputs not declared".
- AC4 provider_policy under `enforce` refuses before `adapter.generate` (adapter call count 0, pinned with a fake adapter).
- AC5 critique under `enforce`: `select` without >=2 qualifying critiques and a human actor is blocked; `--by llm` can
  never approve (keeps BR-16).
- AC6 seeded mutants: making UNASSESSED count as PASS, or skipping the enforce branch, turns a named pole red.
- AC7 `python modules/liveness/reachability.py` shows the seven modules reachable; done_gate PASS.

## Rollback
Report mode changes no behaviour, so rollback of slice A is removing the `creative_checks` calls (one commit revert).
Per project, deleting `config["creative_checks"]` returns it to report mode.

## Out of scope
CLI wiring of BI-15..35, BI-24 (brand book PDF), Phase 8 reads, Ruflo activation, floor_guard consumer choice.
