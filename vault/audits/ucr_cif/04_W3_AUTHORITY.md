# W3 · Baseline authority — what owns what, and how it was decided

Sealed 2026-09-19. Measured, not inherited: the handoff named
`vault/baseline_ledger.jsonl` as the unit to extend, and a targeted ownership scan moved
the whole wave. Both halves of that premise were wrong, and the way they were wrong is the
reusable part.

## 1. The store the handoff named

| question | answer | evidence |
|---|---|---|
| Is `vault/baseline_ledger.jsonl` the source of truth? | **No** | see below |
| What is it, then? | an append-only **historical event log** | `tools/baseline_ledger_append.py` docstring + shape |
| Who writes it? | `tools/baseline_ledger_append.py` (1 writer) | W0 `w0_closure.json` |
| Who reads it? | `tools/baseline_ledger_append.py` — **its own `--show`** | W0 `w0_closure.json`, `direct_readers` |
| Does anything inherit from it? | **No material path in code.** BL-NNNN laws are cited BY HAND in command prose (`commands/resume.md:109`, `resume-clean.md:109`) | grep over `*.py,*.js` finds only the writer |
| How many rows? | **42** at HEAD, at the pinned base, and on `origin/main`. Not 73. | `git show <ref>:vault/baseline_ledger.jsonl` |

**Classification: HISTORICAL EVENT LOG / AUDIT RECORD. Not an authority, not a registry,
not a projection of one.**

So adding a `status` field to it would have produced a revocation nothing could honour —
exactly the "status stored with no consumer" the Reality Contract forbids. The handoff's
instinct (EXTEND, never a new registry) was right; the object it named was not.

**The 73 was read from the other writer's uncommitted working copy** in the shared
checkout. Recorded as `T-POPULATION-FROM-A-DIRTY-SIBLING-001`.

**A second reason it is the wrong home.** Its `ledger_id` is derived from a LINE COUNT
(`next_id()`), so two concurrent writers mint the same `BL-NNNN`. That is a live exposure
today — another session is appending to that file right now — and it is precisely the race
the W3 log avoids by keying on `(capability_id, iso_ts)` and appending with `O_APPEND`.

Also note `tools/baseline_ledger.py` is a DIFFERENT subject entirely: it owns
`~/.claude/vault/global_baseline_ledger.json`, a per-project multi-axis version tracker.
Same basename, unrelated store — a live instance of `T-BASENAME-COLLAPSE-001`.

## 2. The authority that actually exists

`modules/capability_runtime` — the CPP-APIR capability-level registry, store
`vault/capability_runtime/contracts/*.json`, 10 contracts.

It is **live**, not shelved: this session's own tier was computed by `modules.gsd_x.tier`
over it, naming `secret_containment`, `output_quality_gate`, `liveness_reachability` and
`premise_verification` as MANDATORY. That is a per-prompt inheritance path.

It already held both halves of the W3 problem, separated by design and never joined:

- `retirement.py` — evaluates whether a `retirement_condition` has come true. **Propose-only
  on purpose**: "a capability that retires itself is a gate that grades itself."
- `applicability.py` — selects capabilities for a mission through five deterministic gates.
  **Never consulted lifecycle at all.**

An evaluator with no effect, and a selector with no authority input. W3 is the authority
between them: the state an Owner writes and the selector honours.

### Why not `maturity`

`Maturity` is a FITNESS scale consumed as one 0.15-weighted factor. Degrading MATURE →
EXPERIMENTAL moves a score by at most `0.15 × 3/4 = 0.1125`, so a relevant, high-stakes
capability stays MANDATORY however far its maturity falls. Revocation through maturity is
arithmetically impossible, and "less proven" is the wrong claim anyway. The three axes stay
separate: `maturity` ranks, `retirement` evidences, `lifecycle` authorises.

## 3. Consumers, and the bypass sweep

Enumerated structurally (AST import edges + name mentions across 889 Python and 1,642 other
files), never by grepping for the gate:

| consumer | reaches the selector how | honours the gate |
|---|---|---|
| `modules/gsd_x/tier.py` | `evaluate_all` → `evaluate` | **yes** — proven at both poles in the real consumer |
| `modules/setup_os/graph.py` | builds a `MissionContext` only; selects nothing | inherits it |
| `modules/universal-meta-systems/runtime/specialization.py` | `derivatives.derive` | **yes** — `derive` refuses a withdrawn parent |
| `tools/seed_capability_contracts.py` | writer/seeder, no selection | n/a |
| `commands/capability.md` | prompt surface over the CLI | inherits it |

`gsd_x/tier.py::_silence_dormant` imports `_hits` and `load_contracts` directly, which looks
like a bypass and is not: it only FILTERS blocked verdicts for display and never activates.
It did need `_missing_fact` extending, or a lifecycle refusal would have read as "unknown
blocking verdict".

**Gate placement.** Gate 0 in `evaluate`, ahead of anti-triggers and the dormancy gate.
Every other gate asks whether a capability FITS a mission; that question does not arise for
one that may not be inherited at all. First position makes the guarantee a property of the
function rather than of the inputs — proven against a maximally-satisfied context
(evidence, runtime, prerequisites and owner all supplied).

## 4. Migration outcome — no blind default-ACTIVE

Evidence reused from `retirement.py` rather than invented:

| retirement verdict | lifecycle written | count |
|---|---|---|
| ACTIVE (probe ran, condition measurably not met) | `active` | 4 |
| NEVER (declared permanent) | `active` | 2 |
| UNEVALUABLE / NO_CONDITION / EXTERNAL | **nothing — stays `unknown`** | 4 |
| RETIRED_BY_EVIDENCE | reported for an Owner, never auto-revoked | 0 |

Diff: 6 files, 6 insertions, 0 deletions — one line each. A third `--apply` leaves the log
and every contract byte-identical.

**UNKNOWN activates, and that is a decision with a reason.** Resolving absence to "withheld"
would have silently disabled four capabilities this estate runs as MANDATORY every prompt
— `premise_verification` is one, and it lands UNKNOWN. A shrink-only ratchet
(`vault/capability_runtime/lifecycle_ratchet.json`) drives the population down instead;
when it reaches zero, tightening UNKNOWN into WITHDRAWN is one line with no population left
to break.

## 5. Corpus disposition authority

`disposition_ledger.propose` is a candidate generator whose evidence is lexical. Measured
with an instrument that is not the scorer: `spearman(proposals, distinct vocabulary) =
+0.756`, `spearman(proposals, bytes) = +0.735`.

`modules/ucr_cif/ownership_evidence.py` adds structural signals that cannot be won by
saying a word more often, and `tools/ucr_cif_adjudicate.py` promotes only on them.

| | count |
|---|---|
| authoritative disposition | **996** (was 0) |
| candidate REFUTED | 659 |
| ABSTAIN, open and typed | 503 |
| UNRESOLVED, no candidate | 218 |
| **total** | **2376** — verified to sum |

`agents/oneshot-architect-auditor.md` — a single 36 KB file — is refuted on 204 of its 214
claims. Roughly half of `governance-overlay`'s were volume artifacts.

## 6. Open, and honestly so

- **UNMAPPED is not zero and was not forced to zero.** 503 ABSTAIN + 218 UNRESOLVED, each
  carrying a typed reason rather than sitting in an anonymous pile.
- **Hook/mission latency remains UNMEASURED.** W3 added no synchronous hook work, so the
  precondition named in W2 stands unchanged: re-measure on a host with headroom. This
  session's host ran at 7.6–8.8 % free of 32 GB; no timing claim was made from it.
- **`V-UCEIMR-G2-COVERAGE` fails on `cdicf-installer`** and is PRE-EXISTING — proven by
  running that suite with and without W3 and diffing the failure lists. Same root cause as
  its UNKNOWN classification: no retirement probe exists for it. Not silenced.
- **`skill_heat_map_indexer.py:141`** carries the same path-substring identity class as the
  fixed defect, at low severity (a heat-map name). Named debt, not fixed here.
- **Gate 25 is untouched.** W3 proves revocation changes a real consumer; that is one
  property, not the compound-effect contract.
