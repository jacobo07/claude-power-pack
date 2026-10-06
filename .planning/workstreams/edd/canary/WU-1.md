# WU-1 -- EDD Phase 1 as a compiled work unit (canary)

Spec: `vault/specs/edd-compiled-execution-canary.md` (laptop PP) -- this packet is its WU-1b.
You are a fresh worker with no parent transcript. This file is your whole scope, budget and done-gate.
Do NOT run GSD commands, do NOT spawn agents, do NOT re-scan the repository broadly.

## Where
Work tree: `/home/kobii/missions/edd/.claude/worktrees/edd-run` (branch `mission/edd-run`). `cd` there first.
All paths below are relative to it. Commit by explicit pathspec only. Never push. Never touch the live install.

## Inputs (read in this order; nothing else unless a row needs it)
1. `.planning/workstreams/edd/canary/dossier/dossier.md` -- compiled with zero model calls: 81 concepts (the
   section titles of the mission prompt, ids C-01..C-81), the 31 `modules/gsd_x` modules with their public defs and
   importers, and up to 6 candidate owner files per concept with the first matching line.
2. `.planning/workstreams/edd/ROADMAP.md` -- section "Laptop pre-scan" and Phase 1 success criteria.
3. ONLY to settle a specific row: `canary/dossier/refs.jsonl`, a file range (Read with offset/limit, <= 80 lines),
   or the salvaged `phases/01-reality-scan-ownership-matrix-spec/01-RESEARCH.md` (a prior researcher's partial
   notes: a claim, not evidence). That is a PAGE. A row you cannot settle with a page is UNKNOWN in the note --
   never a guess, never a pass.

## Outputs
1. `.planning/workstreams/edd/OWNERSHIP_MATRIX.md`. FIRST ACTION after reading the dossier: write the skeleton with
   all 81 rows (status `DATASET_ONLY`, note `unjudged`), commit it, then fill rows in place. Row format, exactly:
   `| C-NN | <concept title> | <STATUS> | <producer path:line> | <consumer path:line> | <evidence / note> |`
   STATUS is one of: ALREADY_IMPLEMENTED, UNDER_ANOTHER_NAME, PARTIAL, DOCUMENTED_ONLY, DATASET_ONLY,
   REGISTERED_UNREACHABLE, REACHABLE_NOT_EFFECTIVE, NEW, NOT_A_SYSTEM (a process instruction of the mission, e.g.
   MICRO-COMMITS -- say which existing rule already carries it).
   The first five statuses that name an owner need a producer AND a consumer `path:line` that exist at HEAD.
   A dossier candidate is not an owner: confirm the line does what the concept means before citing it.
   Every NEW row gets a section `## 13Q C-NN` answering HR-NOVELTY-001's 13 questions in one line each, with
   file:line; if you cannot answer them, it is not NEW -- reclassify.
2. `vault/specs/edd.md` with front matter `covers: [edd, expectation-driven-development, semantic-conservation,
   self-evolution-debt, decision-frontier, reference-frontier]`: PRD (what EDD adds), architecture (which owners it
   extends, from the matrix), acceptance criteria per ROADMAP phases 2-7, rollback, and the conflicts between the
   iteration standard, CLAUDE.md, UKDL and the mission (only those you observed).
3. `.planning/workstreams/edd/canary/RECEIPT.json`:
   `{"mission_id": "<your mission id from the card>", "boundaries": [{"n": 1, "reason": "AMBIGUITY|NOVELTY|PAGE|PROOF_FAILURE|RECOVERY", "purpose": "<=12 words"}], "pages_read": ["<path or path:range>"], "rows_by_status": {...}, "unknown_rows": ["C-NN"], "learning_paths": []}`
   List every model turn you took after reading this packet as a boundary with its reason. `pages_read` must
   include `canary/dossier/dossier.md`. Leave `learning_paths` empty: the orchestrator fills it.

## Budget (enforced by the mission breaker, measured from transcripts)
- At most 25 model calls. Token estimate 6M; the breaker parks you at 12M. Burn without a work-tree change for
  3M also parks you, so commit the skeleton early and commit again every ~15 rows.
- Batch: settle several rows per turn; issue independent Reads in one turn.

## Done
Run `python3 tools/edd_canary_gate.py`. Your part is G2-G6 and G9; G0/G1 need your receipt and the orchestrator's
envelope, G7/G8 are the orchestrator's after you stop. Commit matrix, spec and receipt (pathspec), then end with
`HANDOFF NOTE:` and one line: rows by status and the gate line. Do not wait for anything.
