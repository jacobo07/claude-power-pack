---
paths:
  - "**/*.go"
  - "**/go.mod"
  - "**/go.sum"
---
<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place as PP doctrine evolves. -->

# Go Security

> This file extends [common/security.md](../common/security.md) with Go specific content.

## Secret Management

```go
apiKey := os.Getenv("OPENAI_API_KEY")
if apiKey == "" {
    log.Fatal("OPENAI_API_KEY not configured")
}
```

## Security Scanning

- Use **gosec** for static security analysis:
  ```bash
  gosec ./...
  ```

## Context & Timeouts

Always use `context.Context` for timeout control:

```go
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
```
