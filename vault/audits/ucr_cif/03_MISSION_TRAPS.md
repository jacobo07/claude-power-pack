---
title: UCR-CIF Compendium — Dataset-Generation Failure & Trap Record
date: 2026-08-25
status: OPEN — appended during the mission, not written at the end
mandate: mission brief §62 (UKDL evaluation) · §63 (error protocol) · deliverable #16
---

# Mission Traps — failures observed while building this compendium

Every entry below was **observed in this session**, with the evidence that produced it.
None is hypothetical. Each carries a proposed disposition; none is auto-promoted to UKDL —
evidence and applicability first (§62).

---

## T-INVENTORY-OUTPUT-CAP-001 — a dense corpus range silently exceeds a subagent's output cap

**Observed.** The inventory agent assigned lines 17,500–35,000 terminated with
`API Error: Claude's response exceeded the 64000 output token maximum`. The entire range's
work was lost. A sibling agent had already reported **259 concepts** in that same range —
at ~250 output tokens per full record, 259 records is ~65k tokens, i.e. the range was over
budget before the agent read its first line.

**Mechanism.** Range size was chosen by *line count* (a uniform 17,500-line split), but the
output cost is driven by *concept density*, which is not uniform. Lines 35,000–52,500
yielded 133 records; 17,500–35,000 yielded 259 — nearly double from an identically sized
range.

**Why it is not just a retry.** Re-running the same shape reproduces the same overflow.
Regla 12 applies: the second attempt must change the mechanism, not the parameters alone.

**First fix — insufficient, recorded as such.** Two changes: split the dense range in half
(17,500–26,250 and 26,250–35,000), and switch to a **compact one-line-per-field record**
(`DEF`/`OWNS`/`IO`/`LAW`). The aggregator was taught to parse both formats so ranges already
written verbose did not need regenerating.

**Second failure, same shape.** The agent on lines **1–17,500** — a range I had judged
*less* dense and dispatched in the verbose format before the pivot landed — died with the
identical error. Two consecutive failures of the same shape triggers Regla 12: the next
attempt must change the **mechanism**, not the parameters.

Note the diagnostic error inside the first fix: I treated range size as the variable and
halved it. But 1–17,500 was never halved and failed anyway, which proves density is high
across the corpus generally, not concentrated in one range. **Halving a range is a parameter
change wearing a mechanism's clothes** — it moves the same design closer to a cliff instead
of stepping away from it.

**Real fix — per-slice files.** The cap is on a *single response*, not on cumulative work.
So the agent now performs **one Read then one Write per 2,000-line slice**, each slice to its
own file (`inv_r1_slice1.txt` … `inv_r1_slice9.txt`), never accumulating records across
slices. No single response can exceed one slice of records (~8–15k tokens against a 64k cap).

Two properties the earlier fixes lacked:
- **Bounded by construction**, not by an estimate of density.
- **Crash-survivable** — a killed agent leaves every completed slice on disk, where the
  previous design lost the entire range.

The agent is also instructed to stop and report partial coverage rather than risk the cap,
because partial coverage recorded honestly outranks a killed agent.

**Generalizes to.** Any fan-out where work is partitioned by a cheap proxy (lines, files,
bytes) while cost is driven by an unmeasured property (density, nesting, match count).
**Partition by the thing that costs, or measure the proxy's correlation to it first.**

**Disposition.** UKDL trap candidate. Applicability is broad (every corpus sweep, every
parallel audit) and the evidence is a hard failure, not an inference.

---

## T-AGENT-BAND-OVEREXTENSION-001 — a subagent reported one contiguous band where the region was interleaved

**Observed.** The range-4 agent reported `CONTAMINATION_BAND: 60177-70365` as a single
contiguous block of pasted harness documentation. Measurement at 100-line resolution using
two independent signals found **nine discontinuous runs totalling ~3,900 lines**, with
genuine Spanish corpus at 66,000–68,100 and continuously from 70,300 onward.

**Consequence had it been accepted.** ~2,000 lines of real corpus discarded — a coverage
loss in precisely the direction the mission's §5 zero-omission rule forbids. The error is
*asymmetric*: an over-wide exclusion band silently deletes source material, while an
over-narrow one merely admits noise that later classification catches.

**Mechanism.** An agent reading sequentially sees contamination start, sees it continue
across several slices, and reports the outer envelope. It has no cheap way to notice a
corpus island *inside* the envelope, because confirming absence of contamination requires a
different signal than detecting its presence.

**Generalizes to.** Any boundary reported by a sequential reader. **A range boundary
asserted by a reader is a hypothesis; boundaries that exclude material must be measured
with a signal independent of the one that found them.** Prefer two orthogonal signals
(here: harness markers *and* Spanish function-word density — a pasted English prompt cannot
score on both).

**Disposition.** UKDL trap candidate, sibling of the existing
`PR-COVERAGE-BY-CONSTRUCTION-001` family.

---

## T-VOCABULARY-ZERO-IS-NOT-ABSENCE-002 — my own grep declared a built system missing

**Observed.** I recorded in the D2A audit that a grep for UBC's function
(`minimum sufficient`, `maturity capsule`, `compile … applicable … mission`) returned
**zero matches across all 84 modules**, and concluded the compiler might not exist.
`modules/capability_runtime/applicability.py` is a *"Capability Applicability Engine —
decides which capability contracts apply to a mission, and how strongly,"* implementing
anti-triggers, graded activation, evidence gates and duplicate-scope rejection.

**Mechanism.** The probe searched the **source corpus's** vocabulary; the module uses its
**own** vocabulary. A gate is bounded by the words it knows, and an unrecognised idiom
reads as zero. **Zero cannot fall.**

**Why it is recorded here rather than silently fixed.** This is the second instance in this
audit (the first being the 24 DEFER rows) and the only one that was mine. The estate's
sealed lesson `feedback_zero_cannot_fall` already names the mechanism — it did not prevent
the recurrence, which is itself the finding: *knowing the rule did not stop me applying a
vocabulary-bounded instrument and believing its zero.*

**Fix applied.** Before any CREATE verdict, a capability-level sweep is now mandatory —
probing the **function under any name**, with the source's acronym deliberately excluded
from the query. Where that still returns near-zero (Certified Primitives & Golden Paths:
2 hits estate-wide across two independent sweeps), the signal is trustworthy.

**Disposition.** Not a new UKDL rule — an **enforcement gap on an existing one**. The right
output is a procedural gate ("no CREATE verdict without a capability-level sweep"), not a
fourth restatement of a lesson already sealed three times.

---

## T-D2A-CONSTANT-FLOOR-001 — 24 of 28 verdicts returned the same number

**Observed.** `d2a_engine.py --family-file --repo-evidence` on 28 spine systems returned
4 KEEP and 24 DEFER, where **every one of the 24 scored coverage = exactly 45 %** — the
engine's plausibility floor.

**Mechanism.** A score identical across 24 items carries no information and cannot rank
them. This is the estate's own sealed pattern *constant factors rank nothing*, appearing
here in the instrument built to prevent duplication.

**Consequence.** The engine's DEFER output is unusable as a build signal in either
direction. Treating it as novelty would repeat the CRPF/IGEF/E1–E5 strikes; treating it as
ownership would suppress genuine gaps. It must be read as **UNKNOWN** and resolved by
per-system evidence sweeps — which, done manually, resolved 9 of the 24 immediately.

**Note on scope.** This is an observation about the engine's behaviour on a 28-item family,
not a defect report against it. The engine correctly declines to name a parent it cannot
evidence; the trap is in *consuming* the floor as if it were a measurement.

**Disposition.** Feed to the D2A owner as a measured observation. Candidate improvement:
emit `UNRESOLVED` as a distinct verdict rather than a capped coverage number, so the
floor cannot be mistaken for a score.

---

---

## T-SELF-CONTAMINATED-DENOMINATOR-001 — the audit's own output polluted the corpus it audits

**Observed.** The Phase 3b capability sweep returned
`vault/knowledge_base/ucr_cif/SOURCE_INVENTORY_FULL.json` as the **top hit for 7 of its 10
probes**. That file is this mission's own inventory, committed roughly an hour earlier, and
it quotes the source corpus's vocabulary verbatim — 1,394 records of it.

**Magnitude.** `HIC-OAR` scored **96 hits** in the contaminated run and **0** once the
mission's own paths were excluded. The contaminated run would have reported the single
strongest novelty signal in the audit as "already owned by the estate."

**Mechanism.** The audit writes into the tree it audits. Every artifact it commits enters
its own denominator, carrying the exact vocabulary the sweep searches for. The effect is
**self-reinforcing and grows monotonically**: the longer a corpus mission runs, the more of
its own output pollutes its next measurement, and the direction of the error is always
toward "this already exists" — the conclusion that ends the mission early.

**Why it nearly passed.** The hit counts looked *plausible*. A system scoring 96 across 4
files reads like dispersed partial ownership, which is a verdict this audit had legitimately
issued elsewhere. Nothing about the number said "you are reading yourself"; only the
**filenames** did.

**Fix applied.** The corpus builder excludes every path matching `ucr_cif` / `ucr-cif`
before a single document is loaded — exclusion at construction, not subtraction afterwards,
so no probe can ever see the mission's own text.

**Generalizes to.** Any measurement whose output lands inside its own input set: repo audits
that write reports into the repo, coverage tools that scan their own output directory,
knowledge-graph indexers that index their own index, dedupe engines whose ledger lives in
the searched tree. **Establish the denominator's boundary before the first measurement, and
re-check it after every write into the tree.** Corollary: *inspect the top hit's path, not
just its count* — the count was unremarkable, the path was diagnostic.

**Disposition.** UKDL trap candidate, high applicability. Sibling of
`PR-COVERAGE-BY-CONSTRUCTION-001` (denominator must be discovered) — this is its inverse:
the denominator must also be **bounded**, or it silently absorbs the thing being measured.

---

## T-BASENAME-COLLAPSE-001 — a relative-spelled chain member, reduced to its basename, reads as missing

**Observed (2026-09-19, UCR-CIF W0).** The hook-chain census reported **44 of 69 chain
members "DEFINED BUT NOT ON DISK"**, among them `secret_firewall_gate.js`. Reported as
written, that is a CRITICAL finding: HR-SECRET-001 unenforced, host-wide. It was false.
The dispatcher spells a member relative to its own directory —
`'../skills/claude-power-pack/hooks/secret_firewall_gate.js'`,
`'./tests/fixtures/drill-fast-critical.js'` — and the census took `os.path.basename`, then
tested for existence in one flat directory. After resolving members the way the dispatcher
resolves them: **0 missing.**

**Why it nearly passed.** The output was *plausible in both directions*. This estate has a
sealed incident where the secret firewall really was unwired, and another where the
canonical hook tree and the live one had diverged. A reader holding either memory would
have accepted "44 missing" as the third instance rather than as a parser bug.

**The second failure, same shape.** The verification probe searched two roots —
`~/.claude/hooks` and the repo's `hooks/` — and returned ABSENT for `context-watchdog.py`,
which the dispatcher spells under `modules/zero-crash/hooks/`. A narrower instrument
confirming a wrong answer is not a confirmation. Two failures of one shape closed the
parameter route under Regla 12: the fix is to resolve exactly as the consumer resolves,
never to widen the search path again.

**Generalizes to.** Any audit of a registry whose entries are *paths interpreted by
somebody else*. **Resolve a reference with the resolver that actually consumes it; a
basename is not an identity.** Corollary, and the reason this is recorded rather than
quietly fixed: *when a sweep accuses a safety-critical component, suspect the sweep first* —
the direction of that error is toward a loud false alarm, which is the survivable
direction, but it costs the credibility the next true alarm needs.

**Disposition.** UKDL trap candidate. Sibling of `T-VOCABULARY-ZERO-IS-NOT-ABSENCE-002` —
both are instruments bounded by an assumption about how the subject names things.

---

## T-CONSTANT-PATH-INVISIBLE-001 — `readers=0` on two live stores, produced entirely by the instrument

**Observed (2026-09-19, UCR-CIF W0).** A first pass at "does anything read what we write?"
reported **0 readers** for `vault/baseline_ledger.jsonl` (73 rows) and `vault/ceps/events.jsonl`
(891 rows). Both numbers were artifacts. Measured properly, both stores are **CLOSED**.

**Two independent mechanisms, and each alone was sufficient.** (1) The classifier bucketed
any file containing an append pattern *anywhere* as a writer, so a module that both appends
and reads could never be counted as a reader. (2) The AST rewrite that replaced it matched
store tokens against the unparsed call expression — but this estate writes
`open(LEDGER_PATH, 'a')`, and the filename appears nowhere in that expression. Tokens taken
from the filename *stem* then failed in both directions at once: `index` matched the English
word throughout the corpus, while `baseline_ledger` matched nothing at all.

**What caught it.** Not inspection — a **positive control naming a known accessor**. The
tool exited 2 on its own control before it could publish a clean-looking table. Had the
control been "did the sweep find *some* access", it would have passed: three other tokens
were matching fine.

**Fix.** Tokens are the filename *with* extension plus the repo-relative path; module-level
string constants are resolved (literals, f-strings, `os.path.join`, pathlib `/` chains) and
substituted before matching; and the count of `open()` sites whose path cannot be resolved
statically is **reported** (299), so coverage is a measured number rather than an assumption
and `INERT` is read as "not statically reachable", never as "dead".

**Generalizes to.** Any static sweep for uses of a *named resource*. **The name you search
for is rarely the name the code writes; resolve the indirection or state your blindness as a
number.** And: a positive control must name a *specific* expected finding — "found
something" is satisfied by the half of the estate that was never broken.

**Disposition.** UKDL trap candidate, high applicability.

---

## PR-STARVED-HOST-COUNT-NOT-CLOCK-001 — at 4.7 % free RAM, build the counter instead of taking the reading

**Observed (2026-09-19, UCR-CIF W0).** The plan's §T required a latency baseline *before*
any gate is added, because once gates exist the "before" number is unrecoverable. The host
measured **1,499 MB free of 32,061 (4.7 %)**, 31 `claude` and 15 `node` processes. This
estate has already recorded a **17×** drift on identical payloads under contention, and has
one sealed incident where a sweep manufactured the very contention it then reported as a
standing defect.

**Decision.** Timing recorded as **UNMEASURED**, with the blocking precondition named —
never as a number, and never silently skipped. The load-*independent* half was captured
instead: 10 chains, 69 members, per-chain concurrency and deadline. Counts do not drift,
they return the same answer on a quiet host, and they are what actually predicts the failure
mode: a chain is killed at its budget and unflushed output is lost, so **members × per-member
cost** is the quantity that matters. That census immediately produced the constraint W6 must
obey — `Stop-chain` holds **25 members at concurrency 8 with no deadline**, and six of ten
chains have no deadline at all.

**Generalizes to.** Any performance claim on a shared machine. **When the clock cannot
resolve the question, stop taking readings and build the counter** — and record the refusal,
because an absent measurement that nobody wrote down becomes, within one session, an
assumption that the thing was fine.

**Disposition.** UKDL process-rule candidate. Companion to the existing measure-the-host-first
lesson; the delta is the *substitution*, not the warning.

---

## T-EXCLUSION-MATCHED-THE-WORKSPACE-001 — the contamination guard became a total blindfold

**Observed (2026-09-19, UCR-CIF W2).** The disposition ledger excludes this mission's own
paths before building its estate index, precisely as `T-SELF-CONTAMINATED-DENOMINATOR-001`
requires. Its first real run reported **`indexed_files=0  distinct_terms=0`**, and therefore
`UNRESOLVED` for all 2,376 requirements.

**Mechanism.** The exclusion pattern `ucr[-_]?cif` was tested against the **absolute** path.
The isolated worktree created for this mission is itself named **`pp-ucr-cif`**, so every
path in the estate contained the excluded token. A guard written to remove ~30 of this
mission's own files removed all 1,339 of everyone else's.

**Why it would have passed as a finding.** This is the part worth keeping. `UNRESOLVED` for
every requirement is *exactly* what a correct sweep of a genuinely novel corpus produces —
and that reading flatters the mission, because it says the corpus is full of unowned,
buildable systems. The estate's sealed history says the opposite is almost always true
(CPP-IAS 150→14, DAIF 22→8, RE Baseline 4→1). **The convenient reading and the broken
instrument pointed the same way**, which is the condition under which nobody looks.

**What caught it.** Not inspection, and not the result looking wrong — the **population
floor** (`indexed_files < 500`). A stale-entry clause could not have; a "did the sweep find
anything" control could not have either, since the answer was a consistent, plausible zero.

**Fix.** Exclusion tests the **repo-relative** path. The absolute path carries the
workspace's name, which is an accident of where the work happens and has nothing to do with
what the file contains.

**Generalizes to.** Any filter whose pattern is derived from the SUBJECT and applied to a
string that also carries the ENVIRONMENT — a working directory, a branch name, a container
id, a temp path, a host name. **Match on the part of the identifier that names the thing,
never on the part that names where you happen to be standing.** And: an isolation workspace
named after its mission will collide with any filter that mentions the mission.

**Disposition.** UKDL trap candidate. Direct inverse of
`T-SELF-CONTAMINATED-DENOMINATOR-001`: that one is a denominator that silently *absorbed*
its subject, this is a denominator that silently *deleted everything else*. Both are
one-line mistakes in the same guard, and both produce a number nobody questions.

---

## W3 · `T-WORKTREE-IDENTITY-BLIND-001` — a repository that could not recognise itself

**Where.** `modules/fable_distillation/federated_ledger.py:49`, `_is_pp_repo`.

**What.** `return "claude-power-pack" in (repo or "")`. UCR-CIF runs from an isolated
worktree at `Apps/pp-ucr-cif`, whose path does not carry the repository's name, so the
Power Pack failed its own self-test and served itself the FIOS/FD-07 advisory written for
*other* repositories. That advisory is what W2 handed over as an open warning.

**Why it survived.** The two obvious readings were both wrong and both actionable. "A
missing asset" invites you to manufacture a deposit to silence it. "The FP-01 false
positive" invites you to ignore it — except FP-01 says the vocabulary is **legitimate**
inside the Power Pack, which is the one place the exemption is supposed to apply.

**The identity was never lost.** A linked worktree's `.git` is a FILE holding
`gitdir: <main>/.git/worktrees/<name>`. INC-025 had already fixed the sibling half of this
— the deposit *key* — by introducing `repo_identity`, and the resolver sits fifteen lines
below the defect. A partial fix left the predicate on the raw substring.

**Fix.** `repo_identity.main_repo_root` resolves a worktree to its repository;
`canonical_repo` deliberately does NOT, so ledger keys stay per-worktree. Collapsing them
would rename every ledger on disk, which `identity.py:41` refuses by name — and a test
pins both directions, because a fix that satisfied only the first would be a silent
migration.

**Generalizes to.** The exact sibling of `T-EXCLUSION-MATCHED-THE-WORKSPACE-001`, one
session later and in the opposite direction: that one matched the environment when it meant
the subject, this one *failed* to match the subject because it was reading the environment.
**A checkout path is where you are standing, not what you are.** Any self-identification by
path substring — repo name, project name, branch — is broken by a worktree, a rename, a
CI checkout directory, or a container mount.

**Disposition.** UKDL hard-rule candidate. Regression `tools/test_repo_identity_worktree.py`
15/15; mutation reverting only the resolution gives 10/15 and reproduces the warning W2
reported, byte-identical.

---

## W3 · `T-POPULATION-FROM-A-DIRTY-SIBLING-001` — 73 rows that exist in no commit

**What.** The handoff and the resumption file both state `baseline_ledger.jsonl` has **73
rows**. Every committed ref — this branch's HEAD, the pinned base `50837ed`, and
`origin/main` — holds **42**. The 31 extra rows exist only as uncommitted working-tree
state in the *other* writer's shared checkout.

**Why it matters more than an off-by-31.** W3's first action was a migration over that
population. Keyed to 73, it would have migrated rows that exist in no commit, on a branch
that cannot see them, and been non-reproducible by anyone.

**Root cause.** A measurement taken in the shared checkout was recorded as an institutional
fact. The concurrent-writers doctrine already says a reading of a shared tree expires the
moment anything else runs; the sharper version is that it was **never about our subject at
all** — a different directory's dirty state.

**Fix.** No tool in W3 hardcodes a population count; every sweep re-reads and carries a
floor. Where a count must be quoted, quote the ref it was read from.

**Generalizes to.** Any figure inherited through a handoff that was measured in a working
tree rather than at a ref. **A population is a property of a commit, not of a directory.**
Cross-check with `git show <ref>:<path>` before building on it.

---

## W3 · `T-FRACTION-CEILING-VACUOUS-001` — a threshold that filtered exactly one thing

**What.** `ownership_evidence.distinctive` began with "a term held by more than 25 % of
owners cannot discriminate". On the synthetic gate (5 owners → ceiling 1) it was absurdly
strict; on the real estate (756 owners → ceiling 189) it admitted **1136 of 1137** held
terms. One instrument, both failure modes, and neither visible from the other population.

**What settled it.** Measuring the actual distribution instead of reasoning about the
shape: 963 of 2100 evidence terms (45.9 %) have ZERO structural holders, and among held
terms it is median 3, p75 7, p90 15, max 474. An absolute ceiling at the measured median is
what "few enough owners to select between them" means.

**Generalizes to.** A threshold expressed as a fraction of a population is only meaningful
if the population is homogeneous and its size is stable. Across a 5-owner fixture and a
756-owner estate it is two different rules wearing one number. **Derive a ceiling from the
measured distribution of the quantity, not from a fraction of the population's size** — and
check it on BOTH the fixture and the real data, because a fraction rule can be simultaneously
too tight and vacuous.

---

## W3 · `T-OWNER-LEVEL-SIGNAL-ATTRIBUTES-A-TERM-001` — a free pass wearing a signal's name

**What.** `CONSUMER` (inbound import edges) was counted among the structural signals that
may promote a candidate owner. Inbound imports are a fact about the **owner**, not about the
term being adjudicated, so the signal fired for every term the owner was ever asked about —
and `quarantine_engine` "verified" as owner of a capability belonging to `ledger_writer`.

**What caught it.** The adversarial gate's "two legitimate owners, no false pick" case. No
amount of reading would have; the signal is individually correct and its aggregation is what
is wrong.

**Generalizes to.** Whenever evidence is fused, check each signal's SUBJECT, not just its
truth. A signal about the container cannot license a claim about the contents. Keep the
corroborating signals — they are real — but only term-attributing ones may promote.

---

## W3 · `T-DISTINCTIVENESS-OVER-MENTIONS-001` — the volume attack through the back door

**What.** Distinctiveness was computed over owners that MENTION a term. So a decoy could
**dilute** a real owner's evidence simply by talking about its capability: the more the
false owner discussed `quarantine`, the less distinctive `quarantine` became, and the real
owner lost its only discriminating term. Simultaneously, filler words unique to one big
document scored as maximally distinctive — rare and meaningless.

**Fix.** Distinctiveness is measured over STRUCTURAL holders (defines / is named for /
registers). A mention cannot make you a holder, so it cannot dilute.

**Generalizes to.** When a metric exists to neutralise a channel, verify the metric is not
itself computed over that channel. The first version imported the very signal it was built
to escape.

**Instrument note.** The mutation that restored mention-counting SURVIVED the first drill,
because the fixture had a single mention-only decoy and the attack needs enough of them to
cross the ceiling. **A fixture that cannot express the attack proves nothing about the
defence**; six decoys made it fail.

---

## W3 · `T-MEMBERSHIP-AGAINST-TUPLES-001` — an assertion that could never match

**What.** `V-W3-LIFE-BYPASS-TIER` asserted `"zzyzx_audit" not in tv.drivers`. `drivers`
holds `(capability_id, verdict)` PAIRS, so the test compared a string against tuples: it can
never match, and it therefore passed with the lifecycle gate removed. It printed the drivers
in its own evidence string, where the tuples were visible.

**Generalizes to.** A negative membership test is satisfied by a type mismatch, silently and
permanently — the positive form would have gone red immediately. Assert on the element shape
you actually have, and be suspicious of any `not in` that has never been seen to fail. The
mutation drill is what exposed it: the gate's own green did not.

**Disposition.** Sibling of the estate's "absence assertion keyed on a translated string"
trap — same family: an absence test whose selector cannot match anything.

---

## W3 · `PR-FORMAT-MATCHES-PRODUCER-001` — a formatter that laundered the evidence

**What.** The adjudicator wrote `disposition_ledger.json` with `indent=2`; its producer
writes `indent=1`. A 996-row change arrived as **58,624 insertions / 57,747 deletions** — a
full-file rewrite in which the actual change was unreviewable. After matching the producer:
4,314 / 4,307, proportionate to 1,655 touched rows.

**Generalizes to.** When writing back to an artifact another tool produces, reproduce its
serialization exactly. **A diff is evidence, and a reformat destroys it** — this is the
shared-file laundering rule applied to a machine-generated artifact rather than to source.

---

## W3 · `PR-LIFECYCLE-IS-NOT-FITNESS-001` — check the arithmetic before reusing a scale

**What.** `contract.Maturity` (EXPERIMENTAL → MATURE) looks like a lifecycle and is a
fitness scale. `applicability` consumes it as one 0.15-weighted factor, so degrading a
capability from MATURE to EXPERIMENTAL shifts its score by at most `0.15 × 3/4 = 0.1125`.
A relevant, high-stakes capability stays MANDATORY however far its maturity falls:
**revocation through maturity is arithmetically impossible**, and "less proven" was the
wrong claim anyway.

**Generalizes to.** Before reusing an existing field for a new meaning, compute the maximum
effect it can have on the decision you need it to change. A scale built to RANK cannot
express WITHDRAWAL, and the test is one multiplication, not a judgement.

---

## W4 · `T-STALE-BYTECODE-OUTLIVES-A-VERIFIED-RESTORE-001` — the restore was perfect and the wrong thing was running

**What.** A mutation drill changed `_PP_MARKS_REQUIRED = 3` to `= 0`, ran a suite, wrote the
original bytes back and verified SHA-256. It reported `restore=OK`. Three suites then ran
against the MUTATED behaviour, because CPython validates a `.pyc` on `(mtime, size)`, the
edit is byte-length preserving, and the restore landed inside the same second — so the
cached bytecode still matched and was served. Measured directly: `pyc records
mtime=1789865699 size=9871`, `source has mtime=1789865699 size=9871`, `pyc considered
VALID: True`, while `grep` showed `= 3` and the running module reported `0`.

**Why it survived its own verification.** The drill verified the SOURCE, and the source was
never wrong. A hash of the artifact upstream of the one that executes is not evidence about
execution.

**How it was caught.** Not by the drill. By the full-suite sweep afterwards, which went
15/17 with two failures the drill had declared clean. A per-change check and a sweep are not
redundant: the sweep sees the composed world.

**The part worth more than the fix.** `tools/mutation_probe.py` line 110 already documented
this exact mechanism, in these words, and already defended against it with
`PYTHONDONTWRITEBYTECODE` plus a cache purge — from its own first real run. The knowledge was
written down, correct, and unreachable at the moment of hand-rolling a drill. The repair is
therefore not a note: `--plan` was added to that harness so a directed mutation cannot be
aimed without inheriting the defence.

**Generalizes to.** Verify the artifact that EXECUTES, not the one you edited. Anywhere a
cache is validated by a coarse key — bytecode by `(mtime, size)`, HTTP by `ETag`, a build by
a timestamp — a same-size change inside the key's resolution is invisible, and a
length-preserving edit is the shape that hits it.

---

## W4 · `T-FROZEN-REASON-CANNOT-NOTICE-IT-IS-FALSE-001` — a ratchet describing a debt that had already been paid

**What.** The W3 lifecycle ratchet froze `spec_depth_selection` as UNKNOWN with the reason
"UNEVALUABLE — no deterministic probe exists for this condition. Probe debt this repository
could pay." Measured: `probe_spec_depth_selection` existed, was registered in `PROBES`, and
RAN. It abstained for a completely different reason — 99 incident records against a sample
floor of 200 — which is an evidence frontier owned by time, not a coding task. A session
acting on the frozen reason would have written a second probe beside a working one and
learned nothing.

**Root cause.** The reason was a CONSTANT in a table keyed by verdict status, and UNEVALUABLE
covers two different debts. A constant cannot notice when it stops being true.

**Fix.** The migration DERIVES the reason from the verdict: no `probe` field means nobody
wrote one, a `probe` field means one ran and honestly could not conclude, and the abstention
carries the number that would resolve it.

**Generalizes to.** A frozen inventory needs its reasons computed from current evidence, not
copied at freeze time. The stale-entry clause stops a list outliving its subjects; this is
the sibling failure — an entry whose subject is still real and whose EXPLANATION has rotted,
which is worse, because the list still looks maintained.

---

## W4 · `T-A-SAMPLE-FLOOR-THAT-GATES-BOTH-POLES-001` — an instrument that could only ever give one answer

**What.** The same probe applied its 200-record sample floor AHEAD of the hit scan, so on a
corpus of 99 it returned UNEVALUABLE whatever the corpus contained. Fifty spec-omission
incidents would have produced the same verdict as zero.

**Why the floor is still right.** A zero over a tiny denominator is evidence of a small
corpus, not of extinction. But PRESENCE is not weakened by a small denominator: one incident
is one incident. The floor belongs on the zero branch alone, and lowering it to 99 to "close
the population" would have been coverage bought with a false certainty.

**Discipline that separates the two.** The fix ships as a PAIR of gates —
`V-PROBE-SPEC-PRESENCE-BEATS-FLOOR` (1 hit over 50 → ACTIVE) and
`V-PROBE-SPEC-ZERO-STILL-FLOORED` (0 over 50 → still UNEVALUABLE). The second is the one that
goes red if anyone later lowers the floor, and it is what makes the change a repair rather
than a purchase. Measured after the fix: 0 hits over 99, so the capability is STILL
UNEVALUABLE — which is exactly why the change was safe to make.

**Generalizes to.** A guard clause placed before the measurement gates both poles. Ask of
every threshold: which of my two answers is this protecting, and can the other one still be
reached?

---

## W4 · `T-A-QUEUE-IS-NOT-A-POPULATION-001` — two gates that went red the moment the work succeeded

**What.** Two new gates asserted over `plan()["to_write"]` — the migration's pending queue.
They passed before the migration was applied and failed immediately after, because an applied
plan has nothing left to write.

**The dangerous version is the one that did not happen.** Phrased as "no row lacks the
disclaimer" instead of "every row has it", the same gates would have passed VACUOUSLY over an
empty set, for ever, and nobody would have looked again.

**Fix.** Audit gates read the durable lifecycle log, with a population floor of one. A
separate gate drives the live classification path on a SYNTHETIC subject, so deleting the
disclaimer is still caught after the queue empties — and the mutation drill confirms that
gate is load-bearing: E2 is caught by it alone.

**Generalizes to.** A transient work queue is not a population. Assert over the durable
record of what happened, and put a floor under it.

---

## W4 · `T-A-ROUND-TRIP-DELETES-WHAT-IT-CANNOT-SEE-001` — one state change, three fields gone

**What.** Writing a lifecycle value into a capability contract deleted `_matcher_note`,
`verification_obligations` and `minimum_runtime_version` from it, and escaped every em dash
to `\uXXXX` so the diff was 61 lines. `from_dict` keeps only declared dataclass fields;
`to_dict` therefore returns a reduced document; `save_contract` wrote that over the original.
`_matcher_note` was the record of why that contract's triggers had been rewritten — the
institutional memory of a previous defect, destroyed by a one-field update.

**Why the round-trip test could not see it.** `V-CAPRT-ROUNDTRIP` saves a contract built IN
MEMORY into an empty directory. There was never a prior document, so there was never anything
to lose. A fixture that constructs its own subject can only express states its author already
believed in.

**Generalizes to.** A store must not destroy what it does not model: merge over the document
on disk rather than replacing it. And any "we round-trip correctly" claim must be tested
against a document the writer did NOT create.

---

## W5 · `T-THE-TRIGGER-VOCABULARY-CANNOT-DISCRIMINATE-001` — an espresso machine routed to the knowledge module

**What.** The first applicability filter admitted a unit when the proposal shared two of its
adjudicated evidence terms. A proposal about an espresso machine — bean freshness, grind size,
portafilter temperature — routed to `modules/knowledge_acquisition` with four matching units.
Every one of those matches was the same pair: `('institutional', 'system')`.

**Why.** Those words are in the novelty gate's own **trigger list**. The gate only fires on a
proposal that contains them, so by construction they are present in 100% of the population
being discriminated. A term the whole population shares is the population's common denominator
and carries no information about membership. Counting terms cannot see this, because two
generic terms and two distinctive ones are both "two". Measured spread across the authoritative
corpus: `failure` is held by 21 owners, `evidence` by 16, `knowledge` by 12.

**Fix.** At least one shared term must be DISTINCTIVE — held by few enough owners to say *which*
owner. The threshold is the producer's own `DISTINCTIVE_MAX_HOLDERS`, imported and never
redefined, with a gate that fails if a copy of the constant ever appears in the consumer. 83%
of evidence terms qualify, so the clause narrows the false pole rather than the true one.

**The negative gate needed a sibling.** "The foreign proposal does not route" is satisfied by a
matcher that stopped matching entirely. `V-W5-SEL-FOREIGN-DID-OVERLAP` asserts those five units
*did* share two terms and were refused for carrying no distinctive one.

**Generalizes to.** Whenever a filter runs downstream of a trigger, the trigger's vocabulary is
useless inside it. Ask what every input that can reach this code already contains, and exclude
exactly that from the evidence.

---

## W5 · `T-A-MEMO-OUTLIVED-THE-FACT-IT-DESCRIBED-001` — a deleted owner kept routing

**What.** Owner existence was memoized beside the ledger rows, keyed on the ledger's mtime and
size — 996 authoritative rows name only 40 distinct owners, so the naive form paid 956
redundant filesystem calls on a hook path. Deleting an owner's directory cannot change the
ledger's mtime, so the memo answered "present" for a directory that was gone, and a stale
authority kept producing obligations.

**Why it is the wave's own disease.** W5 exists because a store's content was not reaching a
consumer. This was a derived view whose key belonged to a *different* source than its subject:
the lifecycle validity of a path is a projection of the filesystem, never of the ledger.

**Fix.** The memo is per selection. One selection is one consistent view of the repository — 40
stat calls instead of 996 — and the next selection looks again. Found by the lifecycle drill,
not by reading; the code looked obviously correct.

**Generalizes to.** Before caching a derived value, name the source that can invalidate it, and
check that the cache key comes from THAT source. Two sources, two lifetimes, one key is a
staleness bug with no symptom.

---

## W5 · `T-A-DETECTOR-MATCHED-ITS-OWN-OUTPUT-001` — "proven" inside "Provenance"

**What.** The UNKNOWN-safety gate scans the emitted obligation for words that would assert a
certainty the institution does not hold — `verified`, `already satisfied`, `proven`. It went
red on a line the same commit added: `Provenance: vault/ucr_cif/...`.

**Generalizes to.** A substring detector run over text the same change writes is measuring
itself. Word-bound the pattern, and check the detector against its own product before trusting
a red.

---

## W5 · `T-THE-SURFACE-CARRIES-THE-MESSAGE-NOT-THE-STRUCTURE-001` — a gate red while its evidence sat in the output

**What.** The live production-reality gate asserted `"Why is extending modules/"` appeared in
the hook's `additionalContext`. That wording exists only in the verdict's `questions` tuple;
the hook injects the verdict's `message`, which names each owner and then asks
`"Why is extending it insufficient?"`. The gate failed while the obligation it was looking for
was in the output it was reading.

**The worse half was the control beside it.** "The junction worked" was asserted by looking for
the ledger path in the output — a string this very change's obligation contains. It could only
confirm what the gate next to it already said, and it passed while its sibling failed. Replaced
by a two-sided control: the marker must be present in the output AND provably absent from the
installed tree, so its presence is attributable to the worktree under test.

**Generalizes to.** Assert on what the SURFACE emits, not on the richest representation
available in-process. And a control whose evidence is produced by the subject is not a control.

---

## W5 · `T-A-FIXTURE-THAT-CANNOT-EXPRESS-THE-DIFFERENCE-001` — the surviving mutation

**What.** `W17-tokenizer-divergence` collapses the producer's two term-length thresholds
(entities ≥ 4, body text ≥ 5) into one. The gate named for exactly that property used the probe
`"compile the mission"` — in which every word survives either threshold. The mutation was
invisible to the fixture asserting about it.

**Classification.** Not an equivalent mutant and not a reachability question: a real behaviour
change the instrument could not express. The repair is the fixture, not a new gate — a
four-letter word, admitted from an entity and refused from body text.

**Generalizes to.** A fixture must contain an input that lies BETWEEN the two behaviours it
distinguishes. If every element of the fixture falls on the same side of the boundary, the test
is named for a property it cannot observe.

---

## W7 · `T-GATE-READS-THE-ARTIFACT-NOT-THE-PRODUCER-001` — my own reader/consumer defect

**What.** `test_ucr_cif_reach_reality` asserted the candidate-policy results by loading
`w7_shadow.json` from disk. Mutation `W30` broke the shadow scorer's population and every one
of those assertions still passed, because a stale artifact answers exactly as a correct one
does.

**Why it is the sharpest trap of the wave.** This is the reader-vs-consumer distinction W5 was
called to make, reproduced inside W7's own evidence layer — by the session that had just
re-run W5's proof of it. Writing a rule down does not transfer it to the moment you type an
assertion; only a drill does.

**Repair.** Import the scorer and DRIVE it. Tell: if deleting the producer's source leaves the
gate green, the gate is reading. Promoted as an amendment to
`PR-MUTATE-THE-LINK-NOT-THE-ENDPOINTS-001`.

---

## W7 · `T-PATCHED-THE-RIGHT-OBJECT-AND-ASSERTED-THE-WRONG-FIELD-001`

**What.** The gate proving the instrument holds no private copy of the product's `SPEC_GLOBS`
patched the product's list and asserted the CEILING flipped. It does flip — but via the gate's
own `_find_spec`, which reads the patched list regardless. Mutation `W26` gave the instrument a
private copy and survived: only `matched_globs`, the glob *attribution*, exposes the copy.

**Generalizes to.** When one patch reaches a subject through two paths, assert on the field the
mutation actually changes, not on the field that is easiest to observe. A patch that flips the
convenient field proves the path you were not worried about.

---

## W7 · `T-THE-FUNNEL-COULD-HAVE-MODELLED-ITS-SUBJECT-001`

**What.** Before the mutation plan was written, a mutant that replaced
`sdd_tier.evaluate(...)` with a prediction of its output from the gate's action satisfied every
gate in the suite. The whole reach measurement would then have measured my model of the signal,
and would have agreed with reality until `sdd_tier` changed.

**Repair.** `V-W7-FUNNEL-DRIVES-THE-LIVE-SIGNAL` severs the call and requires the failure to
surface, with a restore control. Kept as mutation `W33`. This is *mutate the link* turned on the
instrument rather than on the product.

---

## W7 · `T-A-DIRECTORY-IS-NOT-A-REPOSITORY-001`

**What.** Two population errors in the first host sweep, in opposite directions. Matching `.git`
as a DIRECTORY missed every git worktree — 52 found where the corrected instrument finds 181,
and the missing set included the worktree this mission runs in. Then counting each surviving
directory as a repository turned ~5 repositories into 81, and because worktrees share content
they share the measured property, so the inflation correlated perfectly with the result.

**Also.** That sweep printed `COUNT=52` *after* emitting a `Get-ChildItem` reparse-point error —
a partial sweep presenting as a complete one. Errors are now first-class fields of the discovery
result, not log lines.

**Promoted.** `T-N-WORKTREES-ARE-ONE-OBSERVATION-001`.

---

## W7 · `T-A-ZERO-THAT-CONTRADICTS-A-KNOWN-NUMBER-IS-AN-INSTRUMENT-FAILURE-001`

**What.** Reading the disposition ledger for authoritative owners returned `AUTH 0 /
DISTINCT_OWNERS 0`. The estate has recorded 996 authoritative dispositions across 40 owners
since W3, so the answer was impossible. The premise was wrong, not the world: the rows carry
`proposed_owner`, not `owner`, and authority is the disposition VALUE
`EXTEND_EXISTING_OWNER`, not a status word beginning "AUTH".

**Why it matters here.** A zero is the most dangerous reading in this wave, because "nothing is
owned" is also what a correct sweep of a genuinely novel corpus returns — the same inversion
`HR-NOVELTY-001` exists to stop, and the same shape as W2's
`T-EXCLUSION-MATCHED-THE-WORKSPACE-001`. It was caught only because a prior measurement
contradicted it.

**Rule.** Verify a store's real schema before reading it, and treat any result that contradicts
an already-sealed number as an instrument failure until proven otherwise.

---

## W7 · `T-FIRST-MATCH-CLASSIFIER-REPORTS-ITS-OWN-LAYOUT-001`

**What.** The reporting classifier returned the first matching row and put 100 of 127 Tier ≥ 2
prompts into `investigation`, because that row sat first and its needles appear in almost any
long prompt. The per-class funnel — the read that a candidate policy would have been designed
from — was an artifact of the source file's ordering.

**Promoted.** `T-CLASSIFIER-DECIDED-BY-TABLE-ORDER-001`.

---

## Standing obligation

New failures are appended here **in the session they occur** (zero knowledge debt), and
evaluated for UKDL promotion at Phase 9 — never auto-promoted, never silently dropped.

## W9 · `T-THE-STRUCTURAL-FAMILY-WAS-A-PROJECTION-001` — 996/996 = 100 %
The unit-level structural predicate is guaranteed by W3's own promotion rule,
so it is constant over the authoritative population and discriminates nothing.
Caught by measuring the REJECTED population too (14.9 %). Pinned by
`V-W9-UNIT-LEVEL-IS-A-PROJECTION`.

## W9 · `T-THE-STALE-CASE-PASSED-ON-THE-WRONG-CHANNEL-001` — W46 survived
The stale-ledger gate rewrote the ledger with a longer generation id, so the
SIZE check caught it and the `corpus_id` comparison was never exercised.
Disabling that comparison entirely left the suite green. Fixed with a
same-length id swap at an identical 46,364 bytes, plus a HARNESS branch that
fails loudly if the swap ever changes the length again.

## W9 · `T-THE-REPAIRED-ANCHOR-EDITED-DEAD-CODE-001` — W36 survived its repair
Repointed onto `_rank_key`, which the same wave then made the non-shipped
branch. An anchor must follow the code that ships, not the code that shares
its name.

## W9 · `T-THE-CAP-FIXTURE-COULD-NOT-SEE-THE-CAP-001` — three owners, cap of five
"Ranking cannot lose a true positive" passed on a fixture below `MAX_OWNERS`.
Two real labelled cases had the true owner at index 4 and lost it. A second
attempt at the fixture then routed NOTHING, because giving four filler owners
the same term pushed it past `DISTINCTIVE_MAX_HOLDERS` — adding owners to a
term destroys its distinctiveness, and a fixture has to respect the clause
rather than fight it.

## W10 · `T-THE-HEADLINE-HAD-NO-INSTRUMENT-001` — a number with no code behind it
W9's "6 improved / 12 worsened over 30 cases, p = 0.238" existed in exactly two
places: prose in `07_W9_STRUCTURAL.md` and a docstring in
`disposition_consumer`. **No committed code computed it.** A repo-wide sweep at
W10 open is what found this; two directory-scoped greps had already come back
empty and I widened rather than concluded.
The consequence is not untidiness. The brief requires both arms re-derived
fresh rather than read from a stored report — and there was nothing to run, so
the previous wave's headline was unfalsifiable in both directions.
**A measurement recorded only in prose is a claim, not a result.** If a number
gates a decision, the code that produces it ships in the same commit.

## W10 · `T-THE-TRUTH-SET-WAS-A-FUNCTION-OF-THE-ARM-001` — suppression flattered the treatment
`reach_ground_truth.label_case(case.owners_routed, …)` credits an owner only
when that owner **was routed**. Correct for W7's activation question, which
asks whether what we said was useful. Reused for a RANKING question it leaks,
and the leak runs one way: a case whose true owner the treatment DROPS yields
no hits, is re-labelled `NOT_RELEVANT`, and **leaves the population** instead
of counting as the loss it is.
So dropping a true owner improved the apparent score. W9 measured through this.
**An oracle reused across questions inherits the question it was built for.**
Ask what the label is a function of before reusing it; if the treatment is one
of its inputs, it is not ground truth for that treatment.

## W10 · `T-THE-DECOMPOSITION-WAS-DISCARDED-ONE-LINE-LATER-001`
W9 reported that it could not apportion its −6 between ranking and cap
eviction. The reason was two adjacent lines: `owners.sort(...)` computed the
ranked verdict and `owners[:MAX_OWNERS]` threw away everything past the cap on
the next. The quantity was not merely unmeasured — it was **unmeasurable**, and
no amount of labelling would have produced it.
**When a wave reports "cannot apportion", look for the line that discards the
evidence before looking for more data.**

## W10 · `T-A-FIXTURE-CANNOT-CATCH-A-TRUNCATION-001` — the gate I nearly shipped
Designing the mutation `W62-precap-truncated-to-the-cap` exposed a hole in the
suite I had just written: slicing `precap_owners` to `MAX_OWNERS` would delete
the whole rank/cap decomposition, and **every one of my fixture gates would
still have passed**, because a fixture supplies both lists directly and never
calls the selector.
Fixed by forcing `MAX_OWNERS` to 2 in-process — it is read at call time — and
requiring the two lists to differ on a REAL selection.
This is `T-THE-CAP-FIXTURE-COULD-NOT-SEE-THE-CAP-001` one layer up, found by
writing the mutation rather than by writing the test. **Design the mutation
first; it names the gate the suite is missing.**

## W10 · `T-A-BACKGROUND-MUTATION-RUN-IS-A-CONCURRENT-WRITER-001`
`mutation_probe` edits source in place and restores it. Committing while a plan
runs can capture a MUTANT as the healthy world — a false green that survives
review, because the diff looks like whatever the mutation was.
I committed `disposition_consumer.py` with a family re-verification in flight
and had to verify after the fact (it was clean: five markers checked at
`HEAD`). Minutes later the same run had `reach_funnel.py` mutated on disk.
**A mutation run holds a write lock on the tree in every sense that matters.
Commit before it starts or after it finishes, never during — and if you already
did, verify the committed BYTES rather than the exit code.**

## W12 · `T-THE-BINDING-GATE-WAS-NOT-THE-MODELLED-GATE-001`
Two admission authorities decide whether this experiment runs, with different
criteria, and the mission models only one of them.
`environment_qualifier.capacity_probe` reasons about the **workload**: 155 MB
against 4,267 MB available, `ADMITTED`, clear of the ×1.5 margin — and it was
right, the run would have completed. The harness's background-shell reaper
reasons about **host total while the session is idle**, and took the same 155 MB
job at 3,947 MB free. Its own notification says so: *says nothing about the
command or its own memory use.*
A run can be ADMITTED by the first and reaped by the second for ever. This is
not a bad threshold; it is a second gate whose input is a quantity the first
never reads. **When a run keeps dying after its owner's admission gate passes,
stop tuning the workload and go find the other gate.** Shrinking the experiment
cannot reach it — the job was already one twenty-sixth of free memory — and
neither can retrying, because the trigger is sampled exactly when a long
derivation is idle.

## W12 · `T-THE-ANCHOR-MATCHED-ITS-OWN-RESTORE-LINE-001`
W10's `W64` rotted when W11 replaced the `if treatment:` block with the `_ARMS`
table. The faithful-looking repair is to flip `os.environ.pop(k, None)` in the
new `else` branch. At twelve spaces of indentation that string is **also a
substring of the sixteen-space restore line in the `finally` block**, so the
anchor matches twice and the probe mutates the restore path rather than the
selection path — a mutant editing code no arm depends on, behind a diff that
looks perfectly correct. That is `T-THE-REPAIRED-ANCHOR-EDITED-DEAD-CODE-001`
arriving through indentation instead of through a refactor.
**An anchor's uniqueness is a property of the whole file, not of the line you
copied it from. Count the matches before trusting the repair**, and prefer an
anchor at the point where the semantics live — here the identity table, which is
also strictly stronger, because it contaminates the control with the prose
environment as well as the rank one.

## W12 · `T-A-DEFAULT-ARGUMENT-CAN-BE-A-DESTRUCTIVE-DEFAULT-001`
`ucr_cif_oracle.main`'s `--store` defaults to the canonical case store. A
treatment run with default flags therefore **overwrites the control record the
comparison is against**, in place, with no confirmation and no diff — and the
overwrite is invisible until a paired verdict is refused for a drift the
operator caused.
The whole hazard is a convenience: the default is right for the one command that
refreshes the canonical store, and wrong for every other caller. **Ask of every
destructive default what it destroys when the flag is omitted by someone who did
not read the parser**, especially where a tool's ordinary mode and its
answer-key-refreshing mode share one entry point.

## W12 · `T-THE-PRECAUTION-THAT-COST-AN-ARM-001`
`--verify` reported `source_fresh False`. The projection predated W11's own
commits `390c3e6` and `f281762`, one of which changed how declaration works, so
I concluded it was the output of a superseded extractor, killed the running
reference arm and rebuilt.
The rebuild changed four lines — `build_ms`, `built_at`, `repo_fingerprint`,
`files_seen` 1373→1376 — and **no evidence at all**: 674 symbol-held and 236
declaration-held terms byte-identical. The extractor's code had changed and its
output had not.
The reasoning was sound and the conclusion was unmeasured. **A freshness flag
tells you the inputs moved, never that the output did** — and the output is one
diff away. Cost: about fifteen minutes of a half-hour arm. Recorded as a
precaution that bought nothing rather than as a catch, because the next reader
should take the same precaution and check the diff FIRST.

## W12 · `T-A-HAND-ENUMERATED-PREFIX-LIST-EXPIRES-EVERY-WAVE-001`
`prose_authority.SELF_MEASUREMENT_PREFIXES` enumerates `tools/test_w9_`,
`_w10_`, `_w11_` by hand, so this mission's own instruments stop being
recognised as self-measurement the moment a new wave names a file. W12's
`tools/test_w12_verdict.py` already falls outside it. The sibling instance:
`RUNTIME_DIRS` and `CONTRACT_DIRS` both list `"skills"`, which cannot fire at
all, because referrers are enumerated from `ownership_evidence.SCAN_DIRS` and
that tuple has no `skills`.
Same root cause in both directions — a population enumerated rather than
discovered — one over-narrow and one over-wide, and **neither is visible from
the list itself**. Measured inert today (declared terms 814, owners 26,
`governance-overlay` 256, SELF_MEASUREMENT edges 9, all identical to W11's
record with three new `tools/` files present), and deliberately NOT repaired,
because the subject may not move before its first valid measurement.

## W12 · `T-THE-GATE-ASSERTED-A-STRING-THE-OUTPUT-CARRIES-ANYWAY-001`
The W12 comparator's headline must name the **post-cap** half, because W10
proved pre-cap `evicted = admitted = 0` and every set-level effect is the cap's.
The gate asserted `"NOT_RECOVERED" in out` — which the post-cap movement line
satisfies no matter which half the headline is keyed to. A comparator reporting
the flattering half would have passed.
Found by writing the mutation (`W69`) and noticing it had **nothing to fail
against**. The gate now parses the value off the headline line itself.
**A substring assertion over a report that already contains every verdict word
is not an assertion about the field you meant** — and a mutation written beside
the instrument finds that, where a mutation written after the result finds
nothing.
