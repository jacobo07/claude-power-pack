# SQI-02 Part XII — Baseline Guardian: implementation contract

> EXECUTION MODE. Moves SQI from `invoked` to `enforced` on Part XVII's own five-state ladder.
> Read before implementing: `sqi_02_test_reach_v1.txt` Parts XII (the guardian), XIV (drift),
> XV (deletion & weakening), XVIII (attacks on the instrument). Date: 2026-07-12.

---

## 1. What the guardian is

The reconciliation engine measures a **state**. The guardian measures the **derivative** — and
the derivative is where the estate's most dangerous events live, because the states are
frequently acceptable and the transitions between them are frequently not (§12.1).

Its contract is a single asymmetry (§12.2): **an increase requires nothing, and a decrease fails
the build.** It has no opinion about whether the tests are good, whether the count is high
enough, or whether coverage is adequate. It cares only that **protection is not withdrawn in
silence.**

Initial baseline, measured from the disk today (`vault/audits/sqi_report_2026-07-12.json`):

| value | observed |
|---|---|
| executed cases (`pytest tests/`) | **67** |
| executed files | 3 |
| authored files | 100 |
| Test File Reach | 3.0% |
| environment key | `b5ec3ed51c2f23b1` |

---

## 2. Two places the plan would have disarmed it

The inline plan proposed a repository-total baseline of `{executed_count, reach_pct}`. Both
choices are named as defects in the dataset the guardian implements. Correcting them is not
scope creep; shipping them would be shipping a guardian that the first attack defeats.

### 2.1 A repository total permits redistribution (§12.3)

> *"A repository total is a sum, a sum permits redistribution... two hundred tests leave root A
> and one hundred and eighty arrive in root B, the total falls by twenty, and a tolerance of one
> percent swallows it. Worse, a root can die completely while a growing sibling absorbs the
> difference and the total rises."*

**Correction:** the baseline is recorded **per suite root**, keyed by the **environment**, and
carries the **set of node identities** — because a delta of three is an alarm and three names are
an action (§12.5). Totals are derived at the reporting boundary, never stored as the gate.

### 2.2 Gating on a ratio rewards deleting the orphans (§18.2, §8.2)

This is the sharper one. `reach_pct = reached / authored`. **Deleting the 97 orphaned test files
raises reach from 3.0% to 100% and leaves the executed count untouched.** A guardian that gates
on the ratio would report a triumph while the repository lost 97 test files. That is Part XVIII's
*first* attack, verbatim:

> *"The first attack is deletion. The orphan count is seventy; delete the seventy files; the
> orphan count is zero and the reach is one hundred percent. Every metric improves, the
> repository is measurably worse, and no rule anywhere in the ratio-based instrument was
> violated."*

Its stated countermeasure is threefold, and **none of the three is optional**: the **absolute**
executed count must not fall; the ledger is append-only; and every deletion is a weakening event
requiring an attributed baseline update (§18.2, §15.9).

**Correction:** the guardian gates on **three absolutes**, not on a ratio:

| gate | what falls | what it catches | dataset |
|---|---|---|---|
| **A — executed** | executed cases, per root | protection withdrawn: a skip, a scope line, an import error, a relocation | §12.2 |
| **B — authored** | authored test files | the **deletion attack**: improving the ratio by destroying the numerator's denominator | §18.2, §15.9 |
| **C — reach** | Test File Reach | **drift**: code/tests growing faster than the invocation reaches them | §XIV |

Gate C still exists — the plan asked for it and it is right — but it is now *subordinate* to A
and B, which is what makes it safe. With B in place, reach can no longer be raised by deletion.

---

## 3. Verdicts

| verdict | meaning | exit |
|---|---|---|
| `PASS` | nothing fell. Improvements ratchet the baseline up automatically. | 0 |
| `REGRESSED` | an absolute fell without an attributed update. **Identities of what vanished are named.** | **≠0** |
| `CREATED` | no baseline existed; written from the current report. First run. | 0 |
| `ENVIRONMENT_MISMATCH` | the baseline's environment key ≠ this host's. **Not a comparison** — two measurements of two different systems (§12.4). The guardian says so rather than raising an alarm it cannot substantiate. | 0 |
| `UNKNOWN` | the baseline file is unreadable or malformed. Fail-open: **never a false PASS.** | 0 |

A baseline recorded under one toolchain and compared under another reports a catastrophic
decrease that is entirely an artifact of the harness, and an engineer dispatched by that alarm
would go looking for deleted tests that nobody deleted (§12.4). Hence the environment key.

---

## 4. The firewall (§12.7) — the part that makes it governance rather than decoration

> *"The party whose change caused the decrease may not, in the same task, author the baseline
> update that permits it... A baseline lowered calmly, in its own commit, with a stated reason,
> is governance. The same baseline lowered inside the commit that made it necessary is an
> escape, and the two are indistinguishable in the artifact unless the firewall separates them
> in time."*

**Mechanism:** an **increase** ratchets the baseline automatically (it is free, and gating it
would be perverse). A **decrease NEVER auto-updates.** Lowering a baseline requires an explicit,
separate, attributed act:

```
python tools/run_sqi.py --accept-baseline --reason "<why>" --author "<who>"
```

which records the reason, the author, the timestamp, and **the identity set that was removed**.
The guardian does not prevent deletion. It prevents deletion from being **invisible**.

---

## 5. Out of scope — Owner decisions, explicitly not touched

Per the Owner's standing instruction and SQI-02 §9.10 (changing the invocation after seeing the
number is scope laundering):

- the `_logs/` `SystemExit`-at-import crash that breaks the zero-argument default
- the absent root pytest configuration
- the canonical invocation itself
- the 63 of 64 module packages with no reached-test references

The guardian **measures across** these. It does not repair them.

---

## 6. Done-gate

- `V-GUARDIAN-DETECTS-REGRESSION` · `V-GUARDIAN-PASSES-STABLE` · `V-GUARDIAN-UPDATES-BASELINE`
- `V-GUARDIAN-FAILOPEN-CORRUPT` · `V-GUARDIAN-FIRST-RUN` · `V-GUARDIAN-IN-PIPELINE`
- `V-GUARDIAN-BLOCKS-DELETION-ATTACK` — deleting orphans must **not** buy a green
- `V-GUARDIAN-ENV-MISMATCH` · `V-GUARDIAN-SELF-REACH`
- `tools/test_sqi.py` ×3 hermetic (36 prior + new), exit 0. Baseline writes redirected to a
  temp path via `SQI_BASELINE_PATH` so the gate touches no global state.
- `REMOTE_DELTA = 0 0`.
