#!/usr/bin/env python3
"""V-ICN-* gates: pillar N closeout -- UKDL / CBR candidates and reviews (incremental-cognition phase 6, plans 06-03 and 06-04).

    python3 tools/test_ic_closeout.py           run every gate
    python3 tools/test_ic_closeout.py --drill   mutation drill (each mutant must be killed)

Frozen rule N: "candidates go to vault/programs/incremental-cognition/ukdl-candidates.md; promotion into
ukdl-universal.md and CBR is reviewed, never silent". Nothing here promotes anything. The candidates are DISCOVERED from
the candidates file by the `### IC-<U|D|P>-<NN> -- ` header grammar and never listed in this test. A SKIP or an
INCONCLUSIVE is printed and counted apart; it is never a PASS and is outside the n/m denominator. Every gate carries
in-gate controls on synthetic text: a control that reports nothing is a FAIL.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import test_cognitive_economy_program as ce  # noqa: E402  (TERMINALS: the seven terminal names)

PROG = "vault/programs/incremental-cognition"
CAND_REL = f"{PROG}/ukdl-candidates.md"
UKDL_REVIEW_REL = f"{PROG}/reviews/ukdl.md"
CBR_REVIEW_REL = f"{PROG}/reviews/cbr.md"
BUNDLE_REL = f"{PROG}/owner-bundle.md"
LEDGER_REL = f"{PROG}/ledger.json"
UKDL_UNIVERSAL = "vault/knowledge_base/ukdl-universal.md"
FAMILIES_DIR = "vault/tower/families"
TOWER_DIR = "vault/tower"
PHASE6_HEAD = "## Phase 6 -- consumed owners (R2) and closeout"
SUMMARY_HEAD = "## Summary (every Owner item, phases 1-5)"
DUP_SECTION = "## Duplicate sweep"
PROMO_SECTION = "## Promotions recorded"
SELF_CMD = "python3 tools/test_ic_closeout.py"
PHASES_DIR = ".planning/workstreams/incremental-cognition/phases"
PLANES = ("gex44", "laptop", "repo")
DELTA_KINDS = ("product", "intelligence")
REVIEW_KEYS = {"ukdl": UKDL_REVIEW_REL, "cbr": CBR_REVIEW_REL}
# A commit is a PROGRAM commit only when BOTH hold: its subject names the program or carries a phase-number scope, AND it
# touches at least one of these paths (a prefix ends with "/", anything else is an exact file). Neither half alone is
# enough: other GSD workstreams use phase-number scopes too, and peers also write under tools/.
PROGRAM_PATHS = (
    ".planning/workstreams/incremental-cognition/",
    "vault/programs/incremental-cognition/",
    "tools/test_incremental_cognition_program.py",
    "wiki/tools/kme_pillars.py",
    "wiki/tools/kme_replay.py",
    "tools/test_kme_pillars.py",
    "tools/test_kme_replay.py",
    "tools/floor_regression_gate.py",
    "tools/test_floor_regression_gate.py",
    "tools/gex44_env_preflight.py",
    "tools/test_gex44_env_preflight.py",
    "tools/gex44_env_deploy.py",
    "tools/test_gex44_env_deploy.py",
    "tools/mission_launch_gate.py",
    "tools/test_mission_launch_gate.py",
    "tools/test_persistent_failure_park.py",
    "tools/gsd_mission.py",
    "tools/test_gsd_mission_cwd_align.py",
    "tools/ic_r2_evidence.py",
    "tools/test_ic_r2_evidence.py",
    "tools/test_ic_closeout.py",
)

MIN_PER_LEVEL = 3
LEVELS = {"U": "universal", "D": "domain", "P": "project"}
KINDS = ("hard-rule", "process-rule", "trap", "performance")
VERDICTS = ("PROMOTE-PROPOSED", "HOLD", "REJECT")
UKDL_ID = r"\b(?:HR|PR|T)-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}\b"
ID_RE = re.compile(UKDL_ID)
DUP_RE = re.compile(r"duplicate of (" + UKDL_ID + ")")
KNOWN_ID_PATHS = ("vault/knowledge_base", "governance", "rules", "CLAUDE.md")

RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)
QUIET = [False]


# --------------------------------------------------------------------------- gate plumbing
def record(status: str, gate: str, ev_: str = "") -> None:
    RESULTS.append((status, gate, str(ev_)))
    if not QUIET[0]:
        print(f"{status} {gate} {ev_}".rstrip())


def run_gate(gate: str, fn) -> None:
    """fn returns (True|False|'SKIP'|'INCONCLUSIVE', evidence); an exception is a FAIL naming its class."""
    try:
        res, why = fn()
    except Exception as exc:  # noqa: BLE001 -- a gate that crashes must read red, never absent
        res, why = False, f"{exc.__class__.__name__}: {exc}"
    if res in ("SKIP", "INCONCLUSIVE"):
        record(res, gate, why)
    else:
        record("PASS" if res else "FAIL", gate, why)


# --------------------------------------------------------------------------- git readers
def git(*args: str, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=not binary,
                          **({} if binary else {"encoding": "utf-8", "errors": "replace"}))


def head() -> str:
    return git("rev-parse", "HEAD").stdout.strip()


def lf_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def blob_at(commit: str, path: str) -> bytes | None:
    r = git("show", f"{commit}:{path}", binary=True)
    return r.stdout if r.returncode == 0 else None


def commit_reachable(sha: str) -> bool:
    if not re.fullmatch(r"[0-9a-f]{7,40}", sha or ""):
        return False
    if git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}").returncode != 0:
        return False
    return git("merge-base", "--is-ancestor", sha, "HEAD").returncode == 0


_LINES: dict = {}


def line_count(path: str) -> int | None:
    if path not in _LINES:
        data = blob_at("HEAD", path)
        _LINES[path] = None if data is None else len(data.decode("utf-8", "replace").split("\n")) - (
            1 if data.endswith(b"\n") else 0)
    return _LINES[path]


def read_text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def tracked(rel: str) -> bool:
    return git("ls-files", "--error-unmatch", "--", rel).returncode == 0


def id_known(ident: str) -> bool:
    return git("grep", "-q", "-F", "--", ident, "HEAD", "--", *KNOWN_ID_PATHS).returncode == 0


def family_stems() -> list:
    return sorted(p.stem for p in (REPO / FAMILIES_DIR).glob("*.json"))


# --------------------------------------------------------------------------- candidates
FIELD_RE = re.compile(r"^(level|kind|proposed_id|target|statement|evidence|second_workload):[ \t]*(.*)$")


def parse_candidates(text: str) -> list:
    """Blocks headed `### IC-<U|D|P>-<NN> -- <title>`; fields from `key: value` lines (indented continuation lines
    extend the previous field). A header that starts `### IC-` but breaks the grammar yields a malformed entry."""
    out: list = []
    cur = None
    last = None
    for ln in text.split("\n"):
        if re.match(r"^#{1,3} ", ln):
            cur, last = None, None
            m = re.match(r"^### (IC-([UDP])-(\d{2})) -- (\S.*)$", ln)
            if m:
                cur = {"id": m.group(1), "letter": m.group(2), "title": m.group(4).strip(), "fields": {}}
                out.append(cur)
            elif ln.startswith("### IC-"):
                out.append({"id": ln[4:].strip(), "malformed": True, "fields": {}})
            continue
        if cur is None:
            continue
        f = FIELD_RE.match(ln)
        if f:
            last = f.group(1)
            cur["fields"][last] = f.group(2).strip()
        elif last and re.match(r"^[ \t]+\S", ln):
            cur["fields"][last] += " " + ln.strip()
        elif not ln.strip():
            last = None
    for c in out:
        ev_ = c["fields"].get("evidence", "")
        c["evidence"] = [e.strip() for e in ev_.split(" ; ") if e.strip()]
    return out


def candidate_problems(cands: list, min_per_level: int, exists=None, is_tracked=None) -> list:
    exists = exists or (lambda rel: (REPO / rel).is_file())
    is_tracked = is_tracked or tracked
    probs: list = []
    seen: set = set()
    seen_pid: set = set()
    per_level = {k: 0 for k in LEVELS}
    for c in cands:
        if c.get("malformed"):
            probs.append(f"malformed header: {c['id'][:60]}")
            continue
        cid, f = c["id"], c["fields"]
        if cid in seen:
            probs.append(f"{cid}: id used twice")
        seen.add(cid)
        per_level[c["letter"]] += 1
        level = f.get("level", "").lower()
        if level not in LEVELS.values():
            probs.append(f"{cid}: level {level!r} is not one of {sorted(LEVELS.values())}")
        elif LEVELS[c["letter"]] != level:
            probs.append(f"{cid}: id letter {c['letter']} says {LEVELS[c['letter']]} but level is {level}")
        if f.get("kind") not in KINDS:
            probs.append(f"{cid}: kind {f.get('kind')!r} not in {list(KINDS)}")
        pid = f.get("proposed_id", "")
        if not re.fullmatch(UKDL_ID, pid):
            probs.append(f"{cid}: proposed_id {pid!r} does not match the UKDL id grammar")
        elif pid in seen_pid:
            probs.append(f"{cid}: proposed_id {pid} used twice")
        seen_pid.add(pid)
        tgt = f.get("target", "")
        if c["letter"] == "U":
            ok_t = tgt == UKDL_UNIVERSAL and exists(tgt)
        elif c["letter"] == "P":
            ok_t = tgt == CAND_REL and exists(tgt)
        else:
            ok_t = (tgt.startswith("vault/knowledge_base/") and tgt != UKDL_UNIVERSAL and exists(tgt)
                    and is_tracked(tgt))
        if not ok_t:
            probs.append(f"{cid}: target {tgt!r} is not a valid {LEVELS[c['letter']]} target")
        if not f.get("statement"):
            probs.append(f"{cid}: empty statement")
        if not c["evidence"]:
            probs.append(f"{cid}: no evidence ref")
    for letter, name in LEVELS.items():
        if per_level[letter] < min_per_level:
            probs.append(f"level {name} has {per_level[letter]} candidate(s), needs {min_per_level}")
    return probs


def ref_resolves(ref: str) -> str | None:
    """None when the ref resolves at HEAD; otherwise the reason it does not."""
    ref = ref.strip()
    m = re.fullmatch(r"commit:([0-9a-fA-F]{7,40})", ref)
    if m:
        sha = m.group(1).lower()
        if git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}").returncode != 0:
            return f"commit {sha} is not in this clone"
        if git("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
            return f"commit {sha} is not reachable from HEAD"
        return None
    m = re.fullmatch(r"([^\s:]+)(?::(\d+)(?:-(\d+))?)?", ref)
    if not m:
        return f"unparseable ref {ref[:60]!r}"
    path, lo, hi = m.group(1), m.group(2), m.group(3)
    if path.startswith("/") or ".." in path.split("/"):
        return f"path {path} is absolute or escapes the repository"
    n = line_count(path)
    if n is None:
        return f"{path} is not a file at HEAD"
    for v in (lo, hi):
        if v is not None and not 1 <= int(v) <= n:
            return f"{path} has {n} line(s), ref names {v}"
    if lo is not None and hi is not None and int(lo) > int(hi):
        return f"empty range {lo}-{hi}"
    return None


def evidence_problems(cands: list) -> list:
    probs = []
    for c in cands:
        if c.get("malformed"):
            continue
        for ref in c["evidence"]:
            why = ref_resolves(ref)
            if why:
                probs.append(f"{c['id']}: {ref}: {why}")
        sw = c["fields"].get("second_workload")
        if sw:
            why = ref_resolves(sw)
            if why:
                probs.append(f"{c['id']}: second_workload {sw}: {why}")
    return probs


# --------------------------------------------------------------------------- reviews
def split_section(text: str, header: str) -> str | None:
    m = re.search(r"^" + re.escape(header) + r"[ \t]*$", text, re.M)
    if not m:
        return None
    end = text.find("\n## ", m.end())
    return text[m.end():len(text) if end < 0 else end]


def parse_review(text: str, kind: str) -> dict:
    """kind 'ukdl': rows `| candidate | verdict | reason |`; kind 'cbr': `| candidate | family | verdict | reason |`."""
    rev = {"kind": kind, "reviewer": None, "promotion": None, "against": [], "transfer_rule": None, "rows": [],
           "promotions": None, "promotions_none": False, "sweep": None}
    for ln in text.split("\n"):
        m = re.match(r"^reviewer:[ \t]*(.*)$", ln)
        if m:
            rev["reviewer"] = m.group(1).strip()
        m = re.match(r"^promotion:[ \t]*(.*)$", ln)
        if m:
            rev["promotion"] = m.group(1).strip()
        m = re.match(r"^reviewed_against: (\S+) @ ([0-9a-f]{40}) sha256 ([0-9a-f]{64})[ \t]*$", ln)
        if m:
            rev["against"].append({"path": m.group(1), "commit": m.group(2), "sha": m.group(3)})
        m = re.match(r"^transfer_rule:[ \t]?(.*)$", ln)
        if m:
            rev["transfer_rule"] = m.group(1)
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if cells and re.fullmatch(r"IC-[UDP]-\d{2}", cells[0]):
                if kind == "cbr" and len(cells) >= 4:
                    rev["rows"].append({"id": cells[0], "family": cells[1], "verdict": cells[2],
                                        "reason": " | ".join(cells[3:])})
                elif kind == "ukdl" and len(cells) >= 3:
                    rev["rows"].append({"id": cells[0], "family": None, "verdict": cells[1],
                                        "reason": " | ".join(cells[2:])})
                else:
                    rev["rows"].append({"id": cells[0], "family": None, "verdict": "", "reason": ""})
    sec = split_section(text, PROMO_SECTION)
    if sec is not None:
        rev["promotions"] = []
        for ln in sec.split("\n"):
            s = ln.strip()
            if s == "none":
                rev["promotions_none"] = True
            m = re.match(r"^- (IC-[UDP]-\d{2}).*\bcommit ([0-9a-f]{7,40})\b", s)
            if m:
                rev["promotions"].append((m.group(1), m.group(2)))
    rev["sweep"] = split_section(text, DUP_SECTION)
    return rev


def review_problems(review: dict, cands: list, families=None) -> list:
    probs = []
    if not review["reviewer"] or "this run" not in review["reviewer"]:
        probs.append("no `reviewer:` line naming this run")
    if not review["promotion"] or "[N]" not in review["promotion"] or "Owner" not in review["promotion"]:
        probs.append("no `promotion:` line naming [N] and the Owner")
    if review["promotions"] is None:
        probs.append(f"no `{PROMO_SECTION}` section")
    ids = [c["id"] for c in cands if not c.get("malformed")]
    rows = review["rows"]
    seen: dict = {}
    for r in rows:
        seen[r["id"]] = seen.get(r["id"], 0) + 1
    for i in ids:
        if seen.get(i, 0) == 0:
            probs.append(f"{i}: no verdict row")
    for i, n in seen.items():
        if n > 1:
            probs.append(f"{i}: {n} verdict rows")
        if i not in ids:
            probs.append(f"{i}: stale row (no such candidate)")
    for r in rows:
        if r["verdict"] not in VERDICTS:
            probs.append(f"{r['id']}: verdict {r['verdict']!r} not in {list(VERDICTS)}")
        if not r["reason"].strip():
            probs.append(f"{r['id']}: empty reason")
        if review["kind"] == "cbr":
            fam = families if families is not None else family_stems()
            if r["family"] != "none" and r["family"] not in fam:
                probs.append(f"{r['id']}: family {r['family']!r} is not a discovered family {fam} or none")
    return probs


def against_problems(review: dict, required_paths: list, blob=None, reachable=None) -> list:
    blob = blob or blob_at
    reachable = reachable or commit_reachable
    probs = []
    have = {a["path"] for a in review["against"]}
    for p in required_paths:
        if p not in have:
            probs.append(f"no reviewed_against record for {p}")
    for a in review["against"]:
        if not reachable(a["commit"]):
            probs.append(f"{a['path']}: commit {a['commit'][:12]} is not reachable from HEAD")
            continue
        data = blob(a["commit"], a["path"])
        if data is None:
            probs.append(f"{a['path']}: absent at {a['commit'][:12]}")
        elif lf_sha256(data) != a["sha"]:
            probs.append(f"{a['path']}: sha256 at {a['commit'][:12]} is {lf_sha256(data)[:12]}, recorded {a['sha'][:12]}")
    return probs


def duplicate_problems(review: dict, cands: list, known=None) -> list:
    known = known or id_known
    probs = []
    for r in review["rows"]:
        for ident in DUP_RE.findall(r["reason"]):
            if not known(ident):
                probs.append(f"{r['id']}: duplicate of {ident}: no such id in {list(KNOWN_ID_PATHS)}")
    sweep = review.get("sweep")
    if review["kind"] == "ukdl":
        if sweep is None:
            probs.append(f"no `{DUP_SECTION}` section")
        else:
            for c in cands:
                if not c.get("malformed") and not re.search(r"^[-*] " + re.escape(c["id"]) + r":.*->[ \t]*\d+ hit", sweep, re.M):
                    probs.append(f"{c['id']}: no duplicate-sweep line (`- <id>: <command> -> <n> hits`)")
    return probs


def transfer_problems(cbr: dict, cands: list, ledger: dict, ref_ok=None) -> list:
    ref_ok = ref_ok or ref_resolves
    probs = []
    want = ((ledger.get("frozen") or {}).get("materiality") or {}).get("transfer")
    if not want:
        probs.append("ledger has no frozen.materiality.transfer")
    elif cbr["transfer_rule"] != want:
        probs.append(f"transfer_rule is {cbr['transfer_rule']!r}, the ledger's frozen rule is {want!r}")
    by_id = {c["id"]: c for c in cands if not c.get("malformed")}
    for r in cbr["rows"]:
        if r["verdict"] != "PROMOTE-PROPOSED":
            continue
        if r["family"] == "none":
            probs.append(f"{r['id']}: PROMOTE-PROPOSED against family none")
        c = by_id.get(r["id"])
        if c and c["fields"].get("kind") == "performance":
            sw = c["fields"].get("second_workload", "")
            if not sw:
                probs.append(f"{r['id']}: a performance guarantee promoted to CBR needs a second, materially "
                             "independent workload (no second_workload: ref)")
            elif ref_ok(sw):
                probs.append(f"{r['id']}: second_workload {sw} does not resolve")
    return probs


def promotion_problems(cands: list, owner_texts: dict, review: dict, reachable=None) -> list:
    """A candidate id or proposed_id present in the UKDL (owner_texts['ukdl']) or under vault/tower (owner_texts['tower'])
    must be recorded under the matching review's `## Promotions recorded` with a reachable commit."""
    reachable = reachable or commit_reachable
    probs = []
    for c in cands:
        if c.get("malformed"):
            continue
        names = {c["id"], c["fields"].get("proposed_id", "")} - {""}
        for key, which in (("ukdl", "ukdl"), ("tower", "cbr")):
            text = owner_texts.get(key, "")
            hit = sorted(n for n in names if n in text)
            if not hit:
                continue
            rec = [(i, sha) for i, sha in (review[which]["promotions"] or []) if i == c["id"]]
            if not rec:
                probs.append(f"{c['id']}: {', '.join(hit)} appears in the {key} owner file with no recorded promotion "
                             f"in reviews/{which}.md")
            elif not any(reachable(sha) for _i, sha in rec):
                probs.append(f"{c['id']}: promotion recorded in reviews/{which}.md names no reachable commit")
    return probs


# --------------------------------------------------------------------------- owner bundle
def strip_summary(text: str) -> str:
    m = re.search(r"^" + re.escape(SUMMARY_HEAD) + r"[ \t]*$", text, re.M)
    if not m:
        return text
    end = text.find("\n## ", m.end())
    end = len(text) if end < 0 else end + 1
    return text[:m.start()] + text[end:]


def bundle_n_problems(text: str) -> list:
    probs = []
    body = strip_summary(text).split("\n")
    p6 = next((i for i, ln in enumerate(body) if ln.strip() == PHASE6_HEAD), None)
    items = [i for i, ln in enumerate(body) if re.match(r"^- \*\*\[N\]\*\*", ln)]
    if len(items) != 1:
        probs.append(f"{len(items)} `- **[N]**` item(s), exactly one required")
        return probs
    at = items[0]
    if p6 is None:
        probs.append(f"no `{PHASE6_HEAD}` header")
    elif at < p6:
        probs.append("the [N] item sits before the Phase 6 header")
    else:
        nxt = next((i for i in range(p6 + 1, len(body)) if body[i].startswith("## ")), len(body))
        if at > nxt:
            probs.append("the [N] item is not inside the Phase 6 section")
    end = next((i for i in range(at + 1, len(body)) if body[i].startswith("- **[") or body[i].startswith("## ")),
               len(body))
    item = body[at:end]
    blob = "\n".join(item)
    for rel in (UKDL_REVIEW_REL, CBR_REVIEW_REL):
        if rel not in blob:
            probs.append(f"the [N] item does not name {rel}")
    if not any(re.match(r"^ {4,}" + re.escape(SELF_CMD) + r"[ \t]*$", ln) for ln in item):
        probs.append(f"the [N] item has no indented `{SELF_CMD}` line")
    sm = re.search(r"^" + re.escape(SUMMARY_HEAD) + r"[ \t]*$", text, re.M)
    sec = text[sm.end():text.find("\n## ", sm.end())] if sm else ""
    if '[N]#1 "' not in sec:
        probs.append("the summary has no row citing [N]#1")
    return probs


# --------------------------------------------------------------------------- synthetic fixtures for in-gate controls
GOOD_REF = "tools/test_ic_r2_evidence.py"      # committed before this plan; the evidence controls need a stable file
GOOD_DUP_ID = "T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001"


def syn_block(letter="U", num="01", level=None, kind="process-rule", pid="PR-SYNTHETIC-CONTROL-ONE-001", target=None,
              evidence=GOOD_REF, extra=""):
    level = level or LEVELS[letter]
    target = target or {"U": UKDL_UNIVERSAL, "P": CAND_REL}.get(letter, "vault/knowledge_base/ukdl-cognitive-resource-os.md")
    ev_line = f"evidence: {evidence}\n" if evidence is not None else ""
    return (f"### IC-{letter}-{num} -- synthetic\nlevel: {level}\nkind: {kind}\nproposed_id: {pid}\ntarget: {target}\n"
            f"statement: a synthetic statement\n{ev_line}{extra}")


def syn_set(n_per_level=1):
    parts = []
    for letter in "UDP":
        for k in range(1, n_per_level + 1):
            parts.append(syn_block(letter, f"{k:02d}", pid=f"PR-SYNTHETIC-{letter}{k}-001"))
    return "\n".join(parts)


def syn_review(kind, cands, drop=None, verdict="HOLD", family="none", reason="a reason", extra_rows="", promotions="none",
               reviewer="this run", promo_line="promotion: left to the Owner, recorded through [N]", sweep=True):
    lines = [f"reviewer: {reviewer}", promo_line, ""]
    lines.append("| candidate | verdict | reason |" if kind == "ukdl" else "| candidate | family | verdict | reason |")
    lines.append("|---|---|---|" if kind == "ukdl" else "|---|---|---|---|")
    for c in cands:
        if c["id"] == drop:
            continue
        lines.append(f"| {c['id']} | {verdict} | {reason} |" if kind == "ukdl"
                     else f"| {c['id']} | {family} | {verdict} | {reason} |")
    lines.append(extra_rows)
    if sweep and kind == "ukdl":
        lines += ["", DUP_SECTION, ""] + [f"- {c['id']}: `grep -rn x vault/knowledge_base` -> 0 hits" for c in cands]
    lines += ["", PROMO_SECTION, "", promotions, ""]
    return parse_review("\n".join(lines), kind)


def has(problems: list, needle: str) -> bool:
    return any(needle in p for p in problems)


# --------------------------------------------------------------------------- gates
def real_cands() -> list:
    return parse_candidates(read_text(CAND_REL))


def g_candidates_shape():
    syn = parse_candidates(syn_set(1))

    def cp(cs, n):
        return candidate_problems(cs, n, exists=lambda r: True, is_tracked=lambda r: True)
    ctl = {
        "clean synthetic accepted": cp(syn, 1) == [],
        "id letter vs level reported": has(cp(parse_candidates(
            syn_block("D", "01", level="universal")), 0), "id letter D says domain but level is universal"),
        "bad proposed_id reported": has(cp(parse_candidates(
            syn_block("U", "01", pid="not an id")), 0), "UKDL id grammar"),
        "bad kind reported": has(cp(parse_candidates(syn_block("U", "01", kind="whim")), 0), "kind"),
        "level below minimum reported": has(cp(syn, 2), "needs 2"),
        "repeated id reported": has(cp(parse_candidates(
            syn_block("U", "01") + "\n" + syn_block("U", "01", pid="PR-SYNTHETIC-OTHER-001")), 0), "used twice"),
        "wrong target reported": has(cp(parse_candidates(
            syn_block("U", "01", target="vault/knowledge_base/ukdl-cognitive-resource-os.md")), 0), "not a valid universal"),
        "no evidence reported": has(cp(parse_candidates(syn_block("U", "01", evidence=None)), 0),
                                    "no evidence ref"),
        "a target file that is absent is reported": has(candidate_problems(syn, 1, exists=lambda r: False), "not a valid"),
        "malformed header reported": has(cp(parse_candidates("### IC-X-1 -- nope\nlevel: x\n"), 0),
                                         "malformed header"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    cands = real_cands()
    probs = candidate_problems(cands, MIN_PER_LEVEL)
    per = {LEVELS[k]: sum(1 for c in cands if c.get("letter") == k) for k in LEVELS}
    return not probs, f"{len(cands)} candidate(s) {per} (min {MIN_PER_LEVEL} per level), problems={probs[:4]}, {len(ctl)} controls report"


def g_evidence_resolves():
    h = head()[:12]
    ctl = {
        "a committed file is accepted": ref_resolves(GOOD_REF) is None,
        "a line inside the file is accepted": ref_resolves(f"{GOOD_REF}:1") is None,
        "a range inside the file is accepted": ref_resolves(f"{GOOD_REF}:1-2") is None,
        "a line past the end is refused": ref_resolves(f"{GOOD_REF}:999999") is not None,
        "a missing path is refused": ref_resolves("tools/no_such_file_icn.py") is not None,
        "an escaping path is refused": ref_resolves("../outside.md") is not None,
        "a reachable commit is accepted": ref_resolves(f"commit:{h}") is None,
        "an absent commit (21671d6c) is refused": ref_resolves("commit:21671d6c") is not None,
        "a zero commit is refused": ref_resolves("commit:0000000") is not None,
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    cands = real_cands()
    refs = sum(len(c["evidence"]) for c in cands if not c.get("malformed"))
    probs = evidence_problems(cands)
    return bool(refs) and not probs, f"{refs} evidence ref(s) over {len(cands)} candidate(s), problems={probs[:4]}, {len(ctl)} controls report"


def _review_controls(kind: str) -> dict:
    cands = parse_candidates(syn_set(1))
    fam = ["alpha", "beta"]
    cbr = kind == "cbr"

    def mk(**kw):
        return syn_review(kind, cands, **kw)
    ctl = {
        "clean synthetic accepted": review_problems(mk(), cands, fam) == [],
        "a missing row is reported": has(review_problems(mk(drop=cands[0]["id"]), cands, fam), "no verdict row"),
        "a stale row is reported": has(review_problems(mk(extra_rows=(
            "| IC-U-99 | HOLD | r |" if not cbr else "| IC-U-99 | none | HOLD | r |")), cands, fam), "stale row"),
        "an unknown verdict is reported": has(review_problems(mk(verdict="MAYBE"), cands, fam), "verdict"),
        "an empty reason is reported": has(review_problems(mk(reason=" "), cands, fam), "empty reason"),
        "a missing reviewer is reported": has(review_problems(mk(reviewer="somebody else"), cands, fam), "reviewer"),
        "a missing promotion line is reported": has(review_problems(mk(promo_line="promotion: none"), cands, fam), "promotion:"),
    }
    if cbr:
        ctl["an unknown family is reported"] = has(review_problems(mk(family="gamma"), cands, fam), "family")
        ctl["a discovered family is accepted"] = review_problems(mk(family="alpha"), cands, fam) == []
    sec_less = parse_review("reviewer: this run\npromotion: Owner [N]\n", kind)
    ctl["a missing promotions section is reported"] = has(review_problems(sec_less, cands, fam), PROMO_SECTION)
    return ctl


def g_review_coverage():
    ctl = {f"{k}: {n}": v for k in ("ukdl", "cbr") for n, v in _review_controls(k).items()}
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    cands = real_cands()
    out = {}
    for kind, rel in (("ukdl", UKDL_REVIEW_REL), ("cbr", CBR_REVIEW_REL)):
        out[kind] = review_problems(parse_review(read_text(rel), kind), cands)
    ok = not out["ukdl"] and not out["cbr"]
    n = len([c for c in cands if not c.get("malformed")])
    return ok, f"{n} candidate(s) each covered by both reviews, problems={(out['ukdl'] + out['cbr'])[:4]}, {len(ctl)} controls report"


def g_review_against():
    h = head()
    sha = lf_sha256(blob_at(h, UKDL_UNIVERSAL) or b"")
    good = {"kind": "ukdl", "against": [{"path": UKDL_UNIVERSAL, "commit": h, "sha": sha}]}
    wrong = {"kind": "ukdl", "against": [{"path": UKDL_UNIVERSAL, "commit": h, "sha": "f" * 64}]}
    ghost = {"kind": "ukdl", "against": [{"path": UKDL_UNIVERSAL, "commit": "a" * 40, "sha": sha}]}
    empty = {"kind": "ukdl", "against": []}
    ctl = {
        "a true record is accepted": against_problems(good, [UKDL_UNIVERSAL]) == [],
        "a wrong sha256 is reported": has(against_problems(wrong, [UKDL_UNIVERSAL]), "recorded"),
        "an unreachable commit is reported": has(against_problems(ghost, [UKDL_UNIVERSAL]), "not reachable"),
        "a missing record is reported": has(against_problems(empty, [UKDL_UNIVERSAL]), "no reviewed_against"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    fams = [f"{FAMILIES_DIR}/{s}.json" for s in family_stems()]
    u = against_problems(parse_review(read_text(UKDL_REVIEW_REL), "ukdl"), [UKDL_UNIVERSAL])
    c = against_problems(parse_review(read_text(CBR_REVIEW_REL), "cbr"), fams)
    return bool(fams) and not u and not c, (f"ukdl records {UKDL_UNIVERSAL}; cbr records {len(fams)} discovered famil(ies); "
                                            f"problems={(u + c)[:4]}, {len(ctl)} controls report")


def g_duplicate_cited():
    cands = parse_candidates(syn_set(1))
    ok_rev = syn_review("ukdl", cands, reason=f"duplicate of {GOOD_DUP_ID}")
    bad_rev = syn_review("ukdl", cands, reason="duplicate of PR-NO-SUCH-ENTRY-IN-ANY-FILE-999")
    no_sweep = syn_review("ukdl", cands, sweep=False)
    ctl = {
        "a cited id that exists is accepted": duplicate_problems(ok_rev, cands) == [],
        "a cited id that does not exist is reported": has(duplicate_problems(bad_rev, cands), "no such id"),
        "a missing sweep section is reported": has(duplicate_problems(no_sweep, cands), DUP_SECTION),
        "a candidate without a sweep line is reported": has(duplicate_problems(
            parse_review("\n".join(l for l in ("reviewer: this run", "| IC-U-01 | HOLD | r |", DUP_SECTION, "- IC-D-01: x -> 0 hits",
                                               PROMO_SECTION, "none")), "ukdl"), cands[:1] + cands[1:2]), "no duplicate-sweep line"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    real = real_cands()
    u = parse_review(read_text(UKDL_REVIEW_REL), "ukdl")
    c = parse_review(read_text(CBR_REVIEW_REL), "cbr")
    probs = duplicate_problems(u, real) + duplicate_problems(c, real)
    cited = sorted({i for r in u["rows"] + c["rows"] for i in DUP_RE.findall(r["reason"])})
    return not probs, f"cited duplicate id(s) {cited} all found, problems={probs[:4]}, {len(ctl)} controls report"


def g_cbr_transfer_rule():
    ledger = json.loads(read_text(LEDGER_REL))
    want = ledger["frozen"]["materiality"]["transfer"]
    perf = syn_block("D", "01", kind="performance", pid="PR-SYNTHETIC-PERF-001",
                     extra=f"second_workload: {GOOD_REF}\n")
    perf_none = syn_block("D", "01", kind="performance", pid="PR-SYNTHETIC-PERF-001")
    plain = syn_block("D", "01", pid="PR-SYNTHETIC-PLAIN-001")

    def cbr(c_text, verdict="PROMOTE-PROPOSED", family="alpha", rule=want):
        cs = parse_candidates(c_text)
        r = syn_review("cbr", cs, verdict=verdict, family=family)
        r["transfer_rule"] = rule
        return r, cs
    ctl = {
        "the exact rule line is accepted": transfer_problems(*cbr(perf), ledger) == [],
        "an altered rule line is reported": has(transfer_problems(*cbr(perf, rule=want + " (softened)"), ledger), "frozen rule"),
        "a missing rule line is reported": has(transfer_problems(*cbr(perf, rule=None), ledger), "frozen rule"),
        "a performance promotion without a second workload is reported": has(
            transfer_problems(*cbr(perf_none), ledger), "second, materially independent workload"),
        "a performance HOLD without a second workload is accepted": transfer_problems(
            *cbr(perf_none, verdict="HOLD"), ledger) == [],
        "a non-performance promotion is accepted": transfer_problems(*cbr(plain), ledger) == [],
        "a promotion against family none is reported": has(transfer_problems(*cbr(plain, family="none"), ledger), "family none"),
        "an unresolved second workload is reported": has(transfer_problems(*cbr(
            perf.replace(GOOD_REF, "tools/no_such_file_icn.py")), ledger), "does not resolve"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    probs = transfer_problems(parse_review(read_text(CBR_REVIEW_REL), "cbr"), real_cands(), ledger)
    return not probs, f"transfer_rule equals frozen.materiality.transfer; problems={probs[:4]}, {len(ctl)} controls report"


def owner_texts_real() -> dict:
    tower = []
    for p in sorted((REPO / TOWER_DIR).rglob("*")):
        if p.is_file():
            tower.append(p.read_text(encoding="utf-8", errors="replace"))
    return {"ukdl": read_text(UKDL_UNIVERSAL), "tower": "\n".join(tower)}


def g_promotion_never_silent():
    h = head()[:12]
    cands = parse_candidates(syn_block("U", "01", pid="PR-SYNTHETIC-PROMOTED-001"))
    cid = "IC-U-01"
    pid = "PR-SYNTHETIC-PROMOTED-001"
    none_rev = {"ukdl": syn_review("ukdl", cands), "cbr": syn_review("cbr", cands)}
    rec_rev = {"ukdl": syn_review("ukdl", cands, promotions=f"- {cid} promoted to {UKDL_UNIVERSAL} in commit {h}"),
               "cbr": syn_review("cbr", cands)}
    ghost_rev = {"ukdl": syn_review("ukdl", cands, promotions=f"- {cid} promoted in commit {'a' * 12}"),
                 "cbr": syn_review("cbr", cands)}
    in_ukdl = {"ukdl": f"### {pid}\nbody\n", "tower": ""}
    in_tower = {"ukdl": "", "tower": f'{{"id": "{cid}"}}'}
    clean = {"ukdl": "### PR-OTHER-ENTRY-001\n", "tower": "{}"}
    ctl = {
        "an id absent from both owners is accepted": promotion_problems(cands, clean, none_rev) == [],
        "a proposed_id in the UKDL with no record is reported": has(promotion_problems(cands, in_ukdl, none_rev), "no recorded promotion"),
        "an id in the UKDL with a recorded reachable commit is accepted": promotion_problems(cands, in_ukdl, rec_rev) == [],
        "a recorded promotion at an unreachable commit is reported": has(promotion_problems(cands, in_ukdl, ghost_rev), "no reachable commit"),
        "an id under vault/tower with no CBR record is reported": has(promotion_problems(cands, in_tower, none_rev), "tower owner file"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    real = real_cands()
    review = {"ukdl": parse_review(read_text(UKDL_REVIEW_REL), "ukdl"), "cbr": parse_review(read_text(CBR_REVIEW_REL), "cbr")}
    texts = owner_texts_real()
    probs = promotion_problems(real, texts, review)
    recorded = sum(len(r["promotions"] or []) for r in review.values())
    return not probs, (f"{len(real)} candidate id(s) and proposed_id(s) searched in {UKDL_UNIVERSAL} "
                       f"({len(texts['ukdl'])} chars) and {TOWER_DIR}/ ({len(texts['tower'])} chars); recorded promotions "
                       f"{recorded}; problems={probs[:4]}, {len(ctl)} controls report")


def _bundle(item_extra="", head_first=True, two=False, row=True, cmd=True, paths=True):
    p = f"{UKDL_REVIEW_REL} {CBR_REVIEW_REL}" if paths else "no paths"
    item = f"- **[N]** promotion is the Owner's. {p}\n\n" + (f"    {SELF_CMD}\n" if cmd else "") + item_extra
    item2 = ("- **[N]** another\n" if two else "")
    summ = (f"{SUMMARY_HEAD}\n\n| 1 | N | " + ('[N]#1 "promotion is the" ' if row else "") + "| a | b | c |\n\n"
            "## Laptop code sync\n\n")
    sec = f"{PHASE6_HEAD}\n\n"
    if head_first:
        return summ + sec + item + item2
    return summ + item + item2 + "\n" + sec


def g_bundle_n():
    ctl = {
        "a clean synthetic bundle is accepted": bundle_n_problems(_bundle()) == [],
        "an item before the Phase 6 header is reported": has(bundle_n_problems(_bundle(head_first=False)), "before the Phase 6 header"),
        "two [N] items are reported": has(bundle_n_problems(_bundle(two=True)), "exactly one"),
        "a missing review path is reported": has(bundle_n_problems(_bundle(paths=False)), "does not name"),
        "a missing indented command is reported": has(bundle_n_problems(_bundle(cmd=False)), "no indented"),
        "a missing summary row is reported": has(bundle_n_problems(_bundle(row=False)), "no row citing [N]#1"),
        "no item is reported": has(bundle_n_problems("## nothing\n"), "exactly one"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    probs = bundle_n_problems(read_text(BUNDLE_REL))
    return not probs, f"{BUNDLE_REL}: one [N] item in the Phase 6 section, problems={probs[:4]}, {len(ctl)} controls report"


# --------------------------------------------------------------------------- ledger reviews and deltas (plan 06-04)
def current_lf_sha256(rel: str) -> str | None:
    p = REPO / rel
    return lf_sha256(p.read_bytes()) if p.is_file() else None


def reviews_problems(led: dict) -> list:
    """Each of reviews.ukdl / reviews.cbr must be exactly {file, sha256}: the review file and its CURRENT LF sha256."""
    revs = led.get("reviews")
    if not isinstance(revs, dict):
        return ["ledger `reviews` is not an object"]
    probs = []
    for key, rel in REVIEW_KEYS.items():
        r = revs.get(key)
        if not isinstance(r, dict) or set(r) != {"file", "sha256"}:
            probs.append(f"reviews.{key}: must be exactly {{file, sha256}}, got {str(r)[:60]}")
            continue
        if r["file"] != rel:
            probs.append(f"reviews.{key}: file is {r['file']!r}, must name {rel}")
            continue
        now = current_lf_sha256(rel)
        if now is None:
            probs.append(f"reviews.{key}: {rel} is not a file")
        elif r["sha256"] != now:
            probs.append(f"reviews.{key}: recorded sha256 {str(r['sha256'])[:12]}, but the current LF sha256 of {rel} "
                         f"is {now}")
    return probs


def program_commit_problem(subject: str, paths: list) -> str | None:
    """None for a program commit: its subject names the program or carries a phase-number scope AND it touches a program path."""
    subj_ok = "incremental-cognition" in subject or re.match(r"^[a-z]+\((?:\d{2}(?:-\d{2})?)\)", subject) is not None
    path_ok = any((p.startswith(x) if x.endswith("/") else p == x) for p in paths for x in PROGRAM_PATHS)
    if not subj_ok:
        return f"subject {subject[:60]!r} names neither the program nor a phase-number scope"
    if not path_ok:
        return "touches no program-owned path"
    return None


_COMMITS: dict = {}


def commit_subject(sha: str) -> str:
    key = ("s", sha)
    if key not in _COMMITS:
        _COMMITS[key] = git("log", "-1", "--format=%s", sha).stdout.strip()
    return _COMMITS[key]


def commit_paths(sha: str) -> list:
    key = ("p", sha)
    if key not in _COMMITS:
        _COMMITS[key] = [x for x in git("show", "--name-only", "--format=", sha).stdout.split("\n") if x.strip()]
    return _COMMITS[key]


def is_smoke(data: bytes) -> bool:
    return re.search(rb'^evidence_role:[ \t]*"?smoke"?[ \t]*$', data, re.M) is not None


def delta_entry_problems(kind: str, e, pillar_ids: list, seen: set) -> list:
    if not isinstance(e, dict):
        return [f"deltas.{kind}: an entry is not an object"]
    tag = f"deltas.{kind}[{e.get('id')}]"
    probs = []
    ident = e.get("id")
    if not isinstance(ident, str) or not ident.strip():
        probs.append(f"{tag}: no id")
    elif ident in seen:
        probs.append(f"{tag}: id used twice")
    else:
        seen.add(ident)
    ph = e.get("phase")
    if not isinstance(ph, int) or isinstance(ph, bool) or not 1 <= ph <= 6:
        probs.append(f"{tag}: phase {ph!r} is not an int 1..6")
    pil = e.get("pillars")
    if not isinstance(pil, list) or not pil or any(p not in pillar_ids for p in pil):
        probs.append(f"{tag}: pillars {pil!r} is not a non-empty list of ledger pillar ids")
    st = e.get("statement")
    if not isinstance(st, str) or not st.strip():
        probs.append(f"{tag}: empty statement")
        st = ""
    named = [t for t in sorted(ce.TERMINALS) if t in st]
    if named:
        probs.append(f"{tag}: the statement names a terminal name {named}")
    if e.get("plane") not in PLANES:
        probs.append(f"{tag}: plane {e.get('plane')!r} is not one of {list(PLANES)}")
    commits = e.get("commits")
    if not isinstance(commits, list) or not commits:
        probs.append(f"{tag}: no commits")
        commits = []
    for sha in commits:
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            probs.append(f"{tag}: commit {str(sha)[:12]!r} is not 40 hex")
            continue
        if not commit_reachable(sha):
            probs.append(f"{tag}: commit {sha[:12]} is not reachable from HEAD")
            continue
        why = program_commit_problem(commit_subject(sha), commit_paths(sha))
        if why:
            probs.append(f"{tag}: commit {sha[:12]} is not a program commit: {why}")
    ev_ = e.get("evidence")
    if not isinstance(ev_, list) or not ev_:
        probs.append(f"{tag}: no evidence")
        ev_ = []
    for item in ev_:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str) or not isinstance(item.get("sha256"), str):
            probs.append(f"{tag}: an evidence item is not {{ref, sha256}}")
            continue
        ref = item["ref"]
        data = blob_at("HEAD", ref)
        if data is None:
            probs.append(f"{tag}: evidence {ref} is not a file at HEAD")
            continue
        if lf_sha256(data) != item["sha256"]:
            probs.append(f"{tag}: evidence {ref} sha256 is stale, current LF sha256 {lf_sha256(data)[:12]}")
        if ref.startswith(f"{PROG}/measurements/") and is_smoke(data) and "smoke" not in st.lower():
            probs.append(f"{tag}: cites a smoke measurement ({ref}) but the statement never says smoke")
    return probs


def delta_problems(led: dict) -> list:
    d = led.get("deltas")
    if not isinstance(d, dict):
        return ["ledger `deltas` is not an object"]
    pillar_ids = [p.get("id") for p in (led.get("frozen") or {}).get("pillars", [])]
    probs: list = []
    seen: set = set()
    for kind in DELTA_KINDS:
        lst = d.get(kind)
        if not isinstance(lst, list) or not lst:
            probs.append(f"deltas.{kind}: empty or not a list")
            continue
        for e in lst:
            probs += delta_entry_problems(kind, e, pillar_ids, seen)
    return probs


def discover_phases(root: Path):
    """Phase numbers of the `NN-*` directories holding a *-SUMMARY.md or a *-VERIFICATION.md; None when root is absent."""
    if not root.is_dir():
        return None
    out = []
    for d in sorted(root.iterdir()):
        m = re.match(r"^(\d{2})-", d.name)
        if m and d.is_dir() and (any(d.glob("*-SUMMARY.md")) or any(d.glob("*-VERIFICATION.md"))):
            out.append(int(m.group(1)))
    return out


def coverage_problems(led: dict, phases: list) -> list:
    d = led.get("deltas") if isinstance(led.get("deltas"), dict) else {}
    probs = []
    for ph in phases:
        for kind in DELTA_KINDS:
            lst = d.get(kind) if isinstance(d.get(kind), list) else []
            if not any(isinstance(e, dict) and e.get("phase") == ph for e in lst):
                probs.append(f"phase {ph:02d} shipped but has no {kind} delta")
    return probs


GOOD_COMMIT = "143eaca5cccf798d231e8a5caab0dcb6952a8930"     # feat(06-01) R2 printer: a program commit
GOOD_EVIDENCE = f"{PROG}/evidence/C.md"
SMOKE_EVIDENCE = f"{PROG}/measurements/L-KME-G-2026-10-04.md"


def _ev(ref: str) -> dict:
    return {"ref": ref, "sha256": lf_sha256(blob_at("HEAD", ref) or b"")}


def syn_delta(ident: str, **over) -> dict:
    e = {"id": ident, "phase": 2, "pillars": ["C"], "statement": "a synthetic delta", "plane": "gex44",
         "commits": [GOOD_COMMIT], "evidence": [_ev(GOOD_EVIDENCE)]}
    e.update(over)
    return e


def syn_ledger(led: dict, product=None, intelligence=None) -> dict:
    out = copy.deepcopy(led)
    out["deltas"] = {"product": product if product is not None else [syn_delta("SYN-P")],
                     "intelligence": intelligence if intelligence is not None else [syn_delta("SYN-I")]}
    return out


def _full_sha(short: str) -> str | None:
    r = git("rev-parse", "--verify", "--quiet", f"{short}^{{commit}}")
    return r.stdout.strip() if r.returncode == 0 else None


# --------------------------------------------------------------------------- ledger gates
def g_ledger_reviews_pinned():
    base = {"reviews": {k: {"file": rel, "sha256": current_lf_sha256(rel)} for k, rel in REVIEW_KEYS.items()}}

    def mut(fn):
        d = copy.deepcopy(base)
        fn(d)
        return reviews_problems(d)
    ctl = {
        "pins naming the current files are accepted": reviews_problems(base) == [],
        "a flipped sha is reported with the current sha": has(mut(lambda d: d["reviews"]["ukdl"].__setitem__("sha256", "0" * 64)),
                                                           "current LF sha256"),
        "a review naming another file is reported": has(mut(lambda d: d["reviews"]["cbr"].__setitem__("file", UKDL_REVIEW_REL)),
                                                       "must name"),
        "a null review is reported": has(mut(lambda d: d["reviews"].__setitem__("ukdl", None)), "must be exactly"),
        "a missing review is reported": has(mut(lambda d: d["reviews"].pop("cbr")), "must be exactly"),
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    probs = reviews_problems(json.loads(read_text(LEDGER_REL)))
    return not probs, f"ledger reviews pin {sorted(REVIEW_KEYS)} to their current LF sha256; problems={probs[:3]}, {len(ctl)} controls report"


def g_ledger_deltas():
    led = json.loads(read_text(LEDGER_REL))
    peer = _full_sha("5cdd7d9f")
    foreign_phase = _full_sha("d5d5fa0581223e8388225bce556e23543bb7602a")

    def one(**over):
        return delta_problems(syn_ledger(led, product=[syn_delta("SYN-P", **over)]))
    ctl = {
        "a clean synthetic entry is accepted": delta_problems(syn_ledger(led)) == [],
        "an empty list is reported": has(delta_problems({**syn_ledger(led), "deltas": {"product": [], "intelligence": [
            syn_delta("SYN-I")]}}), "empty or not a list"),
        "a duplicate id is reported": has(delta_problems(syn_ledger(led, product=[syn_delta("SYN-P")],
                                                                    intelligence=[syn_delta("SYN-P")])), "used twice"),
        "a 7-hex commit is reported": has(one(commits=[GOOD_COMMIT[:7]]), "not 40 hex"),
        "an unreachable commit is reported": has(one(commits=["a" * 40]), "not reachable from HEAD"),
        "a forged subject with a foreign path is refused by the pure rule": program_commit_problem(
            "fix(incremental-cognition): x", ["tools/mission_capsule.py"]) is not None,
        "a foreign subject with a program path is refused by the pure rule": program_commit_problem(
            "feat(mission_capsule): x", ["tools/test_kme_replay.py"]) is not None,
        "a phase scope with a program path is accepted by the pure rule": program_commit_problem(
            "docs(05): x", [f"{PROG}/evidence/L.md"]) is None,
        "a missing evidence ref is reported": has(one(evidence=[{"ref": f"{PROG}/evidence/no-such.md", "sha256": "0" * 64}]),
                                                  "not a file at HEAD"),
        "a stale evidence sha is reported": has(one(evidence=[{"ref": GOOD_EVIDENCE, "sha256": "0" * 64}]), "sha256 is stale"),
        "a terminal name in a statement is reported": has(one(statement="closed as IMPLEMENTED_AND_VERIFIED"), "terminal name"),
        "a smoke measurement cited without the word smoke is reported": has(
            one(evidence=[_ev(SMOKE_EVIDENCE)], statement="a measured ranking"), "smoke measurement"),
        "a smoke measurement cited with the word is accepted": one(
            evidence=[_ev(SMOKE_EVIDENCE)], statement="a smoke ranking on KME-G") == [],
        "an unknown plane is reported": has(one(plane="mars"), "plane"),
        "an unknown pillar is reported": has(one(pillars=["Z"]), "pillar ids"),
        "a phase outside 1..6 is reported": has(one(phase=7), "phase 7"),
    }
    if peer and commit_reachable(peer):
        ctl["a reachable peer commit (foreign subject and paths) is reported"] = has(one(commits=[peer]), "not a program commit")
    if foreign_phase and commit_reachable(foreign_phase):
        ctl["a reachable foreign phase-scoped commit (another workstream) is reported"] = has(
            one(commits=[foreign_phase]), "not a program commit")
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    probs = delta_problems(led)
    n = {k: len((led.get("deltas") or {}).get(k) or []) for k in DELTA_KINDS}
    return not probs, f"deltas {n}; every commit a reachable program commit, every evidence ref at HEAD with its current sha; problems={probs[:3]}, {len(ctl)} controls report"


def g_ledger_deltas_cover_phases():
    led = json.loads(read_text(LEDGER_REL))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "01-one").mkdir()
        (root / "01-one" / "01-01-SUMMARY.md").write_text("x", encoding="utf-8")
        (root / "02-two").mkdir()
        (root / "02-two" / "02-VERIFICATION.md").write_text("x", encoding="utf-8")
        (root / "03-planned-only").mkdir()
        (root / "03-planned-only" / "03-01-PLAN.md").write_text("x", encoding="utf-8")
        found = discover_phases(root)
    syn = {"deltas": {"product": [{"phase": 1}], "intelligence": [{"phase": 1}]}}
    ctl = {
        "a summary or a verification makes a phase shipped, a plan alone does not": found == [1, 2],
        "a shipped phase without deltas is reported": has(coverage_problems(syn, found), "phase 02 shipped"),
        "a phase with both deltas is not reported": not has(coverage_problems(syn, found), "phase 01"),
        "a missing product list is reported": has(coverage_problems({"deltas": {"intelligence": [{"phase": 1}]}}, [1]), "no product delta"),
        "an absent phases directory is None": discover_phases(root / "absent") is None,
    }
    if not all(ctl.values()):
        return False, f"controls failed: {[k for k, v in ctl.items() if not v]}"
    phases = discover_phases(REPO / PHASES_DIR)
    if phases is None:
        return "SKIP", f"{PHASES_DIR} is absent in this clone; coverage is not measured, never passed"
    if not phases:
        return False, f"no shipped phase discovered under {PHASES_DIR}"
    probs = coverage_problems(led, phases)
    return not probs, f"shipped phases {phases} each carry a product and an intelligence delta; problems={probs[:4]}, {len(ctl)} controls report"


GATES = [
    ("V-ICN-CANDIDATES-SHAPE", g_candidates_shape),
    ("V-ICN-EVIDENCE-RESOLVES", g_evidence_resolves),
    ("V-ICN-REVIEW-COVERAGE", g_review_coverage),
    ("V-ICN-REVIEW-AGAINST-TRUTHFUL", g_review_against),
    ("V-ICN-DUPLICATE-CITED", g_duplicate_cited),
    ("V-ICN-CBR-TRANSFER-RULE", g_cbr_transfer_rule),
    ("V-ICN-PROMOTION-NEVER-SILENT", g_promotion_never_silent),
    ("V-ICN-BUNDLE-N", g_bundle_n),
    ("V-ICN-LEDGER-REVIEWS-PINNED", g_ledger_reviews_pinned),
    ("V-ICN-LEDGER-DELTAS", g_ledger_deltas),
    ("V-ICN-LEDGER-DELTAS-COVER-PHASES", g_ledger_deltas_cover_phases),
]


def summary_line() -> str:
    p = sum(1 for r in RESULTS if r[0] == "PASS")
    f = sum(1 for r in RESULTS if r[0] == "FAIL")
    s = sum(1 for r in RESULTS if r[0] == "SKIP")
    i = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"ICN_PASS={p}/{p + f}  threshold={p + f}/{p + f}  skipped={s}  inconclusive={i}"


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    return 0 if counted and all(r[0] == "PASS" for r in counted) else 1


# --------------------------------------------------------------------------- mutation drill
GATE_FN = dict(GATES)
DRILL_GATES = [n for n, _ in GATES]


def _quiet(names) -> dict:
    """Run the named gates with printing off; {gate: passed} for the ones that ran to PASS/FAIL."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for n in names:
            run_gate(n, GATE_FN[n])
    finally:
        QUIET[0] = False
    return {g: st == "PASS" for st, g, _ in RESULTS[start:] if st in ("PASS", "FAIL")}


def _patch(name: str, value):
    """Rebind a module-level function (the gates resolve it at call time); the returned callable restores it."""
    saved = globals()[name]
    globals()[name] = value
    return lambda: globals().__setitem__(name, saved)


def _without(orig, needle: str):
    """A mutant of a *_problems function that silently drops the problems naming `needle`."""
    def mutant(*a, **k):
        return [p for p in orig(*a, **k) if needle not in p]
    return mutant


def _m_coverage_blind():
    return _patch("review_problems", _without(review_problems, "no verdict row"))


def _m_refs_always():
    return _patch("ref_resolves", lambda ref: None)


def _m_transfer_blind():
    return _patch("transfer_problems", lambda *a, **k: [])


def _m_promotion_blind():
    return _patch("promotion_problems", lambda *a, **k: [])


def _m_level_unchecked():
    return _patch("candidate_problems", _without(candidate_problems, "id letter"))


def _m_sha_unchecked():
    return _patch("against_problems", _without(against_problems, "recorded"))


def _m_review_sha_unchecked():
    return _patch("reviews_problems", _without(reviews_problems, "current LF sha256"))


def _m_reachability_unchecked():
    return _patch("delta_problems", _without(delta_problems, "not reachable from HEAD"))


def _m_smoke_unlabelled_ok():
    return _patch("delta_problems", _without(delta_problems, "smoke measurement"))


def _m_terminal_name_ok():
    return _patch("delta_problems", _without(delta_problems, "terminal name"))


def _m_coverage_blind_phases():
    return _patch("coverage_problems", lambda *a, **k: [])


def _m_program_path_rule_skipped():
    orig = program_commit_problem
    return _patch("program_commit_problem", lambda subject, paths: orig(subject, [PROG + "/x"]))


MUTANTS = [
    ("M1 review_problems ignores missing rows", _m_coverage_blind, ["V-ICN-REVIEW-COVERAGE"]),
    ("M2 ref_resolves accepts every ref", _m_refs_always, ["V-ICN-EVIDENCE-RESOLVES"]),
    ("M3 transfer_problems returns nothing", _m_transfer_blind, ["V-ICN-CBR-TRANSFER-RULE"]),
    ("M4 promotion_problems returns nothing", _m_promotion_blind, ["V-ICN-PROMOTION-NEVER-SILENT"]),
    ("M5 candidate_problems skips the id-letter / level check", _m_level_unchecked, ["V-ICN-CANDIDATES-SHAPE"]),
    ("M6 against_problems skips the sha256 comparison", _m_sha_unchecked, ["V-ICN-REVIEW-AGAINST-TRUTHFUL"]),
    ("M7 reviews_problems skips the sha256 comparison", _m_review_sha_unchecked, ["V-ICN-LEDGER-REVIEWS-PINNED"]),
    ("M8 delta_problems skips the reachability rule", _m_reachability_unchecked, ["V-ICN-LEDGER-DELTAS"]),
    ("M9 delta_problems skips the smoke-label rule", _m_smoke_unlabelled_ok, ["V-ICN-LEDGER-DELTAS"]),
    ("M10 delta_problems skips the terminal-name rule", _m_terminal_name_ok, ["V-ICN-LEDGER-DELTAS"]),
    ("M11 coverage_problems returns nothing", _m_coverage_blind_phases, ["V-ICN-LEDGER-DELTAS-COVER-PHASES"]),
    ("M12 program_commit_problem skips the program-path rule", _m_program_path_rule_skipped, ["V-ICN-LEDGER-DELTAS"]),
]


def run_drill() -> int:
    """Control first (every gate green), each mutant applied and restored, then an unmutated rerun."""
    control = _quiet(DRILL_GATES)
    control_ok = len(control) == len(DRILL_GATES) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: {sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, targets in MUTANTS:
        restore = apply()
        try:
            seen = _quiet(targets)
        finally:
            restore()
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)}")
        else:
            print(f"SURVIVED {label} (still green or absent: {', '.join(t for t in targets if seen.get(t) is not False)})")
    after = _quiet(DRILL_GATES)
    clean = len(after) == len(DRILL_GATES) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: {sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
