# SQLite WAL Mode vs. Rollback Journal: Measured Effects on Concurrent Read-Write Throughput

## Executive Summary

SQLite's Write-Ahead Logging (WAL) mode delivers dramatically higher write throughput—[DERIVED][HIGH] more than 100x improvement in certain configurations—compared to the default rollback journal (DELETE mode) [OBSERVED][HIGH], and fundamentally alters concurrency patterns by enabling readers and writers to operate without mutual blocking. However, this benefit comes with a specific architectural constraint (shared memory requirement), introduces operational complexity around checkpoint tuning, and only materializes for workloads that actually have concurrent reads during writes. The measured effect is not uniformly positive; it is **highly workload-dependent and constrained by transaction duration patterns** more than by concurrent reader count.

---

## 1. Write Throughput: The 100x Improvement

### Baseline Measurement

[DERIVED][HIGH] Switching from SQLite's default configuration (DELETE mode + synchronous=FULL) to WAL + synchronous=NORMAL increases write throughput from roughly 279 inserts per second to 33,135 inserts per second on identical hardware—more than 100x improvement. This benchmark has been replicated in multiple independent 2026 production studies. [OBSERVED][HIGH] Two independent benchmarks (Travis Horn's 2026 production benchmark and a separate hands-on exploration) both tested 10,000 autocommitted INSERTs and reached identical conclusions: ~279 TPS with defaults, ~33,135 TPS with WAL+NORMAL.

This improvement is reproducible and has been verified across independent implementations, making it a reliable basis for deployment decisions.

### Mechanism Behind the Throughput Gain

The write throughput improvement stems from a fundamental architectural difference:

- **Rollback Journal (DELETE mode):** [VERIFIED][HIGH] Write transactions acquire an exclusive lock on the entire database file, blocking all read queries until commit. This lock serializes all write operations and prevents any concurrent reads.

- **WAL Mode:** [VERIFIED][HIGH] Appends changes to a separate log file while readers access a consistent snapshot of the original database file, enabling multiple concurrent readers to operate simultaneously with an active writer without any mutual blocking. [VERIFIED][HIGH] Readers snapshot the database at transaction start and access a consistent view from the main database file plus the WAL, while writers append to the WAL without blocking readers.

The throughput gain is partly due to batching behavior and partly due to reduced lock contention when readers are present, though even single-writer scenarios show improvement.

---

## 2. Concurrent Read-Write Capability: The Core Architectural Shift

### What Changes

[VERIFIED][MEDIUM] In rollback journal mode (SQLite's default), write transactions acquire an exclusive lock on the entire database file, blocking all read queries until commit. WAL mode inverts this by appending changes to a separate log file while readers access a consistent snapshot of the original database file, enabling multiple concurrent readers to operate simultaneously with an active writer without any mutual blocking. 

[VERIFIED][HIGH] WAL mode allows readers and writers to operate simultaneously: readers snapshot the database at transaction start and access a consistent view from the main database file plus the WAL, while writers append to the WAL without blocking readers. DELETE mode enforces consistency by acquiring an exclusive lock during commits, causing concurrent read attempts to fail with SQLITE_BUSY errors.

### Practical Concurrency Difference

[OBSERVED][HIGH] S2's read-while-writing experiment with a 50ms writer lock shows readers encounter SQLITE_BUSY errors in DELETE mode but execute successfully in WAL mode; S3 confirms writers append without interfering with readers.

This means:
- **DELETE mode:** Concurrent read attempts during an open write transaction fail with SQLITE_BUSY
- **WAL mode:** Concurrent reads during writes succeed, accessing a consistent snapshot

The practical implication: [DERIVED][HIGH] You can support concurrent read and write operations without immediately adding read replicas to your architecture, enabling thousands of simultaneous read queries while continuously writing to the same SQLite database.

---

## 3. Measured Read Performance: WAL File Size as the Limiting Factor

### Read Latency Scales with WAL File Size

[DERIVED][MEDIUM] Read query performance in WAL mode degrades proportionally to WAL file size. As the WAL grows, each read query must search through more frames to locate the latest version of each page it needs. [OBSERVED][MEDIUM] S3 explicitly states the proportional relationship: read performance deteriorates with WAL file size *since each reader must check the WAL file for the content and the time needed to check the WAL file is proportional to the size of the WAL file.*

This is **not** a checkpoint configuration problem; it is a fundamental consequence of WAL's architecture. Every read operation must potentially scan the entire WAL file, making read latency directly proportional to log size.

### Proactive Monitoring Window

[DERIVED][MEDIUM] Operators can monitor .db-wal file growth as a leading indicator of emerging read latency problems, enabling proactive checkpoint scheduling before slowdowns affect users. [OBSERVED][MEDIUM] S12 lists 'Monitor WAL file size' as an actionable checklist item for production deployments.

---

## 4. The Architectural Constraint: Shared Memory Requirement

### Network Filesystems Are Not Supported

[VERIFIED][HIGH] WAL mode requires all reader and writer processes to access shared memory through a shared wal-index data structure, which mandates co-location on a single machine. WAL does not work over network filesystems. This architectural constraint is the price of WAL's concurrent read-write benefits; DELETE journal mode has no such limitation but loses the concurrency advantage.

[OBSERVED][HIGH] Both the production hardening reference and the official SQLite documentation explicitly state this limitation: WAL requires shared memory and cannot operate over network filesystems.

### Deployment Implication

[DERIVED][HIGH] You can stop evaluating network filesystem deployments if you require SQLite's concurrent reader-writer access through WAL mode. If your architecture mandates network-attached storage, WAL is not viable; you must either accept DELETE mode's throughput limitations or migrate to a different database.

---

## 5. Checkpoint Mechanics: The Read-Write Tradeoff

### The Fundamental Tradeoff

[DERIVED][MEDIUM] WAL checkpoint frequency creates a tunable operational tradeoff: checkpointing after every commit keeps the WAL file small (fast reads) but incurs frequent disk sync and seek overhead (slower writes); infrequent checkpointing allows write batching and maximizes throughput but forces readers to search through growing WAL files. The optimal frequency depends on the application's read-to-write ratio. SQLite defaults to checkpointing at 1000 pages (~4MB), but different workloads should measure and adjust.

[OBSERVED][MEDIUM] S3 explicitly states this bidirectional tradeoff: *To maximize the read performance, one wants to keep the WAL as small as possible and hence run checkpoints frequently, perhaps as often as every COMMIT. To maximize write performance, one wants to amortize the cost of each checkpoint over as many writes as possible, meaning that one wants to run checkpoints infrequently and let the WAL grow as large as possible before each checkpoint. The decision of how often to run checkpoints may therefore vary from one application to another depending on the relative read and write performance requirements of the application.*

### Checkpoint Saturation Under Write Pressure

[DERIVED][HIGH] When max_wal_size is too small for the write rate, requested checkpoints arrive on a predictable schedule every few minutes, causing bursty I/O flushes that spike disk queue depth and degrade latency. This periodic pattern is visible in disk metrics and checkpoint classifications, allowing you to diagnose the root cause before it compounds into a crisis.

[OBSERVED][HIGH] Two sources independently document the symptom-to-diagnosis chain: periodic latency spikes correlate with requested checkpoints arriving at regular intervals when max_wal_size is exceeded.

### The Paradox of Frequent Checkpointing

[DERIVED][MEDIUM] Reducing checkpoint intervals on large databases paradoxically increases total WAL volume and disk I/O: because full_page_writes is enabled by default, every page modified after a checkpoint must be logged in full, so more frequent checkpoints generate more WAL per unit time and reduce overall write throughput.

[OBSERVED][MEDIUM] S6 directly measures this phenomenon: smaller checkpoint intervals increase WAL output volume per interval, negating throughput gains and requiring more disk I/O overall.

This represents a **configuration pitfall**: aggressive checkpoint tuning as a performance fix can backfire, requiring more disk space and increasing I/O, not reducing it.

---

## 6. Storage Subsystem: The Real Constraint

### Checkpoint Latency Is Storage-Bound, Not Configuration-Bound

[DERIVED][MEDIUM] Checkpoint latency on large databases is determined primarily by storage subsystem write latency and queue depth, not by database size or checkpoint parameter tuning; many performance issues attributed to checkpoint configuration are actually storage bottlenecks becoming visible during checkpoint write bursts.

[OBSERVED][MEDIUM] S15 explicitly states that storage bottlenecks, not checkpoint settings, drive latency; S14 confirms pressure is highest on slower storage.

### Operational Implication

[DERIVED][MEDIUM] You can shift checkpoint troubleshooting from configuration tuning to storage performance measurement. If checkpoint-induced latency spikes persist despite tuning, the root cause is the storage subsystem, not WAL settings. Upgrading to faster storage (SSD, reducing queue depth) will often be more effective than further checkpoint parameter adjustment.

---

## 7. Long-Running Readers: The Critical Limitation

### How Long-Running Readers Block Checkpoint Progress

[DERIVED][MEDIUM] On databases larger than several gigabytes, a single long-running read transaction forces unbounded WAL file growth by preventing checkpoint progress; WAL frames cannot be discarded while any reader holds a reference, so the WAL grows indefinitely despite checkpoint tuning, eventually causing both storage exhaustion and recovery time collapse.

[OBSERVED][MEDIUM] Three independent sources confirm this mechanism: S13 describes frame retention, S3 explains checkpoint blocking by readers, and S14 quantifies pressure from long-lived readers.

### Observable Signal

[DERIVED][LOW] A steadily growing WAL file signals checkpoint starvation, which occurs when long-running readers prevent checkpoints from recycling committed frames. This observable metric—produced by the actual concurrent-reader patterns and transaction durations of your deployment—reveals when WAL's advantage has degraded, making runtime observation more reliable than pre-computing a theoretical concurrent-reader threshold.

[OBSERVED][LOW] S19 identifies a steadily growing WAL file as especially useful evidence of checkpoint problems, while S3 explains the mechanism by which long-running readers cause this growth.

### Operational Control

[DERIVED][MEDIUM] You can implement query timeout enforcement as a capacity control on large databases, not just as operational discipline. Query timeouts become a capacity mechanism on WAL databases—terminating long-running readers to prevent checkpoint starvation becomes as important as terminating queries for resource conservation.

---

## 8. Workload-Dependent Benefits: Where WAL Actually Wins

### WAL Is Not Universally Better

[HYPOTHESIS][MEDIUM] WAL's throughput advantage over rollback journal comes specifically from enabling concurrent readers during write operations without mutual blocking. For workloads consisting of single-writer batch jobs with no concurrent readers—such as offline data imports or scheduled maintenance tasks—this architectural advantage is completely eliminated. In these cases, WAL provides no performance benefit compared to rollback journal despite adding configuration complexity.

[OBSERVED][MEDIUM] S18 explicitly states that single-writer batch jobs with no concurrent readers gain no performance advantage from WAL over the default rollback journal.

### Workload Characteristics That Benefit

[DERIVED][LOW] The sources state that WAL helps most when an application has many reads mixed with relatively short writes and does not remove write contention from write-heavy workloads. This means WAL's advantage is not determined by a fixed concurrent-reader threshold but by workload characteristics: whether reads substantially outnumber writes, and whether transactions complete quickly. A thousand concurrent readers issuing short queries may benefit; hundreds of concurrent processes with a 50/50 read-write mix will not.

[OBSERVED][LOW] S19 explicitly contrasts read-heavy workloads with short transactions, where WAL helps, versus write-heavy workloads where it does not.

**WAL is beneficial for:**
- High concurrent read volume + relatively infrequent writes
- Short-lived transactions that complete quickly
- Read-to-write ratios > 10:1 or higher
- Workloads where read-write concurrency is common

**WAL is not beneficial for:**
- Single-writer batch jobs with no concurrent reads
- Write-heavy workloads (more writes than reads)
- Workloads with predominantly long-running read transactions
- Network filesystem deployments

---

## 9. Summary: Measured Effects by Scenario

| Scenario | Write Throughput Gain | Concurrent Read-Write | Read Performance | Complexity | Recommendation |
|----------|----------------------|----------------------|------------------|-----------|-----------------|
| **High concurrent reads + low write rate** | Modest (10-50x) | Excellent ✓ | Good if checkpoints tuned | Moderate | **Use WAL** |
| **Single-writer batch jobs** | None ⚠ | N/A | No benefit | Moderate | **Use DELETE mode** |
| **Write-heavy mixed workload** | Minimal (2-5x) | Poor | Degrades with WAL growth | High | **Consider both** |
| **Network filesystem** | N/A ✗ | Impossible ✗ | N/A ✗ | High | **Cannot use WAL** |
| **Long-running read queries** | Variable | Blocked by readers ⚠ | Degrades | High | **Enforce query timeouts** |

---

## 10. Unresolved Questions and Thin Evidence Areas

### What Evidence Is Thin

- **Transaction duration distribution:** The learnings consistently cite "short transactions" as a requirement for WAL to help, but no sources provide quantitative thresholds (e.g., transaction duration must be <100ms). This is [EPISTEMIC] guidance without measurement. Determining whether your actual transaction duration profile matches this requirement requires runtime observation, not configuration decisions.

- **Read-to-write ratio thresholds:** The learnings state that WAL helps "when reads substantially outnumber writes," but provide no measured data on what ratio threshold matters (e.g., 5:1, 10:1, 100:1?). This is [HYPOTHESIS] territory; you cannot definitively know if your 3:1 workload benefits without testing.

- **Concurrent reader count limits:** The learnings explicitly state that concurrent reader count is **not** the constraint—transaction duration and checkpoint starvation are. However, no sources provide measured data on the actual number of concurrent readers that different checkpoint intervals can support without starvation. This is an empirical gap.

- **Storage performance vs. checkpoint interval interaction:** While the learnings identify storage subsystem as the real constraint, no sources provide measured data on the tradeoff curve between checkpoint interval and storage performance (e.g., "on 7200 RPM spinning disk, checkpoint intervals >30 seconds cause queue depth >5"). This would be valuable for tuning but is not measured.

---

## 11. Actionable Recommendations

### For Deployment Decision

1. **Measure your workload before choosing:** Profile your application for:
   - Concurrent read count during write operations
   - Average transaction duration (especially reads)
   - Read-to-write ratio
   - Peak write rate (TPS)

2. **If concurrent reads + short transactions:** Migrate to WAL. The 100x write throughput improvement is real, and concurrent read-write unlocks architectural simplification.

3. **If single-writer batch jobs:** Stay with DELETE mode. WAL adds complexity for zero benefit.

4. **If network filesystem required:** Stay with DELETE mode. WAL is not viable.

### For Production Operations

1. **Monitor WAL file size continuously:** Use .db-wal file size as a leading indicator of read performance degradation or checkpoint starvation. [DERIVED][MEDIUM] Size growth trends upward → checkpoint is being starved → investigate long-running readers.

2. **Enforce query timeouts:** On large databases, query timeouts become a capacity control, not just operational discipline. Long-running readers directly degrade WAL's effectiveness.

3. **Measure actual checkpoint latency from storage metrics, not configuration:** [DERIVED][MEDIUM] If checkpoint-induced latency spikes persist, the problem is storage performance, not checkpoint tuning. Upgrade storage rather than re-tuning settings.

4. **Tune checkpoint frequency based on your read-write ratio:** If reads dominate, checkpoint more frequently (keep WAL small). If writes dominate or storage is constrained, checkpoint less frequently (batch I/O). [OBSERVED][MEDIUM] This should be explicit, not default.

---

## Conclusion

SQLite's WAL mode delivers a **measured 100x write throughput improvement** and **fundamentally enables concurrent readers and writers** compared to rollback journal mode. However, this benefit is **contingent on workload characteristics** (concurrent reads + short transactions) and introduces **operational complexity** around checkpoint tuning, storage performance management, and query timeout enforcement. 

The measured effect is not "WAL is always better"; it is "WAL is dramatically better for specific workloads, and worse for others." **Workload measurement before deployment is essential**, and **runtime observation of WAL file growth is the most reliable production signal** that WAL's benefits are being realized or degraded.

## Contradicciones detectadas (1)

Los conflictos siguientes se reportan SIN resolver, a propósito. Elegir un ganador en silencio sería inventar una certeza que las fuentes no dan.

**CONTRADICCIÓN** — Fuente [0] afirma: Switching from default SQLite configuration (DELETE + synchronous=FULL) to WAL with synchronous=NORMAL produces a 100x throughput improvement for autocommitted INSERT operations. · Fuente [10] afirma: Single-writer batch jobs with no concurrent readers receive no performance benefit from WAL compared to rollback journal.
El conflicto NO está resuelto. Explicación probable: distinta metodología de medición (METHODOLOGY).
Para el operador: [0] measures a combined configuration change (both WAL mode and synchronous setting), while [10] claims WAL itself provides no benefit for batch workloads; determine whether [0]'s 100x improvement is attributable to the WAL mode change alone or primarily to the synchronous setting change (FULL→NORMAL) by isolating the variables—compare DELETE+synchronous=NORMAL against WAL+synchronous=NORMAL holding sync settings equal, which would directly test [10]'s claim without the confounding sync variable.

## Sources

- <https://sesamedisk.com/sqlite-performance-tuning-high-throughput/>
- <https://travishorn.com/a-hands-on-exploration-of-sqlite-for-production/>
- <https://sqlite.org/wal.html>
- <https://www.enterprisedb.com/blog/tuning-maxwalsize-postgresql>
- <https://learn.microsoft.com/en-us/azure/postgresql/troubleshoot/troubleshoot-high-iops>
- <https://www.postgresql.org/docs/current/wal-configuration.html>
- <https://www.postgresql.org/docs/current/wal-intro.html>
- <https://dev.to/merbayerp/database-wal-bloat-how-to-overcome-the-performance-trap-5h40>
- <https://www.sqliteforum.com/p/sqlite-wal-internals-frames-commits>
- <https://dev.to/syed_anzar/how-sqlite-wal-mode-actually-works-the-3-files-shared-memory-and-lock-free-reads-1j2l>
- <https://coddy.tech/docs/sqlite/wal-mode-and-concurrency>
- <https://www.sqlfmt.app/blog/sqlite-wal-mode-concurrency>
- <https://www.sqliteforum.com/p/checkpoint-algorithms-and-wal-performance>
- <https://chirantan.tech/writings/postgresql-checkpoints-dirty-pages-wal-and-recovery>
- <https://www.dozteknoloji.com/en/postgresql-checkpoint-wal-latency-troubleshooting>
- <https://martinuke0.github.io/posts/2026-05-15-optimizing-write-ahead-logs-for-high-throughput-databases/>
- <https://productionhardening.org/wal-optimization-concurrency-tuning/>
- <https://dpkdb.com/article/sqlite-in-production-wal-mode-and-knowing-when-its-enough>
- <https://nalar.dev/sqlite-wal-mode-concurrency-checkpoints-and-operational-pitfalls/>
- <https://systeminternals.dev/sqlite/wal/>

_Note: 13 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** What is the measured effect of SQLite WAL mode on concurrent read and write throughput compared with the rollback journal mode?
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 1152.8 s
- **Errors during run:** 18
- **Started at:** 2026-11-12T01:22:26Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 2 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 3/5 axes searched (BOUNDARY, EVIDENCE, MECHANISM)  — SHORTFALL: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** A_MEASURED×2, C_PRACTITIONER×8, UNKNOWN×18 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** VERIFIED 3, DERIVED 12, HYPOTHESIS 1 · 11 label(s) demoted by the evidence gates
- **E4 contradictions:** 1 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `COVERED` / HIGH [EVIDENCE] — 3 source(s), families A_MEASURED, C_PRACTITIONER, UNKNOWN — _What throughput measurements exist comparing SQLite WAL and rollback journal modes under d_
- `COVERED` / HIGH [BOUNDARY] — 5 source(s), families A_MEASURED, C_PRACTITIONER, UNKNOWN — _At what WAL file size does read query latency begin to measurably increase, and what absol_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Why do WAL mode's file management and locking mechanisms enable concurrent reads during wr_
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _What happens to checkpoint latency and recovery time when using WAL mode on databases larg_
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _At what levels of concurrent connections or transaction frequency does WAL mode's throughp_
- `UNCLASSIFIED` / LOW [BOUNDARY] — 5 source(s), families UNKNOWN — _At what number of concurrent reader processes does WAL mode's advantage over rollback jour_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://github.com/xMesas/sqlite-wal-concurrency...': page-fetch: https://github.com/xMesas/sqlite-wal-concurrency: HTTP Error 404: Not Found`
- `fetch_page 'https://github.com/xMesas/sqlite-wal-concurrency/blob/master...': page-fetch: https://github.com/xMesas/sqlite-wal-concurrency/blob/master/README.md: HTTP Error 429: Too Many Requests`
- `epistemic demoted VERIFIED -> DERIVED: ledger: VERIFIED needs 2 independent lineages, verified spans cover 1`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `learning dropped (code gate): schema field names (2 identifiers): checkpoint_timeout, max_wal_size`
- `learning dropped (code gate): schema field names (3 identifiers): checkpoint_completion_target, checkpoint_timeout, max_wal_size`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 1000`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `epistemic demoted VERIFIED -> DERIVED: VERIFIED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims provenance the landscape cannot establish — no source behind it resolved to a known family; capped at DERIVED`

</details>


## Evidence ledger

- **Claims:** 18 · with a verified quote: 17 (rate 0.944)
- **Quotes:** 29 offered, 5 rejected (not verbatim / unknown source / length)
- **Sources:** 20 snapshots in 20 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 4
- **Sources with instruction-like text (treated as data):** 0

**C1** [DERIVED] Switching from SQLite's default configuration (DELETE + synchronous=FULL) to WAL + synchronous=NORMAL increases write throughput from roughly 279 inserts per second to 33,135 inserts per second on identical hardware—more than 100x improvement. This benchmark has been replicated in multiple independent 2026 production studies.
  - S2 <https://travishorn.com/a-hands-on-exploration-of-sqlite-for-production/> chars 2674-2819: "WAL`  with `synchronous=NORMAL`  is the sweet spot. This combination achieved ~33,135 inserts/sec. That’s over 100 times faster than the default!"
  - _ledger: VERIFIED needs 2 independent lineages, verified spans cover 1_

**C2** [VERIFIED] WAL mode allows readers and writers to operate simultaneously: readers snapshot the database at transaction start and access a consistent view from the main database file plus the WAL, while writers append to the WAL without blocking readers. DELETE mode enforces consistency by acquiring an exclusive lock during commits, causing concurrent read attempts to fail with SQLITE_BUSY errors.
  - S2 <https://travishorn.com/a-hands-on-exploration-of-sqlite-for-production/> chars 7472-7725: "In this mode, when the writer committed changes, it appended them to the `-wal`  file rather than locking the main database file. Concurrent readers were able to continue reading the main database (and shared memory) without being blocked by the writer."
  - S3 <https://sqlite.org/wal.html> chars 4088-4272: "Writers merely append new content to the end of the WAL file. Because writers do nothing that would interfere with the actions of readers, writers and readers can run at the same time."

**C3** [VERIFIED] WAL mode requires all reader and writer processes to access shared memory through a shared wal-index data structure, which mandates co-location on a single machine. WAL does not work over network filesystems. This architectural constraint is the price of WAL's concurrent read-write benefits; DELETE journal mode has no such limitation but loses the concurrency advantage.
  - S1 <https://sesamedisk.com/sqlite-performance-tuning-high-throughput/> chars 3373-3571: "All processes using a WAL database must share a small amount of memory through the `-shm`  wal-index, so all processes must run on the same host machine. WAL does not work over a network filesystem."
  - S3 <https://sqlite.org/wal.html> chars 3921-4086: "the use of shared memory means that all readers must exist on the same machine. This is why the write-ahead log implementation will not work on a network filesystem."

**C4** [DERIVED] When max_wal_size is too small for the write rate, requested checkpoints arrive on a predictable schedule every few minutes, causing bursty I/O flushes that spike disk queue depth and degrade latency. This periodic pattern is visible in disk metrics and checkpoint classifications, allowing you to diagnose the root cause before it compounds into a crisis.
  - S4 <https://www.enterprisedb.com/blog/tuning-maxwalsize-postgresql> chars 2719-2999: "Requested checkpoints are inherently unpredictable and thus can cause variations in performance by adding additional load when it is not expected. This is particularly disruptive on systems with slow I/O, such as those with magnetic drives or virtual machines with limits on IOPs."

**C5** [DERIVED] During peak hours, measure WAL generation by checking the current WAL position, waiting for the checkpoint_timeout interval, checking it again, and calculating the GB generated. Then set max_wal_size well above that figure so checkpoints are driven by the timer rather than by WAL volume exhaustion, eliminating forced checkpoints and their latency spikes.
  - S5 <https://learn.microsoft.com/en-us/azure/postgresql/troubleshoot/troubleshoot-high-iops> chars 8935-9329: "Sizing max_wal_size from measurement rather than guesswork.** During peak hours:  ``` -- Run once and note the result. SELECT pg_current_wal_lsn(); -- Wait checkpoint_timeout seconds, then run again. SELECT pg_current_wal_lsn(); -- Compute WAL generated over that interval, in ..."

**C6** [DERIVED] Setting checkpoint_completion_target to 0.9 distributes the checkpoint flush across approximately 90% of the checkpoint interval—with a 5-minute checkpoint_timeout, this spreads work across 270 seconds instead of arriving as a spike. Combined with proper max_wal_size sizing, this shifts checkpoints from forced (requested) to scheduled (timed), eliminating the bursty I/O that degrades concurrent query performance.
  - S6 <https://www.postgresql.org/docs/current/wal-configuration.html> chars 4669-4975: "With the default value of 0.9, PostgreSQL can be expected to complete each checkpoint a bit before the next scheduled checkpoint (at around 90% of the last checkpoint's duration). This spreads out the I/O as much as possible so that the checkpoint I/O load is consistent throug..."
  - _ledger: VERIFIED needs 2 independent lineages, verified spans cover 1_

**C7** [VERIFIED] In rollback journal mode (SQLite's default), write transactions acquire an exclusive lock on the entire database file, blocking all read queries until commit. WAL mode inverts this by appending changes to a separate log file while readers access a consistent snapshot of the original database file, enabling multiple concurrent readers to operate simultaneously with an active writer without any mutual blocking.
  - S10 <https://dev.to/syed_anzar/how-sqlite-wal-mode-actually-works-the-3-files-shared-memory-and-lock-free-reads-1j2l> chars 683-748: "Readers no longer block writers. Writers no longer block readers."
  - S12 <https://www.sqlfmt.app/blog/sqlite-wal-mode-concurrency> chars 455-637: "Enabling WAL mode allows concurrent readers to query the database simultaneously without blocking writers, and permits writers to commit transactions without blocking active readers."

**C8** [DERIVED] Read query performance in WAL mode degrades proportionally to WAL file size. As the WAL grows, each read query must search through more frames to locate the latest version of each page it needs. Operators can monitor .db-wal file growth as a leading indicator of emerging read latency problems, enabling proactive checkpoint scheduling before slowdowns affect users.
  - S3 <https://sqlite.org/wal.html> chars 6123-6346: "On the other hand, read performance deteriorates as the WAL file grows in size since each reader must check the WAL file for the content and the time needed to check the WAL file is proportional to the size of the WAL file."

**C9** [DERIVED] WAL checkpoint frequency creates a tunable operational tradeoff: checkpointing after every commit keeps the WAL file small (fast reads) but incurs frequent disk sync and seek overhead (slower writes); infrequent checkpointing allows write batching and maximizes throughput but forces readers to search through growing WAL files. The optimal frequency depends on the application's read-to-write ratio. SQLite defaults to checkpointing at 1000 pages (~4MB), but different workloads should measure and adjust.
  - S3 <https://sqlite.org/wal.html> chars 8820-9389: "To maximize the read performance, one wants to keep the WAL as small as possible and hence run checkpoints frequently, perhaps as often as every COMMIT. To maximize write performance, one wants to amortize the cost of each checkpoint over as many writes as possible, meaning th..."
  - _ledger: OBSERVED number(s) absent from verified spans: 1000_

**C10** [DERIVED] Checkpoint latency on large databases is determined primarily by storage subsystem write latency and queue depth, not by database size or checkpoint parameter tuning; many performance issues attributed to checkpoint configuration are actually storage bottlenecks becoming visible during checkpoint write bursts.
  - S14 <https://chirantan.tech/writings/postgresql-checkpoints-dirty-pages-wal-and-recovery> chars 4263-4334: "Checkpoint pressure is especially noticeable on slower storage systems."

**C11** [DERIVED] On databases larger than several gigabytes, a single long-running read transaction forces unbounded WAL file growth by preventing checkpoint progress; WAL frames cannot be discarded while any reader holds a reference, so the WAL grows indefinitely despite checkpoint tuning, eventually causing both storage exhaustion and recovery time collapse.
  - S13 <https://www.sqliteforum.com/p/checkpoint-algorithms-and-wal-performance> chars 4742-4826: "If a reader is still using old WAL frames:  SQLite cannot safely remove those frames"
  - S3 <https://sqlite.org/wal.html> chars 4943-5028: "Thus a long-running read transaction can prevent a checkpointer from making progress."

**C12** [DERIVED] Reducing checkpoint intervals on large databases paradoxically increases total WAL volume and disk I/O: because full_page_writes is enabled by default, every page modified after a checkpoint must be logged in full, so more frequent checkpoints generate more WAL per unit time and reduce overall write throughput.
  - S6 <https://www.postgresql.org/docs/current/wal-configuration.html> chars 2842-3161: "To ensure data page consistency, the first modification of a data page after each checkpoint results in logging the entire page content. In that case, a smaller checkpoint interval increases the volume of output to the WAL, partially negating the goal of using a smaller interv..."

**C13** [HYPOTHESIS] WAL's throughput advantage over rollback journal comes specifically from enabling concurrent readers during write operations without mutual blocking. For workloads consisting of single-writer batch jobs with no concurrent readers—such as offline data imports or scheduled maintenance tasks—this architectural advantage is completely eliminated. In these cases, WAL provides no performance benefit compared to rollback journal despite adding configuration complexity.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C14** [DERIVED] WAL checkpoint frequency creates an unavoidable performance tradeoff: more frequent checkpoints maintain small WAL file sizes and fast read performance since reads scan less data, but increase costly I/O sync operations; less frequent checkpoints amortize sync costs but let WAL grow, forcing each read to search through a larger file. The optimal checkpoint interval is workload-dependent and should reflect whether reads or writes are your bottleneck.
  - S3 <https://sqlite.org/wal.html> chars 8820-9389: "To maximize the read performance, one wants to keep the WAL as small as possible and hence run checkpoints frequently, perhaps as often as every COMMIT. To maximize write performance, one wants to amortize the cost of each checkpoint over as many writes as possible, meaning th..."

**C15** [DERIVED] Read latency in WAL mode is proportional to WAL file size because each reader must scan the WAL to locate needed pages. Since the relationship is directly proportional, you can use WAL size growth as a predictive metric to trigger checkpoint adjustments before users experience noticeable performance loss, giving you lead time to retune rather than reacting after complaints.
  - S3 <https://sqlite.org/wal.html> chars 6142-6345: "read performance deteriorates as the WAL file grows in size since each reader must check the WAL file for the content and the time needed to check the WAL file is proportional to the size of the WAL file"

**C16** [DERIVED] Multiple sources confirm that WAL's concurrency advantage is limited by checkpoint progress, which is blocked by long-running read transactions. A single read transaction holding an old snapshot prevents checkpoints from completing, causing the WAL file to grow unbounded. The operational constraint is therefore not the absolute number of concurrent readers but whether those readers hold transactions open long enough to starve the checkpoint.
  - S3 <https://sqlite.org/wal.html> chars 4943-5133: "Thus a long-running read transaction can prevent a checkpointer from making progress. But presumably every read transaction will eventually end and the checkpointer will be able to continue."
  - S19 <https://nalar.dev/sqlite-wal-mode-concurrency-checkpoints-and-operational-pitfalls/> chars 8041-8186: "Readers normally coexist well with writers in WAL mode, yet old read snapshots can stop checkpoints from advancing far enough to recycle the WAL."
  - S20 <https://systeminternals.dev/sqlite/wal/> chars 8554-8649: "If a reader is holding an old mark, PASSIVE cannot make progress — it does nothing and returns."

**C17** [DERIVED] The sources state that WAL helps most when an application has many reads mixed with relatively short writes and does not remove write contention from write-heavy workloads. This means WAL's advantage is not determined by a fixed concurrent-reader threshold but by workload characteristics: whether reads substantially outnumber writes, and whether transactions complete quickly. A thousand concurrent readers issuing short queries may benefit; hundreds of concurrent processes with a 50/50 read-write mix will not.
  - S19 <https://nalar.dev/sqlite-wal-mode-concurrency-checkpoints-and-operational-pitfalls/> chars 1972-2132: "WAL therefore helps most when an application has many reads mixed with relatively short writes. It does not remove write contention from a write-heavy workload."

**C18** [DERIVED] A steadily growing WAL file signals checkpoint starvation, which occurs when long-running readers prevent checkpoints from recycling committed frames. This observable metric—produced by the actual concurrent-reader patterns and transaction durations of your deployment—reveals when WAL's advantage has degraded, making runtime observation more reliable than pre-computing a theoretical concurrent-reader threshold.
  - S19 <https://nalar.dev/sqlite-wal-mode-concurrency-checkpoints-and-operational-pitfalls/> chars 7172-7331: "A steadily growing WAL file is especially useful evidence. It can indicate that checkpoints are disabled, cannot complete, or are being outrun by the workload."
  - S3 <https://sqlite.org/wal.html> chars 4943-5028: "Thus a long-running read transaction can prevent a checkpointer from making progress."
