# Gap 2 — post-edit diagnostics loop: resumption (2026-09-30)

Owner: "go for gap 2" (audit `vault/audits/se-capability-gaps-2026-09-30.md`, backlog D7).
No file edited yet. T2 under SDD-OS: write `vault/specs/post-edit-diagnostics.md` (with
`covers:`) BEFORE the first code edit.

## Findings (verified 2026-09-30, do not re-derive)
- Today nothing runs a checker after an edit. `quality-gate.js` sits in the live dispatcher
  `PreToolUse-Edit-chain` (live `~/.claude/hooks/hook-dispatcher.js` ~line 447) and only PRINTS
  "Run `npx tsc --noEmit`".
- PostToolUse `Write|Edit` entries in `~/.claude/settings.json` today: kg-sync-hook.js,
  governance-overlay/hooks/mistake-ingest.js, gsd-phase-boundary.sh; plus the matcher-less
  `hook-dispatcher.js --event=PostToolUse-default`. Dispatcher chains have NO PostToolUse-Edit chain.
- `hook-dispatcher.js` has uncommitted drift from another pane (backlog D10): do NOT edit it.
  Prefer a NEW standalone hook file registered by its own settings.json PostToolUse entry
  (matcher `Write|Edit|MultiEdit`). settings.json writes may be refused by the auto-mode
  classifier (HR-001): if so, ship the hook + test and give the Owner the exact entry to add.
- Installed: ruff 0.15.6 (PATH + pip). NOT installed: mypy, pyright, eslint, any LSP.

## Plan (v1)
1. Hook `hooks/post_edit_diagnostics.js`: on PostToolUse for the edited file only, run
   - `.py`: `ruff check --select E9,F63,F7,F82 --output-format json <file>` (syntax errors,
     undefined names: real bugs, rarely pre-existing, so near-zero noise);
   - `.js/.mjs/.cjs`: `node --check <file>`; `.json`: parse.
   Report findings as `additionalContext` (the model reads them the same turn). Never block.
   Budget ~3 s, fail-open, silent when clean. TypeScript: declared NOT covered (status PLANNED),
   not faked — per-file tsc ignores tsconfig.
2. Test `tools/test_post_edit_diagnostics.py`: drive the hook with the real PostToolUse stdin
   shape; an undefined name / syntax error must surface; a clean file must be silent (control);
   missing ruff = silent fail-open with a log line. Mutation-drill the detector.
3. Wire (settings entry), then prove it LIVE in a real session: edit a scratch .py with an
   undefined name and see the diagnostic arrive. Register in the liveness registry.

## STATUS 2026-09-30: DONE (steps 1-3)
Hook + spec + test committed 88e8c91; settings.json entry added and proven live (see the spec's
Evidence section). Nothing left for Gap 2 v1. Open follow-ups, not blocking:
- TypeScript is ABSENT by design (per-file tsc ignores tsconfig); a v2 would need a project-aware
  checker.
- `tools/mutation_drill.py` cannot drill a subject whose test lives in another directory (it
  copies only the subject dir, so the live file gets exercised). Worth a `test_env` seam there.
Next repo obligations: D5 (4 unrun pp-eval drills when free RAM >= 6 GB), D4 (read
`~/.claude/state/pp-eval/nights.jsonl` after 2026-10-01 03:30).
