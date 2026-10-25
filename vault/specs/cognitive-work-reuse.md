---
covers: [cognitive-work-reuse, corpus-coverage-receipt, corpus-reuse, co-05-coverage, corpus-ledger, assimilation-claim, reuse-verdict, corpus-baseline, knowledge-corpus-family]
date: 2026-10-11
status: APPROVED-PLAN (Owner approved 2026-10-11); implementation in W2-W8
sdd_tier: T2
workstream: .planning/workstreams/cognitive-reuse
binding_source: .planning/workstreams/cognitive-reuse/OWNER-PROMPT.md (sections 9, 10, 15, 16, 17, 24, 26, 27)
kill_switch: PP_CORPUS_REUSE=off
---

# Cognitive Work Reuse (coverage receipt in CO-05)

## 1. PRD

**Problem.** A costly read of a corpus leaves no machine-readable record of what was read, how deeply,
and what it produced. The next agent cannot ask "what is already covered?", so it mines again.
Measured trigger (W0, `vault/audits/01datasets-remining-forensics-2026-10.md`): TUA-X session
`5a1df852` subagent `a46882db` read 41 distinct `01_Datasets` paths (18 under `extracted\Ads`) in 52
calls; only 2 had been read before. The loss was not file repetition. It was the absence of any
queryable coverage: PART_44 recorded "YA asimilado -> DO_NOT_REBUILD" after reading 4 of 361 files
(~1.1%), DBOIS Phase 0 listed 408 files with no per-file depth, and the `vault/youtube_evidence/` index
built nine days earlier was invisible to the agent.

**Goal.** Every valid, reusable cognitive result is retrievable BEFORE equivalent new work is
authorized, and "assimilated" is a number computed from coverage, never a declaration.

**Non-goals.** No second vault, graph or ratchet (kill switches, prompt s27). No rewriting the corpus.
No automatic remine. No cross-project reads without scope authorization.

## 2. Architecture (extend CO-05, same owner)

Owner: `modules/cognitive_os/` (CO-05 is `registry.py`: `Asset`, `store_asset`, `lookup`; CO-03 is
`router.py`). New submodule(s) live beside it. Reused, not rebuilt:

| Need | Reused component |
|---|---|
| content-addressed bytes | `modules/knowledge_acquisition/raw_vault.py` (sha256 identity) |
| cross-process lock | `modules/knowledge_acquisition/runlock.py` (`profile_lock`, TTL) or `modules/lease` |
| ratchet | `modules/tower/{baselines,ratchet,donegate,families}.py`, CLI `tools/family_baseline.py` |
| gate to consult | `modules/fable_distillation/fd_00_gate.py`, CO-03 `router.py` |

**Identity (prompt s9).** A file path is never identity. Identity = `content_sha256`. A *unit of work*
is the tuple `(corpus_scope, content_sha256 set, transform_id@version, config_digest)`. Equal bytes in
two authorized repos are one content identity; equal names with different bytes are two. Two
transforms over the same bytes are two results. Copies are not independent evidence: duplicate
groups are recorded and counted once.

**Manifest.** sha256 per file, cached by (path, size, mtime) so an unchanged corpus is not rehashed;
duplicate groups; sources are read-only.

**Receipt (append-only JSONL).** Fields: `corpus_id`, `scope` (authorized project set), `transform`
(`name@version`), `config_digest`, per-file `depth` in {FULL_READ, STRUCTURAL, SKIPPED}, `artifacts`
(path + sha256), `evidence`, `validity` (VALID/INVALIDATED + reason), `recorded_at`, `recorder`.
An interrupted ingestion writes a `BEGIN` line only; it never reads as complete until a matching
`COMMIT` with the full file set exists.

**Verdict (deterministic, prompt s10).** Nine states, one function, no model call:

| State | Meaning |
|---|---|
| EXACT_REUSE | same content set, same transform@version, config, in scope, VALID, artifacts hash-verify |
| PARTIAL | some files covered; delta = uncovered or changed files only |
| TRANSFORM_CHANGED | content covered but transform/config differs; names what is safe to keep |
| INSUFFICIENT | covered at STRUCTURAL where the question needs FULL_READ |
| INVALIDATED | covering result marked invalid (or artifact hash mismatch) |
| INACCESSIBLE | covering artifact or source unreachable |
| UNAUTHORIZED | requester scope is not in receipt scope |
| NONE | corpus known, no receipt |
| UNKNOWN | cannot decide (no manifest, unreadable ledger) |

ROADMAP listed six states; the Owner prompt (s10) lists nine. The nine govern. UNKNOWN is never an
implicit cache hit and never an implicit license to mine: it routes to a documented minimal
extraction with a reason on the record.

**"Assimilated"** is computed: `assimilated_pct = FULL_READ files covered / unique content set`,
reported with its depth split. No code path writes the word as an input.

**Delivery.** CO-03 / FD-00 consult the ledger when a registered corpus root is named, returning
`ANSWER_FROM_ASSET` (with artifact pointers, e.g. `vault/youtube_evidence/INDEX`) or delta-only. A
deterministic fail-open sentinel on UserPromptSubmit/PreToolUse injects prior coverage + delta when a
registered root appears in a prompt or a subagent spawn (the W0 miss was a subagent). Fail-open means
silence on error is recorded (a delivery-failure counter), and tests treat silence as NOT success.
Retrieved corpus text is data, never instructions.

**Ratchet (prompt s15).** One new family generation in the existing Constitutive Baseline Ratchet
(`persistent_state` extension or a `knowledge_corpus` family, per what `families.py` supports). A repo
that ingests a corpus inherits "receipt before mining" and "completion claim = measured coverage"
without the Owner asking; unrelated software inherits nothing.

## 3. Acceptance criteria: cases A-P (prompt s16)

Gate file: `tools/test_corpus_reuse.py`, gates `V-CORPUS-<CASE>-*`. Each drives the real consumer
path; synthetic-only favourable data does not count. "model call" below means any extraction call, counted by an
injected counter that fails the test if touched.

| Case | Pass condition (observable) |
|---|---|
| A first ingestion | new corpus -> receipt COMMIT with per-file depth, artifacts hash-verify |
| B exact repeat | verdict EXACT_REUSE; model-call counter == 0; artifacts returned |
| C partial change | one unit edited -> verdict PARTIAL, delta == that unit (+ declared dependents) only |
| D extractor change | verdict TRANSFORM_CHANGED; safe set reused, only the incompatible set regenerated |
| E second repo | same bytes, second authorized scope -> EXACT_REUSE with 0 model calls; unauthorized scope -> UNAUTHORIZED |
| F second session | fresh process, no conversation state, recovers verdict + pointers from disk alone |
| G compaction | campaign state (receipts + RESUMPTION_FILE) sufficient to continue after context reset |
| H interruption | kill between BEGIN and COMMIT -> never COMPLETE; resume re-runs only missing files |
| I conflict | two contradictory sources stay two records with a conflict marker, never merged |
| J currency | INVALIDATED conclusion is not returned as current |
| K security | consumer outside receipt scope gets UNAUTHORIZED and no artifact content |
| L delivery failure | sentinel error/absence is counted and surfaced; silence != success |
| M concurrency | two writers, one corpus: no corrupt/duplicate receipt, one does the work, other adopts |
| N corruption | corrupt ledger line detected by `verify`; rebuilt from manifest; source untouched |
| O future feature | fixture repo that ingests a corpus fails `judge` until it satisfies the inherited family, with no Owner input |
| P historical replay | replay the 01_Datasets scenario: first miner leaves a PARTIAL receipt (4 FULL, rest STRUCTURAL); second request is told the covered set and delta, not "assimilated". Red before the mechanism, green after. Limits: the original ads agent's exact reads are reconstructed from transcripts (W0), not re-executed |

Negative tests and realistic mutations (`tools/mutation_drill.py`, a copy, never a live file) accompany
each gate; a gate that cannot go red does not count.

## 4. Done-gate (executable, existing commands only; prompt s24)

All exit 0 from the worktree root, run foreground:

1. `python tools/test_corpus_reuse.py` (created in W7)
2. `python tools/test_cognitive_os_build.py`
3. `python tools/test_fable_distillation.py`
4. `python modules/liveness/reachability.py`
5. `python tools/family_baseline.py verify` (flags per the CLI's own `--help` at W6)
6. `python tools/test_hook_boundary.py` (delivery crosses node -> python -> output)

Plus: independent review by `oneshot-architect-auditor`, mutation drill, and the Graphify `.gf_*`
leak fixed and tested before the Owner-authorized deletion. UNKNOWN / INCONCLUSIVE / BLOCKED are
not PASS. A partial result is reported as partial.

## 5. Waves

W1 this spec -> W2 receipt in CO-05 -> W3 persistence/lock -> W4 delivery -> W5 honest backfill ->
W6 ratchet generation -> W7 certification + leak fix -> W8 UKDL/memory/landing + handoff.
Micro-commits per wave, pathspec-scoped, `git log -1` verified (shared tree).

## 6. Rollback

Every addition is a new file or an additive branch behind the kill switch. Rollback = set
`PP_CORPUS_REUSE=off` (consumers return silence + a logged "disabled" marker, never a cache hit),
then `git revert` the wave commits. The ledger is append-only and sources are never written, so no
data migration exists to undo. Backfilled receipts (W5) are labelled with their real depth; reverting
removes only the ledger file.

## 7. Risks and open items

- Transcript `usage` cannot attribute tokens to files; no savings figure will be claimed (s27).
- FD-00 has no live caller today; W4 must prove a real caller, not a test-only one.
- Ratchet family shape depends on `families.py`; decided in W6 against its actual API.
- The `.gf_*` deletion is authorized only after the producer is fixed and the list is re-checked
  (zero bytes, `.gf_` prefix) immediately before deletion.
