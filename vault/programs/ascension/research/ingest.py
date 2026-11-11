"""Normalize raw research JSONL (one file per gap) into recon-research.jsonl.

Raw answers G01-G06 used their OWN evidence scale (E1 strongest .. E4 unverified),
inverse of the doc's scale (E1 no source .. E4 reproduced by us). Mapping:
  their E3/E4, or no source_url        -> ours E1 (inference / unverified)
  their E1/E2 with a primary source    -> ours E3
  their E1/E2 with a secondary source  -> ours E2
Nothing reaches ours E4: only a real mwcc + objdiff run can grant it.
Files carrying `"grade_scale":"doc"` (prompts G07+ define the doc scale) are kept as-is, capped at E3.

Usage: python ingest.py            (writes recon-research.jsonl + ingest_report.md next to this file)
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "recon-research.jsonl"
REPORT = HERE / "ingest_report.md"
RETRIEVED = "2026-11-11"

# Files whose answer used the inverted scale (measured: each answer's legend, 2026-11-11).
INVERTED_SCALE = {"G01", "G02", "G03", "G04", "G05", "G06"}

PRIMARY = re.compile(
    r"github\.com/(encounter|zeldaret|doldecomp|decompme|simonlindholm|matt-kempster|"
    r"projectPiki|SeekyCt|mariopartyrd|SMGCommunity|kiwi515|cadmic|MarkMcCaskey|"
    r"electronicarts|zcanann|chasem-dev)/|nxp\.(com|jp)/docs/|eel\.is/|arxiv\.org|doi\.org"
)
SECONDARY = re.compile(r"gist\.github|decomp-academy|decomp\.me|community\.nxp\.com|reddit|discord")

REQUIRED = ("gap", "id", "evidence_grade")


def source_class(url: str) -> str:
    if not url:
        return "none"
    if SECONDARY.search(url):
        return "secondary"
    if PRIMARY.search(url):
        return "primary"
    return "secondary"


def map_grade(gap: str, raw_grade: str, url: str, doc_scale: bool) -> str:
    cls = source_class(url)
    if doc_scale:
        g = raw_grade if raw_grade in ("E1", "E2", "E3") else "E1"
        return "E1" if cls == "none" else g
    if cls == "none" or raw_grade in ("E3", "E4"):
        return "E1"
    return "E3" if cls == "primary" else "E2"


def norm_key(row: dict) -> str:
    text = row.get("claim") or row.get("pragma_or_flag") or row.get("game_or_lib") or row.get("construct") or ""
    return re.sub(r"\W+", " ", text.lower()).strip()


def main() -> int:
    rows, problems = [], []
    for path in sorted(RAW.glob("gap-G*.jsonl")):
        file_gap = path.stem.split("-")[1]
        seq = 0
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"{path.name}:{n} JSON error {e}")
                continue
            missing = [k for k in REQUIRED if k not in row]
            if missing:
                problems.append(f"{path.name}:{n} missing {missing}")
                continue
            seq += 1
            if row["gap"] != file_gap or not str(row["id"]).startswith(file_gap):
                row["orig_id"] = row["id"]
                row["gap"] = file_gap
            row["id"] = f"{file_gap}-{seq:03d}"
            url = row.get("source_url", "") or ""
            row["raw_evidence_grade"] = row["evidence_grade"]
            doc_scale = row.get("grade_scale") == "doc" or file_gap not in INVERTED_SCALE
            row["evidence_grade"] = map_grade(file_gap, row["raw_evidence_grade"], url, doc_scale)
            row["source_class"] = source_class(url)
            row["retrieved"] = RETRIEVED
            row["status"] = "OPEN_QUESTION" if not url else "HYPOTHESIS"
            row["origin"] = "chatgpt-deep-research" if file_gap in INVERTED_SCALE else "codex-search"
            rows.append(row)

    # E2 write-back: experiment verdicts (verdicts.jsonl, keyed by id) and link checks (urlcheck_*.json) survive every re-ingest.
    vpath = HERE / "verdicts.jsonl"
    verdicts = {}
    if vpath.exists():
        for n, line in enumerate(vpath.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                v = json.loads(line)
                verdicts[v["id"]] = v
    links = {}
    for p in sorted(HERE.glob("urlcheck_*.json")):
        links.update(json.loads(p.read_text(encoding="utf-8"))["status"])
    by_id = {r["id"]: r for r in rows}
    for vid in verdicts:
        if vid not in by_id:
            problems.append(f"verdicts.jsonl names unknown id {vid}")
    for r in rows:
        url = (r.get("source_url") or "").split()
        st = [links.get(u.strip(",;")) for u in url]
        if st and all(s is not None for s in st):
            r["link_status"] = "OK" if all(s == "200" for s in st) else "UNCONFIRMED:" + ",".join(s for s in st if s != "200")
        v = verdicts.get(r["id"])
        if v:
            r["status"] = v["status"]                     # CONFIRMED / REFUTED / INCONCLUSIVE
            if v["status"] == "CONFIRMED" and v.get("reproduced"):
                r["evidence_grade"] = "E4"                # only a real mwcc + objdiff run on our toolchain grants E4
            r["experiment"] = {k: v[k] for k in ("evidence", "result", "date") if k in v}

    seen, dupes = {}, []
    for r in rows:
        k = (r["gap"], norm_key(r))
        if k[1] and k in seen:
            dupes.append((r["id"], seen[k]))
        else:
            seen[k] = r["id"]

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    by_gap = defaultdict(Counter)
    for r in rows:
        by_gap[r["gap"]][r["evidence_grade"]] += 1
        by_gap[r["gap"]]["n"] += 1
    reassigned = [r for r in rows if "orig_id" in r]
    lines = ["# Ingest report", "", f"rows: {len(rows)}  problems: {len(problems)}  duplicates: {len(dupes)}  reassigned ids: {len(reassigned)}", "",
             "| gap | rows | E1 | E2 | E3 | E4 |", "|---|---|---|---|---|---|"]
    for g in sorted(by_gap):
        c = by_gap[g]
        lines.append(f"| {g} | {c['n']} | {c['E1']} | {c['E2']} | {c['E3']} | {c['E4']} |")
    lines += ["", "## Reassigned ids"] + [f"- {r['orig_id']} -> {r['id']}" for r in reassigned]
    lines += ["", "## Duplicates"] + [f"- {a} duplicates {b}" for a, b in dupes]
    lines += ["", "## Problems"] + [f"- {p}" for p in problems]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:4 + len(by_gap) + 3]))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
