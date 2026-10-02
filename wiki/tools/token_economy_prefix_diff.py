"""Diff what two sessions sent before their first API call: system-prompt sections (from
prompt_snapshot) and every attachment / user item in order. Names the first item that differs,
which is where cross-session cache sharing breaks. Read-only, zero quota.
Usage: token_economy_prefix_diff.py <session-a> <session-b> [project-dir-slug]"""
import difflib, glob, json, os, sys

slug = sys.argv[3] if len(sys.argv) > 3 else "*"
def load(sid):
    f = glob.glob(os.path.expanduser(f"~/.claude/projects/{slug}/{sid}*.jsonl"))[0]
    sysp, items = [], []
    for line in open(f, encoding="utf-8"):
        d = json.loads(line)
        t = d.get("type")
        if t == "assistant":
            break
        if t == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") == "prompt_snapshot":
                sysp = [s if isinstance(s, str) else json.dumps(s) for s in a.get("systemPrompt") or []]
                continue
            items.append((a.get("type") + ":" + str(a.get("hookName") or ""), json.dumps(a, ensure_ascii=False, sort_keys=True)))
        elif t == "user":
            c = (d.get("message") or {}).get("content")
            items.append(("user", c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)))
    return sysp, items

(sa, ia), (sb, ib) = load(sys.argv[1]), load(sys.argv[2])
print(f"system sections: a={len(sa)} b={len(sb)}")
for i, (x, y) in enumerate(zip(sa, sb)):
    if x != y:
        print(f"  section {i} DIFFERS ({len(x)} vs {len(y)} chars): {x[:70]!r}")
        for l in list(difflib.unified_diff(x.splitlines(), y.splitlines(), lineterm="", n=0))[2:12]:
            print("     ", l[:160])
print(f"pre-call items: a={len(ia)} b={len(ib)}")
for i, ((ka, va), (kb, vb)) in enumerate(zip(ia, ib)):
    same = va == vb
    print(f"  {i:>2} {'same' if same else 'DIFF'} {ka:40} {len(va):>7,} chars")
    if not same:
        for l in list(difflib.unified_diff(va.replace('\\n', '\n').splitlines(), vb.replace('\\n', '\n').splitlines(), lineterm="", n=0))[2:10]:
            print("       ", l[:160])
