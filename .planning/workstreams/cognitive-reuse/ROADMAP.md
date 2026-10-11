# Roadmap — cognitive-reuse (v1)

Read `REQUIREMENTS.md` first: it holds the Phase Zero facts and the Owner's answers.
Each phase ends with: tests run (foreground), pathspec-scoped micro-commit(s) in the worktree,
`STATE.md` + `RESUMPTION_FILE.md` updated. UNKNOWN / INCONCLUSIVE are never PASS.

## Phase 0 — W0 Forensic quantification
- Locate the TUA-X "ads" agent that re-mined 01_Datasets (Owner answer). Sweep TUA-X project
  transcripts (`~/.claude/projects/C--Users-User-Desktop-Cursor-Projects-TUA-X*` and
  `C--Users-User-Apps--wt-*`) for tool calls whose input path contains `01_Datasets`
  (Read file_path, PowerShell/Bash Get-Content/cat), weight `extracted\Ads`. Bounded script in
  scratch, foreground, hard timeout; output a per-session table: session, dates, distinct corpus
  files read, files also read by an earlier session, model tokens (sum of `usage` fields).
- Decide per re-read: legitimate (new files / new question / prior work unreachable) vs redundant.
- Write `vault/audits/01datasets-remining-forensics-2026-10.md` with the measured numbers and
  the commands that produced them. No estimated savings.
- Acceptance: the ads session(s) identified by id, or the search space and why it was not found.

## Phase 1 — W1 Spec (SDD-OS T2)
- `vault/specs/cognitive-work-reuse.md` with `covers:` front matter: PRD, architecture (CO-05
  extension), acceptance criteria for cases A-P (prompt §16), rollback, kill switch env var.

## Phase 2 — W2 Coverage receipt in CO-05
- Extend `modules/cognitive_os/` (new submodule allowed, same owner): content manifest
  (sha256 per file, cached by path+size+mtime, duplicate groups), append-only receipt
  (corpus_id, transform@version, per-file depth FULL_READ/STRUCTURAL/SKIPPED, artifacts + hashes,
  evidence, scope), deterministic verdict EXACT_REUSE/PARTIAL/TRANSFORM_CHANGED/NONE/UNKNOWN/INACCESSIBLE,
  "assimilated" computed from coverage, never declared. CLI for record/plan/status/verify.

## Phase 3 — W3 Persistence
- Cross-process lock (reuse an existing lock: `modules/knowledge_acquisition/runlock.py` or
  `modules/lease`), atomic writes, interrupted record never reads as complete, corrupt-line
  detection + `verify`; sources never touched.

## Phase 4 — W4 Delivery (reachability)
- CO-03 router / FD-00 consult the ledger (corpus named in task -> ANSWER_FROM_ASSET with artifact
  pointers, or delta-only). Deterministic fail-open sentinel on UserPromptSubmit/PreToolUse when a
  registered corpus root is named: inject prior coverage + delta. Scope check prevents
  cross-project leak. Prove the hook path end-to-end (node -> python -> output), not in-process only.

## Phase 5 — W5 Honest backfill of 01_Datasets
- Receipts from real artifacts: PART_44 (4 FULL, rest STRUCTURAL), DBOIS Phase 0 (408 classified,
  STRUCTURAL; FULL only where cited), the W0 ads session. Correct TUA-X memory if it still
  overclaims.

## Phase 6 — W6 Constitutive Baseline Ratchet
- New generation via `tools/family_baseline.py` (extend `persistent_state` or add a
  `knowledge_corpus` family per what `modules/tower/families.py` supports): ingestion => receipt;
  completion claim = measured coverage. Prove with `judge` on a fixture repo (inherits without Owner).

## Phase 7 — W7 Certification + side fix
- `tools/test_corpus_reuse.py` (V-CORPUS-* gates, cases A-P, P = historical replay red-before/green-after),
  mutation drill (`tools/mutation_drill.py`), `oneshot-architect-auditor` review, `/liveness`.
- Graphify leak: find the producer of zero-byte `.gf_*`, fix it, test it, THEN delete (authorized).

## Phase 8 — W8 Institutional closure
- UKDL: one TRAP (assimilation claim without coverage) + one PROCESS rule (receipt before mining),
  no duplicates. PP memory entry. Land the branch into the live checkout. Done-gate:
  test_corpus_reuse, test_cognitive_os_build, test_fable_distillation, liveness reachability,
  family_baseline verify — all exit 0. Final OWNER SUMMARY + ENGINEERING HANDOFF (prompt §26).
</content>
</invoke>
