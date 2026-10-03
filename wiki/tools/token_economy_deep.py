"""Deep cuts over 7 d of MAIN-thread transcripts (zero model quota, read-only).

Transcript lines are NOT what the model sees: some attachments are UI records (a 1.85 MB
hook_success moved measured context by 864 tok; a 145 KB prompt_snapshot copy of the system
prompt by 503), images are stored as base64 but billed as images, large outputs are persisted
to disk with a preview. So per-kind reach is FITTED, not assumed:

  measured ctx(k+1) - ctx(k)  ~=  sum_kind  coef[kind] * chars[kind]  + coef_img * images

over every inter-call interval with no compaction (non-negative least squares). coef is tokens
that reached the context per stored character (0 = not sent). Lifetime cost of an item =
coef * chars * (1 write + N later calls that re-read it).

[R] lifetime re-read cost by kind   [P] mid-session prefix rebuild causes
[T] thinking share of output        [S] Read shapes   [H] API calls per human prompt
USD is an ESTIMATE at list price (Opus 5.5 cache_read). Usage is MEASURED, deduplicated by id.
"""
import json, os, sqlite3, sys, time
from collections import Counter, defaultdict
import numpy as np

sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import usage_index as ui

T0 = time.time()
p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
prices = ui.load_prices()
END = c.execute("select max(ts) from calls").fetchone()[0]
START = END - 7 * 86400
files = [r[0] for r in c.execute(
    "select file from calls where is_sub=0 and ts>? and ts<=? group by file having count(*)>=2",
    (START, END))]
OPUS = ui.price_for("claude-opus-5-5", prices)[0]
CR = OPUS["cache_read"] / 1e6
CW = OPUS["cache_write_1h"] / 1e6


def clen(x):
    if x is None:
        return 0
    return len(x) if isinstance(x, str) else len(json.dumps(x, ensure_ascii=False))


def ts_of(d):
    t = d.get("timestamp")
    try:
        return time.mktime(time.strptime(t[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    except Exception:
        return None


def result_parts(content):
    """(text chars, image count) of a tool_result content."""
    if isinstance(content, list):
        ch = 0; img = 0
        for b in content:
            if isinstance(b, dict) and b.get("type") == "image":
                img += 1
            else:
                ch += clen(b.get("text") if isinstance(b, dict) and "text" in b else b)
        return ch, img
    return clen(content), 0


intervals = []            # (delta, Counter(kind->chars))
items_all = []            # (kind, chars, calls_after, label, file)
rebuild = Counter(); rebuild_usd = Counter(); rebuild_n = 0
think = 0; out_total = 0; effort = Counter()
reads = reread = read_full = read_paged = 0
calls_per_prompt = []
n_files = 0

for f in files:
    try:
        fh = open(f, encoding="utf-8")
    except OSError:
        continue
    n_files += 1
    tool_names = {}; tool_inputs = {}; seen = set()
    calls = []; seg_items = []; cur = Counter(); compact = False
    read_paths = Counter(); in_prompt = False; prompt_calls = 0

    def close():
        n_end = len(calls)
        for kind, ch, n_at, label in seg_items:
            if n_at < n_end:
                items_all.append((kind, ch, n_end - n_at, label, os.path.basename(f)))
        seg_items.clear()

    def add(kind, ch, label=""):
        if ch <= 0:
            return
        seg_items.append((kind, ch, len(calls), label)); cur[kind] += ch

    for line in fh:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        t = d.get("type")
        if t == "system" and d.get("subtype") == "compact_boundary":
            close(); compact = True; cur = Counter()
            continue
        if t == "assistant":
            m = d.get("message") or {}
            mid = m.get("id")
            # "<synthetic>" rows are client-made (usage-limit notices, "No response requested.",
            # connection errors), not model calls. Counting them made every return from a limit
            # wait read as a "model switch" (2026-10-03, token_economy_model_switch.py --synthetic).
            if mid and mid not in seen and m.get("model") != "<synthetic>":
                seen.add(mid)
                u = m.get("usage") or {}
                ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                cw = u.get("cache_creation_input_tokens") or 0
                cw5 = (u.get("cache_creation") or {}).get("ephemeral_5m_input_tokens") or 0
                out_total += u.get("output_tokens") or 0
                think += (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0
                effort[str(d.get("effort"))] += 1
                ts = ts_of(d)
                if calls and not compact:
                    intervals.append((ctx - calls[-1][1], cur))
                if calls and cw > 50_000:
                    gap = (ts - calls[-1][0]) if (ts and calls[-1][0]) else None
                    pm = calls[-1][2]
                    if compact:
                        cause = "after compaction"
                    elif pm and m.get("model") and pm != m.get("model"):
                        cause = "model switch"
                    elif gap is not None and gap > 3600:
                        cause = "idle > 1h (TTL expired)"
                    elif gap is not None and gap > 300 and cw5 > 0:
                        cause = "idle > 5m on 5m TTL"
                    elif gap is not None and gap > 300:
                        cause = "idle 5m-1h on 1h TTL (not TTL)"
                    elif cw >= 0.8 * ctx:
                        cause = "full rebuild, gap <= 5m"
                    else:
                        cause = "partial rebuild, gap <= 5m"
                    rebuild[cause] += 1; rebuild_n += 1; rebuild_usd[cause] += cw * CW
                seg_items.append(("_per_call_const", 1, len(calls), ""))  # unrecorded per-call injection
                calls.append((ts, ctx, m.get("model")))
                cur = Counter(); compact = False
                if in_prompt:
                    prompt_calls += 1
            for blk in m.get("content") or []:
                bt = blk.get("type")
                if bt == "tool_use":
                    tool_names[blk.get("id")] = blk.get("name"); tool_inputs[blk.get("id")] = blk.get("input") or {}
                    add("asst:tool_use", clen(blk.get("input")), blk.get("name"))
                elif bt == "text":
                    add("asst:text", len(blk.get("text") or ""))
                elif bt == "thinking":
                    add("asst:thinking", len(blk.get("thinking") or ""))
        elif t == "user":
            m = d.get("message") or {}
            cont = m.get("content")
            if isinstance(cont, str):
                if not d.get("isMeta"):
                    if in_prompt:
                        calls_per_prompt.append(prompt_calls)
                    in_prompt = True; prompt_calls = 0
                add("user:text", len(cont))
                continue
            for blk in cont or []:
                if blk.get("type") == "tool_result":
                    tid = blk.get("tool_use_id"); name = tool_names.get(tid, "?")
                    ch, img = result_parts(blk.get("content"))
                    inp = tool_inputs.get(tid) or {}
                    kind = "tool:" + name; label = name
                    if name == "Read":
                        fp = inp.get("file_path", ""); reads += 1
                        reread += 1 if read_paths[fp] else 0; read_paths[fp] += 1
                        if inp.get("limit") or inp.get("offset"):
                            read_paged += 1; kind = "tool:Read(paged)"
                        else:
                            read_full += 1; kind = "tool:Read(full)"
                        label = os.path.basename(fp)
                    elif name in ("PowerShell", "Bash"):
                        label = (inp.get("command") or "")[:70].replace("\n", " ")
                    if img:
                        kind_i = "tool:image(count)"
                        seg_items.append((kind_i, img, len(calls), label)); cur[kind_i] += img
                    add(kind, ch, label)
                elif blk.get("type") == "text":
                    add("user:text", len(blk.get("text") or ""))
        elif t == "attachment":
            a = d.get("attachment") or {}
            add("attach:" + str(a.get("type")), clen(a), str(a.get("hookName") or a.get("type"))[:60])
    if in_prompt:
        calls_per_prompt.append(prompt_calls)
    close(); fh.close()

# ---- fit per-kind reach coefficients (NNLS by active-set clipping) ----
kind_tot = Counter()
for _, cv in intervals:
    kind_tot.update(cv)
kinds = [k for k, v in kind_tot.most_common() if v > 0][:40] + ["_per_call_const"]
idx = {k: i for i, k in enumerate(kinds)}
X = np.zeros((len(intervals), len(kinds))); y = np.zeros(len(intervals))
for r, (dl, cv) in enumerate(intervals):
    y[r] = dl
    X[r, idx["_per_call_const"]] = 1.0   # fixed tokens per call that the transcript does not record
    for k, v in cv.items():
        if k in idx:
            X[r, idx[k]] = v
keep = (y >= 0) & (y < 400_000)
X, y = X[keep], y[keep]
active = list(range(len(kinds)))
coef = np.zeros(len(kinds))
for _ in range(len(kinds)):
    sol, *_ = np.linalg.lstsq(X[:, active], y, rcond=None)
    if (sol >= 0).all():
        coef[:] = 0; coef[active] = sol; break
    active = [a for a, s in zip(active, sol) if s >= 0]
pred = X @ coef
r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()

print(f"window {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime(START))} -> {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime(END))}; "
      f"main transcripts={n_files}; intervals fitted={int(keep.sum()):,}; R^2={r2:.3f}; runtime={time.time()-T0:.0f}s")
print("\n[C] fitted reach: tokens reaching context per stored char (0 = not sent; ~0.25 = sent as text)")
for k in kinds:
    unit = "tok/image" if k == "tool:image(count)" else "tok/call" if k == "_per_call_const" else "tok/char"
    flag = "  CONFOUNDED (>0.6 tok/char is not text)" if unit == "tok/char" and coef[idx[k]] > 0.6 else ""
    print(f"  {k:36} coef={coef[idx[k]]:.3f} {unit}   stored={kind_tot[k]:>14,}{flag}")

life = Counter(); ins = Counter(); cnt = Counter(); tops = []
for kind, ch, after, label, fn in items_all:
    k = coef[idx[kind]] if kind in idx else 0.0
    tok = k * ch
    life[kind] += tok * after; ins[kind] += tok; cnt[kind] += 1
    tops.append((tok * after, kind, label, fn))
tot = sum(life.values()); tot_usd = sum(life[k] * CR + ins[k] * CW for k in life)
print(f"\n[R] lifetime cost by kind = write once (1h rate) + re-read on every later call (Opus 5.5 rates)")
print(f"  {'kind':36} {'items':>8} {'ins Mtok':>9} {'reread Btok':>12} {'share':>6} {'usd':>7}")
for k, v in sorted(life.items(), key=lambda x: -x[1])[:22]:
    print(f"  {k:36} {cnt[k]:>8,} {ins[k]/1e6:>9.1f} {v/1e9:>12.2f} {v/tot:>6.1%} {v*CR+ins[k]*CW:>7,.0f}")
print(f"  TOTAL growth items: re-read {tot/1e9:.2f} B tok, ~usd {tot_usd:,.0f} (floor not included: it is not in the transcript as items)")

print("\n[R2] top 12 single items by lifetime re-read tokens")
for v, kind, label, fn in sorted(tops, reverse=True)[:12]:
    print(f"  {v/1e6:>7.1f} Mtok  {kind:24} {str(label)[:56]!r:60} {fn[:12]}")

print(f"\n[P] mid-session prefix rebuilds (cw > 50k, not first call): n={rebuild_n}")
for k, v in rebuild.most_common():
    print(f"  {k:36} n={v:>5}  ~usd {rebuild_usd[k]:>6,.0f}")
print(f"\n[T] output={out_total:,}; thinking={think:,} ({think/max(out_total,1):.1%} of output); effort: {effort.most_common(4)}")
print(f"\n[S] Read calls={reads:,}; full={read_full:,} paged={read_paged:,}; re-read of an already-read path={reread:,} ({reread/max(reads,1):.1%})")
cpp = sorted(calls_per_prompt)
q = lambda x: cpp[min(len(cpp) - 1, int(len(cpp) * x))]
print(f"\n[H] human prompts={len(cpp):,}; API calls per prompt p50/p90/p99/max = {q(.5)}/{q(.9)}/{q(.99)}/{cpp[-1]}; mean={sum(cpp)/len(cpp):.1f}")
