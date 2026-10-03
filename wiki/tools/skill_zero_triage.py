"""Zero-observed-invocation triage (PLAN-SKILL-RESIDENCY C7). Read-only; recommends nothing destructive.

For every installed skill/command (~/.claude/skills dirs, ~/.claude/commands *.md) with no observed
invocation on either channel (tools/skill_invocations.py: model Skill call, typed command) in the
window, record the evidence that bears on WHY, and a class that is an investigation lead, never a verdict:

  LINEAGE            named in an always-loaded file (CLAUDE.md, ~/.claude/rules): the capability may be
                     delivered by that text or by a moved-rule pointer without any invocation event
  HOOK-DELIVERED     a hook references it (body injected or carded): delivery without invocation
  CRITICAL-CANDIDATE description names security / destructive / recovery / authority / incident work:
                     rare-but-critical until coverage is known; recertify, do not retire
  ADVISOR-INDEXED    the heat-map advisor can suggest it (an opportunity proxy exists)
  DEMAND-UNKNOWN     none of the above

"no observed invocation" != "never needed" != "never delivered". Apertures named in the output.
Usage: python wiki/tools/skill_zero_triage.py [days=30]
"""
import json, re, sys
from pathlib import Path

PP = Path(r"C:\Users\User\.claude\skills\claude-power-pack")
sys.path.insert(0, str(PP / "tools"))
import skill_invocations as si  # noqa: E402

DAYS = float(sys.argv[1]) if len(sys.argv) > 1 else 30
HOME = Path.home() / ".claude"
CRIT = re.compile(r"(?i)\b(secur\w*|secret\w*|credential\w*|destructi\w*|delet\w*|recover\w*|rollback|"
                  r"incident|forensic\w*|authori[sz]\w*|irreversib\w*|privacy|tenant)\b")


def description(p: Path) -> str:
    f = p / "SKILL.md" if p.is_dir() else p
    try:
        head = f.read_text(encoding="utf-8", errors="replace")[:3000]
    except OSError:
        return ""
    m = re.search(r"^description:\s*(.+)$", head, re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def corpus(paths) -> str:
    out = []
    for p in paths:
        try:
            out.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(out)


installed = {}
for p in (HOME / "skills").iterdir():
    if p.is_dir():
        installed[p.name] = p
for p in (HOME / "commands").rglob("*.md"):
    installed.setdefault(":".join(p.relative_to(HOME / "commands").with_suffix("").parts), p)

prefix_files = [HOME / "CLAUDE.md", Path.home() / "CLAUDE.md", PP / "CLAUDE.md", *(HOME / "rules").rglob("*.md")]
prefix = corpus(prefix_files)
hooks = corpus([*(HOME / "hooks").glob("*.js"), *(PP / "hooks").glob("*.js"),
                *(PP / "modules" / "zero-crash" / "hooks").glob("*.js")])
try:
    advisor = set((json.loads((PP / "vault" / "skills_heat_map.json").read_text(encoding="utf-8")).get("skills") or {}))
except (OSError, ValueError):
    advisor = set()

scan = si.scan(HOME / "projects", DAYS, set(installed))
seen = set(scan["model"]) | set(scan["typed"])


def word(name, text):
    return re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", text) is not None


rows = []
for name, p in sorted(installed.items()):
    if name in seen:
        continue
    d = description(p)
    # A bare dictionary word ("fix", "update", "vault") collides with prose and code: a text match
    # for it is not evidence (measured 2026-10-03: 6 such names were flagged lineage/hook by collision).
    ambiguous = re.fullmatch(r"[a-z]+", name) is not None
    ev = {"lineage": not ambiguous and word(name, prefix), "hook": not ambiguous and word(name, hooks),
          "critical": bool(CRIT.search(d)), "advisor": name in advisor, "no_description": not d}
    cls = ("NAME-AMBIGUOUS" if ambiguous else "LINEAGE" if ev["lineage"] else
           "HOOK-REFERENCED" if ev["hook"] else "CRITICAL-CANDIDATE" if ev["critical"] else
           "ADVISOR-INDEXED" if ev["advisor"] else "DEMAND-UNKNOWN")
    rows.append((cls, name, ev, len(d)))

print(f"window {DAYS:g} d; installed {len(installed)}; observed (2 channels) {len(seen & set(installed))}; "
      f"no observed invocation {len(rows)}; list-form command rows (UNKNOWN) {scan['unknown_rows']}")
print("apertures: hook-injected bodies, JIT injection and doctrine cards deliver without an invocation event; "
      "HOOK-REFERENCED = a hook names it, not proof it delivers the body; "
      "project-local skills (<repo>/.claude/skills) not enumerated; advisor map "
      f"{len(advisor)} skills; criticality = description keywords only (a lead, not a classification)")
by = {}
for cls, name, ev, dl in rows:
    by.setdefault(cls, []).append((name, ev, dl))
for cls in ("LINEAGE", "HOOK-REFERENCED", "CRITICAL-CANDIDATE", "ADVISOR-INDEXED", "NAME-AMBIGUOUS",
            "DEMAND-UNKNOWN"):
    items = by.get(cls, [])
    print(f"\n[{cls}] {len(items)}")
    for name, ev, dl in items:
        flags = ",".join(k for k, v in ev.items() if v) or "-"
        print(f"  {name:48s} desc={dl:4d}B  {flags}")
print("\nNo row above is a deletion candidate. Retirement needs coverage, criticality, alternative, lineage (plan gate).")
