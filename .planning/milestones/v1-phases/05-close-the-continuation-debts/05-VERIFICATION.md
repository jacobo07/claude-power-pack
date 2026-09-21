---
phase: 05
phase_name: Close the continuation debts
status: passed
verified: 2026-09-21
verifier: session 9af80e55 (goal-backward, re-measured)
supersedes_coverage_in: 05-SUMMARY.md
---

# Phase 5 — VERIFICATION

**Why this file exists and why it is dated after the SUMMARY.** Phase 5 was
executed directly rather than through `gsd-execute-phase`, so no VERIFICATION.md
was produced at the time, and `gsd-audit-milestone` step 2 treats a missing one
as a blocker — correctly. Writing it now is not a formality: three of the four
coverage rows in `05-SUMMARY.md` recorded a state that has since moved, and a
coverage block nobody re-reads is exactly how a stale claim survives.

Every row below was **re-run for this file**, not copied from the summary.

## Goal-backward check

The phase goal was: the three debts this milestone exposed are closed, each with
a driven red branch, or handed to the Owner as a named decision. The measurement
is per-debt, below.

## Coverage, re-measured 2026-09-21 20:5x

| id | claim | at SUMMARY | now | instrument |
|---|---|---|---|---|
| D1 | ledger `armed` row names the same absolute project as the marker | pass | **pass** | `test_gsd_long_run.py` **99/99** (was 96/96; the fifth debt added three) |
| D2 | the `/compact` arg-tail rule lives in one vscode-free module a gate drives | **fail** (5/6, by design) | **pass** | `test_inbox_delivery_enter.py` **INBOX_PASS=6/6**, `V-INBOX-LIVE-MATCHES-REPO: repo and kobii.pp-sessions-0.4.0 identical, sha=234C8DB0BA7B9051`; `test_terminal_inbox.py` 1/1, ok=30/30 |
| D3 | residue inventoried, nothing removed without the Owner | pass (inventoried, kept) | **superseded — deleted under authorization** | `05-RESIDUE-INVENTORY.md`: `RESIDUE_DELETED=4/4 already_absent=0 failed=0`, backup `~/.claude/backups/residue-20260921-211149` (4 files, 51,130 B), each digest re-hashed before removal |
| D4 | the daemon's SENT line records the ack's `enters=` and `arg_tail=` | pass, **unversioned** | **pass, versioned** | mirrored into the repo at `14b2894` with `auto-compact-stop-launcher.ps1` and `auto-compact-session-start-cleanup.ps1`; each verified identical to `~/.claude/hooks` by SHA-256 (`001ACACEB31DEB55`, `E6B9D21CD69DA01B`, `1BC35366C09F60DF`) |

## What changed after the SUMMARY was written

- **D2's gate went green for a real reason, not a lowered bar.** The failing
  assertion was `V-INBOX-LIVE-MATCHES-REPO`, comparing the repo copy against the
  extension that actually runs. It failed because the mirror had not been
  applied. `scratchpad/apply-argtail-helper.ps1` applied it (backups
  `*.20260921-224128.bak`, `node --check` clean, live selftest
  `TERMINAL_INBOX_SELFTEST=PASS ok=30`), and the gate now passes on the same
  assertion it was failing. **The gate compares files on disk.** The extension
  host still runs the previously-loaded module until a `Developer: Reload
  Window`; that is stated here rather than folded into the green.
- **D3 is no longer a kept decision.** The Owner authorized deletion at the
  checkpoint. `scratchpad/residue_delete.py` re-confirmed presence, copied and
  re-hashed each file, and would have refused to proceed at all if any backup
  digest disagreed. The "these are not readers" claim was then *tested* rather
  than asserted: MADM 7/7, INTENT 9/9, GSDLR 96/96 after removal. The two ghost
  fixtures shared digest `b7cb47fe33ed915d` — byte-identical, which the
  inventory had implied and never stated.
- **D4 stopped being unprovable here.** Its rationale was "that file has no
  version-controlled copy in this repo". It has one now, along with the two
  scripts that make it a chain. Direction was `repo ← global` per Mirror Parity
  Law §2, because the global copy is the one that runs, so syncing that way
  adopts rather than clobbers.

## The fifth debt, found during the phase and closed in it

`write_trigger` dropped the delivery request on the floor: a `/compact` or
resume was written to the trigger flag with no ledger row, so the ledger could
not show what had been asked for. Fixed in `7f88790`, with the `kind` **derived
from the payload** rather than recomputed (`derive-don't-recompute`, the same
rule `gsd_autorun_marker.py:253` already follows). Three new gates,
`V-GSDLR-INBOX-DELIVERY-IS-LEDGERED`, `-ROW-KIND-DERIVED`, `-ROW-NAMES-PRODUCER`.
Red branch driven by `scratchpad/drill_t5.py`: three mutations, each landing on
its **own** named assertion (two on one assertion would mean one pole uncovered),
every restore byte-exact by SHA-256, restored suite green.

That drill also caught a defect in my own instrument: `-ROW-NAMES-PRODUCER`
re-stat'd the *marker* to rebuild a cid built from the *transcript*'s mtime, so
it failed against a correct row (98/99). It now derives from the sibling
`recovered` row, and the reason is kept in a comment.

## Anti-patterns

None found. The phase introduced no unfinished-work markers of the kinds the
Reality Contract bans, and its whole delivered surface — three new gates — is
executable: `python tools/test_gsd_long_run.py` runs them.

## Requirements coverage

This project has **no `REQUIREMENTS.md`**. The audit's 3-source cross-reference
therefore cannot run here, and that is reported rather than simulated: the
traceable units are the ROADMAP's named debts (DEBT-1..3 plus the fifth found
in-phase), all four closed above. A coverage percentage computed against an
absent denominator would be a fabricated number.

## Re-verified after the SUMMARY was corrected

`init.manager` reported this phase `verification_status: stale` and it was
right: `05-SUMMARY.md` was edited *after* this file was first written, so the
verification predated a substantive change to its own subject. The change was
not cosmetic — the milestone integration check (FINDING 1) found that the
summary still described the fifth debt as **NOT fixed** long after `7f88790`
fixed it, and still carried the superseded `PARTIAL` gate figure.

Both bullets now carry a SUPERSEDED note. Nothing in the coverage table above
changes: D1's instrument was already the 99/99 suite that the fifth debt's three
gates are part of, so the correction is to the *record*, not to the result.

The shape is worth naming, because it is the third instance in this one
milestone: **a SUMMARY is written once and the code keeps moving under it.**
"This residual is still open" decays into a false statement with nothing to
signal the decay — the same failure as the stale gate figure, and as C7 reading
NOT YET. What caught it all three times was an instrument re-run at the moment
of the claim, never a re-read.

## Verdict

**passed.** Four debts closed with a measured instrument each; one item (D2)
carries a stated runtime caveat that a gate on disk structurally cannot cover.
