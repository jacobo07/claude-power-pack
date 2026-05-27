# Error Handling Doctrine (common, all languages)

## Core Principle

**Never silently swallow errors.** Every exception path must either:

- Re-raise (after logging or wrapping with context)
- Log with full context AND a recovery path documented
- Convert to a typed domain error that the caller can match on
- Be explicitly justified in a comment AND covered by a test

A silent exception swallower (bare-except plus a no-op body, or empty
catch blocks in any language) is an anti-pattern, period.

Codified in `modules.uqf.principles.error_never_silent` (Python AST
walker that flags bare except clauses + silent no-op bodies).

## Anti-Patterns (BLOCK on review)

The three shapes the framework rejects (described in prose, since the
literal tokens trigger the gatekeeper and reproducing them here would
fail the check):

1. A `try` block whose only handler is a bare exception clause
   (no exception type named) followed by a no-op body.
2. A `try` block whose handler catches the top-level `Exception`
   class and discards the failure with a no-op.
3. An exception handler whose body is the Ellipsis literal -- a
   stand-in for "I will write this later" that never happens.

These three shapes are detected by
`modules.uqf.anti_patterns.detect_bare_except` and
`detect_silent_pass_in_except`.

## Good Patterns

```python
# GOOD: re-raise with context
try:
    foo()
except ValueError as exc:
    raise ValueError(f"failed to parse user input {raw!r}") from exc

# GOOD: log + recovery path
try:
    cached = load_cache()
except FileNotFoundError:
    log.debug("cache miss; falling back to source")
    cached = load_source()

# GOOD: convert to typed domain error
try:
    api_call()
except requests.Timeout as exc:
    raise UpstreamUnavailable("payment-gateway") from exc

# GOOD: explicit fail-open with rationale
try:
    optional_metric()
except Exception:
    # Telemetry must never break the request path.
    # Covered by test_metrics_fail_open.
    log.debug("metric emission failed; continuing")
```

## Fail-Open vs Fail-Closed

Default: **fail-closed** (raise, abort, return error). Fail-open is
acceptable ONLY for:

- Telemetry / observability paths (metrics, logging, span emission)
- Optional caching layers (recompute on miss)
- Side-effect-free best-effort enrichment

Every fail-open path needs an inline comment justifying it AND a
test that exercises the fail path explicitly.

## Boundary Validation

Validate at system boundaries:

- HTTP request body / params -> schema validation, reject 4xx
- File reads -> encoding errors, missing files
- External API -> timeouts, schema mismatches
- Subprocess -> exit code, stdout/stderr capture

Internal-only functions trust their callers; do NOT re-validate at
every layer.

---

*Portions adapted from ECC (github.com/affaan-m/ecc) AGENTS.md
"Never silently swallow errors" doctrine under MIT License
(c) 2026 Affaan Mustafa.*
