# V-gates for KeosQwen.Provider -- run with:  mix run gate_provider.exs
#
# Two properties, each with its discriminating control.
#
# DESTINATION: V-KEOSQ-PIN-BEATS-ENV is the one that matters. Everything else
# could pass against a module that happened to be pointed at the right place
# today; only deliberately setting the environment variables that WOULD have
# redirected the request, and still landing on llama.cpp, proves the destination
# is pinned rather than merely correct.
#
# SPEND: the ledger's three answers must be distinguishable from each other, not
# merely from success. "Refused", "could not ask" and "the model failed" send an
# operator to three different fixes, and a gate that only checked "not {:ok, _}"
# would pass against a module that collapsed all three.
#
# The credential value used below is deliberately not key-shaped. An earlier
# revision used a literal beginning with the real vendor prefix; the repo's
# secret scanner refused it, correctly, because a pattern matcher cannot know a
# key is fake and "it is only a test value" is what a real leak would also say.
# The router checks PRESENCE, not shape, so a value that resembles nothing
# proves the property just as well.

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

defmodule Tmp do
  def dir(tag) do
    p = Path.join(System.tmp_dir!(), "keosq_gate_#{tag}_#{System.unique_integer([:positive])}")
    File.mkdir_p!(p)
    p
  end
end

Gate.start()

script = System.get_env("KEOS_LEDGER_SCRIPT") || "/home/kobii/keos/keos_qwen/ledger/ledger.py"
IO.puts("  (ledger script: #{script}, exists=#{File.exists?(script)})")

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
  match?({:remote, _},
    KeosQwen.Provider.served_by(%{__headers__: %{"cf-ray" => ["x"], "server" => ["cloudflare"]}})),
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

# --- the wire, metered against an isolated ledger ----------------------------
wire_root = Tmp.dir("wire")
common = [ledger_script: script, ledger_root: wire_root, max_tokens: 64]

case KeosQwen.Provider.ask("Reply with exactly the word PONG and nothing else.", common) do
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

calls = Path.join(wire_root, "calls.jsonl")
lines = if File.exists?(calls), do: File.read!(calls) |> String.split("\n", trim: true), else: []

Gate.check("V-KEOSQ-LEDGER-RECORDS-THE-CALL", length(lines) == 1,
  "exactly one call was recorded AFTER the effect: #{inspect(List.first(lines))}",
  "expected 1 recorded call, found #{length(lines)}")

# --- THE ONE THAT PROVES PINNING, NOT LUCK -----------------------------------
System.put_env("CLAUDE_CODE_API_PROVIDER", "anthropic")
System.put_env("ANTHROPIC_API_KEY", "set-for-this-gate-and-never-used")

case KeosQwen.Provider.ask("Reply with exactly the word PONG and nothing else.",
       [ledger_script: script, ledger_root: Tmp.dir("pin"), max_tokens: 64]) do
  {:ok, msg} ->
    Gate.check("V-KEOSQ-PIN-BEATS-ENV", match?({:local, _}, KeosQwen.Provider.served_by(msg)),
      "still local with CLAUDE_CODE_API_PROVIDER=anthropic and ANTHROPIC_API_KEY set: " <>
        "the destination is pinned, not merely configured",
      "the environment redirected us to #{inspect(KeosQwen.Provider.served_by(msg))}")

  other ->
    Gate.bad("V-KEOSQ-PIN-BEATS-ENV", "the call failed once the env was set: #{inspect(other)}")
end

System.delete_env("CLAUDE_CODE_API_PROVIDER")
System.delete_env("ANTHROPIC_API_KEY")

# --- spend: three answers that are not each other ----------------------------
kill_root = Tmp.dir("kill")
File.write!(Path.join(kill_root, "DISABLED"), "the gate set this flag on purpose")

refusal = KeosQwen.Provider.ask("this must never reach the model",
            ledger_script: script, ledger_root: kill_root)

Gate.check("V-KEOSQ-LEDGER-REFUSES",
  match?({:refused, "DISABLED_FLAG", _}, refusal),
  "the flag file refuses BY ITS OWN CODE, not as a generic error: #{inspect(refusal)}",
  "expected {:refused, \"DISABLED_FLAG\", _}, got #{inspect(refusal)}")

Gate.check("V-KEOSQ-REFUSED-SPENDS-NOTHING",
  not File.exists?(Path.join(kill_root, "calls.jsonl")),
  "a refused call recorded nothing: the model was never reached",
  "a refused call still wrote to the ledger")

Gate.check("V-KEOSQ-REFUSED-IS-NOT-ERROR",
  not match?({:error, _}, refusal) and not match?({:ok, _}, refusal),
  "a refusal is distinguishable from a model failure and from success -- three " <>
    "outcomes, three different fixes",
  "a refusal was shaped like something else: #{inspect(refusal)}")

unavailable = KeosQwen.Provider.ask("this must never reach the model",
                ledger_script: "/nonexistent/ledger_that_is_not_there.py",
                ledger_root: Tmp.dir("gone"))

Gate.check("V-KEOSQ-LEDGER-UNAVAILABLE-FAILS-CLOSED",
  match?({:unavailable, _}, unavailable),
  "an unconsultable ledger refuses the call rather than licensing it: an " <>
    "unreadable budget must not authorise unbounded spend on a host carrying " <>
    "15 production services",
  "expected {:unavailable, _}, got #{inspect(unavailable)}")

Gate.check("V-KEOSQ-UNAVAILABLE-IS-NOT-REFUSED",
  not match?({:refused, _, _}, unavailable),
  "'we could not ask' is kept apart from 'we were told no': only one of them is " <>
    "fixed by waiting, and only one by repairing a path",
  "could-not-ask was reported as a refusal: #{inspect(unavailable)}")

# --- a caller may not redirect, but may still tune ---------------------------
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
  KeosQwen.Provider.ask("hello",
    ledger_script: script, ledger_root: Tmp.dir("tune"), max_tokens: 8)

  Gate.ok("V-KEOSQ-CALLER-MAY-TUNE",
    "a non-pinned option is still accepted (admitted control: a guard that " <>
      "refused every option would pass the assertion above for the wrong reason)")
rescue
  e in ArgumentError ->
    Gate.bad("V-KEOSQ-CALLER-MAY-TUNE", "refused a legitimate option: #{e.message}")
end

System.halt(Gate.tally())
