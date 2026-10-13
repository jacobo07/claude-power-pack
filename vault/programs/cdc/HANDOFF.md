# CDC handoff

<!-- rendered by tools/cdc_handoff.py from chain.json, WU-*-receipt.md, evidence/cdc-gate.json; do not edit -->

Goal `cdc`, envelope 88000000.

## Units

| unit | receipt status | landing | not proven |
|---|---|---|---|
| C1 | DONE | 170083e7 | 1 |
| C2 | DONE | 512af829 | 2 |
| C3 | DONE | 909ad75b | 1 |
| C4 | DONE | f424dd4b | 1 |
| C5 | DONE | - | 1 |
| C5b | DONE | - | 0 |
| C6 | DONE | 230933f55677 | 2 |
| C7 | DONE | 3539228b673e | 1 |
| C8 | DONE | e6558ba5 | 1 |
| C9 | DONE | 0d64b4af | 2 |
| C10 | DONE | eb78a98c | 2 |
| C11 | NO_RECEIPT | - | - |
| C12 | NO_RECEIPT | - | - |

## Done-gates

PASS 17 / FAIL 1 / UNKNOWN 3 / EXTERNAL_LIMITATION 3; FAIL in scope []; FAIL out of scope [16].

| gate | status | name | reason |
|---|---|---|---|
| 1 | PASS | Role ledger classifies every call | 12 roles + unattributed, goldens and mutants green (C1) |
| 2 | EXTERNAL_LIMITATION | Model-call firewall (interceptable edges only) | host exposes no pre-call hook for the main model turn; enforced at Agent/launch/tool edges only (C3 tests 22/22 + dispatch 4/4); real denied spawn from a deployed session NOT_PROVEN |
| 3 | PASS | Effect enum + ABI refuses deopt-less zero route | REFUSED_EFFECT drill green (C2) |
| 4 | EXTERNAL_LIMITATION | In-epoch context selection / paging | host owns the transcript; met at epoch boundary (rotation + capsule), not in-epoch |
| 5 | EXTERNAL_LIMITATION | In-epoch tool/skill selection | met through MCP/skill exposure settings (C7 floor metrics), not per-turn selection |
| 6 | PASS | Semantic breaker trips on no-progress loop | synthetic loop tripped at call 25, deny budget written (C4 canary) |
| 7 | PASS | Proof locality: closure agrees with full suite | AGREE on 3 landings after serial rerun + parent control; raw 'full minus baseline' was non-empty (3/7/5): baseline non-deterministic, agreement needed control runs |
| 8 | PASS | Derivation store serves repeat query | sess-A stored, sess-B denied with stored answer path (jsonl rows) |
| 9 | UNKNOWN | Research gate observed on a live WebSearch/WebFetch | no live call observed; settings.json registration of the Web events is an Owner step (C6 NOT_PROVEN) |
| 10 | PASS | Cognitive CI blocks a planted regression | planted +8K CLAUDE.md RED, landing refused, live untouched (C7) |
| 11 | PASS | Metamorphic gates (fixed-work metrics invariant) | +skills/history/goals/tests leave fixed-work metrics unchanged |
| 12 | PASS | PGO report over the full window | coverage complete: {"found": 2993, "read": 2993, "complete": true, "elapsed_s": 344.5} |
| 13 | PASS | UNKNOWN kept distinct from zero in PGO | Owner/Constitutional reported as UNKNOWN |
| 14 | PASS | Holdout replay (not used for design) | 28 holdout traces replayed; avoidable shares are replay estimates, realised saving NOT_PROVEN |
| 15 | PASS | Live cross-domain canary in a non-PP repo | TUA-X read-only claude -p, 4 turns, 0 denials; guards wired by --settings |
| 16 | FAIL | Fresh-repo inheritance (deployed dispatcher runs the guards) | deployed ~/.claude/hooks/hook-dispatcher.js lacks cognitive_admission, semantic_breaker; Copy-Item of the repo dispatcher is an Owner act (hooks-dir deploy denied to workers) |
| 17 | UNKNOWN | Admission denial observed from a real deployed session | dispatcher not deployed (gate 16) -> no real-session denial row; hook-level and CLI-level proofs only |
| 18 | PASS | Compiled primitive replaces a motif on a replayed trace | proof_digest replay 3 calls -> 1 (estimates); adoption NOT_PROVEN |
| 19 | PASS | At least one retirement with backup + revert path | R1 retired (-213 chars), guard test 31/31, backup + revert command recorded |
| 20 | PASS | CDC guards registered / matcher liveness green | registration test + mutants; matcher liveness 3/3, hookreg 15/15 |
| 21 | PASS | Every guard has an env kill switch | all 5 switches present in their guard source |
| 22 | UNKNOWN | Self-hosting: C1 ledger measures C0-C12; C5-C12 vs C0-C4 | no per-unit ledger of the CDC worker transcripts is stored; C12 not yet run |
| 23 | PASS | Every bug met in C0-C10 has a Knowledge Vault entry | 6 lessons present |
| 24 | PASS | Handoff rendered from state by script | carries render stamp |

## Pending Owner acts (from gate FAIL out of scope)

- gate 16: deployed ~/.claude/hooks/hook-dispatcher.js lacks cognitive_admission, semantic_breaker; Copy-Item of the repo dispatcher is an Owner act (hooks-dir deploy denied to workers)
