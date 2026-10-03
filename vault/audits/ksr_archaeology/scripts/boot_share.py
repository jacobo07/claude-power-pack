"""T1 follow-up: (1) share of boot-window cost attributable to the hand-kept boot docs;
(2) instrument validity: self vs cross-session consumption over every boot-doc-reading session."""
import glob, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boot_facts as bf

files = sorted(glob.glob(os.path.join(bf.CORPUS, "*.jsonl")))
rows = []
for fp in files:
    sid = os.path.basename(fp)[:8]
    id2, seen = {}, set()
    turns = 0; doc_chars = 0; other_chars = 0; done = False; c0 = c1 = None
    for line in open(fp, encoding="utf-8", errors="replace"):
        try: d = json.loads(line)
        except Exception: continue
        m = d.get("message") or {}
        if d.get("type") == "assistant" and not done:
            u = m.get("usage")
            if u and m.get("id") not in seen:
                seen.add(m.get("id")); turns += 1
                ctx = (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("input_tokens") or 0)
                c0 = ctx if c0 is None else c0; c1 = ctx
            for b in m.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    if b.get("name") in ("Edit", "Write", "NotebookEdit"): done = True
                    elif not done: id2[b.get("id")] = (b.get("name"), b.get("input") or {})
        elif d.get("type") == "user" and not done and isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in id2:
                    nm, inp = id2.pop(b["tool_use_id"])
                    body = b.get("content"); n = len(body) if isinstance(body, str) else len(bf.text_of(body))
                    if nm == "Read" and os.path.normcase(inp.get("file_path", "")) in bf.BOOT: doc_chars += n
                    else: other_chars += n
    if turns: rows.append((sid, turns, doc_chars, other_chars, (c1 or 0) - (c0 or 0)))

with_docs = [r for r in rows if r[2] > 0]; without = [r for r in rows if r[2] == 0]
tot_doc = sum(r[2] for r in rows); tot_other = sum(r[3] for r in rows)
med = lambda xs: statistics.median(xs) if xs else 0
print("sessions", len(rows), "| with boot-doc reads", len(with_docs), "| without", len(without))
print("boot-window tool-result chars: boot docs", tot_doc, "other", tot_other, "doc share %.1f%%" % (100 * tot_doc / max(tot_doc + tot_other, 1)))
print("median boot turns  with docs", med([r[1] for r in with_docs]), " without", med([r[1] for r in without]))
print("median ctx growth  with docs", med([r[4] for r in with_docs]), " without", med([r[4] for r in without]))

# instrument validity over every session that read a boot doc
recs = [bf.analyse(f) for f in files]
recs = [r for r in recs if r["boot_reads"] and r["sid"] not in bf.EXCLUDE]
self_r, cross_r = [], []
for i, a in enumerate(recs):
    srcs = a["_sources"]
    if not srcs or len(recs) < 2: continue
    b = recs[(i + 1) % len(recs)]
    self_r.append(len(a["consumed"]) / len(srcs))
    cross_r.append(sum(1 for f in srcs if any(f in tx for _, tx in b["_later"])) / len(srcs))
print("instrument over n=%d boot-doc sessions: self consumption mean %.3f, cross-session mean %.3f" % (len(self_r), statistics.mean(self_r), statistics.mean(cross_r)))
