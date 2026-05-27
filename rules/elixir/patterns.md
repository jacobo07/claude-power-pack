# Elixir Patterns

Extends [rules/common/patterns.md](../common/patterns.md).

## With-pipeline for fallible flows

`with` collapses nested case branches into a flat happy-path:

```elixir
with {:ok, parsed} <- parse(raw),
     {:ok, validated} <- validate(parsed),
     {:ok, saved} <- save(validated) do
  {:ok, saved}
else
  {:error, reason} -> {:error, reason}
end
```

Each `<-` binds when the right side matches; the first mismatch
falls into `else`.

## Tagged tuples

Return `{:ok, value}` / `{:error, reason}` from any function that
can fail. Pattern-match on the tag.

## GenServer

A GenServer wraps state behind message passing. Use it for:

- Long-lived stateful processes
- Serial access to a shared resource
- Background workers

Avoid:

- One GenServer per request (use processes directly via `Task.async`)
- GenServer as glorified mutable dict (use `Agent` or `:ets`)

## Supervisor tree

Every long-running process belongs in a supervision tree. Children
get one of:

- `:one_for_one` -- restart only the crashed child
- `:one_for_all` -- restart all siblings on any crash
- `:rest_for_one` -- restart the crashed child and everything spawned after

Default to `:one_for_one` and choose differently only when the
state of one child IS the state of others.

## Behaviours

A behaviour is a contract. Define one when you have N+ implementations
of a common interface:

```elixir
defmodule Storage do
  @callback get(key :: String.t()) :: {:ok, term()} | {:error, term()}
  @callback put(key :: String.t(), value :: term()) :: :ok | {:error, term()}
end

defmodule Storage.SQLite do
  @behaviour Storage
  # ...
end
```

## ETS for fast reads

When you need a shared, fast-read, low-write data structure (cache,
registry), use `:ets`. Default to `:public` for cross-process; use
`:protected` for single-writer.

## Atomic file writes

Same idiom as Python: write to a tempfile, then rename.

```elixir
def atomic_write(path, content) do
  tmp = path <> ".tmp"
  File.write!(tmp, content)
  File.rename!(tmp, path)
end
```

---

*Portions adapted from ECC rules/elixir/patterns.md under MIT License
(c) 2026 Affaan Mustafa.*
