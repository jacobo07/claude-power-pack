# Elixir Security

Extends [rules/common/security.md](../common/security.md).

## Atom safety

`String.to_atom/1` on user input is a memory leak (the atom table is
GC-free in BEAM). Use `String.to_existing_atom/1` with a guard:

```elixir
def safe_atom(s) do
  try do
    {:ok, String.to_existing_atom(s)}
  rescue
    ArgumentError -> {:error, :unknown_atom}
  end
end
```

## SQL injection

Use Ecto's parameterized queries. NEVER interpolate strings:

```elixir
# GOOD
from(u in User, where: u.id == ^user_id)

# BAD
Ecto.Adapters.SQL.query!(repo,
  "SELECT * FROM users WHERE id = #{user_id}", [])
```

## Code loading

`Code.eval_string/1` on user input == RCE. Same with `:erlang.binary_to_term`
on untrusted binaries (atom injection).

## Phoenix CSRF

`plug Plug.CSRFProtection` is on by default in `:browser` pipeline.
Don't remove it. If a path genuinely needs CSRF off (webhooks), it
goes in `:api` scope with explicit signature verification.

## Secrets

`config/runtime.exs` reads from `System.fetch_env!/1`. Never put
secrets in `config/config.exs` or `config/prod.exs`.

```elixir
# config/runtime.exs
config :my_app, MyApp.Repo,
  url: System.fetch_env!("DATABASE_URL"),
  pool_size: String.to_integer(System.get_env("POOL_SIZE", "10"))
```

## TLS

Phoenix endpoint:

```elixir
config :my_app, MyAppWeb.Endpoint,
  url: [host: "example.com", port: 443, scheme: "https"],
  force_ssl: [hsts: true]
```

## Rate limiting

Use `:plug_attack` or `Hammer` for endpoint throttling. Never roll
your own counter -- race conditions in ETS counters under load are
hard to get right.

---

*Portions adapted from ECC rules/elixir/security.md under MIT License
(c) 2026 Affaan Mustafa.*
