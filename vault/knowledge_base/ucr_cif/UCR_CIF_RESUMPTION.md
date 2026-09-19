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

**UNMEASURED (not zero, not fine)**

- **Hook/mission latency timing.** Host was at **1,499 MB free of 32,061 (4.7 %)**, 31
  `claude` + 15 `node` processes. A reading under that contention is not a measurement.
  Blocking precondition: re-measure on a host with meaningful headroom before W6 sets any
  regression budget. The structural baseline above stands in the meantime.

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

## 4. Next three actions

1. **Pay the probe debt, and shrink the UNKNOWN ratchet.** Four capabilities are UNKNOWN:
   `cdicf-installer` and `spec_depth_selection` are **probe debt this repository can pay**
   (write a deterministic probe in `capability_runtime/retirement.py::PROBES`);
   `cost_routing` and `premise_verification` are EXTERNAL and may never be probeable, so they
   need an Owner classification instead, not a probe. Then
   `tools/capability_lifecycle_migrate.py --apply` and delete the resolved ids from
   `vault/capability_runtime/lifecycle_ratchet.json`. Paying `cdicf-installer` also closes
   the pre-existing `V-UCEIMR-G2-COVERAGE` failure, which has the same root cause.
   **Highest leverage**: at UNKNOWN=0, tightening UNKNOWN into WITHDRAWN is a one-line
   change with no population left to break, and the lifecycle becomes fully fail-closed.
2. **Drive the 503 ABSTAIN down with a second evidence family.** The structural adjudicator
   promotes on SYMBOL / FILENAME / REGISTRY and abstains when a term is held by more than 3
   owners. The families named in the brief and NOT yet built are: explicit owner
   declaration, test ownership, command/hook ownership, and git history. Each is structural
   and none is lexical. Do **not** loosen `DISTINCTIVE_MAX_HOLDERS` to raise coverage — that
   is coverage bought by forcing false certainty, and the number was derived from the
   measured distribution (median 3 of held terms).
3. **W4 — construction observation + privacy projection.** EXTEND `session_delta` /
   `omnicapture`; all global egress through the `secret_firewall` URB. Exactly-once identity
   so a retry or resume cannot duplicate an institutional record. Red-branch fixtures:
   planted secret, prompt injection from a repo file, poisoned evidence.

## 5. Start instruction

Work only in `C:\Users\User\Apps\pp-ucr-cif`. Read `vault/audits/ucr_cif/01_REALITY_SCAN.md`
§5 (prior-art base rates: CPP-IAS 150→14, DAIF 22→8, RE Baseline 4→1) and all eight entries
of `03_MISSION_TRAPS.md` before proposing any construction — **the correct prior is that most
named systems are already owned at equal or greater maturity**, and `HR-NOVELTY-001` requires
a 13-question proof against a *discovered* sweep before any new institutional system is
admitted. Then execute action 1.
