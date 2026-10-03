[I] -> modules/liveness/reachability.py

Handoff of skill-capability pillar [I] (lifecycle / retirement / self-pruning / GC), predicted MERGED_INTO_EXISTING_OWNER.

Frozen rule (ledger `frozen.pillars`):

> merged into cognitive-economy pillar T; this program hands over its retirement candidates with evidence and deletes nothing

Frozen owners: `modules/liveness/reachability.py`, `vault/programs/cognitive-economy/ledger.json`.

- measured_at_commit: d0f7bab78458471956fa7b9c005f73c77185e35b
- freeze: 217d72b5944a664fbc0baa1060c04617ff10f481
- host: kobicraft-gex44
- plane: committed blobs at measured_at_commit (git grep / cat-file / diff / archive), never the working tree
- produced by: python3 tools/skill_handoffs.py --write I
- claim: PASS reachability=PASS retirement=PASS nowrite=PASS skills=PASS

## Commands and observed output

| command | observed |
|---|---|
| `git archive --format=tar d0f7bab7  (extracted to a temporary directory)` | 72908800 bytes, 5000 members, 0 refused by the data filter |
| `HOME=<empty tmp> python3 modules/liveness/reachability.py --json  (cwd = export)` | rc=1, rows 490, offenders 75 |
| `HOME=<empty tmp> python3 modules/capability_runtime/retirement.py --json  (cwd = export; never --record)` | rc=0, verdicts 13 |
| `git status --porcelain -- vault/capability_runtime vault/liveness vault/programs/cognitive-economy  (before == after); export tree and HOME compared` | watched paths, export tree and HOME unchanged |
| `coverage none rows of evidence/D-coverage.md section '## Plane gex44' at d0f7bab7, cross-checked against evidence/D-live-gex44.json, minus evidence/C-window-G.json key skills` | 161 skills, 159 none, 4 invoked, 155 candidates |

## Claim parts

| part | outcome | reason |
|---|---|---|
| reachability | PASS | 490 rows parsed, 83 candidates |
| retirement | PASS | 13 verdicts parsed |
| nowrite | PASS | watched paths, export tree and HOME unchanged |
| skills | PASS | 155 skill candidates |

## Aperture

- Modules: the reachability scanner's own population (packages under `modules/`), run on a `git archive` export of the measured commit with HOME set to an empty directory, so live ~/.claude seeds are not merged (plan-check W1). A host's live install adds seeds, so a module listed here can be reachable on that host; this list is the committed-blobs plane only.
- Skills: the coverage plane recorded on one host and the invocation window of pillar C on that host, both committed evidence. A skill invoked only outside the window, or on another host, is listed.

## Evidence

### Module candidates (plane: committed export of d0f7bab7, HOME empty)

Rows 490; by status ORPHAN 191, REACHABLE 299; gate offenders 75; gate passed False.
Not REACHABLE, counted by declared class (declared rows are alive by declaration and not listed): LIBRARY 56, PLANNED 52, undeclared 83.
Candidates (status not REACHABLE, class absent or DEPRECATED): 83. `gate offender` = no (the module is in the registry's standing debt `known_orphans`).

| module | status | class | gate offender | via | note |
|---|---|---|---|---|---|
| arch-decision/test_closed_loop | ORPHAN | - | no | - | - |
| arch-decision/test_v_block | ORPHAN | - | no | - | - |
| capability_runtime/agent_bundle | ORPHAN | - | yes | - | - |
| ccf/test_ccf | ORPHAN | - | no | - | - |
| code_review/__init__ | ORPHAN | - | yes | - | - |
| cognitive_os/hibernate_runner | ORPHAN | - | yes | - | - |
| craif/oier | ORPHAN | - | yes | - | - |
| dataset_first/transduction | ORPHAN | - | yes | - | - |
| deployment/test_v_block | ORPHAN | - | no | - | - |
| done_gate/architectural_truth | ORPHAN | - | yes | - | - |
| fable_distillation/fd_04_acceleration | ORPHAN | - | yes | - | - |
| gsd_x/goal/__init__ | ORPHAN | - | yes | - | - |
| gsd_x/goal/bind_mission | ORPHAN | - | yes | - | - |
| gsd_x/goal/brief | ORPHAN | - | yes | - | - |
| gsd_x/goal/contract | ORPHAN | - | yes | - | - |
| gsd_x/goal/convergence | ORPHAN | - | yes | - | - |
| gsd_x/goal/engine_identity | ORPHAN | - | yes | - | - |
| gsd_x/goal/epoch | ORPHAN | - | yes | - | - |
| gsd_x/goal/git_state | ORPHAN | - | yes | - | - |
| gsd_x/goal/judge | ORPHAN | - | yes | - | - |
| gsd_x/goal/log | ORPHAN | - | yes | - | - |
| gsd_x/goal/providers/__init__ | ORPHAN | - | yes | - | - |
| gsd_x/goal/providers/claude | ORPHAN | - | yes | - | - |
| gsd_x/goal/providers/codex | ORPHAN | - | yes | - | - |
| gsd_x/goal/providers/gate | ORPHAN | - | yes | - | - |
| gsd_x/goal/providers/long_run | ORPHAN | - | yes | - | - |
| gsd_x/goal/reconcile | ORPHAN | - | yes | - | - |
| gsd_x/goal/sweep | ORPHAN | - | yes | - | - |
| gsd_x/mission/__init__ | ORPHAN | - | yes | - | - |
| gsd_x/mission/closure | ORPHAN | - | yes | - | - |
| gsd_x/mission/contract | ORPHAN | - | yes | - | - |
| gsd_x/mission/coverage | ORPHAN | - | yes | - | - |
| gsd_x/mission/obligation | ORPHAN | - | yes | - | - |
| gsd_x/mission/store | ORPHAN | - | yes | - | - |
| gsd_x/mission/structured_facts | ORPHAN | - | yes | - | - |
| hard_rules/writer | ORPHAN | - | yes | - | - |
| keos_qwen/__init__ | ORPHAN | - | yes | - | - |
| keos_qwen/goals/__init__ | ORPHAN | - | yes | - | - |
| keos_qwen/goals/fire | ORPHAN | - | yes | - | - |
| keos_qwen/goals/seed_goals | ORPHAN | - | yes | - | - |
| keos_qwen/ledger/__init__ | ORPHAN | - | yes | - | - |
| keos_qwen/ledger/ledger | ORPHAN | - | yes | - | - |
| keos_qwen/outcome | ORPHAN | - | yes | - | - |
| keos_qwen/probe/__init__ | ORPHAN | - | yes | - | - |
| keos_qwen/probe/agentic_loop | ORPHAN | - | yes | - | - |
| keos_qwen/score/score_corpus | ORPHAN | - | yes | - | - |
| knowledge_acquisition/__init__ | ORPHAN | - | yes | - | - |
| knowledge_acquisition/boundary | ORPHAN | - | yes | - | - |
| knowledge_acquisition/classifier | ORPHAN | - | yes | - | - |
| knowledge_acquisition/cli | ORPHAN | - | yes | - | - |
| knowledge_acquisition/corpus_parser | ORPHAN | - | yes | - | - |
| knowledge_acquisition/engine3 | ORPHAN | - | yes | - | - |
| knowledge_acquisition/eva_adapter | ORPHAN | - | yes | - | - |
| knowledge_acquisition/expectation | ORPHAN | - | yes | - | - |
| knowledge_acquisition/models | ORPHAN | - | yes | - | - |
| knowledge_acquisition/provenance | ORPHAN | - | yes | - | - |
| knowledge_acquisition/queues | ORPHAN | - | yes | - | - |
| knowledge_acquisition/raw_vault | ORPHAN | - | yes | - | - |
| knowledge_acquisition/routing | ORPHAN | - | yes | - | - |
| knowledge_acquisition/runlock | ORPHAN | - | yes | - | - |
| knowledge_acquisition/runner | ORPHAN | - | yes | - | - |
| knowledge_acquisition/session | ORPHAN | - | yes | - | - |
| knowledge_acquisition/store | ORPHAN | - | yes | - | - |
| monitoring/monitor | ORPHAN | - | yes | - | - |
| monitoring/observe | ORPHAN | - | yes | - | - |
| osa/gpu_eyes | ORPHAN | - | yes | - | - |
| pp_agents/signals/cascade | ORPHAN | - | yes | - | - |
| pp_agents/signals/error_recurrence | ORPHAN | - | yes | - | - |
| pp_agents/signals/premise_risk | ORPHAN | - | yes | - | - |
| pp_agents/signals/spec_compliance | ORPHAN | - | yes | - | - |
| rule_compiler/reconcile | ORPHAN | - | yes | - | - |
| session_resilience/integration | ORPHAN | - | no | - | - |
| session_resilience/multi_window | ORPHAN | - | no | - | - |
| session_resilience/resume_identity | ORPHAN | - | no | - | - |
| session_resilience/snapshot_versioning | ORPHAN | - | yes | - | - |
| session_resilience/ui_state | ORPHAN | - | no | - | - |
| sqi/ratchet | ORPHAN | - | yes | - | - |
| surface_architecture/verticals/design_md_adapter | ORPHAN | - | yes | - | - |
| surface_architecture/verticals/prd_adapter | ORPHAN | - | yes | - | - |
| surface_architecture/verticals/surface_phrases | ORPHAN | - | yes | - | - |
| tower/donegate | ORPHAN | - | yes | - | - |
| tower/ratchet | ORPHAN | - | yes | - | - |
| uqf/auditor | ORPHAN | - | yes | - | - |

### Adjacent evaluator: modules/capability_runtime/retirement.py (DH-01)

Propose-only evaluator of the `retirement_condition` of capability contracts (`vault/capability_runtime/contracts/*.json`). It enumerates contracts, not modules or skills, and is not a frozen owner of I; its `liveness_reachability` probe reuses `reachability.gate`.
Verdicts 13: ACTIVE 4, EXTERNAL 2, NEVER 2, UNEVALUABLE 5; stale 13.

| contract | status | evidence |
|---|---|---|
| cdicf-installer | UNEVALUABLE | no deterministic probe registered for this condition -- it cannot be measured, and is NOT counted as active |
| reconstruction_parity | UNEVALUABLE | no deterministic probe registered for this condition -- it cannot be measured, and is NOT counted as active |
| spec_depth_selection | UNEVALUABLE | only 99 incident record(s); 200 required before a zero can retire a guard |
| surface_architecture | UNEVALUABLE | no deterministic probe registered for this condition -- it cannot be measured, and is NOT counted as active |
| surface_architecture_design_md | UNEVALUABLE | no deterministic probe registered for this condition -- it cannot be measured, and is NOT counted as active |
| architecture_reconstruction | ACTIVE | no CI workflow directory -- nothing verifies an architecture contract |
| cascade_prevention | ACTIVE | chain set gained a member 38 days ago (79 events) -- two years not elapsed |
| duplicate_detection | ACTIVE | 3 of the last 3 audits still measure majority-owned (upac-corpus-2026-08-18.md=MAJORITY_OWNED, egcc-corpus-2026-08-06.md=MAJORITY_OWNED, cdicf-corpus-2026-08-06.md=MAJORITY_OWNED) |
| liveness_reachability | ACTIVE | liveness still names 75 unreachable/undeclared module(s) |
| cost_routing | EXTERNAL | depends on facts outside this repo: model pricing is a market fact; no repository signal can observe convergence. Retiring it needs an Owner attestation, not a scanner |
| premise_verification | EXTERNAL | depends on facts outside this repo: editor/toolchain symbol verification is a property of the toolchain, not of this repo. Retiring it needs an Owner attestation, not a scanner |
| output_quality_gate | NEVER | declared permanent by contract |
| secret_containment | NEVER | declared permanent by contract |

### Skill candidates (host gex44 / node kobicraft-gex44, coverage recorded 2026-10-03T19:13:14Z; invocation window G 2026-09-26T18:05:00Z..2026-10-03T18:05:00Z, host kobicraft-gex44, 189 transcript files)

Coverage `none` on that host: 159 of 161. Invoked in the window (excluded): gsd-autonomous, gsd-code-review, gsd-execute-phase, gsd-plan-phase. Candidates: 155. Another host or window can differ.

| skill | criticality | D-coverage.md line |
|---|---|---|
| adversarial-longevity | low | 76 |
| agent-reach | low | 77 |
| android-reverse-engineering | medium | 78 |
| anydesign | low | 79 |
| autofix | low | 80 |
| autoresearch | low | 81 |
| carl-manager | low | 82 |
| claude-power-pack | high | 83 |
| claude-power-pack.pre-clone-2026-09-27 | low | 84 |
| code-auditor | low | 85 |
| code-review | low | 86 |
| code-reviewer | low | 87 |
| composition-patterns | low | 88 |
| compound-learnings | low | 89 |
| copywriting | low | 91 |
| cpp-pro | low | 92 |
| debugging-wizard | low | 93 |
| design-taste-frontend | low | 94 |
| develop-here-prove-there | high | 96 |
| dios-segun-buda | low | 97 |
| elevenlabs-music-generation | low | 98 |
| elixir-phoenix-patterns | low | 99 |
| embedded-systems | low | 100 |
| evaluation-corpus-governance | high | 101 |
| fix | low | 102 |
| frontend-design | low | 103 |
| game-feel-codex | low | 104 |
| github-actions-templates | low | 105 |
| governance-overlay | low | 106 |
| gsd-add-tests | low | 107 |
| gsd-ai-integration-phase | low | 108 |
| gsd-audit-fix | low | 109 |
| gsd-audit-milestone | low | 110 |
| gsd-audit-uat | low | 111 |
| gsd-capture | low | 113 |
| gsd-cleanup | low | 114 |
| gsd-complete-milestone | low | 116 |
| gsd-config | low | 117 |
| gsd-debug | low | 118 |
| gsd-discuss-phase | low | 119 |
| gsd-docs-update | low | 120 |
| gsd-eval-review | low | 121 |
| gsd-explore | low | 123 |
| gsd-extract-learnings | low | 124 |
| gsd-fast | low | 125 |
| gsd-forensics | low | 126 |
| gsd-graphify | low | 127 |
| gsd-health | low | 128 |
| gsd-help | low | 129 |
| gsd-import | low | 130 |
| gsd-inbox | low | 131 |
| gsd-ingest-docs | low | 132 |
| gsd-manager | low | 133 |
| gsd-map-codebase | low | 134 |
| gsd-mempalace-capture | low | 135 |
| gsd-mempalace-recall | low | 136 |
| gsd-milestone-summary | low | 137 |
| gsd-mvp-phase | low | 138 |
| gsd-new-milestone | low | 139 |
| gsd-new-project | low | 140 |
| gsd-next | low | 141 |
| gsd-ns-context | low | 142 |
| gsd-ns-ideate | low | 143 |
| gsd-ns-manage | low | 144 |
| gsd-ns-project | low | 145 |
| gsd-ns-review | low | 146 |
| gsd-ns-workflow | low | 147 |
| gsd-onboard | low | 148 |
| gsd-pause-work | low | 149 |
| gsd-phase | low | 150 |
| gsd-plan-review-convergence | low | 152 |
| gsd-pr-branch | low | 153 |
| gsd-profile-user | low | 154 |
| gsd-progress | low | 155 |
| gsd-quick | low | 156 |
| gsd-quick-batch | low | 157 |
| gsd-resume-work | low | 158 |
| gsd-review | low | 159 |
| gsd-review-backlog | low | 160 |
| gsd-secure-phase | low | 161 |
| gsd-settings | low | 162 |
| gsd-ship | low | 163 |
| gsd-sketch | low | 164 |
| gsd-spec-phase | low | 165 |
| gsd-spike | low | 166 |
| gsd-stats | low | 167 |
| gsd-surface | low | 168 |
| gsd-thread | low | 169 |
| gsd-ui-phase | low | 170 |
| gsd-ui-review | low | 171 |
| gsd-ultraplan-phase | low | 172 |
| gsd-undo | low | 173 |
| gsd-update | low | 174 |
| gsd-validate-phase | low | 175 |
| gsd-verify-work | low | 176 |
| gsd-workspace | low | 177 |
| gsd-workstreams | low | 178 |
| guard-event-reachability | high | 179 |
| humanizer | low | 180 |
| image-calco | low | 181 |
| image-to-video | low | 182 |
| instrument-before-claim | high | 183 |
| java-architect | low | 184 |
| kobiicraft-debug | low | 185 |
| kobiicraft-dev | low | 186 |
| kobiicraft-execution | low | 187 |
| kobiicraft-ops | low | 188 |
| kobiicraft-prd | low | 189 |
| kobiicraft-product | low | 190 |
| kobiicraft-review | low | 191 |
| kobiicraft-testing | low | 192 |
| lateral-thinking | low | 193 |
| leverage-research | low | 194 |
| managing-sleepy-skills | low | 195 |
| marketing-psychology | low | 196 |
| mcp-builder | low | 197 |
| minecraft-android-renderer-stack | low | 198 |
| minecraft-mod-jar-patcher | low | 199 |
| mobile-app-ui-design | medium | 200 |
| mobile-game-wii-port | medium | 201 |
| monetary-quantity-integrity | high | 202 |
| motion-promo | medium | 203 |
| on-device-verification-loop | low | 204 |
| pojavlauncher-headless-driver | low | 205 |
| presence-is-not-residency | high | 206 |
| project-bootstrapper | low | 207 |
| project-pulse | low | 208 |
| prompt-engineering-patterns | low | 209 |
| python-best-practices | low | 210 |
| python-pro | low | 211 |
| react-best-practices | low | 212 |
| real-context-reachability | high | 213 |
| recurring-work-cardinality | high | 214 |
| remotion-best-practices | low | 215 |
| remotion-discovery-trap | low | 216 |
| remotion-foundation | low | 217 |
| remotion-kobii-templates | low | 218 |
| secrets-management | low | 219 |
| session-handoff-protocol | low | 220 |
| skill-creator | low | 221 |
| skill-prompt-efficiency-001 | low | 222 |
| sleepy-skills | low | 223 |
| social-content | low | 224 |
| software-best-practices | low | 225 |
| spanish-mc-menus | low | 226 |
| stripe-best-practices | low | 227 |
| test-master | low | 228 |
| video-analyzer | low | 229 |
| vision-video | low | 230 |
| voice-spec-lock | low | 231 |
| web-design-guidelines | low | 232 |
| webapp-testing | low | 233 |
| wii-dev-best-practices | medium | 234 |
| wii-disc-reconstruction | low | 235 |
| wii-power-pack | low | 236 |

## What the owner should do

- Cognitive-economy pillar T ("institutional GC / simplification", predicted AUTHORIZATION_BOUND, owner `vault/programs/cognitive-economy/ledger.json`): take these lists as input to institutional GC. Re-measure before acting: both lists are measured at the commit above.
- `modules/liveness/reachability.py`: the module list is your own output on committed blobs; a candidate leaves it by being wired, declared in the registry, or deleted by its owner.
- A candidate is not a deletion verdict. This program deleted nothing.

## What this program did not do

- Deleted, moved or deprecated nothing; declared nothing in `vault/liveness/reachability_registry.json`.
- Did not run `reachability.py --baseline` or `retirement.py --record` (both write).
- Did not edit `vault/programs/cognitive-economy/**`; the Owner points the CE mission at this file (an `[I]` owner-bundle item written by plan 08-04).
