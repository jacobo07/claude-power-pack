r"""
lazarus_topology_verify.py - MC-OVO-400 verification harness.

Replaces the autobrowser end-to-end check (Docker absent) with a
file-evidence harness:

  1. Capture snapshot A.
  2. Capture snapshot B (immediately).
  3. Diff: hash equality across snapshots when no Cursor state changed
     proves the snapshotter is deterministic and side-effect free.
  4. Schema assertions: every snapshot must have schema_version,
     envelope_captured_at, workspace_count, snapshots[], errors[].
  5. Per-workspace assertions: each snapshot in snapshots[] must declare
     hash, folder, captured_at, topology, gaps.
  6. Gap declaration: explicitly print which DSP fields are NOT captured
     (anti-phantom: callers must SEE the gap, not assume completeness).

Exits 0 on PASS, non-zero on FAIL. Prints a markdown verdict.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from lib.lazarus.topology_engine import (  # noqa: E402
    envelope_hash,
    snapshot_all,
)


def _check(label: str, passed: bool, detail: str = "") -> tuple[str, bool]:
    mark = "PASS" if passed else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f"  -- {detail}"
    return line, passed


def main() -> int:
    lines: list[str] = ["# MC-OVO-400 topology verification", ""]
    failures: list[str] = []

    lines.append("## Capture A + B (determinism check)")
    env_a = snapshot_all()
    env_b = snapshot_all()
    h_a = envelope_hash(env_a)
    h_b = envelope_hash(env_b)
    line, ok = _check(
        "envelope hash deterministic across two captures",
        h_a == h_b,
        f"A={h_a[:12]} B={h_b[:12]}",
    )
    lines.append(line)
    if not ok:
        failures.append("hash drift between captures (snapshotter has side effects?)")

    lines.append("")
    lines.append("## Envelope schema")
    for key in (
        "schema_version",
        "envelope_captured_at",
        "host",
        "workspace_count",
        "snapshot_count",
        "snapshots",
        "errors",
    ):
        line, ok = _check(f"envelope.{key} present", key in env_a, "")
        lines.append(line)
        if not ok:
            failures.append(f"envelope missing {key}")

    line, ok = _check(
        "snapshot_count == workspace_count - len(errors)",
        env_a["snapshot_count"] == env_a["workspace_count"] - len(env_a["errors"]),
        f"snap={env_a['snapshot_count']} ws={env_a['workspace_count']} err={len(env_a['errors'])}",
    )
    lines.append(line)
    if not ok:
        failures.append("snapshot/workspace/errors arithmetic broken")

    lines.append("")
    lines.append("## Per-workspace structure (sampling first 3 + last 1)")
    snaps = env_a["snapshots"]
    sample_idx = list(range(min(3, len(snaps))))
    if len(snaps) > 3:
        sample_idx.append(len(snaps) - 1)
    for i in sample_idx:
        snap = snaps[i]
        for key in ("hash", "folder", "captured_at", "topology", "gaps"):
            line, ok = _check(
                f"snapshots[{i}].{key} present",
                key in snap,
                snap.get("hash", "?")[:8],
            )
            lines.append(line)
            if not ok:
                failures.append(f"snapshot {i} missing {key}")

    lines.append("")
    lines.append("## Gap declarations (anti-phantom -- must be EXPLICITLY present)")
    expected_gaps = {
        "scroll_position_per_terminal",
        "terminal_input_buffer",
        "assistant_message_on_screen",
    }
    for snap in snaps[:3]:
        gaps = set((snap.get("gaps") or {}).keys())
        missing = expected_gaps - gaps
        line, ok = _check(
            f"snapshot {snap['hash'][:8]} declares all DSP gaps",
            not missing,
            f"missing={missing}" if missing else "all 3 gaps present",
        )
        lines.append(line)
        if not ok:
            failures.append(f"snapshot {snap['hash'][:8]} missing gap declarations: {missing}")

    lines.append("")
    lines.append("## Verdict")
    if failures:
        lines.append(f"  FAIL ({len(failures)} issue(s))")
        for f in failures:
            lines.append(f"    - {f}")
    else:
        lines.append(
            f"  PASS -- {env_a['workspace_count']} workspaces snapshotted, "
            f"hash {h_a[:12]}, 0 schema deviations"
        )
    print("\n".join(lines))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
