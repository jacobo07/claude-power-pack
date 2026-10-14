# 05-2 RESEARCH -- premises verified at 63a775c9 (HR-PREMISE-001)

Every symbol a plan touches, with file:line, read this session. Reuse `proof.py`, the certificate and PCC event seams, no new stores.

## Seams that exist (REUSE)
| Premise | Verified at |
|---|---|
| PCC event types and the writer gate: `NEW_TYPES`, `REQUIRED_FIELDS`, `check_payload`, `append_pcc` (refuses unreadable/newer-v) | `modules/gsd_x/goal/proof.py:41-148` |
| `ProofLedger` slots, `project_proofs` (malformed own type raises GoalLogCorrupt; newer `v` -> `unsupported`) | `proof.py:105-133` |
| Six premises `PREMISES`, `POLICY_VERSION`, `observe_premises`, `state_from_premises` | `proof.py:195-251` |
| `combine_states(op, states, k)` AND/OR/SEQ/QUORUM, pure, tested | `proof.py:262-292` |
| `STRENGTH_ORDER = (unit, integration, in_game, live)` | `proof.py:198` |
| `environment_fingerprint(env_deps)`: python version, system, machine, tool NAMES (audit A4) | `proof.py:347-350` |
| `certificate_id(cid, seq)`, `live_certificates` (only `proof.invalidated` kills), `certificate_payload` (premises + `contract_hash`) | `proof.py:552-580` |
| `law_proof_conservation`, `law_unknown_escalates` | `proof.py:583-632` |
| Single choke point for "which certificate is live": `inherit._latest_live`; consumers `plan` (inherit.py:96) and `inherited_ids` (inherit.py:177) | `inherit.py:39-45, 83-190` |
| `ineligible()` rejects non-AND combine (D11 gap) | `inherit.py:54` |
| `observe_current` derives the six premises, environment via `pf.environment_fingerprint` | `inherit.py:68-80` |
| Judge VALIDATE re-derives through `inherit.plan`, never reads a `proof.inherited` event as fact | `judge.py:125-149` |
| Sweep writes certificates (`_certify`) and invalidations | `sweep.py:255-282` |
| `git_state._git(root,*args)`, `blob_oid`, `file_pin`, `tree_id` | `git_state.py:24,62,101,124` |
| Fixture harness for real certificate + real judge: class `JV` | `tools/test_gsd_x_goal_judge_validate.py:96-150` |
| Isolated mutation drill substrate | `tools/mutation_drill.py` (spec JSON: file,test,gate,old,new) |

## Constraints found (they change the design)
- `tools/test_gsd_x_goal_pcc_semantics.py:634` pins `environment_fingerprint(["python"])` as an `env1:` name-only hash. That Phase 2 semantic is resolved and not re-litigated. So the A4 repair adds `proof.environment_canonical` (`env2:`), moves every production caller to it (`certificate_payload`, `inherit.observe_current`), and keeps `environment_fingerprint` as the documented legacy function. Gate `V-TRUST-ENV-NO-LEGACY-CALLER` greps production sources for a remaining caller.
- `SUPPORTED_V = 1` and `check_payload` returns False for a newer `v` (proof.py:92): a `v: 2` certificate would be silently unsupported by older readers. Schema change is therefore additive on `v: 1`.
- `check_payload` rejects an unknown event type with ValueError and `append_pcc` with ProofRefused, so `authority.revoked` must join `NEW_TYPES` + `REQUIRED_FIELDS` + a `ProofLedger` slot, else it cannot be written.
- Graphify/tower/applicability: no existing owner of environment equivalence found in `modules/gsd_x`; the plan row said to search first. `Grep environment_fingerprint modules/gsd_x` returns only proof.py and inherit.py, so `proof` stays the owner.

## Forgery surface (judge VALIDATE path), each attack = a payload an adversary could append
1 edited premises in a `proof.inherited` event (`_agrees`, inherit.py:146, already refuses) -- baseline.
2-11 are new refusals in `trust.verify_certificate` / `trust.inherited_event_ok`; listed in 05-2-02-PLAN.md.

## Unknowns carried
- Whether `git rev-parse HEAD:modules` works in the Linux checkout used by the coordinator: it is the same git command; the coordinator run confirms it.
- The ~40-question list is not in the repo; the registry is built from DENOMINATOR rows and N01-N26 (plan section 5).
