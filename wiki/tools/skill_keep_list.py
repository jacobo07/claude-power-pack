"""Build the skillOverrides keep-list (read-only, zero model quota).

KEEP a skill (full description stays in the listing) if ANY holds:
  1. invoked by the model or a user (Skill tool_use) in the last 30 days, main or subagent;
  2. named in an activation table / criteria of an always-loaded CLAUDE.md;
  3. it is a plugin skill (contains ':'): the CLI returns "on" for plugin skills regardless of
     skillOverrides (claude.exe 2.1.288: `if(e.type!=="prompt"||e.source==="plugin")return"on"`).
Everything else listed -> proposed "name-only".
Also confirms the accepted override values by scanning the installed CLI binary.
Writes: skill_keep_list.<date>.out (report) and skill_overrides.proposed.json (Owner applies).
"""
import json, os, re, sqlite3, time
from collections import Counter

HOME = os.path.expanduser("~")
p = os.path.join(HOME, ".claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
END = c.execute("select max(ts) from calls").fetchone()[0]
DAYS = 30
files = [r[0] for r in c.execute("select distinct file from calls where ts>?", (END - DAYS * 86400,))]

inv = Counter(); listed = Counter(); last_listing = {}
for f in files:
    try:
        fh = open(f, encoding="utf-8")
    except OSError:
        continue
    for line in fh:
        if '"Skill"' not in line and '"skill_listing"' not in line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") == "skill_listing":
                for n in a.get("names") or []:
                    listed[n] += 1
        elif d.get("type") == "assistant":
            for b in (d.get("message") or {}).get("content") or []:
                if b.get("type") == "tool_use" and b.get("name") == "Skill":
                    inv[(b.get("input") or {}).get("skill")] += 1
    fh.close()

# names that always-loaded CLAUDE.md files mention (activation tables, criteria, routers)
md_paths = [os.path.join(HOME, ".claude/CLAUDE.md"), os.path.join(HOME, "CLAUDE.md"),
            os.path.join(HOME, ".claude/skills/claude-power-pack/CLAUDE.md")]
import glob
md_paths += glob.glob(os.path.join(HOME, ".claude/rules/**/*.md"), recursive=True)  # always loaded; moved-rule stubs point to skills
md_text = "\n".join(open(x, encoding="utf-8").read() for x in md_paths if os.path.exists(x))
named = {n for n in listed if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", md_text)}


def own_source(n):
    """True only for a skill or command that lives under ~/.claude (ours to override).
    Bundled harness skills and anything not found on disk are left alone."""
    return (os.path.isfile(os.path.join(HOME, ".claude/skills", n, "SKILL.md"))
            or os.path.isfile(os.path.join(HOME, ".claude/commands", n + ".md")))

# accepted values, from the binary
b = open(os.path.join(HOME, ".local/bin/claude.exe"), "rb").read()
vals = {v: (b.count(f'"{v}"'.encode()) > 0) for v in ("on", "off", "name-only", "user-invocable-only")}
i = b.find(b'"name-only"')
ctx = b[max(0, i - 200): i + 200].decode("utf-8", "replace") if i >= 0 else ""

keep, hide = {}, []
for n in sorted(listed):
    why = []
    if inv[n]:
        why.append(f"invoked {inv[n]}x/30d")
    if n in named:
        why.append("named in CLAUDE.md or rules")
    if ":" in n:
        why.append("plugin (not overridable)")
    elif not own_source(n):
        why.append("bundled / not under ~/.claude (left alone)")
    if why:
        keep[n] = why
    else:
        hide.append(n)

out = []
out.append(f"window {DAYS} d to {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime(END))}; transcripts scanned={len(files):,}")
out.append(f"listed distinct={len(listed)}; invoked distinct={sum(1 for n in inv if n)}; invocations={sum(inv.values())}")
out.append(f"accepted values present in binary: {vals}")
out.append(f"binary context around \"name-only\": {ctx!r}")
out.append(f"\nKEEP ({len(keep)}):")
for n, w in sorted(keep.items(), key=lambda x: (-inv[x[0]], x[0])):
    out.append(f"  {n:45} {'; '.join(w)}")
out.append(f"\nPROPOSED name-only ({len(hide)}):")
out.append("  " + ", ".join(hide))
out.append("\nInvoked but not in any listing seen (commands or renamed):")
out.append("  " + ", ".join(sorted(n for n in inv if n and n not in listed)))
rep = "\n".join(out)
print(rep)
open(f"skill_keep_list.{time.strftime('%Y-%m-%d')}.out", "w", encoding="utf-8").write(rep + "\n")
json.dump({"skillOverrides": {n: "name-only" for n in hide}}, open("skill_overrides.proposed.json", "w", encoding="utf-8"), indent=2)
