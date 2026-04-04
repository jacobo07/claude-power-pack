"""
Kobii Infrastructure — Unified VPS System Query.
Checks health and status of all Elixir projects + services on VPS.

stdlib only — no external dependencies.

Usage:
    python query_infra.py --status          # All systems health
    python query_infra.py --aadef           # AADEF Engine compile + tests
    python query_infra.py --resilience      # KobiiClaw Resilience stats
    python query_infra.py --omnicapture     # OmniCapture telemetry health
    python query_infra.py --lightning       # Agent Lightning trace stats
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = MODULE_DIR / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def ssh_cmd(command: str, timeout: int = 30) -> tuple[int, str]:
    """Run a command on VPS via SSH."""
    config = load_config()
    host = config.get("vps_host", "204.168.166.63")
    user = config.get("vps_user", "kobicraft")
    key = config.get("ssh_key", os.path.expanduser("~/.ssh/kobicraft_vps"))

    full_cmd = ["ssh", "-i", key, "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                f"{user}@{host}", command]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT: VPS did not respond within timeout"
    except FileNotFoundError:
        return 1, "ERROR: SSH client not found"
    except Exception as e:
        return 1, f"ERROR: {e}"


def cmd_status():
    """Check all systems."""
    print("=== KOBII INFRASTRUCTURE STATUS ===\n")

    # OmniCapture
    code, out = ssh_cmd("curl -s http://localhost:9876/api/v1/health 2>/dev/null || echo OFFLINE")
    if "healthy" in out:
        print("OmniCapture (9876):     HEALTHY")
    else:
        print(f"OmniCapture (9876):     OFFLINE — {out[:80]}")

    # Agent Lightning
    code, out = ssh_cmd("curl -s http://localhost:9878/health 2>/dev/null || echo OFFLINE")
    if "healthy" in out:
        print("Agent Lightning (9878): HEALTHY")
    else:
        print(f"Agent Lightning (9878): OFFLINE — {out[:80]}")

    # AADEF
    code, out = ssh_cmd("source ~/.asdf/asdf.sh && cd /home/kobicraft/workspace/aadef_engine && mix test 2>&1 | grep -E 'tests|failure'", timeout=60)
    if "0 failures" in out:
        print(f"AADEF Engine:           PASSING ({out.strip()})")
    else:
        print(f"AADEF Engine:           ISSUE — {out[:80]}")

    # OSA
    code, out = ssh_cmd("source ~/.asdf/asdf.sh && cd /home/kobicraft/workspace/osa-integrated && mix test test/governance/ 2>&1 | grep -E 'tests|failure'", timeout=60)
    if "0 failures" in out:
        print(f"OSA Governance:         PASSING ({out.strip()})")
    else:
        print(f"OSA Governance:         ISSUE — {out[:80]}")

    # Resilience
    code, out = ssh_cmd("source ~/.asdf/asdf.sh && cd /home/kobicraft/workspace/kobiiclaw_resilience && mix test 2>&1 | grep -E 'tests|failure'", timeout=60)
    if "0 failures" in out:
        print(f"KobiiClaw Resilience:   PASSING ({out.strip()})")
    else:
        print(f"KobiiClaw Resilience:   ISSUE — {out[:80]}")

    print()


def cmd_aadef():
    """AADEF Engine details."""
    print("=== AADEF ENGINE ===\n")
    code, out = ssh_cmd("source ~/.asdf/asdf.sh && cd /home/kobicraft/workspace/aadef_engine && mix compile --warnings-as-errors 2>&1 | tail -1 && echo '---' && mix test 2>&1 | tail -5", timeout=120)
    print(out)


def cmd_resilience():
    """KobiiClaw Resilience details."""
    print("=== KOBIICLAW RESILIENCE ===\n")
    code, out = ssh_cmd("source ~/.asdf/asdf.sh && cd /home/kobicraft/workspace/kobiiclaw_resilience && mix test 2>&1 | tail -5 && echo '---' && curl -s http://localhost:9878/api/v1/traces/stats 2>/dev/null", timeout=120)
    print(out)


def cmd_omnicapture():
    """OmniCapture health."""
    print("=== OMNICAPTURE ===\n")
    code, out = ssh_cmd("curl -s http://localhost:9876/api/v1/health 2>/dev/null")
    try:
        data = json.loads(out)
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print(out)


def cmd_lightning():
    """Agent Lightning stats."""
    print("=== AGENT LIGHTNING ===\n")
    code, out = ssh_cmd("curl -s http://localhost:9878/api/v1/traces/stats 2>/dev/null")
    try:
        data = json.loads(out)
        print(f"Total traces:  {data.get('total_traces', 0)}")
        print(f"Sessions:      {data.get('sessions', 0)}")
        print(f"Rewards:       {data.get('rewards', 0)}")
        print(f"Avg reward:    {data.get('avg_reward', 'N/A')}")
        tools = data.get('top_tools', [])
        if tools:
            print("\nTop tools:")
            for t in tools:
                print(f"  {t['tool']:15s} {t['count']} calls")
    except json.JSONDecodeError:
        print(out)


def main():
    parser = argparse.ArgumentParser(description="Kobii Infrastructure Query")
    parser.add_argument("--status", action="store_true", help="All systems health check")
    parser.add_argument("--aadef", action="store_true", help="AADEF Engine details")
    parser.add_argument("--resilience", action="store_true", help="KobiiClaw Resilience stats")
    parser.add_argument("--omnicapture", action="store_true", help="OmniCapture health")
    parser.add_argument("--lightning", action="store_true", help="Agent Lightning stats")
    args = parser.parse_args()

    if args.aadef:
        cmd_aadef()
    elif args.resilience:
        cmd_resilience()
    elif args.omnicapture:
        cmd_omnicapture()
    elif args.lightning:
        cmd_lightning()
    else:
        cmd_status()


if __name__ == "__main__":
    main()
