# Cognitive OS — CO-04 — Context Virtual Memory (Hot / Warm / Cold / External)

> The kernel's memory hierarchy. Context is the scarcest, most expensive resource (CO-00),
> so the kernel treats the live window like a CPU treats its registers: only the working
> set is *hot*; everything else lives one tier down and is paged in on demand. This is what
> keeps effective context under the 60% ceiling without losing access to knowledge.
>
> EXTEND, not from scratch: `tools/jit_skill_loader.py` already implements proto-Hot/Warm —
> it loads skills at three depths (discovery ~80 tokens → summary → full) by trigger, with a
> 40KB circuit breaker and a 2h session-dedupe TTL. CO-04 generalizes that pattern from
> *skills* to *all* context and adds the Cold and External tiers it lacks.

---

## Part I — The Four Tiers

### I.1 The hierarchy, by cost and proximity

CO-04 stratifies all knowledge the kernel might use into four tiers, ordered by context
cost (highest first) and retrieval latency (lowest first):

- **HOT** — in the live window *right now*. Only what the immediate task requires. Highest
  context cost (it counts against the 60% ceiling), zero retrieval latency. The discipline:
  HOT is a *working set*, not an archive. The `jit_skill_loader`'s "full" depth is a HOT
  load; its "discovery" 80-token card is the cheapest possible HOT presence (a pointer, not
  the content).
- **WARM** — out of the window but indexed and instantly recoverable: the Knowledge Vault
  (CO-05), the FTS5 indices, `audit_cache` summaries, the session snapshot. Near-zero context
  cost (it's a pointer until paged in), low retrieval latency (one lookup). The
  `jit_skill_loader`'s "summary" depth and the vault's neural summaries are WARM.
- **COLD** — datasets, historical transcripts, logs, old sessions: large, rarely needed,
  never in context unless explicitly paged in. Zero context cost until summoned, higher
  retrieval latency (a search/scan). The transcripts `token_ground_truth` reads, the
  `vault/research/` and `vault/handoffs/` archives, old `sleepy_index` files — all COLD.
- **EXTERNAL** — memory entirely outside the process: files on disk the kernel does not
  index, other repos, the web, MCP-reachable resources. Zero context cost, highest latency
  and lowest trust (CO-10 marks external data untrusted-until-validated, per the prompt-
  defense baseline). EXTERNAL is the backstop: knowledge the kernel *can* reach but pays the
  most (latency + validation) to use.

### I.2 The working-set principle

The governing rule is the working-set principle borrowed from virtual memory: **HOT holds
only the working set for the current task, and nothing else.** Every token in HOT that the
immediate task does not need is a token spent against the 60% ceiling for no work — pure
waste in the WU/MTok ledger (CO-01). The kernel's job is to keep HOT minimal and page the
rest. This is the direct mechanical answer to context bloat: not "compress when full"
(reactive) but "never load what the task doesn't need" (proactive), with everything else one
page-fault away in WARM/COLD.

The `jit_skill_loader`'s aggressive activation is exactly this principle applied to skills: it
keeps skills at discovery depth (80-token pointers) until a trigger proves one is needed for
*this* prompt, then pages it to full. CO-04 declares this the kernel-wide default for all
context: pointers HOT, content WARM/COLD, paged on proven need.

### I.3 Cost/latency tradeoffs made explicit

Each tier has a price the kernel reasons about (CO-01 prices them):

| Tier | Context cost | Retrieval latency | Trust | When to use |
|---|---|---|---|---|
| HOT | Highest (counts vs 60%) | Zero | Full | Working set of the current task only |
| WARM | ~Zero (pointer) | Low (one lookup) | Full (curated) | Anything recoverable from vault/index |
| COLD | Zero | Medium (search/scan) | Full (own data) | Large/historical, summoned on explicit need |
| EXTERNAL | Zero | High + validation | Untrusted until validated | Backstop; out-of-process knowledge |

The kernel always prefers the *lowest-cost tier that can satisfy the need*: a WARM pointer
over a HOT load, a COLD summary over a HOT full-read. This is the memory-tier expression of
CO-03's cheapest-first cascade — indeed CO-03's Vault/asset rungs *are* reads from WARM.

---

## Part II — Paging: Promotion and Demotion

### II.1 Promotion (page-in) on proven need

Knowledge moves HOT only when the current task *proves* it needs it — a trigger match
(jit_skill_loader's model), an explicit reference, a router decision (CO-03) that the answer
isn't already WARM. Promotion is deliberately gated because every promotion spends context: the
kernel pages in the *minimum depth* that satisfies the need (the discovery→summary→full
ladder), never the full content when a summary suffices. The circuit breaker
(jit_skill_loader's 40KB bound) generalizes to a HOT budget: total promotions in a window are
capped so a burst of page-ins cannot itself breach the ceiling — promotion competes for the
same context budget CO-00 governs.

### II.2 Demotion (page-out / eviction) under pressure

When the action band (CO-00, 45–55%) is entered, CO-04 begins demoting: HOT content the
current task no longer needs is paged back to WARM (it remains a pointer), and the working
set shrinks. Demotion is CO-06's domain (the Garbage Collector decides *what* to evict by
recency/relevance/aging); CO-04 provides the *mechanism* (the tiers and the page-out path)
and CO-06 provides the *policy*. The two compose: CO-04 says "here is how content moves
between tiers and what each costs"; CO-06 says "evict these specific items now." A demotion is
lossless by construction — paged-out content is in WARM/COLD, retrievable on the next proven
need, so demotion frees context without losing knowledge.

### II.3 The relationship to /compact and /kclear

`/compact` and `/kclear` are the *blunt* instruments CO-04 exists to make rarely necessary.
`/compact` is a wholesale HOT→summary demotion of the entire session (lossy, host-driven);
`/kclear` is a full HOT eviction with a checkpoint. CO-04's fine-grained paging is the
*surgical* alternative: by keeping HOT minimal continuously, the kernel reaches the bands that
trigger `/compact`/`/kclear` far less often. When they *are* needed, CO-04 informs them — a
`/compact` should preserve the current working set (HOT) and demote the rest; CO-04 knows what
the working set is. The honest boundary: CO-04 cannot *prevent* the model's turn from holding
context (rung-2 limit, CO-00); it minimizes what is *loaded*, which is the part the kernel
controls.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Thrashing.** A task that repeatedly pages the same content HOT→WARM→HOT (the working set
  is mis-identified). Detection: page-in/page-out churn on one item within a short window →
  the item belongs in the stable working set; pin it HOT for the task's duration. (This mirrors
  the anti-thrash discipline already in the PP's edit gate.)
- **Stale WARM/COLD.** A paged-in pointer resolves to content that has since changed.
  Detection: hash/mtime check on page-in (the `audit_cache` model — hash-match = use cached,
  else re-read). Stale content is re-fetched, never served blind.
- **Over-eager promotion (bloat).** Loading at full depth when summary would do, or paging in
  speculatively. Detection: HOT content that the task never actually referenced → its
  promotion was waste (zero WU contribution) → tighten the promotion gate for that trigger.
- **EXTERNAL trust failure.** Untrusted external data paged in and acted on without validation.
  Prevention: CO-10's prompt-defense baseline — external/fetched/retrieved data is validated or
  rejected before it can influence reasoning; CO-04 marks the EXTERNAL tier untrusted by default.

### III.2 Rollback protocol

CO-04 generalizes an existing, proven mechanism, so rollback is graceful: (1) disable the
generalized paging and revert to `jit_skill_loader`'s skill-only behavior (today's baseline) —
the kernel loses tiered paging for non-skill context but keeps the working JIT loader; (2) if
demotion misbehaves (evicting needed content), pin the demotion policy off so HOT only grows
(reverting to no-eviction, relying on `/compact` as before); (3) the tier *indices* (WARM/COLD)
are read-only catalogs over existing data — disabling CO-04 never deletes them. The fail-safe
direction is "load more, page less" — the pre-kernel behavior — never "lose knowledge".

### III.3 Integration contract

- **CO-00** — HOT is the context the ceiling measures; CO-04's working-set minimization is the
  primary *proactive* defense of the 60% line (load less, rather than compact later). Promotions
  are charged against CO-00's budget.
- **CO-03** — the Vault/asset rungs of the cascade are WARM reads; CO-03 is CO-04's main page-in
  trigger.
- **CO-05** — WARM *is* largely the Cognitive Asset Registry; CO-04 provides the tiering, CO-05
  the content and freshness.
- **CO-06** — provides the eviction *policy* CO-04's demotion mechanism executes.
- **CO-07** — session hibernation is a whole-session demotion to COLD/External (freeze the
  working set to disk); CO-04's tiers define what hibernation serializes.
- **`/compact` `/kclear` `/clear`** — CO-04 makes them rarer (surgical paging vs blunt reset) and
  informs them (preserve the working set, demote the rest).
- **Cursor / Knowledge Vault** — WARM/COLD are the vault + indices; the statusline HUD can expose
  HOT working-set size as a proactive ceiling signal.

### III.4 Anti-patterns (forbidden)

- **Loading content HOT speculatively.** Paging in "just in case". Promotion requires proven
  need; the working set is minimal.
- **Full-depth load when a summary suffices.** Skipping the discovery→summary→full ladder.
- **Serving a stale pointer blind.** Page-in without a freshness check.
- **Acting on EXTERNAL data without validation.** Trusting untrusted-tier content.
- **Treating /compact as the primary tool.** Reaching for the blunt reset instead of keeping HOT
  minimal continuously — that is reactive context management, the exact pattern CO-04 replaces.

---

### CO-04 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Keeps HOT to the current task's working set; everything else WARM/COLD/External as pointers | Continuous; promotion on proven need only | It cannot evict context the running turn itself holds (rung-2 limit) |
| Promotion pages in the minimum depth (discovery→summary→full) under a HOT budget cap | Always | Speculative pre-loading |
| Demotion is lossless — paged-out content is retrievable from WARM/COLD on next need | Always | — |
| Page-in performs a freshness check; stale content is re-fetched, EXTERNAL is validated | Always | Trust of unvalidated external data |
| Rollback reverts to load-more/page-less (pre-kernel) without losing knowledge | On misbehavior | — |

**Guarantee level (honest):** CO-04 is a *proactive load-discipline* layer — it minimizes what
enters HOT (the part the kernel controls), which is the strongest proactive defense of CO-00's
ceiling. It cannot revoke context a running turn already holds; that residual remains `/compact`
+ the breach protocol. *Sealed under SCS C61.*
