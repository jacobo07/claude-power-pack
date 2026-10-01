"""Count agent tool calls that read vs write PP knowledge stores, from session transcripts.

Aperture: only tool calls the agent made (tool_use blocks in ~/.claude/projects/**/*.jsonl).
Blind to hook reads (hooks run outside the transcript) and to content injected via system-reminders.
"""
import json, os, sys, time, glob, collections

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
ROOT = os.path.expanduser(r"~/.claude/projects")
DEADLINE = time.time() + (int(sys.argv[2]) if len(sys.argv) > 2 else 240)

STORES = {
    "portfolio_learnings": "knowledge/portfolio_learnings.md",
    "ukdl_universal": "ukdl-universal.md",
    "knowledge_graph": "_knowledge_graph",
    "audit_cache_map": "_audit_cache/source_map.json",
    "knowledge_vault": ".claude/knowledge_vault",
    "hard_rules_digest": "hard-rules-digest.md",
    "memory_md": "memory/memory.md",
    "memory_dir_other": "/memory/",
    "resumption_file": "resumption_file.md",
    "pp_wiki": "claude-power-pack/wiki/",  # positive control: written this session
}
READ_TOOLS = {"Read", "Grep", "Glob"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}


def norm(s):
    return s.replace("\\", "/").lower()


def classify(name, inp):
    if name in READ_TOOLS:
        txt = " ".join(str(inp.get(k, "")) for k in ("file_path", "path", "pattern"))
        return "read", txt
    if name in WRITE_TOOLS:
        return "write", str(inp.get("file_path", ""))
    if name in SHELL_TOOLS:
        return "shell", str(inp.get("command", ""))
    return None, ""


cut = time.time() - DAYS * 86400
files = [f for f in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True)
         if os.path.getmtime(f) >= cut]
counts = collections.defaultdict(lambda: collections.Counter())
sessions = collections.defaultdict(lambda: collections.defaultdict(set))
total_tool_uses = 0
scanned = 0
timed_out = False
for f in files:
    if time.time() > DEADLINE:
        timed_out = True
        break
    scanned += 1
    try:
        fh = open(f, encoding="utf-8", errors="replace")
    except OSError:
        continue
    with fh:
        for line in fh:
            if '"tool_use"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            ts = rec.get("timestamp", "")
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                total_tool_uses += 1
                kind, txt = classify(b.get("name", ""), b.get("input") or {})
                if not kind:
                    continue
                t = norm(txt)
                for store, needle in STORES.items():
                    if needle in t:
                        if store == "memory_dir_other" and "memory/memory.md" in t:
                            continue
                        counts[store][kind] += 1
                        sessions[store][kind].add(f)

print(f"window_days={DAYS} transcripts_in_window={len(files)} scanned={scanned} timed_out={timed_out}")
print(f"total_tool_uses={total_tool_uses}")
print(f"{'store':22} {'read':>6} {'write':>6} {'shell':>6}  sess_r sess_w sess_sh")
for store in STORES:
    c = counts[store]; s = sessions[store]
    print(f"{store:22} {c['read']:6} {c['write']:6} {c['shell']:6}  {len(s['read']):6} {len(s['write']):6} {len(s['shell']):6}")
