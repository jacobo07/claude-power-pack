# Elixir Coding Style

Extends [rules/common/coding-style.md](../common/coding-style.md).

## Module organization

- One module per file
- Module name matches file name (`MyApp.Foo` -> `lib/my_app/foo.ex`)
- Function order: public first, private after (`def` before `defp`)
- Type specs (`@spec`) on every public function

## Function size

- Default: < 10 lines (functional style enforces short funcs)
- Hard cap: 30 lines for pure functions, 50 for pattern-matching
  cascades
- Use `with` for happy-path chains; never nest 4+ `case` levels

## Pattern matching first

Prefer pattern matching over conditional logic:

```elixir
# GOOD
def handle({:ok, value}), do: process(value)
def handle({:error, reason}), do: log_error(reason)

# AVOID
def handle(result) do
  if elem(result, 0) == :ok do
    process(elem(result, 1))
  else
    log_error(elem(result, 1))
  end
end
```

## Pipelines

- Each pipeline step should be readable in isolation
- Avoid pipelines > 6 steps -- extract a named function
- The first arg of each pipe step must be a value (not a tuple of
  options)

```elixir
"raw input"
|> String.trim()
|> String.downcase()
|> String.split(",")
|> Enum.map(&String.trim/1)
|> Enum.reject(&(&1 == ""))
```

## Naming

- Modules: `CamelCase`
- Functions and variables: `snake_case`
- Predicate functions: `?` suffix (`empty?`, `valid?`)
- Bang functions (raises on error): `!` suffix (`load!`, `parse!`)
- Atoms: `:snake_case`

## Comments

Same rule as common: write a comment when the WHY is non-obvious. Use
`@moduledoc` and `@doc` for public APIs; never leave them empty
(empty doc string == lazy doc).

## Anti-patterns

- `String.to_atom` on user input (memory leak; use `String.to_existing_atom`)
- Catching `_` in `case` without comment (mirrors bare-except in Python)
- Long if/else cascades when pattern matching would express it cleaner

---

*Portions adapted from ECC rules/elixir/ under MIT License
(c) 2026 Affaan Mustafa. Augmented with PP InfinityOps Elixir
conventions.*
