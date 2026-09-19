# Phase 4 — Reap the stale autorun markers

**Status:** planned 2026-09-19, session `37cfb187`.
**Files in scope:** `tools/gsd_long_run.py`, `tools/gsd_autorun_marker.py`,
`tools/test_gsd_long_run.py`. Out of scope: the daemon, the watchdog, the
transport.

## The roadmap's premise is false as written, and the measurement is the finding

ROADMAP Phase 4 says *"Seven markers are armed for sessions that no longer
exist."* Measured before touching anything, against nine armed markers:

| instrument | verdict |
|---|---|
| the sweep's own rule (transcript missing, or file mtime idle > `DEAD_HOURS`=48) | **reap 0 of 9** |
| session registry `~/.claude/sessions/<pid>.json` + pid alive | 4 of 9 named by a live `claude` process |
| the transcript's own newest timestamped row | 0 of 9 silent longer than 48 h |

Nothing is reapable today, and the reason is not that the markers are healthy —
it is that **every instrument the reap path could use is a proxy that other
events move.** So the phase's deliverable is the instrument, not a purge: the
reap rule is made to measure the session, and the run that produces no reaps
says so by name.

### D1 — the reap clock is fed by writes that are not the conversation

`sweep()` derives `idle_s` from the transcript's **file mtime**. Transcripts
also carry host metadata rows — `custom-title`, `cost-state` — which carry **no
timestamp at all** and still advance the file's mtime. Measured gap between the
file clock and the conversation clock, per marker:

```
4152e00b  file idle  1.45 h   conversation idle 20.46 h   gap 19.00 h
8178f7d0  file idle  0.25 h   conversation idle 17.31 h   gap 17.06 h
23c962ed  file idle  8.45 h   conversation idle 20.80 h   gap 12.35 h
1024f3b2  file idle  8.45 h   conversation idle 19.15 h   gap 10.69 h
a64ed52e  file idle 24.91 h   conversation idle 33.83 h   gap  8.93 h
```

Up to **19 hours** of a 48-hour clock can be consumed by writes the session did
not make. At today's readings the two clocks agree on the verdict (0 reaps
either way), so this is a defect in the instrument and not yet in the verdict —
stated that way deliberately.

### D2 — registry absence is not death

The obvious second instrument is the session registry. It has false negatives on
live sessions: at 11:40 `fa6961b6` had **no registry row** while its transcript's
last row was a `user` row written **0.00 h earlier** in KobiiSports Resort. 25
`claude` processes against 24 registry rows; the one process without a row was a
`--chrome-native-host` helper, so the gap was not explained by that.

Re-measured at 12:52 the same session reads `live` — a row for it was **created
at 12:24 under a different pid (53548, CLI 2.1.278)**, i.e. the pane restarted
and only then registered. That closes the question from both directions: the
registry does not merely omit sessions it has not seen, it acquires them late,
so its silence is a statement about the registry and never about the session.

Therefore liveness has three outcomes and `dead` is never one of them:
`live` (a registry row names the session and its pid is alive) · `unknown`
(no row, unreadable registry, or the pid cannot be queried). Reaping requires
the clock AND `not live`; `unknown` alone never licenses a reap, and `live`
always vetoes one.

### D3 — a marker's `cwd` is stored as the caller typed it

`/cpp-gsd-long` documents `--cwd .` and `write_marker` stores the raw string, so
**8 of 9 markers hold `"."`**. The sweep runs outside the session, in its own
directory, and resolves that `"."` against itself. Two consequences, both live
today:

- `_restore_config(cwd)` would restore **the sweep's own project's**
  `.planning/config.json` in the name of a marker armed elsewhere;
- worse, the *finish* path: `if cmd.startswith("/gsd-autonomous") and cwd and
  Path(cwd).is_dir(): gsd_status(cwd)`. `Path(".").is_dir()` is always true, so
  a single `ALL_COMPLETE` in whatever project the scheduled sweep sits in would
  unlink **every** `cwd: "."` marker and declare eight unrelated runs finished.

This is the identity rule the milestone already turns on (PR-CONT-02, capture
identity at the point of observation): the arming session knows its absolute
directory; the sweep does not, and must not guess.

## Changes

1. **`write_marker`** resolves a non-empty `cwd` to an absolute path at arming
   time. An empty `cwd` stays empty — it means *unknown*, never *here*.
2. **`marker_project(marker)`** in `gsd_long_run.py`: returns an absolute,
   existing directory, or `None`. A relative stored `cwd` returns `None` — the
   eight legacy `"."` markers become unusable for `gsd_status`/`_restore_config`
   rather than silently pointing at the sweep. Both call sites go through it.
3. **`session_idle_seconds(transcript)`**: idle measured from the newest
   timestamped row in a bounded tail; falls back to mtime when the tail holds no
   timestamped row, and the fallback is reported in the ledger row so a reap
   taken on the weaker clock is identifiable afterwards.
4. **`session_liveness(sid)`** → `live` | `unknown`, per D2, fail-open to
   `unknown` on any error (an unreadable registry must not become a licence).
5. **Reap rule**: `(transcript missing) or (session_idle > DEAD_HOURS and
   liveness != "live")`. The ledger row carries `clock`, `idle_h` and
   `liveness`.

## Acceptance

- `python tools/test_gsd_long_run.py` exits 0 with the new `V-GSDLR-REAP-*` and
  `V-GSDLR-PROJECT-*` gates, each red branch driven by a mutation and every
  restore SHA-256 verified.
- A live `sweep --dry-run` reaps nothing and names, per marker, which of the
  three clauses held it — an empty result that can say why it is empty.
- A marker armed after this change carries an absolute `cwd`.
- No existing marker is deleted by this phase: today's measurement says none
  qualifies, and a phase that purges on a rule it just wrote has tested nothing.
