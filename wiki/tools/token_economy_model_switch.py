"""A4: where do mid-session model switches come from? (zero model quota, read-only)

Same population and cause rule as token_economy_deep.py [P]: main-thread transcripts with >= 2
calls in the 7 d window ending at the newest indexed call; a "model switch" rebuild is a call
writing > 50k cache tokens whose model differs from the previous call's, with no compaction
between. For every model change (rebuild or not) we record from->to and what sits between the
two calls: user prompt text, slash commands, system subtypes, attachment types.
"""
import json, os, re, sqlite3, sys
from collections import Counter

sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
END = c.execute("select max(ts) from calls").fetchone()[0]
START = END - 7 * 86400
files = [r[0] for r in c.execute(
    "select file from calls where is_sub=0 and ts>? and ts<=? group by file having count(*)>=2",
    (START, END))]
prices = ui.load_prices()
CW = ui.price_for("claude-opus-5-5", prices)[0]["cache_write_1h"] / 1e6

pairs = Counter(); pairs_rebuild = Counter(); between = Counter(); between_rebuild = Counter()
usd = Counter(); examples = {}; n_switch = n_rebuild = 0; files_with = set()
CMD = re.compile(r"<command-name>\s*(/[\w:.-]+)")
# deep.py [P] counts "<synthetic>" rows (client-made, e.g. a usage-limit notice) as a model;
# --synthetic reproduces that count so the two instruments can be reconciled.
INCLUDE_SYNTHETIC = "--synthetic" in sys.argv


def marks(ev):
    out = set()
    for e in ev:
        out.add(e)
    return out or {"(nothing recorded)"}


for f in files:
    try:
        fh = open(f, encoding="utf-8")
    except OSError:
        continue
    prev_model = None; seen = set(); ev = []; compact = False
    for line in fh:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        t = d.get("type")
        if t == "system":
            st = d.get("subtype") or "?"
            if st == "compact_boundary":
                compact = True
            ev.append("system:" + st)
            continue
        if t == "attachment":
            a = d.get("attachment") or {}
            ev.append("attachment:" + str(a.get("type")))
            continue
        if t == "user":
            m = d.get("message") or {}
            cont = m.get("content")
            if isinstance(cont, str):
                cm = CMD.search(cont)
                if cm:
                    ev.append("cmd:" + cm.group(1))
                elif not d.get("isMeta"):
                    ev.append("user:prompt")
                else:
                    ev.append("user:meta")
            continue
        if t != "assistant":
            continue
        m = d.get("message") or {}
        mid = m.get("id"); model = m.get("model")
        if not mid or mid in seen or not model:
            continue
        if model == "<synthetic>" and not INCLUDE_SYNTHETIC:
            continue
        seen.add(mid)
        u = m.get("usage") or {}
        cw = u.get("cache_creation_input_tokens") or 0
        if prev_model and model != prev_model and not compact:
            n_switch += 1; files_with.add(f)
            key = f"{prev_model} -> {model}"
            pairs[key] += 1
            mk = marks(ev)
            for x in mk:
                between[x] += 1
            if cw > 50_000:
                n_rebuild += 1; pairs_rebuild[key] += 1; usd[key] += cw * CW
                for x in mk:
                    between_rebuild[x] += 1
                examples.setdefault(key, []).append((os.path.basename(f)[:8], d.get("timestamp", "")[:16], sorted(mk)[:6]))
        prev_model = model; ev = []; compact = False

print(f"window {START:.0f}..{END:.0f}  files {len(files)}  model changes {n_switch} in {len(files_with)} files"
      f"  of which rebuilds (>50k write) {n_rebuild}")
print("\n[pairs] all changes / rebuilds / est USD of rebuilds")
for k, v in pairs.most_common():
    print(f"  {v:4d} {pairs_rebuild[k]:4d} ${usd[k]:7.2f}  {k}")
print("\n[between] events between the two calls -- all changes / rebuilds")
for k, v in between.most_common(30):
    print(f"  {v:4d} {between_rebuild[k]:4d}  {k}")
print("\n[examples] up to 4 per rebuild pair")
for k, ex in examples.items():
    print("  " + k)
    for e in ex[:4]:
        print("     ", e)
