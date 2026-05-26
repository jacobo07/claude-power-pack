"""/observe CLI -- Owner-facing entry point for the Monitoring Axis.

Five flags, all sealed by Q&A:

  --once   [--project NAME|all]   single-poll snapshot of given project(s)
                                  (absorbs P2.3 health-all)
  --watch  [--project NAME|all]   foreground poll loop (Ctrl-C to stop)
  --status [--project NAME|all]   read last persisted state, no new check
  --alerts [--project NAME] [--last N]  list recent vault/alerts/*.md
  --daemon [--project NAME]       print cron/Task Scheduler instructions
                                  (NEVER auto-installs -- Hawkins lens)

Single entry: `python -m modules.monitoring.observe --once`.

Sec 10 invariant (inherited from Rollback Axis): this CLI suggests via
alert receipts; it never invokes modules.rollback. The receipt's
markdown body carries the "/rollback --project X" string as text for
the Owner to copy, never as a subprocess.
"""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from alert import emit_alert, list_alerts, purge_old_alerts  # noqa: E402
from monitor import (  # noqa: E402
    MonitorState,
    STATUS_DOWN,
    STATUS_UNKNOWN,
    STATUS_UP,
    config_path,
    load_config,
    load_state,
    poll_loop,
    poll_once,
)


def _all_projects(repo_root: Path | None = None) -> list[str]:
    """Enumerate the projects with a config in vault/monitor/."""
    base = (repo_root or THIS_DIR.parent.parent) / "vault" / "monitor"
    if not base.is_dir():
        return []
    out: list[str] = []
    for f in sorted(base.glob("*.json")):
        if f.name.endswith("_state.json"):
            continue
        out.append(f.stem)
    return out


def _resolve_projects(arg: str | None, repo_root: Path | None = None) -> list[str]:
    if not arg or arg.lower() == "all":
        return _all_projects(repo_root)
    return [arg]


def _on_alert_callback(state: MonitorState, alert_kind: str, config: dict[str, Any], repo_root: Path | None = None) -> None:
    """Bridge from poll_loop's alert hook to the file+stdout emitter."""
    emit_alert(state.project, alert_kind, state.last_evidence or "", config, repo_root=repo_root)


# ---------------------------------------------------------------------------
# Flag handlers
# ---------------------------------------------------------------------------


def cmd_once(args: argparse.Namespace, repo_root: Path | None = None) -> int:
    projects = _resolve_projects(args.project, repo_root)
    if not projects:
        print("[observe] no monitor configs found in vault/monitor/", file=sys.stderr)
        return 4

    rows: list[tuple[str, str, str, str]] = []
    any_down = False
    for project in projects:
        try:
            config = load_config(project, repo_root)
            state, alert_kind = poll_once(project, repo_root)
            if alert_kind:
                emit_alert(project, alert_kind, state.last_evidence or "", config, repo_root=repo_root)
            rows.append((project, state.status, state.last_check_iso, state.last_evidence[:80]))
            if state.status == STATUS_DOWN:
                any_down = True
        except (FileNotFoundError, ValueError) as exc:
            rows.append((project, "ERROR", "", f"{type(exc).__name__}: {exc}"))
            any_down = True

    _print_status_table(rows)
    print("\nP2.3 health-all absorbed by --once flag (one snapshot, N projects).")
    return 1 if any_down else 0


def cmd_watch(args: argparse.Namespace, repo_root: Path | None = None) -> int:
    projects = _resolve_projects(args.project, repo_root)
    if not projects:
        print("[observe] no monitor configs found in vault/monitor/", file=sys.stderr)
        return 4

    stop = threading.Event()
    threads: list[threading.Thread] = []

    def _alert_bridge(s: MonitorState, k: str, c: dict[str, Any]) -> None:
        _on_alert_callback(s, k, c, repo_root=repo_root)

    for project in projects:
        t = threading.Thread(
            target=poll_loop,
            args=(project,),
            kwargs={"stop_event": stop, "on_alert": _alert_bridge, "repo_root": repo_root},
            daemon=True,
            name=f"observe-{project}",
        )
        t.start()
        threads.append(t)
        print(f"[observe] watching {project} (Ctrl-C to stop)")

    try:
        while not stop.is_set():
            stop.wait(timeout=1.0)
    except KeyboardInterrupt:
        print("\n[observe] Ctrl-C -- stopping watcher threads cleanly...")
    finally:
        stop.set()
        for t in threads:
            t.join(timeout=2.0)
    return 0


def cmd_status(args: argparse.Namespace, repo_root: Path | None = None) -> int:
    projects = _resolve_projects(args.project, repo_root)
    if not projects:
        print("[observe] no monitor configs found in vault/monitor/", file=sys.stderr)
        return 4

    rows: list[tuple[str, str, str, str]] = []
    for project in projects:
        state = load_state(project, repo_root)
        rows.append((project, state.status, state.last_check_iso or "(never polled)", state.last_evidence[:80]))
    _print_status_table(rows, header_suffix="(last known, from disk; no new check)")
    return 0


def cmd_alerts(args: argparse.Namespace, repo_root: Path | None = None) -> int:
    limit = int(args.last)
    project = args.project if args.project and args.project.lower() != "all" else None
    entries = list_alerts(project=project, repo_root=repo_root, limit=limit)
    if not entries:
        print("[observe] no alerts found.")
        return 0
    print(f"{'TIMESTAMP':<18} | {'PROJECT':<14} | {'EVENT':<12} | PATH")
    print(f"{'-'*18} + {'-'*14} + {'-'*12} + {'-'*40}")
    for e in entries:
        ts_human = (
            f"{e['ts_compact'][0:4]}-{e['ts_compact'][4:6]}-{e['ts_compact'][6:8]}T"
            f"{e['ts_compact'][9:11]}:{e['ts_compact'][11:13]}Z"
        )
        rel = Path(e["path"]).name
        print(f"{ts_human:<18} | {e['project']:<14} | {e['event']:<12} | {rel}")
    return 0


def cmd_daemon(args: argparse.Namespace, repo_root: Path | None = None) -> int:
    """Print install instructions. NEVER auto-installs (Hawkins lens)."""
    project = args.project or "all"
    repo = (repo_root or THIS_DIR.parent.parent).resolve()

    print("=" * 70)
    print("PP Monitoring Axis -- daemon install instructions")
    print("=" * 70)
    print()
    print("This command does NOT install anything. It prints the exact")
    print("commands you copy-paste. The Owner decides when, where, and how.")
    print()
    print("Linux / VPS (crontab):")
    print("  crontab -e")
    print(f"  */1 * * * * cd {repo} && \\")
    print(f"    python -m modules.monitoring.observe --once --project {project} \\")
    print( "    >> /var/log/pp-monitor.log 2>&1")
    print()
    print("Windows Task Scheduler (one-time setup):")
    print("  Action      : python")
    print(f"  Arguments   : -m modules.monitoring.observe --once --project {project}")
    print(f"  Start in    : {repo}")
    print( "  Trigger     : Every 1 minute, indefinitely")
    print( "  Run whether user logged on or not")
    print()
    print("Foreground alternative (no daemon -- pane stays open):")
    print(f"  cd {repo}")
    print(f"  python -m modules.monitoring.observe --watch --project {project}")
    print()
    print("=" * 70)
    return 0


# ---------------------------------------------------------------------------
# Table printer (shared by --once and --status)
# ---------------------------------------------------------------------------


def _print_status_table(
    rows: list[tuple[str, str, str, str]],
    header_suffix: str = "",
) -> None:
    title = "PP Monitoring -- status"
    if header_suffix:
        title += " " + header_suffix
    print(title)
    print()
    print(f"{'PROJECT':<14} | {'STATUS':<8} | {'LAST_CHECK':<22} | EVIDENCE")
    print(f"{'-'*14} + {'-'*8} + {'-'*22} + {'-'*60}")
    for project, status, ts, evidence in rows:
        print(f"{project:<14} | {status:<8} | {ts:<22} | {evidence}")


# ---------------------------------------------------------------------------
# argparse driver
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="observe",
        description="PP Monitoring/Alert Axis CLI -- /observe",
    )
    p.add_argument("--once", action="store_true", help="Single poll snapshot of N projects")
    p.add_argument("--watch", action="store_true", help="Foreground poll loop (Ctrl-C to stop)")
    p.add_argument("--status", action="store_true", help="Read last persisted state, no new check")
    p.add_argument("--alerts", action="store_true", help="List recent vault/alerts/*.md")
    p.add_argument("--daemon", action="store_true", help="Print cron / Task Scheduler instructions")
    p.add_argument("--project", default=None, help="Project name or 'all' (default 'all' for --once/--watch/--status)")
    p.add_argument("--last", default="10", help="N for --alerts (default 10)")
    p.add_argument("--repo-root", default=None, help="Override repo root (testing)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    flags = [args.once, args.watch, args.status, args.alerts, args.daemon]
    if sum(bool(f) for f in flags) != 1:
        print("[observe] exactly one of --once / --watch / --status / --alerts / --daemon required", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).resolve() if args.repo_root else None

    if args.once:
        return cmd_once(args, repo_root)
    if args.watch:
        return cmd_watch(args, repo_root)
    if args.status:
        return cmd_status(args, repo_root)
    if args.alerts:
        return cmd_alerts(args, repo_root)
    if args.daemon:
        return cmd_daemon(args, repo_root)
    return 2


if __name__ == "__main__":
    sys.exit(main())
