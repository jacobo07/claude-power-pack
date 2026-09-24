defmodule KeosQwen.Provider do
  @moduledoc """
  The only way KEOS-Qwen reaches a model, with the destination pinned in code.

  Measured 2026-09-24, and this module exists because of it: `ClaudeCode.query/2`
  was given `provider: :ollama`, `model: "qwen3-coder-30b"` and
  `OLLAMA_HOST=http://127.0.0.1:8081`, and sent the request to Anthropic anyway
  -- `cf-ray: a403245c7c49d34a-FRA`, `server: cloudflare`, `HTTP 401`. Three
  runs, three times. The same repo's `Services.API.Router.create_message/3`,
  called directly with the same values, answered `server: llama.cpp` with the
  right model and zero egress.

  So the harness is used as a LIBRARY, entered at its own documented single
  entry point, and the destination is a module attribute rather than an
  environment variable. An env var is a value something else can win; a compiled
  constant is not. Nothing here reads `OLLAMA_HOST`, `ANTHROPIC_API_KEY` or
  `CLAUDE_CODE_API_PROVIDER`, so nothing there can redirect us.

  The caller may not override the destination either. Passing `:provider`,
  `:model` or `:base_url` raises rather than being silently ignored: a caller
  that believed it was redirecting the request and was not is exactly the
  failure this module was built to remove, and swallowing the option would
  reproduce it one layer up.
  """

  alias ClaudeCode.Services.API.Router

  @provider :ollama
  @model "qwen3-coder-30b"
  @base_url "http://127.0.0.1:8081"
  @default_max_tokens 4096

  @pinned_keys [:provider, :model, :base_url]

  @doc """
  The destination, readable so a gate can assert on it instead of on a comment.
  """
  def pinned, do: %{provider: @provider, model: @model, base_url: @base_url}

  @doc """
  Ask the pinned local model.

  Returns whatever the Router returns: `{:ok, message}` or `{:error, reason}`.
  It is NOT normalised here -- the outcome vocabulary that decides whether a
  failure is the model's or ours lives in `modules/keos_qwen/outcome.py`, and
  duplicating its judgement in Elixir would create the second vocabulary of
  INCONCLUSIVE that the phase-4 audit warned against.
  """
  def ask(prompt, opts \\ []) when is_binary(prompt) and is_list(opts) do
    case Enum.filter(@pinned_keys, &Keyword.has_key?(opts, &1)) do
      [] -> :ok
      offending ->
        raise ArgumentError,
              "#{inspect(offending)} is pinned in KeosQwen.Provider and cannot be " <>
                "overridden by a caller. The destination is a compiled constant " <>
                "precisely because a configurable one was measured silently losing " <>
                "to Anthropic on 2026-09-24."
    end

    Router.create_message(
      [%{role: "user", content: prompt}],
      Keyword.get(opts, :tools, []),
      provider: @provider,
      model: @model,
      base_url: @base_url,
      max_tokens: Keyword.get(opts, :max_tokens, @default_max_tokens)
    )
  end

  @doc """
  Did this response come from our own endpoint?

  Answered from the response's own headers, not from what we intended to send.
  `llama-server` identifies itself as `llama.cpp`; a remote provider fronted by
  Cloudflare carries `cf-ray` and `server: cloudflare`. Three outcomes, because
  "we could not tell" is not "it was local": a response with no headers proves
  nothing about where it came from and must not read as a pass.
  """
  def served_by(%{__headers__: headers}) when is_map(headers) and map_size(headers) > 0 do
    server = headers |> Map.get("server", []) |> List.first() |> to_string() |> String.downcase()

    cond do
      String.contains?(server, "llama.cpp") -> {:local, server}
      Map.has_key?(headers, "cf-ray") or String.contains?(server, "cloudflare") -> {:remote, server}
      true -> {:unknown, server}
    end
  end

  def served_by(_), do: {:unknown, "no headers on the response"}
end
