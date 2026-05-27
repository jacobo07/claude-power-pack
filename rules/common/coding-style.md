# Coding Style (common, all languages)

## Function size

- Target: < 50 lines
- Hard cap: 80 lines unless justified (exhaustive switch, config table)

ECC anti-pattern detector `detect_god_function` flags functions > 50.

## File size

- Target: 200-400 lines
- Hard cap: 800 lines -- extract modules by responsibility

## Nesting

- Max 4 levels of nesting (if / for / while / try)
- Beyond 3 -> use early returns, extract helpers, or invert control flow

## Naming

- Public functions / classes / constants: clear, full-word
- Private helpers (`_foo`): can be terse if scope is < 30 lines
- No single-letter names except canonical loops (`i, j, k` for indices,
  `x, y` for coordinates) and short comprehensions
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Boolean vars: prefix with `is_` / `has_` / `should_`

## Immutability (where the language allows)

- Prefer immutable data structures by default
- Return new objects instead of mutating arguments
- In Python: dataclasses with `frozen=True` for value objects; never
  use mutable defaults in function signatures (caught by
  `detect_mutable_defaults`)

## Comments

- Default: **no comments** -- well-named identifiers do that job
- Write a comment when the WHY is non-obvious (hidden constraint,
  workaround for a specific bug, surprising invariant)
- Never narrate WHAT the code does
- Never reference the current task / fix / caller -- those belong
  in the commit message or PR description

## Type hints (typed languages)

Public functions MUST have type hints on parameters and return value.
Internal helpers (`_foo`) are exempt. Detected by
`detect_missing_type_hints`.

## Constants vs magic numbers

```python
# BAD: magic number
if retries > 3:
    raise TimeoutError(...)

# GOOD: named constant
MAX_RETRIES = 3
if retries > MAX_RETRIES:
    raise TimeoutError(...)
```

Well-known constants are exempt: `0, 1, -1, 100, 200, 404, 500, 1000,
1024, 60, 24, 365` and other HTTP status codes / time-unit conversions.

Detected by `detect_magic_numbers`.

## Imports

- Stdlib first, third-party second, project-local third
- One import per line for `from X import a, b, c` only when items are
  related; otherwise split
- No wildcard imports (`from X import *`)
- No conditional imports inside hot paths (lazy-import at top of the
  one function that needs them)

---

*Portions adapted from ECC (github.com/affaan-m/ecc) rules/common/
under MIT License (c) 2026 Affaan Mustafa.*
