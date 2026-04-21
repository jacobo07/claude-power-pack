# Action Scripts — YAML Format

Action scripts describe *what the pipeline does to the target*. They are
YAML files parsed into `ActionScript` Pydantic models.

## Structure

```yaml
name: <unique-name>
runtime_class: web | minecraft | python_daemon | cli
description: <one-liner>

setup:
  # Runtime-class-specific keys:
  # web:             url, viewport
  # minecraft:       host, port, username, version, paper_log_path, overall_timeout_ms
  # python_daemon:   launch_cmd, base_url, uvicorn_startup_wait_seconds
  # cli:             command

steps:
  - kind: <step-kind>
    target: <selector or path or empty>
    value: <text or command or empty>
    timeout_ms: 5000
    extra: {}

expectations:
  # Optional structural assertions for contract strategy
  http:
    - method: GET
      path: /health
      status: 200
      json_contains: ["status", "uptime"]
```

## Step kinds by runtime class

| Runtime | Supported kinds |
|---|---|
| web | `navigate`, `click`, `type`, `wait`, `custom` (JS eval) |
| minecraft | `chat`, `command`, `wait` |
| python_daemon | `http` (set `extra.method` and `extra.json`) |
| cli | (steps ignored — setup.command is the whole script) |

## Priority ladder enforcement

Verdict output carries a `priority_level`:
- 1 = stability (crashes, segfaults, ISI, uncaught exceptions)
- 2 = functionality (HTTP contracts, input handling)
- 3 = aesthetics (visual issues that don't break function)
- 4 = polish (minor animation, particles, audio)

Any L1 open ticket blocks L4 work. See `~/.claude/CLAUDE.md` Ley 24.

## Twin mandate (Ley 27)

Every new runtime feature must ship with a `.yml` action script twin in the
same commit. Examples live under `examples/`. Copy one that matches your
runtime class and adapt.
