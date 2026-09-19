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

## Standing obligation

New failures are appended here **in the session they occur** (zero knowledge debt), and
evaluated for UKDL promotion at Phase 9 — never auto-promoted, never silently dropped.
