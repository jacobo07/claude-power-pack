#!/usr/bin/env python3
"""
Claude Power Pack — Token Forensics: Burn Report (Part R)

Parses Claude Code's actual JSONL session logs to generate a forensic
TOKEN_BURN_REPORT.md with exact token breakdown by tool, file, and cost.

Usage:
    python token_autopsy.py                          # Latest session
    python token_autopsy.py --session all             # All sessions today
    python token_autopsy.py --output report.md        # Custom output path
    python token_autopsy.py --top 20                  # Top 20 files by cost
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [token-autopsy] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

def _load_pricing() -> tuple[dict, str]:
    """USD per million tokens from the estate's ONE pricing source (tools/pricing_source.py ->
    newest vault/pricing/anthropic_*.json). Replaced 2026-09-27: a hardcoded table here priced
    Opus 4.6 at $15/$75 (real $5/$25) and had no row for the models in use. Missing or
    unreadable -> empty table, so every model reports as unpriced rather than guessed."""
    tools_dir = Path(__file__).resolve().parents[2] / "tools"
    try:
        sys.path.insert(0, str(tools_dir))
        import pricing_source
        path = pricing_source.pricing_path_or_missing()
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # reported, not swallowed: the report says it is unpriced
        return {}, f"unpriced ({type(exc).__name__}: {exc})"
    table = {m: {"input": p["input"], "output": p["output"],
                 "cache_write": p["cache_write_5m"], "cache_read": p["cache_read"]}
             for m, p in (data.get("models") or {}).items()}
    return table, f"{path.name} (fetched {data.get('fetched_iso', '?')})"


PRICING, PRICING_SOURCE = _load_pricing()


def get_pricing(model_id: str) -> dict | None:
    """Prices for a model, or None when it is not in the table -- an unpriced model is
    reported as unpriced, never billed at some other model's rate. Longest key first, so
    `claude-opus-5-5` is not matched by `claude-opus-5`."""
    for key in sorted(PRICING, key=len, reverse=True):
        if key in (model_id or ""):
            return PRICING[key]
    return None


def find_project_dir() -> Path | None:
    """Find the Claude projects directory for the current working directory."""
    claude_dir = Path.home() / ".claude" / "projects"
    if not claude_dir.exists():
        return None
    return claude_dir


def find_session_logs(project_dir: Path, session_filter: str = "latest") -> list[Path]:
    """Find JSONL session log files."""
    if not project_dir or not project_dir.exists():
        return []

    all_jsonl = []
    for subdir in project_dir.iterdir():
        if not subdir.is_dir():
            continue
        for jsonl_file in subdir.glob("*.jsonl"):
            # Skip subagent logs
            if "subagent" in str(jsonl_file).lower():
                continue
            all_jsonl.append(jsonl_file)

    if not all_jsonl:
        return []

    # Sort by modification time, newest first
    all_jsonl.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    # One session per id. A session with extra working directories is recorded under each
    # project folder (measured 2026-09-27: the same 5.8 MB transcript under two folders),
    # and counting both doubled every figure.
    unique, seen_stems = [], set()
    for p in all_jsonl:
        if p.stem not in seen_stems:
            seen_stems.add(p.stem)
            unique.append(p)
    all_jsonl = unique

    if session_filter == "latest":
        # "latest" means THIS session when it is known. Newest-by-mtime is whichever pane
        # wrote last: measured 2026-09-27 it analysed another pane's transcript.
        own = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        mine = [f for f in all_jsonl if own and f.stem == own]
        if mine:
            return mine
        logger.warning("CLAUDE_CODE_SESSION_ID unset or unmatched; using the newest transcript "
                       "on disk, which may belong to another session")
        return all_jsonl[:1]
    elif session_filter == "all":
        # All sessions from today
        today = datetime.now().date()
        return [
            f for f in all_jsonl
            if datetime.fromtimestamp(f.stat().st_mtime).date() == today
        ]
    else:
        # Specific session ID
        return [f for f in all_jsonl if session_filter in f.stem]


def parse_session(jsonl_path: Path) -> dict:
    """Parse a JSONL session file and extract structured data."""
    messages = []
    tool_calls = []
    total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    models_used = set()
    seen_ids: set = set()
    first_ts = None
    last_ts = None

    try:
        text = jsonl_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", jsonl_path, exc)
        return {"messages": [], "tool_calls": [], "usage": total_usage, "models": set()}

    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        ts = entry.get("timestamp")
        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts

        msg_type = entry.get("type", "")

        # Extract usage and tool calls from assistant messages
        message = entry.get("message", {})
        if isinstance(message, dict):
            usage = message.get("usage", {})
            # One API response is written as several transcript lines (one per content
            # block), each repeating the same usage. Count each message id once: without
            # this the 2026-09-27 run reported 485 M cache reads for a session that had 80 M.
            mid = message.get("id")
            if usage and not (mid and mid in seen_ids):
                if mid:
                    seen_ids.add(mid)
                for key in total_usage:
                    total_usage[key] += usage.get(key, 0)
            model = message.get("model", "")
            if model:
                models_used.add(model)

            # Tool calls are inside message.content[] as {type: "tool_use"}
            content = message.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tool_calls.append({
                            "name": item.get("name", "unknown"),
                            "input": item.get("input", {}),
                            "timestamp": ts,
                        })

        # Also check top-level toolUse (some log formats)
        tool_use = entry.get("toolUse", {})
        if tool_use:
            tool_calls.append({
                "name": tool_use.get("name", "unknown"),
                "input": tool_use.get("input", {}),
                "timestamp": ts,
            })

        messages.append(entry)

    return {
        "messages": messages,
        "tool_calls": tool_calls,
        "usage": total_usage,
        "models": models_used,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "file": str(jsonl_path),
    }


def aggregate_by_tool(tool_calls: list) -> dict:
    """Group tool calls by tool name with counts."""
    by_tool = defaultdict(lambda: {"count": 0, "details": []})
    for tc in tool_calls:
        name = tc["name"]
        by_tool[name]["count"] += 1
        by_tool[name]["details"].append(tc)
    return dict(by_tool)


def aggregate_by_file(tool_calls: list) -> dict:
    """Track files read and how many times."""
    file_reads = defaultdict(int)
    for tc in tool_calls:
        if tc["name"] == "Read":
            file_path = tc["input"].get("file_path", "unknown")
            file_reads[file_path] += 1
        elif tc["name"] == "Glob":
            pattern = tc["input"].get("pattern", "")
            file_reads[f"[glob] {pattern}"] += 1
        elif tc["name"] == "Grep":
            pattern = tc["input"].get("pattern", "")
            path = tc["input"].get("path", "cwd")
            file_reads[f"[grep] {pattern} in {path}"] += 1
    return dict(file_reads)


def detect_waste(tool_calls: list, file_reads: dict) -> list[str]:
    """Identify wasteful patterns."""
    warnings = []

    # Repeated file reads
    repeated = {f: c for f, c in file_reads.items() if c > 1 and not f.startswith("[")}
    if repeated:
        total_repeats = sum(c - 1 for c in repeated.values())
        warnings.append(
            f"{len(repeated)} files read multiple times ({total_repeats} redundant reads)"
        )

    # Mass grep operations
    mass_greps = [
        tc for tc in tool_calls
        if tc["name"] == "Grep"
        and not tc["input"].get("path")  # No path = searched everything
    ]
    if mass_greps:
        warnings.append(
            f"{len(mass_greps)} grep commands searched without path restriction"
        )

    # Mass bash operations
    mass_bash = [
        tc for tc in tool_calls
        if tc["name"] == "Bash"
        and any(cmd in str(tc["input"].get("command", ""))
                for cmd in ["grep -r", "find /", "find .", "rg ", "ag "])
    ]
    if mass_bash:
        warnings.append(
            f"{len(mass_bash)} bash commands ran mass-search operations"
        )

    # Sub-agent count
    agents = [tc for tc in tool_calls if tc["name"] == "Agent"]
    if len(agents) > 3:
        warnings.append(
            f"{len(agents)} sub-agents spawned (consider consolidating)"
        )

    # Total tool calls
    if len(tool_calls) > 50:
        warnings.append(
            f"{len(tool_calls)} total tool calls — possible agentic loop"
        )

    return warnings


def estimate_cost(usage: dict, model: str) -> dict:
    """Cost of what was billed, at the session model's own rates: every token class is a
    charge. The previous version SUBTRACTED 90% of cache reads priced at the input rate --
    which produced -$746 on a real session, because cache reads dominate a long one."""
    prices = get_pricing(model)
    if prices is None:
        return {}
    per_m = lambda n, rate: (n / 1_000_000) * rate
    parts = {
        "input": per_m(usage["input_tokens"], prices["input"]),
        "cache_write": per_m(usage["cache_creation_input_tokens"], prices["cache_write"]),
        "cache_read": per_m(usage["cache_read_input_tokens"], prices["cache_read"]),
        "output": per_m(usage["output_tokens"], prices["output"]),
    }
    return {model: {**parts, "total": sum(parts.values())}}


def generate_report(sessions: list[dict], output_path: Path, top_n: int = 10) -> str:
    """Generate TOKEN_BURN_REPORT.md from parsed sessions."""
    # Aggregate across all sessions
    total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    all_tool_calls = []
    all_models = set()
    first_ts = None
    last_ts = None

    for session in sessions:
        for key in total_usage:
            total_usage[key] += session["usage"][key]
        all_tool_calls.extend(session["tool_calls"])
        all_models.update(session["models"])
        if session.get("first_ts"):
            if first_ts is None or session["first_ts"] < first_ts:
                first_ts = session["first_ts"]
        if session.get("last_ts"):
            if last_ts is None or session["last_ts"] > last_ts:
                last_ts = session["last_ts"]

    # Every class the API billed. Input+output alone reported 124,927 on a session that re-read
    # 56.8 M cached tokens: the dominant cost of a long session was invisible in the headline.
    total_tokens = sum(total_usage.values())
    by_tool = aggregate_by_tool(all_tool_calls)
    file_reads = aggregate_by_file(all_tool_calls)
    waste_warnings = detect_waste(all_tool_calls, file_reads)
    real_models = sorted(m for m in all_models if m and not m.startswith("<"))
    primary_model = real_models[0] if real_models else "unknown"
    costs = estimate_cost(total_usage, primary_model)

    # Format timestamps
    ts_start = first_ts or "unknown"
    ts_end = last_ts or "unknown"
    if isinstance(ts_start, str) and len(ts_start) > 16:
        ts_start = ts_start[:16]
    if isinstance(ts_end, str) and len(ts_end) > 16:
        ts_end = ts_end[:16]

    lines = []
    lines.append("# Token Burn Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Session:** {ts_start} — {ts_end}")
    lines.append(f"**Sessions analyzed:** {len(sessions)}")
    lines.append(f"**Models:** {', '.join(all_models) or 'unknown'}")
    lines.append(f"**Total tokens:** {total_tokens:,}")
    lines.append(f"  - Input: {total_usage['input_tokens']:,}")
    lines.append(f"  - Output: {total_usage['output_tokens']:,}")
    lines.append(f"  - Cache created: {total_usage['cache_creation_input_tokens']:,}")
    lines.append(f"  - Cache reads: {total_usage['cache_read_input_tokens']:,}")
    lines.append("")

    # Tool breakdown
    lines.append("## Token Breakdown by Tool")
    lines.append("")
    lines.append("| Tool | Calls | % of Activity |")
    lines.append("|------|-------|--------------|")
    total_calls = len(all_tool_calls) or 1
    sorted_tools = sorted(by_tool.items(), key=lambda x: x[1]["count"], reverse=True)
    for tool_name, data in sorted_tools:
        pct = (data["count"] / total_calls) * 100
        lines.append(f"| {tool_name} | {data['count']} | {pct:.1f}% |")
    lines.append("")

    # File reads
    if file_reads:
        lines.append(f"## Files Accessed (Top {top_n} by frequency)")
        lines.append("")
        lines.append("| File | Accesses | Redundant? |")
        lines.append("|------|----------|------------|")
        sorted_files = sorted(file_reads.items(), key=lambda x: x[1], reverse=True)[:top_n]
        for filepath, count in sorted_files:
            redundant = "YES" if count > 1 and not filepath.startswith("[") else ""
            # Truncate long paths
            display = filepath if len(filepath) < 60 else "..." + filepath[-57:]
            lines.append(f"| {display} | {count} | {redundant} |")
        lines.append("")

    # Waste detection
    if waste_warnings:
        lines.append("## Waste Detection")
        lines.append("")
        for warning in waste_warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Cost estimate
    lines.append("## Cost Estimate")
    lines.append("")
    lines.append(f"Prices: {PRICING_SOURCE}. List price, first-party API; a subscription is not billed this way.")
    lines.append("")
    if not costs:
        lines.append(f"**Unpriced:** no price for `{primary_model}` in the pricing source.")
    for model_name, cost_data in costs.items():
        lines.append(f"| {model_name} | USD |")
        lines.append("|---|---|")
        for part in ("cache_read", "cache_write", "input", "output", "total"):
            lines.append(f"| {part} | ${cost_data[part]:.2f} |")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")

    repeated_files = {f: c for f, c in file_reads.items() if c > 1 and not f.startswith("[")}
    if repeated_files:
        lines.append(f"1. **Cache file reads** — {len(repeated_files)} files were read multiple times")

    agents = [tc for tc in all_tool_calls if tc["name"] == "Agent"]
    if len(agents) > 3:
        lines.append(f"2. **Consolidate sub-agents** — {len(agents)} agents spawned, consider merging")

    mass_greps = [
        tc for tc in all_tool_calls
        if tc["name"] == "Grep" and not tc["input"].get("path")
    ]
    mass_bash = [
        tc for tc in all_tool_calls
        if tc["name"] == "Bash"
        and any(cmd in str(tc["input"].get("command", ""))
                for cmd in ["grep -r", "find /", "find .", "rg ", "ag "])
    ]
    if mass_greps or mass_bash:
        total_mass = len(mass_greps) + len(mass_bash)
        lines.append(f"3. **Narrow search scope** — {total_mass} search operations lacked path restrictions")

    if total_tokens > 100000:
        lines.append(f"4. **High token burn** — {total_tokens:,} tokens in this session. Consider splitting into smaller tasks.")

    if not (repeated_files or len(agents) > 3 or mass_greps or mass_bash
            or total_tokens > 100000):
        lines.append("Session looks efficient. No major waste detected.")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by Claude Power Pack — Token Forensics (Part R)*")
    lines.append("")

    report = "\n".join(lines)

    # Write report
    output_path.write_text(report, encoding="utf-8")
    logger.info("Report written to: %s", output_path)

    return report


def main():
    parser = argparse.ArgumentParser(
        prog="token-autopsy",
        description="Forensic analysis of Claude Code session token usage.",
    )
    parser.add_argument(
        "--session", default="latest",
        help="Which session(s) to analyze: 'latest', 'all' (today), or a session ID",
    )
    parser.add_argument(
        "--output", default="TOKEN_BURN_REPORT.md",
        help="Output file path (default: TOKEN_BURN_REPORT.md)",
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="Show top N files by access count (default: 10)",
    )
    args = parser.parse_args()

    project_dir = find_project_dir()
    if not project_dir:
        print("No Claude Code project directory found at ~/.claude/projects/", file=sys.stderr)
        sys.exit(1)

    log_files = find_session_logs(project_dir, args.session)
    if not log_files:
        print(f"No session logs found for filter '{args.session}'.", file=sys.stderr)
        print("Run a Claude Code session first, then re-run this tool.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(log_files)} session(s)...")

    sessions = []
    for log_file in log_files:
        session = parse_session(log_file)
        sessions.append(session)
        total = session["usage"]["input_tokens"] + session["usage"]["output_tokens"]
        print(f"  - {log_file.name}: {total:,} tokens, {len(session['tool_calls'])} tool calls")

    output_path = Path(args.output).resolve()
    report = generate_report(sessions, output_path, args.top)

    # Print summary to stdout
    print("")
    print("=" * 60)
    total_all = sum(
        s["usage"]["input_tokens"] + s["usage"]["output_tokens"]
        for s in sessions
    )
    print(f"TOTAL: {total_all:,} tokens across {len(sessions)} session(s)")
    print(f"Report: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
