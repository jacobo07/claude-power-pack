# V-gates for KeosQwen.Provider -- run with:  mix run gate_provider.exs
#
# The gate that matters is V-KEOSQ-PIN-BEATS-ENV. Everything else could pass
# against a module that simply happened to be pointed at the right place today;
# only deliberately setting the environment variables that WOULD have redirected
# the request, and still landing on llama.cpp, proves the destination is pinned
# rather than merely correct. Measured 2026-09-24: CLAUDE_CODE_API_PROVIDER is
# priority 2 in the harness's own selection chain and OLLAMA_HOST is priority 8,
# so an env-configured destination loses to six other variables.

defmodule Gate do
  def start, do: Agent.start_link(fn -> {[], []} end, name: __MODULE__)

  def ok(g, ev) do
    Agent.update(__MODULE__, fn {p, f} -> {[g | p], f} end)
    IO.puts("  PASS #{g}: #{ev}")
  end

  def bad(g, why) do
    Agent.update(__MODULE__, fn {p, f} -> {p, [g | f]} end)
    IO.puts("  FAIL #{g}: #{why}")
  end

  def check(g, true, ev, _why), do: ok(g, ev)
  def check(g, _cond, _ev, why), do: bad(g, why)

  def tally do
    {p, f} = Agent.get(__MODULE__, & &1)
    total = length(p) + length(f)
    IO.puts("\nKEOSQ_PROVIDER_PASS=#{length(p)}/#{total}  threshold=#{total}/#{total}")
    if f == [], do: 0, else: 1
  end
end

Gate.start()

pin = KeosQwen.Provider.pinned()
Gate.check(
  "V-KEOSQ-PIN-DECLARED",
  pin.provider == :ollama and pin.model == "qwen3-coder-30b" and
    pin.base_url == "http://127.0.0.1:8081",
  "the destination is readable: #{inspect(pin)}",
  "unexpected pin: #{inspect(pin)}"
)

# --- the detector's own poles, before trusting it about anything -------------
Gate.check(
  "V-KEOSQ-DETECTOR-REMOTE",
  match?({:remote, _}, KeosQwen.Provider.served_by(%{__headers__: %{"cf-ray" => ["x"], "server" => ["cloudflare"]}})),
  "a Cloudflare-fronted response is detected as remote (red pole: without this, " <>
    "a served_by that always answered :local would pass every assertion below)",
  "remote headers were not detected as remote"
)

Gate.check(
  "V-KEOSQ-DETECTOR-UNKNOWN",
  match?({:unknown, _}, KeosQwen.Provider.served_by(%{__headers__: %{}})),
  "a response with no headers is unknown, not local",
  "an empty header map was not reported as unknown"
)

# --- the wire ----------------------------------------------------------------
case KeosQwen.Provider.ask("Reply with exactly the word PONG and nothing else.", max_tokens: 64) do
  {:ok, msg} ->
    text = msg |> Map.get(:content, []) |> Enum.map(&Map.get(&1, :text, "")) |> Enum.join()
    Gate.check("V-KEOSQ-WIRE-ANSWERS", String.contains?(String.upcase(text), "PONG"),
      "the pinned model answered: #{inspect(text)}", "unexpected content: #{inspect(text)}")

    Gate.check("V-KEOSQ-WIRE-MODEL", Map.get(msg, :model) == pin.model,
      "the response names the pinned model", "model was #{inspect(Map.get(msg, :model))}")

    Gate.check("V-KEOSQ-WIRE-LOCAL", match?({:local, _}, KeosQwen.Provider.served_by(msg)),
      "served by #{inspect(KeosQwen.Provider.served_by(msg))} -- our endpoint, zero egress",
      "served by #{inspect(KeosQwen.Provider.served_by(msg))}")

  other ->
    Gate.bad("V-KEOSQ-WIRE-ANSWERS", "the call did not return {:ok, _}: #{inspect(other)}")
end

# --- THE ONE THAT PROVES PINNING, NOT LUCK -----------------------------------
System.put_env("CLAUDE_CODE_API_PROVIDER", "anthropic")
System.put_env("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key-for-the-gate")

case KeosQwen.Provider.ask("Reply with exactly the word PONG and nothing else.", max_tokens: 64) do
  {:ok, msg} ->
    Gate.check("V-KEOSQ-PIN-BEATS-ENV", match?({:local, _}, KeosQwen.Provider.served_by(msg)),
      "still local with CLAUDE_CODE_API_PROVIDER=anthropic and an ANTHROPIC_API_KEY set: " <>
        "the destination is pinned, not merely configured",
      "the environment redirected us to #{inspect(KeosQwen.Provider.served_by(msg))}")

  other ->
    Gate.bad("V-KEOSQ-PIN-BEATS-ENV", "the call failed once the env was set: #{inspect(other)}")
end

System.delete_env("CLAUDE_CODE_API_PROVIDER")
System.delete_env("ANTHROPIC_API_KEY")

# --- a caller may not redirect either ----------------------------------------
try do
  KeosQwen.Provider.ask("hello", provider: :anthropic)
  Gate.bad("V-KEOSQ-CALLER-CANNOT-OVERRIDE", "a caller-supplied :provider was accepted")
rescue
  e in ArgumentError ->
    Gate.check("V-KEOSQ-CALLER-CANNOT-OVERRIDE", String.contains?(e.message, "pinned"),
      "a caller-supplied :provider raises instead of being silently ignored",
      "raised, but not with the pinning reason: #{e.message}")
end

try do
  KeosQwen.Provider.ask("hello", max_tokens: 8)
  Gate.ok("V-KEOSQ-CALLER-MAY-TUNE",
    "a non-pinned option is still accepted (admitted control: a guard that " <>
      "refused every option would pass the assertion above for the wrong reason)")
rescue
  e in ArgumentError -> Gate.bad("V-KEOSQ-CALLER-MAY-TUNE", "refused a legitimate option: #{e.message}")
end

System.halt(Gate.tally())
