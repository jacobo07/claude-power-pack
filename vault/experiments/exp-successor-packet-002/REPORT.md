# exp-successor-packet-002 — result and decision

Registered `786d7a79…` at 2026-09-28T16:58:48Z, committed (`7e12fcb`) before any run. Four real
headless successors (`claude -p`, read-only), two cases (training + holdout), both arms on the same
model (`claude-opus-5-5[1m]`), blinded deterministic grading. Files: `registration.json`,
`material.json`, `runs.json`, `outputs.json`, `grades.json`, `analysis.json`, `dryrun.json`.

## What was measured

| | baseline (card) | candidate (card + packet reference) |
|---|---|---|
| quality (vendored analysis) | 4 / 4 | 4 / 4 |
| worker tokens, both cases | 1,007,045 | 1,007,852 (+0.08 %) |
| turns | 3, 3 | 4, 3 |
| elapsed | 71 s, 57 s | 75 s, 82 s |
| preregistered token target (−5 %) | — | **not met** |

Placement dry run over every real mission card on the host (32 with a live work tree): inlining a
packet into the card's remaining headroom truncates **28 of 32** and loses **249,455 of 432,571
bytes (58 %)**; a card carrying a reference fits all 32 (largest 4,081 / 8,000 bytes).

## Decision (the canonical rule for successor-context payload placement)

1. **Evidence never goes inline.** A packet is stored whole, content-addressed, and a card carries
   only its reference (path, sha256, bytes, gaps) plus a verify command. Truncating evidence to fit
   an envelope is refused by construction.
2. **A reference is not an efficiency lever.** On targeted questions it cost the same and scored the
   same. Carry one when the predecessor has a specific region the successor must not re-derive
   (mid-edit state, a hunk under review) — for provenance and staleness detection, not to save
   tokens. Hence item 12's consumer is OPT-IN on the handoff (`gsd_mission.py handoff --packet`),
   never a default dump.
3. **The lever is elsewhere.** Each fresh successor re-read ≈ 350 k cached + ≈ 150 k other input over
   3–4 turns, i.e. ≈ 167 k resident tokens *per turn*, identical in both arms. Card bytes are noise
   against that; turn count and resident bootstrap size are what Parent Context Epoch economics must
   attack.

## Limits, stated

- Two cases is diagnostic scope (as registered), not representative. It can refute "a reference is a
  big win"; it cannot establish a small effect in either direction.
- Tasks were answerable by reading one file; a successor that cannot read the repository was not
  tested (not the CPP case).
- The vendor's credential-line filter blocks 441 / 1,091 Python files here whole (322 only for the
  word "pass" before `:`/`=`), so whole-file packets of much CPP tooling are empty. Case files were
  chosen from unblocked files; this is recorded, not worked around.
- The host model id `claude-opus-5-5[1m]` is outside the vendor identifier grammar; the analysis
  request escapes it injectively (`tools/paired_experiment.vendor_id`), `runs.json` keeps it raw.
