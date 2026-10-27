---
covers: [founder-os, founder_round, business-round, repo-isolation, evidence-kernel, production-reality, constitutive-ratchet]
tier: T2
status: IN PROGRESS (F0 only; F1-F7 are written here as intent and each gets its own amendment before its first edit)
supersedes: vault/specs/founder-os-v0.md (extends, does not replace)
---

# Founder OS v1 — campaign spec

## Objective
Turn the v0 evidence journal into a repo-isolated business-intelligence capability whose every
claim of impact is observed, and whose proven lessons raise the baseline for later builds.
Two deltas are required, and neither stands in for the other: a business-capability delta and
an institutional-intelligence delta (a standard a new feature inherits by execution).

## Ownership (reuse, never duplicate)
Identity: `modules/repo_identity`. Secrets: `modules/secret_firewall` (shared; Founder adds a stricter
local guard, it does not fork the patterns). Install: `tools/install_global_core.py` discovery
(`modules.mirror_discovery`). Ratchet/promotion: UCR-CIF, `modules/done_gate/strength_ladder.py`, UKDL.
Loops: existing CPP loops; from the iteration prompt only the immutable done-gate and
false-premise-as-root-cause classification are adopted.

## F0 findings (each has a regression test in `tools/test_founder_os_f0.py`)
| ID | Defect in v0 | Evidence | Class |
|---|---|---|---|
| F0-1 | Secret Firewall passes Stripe live keys and all PII (email, IBAN, card, phone) into the journal | probe on `redact_for_log`, 5 of 9 shapes passed through | gate that asserts privacy it does not measure |
| F0-2 | `estimated_cost` / `estimated_value` accepted with no currency or sign check | `record()` allow-list, no currency rule | unit-less quantity |
| F0-3 | Same `action_ref` recordable twice in a round | `record()` has no duplicate check | non-idempotent action |
| F0-4 | A crash mid-append leaves a torn last line; every later call fails as generic integrity failure with no recovery path | `_append` writes without a torn-tail rule | crash between writes |
| F0-5 | A lock left by a dead process blocks the business forever | `_locked` O_EXCL, no owner liveness | stale lock |

## Deferred with reason (registered, not silently dropped)
- Tail truncation of a hash chain is undetectable without an external anchor; a local attacker who can
  write the journal can rewrite it. Mitigation is an anchor outside the state dir. Deferred to F5.
- `authorization_ref` is metadata and confers no authority (v0 contract 4/5). Real verification needs an
  owner-grant store; designed in F0b, built before any non-internal effect is executable.
- Installed `~/.claude/skills/claude-power-pack` currently tracks another branch, so the command's
  `tools/founder_round.py` is absent there until this work lands. Installer discovery is verified
  (`_repo_population('commands')` contains `cpp-founder-round.md`); end-to-end global activation
  is a post-landing gate, not claimed now.

## Gates
G1 foundational integrity: `python tools/test_founder_os.py` and `python tools/test_founder_os_f0.py` exit 0.
Remaining gates per the campaign prompt; each is reported with its real command and exit code.

## F0b — foundational decisions (decided from repo evidence, 2026-10-27)
| Decision | Choice | Evidence / reason |
|---|---|---|
| Where business state lives | Host-local `~/.claude/state/founder-os/<sha256(canonical_repo)[:32]>/`, as in v0. Never inside the business repo. | v0 contract 1; keeps customer-adjacent metadata out of commits. Cross-host portability stays deferred (`repo_identity.portable_repo_id`). |
| Repo vs business identity | A namespace is a repo. `identity.json` carries `business_name`/`sector` as `UNKNOWN` until an Owner-confirmed mapping sets them. A repo that holds several ventures, or a company with several repos, is reported as ambiguous and gets NO automatic merge. | v0 fields already exist and are null; the prompt forbids inventing identities. |
| Multi-repo company | Only through an explicit grant file listing namespaces, written by the Owner. Default is no sharing. | Isolation gate G3; privacy by default. |
| Recommend vs act | The kernel returns recommendations. Any non-internal effect needs a grant record naming scope, expiry and the hash of the exact action bytes; a bare `authorization_ref` string never suffices. Built before any executable external action (F5). | `human-facing-external-effects` doctrine; v0 contract 5. |
| Promotion to baseline | Reuse the live Constitutive Baseline machinery: `vault/tower/families/*.json` + immutable `vault/tower/baselines/<family>/B<n>.json`, `tools/family_baseline.py review|revert`, injection via `modules/gsd_x/cli.py`, kill switch `CPP_FAMILY_BASELINES=off`. F6 adds ONE family for business-context work; business-only requirements apply only when its triggers fire, and a prompt of no family receives nothing (`FALSE ACTIVATION IS A BUG`). | `docs/superpowers/specs/2026-09-24-family-baselines-design.md` (T3, Owner decisions 2026-09-24); files verified present in this tree. |
| UWCP | No integration. It is the *Universal Workstream Continuity Plane*, a TLA+ model of goal/epoch/fence continuity (`vault/specs/tla/UWCP.tla`) used by long-run continuation, not a business-state concern. Founder rounds are single-writer and already lock-guarded. | Header of `UWCP.tla`; no advantage found for this mission. |
| Iteration prompt | Adopt two mechanisms only: classify the failing premise before fixing (CLASE N) and a done-gate that does not move while a loop runs. Everything else duplicates SCS C28, the premise verifier and NEVER_AGAIN. | `iteracion-avanzada-universal.txt` read through line 120. |

## F1 — Founder Kernel contract
`modules/founder_os/kernel.py` is a pure fold over the journal; there is no second store, so the kernel
cannot hold a fact the journal does not. An observation/measurement/hypothesis event may carry `subject`
(a profile field) and `value` (short text). Per field the view returns one of VERIFIED, OBSERVED, INFERRED,
HYPOTHESIS, SIMULATED, STALE, CONTRADICTED, UNKNOWN. The agent's own inference is the class `inferred`
and never proves a closing outcome. Rules: freshness uses `observed_at` (else the record time, flagged
`recorded_at`); two live claims of class VERIFIED/OBSERVED with different values are CONTRADICTED and are
never resolved silently, only by a later event naming the retired one in `supersedes`; no event means UNKNOWN
with the evidence that would change it. BLOCKED is a round outcome, not a profile-field state.
`plan_round` is deterministic and returns at most 5 recommendations ordered contradiction, then the most
valuable missing core fact, then stale facts, then instrumentation; it never names a company and never acts.

## F2 — Business Knowledge Compiler contract
`modules/founder_os/compiler.py` composes a specialist context from exactly two sources and invents a third
never: (1) the kernel view of ONE business, and (2) the active entries of the `business_round` family baseline
(universal principles, already cited and generation-stamped). It does not read the Knowledge Vault, UKDL or AKOS
directly: those retrievals run in the agent session, and anything they return enters a round only as a journal
event with a `source_ref`, so it is then company evidence with provenance, not an uncited paragraph.
Every item carries `kind` (principle | verified_fact | observed_fact | inferred | hypothesis | simulated |
stale | contradicted | gap), `scope` (`universal` | `this_business`), `provenance` and freshness. Lenses are
a field map, not standing agents: Strategy, Growth, Sales, Finance, Product, Operations, Customer, Competitive,
Research, Experimentation, Risk, Knowledge. A lens receives only its fields and is capped (12 items, 2600 chars);
a cut is reported as `omitted`, never silent. `Competitive` owns no kernel field, so it returns a `gap` naming the
evidence needed, not text from memory. A function takes one business's events; no signature accepts two.

## Rollback
Each fix is one commit on `feat/founder-os-v1-20261027`; revert the commit.
