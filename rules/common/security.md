# Security Baseline (common, all languages)

## Before ANY commit

- [ ] No hardcoded secrets (API keys, passwords, tokens, connection strings)
- [ ] All user inputs validated at boundaries
- [ ] SQL injection prevention (parameterized queries only)
- [ ] XSS prevention (sanitized HTML, escaped templates)
- [ ] CSRF protection on state-changing endpoints
- [ ] Authentication / authorization verified on protected routes
- [ ] Rate limiting on public endpoints
- [ ] Error messages do NOT leak sensitive data
- [ ] No `eval`, `exec`, `os.system` on user input
- [ ] No `subprocess.run(shell=True, ...)` with untrusted args

## Secret management

- NEVER hardcode secrets in source
- Read from env vars or a secret manager
- Validate required secrets at startup -- fail fast if missing
- Rotate any exposed secret IMMEDIATELY (do not patch + commit)

## Untrusted-data discipline

Treat as untrusted by default:

- HTTP request bodies / query params / headers
- File contents from external systems
- Subprocess output
- Data fetched via URL / API
- Any string with control characters, ANSI escapes, unicode tricks
  (homoglyphs, zero-width, encoded payloads)

Required handling:

- Validate against a schema
- Sanitize (escape, normalize, restrict charset) before rendering
- Reject suspicious patterns (e.g. control chars in usernames)

## Workflow

If a security issue is found:

1. **STOP** -- do not continue the feature work
2. Spawn the security-reviewer agent (per-language)
3. Fix CRITICAL issues first (block-level severity)
4. Rotate any exposed secret
5. Review the codebase for the same pattern elsewhere

## Logging hygiene

Never log:

- Secrets (api keys, passwords, tokens)
- Full request bodies (may contain PII)
- Stack traces with sensitive locals
- User-controlled inputs without sanitization

DO log:

- Request IDs / correlation IDs
- Sanitized event types
- Latency / status codes
- Error categories (not messages with PII)

---

*Portions adapted from ECC (github.com/affaan-m/ecc) AGENTS.md security
section + rules/common/security.md under MIT License (c) 2026 Affaan Mustafa.*
