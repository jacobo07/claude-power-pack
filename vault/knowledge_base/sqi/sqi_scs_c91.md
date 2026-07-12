# SCS C91 — SQI-Executable: the corpus becomes infrastructure

> Sealed 2026-07-12. Predecessor: SCS C90 (spearhead corpus, SQI-00…03).
> The Verification axis stops being doctrine and starts refusing things.

---

## What shipped

| artifact | dataset | what it does |
|---|---|---|
| `modules/sqi/repo_reality_scanner.py` | SQI-01 | read-only inventory; manifest-first; five parameters per language context; sixteen domains as a **set**; fail-open to UNKNOWN |
| `modules/sqi/environment_qualifier.py` | SQI-03 | seven short-circuiting gates; six states; verbatim blockers; QUALIFIED never granted by the absence of a complaint |
| `modules/sqi/reconcile.py` | SQI-02 | two censuses that do not share a producer; identities not counts; three oracles; join-sanity assertion; surprise-set self-audit; five green verdicts |
| `modules/sqi/discovery_rules.json` | SQI-02 §3.4 | the governed artifact: patterns, exclusions, per-rule hit counts |
| `tools/run_sqi.py` | — | unified runner → `vault/audits/sqi_report_<date>.md` + JSON sidecar |
| `tests/test_sqi_engine.py` | SQI-02 §5.10 | 24 tests, **inside** the canonical invocation |

**Gate:** `python tools/test_sqi.py` → `SQI_PASS=36/36`, ×3 hermetic, exit 0 (27 corpus + 9 engine).
**Liveness:** `sqi-runner` registered in the D1 Ledger. **Telemetry:** CO-12 `sqi_reconcile` signal.

---

## What the engine found, on its first contact with this repository

The plan predicted it would reproduce the founding finding — 70 of 76 test files unreached,
an orphan ratio near 0.92. Every number came out different, and each difference is a fact
about the repository rather than a defect in the instrument.

**1. The gap widened. It did not close.**
The authored census is **100** python test files, not 76. Ten were authored in the four days
*after* the founding audit — including `tools/test_sqi.py`, the gate of this very corpus — and
every one landed outside the canonical invocation. Thirteen more match `*_test.py`, a suffix
class the audit's discovery rule never counted at all.

**2. The canonical invocation reaches 2 files, not 6.**
Four of the six files inside `tests/` are script-style V-gate runners with zero
pytest-discoverable cases. The audit counted **files in a directory**; the engine counts
**identities in a manifest**. Test File Reach is **3.0%**, not 7.9%. These four are not orphans
— orphans are outside — they are a class the corpus had not named: **inert-in-root**, sitting
inside the reach boundary and protecting nothing. Sealed as `T-SQI-DIRECTORY-NOT-MANIFEST-001`.

**3. The authoritative invocation reaches nothing at all.**
There is no CI workflow and no pytest configuration at the root, so by SQI-02 §9.4's oracle
precedence the **zero-argument default is authoritative** — it is what a human, a hook, or an
agent with no prior context will type. Run today, `pytest` exits **3** with an INTERNALERROR
and collects **zero** tests: `_logs/_m1_secret_firewall_test.py` calls `sys.exit()` at module
scope, pytest imports it during collection, and the `SystemExit` aborts the entire run. One
file removes every other file in the repository from collection.

Reach under the estate's de facto canonical command is **UNKNOWN, not zero**. Zero is a
measurement; this is the absence of one, and reporting zero would attribute to the repository a
defect that belongs to the invocation (SQI-02 §5.8).

**4. Executed Protection Ratio: 1.6%.** Sixty-three of sixty-four module packages have zero
references from any test the canonical invocation reaches — including `secret_firewall` and
`cascade_prevention`, which back seven CRITICAL Hard Rules.

---

## What the engine found about itself

Twice, on the first run, and both were real:

- Its module was named `test_reconciliation_engine.py`, which **matched its own `test_*.py`
  discovery pattern** and entered its own authored census as a test file. The Part III §3.4
  naming false positive, committed by the instrument against itself. Renamed to `reconcile.py`.
- It reported **SELF-REACH ZERO**: no test the canonical invocation reaches exercised the
  engine. *An auditor exempt from its own audit is not an auditor* (§5.10), and a report without
  a positive self-reach assertion is inadmissible. Remediated by rung one of the engine's own
  ladder — connect the artifact to the invocation — which is why `tests/test_sqi_engine.py`
  lives in `tests/` and not in `tools/`, where 72 of this repository's test files sit unreached.

---

## The boundary that held

No parent system was forked (`T-SQI-PARALLEL-SYSTEM-001`). CO-12's `record_signal` already
accepted an arbitrary signal kind, so telemetry **extends** it rather than standing up a rival
bus. The D1 Liveness Ledger already had a `file-mtime` probe type, so `sqi-runner` is a registry
entry, not a second liveness layer. The engine emits `FailureRecord`-shaped findings for FD-03
to route; it does not route them itself.

---

## What is still open

The engine **measures**. It does not yet **gate**: SQI-02 Part XII specifies a baseline guardian
that fails the build on a silent decrease in the executed count, and it is not built. Until it
is, the reach figure trends in a report that nothing consumes — and a quality signal that is
emitted and never read is functionally identical to one that was never computed (§8.4).

The three findings above are **surfaced, not fixed**. Widening the canonical invocation is a
governance event (§9.10: changing the invocation after seeing the number is scope laundering),
so it belongs to the Owner, not to the agent that measured it.

**UKDL sealed:** `PR-SQI-EXECUTABLE-GOVERNANCE-001`, `T-SQI-FINDING-FABRICATION-001`,
`T-SQI-DIRECTORY-NOT-MANIFEST-001`.

**Reproduce:** `python tools/run_sqi.py` · `python tools/test_sqi.py`
