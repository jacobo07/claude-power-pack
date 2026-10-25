# Incident: red-team breaches of the progress signal and the replay time accounting (2026-10-25)

**Class:** GUARD ASSERTED BY PROSE AND NEVER ATTACKED.
The phase-8 red team attacked all 15 Owner hypotheses with a guard-removed control each. Two were BREACH: the
semantic progress fingerprint can be moved by content-free changes (claim 8), and the replay's headline mission-hours
count is dominated by open missions ended at the pin (claim 12). Neither was repaired in phase 8.

## Symptom

### Claim 8: the progress signal can be gamed

- The fingerprint moves, and `mission_spend.judge` grants a lease renewal, for three content-free changes:
  a root `RESUMPTION_FILE.md`-only edit, a tracked junk file, and an untracked test log (`noise-cases` BREACH,
  GEX44-temp-copy, control fired, negative control quiet).
- Six other noise cases held (amended identical tree, empty commit, gitignored file, mtime only, STATE.md only,
  `.planning` RESUMPTION.md only). Damage is bounded by the authority less the closeout reserve (claim 7) and by
  LEASE_MAX_RENEWALS=20.

### Claim 12: replay is biased by missing telemetry

- An independent recomputation with its own terminal predicate reads 27527.9 h summed against 1695.9 h bounded:
  25831.952 h (1523%) over the bounded figure, because 92 of 148 missions have no terminal row and are ended at
  the pin, not at their last row. flow_replay's own figure (27483.9 h) agrees with the recomputation within 1%.
- A seeded complete ledger reads bias 0; the same ledger with its terminal rows removed reads 9 h.

## Timeline (local time, CEST)

| when | what | instrument |
|---|---|---|
| 2026-10-25 | claim 8 attacked in temp git repos with nine noise cases | `gsd_mission.progress_fingerprint` before and after, `mission_spend.judge` |
| 2026-10-25 | claim 12 attacked by recomputing mission spans on the 6339-row pin | `tools/redteam_s9.py` attack_12 against 07-REPLAY accounting |
| 2026-10-25 | both verdicts recorded and the report regenerated (75b791a3) | `tools/redteam_s9.py run --claims all` |

## Root cause

The fingerprint was specified by what it should ignore (bookkeeping files named in prose) rather than by an
enumerated set of what counts, so a file outside the named bookkeeping set still moves it. The replay headline sums
spans per mission and closes an open mission at the pin; the unobserved tail was disclosed in the report text, but
the figure itself is not bounded. Both are guards asserted in prose and never attacked until this phase.

## Why the existing rule did not prevent it

The gates for both pinned the cases their author listed. Neither had a control that varied the content-free input
or the terminal telemetry against an independent count.

## Earliest discoverable point

The red-team attack itself, runnable at any commit after the fingerprint and the replay existed; no earlier instrument
measured them against an adversary.

## Repair

None in phase 8. Owner: a gap-closure plan (claim 8: fingerprint over an allow-listed content set; claim 12:
headline bounded or labelled per open mission). The breaches are recorded, not hidden.

## Test

- commit: 75b791a3
- gate: V-S9RT-C8-SUBJECT in tools/test_s9_redteam.py
- gate: V-S9RT-C12-SUBJECT in tools/test_s9_redteam.py

## Pattern

A guard asserted by prose and never attacked. Each claim is now attacked with a positive control (guard removed ->
the breach appears) and a quiet negative control, so a repair has an existing failing test to turn green.
