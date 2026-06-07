---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/go.sum"
---
<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place as PP doctrine evolves. -->

# Go Coding Style

> This file extends [common/coding-style.md](../common/coding-style.md) with Go specific content.

## Formatting

- **gofmt** and **goimports** are mandatory — no style debates

## Design Principles

- Accept interfaces, return structs
- Keep interfaces small (1-3 methods)

## Error Handling

Always wrap errors with context:

```go
if err != nil {
    return fmt.Errorf("failed to create user: %w", err)
}
```

## Reference

See skill: `golang-patterns` for comprehensive Go idioms and patterns.
