---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/go.sum"
---
<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place as PP doctrine evolves. -->

# Go Testing

> This file extends [common/testing.md](../common/testing.md) with Go specific content.

## Framework

Use the standard `go test` with **table-driven tests**.

## Race Detection

Always run with the `-race` flag:

```bash
go test -race ./...
```

## Coverage

```bash
go test -cover ./...
```

## Reference

See skill: `golang-testing` for detailed Go testing patterns and helpers.
