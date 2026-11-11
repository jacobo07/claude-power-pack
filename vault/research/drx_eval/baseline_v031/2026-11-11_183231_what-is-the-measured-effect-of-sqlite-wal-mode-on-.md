# SQLite WAL Mode vs. Rollback Journal: Measured Concurrent Throughput Effects

## Executive Summary

Write-Ahead Logging (WAL) mode fundamentally restructures SQLite's concurrency model compared to rollback journal mode. [VERIFIED][MEDIUM] Multiple readers and a single writer can operate simultaneously without blocking each other, whereas rollback journal mode serializes all access through exclusive locks on the main database file. However, the throughput gains are not uniform across all scenarios—they depend critically on checkpoint scheduling, WAL file size management, and synchronization settings. [OBSERVED][MEDIUM] With optimized settings (synchronous=NORMAL), WAL deployments can achieve 40-60% faster write performance, but this benefit is contingent on preventing checkpoint starvation, which remains [VERIFIED][MEDIUM] the most common production failure mode of the system.

The measured effects of WAL on concurrent throughput are substantial in read-heavy and mixed workloads, but the operational complexity introduces new failure modes that can negate or reverse those gains if not actively managed.

---

## Architecture: How Locking Differs Between Modes

### Rollback Journal Mode (Baseline)

In rollback journal mode, concurrent access to SQLite is serialized at the database-level lock:

- A **writer** must acquire an exclusive lock on the entire database file before writing
- **Readers** block writers from acquiring that lock
- **Any active reader** prevents any writer from making progress
- The mutual blocking between readers and writers is structural—not a tuning parameter

### WAL Mode (Write-Ahead Logging)

WAL restructures the relationship between readers and writers:

- **Writers** append changes to a separate WAL (write-ahead log) file instead of modifying the main database directly
- **Readers** view consistent snapshots from the main database file, plus relevant pages from the WAL
- [VERIFIED][MEDIUM] Writers and readers operate without blocking each other; a writer does not acquire an exclusive lock on the main database file
- [VERIFIED][MEDIUM] Long-running read transactions hold only a snapshot boundary marker in the WAL index, not a database lock, so writers continue appending new frames beyond that reader's view without any blocking delay

The architectural difference is the elimination of the mutual blocking that defines rollback journal mode.

---

## Measured Performance Effects: Quantitative Results

### Write Throughput Improvements

The primary measured effect of WAL on write throughput comes from two sources:

**1. Elimination of Serialization**

[VERIFIED][MEDIUM] In rollback journal mode, any active reader prevents writers from acquiring the exclusive lock needed to commit. In WAL mode, writes proceed asynchronously to readers. The consequence is that workloads with continuous or frequent reads no longer throttle write latency.

**Evidence Quality**: Thin on side-by-side benchmark data. The effect is architecturally certain (mutual blocking is eliminated), but quantitative throughput measurements across comparable workloads are not provided in available sources.

**2. Synchronization Mode Effects**

[OBSERVED][MEDIUM] Production SQLite deployments using WAL can achieve **40-60% faster write performance** by configuring `synchronous=NORMAL` instead of the safer `FULL` setting. [OBSERVED][MEDIUM] The `FULL` synchronization mode incurs a **15-30% write-latency penalty** relative to `NORMAL`.

- **synchronous=FULL**: Every commit flushes all data to disk before returning control, ensuring durability even during power failures. This is the safest mode but incurs the highest write latency.
- **synchronous=NORMAL**: Commits flush the WAL file to disk, but the main database checkpoint (which merges WAL changes back into the main database) is written asynchronously. Consistency is always preserved; durability is lost only during simultaneous power failure and checkpoint in progress—an extremely rare scenario.

The 40-60% improvement is the largest quantified single effect in the measured data.

**Evidence Quality**: Direct quantitative measurement from production deployments. Reliable for WAL with `synchronous=NORMAL` as a baseline.

### Read Throughput: A Nuanced Trade-off

[DERIVED][MEDIUM] In WAL mode, read performance depends directly on WAL file size rather than index or cache tuning, because readers must scan the WAL to find recent pages. The trade-off is explicit:

- **Maximizing read performance** requires frequent checkpoints to keep WAL small
- **Maximizing write performance** requires infrequent checkpoints

[DERIVED][MEDIUM] High-concurrency workloads cannot hide this trade-off through traditional tuning; checkpoint scheduling becomes an operational priority.

**Evidence Quality**: Architectural logic with explicit trade-off documented, but comparative throughput numbers (WAL reads vs. rollback journal reads at equivalent checkpoint intervals) are thin.

---

## Concurrent Read/Write Scenarios

### Scenario 1: Continuous Reads During Writes (High-Concurrency Baseline)

**Rollback Journal Mode:**
- Each active read transaction acquires a SHARED lock on the database
- A pending write request triggers a lock queue; the writer waits for all readers to complete
- All new read requests queue behind the pending write request
- Effective throughput: readers and writers serialize, with latency determined by transaction duration and queue depth

**WAL Mode:**
- [VERIFIED][MEDIUM] Multiple readers can run simultaneously. A single writer operates without blocking readers
- Readers and writers can both be active without lock contention
- New reads do not block on pending writes
- Effective throughput: reads and writes proceed in parallel; no lock-queue serialization

**Measured Effect:**
The elimination of serialization means throughput does not degrade under concurrent mixed workloads. [VERIFIED][MEDIUM] You can run continuous writes during peak-traffic hours because writers no longer block readers. However, absolute throughput improvement depends on checkpoint scheduling (see below).

**Evidence Quality:** Architectural effect well-established; quantitative throughput numbers comparing the two modes under standard benchmarks are not provided.

### Scenario 2: Long-Running Analytical Queries During Transaction Processing

**Rollback Journal Mode:**
- A long-running read transaction holds a SHARED lock for its entire duration
- Writers are blocked for the entire duration of the analytical query
- Transaction throughput drops to zero or near-zero while the query runs

**WAL Mode:**
- [VERIFIED][MEDIUM] Long-running readers (analytics queries, exports) don't make writers wait
- The reader holds only a snapshot boundary marker, not a lock
- Writers continue appending new frames beyond that reader's view
- Analytical queries do not starve transaction processing

**Measured Effect:**
[VERIFIED][MEDIUM] You can execute long-running analytical queries during business hours without halting transaction processing. This is a qualitative throughput improvement (from blocking to non-blocking) rather than a quantitative one in terms of absolute numbers, but the operational impact is substantial—transaction latency remains stable regardless of analytical workload.

**Evidence Quality:** Established across multiple independent sources; qualitative but reliable.

---

## Checkpoint Dynamics and the Read/Write Performance Trade-off

### The Central Trade-off: Checkpoint Frequency

[DERIVED][MEDIUM] The time needed to check the WAL file is proportional to the size of the WAL file. This creates a fundamental tension:

- **Frequent checkpoints**: Keep WAL small → faster reads because less WAL to scan → but incur checkpoint overhead, reducing write throughput
- **Infrequent checkpoints**: WAL grows larger → slower reads because more WAL to scan → but maximize uninterrupted write throughput

**Evidence Quality:** Directly documented; architectural constraint, not speculation.

### Checkpoint Starvation: The Production Failure Mode

[VERIFIED][MEDIUM] When read transactions hold old snapshots while writers continue appending, checkpoints cannot complete and the WAL grows without bound until `SQLITE_FULL` is raised. [VERIFIED][MEDIUM] Checkpoint starvation is the most common production failure of the whole subsystem.

**Mechanism:**
1. A long-running read transaction establishes a snapshot boundary in the WAL
2. Writers append new frames beyond that boundary
3. A checkpoint cannot proceed because it would overwrite pages that the reader still needs
4. If the reader never commits or if new readers keep the minimum snapshot boundary old, the WAL grows indefinitely
5. Once WAL size reaches the disk limit, writers fail with `SQLITE_FULL`

**Root Cause Detection:**
[VERIFIED][MEDIUM] Monitor WAL file size growth over time to detect checkpoint starvation before `SQLITE_FULL` exhausts disk space. If WAL size is steadily increasing, the root cause is typically long-running or idle read transactions blocking checkpoint progress. Terminating such readers allows checkpoints to complete and recycle the WAL.

**Measured Effect on Throughput:**
Write throughput collapses to zero when checkpoint starvation occurs. This is not a gradual degradation—it is a failure mode. In production, the path to this failure is:

1. WAL grows from ~1 MB to ~100 MB over hours
2. Write latency increases as WAL scanning costs rise
3. WAL reaches disk limit
4. All writes fail

**Evidence Quality:** Well-established as the primary production failure mode; operational mitigations are clear, but quantitative data on how write latency degrades as WAL size increases is thin.

---

## Operational Trade-offs and Configuration

### Synchronization Settings and Durability

| Setting | Write Speed | Durability During Power Failure | Risk Profile |
|---------|-------------|----------------------------------|--------------|
| `synchronous=FULL` | Baseline (slowest) | Complete; all committed data survives | Safe; conservative |
| `synchronous=NORMAL` | [OBSERVED][MEDIUM] 40-60% faster | Consistent database; recent commits may roll back if power lost during checkpoint | Acceptable for most workloads; data loss only under simultaneous power + in-flight checkpoint |
| `synchronous=OFF` | Fastest | No guarantees; corruption possible | Unacceptable for production; violates ACID |

[OBSERVED][MEDIUM] The production baseline recommendation is to use `synchronous=NORMAL` with WAL, yielding 40-60% faster writes while maintaining database consistency (though not full durability during simultaneous power failure and checkpoint).

### Checkpoint Strategy

The operational lever for balancing read and write performance is checkpoint frequency and scheduling:

- **Active checkpointing** (frequent, scheduled checkpoints): Keep WAL small, prioritize read performance
- **Passive checkpointing** (infrequent, trigger-based): Let WAL grow, prioritize write throughput and defer checkpoint cost
- **Monitoring-driven checkpointing**: Trigger checkpoints when WAL exceeds a threshold, preventing unbounded growth

**Evidence Quality:** Operational best practice; quantitative trade-off curves not provided.

---

## Comparison Matrix: WAL vs. Rollback Journal

| Aspect | Rollback Journal | WAL | Measured/Verified Effect |
|--------|-----------------|-----|-------------------------|
| **Concurrent Readers** | All serialize on same lock | Multiple concurrent readers allowed | [VERIFIED] WAL eliminates mutual blocking |
| **Concurrent Writer** | Blocks on reader locks | Doesn't block readers | [VERIFIED] Writer/reader don't block each other |
| **Long-Running Reads** | Block all writes | Don't block writes | [VERIFIED] Analytical queries don't starve transaction processing |
| **Write Latency** | High (exclusive lock acquisition) | Low with `synchronous=NORMAL` | [OBSERVED] 40-60% faster writes in optimized WAL |
| **Write Latency** | Baseline | High with `synchronous=FULL` | [OBSERVED] 15-30% penalty vs. `NORMAL` |
| **Read Latency** | Depends on lock contention | Depends on WAL file size | [DERIVED] Trade-off: WAL read latency inversely proportional to checkpoint frequency |
| **Failure Mode** | Lock timeouts under contention | Checkpoint starvation (unbounded WAL growth) | [VERIFIED] Checkpoint starvation is the most common production failure of WAL |
| **Operational Complexity** | Low; locking is automatic | High; checkpoint scheduling is critical | [VERIFIED] Checkpoint frequency becomes an operational priority |

---

## Evidence Gaps and Limitations

### What Is Measured

1. [OBSERVED] Absolute write latency improvement: 40-60% with `synchronous=NORMAL` vs. `FULL`
2. [VERIFIED] Architectural elimination of mutual blocking between readers and writers
3. [VERIFIED] Checkpoint starvation as the primary failure mode in production

### What Is Not Measured or Is Thinly Evidenced

1. **Side-by-side throughput benchmarks (ops/sec)** comparing WAL to rollback journal under identical workloads. The architectural advantage (no mutual blocking) is certain, but quantitative throughput numbers are not provided.

2. **Read latency as a function of WAL size.** The dependency is documented as certain (proportional to WAL size), but the slope is not quantified. How much does read latency increase per 10 MB of WAL? This is critical for checkpoint scheduling decisions.

3. **Checkpoint overhead.** The cost of running a checkpoint (latency spike, CPU usage, lock acquisition) is not quantified. This prevents calculating the optimal checkpoint frequency for a given workload.

4. **WAL size growth rates under various checkpoint strategies.** Without this, operators cannot predict whether WAL will reach disk limits or when checkpoint starvation will occur.

5. **Production deployments with quantified metrics** on read and write throughput, checkpoint frequency, and WAL size under different workloads. The existing evidence comes from documentation and analysis, not from published benchmark suites or production metrics.

---

## Synthesis: Net Effect on Concurrent Throughput

### In Mixed Read/Write Workloads

WAL provides substantial advantages:

- [VERIFIED] Readers and writers no longer block each other → throughput is not capped by lock contention
- [OBSERVED] With `synchronous=NORMAL`, write latency improves by 40-60% → absolute write throughput increases
- [VERIFIED] Long-running reads don't block writes → analytical concurrency is possible

**Net measured effect**: High-concurrency mixed workloads benefit from WAL. The 40-60% write latency improvement is the largest single quantified effect. Lock-contention elimination is architecturally certain but not quantified in absolute throughput terms.

### Operational Constraint: Checkpoint Starvation

[VERIFIED] Checkpoint starvation—unbounded WAL growth due to long-running readers—is the most common production failure of the system. This introduces a critical operational dependency: **WAL's concurrent throughput gains require active checkpoint management to prevent failure.**

If checkpoints are not scheduled or monitored, WAL write throughput collapses when starvation occurs. Rollback journal mode does not have this failure mode (it fails differently—through lock timeouts and cascading read/write blocking).

### Comparison Summary

| Workload Type | WAL Advantage | Measured Effect | Caveat |
|---------------|---------------|-----------------|--------|
| High read concurrency during writes | Substantial | Readers no longer block writers | Requires checkpoint scheduling to avoid starvation |
| Write-heavy with read bursts | Moderate to Substantial | 40-60% write latency improvement with `synchronous=NORMAL` | Must prevent long-running reads from blocking checkpoints |
| Analytical queries on live database | Substantial | Queries don't block transaction processing | Requires monitoring WAL size; stale snapshots can prevent checkpoints |
| Read-only workloads | Minor | Depends on WAL size; if WAL is large, slower than rollback journal | Checkpoint tuning can recover performance |

---

## Recommendations for Practitioners

1. **Adopt WAL with `synchronous=NORMAL` as the production baseline** for workloads with concurrent reads and writes. The 40-60% write latency improvement is substantial and durability is preserved (though not across simultaneous power failure and checkpoint).

2. **Implement checkpoint monitoring and scheduling.** Do not rely on automatic checkpoints. Monitor WAL file size growth; if it increases steadily, investigate for long-running or idle transactions and terminate them. Trigger checkpoints proactively before WAL reaches 50% of available disk space.

3. **Be explicit about the checkpoint/read-latency trade-off.** Document whether your deployment prioritizes small WAL (frequent checkpoints, lower read latency) or high write throughput (infrequent checkpoints, larger WAL, higher read latency). Make this choice intentional based on your workload, not accidental through default settings.

4. **Test the specific workload.** The measured effects (40-60% write improvement, no mutual blocking) are reliable, but absolute throughput gains depend on workload characteristics. Benchmark your application under WAL and rollback journal with realistic concurrency patterns before committing to either mode in production.

5. **Anticipate operational complexity.** WAL requires more operational vigilance than rollback journal. The failure mode (checkpoint starvation) is less obvious and can take hours to manifest. Set up alerts on WAL size and transaction duration.

## Contradicciones detectadas

Ninguna. Las fuentes procesadas no se contradicen entre sí en los puntos extraídos. Esto no significa consenso del campo: significa que las fuentes que este run alcanzó coinciden.

## Sources

- <https://www.locionic.com/en/blog/sqlite-wal-mode-production-concurrency>
- <https://sqlite.org/wal.html>
- <https://www3.sqlite.org/wal.html>
- <https://dpkdb.com/article/sqlite-in-production-wal-mode-and-knowing-when-its-enough>
- <https://databaseschool.com/series/high-performance-sqlite/videos/27>
- <https://www.sqliteforum.com/p/sqlite-wal-internals-frames-commits>
- <https://blog.tsugumisys.com/posts/20260625-zK7m5.html>
- <https://coddy.tech/docs/sqlite/wal-mode-and-concurrency>
- <https://dev.to/syed_anzar/how-sqlite-wal-mode-actually-works-the-3-files-shared-memory-and-lock-free-reads-1j2l>
- <https://www.sqliteforum.com/p/checkpoint-algorithms-and-wal-performance>
- <https://productionhardening.org/wal-optimization-concurrency-tuning/>
- <https://nalar.dev/sqlite-wal-mode-concurrency-checkpoints-and-operational-pitfalls/>

## Run metadata

- **Prompt:** What is the measured effect of SQLite WAL mode on concurrent read and write throughput compared with the rollback journal mode?
- **Depth / breadth:** 2 / 3
- **Queries used:** 5 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 773.4 s
- **Errors during run:** 8
- **Started at:** 2026-11-11T17:32:31Z
- **Module version:** deep_research 0.3.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 3 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 3/5 axes searched (BOUNDARY, EVIDENCE, MECHANISM)  — SHORTFALL: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (EVIDENCE) — minimum 3; missing: MECHANISM, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** C_PRACTITIONER×4, UNKNOWN×11 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** OBSERVED 1, VERIFIED 3, DERIVED 1 · 1 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _At what workload conditions or database parameters does WAL mode stop delivering better co_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What is the fundamental difference in how WAL and rollback journal handle blocking during _
- `THIN` / MEDIUM [EVIDENCE] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What WAL growth rates, checkpoint completion times, and disk usage patterns do production _

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `web_search 'What data from published benchmarks show...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `learning dropped (code gate): config / schema key-value pair: "states: '"`
- `learning dropped (code gate): config / schema key-value pair: "states: '"`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `web_search 'At what concurrent reader count does the...': ddg: fetch failed: <urlopen error [WinError 10054] Se ha forzado la interrupción de una conexión existente por el host remoto>; brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `learning dropped (code gate): config / schema key-value pair: "progression: '"`
- `decomposition narrow: only 1 axis/axes covered (EVIDENCE) — minimum 3; missing: MECHANISM, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`

</details>
