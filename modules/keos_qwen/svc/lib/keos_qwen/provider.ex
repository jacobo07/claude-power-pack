defmodule KeosQwen.Provider do
  @moduledoc """
  The only way KEOS-Qwen reaches a model: destination pinned, spend metered.

  ## Why the destination is a compiled constant

  Measured 2026-09-24. `ClaudeCode.query/2` was given `provider: :ollama`,
  `model: "qwen3-coder-30b"` and `OLLAMA_HOST=http://127.0.0.1:8081`, and sent
  the request to Anthropic anyway -- `cf-ray: a403245c7c49d34a-FRA`,
  `server: cloudflare`, `HTTP 401`. Three runs, three times. The same repo's
  `Services.API.Router.create_message/3`, entered directly with the same values,
  answered `server: llama.cpp` with the right model and zero egress.

  So the harness is a LIBRARY entered at its documented single entry point, and
  the destination is a module attribute. An environment variable is a value
  something else can win; a compiled constant is not.

  ## Why the LEDGER ROOT is not pinned the same way, and what that costs

  The destination must be unspoofable. The ledger's *location* is legitimately
  per-deployment and per-test, so it is read from `KEOS_QWEN_LEDGER_ROOT` with
  the production path as the default. That is a weaker property and it is worth
  saying plainly: a caller who can set that variable can point us at an empty
  directory and reset the budget. It is acceptable because the variable is set
  by the unit file rather than by a request, and because the property it guards
  is spend rather than egress. If that stops being true, pin it.

  ## Three refusals that are not each other

    * `{:refused, code, reason}`   -- the ledger said no. Nothing was spent.
    * `{:unavailable, reason}`     -- we could not ASK the ledger. Fails CLOSED:
      an unreadable budget must not license unbounded spend on a host carrying
      15 production services, and "could not tell" is not "go ahead".
    * `{:error, reason}`           -- the call was made and the model or the
      transport failed. This one IS about the subject.

  Collapsing any two of these tells the operator something false about their own
  system: a permission problem would read as a spent budget and send them to
  wait for midnight.
  """

  alias ClaudeCode.Services.API.Router

  @provider :ollama
  @model "qwen3-coder-30b"
  @base_url "http://127.0.0.1:8081"
  @default_max_tokens 4096

  @pinned_keys [:provider, :model, :base_url]

  @ledger_script "/home/kobii/keos/keos_qwen/ledger/ledger.py"
  @ledger_python "python3"
  @default_ledger_root "/home/kobii/keos/ledger"
  @ledger_root_env "KEOS_QWEN_LEDGER_ROOT"
  @caller "elixir:KeosQwen.Provider"

  # ledger.py's own exit contract. Read as a POSITIVE list: an exit code we have
  # not seen is HARNESS territory, not permission to proceed.
  @ledger_allow 0
  @ledger_refused 3
  @ledger_unreadable 4

  def pinned, do: %{provider: @provider, model: @model, base_url: @base_url}

  def ledger_root, do: System.get_env(@ledger_root_env) || @default_ledger_root

  @doc """
  Ask the pinned local model, if the ledger allows it.

  Order is not cosmetic: decide, then call, then record. Recording before the
  effect would spend budget on calls that never happened; recording only on
  success would hide the ones that consumed the endpoint's attention and
  returned nothing, which is precisely the class the ledger exists to bound.
  """
  def ask(prompt, opts \\ []) when is_binary(prompt) and is_list(opts) do
    refuse_pinned_overrides!(opts)

    case consult_ledger(opts) do
      {:ok, _decision} ->
        result =
          Router.create_message(
            [%{role: "user", content: prompt}],
            Keyword.get(opts, :tools, []),
            provider: @provider,
            model: @model,
            base_url: @base_url,
            max_tokens: Keyword.get(opts, :max_tokens, @default_max_tokens)
          )

        record(result, opts)
        result

      refusal ->
        refusal
    end
  end

  defp refuse_pinned_overrides!(opts) do
    case Enum.filter(@pinned_keys, &Keyword.has_key?(opts, &1)) do
      [] ->
        :ok

      offending ->
        raise ArgumentError,
              "#{inspect(offending)} is pinned in KeosQwen.Provider and cannot be " <>
                "overridden by a caller. The destination is a compiled constant " <>
                "precisely because a configurable one was measured silently losing " <>
                "to Anthropic on 2026-09-24."
    end
  end

  defp consult_ledger(opts) do
    script = Keyword.get(opts, :ledger_script, @ledger_script)
    root = Keyword.get(opts, :ledger_root, ledger_root())

    try do
      case System.cmd(@ledger_python, [script, "decide", "--root", root],
             stderr_to_stdout: true) do
        {out, @ledger_allow} ->
          {:ok, out}

        {out, @ledger_refused} ->
          {code, reason} = parse_refusal(out)
          {:refused, code, reason}

        {out, @ledger_unreadable} ->
          {:unavailable, "the ledger could not answer: #{String.trim(out)}"}

        {out, other} ->
          # An exit code we have not seen. Not a licence.
          {:unavailable,
           "ledger exited #{other}, which is not one of its declared outcomes " <>
             "(#{@ledger_allow}/#{@ledger_refused}/#{@ledger_unreadable}): #{String.trim(out)}"}
      end
    rescue
      e in ErlangError ->
        {:unavailable,
         "could not run the ledger (#{@ledger_python} #{script}): #{inspect(e.original)}. " <>
           "Failing closed: an unconsultable budget does not authorise spend."}
    end
  end

  # Extracted with a pattern rather than a JSON decoder, deliberately. A decoder
  # would make the refusal CODE depend on a library being loaded in whatever
  # application hosts us -- and then a missing dependency would surface as
  # "UNPARSEABLE" and read exactly like a ledger that answered something we do
  # not understand. The producer is our own CLI with a fixed shape, so a pattern
  # over it has no dependency and cannot fail for a reason unrelated to spend.
  @verdict_re ~r/"verdict"\s*:\s*"([A-Z_]+)"/
  @reason_re ~r/"reason"\s*:\s*"((?:[^"\\]|\\.)*)"/

  defp parse_refusal(out) do
    trimmed = String.trim(out)

    code =
      case Regex.run(@verdict_re, trimmed) do
        [_, v] -> v
        _ -> "UNPARSEABLE"
      end

    reason =
      case Regex.run(@reason_re, trimmed) do
        [_, r] -> r
        _ -> trimmed
      end

    {code, reason}
  end

  defp record(result, opts) do
    script = Keyword.get(opts, :ledger_script, @ledger_script)
    root = Keyword.get(opts, :ledger_root, ledger_root())

    {outcome, detail} =
      case result do
        {:ok, msg} ->
          {local, server} = served_by(msg)
          {if(local == :local, do: "OK", else: "HARNESS_FAILED"), "served_by=#{server}"}

        {:error, reason} ->
          {"UNAVAILABLE", inspect(reason) |> String.slice(0, 400)}

        other ->
          {"HARNESS_FAILED", inspect(other) |> String.slice(0, 400)}
      end

    _ =
      try do
        System.cmd(@ledger_python,
          [script, "record", "--root", root, "--caller", @caller,
           "--outcome", outcome, "--detail", detail], stderr_to_stdout: true)
      rescue
        _ -> :could_not_record
      end

    :ok
  end

  @doc """
  Did this response come from our own endpoint?

  Answered from the response's own headers, not from what we intended to send.
  Three outcomes, because a response with no headers proves nothing about where
  it came from and must not read as a pass.
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
