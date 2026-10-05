"""K5: Original Obligation Set for InfinityOps odr-device-trust Phase 4, extracted READ-ONLY by quotation. Zero-model.
Every row quotes its source line; type is a KEYWORD HEURISTIC (flagged), never an invention of obligations."""
import glob, os, re, sys
D = r"C:\Users\User\Apps\io-device-trust\.planning\workstreams\odr-device-trust"
OUT = sys.argv[1]
def lines(p): return open(p, encoding="utf-8", errors="replace").read().splitlines()
def typ(t):
    x = t.lower()
    for k, ks in (("security", ("secur", "secret", "credential", "signing", "crypto", "csrf", "xss", "inject")), ("authority", ("authority", "founder", "approv", "ownership", "owner ", "permission", "authoriz")),
                  ("observability", ("log", "metric", "observab", "audit", "telemetry", "alert", "trace")), ("production-reality", ("production", "prod ", "live ", "deploy", "staging", "real ", "seam")),
                  ("proof", ("prove", "proof", "test", "verif", "evidence", "drill", "measured")), ("invariant", ("never", "must not", "always", "idempot", "exactly", "only ", "invariant")),
                  ("deliverable", ("ui", "screen", "page", "component", "document", "deliver", "route", "endpoint"))):
        if any(w in x for w in ks): return k
    return "requirement"
req = os.path.join(D, "REQUIREMENTS.md"); road = os.path.join(D, "ROADMAP.md")
ph = glob.glob(os.path.join(D, "phases", "04*"))
ph = ph[0] if ph else ""
ctx = os.path.join(ph, "04-CONTEXT.md"); ui = os.path.join(ph, "04-UI-SPEC.md"); rs = os.path.join(ph, "04-RESEARCH.md")
R = lines(road)
start = next((i for i, l in enumerate(R) if re.search(r"^#{2,4}\s*Phase 4\b", l)), None)
if start is None: start = next(i for i, l in enumerate(R) if re.search(r"Phase 4\b", l))
end = next((i for i in range(start + 1, len(R)) if re.search(r"^#{2,4}\s*Phase 5\b", R[i]) or (re.match(r"^#{2,3}\s", R[i]) and i > start + 1 and "Phase 4" not in R[i])), len(R))
sec = R[start:end]
ids = []
for l in sec:
    for m in re.findall(r"\b([A-Z][A-Z0-9]{1,6}-\d{1,3}[a-z]?)\b", l):
        if m not in ids and not m.startswith("D-"): ids.append(m)
O = ["# Original Obligation Set -- InfinityOps odr-device-trust Phase 4 (Gen3 T1 K5)", "",
     "Read-only extraction by quotation from `C:\\Users\\User\\Apps\\io-device-trust\\.planning\\workstreams\\odr-device-trust\\`. No obligation is invented: every row quotes a source line.",
     "`type` is a KEYWORD HEURISTIC (security/authority/observability/production-reality/proof/invariant/deliverable, else requirement) -- UNREVIEWED; a human may re-type a row, the quote and source stay.", ""]
rows, flags = [], []
Q = lines(req); found = set()
for i, l in enumerate(Q):
    for m in re.findall(r"\b([A-Z][A-Z0-9]{1,6}-\d{1,3}[a-z]?)\b", l):
        if m in ids and m not in found and re.match(r"^\s*([-*|]|\d+\.)", l):
            found.add(m); rows.append((m, re.sub(r"\s+", " ", l.strip())[:400], f"REQUIREMENTS.md:{i+1}", typ(l)))
for m in ids:
    if m not in found: flags.append(f"{m} is named in ROADMAP Phase 4 but has no list/table line in REQUIREMENTS.md (AMBIGUOUS: obligation text not found)")
n = 0
for j, l in enumerate(sec):
    if re.search(r"success criteria", l, re.I):
        for k in range(j + 1, len(sec)):
            if re.match(r"^\s*(\d+\.|[-*])\s+\S", sec[k]) :
                n += 1; rows.append((f"SC-{n}", re.sub(r"\s+", " ", sec[k].strip())[:500], f"ROADMAP.md:{start+k+1}", typ(sec[k])))
            elif sec[k].strip() and not sec[k].startswith(" ") and re.match(r"^\*\*|^#", sec[k]) and n: break
        break
O += [f"## Phase 4 section in ROADMAP.md: lines {start+1}-{end}; IDs referenced: {', '.join(ids) or 'none'}", "", "## Obligations (requirements + roadmap success criteria)", "", "| id | text (quoted) | source | type (heuristic) |", "|---|---|---|---|"]
for r in rows: O.append("| " + " | ".join(x.replace("|", "\\|") for x in r) + " |")
dec = []
for p, nm in ((ctx, "04-CONTEXT.md"),):
    if os.path.exists(p):
        for i, l in enumerate(lines(p)):
            m = re.match(r"^\W*(D-\d+)\W+(.*)", l)
            if m: dec.append((m.group(1), re.sub(r"\s+", " ", m.group(2).strip())[:450], f"{nm}:{i+1}"))
    else: flags.append(f"{nm} not found")
O += ["", "## Decisions (04-CONTEXT.md)", "", "| id | decision (quoted) | source |", "|---|---|---|"]
for d in dec: O.append("| " + " | ".join(x.replace("|", "\\|") for x in d) + " |")
for p, nm in ((ui, "04-UI-SPEC.md"), (rs, "04-RESEARCH.md")):
    O += ["", f"## Headings of {nm}", ""]
    if os.path.exists(p):
        for i, l in enumerate(lines(p)):
            if re.match(r"^#{1,4}\s", l): O.append(f"- `{nm}:{i+1}` {l.strip()[:120]}")
    else: flags.append(f"{nm} not found")
O += ["", "## Ambiguities / flags", ""] + ([f"- {f}" for f in flags] or ["- none detected by the extractor"])
O += [f"- Decisions D-nn found: {len(dec)}; obligations rows: {len(rows)}. If either is 0 the line patterns did not match this file's layout (instrument blind) -- inspect the source manually.",
      "- Obligations carried only in prose paragraphs (no list/table line) are NOT extracted: counts are a FLOOR, not the full set."]
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(O) + "\n")
print("phase4 roadmap lines", start + 1, end, "ids", ids[:30]); print("obligation rows", len(rows), "decisions", len(dec), "flags", len(flags))
for r in rows[:6]: print(r[0], r[2], r[3], r[1][:100])
for d in dec[:4]: print(d[0], d[2], d[1][:100])
for f in flags[:5]: print("FLAG", f[:140])
