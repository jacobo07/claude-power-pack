# Self-Improve x Claude Power Pack -- atomic assimilation (2026-11-21)

Mission record and resumption point. Source audit (hypotheses, not truth):
`~/Downloads/self_improve_cpp_assimilation_audit_2026-11-21.md` (upstream grandamenium/self-improve-skill @ 5a99b6a).
Mode: EXECUTION, in-session (Owner chose it over a Ralph mission: the GSD-X scaffold would have archived another
workstream's dirty `.planning/`). Branch `feature/knowledge-acquisition` (shared tree; pathspec / private-index commits).

## Reality scan verdicts (SI backlog)

| id | verdict | evidence / action |
|---|---|---|
| SI-00 | LIVE -> FIXED | `confirm_draft` filed the Owner's words as a high-confidence root cause. `3bd09a42`. History: 0 rows affected |
| SI-01 | LIVE (adversarial) -> FIXED | `[1,2]` crashed 3 Python readers; `null` crashed the JS hook. `9f90e227`, `ec74ce4e`. Live corpus: 0 such lines |
| SI-02 | LIVE -> FIXED | two Owner-turn definitions (8 vs 12 wrappers); JS read sidechain as Owner. One list + V-EVENTS-JS-PARITY. `5f7daaed` |
| SI-03/04/10 | REJECTED by measurement | one streaming pass: 7 days / 173 MB in 8-26 s, heap 1.8 MB. No cache, DB, cursor or daemon justified |
| SI-05 | REAL, small -> FIXED | windows filter on each event's own ts (4,189-4,615 records/7d were outside by event time) |
| SI-06 | LIVE -> FIXED | old cue: 15 hits/1,296 turns, all FP; new: 7/7 in-sample, 2/2 held-out, recall UNKNOWN. `8af361d1` |
| SI-07 | ALREADY SOLVED -> REUSED | usage deduped per (message.id, requestId), token_ground_truth contract |
| SI-08 | LIVE -> CANONICAL FIXED, LIVE PENDING OWNER | producer never registered (0 drafts ever). `584ba206`; live needs the one line below |
| SI-09 | FIXED | Secret Firewall + home + e-mail redaction in reader and CEPS drafts; canary gates + drills |
| SI-11 | OPEN (frontier) | skill baseline-vs-candidate A/B in PP Eval not attempted |
| SI-12 | PARTIAL | retrieval proven (recall ranks each new UKDL entry #1); application in a LATER task not yet observable |

## What exists now

- `tools/transcript_events.py` -- streaming normalised events: ref `<sid>:<line>`, 9 authority classes (OWNER is
  a structural heuristic, never authentication), event-time windows, redaction, store identity via tis_observed.
- `tools/analyze_transcripts.py` + `commands/analyze-transcripts.md` (live in `~/.claude/commands`) -- read-only
  retrospective; proposes ranked HYPOTHESES with owner/validate/risk/refs; EMPTY/PARTIAL labelled.
- `tools/ceps.py` -- `correction_cue`, UNDIAGNOSED/OWNER_DIAGNOSED/VERIFIED, `confirm --root-cause`, redacted drafts.
- `/ceps` is now installed live (it never was).
- UKDL `25c70ee8`: 6 T- + 2 PR- entries (no HR).

## Gates (run from the repo root)

```
python tools/test_analyze_transcripts.py   # V-AT-*      25/25 (2 mutation drills)
python tools/test_reader_robustness.py     # V-READER/V-EVENTS 9/9 (incl. JS parity)
python tools/test_ceps_corrections.py      # 15/15
python tools/test_ceps_admission.py        # 20/20 (was 19/20 for its life: FP instrument, 0bad59dd)
node hooks/_tests/test-ceps-correction-stop.js   # 8/8
node hooks/tests/test-dispatcher-session-of.js   # all passed (was red on CRLF, 4762b093)
```
Unchanged neighbours green: usage_dedup 14/14, tco_tracking 6/6, conversation_quality_audit 6/6, ceps closed_loop
10/10, edge 6/6, full_cycle, hook_boundary 7/7, dispatch_liveness 6/6.

**Production Reality Gate** (fresh process `claude -p "/analyze-transcripts --days 2 --top 3"`, session 47bdafa3):
slash command recorded; engine call `:42`; engine result `:44` (9,291 chars, not an error); cited ref
`0d8a9cb8:291` is a real `hook_cancelled` PreToolUse:Edit timedOut=true record. SI-08 chain: real hook process
dispatched `ceps.py from-stop` (turns=1, tool_result excluded); CLI path produced a redacted HEURISTIC draft.

## Owner actions (authorisation required)

1. **Make SI-08 live** -- ONE line, not a file copy (a copy would also activate `corpus-reuse-sentinel.js`, which
   canonical registers and live does not). Tested on a scratch copy of live: +1 line, node --check clean, idempotent:
   ```
   ! $f="$env:USERPROFILE\.claude\hooks\hook-dispatcher.js"; $t=[IO.File]::ReadAllText($f); $a="tools/ceps_promote_stop.py', timeoutMs: 8000 },"; if (-not $t.Contains('ceps_correction_stop.js')) { $t=$t.Replace($a, $a + "`n    { exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/ceps_correction_stop.js', timeoutMs: 3000 },"); [IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding($false))) }; node --check $f
   ```
   Then `/ceps drafts` after a few sessions; confirm (UNDIAGNOSED unless you state the cause) or dismiss.
2. **Legacy test pollution:** live UKDL / session_lessons hold 74 / 73 copies of `ceps_cfe92dd0fab0552c`
   (old test_ceps_admission runs). Removing them edits a file the CEPS bridge appends to continuously -- yours to approve.

## Debt / frontier (named)

- Top real finding: PreToolUse Write/Edit/PowerShell hooks time out ~4-5% of runs (123/2407, 108/1880, 97/2771 in 7d),
  i.e. their guards fail open. Confounder: host RAM (child session started at 4.9% free). Owner: hook-dispatcher.js.
- Ripgrep timeouts on Glob/Grep: 11 failures across 10 sessions (7d).
- `test_ceps_admission` takes 129 s > verify_spp's 60 s cap: its verify_spp row has never produced a verdict.
- Dispatcher drift: `corpus-reuse-sentinel.js` is registered in CANONICAL only (live: 0). Whether to activate it is
  its owner's decision; a whole-file copy would do it silently (T-WHOLE-FILE-MIRROR-SYNC-SHIPS-EVERY-PENDING-CHANGE-001).
- Liveness reachability scans `modules/` only; it is silent (not green) about `tools/`.
- SI-11, SI-12 application proof (above).

## Meta-analysis

False premises: the hermetic gate's 19/20 looked like a leak (it was a history-blind instrument); `/ceps` was assumed
installed (it was not); "copy canonical -> live" looked safe (it would activate an unapproved hook). RETRACTED: I first
published that drift backwards (live-only) from a misread `Compare-Object` side indicator -- in the dispatcher comment,
the message of `584ba206`, UKDL `25c70ee8` and this file; a scratch-copy test of the Owner command exposed it; corrected
in `1f64762f` (T-DIFF-SIDE-READ-BACKWARDS-001) and the next commit. The commit message of `584ba206` stays wrong. Decisive evidence: the
harness's own hook telemetry (19k records with duration/exit/timeout) -- it made upstream's hook heuristics obsolete.
What the first real run taught: three gates and two signatures were wrong until run on real data and drilled; every
negative gate now has a drill. Deterministic now: authority, windows, dedup, signatures, retries. Still semantic: why a
successful session worked, whether a gate refusal is a true catch. Marginal cost: a retrospective that took a manual
audit now costs one command and ~10-30 s.

## Resumption

Read this file, run the gate block above, then pick from Debt/frontier. NEXT MODE: EXECUTION.
