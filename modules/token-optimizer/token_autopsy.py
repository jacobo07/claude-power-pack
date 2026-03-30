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

# Pricing per million tokens (USD)
PRICING = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0},
    # Fallback for unknown models
    "default": {"input": 3.0, "output": 15.0},
}


def get_pricing(model_id: str) -> dict:
    """Get pricing for a model, falling back to default."""
    for key in PRICING:
        if key in (model_id or ""):
            return PRICING[key]
    return PRICING["default"]


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

    if session_filter == "latest":
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
            if usage:
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
    """Calculate cost estimates for different model tiers."""
    total_input = usage["input_tokens"] + usage["cache_creation_input_tokens"]
    total_output = usage["output_tokens"]
    cache_reads = usage["cache_read_input_tokens"]

    costs = {}
    for model_key, prices in PRICING.items():
        if model_key == "default":
            continue
        input_cost = (total_input / 1_000_000) * prices["input"]
        output_cost = (total_output / 1_000_000) * prices["output"]
        # Cache reads are typically 90% cheaper
        cache_savings = (cache_reads / 1_000_000) * prices["input"] * 0.9
        costs[model_key] = {
            "input": input_cost,
            "output": output_cost,
            "cache_savings": cache_savings,
            "total": input_cost + output_cost - cache_savings,
        }
    return costs


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

    total_tokens = total_usage["input_tokens"] + total_usage["output_tokens"]
    by_tool = aggregate_by_tool(all_tool_calls)
    file_reads = aggregate_by_file(all_tool_calls)
    waste_warnings = detect_waste(all_tool_calls, file_reads)
    primary_model = next(iter(all_models), "unknown")
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
    lines.append("| Model | Input | Output | Cache Savings | Total |")
    lines.append("|-------|-------|--------|--------------|-------|")
    for model_name, cost_data in costs.items():
        short_name = model_name.replace("claude-", "").replace("-", " ").title()
        lines.append(
            f"| {short_name} "
            f"| ${cost_data['input']:.4f} "
            f"| ${cost_data['output']:.4f} "
            f"| -${cost_data['cache_savings']:.4f} "
            f"| ${cost_data['total']:.4f} |"
        )
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

    if not (repeated_files or len(agents) > 3 or mass_ops or total_tokens > 100000):
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
