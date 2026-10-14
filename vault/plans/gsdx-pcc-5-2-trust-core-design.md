# Phase 5.2 -- Trust core (design record = 05-2-CONTEXT.md)

Packet: `packets/WU-P52.md`. Plan of record: `CONTINUATION-PLAN-2026-10-14.md` row 5.2. Base `gsdx/pcc` 63a775c9.
Planes: Windows laptop py3.12 for everything built here; the Linux leg of N17 is the coordinator's.

## RED list (verbatim from the packet Scope)
- N01 revocation: a revoked authority keeps its certificate invalid with the certificate bytes UNCHANGED.
- N02 lineage: a certificate carries its derivation lineage.
- N05 authority monotonicity: inherited authority greater than the original is refused.
- N16 certificate forgery: at least 8 distinct forgery attacks, each refused (each has a control that is admitted).
- N17 canonical environment equivalence: repair audit A4, `modules/gsd_x/goal/proof.py:347`. Environment drift invalidates.
- N19 platform vs portability semantics: PLATFORM = one plane, PORTABILITY = same claim on two planes with the same `modules/` tree. A checked field of the certificate/receipt, not prose.
- D11 wiring (audit A2).
- N23 ledger seed.
- `tools/gsdx_pcc_done.py` as a question registry (~40 questions -> V-gate id + evidence file + plane); exit 1 while any question is OPEN, UNKNOWN or single-plane where portability is claimed.

## Gray areas, decided (internal, reversible by git)
1. **Schema version stays `v: 1`; new certificate fields are ADDITIVE** (`authority`, `lineage`, `plane`, `element_premises`). SUPPORTED_V=1 makes `v: 2` UNKNOWN to every older reader (proof.py:92) and D43 legacy replay must keep reading old logs. A certificate without the new fields is untrusted: never inherited, always re-run, never raises.
2. **Code lives in a new pure module** `modules/gsd_x/goal/trust.py` (no import from proof.py, so proof can import it). proof.py gains only: the `authority.revoked` event type, the new certificate fields, revocation-aware `live_certificates`. No new store (D44): revocation is an event, trust is a projection of the GoalLog.
3. **Revocation is an event, never a rewrite.** `authority.revoked` {v, authority:{id,version}, reason}. The `proof.produced` bytes are never touched; validity is computed.
4. **Authority** = `{id, version, strength}`; id/version come from a code registry `trust.AUTHORITIES` (gate receipt path = `gate-receipt` v1). An authority not in the registry is untrusted: the builder must not name its own authority.
5. **Monotonicity.** An inherited event's authority strength may not exceed the original certificate's nor its lineage root's. Writer refuses (`ProofRefused`), reader ignores. Order = `proof.STRENGTH_ORDER`.
6. **Lineage** `{root, parent, depth, via}`: a produced certificate is its own root (`parent: null, depth 0, via produced`). Forged parent (other claim, missing, cyclic, wrong depth) is refused.
7. **Forgery gate is one function** `trust.verify_certificate`, called from `inherit._latest_live`, the choke point that both `inherit.plan` (judge VALIDATE) and `inherited_ids` pass through. A check beside one caller is a courtesy.
8. **N17 environment.** `env2:` body = python full version + implementation + system + machine + one resolved entry per `env_deps`. Grammar: `pkg:<name>` (installed version), `tool:<name>` (`--version`, 5 s bound), `lock:<relpath>` (blob id), `runtime:python`. A bare legacy name (A4 weakness: names only) resolves UNKNOWN -> premise unknown -> full run. Old `env1:` certificates compare CHANGED against `env2:` and are invalidated once: the one migration.
9. **N19.** `plane` = `{claim: PLATFORM|PORTABILITY, planes: [...], modules_tree}`. Production writes PLATFORM with one plane. PORTABILITY verifies only with >= 2 distinct plane ids, identical clean `modules_tree`, none unknown. The done-gate registry applies the same predicate to receipts.
10. **D11.** Non-AND contracts are evaluated through `combine_states` using per-element premises recorded in the certificate (`element_premises`). A non-AND claim whose certificate lacks them, or whose count disagrees with the contract, re-runs.
11. **N23 seed.** `trust.ledger(...)` projection: per authority ACTIVE/REVOKED, issued, live. Seed only; descent/recovery maturity events are wave 10.
12. **Done-gate registry.** `tools/gsdx_pcc_done.py` holds the question list inside the tool; a question closes only when its gate id is in the named evidence file's PASS lines AND its plane covers the claim.
13. **Liveness.** The WU-P51 Linux offenders are NOT declared; green liveness is PLATFORM proof of the installed host only.
14. New tests never index `GIT_CANDIDATES[0]`.
15. Drills run through `tools/mutation_drill.py`, one per call; a drill killed for memory is UNRUN and listed for the coordinator.

## Not in scope
Wave 6 (mutant farm), adapter authority (wave 7), trust descent/recovery (wave 10).
