# SCS C94 — SQI Weakening Detectors: the attack the guardian cannot see

> Sealed 2026-07-12. Predecessor: SCS C93 (the baseline guardian).
> SQI-02 Part XV, implemented. The Verification axis now gates the CONTENT of the suite, not
> only its size.

---

## Why this had to exist

SCS C93 shipped a guardian that fails the build on a decrease. It gates **counts** — executed
cases per root, authored files, reach — so it catches every failure that lowers a number: a
deletion, a skip, a scope line, a relocation.

**Weakening lowers nothing** (§15.1). A removed assertion, a widened exception handler, an unreal
fixture, over-mocking, a lowered threshold, a tautological assertion: in every one the file is
present, the case is collected, the case is executed, **the case passes, the count is identical,
and the protection is gone.** Part XV is blunt about what that makes it — *the perfect attack
against a count-based instrument* — and the guardian is a count-based instrument. It was a locked
door in a building with no walls.

---

## What shipped

| artifact | what it does |
|---|---|
| `modules/sqi/weakening_detectors.py` | AST counters (assertions, mocks, cases, broad catches), content hashes, the §15.8 mutation probe |
| `modules/sqi/weakening_baseline.py` | ONE store, per-file records, four gates, the §15.10 firewall |
| `tools/run_sqi.py` | layer 5. **Exits non-zero on `WEAKENED`.** `--mutation-probe` is opt-in |
| `modules/sqi/discovery_rules.json` | the assertion vocabulary, now a **governed** artifact |
| `tests/test_sqi_engine.py` | +10 tests inside the canonical invocation (76 → **86**) |
| `tools/test_sqi.py` | +8 V-gates. **`SQI_PASS=53/53` ×3 hermetic, exit 0** |

| gate | catches | verdict | §  |
|---|---|---|---|
| **A** assertions fell | the removed assertion | **FAIL** | 15.2 |
| **B** mocks rose ∧ assertions did not | over-mocking | **FAIL** | 15.6 |
| **C** hash moved ∧ arithmetic held | unreal fixture · same-name rewrite | REVIEW | 15.4 / 15.9 |
| **D** broad handlers rose | the widened handler | REVIEW | 15.3 |
| probe | a mutant survives | the tautological assertion | **FAIL-class** | 15.8 |

**C and D are advisory by the Part's own instruction, not by concession.** §15.3: the broad-handler
detector's output is *"a candidate list for review rather than a verdict, because a broad handler
is sometimes correct."* §15.4, of the unreal fixture: *"there is no counting detector for this and
it would be dishonest to claim one."* A gate that failed a build on either would be wrong often
enough to be switched off — and a switched-off gate protects nothing, which is the entire subject
of this corpus.

---

## The two places the plan would have disarmed it

Same family as SCS C93's ratio finding. The dataset's own attack catalogue defeats both.

### 1. A mocks/assertions RATIO gate is quieted by the attack it exists to catch

The plan specified `mock_count / assertion_count > threshold`. A ratio falls when its **denominator
rises**, and the cheapest way to raise an assertion count is to add `assert result is not None` —
an assertion that passes for every implementation **including a broken one**. That is weakening
**§15.8**. The gate would be silenced by the precise attack Part XV exists to catch, and it would
report an improvement while the suite got weaker.

It also has no basis in the text: §15.6 specifies a **delta** (*"a test whose mock count rose while
its assertion count did not"*), not a ratio, and inventing a threshold and attributing it to the
Part would be `T-SQI-FINDING-FABRICATION-001` exactly.

**Built instead:** the delta on two absolutes — mocks rose **and** assertions did not rise.

### 2. Three baseline stores would fork the mechanism the guardian owns

The plan specified `assertion_baseline.py`, `mock_baseline.py`, `content_hash_baseline.py`. But
**§15.6 is a predicate over TWO numbers**, and three independent stores cannot express it without
one reaching into another's file. It would also triple-fork the firewall, the ratchet, and the
acceptance path `baseline_guardian` already owns (`T-SQI-PARALLEL-SYSTEM-001`).

**Built instead:** one store, per-file records `{assertions, mocks, cases, sha256, verification}`.

**And one departure from Part XII, deliberately:** this baseline is **not** environment-keyed. The
Part XII key exists because *execution* results vary by toolchain. These counts are **static** —
read from the syntax tree, identical on every host. Keying them to the environment would make
"run it on a different machine" the cheapest way to erase every assertion you had removed.

---

## The detector's first finding was about the detector

First run: **230 assertions across 101 authored test files.** Ninety-two of those files reported
**zero** — and sixty of them had been verifying things all along, in the estate's own V-gate idiom
(`_ok` / `_fail`), **one file 139 times over.** Every one of those 139 gates could have been
deleted without moving a single number, **because zero cannot fall.** The gate was theater across
59% of the census, and it would have reported a clean bill of health forever.

Corrected vocabulary — now a **governed artifact**, where narrowing it is a reviewable act:
**2,158 assertions.** Sealed as `T-SQI-NARROW-VOCABULARY-BLINDS-THE-GATE-001`.

A third idiom surfaced with it. **23 files gate on a non-zero exit code** and contain no assertion
of any recognized form: they build a results table, count failures, and `sys.exit(main())`.
Recording them as zero would have been the worst available answer — it would call them unprotected
**and** hand the gate a number that can never alarm. They are **UNKNOWN**, tracked by content hash
only. *Zero is a measurement; this is the absence of one.*

And **nine files verify nothing at all** — no assertion, no exit gate. Per §15.2 those are not
tests; they are executions, and every runner reports them as passing. They are named in the report.

---

## The probe found a hole in its own author's tests

`python tools/run_sqi.py --mutation-probe` — 8 mutants, and **two survived**: the `return` in
`default_baseline_path`'s fallback branch, in **both** baseline modules. Breaking it left **41
tests green.** That branch is the only reason the done-gate is hermetic — it redirects the
baselines into a temp tree — and had it silently stopped working, every gate run would have
ratcheted the repository's real baselines as a side effect of being run.

A test was added. Both mutants now die. **Survivors: 0. Killed: 5.**

That is 15.8 working exactly as written, and it is the reason the probe is worth its cost: *every
green test through a broken return value is asserting nothing about the value it claims to
protect.*

**One precision the Part leaves implicit and this implementation states:** a surviving mutant means
*either* no reached test executes the line *or* one does and asserts nothing. From the point of
view of protection these are the same fact — the value is unprotected. They differ only in the
repair: the first wants a test, the second wants an assertion.

---

## Declared, not faked

- **The lowered threshold (§15.7) is NOT detected.** It needs an inventory of every threshold in
  the repository, versioned, each change a governance event. That inventory does not exist.
- **The unreal fixture (§15.4) has no counting detector**, by the Part's own admission. What is
  offered is the content hash: the change is surfaced for review, and the reviewer is told the
  arithmetic did not move — which is the signature of a fixture edit and of a same-name rewrite.
- **The mutation probe is opt-in.** It mutates source and executes tests, and a measurement that
  alters what it measures as a side effect of measuring it is not a measurement. Absent the flag it
  is `NOT_RUN`, which is reported as such — **never as zero survivors**.
- **A KILLED verdict certifies one return value, never a file.** The probe breaks one site.

## Owner decisions, untouched

The `_logs/` `SystemExit`-at-import crash · the absent root pytest configuration · the canonical
invocation · the 63 of 64 module packages with no reached-test references. All four still stand in
the report, unrepaired (SQI-02 §9.10 — changing the invocation after seeing the number is scope
laundering).

**UKDL sealed:** `T-SQI-WEAKENING-INVISIBLE-001`, `T-SQI-NARROW-VOCABULARY-BLINDS-THE-GATE-001`.

**Reproduce:** `python tools/run_sqi.py --mutation-probe` · `python tools/test_sqi.py`
