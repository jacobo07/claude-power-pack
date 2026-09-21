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
**As of 2026-09-19 `origin/main` has advanced to `06d88cd`, 33 commits past that base**
(the other writer landing work). Our seven W0–W2 commits plus W3's three remain ancestors of
HEAD; nothing was rebased. Re-measure the divergence before any merge, and note that
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

## 4. Next three actions — frontier RECALCULATED 2026-09-21 (W7 close)

**W7 answered the question W6 left open and the frontier moved off the trigger.** Do not open a
third consumption boundary and do not revisit the `create_spec` decision without new evidence —
it is measured, holdout-validated and recorded with its reopening conditions in
`vault/audits/ucr_cif/05_W7_REACH.md` §9.

1. **HIGHEST LEVERAGE — applicability precision at real prompt length.** The selector routes at
   least one owner on **99.4 %** of long real prompts (mean 4.74 of a cap of 5), and the three
   most-routed owners are the three largest by unit count — W3's measured vocabulary-volume
   bias (`spearman = +0.756`) surviving where the DISTINCTIVE clause was never tested. This is
   the reason no widening is affordable: the door is currently doing the selector's job, so
   every extra door multiplies noise rather than value. **Do NOT loosen
   `DISTINCTIVE_MAX_HOLDERS`** — the defect is the opposite, the clause is too weak at length.
   Candidate mechanisms, none yet built: require distinctiveness proportional to input length;
   rank and cap by evidence strength rather than accepting the first five; require a term to be
   distinctive *and* topically central rather than merely present. Success is measurable
   directly: re-run `tools/ucr_cif_shadow.py` and watch `P1-ANY-OWNER`'s holdout precision. It
   is 23.5 % today; the widening decision reopens exactly when it stops collapsing.
   `PR-W7-X1-SELECTOR-SATURATION-ON-LONG-PROMPTS` is the characterization to INVERT IN PLACE
   when this lands — never delete it.
2. **Drive the 503 ABSTAIN down with a second evidence family.** Unchanged from W6, and now
   second rather than first: the structural adjudicator promotes on SYMBOL / FILENAME /
   REGISTRY. Families named in the brief and not built: explicit owner declaration, test
   ownership, command/hook ownership, git history. Each structural, none lexical.
3. **W5-style construction observation + privacy projection.** EXTEND `session_delta` /
   `omnicapture`; all global egress through the `secret_firewall` URB; exactly-once identity so
   a retry or resume cannot duplicate an institutional record. W7 built a privacy-safe local
   derivation pipeline (`modules/ucr_cif/prompt_population.py`) that reads real prompts,
   classifies and discards them — reuse it rather than re-deriving the boundary.

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

Re-run this session's evidence before trusting any of it. Three plans, all re-verified at
W7 close on 2026-09-21:

    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w4.json
    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w5.json
    python tools/mutation_probe.py --plan vault/governance/mutation_plans/ucr_cif_w7.json

14/14, **23/23** (the W5 plan absorbed W6's six as `W18`..`W23`; the filename is historical)
and **10/10**. A HARNESS-FAILED line means an anchor has rotted against the source, which is a
stale plan and never a verdict about the suites.

Ask how often the corpus actually reaches a decision, and what it would cost to make it reach
more — both are now commands rather than arguments:

    python tools/ucr_cif_reach.py --ceiling --funnel --sessions 400
    python tools/ucr_cif_shadow.py

The first replays real `UserPromptSubmit` history through the live chain and persists derived
cases only — no prompt text, no host paths. The second scores six activation policies on a
session-split holdout. **The decision they produced is KEEP; read
`vault/audits/ucr_cif/05_W7_REACH.md` §9 before proposing to widen anything.**
