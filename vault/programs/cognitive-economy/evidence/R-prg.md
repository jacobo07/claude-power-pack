# [R] Institutionalization -- PRG

Frozen rule: the UKDL 3-level (hard / process / trap) and CBR review is written to the campaign-owned
`vault/programs/cognitive-economy/ukdl-candidates.md`. Each entry is evidence-cited with a promote / reject /
keep-candidate verdict and a reason. Promotion INTO `ukdl-universal.md` (peer-hot, audit G10) is an Owner item.

## What exists

- `ukdl-candidates.md`: 7 candidates (UC-01..UC-07), 4 traps and 3 process rules. No hard rule was earned: no
  candidate is a production bug with a recurrence. Verdicts: 1 promote (UC-04, sent to the Owner as `[R] UC-04`),
  2 reject (UC-02, UC-03, each already owned by a named rule), 4 keep-candidate. CBR maturity is EXPERIMENTAL for
  all seven, as the plan fixes until earned.
- `gates/gate_ukdl_candidates.py`: checks the format, and on every run it also proves it can fail. Five mutants of
  the real file (dropped evidence, unknown verdict, duplicate id, promote missing from the bundle, empty reason)
  must each be caught. If any mutant passes, the gate reports FAIL.

## Gate run (fresh process, worktree `cognitive-economy/autonomous-run`, 2026-10-03)

command: `python vault/programs/cognitive-economy/gates/gate_ukdl_candidates.py`

```
  ok   mutant dropped-evidence caught
  ok   mutant unknown-verdict caught
  ok   mutant duplicate-id caught
  ok   mutant promote-not-in-bundle caught
  ok   mutant empty-reason caught
GATE_UKDL_CANDIDATES=PASS candidates=7 failures=0
exit=0
```

## Not part of this terminal

Writing UC-04 into `ukdl-universal.md` is the Owner's (owner-bundle `[R] UC-04`).

## Product Delta / Intelligence Delta

- Product: the campaign's lessons have a checked home with verdicts, instead of prose in seven evidence files.
- Intelligence: two of seven candidates were rejected as already owned (instrument-before-claim,
  real-context-reachability). The doctrine already covered them; what failed was applying it at write time. Writing
  them into the UKDL again would not have changed that.
