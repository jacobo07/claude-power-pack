"""
Agent Lightning — Query Client for Claude Code.
Queries the VPS trace receiver for optimization results, stats, and patterns.

stdlib only — no external dependencies.

Usage:
    python query_lightning.py --suggestions
    python query_lightning.py --patterns
    python query_lightning.py --model-stats
    python query_lightning.py --trace-stats
    python query_lightning.py --train
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_api_key(config: dict) -> str | None:
    env_var = config.get("api_key_env", "OMNICAPTURE_API_KEY")
    return os.environ.get(env_var)


def api_get(config: dict, endpoint: str) -> dict | None:
    base_url = config.get("vps_url", "http://204.168.166.63:9878")
    url = f"{base_url}{endpoint}"
    api_key = get_api_key(config)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach VPS — {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return None


def api_post(config: dict, endpoint: str, body: dict = None) -> dict | None:
    base_url = config.get("vps_url", "http://204.168.166.63:9878")
    url = f"{base_url}{endpoint}"
    api_key = get_api_key(config)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return None


def cmd_trace_stats(config: dict):
    data = api_get(config, "/api/v1/traces/stats")
    if not data:
        return

    print("=== Agent Lightning Trace Stats ===")
    print(f"Total traces:  {data.get('total_traces', 0)}")
    print(f"Sessions:      {data.get('sessions', 0)}")
    print(f"Rewards:       {data.get('rewards', 0)}")
    print(f"Avg reward:    {data.get('avg_reward', 'N/A')}")
    print(f"Date range:    {data.get('earliest', '?')} → {data.get('latest', '?')}")

    top_tools = data.get("top_tools", [])
    if top_tools:
        print("\nTop tools:")
        for t in top_tools:
            print(f"  {t['tool']:15s} {t['count']} calls")


def cmd_suggestions(config: dict):
    data = api_get(config, "/api/v1/optimizations")
    if not data:
        return

    suggestions = data.get("suggestions", [])
    if not suggestions:
        needed = data.get("min_traces_needed", 50)
        current = data.get("current_traces", 0)
        print(f"No suggestions yet. Need {needed} traces, have {current}.")
        return

    print("=== APO Suggestions ===")
    for s in suggestions:
        conf = s.get("confidence", 0)
        badge = "AUTO" if conf >= 0.9 else "REVIEW" if conf >= 0.7 else "LOW"
        print(f"\n[{badge}] {s.get('type', 'unknown')} (confidence: {conf:.0%})")
        print(f"  {s.get('content', s.get('description', ''))}")
        print(f"  Based on {s.get('based_on_traces', '?')} traces")


def cmd_patterns(config: dict):
    data = api_get(config, "/api/v1/optimizations")
    if not data:
        return

    patterns = data.get("anti_patterns", [])
    if not patterns:
        print("No anti-patterns discovered yet.")
        return

    print("=== Discovered Anti-Patterns ===")
    for p in patterns:
        print(f"\n- {p.get('description', '?')}")
        print(f"  Occurrences: {p.get('occurrences', '?')}")
        print(f"  Confidence: {p.get('confidence', 0):.0%}")


def cmd_model_stats(config: dict):
    data = api_get(config, "/api/v1/optimizations")
    if not data:
        return

    routing = data.get("model_routing", {})
    if not routing:
        print("No model routing data yet. Need more traces with model info.")
        return

    print("=== Model Routing Stats ===")
    for model, stats in routing.items():
        print(f"\n{model}:")
        print(f"  Success rate: {stats.get('success_rate', '?')}")
        print(f"  Avg cost:     {stats.get('avg_cost', '?')}")
        print(f"  Tasks:        {stats.get('task_count', '?')}")


def cmd_train(config: dict):
    print("Triggering APO training run...")
    data = api_post(config, "/api/v1/optimizations/train")
    if data:
        print(f"Result: {json.dumps(data, indent=2)}")
    else:
        print("Training trigger failed or endpoint not yet available (Phase 3).")


def main():
    parser = argparse.ArgumentParser(description="Agent Lightning Query Client")
    parser.add_argument("--suggestions", action="store_true", help="Show APO suggestions")
    parser.add_argument("--patterns", action="store_true", help="Show discovered anti-patterns")
    parser.add_argument("--model-stats", action="store_true", help="Show model routing stats")
    parser.add_argument("--trace-stats", action="store_true", help="Show trace collection stats")
    parser.add_argument("--train", action="store_true", help="Trigger manual APO run")
    args = parser.parse_args()

    config = load_config()

    if args.suggestions:
        cmd_suggestions(config)
    elif args.patterns:
        cmd_patterns(config)
    elif args.model_stats:
        cmd_model_stats(config)
    elif args.trace_stats:
        cmd_trace_stats(config)
    elif args.train:
        cmd_train(config)
    else:
        cmd_trace_stats(config)


if __name__ == "__main__":
    main()
