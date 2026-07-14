# Plan — DAIF-08 §11.7 Two-Arm Behavioral Trial (2026-07-13)

**This file is written BEFORE the trial runs.** The sample and the rubric below are sealed here so
that neither can be amended after the outputs are visible (DAIF-03 10.4: a rubric written after the
outputs exist is a rubric written to fit them).

## PASO -1 — what the corpus actually says

**DAIF-08 §11.7** does not define a procedure. It states the prohibition (no savings figure asserted
in advance, because an unmeasured efficiency claim is a fabrication), names the three quantities to
record on each arm — **reasoning cost**, **fidelity as behavioral equivalence**, **rework** — and
then *composes* the method rather than reinventing it: "the behavioral trial DAIF-03 Part X already
defines." So the procedure is DAIF-03 Part X, and it was read in full before this plan.

**DAIF-03 Part X — the constraints it imposes, each of which binds this trial:**
- 10.2 The sample is drawn and sealed BEFORE the compilation exists. **Ours is not** — the compiler
  shipped in SCS C96, yesterday. This is recorded, not hidden, and it caps what the trial may
  conclude (below).
- 10.3 Control arm = full source S. Compiled arm = the pack, with **no tool by which S could be
  reached**. Everything else identical: same model, same build, same window, same tooling.
- 10.4 Blind adjudication against a rubric fixed in advance, by an actor that is not the compiler.
- 10.5 Report a **vector**, never a pooled score. "Source re-reads attempted" is named the sharpest
  single signal in the procedure.
- 10.6 **"A single passing mission proves that a single mission passed."**
- 10.7 A compiled arm that BEATS the control is held at DEGRADE pending root-cause — an unexplained
  win is an unmeasured mechanism.

## Correction to the brief (reported, not silently absorbed)

The brief numbers the clauses as: c3 = "continues without re-reading", c4 = "invents no new claims".
The corpus (11.5) says: **c3 = the current state is correctly identified**; **c4 = the actor
continues without indiscriminate re-reading**. "No invented claims" is **not one of the six
clauses** — it is the extra gate already shipped and passing (`V-NO-INVENTED-CLAIMS`). All three are
measured; they are labelled by the corpus's numbering.

## The sample (sealed — deterministic selection rule, declared before any run)

Rule: the 3 real session transcripts of this project with the largest conversational source text
whose full source fits one context window (5k–120k est. tokens). No mission was inspected for
whether the pack would do well on it. Selection is reproducible from disk by the rule alone.

1. `c718d3f5-7a13-4c49-86ef-3f4c5ed63a43` — 305,356 chars (~76k tok)
2. `78014709-12f5-4d90-9d66-2e85aae1fab3` — 171,913 chars (~43k tok)
3. `f2910b35-5d62-485c-a011-f556e8b13657` — 171,199 chars (~43k tok)

Stratum: **representative only.** The adversarial and regression strata of 10.2 are NOT run. That
is a declared gap, not an oversight.

## The arms

Identical in every respect except the input packet: same model (`claude-sonnet-5`, build recorded
from the CLI), same window, **zero tools in both arms** (`--disallowed-tools` denies Read/Glob/Grep/
Bash/Write/Edit/Task/WebFetch/WebSearch), same continuation task verbatim, stdin-delivered.

- **Arm A (compiled):** the resume pack JSON. Nothing else. No path by which the transcript is reachable.
- **Arm B (control):** the full conversational source of the same session (every user + assistant
  turn). Tool-result bodies are excluded — they run to millions of characters and fit no context.
  This exclusion makes the control arm CHEAPER than a true full-source arm, which is conservative:
  it can only understate the pack's advantage, never inflate it.

## The rubric (fixed in advance; adjudicator is deterministic code, arm labels stripped)

- **Clause 3 — state identified.** PASS iff the arm emits all three of done / in-flight / not-started
  with ≥1 item total, and (Arm A) every id it cites exists in the pack.
  **Declared limit:** correctness against an independent ground truth is NOT measured, because the
  only obligation ledger in the estate is the artifact's own producer, and scoring the artifact
  against its own output is the circular rubric 10.7 forbids. What is measured is that a grounded
  state was produced, not that it is true. This is an honest downgrade of the clause.
- **Clause 4 — no indiscriminate re-reading.** PASS iff `need_source_access` is false and
  `source_requests` is empty. Fully measurable; 10.5's sharpest signal.
- **Invention (extra gate).** Arm A's cited ids ⊆ pack ids.
- **Economic.** Real input/output tokens and USD from the API, per arm. Session overhead (system
  prompt, CLAUDE.md, hooks) is measured once with an empty task and reported separately; it is
  identical in both arms and cancels in the delta.
- **Equivalence.** Word-overlap between the arms' open-obligation sets. Reported as a number, never
  as a verdict.
- **Safety** (constraints violated, obligations dropped): **N/A** — the mission is read-only.
  Recorded as N/A rather than as a pass.

`token_delta_saved = B − A`. If negative, the pack cost MORE than the source, and the number is
reported negative. No floor at zero, no re-run to hunt a better answer (DAIF-21 Part XIX lists this
as one of its three honest risks).

## What this trial may and may not conclude

May: per-mission measured facts for clauses 3 and 4, and a real cost delta.
**May not:** an artifact-level PASS. The sample post-dates the artifact (10.2), only the
representative stratum is run, and three missions is a small sample (10.6). The artifact-level
fidelity verdict is therefore capped at **DEGRADE**, and if Arm A beats Arm B the outperformance is
held at DEGRADE pending attribution (10.7).
