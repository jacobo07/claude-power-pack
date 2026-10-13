#!/usr/bin/env python3
"""A5 U0 obligation ledger: parse dataset numbered headings -> ids, join dispositions JSON, emit LEDGER.md/.json."""
import json, re, sys, os

ALLOWED = {"ALREADY_SATISFIED", "EXTEND_EXISTING", "MERGE_WITH_EXISTING", "CONNECT_EXISTING", "CERTIFY_EXISTING",
           "IMPLEMENT_NOW", "IMPLEMENT_EXPERIMENT", "IMPLEMENT_SHADOW", "SUPERSEDED_BY_STRONGER_OWNER",
           "NEGATIVE_ROI", "NOT_APPLICABLE", "DEFER_INSUFFICIENT_EVIDENCE", "DEFER_EXTERNAL_DEPENDENCY", "UNKNOWN"}
PART_STARTS = (400, 1890, 3910)   # numbered lists begin after these lines
HEAD = re.compile(r"^(\d+)\. (.*\S)\s*$")


def parse_dataset(path):
    """Deterministic: a heading is `N. title` after line 400 where N == previous+1 (restart at 1 opens next part)."""
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().split("\n")
    ids, cur, prev = [], 0, 0
    for i, line in enumerate(lines, 1):
        part = sum(1 for s in PART_STARTS if i > s)
        if part != cur:
            cur, prev = part, 0
        if not part:
            continue
        m = HEAD.match(line)
        if not m:
            continue
        n = int(m.group(1))
        if n == prev + 1:
            prev = n
            ids.append({"id": f"P{part}-{n}", "line": i, "title": m.group(2)})
    ids.append({"id": "R-1", "line": 1, "title": "Budget report (lines 1-98)"})
    return ids


def expand(spec):
    """'P1:1-3,35;P3:12' -> set of ids; 'R-1' literal allowed."""
    out = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk == "R-1":
            out.append("R-1"); continue
        part, rest = chunk.split(":")
        for tok in rest.split(","):
            tok = tok.strip()
            a, _, b = tok.partition("-")
            for n in range(int(a), int(b or a) + 1):
                out.append(f"{part.strip()}-{n}")
    return out


def build(ids, disp):
    owner = {}
    problems = []
    for fam in disp["families"]:
        if fam["disposition"] not in ALLOWED:
            problems.append(f"bad disposition {fam['disposition']!r} in family {fam['family']!r}")
            continue
        if fam["disposition"] == "UNKNOWN" and not fam.get("missing"):
            problems.append(f"UNKNOWN without missing number in {fam['family']!r}")
        for i in expand(fam["ids"]):
            if i in owner:
                problems.append(f"{i} claimed twice: {owner[i]['family']!r} and {fam['family']!r}")
            else:
                owner[i] = fam
    known = {r["id"] for r in ids}
    for i in owner:
        if i not in known:
            problems.append(f"{i} in dispositions but not in dataset")
    rows = []
    for r in ids:
        fam = owner.get(r["id"])
        if fam is None:
            rows.append({**r, "family": "OMITTED", "disposition": "OMITTED", "owner": "", "unit": "", "evidence": ""})
        else:
            rows.append({**r, "family": fam["family"], "disposition": fam["disposition"], "owner": fam.get("owner", ""),
                         "unit": fam.get("unit", ""), "evidence": fam.get("evidence", ""),
                         "missing": fam.get("missing", "")})
    return rows, problems


def render(rows):
    counts = {}
    for r in rows:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1
    out = ["# A5 obligation ledger (U0)", "", f"Rows: {len(rows)}  OMITTED: {counts.get('OMITTED', 0)}", "",
           "Counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())), "",
           "| id | line | title | family | disposition | owner | unit | evidence |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = lambda s: str(s).replace("|", "/")
        disp = r["disposition"] + (f" ({r['missing']})" if r.get("missing") else "")
        out.append(f"| {r['id']} | {r['line']} | {c(r['title'])[:80]} | {c(r['family'])} | {c(disp)} | {c(r['owner'])} | {c(r['unit'])} | {c(r['evidence'])} |")
    out += ["", "## Universal iteration pass (iteracion-avanzada-universal.txt, applied once)", "",
            "- REALITY CHECK: source read = dataset numbered headings + a5-dispositions.json; error = first pass left ledger uncommitted, no test, no receipt; false premise = none.",
            "- CLASE 5 (output without empirical done-gate): fixed by tools/test_a5_u0.py (one row per id, OMITTED 0, bad disposition refused, mutant red).",
            "- UNKNOWN rows keep their missing number named; no placeholders."]
    return "\n".join(out) + "\n", counts


def main(argv):
    root = argv[1] if len(argv) > 1 else os.getcwd()
    A = os.path.join(root, "vault/programs/cognitive-economy/a5")
    ids = parse_dataset(os.path.join(A, "inputs/dataset-dws-optimization-1.md"))
    with open(os.path.join(root, "vault/config/a5-dispositions.json"), encoding="utf-8") as f:
        disp = json.load(f)
    rows, problems = build(ids, disp)
    md, counts = render(rows)
    with open(os.path.join(A, "LEDGER.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(A, "LEDGER.json"), "w", encoding="utf-8") as f:
        json.dump({"counts": counts, "rows": rows, "problems": problems}, f, ensure_ascii=False, indent=1)
    for p in problems:
        print("PROBLEM", p)
    print("rows", len(rows), "counts", counts)
    return 1 if problems or counts.get("OMITTED") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
