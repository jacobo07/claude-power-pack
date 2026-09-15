# Dataset GSD X

`claims.jsonl` is the dataset. This file is a projection of it and is allowed to
go stale; the JSONL is not.

## Why it is not the .txt in Downloads

`Downloads/Dataset GSD X 1.txt` is 23,052 lines: a prompt followed by four
pasted reasoning transcripts. It is real provenance and it stays where it is.
What it cannot do is answer a question mechanically. Nothing can ask it which
claims are observed, which are proposals, which have been superseded, or which
were wrong — so a later session re-derives what an earlier one already settled,
and a claim that has since been falsified reads exactly like one that holds.

One line per claim, with the epistemic state as a field, fixes precisely that.

## The state vocabulary

| state | means | required companion |
|---|---|---|
| `OBSERVED` | measured, with the instrument named | `evidence` |
| `CONTRADICTED` | was asserted, later falsified — kept, not deleted | `contradicted_by` |
| `DECISION` | a choice that closed a question | `rationale` |
| `NOT_BUILT_BY_DECISION` | decided against, which is not the same as forgotten | `revisit_when` |
| `UNPROVEN` | claimed by nobody yet; the gap is named on purpose | `resolved_by` |

`CONTRADICTED` entries are the point of the format rather than clutter in it.
`GSDX-R08` asserted that no prior art occupied this space because a grep for
"GSD X" found nothing. The grep was accurate and the inference was false, and
deleting it would leave the next reader free to make the same inference with the
same instrument. It stays, pointed at what disproved it.

## Rules

- **Zero inline code.** Architecture, contracts, evidence, decisions. The code
  lives in the repository and is referenced by path and line.
- **Every claim carries its instrument**, not only its conclusion. "36 NPCs"
  is a claim; "36 NPCs (regex over the raw export)" is checkable.
- **A superseded claim is edited, never removed.** `supersedes` and
  `contradicted_by` are how the corpus stays honest about its own history.

`python tools/test_gsd_x_dataset.py` enforces all three and fails on a state
whose companion field is missing.

## What this dataset currently says, in one paragraph

GSD Core v1.14.0 is a real Node runtime publishing a frozen host-integration
SDK, and it already owns nearly everything the GSD X corpus proposed building —
including the corpus's own declared first proof slice. Power Pack owns the one
thing GSD does not: an evidence-conditioned applicability engine. That engine is
reachable only when an operator types a slash command, and a constant tier menu
already occupies the event where it should run. So the gap is not a missing
capability. It is a missing event.
