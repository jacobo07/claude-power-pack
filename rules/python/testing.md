# Python Testing

Extends [rules/common/testing.md](../common/testing.md).

## Framework

`pytest` is the PP-standard test runner. PP V-* gates are typically
standalone scripts in `tools/test_*.py` that print PASS/FAIL and exit
0/1; `tests/` holds pytest-collected tests.

## Fixtures

Use `pytest.fixture` for setup that multiple tests share. Scope:

- `function`: default, fresh per-test
- `module`: shared across tests in a file
- `session`: shared across the whole pytest run (rare; use cautiously)

## Isolation

Tests that touch the filesystem MUST use `tempfile.mkdtemp` and clean
up in a teardown / fixture finalizer. Never write to `vault/`,
`memory/`, or other persistent paths from a test.

When patching module-level constants:

- For modules imported via different paths (namespace packages),
  override on BOTH `import X` and `from pkg import X` instances --
  they are distinct module objects (L13 from TCO cycle).
- For subprocess-spawned tools that re-import fresh, pass overrides
  via CLI flags, NOT monkey-patched constants (L12 from TIS cycle).

## AAA Pattern in pytest

```python
def test_appends_event_to_log(tmp_path):
    # Arrange
    log = TempLog(tmp_path / "events.jsonl")
    event = make_event(input_tokens=100)

    # Act
    log.append(event)

    # Assert
    assert log.count() == 1
    assert log.last().input_tokens == 100
```

Codified in `modules.uqf.principles.aaa_test_pattern`.

## V-* gate convention

PP feature tests typically follow this pattern:

```python
def main() -> int:
    passes = 0
    fails = 0
    # ... V-* checks, increment passes/fails

    print(f"V-NAME-PASS={passes}/{passes+fails}")
    return 0 if fails == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

## Property-based testing (future)

ECC has hypothesis-based property tests for hooks/validators. PP
stdlib-first policy means we adopt this only when a property test
catches something assertion tests cannot. See
`vault/knowledge_base/ecc-specs/` for the spec.

---

*Portions adapted from ECC rules/python/testing.md under MIT License
(c) 2026 Affaan Mustafa.*
