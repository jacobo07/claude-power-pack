# SOFTWARE ELITE PATTERNS — The Titan Constitution

> **Purpose:** Universal design patterns extracted from the world's most resilient software systems. This document is the architectural backbone for every project built under the Claude Power Pack. Language-agnostic, project-agnostic, but with an **Elixir/OTP bias** — because the BEAM VM's philosophy of isolated processes, immutable messages, and supervised failure is the closest thing software engineering has to a law of physics.

> **How to use:** Before designing any system, scan the Quick Reference table below. If your problem maps to a pattern, apply it. If you're tempted to skip one, ask yourself: "Would WhatsApp/Stripe/Discord skip this at scale?" The answer is no.

---

## The Elixir Bias Philosophy

The BEAM virtual machine (Erlang/Elixir) was built for telephone switches that could never go down. Its core insight applies to ALL software:

1. **Everything is a process** — not an object, not a thread, not a goroutine. A lightweight, isolated unit of computation with its own memory.
2. **Communication is message-passing** — processes never share memory. They send immutable messages. This eliminates 90% of concurrency bugs by design.
3. **Failure is expected** — instead of preventing crashes (defensive programming), you *contain* them. A crashed process is restarted by its supervisor. The system self-heals.

Even if you write TypeScript, Python, or Rust: **think in processes, communicate with messages, let failures be contained.**

---

## Quick Reference

| # | Pattern | Titan | Universal Rule |
|---|---------|-------|---------------|
| 1 | Supervision Trees | WhatsApp/Discord | Crash fast, restart clean — never let one failure cascade |
| 2 | Process Isolation | WhatsApp/Discord | No shared mutable state — communicate only via messages |
| 3 | Backpressure | WhatsApp/Discord | Producers must respect consumer capacity — never overwhelm |
| 4 | Functional Core / Imperative Shell | Phoenix/Ecto | Business logic is pure; side-effects live at the edges |
| 5 | Changeset Pipeline | Phoenix/Ecto | Validate and transform data before it touches persistence |
| 6 | Context Boundaries | Phoenix/Ecto | Modules expose APIs, never internals |
| 7 | Idempotency Keys | Stripe/Kafka | Same input + same key = same output, always |
| 8 | Event-Driven Decoupling | Stripe/Kafka | Services publish facts; interested parties subscribe |
| 9 | Exponential Backoff + DLQ | Stripe/Kafka | Retries must decelerate; permanent failures go to a cemetery |
| 10 | UI = f(State) | React/LiveView | The view is a pure function of the current state |
| 11 | Immutable State Transitions | React/LiveView | State is replaced, never mutated |
| 12 | Minimal Diffing | React/LiveView | Compare old and new — apply only what changed |
| 13 | The Elixir Bias | META | Think in processes, not objects |

---

## TITAN 1: WhatsApp / Discord — BEAM Concurrency

### Pattern 1: Supervision Trees & Let it Crash

**Universal Rule:** A failing process must die fast and be restarted by a supervisor. Never let one failure cascade into a system-wide outage.

**The Problem It Solves:** Defensive programming (wrapping everything in try-catch) creates code that silently swallows errors, accumulates corrupt state, and eventually fails in unpredictable ways. WhatsApp serves 2 billion users with ~50 engineers because their processes crash cleanly and restart in microseconds.

**Architecture:**
```
        [Application Supervisor]
           /        |        \
    [Web Sup]  [Worker Sup]  [PubSub Sup]
      /    \       |    \        |
  [Conn1] [Conn2] [W1] [W2]  [Channel1]
```
Each supervisor monitors its children. When a child crashes:
- `:one_for_one` — restart only the crashed child
- `:one_for_all` — restart all children (for tightly coupled groups)
- `:rest_for_one` — restart the crashed child and all children started after it

If a child crashes too many times (`:max_restarts` in `:max_seconds`), the supervisor itself crashes — escalating to its parent supervisor. This is **hierarchical failure containment**.

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | `Supervisor`, `GenServer`, `Task.Supervisor` | Built-in OTP |
| TypeScript | Process manager with health checks | PM2 cluster, BullMQ workers |
| Python | Worker pools with restart policies | Celery + supervisor config, `multiprocessing` |
| Rust | Supervised async tasks | `tokio::spawn` + `JoinSet` with restart logic |
| Java | Thread pools with `UncaughtExceptionHandler` | Virtual threads (Loom) + custom supervisors |

**Anti-Pattern:** `try { riskyOperation() } catch (e) { console.log(e); /* continue with corrupt state */ }` — This catches the error but leaves the process in an unknown state. The Titan approach: let the process die, let the supervisor restart it with clean state.

**Power Pack Integration:** When designing any service with independent units of work (connections, jobs, handlers), structure them as supervised workers. Never catch-and-continue with potentially corrupt state. Define restart strategies. Wire `Mistake #37 (Silent Quality Degradation)` — every fallback must log WARNING and be observable.

---

### Pattern 2: Process Isolation (Actor Model)

**Universal Rule:** Each unit of work lives in its own memory space. Communication happens exclusively through immutable messages. No shared mutable state. Ever.

**The Problem It Solves:** Shared mutable state is the root cause of race conditions, deadlocks, and "works on my machine" bugs. Discord handles millions of concurrent voice/text connections because each user session is an isolated process that cannot corrupt another's state.

**Architecture:**
```
Process A (own heap)  --[message]--> Process B (own heap)
        |                                    |
   [mailbox: FIFO]                    [mailbox: FIFO]
        |                                    |
  handle_info/cast/call              handle_info/cast/call
```
- Each process has its own garbage collector (no stop-the-world GC)
- Messages are copied between process heaps (true isolation)
- A crashed process only loses its own state — no collateral damage

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | `GenServer`, `Agent`, process mailboxes | Built-in OTP |
| TypeScript | Worker threads, message channels | `worker_threads`, BullMQ, `postMessage` |
| Python | Multiprocessing with queues | `multiprocessing.Queue`, `asyncio.Queue` |
| Rust | Channels between async tasks | `tokio::sync::mpsc`, `crossbeam-channel` |
| Go | Goroutines + channels | Built-in `chan` |

**Anti-Pattern:** Global singleton database connection pool mutated by multiple request handlers simultaneously. Shared `Map<string, UserState>` accessed without locks from concurrent requests.

**Power Pack Integration:** When writing concurrent code, default to message-passing. If two components need to share data, they send messages — never reference the same mutable object. Wire `Mistake #39 (Synchronous Default Trap)` — if runtime has event loop, ALL I/O goes off-thread.

---

### Pattern 3: Backpressure & Mailbox Semantics

**Universal Rule:** A producer must never overwhelm a consumer. The system must signal when to slow down, and producers must respect that signal.

**The Problem It Solves:** Without backpressure, a fast producer floods a slow consumer's queue until memory explodes (OOM kill). WhatsApp handles message spikes by having each process mailbox act as a natural buffer — and when a process can't keep up, the supervisor can shed load or spawn helpers.

**Architecture:**
```
[Producer] --demand(10)--> [ProducerConsumer] --demand(5)--> [Consumer]
     |                           |                              |
  produces 10              transforms 10                  processes 5
  waits for                 buffers rest                  asks for more
  next demand               until demanded                when ready
```
This is **demand-driven** (pull-based), not push-based. The consumer controls the rate.

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | `GenStage`, `Flow`, `Broadway` | Built-in ecosystem |
| TypeScript | Streams with `highWaterMark` | Node.js streams, RxJS `concatMap` |
| Python | Bounded async queues | `asyncio.Queue(maxsize=N)`, `aiostream` |
| Rust | Bounded channels | `tokio::sync::mpsc::channel(N)` |
| Kafka | Consumer groups with partition lag | Built-in consumer group protocol |

**Anti-Pattern:** `while (true) { queue.push(generateItem()) }` — unbounded producer with no consumer feedback. Also: setting `maxsize=0` (unlimited) on queues "because it's easier."

**Power Pack Integration:** Every pipeline, queue, or producer-consumer pair must have a bounded buffer. Default to pull-based (consumer requests work) over push-based (producer dumps work). Monitor queue depth as a health metric.

---

## TITAN 2: Phoenix / Ecto — Pure Data Architecture

### Pattern 4: Functional Core / Imperative Shell

**Universal Rule:** Business logic is a pure function: input in, decision out. Side-effects (database, HTTP, filesystem, email) live at the outermost shell of the system, never inside the core.

**The Problem It Solves:** When business logic is tangled with database calls and HTTP requests, it becomes untestable, unreusable, and fragile. Phoenix contexts keep domain logic pure — you can test `Accounts.validate_registration(params)` without a database, a web server, or network access.

**Architecture:**
```
[HTTP Request] --> [Controller (Shell)]
                       |
                  [Context (Core)] --> pure business logic
                       |              no DB, no HTTP, no side-effects
                  [returns decision]
                       |
                  [Controller (Shell)] --> Repo.insert / send_email / redirect
```

The core answers: "What SHOULD happen?" The shell executes: "Make it happen."

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | Contexts + Schemas (no Repo in core) | Phoenix Contexts, Ecto.Changeset |
| TypeScript | Service layer (pure) + Repository (shell) | Domain functions returning commands |
| Python | Domain module (pure) + Infrastructure (shell) | Dataclasses for decisions, SQLAlchemy at edges |
| Rust | Core crate (no IO traits) + App crate (IO) | Pure functions + `async` only at boundaries |
| Java | Domain objects (no Spring deps) + Service layer | Hexagonal Architecture / Ports & Adapters |

**Anti-Pattern:** `function createUser(data) { const user = db.insert(data); sendEmail(user.email); return user; }` — This function does validation, persistence, AND side-effects. Untestable without mocking everything.

**Power Pack Integration:** When designing any module, ask: "Can I test this function without a database or network?" If no, extract the pure logic. Domain functions return *decisions* (create this, reject that, send this email). The caller (shell) executes those decisions. Wire `Mistake #2 (Detail Without Integration)`.

---

### Pattern 5: Changeset Pipeline (Validate Before Commit)

**Universal Rule:** Data is cast, validated, and constrained in an explicit pipeline BEFORE touching persistence. The pipeline is the single source of truth for data integrity.

**The Problem It Solves:** Scattering validation across controllers, models, and database triggers creates "validation gaps" where invalid data slips through. Ecto Changesets solve this: one pipeline, one place, all validation before the DB ever sees the data.

**Architecture:**
```
Raw params --> cast(fields) --> validate_required() --> validate_format() 
          --> validate_length() --> unique_constraint() --> Repo.insert()
                                                            |
                                                     {:ok, user} | {:error, changeset}
```
The changeset accumulates errors. You never get a partial write — it either passes ALL validations or none.

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | `Ecto.Changeset` pipeline | Built-in Ecto |
| TypeScript | Schema validation at boundary | Zod `.parse()` / `.safeParse()` chain |
| Python | Model validation before ORM | Pydantic `model_validate()` before SQLAlchemy |
| Rust | Type-state pattern + validation | `validator` crate, custom `Validated<T>` wrapper |
| Java | Bean Validation before JPA | `@Valid` + Hibernate Validator |

**Anti-Pattern:** Validating inside the ORM's `save()` method. Or worse: validating in the controller AND the model with different rules. Or: no validation at all, relying on DB constraints to catch errors (losing context for user-facing messages).

**Power Pack Integration:** All external data (user input, API payloads, file uploads) must pass through a validation pipeline before reaching business logic or persistence. Wire `Mistake #24 (MVP Validators)` — if schema defines types + formats + ranges, validator must check all three.

---

### Pattern 6: Context Boundaries (Bounded Contexts)

**Universal Rule:** Each module exposes a clean public API. No module accesses another module's internal tables, schemas, or private functions. Communication between contexts goes through the public API.

**The Problem It Solves:** Without boundaries, modules become a tangled web of cross-dependencies. Changing a table in the `Accounts` module breaks the `Billing` module because it was querying `accounts` directly. Phoenix Contexts enforce this: `Accounts.get_user!(id)` yes; `Repo.get(User, id)` from the Billing module, NEVER.

**Architecture:**
```
[Accounts Context]          [Billing Context]
  - User schema               - Invoice schema
  - create_user/1             - create_invoice/2
  - get_user!/1               - list_invoices/1
  - authenticate/2            - charge_user/2
       |                           |
       +--- public API only -------+
       |                           |
  [accounts table]           [invoices table]
  (PRIVATE to Accounts)      (PRIVATE to Billing)
```

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | Phoenix Contexts with public function API | `mix phx.gen.context` |
| TypeScript | Barrel exports (`index.ts`) per module | ESLint `no-restricted-imports` |
| Python | `__all__` exports + service layer | Explicit public API per package |
| Rust | `pub` only on module boundary functions | Crate-level `pub(crate)` for internals |
| Java | Package-private by default, public interfaces only | Java modules (JPMS) or package structure |

**Anti-Pattern:** `import { userTable } from '../accounts/schema'` inside the billing module. Direct table joins across context boundaries in SQL queries. "It's faster to just query the table directly."

**Power Pack Integration:** When creating a new module, define its public API first. Other modules interact ONLY through that API. If you need data from another context, call its public function — never import its internals. This prevents `Mistake #5 (Config Without Consumers)` by forcing explicit contracts.

---

## TITAN 3: Stripe / Kafka — Distributed Resilience

### Pattern 7: Idempotency Keys

**Universal Rule:** Every operation with side-effects must produce the same result whether executed 1 time or N times with the same idempotency key. Duplicate execution must be safe by design.

**The Problem It Solves:** Networks are unreliable. A payment request might succeed but the response gets lost. The client retries. Without idempotency, the customer gets charged twice. Stripe solves this: every API call accepts an `Idempotency-Key` header. If the key already has a stored result, return it without re-executing.

**Architecture:**
```
Client --> POST /charges {amount: 100, idempotency_key: "abc-123"}
  |
  v
[Lookup "abc-123" in idempotency store]
  |
  +--> EXISTS? Return stored result (200 OK, same response)
  |
  +--> NOT EXISTS? 
         1. Lock the key
         2. Execute the operation
         3. Store the result with the key
         4. Return result
```

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | Idempotency plug + ETS/DB lookup | Custom plug middleware |
| TypeScript | Middleware + Redis/DB key store | Express middleware, `ioredis` |
| Python | Decorator + DB lookup | `@idempotent(key_param="idempotency_key")` |
| SQL | `INSERT ... ON CONFLICT DO NOTHING` + lookup | Native PostgreSQL / MySQL |
| Kafka | Consumer offset tracking + dedup table | Built-in offset commit |

**Anti-Pattern:** `POST /send-email` with no idempotency — network retry sends the email twice. `POST /create-order` that creates a duplicate order on retry instead of returning the existing one.

**Power Pack Integration:** Every API endpoint that mutates state (POST, PUT, DELETE) should accept an idempotency key. Every background job should check "did I already process this?" before executing. Wire `Mistake #7 (Upgrade Without Replacement)` — idempotency must be wired into the existing call chain, not bolted on.

---

### Pattern 8: Event-Driven Decoupling (Pub/Sub)

**Universal Rule:** Services don't call each other synchronously for side-effects. They publish facts ("order.completed", "payment.succeeded") and interested services subscribe and react independently.

**The Problem It Solves:** Synchronous inter-service calls create cascading failures: if the email service is down, the order service hangs waiting for a response. Kafka's event-driven model decouples producers from consumers — the order service publishes `order.completed` and moves on. The email service, analytics service, and inventory service each consume the event at their own pace.

**Architecture:**
```
[Order Service]                    [Email Service]
     |                                  |
  publishes:                       subscribes to:
  "order.completed"                "order.completed"
     |                                  |
     v                                  v
  [Event Bus / Message Broker]     [process event → send email]
     |
     +---> [Analytics Service] (subscribes independently)
     +---> [Inventory Service] (subscribes independently)
```
Adding a new consumer requires ZERO changes to the producer.

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | PubSub + Broadway consumers | `Phoenix.PubSub`, `Broadway` |
| TypeScript | Event emitter + message queue | `EventEmitter`, Redis Streams, RabbitMQ |
| Python | Signal/event system + queue | Django signals, Celery, `asyncio` events |
| Infrastructure | Centralized event bus | Apache Kafka, AWS SNS/SQS, NATS |

**Anti-Pattern:** `OrderService.createOrder() { emailService.sendConfirmation(); analyticsService.track(); inventoryService.decrement(); }` — The order service is now coupled to three other services and will fail if any of them is down.

**Power Pack Integration:** When a service needs to trigger work in another service, publish an event instead of making a direct call. Design events as immutable facts about what happened (past tense: `order.created`, not commands: `create.order`). Wire `Mistake #38 (Producer-Consumer Gap)` — every event published must have at least one consumer wired in the same session.

---

### Pattern 9: Exponential Backoff + Dead Letter Queue

**Universal Rule:** Retries without deceleration are a DDoS attack against yourself. Failed retries that will never succeed must go to a Dead Letter Queue for human investigation.

**The Problem It Solves:** When a service is overloaded or down, immediate retries make it worse. Stripe's retry strategy: wait longer between each attempt, and after a maximum number of retries, park the message for manual review rather than losing it forever.

**Architecture:**
```
Attempt 1: immediate
Attempt 2: wait 1s  (+jitter)
Attempt 3: wait 2s  (+jitter)
Attempt 4: wait 4s  (+jitter)
Attempt 5: wait 8s  (+jitter)
Attempt 6: GIVE UP --> Dead Letter Queue
                          |
                    [Alert + Dashboard]
                    [Human reviews and replays]
```
**Jitter** is critical — without it, all retrying clients synchronize and hit the server in waves (thundering herd).

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | Task.Supervisor + exponential delay | Custom retry with `:timer.sleep` |
| TypeScript | Retry wrapper with backoff | `p-retry`, `axios-retry`, `exponential-backoff` |
| Python | Retry decorator | `tenacity` with `wait_exponential` + `stop_after_attempt` |
| Rust | Retry with backoff | `backoff` crate, `tokio-retry` |
| Infrastructure | Queue-level retry + DLQ | SQS DLQ, Kafka DLT, RabbitMQ `x-dead-letter-exchange` |

**Anti-Pattern:** `while (!success) { retry(); }` — infinite retry with no delay. `catch (e) { setTimeout(() => retry(), 1000) }` — fixed delay with no backoff. Both will hammer a struggling service into oblivion.

**Power Pack Integration:** Every external call (HTTP, DB, queue) must have: (1) a finite timeout, (2) a retry count with exponential backoff + jitter, (3) a fallback path for permanent failure. Wire `Mistake #16 (Scaffold Illusion)` — every external call needs finite timeout + retries + error handler.

---

## TITAN 4: React / LiveView — State Management

### Pattern 10: UI = f(State)

**Universal Rule:** The user interface is a pure function of the current application state. You never manipulate the view directly — you update the state, and the view re-renders automatically.

**The Problem It Solves:** Manual DOM manipulation (`document.getElementById('counter').innerHTML = count`) creates a divergence between what the state says and what the UI shows. LiveView eliminated this class of bugs entirely: the server holds the state, renders HTML, diffs it, and pushes only the changes over WebSocket.

**Architecture:**
```
State: {count: 5, user: "Kobi", items: [...]}
          |
          v
    render(state) --> HTML/VDOM
          |
          v
    [Displayed to user]
          |
    [User clicks button]
          |
          v
    dispatch({type: "INCREMENT"})
          |
          v
    new_state = reducer(old_state, action)
          |
          v
    render(new_state) --> new HTML/VDOM
```

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | `assign/2` + `render/1` in LiveView | Phoenix LiveView |
| TypeScript | Component re-render on state change | React `useState`/`useReducer`, Svelte stores |
| Python | Reactive data binding | Textual, Streamlit, NiceGUI |
| Rust | Elm-like architecture | Yew, Dioxus, Leptos |
| Swift | Declarative UI from state | SwiftUI `@State`, `@Observable` |

**Anti-Pattern:** `document.querySelector('#status').classList.add('active')` alongside a state object that says `status: 'inactive'`. The DOM says one thing, the state says another. Bugs guaranteed.

**Power Pack Integration:** In any UI (web, CLI, game), the displayed output must be derived from a single state source. Never mutate the view directly. State changes → view re-renders. Wire `Mistake #15 (Static Display of Dynamic Data)` — counters and displays must track real state, not initial values.

---

### Pattern 11: Immutable State Transitions

**Universal Rule:** State is never mutated in place. Every state change creates a new state object from the old state + an action. The old state remains untouched.

**The Problem It Solves:** Mutable state makes it impossible to track what changed, when, and why. It makes undo/redo impossible, time-travel debugging impossible, and introduces subtle bugs where one part of the code mutates state that another part depends on. Elixir enforces this at the language level — all data is immutable by default.

**Architecture:**
```
old_state = %{count: 5, items: ["a", "b"]}
action    = {:add_item, "c"}

new_state = update(old_state, action)
# => %{count: 5, items: ["a", "b", "c"]}

old_state is UNCHANGED
# => %{count: 5, items: ["a", "b"]}
```

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | All data is immutable by default | Language-level guarantee |
| TypeScript | Spread operator, `Object.freeze`, Immer | `{...state, count: state.count + 1}`, Immer `produce` |
| Python | Frozen dataclasses, `NamedTuple` | `@dataclass(frozen=True)`, `tuple` over `list` |
| Rust | Ownership + `Clone` for new versions | Move semantics, `Arc` for shared immutable |
| Java | Records (Java 16+), Vavr collections | `record Point(int x, int y)`, Vavr persistent collections |

**Anti-Pattern:** `state.items.push(newItem); setState(state);` — mutating the array in place and then "setting" the same reference. React won't re-render because the reference hasn't changed. Elixir makes this impossible.

**Power Pack Integration:** Default to immutable data structures. In TypeScript: spread/Immer. In Python: frozen dataclasses. Treat state as a value, not a container. If you need to "change" state, create a new version. This enables undo, audit trails, and eliminates mutation bugs.

---

### Pattern 12: Minimal Diffing (Reconciliation)

**Universal Rule:** Never recalculate or re-render everything. Compare the old state with the new state, compute the minimal diff, and apply only what changed.

**The Problem It Solves:** Full re-renders are expensive. If you have a list of 10,000 items and one changes, re-rendering all 10,000 is O(N) waste. React's VDOM diffing and LiveView's server-side HTML diffing both solve this: compute the minimal set of changes and apply only those.

**Architecture:**
```
old_tree:                    new_tree:
  <div>                        <div>
    <h1>Title</h1>               <h1>Title</h1>        (same - skip)
    <p>Count: 5</p>              <p>Count: 6</p>        (CHANGED)
    <ul>10000 items</ul>         <ul>10000 items</ul>   (same - skip)
  </div>                       </div>

Diff: [patch(<p>, "Count: 6")]
Only 1 DOM update instead of 10,002.
```

**Implementation Matrix:**

| Language | Pattern | Library/Tool |
|----------|---------|-------------|
| Elixir | Server-side HTML diff, send patches over WS | Phoenix LiveView (built-in) |
| TypeScript | Virtual DOM reconciliation | React Fiber, Svelte compiled reactivity |
| Databases | Event sourcing (diff = event) | Append-only log of changes |
| APIs | JSON Patch / partial updates | `PATCH` with only changed fields |
| Git | Content-addressable diffing | `git diff` (same principle) |

**Anti-Pattern:** `container.innerHTML = renderAll(state)` — nuking the entire DOM and rebuilding. Re-fetching an entire 500-row table when one row changes. `SELECT * FROM users` after every single update.

**Power Pack Integration:** When building any system that renders or syncs state, implement diffing. For UIs: use framework-native reconciliation. For APIs: support partial updates (`PATCH`). For data sync: send only deltas, not full snapshots. This is a performance pattern AND a correctness pattern.

---

## META-PATTERN: The Elixir Bias

### Pattern 13: Think in Processes, Not Objects

**Universal Rule:** Every complex system becomes simple when you model it as isolated processes that communicate through immutable messages, fail in contained ways, and are supervised by a hierarchy that can restart them.

**This is not about using Elixir.** This is about adopting BEAM's mental model in ANY language:

| OOP Thinking | Process Thinking |
|-------------|-----------------|
| Object with mutable state | Process with immutable state + message mailbox |
| Method call (synchronous, coupled) | Message send (async, decoupled) |
| try-catch-recover (defensive) | Let it crash + supervisor restart (offensive) |
| Shared database/cache | Each process owns its data, communicates changes |
| Thread pool + locks | Process per connection, no locks needed |
| Inheritance hierarchy | Supervision hierarchy |
| Global singleton | Named process with registered address |

**The Acid Test:** For any architecture decision, ask:
1. "If this component crashes, does it take anything else down?" → If yes, isolate it.
2. "Are two components sharing mutable state?" → If yes, make one own the state and the other request it via message.
3. "Is a producer faster than its consumer?" → If yes, add backpressure.
4. "Is business logic mixed with side-effects?" → If yes, extract the pure core.
5. "Can a retry cause duplicate effects?" → If yes, add idempotency keys.

---

## Cross-Pattern Synergies

These patterns reinforce each other. Use them in combination:

| Problem Domain | Primary Pattern | Reinforcing Patterns |
|---------------|----------------|---------------------|
| **Real-time messaging** | Process Isolation (#2) | Backpressure (#3), Event-Driven (#8), UI=f(State) (#10) |
| **Payment processing** | Idempotency (#7) | Exponential Backoff (#9), Changeset Pipeline (#5), Supervision (#1) |
| **API design** | Context Boundaries (#6) | Functional Core (#4), Changeset Pipeline (#5), Idempotency (#7) |
| **Microservices** | Event-Driven (#8) | Process Isolation (#2), Backpressure (#3), Exponential Backoff (#9) |
| **Frontend apps** | UI=f(State) (#10) | Immutable Transitions (#11), Minimal Diffing (#12), Functional Core (#4) |
| **Data pipelines** | Backpressure (#3) | Supervision (#1), Event-Driven (#8), Exponential Backoff (#9) |

## Decision Matrix

When facing a problem, find your row and apply the prescribed patterns:

| When you need to... | Apply Pattern(s) |
|---------------------|------------------|
| Handle concurrent users/connections | #1 Supervision + #2 Process Isolation |
| Process a queue/stream of data | #3 Backpressure + #9 Exponential Backoff |
| Design business logic for a new feature | #4 Functional Core + #5 Changeset Pipeline |
| Organize a growing codebase into modules | #6 Context Boundaries |
| Make an API call safe to retry | #7 Idempotency Keys |
| Connect two services | #8 Event-Driven + #9 Backoff + DLQ |
| Build a UI (web, mobile, CLI) | #10 UI=f(State) + #11 Immutable + #12 Diffing |
| Make any architectural decision | #13 The Elixir Bias (acid test) |

---

*This document is a living constitution. Patterns may be added as new Titans are deconstructed. Version: 1.0 — 2026-04-07.*
