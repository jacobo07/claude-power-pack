# Sleepy Skills — frontend pilot (2026-06-02, BL-SLEEPY-SKILLS-001)

Plan-backup / decision record. Doctrine seal: SCS C30 in
`vault/knowledge_base/apex_baseline_doctrine.md`.

## CONTRATO DE REALIDAD (met)
"build me a landing page with Tailwind" → `frontend-design` (+peers) is
surfaced with no command; "fix the JWT auth bug" → nothing fires.
Empirically: V-JIT-INTEGRATION (FE card present, BE clean) + 6/6 accuracy.

## FASE -1 findings that reshaped the plan
- The JIT loader (`tools/jit_skill_loader.py`) is ALREADY a sleepy-by-default
  UserPromptSubmit injector — but only for the 11 vendored Apollo modules.
  Its extension idiom is a decorator on `run()` (5 already exist).
- `jit_skill_loader_v2.js` does NOT exist (plan's JS path was moot).
- `modules/skill_router/` was greenfield.
- Premise correction: skills are ALREADY body-lazy (loaded on Skill-tool
  invocation); only ~1-line descriptions are always-on. The "110K wasted"
  justification is false. The real gap was AUTO-ACTIVATION, not waste.
- Skill authors already wrote triggers in frontmatter `description` —
  a far better source than the plan's word-frequency counting.

## Architecture decision (Owner-confirmed)
- **Hybrid** (not A or B-strict): testable `modules/skill_router/`
  (index + classifier) wired as ONE new decorator `_skill_router_inject`
  on the existing `run()`. No second hook.
- **Pointer cards** (~80 tok, like `LATERAL_CARD`), not skill bodies.

## What shipped
| File | Role |
|---|---|
| `modules/skill_router/skill_index.py` | frontmatter catalog, word-boundary domain classify, disk cache (1h TTL), hot-path `load_cached_index()` vs off-path `build_index()` |
| `modules/skill_router/intent_classifier.py` | strong/medium/negative signals (EN+ES), ≥0.6 wakeup, ctx>0.75 sleep, ≤2 skills, candidate-pool-in (no disk) |
| `tools/jit_skill_loader.py` | `_skill_router_inject` decorator + index pre-warm in `_warm_run()` |
| `tools/test_sleepy_skills.py` | 8 V-gates |
| `tools/verify_spp.py` | `sleepy-skills` umbrella row (strict) |

## Evidence
- test_sleepy_skills 8/8 · classify accuracy 6/6 · dataset-build 48/48 (no regression)
- verify_spp `sleepy-skills` row rc=0 · hot-path added cost ~24ms (classify 1ms), warm pre-builds cache
- pp-code-reviewer: APPROVE, 0 findings

## Honest scope notes
- `context_pct` is not threaded from the hook (payload has no context field);
  forced-sleep is API-tested only; system austerity = HR-CASCADE-005. Commented at call site.
- Skill RANKING for build prompts is rough (`anydesign` can edge `frontend-design`);
  both are named in the top-2 card. Future ranking refinement.
- Frontend pilot only. Adding a domain = extend `INTENT_SIGNALS` + tests.
- UKDL "skills-always-active" trap NOT sealed: its premise (token waste) is false
  (skills are already lazy). The real lesson is captured in SCS C30 instead.
