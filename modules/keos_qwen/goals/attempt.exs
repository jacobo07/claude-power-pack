# One attempt at one goal, against the pinned local model. Run as:
#
#   elixir attempt.exs          (prompt read from $KEOS_PROMPT_FILE)
#
# Emits EXACTLY ONE line beginning with the sentinel KEOSQ_ATTEMPT, followed by
# a JSON object. Everything else this process prints is noise and the caller
# discards it.
#
# The sentinel is not decoration. Measured on GEX44 2026-09-25, a single call
# interleaves the answer with, on stdout and stderr:
#
#   [error] Exqlite.Connection ... failed to connect: You must provide a
#           :database to the database
#   [debug] [ToolRegistry] Initialized with 39 built-in tool(s): ...
#   [debug] [Router] create_message via ollama
#   [debug] [OpenAI] POST http://127.0.0.1:8081/v1/chat/completions model=gpt-4o
#
# A caller that parsed "the last line" or "the first JSON-looking thing" would be
# reading the harness's diagnostics and calling them a result. The sentinel is
# how the answer is told apart from the log.
#
# THE JSON IS BUILT BY HAND, not by Jason, for the same reason the provider
# parses refusals with a regex: a decoder makes the RESULT depend on a library
# being loaded, and then a missing dependency surfaces as a malformed attempt
# and reads exactly like a model that answered garbage.

defmodule Emit do
  # Minimal, total JSON string escaping. Total matters: a model reply is
  # arbitrary text and will eventually contain a quote, a newline and a
  # backslash in the same sentence.
  def esc(s) when is_binary(s) do
    s
    |> String.replace("\\", "\\\\")
    |> String.replace("\"", "\\\"")
    |> String.replace("\n", "\\n")
    |> String.replace("\r", "\\r")
    |> String.replace("\t", "\\t")
    |> String.graphemes()
    |> Enum.map_join(fn g ->
      case :binary.first(g) do
        c when is_integer(c) and c < 0x20 -> "\\u" <> String.pad_leading(Integer.to_string(c, 16), 4, "0")
        _ -> g
      end
    end)
  end

  def esc(other), do: esc(inspect(other))

  def line(pairs) do
    body = Enum.map_join(pairs, ",", fn {k, v} -> "\"#{k}\":#{v}" end)
    IO.puts("KEOSQ_ATTEMPT {" <> body <> "}")
  end

  def str(s), do: "\"" <> esc(s) <> "\""
end

prompt_file = System.get_env("KEOS_PROMPT_FILE")
goal_id = System.get_env("KEOS_GOAL_ID") || "unknown"
max_tokens = String.to_integer(System.get_env("KEOS_MAX_TOKENS") || "1024")

cond do
  is_nil(prompt_file) ->
    Emit.line([{"outcome", Emit.str("HARNESS_FAILED")}, {"goal", Emit.str(goal_id)},
               {"reason", Emit.str("KEOS_PROMPT_FILE is not set")}])
    System.halt(1)

  not File.exists?(prompt_file) ->
    Emit.line([{"outcome", Emit.str("HARNESS_FAILED")}, {"goal", Emit.str(goal_id)},
               {"reason", Emit.str("no prompt at " <> prompt_file)}])
    System.halt(1)

  true ->
    prompt = File.read!(prompt_file)
    t0 = System.monotonic_time(:millisecond)

    {:ok, _} = Application.ensure_all_started(:claude_code)

    result =
      KeosQwen.Provider.ask(prompt,
        ledger_script: System.get_env("KEOS_QWEN_LEDGER_SCRIPT"),
        ledger_root: System.get_env("KEOS_QWEN_LEDGER_ROOT"),
        max_tokens: max_tokens)

    ms = System.monotonic_time(:millisecond) - t0
    base = [{"goal", Emit.str(goal_id)}, {"wall_ms", Integer.to_string(ms)}]

    case result do
      {:ok, m} ->
        text = m |> Map.get(:content, []) |> Enum.map(&Map.get(&1, :text, "")) |> Enum.join()
        {where, server} = KeosQwen.Provider.served_by(m)

        # Where the response came from decides the OUTCOME, not just a label.
        # A remote answer is not a better answer: it is an egress event, and
        # counting it as OK would put another provider's text into the corpus
        # this whole programme exists to build from the LOCAL model. T-KEOSQ-02.
        outcome = if where == :local, do: "OK", else: "HARNESS_FAILED"

        Emit.line(base ++ [
          {"outcome", Emit.str(outcome)},
          {"served_by", Emit.str(to_string(where))},
          {"server", Emit.str(to_string(server))},
          {"model", Emit.str(to_string(Map.get(m, :model)))},
          {"stop_reason", Emit.str(to_string(Map.get(m, :stop_reason)))},
          {"text", Emit.str(text)}
        ])

        System.halt(if outcome == "OK", do: 0, else: 1)

      {:refused, code, why} ->
        Emit.line(base ++ [{"outcome", Emit.str("UNAVAILABLE")},
                           {"refused", Emit.str(code)}, {"reason", Emit.str(why)}])
        System.halt(3)

      {:unavailable, why} ->
        Emit.line(base ++ [{"outcome", Emit.str("HARNESS_FAILED")},
                           {"reason", Emit.str("could not consult the ledger: " <> why)}])
        System.halt(4)

      {:error, why} ->
        Emit.line(base ++ [{"outcome", Emit.str("UNAVAILABLE")},
                           {"reason", Emit.str(inspect(why))}])
        System.halt(1)

      other ->
        Emit.line(base ++ [{"outcome", Emit.str("HARNESS_FAILED")},
                           {"reason", Emit.str("unrecognised provider return: " <> inspect(other))}])
        System.halt(1)
    end
end
