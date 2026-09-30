---
name: evaluation-corpus-governance
description: Evaluation-boundary doctrine for anything that learns from a corpus and is later judged against it (fine-tuning, retrieval corpora, knowledge bases, prompt libraries, rule distillation). Use BEFORE ingesting material: partition by contamination group not by row, generated seeds never caller-supplied, edits to a registered item refused rather than re-drawn, held-out fraction sized to evaluator throughput, the learning-side gate bound where ingestion really happens, three-outcome screening, and claims decomposed to their real size. Core rule - govern, register and partition before teaching; a corpus cannot be un-taught.
---

# Evaluation Corpus Governance

Any system that learns from a body of material and is later evaluated against
that same body must have its evaluation boundary governed **before** ingestion.
This covers model fine-tuning, retrieval corpora, knowledge bases, prompt
libraries, rule distillation — anything where material can reach the system's
reasoning and later be used to test it.

The ordering is not procedural, it is physical:

    GOVERN → REGISTER → PARTITION → FREEZE → TEACH one side → RESERVE the other

A corpus cannot be un-taught. Every decision below is cheap before ingestion and
impossible afterwards, and each one is the kind that feels reasonable to defer.

## Why the obvious defence is the wrong one

"Exclude cases the system learned from" excludes everything, because the same
body is usually both the teaching material and the only realistic source of
evaluation cases. The mechanism is a **partition** with two gates refusing in
opposite directions — one refuses held-out material at the learning boundary,
the other refuses learned material at the evaluation boundary — reading one
assignment made once, before either consumer looked.

Build both. The learning-side gate is the one that gets left out, because
nothing visibly breaks without it: the evaluation still runs, the scores still
appear, and they are recall wearing the costume of judgement.

## Partition the contamination group, not the exported row

One real-world situation typically exports as several items — a follow-up, a
revision, a summary, a translation, a re-ask. Assigning per item puts siblings on
opposite sides: one teaches the answer the other is tested on.

**Nothing downstream can detect this.** There is no error, no anomaly, no
implausible number — just a score that is too good, in a system where a good
score is what everyone wanted. So it has to be prevented at assignment time.

An item with no declared group is its own group. Safe by construction, free when
there are no siblings. Let the *source* declare the grouping where it can; it
knows which of its exports describe one situation and you do not.

## A re-roll attempt must produce a refusal, not a new answer

Determinism alone is not integrity. Ask what an operator who dislikes an
assignment can change, then check what each change produces:

| Change | Must produce |
|---|---|
| rename the file | the same assignment |
| reorder the export | the same assignment |
| re-submit the corpus | the same assignment, or a refusal |
| restart the process | the same assignment |
| **edit the content** | **a refusal** |

The last row is the one that gets designed wrongly. An edited item no longer
matches its recorded identity, and the tempting behaviour is to treat it as new
material — which hands back exactly the capability the design removed. The
attacker's move is not "give me a new draw", it is "make this look like a
different item", and answering that with a fresh label is identical to letting
them choose.

So: **membership by location, identity by content.** Either alone has a hole and
they are different holes. Content identity cannot survive an edit; location
cannot say which item a file is. Together, an unrecognised item inside a governed
boundary is refused, and a recognised item found outside it is still that item.

## Generate the seed; never accept it from the caller

If assignment is a hash of (identity, seed) and the identities are known before
registration — they arrive *with* the corpus — then a caller-supplied seed can be
ground offline in seconds until the awkward cases land on the teaching side. The
determinism that makes the split honest is the same property that makes the
search cheap.

Generate it from a CSPRNG at registration. If a fixed-seed path is needed for
tests or backup restore, give it a name nobody types by accident and **ship a
test that enumerates production modules and asserts none calls it** — a docstring
saying "internal use only" is not a boundary.

## Choose the fraction from evaluator throughput, not convention

Held-out material is an inventory, not a dataset. Each unit is spent once: the
moment an outcome is revealed it has been seen, and no later run on it is an
unseen evaluation however it is presented.

So size it against what evaluation actually costs — how many units a reviewer
will genuinely assess per wave, and how many waves are wanted — not against a
habitual percentage. Beyond that point the option value flattens against reviewer
supply while the knowledge you gave up keeps growing linearly.

Reading the *structure* before declaring the fraction is legitimate: how many
independent groups exist, how large they are. The fraction cannot select *which*
groups are reserved — only the seed does that, and the seed is not chosen by a
human. Reading the *content* first is not legitimate, and that is the line.

## Bind the gate where ingestion actually happens

The most likely failure is not a weak gate. It is a correct gate with no caller.

Check where the real ingestion path writes, and whether the gate can be reached
from there **at all**. A gate that resolves against one data plane cannot be
called from a writer on another; the two halves are then unable to touch, no
matter how correct each is, and nothing about the running system makes that
visible. A docstring instructing a future reader to call it is operator
discipline, which is what the design exists to replace.

Bind before validation, too, or a refusal ends up conditional on whether the
material happened to be well-formed.

## Give the screen three outcomes

- registry readable → screen
- registry provably not deployed → admit, and log it loudly
- **registry unreadable for any other reason → raise**

A database briefly unreachable and a database reporting nothing governed return
the same empty answer. Only one of them is safe to ingest under. The middle case
is legitimate only when it is *known* that nothing is governed — because the
table does not exist — rather than *unknown*.

## Isolation is a chain, not a per-reader audit

To claim held-out material cannot be retrieved, do not secure each retrieval
surface. Show that the material never enters the pipe they all read from:
enumerate the writers of each store in the chain and prove each has exactly one,
gated. Enumerate them **structurally** (AST, schema, registry) — grepping for the
gate finds the modules that have it, which is the opposite of the question.

Then state the claim at exactly its real size. "Cannot be retrieved through the
system's knowledge surfaces" is not "the bytes are unreachable"; the files are
still on disk and anyone with filesystem access can open one.

## Claims must decompose

Keep these separable, because they are not interchangeable and the weaker ones
are usually the true ones: infrastructure exists · policy declared · corpus
registered and partitioned · one side taught and the other reserved · held-out
cases evaluated · the system matched or beat human experts on them · it predicted
real outcomes.

And bound the claim by exposure that was actually controlled. If the operator
also absorbed the source material through some other channel — a course, a
mentorship, their own prior writing — no partition removes that. The supportable
claim is about **exact case and outcome exposure**, never "learned nothing from
this material". Render that limitation beside the numbers, not in a document
nobody opens.

## DON'T

- **Don't let a benchmark hide its failures.** Exclusions need explicit reasons,
  preserved history, and visibility in the aggregate. A benchmark that cannot
  embarrass the product is measuring nothing.
- **Don't freeze an empty manifest.** It refuses the whole corpus while reporting
  that the *files* are unrecognised, pointing the reader at the wrong thing.
- **Don't let a retry change the population.** Idempotent re-declaration is a
  no-op; a re-declaration that would *change* an item must raise, or the contents
  depend on how many times someone retried.
- **Don't present a revealed case as unseen again.** Once consumed, it is
  knowledge; its future value is learning, not evidence.
- **Don't build the fixture with the same library that reads it.** It inherits
  the reader's assumptions and cannot falsify them — see the BOM below.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/evaluation-corpus-governance.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
