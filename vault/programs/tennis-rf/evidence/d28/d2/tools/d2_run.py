"""WU-D2 steps 1 (causality) and 4 (leave-one-fact-out attribution). Runs on GEX44, m2c + lint only, NO compile.
    KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python d2_run.py <out_dir> <w12_records.jsonl> [--jobs 20]
Outputs: causality.json, shock_attribution.json (+ ctx/ variant headers).
"""
import json, os, re, sys, random, collections, multiprocessing as mp

M = "/home/kobii/missions/tennis-w11"
OUT = sys.argv[1]
W12REC = sys.argv[2]
JOBS = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 20
P1 = M + "/out/p1p2"
sys.path.insert(0, P1 + "/tools")
import m2c_run as R  # noqa: E402  (also puts decomp + gex44 on sys.path)
import tennis_context, source_lint  # noqa: E402

P = R.P
HEADER = open(P1 + "/ctx/tennis_context.h", encoding="utf-8").read()
WORD = lambda w: re.compile(r"\b%s\b" % re.escape(w))


# ---------------------------------------------------------------- header model
def split_header(h):
    """-> (prelude_text, chunks). chunk = (kind, text, defined_tag or None). kinds: comment, struct, line."""
    lines = h.split("\n")
    end = next(i for i, l in enumerate(lines) if l.startswith("typedef double f64;"))
    prelude = "\n".join(lines[:end + 1])
    chunks, i = [], end + 1
    while i < len(lines):
        l = lines[i]
        if l.startswith("/*") and "*/" not in l:  # multi-line comment
            j = i
            while "*/" not in lines[j]:
                j += 1
            chunks.append(("comment", "\n".join(lines[i:j + 1]), None)); i = j + 1
        elif re.match(r"typedef struct (\w+) \{", l):
            tag = re.match(r"typedef struct (\w+) \{", l).group(1)
            j = i
            while not re.match(r"\} %s;" % tag, lines[j]):
                j += 1
            chunks.append(("struct", "\n".join(lines[i:j + 1]), tag)); i = j + 1
        else:
            chunks.append(("comment" if l.startswith("/*") or not l.strip() else "line", l, None)); i += 1
    return prelude, chunks


PRELUDE, CHUNKS = split_header(HEADER)
TAGS = sorted({t for k, _, t in CHUNKS if k == "struct"})


def render(chunks):
    return PRELUDE + "\n" + "\n".join(c[1] for c in chunks) + "\n"


def drop_tag(tag):
    """Remove the struct `tag`, its forward decl, and (to a fixed point) every struct/prototype/extern that names a
    removed tag. Returns (text, removed_tags)."""
    removed = {tag}
    keep = list(CHUNKS)
    changed = True
    while changed:
        changed = False
        new = []
        for kind, text, dt in keep:
            if kind == "comment":
                new.append((kind, text, dt)); continue
            names = set(re.findall(r"\b\w+\b", text))
            if (kind == "struct" and dt in removed) or (names & removed):
                if kind == "struct" and dt not in removed:
                    removed.add(dt)
                changed = True
                continue
            new.append((kind, text, dt))
        keep = new
    return render(keep), sorted(removed)


# ---------------------------------------------------------------- step 1: causality
def causality():
    recs = [json.loads(l) for l in open(W12REC, encoding="utf-8") if l.strip()]
    judged = [r["fn"] for r in recs if r["verdict"] != "EXCLUDED_LINT_UNK_FIELD"]
    members = tennis_context.members(HEADER)
    externs = re.findall(r"^extern\s+[^;]*?\b(\w+)\s*(?:\[[^\]]*\])?\s*;", HEADER, re.M)
    protos = {}
    for kind, text, _ in CHUNKS:
        if kind == "line":
            m = re.match(r"[\w\s\*]+?\b(fn_[0-9A-Fa-f]+)\s*\(", text)
            if m:
                protos[m.group(1)] = text
    rows = []
    for fn in judged:
        path = "%s/out/w12/m2c/c/main_%s.c" % (M, fn[3:])
        src = source_lint.strip_noise(open(path, encoding="utf-8").read())
        used_tags = [t for t in TAGS if WORD(t).search(src)]
        used_fields = []
        for t in used_tags:
            for name, _off in members.get(t, []):
                if re.search(r"(?:->|\.)\s*%s\b" % re.escape(name), src):
                    used_fields.append("%s.%s" % (t, name))
        prelude_used = [t for t in tennis_context.M2C_TYPES.replace(";", " ").split() if t in
                        ("s8", "s16", "s32", "s64", "u8", "u16", "u32", "u64", "f32", "f64") and WORD(t).search(src)]
        ext_used = [e for e in externs if WORD(e).search(src)]
        own_proto = fn in protos
        called_protos = sorted(f for f in protos if f != fn and WORD(f).search(src))
        facts = used_tags + used_fields + ["prelude:" + p for p in prelude_used] + ["extern:" + e for e in ext_used] \
            + (["proto:" + fn] if own_proto else []) + ["proto:" + c for c in called_protos]
        rows.append(dict(fn=fn, verdict=next(r["verdict"] for r in recs if r["fn"] == fn), used_tags=used_tags,
                         used_fields=sorted(used_fields), prelude_types=sorted(set(prelude_used)), externs=ext_used,
                         own_prototype=own_proto, called_prototypes=called_protos, n_header_facts_used=len(facts),
                         source_sha=path.split("/")[-1]))
    never = sorted(set(TAGS) - {t for r in rows for t in r["used_tags"]})
    json.dump(dict(n_rows=len(rows), n_header_tags=len(TAGS), tags_never_used_by_judged=never, rows=rows,
                   method="word/member grep of out/w12/m2c/c/main_<addr>.c (m2c --context output) against the header model; "
                          "fields attributed to tags that also appear in the same source",
                   ), open(OUT + "/causality.json", "w"), indent=1, sort_keys=True)
    print("CAUSALITY rows=%d tags=%d never_used=%d" % (len(rows), len(TAGS), len(never)))


# ---------------------------------------------------------------- step 4: attribution
def eval_variant(task):
    vid, ctxpath, ctxtext, job = task
    R.G.update(flags=P.build_flags(False, ctxpath), context=ctxpath, ctx_text=ctxtext, arm="ctx")
    try:
        rec, _ = R.one(job)
        return vid, job[0], bool(rec["clean"]), rec["status"], rec.get("lint_codes")
    except Exception as e:
        return vid, job[0], False, "EXC:" + type(e).__name__, []


def attribution():
    def clean_set(run):
        p = "%s/m2c/%s/records.jsonl" % (P1, run)
        return {json.loads(l)["fn"] for l in open(p) if json.loads(l)["clean"]}
    ks = json.load(open(P1 + "/knowledge_shock.json"))
    after = before = None
    for a in ("ctx_run2", "ctx_run1"):
        for b in ("noctx_run2", "noctx_run1"):
            ca, cb = clean_set(a), clean_set(b)
            if (len(cb), len(ca)) == (ks["clean_before"], ks["clean_after"]):
                after, before = (a, ca), (b, cb)
                break
        if after:
            break
    assert after, "cannot reproduce 175/276 from the p1p2 runs"
    newly = sorted(after[1] - before[1])
    assert len(newly) == ks["newly_clean"], (len(newly), ks["newly_clean"])

    facts = {json.loads(l)["fn"]: json.loads(l) for l in open(P1 + "/facts.jsonl")}
    text, tables = P.blocks(R.ASM)
    jobs = {}
    for fn in newly:
        block, extra = text[fn], []
        for t in sorted(set(P.TABLE_REF.findall(block))):
            if t in tables:
                block, tab = P.adapt_table(block, tables[t], fn, int(facts[fn]["addr"], 16))
                extra.append(tab)
        jobs[fn] = (fn, facts[fn]["addr"], block, extra)

    os.makedirs(OUT + "/ctx", exist_ok=True)
    variants = {"FULL": HEADER, "EMPTY(prelude only)": PRELUDE + "\n"}
    removed_by = {}
    for t in TAGS:
        txt, rem = drop_tag(t)
        variants["drop:" + t] = txt
        removed_by[t] = rem
    rng = random.Random(20261013)
    fake = ["Zz%08x" % rng.getrandbits(32) for _ in range(5)]
    for f in fake:  # red control: a struct name that is not in the header
        txt, rem = drop_tag(f)
        assert rem == [f]
        variants["red:" + f] = txt
    paths = {}
    for vid, txt in variants.items():
        p = "%s/ctx/ctx_%s.h" % (OUT, re.sub(r"\W", "_", vid))
        open(p, "w", encoding="utf-8").write(txt)
        paths[vid] = p
    # warm every variant's m2c context cache serially so workers only read it
    R.init(P.build_flags(False, paths["FULL"]), paths["FULL"], "ctx")
    for vid in variants:
        R.G.update(flags=P.build_flags(False, paths[vid]), context=paths[vid], ctx_text=variants[vid], arm="ctx")
        R.one(jobs[newly[0]])
    tasks = [(vid, paths[vid], variants[vid], jobs[fn]) for vid in variants for fn in newly]
    res = collections.defaultdict(dict)
    with mp.get_context("fork").Pool(JOBS, initializer=R.init, initargs=(P.build_flags(False, paths["FULL"]), paths["FULL"], "ctx")) as pool:
        for vid, fn, clean, status, codes in pool.imap_unordered(eval_variant, tasks, chunksize=8):
            res[vid][fn] = (clean, status, codes)
    full_clean = {fn for fn in newly if res["FULL"][fn][0]}
    not_reproduced = sorted(set(newly) - full_clean)
    empty_clean = sorted(fn for fn in newly if res["EMPTY(prelude only)"][fn][0])
    crit = {}  # fn -> sorted tags whose drop makes fn dirty
    for fn in full_clean:
        crit[fn] = sorted(t for t in TAGS if not res["drop:" + t][fn][0])
    alone = collections.defaultdict(list); shared = collections.defaultdict(list)
    credit = collections.defaultdict(float)
    redundant = []
    for fn, c in sorted(crit.items()):
        if not c:
            redundant.append(fn)
        elif len(c) == 1:
            alone[c[0]].append(fn); credit[c[0]] += 1.0
        else:
            for t in c:
                shared[t].append(fn); credit[t] += 1.0 / len(c)
    per_fact = []
    for t in TAGS:
        per_fact.append(dict(tag=t, also_removed_by_cascade=[x for x in removed_by[t] if x != t],
                             alone=sorted(alone[t]), n_alone=len(alone[t]),
                             needs_with_others=sorted(shared[t]), n_needs_with_others=len(shared[t]),
                             credit=round(credit[t], 4)))
    per_fact.sort(key=lambda r: (-r["n_alone"], -r["credit"], r["tag"]))
    for i, r in enumerate(per_fact, 1):
        r["rank"] = i
    n_alone = sum(len(v) for v in alone.values())
    n_shared = sum(1 for c in crit.values() if len(c) > 1)
    red_changes = {v: sum(1 for fn in newly if res[v][fn][0] != res["FULL"][fn][0]) for v in variants if v.startswith("red:")}
    out = dict(
        shock=dict(clean_before=len(before[1]), clean_after=len(after[1]), newly_clean=len(newly), sources=[before[0], after[0]]),
        method="leave-one-fact-out: a fact = one header struct tag; its variant header drops the struct, its forward decl and "
               "(fixed point) every struct/prototype/extern naming a removed tag; m2c --context + source_lint only, NO compile; "
               "evaluated on the %d newly-clean functions (the 175 clean-without-header are not re-tested; knowledge_shock "
               "newly_dirty=[])" % len(newly),
        n_tags=len(TAGS),
        reconcile=dict(newly_clean=len(newly), alone_sum=n_alone, shared_functions=n_shared, redundant_no_single_tag=len(redundant),
                       not_reproduced_with_full_header=len(not_reproduced), clean_with_prelude_only=len(empty_clean),
                       sum_check=(n_alone + n_shared + len(redundant) + len(not_reproduced)) == len(newly),
                       credit_total=round(sum(credit.values()), 4)),
        residual=dict(redundant_no_single_tag=redundant, not_reproduced=not_reproduced, clean_with_prelude_only=empty_clean,
                      note="redundant = clean with the header and still clean after every single-tag drop (disjunctive support "
                           "or the facts it uses are in more than one tag); not_reproduced = m2c rerun disagrees with the p1p2 run"),
        red_control=dict(fake_names=fake, functions_changed_vs_full=red_changes, passed=all(v == 0 for v in red_changes.values())),
        per_fact=per_fact,
        critical_sets={fn: c for fn, c in sorted(crit.items())},
    )
    json.dump(out, open(OUT + "/shock_attribution.json", "w"), indent=1, sort_keys=True)
    print("ATTRIBUTION newly=%d alone=%d shared=%d redundant=%d not_repro=%d red=%s" % (
        len(newly), n_alone, n_shared, len(redundant), len(not_reproduced), red_changes))
    for r in per_fact[:10]:
        print(r["rank"], r["tag"], r["n_alone"], r["n_needs_with_others"], r["credit"])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    causality()
    attribution()
    print("D2_RUN_DONE")
