---
name: cpp-stop-ledger
description: Reconcile every STOP #1 plan against the evidence. Regenerates the derived disposition ledger — which audits are genuinely open, which read as awaiting but are contradicted by a later artifact, and which state their own outcome.
---

# /cpp-stop-ledger — STOP #1 disposition reconciliation

Every corpus audit in this estate ends at a STOP #1 and records its state in its own
frontmatter. **Nothing transitions that field.** A plan struck three weeks ago still
reads `status: STOP #1 -- awaiting Owner selection`, and the only way to learn the truth
is to cross-read a closure report filed somewhere else. That is
`feedback_status_field_nobody_can_transition` at portfolio tier: a field with no
transition producer is decoration, and the ledger lies — in the safe-sounding direction,
because a stale "awaiting" reads as work outstanding.

This command is that missing producer.

## Run

```
python -m modules.owner_queue.stop_ledger            # print
python -m modules.owner_queue.stop_ledger --write    # regenerate vault/plans/STOP_LEDGER.md
```

Verify: `python tools/test_stop_ledger.py` → 9/9, exit 0.

## What it does, and what it refuses to do

It **discovers** the denominator from `vault/plans/*.md` — never a hand-kept list
(`PR-COVERAGE-BY-CONSTRUCTION-001`: an audit set enrolled by hand measures memory, not
reality). For each STOP-bearing plan it looks for a **witness**: another artifact —
never the plan itself — naming that family beside a disposition verb.

| Verdict | Meaning |
|---|---|
| `OPEN` | open-shaped status, no witness anywhere. Genuinely outstanding — act on these |
| `CONTRADICTED` | reads as awaiting, but another artifact disputes it. **A contradiction, not a resolution** — verify before acting |
| `RESOLVED` | the plan's own status states its outcome |

**It never edits a plan.** One line would rewrite each stale `status:`, and that is
refused: the RE Baseline closure report established that rewriting a sealed artifact to
match a later verdict destroys the record of what was believed when. A plan is a dated
statement of belief. The ledger is *derived* instead — regenerated from the filesystem
every run, so it cannot drift the way a hand-maintained list does. `V-STOP-NEVER-EDITS-PLANS`
hashes the plans before and after and fails if a single byte moves.

## Reading the output honestly

`CONTRADICTED` is deliberately weaker than "resolved". The witness test matches at line
level, so an audit citing another family's verdict as prior art — an
`| EFAIF | DO-NOT-BUILD |` row inside a base-rate table — is indistinguishable from a
statement about that family's own STOP. The tool surfaces the disagreement; a human
adjudicates it.

Misses fall toward `OPEN`. A disposition recorded under a different name than the
filename is not found — `e-passes-audit` was struck 2026-07-29, but the closure report
records it as `E1-E5`, so it reads OPEN here. The producer over-reports outstanding
work and never under-reports it.

## Two producers, one boundary

`modules/backlog_autopilot/stop1_queue.py` is the other half, built independently the
same day. Keep both — they answer different questions:

| | this command | `stop1_queue` |
|---|---|---|
| role | **derived read model** — infers from evidence | **Owner-authored writer** — `resolve()` records a terminal status |
| writes | never | one front-matter key |
| answers | what does the evidence say became of this? | what has the Owner decided? |

A read model may not write and a writer may not infer. Their counts disagreed (22 vs
15); the 2026-08-06 reconciliation found **four causes, not one bug**: 9 from the
witness test vs. self-reported `status:` (by design), 2 from this module counting a
`STOP #2` under a STOP #1 heading (fixed — the checkpoint is now labelled), 1 from
`stop1_queue`'s literal `"STOP #1"` marker missing a hyphenated `STOP-1` (reported, not
patched — that module belongs to another pane), and 1 genuine source ambiguity where a
status asserts a closure and a wait in the same line.

Neither number was right. Two independent instruments disagreeing is what makes the
error findable at all.

## When to run it

Before opening a new STOP #1, and before quoting a count of open ones. Three separate
audits quoted "four open STOP #1s" without anyone being able to check the number; the
first real measurement found **18** STOP-bearing plans, not the 16 counted by hand.
