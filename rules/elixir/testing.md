# Elixir Testing

Extends [rules/common/testing.md](../common/testing.md).

## Framework

`ExUnit` is the standard. `mix test` runs the suite.

## File layout

```
lib/my_app/foo.ex
test/my_app/foo_test.exs
```

## Test structure

```elixir
defmodule MyApp.FooTest do
  use ExUnit.Case, async: true

  describe "process/1" do
    test "returns ok tuple for valid input" do
      # Arrange
      input = %{value: 42}

      # Act
      result = MyApp.Foo.process(input)

      # Assert
      assert {:ok, %{value: 42}} = result
    end
  end
end
```

## Async tests

- Default to `async: true` -- tests run in parallel
- Disable async only when the test touches global state (a singleton
  GenServer, a registered name, a shared ETS table)

## Setup

```elixir
setup do
  # tmpdir / start a Supervisor / etc
  on_exit(fn -> cleanup() end)
  {:ok, %{key: :value}}
end
```

## Property-based testing

`StreamData` is ExUnit's property test library. Use it when:

- You can articulate an invariant ("for any list xs, reverse(reverse(xs)) == xs")
- You want broader coverage than handwritten cases

Example:

```elixir
property "reverse is involutive" do
  check all xs <- list_of(integer()) do
    assert xs == xs |> Enum.reverse() |> Enum.reverse()
  end
end
```

## Doctests

Use `@doc` examples as runnable tests:

```elixir
@doc \"\"\"
Sum a list.

    iex> MyApp.Sum.sum([1, 2, 3])
    6
\"\"\"
def sum(xs), do: Enum.sum(xs)
```

```elixir
defmodule MyApp.SumTest do
  use ExUnit.Case, async: true
  doctest MyApp.Sum
end
```

## Coverage

`mix test --cover` -- target 80% baseline (per common testing rule).

---

*Portions adapted from ECC rules/elixir/testing.md under MIT License
(c) 2026 Affaan Mustafa.*
