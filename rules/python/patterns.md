# Python Patterns

Extends [rules/common/patterns.md](../common/patterns.md).

## Context managers

Anything that acquires a resource exposes a `__enter__/__exit__`
contract OR is wrapped by `contextlib.contextmanager`. No manual
"don't forget to close" comments.

```python
from contextlib import contextmanager

@contextmanager
def temp_session_id(sid: str):
    old = os.environ.get("PP_SESSION_ID")
    os.environ["PP_SESSION_ID"] = sid
    try:
        yield sid
    finally:
        if old is None:
            os.environ.pop("PP_SESSION_ID", None)
        else:
            os.environ["PP_SESSION_ID"] = old
```

## Decorator pattern (telemetry)

PP convention: stack decorators top-down for cross-cutting concerns.
Example from `tools/jit_skill_loader.py`:

```python
@_tis_log_call         # outer: token telemetry
@_tco_inject_routing   # middle: cost routing advisory
def run(data) -> dict:
    ...
```

The decorator wraps `run()` once at module load. Each decorator must
fail-open (any exception in the wrapper swallowed by the wrapper,
NEVER by the wrapped function) so a broken decorator never breaks
production.

## Atomic write idiom

```python
import tempfile, os
from pathlib import Path

def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
```

Used in: `tools/tis.py`, `modules/uqf/`, `tools/normalize_paths.py`,
`tools/_tco_standards_append.py`, `tools/_apex_*_recovery.py`.

## Subprocess + env discipline

When spawning a subprocess:

```python
import os, subprocess, sys

env = os.environ.copy()
env["PATH"] = r"C:\Program Files\Git\cmd;" + env.get("PATH", "")
result = subprocess.run(
    [sys.executable, "tools/foo.py", "--flag", value],
    capture_output=True, text=True, timeout=30, env=env,
)
```

Why: Windows `-NonInteractive` PowerShell has a slimmed PATH that
omits Git, npm, etc. Inheriting from a slimmed parent leaks the gap.

## Iterating safely

```python
# GOOD: iterate, append to new list
results = [transform(item) for item in items if predicate(item)]

# BAD: mutate list during iteration
for item in items:
    if predicate(item):
        items.remove(item)   # UB / undefined order
```

## Walrus operator (Python 3.8+)

```python
if (m := pattern.match(line)) is not None:
    use(m.group(1))
```

Use sparingly; clarity over cleverness.

---

*Portions adapted from ECC rules/python/patterns.md under MIT License
(c) 2026 Affaan Mustafa.*
