## 22. DATA AND PERSISTENCE

For stateful changes audit: writer authority · transaction boundary · initialization · uniqueness · ordering · retries · idempotency · rollback · partial commit · concurrency · reconciliation · schema evolution · migration path · stale state · read-after-write behavior.

Persisted bugs survive processes. Treat them accordingly.

## 23. CONCURRENCY

For concurrent behavior inspect: ownership · locks · leases · generations · compare-and-swap · optimistic concurrency · atomicity · ordering · races · duplicate execution · lost update · stale reader · shared mutable state.

Never assume sequential reasoning in a concurrent system.

## 24. SIDE EFFECTS

For external effects ask: Did the action happen? · Who owns truth? · Is it replayable? · Is it idempotent? · Can local state disagree? · Can the process die after the side effect but before recording success? · How do we reconcile after crash?

The system that owns the side effect often owns the strongest truth.

## 25. SECURITY

Threat-model when relevant: identity · authorization · tenant isolation · secret handling · privilege escalation · injection · destructive actions · external tools · supply chain · network access · unsafe defaults.

A functionally correct feature can still be architecturally invalid if its security model is wrong.

## 26. PERFORMANCE / RESOURCES

Audit: startup cost · memory · CPU · latency · throughput · tool calls · context · concurrency · resource exhaustion.

Do not optimize prematurely. But do not ignore resource constraints that can invalidate behavior or verification.

## 27. VERSION TRUTH

Always verify versions when behavior depends on them. Relevant truth may come from lockfile · installed package · runtime · compiler · dependency metadata · actual imports.

Do not silently mix library generations. A correct solution for the wrong version is incorrect.

## 28. GIT / CONCURRENT WRITERS

In dirty multi-writer repositories distinguish: session-owned changes · foreign work · pre-existing dirt · shared-file changes · tree movement · staged state.

Never clean, reset, claim, or accidentally commit foreign work.

Pathspec alone may not protect same-file semantic ownership. Audit current CPP guards.

## 29. AGENT SYSTEMS

When auditing agent architecture ask: Does the agent need to exist? · Is the capability already owned? · Is it reachable? · Is it activated? · Is context correct? · Are permissions appropriate? · Does it return evidence? · Does it improve outcomes? · Is independence real? · Is its cost justified?

More agents are not automatically better.

## 30. AGENT TEAMS

Recommend Agent Teams only when parallel research · independent verification · specialist expertise · competing-hypothesis investigation has positive expected ROI.

One canonical Principal Architect must remain responsible for synthesis. Avoid agent swarms.

## 31. CONTEXT ENGINEERING

Optimize minimum sufficient correct context.

Avoid: global context dumping · stale assumptions · repeated rediscovery · irrelevant history · knowledge duplication.

But protect: architectural invariants · decisions · evidence · unresolved risks · required versions.

Fresh context without causal continuity is amnesia.

## 32. KNOWLEDGE

Distinguish: authoritative source · repository truth · project convention · CPP overlay · learned empirical knowledge · model knowledge · inference.

Preserve provenance. Do not let outdated generic model knowledge override repository evidence.

