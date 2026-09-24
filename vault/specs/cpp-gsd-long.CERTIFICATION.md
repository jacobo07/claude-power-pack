# /cpp-gsd-long — certification of what works, and what is not proven

**Issued** 2026-09-19 by session `37cfb187` · **tree** `e2acb69`, branch
`feature/knowledge-acquisition` · **host** Windows 11, this estate.

This document exists because the Owner asked for a certificate that the command
works 100 %. A certificate is only worth the measurements behind it, so every
claim below carries the instrument that produced it and the command that
re-derives it. **Two claims are NOT proven and say so.** A document that printed
100 % over them would be the least useful artifact this work could produce.

---

## 0. What "it works" decomposes into

`/cpp-gsd-long` is a chain, and a chain is not certified by its parts. Seven
claims, in the order the run exercises them:

| # | claim | status |
|---|---|---|
| C1 | arming refuses a run it cannot execute | **PROVEN** |
| C2 | the wall is narrowed per session, and the watchdog applies it | **PROVEN** |
| C3 | a crossing checkpoints and asks for `/compact` | **PROVEN** |
| C4 | the compaction is recognised from its post-condition, never a proxy | **PROVEN** |
| C5 | the resume is delivered to the session that owns it, or to nobody | **PROVEN, both sides, live 2026-09-20 (runid `enterfix`). Pane A `92000647` in a terminal the window owns (pid 6992) received AND submitted; pane B `37cfb187` — this session, same window, same `t0` — received nothing. See §9e** |
| C6 | a resume counts only when the transcript shows it was submitted | **PROVEN — first ever recorded 2026-09-19 09:30:37** |
| C7 | two crossings, each with a confirmed resume (`report` = PROVEN) | **PROVEN 2026-09-21T20:54:39Z — `report` reads PROVEN: 4 crossings, 2 confirmed, `window_confirmed 2`. See §10** |

The command's own done-gate is C7. **It was not met at the time of issue** — §6
says what was missing and why, and §10 records the run that closed it. Sections
6 and 9x are left as written: they describe measurements taken on the days they
name, and editing a record of a past run to match the present would fabricate a
verification rather than report one.

---

## 1. Gate results at this tree

```
python tools/test_gsd_long_run.py            GSDLR_PASS=87/87   exit 0
python tools/test_gsd_autocompact.py         GSDAC_PASS=26/26   exit 0
python tools/test_autocompact_per_session.py ACPS_PASS=38/38    exit 0
python tools/test_continuation_wiring.py     CWIRE_PASS=14/14   exit 0
python tools/test_two_pane_exactness.py      TWOPANE_PASS=4/4   exit 0
```

Green is not evidence by itself. Every gate added in this milestone had its red
branch driven by a mutation that removes exactly one fix, with every restore
verified by SHA-256:

| mutation | result |
|---|---|
| resume-not-compact discriminator removed | 62/68, reproducing the production symptom byte-for-byte |
| confirmation aperture back to 256 KB | 71/72 |
| reap clock back to file mtime | 83/87 |
| liveness always `unknown` | 85/87 |
| `marker_project` resolves a relative cwd | 85/87 |
| arming stores the raw cwd | 86/87 |
| a tool result counts as a keystroke | 3/4 |
| every subject looks addressable | 3/4 |
| `observe` counts a mere mention of the nonce | 3/4 |

**Three of those mutations first SURVIVED**, and each survival was a defect in my
own instrument rather than in the subject. They are listed in §7 because a
certificate that hides its instrument failures is describing a different run.

---

## 2. C4 — a compaction is claimed only from its post-condition

A landed compaction requires a host-written `type=system, subtype=compact_boundary`
row newer than the cycle reference. A low context reading is not one: on
2026-09-18 a resumed session read ~17 % and the watchdog called it a compaction
25 hours after the last real one, then had a daemon type `/d1-continue` into
whichever window had focus.

Sealed in `5d17c1e`. One resume per boundary, fenced by
`resume_reference() = max(marker armed_at, boundary_ts of prior resume_requested rows)`.

## 3. C5 — exact-target delivery: what is proven and what is not

**Proven, on real bytes, three ways.**

- *An owned request is answered and refused.* A request whose ancestor chain
  contains a terminal this window owns, naming a `claude_pid` with no
  `~/.claude/sessions/<pid>.json`, was answered in **0.28 s**:
  `status refused, reason session-unreadable`, `window_cwd` this repo.
- *An unowned request is ignored, not typed.* Ancestors = one pid in no process
  table: 15.04 s, no ack, nothing typed. That silence is evidence only because
  the owned leg was answered in the same run — an extension that was not polling
  produces the same result.
- *A real unowned subject is refused by the real daemon.* A live session started
  in Windows Terminal (`21692 claude.exe -> 32340 powershell.exe ->
  54752 WindowsTerminal.exe`): the daemon logged
  `REQUESTED ... ancestors=12 typed=[DRILL-A-phase1-live]`, then
  `REFUSED -- no terminal-inbox provider answered ... foreground fallback disabled`,
  and ledgered it. The old behaviour would have typed that line into whichever
  window had focus.

The negative control was checked **where a keystroke would have landed** — the
Owner's own working pane, which is where the owned leg's ownership resolved: 0
typed rows carrying the probe, against an 801-occurrence positive control proving
the search was not blind.

**NOT PROVEN: the positive side.** No line has ever been observed being typed
INTO a subject's own terminal by this mechanism, with a second pane shown to
receive nothing. It needs a subject session inside a Cursor integrated terminal.
The drill cannot create one, and the attempt to create one unattended — opening
a Cursor window on a folder carrying a `folderOpen` task — was **denied by the
auto-mode classifier** (`Create Unsafe Agents`). That denial is recorded rather
than worked around.

Evidence: `.planning/01-EVIDENCE-refusal-legs.md`, `3e56322`, `e2acb69`.

## 4. C6 — a resume counts only when the transcript shows it

**Proven, and it is the headline measurement of this milestone.** Until
2026-09-19 this estate had never recorded a single `resume_confirmed`. The cause
was an aperture: the confirmation runs in the Stop hook at the end of the turn
the resume began, and that turn has already written its whole tool output ahead
of the row — the `/gsd-autonomous` row sat **598,625 bytes** from the end of a
5.8 MB transcript against a **262,144 byte** window. The coupling is perverse:
the more the turn did, the further back the row, so it failed exactly in the case
it exists for.

Fixed in `f2462ee`. First confirmation ever recorded:

```
crossing  2026-09-18T23:06:01+00:00
confirmed 2026-09-19T09:30:37+00:00
```

Re-derive: `python tools/gsd_long_run.py report --session 37cfb187-...`

## 5. Marker hygiene (Phase 4)

The roadmap asserted seven markers armed for dead sessions. Measured: **zero of
nine** were reapable, and the reason was that every instrument the reap path used
is a proxy other events move.

- The reap clock read the transcript's **file mtime**, which `custom-title` and
  `cost-state` rows advance without the session speaking — measured drift up to
  **19.0 h** on a 48 h threshold.
- The registry answers `live` or `unknown`, **never `dead`**: a session with no
  row was conversing 0.00 h earlier, and acquired a row 44 minutes later under a
  new pid when its pane restarted.
- `cwd` was stored as typed — `"."` in 8 of 9 markers — and `Path(".").is_dir()`
  is true everywhere, so one project reaching `ALL_COMPLETE` would have unlinked
  **every other project's marker** and restored the wrong `.planning/config.json`.

Sealed in `d0477b8`. `sweep --dry-run --explain` now names the clause holding
each kept marker, so an empty sweep is distinguishable from a sweep that judged
nothing. This run's own marker was armed before the change and stored `"."`; it
was absolutised in place, backed up first, every other field preserved.

## 6. What is missing for C7, and why it is not a defect

`report` = PROVEN needs **two crossings each followed by a confirmed resume**.
Current state: 3 crossings, 1 confirmed.

- Crossing 1 (22:39:30) — refused by the 60 s inbox TTL, fixed in `691c09a`.
- Crossing 2 (23:06:01) — **confirmed** 09:30:37.
- Crossing 3 (10:10:22) — the `/compact` landed; the trailing `/gsd-autonomous`
  was not submitted automatically, so no confirmation exists for it.

Every mechanism C7 depends on is now proven individually, including the one that
made confirmation impossible until today. What remains is a fourth crossing with
its resume submitted — produced by the run continuing to consume context, not by
further engineering. Budget at issue: cycle 1 of 12, 24 h from
`2026-09-18T22:08:37Z`. Wall: 35/40/30 (crossing at 40 % used).

**Nobody should read PARTIAL as "the command is broken".** It means the ledger
has not yet seen the second confirmed round trip, and the ledger is the only
authority this project accepts.

## 7. Instrument failures in the work that produced this certificate

Recorded because a certificate whose author hid these is describing a different
run.

1. **A control counted my own tool output as a keystroke.** A tool result is a
   `type: "user"` row, so a script printing the probe string produced a row
   shaped like a typed prompt. It reported a keystroke into the Owner's live
   session that never happened. Rows are now classified by shape.
2. **A mutation survived because a guard was redundant for its fixture.** The
   echoed row carried `content` as `tool_result` blocks, already rejected by the
   shape check. The case that needs the guard is a tool result whose content is a
   plain string.
3. **A gate passed for a reason other than the one it names.** A fixture prompt
   stamped 10:00Z was excluded by the TIME bound, so the text predicate was never
   reached and a mutation making `observe` count a mere mention survived.
4. **An `arm` PASS on a subject nothing could address**, discovered only when
   `fire` spent its 10 s timeout and produced a refusal indistinguishable from the
   one the drill demonstrates deliberately. Addressability is now a precondition.
5. **A `--cwd .` in the command's own documentation** propagated a relative path
   into every marker for months. The documented recipe was the defect.

## 8. How to re-derive every number here

```powershell
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$pp = 'C:\Users\User\.claude\skills\claude-power-pack'
& $py "$pp\tools\test_gsd_long_run.py"
& $py "$pp\tools\test_gsd_autocompact.py"
& $py "$pp\tools\test_autocompact_per_session.py"
& $py "$pp\tools\test_continuation_wiring.py"
& $py "$pp\tools\test_two_pane_exactness.py"
& $py "$pp\tools\gsd_long_run.py" report --session 37cfb187-ec05-43db-b57d-4bdcb5625362
& $py "$pp\tools\gsd_long_run.py" sweep --dry-run --explain
```

## 9b. Two findings AFTER issue (2026-09-20 00:0x, measured before acting)

The certificate was issued at 13:0x on 09-19 expecting C7 to close by itself.
It did not, and the reason is two defects neither the gates nor the ledger's
verdict could show. Both are recorded here rather than in a new document,
because a certificate that does not track its own subject is a snapshot
pretending to be a guarantee.

**F1 — the narrow wall reverted silently, and nothing noticed.** At
`2026-09-19T13:13:00Z` the watchdog read **`used_pct=45.0` against a 40 % wall
and returned `pass`.** It was right to: `~/.claude/state/ctxwd-thresholds-<sid>.json`
no longer existed, so `_thresholds()` fell back to the production constants
(60/70/45), under which 45 passes. The ledger shows why:

```
12:49:36  de7f3c91…  thresholds_cleared
12:49:37  37cfb187…  thresholds_cleared
```

Two sessions one second apart — something iterated the armed markers and cleared
each one. The only production caller of `clear_thresholds()` is the CLI's
`thresholds --clear`; the rest are tests, which redirect the state directory.

The whodunit matters less than the shape: **a run's most important parameter
lived in a sidecar file with no owner, and its disappearance degraded the run
into looking healthy.** `status` reported the run armed, `report` reported
PARTIAL, every gate stayed green, and the wall the run existed to prove was
simply not in force for eleven hours. The wall has been restored (35/40/30,
verified: this session resolves `(35.0, 40.0, 30.0)`, production `(60, 70, 45)`),
and the durable fix is to carry the thresholds **in the marker**, which is the
run's own record, so a lost sidecar cannot widen a wall in silence.

**F2 — a compaction happened and wrote no boundary row.** C4 accepts exactly one
piece of evidence: a host-written `type=system, subtype=compact_boundary` row.
Scanning the whole 10.7 MB transcript, not a tail:

```
2026-09-18T23:07:25.834Z  trigger=manual  pre=465557  post=20445
2026-09-18T23:51:55.273Z  trigger=manual  pre=16911   post=24260
```

**Two rows, both from 09-18.** The crossing-3 compaction of 09-19 ~10:15 — the
one this session visibly came through — produced none, which is why the Stop
chain logged `compaction_unobserved` at 11:06:40 with the 23:51 boundary as the
newest it could find. The reader does not filter on `trigger` (it accepted both
manual rows), and its window is already 8 MB, so this is not the aperture defect
of T-CONT-07 recurring: the row does not exist.

The consequence is precise and it is not "weaken C4". The boundary row is
*sufficient* evidence and the design treats it as *necessary*; when the host
writes none, a correct implementation must refuse to claim a compaction, and
this one did. What that costs is the automatic advance: the fence stays where it
was and the resume is never owed. Relaxing it would reopen the 2026-09-18
incident, where a low reading was read as a compaction 25 hours late. So the
honest statement is that **C4 is sound and incomplete**: it can recognise a
compaction the host records, and it cannot recognise one the host does not.
Whether every compaction path writes that row is now an OPEN question about the
host, not about this code, and it is the first thing to measure next.

## 9c. F3 — the guard that decides the run's survival was never heard (2026-09-20)

F1 explained why a 45 % reading passed a 40 % wall. It did not explain the
silence that followed: after the wall was restored, **the watchdog logged
nothing at all for this session across many ended turns**, so no crossing could
be requested however high the context climbed.

The sibling comparison localised it in one read. The watchdog was alive and
judging — 240 lines that day, including a live session whose transcript is
**53.8 MB** judged in 1995 ms, which also kills the obvious hypothesis that this
session's 11.5 MB transcript had outgrown it. Only this session was missing.

`hook-dispatcher-errors.log` names the cause:

```
10:27:26Z  [Stop-chain] context-watchdog.py   Error: ETIMEDOUT after 20000ms
10:49:12Z  [Stop-chain] ten members reported ETIMEDOUT within 8 ms
```

Ten hooks failing in the same instant is not ten slow hooks; it is **the whole
chain being abandoned at its deadline**, which takes the members that had
already finished with it. One of that chain's members carries a 70,000 ms
timeout.

The dispatcher had met this before and answered by raising the watchdog's
ceiling 6,000 → 20,000 ms, closing the note with the right test: *"Whether that
is enough is now an observable, not an assumption: logs/context-watchdog.log."*
**The observable has answered: it was not.** Raising moved the cliff, which is
what this estate's own doctrine predicts — the fix is scheduling, not budget.

So the hook is now in the Stop chain's **critical lane**, which runs before the
pool opens, uncontended, alongside the dead-screen guard. The counter-argument
in the note it replaces was real and was measured rather than dismissed: the
lane runs sequentially on every turn, so the ordinary path is what matters.
Timed alone against the 11.5 MB transcript at 3.5 GB free, n=5: 463 / 1183 /
1523 / 3037 / 6823 ms, **median 1523**. The lane totals about 3 s per turn end,
against a measured alternative of the run stalling for eleven hours with every
gate green.

This is the third instance in this estate of one shape, and it is worth naming
plainly: **a guard that runs, is correct, and cannot be heard is
indistinguishable from one that approved.** Here the silence was read for
eleven hours as "the run is fine".

## 9d. 2026-09-20, later — one premise retracted, one defect closed, one opened

**F2 IS RETRACTED. The host DOES write `compact_boundary`.** §9b recorded "a
compaction happened and wrote no boundary row" as an open question about the
host. Measured today on this transcript: **three** boundary rows exist
(2026-09-18T23:07:25Z, 2026-09-18T23:51:55Z, 2026-09-20T12:43:08Z). The single
`compaction_unobserved` row was a compaction that **never happened** — the
`/compact` line was never submitted — not a row the host failed to write. C4
needs no weakening and none was applied. What remains from F2 is a delivery
question, which is F5 below.

**F4 — the advisory took the Stop the run was standing on. CLOSED, `15bcdbe`.**
`_run_inner` opened with `overlay = _orchestrator_overlay(event); if overlay:
return overlay`, and the whole continuation mechanism lives below that line:
the used_pct stamp, the endpoint refresh, the resume confirmation, the rearm,
the post-compaction resume, the snapshot, the crossing and the `/compact`
instruction. The overlay is once-per-session, so it cost one Stop — but it
fires on CONTEXT PRESSURE, the same condition that produces a crossing, so the
one Stop it could take was the one most likely to matter. Its signature in
`logs/context-watchdog.log` is `used_pct=?`, because `_LAST["used_pct"]` is
stamped just past the early return. Armed runs now keep the path; unarmed
sessions are unchanged; the advisory is layered on and still surfaces.
`tools/test_watchdog_overlay_precedence.py` 4/4 both poles, mutation 3/4 red on
its own assertion, restore SHA-256 verified.

**F5 — delivery is not submission. OPEN, and it is what blocks C7.** At
13:11–13:13 this run re-entered itself with **no human input**:
`resume_requested` → `resume_dispatched` → terminal-inbox ack `status:"sent"`,
`terminal:"claude"`, `window_cwd` = this project. `/gsd-autonomous` then
executed. But **no user row records the submission**, so C6's oracle
(`user_issued_command_since`) reads False and `resume_confirmed` cannot fire.
On 2026-09-19 the identical flow left `type=user, isMeta=True, list['text']` at
09:08:06.552Z and confirmed — which is the only reason C6 is marked PROVEN at
all. Excluded by measurement: late flush (two further turns closed, transcript
grew to 14.7 MB, still absent), the 8 MB window (the row would sit at ~14.0 MB
of 14.7), and the time bound (removing it changes nothing). Control: the
Owner's own typed messages that day ARE recorded. Two readings remain — the
host did not record this delivery, or it reached the model by a path that
produces no user row — and the archaeology cannot separate them.

**The oracle was NOT weakened to close this.** The outcome the milestone is
about did occur — three commits (`15bcdbe`, `ba540f2`, `27a7094`) landed and
were pushed AFTER the 12:43 boundary with zero human continuation input, which
is meaningful post-boundary work by any reading. But "the mechanism-specific
oracle missed a real success" is a reason to add a second observable, not a
licence to lower the first. The next watchdog-initiated crossing is to be
watched live end to end; that observation separates the two readings.

**Also note what this cycle does NOT support.** The 12:43 compaction was run by
the Owner, so this cycle cannot count toward C7 however well the rungs after it
behaved. A crossing the Owner triggered is not a crossing the run produced.

## 9e. 2026-09-20, evening — C5 closed live, and my own F5 fix measured WRONG

**C5 IS NOW PROVEN ON BOTH SIDES, live.** runid `enterfix`. A disposable
subject was opened in a Cursor terminal this window owns; `arm` latched it by
NONCE (`DRILL-A-enterfix`), and its addressability precondition passed rather
than being discovered later by `fire`:

    arm/A: addressable -- c--Users-User--claude-skills-claude-power-pack.json
           owns terminal pid 6992
    PASS arm/A: session=92000647-be77-4e2d-86c6-64b5fbea495e pid=40712

`fire` delivered through the inbox with no focus change, and both halves were
judged from one `t0`:

| pane | role | result |
|---|---|---|
| A `92000647`, terminal pid 6992 | subject | received AND submitted |
| B `37cfb187`, this session, same window | negative control | untouched |

`tools/test_two_pane_exactness.py --runid enterfix` = **6/6**, including
`V-TWOPANE-A-RECEIVED` and `V-TWOPANE-B-UNTOUCHED`. Pane B matters more than
the earlier 33-pane sweep: it is precisely the pane a mis-resolved request
would reach. The old framing — "the positive leg needs an operator to open a
second window" — was true only of opening the pane; everything after it ran
unattended.

**A RETRACTED MEASUREMENT, recorded because it nearly became a finding.**
The first attempt to test `0c7f304`'s second Enter used `/help` as the slash
subject and read:

| payload | ack | `user_issued_command_since` |
|---|---|---|
| `ping-control-<rand>` (plain) | `status:"sent"`, `enters: 2` | True |
| `/help` (slash) | `status:"sent"`, `enters: 2` | **False** |

and was about to be written up as "the fix is insufficient". It is not
evidence. **`/help` is a CLIENT-SIDE command: it submits and writes no
transcript row**, so a perfect delivery reads False. The measurement was of
the oracle's aperture, not of the transport — the same class of error this
certificate documents elsewhere, committed by the instrument built to find it.

What caught it was not an instrument. Pane A was left in `status: waiting` —
the only one of 24 live sessions, against 14 idle and 9 busy — and two
incompatible readings fitted that equally well: a stuck completion menu with
both Enters eaten, or the help screen after a successful submit. Nothing
reachable from outside the pane separates them, so the Owner was asked to look
at the pane and answered: **the help screen**. The delivery had worked.

Two things follow, and both are worth more than the retracted claim:

1. **Choose a slash subject with a postcondition the oracle can see.** The
   re-test uses `/compact`, whose postcondition is a host-written
   `compact_boundary` row — C4's own predicate, independent of any user row —
   and which is also the command that actually failed in the live run.
2. **`enters: 2` in the ack is confirmed genuine.** The extension host had been
   restarted and the new code is what ran, so whatever the re-test says, it is
   a statement about the current build.

`test_inbox_delivery_enter.py` remains 5/5 and remains STRUCTURAL: it asserts
shipped source and copy identity and its own docstring says it cannot see
submission. That is why 5/5 was never allowed to close F5.

**F5 IS CLOSED. The second Enter works, proven against the real command.**
Re-tested with `/compact` rather than `/help`, judged by the host's own
postcondition:

    pane A status=idle   compact_boundary rows BEFORE: 0
    delivered '/compact'
    ack {"status":"sent","terminal":"claude","enters":2}
    compact_boundary rows AFTER: 1
    V-COMPACT-SUBMITS: PASS -- a real compaction happened in pane A
                              (2026-09-20T18:25:26.869Z)

So the Owner's original diagnosis, made from looking at the pane, was correct
on the first attempt: the slash-command completion popup consumes the first
Enter and a second one submits. Every model I reached by measurement was
wrong — host-queues-input, then a stale readiness row — and both were
retracted above. **The fix that survived came from an observation of the
running product, not from the archaeology.**

The delivery mechanism is therefore complete end to end: the request reaches
the pane that owns the session and no other (C5, 6/6 live), and the line it
carries is really submitted (this section). What remains for C7 is not the
transport.

**F6 — a submitted `/compact` can fail with EBUSY, and that is probably what
`compaction_unobserved` has always been.** The fix above was then exercised on
the REAL session, and the delivery worked: the line was typed and submitted,
and `/compact` ran. The compaction itself failed:

    Error during compaction: EBUSY: resource busy or locked, open
    '\\?\C:\Users\User\.claude\projects\...\37cfb187-....jsonl'

Measured immediately afterwards: nothing held the file — an exclusive
`ReadWrite/None` open succeeded — so the lock was TRANSIENT and contemporaneous
with the submission. The mechanism is specific. A compaction rewrites the
transcript, and on Windows a rename/replace fails while any open handle lacks
`FILE_SHARE_DELETE`, which CPython's default `open()` does not request. The
delivery lands at TURN END, which is exactly when the Stop chain runs its six
unconditional transcript-scaling members (`lazarus-snapshot`,
`mark-live-session`, `research-intent-detector`, `session_snapshot_stop`,
`output_contract_stop`, `ceps_promote_stop`), and `session-snapshot.py` was
observed alive at the time.

So a PP hook reading the transcript can block the host from compacting it, and
the observable is a `/compact` that was genuinely submitted and produced no
boundary row. **That is the signature this certificate previously recorded as
"a compaction that never happened" (§9d, the 2026-09-19
`compaction_unobserved`).** That earlier reading said the line was never
submitted; this one says it was submitted and the rewrite was refused. The
second fits the evidence better and is now the leading explanation, though the
09-19 event itself cannot be re-measured. C4 is unaffected either way: it
requires a boundary row and correctly reported its absence both times.

This is an own-goal of the same family as the rest of the day: the estate's own
instruments are part of the system under test, and here they are plausibly
preventing the very effect the run is trying to produce.

**One claim examined and dropped rather than recorded.** A pane sitting in
`status: waiting` defers every delivery, which looked like a silent deadlock
for an unattended run. It is not: `decide` refuses a request as `expired`
past its `ttl_ms`, the daemon tracks `pending`/`deferred`, and a request that
never becomes deliverable is promoted to `auto-compact-refused-<sid>.flag`
with a `refused` ledger row naming the reason. The behaviour is correct and
instrumented. It is recorded here only because it was nearly written up as a
defect, and the thing that stopped it was reading the daemon rather than
reasoning about it.

One instrument failure of mine in the same run, caught by its own three-outcome
design rather than by inspection: the first slash attempt reported
HARNESS-FAILED because pane A was still busy ANSWERING the control delivery I
had just sent it, and my 120 s idle wait expired. A two-outcome harness would
have recorded that as "the slash command failed to submit" — the right answer
for the wrong reason, which is worse than a red.

**So F5 stays OPEN and C7 stays blocked on it.** What is now known that was not
this morning: the transport reaches the right pane and only the right pane
(C5), the failure is specific to lines beginning `/`, and the number of Enters
is not the variable.

## 9. The honest summary

The machinery of `/cpp-gsd-long` is proven part by part, and two of its three
historical failure modes were closed today with their red branches driven: the
sweep re-typing `/compact` instead of the resume (`64ec155`), and the
confirmation that could not see the row it looks for (`f2462ee`). The third —
delivery into the wrong window — is closed on its refusal side with live
evidence, and its positive side has never been observed.

So: **not 100 %.** Five of seven claims proven, one proven on one side, one
pending a fourth crossing that the run produces by running. Anyone who needs the
missing two can get them with one action each: open a Claude session in a Cursor
integrated terminal (C5 positive), and let this run cross its wall once more
(C7).

---

## 10. C7 CLOSED — 2026-09-21T20:54:39Z, session `9af80e55`

§9 above is the state at issue and stays as written. This section supersedes its
verdict on C7 only.

`report --session 9af80e55-9865-4c6f-877c-d155da18becf`:

```
"verdict": "PROVEN", "crossings": 4, "confirmed": 2,
"proven_window": 2, "window_confirmed": 2
```

| crossing | resume confirmed |
|---|---|
| 2026-09-21T18:52:03Z | 2026-09-21T18:56:24Z · `/gsd-autonomous` |
| 2026-09-21T20:48:26Z | 2026-09-21T20:54:39Z · `/gsd-autonomous` |

**What the fourth cycle actually was**, because the shape of it is the claim:
the watchdog crossed the narrowed wall, the turn emitted one `/compact` line and
did no further tool work (the rule §9d bought with a nine-hour deadlock), the
terminal inbox typed it into this session's own pane, the compaction landed, the
Stop chain asked for `/gsd-autonomous`, the inbox typed that too, and the run
re-entered itself and carried on. No human keystroke is in that sequence.

**F5 — "delivery is not submission" — is therefore CLOSED**, and it was closed by
`64ec155` + `f2462ee` rather than by anything in this session: both confirmed
cycles ran on that code. §9d's `OPEN` describes 09-20 and remains true of 09-20.

**The confirmation was written by the hook, not by the agent.** Before the turn
that produced it ended, the preconditions of `_confirm_resume`
(`context-watchdog.py:800`) were probed read-only with the hook's own predicate:
`marker_present=True`, `done_flag_exists=True`, `confirmed_flag_set=False`,
`user_issued_command_since('/gsd-autonomous')=True`, and the control
`'/this-was-never-typed'=False` — the predicate was shown able to answer both
ways before its answer was believed. The probe wrote nothing. The ledger row
that followed is the hook's.

**Superseded as the default path on 2026-09-24 — see §11.** The claims above certify the
keystroke compact-and-resume mechanism and remain true of it.

**Still not proven, and unchanged by any of this:** C5's positive side beyond the
09-20 `enterfix` observation, and F6 (a submitted `/compact` failing with EBUSY)
remains an open hypothesis rather than a closed cause. Four of this session's
crossings, two are unconfirmed and both have a recorded reason — 09-20T21:56 has
none beyond the run being abandoned, and 18:11:46 is the 310 s refusal. Neither
was silently dropped from the count: `crossings 4` is reported beside
`confirmed 2`, and the window that matters is the last two.

---

## 11. Mission continuity (v3, Ralph) — certifies the MISSION, not one mechanism

Owner decision 2026-09-23: a run continues in a fresh session at its wall. Spec
`vault/specs/mission-continuity.md`; evidence `.planning/mission-continuity/W0-EVIDENCE.md`.

| # | claim | status |
|---|---|---|
| M1 | prepared is not running: only the launched worker's ack, or the host listing the id printed for that launch, makes RUNNING | **PROVEN** — unit + live (adopted 23:57:29, 00:15:50) |
| M2 | the wall is judged mid-turn and asks for a tool-free hand-off | **PROVEN live** — flag 00:32:00, worker stopped at f23 with a HANDOFF NOTE |
| M3 | a successor in a fresh process continues exactly, carrying the note | **PROVEN live** — relay 00:41:25, f24.. by the successor only, 0 dupes (E24) |
| M4 | a crashed busy background worker is never replaced beside its host restart | **PROVEN** — measured E14/E15, pinned V-MC-BG-KILLED-* with a mutation |
| M5 | a halt stops its workers; duplicate supervisors launch one worker | **PROVEN** — unit + mutation (race 1 winner / 5 losers) |
| M6 | a real `/gsd-autonomous` run crosses ≥ 2 relays and completes | **PROVEN LIVE 2026-09-24 (relay criteria); run stopped by the Owner before it ended on its own.** The halt path on a real run was exercised by the Owner's stop (E34: HALTED, worker reaped, nothing left running) and on budget in W8 (E25). The COMPLETED path (GSD ALL_COMPLETE) is proven by gates only (V-MC-SUP-COMPLETE-NO-LAUNCH, V-MC-SUP-REPLACE-ASKS-GSD-FIRST), never on a real run. Prior status: 2 relays (11:32:49, 14:48:20), 3 workers each committing on `gsd-autonomous-run` (w1 phase 1 + phase-2 planning, w2 phases 2–4, w3 phase 4 close + phase 5 plan), no phase redone, one writer at a time (W0-EVIDENCE E26–E33). Found and fixed live: the run moving into a git worktree (`582db71`) and the relay held by a 45 s GSD ceiling (`8b979bb`). Not yet observed: the mission ENDING (COMPLETED or HALTED on budget). Superseded text follows. **NOT PROVEN — RUN IN FLIGHT.** Blocker removed: Owner chose `auto` (default since `18c7299`). Mission `m-7f6d988e3c93` armed 2026-09-24 09:49Z on the trusted `gsd-long-smoke` canary (1/8 phases, HEAD `4f09667`), worker 1 `f3c0b67e` adopted 09:54Z, budget 5 iterations / 8 h. Passes only on: ≥ 2 relays, roadmap strictly advancing with no phase redone, commits from ≥ 3 workers, never two workers at once, ending COMPLETED or HALTED-on-budget. Result replaces this cell. |
| M7 | Windows | the tested host throughout |

Gates: `tools/test_gsd_mission.py` 76/76 · `tools/test_mission_watchdog.py` 12/12 ·
`node tools/test_hub_mission_start.js` 8/8 · `node tools/test_mission_wall.js` 7/7.