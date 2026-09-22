---
id: UACF-UKDL-ADJUDICATION
name: Adjudication of the eight surface-architecture UKDL seeds
type: ukdl-adjudication
domain: uacf
status: adjudicated; canonical write DEFERRED-BY-CONCURRENCY
supersedes: none
adjudicates: UACF-UKDL-SEED
date: 2026-09-22
session: mission-002
---

# Adjudication — the eight seeds from `UACF-UKDL-SEED.md`

This file is a SIBLING of the seed record, never a rewrite of it. The estate's
ledger discipline (`ukdl_queue.py`: "a transition is APPENDED ... rows are never
mutated, so the queue's history stays auditable") applies to knowledge promotion
as much as to the queue that tracks it.

Each seed was adjudicated **against the canonical corpus**, not against memory.
Every verdict below names the line in `ukdl-universal.md` that was read to reach
it. A verdict reached without reading the named parent is the exact failure the
first seed is about.

---

## 0. Why the canonical archive was NOT written this session

`vault/knowledge_base/ukdl-universal.md` — 828,642 bytes, ` M` (dirty), on a
branch carrying 19 foreign commits from a live concurrent session.

Two independent readings, twelve minutes apart:

| reading | wall clock | archive mtime | age |
|---|---|---|---|
| 1 | 2026-09-22 10:33:37 | 10:28:15 | 5.4 min |
| 2 | 2026-09-22 10:45:56 | **10:42:12** | 3.7 min |

The file moved BETWEEN the two readings. That is positive evidence of an active
writer, not a stale dirty flag — the distinction matters, because a stale flag
would have been safe to write through and an active writer is not. Pathspec
isolation is file-granular and cannot protect two writers inside one file
(`~/.claude/rules/concurrent-writers-shared-tree.md`).

**Classification: `DEFERRED-BY-CONCURRENCY`.** Not "done", not "blocked" — the
adjudication is complete and the write is owed. The next quiet tree closes it,
and this file is the executable instruction for doing so.

The seeds were NOT injected into `modules/fable_distillation/ukdl_queue.py`
either, and that was a deliberate refusal rather than an oversight. That queue's
candidates carry fingerprints and session ids minted by the fable-distillation
flywheel (`fd_07_flywheel`). These eight came from the surface-architecture
build. Minting rows to make them appear in a queue that did not produce them
would be supplying provenance that should only ever be computed — the queue
would then read as evidence about a pipeline that never ran.

---

## 1. Verdicts

Eight seeds in, eight adjudicated: **five promoted as new**, **one derived and
promoted**, **two merged into existing rules**, **one refused from the universal
corpus**. Seed count is not the measure; a near-duplicate is a cost, not a gain.

### MERGE — 2

**S1 · `T-D2A-FALSE-FOLD-ON-VOCABULARY-001` → merge into
`PR-OWNERSHIP-EVIDENCE-BEATS-SCORE-001`** (`ukdl-universal.md:41`).

The parent already states that a `file:line` reading overrides a similarity score
*in both directions*, and that a DEFER verdict means UNKNOWN and never NEW. Read
in full, it does **not** cover the two things this seed measured, and both are
genuine additions rather than restatements:

1. The parent's examples are all mislabels at LOW or ambiguous confidence. This
   incident failed at the **highest** confidence the instrument can emit — a 95 %
   FOLD into `MOD-ARCHITECTURE-HORIZON`, where the only thing the two systems
   shared was the word "architecture" and the named parent's own docstring says
   it simulates nothing and selects nothing. High confidence is not an exemption
   from reading the mechanism; it is the case where nobody reads it.
2. **Flat-instrument corollary.** In the same run, 17 of 20 systems returned
   DEFER at *exactly* 45 %. One instrument returning one number to seventeen
   different questions carries no information, and a spread of identical scores
   should be read as instrument failure before it is read as a finding about the
   subjects.

Added as two clauses on the parent. A second trap saying "read the mechanism"
beside a rule that says "read the mechanism" would make the corpus worse.

**S8a · self-declared-string half of `T-A-GATE-THAT-GRADED-ITSELF-WITH-A-STRING-001`
→ merge into `PR-NO-SELF-CERTIFICATION-001`** (`ukdl-universal.md:4904`).

The parent already refuses a stored epistemic level in favour of a derived one,
and already caps a producer that grades its own claims. The sharpening this
incident supplies is about **reachability**, which the parent does not mention:
the dangerous configuration is not merely that a self-certifying producer exists,
but that the self-certifying producer was the **reachable** one
(`gsd_x/mission/closure.py:116`, a string defaulting to `"UNPROVEN"`) while the
honest derivation (`done_gate/strength_ladder.assess`, thirteen rungs,
three-valued evidence) had **no caller at all** and is recorded `PROSE_ONLY` in
`callable_inventory.json:571-573`.

An honest grader nobody calls and a dishonest grader everybody calls produce one
observable: a verdict. Added to the parent as the reachability clause.

### PROMOTE — 5 new, 1 derived

**S2 · `T-SUBSTRING-DETECTOR-FLAGS-ITS-OWN-RULE-001`** — trap. No parent found.
A prohibition that names its forbidden examples trips its own substring detector;
a matcher cannot distinguish a mention from a violation. The durable half is the
second clause: **do not answer it with an exemption list**, because an exemption
written by the rule's author exempts everything. Carries the unanchored-match
corollary (`contaminates_kernel` has no `\b`, so `"sign"` hits `"design"` and
`"form"` hits `"information"`), and therefore the rule that domain vocabulary
must be multi-token. Evidence: `c190bd5`.

**S3 · `T-DISQUALIFIER-INFLATION-001`** — trap. No parent found. A scoring
function summed `requires + disqualifiers`, so the archetype declaring the most
ways it could LOSE won. A condition that did not fire is the absence of evidence
against; it is never evidence for. Universal to any weighted selector. Evidence:
`e17eb4f`, caught by a contrasting-fixture set and invisible to unit tests.

**S4 · `T-RESIDUAL-MAKES-AN-OUTCOME-UNREACHABLE-001`** — trap, cross-linked to
`HR-THRESHOLD-BAND-MUST-BE-REACHABLE-001` (`ukdl-universal.md:159`) as its
non-numeric sibling. That parent was read and its TRIGGER is explicitly "writing
or validating a threshold" — a numeric band. This is a different mechanism: an
always-true member added to a decision SET, which makes "nothing matched"
impossible and silently retires an outcome. `STRUCTURED_CONFIGURATOR` is always
justified, so `ABSTAIN` became unreachable while remaining declared, tested and
documented. Evidence: `e17eb4f`.

**S5 · `PR-INHERIT-VERBATIM-NEVER-PARAPHRASE-001`** — process rule. No parent
found. When a child inherits a boundary from a parent, copy the strings; do not
improve the wording. `HR-APA-017` compares by value, so an improved paraphrase
reads as a **dropped** boundary and `derive()` refused the first real seed. The
durable fix is structural rather than behavioural: declare ADDITIONS only and
union the parent's list at build time, so a new parent boundary is inherited
automatically instead of being silently lost. Evidence: `b6dc52a`.

**S6 · `PR-FIXTURES-FALSIFY-THEY-DO-NOT-CONFIRM-001`** — process rule.
Cross-linked to `T-FIXTURE-NEUTRALIZED-BEFORE-OBSERVATION-001`
(`ukdl-universal.md:8368`), which was read and is a different failure: a fault
disarmed by the subject before observation. This one is about **ordering and
oracle authority** — write the expected outcome of every fixture BEFORE running
it, and when reality disagrees decide explicitly whether the expectation or the
code was wrong, then say which, in the fixture. In this build the contrasting set
produced three genuine defects and two wrong expectations of mine; had the
expectations been written after the first run, all five would have been recorded
as passes. Evidence: `e17eb4f`.

**S8b · `PR-SKIPPED-INSTRUMENT-MUST-DROP-THE-RUNG-001`** — process rule,
DERIVED from the second half of S8 and promoted in its own right because it is
the rule Mission 002 Slice 5 implements.

A skipped instrument removes the evidence that instrument would have supplied.
The rung falls; it never holds at a prior value. `tools/prg_assess.py --fast`
demonstrates the correct behaviour by dropping the ladder from
ADVERSARIALLY-VERIFIED to WIRED when it omits the one instrument that could
measure reachability. A probe that carried the unmeasured rung forward would be
performing exactly the laundering the gate exists to refuse.

Generalises beyond this estate: a previous run does not prove the current tree, a
mock does not prove an integration, registry reachability does not prove
invocation, invocation does not prove consumption, and consumption in a fixture
does not prove product behaviour. Evidence: `d1ee4ed`.

### REFUSED from the universal corpus — 1

**S7 · `T-DATACLASS-NEEDS-SYS-MODULES-REGISTRATION-001`** — **not promoted.**
Retained here, in full, with its evidence (`b6dc52a`).

The trap is real: a module loaded via `importlib.util.spec_from_file_location` is
absent from `sys.modules`, `@dataclass` resolves
`sys.modules.get(cls.__module__).__dict__` (`dataclasses.py:749`), and every
dataclass in that module raises `AttributeError: 'NoneType' object has no
attribute '__dict__'` — a message pointing nowhere near its cause. The fix is to
register the module before `exec_module` and pop it on failure.

It is refused from the universal corpus for two reasons, and the second is the
stronger:

1. It is single-language and single-mechanism — a Python stdlib interaction,
   reached here only because a package directory name contains a hyphen that
   `import` cannot spell. LAW 10: applicability before universalization.
2. A plausible parent exists — `T-JIT-MODULES-UNIMPORTABLE-001`
   (`ukdl-universal.md:5918`) — **which I did not read.** Promoting a rule
   alongside an unread candidate parent is precisely the near-duplicate risk that
   S1 is about. Refusing on an unread parent is honest; promoting on one is not.

**Reopen condition:** read `T-JIT-MODULES-UNIMPORTABLE-001`. If it does not
cover dynamic-load dataclass registration, promote S7 as a trap under it. If it
does, merge the `sys.modules`-before-`exec_module` clause into it.

---

## 2. The write that is owed

When the archive is quiet — no dirty flag, or an mtime old enough that no writer
is live — apply, in this order:

1. Two clauses onto `PR-OWNERSHIP-EVIDENCE-BEATS-SCORE-001` (highest-confidence
   failure; flat-instrument corollary).
2. One reachability clause onto `PR-NO-SELF-CERTIFICATION-001`.
3. Five new entries: S2, S3, S4 (traps), S5, S6 (process rules).
4. One derived entry: `PR-SKIPPED-INSTRUMENT-MUST-DROP-THE-RUNG-001`.
5. Resolve S7's reopen condition by reading `T-JIT-MODULES-UNIMPORTABLE-001`.

Re-measure the archive mtime **immediately before** the write, not at the start
of the session that performs it. A reading taken before a long command expired
the moment the command started.
