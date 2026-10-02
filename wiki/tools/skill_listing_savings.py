"""Characters the proposed name-only overrides would remove from the skill listing, measured on
the most recent full (isInitial) skill_listing recorded in this repo's transcripts.
Read-only. Tokens estimated at 3.9 chars/token (corpus calibration in token_economy_deep)."""
import glob, json, os

prop = json.load(open("skill_overrides.proposed.json", encoding="utf-8"))["skillOverrides"]
files = sorted(glob.glob(os.path.expanduser("~/.claude/projects/C--Users-User--claude-skills-claude-power-pack/*.jsonl")),
               key=os.path.getmtime, reverse=True)
for f in files[:40]:
    content = None
    for line in open(f, encoding="utf-8"):
        if '"skill_listing"' in line:
            a = json.loads(line).get("attachment") or {}
            if a.get("type") == "skill_listing" and a.get("isInitial"):
                content = a.get("content"); break
    if content:
        break
lines = content.splitlines()
total = len(content); removed = 0; hit = 0
for ln in lines:
    if ln.startswith("- "):
        name = ln[2:].split(":", 1)[0].strip()
        if name in prop:
            hit += 1
            removed += len(ln) - len(f"- {name}")
print(f"listing from {os.path.basename(f)}: {total:,} chars, {sum(1 for l in lines if l.startswith('- '))} entries")
print(f"proposed name-only entries found in it: {hit} of {len(prop)}; description chars removed: {removed:,} "
      f"({removed/total:.0%} of the listing) ~ {removed/3.9:,.0f} tok per call")
