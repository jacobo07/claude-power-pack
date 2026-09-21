---
phase: 05-close-the-continuation-debts
plan: 01
subsystem: infra
tags: [gsd-long-run, terminal-inbox, ledger, mutation-testing, vscode-extension]

requires:
  - phase: 04-make-non-admission-visible
    provides: "the --explain sweep that names a refused marker, and the two ghost files debt 3 inventories"
provides:
  - "a ledger `armed` row that cannot disagree with the marker of the same arming"
  - "argumentTail() as a pure, exported, gate-reachable predicate in terminal_inbox.js"
  - "a population FLOOR in test_terminal_inbox.py, plus HARNESS-FAILED as an outcome distinct from a verdict"
  - "a residue inventory of four items, recommended and undeleted"
  - "a daemon SENT line that records what the extension actually did (enters=, arg_tail=)"
affects: [milestone-v1-continuation-proven-live, terminal-inbox-delivery, residue-cleanup]

actuals:
  tokens: 9200
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "derive-don't-recompute: a second record of one event reads its value back from the first"
    - "move the predicate to where a gate can reach it, instead of writing a gate that cannot"
    - "a population count is a FLOOR, never an equality — equality makes growth red"

key-files:
  created:
    - .planning/phases/05-close-the-continuation-debts/05-RESIDUE-INVENTORY.md
  modified:
    - tools/gsd_autorun_marker.py
    - tools/test_gsd_long_run.py
    - extension/src/terminal_inbox.js
    - extension/src/extension.js
    - tools/test_terminal_inbox.py
    - tools/test_inbox_delivery_enter.py
    - ~/.claude/hooks/auto-compact-sendkeys-daemon.ps1

key-decisions:
  - "gsd_autorun_marker.py:98 was deliberately NOT touched — the asymmetry between :98 and :253 WAS the defect, so only the later write moved."
  - "The tail rule moved into terminal_inbox.js rather than a gate being written against extension.js: extension.js requires vscode, so no Python or node gate can reach it. Moving the predicate IS the mechanism."
  - "Every V-INBOX-ARGTAIL-* case is SYNTHETIC. This session's real /compact line is deliberately absent — a drill built from the artifact it guards stops testing anything the moment that artifact changes, and that line changes every crossing."
  - "test_inbox_delivery_enter.py stopped pinning the literal `enters: 2` and asserts the PROPERTY instead. The old gate was measuring one build's spelling, so a correct change turned it red."
  - "V-INBOX-LIVE-MATCHES-REPO is left FAILING rather than skipped or re-baselined. It is correct: Cursor executes a copy this commit did not touch."
  - "Nothing in the residue inventory was deleted or staged for deletion. Silence is not authorization."

patterns-established:
  - "Instrument repair is part of the task, not a follow-up: a gate red because its floor decayed is not evidence about its subject."
  - "A verifier failure (no node, spawn error, no summary line) exits 2 as HARNESS-FAILED — never reported as a verdict about the subject."
  - "Each mutation must land on its OWN assertion set. Two mutations landing on one assertion means only one pole is covered."

requirements-completed: [DEBT-1, DEBT-2, DEBT-3]

coverage:
  - id: D1
    description: "A ledger `armed` row names the same absolute project as the marker written by that arming; an unnamed project stays unnamed in both."
    requirement: DEBT-1
    verification:
      - kind: unit
        ref: "tools/test_gsd_long_run.py#V-GSDLR-LEDGER-CWD-ABSOLUTE, -MATCHES-MARKER, -EMPTY-STAYS-EMPTY (96/96)"
        status: pass
      - kind: other
        ref: "scratchpad/drill_t1.py — 2 mutations, distinct assertions, restore SHA-256 3bc96c1ab2fd…"
        status: pass
    human_judgment: false
  - id: D2
    description: "The /compact argument-tail rule lives in a vscode-free module a gate already drives; extension.js calls it and carries no second copy."
    requirement: DEBT-2
    verification:
      - kind: unit
        ref: "tools/test_terminal_inbox.py — TERMINAL_INBOX_PASS=1/1 ok=30/30"
        status: pass
      - kind: integration
        ref: "tools/test_inbox_delivery_enter.py — INBOX_PASS=5/6 (V-INBOX-LIVE-MATCHES-REPO failing by design, see below)"
        status: fail
      - kind: other
        ref: "scratchpad/drill_t2.py — 3 mutations, distinct assertion sets, restore SHA-256 4400f98c3c86…"
        status: pass
    human_judgment: true
    rationale: "The repo half is proven; the executing copy is ~/.cursor/extensions/kobii.pp-sessions-0.4.0 and only the Owner can mirror it (HR-001). Until that happens and the window reloads, this commit changes nothing at runtime."
  - id: D3
    description: "Four residue items inventoried with size, mtime, tracked status, readers finding and a reasoned recommendation; nothing removed."
    requirement: DEBT-3
    verification:
      - kind: other
        ref: "05-RESIDUE-INVENTORY.md — ROWS=4"
        status: pass
    human_judgment: true
    rationale: "A deletion is the Owner's decision. The largest item is UNTRACKED, so git cannot undo a wrong call."
  - id: D4
    description: "The daemon's SENT line records the ack's enters= and arg_tail=, so a crossing leaves durable evidence of what the extension did."
    verification:
      - kind: manual_procedural
        ref: "~/.claude/hooks/auto-compact-sendkeys-daemon.ps1 — SENT Log call, fields read from the already-parsed ack; REFUSED and WOULD-SEND untouched"
        status: pass
    human_judgment: true
    rationale: "That file has no version-controlled copy in this repo, so the edit is unversioned and cannot be proven by a gate here. The first crossing after this phase is what exercises it."

duration: 17min
completed: 2026-09-21
status: complete
---

# Phase 5: Close the Continuation Debts — Summary

**Two records of one arming stopped disagreeing, the `/compact` tail rule moved to where a gate can
actually reach it, and the residue was inventoried and handed over undeleted.**

## Performance

- **Duration:** 17 min (execution; planning preceded it)
- **Started:** 2026-09-21T20:35:05
- **Completed:** 2026-09-21T20:51:49
- **Tasks:** 3
- **Files modified:** 7 tracked + 1 unversioned (`auto-compact-sendkeys-daemon.ps1`)

## Accomplishments

- **DEBT-1.** `gsd_autorun_marker.py:253` passed the caller's raw `args.cwd` to the ledger while
  `write_marker` had stored `resolve_cwd(cwd)`, so one arming could produce an absolute path in the
  marker and a bare `"."` in the ledger row — the same defect `marker_project` REFUSES rather than
  resolves (`gsd_long_run.py:739`). The row now derives its cwd from the marker dict already loaded
  at `:246`. `:98` was left alone on purpose. Three gates added, suite 96/96.
- **DEBT-2.** `argumentTail()` moved out of `extension.js` — which requires vscode, so nothing could
  drive it — into `terminal_inbox.js`, which is vscode-free and already run by a Python gate. Seven
  synthetic `V-INBOX-ARGTAIL-*` cases; selftest `ok=23 → ok=30`.
- **DEBT-3.** Four residue items inventoried with size, mtime, tracked status, a readers search and a
  recommendation each. Nothing deleted, nothing staged for deletion.
- **Two instruments repaired**, both found by running rather than reading (below).

## Task Commits

1. **Task 1: one arming, one project** — `839a14c` (fix)
2. **Task 2: the tail rule moves where a gate can reach it** — `f702c5a` (fix)
3. **Task 3: residue inventory** — `c71e9a4` (docs)

**Plan metadata:** `06affee` (plan + context, debt 2's claim narrowed on measurement)

## Files Created/Modified

- `tools/gsd_autorun_marker.py` — `:253` derives cwd from the marker it just wrote
- `tools/test_gsd_long_run.py` — three `V-GSDLR-LEDGER-CWD-*` gates, armed via the CLI with `--cwd "."`
  and the subprocess cwd set to the temp project (the shape 8 of 9 real markers held)
- `extension/src/terminal_inbox.js` — `argumentTail()` + seven synthetic selftest cases, exported
- `extension/src/extension.js` — destructures `argumentTail` at `:35`, calls it at `:160`; no regex left
- `tools/test_terminal_inbox.py` — floor instead of equality, `HARNESS-FAILED` as its own outcome
- `tools/test_inbox_delivery_enter.py` — asserts the property, not the literal; new
  `V-INBOX-ARGTAIL-VIA-SHARED-HELPER` requires the call AND the absence of an inline regex
- `05-RESIDUE-INVENTORY.md` — four items, awaiting one decision
- `~/.claude/hooks/auto-compact-sendkeys-daemon.ps1` — SENT line carries `enters=` and `arg_tail=`

## Decisions Made

See `key-decisions` in the frontmatter. The load-bearing one: **the tail rule was not gated where it
lived — it was moved to where a gate already runs.** Writing a gate against `extension.js` was
impossible, and a second copy of one rule drifts.

## Deviations from Plan

**One, and it is a correction to the plan's own prediction rather than to the code.**

`05-PLAN.md` predicted that dropping the `^` anchor (mutation c) would fail the `/gsd-autonomous`
case. Driven, it fails only `V-INBOX-ARGTAIL-ANCHORED-AT-START`: dropping the anchor lets a `/compact`
appearing *later* in a line match, so a command containing no `/compact` at all still tails to `""`.
The mutation that produces the predicted failure is (b), removing the guard.

**Why this matters more than the fix:** had (c) been driven alone and its prediction taken on trust,
`V-INBOX-ARGTAIL-OTHER-COMMANDS-EMPTY` would have been recorded as covered while nothing had
exercised it. Recorded in `f702c5a`'s message.

## Issues Encountered

- **Two instruments were red or silently wrong, and both were repaired in the task that found them.**
  `test_terminal_inbox.py` compared the selftest's case count by **equality** against 12 while the
  selftest emitted 23 — permanently red for *growing*, and the equality also matched as a substring,
  so `ok=12` was satisfied by `ok=120`. It now parses the integer and holds a floor (30).
  `test_inbox_delivery_enter.py` pinned the literal `enters: 2`, which `f771f55` made `argTail ? 3 : 2`,
  so a **correct** change was failing a gate measuring one build's spelling.
- **A `HR-SECRET-001 … detector timed out (host likely starved)` denial** on a Write. Measured the
  host before retrying: 6,198 MB free of 32,061 (19.3 %), 6 node processes — transient contention
  from this session's own drill fan-out, not a starved host. Retried once, successfully.
- **A wide PowerShell sweep timed out at 120 s.** Pivoted to the Grep tool (ripgrep), which answered
  immediately. This session's own recorded rule about wide oracles.

## Open Residuals — named, not closed

**1. The popup-behaviour coupling is made OBSERVABLE, never closed.** `05-CONTEXT.md` §2 names the
class: a future build changes the completion-popup behaviour, the `/compact` tail becomes a stray
message in every crossing, and no test says so. **That class is no longer hypothetical** — the 18:24
crossing compacted on the command line's own two Enters and the tail landed in the fresh prompt as a
bare user message.

No unit test can close it. The subject is a host popup in a build this estate does not own, and
asserting an Enter arity would pin the very number a build is expected to move — trading an
unobservable failure for a brittle gate. What this phase closed instead is the reason that crossing
could not answer the question afterwards: the ack file is consumed the moment delivery completes, so
nothing durable said what the extension did. The daemon's SENT line now carries `enters=` and
`arg_tail=`. **The first crossing after this phase is what tests it.**

**2. Whether the tail is NEEDED is deliberately undecided.** One observation each way (16:51 yes,
18:24 no) with a window reload between them. Neither reading may be asserted, so debt 2 pins the
*contract* — extraction, anchoring, scoping — and not the disputed claim.

## User Setup Required

Three items, all the Owner's:

1. **Mirror the live extension.** Run `scratchpad/apply-argtail-helper.ps1` (backs up, copies,
   `node --check`, live selftest), then reload the Cursor window. Until then
   `V-INBOX-LIVE-MATCHES-REPO` stays red and `f702c5a` changes nothing at runtime. That gate is
   correct and must not be skipped or re-baselined to make the suite look clean.
2. **Decide the residue** — **ANSWERED 2026-09-21 21:11 and carried out** (`e879d18`). All four,
   per the recommendation: backup first at `~/.claude/backups/residue-20260921-211149`, every copy
   re-hashed before anything was removed, `RESIDUE_DELETED=4/4`. The readers finding was then tested
   rather than trusted — MADM 7/7, INTENT 9/9, GSDLR 96/96 afterwards. Digests in
   `05-RESIDUE-INVENTORY.md`.
3. **Decide whether the daemon gets a repo mirror.** `auto-compact-sendkeys-daemon.ps1` has no
   version-controlled copy here, so this phase's edit to it is unversioned. Creating a mirror is a
   drift decision, not a tidy-up.

## Next Phase Readiness

- Debts 1 and 2 are gated with a driven red branch each and a digest-verified restore. Debt 3 is
  answered, carried out and digest-recorded.
- **The milestone gate reads PARTIAL, not UNPROVEN — and the figure printed above was wrong.**
  Measured 2026-09-21 21:17: `crossings 3, confirmed 1, proven_window 2, window_confirmed 1`. This
  session's own 18:52:03 crossing confirmed at 18:56:24 with `/gsd-autonomous`, which is the first
  confirmed resume this session produced. The "crossings 2, confirmed 0" written elsewhere in this
  file and in `da489a0` / `f59c471` / `e879d18` was carried forward from a pre-compaction summary
  and never re-measured, while the confirmation had already landed. **One more crossing whose resume
  confirms is all `PROVEN` needs**, and nothing about the wall is blocking it.
  **SUPERSEDED 2026-09-21T20:54:39Z — that crossing happened.** `report` now reads `PROVEN`:
  crossings 4, confirmed 2, `window_confirmed 2`. See `.planning/STATE.md` and §10 of
  `vault/specs/cpp-gsd-long.CERTIFICATION.md`.
- **A fifth debt was named and is NOT fixed:** a manual `gsd_long_run.write_trigger()` writes the flag
  the daemon consumes but not the `delivery_inbox_requested` ledger row (`context-watchdog.py:675`),
  so a successful manual re-arm is invisible to the milestone gate. It was used to break the
  delivery deadlock in this session, which is how it was found.
  **SUPERSEDED — fixed in `7f88790`, later the same day.** `tools/gsd_long_run.py:725` now appends
  the row with `producer="gsd_long_run.write_trigger"` and a `kind` **derived** from the payload it
  just wrote rather than recomputed. Three gates (`V-GSDLR-INBOX-DELIVERY-IS-LEDGERED`,
  `-ROW-KIND-DERIVED`, `-ROW-NAMES-PRODUCER`), red branch driven, 96 → 99/99.

  Both corrections above were surfaced by the milestone integration check, not by a re-read: a
  SUMMARY is written once and the code keeps moving under it, so *"this residual is still open"*
  decays into a false statement silently. That is the same failure as the stale gate figure two
  bullets up, one artifact later. Recorded in `.planning/INTEGRATION-CHECK.md` as FINDING 1.

---
*Phase: 05-close-the-continuation-debts*
*Completed: 2026-09-21*
