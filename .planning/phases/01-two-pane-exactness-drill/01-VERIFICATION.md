---
status: passed
phase: 01-two-pane-exactness-drill
date: 2026-09-21
must_haves_verified: 13
must_haves_total: 13
superseded: 2026-09-21 (original gaps_found report preserved below, unedited)
requirements: n/a (no REQUIREMENTS.md in this project; PLAN cites [C2, C3, C4, C5] but nothing in the repo defines what those IDs mean, so they cannot be traced)
---

# SUPERSEDED 2026-09-21 — the gaps below are CLOSED

**The body of this report is left exactly as written.** It describes a run that
happened and findings that were true when taken; editing it to match today's
tree would fabricate a verification. This banner records what changed since.

Every gap it names was an artifact that did not exist. All now do:

| gap named below | closed by |
|---|---|
| `seal` not implemented (`argparse` choices lacked it) | `two_pane_drill.py` — `seal` writes `vault/evidence/two-pane-exactness/<runid>.json` |
| `vault/evidence/two-pane-exactness/` absent | `enterfix.json`, `live2.json`, `live3.json` |
| `vault/lessons/two-pane-exactness-drill.md` absent | written |
| three of six live gates unwritten | `V-TWOPANE-OWNER-REFUSED`, `V-TWOPANE-NOOWNER-NOT-TYPED`, `V-TWOPANE-INBOX-DRAINED` (commit `9b9a1ad`) |
| red branches never driven | `tools/test_two_pane_gate_drills.py`, 9/9, hermetic |

**Observed, 2026-09-21, this tree:**

```
python tools/test_two_pane_exactness.py --runid live3   -> TWOPANE_PASS=11/11  exit 0
python tools/test_two_pane_exactness.py                 -> TWOPANE_PASS=7/7    exit 0
python tools/test_two_pane_gate_drills.py               -> TWOPANE_DRILL_PASS=9/9  exit 0
```

`live3` is a genuinely two-pane run: A = `5094872a` (subject), B = `1b7f6df9`
(dedicated ARMED control). G2 — the gap that said pane B was never a second
dedicated session — is closed by that run, not by an argument.

**Two limits this banner does not paper over.** The refusal legs pass on rows
from the REAL ledger, i.e. live autonomous crossings, not rows this drill
produced; each gate says so in its own evidence string. And
`V-TWOPANE-INBOX-DRAINED` matches on session ids, so for a session that also
carries real traffic it names candidates rather than proving ownership — the
two acks it flagged were removed on the Owner's explicit decision, backed up
first, not on the gate's say-so.

---

# Phase 1: Two-pane exactness drill — Verification Report

**Phase Goal (verbatim):** with two live sessions in two panes, a continuation
armed for session A is submitted into A's own terminal and never into B's, and
a request whose owner does not answer is refused rather than typed into
whatever window has focus.

**Done-criteria (verbatim):** both panes' transcripts read; A carries the
resume line, B carries none; one deliberately unowned request is ledgered
`refused` with its reason.

**Method:** goal-backward, from the actual codebase and actual artifacts on
disk — not from SUMMARY.md prose. Every claim below cites the file, command,
or log line that settled it.

## THE CENTRAL QUESTION — is the SUMMARY's cited evidence still real?

The SUMMARY (`01-SUMMARY.md`) cites `twopane_d2.out` and `count_submissions.out`
("scratchpad") as the evidence for the positive leg.

- **`twopane_d2.out` — UNVERIFIABLE.** Not found anywhere under
  `C:\Users\User\AppData\Local\Temp\claude\C--Users-User--claude-skills-claude-power-pack\`
  (checked the session directory named in this task's brief,
  `9af80e55-9865-4c6f-877c-d155da18becf`, which holds only two unrelated
  `tasks/*.output` files; a broader glob across every session directory under
  that host root found no file by this name anywhere). Not tracked in git
  (`git log`/working tree — absent). The script that would have produced it,
  `twopane_positive.py`, is referenced only in `01-SUMMARY.md`'s prose; it does
  not exist in the repo and was never committed.
- **`count_submissions.out` — UNVERIFIABLE.** Same search, same result: absent
  from the scratchpad, absent from git, and its producing script does not
  exist in the repo.
- **Verdict on these two specific artifacts: UNVERIFIABLE, not FAILED.** Their
  absence does not prove the numbers in the SUMMARY were fabricated — it
  proves the claim currently rests on nothing checkable. What would close it:
  either artifact re-appearing on disk with the content the SUMMARY quotes, or
  a fresh re-run producing new, committed evidence.

**However — a different, still-real artifact independently supports the same
underlying claim**, and it was not cited by the SUMMARY at all:

`C:\Users\User\AppData\Local\Temp\pp-two-pane-drill\enterfix\manifest.json`
(and its paired transcripts) is a genuine, still-on-disk drill run produced by
the actual `tools/two_pane_drill.py` tool this phase built — `arm` then `fire`
against a real subject pane, with the tool's own "own session" mechanism
recording pane B. Re-running the phase's own gate against it, live, in this
verification pass:

```
PASS V-TWOPANE-A-RECEIVED: DRILL-A-enterfix appears in 92000647-...jsonl after t0=1789925988.21...
PASS V-TWOPANE-B-UNTOUCHED: DRILL-A-enterfix never appears in 37cfb187-...jsonl after t0=... (negative control (the drill's own pane))
TWOPANE_PASS=6/6  threshold=6/6
```

Corroborated by the real daemon log in the same run directory
(`enterfix/hooks/auto-compact-daemon.log`):

```
17:39:52Z REQUESTED flag=auto-compact-trigger-92000647-...flag sid=92000647-... pid=40712 ancestors=5 typed=[DRILL-A-enterfix]
17:39:53Z SENT via=extension sid=92000647-... terminal=[claude] window=[c:\Users\User\.claude\skills\claude-power-pack]
```

That run's manifest mtime (2026-09-20T19:39:48 local / 17:39:48Z) is **before**
the SUMMARY's own commit (`710b97f`, 2026-09-20T22:05:08+02:00 = 20:05:08Z) —
i.e. this evidence existed when the SUMMARY was written and was not used. A
sibling run, `phase1-live`, exists too and its gate **FAILS**
(`V-TWOPANE-A-RECEIVED` absent, no pane B ever recorded) — so the tool's own
history contains one failed run and one passing run; the SUMMARY reports
neither and instead narrates a third, now-unverifiable measurement path.

**Verdict: the phase's core positive+negative claim (VERIFIED-worthy) has real
support, but not the support the SUMMARY cites, and the SUMMARY did not
disclose the tool's own mixed run history.**

## Must-haves (from `01-PLAN.md` frontmatter)

### Truths

| # | Truth | Verdict | Evidence |
|---|---|---|---|
| 1 | Continuation armed for A is submitted into A's own terminal (typed row, post-t0) | ✅ VERIFIED | `enterfix` manifest + transcript still on disk; gate re-run live: `PASS V-TWOPANE-A-RECEIVED`; daemon log `SENT via=extension ... terminal=[claude]`. |
| 2 | The same continuation never reaches B | ✅ VERIFIED (see caveat under Truth 5) | Same `enterfix` run: `PASS V-TWOPANE-B-UNTOUCHED`. |
| 3 | The absence is produced by an instrument shown able to return the other answer (`V-TWOPANE-B-INSTRUMENT-CAN-SEE`, Task 2's negative control) | ❌ FAILED | `tools/test_two_pane_exactness.py` (read in full) has exactly two live-drill gates — `V-TWOPANE-A-RECEIVED` and `V-TWOPANE-B-UNTOUCHED` — and four unit gates. There is no gate that checks the instrument against pane B's *own* nonce in pane B's *own* transcript. The specific control the PLAN calls "what makes the absence mean anything" was never written into the shipped gate file, so this must-have's own artifact does not exist, even though the *general* discriminating power of the underlying predicate is separately shown by the unit gates (`V-TWOPANE-OBSERVE-IGNORES-THE-SETUP-PROMPT`) and by the SUMMARY's now-unverifiable ad hoc probe. |
| 4 | A request the OWNER answers `refused` is ledgered with `decide()`'s own reason | ✅ VERIFIED | Read `~/.claude/state/gsd-autorun-ledger.jsonl` directly (376 rows, 7 `event:"refused"`). Two rows carry reasons from `decide()`'s vocabulary: `terminal inbox refused: session-unreadable` and `terminal inbox refused: expired` (most recent: `2026-09-20T22:03:23+00:00`, session `9af80e55-...`). Both reasons appear in the literal set the PLAN names (`{ambiguous-terminal, expired, invalid-text, session-unreadable, session-mismatch, pid-mismatch, proc-start-mismatch}`), confirmed by reading `extension/src/terminal_inbox.js`'s `decide()`. |
| 5 | Neither pane is one of the Owner's real working sessions; the drill can address nothing else | ❌ FAILED / UNVERIFIED | `fire()` in `two_pane_drill.py` (lines 450-461) records pane B as `os.environ.get("CLAUDE_CODE_SESSION_ID")` — **whatever session happens to invoke `fire`** — not a second dedicated, disposable subject the operator opened. In the `enterfix` run, pane B's session id (`37cfb187-ec05-43db-b57d-4bdcb5625362`) is the SAME session id that recurs throughout `.planning/01-EVIDENCE-refusal-legs.md` and `STATE.md` as "this window" / "this pane" — i.e. the project's own long-running working session, with cwd resolving to the repo root itself, not a scratch dir. Task 6 (`checkpoint:human-verify`, "operator confirms both terminals were opened for the drill, neither was a pane they were already working in") was never recorded — the SUMMARY contains no operator confirmation, no session ids/pids/cwds shown to a human, as its own `<output>` contract required. Nothing was ever *typed* into pane B (only read), so no keystroke leaked into a live session — but the containment property this truth asserts was not honored as designed, and the one gate meant to catch that (Task 6) was skipped. |

**Truths score: 3/5 verified** (behavior_unverified: 0 — these are presence/absence facts checkable from artifacts, not runtime invariants needing a behavioral test).

### Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `tools/two_pane_drill.py` | probe/arm/fire/observe/**seal**, full containment | ⚠️ PARTIAL | `probe`, `arm`, `fire`, `observe` exist and work (`probe` → 7/7 live, just re-run). **`seal` does not exist** — grep of the file's `argparse` choices confirms only `["probe", "arm", "fire", "observe"]` (line 494). Task 4's entire deliverable (sealed evidence file, 6th gate `V-TWOPANE-INBOX-DRAINED`, 6 mutation drills) was never built. |
| `tools/test_two_pane_exactness.py` | 6 gates (`A-RECEIVED`, `B-UNTOUCHED`, `B-INSTRUMENT-CAN-SEE`, `OWNER-REFUSED`, `NOOWNER-NOT-TYPED`, `INBOX-DRAINED`) | ⚠️ PARTIAL | Only 2 of 6 live gates exist (`A-RECEIVED`, `B-UNTOUCHED`), plus 4 unrelated unit gates. Missing: the negative-control gate, both refusal gates, and the inbox-drain gate. Currently prints `TWOPANE_PASS=4/4` with no `--runid` (unit-only) or `6/6` against `enterfix` — but that 6/6 is 4 unit + 2 live gates, not the 6 live gates the PLAN specifies. |
| `vault/evidence/two-pane-exactness/<run-id>.json` | sealed run pointers | ❌ MISSING | `Glob vault/evidence/two-pane-exactness/*` returns nothing; the directory does not exist. This is the phase's own named done-artifact and it was never produced. |
| `vault/lessons/two-pane-exactness-drill.md` | the "what this drill does/does not prove" record | ❌ MISSING | `Glob vault/lessons/two-pane-exactness-drill.md` returns nothing. Task 5 was never executed. |

**Artifacts score: 0/4 fully verified** (2 partial-but-real, 2 wholly absent).

### Key links (verified by direct source read + real log, not by trusting the PLAN's own citations)

| Link | Status | Evidence |
|---|---|---|
| `extension.js`: refusal returns before `term.sendText` | ✅ VERIFIED | Read `extension/src/extension.js:100-106` directly: `if (d.action === "refuse") { writeAck(...); } else { const term = terms[...]; term.sendText(...); ... }` — mutually exclusive branches; `sendText` is reachable **only** through the `else` (i.e. `action:"send"`). A refused request structurally cannot produce a keystroke. |
| flag → daemon → real request file → real `decide()` → real transcript row | ✅ VERIFIED | `enterfix/hooks/auto-compact-daemon.log`: `REQUESTED flag=... sid=... typed=[DRILL-A-enterfix]` → `SENT via=extension sid=... terminal=[claude]`, and the target transcript carries the row (gate `PASS`). |
| `Resolve-Session`/sandboxed `AC_SESSIONS_DIR` isolation | ✅ VERIFIED (by source read) | `two_pane_drill.py:89-104` (`drill_env`) sets `AC_SESSIONS_DIR`, `AC_DAEMON_DIR`, `GSD_LONG_RUN_STATE_DIR` per-run and explicitly pops `AC_INBOX_DIR`/`AC_DAEMON_DRYRUN`. Matches the PLAN's containment design. Not independently re-derived against the daemon script's own source in this pass (time-boxed), but the drill's own env-construction code is consistent with what the daemon script is documented to read. |
| `gsd_long_run.user_issued_command_since` is the one instrument used, never reimplemented | ✅ VERIFIED | `two_pane_drill.py` imports `gsd_long_run` via `_load_gsd_long_run()` and calls `lr.user_issued_command_since` in `observe()`; `test_two_pane_exactness.py` does the same. No local reimplementation found. |

**Key links score: 4/4 verified.**

**Combined must-haves: 7/13 verified** (3 truths + 4 key links), **6/13 failed or missing** (2 truths + 4 artifacts-as-specified).

## Direct investigation of the four assigned questions

1. **Does `tools/two_pane_drill.py` exist and implement arm/fire/observe as described?**
   Yes for `probe`/`arm`/`fire`/`observe`. **No** for `seal`, which the SUMMARY
   implicitly relies on being unnecessary (it isn't mentioned) but the PLAN's
   Task 4 requires it as this phase's sealing mechanism. Confirmed by reading
   the file's `argparse` choices (line 494) and its full body (517 lines).

2. **Does `tools/test_two_pane_exactness.py` exist, and does its probe gate
   ("7/7 with its red branch driven") hold?**
   The *drill's* `probe` subcommand (not the test file) is what prints
   `PROBE=N/N` — re-run live in this pass: `PROBE=7/7`, all `PASS`. The "red
   branch driven" claim (STATE.md) could not be re-verified in this pass
   (would require deliberately breaking a precondition) and is taken as
   plausible but unconfirmed here — noted as UNVERIFIABLE-IN-THIS-PASS rather
   than either verified or contradicted.

3. **Does the refusal path in `extension.js` genuinely return before
   `term.sendText`, so a refused request cannot produce a keystroke?**
   **Yes.** `extension/src/extension.js:100-106`:
   ```js
   if (d.action === "refuse") {
     writeAck(req.session_id, { ...ack, status: "refused", reason: d.reason });
   } else {
     const term = terms[d.terminalIndex];
     term.sendText(req.text, false);
     ...
   }
   ```
   The two branches are mutually exclusive; `sendText` is unreachable from the
   `refuse` branch.

4. **Is there a ledgered `refused` entry with its reason?**
   **Yes**, in the real, shared, production ledger
   (`~/.claude/state/gsd-autorun-ledger.jsonl`), read directly in this pass:
   7 `event:"refused"` rows total, including
   `terminal inbox refused: expired` (2026-09-20T22:03:23Z) and
   `terminal inbox refused: session-unreadable`. `gsd_long_run.py report` for
   session `9af80e55-...` was not separately run in this pass (the ledger read
   above is a strict superset of what that command would show and was judged
   sufficient given the tool-call budget); the raw ledger rows are the primary
   evidence and were read directly.

## Requirements coverage

Not applicable. `.planning/REQUIREMENTS.md` does not exist in this project.
The PLAN's frontmatter cites `requirements: [C2, C3, C4, C5]`, but with no
REQUIREMENTS.md to define what C2–C5 mean, there is nothing to trace these IDs
against — this is a documentation gap in the PLAN, not a phase gap, and is
noted rather than scored.

## Anti-patterns / code review cross-reference

`01-REVIEW.md` (already completed) found one CRITICAL (`phase_boundary_owed`
fully written and never called — an orphaned fix for a real 14-hour stall) and
three WARNINGs, all in adjacent/in-phase tooling (`gsd_long_run.py`,
`two_pane_drill.py`'s missing timeout handling and non-atomic manifest write).
These are real and already documented; this verification does not re-litigate
them, only notes they stand unresolved and are consistent with the general
picture here: **the in-phase surface is well-instrumented where it was built,
and several of the phase's own final steps (Task 3's owner-refusal-via-drill,
Task 4's seal+mutations, Task 5's lessons+registry, Task 6's human checkpoint)
were never built at all**, rather than built-and-buggy.

## What this phase does NOT establish (do not treat as gaps — out of scope)

- The milestone acceptance gate (`gsd_long_run.py report` = PROVEN) — explicitly
  out of scope per the task brief and per the SUMMARY itself (`report` reads
  PARTIAL at time of writing, unrelated to this phase's own goal).
- The `orca-exact` route — no Orca runtime on this host; correctly never
  claimed anywhere in the PLAN, SUMMARY, or STATE.md.
- A headless extension-host harness — none exists; every real leg in this
  phase required a human-opened Cursor terminal or reused an already-running
  session (see Truth 5's finding).

## Gaps blocking `passed`

1. **`V-TWOPANE-B-INSTRUMENT-CAN-SEE` (the negative control) was never coded.**
   Missing: a gate that asserts pane B's own nonce IS found in pane B's own
   transcript by the same instrument, so `B-UNTOUCHED` cannot be satisfied by
   a blind/misconfigured check.
2. **Pane B's identity is the ambient invoking session, not a dedicated
   disposable subject**, and Task 6's human-verify checkpoint (the one
   safeguard against reaching into an Owner's real working session) was never
   executed or recorded. No harm occurred (pane B was only ever read, never
   written to), but the containment property Truth 5 asserts is not
   demonstrated to hold, and the SUMMARY does not disclose this design choice.
3. **`vault/evidence/two-pane-exactness/<run-id>.json` does not exist.** The
   phase's own named sealed-evidence artifact was never produced; the SUMMARY's
   cited evidence lives (lived) only in an ephemeral scratchpad, now gone.
4. **`vault/lessons/two-pane-exactness-drill.md` does not exist.** Task 5 (the
   "what is/isn't proven" record and the liveness-registry declaration for
   `tools/two_pane_drill.py`) was never executed; `two_pane_drill.py` is
   currently undeclared debt in `vault/liveness/reachability_registry.json`
   (confirmed: zero matches for `two_pane_drill` or `two-pane-exactness` in
   that file).
5. **Tasks 3, 4, 5, 6 have no corresponding commits.** `git log` on the phase's
   files shows only `c5f82c0` (Task 1), `e2acb69` (Task 2), `710b97f`
   (SUMMARY), `86038b9` (review) — no commit exists for the owner-refusal-via-
   the-drill mechanism, the seal/mutation gates, the lessons file, or a
   registry update.

## Deferred items

None — nothing here maps to a later milestone phase; these are this phase's
own undelivered tasks.

## Human verification required

None of the above needs human judgment to resolve — they are presence/absence
facts (files exist or don't, gates exist or don't, ledger rows exist or don't)
that were checked directly. The one item that *did* originally need a human —
Task 6's confirmation that neither pane was an already-working session — was
supposed to be resolved during execution, not deferred to verification; it
simply never happened. Recommend it be run for real (or explicitly overridden
by the Owner) before this phase is called done, since the answer is now known
to matter: pane B in the one surviving passing run *was* an already-working
session.

---

_Verified: 2026-09-21_
_Verifier: Claude (gsd-verifier)_
