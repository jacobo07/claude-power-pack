# Zero-Issue Baseline — Kill-Switch Methodology

## Concept
Every Claude Code session runs a physical enforcement hook (`zero-issue-gate.js`) on Stop that auto-detects the project language and runs compile + scaffold audit + tests. If ANY gate fails, Claude is BLOCKED from claiming completion. After 3 consecutive failures, `BLOCKED_DELIVERY.md` is created and the session terminates.

## Components

### Domain Registry (`~/.claude/hooks/domain-registry.json`)
Maps project markers to compile/test/lint commands:
- `mix.exs` → Elixir: `mix compile --warnings-as-errors` + `mix test`
- `tsconfig.json` → TypeScript: `npx tsc --noEmit` + `npm test`
- `pyproject.toml` → Python: `python -m compileall` + `pytest`
- `pom.xml` → Java: `mvn compile -q` + `mvn test -q`
- `Cargo.toml` → Rust: `cargo check` + `cargo test`
- `go.mod` → Go: `go build ./...` + `go test ./...`
- `CMakeLists.txt` → C/C++: `make` + `make test`

### Per-Project Override (`.claude-quality-gate.json`)
Projects can customize gates by placing this file in their root:
```json
{"compile": "mix compile --warnings-as-errors", "test": "mix test test/specific/", "extra_gates": ["mix dialyzer"]}
```

### 3-Gate Evaluation
1. **COMPILE** — Language-specific compile command (strict mode)
2. **SCAFFOLD** — Pattern scan for `:infinity`, TODO, commented-out wiring, empty catches
3. **TEST** — Language-specific test command (skip if no test framework detected)

### 3-Strike Escalation
- Failure 1: Warning message with exact error output
- Failure 2: Warning with "Fix before claiming done"
- Failure 3: `BLOCKED_DELIVERY.md` created in project root + `{"continue": false}` kills session

### Reward Integration (Agent Lightning)
- All gates pass → positive reward (1.0) emitted to trace buffer
- Any gate fails → negative reward (0.0) with failed gate name
- Rewards feed APO for automatic prompt optimization

## Adding a New Language
1. Add entry to `domain-registry.json` with `detect`, `compile`, `test`, `lint` fields
2. The zero-issue-gate auto-detects based on `detect` file markers
3. No code changes needed — purely configuration
