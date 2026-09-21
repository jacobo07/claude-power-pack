---
status: passed
phase: 04-reap-the-stale-autorun-markers
date: 2026-09-21
must_haves_verified: 8
must_haves_total: 8
requirements: n/a (no REQUIREMENTS.md in this project)
verified_by: orchestrator (direct measurement, not delegated)
gap_closure: G1 closed 2026-09-21 in c3b493b — see "Gap closure" at the end
---

# Phase 4: Reap the stale autorun markers — Verification Report

> **Superseded in part, 2026-09-21.** This report was written at `gaps_found`
> 7/8. G1 was then fixed in `c3b493b` and re-measured against the live estate,
> so the frontmatter now reads `passed` 8/8. **The body below is left exactly as
> it was written.** It describes the run that happened, and editing a
> verification's findings to match a later repair would fabricate a verification.
> What changed is recorded at the end, with its own date and commit.

Verified by running the subject, not by reading its SUMMARY — this phase has no
SUMMARY, and its plan lives at `.planning/04-PLAN.md` rather than in a phase
directory, which is why every index reported `no_directory` for it.

## Where the artifacts actually are

| artifact | location | note |
|---|---|---|
| plan | `.planning/04-PLAN.md` | at the planning ROOT, not `phases/04-*/` |
| implementation | `d0477b8` (2026-09-19) | `gsd_autorun_marker.py`, `gsd_long_run.py`, `test_gsd_long_run.py` |
| summary | — | none was ever written |
| this report | `phases/04-.../04-VERIFICATION.md` | placed by convention, away from its own plan |

## Must-haves

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | `test_gsd_long_run.py` exits 0 with the new `V-GSDLR-REAP-*` / `V-GSDLR-PROJECT-*` gates | **VERIFIED** | Run 2026-09-21: `GSDLR_PASS=93/93 threshold=93/93`, exit 0. Gates observed by name: `REAP-SILENT-AND-NOT-LIVE`, `REAP-MISSING-TRANSCRIPT-STILL-REAPS`, `REAP-LEDGERS-ITS-INSTRUMENT`, `PROJECT-ABSOLUTE-RESOLVES`, `PROJECT-REFUSES-RELATIVE`. 93 ≥ the 87 the phase claimed. |
| 2 | Each red branch driven by a mutation, restores SHA-256 verified | **UNVERIFIABLE** | A historical claim about runs on 2026-09-19. No mutation log persists. The gates exist and pass; that they were once driven red cannot be re-derived today. Not a failure — an absent record. |
| 3 | A live `sweep --dry-run` reaps nothing | **VERIFIED** | Run 2026-09-21 against the 8 real marker files: zero `reaped` actions, zero `config` restore actions. |
| 4 | …and names, per marker, which clause held it | **GAP — see G1** | 6 `kept` rows, each naming its clause (`"spoke 16.53 h ago (< 48 h)"`) with `clock` and `liveness`. But 8 files match the sweep's own glob. |
| 5 | The reap clock reads the session's newest timestamped row, not the transcript's file mtime | **VERIFIED** | `session_idle_seconds` called from `reap_decision` at `gsd_long_run.py:881`; live sweep output carries `"clock": "conversation"` on every row. |
| 6 | Liveness answers `live` or `unknown`, never `dead` | **VERIFIED** | Only `"live"` and `"unknown"` are returned anywhere in the module. Live run exercised **both** poles in one pass: `live` for the session that is typing, `unknown` for five others — so this is not a predicate that can only return one answer. |
| 7 | A marker's `cwd` is absolutised at arming | **VERIFIED** | `resolve_cwd()` applied at `gsd_autorun_marker.py:98`. Confirmed on disk, not inferred: this run's own marker holds `C:\Users\User\.claude\skills\claude-power-pack`. |
| 8 | No project config needed restoring, because nothing was reaped | **VERIFIED** | No `config` actions in the live sweep. Vacuously true, and correctly so. |

## G1 — a file the sweep refuses to admit is invisible

`gsd_long_run.py:901`

```python
if isinstance(data, dict) and data.get("session_id"):
    out.append((path, data))
```

Any `gsd-autorun-*.json` lacking a `session_id` is dropped with no row, no log
and no count. Two such files are present and have been since 2026-09-19:
`gsd-autorun-intent-ghost-30594a7d.json` and `-df5d917a.json`, 82 bytes each,
carrying `{"resume_command": "/gsd-autonomous", "post_compact_intent": "something"}`
— test residue.

So the live sweep judged **6 of the 8 files** matching its own glob and reported
on 6. It cannot distinguish "I judged all eight" from "I judged six and silently
ignored two".

This is narrow and it is arguable — a file with no `session_id` is not a marker,
and refusing to admit it is defensible. What is not defensible is doing it
**silently**, because this phase's own done-criterion is that

> an empty sweep is distinguishable from a sweep that judged nothing

and that is exactly the distinction lost here. Phase 4 made *declines* auditable
(`kept`, with the clause that held each one). It left *non-admissions* invisible,
one level below. It is the same family as the population-floor rule in
`instrument-before-claim.md`: a structural sweep needs a floor so it can tell
"nothing qualified" from "I stopped seeing things".

**What would close it:** under `--explain`, emit one row per glob match the
sweep declined to admit, naming the reason (`no session_id`, `unparseable`), plus
a count of files seen against files admitted.

## Adjacent finding (not a must-have)

`gsd_autorun_marker.py:253` passes `cwd=args.cwd` to `ledger_append` while `:98`
passes `resolve_cwd(cwd)` to the marker. The marker therefore records the
absolute path and the ledger records `"."`. Nothing consumes the ledger's `cwd`
for resolution today, so this is a fidelity gap in the audit record rather than a
safety defect — but it is the same bug Phase 4 fixed, surviving one field over,
and it is what a future reader asking "what was this run armed with" would read.

## What this phase does NOT establish

- That any marker is reapable. Zero of the population qualifies, which was the
  phase's own measured finding — the premise it was given ("seven markers are
  armed for sessions that no longer exist") was false.
- That the reap path works **in anger**. Nothing has ever been reaped in
  production. The deletion branch is covered by tests and has never run for real.
- Anything about the 19.0 h mtime-drift figure, which is a historical measurement
  this run did not reproduce.

## Gap closure — G1, 2026-09-21, `c3b493b`

`_scan_markers()` now returns admitted markers and refusals from one pass and
one predicate; `_markers()` keeps its exact signature and returns the admitted
half, so the three callers that unpack `(Path, dict)` are untouched. Under
`--explain` the sweep emits a `not_a_marker` row per refusal, with its reason,
plus a `scanned` row carrying `files` / `admitted` / `rejected`.

That last row is the point. Naming the refusals alone would still leave a glob
that silently stopped matching indistinguishable from an estate with nothing to
judge — the population floor is what closes that, and it is the clause
`instrument-before-claim.md` says every structural sweep needs.

**Re-measured live, same command, same estate:**

```
not_a_marker  gsd-autorun-intent-ghost-30594a7d.json  no session_id
not_a_marker  gsd-autorun-intent-ghost-df5d917a.json  no session_id
scanned       files 8   admitted 6   rejected 2
kept 6 · advance_declined 5 · reaped 0
```

Both ghosts named, the denominator explicit, nothing reaped.

**Proof:** `tools/test_marker_admission.py` 7/7. Three mutations driven red —
non-admissions not emitted (4/7), floor removed (6/7), admit-nothing (4/7, which
reds the *green control*, so the detector cannot pass by rejecting everything).
Restores SHA-256 verified. No regression: GSDLR 93/93, PBA 11/11.

**Instrument failure recorded rather than hidden:** the third drill first
returned `ANCHOR MISS` — twelve spaces of indentation against the file's eight.
A mutation that never applied is not a mutation that survived. It was re-run
with the correct anchor, not counted as a result.

**Still open, and NOT closed by the above:**

- Must-have 2 remains UNVERIFIABLE. The 2026-09-19 mutation drills leave no
  artifact; today's drills are evidence about today's code, not about that run.
- The reap path has still never deleted anything in production.
- The adjacent `ledger_append(cwd=args.cwd)` fidelity gap at
  `gsd_autorun_marker.py:253` is untouched.
