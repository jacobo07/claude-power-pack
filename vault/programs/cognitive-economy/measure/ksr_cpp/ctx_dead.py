"""KSR context-admission forensics v2 (PLAN-KSR-EPOCH-REHYDRATION s12 C, phase-4 fixes C1-C10, S1-S3).
Read-only, deterministic.

Modes:
  --manifest : freeze (file, size, sha256) for every top-level session file and draw the pre-registered
               10-session validation sample. Committed BEFORE --measure (S3).
  --measure  : whole-corpus dead carriage per class (the decision input, C4) + detector controls (C5)
               + the sample's per-session rows. Reads each file only up to its frozen size.

Definitions (pre-registered, phase-4 fixes):
  model call      : distinct message.id of a type=assistant line with usage, not isSidechain, model != <synthetic> (C2)
  residency       : from the call after admission until the next compact_boundary/isCompactSummary or file end (C7;
                    a file resumed from another is measured on its own: lower bound)
  pricing         : each resident call priced from that call's usage mix: cache_read share x0.1, 1h-write share x2,
                    5m-write share x1.25 (C3). The write-priced part is reported separately (RANK-4 overlap) and is
                    EXCLUDED from the >=3% decision.
  tokens          : chars / 3.6 (ESTIMATE); calibration control = estimated resident tokens / actual context (C1)
  distinctive     : token >=12 chars or line >=40 chars, present in tool results of exactly ONE session file
                    (df <= 1 file, ~1.4% of 73) and first seen in THIS result within the session (C5)
  used            : a distinctive probe appears in a later assistant text/tool input before residency ends;
                    items with <3 probes are UNMEASURED (never NOT_OBSERVED)
  dead carriage   : resident calls after max(admission, last observable use) -- an UPPER bound on waste, because
                    NOT_OBSERVED is a lower bound on use
  identical repeat: same tool + normalized input + identical sha256 of result, no compaction in between (C8)
  replaceable cand: >= 8k tokens and <= 10% of probes used (C10)
  decision        : a tool-output class (or all tool output) with READ-PRICED dead carriage >= 3% of the matching
                    weighted total -> candidate; computed with and without 489739e3 (C4). Semantic GC vs
                    admission compared in weighted tokens only (C9).
"""
import argparse, glob, hashlib, json, os, random, re, statistics, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctx_admission as ca

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "ctx_manifest.json")
SEED, EXCLUDE = 20261004, "489739e3"
TOK_RE = re.compile(r"[A-Za-z0-9_./\\:#-]{12,}")
CPT = 3.6


def h8(s):
    return hashlib.blake2b(s.encode("utf-8", "replace"), digest_size=8).digest()


def cand(text):
    out = {h8(t) for t in TOK_RE.findall(text)}
    for ln in text.splitlines():
        s = ln.strip()
        if len(s) >= 40:
            out.add(h8(s))
    return out


def rtext(c):
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")


def lines_of(fp, size):
    with open(fp, "rb") as fh:
        data = fh.read(size)
    for raw in data.splitlines():
        try:
            yield json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            continue


def parse(fp, size, plant=None):
    calls, seen, id2 = [], set(), {}
    results, uses, bounds = [], [], []
    for d in lines_of(fp, size):
        if d.get("isCompactSummary") or (d.get("type") == "system" and d.get("subtype") == "compact_boundary"):
            bounds.append(len(calls))
        if d.get("isSidechain"):
            continue
        m = d.get("message") or {}
        if d.get("type") == "assistant":
            u, mid = m.get("usage"), m.get("id")
            if u and mid and mid not in seen and m.get("model") != "<synthetic>":
                seen.add(mid)
                cc = u.get("cache_creation") or {}
                c1 = cc.get("ephemeral_1h_input_tokens", 0) or 0
                cwt = u.get("cache_creation_input_tokens", 0) or 0
                c5 = cc.get("ephemeral_5m_input_tokens") if cc.get("ephemeral_5m_input_tokens") is not None else cwt - c1
                cr = u.get("cache_read_input_tokens", 0) or 0
                inp = u.get("input_tokens", 0) or 0
                calls.append((cr, c1, c5, inp))
            for b in m.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    uses.append((len(calls), b.get("text", "")))
                elif b.get("type") == "tool_use":
                    ip = b.get("input") or {}
                    uses.append((len(calls), json.dumps(ip)))
                    id2[b.get("id")] = (b.get("name"), ip)
        elif d.get("type") == "user" and isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    nm, ip = id2.get(b.get("tool_use_id"), ("?", {}))
                    if nm == "Read":
                        cls, key = ca.read_class(ip.get("file_path")), ("Read", ip.get("file_path"), ip.get("offset"), ip.get("limit"))
                    elif nm in ("PowerShell", "Bash"):
                        pc = ca.ps_class(ip.get("command"))
                        cls, key = (pc if nm == "PowerShell" else "bash:" + pc[3:]), (nm, (ip.get("command") or "").strip())
                    else:
                        cls, key = "tool:" + str(nm), (nm, json.dumps(ip, sort_keys=True))
                    txt = rtext(b.get("content"))
                    results.append([len(calls), cls, key, ca.text_len(b.get("content")), txt])
    if plant:
        results.append([plant["at"], "tool:PLANT", ("PLANT",), 2000, plant["text"]])
        if plant.get("use_at") is not None:
            uses.append((plant["use_at"], plant["text"].split()[0]))
    return calls, results, uses, bounds


def df_pass(man):
    df = Counter()
    for f in man["files"]:
        _, results, _, _ = parse(f["path"], f["size"])
        s = set()
        for r in results:
            s |= cand(r[4])
        df.update(s)
    return df


def analyse(f, df, plant=None):
    calls, results, uses, bounds = parse(f["path"], f["size"], plant)
    n = len(calls)
    rr, rw = [0.0], [0.0]
    for cr, c1, c5, inp in calls:
        ctx = cr + c1 + c5 + inp
        rr.append(rr[-1] + (cr * 0.1 / ctx if ctx else 0))
        rw.append(rw[-1] + ((c1 * 2 + c5 * 1.25 + inp) / ctx if ctx else 0))
    idx = defaultdict(list)
    for c, tx in uses:
        for p in cand(tx):
            idx[p].append(c)
    seen_sess = set()
    per = defaultdict(Counter)
    last_key = {}
    for ci, cls, key, chars, txt in sorted(results, key=lambda r: r[0]):
        end = next((b for b in bounds if b > ci), n)
        pr = {p for p in cand(txt) if (df.get(p, 0) <= 1 or cls == "tool:PLANT") and p not in seen_sess}
        seen_sess |= cand(txt)
        tok = chars / CPT
        lo, hi = min(ci, n), min(end, n)
        c = per[cls]
        c["items"] += 1
        c["chars"] += chars
        c["carry_read_w"] += tok * (rr[hi] - rr[lo])
        c["carry_write_w"] += tok * (rw[hi] - rw[lo])
        if len(pr) < 3:
            c["unmeasured_items"] += 1
            c["unmeasured_read_w"] += tok * (rr[hi] - rr[lo])
            continue
        used = set()
        last = None
        for p in pr:
            for u in idx.get(p, ()):
                if ci < u <= end:
                    used.add(p)
                    last = u if last is None or u > last else last
        start_dead = min(max(ci, last or ci), n)
        c["dead_read_w"] += tok * (rr[hi] - rr[start_dead])
        c["dead_write_w"] += tok * (rw[hi] - rw[start_dead])
        c["measured_read_w"] += tok * (rr[hi] - rr[lo])
        c["not_observed_items" if last is None else "used_items"] += 1
        if tok >= 8000 and len(used) / len(pr) <= 0.10:
            c["replaceable_items"] += 1
            c["replaceable_read_w"] += tok * (rr[hi] - rr[lo])
        h = hashlib.sha256(txt.encode("utf-8", "replace")).hexdigest()
        prev = last_key.get(key)
        if prev and prev[0] == h and not any(prev[1] < b <= ci for b in bounds):
            c["repeat_items"] += 1
            c["repeat_read_w"] += tok * (rr[hi] - rr[lo])
        last_key[key] = (h, ci)
    wtot = sum(cr * 0.1 + c1 * 2 + c5 * 1.25 + inp for cr, c1, c5, inp in calls)
    ctx_sum = sum(sum(x) for x in calls)
    est = sum(per[k]["carry_read_w"] / 0.1 for k in per)  # resident token-calls from tool results only
    return per, wtot, ctx_sum, est, uses


def do_manifest():
    # CAMPAIGN COPY: population = top-level session files of the CPP corpus written in or after D-W7
    # (mtime >= 2026-09-26T00:00:00Z); everything else is the original instrument unchanged.
    files = sorted(f for f in glob.glob(os.path.join(ca.CORPUS, "*.jsonl")) if os.path.getmtime(f) >= 1790380800)
    rows = []
    for fp in files:
        b = open(fp, "rb").read()
        rows.append({"sid": os.path.basename(fp)[:8], "path": fp, "size": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    man = {"files": rows}
    pop = []
    for f in rows:
        if f["sid"] == EXCLUDE:
            continue
        calls, results, _, _ = parse(f["path"], f["size"])
        tot = sum(r[3] for r in results)
        if len(calls) < 20 or not tot:
            continue
        ps = sum(r[3] for r in results if r[1].startswith("ps:")) / tot
        unk = sum(r[3] for r in results if r[1] in ("read:unclassified", "ps:other")) / tot
        pop.append((f["sid"], ps, unk))
    shares = [p[1] for p in pop]
    q1, q2, q3 = statistics.quantiles(shares, n=4, method="inclusive")
    top = sorted(p[0] for p in pop if p[1] >= q3)
    low = sorted(p[0] for p in pop if p[1] <= q1)
    mid = sorted(p[0] for p in pop if q2 - 0.05 <= p[1] <= q2 + 0.05)
    rnd = random.Random(SEED)
    pick = [(s, "top-PS") for s in rnd.sample(top, 3)] + [(s, "mid-PS") for s in rnd.sample([m for m in mid if m not in top], 3)]
    chosen = {s for s, _ in pick}
    pick += [(s, "low-PS") for s in rnd.sample([x for x in low if x not in chosen], 2)]
    chosen = {s for s, _ in pick}
    rest = sorted([p for p in pop if p[0] not in chosen], key=lambda p: (-p[2], p[0]))[:2]
    pick += [(p[0], "high-unknown") for p in rest]
    man.update({"population_n": len(pop), "quartiles": [q1, q2, q3], "seed": SEED, "sample": pick,
                "rule": "S1-S3 of phase4_bc_gaps.md; population = top-level jsonl, >=20 model calls, excl 489739e3"})
    blob = json.dumps(man, indent=1, sort_keys=True)
    open(MANIFEST, "w", encoding="utf-8", newline="\n").write(blob)
    print("manifest sha256", hashlib.sha256(blob.encode()).hexdigest(), "files", len(rows), "population", len(pop))
    print("sample", pick)


def do_measure():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    df = df_pass(man)
    agg = {"all": defaultdict(Counter), "excl": defaultdict(Counter)}
    W = {"all": 0.0, "excl": 0.0}
    calib = [0.0, 0.0]
    sample_ids = {s for s, _ in man["sample"]}
    sample_rows = {}
    for f in man["files"]:
        per, wtot, ctx_sum, est, _ = analyse(f, df)
        for scope in ("all", "excl"):
            if scope == "excl" and f["sid"] == EXCLUDE:
                continue
            W[scope] += wtot
            for k, v in per.items():
                agg[scope][k].update(v)
        calib[0] += est
        calib[1] += ctx_sum
        if f["sid"] in sample_ids:
            t = sum(v["measured_read_w"] for v in per.values())
            sample_rows[f["sid"]] = {"measured_read_w": round(t), "dead_read_w": round(sum(v["dead_read_w"] for v in per.values())),
                                     "not_observed_items": sum(v["not_observed_items"] for v in per.values()),
                                     "used_items": sum(v["used_items"] for v in per.values())}
    # controls on the first sampled session (real file, planted items)
    f0 = next(f for f in man["files"] if f["sid"] == man["sample"][0][0])
    tok = "ZZPLANTQ1X9Y8W7V6U5"
    pos, *_ = analyse(f0, df, plant={"at": 1, "use_at": 3, "text": tok + " alpha\n" + tok + "-two\n" + tok + "-three planted line padded to forty characters"})
    neg, *_ = analyse(f0, df, plant={"at": 1, "use_at": None, "text": tok + " alpha\n" + tok + "-two\n" + tok + "-three planted line padded to forty characters"})
    ctrl = {"planted_used_detected": pos["tool:PLANT"]["used_items"] == 1,
            "planted_unused_not_observed": neg["tool:PLANT"]["not_observed_items"] == 1}
    # cross-session shuffle: probes of session i against uses of session i+1, per family
    fams = defaultdict(lambda: [0, 0, 0])
    files = [f for f in man["files"] if f["sid"] != EXCLUDE]
    for i, f in enumerate(files):
        _, results, uses_a, _ = parse(f["path"], f["size"])
        g = files[(i + 1) % len(files)]
        _, _, uses_b, _ = parse(g["path"], g["size"])
        ia = set().union(*[cand(t) for _, t in uses_a]) if uses_a else set()
        ib = set().union(*[cand(t) for _, t in uses_b]) if uses_b else set()
        for _, cls, _, _, txt in results:
            pr = {p for p in cand(txt) if df.get(p, 0) <= 1}
            if len(pr) < 3:
                continue
            fam = cls.split(":")[0]
            fams[fam][0] += 1
            fams[fam][1] += bool(pr & ia)
            fams[fam][2] += bool(pr & ib)
    ctrl["self_vs_cross_by_family"] = {k: {"n": v[0], "self": round(v[1] / v[0], 3), "cross": round(v[2] / v[0], 3),
                                           "ratio": round(v[1] / v[2], 2) if v[2] else None,
                                           "valid": (v[2] == 0 and v[1] > 0) or (v[2] and v[1] / v[2] >= 2)} for k, v in fams.items() if v[0]}
    ctrl["token_calibration_est_over_actual"] = round(calib[0] / calib[1], 4)
    out = {"manifest_sha256": hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest(), "controls": ctrl, "sample_rows": sample_rows}
    for scope in ("all", "excl"):
        rows = {}
        for k, v in agg[scope].items():
            rows[k] = {kk: round(vv, 1) if isinstance(vv, float) else vv for kk, vv in v.items()}
            rows[k]["dead_read_share"] = round(v["dead_read_w"] / W[scope], 5)
            rows[k]["carry_read_share"] = round(v["carry_read_w"] / W[scope], 5)
            rows[k]["unmeasured_read_share"] = round(v["unmeasured_read_w"] / W[scope], 5)
            rows[k]["repeat_read_share"] = round(v["repeat_read_w"] / W[scope], 5)
            rows[k]["replaceable_read_share"] = round(v["replaceable_read_w"] / W[scope], 5)
            rows[k]["dead_write_share_RANK4"] = round(v["dead_write_w"] / W[scope], 5)
        tool_rows = [r for k, r in rows.items() if k.split(":")[0] in ("read", "ps", "bash", "tool")]
        out[scope] = {"weighted_total": round(W[scope]), "classes": rows,
                      "tool_output_dead_read_share": round(sum(r["dead_read_share"] for r in tool_rows), 5),
                      "tool_output_carry_read_share": round(sum(r["carry_read_share"] for r in tool_rows), 5),
                      "tool_output_unmeasured_read_share": round(sum(r["unmeasured_read_share"] for r in tool_rows), 5),
                      "tool_output_replaceable_read_share": round(sum(r["replaceable_read_share"] for r in tool_rows), 5),
                      "tool_output_repeat_read_share": round(sum(r["repeat_read_share"] for r in tool_rows), 5)}
    blob = json.dumps(out, indent=1, sort_keys=True)
    open(os.path.join(HERE, "ctx_dead_out.json"), "w", encoding="utf-8", newline="\n").write(blob)
    print("sha256", hashlib.sha256(blob.encode()).hexdigest())
    print("controls", json.dumps(ctrl))
    for scope in ("all", "excl"):
        o = out[scope]
        print(f"[{scope}] weighted {o['weighted_total']/1e6:.1f}M | tool output: carry {100*o['tool_output_carry_read_share']:.2f}%"
              f" dead<= {100*o['tool_output_dead_read_share']:.2f}% unmeasured {100*o['tool_output_unmeasured_read_share']:.2f}%"
              f" replaceable {100*o['tool_output_replaceable_read_share']:.2f}% repeat {100*o['tool_output_repeat_read_share']:.2f}%")
        top = sorted(o["classes"].items(), key=lambda x: -x[1]["dead_read_share"])[:12]
        for k, r in top:
            print(f"   {k[:40]:40s} carry {100*r['carry_read_share']:5.2f}%  dead<= {100*r['dead_read_share']:5.2f}%  unmeas {100*r['unmeasured_read_share']:5.2f}%"
                  f"  repl {100*r['replaceable_read_share']:5.2f}%  rep {100*r['repeat_read_share']:5.2f}%  rank4w {100*r['dead_write_share_RANK4']:5.2f}%")
    print("sample", json.dumps(sample_rows))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--measure", action="store_true")
    a = ap.parse_args()
    if a.manifest:
        do_manifest()
    if a.measure:
        do_measure()
