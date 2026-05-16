r"""
lazarus_topology_push_vps.py - MC-LAZ-36-A scoped VPS push.

Local-side only. Pushes the latest topology snapshot JSON to KobiiClaw
VPS via scp using the kobicraft_vps SSH key (per CLAUDE.md key map: the
GEX44 key is reserved for KobiiCraft / KobiiSports / video work).

VPS-side suggestion engine (KobiiClaw "rebuild this layout?" prompt) is
DEFERRED -- it requires a VPS daemon and topology-aware UI work that
cannot ship in one local turn without phantom-scaffolding.

Conditional: SSH unreachable -> log and exit 0 (don't fail downstream
verification). Reachable -> scp the file and emit a receipt.

Usage:
  python tools/lazarus_topology_push_vps.py
  python tools/lazarus_topology_push_vps.py --host kobicraft@204.168.166.63
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HOST = "kobicraft@204.168.166.63"
DEFAULT_KEY = Path(os.path.expanduser("~/.ssh/kobicraft_vps"))
DEFAULT_REMOTE_DIR = "~/lazarus_topology"
LOCAL_LATEST = Path(os.path.expanduser("~/.claude/lazarus/topology/topology_latest.json"))
RECEIPTS_LOG = Path(os.path.expanduser("~/.claude/lazarus/topology/vps_push_receipts.jsonl"))


def _record_receipt(payload: dict) -> None:
    RECEIPTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPTS_LOG.open("a", encoding="utf-8") as h:
        h.write(json.dumps(payload, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(prog="lazarus_topology_push_vps")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--key", default=str(DEFAULT_KEY))
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument(
        "--probe-timeout",
        type=int,
        default=5,
        help="seconds to wait for SSH probe before falling back to no-op",
    )
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    receipt = {"ts": ts, "host": args.host, "outcome": None, "detail": None}

    if not LOCAL_LATEST.is_file():
        receipt["outcome"] = "no-snapshot"
        receipt["detail"] = f"missing {LOCAL_LATEST}"
        _record_receipt(receipt)
        print(json.dumps(receipt, indent=2))
        return 0

    if shutil.which("ssh") is None or shutil.which("scp") is None:
        receipt["outcome"] = "no-ssh-tooling"
        _record_receipt(receipt)
        print(json.dumps(receipt, indent=2))
        return 0

    if not Path(args.key).is_file():
        receipt["outcome"] = "no-ssh-key"
        receipt["detail"] = f"missing {args.key}"
        _record_receipt(receipt)
        print(json.dumps(receipt, indent=2))
        return 0

    probe = subprocess.run(
        [
            "ssh",
            "-i",
            args.key,
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={args.probe_timeout}",
            "-o",
            "StrictHostKeyChecking=accept-new",
            args.host,
            "true",
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        receipt["outcome"] = "vps-unreachable"
        receipt["detail"] = (probe.stderr or probe.stdout or "no output").strip()[:200]
        _record_receipt(receipt)
        print(json.dumps(receipt, indent=2))
        return 0

    mkdir = subprocess.run(
        [
            "ssh",
            "-i",
            args.key,
            "-o",
            "BatchMode=yes",
            args.host,
            f"mkdir -p {args.remote_dir}",
        ],
        capture_output=True,
        text=True,
    )
    if mkdir.returncode != 0:
        receipt["outcome"] = "remote-mkdir-failed"
        receipt["detail"] = (mkdir.stderr or "").strip()[:200]
        _record_receipt(receipt)
        print(json.dumps(receipt, indent=2))
        return 1

    remote_target = f"{args.host}:{args.remote_dir}/topology_latest.json"
    push = subprocess.run(
        [
            "scp",
            "-i",
            args.key,
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            str(LOCAL_LATEST),
            remote_target,
        ],
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        receipt["outcome"] = "scp-failed"
        receipt["detail"] = (push.stderr or "").strip()[:200]
        _record_receipt(receipt)
        print(json.dumps(receipt, indent=2))
        return 1

    receipt["outcome"] = "pushed"
    receipt["detail"] = remote_target
    receipt["bytes"] = LOCAL_LATEST.stat().st_size
    _record_receipt(receipt)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
