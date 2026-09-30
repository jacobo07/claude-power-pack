---
covers: [post-edit-diagnostics, post_edit_diagnostics, gap-2, se-gap-2, d7]
tier: T2
status: SPEC (nothing below is implemented unless marked LIVE)
owner_decisions: 2026-09-30 ("go for gap 2")
---

# Post-edit diagnostics loop

Source: `vault/audits/se-capability-gaps-2026-09-30.md` Gap 2, backlog D7.
Resumption notes: `vault/specs/post-edit-diagnostics.RESUMPTION.md`.

## Problem (measured 2026-09-30)

After the agent edits a file, nothing checks the file. `quality-gate.js` sits in the live
dispatcher `PreToolUse-Edit-chain` and only prints the advice "Run `npx tsc --noEmit`". The
dispatcher has no PostToolUse-Edit chain. The three PostToolUse `Write|Edit` hooks in
`~/.claude/settings.json` (kg-sync-hook, mistake-ingest, gsd-phase-boundary) do bookkeeping,
not diagnostics. So a syntax error or an undefined name written by an Edit is found only when
something later imports or runs the file: often a different turn, sometimes a different session.

An IDE closes this loop by showing diagnostics as you type. The agent's equivalent is a
PostToolUse hook that returns the diagnostics as `additionalContext` in the same turn.

## Scope (v1)

One standalone hook, `hooks/post_edit_diagnostics.js`, registered by its own PostToolUse
entry in `~/.claude/settings.json` with matcher `Write|Edit|MultiEdit`. It does not touch
`hook-dispatcher.js`, because another pane has uncommitted edits to it (backlog D10).

The hook checks exactly one file: `tool_input.file_path` of the tool call that just
succeeded. Checkers by extension:

| extension | checker | what it reports | status |
|---|---|---|---|
| `.py` | `ruff check --select E9,F63,F7,F82 --output-format json <file>` | syntax errors, invalid `is`/comparison forms, statement-placement errors (`break` outside loop, `return` outside function), undefined names | PLANNED |
| `.js` `.mjs` `.cjs` | `node --check <file>` (the node running the hook) | syntax errors | PLANNED |
| `.json` | `JSON.parse` in-process | parse errors; a leading UTF-8 BOM reported as its own finding, because `JSON.parse` and Python's `json` with `utf-8` both reject it | PLANNED |
| `.ts` `.tsx` | none | not covered. A per-file `tsc` ignores `tsconfig.json`, so it would report errors the project does not have. | ABSENT |

Why this rule set and not all of ruff: E9/F63/F7/F82 are real bugs in almost every project, and
a file rarely carries them from before the edit. Style rules would repeat pre-existing noise on
every edit of a legacy file, and the agent would learn to ignore the channel.

Probed 2026-09-30: `node --check` on Node v24.15.0 accepts ESM `import`/`export` in a `.js`
file (exit 0), so ESM files do not produce a false syntax error.

## Behaviour contract

1. **Never blocks.** Output is `hookSpecificOutput.additionalContext` on PostToolUse and exit 0,
   every path. A diagnostic is information for the model, not a gate.
2. **Silent when clean.** No output at all when the checker finds nothing, so the channel only
   speaks when there is something to act on.
3. **Fail-open, but never mute.** A missing checker binary, a timeout, an unreadable file or a
   malformed stdin produce no additionalContext, and each writes one line to the log with the
   reason. "Could not check" and "checked, clean" are different log outcomes (`unchecked` vs
   `clean`), never merged.
4. **Bounded.** stdin read budget 2 s through `hook-utils.readStdinRaw`; each checker spawn has a
   2.5 s timeout; a hard-exit backstop at 6 s. Files over 2 MB are skipped (`skipped:size`).
5. **Output cap.** At most 20 diagnostics listed, then `... and N more`. Each line is
   `L<row>:<col> <code> <message>`.
6. **Kill switch.** `CLAUDE_POST_EDIT_DIAG=off` disables the hook with one log line.
7. **Test seams, both env-driven:** `POST_EDIT_DIAG_LOG` (log path) and `POST_EDIT_DIAG_RUFF`
   (ruff binary, so a test can point it at a path that does not exist).

## Log

`~/.claude/state/post-edit-diagnostics.jsonl`, one JSON line per invocation:
`{ts, tool, ext, outcome, count, ms, reason?}` with `outcome` in
`clean | findings | unchecked | skipped | disabled`. When the file passes 1 MB it is renamed to
`.jsonl.1` (one generation kept), so one edit adds one line and the file cannot grow without bound.
The log is how liveness is proven: if the hook is registered and edits happen, lines appear.

## Acceptance

- `python tools/test_post_edit_diagnostics.py` exit 0, driving the real hook with the real
  PostToolUse stdin shape:
  - a `.py` with an undefined name and a `.py` with a syntax error each surface the code and row;
  - a clean `.py` is silent (control: the same harness that sees the bad file sees nothing here);
  - a `.js` syntax error surfaces, a clean ESM `.js` is silent;
  - a malformed `.json` and a BOM `.json` surface, a clean `.json` is silent;
  - `POST_EDIT_DIAG_RUFF` pointed at a missing binary gives no output, exit 0, and an
    `unchecked` log line;
  - a non-edit tool (`Bash`) and a `.ts` file give no output;
  - kill switch gives no output and a `disabled` line.
- Mutation drill: with the detector's findings-to-context step broken, the suite goes red.
- Live proof: in a real session after registration, an Edit that introduces an undefined name in
  a scratch `.py` returns the diagnostic in that turn, and the log gains a `findings` line.
- Registered in `vault/liveness/reachability_registry.json` if the reachability gate asks for it.

## Rollback

Remove the settings.json PostToolUse entry. The hook has no state other than its log.

## Not in v1

TypeScript, mypy/pyright (not installed), LSP, whole-project checks, auto-fix.
