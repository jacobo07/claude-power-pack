---
title: The trust root — proving the enforcement path runs, not just that it is correct
date: 2026-09-13
tier: T2
session: CDIO automatic-enforcement closure (follows callable-liveness-and-gate-honesty)
covers: [cdio, design_gate, review_gate, hook_boundary, trust_root, registration,
         abstain, revise_reachability, score_composition, liveness, subprocess]
---

# Enforcement trust root, and the honesty of a boundary test

Sibling of `callable-liveness-and-gate-honesty.md`. That one established that a
capability nothing calls is not a delivered capability. This one is the next
question: **something calls it — can you prove the thing that calls it runs?**

UKDL router pointer into `ukdl-universal.md` is **still OWED**: that file carries
another session's uncommitted work, on 2026-09-13 as on 2026-09-12. Add it when
their edits land.

## HARD RULES

**HR-BOUNDARY-PROOF-001 — When correctness depends on a process boundary, in-process
invocation is supporting evidence, never completion evidence.**
Every CDIO gate called `design_gate()` directly. The product spawns node, which
spawns python, and turns the second process's stdout into a `permissionDecision`.
Proof, not argument: break ONLY the serialisation between them — the gate still
computes the correct BLOCK, but its stdout stops being parseable — and
`test_design_gate.py` stays GREEN while `test_hook_boundary.py` goes RED. The
enforcement is entirely absent and every pre-existing suite is content. A suite
whose subject is a boundary must cross it.

**HR-EVIDENCE-FLOOR-001 — Absence of evidence must never arrive at the top of a
scale, and neither must collapsed evidence.**
Two spellings of one defect, both measured here. `score_review([])` returned
100/APPROVE/done: a formula that starts at 100 and subtracts hands the strongest
claim to the weakest evidence. And N independent contradictions joined into one
verdict deduct once, which made `REVISE` structurally unreachable — the floor was
84, already ≥ APPROVE. Abstention gets its own state, kept away from the neutral
one; N wrongs cost N deductions.

## PROCESS RULES

**PR-VERDICT-CONTRADICTS-EVIDENCE-001 — When a verdict contradicts the evidence
printed beside it, the parser is wrong, not the world.**
The duplicate-registration scan reported "no matcher reaches it twice" minutes
after the duplicate had been measured by hand. Cause: it grouped per settings
ENTRY, and the two registrations live in two SEPARATE entries that share a
matcher, so the intersection inside either alone is necessarily empty.
Generalised: **a grouping key finer than the effect being measured can only ever
return "clean".** Group at the granularity of the effect — here, per TOOL, because
the question is "when the harness runs tool T, is this script reached twice".

**PR-NEGATIVE-CONTROL-NEEDS-POSITIVE-EVIDENCE-001 — An assertion that something did
NOT happen must be paired with evidence that anything happened at all.**
`decision != "deny"` passed against `{}` — which is equally what a throttled hook,
a crashed gate and a hook that never found the document return. The gate had never
run. Require the system's own acknowledgement (here: the hook reporting which
verdict it reached, on THIS fixture's document), not merely the absence of the
thing you feared.

**PR-WIDENING-IS-A-SEPARATE-QUESTION-001 — After making a state reachable, ask what
ELSE became reachable along the same axis.**
Splitting one verdict into N was approved to make `REVISE` reachable. Carried
further it makes BLOCK reachable with no critical at all: six majors → 52 → the
hook DENIES a write that scored 84/APPROVE the day before. Verifying the
consequence you aimed at and stopping is how the one past it ships unannounced.
Pin the widening as a documented decision — an undocumented one is how a gate gets
switched off; a documented one can be argued with.

## TRAPS

**T-SET-VIEW-CANNOT-COUNT-001.** A registry scan returning a SET of names is
structurally incapable of detecting duplication — a set is precisely the structure
that discards "how many times". `_registered_hooks` correctly answered the question
it was built for ("is this registered at all") and was blind to a hook registered
twice per tool. The repair is a second VIEW of the same parse, never a second
parser: regex, surface list and fail-open contract stay single-sourced.

**T-TRUNCATED-COMPOSITE-KEY-001.** A cache/throttle key that is sanitised and then
truncated collides on any long shared prefix. Five fixtures under one temp root all
reduced to `CUsersUserAppDataLocalTemptmpoyp` — the distinguishing segment fell off
the end at 32 characters — so case 2 silently throttled case 3. The symptom is not
an error; it is a component going quiet, which reads as consent.

**T-UNKNOWN-VERDICT-DEFAULTS-TO-ALLOW-001.** `{...}.get(verdict, 0)` mapped every
unrecognised verdict to exit 0 = ALLOW, silently. Adding one verdict to the scorer
was enough to reach it. Fail-open is right for a gate that must not block real work;
fail-open WITHOUT A WORD is the unknown-becomes-favourable pattern. Keep the
permissive default, make it announce itself.

**T-SAME-MODULE-CALL-READS-AS-DEAD-001.** `callable_reach` attributes references by
qualified cross-file name, so a public function whose only production caller lives
in its OWN module reads as unreached. This is the detector's accusing direction
working as designed — it is loud about a live thing rather than quiet about a dead
one — but the resolution must be a recorded `--absorb-new` with a reason, never a
silent re-freeze.

## What is still not proven

- The hook EMITS a deny; that the harness HONOURS one is the harness's own contract
  and is exercised by nothing here.
- No fixture drives a successful UPWARD walk to a DESIGN.md in an ancestor, nor
  proves the walk stops at a `.git` boundary.
- No rendered surface is observed automatically; the reduced-motion floor remains
  reachable only from the agent path.
- Nothing runs the callable ratchet or this boundary suite automatically. They are
  CLI gates, and therefore still subject to the defect they detect, one level up.
