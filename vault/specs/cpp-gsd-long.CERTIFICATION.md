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
| C5 | the resume is delivered to the session that owns it, or to nobody | **PROVEN (refusal side); the positive side is NOT PROVEN live** |
| C6 | a resume counts only when the transcript shows it was submitted | **PROVEN — first ever recorded 2026-09-19 09:30:37** |
| C7 | two crossings, each with a confirmed resume (`report` = PROVEN) | **NOT YET — `report` reads PARTIAL: 3 crossings, 1 confirmed** |

The command's own done-gate is C7. **It is not met at the time of issue**, and
section 6 says exactly what is missing and why.

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
