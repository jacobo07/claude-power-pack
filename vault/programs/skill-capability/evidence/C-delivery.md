# [C] opportunity / delivery / recall / precision -- evidence

Frozen C rule (ledger.json, never edited here):

> opportunity, delivery, recall and precision are computed by one gate from transcripts over a named window; recall and precision report n and are never extrapolated from n < 5

## Definitions

- opportunity: a commit-card judgement row with decision `opportunity`, `deny-card` or `pass-unrecordable` that lists at least one foreign file (the capability was needed or shown at a commit; `pass-unrecordable` is a commit whose card could not be shown, so card delivery missed it). A commit row with any other decision value is counted in `other_decision`, never dropped.
- delivered: the capability reached the model at or before the judgement `ts` in the same session, by the card (decision `deny-card`) OR by an invocation (a Skill tool_use or a typed command counted by tools/skill_invocations.py); a mention, listing or hook body is never delivery.
- recall: delivered / opportunities whose delivery is measured. An opportunity with no transcript read or only untimed candidate rows is UNMEASURED and sits outside n, never counted as not delivered.
- precision: (delivered AND needed) / delivered with a needed label; needed = frozen D-CARD ground truth or the window fixture's per-row label.
- small n: a rate is printed with its n, and with n < 5 no ratio is printed or estimated.
- a skill with no opportunity detector reports opportunity UNMEASURED, never 0.
- subagent caveat: a Skill call inside a subagent transcript is joined to its parent session (tools/skill_invocations.py session_of), so invocation delivery can count a call that reached the subagent's context and not the parent's; the gate does not split subagent from main-session hits.

## Planes

- Window F is the fixture plane: synthetic rows authored for a known answer, host-independent.
- Window L is the laptop plane: the committed content-free evidence pack (a selection of the laptop's card ledger), pinned by its LF sha256.
- Window G is this host's own transcripts (plane: the host named in its record), a recorded measurement: invocation delivery is measured there, opportunity is UNMEASURED because the host has no card ledger.
- Window G is a recorded measurement, not an L5 input: the gate's default mode reads only committed files, because `--final` re-runs it on the laptop where this host's transcripts do not exist. This host's transcripts also keep growing while the run writes them, and Claude Code prunes old ones, so a fixed window can vanish.
- Re-measuring on gex44 stays pinned: the window is named by --root + --days + --end, rows are bounded by their own timestamps, and --compare shows that a re-run reproduces the record.
- Laptop owner command shape: python tools/test_skill_delivery.py --measure-live --window laptop --root ~/.claude/projects --days 7 --end <ISO> --out vault/programs/skill-capability/evidence/C-window-laptop.json
- No figure in this file sums across windows. Each figure line carries its window prefix and its n.

## Window F

[F] plane: fixture
[F] selection: synthetic: every row authored for a known answer
[F] opportunities: 9
[F] delivery measured: 7
[F] delivery UNMEASURED: 2 (outside the recall n): f0000000-0000-4000-8000-000000000006 opportunity 2026-10-01T11:30:00.000Z: no transcript read; f0000000-0000-4000-8000-000000000008 opportunity 2026-10-01T12:00:00.000Z: only untimed candidate rows
[F] delivered: 4 (card 3, invocation-only 1, card and invocation 1)
[F] recall: 4/7 = 0.571 (n=7)
[F] precision: n=4 (< 5, not estimated)
[F] pass-after-card rows (not opportunities): 1
[F] no_opportunity rows: 1
[F] judgement unknown or timeout rows: 2
[F] non-commit rows ignored: 1
[F] other decision rows (counted, never dropped): 1
[F] unparseable card ts (counted; a deny-card keeps card delivery, any other decision is UNMEASURED): 0

## Window L (plane: laptop, selection: 20 of 140 ledger rows picked by the builder rule)

[L] pack: vault/programs/skill-capability/card_evidence_pack.json, LF sha256 dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05
[L] selection rule: decision in ("deny-card", "pass-after-card") or "exit 128" in str(reason)  (card_evidence_pack.py lines 81-82)
[L] selection: 20 of 140 ledger rows; by decision {'deny-card': 6, 'pass-after-card': 8, 'unknown': 6}
[L] opportunities: 6 (n=6)
[L] delivery measured: 6, UNMEASURED: 0
[L] delivered: 6 (by card 6, invocation-only 0)
[L] card and invocation: UNMEASURED (the pack ships 9 Skill tool calls with no skill name, so the invocation channel is UNMEASURED, never 0 and never 9)
[L] recall: 6/6 = 1.000 (n=6) -- selection-bound: the builder picks no undelivered opportunity rows, so this is 1 by construction and is not a population recall
[L] population recall: UNMEASURED on host gex44
[L] precision (card channel): 0/5 = 0.000 (n=5), labels from frozen D-CARD (live_denies 5, true_positives 0)
[L] unlabelled delivered beside D-CARD, never folded in: 1 (4615e1d1)
[L] pass-after-card rows (not opportunities): 8
[L] judgement unknown (git exit 128), beside and never counted: 6
[L] other decision rows (counted, never dropped): 0

## Window G (plane: kobicraft-gex44, recorded measurement)

[G] host: kobicraft-gex44; root ~/.claude/projects; days 7; start 2026-09-26T18:05:00Z; end 2026-10-03T18:05:00Z
[G] selection: transcript files with mtime >= start under root; transcript rows with timestamp in [start, end]; card rows with ts in [start, end]
[G] concurrent-writers-shared-tree invocations: model 0, typed 0 (measured); opportunity UNMEASURED (card ledger ABSENT on this host)
[G] recall and precision: UNMEASURED (no opportunity source on this plane)
[G] totals: model 31, typed 23, unknown_rows 0, untimed_rows 0, sessions with calls 23
[G] files scanned (informational, excluded from --compare): 189
[G] installed names: 271; other skills: UNMEASURED (no detector)
[G] skill gsd-autonomous: model 3, typed 23, opportunity UNMEASURED
[G] skill gsd-code-review: model 5, typed 0, opportunity UNMEASURED
[G] skill gsd-execute-phase: model 12, typed 0, opportunity UNMEASURED
[G] skill gsd-plan-phase: model 11, typed 0, opportunity UNMEASURED
[G] command: python3 tools/test_skill_delivery.py --measure-live --window G --root ~/.claude/projects --days 7 --end 2026-10-03T18:05:00Z
[G] command: python3 tools/test_skill_delivery.py --measure-live --window G --root ~/.claude/projects --days 7 --end 2026-10-03T18:05:00Z --compare vault/programs/skill-capability/evidence/C-window-G.json

## Commands

- command: python3 tools/test_skill_delivery.py
- command: python3 tools/test_skill_delivery.py --write-evidence

## D-SESSIONS

- 0 fresh sessions were consumed in this phase (frozen D-SESSIONS: new_benchmark_cap 10).
