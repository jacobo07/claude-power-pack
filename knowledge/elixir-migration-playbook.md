# Elixir Migration Playbook

## When to Migrate

Score the project against the 10-criteria fragility gate:

| # | Criterion | Score 1 if True |
|---|-----------|----------------|
| C1 | Long-running process (daemon, worker, agent) | 1 |
| C2 | Concurrent operations (parallel API calls, multi-agent) | 1 |
| C3 | Fault tolerance required (production, user-facing) | 1 |
| C4 | State management across requests (sessions, caches) | 1 |
| C5 | Real-time communication (WebSocket, streaming) | 1 |
| C6 | Multi-provider failover (LLM gateways, API routing) | 1 |
| C7 | Background job processing (queues, pipelines) | 1 |
| C8 | Hot code reload needed (zero-downtime updates) | 1 |
| C9 | Configuration complexity (multi-env, runtime config) | 1 |
| C10 | Process isolation required (crash containment) | 1 |

**Score 0-1:** Keep current language. No migration needed.
**Score 2-3:** Recommend Elixir. Create LDR if choosing otherwise.
**Score 4+:** Elixir is default. Non-Elixir requires LDR + explicit override.

## Language Decision Record (LDR) Template

```markdown
# LDR: [Project Name]
- **Fragility Score:** X/10
- **Criteria Met:** C1, C3, C5, ...
- **Chosen Language:** [Elixir | Python | TypeScript | ...]
- **If Not Elixir, Reason:** [deadline, team expertise, existing codebase]
- **OTP Equivalents Required:**
  - [ ] Supervision: [PM2 / systemd / custom]
  - [ ] Circuit breaker: [opossum / custom]
  - [ ] Graceful shutdown: [SIGTERM handler]
  - [ ] State persistence: [Redis / file / DB]
  - [ ] Hot reload: [nodemon / not available]
```

## Case Studies

### AADEF Engine (Score 8/10 → Elixir)
- 65 tests, 0 failures
- GenServer for self-healing agent, LLM gateway, pattern store
- ETS for in-memory cache (survives process crashes)
- Supervision tree: rest_for_one (infra → engines → routing)
- Result: Zero unhandled crashes in production

### KobiiClaw Resilience (Score 7/10 → Elixir)
- 45 tests, 0 failures
- 4 domain adapters via @behaviour (compile-time contract enforcement)
- ProxyRotator + RateLimiter as supervised GenServers
- Python bridge via Port (existing daemon untouched)
- Result: Fault isolation between domains, automatic recovery

## Anti-Fragility Patterns

| Python Problem | Elixir Solution |
|---------------|----------------|
| `spawn` without cleanup | `Task.Supervisor.async_nolink` |
| Direct dict mutation from threads | GenServer serialized access |
| JSON file persistence every 10 min | ETS/DETS write-through |
| `process.exit(1)` kills everything | Supervision tree isolates failure |
| Manual retry loops | `Task.Supervisor` + exponential backoff |
| `try/except: pass` swallows errors | Pattern matching forces handling |
