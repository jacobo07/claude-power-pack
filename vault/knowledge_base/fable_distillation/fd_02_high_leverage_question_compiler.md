# FD-02 — High-Leverage Question Compiler (S-QUESTION)

> The only FD dataset that acts *before* the frontier model speaks. Where FD-01 extracts the delta
> from an answer, FD-02 shapes the *question* so that the answer is likelier to contain a delta worth
> extracting. Its thesis: the ceiling of what a session can distill is set by the question, not the
> model — a low-leverage question cannot produce a high-leverage delta no matter how capable the
> model is. Parents: the one_shot Q&A scaffold (which it generalizes from a fixed six-question ritual
> into a leverage-ranked compiler) and CO-03 (which routes each compiled question to the cheapest
> sufficient model). Sealed under **SCS C82**. Guarantee level (CO-10): **rung-2 advisory** — it
> proposes and ranks questions; the session chooses, and the choice is logged for audit.

---

## Part I — Mission, the Question-Quality Ceiling, and the Leverage Taxonomy

### I.1 Mission

FD-02 exists because the suite's entire output is bounded by a variable no other dataset controls:
the quality of the question put to the frontier model. Every downstream station — FD-01's extraction,
FD-03's routing, FD-04's decay test, FD-05's arbitrage, FD-06's writeback — operates on whatever the
model produced, and what the model produced is a function of what it was asked. A brilliant extraction
engine applied to the answer to a trivial question yields, at best, a trivially-classified DISCARD.
FD-02's mission is to raise the ceiling: to compile, before the session spends a frontier token, a
ranked set of questions engineered to make the resulting answer carry a genuine, above-floor,
portable delta. It is the input-side complement to FD-01's output-side extraction, and the two
bracket the frontier call exactly as FD-00's admission and deposit clauses do — one improves what
goes in, the other captures what comes out.

The mission is deliberately framed as *compilation* rather than *generation*, and the distinction is
load-bearing. Generation would mean inventing questions from the task alone; compilation means taking
the task, the FD-00 baseline (what the stack already knows), and the suite's record of where the
stack is weak (from FD-01's class distribution and FD-04's decay results), and *deriving* the
questions whose answers would most move the dependence curve. A compiler has inputs and an
optimization target; a generator has a vibe. FD-02 is a compiler because its output must be
defensible: each compiled question carries a leverage score and a rationale, so the session can see
*why* this question is worth a frontier token and the audit can later check whether high-leverage
questions actually produced high-value deltas. A question that cannot state why it is worth asking is
not compiled; it is guessed, and the compiler rejects it.

The deeper reason the mission matters is the same asymmetry FD-00 identifies on the admission side.
Asking a low-leverage question is not merely a small waste; it is a *structural* waste, because the
session then spends a frontier token, receives an at-floor or DUP answer, and FD-01 correctly
discards it — the token bought nothing, and worse, it consumed a session slot that a high-leverage
question could have occupied. The cost of a bad question is therefore the opportunity cost of the good
question that was not asked, which for a rare and expensive frontier session is the highest-value
resource the suite spends. FD-02 exists to protect that resource by ensuring the questions asked are
the ones most likely to produce a keepable delta.

### I.2 The question-quality ceiling (why the model is not the bottleneck)

The counter-intuitive premise of FD-02 is that in a mature stack the frontier model is rarely the
binding constraint on distillation output — the question is. This follows directly from the dependence
curve. As the floor rises, the set of questions whose answers exceed it shrinks; most obvious
questions about a well-worked domain now have at-floor answers, because the stack already distilled
them. The remaining above-floor deltas live behind *non-obvious* questions: the ones that probe the
edge of the floor, that force the model to synthesize across domains the stack has not connected, that
demand a critique the stack cannot self-generate, or that target a capability the stack has repeatedly
had to escalate to the frontier for. A session that asks the obvious questions of a mature domain will
correctly receive DISCARD after DISCARD and conclude, wrongly, that there is no delta left — when in
fact the delta was behind a question no one thought to ask. FD-02's job is to find those questions.

This reframes the whole session economy. In an immature domain (empty floor) almost any question
produces a delta, so question compilation adds little and the session should spend freely. In a mature
domain (high floor) the delta is scarce and question-gated, so compilation is where the leverage
lives, and a session that skips it will systematically under-distill. FD-02 therefore scales its
effort to the floor's maturity: cheap, shallow compilation on an empty-floor class (any question
works), deep, ranked compilation on a mature class (only the right question works). This is the same
task-aware budgeting CWOPS §2.5 prescribes for step caps — different task classes warrant different
default effort — applied to the question rather than the loop.

### I.3 The leverage taxonomy

FD-02 classifies and ranks candidate questions by *leverage*: the expected magnitude and portability
of the delta the answer would carry, weighted by the probability the question is above-floor. Four
leverage archetypes anchor the ranking, drawn from the prompt's own framing and sharpened into
measurable categories.

- **Irreversible questions.** Questions whose answers commit the stack to a design direction that is
  expensive to reverse — architecture choices, data-model decisions, protocol definitions. These have
  the highest leverage because the delta they produce propagates: a good architectural answer improves
  every future session in that domain, and a bad one is a debt paid for months. The frontier model's
  greatest marginal value over a cheaper rung is precisely on these high-stakes, hard-to-reverse
  judgments, so they are the questions most worth a frontier token. CWOPS §1.1's reversibility branch
  is the direct parent: irreversible operations warrant the most deliberation, and here the most
  capable model.
- **System-generating questions.** Questions whose answers are not a single artifact but a *reusable
  protocol* — "how should we always do X?" rather than "do X here." A system-generating answer is a
  portable deposit by construction: it distills into a recipe, a checklist, or a gate that serves the
  whole class, which is exactly the deterministic/mid-model portability the suite prizes. These
  questions have high leverage because their delta's reuse potential is high — one answer, many future
  saved calls.
- **Critique questions.** Questions that ask the model to find the flaw the stack cannot see in its
  own work — "what is wrong with this design?", "where does this fail under load?" The stack cannot
  self-generate a critique of its own blind spots (that is the definition of a blind spot), so a
  critique answer is reliably above-floor: it is a capability the stack structurally lacks. This is
  where the frontier model's adversarial reasoning is irreplaceable and where CDIO's review-swarm
  pattern is borrowed but generalized beyond design.
- **Dependence-reducing questions.** Questions whose answers directly attack the stack's frontier-
  dependence — "how would you make this runnable without a frontier model?", "what is the deterministic
  core of this judgment?" These have leverage precisely because their deltas carry a
  `deterministic`/`small-model` portability target: they are questions engineered to produce the
  portable capabilities that bend the dependence curve fastest, and they are the questions FD-05 most
  wants asked.

The four archetypes are not mutually exclusive — the best questions are often several at once (a
system-generating critique of an irreversible decision is maximal leverage) — and the compiler scores
a candidate on all four axes and sums, rather than forcing a single label. The taxonomy's purpose is
to give the leverage score defensible components, so a high score can be explained ("high on
irreversible and dependence-reducing") rather than asserted.

### I.4 Difference from existing systems

**Versus the one_shot Q&A scaffold.** one_shot's ULTRA workflow includes a mandatory six-question
Q&A pass — a fixed, valuable ritual that surfaces requirements before planning. But it is *fixed*: the
same six slots regardless of domain maturity, and oriented to requirement-elicitation, not delta-
maximization. FD-02 generalizes it into a compiler: a variable-length, leverage-ranked set derived
from the baseline and the stack's weak spots, oriented to producing distillable deltas. one_shot asks
"what do we need to know to plan?"; FD-02 asks "what should we ask the frontier model so its answer is
worth keeping?" The former is about the task; the latter is about the distillation.

**Versus CDIO (design critic swarm).** CDIO critiques *outputs* — a rendered surface, a design — via
its six-lens review. FD-02 compiles *inputs* — the questions — and it borrows CDIO's critique
discipline only for the critique-question archetype, generalized from design to any domain. CDIO acts
after an artifact exists; FD-02 acts before the artifact is requested. They are complementary book-
ends, not competitors, and FD-02 explicitly does not review outputs (that is CDIO's and FD-01's job).

**Versus prompt-engineering skills.** General prompt-engineering guidance improves how a single prompt
is phrased for clarity and reliability. FD-02 is not about phrasing; it is about *selection and
ranking* — which questions to ask at all, ordered by expected delta value against this stack's floor.
A perfectly-phrased low-leverage question is still a wasted frontier token; FD-02's contribution is
choosing the high-leverage question in the first place, a decision phrasing-level guidance does not
address.

### I.5 What FD-02 does NOT duplicate (explicit)

FD-02 does **not** route questions to models (CO-03 owns routing; FD-02 hands CO-03 the compiled
question and CO-03 picks the substrate), does **not** classify the resulting answer (FD-01), does
**not** review outputs (CDIO/FD-01), does **not** manage the session budget (CO-00), and does **not**
generate the requirements plan (one_shot). It performs one operation — compile and rank the questions
worth asking — and emits a ranked list with rationales. If an edit to FD-02 begins to route, classify,
or plan, it has left its lane and must be relocated.

### I.6 Core principles

- **The question is the ceiling.** A session cannot distill above the leverage of the questions it
  asks; compilation is where a mature-domain session's value is won or lost.
- **Compile, do not generate.** Every question carries a leverage score and rationale; an
  unexplainable question is rejected.
- **Scale effort to floor maturity.** Cheap compilation on an empty floor, deep compilation on a
  mature one — the CWOPS task-aware budget applied to questions.
- **Leverage is multi-axis.** Irreversible, system-generating, critique, and dependence-reducing are
  scored and summed, not forced into one label; the best questions are several at once.
- **The compiler is auditable against outcomes.** A high-leverage question that repeatedly produced
  DISCARD answers is mis-scored; the leverage model is graded against FD-01's actual class results.

### I.7 Why the question is the moat's leading edge, not the model

FD-02 makes explicit a claim the rest of the suite depends on but does not state: in a world where the
frontier model is a commodity available to every competitor with an API key, the *questions a system
knows to ask* are proprietary in a way the model is not. Two teams share the same Fable; they do not
share the same accumulated knowledge of where their own stack is weak, which irreversible decisions
are still open, or which capabilities they keep having to escalate for. That knowledge — the input to
FD-02's Step 2 weak-spot targeting — is a function of the team's own distillation history, and it is
therefore un-replicable over a weekend in exactly the sense CWOPS Part IV attributes to a data
flywheel. The compiled question is the leading edge of that moat: it is the point where the stack's
proprietary self-knowledge is converted into a frontier prompt that no competitor, lacking that self-
knowledge, would think to write. A competitor asking the obvious questions of the same domain gets
obvious, at-floor answers; the stack asking its weak-spot-targeted questions gets the scarce above-
floor deltas, because it alone knows where its floor has holes.

This is why the compiler's Step 2 is as load-bearing as FD-01's baseline operand. A compiler that
scored questions on general interest — how profound they sound in the abstract — would produce the
same questions any competent engineer anywhere would produce, and its output would be as commoditized
as the model's answers. A compiler that scores questions against *this stack's measured dependence*
produces questions specific to this stack's history, and the deltas that come back are correspondingly
proprietary. The moat is thus not in the model (shared) nor even in the answers (obtainable by anyone
asking the same question) but in the *matching* of question to the stack's private weak-spot map —
which is precisely the operation FD-02 performs and precisely why it consumes FD-01's class
distribution and FD-04's decay results rather than reasoning from the task in isolation. The
implication for the compiler's design is strict: a question whose leverage derives entirely from
general interest, with no anchor in a measured weak spot, is flagged low on the dependence-reducing
axis even if it sounds brilliant, because a brilliant-in-general question produces a commoditized-in-
general delta, and the suite's entire purpose is to produce the delta only *this* stack could have
extracted. The compiler that internalizes this treats the frontier model not as an oracle to be
impressed but as a lever to be aimed, and the aiming — at the stack's own private holes — is the
scarce, proprietary, moat-forming act.

### I.8 The maturity threshold and when compilation earns its cost

The claim that compilation effort should scale to floor maturity needs a concrete operating point, or
it remains a slogan. FD-02 defines maturity for a task class by two observable quantities the suite
already tracks: the class's *deposit density* (how many above-floor deltas FD-01 has already recorded
for it) and its *recent NEW rate* (what fraction of frontier answers in the class still classify NEW
versus DUP/DISCARD). A class with low deposit density and a high NEW rate is immature — the floor is
sparse, almost any question lands above it, and compilation should be shallow because the marginal
value of choosing a better question is small when nearly all questions succeed. A class with high
deposit density and a low NEW rate is mature — the floor is dense, most questions now land at-floor,
and compilation should be deep because the marginal value of finding the rare above-floor question is
large. The threshold between the two is not a universal constant; it is the point at which the
*expected saved frontier calls* from asking the compiled question rather than a random one exceeds the
compilation cost, and that crossover shifts per class with its frequency and its deposit history.

Making the threshold explicit resolves a real operational risk: without it, a session either over-
invests in compilation on immature classes (spending careful ranking effort where any question would
do, a small but real waste repeated across many young classes) or under-invests on mature ones
(treating a saturated domain like a fresh one and asking obvious questions that all come back DISCARD,
then wrongly concluding the domain is exhausted). Both errors are invisible without the maturity
signal because both produce plausible-looking sessions. The deposit-density-and-NEW-rate threshold
turns compilation depth into a measured decision: the compiler reads the class's maturity, sets its
depth accordingly, and records which regime it operated in, so the III.4 depth-appropriateness metric
can later confirm that effort tracked maturity rather than being applied uniformly. This is the same
instinct FD-00 applies to admission and FD-01 applies to classification cost — spend the expensive
judgment only where the leverage difference justifies it — and it is what keeps FD-02 itself from
becoming the kind of uniform-effort overhead the whole suite is designed to eliminate. A compiler that
compiled every class at full depth would be a guardrail costing more than the loss it prevents on the
immature classes and, paradoxically, might still under-serve the mature ones if its fixed budget were
spread thin; the maturity threshold concentrates the depth where the scarce deltas actually live.

---

## Part II — The Compilation Contract and the Leverage Scoring Model

### II.1 Operating contract (inputs and outputs)

FD-02's **inputs** are: the session's declared task; the FD-00 baseline for the task class (so the
compiler knows what is already at-floor and avoids compiling questions whose answers would be DUP);
the stack's *weak-spot record* (the FD-01 class distribution and FD-04 decay results for this class,
which reveal where the stack has repeatedly had to escalate to the frontier); and the CO-00 band (how
many questions the session can afford to pursue). Its **output** is a ranked list of compiled
questions, each carrying `{question_text, leverage_score, axis_breakdown, rationale, target_delta_
type, suggested_route}`. The `suggested_route` is a hint to CO-03, not a decision — FD-02 proposes
that a low-leverage question be routed cheaper or dropped, and CO-03 makes the actual routing call.
The contract's postcondition: the session receives a *ranked* set with the highest-leverage question
first, so that if the budget allows only one frontier call, it is spent on the question most likely to
produce a keepable delta.

Two output fields are worth emphasizing. `target_delta_type` is the compiler's prediction of what kind
of delta a good answer would yield (NEW capability, STRONGER improvement, or a portable deterministic
core), which lets FD-01 and FD-04 anticipate the extraction. `axis_breakdown` decomposes the leverage
score across the four archetypes, which is what makes the score auditable: a question scored high can
be inspected to see whether its leverage was real (high on irreversible + dependence-reducing) or a
scoring artifact (high on a single soft axis), and a systematic gap between predicted leverage and
FD-01's realized class is the signal the scoring model needs recalibration.

### II.2 The compilation procedure

Compilation runs in five steps so the ranked output is traceable. **Step 1 — floor subtraction.**
Remove from the candidate space any question whose answer the baseline already covers; there is no
point compiling a question whose best answer FD-01 would classify DUP. **Step 2 — weak-spot
targeting.** Bias the candidate space toward the stack's known frontier-dependence: classes where
FD-01 shows repeated NEW/STRONGER escalations and FD-04 shows `frontier-only` deposits are the classes
where above-floor deltas still live, so questions probing them score higher on the dependence-reducing
axis. **Step 3 — archetype scoring.** Score each candidate on the four leverage axes with explicit
criteria (II.3). **Step 4 — portability weighting.** Up-weight questions whose `target_delta_type` is
portable (`deterministic`/`small-model`), because a portable delta bends the dependence curve more
than a `frontier-only` one of equal magnitude. **Step 5 — rank and rationale.** Sum the weighted axes,
rank, and attach the rationale and axis breakdown to each question.

The procedure is explicit because, like FD-01's, its failures localize to specific steps. A skipped
Step 1 compiles questions whose answers are DUP (wasted calls on already-distilled ground). A weak
Step 2 compiles generically-interesting questions unmoored from where *this stack* is actually
dependent (interesting answers, no dependence reduction). A soft Step 3 produces scores that do not
predict FD-01's classes (leverage theater). Making each step inspectable is what lets the compiler
improve against the outcome data rather than remain a black box that emits plausible questions.

### II.3 The leverage scoring model

Each candidate question is scored on the four axes with concrete criteria:

| Axis | High-score criteria | Low-score criteria |
|---|---|---|
| **Irreversible** | commits an architecture/data-model/protocol decision expensive to reverse; frontier judgment materially better than a cheaper rung | a local, easily-reversed choice a cheaper rung handles |
| **System-generating** | answer is a reusable protocol/recipe serving the whole class | answer is a one-off artifact with no reuse |
| **Critique** | asks for a flaw the stack cannot self-see; adversarial, blind-spot-probing | asks for confirmation of what the stack already believes |
| **Dependence-reducing** | answer's `target_delta_type` is `deterministic`/`small-model`; directly attacks a frontier-dependence | answer would be `frontier-only`; deepens rather than reduces dependence |

The axes are summed with the Step-4 portability weight, producing a single leverage score in [0,1].
The scoring commitment that keeps it honest: the score must *predict* FD-01's downstream class. A
compiler whose high-leverage questions produce DISCARD/DUP answers as often as its low-leverage ones
is not measuring leverage; it is guessing. The predictive check — correlation between compiled
leverage score and realized delta value — is the compiler's primary evaluation metric (III.4), and it
is the same valid-outcome-not-proxy discipline CWOPS §4.6 demands: the score is graded against the
actual distilled outcome, never against how impressive the question sounds.

The scoring model is also deliberately *thresholded rather than continuous* at the decision boundary
the session actually cares about. The session does not need a perfectly-ordered ranking of twenty
questions; it needs to know which one or two clear the bar for a frontier token and which fall below
it into route-cheaper or drop territory. FD-02 therefore reports, alongside the continuous score, a
three-band verdict per question: `frontier-worthy` (leverage high enough that a frontier answer is
likely to carry a keepable delta), `route-cheaper` (some value but a sub-frontier rung suffices), and
`drop` (at-floor or DUP-producing, not worth asking at all). The banding matters because it aligns the
compiler's output with FD-00's admission gate, which is itself a four-valued verdict: a compiler that
emitted only a continuous score would force the admission gate to re-derive the band, duplicating the
judgment; by emitting the band directly, FD-02 hands the gate a decision-ready input and keeps the two
in lockstep. The band boundaries are not fixed constants but per-class thresholds tuned by the same
FD-04 outcome join that tunes the portability weight — a class where frontier answers have historically
distilled well has a lower `frontier-worthy` threshold (the model reliably adds value there), while a
class where frontier answers keep coming back DUP has a higher one (the floor already covers most of
it). This is the CWOPS task-aware-budget principle expressed as a per-class admission threshold rather
than a global one, and it is what stops the compiler from applying an immature-domain generosity to a
mature domain or a mature-domain severity to a young one.

A further design commitment concerns what the compiler does with its own uncertainty about a score. A
question whose axis breakdown is internally contradictory — high on critique, low on dependence-
reducing, with a `target_delta_type` the compiler cannot confidently predict — is not force-banded;
it is emitted with an explicit low-confidence flag and its band set to the more conservative of the
two candidate bands. The rationale mirrors FD-01's deferral discipline: when the compiler genuinely
does not know whether a question is `frontier-worthy` or `route-cheaper`, the honest and cheaper move
is to route it cheaper and let the outcome teach the model, rather than to spend a frontier token on a
coin-flip and hope. Over many sessions this conservative-on-uncertainty policy has a compounding
benefit: the frontier budget is concentrated on the questions the compiler is *confident* are high-
leverage, which are exactly the questions whose outcomes most sharply calibrate the scoring model, so
the compiler's confident band gets more reliable over time while its uncertain band is quietly
resolved by cheaper substrates. The alternative — spending frontier tokens on uncertain questions to
"find out" — is the CWOPS unbounded-loop anti-pattern wearing a curiosity costume, and the banding
plus conservative-on-uncertainty rule is the bound that prevents it.

### II.4 Interfaces with existing PP systems

- **one_shot** — FD-02 generalizes its Q&A scaffold; on an ULTRA-mode task the compiled questions
  populate the Q&A pass rather than the fixed six, so the two compose rather than compete.
- **CO-03** — receives each compiled question with a `suggested_route`; makes the actual model
  choice. A low-leverage question FD-02 flags is a candidate for CO-03 to route to a cheaper rung.
- **FD-00** — supplies the baseline for Step 1 and the band for output sizing; FD-02's ranked list
  drives FD-00's protocol stage 3 (question selection).
- **FD-01** — supplies the weak-spot record (class distribution) for Step 2 and is the downstream
  grader of whether a compiled question's answer actually carried a delta.
- **FD-04** — supplies the decay results that mark which classes are still `frontier-only` and thus
  high-leverage to probe.
- **FD-05** — the biggest consumer of dependence-reducing questions; FD-02 compiles the questions
  whose answers FD-05 turns into routing rules.
- **CDIO** — the critique-question archetype borrows CDIO's review discipline, generalized.

### II.5 Decision rights and non-decision rights

FD-02 **may decide**: which candidate questions to compile; their leverage scores and axis
breakdowns; their ranking; the `suggested_route` hint; and the `target_delta_type` prediction. FD-02
**may not decide**: the actual model route (CO-03); whether to spend a frontier token on a question
(FD-00's admission gate makes that call using FD-02's ranking as input); the classification of the
answer (FD-01); or the session budget (CO-00). The boundary with FD-00 is precise: FD-02 *ranks* the
questions, FD-00 *admits* the calls — FD-02 says "this is the highest-leverage question," FD-00 says
"and it clears the admission gate, so spend the token." A compiler that decided admission would
duplicate FD-00's gate; a doctrine that ranked questions would duplicate FD-02's model. The split
keeps each auditable.

### II.6 Token-ROI rules

FD-02 is itself a pre-call cost, and it must earn its place by saving more than it spends. Its ROI
rule mirrors FD-01's: compilation runs on the cheapest sufficient substrate, and its *depth* scales
to the floor's maturity (I.2). On an empty-floor class, compilation is shallow and cheap because any
question works; on a mature class, deep compilation is justified because the leverage difference
between the best and a random question is large — the difference between a keepable delta and a wasted
frontier call. The ROI is measured over the session: a compiler that reliably moves the asked question
from a random draw to a top-leverage draw converts wasted frontier calls into keepable deltas, and the
value of that conversion is the recurring cost of the wasted call the good question avoided. A compiler
that costs as much as the frontier call it improves has no ROI and violates the CWOPS guardrail-
economics principle; FD-02's depth-scaling is what keeps it cheap where it adds little.

### II.7 Portability and no-bloat rules

FD-02's portability contribution is upstream and structural: by up-weighting dependence-reducing
questions (those whose answers target a portable delta), it biases the whole suite toward producing
portable deposits rather than `frontier-only` trophies. The compiler is, in effect, the earliest lever
on the portability slope FD-00 tracks — it shapes questions so the deltas that come back are the kind
FD-05 can convert. Its no-bloat rule is Step 1: never compile a question whose answer would be DUP,
because a DUP-producing question is a wasted call by construction. The compiler protects deposit
precision from the input side, exactly as FD-01 protects it from the output side — together they
ensure the vault fills with above-floor, portable deltas rather than restated commodities.

### II.8 A worked compilation: three questions, one task, one winner

The compilation contract is clearest on a concrete task run end to end. Take the task "our concurrent-
pane coordination sometimes double-processes a work item; help us fix it." A naive session would ask
the model directly to fix the bug and take whatever comes back. FD-02 instead compiles a candidate
set and ranks it, and walking the three strongest candidates shows how the leverage model discriminates
between questions that all *sound* reasonable.

**Candidate 1: "What is the bug and how do we fix this specific double-processing?"** Step 1 (floor
subtraction) does not remove it — the stack does not already hold this fix. Step 3 scoring:
irreversible — low (it is a local patch, easily changed); system-generating — low (it produces a
one-off fix, not a reusable protocol); critique — low (it asks for a fix, not a flaw the stack cannot
see); dependence-reducing — low (the answer will be a specific patch, likely `frontier-only` in the
sense that re-deriving it for the next bug needs the model again). Summed leverage: low. The answer
would probably be classified STRONGER at best, and would not move the class's dependence much, because
the *next* double-processing bug would require another frontier call.

**Candidate 2: "Under what interleavings can any work-item dispatcher double-process, and what
invariant prevents all of them?"** Step 1: not on the floor. Step 3: irreversible — high (an invariant
is an architecture-level commitment); system-generating — high (an invariant that prevents *all* such
interleavings is a reusable protocol, not a one-off fix); critique — high (it asks the model to
enumerate the failure space the stack cannot see); dependence-reducing — high (the invariant is a rule,
`deterministic` portability: once stated, it prevents the whole bug class without further model calls).
Summed leverage: maximal — high on all four axes. This is the question whose answer distills into a
permanent asset that retires the entire bug class.

**Candidate 3: "What do other systems do for exactly-once processing?"** Step 1: partially on the
floor — the stack likely already navigates general exactly-once knowledge via GK, so much of the
answer would be DUP/at-floor. Step 3: system-generating — medium; critique — low; dependence-reducing
— low (general knowledge a cheaper rung or the graph already supplies). Summed leverage: medium-low,
and Step 1 flags that a chunk of the answer is at-floor. Better routed to a cheaper rung than a
frontier token.

The compiler ranks Candidate 2 first, Candidate 1 second, Candidate 3 last (with a `route-cheaper`
hint). The session, following FD-00 stage 3, asks Candidate 2 first. The frontier answer supplies the
double-dispatch invariant; FD-01 classifies it NEW with `deterministic` portability; FD-06 writes it
as a CO-05 rule; and the *next* double-processing report is now answered by the invariant with no
frontier call — the dependence curve for the class bent because the session asked the invariant
question instead of the patch question. This is the compiler's whole value in one trace: all three
candidates were plausible, a naive session would likely have asked Candidate 1 (the literal request),
and only the leverage model surfaced that Candidate 2 — the same task, asked one level up — was worth
roughly the entire class's future frontier spend. The axis breakdown is what makes this defensible
rather than lucky: Candidate 2 did not win because it "sounded deeper," it won because it scored high
on four named, inspectable axes, and the audit can later confirm the score predicted the NEW,
`deterministic`, class-retiring outcome. Had the audit instead found Candidate 2's answer classified
DUP, the axis breakdown would localize the error — most likely a stale Step 1 baseline that missed an
existing invariant — rather than leaving "the compiler guessed wrong" as an unactionable verdict. The
same trace also illustrates why the compiler emits a ranked *set* rather than a single best question:
had Candidate 2's answer come back thin, the session still holds Candidate 1 as a ranked fallback and
spends its next call there rather than re-compiling from scratch, so a single weak frontier answer
degrades the session gracefully instead of stalling it — the bounded-retry discipline CWOPS §2.4
prescribes, applied to questions rather than tool calls.

---

## Part III — Failure Modes, Gates, Benchmarks, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis | Root cause |
|---|---|---|---|
| **Leverage theater** | high-scored questions produce DISCARD/DUP as often as low-scored | correlate compiled leverage score with FD-01 realized class | scoring model not predictive; soft Step 3 criteria |
| **Interesting-but-irrelevant** | answers are novel yet do not reduce dependence | check `target_delta_type` distribution; mostly `frontier-only` | weak Step 2 weak-spot targeting; questions unmoored from this stack's dependence |
| **DUP compilation** | frontier calls returning DUP answers | audit compiled questions against the baseline | Step 1 floor-subtraction skipped or stale baseline |
| **Obvious-question saturation** | mature class returns only DISCARD, session concludes "no delta left" | inspect whether compilation went deep on the mature class | compilation depth not scaled to floor maturity (I.2) |
| **Phrasing-not-selection drift** | compiler tweaks wording instead of choosing better questions | check whether candidates differ in substance or only phrasing | conflating FD-02's selection role with prompt-phrasing |

The characteristic failure is leverage theater, and it is dangerous for the same reason FD-01's
NEW-inflation is: it *looks* like success. Impressive-sounding questions with high self-assigned scores
feel productive, and only the correlation to FD-01's actual class results reveals that the scores did
not predict value. The cross-check is the predictive-correlation metric, and it is the compiler's
single most important health signal.

### III.2 Anti-patterns with evidence

- **The impressive question.** Compiling questions that sound profound but probe already-distilled
  ground. Evidence: the a16z empty-moat finding — the appearance of depth is not advantage; only the
  above-floor delta is. Forbidden by Step 1 floor-subtraction.
- **Generic curiosity.** Compiling generically-interesting questions unanchored to where *this stack*
  is dependent. Evidence: CWOPS's insistence on outcome data from an *instrumented* process — the
  questions must target this stack's measured weak spots, not general interest. Forbidden by Step 2.
- **The single-axis inflator.** Scoring a question high on one soft axis (it sounds like a critique)
  without the others. Evidence: the multi-axis scoring exists precisely so a single soft signal cannot
  dominate. Forbidden by the axis-breakdown audit.
- **Phrasing as leverage.** Treating better wording as higher leverage. Evidence: I.4 — a well-phrased
  low-leverage question is still a wasted token. Forbidden by the selection-not-phrasing principle.
- **Depth-blind compilation.** Spending deep compilation effort on an empty-floor class where any
  question works, or shallow effort on a mature class where only the right question works. Evidence:
  CWOPS task-aware budgeting. Forbidden by the floor-maturity scaling.

### III.3 Quality gates (binary)

- **G1 — Floor-subtracted.** Was every compiled question checked against the baseline so its best
  answer would not be DUP? Binary.
- **G2 — Scored and ranked.** Does every question carry a leverage score, axis breakdown, and
  rationale, in ranked order? Binary.
- **G3 — Weak-spot anchored.** Were the stack's FD-01/FD-04 weak-spot records consulted in Step 2?
  Binary.
- **G4 — Depth scaled.** Did compilation depth match the class's floor maturity? Binary.
- **G5 — Route-hinted.** Does every question carry a `suggested_route` hint for CO-03? Binary.

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Predictive leverage | correlation between compiled leverage score and FD-01 realized delta value | leverage↔class join | strongly positive |
| Dependence targeting | fraction of compiled questions whose realized delta is portable (`deterministic`/`small-model`) | FD-04 portability results | rising |
| DUP avoidance | fraction of frontier answers to compiled questions classified DUP | FD-01 class log | falling toward 0 |
| Depth appropriateness | compilation cost as a fraction of session value, sliced by floor maturity | cost + FD-01 join | low on empty floor, justified on mature |
| Ranking quality | fraction of sessions whose top-ranked question produced the session's best delta | rank↔class join | rising |

### III.5 Benchmarks with reference values

**Predictive floor:** the leverage↔class correlation must be strongly positive or the compiler is not
measuring leverage — this is the compiler's existence proof, analogous to FD-01's ≥0.85 accuracy
floor. **DUP ceiling:** frontier answers to compiled questions should be classified DUP well below the
rate for un-compiled questions — the whole point of Step 1. **Portability lift:** compiled sessions
should show a higher portable-delta fraction than un-compiled ones, the input-side contribution to
FD-00's portability slope. **Cost ratio:** compilation cost must stay a small fraction of the frontier
call it improves (CWOPS guardrail economics), enforced by depth-scaling. **Ranking hit-rate:** the
top-ranked question should produce the session's best delta more often than chance, the direct measure
that ranking, not just selection, adds value.

### III.6 Example operational traces

**Trace A — mature-class deep compilation.** Task: improve the concurrency subsystem, a heavily-worked
class. Step 1 removes the obvious questions (their answers are on the floor). Step 2 finds FD-04 marks
one capability `frontier-only`. Step 3 scores a critique-question ("under what interleaving does the
current scheme deadlock?") high on critique + irreversible. Step 4 up-weights it (its answer targets a
portable fix). Step 5 ranks it first. The frontier answer yields a NEW deadlock-avoidance rule; FD-01
confirms; the compiler's high score is vindicated by the class result.

**Trace B — empty-class shallow compilation.** Task: a brand-new domain, empty floor. Compilation is
shallow — any reasonable question produces a delta — and cheap. The compiler spends little effort here
because leverage differences are small when the floor is empty; the session spends its budget on the
answers, not on choosing the question.

**Trace C — dependence-reducing question.** Task: a class the stack keeps escalating to the frontier.
FD-02 compiles "what is the deterministic core of this judgment that a rule could capture?" — high on
dependence-reducing. The answer yields a deterministic checklist (portability `deterministic`); FD-05
converts it into a CO-05 asset; the class's future frontier calls drop. The compiler directly bent the
dependence curve by asking the portability question.

**Trace D — leverage-theater caught.** A compiled question scored 0.9 but its answer was classified
DUP by FD-01. The leverage↔class correlation flags the mismatch; audit shows Step 1 used a stale
baseline, so the question probed ground already distilled last week. The fix is baseline freshness,
not a re-score.

### III.7 Edge cases

- **Empty weak-spot record (new stack).** Step 2 has nothing to target; compilation falls back to the
  archetype scoring alone and flags that weak-spot targeting was unavailable, so a low dependence-
  targeting metric is not misread as a compiler failure.
- **All candidates at-floor.** Step 1 removes everything; the compiler reports "no above-floor question
  found for this class," which is itself a signal that the class is saturated (its floor covers the
  domain) and the session should not spend a frontier token — a legitimate, valuable null output.
- **Conflicting axes.** A question high on critique but its answer would be `frontier-only` (low
  dependence-reducing). The compiler surfaces the tension in the axis breakdown rather than hiding it,
  so the session can choose knowingly.
- **one_shot integration.** On an ULTRA task, the compiled questions replace the fixed six; if fewer
  than a useful number of above-floor questions exist, the compiler says so rather than padding to six.
- **Adversarial task framing.** A task phrased to elicit a specific answer is neutralized by the
  critique archetype, which compiles a question probing the framing itself.

### III.8 Writeback rules

FD-02 does not write deposits; its output is the ranked question list, which is consumed by the
session and logged for the leverage↔class audit. The one thing it *does* persist is the leverage
score paired later with FD-01's realized class, because that pairing is the ground-truth the scoring
model is graded against (III.4). The compiler never writes to the graph or the asset registry — its
influence is entirely upstream, shaping what gets asked, not what gets stored.

### III.9 Conceptual regression tests

- **R1 — Floor subtraction.** Feed a task whose obvious questions are all at-floor; assert the compiler
  removes them and either compiles a non-obvious above-floor question or reports the null.
- **R2 — Predictive scoring.** Feed a set of questions with known downstream classes; assert leverage
  scores correlate with realized value.
- **R3 — Depth scaling.** Feed an empty-floor and a mature-floor class; assert compilation depth (cost)
  differs appropriately.
- **R4 — Dependence targeting.** Feed a class marked `frontier-only`; assert a dependence-reducing
  question is compiled and ranked highly.
- **R5 — Null honesty.** Feed a saturated class; assert the compiler reports "no above-floor question"
  rather than padding.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness; the predictive-correlation
metric is measured against real FD-01 outcomes, the honest observation the anti-test-theater rule
requires.

### III.10 Done criteria (verifiable)

FD-02 is done when: the dataset exists on disk, un-truncated, >2500 real words/Part; the four-axis
leverage taxonomy is defined with concrete high/low criteria; the five-step compilation procedure is
specified with each step's failure localized; the leverage score is committed to *predicting* FD-01's
class (not sounding impressive); G1–G5 are binary; the compiler declares CO-03 as the router and
one_shot as the scaffold it generalizes (no re-implementation); and V-FD-NO-CODE finds zero fences.

### III.11 Upgrade path

- **v1 (this dataset):** the leverage-ranking compiler as a rung-2 advisory feeding FD-00 stage 3.
- **v2 (EXECUTION-mode):** the leverage↔class correlation is computed on accumulated sessions and used
  to recalibrate the axis weights, so the scoring model learns which axes actually predict value for
  this stack; the null-output ("no above-floor question") becomes a signal that feeds FD-00's decision
  to decline the session entirely.
- **v3:** the weak-spot targeting (Step 2) is served by the GK route compiler so the compiler navigates
  to the stack's dependence hot-spots rather than re-deriving them from FD-01's raw distribution.
- **Deprecation trigger:** if a class's floor rises to full saturation (Step 1 removes all candidates
  durably), FD-02 stops compiling for that class and reports it saturated — the compiler's own success
  retires it from the domains it has helped fully distill, mirroring the suite's terminal state.

### III.12 The relationship to FD-04 and the closed compilation loop

FD-02 is the input-side of a loop that only closes when it is joined to FD-04's portability test, and
spelling out that join is what distinguishes a compiler that learns from one that merely emits. The
compiler predicts, per question, a `target_delta_type` — its guess at whether a good answer would yield
a portable (`deterministic`/`small-model`) delta or a `frontier-only` one. FD-04 later measures the
truth: it takes the delta that actually came back and tests whether it survives on a cheaper substrate.
The pairing of FD-02's prediction with FD-04's measurement is a free, continuously-generated training
signal, and it is the mechanism by which the compiler's dependence-reducing axis becomes calibrated
rather than aspirational. If the compiler systematically predicts `deterministic` for questions whose
answers FD-04 proves are stubbornly `frontier-only`, its dependence-reducing scoring is over-optimistic
and must be tuned down; if it systematically under-predicts portability, it is failing to compile the
very questions that would most bend the dependence curve, leaving portable advantage un-asked-for.
Either way the correction comes from an outcome (FD-04's test) rather than from the compiler grading
its own predictions, which is the same non-self-grading discipline FD-01 applies and the same valid-
closed-fast structure CWOPS prescribes for any learning loop.

This closed loop also resolves a tension that would otherwise sit unaddressed in the leverage model:
the fact that the highest-*magnitude* delta and the highest-*portability* delta are not always the
same question. An irreversible architecture question might yield a huge but `frontier-only` delta (a
judgment that still needs the model to re-apply), while a humbler dependence-reducing question yields a
small but `deterministic` one (a rule that never needs the model again). Which is higher leverage? The
answer is not fixed; it depends on the class's frequency and the stack's current dependence, and it is
precisely the kind of trade-off the Step-4 portability weight exists to tune. On a high-frequency
class where the stack is escalating constantly, the small deterministic delta wins because it retires
many future calls; on a rare, high-stakes class, the large `frontier-only` delta wins because getting
the architecture right once is worth more than saving calls that will seldom be made. The compiler
does not hard-code this; it exposes both magnitudes in the axis breakdown and lets the Step-4 weight —
itself tuned by the FD-04 join — settle the balance per class. The result is a compiler whose notion
of leverage is not a fixed formula but a per-class, outcome-calibrated function that gets sharper every
time a compiled question's answer is decay-tested, which is the only configuration under which the
input side of the suite can keep pace with a floor that is itself always rising. A compiler frozen at a
single leverage formula would, as the floor rose, keep compiling questions calibrated to last quarter's
weak spots; the FD-04 join is what keeps its aim current with where the stack is dependent *now*.

### III.13 Compilation under concurrency and the shared question ledger

Like FD-01, FD-02 rarely runs alone — the Parallel Mesh permits several panes on one repo, and if each
pane compiles questions independently against the same weak-spot map, two panes may compile near-
identical high-leverage questions and both spend a frontier token on what is effectively the same
inquiry. This is the input-side analogue of FD-01's duplicate-extraction race, and it is resolved by
the same Mesh mechanism: a shared question ledger on PM-03's findings bus. When a pane commits to
asking a compiled question, it publishes the question's identity and its target weak-spot to the bus;
a concurrent pane's Step 1 reads that ledger and treats an in-flight question as provisionally
covering its weak-spot, so it compiles the *next* highest-leverage question rather than duplicating the
first. The ledger does not prevent two panes from working the same domain — parallelism is allowed —
it prevents them from spending two frontier tokens on one question, which is the duplicate cognition
the Mesh's root law forbids. This is a direct reuse of PM-03's consume-before-reason gate, not a new
coordination layer, and it keeps the compiler correct at the six-to-ten-pane scale the Owner actually
runs rather than only in the single-pane idealization.

The shared ledger has a second, subtler benefit that closes a gap a single-pane design would leave
open: it makes the weak-spot map *self-updating within a session window*. In a single-pane world, the
weak-spot map is only refreshed when FD-01 deposits a new delta, which happens at session close; but
under concurrency, pane A asking a dependence-reducing question about a weak spot is itself evidence
that the weak spot is being addressed, and pane B benefits from knowing that before pane A's deposit
lands. The question ledger carries this in-flight signal, so pane B does not compile a question aimed
at a hole pane A is already filling. This is the same near-real-time floor-freshness FD-01 gains from
reading in-flight deltas off the bus, applied to the input side: the compiler's aim stays current not
only with the last committed floor but with the floor the other panes are *in the process of* raising.
The net effect is that a repo worked by many panes compiles a *coordinated* question portfolio — each
pane aiming at a distinct hole, none duplicating another's frontier spend — rather than several panes
independently rediscovering and re-asking the same few obvious high-leverage questions. Achieving this
without a bespoke coordination system, purely by consuming the Mesh's existing bus, is what keeps FD-02
inside the "one system, no parallel systems" discipline the suite inherits, and it is the reason the
compiler treats the question ledger as a first-class input alongside the baseline and the weak-spot map
rather than as an afterthought bolted on for the multi-pane case.
