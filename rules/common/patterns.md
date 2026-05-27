# Common Patterns (cross-language)

## Repository pattern

Encapsulate data access behind a standard interface:

- `find_all() -> list[T]`
- `find_by_id(id) -> T | None`
- `create(data) -> T`
- `update(id, data) -> T`
- `delete(id) -> bool`

Business logic depends on the interface, not the storage mechanism.
Swapping SQLite -> Postgres -> in-memory test fixture requires zero
business-logic changes.

## API response envelope

Consistent shape:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "page": 1, "total": 42 }
}
```

Reject inconsistent shapes -- one place for "is this OK", one place
for "what's the payload", one place for "what failed".

## Adapter pattern (untrusted boundary)

Every untrusted boundary (external API, user input, file format) gets
an adapter that produces a known internal shape OR raises a typed
error. The rest of the codebase never sees the raw external shape.

```python
class StripeAdapter:
    def parse_webhook(self, raw: bytes) -> WebhookEvent:
        # validate signature, parse JSON, schema-check
        # return WebhookEvent (typed internal shape) or raise.
```

## Atomic write pattern (filesystem)

Never write partial state:

```python
import tempfile, os
fd, tmp = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp",
                           dir=target.parent)
with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(content)
os.replace(tmp, target)
```

Used in PP for SCS C6, JIT skill_loader, monitoring state. ECC has
the same pattern in `scripts/lib/atomic-write.js`.

## Fail-open vs fail-closed

Default: fail-closed. Fail-open only for telemetry / optional caching
/ best-effort enrichment, and always with a comment + test. See
[error-handling.md](error-handling.md).

## Single source of truth

When two pieces of data must stay consistent (config + docs, schema +
type, pricing constant + JSON file), pick ONE as the source of truth
and DERIVE the other. The PP's TCO axis derives pricing from
`vault/pricing/anthropic_2026-05.json`; no constants in code.

## Idempotency by default

State-changing operations should be safe to retry. SCS C10 in PP, and
also ECC pattern. Means:

- Use UPSERT instead of INSERT where retries are possible
- Tag operations with a client-supplied idempotency key
- Tests that call the operation twice and verify the second is a no-op

---

*Portions adapted from ECC (github.com/affaan-m/ecc) rules/common/
under MIT License (c) 2026 Affaan Mustafa.*
