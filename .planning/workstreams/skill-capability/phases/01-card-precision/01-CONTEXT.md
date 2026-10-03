# Phase 1: Card precision - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), enriched with the orchestrator's evidence read
**Host:** gex44 (every runtime claim below names its plane)

<domain>
## Phase Boundary

Pillar A of `vault/programs/skill-capability/ledger.json`. The commit card (`hooks/doctrine_cards.js`) stops
denying the session's own tool-mediated writes without letting a foreign hunk through. Frozen rule (ledger
`frozen.pillars[A].rule`, immutable): mtime-window provenance; arm C stays 2/2 GREEN; a gate replays the 5 live
false denies as allowed AND keeps a pre-session foreign hunk denied; the `git exit 128` x6 class is root-caused
and named. C8 target: a delivery card (deny-once question), never an authority.

</domain>

<decisions>
## Implementation Decisions

### D-01 mtime-window provenance (the fix)
- The card already reads the session transcript (+ `subagents/*.jsonl`). Add: per shell tool call
  (`Bash` / `PowerShell` tool_use), a window `[tool_use row timestamp, matching tool_result row timestamp]`;
  per file the session edits with Edit/Write/MultiEdit/NotebookEdit, the time of its last own edit.
- In `judge`, a file that has foreign hunks is moved to `unknown` (reason `mtime-in-own-shell-window`) when its
  current mtime lies inside one of this session's shell windows (small slack, 1 s, for fs/clock granularity)
  AND after its last own edit. Otherwise it stays foreign. Missing file (deleted), unreadable stat, rows
  without timestamps -> no window -> stays foreign (fail toward the card, which is deny-once, never a block).
- Ledger rows for this class name the reason so the effect is measurable afterwards.
- Aperture (documented in the header, not hidden): a peer writing the same file during one of this session's
  shell windows reads as unknown; a file this session's shell touched after a pre-session foreign edit reads
  as unknown. Pre-session foreign hunks whose mtime precedes every shell window stay foreign.

### D-02 Replay gate (evidence-driven, not invented)
- Laptop evidence pack (`/home/kobii/missions/skill-capability-data/card_evidence_pack.json`, content-free,
  20 card-ledger rows / 7 sessions) is copied as a fixture under `vault/programs/skill-capability/` and cited
  by sha256. The gate drives the REAL card as a child process against REAL scratch git repos, using each
  deny session's real tool-call windows (timestamps from the pack).
- Writer windows identified from the pack (orchestrator read, verify in research):
  - 300ac3a1: ucep ROADMAP/STATE written by `gsd-tools roadmap.update-plan-progress` 12:13:52-12:14:04Z, deny 12:14:12Z
    (the pack's mtime is of the MAIN checkout copy, the session worked in `.claude/worktrees/ucep`: not usable).
  - 3a05f288: census.json mtime MEASURED 13:40:45.084Z inside the own-script window 13:39:24-13:40:45.729Z.
  - 5b36b02f #1: force-reload spec, last own Edit 13:23:49Z, oxfmt window 13:26:38-13:27:00Z, deny 13:29:15Z.
  - 5b36b02f #2: terminal-input-probes.ts, last own Edit 13:49:53Z, oxlint+oxfmt 13:50:01-13:50:27Z, deny 13:50:42Z.
  - 4a7ee8bc: CE ledger.json written by `ledger_write.py` run 14:23:51-14:24:04Z, deny 14:25:15Z.
  Only 3a05f288 has a measured mtime; for the other four the gate places the mtime inside the writer window
  and SAYS so (the identification is from command text). Never claim measured mtimes that were not measured.
- Red poles in the same gate: same transcripts with the file mtime set BEFORE the session's first tool call
  (pre-session foreign hunk, arm C shape) -> still denied; a mutant card without the window rule -> the 5
  replays deny again.
- The 6th deny (4615e1d1, Orca X, after the freeze) is reported BESIDE D-CARD, never folded in. Orchestrator
  read: a rollover-resumed session (certify --from 5b36b02f) committing lines its predecessor wrote by Edit
  at 13:38:30Z; mtime = its own Edit at 14:42:07Z, not a shell window -> the window rule does NOT allow it.
  Name the class ("rollover predecessor lines"), do not fix it here.

### D-03 `git exit 128` x6
- 3 rows, session `abcd1234`, basis `index`: `hooks/tests/test-capsule-mutation-guard.js` e2e section runs the
  real dispatcher with a PowerShell `git commit -m x`, `cwd: 'C:\\proj'`, and NO `DOCTRINE_CARDS_STATE_DIR` in
  its env -> the card runs `git -C C:\proj diff --cached` -> exit 128 (cannot change dir / not a repo) and writes
  the row into the LIVE ledger. Fix: the test sets a private `DOCTRINE_CARDS_STATE_DIR`; reproduce the 128 on a
  nonexistent repo path in the gate.
- 3 rows, session `fce2689e`, basis `only-paths`, cwd `C:\Users\User\Apps\io-mnb-w0`: the card records no
  stderr, so the cause is not recoverable from the ledger. Fix: classify git's stderr on a non-zero exit
  (`not_a_repo`, `cannot_chdir`, `unborn_head`, `outside_repo`, `dubious_ownership`, `other`) into the ledger
  row; reproduce each class that yields 128 in the gate. A commit in a repo with no HEAD (first commit) is a
  real false unknown: diff against the empty tree instead.
- What the gate cannot reproduce from GEX44 (the exact fce2689e command) is stated as such.

### D-04 Ledger closure
- `state.A` = IMPLEMENTED_AND_VERIFIED with evidence kinds `gate` (argv of the new python gate under `tools/`)
  and `prg` (a progress/evidence md under `vault/programs/skill-capability/evidence/`), sha256 of LF bytes.
- Savings: none realized; the turn saving (+1 turn per false deny, 5 in D-CARD) is an `upper_bound`,
  displacement `unknown`, denominator `D-CARD`.
- `python tools/test_skill_capability_program.py --pillar A` must print PASS.

### Claude's Discretion
Code layout inside `doctrine_cards.js`, test names (`V-DC-*` / `V-SCA-*`), fixture shape.

</decisions>

<code_context>
## Existing Code Insights

- `hooks/doctrine_cards.js` (365 lines): `plan` -> `git` -> `ownership(transcriptPath)` -> `judge(diff, own)`.
  `ownership` already scans tool_use rows; transcript rows carry a top-level `timestamp`; tool_result blocks
  carry `tool_use_id`. Exports `{ plan, parseDiff, judge, COMMIT_RE }`.
- `hooks/tests/test-doctrine-cards.js`: real child process + real scratch repo pattern; arm C is case 7b.
  `hooks/tests/test-destructive-doctrine-card.js` must stay green. Run with `node`.
- Done-gate wrapper: `tools/test_skill_capability_program.py` (do not edit CE's verifier).
- GEX44 has `git` on PATH; the hook's Windows fallback path is inert here.

</code_context>

<specifics>
## Specific Ideas

- Gate script name: `tools/test_card_precision.py` (python, so the ledger's gate argv form `["python", "tools/..."]`
  admits it) that runs the node suites and the replay.

</specifics>

<deferred>
## Deferred Ideas

- Rollover-predecessor ownership (read the certified predecessor's transcript): named, not built.
- Live hook sync of `hooks/doctrine_cards.js` to the laptop's `~/.claude/hooks/`: laptop plane -> owner bundle.

</deferred>
