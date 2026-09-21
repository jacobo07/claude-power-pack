---
milestone: v1
milestone_name: continuation-proven-live
audited: 2026-09-21T21:00:00Z
status: tech_debt
scores:
  requirements: n/a   # no REQUIREMENTS.md exists in this project — see gaps.requirements
  phases: 5/5
  integration: 7/7    # legs of the stated E2E flow, all WIRED
  flows: 1/1          # the one flow this milestone exists to prove, observed end to end
acceptance_gate:
  instrument: "tools/gsd_long_run.py report --session 9af80e55-9865-4c6f-877c-d155da18becf"
  verdict: PROVEN
  crossings: 4
  confirmed: 2
  proven_window: 2
  window_confirmed: 2
gaps:
  requirements:
    - id: "n/a"
      status: "not applicable"
      phase: "all"
      evidence: "No REQUIREMENTS.md exists. The 3-source cross-reference cannot run. Phase 5 mints local DEBT-1..3 that exist in no shared register. A coverage percentage over an absent denominator would be a fabricated number, so none is reported."
  integration: []   # zero blockers
  flows: []         # zero broken legs
nyquist: skipped    # no validate-phase step hook is active (.planning/config.json hooks = {}), and no *-VALIDATION.md exists
tech_debt:
  - phase: 02-userpromptsubmit-chain-deadline
    items:
      - "No raw n=5 sample log checked in; the measurement is not re-derivable by a third party without re-running a manual command."
      - "No reusable instrument (`tools/measure_chain_deadline.py`-shaped) exists."
      - "Worst-case chain time under a REAL transcript was never measured — the probe used an empty transcript_path, so the historical 11.4 s straggler never did its real work."
      - "No PLAN or CONTEXT artifact for this phase."
  - phase: 03-promote-the-exact-target-lessons
    items:
      - "Promotion is not activation: nothing measures whether a future session consults the promoted rules."
      - "The router edit cannot be attributed to this phase — `~/.claude/CLAUDE.md` is not under version control."
      - "03-SUMMARY.md cites the wrong commit for its Half 1 evidence; not retroactively closeable."
      - "~254 uncommitted CEPS lines in ukdl-universal.md — an open Owner decision, not a gap."
  - phase: 04-reap-the-stale-autorun-markers
    items:
      - "The reap path has never run in anger. Zero of the population qualified; the deletion branch is test-covered and has never deleted a real marker."
      - "Internal id-resolution asymmetry: find_transcript matches a FILENAME, session_liveness matches the row field `sessionId` (gsd_long_run.py:891). Conservative direction, so it cannot cause a wrong deletion."
  - phase: 05-close-the-continuation-debts
    items:
      - "D2 is proven on disk and unwired at runtime until `Developer: Reload Window`. A gate that compares files structurally cannot cover this."
      - "Two producers of `resume_confirmed` exist (continuation_transport.py:344 and context-watchdog.py:812); only the second has ever fired. The verdict rests on an event whose other implementation this flow never executes."
  - phase: cross-cutting
    items:
      - "Six pre-existing DRIFT pairs in verify_global_mirrors (cpp-compound.md, _oneshot_solitary_empty_shell_cleanup.js, hook-dispatcher.js, apex-completion-standard.md, code-review.md, testing.md). None introduced by this milestone."
      - "The three auto-compact chain files mirrored in 14b2894 are not TRACKED pairs until the branch reaches main — the verifier reads main (Mirror Parity Law §4), so it cannot see them at all."
      - "tools/compound_unattended.py carries 118 uncommitted insertions from 2026-09-10 (another writer's, 269 h old). The durable /cpp-compound fix — owning Steps 7+8 in-process — is blocked behind it."
---

# Milestone v1 `continuation-proven-live` — AUDIT

**Status: `tech_debt`.** Zero blockers, zero broken integration legs, the
acceptance gate PROVEN — and a real list of named deferred items that deserve a
decision rather than a silent carry-forward. That is what `tech_debt` means
here; it is not a softened `passed`.

## The milestone's own definition of done

> The milestone is accepted when `gsd_long_run.py report --session <sid>`
> returns **PROVEN**: at least two crossings, each followed by a resume the
> transcript shows was really submitted, typed by the terminal inbox that owns
> the pane rather than by a human.

**Met, 2026-09-21T20:54:39Z.**

| crossing | resume confirmed |
|---|---|
| 2026-09-20T21:56:22Z | — (run abandoned) |
| 2026-09-21T18:11:46Z | — (the 310 s inbox refusal; diagnosed, see STATE.md) |
| **2026-09-21T18:52:03Z** | **18:56:24Z** · `/gsd-autonomous` |
| **2026-09-21T20:48:26Z** | **20:54:39Z** · `/gsd-autonomous` |

Both unconfirmed crossings have a recorded reason and neither was dropped from
the count: `crossings 4` is reported beside `confirmed 2`, and the window that
the verdict reads is the last two.

## Phases

| phase | status | verification | note |
|---|---|---|---|
| 01 two-pane exactness drill | passed | `01-VERIFICATION.md` | opened `gaps_found`; superseded, original preserved unedited |
| 02 UserPromptSubmit chain deadline | passed | `02-VERIFICATION.md` | 4/4 must-haves; two re-derivability limits recorded as debt |
| 03 promote the exact-target lessons | passed | `03-VERIFICATION.md` | 3/3 must-haves, corroborated three ways |
| 04 reap the stale autorun markers | passed | `04-VERIFICATION.md` | opened `gaps_found`; G1 closed in `c3b493b` |
| 05 close the continuation debts | passed | `05-VERIFICATION.md` | written at audit time — the phase ran outside `gsd-execute-phase` and had none |

Phase 04's finding is worth keeping visible: the premise it was given — *"seven
markers are armed for sessions that no longer exist"* — **was false**, and the
phase's value was measuring that rather than acting on it.

## Integration

`.planning/INTEGRATION-CHECK.md`. All 7 legs WIRED, 0 blockers, 4 warnings, and
one of the warnings was a live defect in the record: `05-SUMMARY.md` still
called the fifth debt open after `7f88790` had fixed it. Corrected.

## Gates re-run at audit time

| suite | result |
|---|---|
| `test_gsd_long_run.py` | 99/99 |
| `test_continuation_transport.py` | 28/28 |
| `test_compaction_truth.py` | 15/15 |
| `test_gsd_autocompact.py` | 26/26 |
| `test_proven_window.py` | 10/10 |
| `test_inbox_delivery_enter.py` | 6/6 |
| `test_terminal_inbox.py` | 1/1 (ok=30/30) |

## What this milestone does NOT establish

Stated here so the `PROVEN` above is read at its real size:

- **That the loop survives unattended for many cycles.** Two confirmed cycles
  is the gate; it is not a claim about twelve.
- **That `continuation_transport`'s own delivery and confirmation path works** —
  on this host the route is `terminal-inbox` and that code never ran.
- **That the reaper can delete anything in production** — it never has.
- **That the promoted doctrine changes any future session's behaviour** —
  promotion is not activation, and nothing measures consultation.
- **That the mirrored extension is live.** It is on disk; the host loads it at
  the next window reload.

## Owner decisions this audit surfaces

1. **Merge `feature/knowledge-acquisition` to `main`?** Until then the three
   mirrored chain files are invisible to the mirror verifier by construction.
2. **The six pre-existing DRIFT pairs** — adopt `repo ← global` per §2, or leave.
3. **`tools/compound_unattended.py`** — 118 insertions, 269 h old, another
   writer's. It blocks the durable `/cpp-compound` fix.
4. **Reload the Cursor window** to make the mirrored extension the running one.
