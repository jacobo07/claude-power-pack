# CPP-VCR-001 — Verified Complexity Reduction & Failure-Immunity Absorption

**Date:** 2026-10-15  
**Status:** EVIDENCE-BASED BACKLOG / NOT IMPLEMENTED / NOT CERTIFIED  
**Priority:** P1 candidate, subject to measured scheduling against active CPP work  
**CPP baseline inspected:** `jacobo07/claude-power-pack@f4ea20c2150ec65da344ab9049386afa13dee220` (`main`)  
**External reference revisions:** Ponytail `84740e3d344b69b4a133201fa519eb37a62a2b2a`; pstack `1f0f9c3bac03c4297f6fc8f7644fa412eda57085`; cursor/plugins `e5136d82418d2db3165ea1050d17577cd618cc05`.  
**Companion backlogs:** `CPP-DBG-001` (2026-10-11 causal proof), `CPP-TDD-001` (2026-10-11 behavioral verification). These remain separate scoped missions; reuse their owners and avoid duplicating their execution systems.

## 1. Mission and constitutional boundary

Absorb the useful mechanics of:

- [Ponytail](https://github.com/dietrichgebert/ponytail): smallest **complete** solution, inspect touched flows, preserve security/error handling, exercise consequential logic.
- [pstack](https://github.com/backnotprop/pstack): `correct` (turn repeated human corrections into enforced structural impossibility), `blast-radius` (prove safety-critical facts in executable form), `create-verification-skill` (exercise actual user-facing paths).
- [Cursor Thermo-Nuclear Review](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md): seek structural simplification / "code judo", prevent incidental state/branch growth, guard ownership and layering.

**Target property:** A coding change is valid only if its functional/security/operational contracts are preserved, its added complexity is justified against reused alternatives, and consequential safety claims have independently reproducible evidence. Permanent improvements are only **proposed** for ratchet promotion until their owner-authorized proof is complete.

**No new framework, agent runtime, daemon, scheduler, second code-review owner, global quality score, independent baseline, rule registry or hook.** No wholesale copying of external instructions. External benchmark claims are hypotheses to reproduce, not CPP outcome measurements.

## 2. Reality Scan — measured source vs declared capability

This inventory comes from reading named files at the pinned CPP commit, not from executing the host. **CODE-READ** means source inspected; **DOC-READ** means the stated design inspected; **LIVE-VERIFIED is NOT claimed.**

| Requirement | Existing canonical/likely owner | Observed evidence | Decision |
|---|---|---|---|
| Reuse before creation | `modules/duplicate_to_advantage/d2a_engine.py` | CODE-READ: duplicate detection, portfolio candidate choice, `govern_build` | EXTEND its application to solution alternatives; do not reimplement detection |
| Fast code and complexity review | `modules/code-review/code_reviewer.py`; `commands/code-review.md` | CODE-READ: diff parser, security/doctrine/complexity; `_detect_complexity` checks **added hunks**, >80-line functions and nesting >5; reviewer file itself currently >1k LOC | EXTEND; do not create `thermo_reviewer` |
| Architecture conflict review | `modules/arch-decision/arch_check.py` | CODE-READ: CLEAR/WARNING/COLLISION over vault index | REUSE for architecture context; do not confuse with full runtime contract tracing |
| Recurrent correction intake | `hooks/ceps_correction_stop.js`, `tools/ceps.py` | CODE-READ: Stop-triggered owner correction extraction, LOW-confidence drafts needing human confirmation | CONNECT without silently promoting drafts |
| Rule-to-incident counterfactual | `modules/rule_compiler/counterfactual.py` | CODE-READ: recorded incident + rule + executable detector can be measured retrospectively | REUSE; no new "immunity proof" engine |
| Rule issuance | `modules/rule_compiler/compiler.py` | CODE-READ: active rule DB, digest, rejected rules; malformed rules excluded, not silently deleted | REUSE; enforce at highest applicable level after evidence |
| Applicability and execution tier | `modules/capability_runtime/applicability.py`, `modules/gsd_x/tier.py` | CODE-READ: explicit applicable/blocked states and tier calculation | EXTEND selectively; never introduce a competing router |
| Quality baseline protection | `modules/sqi/baseline_guardian.py`, `modules/sqi/ratchet.py`, `modules/intent_verified/ratchet.py` | CODE-READ: asymmetric regression check; saturation proposes, cannot self-adopt | REUSE with owner approval |
| Institutional promotion | `modules/fable_distillation/fd_07_flywheel.py`, `modules/tower/` | DOC-READ: `vault/audits/ucr_cif/10_E1_E2_OWNER_DISPOSITION.md` names FD-07 for Construction Return; 08 recovers Tower Lift as verified, deduplicated capability delta | CONNECT, not parallel "construction return" runtime |
| Existing ownership collision | `modules/code-review/` versus `modules/code_review/` | CODE-TREE + `OWNERSHIP_OVERLAP_AUDIT.md` reports both paths | NO automatic rename; targeted call-graph/consumer audit needed |

**Unverified, not missing:** actual automatic invocation of FAST reviewer in every expected workflow; CEPS-to-rule-counterfactual end-to-end; adversarial behavior across platforms; live parity of dispatcher and installed hooks; cross-repo lift transfer. Their presence in comments or docs is not liveness proof.

**Source boundaries:** `vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md` describes an earlier owner decision pending; later `vault/audits/ucr_cif/17_P3B_RESULT_STOPPED.md`, `19_S1_FAMILY_CLASSIFIER_RESULT.md`, and `21_O0_RESULT.md` contain subsequent measurement and stop decisions. Do not treat the stale resumption text as proof that the later STOP was resolved.

## 3. Hard stop gates inherited from CPP

1. **HR-NOVELTY-001 / D2A:** Before introducing a new authority, data model, or runtime entrypoint, perform the existing novelty/ownership proof and prefer `EXTEND` or `CONNECT`. If unresolved, abstain.
2. **UCR-CIF P3b STOP:** The persistent-state family classifier produced false positives on full-depth traversal. This audit does not reopen, silently adjust, or distribute capsules based on that classifier. New predeclaration and Owner review required.
3. **UCR-CIF S1 evidence:** The family classifier misfires on status/meta questions; do not infer build intent from topic words or paths alone.
4. **G-3 measured liveness:** `vault/audits/ucr_cif/09_G3_DECISION.md` recorded 815 chain abandonments and adopts out-of-band producer + explicit degraded status, not new hot-path work. Do **not** add a new `UserPromptSubmit`, Stop, or PreToolUse process here. Measure installed/live parity before any routing change.
5. **DRK-07 / SQI:** Agents may propose but never self-promote sealed thresholds, baselines, or constitutional rules. No autonomous rule ratification or newly mandatory blocker.
6. **Privacy and safety:** do not log sensitive code/prompts or send private diffs to new third-party services without explicit approval; follow current security controls.
7. **No green-by-shrinking-denominator:** deleted tests, disabled checks, hidden populations, synthetic probes or renamed criteria cannot count as a quality gain.
8. **Known runtime fragility:** any new in-band hook or unbounded scan must justify its process cost, timeout/cancellation behavior, and observability; default architecture is offline or invoked existing owner.

## 4. Proposed contract extensions — **not yet implemented**

### VCR-C1 — Minimal Complete Construction (Ponytail semantics)

Before substantive implementation, identify: requested behavior; real callers/fixtures/config; security and failure invariants; existing repository/platform/dependency candidates; smallest complete implementation; rejected unnecessary work; residual risks.

A reviewer may reject an addition that materially complicates the system without justified value. **Do not optimize by LOC alone**: minimize new concepts, states, dependencies, coupling and lifecycle work under correctness constraints. An eight-line unsafe shortcut loses to a longer correct solution.

**Owner:** existing D2A build-contract judgment plus code-review completion report. **No global numeric complexity score until experimentally calibrated.**

### VCR-C2 — Structural Review (Thermo-Nuclear semantics)

At review time examine **whole changed modules and interfaces**, not only added lines. Flag: growth across ~1,000 LOC where it harms cohesion (not an automatic universal ban), dispersed conditional branches, identity wrappers, unnecessary optionality/casts, incorrect canonical layer, non-atomic state transitions and misleading simplicity via moved code.

Demand a specific alternative that removes complexity **without weakening behavior, security or observability**. Begin with high-confidence findings as advisory `WARN`, not hard BLOCK. Measure false-positive rate, reviewer cost and regression detection before escalating.

**Owner:** `modules/code-review/code_reviewer.py`; architectural context from `arch_check.py`. Avoid having a model's taste counted as mechanical proof. Proposed acceptance fixtures should include a large cohesive module that must NOT be split blindly.

### VCR-C3 — Error Class Immunization (pstack /correct semantics)

Use existing CEPS-confirmed incidents and rule compiler. Group a repeat class from at least two **genuine** independent occurrences, preserve counterexample inputs, rank prevention mechanisms: eliminate unsupported architecture/entrypoint first; types/schema second; deterministic lint/boundary validation third; behavioral test next; prompt prose last.

For any new enforcement, the actual historical bad input must go RED under the new mechanism and the corrected variant GREEN; detectors must identify the violated boundary and remedy. False positives, expiry and explicit Owner-approved exceptions are part of evidence. **A written prohibition is not an enforced prevention.**

**Owners:** CEPS intake, `rule_compiler/counterfactual.py`, `rule_compiler/compiler.py`; consume `CPP-DBG-001` for causal claims and `CPP-TDD-001` for verified test ordering.

### VCR-C4 — Blast-Radius Causal Proof (pstack /blast-radius semantics)

Material or irreversible changes require a named **safety fact** with provenance and an evidence level: ASSERTED → SOURCE-CITED → PATH-EXCLUDED → EXECUTED → RUNTIME-REPRODUCED. For affected serialized formats, cross-language readers, pinned dependency behavior, scheduling/concurrency, transactional state and version compatibility, grep of callers alone is insufficient.

Material high-risk facts at ASSERTED/SOURCE-CITED cannot be called 'safe' or 'ready'; either run a faithful proof or expose UNVERIFIED and stop the affected merge decision under its **existing** gate. Low-risk reversible changes need only risk-proportional evidence.

**Owner:** architectural/intent verification and existing completion gate; store proof using their ledger rather than a new `blast_radius.json` authority.

### VCR-C5 — Verification Adapter (pstack /create-verification-skill semantics)

Where a project cannot be exercised through the user path, extend its existing verification guidance with recorded **launch → doctor → drive → observe → cleanup**. Ground commands in actual host/tooling, make isolation explicit, track side effects, and retain evidence after cleanup. No generated verification skill is certified until its own instructions execute successfully once.

**Owner:** existing `verification-loop`, `auto-test` and project-local harness; coordinate `CPP-TDD-001` and `CPP-DBG-001`. Reuse existing adapters and do not force a universal scaffolder.

### VCR-C6 — Evidence-Gated Ratchet

A successful local change is not automatically an institutional lift. A promotable discovery requires: source commit, original bad case, causal improvement, maintained denominator, validated target project, applicability conditions, transfer evidence, version/rollback and explicit owner authorization. Deduplicate against FD-07/Tower state.

**Owner:** FD-07 + existing Tower/SQI and DRK-07 authority. Status is PROPOSED until independently verified and approved.

## 5. Execution work packages (order is contractual)

**W0 — Runtime and ownership reconciliation (blocking):** pin fresh checkout HEAD, enumerate consumers and real caller graph for `code-review`/`code_review`, fast/deep integration, D2A, CEPS, counterfactual, SQI and Tower. Verify currently installed hooks and source parity. Produce owner matrix with reachable/not-reachable/unverified. Inspect repository-native `CLAUDE.md` safety and active worktrees. Do not silently mutate overlapping work.

**W1 — Frozen evaluation design (before modifications):** predeclare task corpus and blind holdouts across TypeScript/JavaScript/Python, small changes vs structural refactors, security/data loss/concurrency, false-positive controls and genuine repeated historical errors. Collect existing CPP outcomes, cost/tokens/latency, lines+concepts added, defects detected, mutations killed, reviewer disagreements and full-lifecycle failure cases. Pin upstream SHA above and license status; reproduce external claims on CPP if desired, never import their percentages as expected result.

**W2 — Smallest tested code-review extension:** select **one** evidence-backed structural blind spot in the existing reviewer. Write a regression fixture that first fails, implement the minimum detector/advisory with a false-positive counterexample, validate differential behavior, and keep FAST within its current resource envelope. Verify end-to-end reachability at the claimed integration point. Do not ship a broad generic complexity score.

**W3 — One historical immunization:** choose a confirmed CEPS class, run existing `counterfactual` on recorded input, add the highest-level valid guard in the incumbent owner, demonstrate historical RED/current GREEN, and explicitly show what older control failed to detect.

**W4 — One safety-fact proof pilot:** choose one existing materially risky path, prove or honestly leave unverified the decisive fact using actual runtime/library at pinned version. Measure time/cost vs ordinary review; submit proof to existing review artifacts.

**W5 — Applicability/routing only if W2–W4 show net gain:** route via `capability_runtime` and existing `gsd_x/tier.py`; preserve dormant/blocked semantics, no new hot-path process, explicit degraded state, cancellation and negative controls; verify opt-out and cost floors. Reviewers stay independent only when risk justifies independence.

**W6 — Institutional transfer:** propose a deduplicated FD-07/Tower lift and test it on a **different** applicable repo. If transfer not proven, retain as project-local guidance. Owner reviews all baseline changes. Cross-project rollout must be reversible.

## 6. Required adversarial acceptance suite

These are **fixtures to construct and run**, not tests already passed.

| ID | Counterexample / positive control | Required result |
|---|---|---|
| VCR-01 | Native/repo capability already solves request | No new dependency or wrapper |
| VCR-02 | Tiny change omits security validation, cleanup or caller | Minimality does **not** approve it |
| VCR-03 | Refactor shifts branches across files but does not reduce conceptual complexity | Structural review identifies non-improvement |
| VCR-04 | Cohesive >1k-LOC module / generated file | No automatic unjustified extraction |
| VCR-05 | Change crosses 999→1001 lines with clear complexity growth | Explainable advisory, not uncalibrated blocker |
| VCR-06 | Security-critical JSON format read by a different language with no symbol reference | Blast-radius proof follows wire contract |
| VCR-07 | Safety fact asserted but not executed | Not certified as proven |
| VCR-08 | Two confirmed recurrent incidents with executable counterexample | New guard catches historical bad input; fixed input passes |
| VCR-09 | Draft owner correction not confirmed | No rule or baseline promotion |
| VCR-10 | Missing/corrupt baseline or shrunken test denominator | UNKNOWN/FAIL, never success |
| VCR-11 | Status-only user prompt / path mentions build family | Does not activate heavyweight construction review |
| VCR-12 | Hook chain stalls or installed version drifts | Explicit degradation; no false liveness claim |
| VCR-13 | Different project with nonapplicable rule | No incorrect universal enforcement |
| VCR-14 | Reviewer design proposal creates more states than it removes | D2A / structural critique prefers simpler owner |
| VCR-15 | User-path verification cannot run on target platform | UNVERIFIED, never certified by a stand-in |

Use red-capable tests, restore all mutants, prove exact worktree identity after drills, and report false positives separately from misses. Any missing instrument lowers claim strength, not the bar.

## 7. Completion evidence / decision gate

Before any “absorbed” claim, produce a linked evidence bundle containing: baseline commit, exact changed files, owner resolution, protocol frozen before results, human-readable findings with real code locations, before/after behavior, mandatory contracts, adversarial test logs, negative controls, integration reachability, installed/live parity where relevant, latency/tokens/cost, rollback, and cross-project transfer outcome.

**Accept W2/W3/W4 independently** if each improves independently measured correctness or maintainability at bounded cost and without weakened security. **Do not** block unrelated changes merely because the larger program is open.

**Do not silently adopt:** benchmark statistics from upstream; an unmeasured 1,000-line global cutoff; always-on aggressive review; wholesale pstack orchestration; Ponytail token-maximization; new rule/ledger/tier/agent/system owners; any UCR-CIF baseline lift before approval.

## 8. Provenance and claim limits

Sources read through connected GitHub on 2026-10-15: CPP tree, named source and audit files; Ponytail SKILL; pstack `correct`, `blast-radius`, `create-verification-skill`; Cursor Thermo-Nuclear SKILL. The linked upstream repositories are credited for inspiration; this backlog is a newly authored synthesis, not imported third-party code.

**What this audit has NOT done:** run CPP tests; reproduce benchmark results; execute the hooked host; prove CI/installed parity; measure real review false-positive rates; ratify baselines; implement any production change. Those absences are explicit stop conditions for making implementation/certification claims.

**Next action:** W0 Reality Scan in a properly isolated CPP checkout, then W1 predeclaration. Reconcile with newer UCR-CIF decisions and live worktrees before selecting even the first implementation file.
