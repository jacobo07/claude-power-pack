# Python Coding Style

Extends [rules/common/coding-style.md](../common/coding-style.md) with
Python-specific guidance.

## Stdlib first

PP doctrine: prefer stdlib. Reach for third-party only when stdlib
has a genuine gap. Any new dependency goes through the SCS C7 (RTK
proxy compatibility) + deps-approved gate.

Existing PP example: `tools/tis.py`, `tools/tco_compact_gate.py`,
`modules/uqf/` -- all stdlib-only.

## Type hints

- Public functions: full hints on params + return
- Use `from __future__ import annotations` for forward refs without
  string quoting
- `list[T]`, `dict[K, V]`, `tuple[A, B]` (PEP 585) over typing.List
- Use `T | None` (PEP 604) over `Optional[T]`
- `ClassVar[T]` for class-level constants in dataclasses

## Dataclasses

- Default to `@dataclass` for value objects
- `frozen=True` when immutability is desired
- Field defaults: `field(default_factory=list)` for mutable defaults
  (NEVER `default=[]` -- caught by `detect_mutable_defaults`)

## Exceptions

- Subclass from a project-domain base: `class ECCError(Exception)`
- `raise X from exc` to preserve causality
- Never `raise X` from inside an `except` without `from exc` -- the
  original traceback is lost

## Atomic writes

Use `tempfile.mkstemp + os.replace` (see
[rules/common/patterns.md](../common/patterns.md)). PP repeatedly:
SCS C6.

## f-strings vs .format

- Default: f-strings
- Use `.format` only for templates loaded from external sources
- Never `%`-formatting in new code

## Imports

```python
# Stdlib
import os
import json
from pathlib import Path

# Third-party (when present)
import requests

# Project-local
from modules.uqf.principles import Principle
```

## Async

- Mark async functions with `async def`
- Type return as `-> Awaitable[T]` or `-> Coroutine[Any, Any, T]`
- `asyncio.create_task` for fire-and-forget; catch errors in the
  callback OR `task.add_done_callback`

---

*Portions adapted from ECC rules/python/ under MIT License
(c) 2026 Affaan Mustafa.*
