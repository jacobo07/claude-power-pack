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

1. **W3 — capability authority + baseline lifecycle.** `vault/baseline_ledger.jsonl` (73
   rows) has fields `iso_ts / ledger_id / law / evidence / session_id / trigger / scope /
   schema_version` and **no status field**, so §XXXI revocation
   (ACTIVE/SUPERSEDED/DEPRECATED/SUSPENDED/REVOKED) has no representation today. That is a
   proven gap on an existing authority → **EXTEND, never a new registry.** Absence must
   read as the safest state, never as ACTIVE. Production Reality: a real mission start
   compiles a baseline, and a revoked capability is provably not inherited.
2. **Review pass over the 218 UNRESOLVED + the top-bias proposals.** Turn
   `proposed_disposition` into `disposition` where evidence supports it. Do **not** let a
   vocabulary-volume winner (`governance-overlay`, an agent `.md`) stand as an owner. A
   capability-level sweep under any name is mandatory before any `IMPLEMENT` verdict
   (`T-VOCABULARY-ZERO-IS-NOT-ABSENCE-002`), and `HR-NOVELTY-001`'s 13-question proof is
   required before admitting any new institutional system.
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
