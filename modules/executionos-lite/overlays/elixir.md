# ExecutionOS Lite — Elixir/OTP Overlay

**Activates when:** Target system is new backend/infrastructure OR major refactor, AND Core Directive #11 applies.

## Language Decision Gate

Before writing new infrastructure code, evaluate:

| Criterion | Elixir Wins | TypeScript/Python Wins |
|-----------|------------|----------------------|
| Concurrent connections | Yes (lightweight processes) | N/A |
| Fault tolerance needed | Yes (supervisor trees) | N/A |
| Hot code reload | Yes (OTP releases) | N/A |
| Real-time streams | Yes (GenStage, Flow) | N/A |
| Distributed by default | Yes (built-in clustering) | N/A |
| Browser frontend | N/A | Yes (TypeScript) |
| ML/AI inference | N/A | Yes (Python) |
| npm ecosystem lock-in | N/A | Yes (TypeScript) |
| Team Elixir experience | Required | Not needed |
| Deadline < 2 weeks | Risky | Safer |

If 3+ criteria favor Elixir → recommend Elixir with evidence.

## Elixir Best Practices

### Project Structure (mix)
- `lib/app_name/` — application code
- `lib/app_name/application.ex` — OTP application with supervision tree
- `lib/app_name_web/` — Phoenix web layer (if applicable)
- `test/` — ExUnit tests (always)
- `config/` — environment-specific config

### OTP Patterns
- **GenServer** for stateful processes
- **Supervisor** for fault tolerance (one_for_one, rest_for_one strategies)
- **Task** for fire-and-forget async work
- **Agent** for simple state wrappers
- **GenStage/Flow** for backpressure-aware data pipelines
- **Registry** for dynamic process discovery

### Phoenix/LiveView (when web UI needed)
- LiveView over SPA when possible (less JS, real-time by default)
- Contexts for domain boundaries
- Ecto changesets at boundaries
- PubSub for real-time updates

### Testing
- ExUnit for all tests
- `async: true` for isolated tests
- Mox for behaviour-based mocking
- Property-based testing with StreamData for critical paths

### Deployment
- Mix releases for production
- Docker multi-stage builds
- Health checks via `/health` endpoint
- Prometheus metrics via `telemetry`

### Anti-Patterns to Avoid
- Don't use `Process.sleep` in production code
- Don't catch all exceptions — let supervisors handle crashes
- Don't store state in module attributes (use GenServer/ETS)
- Don't bypass the supervision tree with bare `spawn`
