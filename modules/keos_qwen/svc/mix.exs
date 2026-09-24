defmodule KeosQwen.MixProject do
  use Mix.Project

  # The harness is a LIBRARY here, not an application we run. Its provider layer
  # was proven against our llama-server on 2026-09-24; its SDK session layer was
  # measured dropping the provider option and egressing to Anthropic, so we do
  # not enter through it. See lib/keos_qwen/provider.ex.
  #
  # KEOS_HARNESS_PATH exists because this project is authored inside the Power
  # Pack repo and deployed beside the harness on GEX44; the two trees are not in
  # the same relative position. The default is the deployed layout.
  @harness_path System.get_env("KEOS_HARNESS_PATH") || "../osa-claude-code"

  def project do
    [
      app: :keos_qwen,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [extra_applications: [:logger]]
  end

  defp deps do
    [{:claude_code, path: @harness_path}]
  end
end
