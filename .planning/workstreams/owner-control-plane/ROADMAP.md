# Roadmap — owner-control-plane (v1)

Read `REQUIREMENTS.md`, then `vault/plans/owner-control-plane-2026-10-19.md` (design, root causes, budget).
Worktree: `C:\Users\User\Apps\pp-owner-control`, branch `ocp/owner-control`. Goal: `owner-control-plane` (programme 22M, applied from packet sha 0878ac15a056).
Each phase ends with: tests run (foreground, bounded), pathspec-scoped micro-commit(s) in this worktree, `STATE.md` + `RESUMPTION_FILE.md` (this dir) updated with measured spend.
UNKNOWN / INCONCLUSIVE are never PASS. Prefer Sonnet subagents for build work; at most 2 in parallel. Do not edit files in another pane's worktree.

## Phases

- [ ] **Phase 1: Reality delta + fence audit** (read first: vault/plans/econ-succession-2026-10-11*.md and owner-capital-ctx-rent-2026-10-11.md; they already treat "approved authority not executable from the control plane")
- [x] **Phase 2: Capital grammar** (ADD/SET/KEEP/STOP, Spanish por/a, units, ambiguity)
- [ ] **Phase 3: Pre-budget router** (inside hooks/econ_admission.js) + principal and target binding
- [ ] **Phase 4: owner_intent receipt** (idempotency, CAS, recovery WAL, crash points)
- [ ] **Phase 5: WAIT_OWNER_CAPITAL fold + PROGRAMME_AUTHORITY_CHANGED event + wake consumer**
- [ ] **Phase 6: Adaptive successor lease sizing + automatic activation**
- [ ] **Phase 7: Dirty-residual classifier + proof reuse**
- [ ] **Phase 8: Decision, resource and STOP providerless paths**
- [ ] **Phase 9: Fault-injection matrix + liveness gate**
- [ ] **Phase 10: econ-safex canary** (OWNER GATE: render the typed choice `ADD +70M`; apply only on the Owner's typed reply or an explicit Owner instruction to promote by fingerprint)
- [ ] **Phase 11: Knowledge vault, FIOS, UKDL, CBR**

## Phase Details

### Phase 1: Reality delta + fence audit
- Confirm which hooks run on UserPromptSubmit and in what order; whether a `decision:block` from econ_admission.js stops the capture hook (it did not for `approve owner-control-plane only`).
- Read the ledger fold, `ledger.py` succession code and the Decision Plane entry points; list what is reusable.
- Output: `vault/programs/owner-control-plane/P1-reality.md` with file:line evidence. Acceptance: every claim cites a file and line or a command output.

### Phase 2: Capital grammar
- New pure module with a closed grammar; tests drive each alias from both poles, including `subelo por 70M` = ADD and `subelo a 70M` = SET, negation, malformed units, overflow, zero and negative values.
- Acceptance: V-OCP-GRAMMAR-* pass; no model call anywhere on the path.

### Phase 3: Pre-budget router
- Classify before the affordability block; MODEL_REQUIRED stays fenced; `econ status` and `econ detach` unchanged.
- Target = explicit goal in the message, or the single open `authority_required` boundary; cwd alone never selects a programme.
- Acceptance: zero-headroom status, ADD, SET, STOP and random chat all behave per the plan.

### Phase 4: owner_intent receipt
- Receipt fields per the plan; idempotency key = source fingerprint; CAS on the expected programme; SET below settled+open refused; intent written before effect.
- Acceptance: replay, duplicate, concurrent ADD and the three crash points are tested.

### Phase 5: WAIT_OWNER_CAPITAL + event + wake
- Fold derived from unresolved `authority_required`; consumer recomputes residual and wakes the frontier on `PROGRAMME_AUTHORITY_CHANGED`.

### Phase 6: Adaptive successor lease
- Fix the automatic-succession tranche problem (a fixed 50M tranche opens a lease of about 50M against a 102M programme): lower the tranche or derive the size from residual and forecast. Owner never sizes a lease.
- Activation without `/clear` and without a manual lease-open.

### Phase 7: Dirty-residual classifier
- Classes OWNED_VALIDATED_PENDING_COMMIT / OWNED_UNVALIDATED / GENERATED_REPRODUCIBLE / FOREIGN / CONFLICTING / UNKNOWN; seal-first; never commit FOREIGN or UNKNOWN.

### Phase 8: Decision, resource, STOP
- Active Decision option tokens and a declared REC alias resolve providerlessly, bound to the packet fingerprint. STOP outranks everything.

### Phase 9: Fault matrix + liveness
- `tools/test_owner_control.py` (V-OCP-*), every detector driven from both poles; `python modules/liveness/reachability.py` clean; existing goal-lease and capital-authority tests unchanged green.

### Phase 10: econ-safex canary
- Verify the live ledger first (programme still 32,000,000, message unapplied). Stop and return to the Owner at the typed choice. After a valid receipt: reconcile L2, classify the seven dirty routes, seal, open the successor, verify productive progress.

### Phase 11: Knowledge
- Vault entries for each confirmed failure class, FIOS promotion, UKDL hard rules / process rule / traps, CBR ratchet. Dedupe against existing entries first.
