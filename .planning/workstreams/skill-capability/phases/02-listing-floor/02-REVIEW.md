---
phase: 02-listing-floor
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - tools/test_listing_floor_verdict.py
  - vault/programs/skill-capability/ledger.json
  - vault/programs/skill-capability/evidence/B-listing-floor.md
  - vault/programs/skill-capability/owner-bundle.md
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: fixed
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Observed (foreground): `python3 tools/test_listing_floor_verdict.py` gives LF_PASS=11/11, rc 0; `test_skill_capability_program.py --pillar B` prints CEP_PILLAR_B=PASS; the evidence file sha256 (941e7185...) equals the ledger pin; `frozen` is byte-identical to bbbdf3d9 and only `state.B` changed. Every figure in the evidence file is rendered from the jsonl rows, the frozen ledger, git and the plan texts, and the checked figures typed into the ledger reason / owner-bundle (29,991 -> 30,002; 30,000 -> 29,795; 87,739 -> 89,844; 9000 / 4000 / 1500; 8 of 12) all equal the derived ones today. Red branches are real: I drove mutants and they flip the intended clause. UNMEASURED and duplicate rows give INCONCLUSIVE and exit 1, never ok. The band arithmetic (floor(cap*0.01) = 300 for cap 30000) is right, and I checked it equals cap//100 for the caps I tried.

No blockers. The defects are about what the verdict does with inputs the drills do not cover.

## Warnings

### WR-01: verdict_of ignores V-LF-DENOM-MATCH, so a verdict of FALSIFIED can sit beside a FAIL clause

**File:** `tools/test_listing_floor_verdict.py:374-380` (rendered at 459, emitted by `derived_json` at 637)
**Issue:** `verdict_of` reads only V-LF-TOKENS and V-LF-CAP. I mutated challenger startup_tokens +5: the result is TOKENS ok, CAP ok, DENOM-MATCH FAIL, and `verdict_of` returns `FALSIFIED`. The rendered evidence line `- verdict: FALSIFIED` and `--json` `verdict` would then claim a falsification on rows that no longer equal the frozen D-LISTING. The process exit is 1, but a consumer of `--json` (which always returns 0, line 721) or of the evidence file reads FALSIFIED. The drill list pins only the per-clause statuses, never `verdict_of`, so this is untested.
**Fix:** make FALSIFIED require all of SOURCES, TOKENS, CAP and DENOM-MATCH to be `ok`, and return INCONCLUSIVE or a distinct `ROWS_DRIFTED` otherwise. Add a drill asserting `verdict_of` for the `challenger-tokens-changed` mutant.

### WR-02: V-LF-TOKENS ignores the stated noise: a 1-token drop is "the floor fell", a 1500-token drop is NOT_FALSIFIED

**File:** `tools/test_listing_floor_verdict.py:319-325`, `delta_wording` 405-410, drill `tokens-lowered` 528-530
**Issue:** The clause compares the raw delta to 0 (`delta >= 0` ok, else FAIL). The same file's `delta_wording` says a rise inside noise (+-1500) is "no saving shown", and a fall is "n=1 per arm, not a saving without a repeat". The gate therefore treats a fall of 1 token (well inside the stated noise) as proof the floor fell, and as NOT_FALSIFIED (verified: a -1000 delta gives NOT_FALSIFIED). Meanwhile the CONTEXT D-03 itself calls the real +2105 "inside the stated noise only partly". The clause is asymmetric and the drill is built around the 1-token case, so the gate fails on noise while claiming a measurement. Note the safe direction (FAIL means the claim is not confirmed), but the text `challenger is below champion, the floor fell` asserts a saving the data cannot support.
**Fix:** use the noise as a three-way band: delta >= 0 ok (falsified); delta < -noise FAIL (floor fell); -noise <= delta < 0 INCONCLUSIVE ("fall inside noise, n=1, repeat needed"). Read the noise from `static()["noise"]` as `render` already does, and add a drill for the inside-noise fall.

### WR-03: A zero or implausible reading is accepted as a measurement, so it reads as NOT_FALSIFIED instead of INCONCLUSIVE

**File:** `tools/test_listing_floor_verdict.py:83-84, 98-101`
**Issue:** `k4_arms` only requires an int. The probe (`wiki/tools/listing_floor_probe.py`) sets `startup_tokens` to `(usage fields or 0) + ...` and a first call with all-zero usage fields yields `0`; an empty-content listing yields `chars` 0. Both pass `_is_int`. Mutants: startup_tokens=0 gives TOKENS FAIL, chars=0 gives CAP FAIL, so the verdict is NOT_FALSIFIED. A broken session therefore reads as a lowered floor (the opposite of the stated rule that a gate that could not read its source must not look green or red wrongly). In the committed data DENOM-MATCH also fails, but in `--jsonl` or after a future re-baseline it will not.
**Fix:** require `startup_tokens > 0` and `listing.chars > 0` in `k4_arms` (refuse as INCONCLUSIVE otherwise) and add a drill for each.

### WR-04: Pillar B's terminal does not execute the verdict gate; its figures in the ledger are typed with no tie to the derived ones

**File:** `vault/programs/skill-capability/ledger.json` (state.B, evidence list; reason; savings)
**Issue:** state.B evidence is one `measurement` (sha-pinned file), one `owner` and three `commit` entries; there is no `gate` entry for `tools/test_listing_floor_verdict.py`, unlike pillar A, which pins its gate. CONTEXT D-04 chose that deliberately, but the `reason` still says the figures are "recomputed ... by tools/test_listing_floor_verdict.py". The only mechanical check at the program level is the sha of the generated file: editing the jsonl or the plan text keeps `--pillar B` at PASS (the sha is of the stale committed file), and no red branch of the verdict gate is ever run by the program gate. The numbers in `reason`, `savings` (9000, 1500, +2105) and the owner-bundle line are hand typed and nothing ties them to the render, so they can drift silently. They are correct today.
**Fix:** add `{"kind":"gate","argv":["python3","tools/test_listing_floor_verdict.py"]}` to state.B evidence (the same shape A uses) so the program gate runs the drills and the evidence-current check; optionally have the script assert that the typed ledger figures appear in its derived JSON.

## Info

### IN-01: C6 regex can span bullets; "cap still binds" is asserted, not checked

**File:** `tools/test_listing_floor_verdict.py:143-144, 259-269`
**Issue:** `C6_RE` uses an unbounded lazy `.*?` over the whitespace-collapsed whole plan text, so if the `C6 DONE` bullet loses its own "initial listing before" phrase it can bind to a later bullet's figures instead of returning None. Separately, `clause_c6` prints "cap still binds" when after >= before - band, but never compares either figure to the cap (30,002 is above the 30,000 cap in the real data, so the claim rests on the delta only).
**Fix:** bound the span (e.g. `[^.]{0,400}?` or stop at the next `- C` bullet) and reword the ok text to "listing did not drop" unless the figure is compared with the cap.

### IN-02: Band computed in floating point

**File:** `tools/test_listing_floor_verdict.py:111-112`
**Issue:** `math.floor(cap * 0.01)` is float arithmetic. It is correct for the caps I checked (30000, 29000, 29900, 3100, 1900, ...) but is not guaranteed for every integer, and a 1-char shortfall moves the boundary drill. The 1% choice is also the author's own discretion (no source).
**Fix:** `cap // 100` (or `cap * 1 // 100`) with `CAP_BIND_PERCENT = 1`.

### IN-03: The aperture clause executes historical repo code

**File:** `tools/test_listing_floor_verdict.py:186-209`
**Issue:** `aperture_probe` writes the K4 probe source from `git show` to a temp file and `exec_module`s it in-process. The source is the repo's own history, and `main` is guarded, so the risk is low; but a probe revision with import-time side effects would run inside the verdict gate. Fails closed (INCONCLUSIVE) on any exception, which is right.
**Fix:** run it in a subprocess with a timeout, or document the trust assumption in the clause docstring.

### IN-04: The noise figure that decides "above noise" is an unsourced assertion

**File:** `vault/programs/skill-capability/evidence/B-listing-floor.md` (Economics line 3); owner-bundle `[B]` line
**Issue:** "+2105 ... above the stated noise (+-1500) by 605" derives from `noise +-1.5k` in the lessons file, with no sample behind it (n=1 per arm). The evidence correctly says "stated", but the owner-bundle sentence "+2105 above the +-1500 noise" and the ledger savings note read it as an established margin.
**Fix:** keep "stated" in the owner-bundle and ledger wording, or name where the 1.5k came from when the next paired sessions are run.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Fix log

Fixed 2026-10-03 in `tools/test_listing_floor_verdict.py` (evidence file re-rendered, state.B sha256 re-pinned; `frozen` untouched).
Verified: `LF_PASS=11/11` rc 0, verdict FALSIFIED on the committed jsonl; `--json` rc 0 (exits 1 for any verdict other than FALSIFIED); pillars A and B PASS.

- WR-01: fixed. `verdict_of` returns FALSIFIED only when V-LF-SOURCES, V-LF-TOKENS, V-LF-CAP and V-LF-DENOM-MATCH are all ok, else INCONCLUSIVE (NOT_FALSIFIED stays for a FAIL in TOKENS/CAP). `--json` exits 1 when the verdict is not FALSIFIED. Drill: challenger startup_tokens +5 gives verdict INCONCLUSIVE (plus clean / inside-noise / zero / beyond-noise verdict drills).
- WR-02: fixed. V-LF-TOKENS: delta >= 0 ok (no saving); -noise <= delta < 0 INCONCLUSIVE ("change inside the stated noise, no saving shown"); delta < -noise FAIL (a saving larger than noise appeared). Noise read from the lessons file via `static()`. Drills for -1, -1000 (INCONCLUSIVE) and -2000 (FAIL).
- WR-03: fixed. `k4_arms` refuses `startup_tokens <= 0` and `listing.chars <= 0` as UNMEASURED, so every clause is INCONCLUSIVE. Drills for tokens 0 and chars 0.
- WR-04: no_change_needed. No `gate` entry under FALSIFIED is a deliberate, verified design: the CE verifier re-runs gate argv only for IMPLEMENTED_AND_VERIFIED, so a gate entry on a FALSIFIED pillar would not be executed and would only imply a check that does not run. The evidence-file sha pin remains the program-level tie; the typed ledger figures were re-checked against `--json` after this fix and are unchanged.
- IN-01: fixed. The C6 regex is applied only to the `C6 DONE` bullet (bounded to the next `- ` bullet). The "cap still binds" claim is no longer printed; the text now says "listing did not drop (within the band of its before figure)", since neither figure is compared with the cap in code.
- IN-02: fixed. `band_of(cap) = cap // 100` (integer, `CAP_BIND_DIVISOR`).
- IN-03: no_change_needed. Low risk as the reviewer states (repo's own history, `main` guarded, fails closed to INCONCLUSIVE); not acted on per scope.
- IN-04: fixed (rendered wording only). The evidence now states the noise figure is a stated estimate from the lessons file (with its line), not a computed spread, and that each arm is n=1 session. Ledger and owner-bundle wording unchanged.
