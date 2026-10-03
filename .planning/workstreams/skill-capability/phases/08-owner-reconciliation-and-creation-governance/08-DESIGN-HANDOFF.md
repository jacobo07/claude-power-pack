# Phase 8 design hand-off (planner stopped at the mission context wall, epoch 3)

Plan-time values measured on gex44 at HEAD 30d3baa6. Plans must RE-READ every figure at execution time.

## Verifier contract (CE file, read-only, rebound by tools/test_skill_capability_program.py)
- MERGED_INTO_EXISTING_OWNER / DEFERRED_STRONGER_OWNER need `owner` (ref equals a frozen owner string exactly) and
  `handoff` (file under `vault/programs/skill-capability/handoffs/`, contains `[<P>]` and a frozen owner string
  verbatim, LF sha256 pin, `handoff_landed` = a commit touching it that is not an ancestor of FROZEN_AT 217d72b5).
- IMPLEMENTED_AND_VERIFIED needs `gate` + `prg`; L5 runs argv via sys.executable.
- L7: reason must not match `(?i)\b(later|todo|tbd|future work|eventually|someday)\b` ("deferred" is allowed).
- `--pillar X` = final=True, only=[X]; L1 still checks all pillars' owners exist.
- Frozen owners: I `modules/liveness/reachability.py`, `vault/programs/cognitive-economy/ledger.json`;
  J `~/.claude/skills/skill-creator/SKILL.md`; K `vault/specs/agent-capability-virtualization.md`,
  `modules/capability_runtime/agent_spec.py`; L `modules/cognitive_os/co_12_telemetry.py`, the CE ledger;
  M `tools/usage_index.py`.
- State lines I..M are `{"terminal": null, "evidence": [], "savings": []}`. Savings exist only for A (5 turns,
  upper_bound, D-CARD) and B (9000 tokens, upper_bound, D-LISTING).

## I (MERGED) sources
- `python3 modules/liveness/reachability.py --json` (0.13 s, exit 1; keys passed/offenders/rows; 490 rows,
  310 REACHABLE, 180 ORPHAN, 64 offenders). `gate(repo_root)` accepts a root -> run on a `git archive HEAD` export.
- UNCHECKED: `modules/capability_runtime/retirement.py` (`_audit_frontmatter`) may be an existing retirement owner;
  read before planning I/K.
- Skill candidates = gex44-plane coverage `none` (D-live-gex44.json: 161 skills, 159 none; built by
  `test_skill_coverage.compute(repo, disp_text, recs)`) minus skills invoked in C-window-G.json (gsd-autonomous,
  gsd-code-review, gsd-execute-phase, gsd-plan-phase; window 2026-09-26T18:05Z..2026-10-03T18:05Z, host
  kobicraft-gex44, 189 files). Label host+window; a candidate is never a deletion verdict; nothing is deleted.

## K (MERGED) sources
- Producer `tools/skill_opportunity_signals.py` (KIND capability_opportunity, CAPABILITY
  concurrent-writers-shared-tree, writes only via record_signal). Never run `sync` (writes); `report` reads
  `~/.claude/state/co12_readiness/signals.jsonl`. gex44 has no `~/.claude/state/doctrine-cards/` -> row count
  UNMEASURED here, laptop count is a [K] item.
- No-router sweep: files added in FROZEN_AT..HEAD under modules/ and tools/ (plan time 12, all tools/). The range
  includes foreign commit 6d3113b8 (incremental-cognition) -> sweep covers a superset; say so. Markers `def route(`,
  `class .*Router`, route/router in filename. Positive controls: modules/cost_collapse/router.py:65,
  modules/cognitive_os/router.py:75, modules/knowledge_acquisition/routing.py:189.

## L (DEFERRED) sources
- Name search finds no Context Compiler implementation (`git ls-files | grep -icE "context[_-]?compiler"` = 0;
  no `class ContextCompiler|def compile_context|context_compiler` in *.py/*.js). Aperture: by name only.
- Contradicting claim to surface: `vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md:63` ("Memory Runtime and Context
  Compiler EXISTS_AND_COMPLETE"); also `vault/audits/frontier28/VERDICTS.md:253`,
  `vendor/genesis-suite/.../genesis-batch-drafts.cjs:3`.
- signals.jsonl writers at HEAD (positive controls): co_12_telemetry.py:111, tools/test_agent_telemetry.py:271,
  tools/test_co12_signal_race.py:47; added lines in FROZEN_AT..HEAD must add no writer.

## M (MERGED) sources
- Do not grep evidence for "token" (hits CARD_TOKEN); use ledger savings[] + B-listing-floor.md, E-contribution.md.
- No-cost-model sweep: same aperture as K; positive control tools/usage_index.py (62 usd/cost/price hits).

## J (IMPLEMENTED) design
- Frontmatter: `opportunity_detector: <repo-relative path>` OR `opportunity_detector: none` +
  `opportunity_detector_reason: <non-blank>`. Non-standard keys already load (origin:, tools:, trigger:); grammar
  `skill_index._FM_RE` (modules/skill_router/skill_index.py:123); F body_sha strips frontmatter.
- UNCHECKED: allowed keys in `~/.claude/skills/skill-creator/scripts/quick_validate.py`.
- Coverage cross-check on committed blobs: `discover_cards(<empty tmp>, dispatcher_text=<blob>,
  hook_texts=<tracked hooks blobs>, read_disk=False)`, `opportunity_adapters(<empty tmp>, adapter_texts=<tracked
  tools/*.py blobs>)`, then `coverage(skill, cards, adapters)`. Repo classes: concurrent-writers-shared-tree ->
  declare hooks/doctrine_cards.js; destructive-state-authorization -> none + reason (card only); other 22 -> none.
- Clauses (independent, zero declaration lines -> UNMEASURED): per skill DECLARED, FORM, TARGET, COVERAGE-AGREES;
  gate FLOOR, POSITIVE-CONTROL, EVIDENCE-CURRENT; git failure -> INCONCLUSIVE.
- Drills/full fail sets: undeclared {DECLARED,FORM,TARGET,COVERAGE-AGREES}; duplicate key {DECLARED};
  `./hooks/doctrine_cards.js` {FORM}; none w/o reason {TARGET}; untracked path {TARGET,COVERAGE-AGREES}; DSA declares
  its card {COVERAGE-AGREES}; CWST declares none {COVERAGE-AGREES}; empty population {FLOOR,POSITIVE-CONTROL};
  CWST removed {POSITIVE-CONTROL}; CRLF PASS; worktree-only edit judged on blob; git missing INCONCLUSIVE; each
  singleton drill gets a forced-PASS flip.

## Cross-pillar cost of declaring all 24 skills
- Editing CWST and DSA SKILL.md turns G and H red until re-derivation: commit SKILL.md edits -> `python3
  tools/card_lineage.py --trailer-for <skill>` per skill, replace trailers -> commit cards -> `python3
  tools/skill_mirror_drift.py --record-cards` -> `python3 tools/test_skill_drift.py --write-evidence` and
  `python3 tools/test_card_lineage.py --write-evidence` -> commit -> move state.G pins (G-lineage.md,
  card_source_digests.json) and state.H pins (H-drift.md, card_source_digests.json).
- H gex44 recording pinned to 97ded664: the other 22 edits do not move it. Do not edit repo CLAUDE.md (D-coverage.md
  cites its line numbers). Measure tools/test_cdio_mobile.py:194 (repo vs live mobile-app-ui-design/SKILL.md)
  before/after; never weaken it. Re-run --pillar F (its gate builds a recording at HEAD).

## Proposed plans
| Plan | Wave | Content |
|---|---|---|
| 08-01 | 1 | J gate: tools/skill_creation_gate.py, tools/test_skill_creation_gate.py, evidence/J-creation-gate.md |
| 08-02 | 2 (after 08-01) | declarations in all 24 SKILL.md derived from D classes by script; G/H re-derivation + pin moves |
| 08-03 | 1 | tools/skill_handoffs.py, tools/test_skill_handoffs.py, handoffs/{I,K,L,M}.md (first line `[<P>] -> <owner>`) |
| 08-04 | 3 | ledger lines I/J/K/L/M; owner-bundle [I][J][K][L][M]; regression --pillar A..M |

Expected terminals: I MERGED, J IMPLEMENTED_AND_VERIFIED, K MERGED, L DEFERRED_STRONGER_OWNER, M MERGED.
Owner-reserved (owner-bundle lines, never checkpoints): [J] skill-creator emitting the field on live ~/.claude;
[I] point the CE mission at handoffs/I.md; [L] point the CE mission at handoffs/L.md and adjudicate the USIRC claim;
[K] laptop CO-12 row count.
