# Elixir Hooks (PP / InfinityOps integration)

This file documents how the Elixir side of InfinityOps integrates
with the PP harness hook system. The harness hooks themselves are
JS/Node; this file is about the Elixir-side touchpoints.

## Boundary: HTTP / IPC

The PP harness invokes Elixir services over HTTP (or a Unix socket
in production). Hook-side payloads are JSON; the Elixir side decodes,
processes, encodes back.

```elixir
def handle_hook_request(conn, %{"event" => event, "data" => data}) do
  case process(event, data) do
    {:ok, response} ->
      conn |> put_resp_content_type("application/json")
           |> send_resp(200, Jason.encode!(response))
    {:error, reason} ->
      conn |> put_resp_content_type("application/json")
           |> send_resp(400, Jason.encode!(%{error: reason}))
  end
end
```

## Telemetry events

Phoenix and Ecto emit telemetry events. Hook business logic that
consumes them:

```elixir
:telemetry.attach(
  "pp-cost-tracker",
  [:my_app, :request, :stop],
  fn _event, measurements, metadata, _config ->
    # emit to PP TIS via HTTP / GenServer / etc
    track_cost(metadata, measurements)
  end,
  nil
)
```

## Fail-open at boundaries

Hooks must NEVER break the request path. If telemetry emission fails:

```elixir
try do
  emit_telemetry(payload)
rescue
  exc -> Logger.warning("telemetry emit failed: #{inspect(exc)}")
end
```

A failed telemetry call returns `:ok` to the caller; the caller never
sees the failure.

## Process supervision for hook clients

If a hook makes outbound HTTP calls (e.g. to the PP harness or to
Anthropic API for cost reporting), the HTTP client lives in a
supervised GenServer with a circuit breaker. A flapping upstream
must not bring the Elixir node down.

---

*Most patterns here are PP/InfinityOps-native; the JSON-over-HTTP
hook contract is consistent with ECC's harness-hook style.*
