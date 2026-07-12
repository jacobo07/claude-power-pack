# SQI Part XV — Weakening Detectors · implementation contract

> Backup of the inline plan, corrected against the dataset it implements.
> Predecessor: SCS C93 (the baseline guardian). Read `sqi_02_test_reach_v1.txt` §15.1–15.10.

---

## 1. What Part XV actually specifies

Ten weakenings (15.2–15.9). The guardian of Part XII catches **only the loud one**.

| # | weakening | §  | detector Part XV specifies | verdict class |
|---|---|---|---|---|
| 1 | removed assertion | 15.2 | assertion count per file, compared per commit | **FAIL** (arithmetic) |
| 2 | widened exception handler | 15.3 | diff-level pattern match on broad-catch constructs | **REVIEW** — "its output is a candidate list for review rather than a verdict, because a broad handler is sometimes correct" |
| 3 | unreal fixture | 15.4 | **none** — "there is no counting detector for this and it would be dishonest to claim one" | **REVIEW** (fixture diff as a first-class artifact) |
| 4/5 | skip · marker exclusion | 15.5 | already measured — the executed count moves; Part XII/VI catch these | already gated |
| 6 | over-mocking | 15.6 | mocked collaborators per file, **trended**; "a test whose mock count ROSE while its assertion count did NOT" | **FAIL** (delta) |
| 7 | lowered threshold | 15.7 | every threshold inventoried, versioned; each change a governance event | out of scope this sprint — declared, not built |
| 8 | tautological assertion | 15.8 | **only a mutation probe distinguishes it** | **FAIL** (surviving mutant) |
| 9/10 | relocation · same-name rewrite | 15.9 | identities (Part XII, shipped) + **content hash of the test file** | identities: gated. hash: **REVIEW** |

**15.10, the governance link:** the party blocked by a test may not, within the same task, weaken it.
Identical in shape to the Part XII firewall — so it reuses that firewall, it does not grow a second one.

---

## 2. Two places the inline plan would have disarmed the detector

Both are the same failure family as the reach-ratio finding of SCS C93. Both are corrected here.

### 2.1 The mock/assertion **ratio** gate rewards the tautological assertion

The plan specifies: *"Ratio alarm: `mock_count / assertion_count > umbral definido en Part XV`."*

Two independent defects.

**(a) Part XV defines no such threshold.** It defines a *delta* rule (15.6: the mock count rose while
the assertion count did not) and it cites the estate's existing static standard — four or more mocked
collaborators means the unit under test is doing too much (`rules/python/testing.md`). Inventing a
numeric threshold and attributing it to the Part would be `T-SQI-FINDING-FABRICATION-001` exactly.

**(b) A ratio gate is satisfied by inflating its denominator, and the cheapest inflation is weakening
#8.** `mocks / assertions` falls when assertions rise. Adding `assert result is not None` to a test —
an assertion that passes for every implementation including a broken one — *lowers the ratio and
quiets the alarm*. **The gate would be defeated by the precise attack the Part exists to catch**, and
it would report an improvement while the suite got weaker. This is `T-SQI-RATIO-GATE-REWARDS-DELETION-001`
in a second costume.

**Corrected:** gate the **delta on absolutes** — `mocks rose AND assertions did not rise` → WEAKENED.
Report the ratio; never gate on it. Surface `mocks >= 4` as a standing static advisory.

### 2.2 Three baseline stores would fork the mechanism the guardian already owns

The plan specifies `assertion_baseline.py`, `mock_baseline.py`, `content_hash_baseline.py` — three
modules, three JSON files, three env-keyings, three ratchets, three firewalls. That is a triple fork
of `baseline_guardian.py`, which `T-SQI-PARALLEL-SYSTEM-001` forbids.

And decisively: **the sharpest signal in Part XV is cross-metric.** 15.6 is *"a test whose mock count
rose while its assertion count did not"* — one predicate over **two** numbers. Three stores cannot
express it without one reaching into another's file.

**Corrected:** one detector module (stateless counters) + **one** baseline store holding a per-file
record `{assertions, mocks, sha256}`, keyed by environment, reusing the Part XII firewall verbatim.

---

## 3. What ships

| unit | artifact | contract |
|---|---|---|
| W1 | `modules/sqi/weakening_detectors.py` | `count_assertions` · `count_mocks` · `hash_test_content` · `scan()`. AST-based, never regex-on-source: a `#` comment and a docstring must not count as assertions. Unparseable file → `UNKNOWN`, never zero. |
| W2 | `modules/sqi/weakening_baseline.py` | one store, per-file records, env-keyed. Gates A (assertions fell) · B (mocks rose ∧ assertions did not) · C (hash changed ∧ arithmetic unchanged → REVIEW, not FAIL). |
| W3 | content hash | `sha256` of the file bytes, per authored test file. Defeats the same-name rewrite (15.9), which is invisible to every instrument that stores numbers. |
| W4 | mutation probe | **opt-in** (`--mutation-probe`). Executes tests, so it is not in the default pipeline. Refuses to run against a dirty working tree. Restores from bytes in a `finally` and verifies the restore by hash. |
| W5 | `tools/run_sqi.py` layer 5 | exits non-zero on `WEAKENED`. `UNKNOWN` and `REVIEW` never fail the build. |
| W6 | gates | 7 new V-gates, ×3 hermetic, on top of 45. |

## 4. What this build will NOT do

- **It will not gate the lowered threshold (15.7).** That needs a threshold inventory, which does not
  exist. Declared as a gap, not faked.
- **It will not claim to detect the unreal fixture (15.4).** The Part says a counting detector for it
  would be dishonest. There is none here.
- **It will not touch** the `_logs/` crash, the absent root pytest config, the canonical invocation, or
  the 63 unprotected packages. Owner decisions, standing (SQI-02 §9.10).
- **It will not run the mutation probe by default.** A probe that mutates the working tree as a side
  effect of a measurement is a measurement that changes what it measures.
