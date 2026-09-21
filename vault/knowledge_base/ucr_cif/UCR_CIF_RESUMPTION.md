# UCR-CIF — RESUMPTION

Read this file and continue with zero prior context. Update it after every sealed unit,
never only at the end.

## 0. Lineage — what changed on 2026-09-19, and why this is not a silent supersession

A predecessor session (2026-08-25) ran this mission against a **1,521,366-byte** corpus and
read it as a **prose dataset compendium**: author `ucr_cif_NN_*.txt` Parts. It sealed a
Reality Scan, a full source inventory, and a first D2A pass, then **halted on an open Owner
ruling A/B/C** — how many Parts to write, where B implied 1,200–1,600 Parts (~1.8 M words).

The Owner ruled on **2026-09-19: option A, and the compendium framing is SUPERSEDED as the
primary deliverable.** The mission's new brief states it directly — a mission that mainly
produces Markdown, registries and plans is not complete. The deliverable is **executable
institutional capability**; corpus coverage is proven by a machine-checkable disposition
ledger, not by word count.

**Nothing of the predecessor is discarded.** Its 1,394 inventory records are institutional
capital and are reused, not re-derived. Its five measured traps are adopted as design input.
Existing Parts may persist as historical artifact, derived view or compatibility surface —
they are simply no longer the completion mechanism.

> **Hard rule adopted:** NO MANUAL PROSE EXPANSION MAY SUBSTITUTE EXECUTABLE SEMANTIC CLOSURE.

## 1. Identity

Convert the **full** corpus — `Dataset Claude Power Pack Universal Construction Ratchet &
Compounding Intelligence Fabric 1 (1).txt`, `C:\Users\User\Downloads\`, **167,842 lines /
3,037,867 chars** — into executable institutional capability for Claude Power Pack, without
re-authoring capability the estate already owns.

**Corpus identity, proven by content not filename:** the older 75,350-line file is a
**literal line-for-line prefix** (`first_differing_line_index=None`). The `(1)` copy appends
**92,492 lines (55.1 %)**, reaching the Evo-Devo / developmental-inheritance layer. The new
region measured **clean** — 0 harness-contamination windows of 925, Spanish density median 7
— so the old half's nine classified contamination runs remain the only ones.

**Physical constraint, and therefore an architecture requirement:** ~870 k tokens. **The full
corpus may never enter model context.** It is processed by tooling into durable intermediate
state; the model consumes only targeted slices, structured summaries, unresolved conflicts
and evidence windows. Subagents are not a context-limit workaround.

## 2. Exact state

**Working surface — ISOLATED.** Worktree `C:\Users\User\Apps\pp-ucr-cif`, branch
`ucr-cif/construction`, base pinned at **`50837ed`** (`main`).
**As of 2026-09-22 (W9 close) HEAD is `9c93db4`, 51 ahead / 74 behind `origin/main`.**
W9 audited those 74 upstream commits BEFORE building: 109 files changed, and the only overlap
with this mission's dependency surface is
`vault/capability_runtime/contracts/reconstruction_parity.json`, a contract DATA file. Nothing
upstream touches `modules/ucr_cif`, `capability_runtime` code, `spec_gate`, `graphify`,
`liveness`, `repo_identity` or `mutation_probe`. **Upstream is orthogonal; do not rebase on
its account.**
**W9's own pin lesson: the prompt's pin was CORRECT and the CHECKOUT was wrong.** That session
opened in the SHARED tree `~/.claude/skills/claude-power-pack` (branch
`feature/knowledge-acquisition`, ~400 dirty paths from the other writer), whose harness
snapshot reported it "clean". Verify the WORKTREE, not only the commit.
The other writer keeps landing work. Every earlier wave's commits remain
ancestors; nothing has ever been rebased. **W8 opened by falsifying its own handoff**: the
prompt that started it carried a state pin of `3c02e32` (W5 seal, 27 ahead / 33 behind) and
asked for W6 to be built, but `3c02e32` was already **eleven commits** behind the branch tip —
W6 (`aace845`) and W7 (`b3fefe7`) were both sealed. Executing it literally would have rebuilt a
landed wave, which is the exact duplication this mission exists to prevent. **Read this file,
not the prompt's pin, and check `git log` before believing either.**
Re-measure the divergence before any merge, and note that
`git status` in the SHARED checkout (`~/.claude/skills/claude-power-pack`) describes the
OTHER writer's branch `feature/knowledge-acquisition` — never read this mission's state from
there.
Base chosen by measurement: `feature/knowledge-acquisition` was **0 ahead / 23 behind**
`main`, so `main` is a strict superset. A **live concurrent writer** is confirmed on the
shared tree — HEAD moved `d243137` → `3e56322` mid-session and `origin` advanced. That tree
is never written by this mission and never rolled back.

**SEALED (this session)**

- **Phase 0/3 plan** — approved inline, Owner decisions 1–6 authoritative (see §3).
- **W0 · institutional closure** — `a86b131`. `tools/institutional_closure_audit.py` +
  `vault/audits/ucr_cif/w0_closure.json`. **Both spine stores are CLOSED**:
  `baseline_ledger.jsonl` (1W/1R) and `ceps/events.jsonl` (1 direct + 9 indirect writers,
  7 direct readers). Caveat recorded, not buried: **299 unresolved `open()` sites**, so every
  verdict is a lower bound and `INERT` means "not statically reachable", never "dead".
- **W0 · hook-chain baseline** — `44999eb`. `tools/hook_chain_census.py` +
  `vault/audits/ucr_cif/w0_hook_baseline.json`. 10 chains, 69 members, **0 missing**.
  **`Stop-chain` = 25 members, concurrency 8, NO deadline**; six of ten chains have no
  deadline; only `UserPromptSubmit-chain` is bounded (11,500 ms / 4 lanes).
- **W0 · traps** — three instrument failures recorded in `03_MISSION_TRAPS.md`
  (`T-BASENAME-COLLAPSE-001`, `T-CONSTANT-PATH-INVISIBLE-001`,
  `PR-STARVED-HOST-COUNT-NOT-CLOCK-001`), appended to the predecessor's five.

- **W1 · corpus compiler** — `7f08ba0`. `modules/ucr_cif/corpus_compiler.py`. Deterministic,
  no model call. Lines 75,351..167,842 → **47 slices, 982 unique units**, coverage gaps
  NONE, overlaps NONE. law 619 / definition 202 / metric 149 / trap 12.
  **Production Reality met:** idempotent (two runs SHA-256 identical); **killed with 19 of
  47 slices on disk, restarted, completed to 47, byte-identical to the clean run.**
  `--selftest` drives boundary independence at both poles (green 60/60 identical; red
  `readahead=0` changes 10 ids). Its first green on the real corpus was **vacuous** — no
  paragraph straddled a slice edge — and forcing the case exposed a real split-unit bug.
- **W1 · unified corpus** — `2cec9b7`. `vault/ucr_cif/requirement_corpus.json`,
  **2,376 units** = 1,394 inherited concepts (`claim_class=INFERRED`) + 982 compiled
  statements (`OBSERVED`). **Partition VERIFIED:** inherited max line 75,323, compiled span
  75,352..167,812, out-of-prefix 0, uid collisions 0, 1 cross-half key match. 362 inherited
  records are unattributed (their `ranges` says `r2_slice4`) and are counted as such.
- **W2 · disposition ledger** — `085ba2f`. `modules/ucr_cif/disposition_ledger.py`.
  **2,158 of 2,376 (90.8 %) propose an existing owner; 218 (9.2 %) UNRESOLVED.** Confidence
  spans 115 distinct values (0.006–0.533), so it is not the D2A constant floor. Independent
  agreement with the predecessor's prior and the estate's 9–36 % historical CREATE rate.
  Gate driven red **five ways** (unmapped · laundering · shrunken denominator · degenerate
  confidence · blind index) plus the green pole.
  **`disposition` is authoritative and still 0 — `proposed_disposition` is a candidate.**
  Known bias, stated not buried: `governance-overlay` (452) and one agent `.md` (214) win
  by vocabulary volume, not ownership. Review is W3's input.
- **W2 · trap** — `T-EXCLUSION-MATCHED-THE-WORKSPACE-001`: the contamination guard matched
  the worktree's own name `pp-ucr-cif` and indexed **0** files. Caught only by the
  population floor, because "all UNRESOLVED" is also what a correct sweep of a truly novel
  corpus returns — the broken instrument and the flattering reading pointed the same way.

- **W3 · repository self-identity** — `560720c`. `repo_identity.main_repo_root` +
  `tools/test_repo_identity_worktree.py` (15/15). The standing FIOS/FD-07 warning W2 handed
  over was neither a missing asset nor the FP-01 false positive: `_is_pp_repo` tested
  `"claude-power-pack" in <path>` and **this mission's own worktree does not carry that
  name**, so the Power Pack served itself an advisory written for other repositories.
  Reproduced before the fix, byte-identical. Mutation 10/15.
- **W3 · capability lifecycle** — `54d4c88`. `modules/capability_runtime/lifecycle.py`,
  gate 0 in `applicability.evaluate`, `derive()` propagation refusal,
  `tools/capability_lifecycle_migrate.py`, `tools/test_capability_lifecycle.py` (41/41),
  8/8 mutations caught.
  **The handoff's premise was wrong in both halves and the scan is what moved the wave:**
  `baseline_ledger.jsonl` is an append-only HISTORICAL LOG whose only reader is its own
  `--show` (W0's own closure audit), so a status field there would have been a revocation
  nothing could honour; and it holds **42** rows at every committed ref, not 73 — the 73 was
  read from the other writer's uncommitted working copy. Full classification:
  `vault/audits/ucr_cif/04_W3_AUTHORITY.md`.
  **Authority = `modules/capability_runtime`**, which is live (this estate's per-prompt tier
  is computed over it). Lifecycle is orthogonal to `maturity`: maturity is a 0.15-weighted
  ranking factor, so it can move a score by at most 0.1125 and **cannot express withdrawal
  at all**.
  Migration classified **6 ACTIVE on real probe evidence, 4 UNKNOWN with named reasons, 0
  blind defaults** — 6 files, 6 insertions, 0 deletions; a third `--apply` is byte-identical.
  UNKNOWN deliberately still activates (withholding it would have silently disabled four
  MANDATORY capabilities, `premise_verification` among them) and is driven down by
  `vault/capability_runtime/lifecycle_ratchet.json`, shrink-only.
- **W3 · corpus disposition authority** — `9094754`.
  `modules/ucr_cif/ownership_evidence.py`, `tools/ucr_cif_adjudicate.py`,
  `tools/test_false_owner_adversarial.py` (18/18), 4/4 mutations.
  The vocabulary-volume bias is now a measurement, not a suspicion:
  `spearman(proposals, distinct vocabulary) = +0.756`, `bytes = +0.735`.
  **Authoritative dispositions 0 -> 996**; 659 candidates REFUTED, 503 ABSTAIN, 218
  UNRESOLVED, partition verified to sum to 2,376. `agents/oneshot-architect-auditor.md`
  (one 36 KB file) refuted on **204 of its 214** claims.
  The adversarial gate found three defects in the thing it tests, and the mutation drill
  found two more in the gate itself — see `03_MISSION_TRAPS.md`.
- **W3 · completion-standard ratchet** — `8236636`. **Axis C — durable institutional state**
  added to the EXISTING owner `knowledge_vault/core/apex-completion-standard.md`, beside
  Axis A and Axis B. No second standard was created. It is APPLICABILITY-GATED: it binds
  only a feature introducing state future sessions inherit, and silence is the correct
  answer for everything else.
- **W3 · knowledge** — `529ac7c`. Eight entries in `03_MISSION_TRAPS.md`, nine rules in
  UKDL (dedup-checked; two join existing families by reference rather than restatement),
  and `04_W3_AUTHORITY.md` as the authority classification of record.

- **W4 · probe evidence** — `ca54685`. The handoff called `cdicf-installer` and
  `spec_depth_selection` probe debt. **Only one was.** `probe_spec_depth_selection` already
  existed, was registered, and RAN; it abstains because the incident record holds **99**
  entries against a floor of **200**. `cdicf-installer` had no probe and its condition looked
  EXTERNAL — the cause is (npm gaining transactional provenance), the condition's terminal
  clause is not ("making a CDICF-specific installer redundant"), and redundancy is settled
  here. `probe_cdicf_installer` measures the MECHANISM (journal · provenance · recover) plus
  a production consumer of the record the installer writes: verdict ACTIVE, 4 consumers.
  The sample floor also sat AHEAD of the hit scan, so the probe could return UNEVALUABLE and
  nothing else — fixed by placement, **not** by lowering 200, and pinned by a pair of gates.
- **W4 · contract store** — `4ae8e30`. Applying the classification **deleted three fields**
  from `cdicf-installer.json` (`_matcher_note`, `verification_obligations`,
  `minimum_runtime_version`) and escaped every em dash. A dataclass round-trip keeps only
  declared fields; `save_contract` wrote the reduced document over the original. Saves now
  MERGE over what is on disk. `V-CAPRT-ROUNDTRIP` could not have caught it — it saves a
  record built in memory into an empty directory.
- **W4 · external ownership** — `35465dd`. `retirement.py` separates EXTERNAL from
  UNEVALUABLE on purpose; W3's migration mapped both to UNKNOWN. With the owner NAMED,
  external is a closed question, so `cost_routing` and `premise_verification` classify by
  Owner transition (own actor, authority-only disclaimer in the evidence). An external entry
  with no named owner stays UNKNOWN — the fail-closed default, driven on a synthetic subject.
  **UNKNOWN 4 → 1.**
- **W4 · repository identity** — `dd1f66a`. W3 fixed "our worktree does not look like us"
  and left the mirror: an unrelated repo under a path containing `claude-power-pack` reads as
  the Power Pack for ever, because the substring fast path answers before any resolution.
  Replaced, not patched: `repo_identity.is_power_pack` reads the repository's CONTENTS
  (majority of 5 structural marks) through the worktree resolver. Two W3 gates INVERTED IN
  PLACE; identity 15/15 → 17/17.
- **W4 · mutation harness** — `e104f83`. `mutation_probe.py --plan` drives named
  (file, old, new, suite) edits through the harness's own bytecode defences, with
  HARNESS-FAILED as a third outcome when an anchor has rotted. This session's 14 mutations
  are committed as `vault/governance/mutation_plans/ucr_cif_w4.json` and are re-runnable.
- **W4 · knowledge** — `fe87d34`. Five mission traps, six UKDL rules + one amendment
  (`T-PATH-SUBSTRING-IDENTITY-001` EXTENDED, not duplicated), and **Axis C-2** inside the
  existing Apex Axis C — when an unknown population may be CLOSED.
- **W5 · selection** — `bc260cb`. `modules/ucr_cif/disposition_consumer.py` answers "which
  owners does the corpus already hold authority about, for this proposal?" through four
  ordered filters — authority, semantics, lifecycle, applicability — and **four
  distinguishable refusals**, so an instrument failure can never be read as evidence of
  novelty. Applicability requires one DISTINCTIVE shared term, using the producer's own
  `DISTINCTIVE_MAX_HOLDERS` (imported, never redefined, gated against a local copy): without
  that clause a proposal about an espresso machine routed to `modules/knowledge_acquisition`
  on the pair `('institutional', 'system')`, both of them words from the consuming gate's own
  trigger list.
- **W5 · consumption** — `8d18717`, `10d9fee`. `check_novelty_gate` replaces question 4 in
  place with the named owners, their counts and their uids. The count is unchanged on purpose:
  a first version appended, and the verdict then asked for "all 13 questions" while carrying
  14 — caught by the pre-existing `V-NOVELTY-TRIGGER-HIT`, not by any new gate.
  **PRODUCTION REALITY 6/6** drives the real hook in a subprocess under an isolated HOME
  junctioned to this worktree, because the hook computes `PP_ROOT` from `HOME` and would
  otherwise have measured the installed copy.
- **W5 · proof** — `64d3707`. `vault/governance/mutation_plans/ucr_cif_w5.json`, **17/17
  ALL_CAUGHT**. W1 severs the consumer edge with both endpoints intact; a gate that survives
  that was never measuring consumption.
- **W5 · knowledge** — `ae7246a`. Five mission traps, five UKDL rules (dedup-checked against
  the existing inert-state family), and **Axis C-3 — Circulation** inside Apex Axis C.

- **W6 · the second door** — `226ef90`, `aace845`, `7634043`, `dbaa690`, `77b5169`. The SDD-OS
  L/XL spec boundary consumes the same authority through `sdd_tier`'s ProactiveSignal. Six
  directed mutations (`W18`..`W23`) appended to the W5 plan, which therefore carries **23**.
- **W7 · reach calibration** — `a0c96b6` (instrument), `5e18146` (measurement + decision),
  `43abf73` (proof), `8cb3074` (knowledge). **DECISION: KEEP the current policy; all five
  widening candidates REJECTED on measured evidence.**
  Control over 400 real sessions / 2,350 engineering prompts: activation precision **8/8 =
  100 %** (all 8 the correct owner), recall **8/27 = 29.6 %**, false-activation **0/88 = 0 %**,
  labelled population **115 of 1,141** with the 1,026 unlabelled cases named and held outside
  the confusion matrix. Every candidate bought recall at an 85–90 % false-activation rate; two
  were strictly dominated, scoring below doing nothing on recall as well as precision.
  **The bottleneck is no longer the door.** Route rate by prompt length runs 0 % → 99.4 % from
  xs to xl, and 85 % of real Tier ≥ 2 prompts are xl: the DISTINCTIVE-term clause was proven on
  SHORT synthetic proposals and does not discriminate at real length, so the shipped boundary's
  precision is produced by the `create_spec` FILTER, not by the selector. Pinned as the
  characterization `PR-W7-X1`, which is EXPECTED to go red when applicability is repaired.
  Repo-side ceiling, measured before any prompt was read: door open in **63/77 repositories**
  but **73/181 working directories** and **52/109 recently active** — reach is anti-correlated
  with traffic, and all three Power Pack checkouts (where all 40 owners live) are shut.
  Gates: `tools/test_ucr_cif_reach.py` 27/27, `tools/test_ucr_cif_reach_reality.py` 18/18,
  `vault/governance/mutation_plans/ucr_cif_w7.json` **10/10 ALL_CAUGHT** — after two mutants
  SURVIVED the first run and were fixed as real defects in the instrument, one of them my own
  gate reading a persisted artifact instead of driving its producer.

- **W8 · applicability precision** — `0dc2a8f` (spec), `b4f3588` (mechanism + proof),
  `5b1c836` (mutations), `d5a94a6` (audit), `9e85e65` (anchor repair), `41bb2f1` (knowledge).
  **PARTIAL: the saturation moved, the precision did not, and the ceiling is now measured.**
  Two mechanisms in the ONE selector, so both doors inherit them: the applicability bar scales
  with prompt term count (floor 1, ceiling 3) and owners rank by evidence strength — the summed
  inverse-holder weight of DISTINCTIVE matched terms — instead of by unit count.
  On the identical **683 xl cases** of a paired re-derivation: routing ≥1 owner **99.6 % →
  93.9 %**, mean owners **4.76 → 3.98**, owner slots **−20.3 %**, `cdicf` −56 %, `sqi` −30 %,
  and **zero true positives lost** (TP 12 → 12, recall 100 %). Holdout precision **20.0 % →
  20.0 %**: of 128 shared labelled cases exactly **one** changed its fire decision, ~0.8 points
  against 31 positives, below this oracle's resolution. **The headline acceptance criterion
  FAILED and is recorded as failed**, not softened.
  **The finding that reorders the frontier:** sweeping the ceiling cliffs 42 % → 5 % routed
  between a bar of 3 and 4, and the corpus's distinctive supply is median 3 with only 404 of
  996 units holding 4. Headroom above the shipped setting is **zero**, and that is a property
  of the EVIDENCE FAMILY, not of the threshold — so applicability precision is unreachable by
  tightening a lexical clause at all.
  Two instrument findings came BEFORE the subject: `ucr_cif_shadow.py` replays a persisted
  report and never calls `select_for` (W7's one-line success criterion was unfalsifiable in the
  wrong direction), and W7's stored 23.5 %/2,350 re-derived TODAY unchanged as 20.0 %/2,306 —
  population drift worth 3.5 points. Both are now UKDL rules.
  Gates: `tools/test_w8_applicability_precision.py` **17/17** (each mechanism independently
  discriminative, with the positive control that short thin evidence still routes),
  `ucr_cif_w8.json` **6/6 ALL_CAUGHT**, and the whole family re-verified — W4 14/14, W5 23/23,
  W7 10/10 = **53 mutations**, restore checked at source and runtime. `DISTINCTIVE_MAX_HOLDERS`
  untouched; `PR-W7-X1` still GREEN at 93.9 % and deliberately NOT inverted.

- **W9 · structural ownership evidence** — `3a46817` (spec), `5ae9784`
  (projection), `7755063` (fusion), `4f7e63a` (gates + mutations + anchor
  repair), `2856a3f` (measurement + verdict), `<knowledge>`.
  **BUILT, MEASURED, NOT PROMOTED — and that is the result, not a failure to
  finish.** Full account: `vault/audits/ucr_cif/07_W9_STRUCTURAL.md`.
  **The obvious family was rejected before it was built.** "Does the owner
  structurally hold this unit's terms" measures **996/996 = 100.0 %** — a
  PROJECTION of W3's adjudication, which promotes on exactly that predicate.
  Constant over the admitted population, zero discrimination; the rejected
  population sits at 14.9 %. The granularity that survives is the TERM,
  because a prompt matches a subset the adjudication never saw: **21.0 %** of
  (unit, term) pairs, **18.0 %** of the corpus-distinctive ones, so the two
  channels disagree on 82 % of what the selector ranks by.
  `modules/ucr_cif/structural_projection.py` compiles the 45,525 ms index into
  **674 terms / 65,834 bytes / 0.73 ms**, with a clone-stable binding
  (corpus_id + size; `mtime_ns` recorded, never compared) and four distinct
  degradation states. Two self-inflicted cost defects were found by measuring
  the read path: a 1.9 MB ledger re-parse per selection (**70.8 → 2.71 ms**)
  and an mtime comparison that would have reported every fresh checkout stale.
  **Paired on 2,098 of 2,098 shared cases, zero drift** (keyed on
  `prompt_sha`, control via `UCR_CIF_STRUCTURAL_DISABLE=1`, both arms five
  minutes apart in one session). The mechanism is NOT inert: order changed on
  **78.5 %** of routed selections, top-1 on **59.0 %**, `governance-overlay`
  net **−473** top-1 slots. Fire/no-fire identical **by construction**, as the
  spec said before the run.
  **Against the independent git-behaviour oracle it does not help:** of 30
  labelled cases with the true owner routed, rank improved 6 / worsened 12,
  two-sided **p = 0.238 → UNRESOLVED**. Two measured reasons not to promote
  regardless: prose-form owners are systematically under-credited
  (`governance-overlay` 13.7 % structural, yet credited at 21.1 % of oracle
  hits against a 23.7 % routing share — it is a real owner), and **the
  `MAX_OWNERS` cap turns a reorder into a loss** (two labelled cases lost the
  true owner from index 4). The oracle was checked for volume bias first and
  is not a mirror of routing: `duplicate_to_advantage` is routed 3.4 % and
  credited 21.1 %.
  **Therefore `STRUCTURAL_RANKING_ENABLED = False` and
  `REQUIRE_STRUCTURAL_ATTRIBUTION = False`.** The default order is W8's, byte
  for byte; the evidence is computed, reported and rendered by `--explain` as
  *BUILDS …*, and decides nothing. Re-enable with `UCR_CIF_STRUCTURAL_RANK=1`.
  Gates `tools/test_w9_structural_evidence.py` **29/29**;
  `ucr_cif_w9.json` **7/7**; family re-verified **60 mutations ALL_CAUGHT**
  (W4 14, W5 23, W7 10, W8 6, W9 7). `PR-W7-X1` untouched and green;
  `DISTINCTIVE_MAX_HOLDERS`, `MAX_DISTINCTIVE_REQUIRED`, `create_spec` and the
  corpus all untouched.
  Three instrument failures, all mine, all recorded: W46 survived because the
  stale-ledger case changed the file SIZE and never exercised the `corpus_id`
  channel; W36 survived its own repair because I repointed it at a function
  the shipped path had stopped calling; and the cap fixture first routed
  nothing because four owners sharing one term pushed it past
  `DISTINCTIVE_MAX_HOLDERS`.

**UNMEASURED (not zero, not fine)**

- **Hook/mission latency timing.** Host was at **1,499 MB free of 32,061 (4.7 %)**, 31
  `claude` + 15 `node` processes. A reading under that contention is not a measurement.
  Blocking precondition: re-measure on a host with meaningful headroom before W6 sets any
  regression budget. The structural baseline above stands in the meantime.
  **W5 addendum (host at 6.3 %, so the same caveat):** the label stays UNMEASURED, but W5
  added synchronous work to `UserPromptSubmit` and therefore owes a number. Taken as a
  **paired** delta — the same hook, the same payload, three runs each, routing on vs
  `CLAUDEPP_UCR_ROUTING_DISABLE=1` — the median was **5,212 ms vs 5,067 ms, +145 ms**, and it
  is paid only when the novelty signal fires. The absolute figures are the host's; the delta
  is the measurement. In-process the selection is 58 ms cold (the 1.9 MB parse) and 5–7 ms
  warm, and **0.5 ms when the gate does not apply**, because the store is opened only after
  the trigger fires.
  **W7 addendum (host at 1.1–3.8 % free of 32,061 MB, 41 `claude` + 23 `node` processes, so the
  caveat stands and the label does not move):** in-process and paired, re-measured on the day,
  warm applicable L **12.73 ms**, warm no-match L **12.06 ms**, non-applicable S/M **0.00 ms**,
  marginal **+10.4 ms**. The number W7 actually needed was not latency at all — widening costs
  **zero** extra selector calls, because the gate already computes `routing` on every branch.
  Its whole price is context: **1,052 B per owner-naming signal** (534 advisory + 518
  actionable), measured live in a fresh subprocess, i.e. about **+764 B on every Tier ≥ 2
  prompt** under the widest candidate. Measure the resource the change actually spends.

**Coherence anchor:** `SOURCE_INVENTORY_FULL.json` parses and holds **1,394 records with a
`KIND` on every one** (verified this session — the predecessor's own seal test, re-run, not
trusted). If that fails, the inventory is not sealed and W1's prefix reuse is invalid.

## 3. Active decisions (Owner-authoritative, do not re-ask)

1. **Artifact form = A.** Executable capability; compendium superseded; predecessor preserved
   and extended, never re-authored.
2. **Concurrency = A.** Isolated worktree; never stop, overwrite or roll back the other
   writer; a collision on a shared authority is an *Institutional Concurrent Mutation
   Conflict*, resolved by semantics and provenance, never last-writer-wins.
3. **Enforcement = progressive.** observe → advisory → red-branch proven → false-positive
   challenged → Production-Reality verified → blocking-eligible → blocking. No host-wide
   blocking before a gate's own failure detector is proven. HR-001 respected: repo-owned half
   built and proven, then **one** consolidated, reversible, idempotent registration
   transaction. `SOURCE ≠ REGISTERED ≠ LOADED ≠ EFFECTIVE` — four claims, each measured.
4. **Capture = C with a strong privacy boundary.** Universal observation, **not** universal
   raw-data replication. Semantic-first, minimum-necessary, provenanced, typed. Never
   globalise secrets, raw content, absolute host paths or raw commit subjects.
5. **Gate 25 closes empirically** — a real second mission, chosen from repository evidence
   *after* the runtime exists, with control/treatment and anti-gaming rules.
6. **Scope = host-local.** No VPS, no remote DB, no external credentials. No video exists.

## 4. Next three actions — frontier RECALCULATED 2026-09-22 (W9 close)

**W9 executed W8's action 1 and the answer inverts the priority order.** The
structural family is built, orthogonal and measured; what blocks it is not a
missing evidence family but an oracle that cannot resolve 3 points. **Action 3
of the W8 list is now action 1, and it gates every precision claim this
mission can make.**

1. **HIGHEST LEVERAGE — widen the labelled oracle.** W9 could not resolve its
   own headline: 30 labelled cases with the true owner routed, 18 of which
   changed, giving p = 0.238 on a 6/12 split. One case is 3.3 points. Until
   this moves, **no precision wave can succeed or fail honestly**, and a
   built, working, orthogonal mechanism sits switched off for want of
   measurement rather than for want of engineering. The oracle's domain is
   Power Pack checkouts only (`05_W7_REACH.md` §9); the git-behaviour labeller
   in `modules/ucr_cif/reach_ground_truth.py` is sound and independent — it is
   simply starved. Widen by window, by repository domain, or by a second
   independent labeller. Do NOT pad it with weak guesses: evidence quality
   over sample count, and a labelled case whose provenance is a heuristic is
   worse than no case.
2. **Give prose-form ownership a structural signal.** The measured reason W9
   did not promote is that `governance-overlay` holds 13.7 % of its term-pairs
   structurally because its capability ships as Markdown, and the behavioural
   oracle says it is a real owner at roughly its routing share. A family that
   reads governance rule ids, document headings or front-matter `covers:` keys
   as DECLARATIONS would credit exactly the owners the current signals miss.
   It is untested and it is the cheapest remaining orthogonal axis. Measure
   its supply before choosing any policy, as W9 did.
3. **Separate the cap from the ranking question.** Ranking below
   `MAX_OWNERS` and eviction at the boundary are two effects and the current
   measurement cannot apportion the −6 between them. Re-run the paired
   comparison with the cap raised, or score rank quality on the pre-cap list,
   before concluding anything about the ranking key itself.

**Then, and only then, re-run W9's arms.** The mechanism, the projection, the
gates and the mutation plan are all in place; enabling it is one constant.
Do not rebuild any of it.

**Carried from W8 and still true:** W5-style construction observation +
privacy projection (EXTEND `session_delta` / `omnicapture`, reuse
`modules/ucr_cif/prompt_population.py`) remains unstarted and is unaffected by
W9.

## 4a. Superseded — the W8-close frontier

**W8 executed W7's action 1 and the answer changed what action 2 IS.** Do not open a third
consumption boundary and do not revisit the `create_spec` decision — still measured,
holdout-validated, and recorded with its reopening conditions in
`vault/audits/ucr_cif/05_W7_REACH.md` §9. That condition is **not** met and W8 is evidence it
will not be met by threshold work. Full result: `vault/audits/ucr_cif/06_W8_PRECISION.md`.

**What W8 settled.** The lexical distinctive-term clause is now at its measured ceiling. The
bar scales with prompt length and stops at 3, which is the corpus's own MEDIAN distinctive
supply — only 404 of 996 units hold 4, and the sweep cliffs from 42 % routed to 5 % exactly
there. Raising it further refuses on SUPPLY rather than relevance. On the identical 683 xl
cases of a paired re-derivation, routing fell 99.6 % → **93.9 %**, mean owners 4.76 → **3.98**,
owner slots **−20 %**, with **zero** true positives lost. Holdout precision did **not** move
(20.0 % → 20.0 %): of 128 shared labelled cases exactly **one** changed its fire decision.

1. **HIGHEST LEVERAGE — a STRUCTURAL evidence family. This was action 2, and W8 promoted it
   from a stock task to the only remaining precision lever.** The adjudicator promotes on
   SYMBOL / FILENAME / REGISTRY and abstains when a term is held by more than three owners.
   The families named in the brief and still unbuilt — explicit owner declaration, test
   ownership, command/hook ownership, git history — are **structural, not lexical**, and that
   is now the whole point: a 20,000-character prompt contains three distinctive terms of
   almost any owner by coincidence, and it cannot fabricate a declaration, a test that names
   the owner, or a commit that touched it. None of them is subject to the supply cliff W8
   measured. Expect this to move precision where a threshold could not, and drive the 503
   ABSTAIN down as a side effect rather than as the goal. **Do NOT loosen
   `DISTINCTIVE_MAX_HOLDERS` (3) and do NOT raise `MAX_DISTINCTIVE_REQUIRED` (3)** — both are
   pinned to measured distributions and the second is enforced against the LIVE ledger by
   `V-W8-BAR-NEVER-EXCEEDS-MEASURED-SUPPLY`.
2. **W5-style construction observation + privacy projection.** EXTEND `session_delta` /
   `omnicapture`; all global egress through the `secret_firewall` URB; exactly-once identity so
   a retry or resume cannot duplicate an institutional record. W7 built a privacy-safe local
   derivation pipeline (`modules/ucr_cif/prompt_population.py`) that reads real prompts,
   classifies and discards them — reuse it rather than re-deriving the boundary.
3. **Widen the labelled oracle before trusting another precision claim.** W8's headline could
   not be resolved because the labelled population is 128 shared cases with 31 positives, so
   one case is ~0.8 points and anything under ~3 points is below resolution. Any future
   precision wave inherits that blindness. The oracle's domain is Power Pack checkouts only;
   `05_W7_REACH.md` §9 already names widening it as a reopening condition in its own right.

**Two things W8 measured that the next wave should not re-derive.** (a) `tools/ucr_cif_shadow.py`
REPLAYS a persisted control report and never calls `select_for`, so it cannot see a selector
change; the re-derivation step (`tools/ucr_cif_reach.py --funnel`) is part of the success
criterion, not an optional preamble. (b) The funnel's population rolls between runs — W7's
stored 23.5 %/2,350 re-derived as 20.0 %/2,306 with nothing changed — so a stored baseline from
another session is not a control, and paired runs must be compared on their shared cases.

**`PR-W7-X1-SELECTOR-SATURATION-ON-LONG-PROMPTS` STAYS GREEN and must NOT be inverted.** It
asserts `rate > 0.90`; the rate is 93.9 %. It was to be inverted WHEN it went red. It did not,
and inverting a characterization that has not turned destroys the evidence of a live defect.

**Two things W7 measured that the next wave should not re-derive.** (a) A THIRD suppressed
action nobody had named: DFP's `knowledge_first_required` pre-empts the spec question on 143 of
1,243 Tier ≥ 2 prompts and discards its owners too. (b) The six historical manual ownership
sweeps belong to the FIRST door's population (mega-system proposals → the novelty gate, closed
by W5), so widening the second door would not have retired any of them. No human-rediscovery
saving beyond the measured 27 labelled-relevant prompts, of which 8 already receive the owner.

**Superseded, kept because the reasoning still holds and only its action is done:**

---

## 4b. Superseded — the W6-close frontier

**W6 closed the action that stood here.** There are now TWO proven consumption boundaries, and
each is independently observable. Ordinary L/XL engineering work — a prompt that never says
"fabric", "kernel" or "operating system" — reaches the same 996 authoritative dispositions
through the SDD-OS spec boundary, and the agent is told to inspect the named owners before
writing a spec that creates something new.

Commits: `226ef90` (W5 provenance drill repaired), `aace845` (the edge), `7634043` (six
directed mutations + the isolation proof), `dbaa690` (anchor rot), `77b5169` (UKDL).

**Three handoff premises were false and are recorded so they are not re-inherited.**
(a) `spec-injected ... 8979 B` is the JIT injecting the BODY of an existing spec file;
`check_spec_gate` appears nowhere in `jit_skill_loader.py`. (b) The JIT's One-Shot injector
calls `compile_contract(prompt[:300], "L")` with **no cwd**, and the compiler consults the gate
only when a cwd is given — that path never reaches the gate at all. (c) `sdd_tier` DOES reach
it, with the full prompt and a real cwd, and threw `message` away. So the live chain is
`jit_skill_loader → proactive_dispatcher → sdd_tier → check_spec_gate`, and the material effect
had to land on the ProactiveSignal, not on the gate's prose. A tripwire
(`V-W6-ONESHOT-IS-NOT-THE-BOUNDARY`) goes red if the One-Shot call site ever starts passing cwd.

**Measured at the new boundary.** Warm applicable L 10–40 ms; warm no-match L 10–23 ms;
non-applicable S/M 0.00 ms (it returns before the corpus is consulted). Marginal cost to the
live consumer +7.9 to +17.2 ms, paired, same process. Exactly ONE selector call per boundary
per UserPromptSubmit, both served from one per-process ledger parse (107.9 ms cold).
Bounded materialization holds: every corpus term at once yields 5 owners / 1851 bytes.
**Absolute hook wall-clock on this host is not reportable** — a single arm moved 3110 → 11803 ms
between runs at 2–4% free memory; that gate was replaced by a count plus an in-process median.

**Gate 25 is NOT satisfied by W6.** W6 is implementation of UCR-CIF, not an independent mission.

Superseded — kept because the reasoning still holds, only its action is done:
`modules/spec_gate/gate.py::check_novelty_gate`, reached live from
`tools/jit_skill_loader.py` on `UserPromptSubmit`. When a proposal matches, question 4 of the
novelty proof — *"Why is extending an existing owner insufficient?"* — is replaced in place by
the named owners, their unit counts and their uids. Severing that one call turns the suite red
with both endpoints intact (`W1-consumer-edge-severed`), which is the only evidence that
distinguishes a consumer from a reader.

Measured coverage, stated as a vector rather than a score: **934 of 996 (94%) authoritative
units are routable** — their owner can be reached by some proposal — across **30 of 40**
owners. The 62 that cannot: 53 carry no distinctive evidence term (every term they hold is
shared by more than three owners, so no term says *which* owner), and 9 belong to an owner
with only one eligible unit. **One semantic class is present and one is supported**, so there
is no unsupported class and no fake mapping; the other eleven members of the closed
disposition set are declared and empty.

The bottleneck moved to the TRIGGER, not the corpus. 934 units are routable in principle and
the only door is a gate that fires on *"fabric / kernel / operating system / compendium"* or
an enumerated dataset catalog. Ordinary L/XL work — where "this is already owned by
modules/X" would prevent the most duplicated effort — never reaches it.

1. **DONE (W6).** Open the second consumption boundary: the L/XL spec gate. Closed as above.
   The one thing to carry forward is the shape of the miss: the boundary was named correctly
   and every piece of EVIDENCE offered for it was wrong, so the route was re-measured rather
   than inherited. Do that again for boundary three.

   **NEW HIGHEST LEVERAGE — measure the second door's real reach before adding a third.**
   W6 proved the edge works; it did NOT measure how often it fires in practice, and there is a
   specific reason to doubt the optimistic reading. `sdd_tier` returns None unless
   `action == "create_spec"`, i.e. unless the repo has NO spec — and `SPEC_GLOBS` includes
   `vault/specs/*.md` and `vault/plans/*.md`, so in THIS repo a spec is almost always found and
   the second door stays shut. The door is widest in a fresh project and narrowest at home,
   which is the opposite of where it was measured. Count, over real prompts: how many reach
   Tier ≥ 2, how many of those hit `create_spec`, how many route ≥ 1 owner, and how many route
   falsely. Do not widen `sdd_tier`'s trigger to raise the number — that trades precision for
   reach and the negative pole is the expensive one to lose. A correct zero beats a generic
   routing.
2. **Drive the 503 ABSTAIN down with a second evidence family.** The structural adjudicator
   promotes on SYMBOL / FILENAME / REGISTRY and abstains when a term is held by more than 3
   owners. Families named in the brief and NOT yet built: explicit owner declaration, test
   ownership, command/hook ownership, git history. Each is structural, none lexical. Do
   **not** loosen `DISTINCTIVE_MAX_HOLDERS` to raise coverage — the number came from the
   measured distribution (median 3 of held terms), and loosening it buys coverage with false
   certainty.
3. **W5 — construction observation + privacy projection.** EXTEND `session_delta` /
   `omnicapture`; all global egress through the `secret_firewall` URB. Exactly-once identity
   so a retry or resume cannot duplicate an institutional record. Red-branch fixtures:
   planted secret, prompt injection from a repo file, poisoned evidence.

**Do not mistake reach for coverage.** "934 routable" means a proposal EXISTS that would route
them, not that any given mission sees them. The number that matters is still the one W5 moved
off zero: authoritative dispositions with a proven material consumer. Raising 996 toward 1,499
before the second boundary exists repeats the mistake W5 was called to fix, one level out.

**Carried, not forgotten.** (a) `spec_depth_selection` stays UNKNOWN as a named EVIDENCE
FRONTIER — 99 incident records of 200 — and **the UNKNOWN→withdrawn tightening must not be
executed while it stands**; it resolves when the estate's incident record grows, not by code.
(b) The identity fix is committed here and **NOT SHIPPED**: the live installed copy at
`~/.claude/skills/claude-power-pack` still carries the old substring test and has no
`main_repo_root`, so the Stop-time FIOS advisory the Owner sees is a stale deployment. That
tree is the other writer's live checkout — Concurrency=A forbids writing it and HR-001
forbids writing under `~/.claude/` regardless. **Owner-side step:** merge
`ucr-cif/construction` into `main` (or mirror `modules/repo_identity/` and
`modules/fable_distillation/federated_ledger.py`) and the warning stops at the next Stop.

## 5. Start instruction

Work only in `C:\Users\User\Apps\pp-ucr-cif`. Read `vault/audits/ucr_cif/01_REALITY_SCAN.md`
§5 (prior-art base rates: CPP-IAS 150→14, DAIF 22→8, RE Baseline 4→1) and all eight entries
of `03_MISSION_TRAPS.md` before proposing any construction — **the correct prior is that most
named systems are already owned at equal or greater maturity**, and `HR-NOVELTY-001` requires
a 13-question proof against a *discovered* sweep before any new institutional system is
admitted. Then execute action 1.

Ask the corpus what it already owns before proposing anything — that is now a command, not a
sweep somebody has to remember to run:

    python -m modules.ucr_cif.disposition_consumer --explain "<your proposal>"

Re-run this session's evidence before trusting any of it. Four plans, all re-verified at
W8 close on 2026-09-22:

    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w4.json
    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w5.json
    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w7.json
    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w8.json
    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w9.json

14/14, **23/23** (the W5 plan absorbed W6's six as `W18`..`W23`; the filename is historical),
**10/10**, **6/6** and **7/7** — 60 directed mutations, every restore verified at source AND
runtime.
A HARNESS-FAILED line means an anchor has rotted against the source, which is a stale plan and
never a verdict about the suites. **W8 rotted one and the repair is the lesson**: re-pointing
an anchor at whichever new line LOOKS like the old one produced a mutant that changed nothing
and would have SURVIVED as a false green. When the source changes shape, restore the FALSE
WORLD, not the string.

Suites, all green at W9 close: selection 22/22, consumption 19/19 (+PR 7/7), spec boundary
22/22, reach 27/27, W8 applicability 17/17, adversarial 18/18, **W9 structural 29/29**.

**W9 added a THIRD anchor-rot lesson, and it is the subtle one.** Restoring the false world
rather than the string is necessary and NOT sufficient: once a refactor splits a path into a
shipped branch and an alternative, the anchor must follow **the branch that actually runs
under the default configuration**. W9 repaired W8's `W36` onto `_rank_key` and then defaulted
structural ranking OFF, so the mutant edited a function `select_for` no longer calls and
SURVIVED behind a diff that looked perfectly correct. It is caught on `_rank_key_lexical`.

**The structural projection is a build artifact with a rebuild command.** If `--verify`
reports `source_fresh False`, the repository moved since it was compiled:

    python -m modules.ucr_cif.structural_projection --verify
    python -m modules.ucr_cif.structural_projection --build

Staleness is SAFE while ranking is off, because nothing consults the projection for a
decision. That stops being true the moment `STRUCTURAL_RANKING_ENABLED` or
`REQUIRE_STRUCTURAL_ATTRIBUTION` is switched on, and the module's docstring says so.

Ask how often the corpus actually reaches a decision, and what it would cost to make it reach
more. **The order below is the measurement protocol, not a menu** — step 2 alone cannot see a
selector change, because it replays step 1's output rather than calling the selector:

    python tools/ucr_cif_reach.py --funnel --sessions 400 --out <somewhere>.json
    python tools/ucr_cif_shadow.py --report <somewhere>.json

The first replays real `UserPromptSubmit` history through the live chain
(`sdd_tier -> check_spec_gate -> select_for`) and persists derived cases only — no prompt
text, no host paths. It takes roughly ten minutes and is CPU-bound. The second scores six
activation policies on a session-split holdout **of that file**.

**To measure a change to the selector you must re-derive BOTH halves and compare on their
SHARED cases.** The population rolls between runs: W7's stored 23.5 % over 2,350 cases
re-derived at W8 as 20.0 % over 2,306 with nothing modified, and two runs twenty minutes apart
shared only 1,792 cases. A stored figure from an earlier session is not a control, and the
labelled subset is ~128 cases with ~31 positives, so anything under ~3 points is below
resolution.

**The activation decision is still KEEP; read `vault/audits/ucr_cif/05_W7_REACH.md` §9 before
proposing to widen anything, and `06_W8_PRECISION.md` §6 before proposing to tighten anything.**
