# Testing Requirements (common, all languages)

## Minimum coverage: 80% (aspirational)

Three test types, all required for production features:

1. **Unit tests** -- individual functions, utilities, components
2. **Integration tests** -- API endpoints, database operations,
   cross-module flows
3. **E2E tests** -- critical user flows / scripted end-to-end paths

PP empirical layer: every feature ships with at least one V-* gate
that exercises the feature end-to-end (NOT just unit).

## Test-Driven Development (TDD)

MANDATORY workflow:

1. Write the test first -- **RED** (test fails)
2. Run the test -- confirm it FAILS for the right reason
3. Write the minimal implementation -- **GREEN** (test passes)
4. Run the test -- confirm it PASSES
5. **REFACTOR** -- clean up, keep tests green
6. Verify coverage / V-gates -- progress, not regression

Codified in `modules.uqf.principles.tdd_workflow` (heuristic: every
new source file in a change set must have a corresponding test file).

## Test Structure (AAA Pattern)

Prefer Arrange-Act-Assert layout:

```python
def test_appends_event_to_log():
    # Arrange
    log = TempLog()
    event = make_event(input_tokens=100)

    # Act
    log.append(event)

    # Assert
    assert log.count() == 1
    assert log.last().input_tokens == 100
```

Codified in `modules.uqf.principles.aaa_test_pattern`.

## Test Naming

Descriptive names that explain the behavior under test:

```python
def test_returns_empty_list_when_no_matches():
def test_raises_value_error_when_api_key_missing():
def test_falls_back_to_default_when_cache_unavailable():
```

Avoid:

```python
def test_function_1():   # opaque
def test_works():        # vacuous
def test_edge_case():    # which edge?
```

## Troubleshooting Test Failures

1. Check test ISOLATION first (env vars, tmpdir, module state)
2. Verify mocks/fixtures are correct
3. Fix the IMPLEMENTATION, not the test (unless the test was wrong)

## V-* Gate Convention (PP-native)

PP tests are conventionally named `V-<DOMAIN>-<CHECK>` and emit
`PASS/FAIL` lines. A test file that exercises N gates ends with:

```
TCO_PASS=8/8  threshold=8/8
```

This is parseable by `verify_spp.py` rows and by cold-boot evidence
files.

---

*Portions adapted from ECC (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa.*
