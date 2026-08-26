---
title: Frontier-28 — D2A verdicts for the 28 hypotheses
date: 2026-08-25
status: PHASE 3 COMPLETE — all 28 classified
cutoff: bc81ca76cd8ef9ea78982c99016a03e979a91570
mandate: brief §10 (verdict set) · §13 (cross-hypothesis dedupe) · §21 (owner minimisation) · §58 (no metric gaming)
---

# Verdicts

## Correction first: two claims of mine were wrong

**1. "Both predictors are starved."** Committed in `3a3e78c`. It is false.
The claim traced to a module comment measured **2026-08-06** reporting 9 events. Measured
today, `vault/ceps/events.jsonl` holds **69 events across 9 distinct categories and 10
days**, four categories repeating, most recent written *today*. Both subagents read the
self-report; neither read the store. `predictive.substrate_quality()` now returns
**`SUBSTRATE_OK`** with three learned pairs: `regression→tooling`, `tooling→env`,
`tooling→regression`.

**A module's statement about its own data is a measurement with a timestamp, not a fact.**
It ages exactly like any other cached value, and it ages invisibly because it reads as
documentation.

**2. EED is not `DOCUMENTED`.** `modules/cognitive_load/load.py` measures the cost of
assembling enough context to change a unit — public-symbol surface, dependency width,
declared entry points. That is a real complexity metric with an executable surface.
Corrected to `PARTIALLY_MATERIALIZED`; the missing part is any *trend* over time or
complexity-per-unit-**capability**, which is what the hypothesis actually asks for.

## The sharpest finding: two broken halves of one capability

FPO and AFP are the same capability — predict a failure from precursor signatures in
`vault/ceps/events.jsonl` — implemented twice, and neither delivers, for **different and
individually invisible reasons**.

| | FPO (`cascade_prevention/predictive.py`) | AFP (`pp_agents/signals/cascade.py`) |
|---|---|---|
| Dispatched automatically? | **No** — registered at `SURFACE_DETECTORS["session"]`, no caller supplies that key | **Yes** — every prompt, via `jit_skill_loader` from three hooks |
| Substrate | `SUBSTRATE_OK`, 3 learned pairs | same store |
| Fires on real input? | would — never asked | **No** |

AFP's failure is at the **interface**. `_build_cascade_map()` keys on
`f"{category}:{subsystem}"` — learned keys are `regression:bash:cat`, `tooling:bash:cd`,
`regression:bash:cd`. `evaluate()` then tests `src_key.lower() in haystack`, where the
dispatcher passes **raw error message text** (`proactive_dispatcher.py:127`). Proven both
ways: the store's own most recent error text
(`"[Tool result missing due to internal error]"`) returns `None`; the synthetic composite
key fires. A composite assembled from two structured CEPS fields will never appear
verbatim inside an error string.

So the estate holds a predictor with a healthy substrate that nothing calls, and a
predictor that is called constantly and cannot match. Three distinct silent-failure modes
across two modules — **never dispatched**, **type-mismatched at the boundary**, and the
one I wrongly assumed, **starved** — and only the third would have been visible to any
existing instrument.

**Verdict: MERGE.** Not a new system, not even new logic. FPO's substrate analysis is
correct and its pairs are real; AFP's dispatch path is correct and already automatic.
One working capability exists across two files; it has never been assembled.

## Production evidence — the merge fired on a real prompt

Observed 2026-08-25, roughly an hour after the fix landed. The `UserPromptSubmit`
advisory on the Owner's next turn carried:

> `[Woz] [pp-cascade-guard] 'regression:bash:cd' has historically preceded: tooling:bash:cd.`

The whole chain, verified against live state rather than inferred: a real CEPS event
`regression:bash:cd` was recorded at `14:50:20Z` (store grew 69 → 72) → the 30-minute
window admitted it → `_recent_error_context()` returned the structured key →
`cascade.evaluate()` matched on `category:subsystem` → the dispatcher put it in
`additionalContext`. At commit time the honest claim was "capability installed,
compounding effect not yet proven" (§78). It is now proven: **AFP/FPO moves from
`ENFORCED` to `PRODUCTION_PROVEN`**, on an observed fire, not an assertion.

**And the counterweight, which matters more than the win.** The event's recorded
`root_cause` is **`"0 failed"`** — a *test-success* line, classified as a `regression`.
The prediction mechanism is correct and the key match is sound, because matching uses
`category:subsystem` and never the text. But the producer feeding it is recording benign
output as errors, so some fraction of these advisories will be built on non-events.

Turning the signal on has therefore made a **second, older defect visible for the first
time**: while every consumer returned `None`, nothing could reveal that the store's
contents were unreliable. Data quality was untestable precisely because nothing read the
data. This is a new finding of this mission, not a regression introduced by it, and it
belongs to whoever owns `hooks/bug-hunter-ceps-bridge.js` — recorded here, not silently
carried, and it does not alter the rung, which rests on the mechanism firing correctly on
a genuinely recorded event.

## The 28

| # | Hypothesis | Rung | Verdict | Owner / action |
|---|---|---|---|---|
| 1 | SCIF | ENFORCED ⚠ | **DONE (this mission)** | `duplicate_to_advantage/provenance.py`, shipped `ca8e885` |
| 2 | EIAA | PARTIAL | **EXTEND** | `graphify/global_store.py` — read `origins` back to discount echoes |
| 3 | OECL | PROVEN | **OWNED** | `daif/two_arm_trial.py`; scope narrow (tokens only), stated |
| 4 | BSC | PARTIAL | **CONNECT** | 4 modules already declare their blind spots — generate a view, do not add a registry |
| 5 | NMIE | DOCUMENTED | **EXTEND** | CEPS producer exists and is dispatcher-registered; add near-miss capture, do not build an archive |
| 6 | FPO | MATERIALIZED | **MERGE** → with 26 | dispatch it |
| 7 | IRBE | DOCUMENTED | **CREATE** (gated) | genuinely absent; `HR-NOVELTY-001` proof required |
| 8 | CCCE | MATERIALIZED | **OWNED** | `mutation_ratchet.py` + `run_sqi.py` |
| 9 | CIG | MATERIALIZED | **OWNED** | `decision_review/decision_kernel.py` |
| 10 | IBRS | MATERIALIZED | **OWNED** | `decision_kernel` + `architecture_horizon` |
| 11 | BPCC | PARTIAL | **EXTEND** | `rollback/` owns revocation; canary half absent |
| 12 | FLSA | DOCUMENTED | **DEFER** | no observed instance of the failure it prevents |
| 13 | CSO | DOCUMENTED | **CREATE** (gated) | confirmed absent; `cognitive_os` does eviction, not sufficiency |
| 14 | TND | ENFORCED | **OWNED** | `spec_gate.check_novelty_gate` via `jit_skill_loader` |
| 15 | DEC | PARTIAL | **EXTEND** | `decision_review` records decisions; erasure semantic missing |
| 16 | SREE | PARTIAL | **EXTEND** | `deep-research` annotates overlap; nothing is skipped |
| 17 | EED | PARTIAL ▲ | **EXTEND** | `cognitive_load/load.py` — add trend, not a new meter |
| 18 | ACD | ENFORCED | **OWNED** | `hooks/d2a_gate.js` |
| 19 | CLAO | PROVEN ± | **EXTEND** | `liveness/reachability.py` — dispatch-awareness (see below) |
| 20 | CCV | PARTIAL | **DEFER** | closest owner self-declares SPEC, not a running system |
| 21 | ADW | PARTIAL | **EXTEND** | `architecture_horizon` links consumers; nothing watches for drift |
| 22 | CHF | PARTIAL | **DEFER** | needs upstream version/EOL feeds that do not exist here |
| 23 | KRR | ENFORCED | **CONNECT** | consumer auto-fires; **producer is manual** — automate the rebuild |
| 24 | ERDR | MATERIALIZED | **CONNECT** | `verify_global_mirrors.py` works; reachable only by hand |
| 25 | HEC | PARTIAL | **EXTEND** | `alert_escalation` cuts frequency, not decision size |
| 26 | AFP | ENFORCED | **MERGE** → with 6 | interface mismatch |
| 27 | IRRL | PROVEN | **OWNED** | `fd_04_contrast.py` + `FRONTIER_RESIDUAL_MAP.md` |
| 28 | ICRA | PROVEN | **OWNED** | `sqi/weakening_detectors.py` |

### Distribution

| Verdict | Count |
|---|---:|
| **OWNED / REFERENCE** | 8 |
| **EXTEND** | 9 |
| **CONNECT** | 3 |
| **MERGE** | 1 (covering 2 hypotheses) |
| **DEFER** | 3 |
| **CREATE** | **2** — IRBE, CSO, both gated on `HR-NOVELTY-001` |
| DONE this mission | 1 |

**CREATE: 2 of 27 = 7.4%.** Below this estate's historical band (IAS 9%, RE Baseline 25%,
DAIF 36%). Recorded as measured, not steered — §58 forbids aiming at a distribution, and
that prohibition binds in both directions.

## Cross-hypothesis dedupe (§13)

The 28 do not survive as 28.

- **FPO + AFP → one capability**, two broken halves (above).
- **CLAO's extension *is* the instrument the BSC/FLSA findings demand.** Dispatch-awareness
  in `reachability.py` is what would have caught FPO automatically. One extension, three
  hypotheses served.
- **IBRS ⊂ CIG.** Both live in `decision_kernel.py`; blast radius is the input to
  amplification governance, not a separate owner.
- **EIAA and BSC are the same shape** — a claim capped by what its evidence can support.
  EIAA caps on ancestry, BSC on visibility.
- **KRR and ERDR are one pattern**: an automatic consumer with a manual producer (KRR), and
  a correct comparator nothing calls (ERDR). Same `CONNECT`.

Fourteen of twenty-seven are real code that no automatic surface invokes. **That is one
problem wearing fourteen names**, and it is the mission's actual subject.

## What will not be built, and why

- **No new autonomy OS.** HIC-OAR owns avoidable human intervention.
- **No dispatch-coverage system.** `reachability.py:78-85` already holds that reasoning,
  sealed 2026-07-22 for the hook layer — carry it down, do not re-found it.
- **No blindspot registry.** Four modules already declare theirs in code; a generated view
  beats a parallel registry (§61).
- **No near-miss archive.** The event store, its producer and two consumers already exist.
- **FLSA, CCV, CHF deferred** — each would be built against an unobserved failure, an
  owner that self-declares non-running, or data feeds that do not exist.

## Phase 5 order and status

1. **MERGE FPO + AFP** — **DONE** (`44a8f7f`), and **PRODUCTION_PROVEN** (`39c2e00`):
   observed firing on a real prompt within the hour. A regression I introduced here — the
   no-input fast path — was caught by the `benchmarks-ok` gate and fixed in `064d29b`.
2. **EXTEND liveness with dispatch-awareness** — **DONE** (`904dd21`, wired `9a3dd22`).
   `modules/liveness/dispatch.py`; 5 of 7 `SURFACE_DETECTORS` keys never supplied. Now
   reported per-session through the Stop delta, not only inside a test row.
3. **CONNECT KRR's producer** — **DONE** (`9a3dd22`). `audit_cache.py --refresh` plus
   `session_delta.refresh_audit_cache`; 3016 ms → 92 ms after persisting the stem map.
4. **Remaining, in order:** EIAA (read `origins` back to discount echoes) · DEC (cache a
   verdict as a default so a repeat decision stops being a decision) · SREE (skip, do not
   annotate) · HEC (compress the ask, not the frequency) · ADW · EED · BPCC · CLAO ·
   CCV — then the two gated CREATEs (**IRBE**, **CSO**) once each passes the
   `HR-NOVELTY-001` 13-question proof against a discovered sweep.

### Umbrella state, recorded rather than waved off

The full `verify_spp` run exits 1 on 7 rows. Each was checked against my changed-file set,
which contains **zero** files under `hooks/` or any global path:

| Row | Cause | Mine? |
|---|---|---|
| `benchmarks-ok` | `proactive_dispatch_ms` 103 > 30 — cold lazy-import of ~14 signal modules (94.5 ms cold / 69.2 ms warm; `cascade.evaluate` = 0.003 ms). Was 43 ms at S0, already 91 ms in the 2026-06-03 audit. | **the 123→103 part was** — fixed in `064d29b`; the residue is not |
| `hooks-registration` | marker-set mismatch including `output_contract_stop`, which a **concurrent pane** has modified and not committed | no |
| `mirror-parity` | canonical↔live drift in 5 files (`hook-dispatcher.js`, `lazarus-stub-recover.js`, …) | no |
| `dataset-build` | **passes standalone**; fails only under parallel execution | no |
| `drift-report` | `PAIRS is empty/missing` (config) | no |
| `paths+secrets` | pre-existing 129-entry allowlist across 50 files | no |
| `restart-and-lag` | environment/timing gate | no |

`mirror-parity` is the ERDR finding made concrete: the comparator works, nothing invokes it
automatically, so drift accumulates until someone runs it by hand. None of these are
dismissed — they are attributed, and the ones that are mine are fixed.

---

## Continuation session — 2026-08-26

Nine workstreams. The order was recompiled from the dependency graph rather than taken
from the previous list: producer semantics and evidence independence are the substrate
every downstream verdict rests on, so they went first. Two of the brief's own premises
were disproved by reading the code, and two of my own claims from the previous session
were retracted by measurement.

### Corrections to claims I made yesterday

| Claim | Reality | Evidence |
|---|---|---|
| "AFP/FPO is PRODUCTION_PROVEN" | The **mechanism** is. The **capability** is not: it fired on `regression:bash:cd`, and `bash:cd` is a navigation prefix that fused 15 unrelated commands into one bucket. Every key in the learned map was corrupt; the map is now empty and correctly silent. | `1f3a3a1` |
| "dataset-build passes standalone, fails only in parallel" | `verify_spp` **has no parallelism** — rows run sequentially through one `subprocess.run` loop. The row takes 176.8s against a 60s budget and can never pass. | `2aebbaa` |
| "mirror-parity fails on canonical↔live drift" | It was failing on a **crash**: bare `git` via subprocess, `FileNotFoundError`, before a single check ran. It was not measuring drift; it was not measuring anything. | `563a565` |
| "drift-report fails on empty PAIRS config" | `PAIRS` does not exist. The producer migrated to discovery; the consumer still read the retired constant and exited 2 for months. | `dd2b6ad` |

### The producer defect was three defects, and the store was majority-corrupt

| | Defect | Scale |
|---|---|---|
| P1 | `\b\d+ failed\b` matched **"0 failed"** — a pytest SUCCESS line filed as a regression | 1 event |
| P2 | text a tool PRINTED was not distinguished from a failure it SUFFERED | **51 of 75** |
| P3 | `subsystemOf` took a chained command's leading token, so `cd X && pytest` bucketed as `cd` | 15 of 19 regressions |

P2 at scale was greps and file reads of Python and JS: root causes like
`except Exception as e:  # noqa: BLE001`. Reading this repo's own source recorded failures.

Backfill classified all 75 without purging: **24 valid, 51 identity_suspect, 1 invalid**.
Both readers honour the verdict — filtering one left `cascade_prevention/predictive` still
inferring from the same rows, caught only because the filtered reader reported 0 pairs
while that one still reported 3.

### Capability dispositions

| Cap | Verdict | Evidence |
|---|---|---|
| **EIAA** | **DONE** `95f7c0c` | `ancestry()` counts ancestors, not addresses. Live: **79 addresses → 28 independent roots**; 27 of 28 multi-origin nodes carry byte-identical content. |
| **DEC** | **DONE** `ac1fa4c` | Input-fingerprint + precedent reuse. Identical decision → verdict from precedent, nine stages skipped; moved evidence still re-reasoned. |
| **SREE** | **DONE** `9909076` | `research_discovery` was an audited ORPHAN; now consulted BEFORE the spawn. A fresh run is reused, a 30-day-old one expires into a real search. |
| **EED** | **DONE** (this commit) | `eed_delta.py`. This mission: owners 84→85, context cost **+1.2%** — and the one new owner is a **concurrent pane's**, not mine. My 12 commits added 2 files to existing owners. |
| **CLAO** | **DONE** `904dd21` + `9a3dd22` + `d48a501` | Dispatch-awareness reports per-session; 2 of 5 never-supplied keys now supplied from a live surface. |
| **ADW** | **DEFERRED-WITH-OWNER** | `architecture_horizon` links consumers; nothing watches for drift. Not built: it would be built against an unobserved failure, and this session found four real ones with evidence. Reopen when an assumption actually goes stale in the record. |
| **HEC** | **DEFERRED-WITH-OWNER** | `alert_escalation`. Subordinate to HIC-OAR by prior verdict; no measured escalation in this session to compress. |
| **BPCC** | **DEFERRED-WITH-OWNER** | `rollback/` owns revocation; the canary half is absent. No high-fanout propagation occurred here to canary. |
| **CCV** | **DEFER** (unchanged) | Closest owner self-declares SPEC, not a running system. |
| **IRBE** | **NOT ENTERED** | `HR-NOVELTY-001` unsatisfied — the 13-question proof against a discovered sweep was not run, so implementation is forbidden. |
| **CSO** | **NOT ENTERED** | Same gate. The open question remains whether it is a new system or an evaluation head of the existing context compiler. |

Four deferrals are deliberate. Building against an unobserved failure is how this estate
accumulated fifteen consecutive majority-owned proposals; the four findings below were
observed, and they were worth more than four speculative capabilities.

### The deepest finding: two sealed Hard Rules were starving

HR-CASCADE-001 (refuse a deploy without passing tests) and HR-CASCADE-003 (pause a commit
without verification) both read `ctx["verified"]`. **Nothing in the estate had ever written
it** — zero producers across `modules/`, `tools/`, `vault/`. Both defaulted to True at
every call site and could not fire under any circumstances. They read as enforcement and
were inert. `d48a501` ships the producer and supplies both surfaces; the gate proves they
fire when fed and stay silent when verified.

### Owner actions, named because this repo cannot take them

1. **`~/.claude/settings.json`** — the entry whose command ends `--event=PreToolUse-Bash-chain`
   has `"matcher": "Bash"`. The whole chain, HR-CASCADE-002 included, therefore never sees
   PowerShell, on a host whose own doctrine mandates PowerShell for python/git/npm.
   Change to `"Bash|PowerShell"`, the shape two sibling matchers in that file already use.
   `verify_spp` row `correctness-traps` is RED BY DESIGN until this lands and flips green
   by itself afterwards.
2. **Five drifted mirror files**, now with direction and age: `hook-dispatcher.js` (repo
   +11.8d), `session-file-guard.js` (repo +67d), `lazarus-stub-recover.js` (+1.9d),
   `_oneshot_solitary_empty_shell_cleanup.js` (+1.8d), `apex-completion-standard.md`
   (loose +57d). Not remediated deliberately: `~/.claude/hooks` is write-denied here, and
   mtime is not content lineage — adopting a 57-day-newer loose file could discard
   deliberate PP edits.
3. **343 files exist on one side only** (hooks 37/28, commands 10/59, agents 31/10,
   knowledge_vault 168/0). Only 28 pairs are compared at all. Unpaired is not equal, and
   that number is not yet dispositioned.

### Concurrency

A concurrent pane checked out `feature/knowledge-acquisition` from `main` mid-session and
committed three times; my commits landed on top of theirs in the shared worktree. Nothing
of theirs was reset, rebased, or force-pushed. My work was additionally cherry-picked onto
`frontier28/producer-semantics` from `main` via a throwaway worktree and pushed, so it is
durable without publishing another pane's unfinished branch.
REE | PARTIAL | **EXTEND** | `deep-research` annotates overlap; nothing is skipped |
| 17 | EED | PARTIAL ▲ | **EXTEND** | `cognitive_load/load.py` — add trend, not a new meter |
| 18 | ACD | ENFORCED | **OWNED** | `hooks/d2a_gate.js` |
| 19 | CLAO | PROVEN ± | **EXTEND** | `liveness/reachability.py` — dispatch-awareness (see below) |
| 20 | CCV | PARTIAL | **DEFER** | closest owner self-declares SPEC, not a running system |
| 21 | ADW | PARTIAL | **EXTEND** | `architecture_horizon` links consumers; nothing watches for drift |
| 22 | CHF | PARTIAL | **DEFER** | needs upstream version/EOL feeds that do not exist here |
| 23 | KRR | ENFORCED | **CONNECT** | consumer auto-fires; **producer is manual** — automate the rebuild |
| 24 | ERDR | MATERIALIZED | **CONNECT** | `verify_global_mirrors.py` works; reachable only by hand |
| 25 | HEC | PARTIAL | **EXTEND** | `alert_escalation` cuts frequency, not decision size |
| 26 | AFP | ENFORCED | **MERGE** → with 6 | interface mismatch |
| 27 | IRRL | PROVEN | **OWNED** | `fd_04_contrast.py` + `FRONTIER_RESIDUAL_MAP.md` |
| 28 | ICRA | PROVEN | **OWNED** | `sqi/weakening_detectors.py` |

### Post-review corrections — 2026-08-26, after the adversarial pass

An independent review run with the sole objective of falsifying this session's
claims found three real defects and forced two maturity claims down. Both are
recorded here because a claim I had to retract is worth more than one I got right.

**A data-loss path in code shipped this session.** `ceps_backfill_audit.load()`
dropped unparseable lines and `--apply` rebuilt the whole log from the survivors,
so a torn write would have been deleted permanently — by the tool whose docstring
promises it never purges. Also non-atomic (a truncating 55KB write under a 30s
budget) and unguarded against the producer appending mid-run. All three fixed in
`d5bd18d`; three gates pin them.

**A forgeable green.** `verify_spp --row <one>` recorded a full-tree verification,
so a ten-second row could vouch for the estate and satisfy HR-CASCADE-001's deploy
gate for an hour. A partial run now records nothing and says so.

**An orphan I shipped.** `test_eed_delta.py` landed with no umbrella row — the exact
defect this session sealed a rule about, three commits after sealing it. Wired.

**And a THIRD consumer of the corrupt events that I had missed.** `ceps.propagate()`
queries the FTS5 sidecar and returns its prevention rules as live advisories. I had
filtered the two cascade readers and left this one untouched, so judged-bad events
kept reaching a live surface by a path nobody had looked at. Pruning on `--apply`
took the index from **97 rows to 19** — the advisory surface had been serving rules
derived overwhelmingly from events that were never failures. A verdict honoured in
one representation and ignored in another is not a verdict.

#### Two maturity claims corrected downward

| Capability | Claimed | Actual | Why |
|---|---|---|---|
| HR-CASCADE-001/003 supply | live | **WIRED, not exercised** | The producer only fires on a full umbrella pass; none had completed when the claim was written, so `was_verified()` returned None and both surfaces were correctly silent — and therefore inert. |
| **SREE** | live | **CANONICAL ONLY, NOT RUNNING** | `hook-dispatcher.js:123` registers `'./research-intent-detector.js'` — a RELATIVE path resolving to `~/.claude/hooks/`, whose copy is 95 days old. It registers the CEPS bridge (`:267`) and cascade gate (`:197`) by PP path, so those edits ARE live. Same repo, same session, two different answers, decided by one character of path. |

The SREE correction is this repo's own documented split-brain — canonical versus
live — landing on my own work, in the same session that repaired the comparator
which detects it. The comparator is what caught it.

#### Umbrella, before and after the timeout repair

| Row | Before | After |
|---|---|---|
| `dataset-build` | rc=124, unmeasured | **rc=0, 94.4s — passes** |
| `auto-reset` | rc=124, unmeasured | **rc=0, 58.7s — passes** |
| `claude-md-router` | rc=124, unmeasured | **rc=0, 50.4s — passes** |
| `paths+secrets` | rc=124, unmeasured | rc=1, 11.9s — **its real failure, now visible** |

STRICT FAIL fell 10 → 7. Three rows were never failing; they were never finishing.
The fourth was failing for a real reason that an unmeasured verdict had been hiding,
which is what raising a budget is supposed to expose rather than paper over.

Remaining 7, each attributed: `mirror-parity` and `drift-report` (real drift, Owner
decision, listed above) · `paths+secrets` (pre-existing 129-entry allowlist across 50
files) · `hooks-registration` (marker set includes a concurrent pane's uncommitted
`output_contract_stop`) · `restart-and-lag` (environment/timing) · `correctness-traps`
(RED BY DESIGN until the Owner widens one matcher) · `benchmarks-ok` (4/8 over target;
`tco_gate_ms` 357>270 — pre-existing drift, not this session's).

#### Third Owner action

`hook-dispatcher.js:123` resolves `./research-intent-detector.js` against
`~/.claude/hooks/`, which this repo cannot write. Either copy PP's canonical hook
across, or change that entry to the `../skills/claude-power-pack/hooks/...` form the
two sibling entries already use. Until then the SREE skip exists and does not run.
