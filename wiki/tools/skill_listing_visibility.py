"""C6 re-measure: description visibility in the initial skill_listing, before vs after skillOverrides.
Usage: python skill_listing_visibility.py <transcript_before.jsonl> <transcript_after.jsonl>
Read-only. A listing line is "- name: description"; a bare "- name" carries no description."""
import json, sys

WATCH = ("concurrent-writers-shared-tree", "guard-event-reachability", "presence-is-not-residency")


def listing(path):
    for line in open(path, encoding="utf-8"):
        if '"skill_listing"' in line:
            a = json.loads(line).get("attachment") or {}
            if a.get("type") == "skill_listing" and a.get("isInitial"):
                return a.get("content") or ""
    return None


def summary(content):
    entries = {}
    for ln in content.splitlines():
        if ln.startswith("- "):
            name, _, desc = ln[2:].partition(":")
            entries[name.strip()] = desc.strip()
    return entries


for label, path in (("before", sys.argv[1]), ("after", sys.argv[2])):
    c = listing(path)
    if c is None:
        print(f"{label}: NO initial skill_listing in {path} (unmeasured, not zero)")
        continue
    e = summary(c)
    described = sum(1 for d in e.values() if d)
    print(f"{label}: {len(c):,} chars, {len(e)} entries, {described} with description")
    for w in WATCH:
        d = e.get(w)
        print(f"  {w}: " + ("ABSENT from listing" if d is None else (f"described ({len(d)} chars)" if d else "name-only")))
