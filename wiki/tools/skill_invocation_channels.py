"""Skill invocation channels: model Skill tool_use vs Owner-typed /command (zero quota, read-only).

Parses JSON (never substring-matches lines), so a skill name inside a listing, a hook's output, a
pointer, or a tool INPUT that merely mentions it cannot count. Two channels:
  model: assistant tool_use name=="Skill" -> input.skill
  typed: user message whose string content carries <command-name>/X</command-name>
Positive control (2026-10-03): session 6d128db5 typed /kresume -> typed=1, model=0 for kresume.
Usage: python skill_invocation_channels.py [days=7]
"""
import json, os, re, sys, time
from collections import Counter
from pathlib import Path

DAYS = float(sys.argv[1]) if len(sys.argv) > 1 else 7
ROOT = Path(os.path.expanduser("~/.claude/projects"))
CMD = re.compile(r"^\s*<command-message>[^<]*</command-message>\s*<command-name>/([\w:.-]+)</command-name>")
SKILLS = set()
for base in (Path(os.path.expanduser("~/.claude/skills")), Path(os.path.expanduser("~/.claude/commands"))):
    if base.is_dir():
        for p in base.iterdir():
            SKILLS.add(p.stem if p.is_file() else p.name)

cut = time.time() - DAYS * 86400
model = Counter(); typed = Counter(); files = 0
for f in ROOT.rglob("*.jsonl"):
    try:
        if f.stat().st_mtime < cut:
            continue
        fh = open(f, encoding="utf-8")
    except OSError:
        continue
    files += 1
    with fh:
        for line in fh:
            if '"Skill"' not in line and "<command-name>" not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            m = d.get("message") or {}
            if d.get("type") == "assistant":
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                        model[(b.get("input") or {}).get("skill")] += 1
            elif d.get("type") == "user" and isinstance(m.get("content"), str):
                mm = CMD.match(m["content"])
                if mm:
                    typed[mm.group(1)] += 1

names = set(model) | set(typed)
only_typed = sorted((n for n in names if typed[n] and not model[n]), key=lambda n: -typed[n])
print(f"window {DAYS:g} d; transcripts {files}; model Skill calls {sum(model.values())} "
      f"({len(model)} names); typed commands {sum(typed.values())} ({len(typed)} names)")
print(f"typed names that are installed skills/commands: {sum(1 for n in typed if n.split(':')[-1] in SKILLS)}")
print(f"names seen ONLY as typed (a tool_use counter reports them as zero): {len(only_typed)}")
for n in only_typed[:40]:
    print(f"  {typed[n]:5d}  /{n}")
print("top by total (model / typed):")
for n in sorted(names, key=lambda n: -(model[n] + typed[n]))[:25]:
    print(f"  {model[n]:5d} {typed[n]:5d}  {n}")
