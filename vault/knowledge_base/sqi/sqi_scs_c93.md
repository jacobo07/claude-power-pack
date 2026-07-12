# SCS C93 — SQI Baseline Guardian: measuring becomes gating

> Sealed 2026-07-12. Predecessor: SCS C91 (SQI-Executable — the three engines).
> The Verification axis moves from `invoked` to `enforced` on SQI-02 Part XVII's own ladder.

---

## Why this had to exist

SCS C91 shipped three engines that reconciled this repository and reported Test File Reach at
3.0%, 98 orphaned files, an Executed Protection Ratio of 1.6%, and an authoritative invocation
that collects nothing at all. Every number was correct, every number was durable — and **nothing
consumed any of them.** The report was furniture.

SQI-02 §8.4 is unambiguous about what that means: *quality signals do not decay by concealment,
they decay by non-consumption, and a number that is emitted and never read is functionally
identical to a number that was never computed.* The axis stood at `invoked`, which has a small
non-zero protective value, and not at `enforced`, which is where the value actually lives. The
distance between them is one suppressed exit code.

---

## What shipped

| artifact | what it does |
|---|---|
| `modules/sqi/baseline_guardian.py` | per-root, environment-keyed, identity-carrying baselines; three absolute gates; the §12.7 firewall |
| `tools/run_sqi.py` | layer 4 of the pipeline. **Exits non-zero on an unexplained decrease.** `--accept-baseline --reason … --author …` |
| `vault/audits/sqi_baseline.json` | the recorded derivative. Initial: **67** executed → ratcheted to **76** by this build's own tests |
| `tests/test_sqi_engine.py` | +9 guardian tests, **inside** the canonical invocation |
| `tools/test_sqi.py` | +9 V-gates. **`SQI_PASS=45/45` ×3 hermetic, exit 0** |

**The contract is one asymmetry (§12.2): an increase requires nothing, and a decrease fails the
build.** The guardian has no opinion about whether the tests are good or whether the count is
high enough. It cares only that **protection is not withdrawn in silence.**

---

## The two places the plan would have disarmed it

Both are named as defects in the dataset the guardian implements. Shipping either would have
shipped a guardian that the first attack defeats.

### 1. A repository total permits redistribution (§12.3)

The plan proposed a single repo-wide `executed_count`. But a total is a sum, and a sum permits
redistribution: two hundred tests leave root A, one hundred and eighty arrive in root B, and a
tolerance swallows the difference. Worse, **an entire root can die completely while a growing
sibling absorbs it and the total rises.**

Corrected: baselines are **per-root**, keyed by the **environment hash** (§12.4 — the same
repository yields 1,606 assertions under one toolchain and zero under a runtime one major version
behind, and a comparison across those keys is not a comparison but two measurements of two
different systems), and they carry **node identities** rather than counts (§12.5 — a delta of
three is an alarm and three names are an action; identities are also the only thing that catches
a relocation or a same-name rewrite, both invisible to any instrument that stores numbers).

### 2. Gating on the ratio rewards deleting the orphans

The sharper one. The plan specified `check falla si reach_pct < baseline.reach_pct`.

`reach = reached / authored`. This repository: 3 reached, 101 authored, **3.0%**. **Delete the 98
orphaned test files and reach becomes 100% while the executed count never moves.** Every ratio
improves. The repository is worse by 98 test files. No ratio-based rule has been violated. The
guardian reports a triumph.

That is SQI-02 Part XVIII's **first attack on its own instrument**, and the plan proposed exactly
the gate it defeats. Corrected: the guardian gates **three absolutes** —

| gate | catches | source |
|---|---|---|
| **executed**, per root | protection withdrawn: a skip, a scope line, an import error, a relocation | §12.2 |
| **authored** | **the deletion attack** — a ratio can be improved by shrinking its denominator; an absolute cannot | §8.2, §18.2 |
| **reach** | drift: code growing faster than the invocation reaches it | Part XIV |

Reach *is* still gated, because the plan was right that drift matters — but it is now
*subordinate* to the two absolutes, which is what makes it safe.

`V-GUARDIAN-BLOCKS-DELETION-ATTACK` forges reach to 100% by deleting every orphan and asserts the
guardian **refuses**, naming all 98 lost files.

---

## The firewall (§12.7) — what makes it governance rather than decoration

An **increase** ratchets the baseline automatically. A **decrease NEVER auto-updates.** Lowering
a baseline requires a separate, attributed act that records what was surrendered:

```
python tools/run_sqi.py --accept-baseline --reason "<why>" --author "<who>"
```

Not because the party is suspected. Because when a gate is the only object standing between an
agent and completion, editing the gate is one write and every honest path is work — and the
gradient is followed by sincere parties as reliably as by hostile ones. *A baseline lowered
calmly, in its own commit, with a stated reason, is governance. The same baseline lowered inside
the commit that made it necessary is an escape, and the two are indistinguishable in the artifact
unless the firewall separates them in time.*

**The guardian does not prevent deletion. It prevents deletion from being invisible.**

---

## Verdicts

| verdict | exit | meaning |
|---|---|---|
| `BASELINE_PASS` | 0 | nothing fell. Improvements ratchet. |
| `BASELINE_REGRESSION` | **1** | an absolute fell. Identities of what vanished are named. |
| `BASELINE_CREATED` | 0 | first run. |
| `BASELINE_ENVIRONMENT_MISMATCH` | 0 | not a comparison. The guardian refuses to raise an alarm it cannot substantiate (§12.4). |
| `BASELINE_UNKNOWN` | 0 | the baseline is unreadable. **Never a false PASS** — a disarmed guard reporting success is the exact artifact this corpus discredits. |

---

## Owner decisions, untouched

Per SQI-02 §9.10 — changing the invocation after seeing the number is scope laundering — none of
these was repaired, and all four remain in the report:

- the `_logs/` `SystemExit`-at-import crash that breaks the zero-argument default
- the absent root pytest configuration
- the canonical invocation itself
- the 63 of 64 module packages with no reached-test references

It would have been trivial to declare `pytest tests/` the canon and report a comfortable figure.
It was not done.

---

## Still open

The guardian gates the **executed count**, which catches deletion, skips, and relocation. It does
**not** catch **weakening** (Part XV): a removed assertion, a widened exception handler, an
unreal fixture, over-mocking, a lowered threshold, a tautological assertion. In every one of
those the file is present, the case is collected, the case passes, **the count is identical, and
the protection is gone.** Weakening is the perfect attack on a count-based instrument, and this
instrument is count-based. Part XV specifies the detectors — assertion counts, mock counts,
content hashes, a mutation probe — and none is built.

**UKDL sealed:** `PR-SQI-SIGNAL-MUST-GATE-001`, `T-SQI-RATIO-GATE-REWARDS-DELETION-001`,
`T-SQI-SCOPE-LAUNDERING-001`.

**Reproduce:** `python tools/run_sqi.py` · `python tools/test_sqi.py`
