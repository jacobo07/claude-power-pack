---
phase: 03-opportunity-and-delivery-measurement
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - tools/test_skill_delivery.py
  - tools/skill_invocations.py
  - tools/test_skill_invocations.py
  - vault/programs/skill-capability/delivery_fixture.json
  - vault/programs/skill-capability/evidence/C-delivery.md
  - vault/programs/skill-capability/evidence/C-window-G.json
  - vault/programs/skill-capability/ledger.json
  - vault/programs/skill-capability/owner-bundle.md
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: fixed
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

`python3 tools/test_skill_delivery.py` was run on gex44: SD_PASS=36/36. MIN_N was mutated in-process to 4 and to 6; both
go red (V-SD-PRECISION/SMALL-N/LIVE-PATH/EVIDENCE-CURRENT), so the "n < 5" boundary is pinned from both sides and no
ratio is printed at n < 5. The default argv reads only committed files plus its own TemporaryDirectory; it makes no
git, network, `~/.claude` or wall-clock reads. Every read has `encoding="utf-8"` and every write `newline="\n"`.
The pack hash and the evidence compare are CRLF-normalised. No Critical issue. The skill_invocations.py change is
backward compatible: grep shows only `si.scan(...)` (wiki/tools/skill_zero_triage.py) and the module's own `main`
call it, both unbounded, and `count_file` only gains an `untimed_rows` key.

Three Warnings follow: one opportunity decision is silently uncounted, the deviation you asked about, and
provenance clauses that are never driven red.

## Warnings

### WR-01: `pass-unrecordable` commit rows are in no bucket, so recall is overstated

**File:** `tools/test_skill_delivery.py:67,89-100,154-163`
**Issue:** The hook (`hooks/doctrine_cards.js:493-497`) ledgers `pass-unrecordable` for a commit that has foreign
files in deny mode when the card flag cannot be written. The card was NOT shown, so this is an undelivered opportunity.
`OPPORTUNITY_DECISIONS = ("opportunity","deny-card")` and `UNKNOWN_DECISIONS = ("unknown","timeout")` omit it. Because
`is_opportunity` is false it hits `continue` and is counted nowhere (not `opportunities`, not `judgement_unknown`,
not `ignored_non_commit`). `tools/skill_opportunity_signals.py:DECISIONS` lists it, so the sibling module knows it.
Reproduced: adding a `pass-unrecordable` row (foreign=1) to window F gives opportunities 8, recall 4/6, every counter
unchanged. The row vanishes, so a laptop `--measure-live` run silently drops exactly the cases where delivery
failed. The fixture has no such row, so no clause can see it. That breaks "UNMEASURED never counted as 0": a
missed delivery is neither counted nor reported.
**Fix:** Treat it as an opportunity (undelivered unless an invocation precedes `ts`):
`OPPORTUNITY_DECISIONS = ("opportunity", "deny-card", "pass-unrecordable")`. Add a fixture row plus an
`expected` figure so V-SD-OPPORTUNITY covers it, and a mutant that drops it. Better: derive the decision set
from one shared constant, not two copies. At minimum, count unrecognised commit decisions in a visible
`other_decision` counter so none can vanish.

### WR-02: deny-card row with unparseable `ts` marked UNMEASURED (the deviation) is wrong in `compute_window`

**File:** `tools/test_skill_delivery.py:166-187,497-498`
**Issue:** Card delivery is proven by the `deny-card` decision alone. The ts only orders an invocation against the
judgement. The code's own `card_invocation_unmeasured` field already models "delivered by card, overlap with an
invocation unknown". Instead the whole row becomes UNMEASURED and leaves the recall n and the precision n.
Reproduced on window F: one bad deny-card ts moves recall 4/6 to 3/5 and precision n 4 to 3. Two bad ts moves recall to
`n=4 (< 5, not estimated)`. Unparseable timestamps can therefore hide a recall figure by shrinking n below 5, and
bias recall downward. `dcard_labels` also sorts such a row at 0.0, which reorders label consumption. V-SD-TS-UNPARSEABLE
hard-codes `delivered == clean - 1`, so the test pins the deviation instead of checking it. The only real argument
for it is window membership: `measure_live` keeps ts-less rows (`ep is None or ...`), so membership in [start, end]
is unknowable. That argument belongs in `measure_live`, not in `compute_window`. F and L have membership by
construction. In L the effect is loud, not silent: V-SD-L-PRECISION fails because n != live_denies.
**Fix:** In `compute_window`, for `dec == "deny-card"` set `state = "card"` regardless of `until`, with
`invoked = None` when `until is None`. Keep `unparseable_ts` counted, and keep UNMEASURED for non-deny decisions, whose
invocation ordering truly needs the ts. Put the window-membership policy in `measure_live`: keep the row but add a
separate `window_membership_unknown` count and print it beside recall. Update V-SD-TS-UNPARSEABLE to expect
`delivered == clean` and `card_and_invocation == "UNMEASURED"`.

### WR-03: provenance clauses are never driven to the other answer; the L-drill "PINNED stays ok" is vacuous

**File:** `tools/test_skill_delivery.py:455-472, 375-381, 642-668`
**Issue:** (phase 2 WR-01 pattern). In `l_drills`, `l_clauses(rep, pack, dcard)` is always called with the REAL `pack`
and the default `pack_path`. So `V-SD-L-PINNED` hashes the unmodified file on disk every time. The `pinned` check
("mutant did not touch the file") can never be red, whatever the mutant does, and `not pinned` is dead code.
No mutant ever makes V-SD-L-PINNED, V-SD-L-SELECTION or V-SD-L-DCARD-MATCH go red, and V-SD-G-RECORD is driven only
on its `opportunities` sub-clause (host, ABSENT, root, schema, totals, command are never driven). Nor is
V-SD-LIVE-PATH driven. Each could be deleted and 36/36 would remain. The verdict does depend on them, because
a wrong pack, wrong host or a tampered record fails the default run, but nobody has shown the red branch.
**Fix:** Add mutants that change the file or record:
(a) pass a tampered temp copy of the pack to `l_clauses(..., pack_path=tmp)` and require V-SD-L-PINNED red;
(b) append an out-of-rule row (e.g. `decision: "opportunity"`) and require V-SD-L-SELECTION red;
(c) drop one `deny_sha` or add an extra one and require V-SD-L-DCARD-MATCH red;
(d) flip `card_ledger` to "PRESENT", `host` to a non-gex44 value, and `root` to an expanded path, requiring
V-SD-G-RECORD red on each;
(e) break one measure_live field and require V-SD-LIVE-PATH red.
Then drop the vacuous `pinned` guard or make it real by hashing the mutant.

## Info

### IN-01: naive ISO timestamps are host-timezone dependent

**File:** `tools/skill_invocations.py:70-78`
**Issue:** `datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp()` on a string with no offset (or a date-only
string) interprets it in the host's local timezone. The same transcript row bounds differently on gex44 (UTC?) and the
Windows laptop. Real data is `...Z`, so there is no current impact. A naive row would be mis-ordered silently
instead of becoming `untimed_rows`. On Python < 3.11, `fromisoformat` rejects non-3/6 fractional digits, and those
rows become untimed (conservative, not wrong).
**Fix:** After parsing, `if dt.tzinfo is None: return None` (count as untimed), or attach `timezone.utc` explicitly.

### IN-02: subagent invocations count as parent-session delivery

**File:** `tools/test_skill_delivery.py:103-121`, `tools/skill_invocations.py:63-67`
**Issue:** `transcript_index` joins `subagents/*.jsonl` to the parent session id, and `invoked_before` returns True
on any of them. A Skill call inside a subagent puts the body in the subagent's context, not necessarily the parent's.
The card judgement's `session` may name either. The metric then over-counts invocation delivery by an amount the
gate does not report. `by_invocation_only` has no subagent/main split.
**Fix:** Record per row whether the hit came from a `subagents/` file and report it beside recall (or state it as
a definition caveat in DEFINITIONS).

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Fix log

Fixed in `fix(03): C -- delivery gate review fixes WR-01..03, IN-01`. Gate after the fixes: SD_PASS=53/53 (was 36/36),
also with an empty HOME; SKINV_PASS=11/12 (only V-SKINV-REAL-TYPED fails, the known missing positive-control transcript);
CEP_PILLAR_A/B/C PASS. `frozen` equals the FROZEN_AT blob; only `state.C` changed in ledger.json.

- **WR-01: fixed.** `OPPORTUNITY_DECISIONS` now holds `pass-unrecordable` (an undelivered-by-card opportunity; an invocation
  can still deliver). `KNOWN_DECISIONS` is the one recognised set; any other commit decision lands in a visible
  `other_decision` counter (rendered for F and L, carried by `measure_live`). Fixture gained S9 (`pass-unrecordable`, no
  invocation) and one `future-decision` row. Mutants DROP-UNRECORDABLE and OTHER-DECISION-SILENT go red on V-SD-OPPORTUNITY
  with V-SD-DELIVERY staying ok. Window F figures by reasoning: opportunities 8 -> 9 (S9 row), delivery measured 6 -> 7
  (S9 has a timed transcript with no Skill call, so it is measured and undelivered), delivered 4 unchanged, recall 4/6 =
  0.667 -> 4/7 = 0.571 (n=7), precision 1/4 (n=4, not estimated) unchanged, other_decision 0 -> 1. The pass-unrecordable row
  is not in the precision n because it was not delivered. Window L is unchanged (other_decision 0).
- **WR-02: fixed.** A `deny-card` row with an unparseable ts keeps card delivery; only the invocation overlap becomes
  UNMEASURED (`card_invocation_unmeasured`, `card_and_invocation == "UNMEASURED"`). Other decisions with a bad ts stay
  UNMEASURED. `dcard_labels` now sorts ts-less deny rows last. `measure_live` keeps ts-less rows and counts them in
  `window_membership_unknown` (top-level, beside recall). V-SD-TS-UNPARSEABLE now expects delivered and the recall n unchanged;
  a second mutant (`tsless_deny="unmeasured"`, the old behaviour) is killed by it. V-SD-LIVE-PATH runs a second window with a
  ts-less ledger row and requires window_membership_unknown 1.
- **WR-03: fixed.** `l_drills` passes each mutant's own pack and D-CARD to `l_clauses`, and a pack mutant is written to a temp
  file and hashed, so V-SD-L-PINNED is red exactly when the pack bytes changed (the vacuous guard is replaced by
  `pinned_ok == (transform is _same)`). New mutants: PACK-TAMPER (V-SD-L-PINNED), OFFRULE-ROW (V-SD-L-SELECTION),
  DCARD-EXTRA-SHA and DCARD-REFUSAL (V-SD-L-DCARD-MATCH). DCARD-DROP-SHA is killed by V-SD-L-PRECISION, not DCARD-MATCH: a
  dropped sha is a legitimate unlabelled row for DCARD-MATCH, and the precision n against `live_denies` is the clause that sees it.
  V-SD-G-RECORD is driven per sub-clause (opportunities, schema, host, ABSENT, recall null, totals, command, root), each
  required to FAIL with its own diagnostic text. V-SD-LIVE-PATH is driven by LIVE-END-EARLY and LIVE-ROW-DROPPED.
- **IN-01: fixed.** `row_epoch` returns None for a timezone-naive timestamp (untimed, never host-local). V-SKINV-ROW-BOUNDS
  carries a naive-ts Skill row (untimed 2 in both bounded reads, 3 model calls unbounded); 11/12 as before.
- **IN-02: no_change_needed (code).** Subagent calls staying joined to the parent session is the owner module's contract;
  one definition line ("subagent caveat") now states it in the rendered evidence, as the review allowed.

Re-pinned in ledger.json state.C: evidence/C-delivery.md sha256 and delivery_fixture.json sha256, plus the two figures its
reason quotes (window F 9 opportunities / 7 measured / recall 4/7 (n=7), and 53/53 clauses). C-window-G.json and the pack
sha are unchanged.
