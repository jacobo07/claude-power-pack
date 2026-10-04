---
phase: 05-offline-replay-and-owner-bundle
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - wiki/tools/kme_replay.py
  - tools/test_kme_replay.py
  - wiki/tools/kme_pillars.py
  - tools/test_incremental_cognition_program.py
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-04
**Depth:** standard
**Files Reviewed:** 4 (kme_pillars.py and test_incremental_cognition_program.py: phase-5 hunks only)
**Status:** issues_found

## Summary

`wiki/tools/kme_replay.py` is careful about the focus items that concern the instrument itself. I found no defect there on
"UNMEASURED becomes 0 or a rank": `split_ranking` / `candidate_status` / `rank_candidates` only rank entries that carry a
number, and a drifted population makes all three unranked with no figure. Writes are guarded by the `_prepare` out-dir-inside-root
check, labels are validated, and the whole rendered text goes through `redact()`. `tools/test_kme_replay.py` (41/41) and
`test_incremental_cognition_program.py --selftest` both pass on this host. The real problems are in the done-gate (R4 / R3-L),
which can be bypassed, plus a few places where the ranking file's numbers say more than they measure.

I reproduced every Critical/Warning below with scratch scripts under `/tmp/rv` (nothing in the repo was modified).

## Critical Issues

### CR-01: R4 is bypassed by any spelling of the bundle path that `_bundle_ref` does not resolve the way `ce.Resolver` does

**File:** `tools/test_incremental_cognition_program.py:363-374` (R4), interplay with `tools/test_cognitive_economy_program.py:131-141`
**Issue:** `_bundle_ref` normalises backslashes, `./`, `..` and the absolute checkout path, then compares to
`OWNER_BUNDLE_REL`. But the resolver that L4 uses to read and sha-pin the evidence (`Resolver._path`) also does
`Path(rel).expanduser()` and accepts any absolute path, while `_bundle_ref` never expands `~` and only recognises
POSIX-absolute paths under `REPO`. So the same file, spelled differently, is accepted by R4 and by L4:

```
$ python3 /tmp/rv/gate.py
tilde  '~/missions/incremental-cognition/.claude/worktrees/ic-run/vault/programs/incremental-cognition/owner-bundle.md' -> R4 refuses: False   exists: True
main-checkout-abs '/home/kobii/missions/incremental-cognition/vault/programs/incremental-cognition/owner-bundle.md'      -> R4 refuses: False   exists: True
```

Scenario: ledger `L = {terminal: AUTHORIZATION_BOUND, evidence: [{kind: owner_decision, ref: "~/missions/.../owner-bundle.md", sha256: <its sha>}]}`.
The bundle names `[L]`, so L4 passes (`_check_evidence` requires `[L]` in the text), R4 passes, and R3-L stays silent for
AUTHORIZATION_BOUND (no ranking file needed). The bundle, which is the mission's request, closes pillar L as the Owner's decision,
which is the exact thing R4 exists to prevent (focus item 3). The five spellings pinned in `V-ICP-R4-BUNDLE-REFUSED` did not include `~`
or a second checkout of the same path.
**Fix:** decide identity by resolving the ref the way the reader does and comparing files, not strings:
```python
def _bundle_ref(ref) -> bool:
    if not isinstance(ref, str) or not ref:
        return False
    p = ce.Resolver._path(ref.replace("\\", "/"))       # same ~ / absolute handling as L4
    bundle = REPO / OWNER_BUNDLE_REL
    try:
        return p.exists() and bundle.exists() and os.path.samefile(p, bundle)
    except OSError:
        return False
```
Add `~`, a symlink and a second-checkout absolute path to the pinned spellings, each with a positive control.

## Warnings

### WR-01: R4 is string-based on a POSIX-only shape, so it does not hold (and its own gate goes red) on the Windows laptop

**File:** `tools/test_incremental_cognition_program.py:363-374`, `:628-631` (the `bundle_forms` list in the selftest)
**Issue:** After `replace("\\", "/")`, a Windows absolute path is `C:/Users/.../owner-bundle.md`; it does not start with `/`, so the
`relative_to(REPO)` branch is skipped and the function returns False (reproduced: `_bundle_ref(r"C:\Users\User\repo\vault\programs\incremental-cognition\owner-bundle.md")` is `False`). The selftest builds one form
from `str(REPO / OWNER_BUNDLE_REL)`, which on the laptop is exactly such a path, so `V-ICP-R4-BUNDLE-REFUSED` would fail there. The owner bundle (item 1)
tells the Owner to run this suite on the laptop expecting exit 0. NTFS is also case-insensitive, so `Owner-Bundle.md` names the same file but compares unequal.
**Fix:** same as CR-01 (`os.path.samefile` handles drive letters, case and symlinks on both hosts).

### WR-02: R4 identifies "the bundle" by name only; a verbatim copy or any agent-written file naming `[L]` is accepted as the Owner's decision

**File:** `tools/test_incremental_cognition_program.py:377-387`
**Issue:** reproduced: `vault/programs/incremental-cognition/evidence/L.md` (the mission's own evidence file, six `[L]` occurrences) and a byte copy of the bundle at
another path both pass `check_owner_decisions` and `ce._check_evidence` as `owner_decision`. The docstring and bundle text promise "only a
file the Owner wrote in their own words counts", but nothing distinguishes an Owner-authored file from a mission-authored one.
**Fix:** require the ref to be exactly `vault/programs/incremental-cognition/evidence/<PILLAR>-owner-decision.md` (the name the bundle tells the Owner to use),
refuse an owner_decision whose sha256 equals the bundle's or any other mission-written evidence file's, and consider requiring that the file's first commit is not authored by the mission identity.

### WR-03: A hand-written file closes pillar L: R3-L trusts self-asserted front matter and never checks the ranking itself

**File:** `tools/test_incremental_cognition_program.py:262-290` (L branch of `terminal_claim_problems`)
**Issue:** reproduced with `/tmp/rv/forged.md` (front matter only, `ranked_ids: []`, `unranked_ids: []`, the real frozen-file sha, `command: "hand typed"`, body `KME-L [L]`):
`check_measurement_scope(..., only=["L"])` returns `[]` for terminal `RESEARCH_INSUFFICIENT_EVIDENCE`. The L branch checks `unranked_ids == []` but not that
`ranked_ids` is exactly the three candidates, not the `<!-- kmer-json -->` block against the front matter, not `measured_at`/`until`/`weighted_denominator`. The test's own message says "a hand-written ... file cannot stand in"; it can.
(The D..I gate has the same property; that makes it a known limitation, but for L it is cheap to narrow: the gate can at least require internal consistency.)
**Fix:** in the L branch require `sorted(fm.get("ranked_ids", []) + fm.get("unranked_ids", [])) == sorted(CANDIDATES)`, parse the json block and require its `ranked_ids`, `unranked_ids`, `population_match`, `denominator`, `frozen_source` to equal the front matter, and require `ranked_ids != []` when `unranked_ids == []`.

### WR-04: The gate and `terminal_ok` do not pin `rollover_growth`, so a primary "terminal" ranking can be produced at any G

**File:** `wiki/tools/kme_replay.py:470-474, 628-629`; `tools/test_incremental_cognition_program.py:262-290`
**Issue:** `--rollover-growth 1000000000` is accepted (only `< 1` is refused). With KME-L, an exact population and the committed frozen source,
`terminal_ok` returns True and the file is a primary terminal, with `late_rollover` a MEASURED 0 ranked last (the 0 is a statement about the chosen G, not about late rollover).
Nothing in R3-L reads `rollover_growth` either. The ranking that is supposed to decide which live experiment the Owner spends quota on can thus be steered by a CLI flag.
**Fix:** make `terminal_ok` require `growth == ROLLOVER_GROWTH` (and print the reason otherwise), and have R3-L require `fm.get("rollover_growth") == 100000`; keep other G as smoke/sensitivity.

### WR-05: Ranked numerators emit `weighted_lo` / `weighted_interval` that are not lower bounds on anything, with unrounded float noise

**File:** `wiki/tools/kme_replay.py:283-285` (rollover), `:420-423` (retries), `:535`; committed example `vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md:132-137`
**Issue:** for `late_rollover` the file records `"weighted_lo": 8773727.999999996, "weighted_hi": 8773727.999999996` and `weighted_interval: [8773727.99.., 8773727.99..]`. `lo` is `avoided x 0.1`, which equals `hi` whenever no call is cold, and in any case is the *gross cost of the avoided tokens*, not a lower bound on a saving (the rollover's own cost is not subtracted, as CAVEATS says). A consumer that reuses the kme_pillars convention (`weighted_interval` = [lower, upper] of the numerator, lower bound at or above 3 % confirms materiality) would read a 16 % "lower bound" for late rollover. The entry-level `saving_status: upper_bound` is correct but sits one level away from the interval, and `ROUND` is documented as "float noise is not a measurement" yet `numerator` is emitted unrounded.
**Fix:** do not emit `weighted_lo` / `weighted_interval` for ranked entries (or rename to `gross_cost_lo` / `gross_cost_hi` and apply `_r`); keep only `upper_bound_weighted`.

### WR-06: Inline-sidechain files are UNMEASURED for late_rollover but silently MEASURED for retries and rereads

**File:** `wiki/tools/kme_replay.py:239-243, 323-380`
**Issue:** `RolloverObserver` declares a session unobserved when its main file holds usage-bearing `isSidechain` lines, because "one thread = one context" no longer holds. `RetryObserver` (and `EObserver`, observability fixed 1.0) key all state on the file path, so an interleaved subagent and the main thread share one "thread". Reproduced (`/tmp/rv/obs.py`, P4): main `git status` followed by a sidechain `git status` in the same file yields one `strict` retry, and the candidate is MEASURED. That is a cross-context repeat counted as an unchanged-precondition retry, inflating exactly the figure used to rank. It does not trigger on the committed KME-G corpus (0 such sessions), but the inconsistency means a corpus that has them gets a "measured" retries/rereads figure and an unmeasured rollover.
**Fix:** give `RetryObserver` the same inline-sidechain detection and make `observability` account for it (and for rereads, wrap `EObserver.result` or reject the session in `candidate_status`).

## Info

### IN-01: Equal figures get distinct ranks, and the CLI `share=` is not labelled as a bound

**File:** `wiki/tools/kme_replay.py:181-186, 538-539, 641-642`
**Issue:** a three-way tie of measured zeros prints `rank=1/2/3` (pinned by `V-KMER-RANK-TIE-DETERMINISTIC`), which reads as an order of preference; `KMER rank=... share=...` on stdout drops the "upper_bound" qualifier that the file carries.
**Fix:** give tied entries the same rank (competition ranking) and print `upper_bound_share=`.

### IN-02: Overlap-sensitive details and raw read paths from transcripts are written to a committed file

**File:** `wiki/tools/kme_replay.py:535-536` (details), `wiki/tools/kme_pillars.py` (`EObserver.result` `top_paths`)
**Issue:** `details.top_paths` carries absolute file paths taken from transcripts; protection is only the regex `redact()` over the whole text. A path such as `/home/u/.env.production` or one embedding a customer name is written as is (V-KMER-NO-SECRET only proves a key-shaped canary is masked).
**Fix:** emit the path basename or a hash for paths outside the repo, or drop `top_paths` from the ranking file.

### IN-03: Docstring says only AUTHORIZATION_BOUND needs no ranking file; code exempts four more terminals

**File:** `tools/test_incremental_cognition_program.py:325`
**Issue:** `needs_primary` is true for L only for the two measurement terminals, so L can close as IMPLEMENTED_AND_VERIFIED, MERGED_INTO_EXISTING_OWNER, DEFERRED_STRONGER_OWNER or EXTERNAL_BLOCKED with no ranking cited and R3 silent (L4 still demands its own evidence kinds). Probably intended; the header comment (lines 36-40) should say so.
**Fix:** list the exempt terminals in the docstring, or invert the test to `terminal not in ("AUTHORIZATION_BOUND",)` if the narrower reading was meant.

Minor, not scored: parallel identical tool calls issued in one assistant message are counted as a `strict` retry (reproduced, P1) although the first result had not been seen when the second was issued.

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
