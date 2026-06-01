"""One-shot audit: which PP tools require manual invocation, and how the PP would automate each.
Deterministic. Reads global settings.json + agents + commands to decide 'already automated' vs 'manual'.
Outputs JSON to stdout for report authoring. Not a production module; analytical scanner.
"""
import json
import re
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
HOME = Path.home() / ".claude"

# --- Load automation surfaces (what already references a tool) ---
def safe_read(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

settings_text = safe_read(HOME / "settings.json")
agents_text = "\n".join(safe_read(f) for f in (HOME / "agents").glob("*.md")) if (HOME / "agents").exists() else ""
commands_text = "\n".join(safe_read(f) for f in (HOME / "commands").glob("*.md")) if (HOME / "commands").exists() else ""
# PP-local hooks dir + skill bodies can also auto-invoke
pp_hooks_text = "\n".join(safe_read(f) for f in (PP / "hooks").glob("*")) if (PP / "hooks").exists() else ""
home_hooks_text = "\n".join(safe_read(f) for f in (HOME / "hooks").glob("*")) if (HOME / "hooks").exists() else ""
automation_blob = settings_text + "\n" + agents_text + "\n" + commands_text + "\n" + pp_hooks_text + "\n" + home_hooks_text

# --- Gather candidate tools ---
candidates = []
for base in ["tools", "modules"]:
    for f in (PP / base).rglob("*.py"):
        s = str(f)
        if "__pycache__" in s:
            continue
        candidates.append(f)

def first_docline(content):
    # strip a leading shebang + blank lines so the real module docstring is at the top
    lines = content.splitlines()
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or lines[i].strip() == "" or lines[i].startswith("# -*-")):
        i += 1
    stripped = "\n".join(lines[i:])
    m = re.search(r'^\s*("""|\'\'\')(.*?)(\1)', stripped, re.DOTALL)
    if m:
        body = [b for b in m.group(2).strip().splitlines() if b.strip()]
        if body:
            return body[0].strip()[:160]
    # fallback: first meaningful top-of-file comment (not shebang/encoding)
    for line in lines[:8]:
        ls = line.strip()
        if ls.startswith("#") and not ls.startswith("#!") and len(ls) > 4 and "-*-" not in ls:
            return ls.lstrip("# ").strip()[:160]
    return ""

def detect_subcommands(content):
    subs = set()
    for m in re.finditer(r'add_parser\(\s*["\']([a-zA-Z0-9_-]+)["\']', content):
        subs.add(m.group(1))
    return sorted(subs)

def detect_flags(content):
    flags = []
    seen = set()
    for m in re.finditer(r'add_argument\(\s*["\'](--[a-zA-Z0-9_-]+)["\']', content):
        f = m.group(1)
        if f not in seen:
            seen.add(f)
            flags.append(f)
    return flags[:4]

def classify_mechanism(name, content):
    c = content
    # ordered: most specific first
    if re.search(r'\b(deploy|rollback|restore|backup)\b', c, re.I) and re.search(r'post[_-]?deploy|post[_-]?rollback|callback', c, re.I):
        return "E"
    if re.search(r'\b(schedule|cron|periodic|daemon|--watch|while True|sleep\()', c) and re.search(r'heartbeat|miner|daemon|watch|topology', c, re.I):
        return "F"
    if re.search(r'PostToolUse|PreToolUse|hook', c):
        return "A"
    if re.search(r'SessionStart|UserPromptSubmit|signal|advisory|budget|token', c) and re.search(r'monitor|budget|signal|context|watchdog', c, re.I):
        return "B"
    if re.search(r'research|graph|knowledge|distill|mine|enrich|summari|index', c, re.I):
        return "D"
    if re.search(r'argparse|ArgumentParser', c):
        return "C"
    return "C"

MECH_NAME = {
    "A": "Hook automatico (settings.json event)",
    "B": "Signal proactiva (proactive_dispatcher / SessionStart)",
    "C": "Agente global (~/.claude/agents)",
    "D": "jit_skill_loader trigger (intent semantico)",
    "E": "Post-deploy / post-rollback callback",
    "F": "Task Scheduler / cron daemon",
}

def is_test_or_private(f):
    n = f.name
    return n.startswith("test_") or n.startswith("_") or n in ("__init__.py", "__main__.py", "conftest.py")

rows = []
for f in candidates:
    content = safe_read(f)
    has_cli = bool(re.search(r'__name__\s*==\s*["\']__main__["\']', content)) or "argparse" in content or "ArgumentParser" in content
    rel = f.relative_to(PP).as_posix()
    name = f.stem
    # automated if its filename (with/without .py) appears in any automation surface
    referenced = (f.name in automation_blob) or (rel in automation_blob) or (name in automation_blob)
    rows.append({
        "path": rel,
        "name": name,
        "has_cli": has_cli,
        "is_test_or_private": is_test_or_private(f),
        "referenced": referenced,
        "doc": first_docline(content),
        "subcommands": detect_subcommands(content),
        "flags": detect_flags(content),
        "mechanism": classify_mechanism(name, content),
        "loc": content.count("\n") + 1,
    })

# CLI tools only, excluding tests/private dunder
cli_tools = [r for r in rows if r["has_cli"] and not r["is_test_or_private"]]
manual = [r for r in cli_tools if not r["referenced"]]
automated = [r for r in cli_tools if r["referenced"]]

summary = {
    "total_py": len(rows),
    "cli_tools": len(cli_tools),
    "automated": len(automated),
    "manual": len(manual),
    "tests_private_excluded": len([r for r in rows if r["is_test_or_private"]]),
}
by_mech = {}
for r in manual:
    by_mech.setdefault(r["mechanism"], []).append(r["name"])

out = {
    "summary": summary,
    "by_mech_counts": {k: len(v) for k, v in by_mech.items()},
    "mech_names": MECH_NAME,
    "automated": sorted([r["name"] for r in automated]),
    "manual": manual,
}
Path("_manual_audit_clean.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("WROTE _manual_audit_clean.json  manual=%d automated=%d cli=%d" % (
    summary["manual"], summary["automated"], summary["cli_tools"]))
