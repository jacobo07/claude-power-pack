"""handoff_check.py - phase-local instrument for the Phase 6 hand-back (PERF-06, plan 06-03).

  python3 -I handoff_check.py inventory [--head REF]   print the counts derived from the phase files
  python3 -I handoff_check.py check FILE               check a HANDOFF.md against the derived counts
  python3 -I handoff_check.py selftest                 drive every refusal on in-memory documents

The counts of a hand-back (unknowns per phase, laptop-only items, Owner decisions, changed files) are
computed here from the phase VERIFICATION frontmatter, the LP ids of the phase EVIDENCE and VERIFICATION
files, STATE.md and `git diff --name-only <mission base> <head>`; the document carries one INVENTORY line
and the check recomputes it. The changed-file count is taken at the head the document states, so a later
commit (including the commit that adds the hand-back itself) does not move it.

Stdlib only, GEX44 plane, registered nowhere (D6-01). It reads files and runs `git` with list argv.
"""
import os
import re
import subprocess
import sys
import tempfile

BASE = "a0e12830"
FIRST_LINE = "Creation speed on the laptop: UNKNOWN"
SECTIONS = ["Owner summary", "Engineering handoff", "Laptop-only checklist",
            "Known unknowns", "Exact next task"]
LP_STATUS = "LAPTOP-ONLY / UNJUDGED"
LP_VALUE = "UNJUDGED"
NEXT_TASK = "LP-05"
NEXT_COMPANIONS = ["LP-07", "LP-08", "LP-10"]

# Closed list of claims the owner summary may never make (T-06-11, F1). Compared case-insensitively
# after whitespace is collapsed.
FORBIDDEN = [
    "faster on the laptop", "slower on the laptop", "creation is now faster", "creation is faster",
    "creation got faster", "creation is now slower", "speed-up measured", "speedup measured",
    "speed-up was measured", "measured speed-up", "improved creation speed", "creation speed improved",
    "creation speed regressed", "creation time reduced", "reduced creation time", "sped up creation",
    "fixed the slowness", "slowness is fixed", "slowness fixed",
]
CONDITIONAL = "measured on the laptop"   # allowed only with the word UNJUDGED within 200 characters

HERE = os.path.dirname(os.path.abspath(__file__))
PHS = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(HERE, *([".."] * 5)))
STATE = os.path.join(ROOT, ".planning", "workstreams", "perf-construction", "STATE.md")


# --------------------------------------------------------------------------- inventory

def _git(args, root=ROOT):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout, r.stderr


def parse_unknowns(text):
    """Count the entries under the `unknowns:` key of a frontmatter block. None when it cannot be read.

    Frontmatter is the text between the first two `---` lines. An entry is a line of two spaces, a dash
    and a quoted string; `unknowns: []` counts 0; a top-level key ends the block. No YAML library.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    block = lines[1:end]
    for i, ln in enumerate(block):
        if re.match(r"^unknowns:\s*\[\s*\]\s*$", ln):
            return 0
        if re.match(r"^unknowns:\s*$", ln):
            n = 0
            for nxt in block[i + 1:]:
                if re.match(r'^  - ["\']', nxt):
                    n += 1
                elif nxt and not nxt.startswith(" "):
                    break
            return n
    return None


def lp_ids_in(text):
    return set(re.findall(r"LP-\d{2}", text))


def owner_decisions_in(text):
    return sorted({int(n) for n in re.findall(r"OWNER DECISION NEEDED \((\d+)\)", text)})


def inventory(phs=PHS, state=STATE, head="HEAD", root=ROOT):
    """Return a dict; a value that cannot be read is None (absent is not zero)."""
    inv = {"unknowns": [], "lp_ids": [], "owner_ids": None, "changed_files": None, "head": None,
           "problems": []}
    lps = set()
    for n in range(1, 6):
        pre = "%02d-" % n
        dirs = sorted(d for d in os.listdir(phs) if d.startswith(pre) and os.path.isdir(os.path.join(phs, d)))
        ver = os.path.join(phs, dirs[0], "%02d-VERIFICATION.md" % n) if len(dirs) == 1 else None
        if ver is None or not os.path.isfile(ver):
            inv["unknowns"].append(None)
            inv["problems"].append("phase %d VERIFICATION file not found" % n)
            continue
        with open(ver, encoding="utf-8") as fh:
            vt = fh.read()
        u = parse_unknowns(vt)
        if u is None:
            inv["problems"].append("phase %d: no readable unknowns key" % n)
        inv["unknowns"].append(u)
        lps |= lp_ids_in(vt)
        ev = os.path.join(phs, dirs[0], "%02d-EVIDENCE.md" % n)
        if os.path.isfile(ev):
            with open(ev, encoding="utf-8") as fh:
                lps |= lp_ids_in(fh.read())
        else:
            inv["problems"].append("phase %d EVIDENCE file not found" % n)
    inv["lp_ids"] = sorted(lps)
    if os.path.isfile(state):
        with open(state, encoding="utf-8") as fh:
            inv["owner_ids"] = owner_decisions_in(fh.read())
    else:
        inv["problems"].append("STATE.md not found")
    rc, out, _ = _git(["rev-parse", "--verify", "--quiet", head + "^{commit}"], root)
    if rc == 0:
        full = out.strip()
        inv["head"] = full[:12]
        rc2, out2, _ = _git(["diff", "--name-only", BASE, full], root)
        if rc2 == 0:
            inv["changed_files"] = len([x for x in out2.split("\n") if x.strip()])
        else:
            inv["problems"].append("git diff against the mission base failed")
    else:
        inv["problems"].append("head %s does not resolve" % head)
    return inv


def inventory_line(inv):
    ukn = ",".join("?" if u is None else str(u) for u in inv["unknowns"])
    oids = inv["owner_ids"]
    return "INVENTORY unknowns=%s lp=%d lp_ids=%s owner_decisions=%s changed_files=%s head=%s" % (
        ukn, len(inv["lp_ids"]), ",".join(inv["lp_ids"]),
        "?" if oids is None else len(oids),
        "?" if inv["changed_files"] is None else inv["changed_files"],
        inv["head"] or "?")


def parse_inventory_line(text):
    lines = [ln for ln in text.split("\n") if ln.startswith("INVENTORY ")]
    if len(lines) != 1:
        return None, "expected exactly one INVENTORY line, found %d" % len(lines)
    kv = dict(re.findall(r"(\w+)=(\S*)", lines[0]))
    need = ["unknowns", "lp", "lp_ids", "owner_decisions", "changed_files", "head"]
    miss = [k for k in need if k not in kv]
    if miss:
        return None, "INVENTORY line lacks " + ",".join(miss)
    return kv, None


# --------------------------------------------------------------------------- file system seam

class RealFS:
    def __init__(self, root=ROOT):
        self.root = root

    def exists(self, rel):
        return os.path.exists(os.path.join(self.root, rel))

    def line(self, rel, n):
        try:
            with open(os.path.join(self.root, rel), encoding="utf-8") as fh:
                ls = fh.read().split("\n")
        except OSError:
            return None
        return ls[n - 1] if 1 <= n <= len(ls) else None

    def inventory(self, head):
        return inventory(head=head, root=self.root)


# --------------------------------------------------------------------------- the check

HEADING_RE = re.compile(r"^## (\d+)\. (.+?)\s*$")
TOKEN_RE = re.compile(r"`([^`\n]+)`")
PATH_RE = re.compile(r"^(?:\./)?[A-Za-z0-9_.][A-Za-z0-9_.\-]*(?:/[A-Za-z0-9_.\-]+)+/?$")
TOP_DIRS = {"tools", "modules", "vault", "hooks", "tests", "scripts", "governance", "wiki", "knowledge",
            "commands", "skills", ".planning", "docs"}
ABS_BAD = [re.compile(r"/home/\S"), re.compile(r"/Users/\S"), re.compile(r"[A-Za-z]:\\"),
           re.compile(r"\\Users\\")]


def split_sections(text):
    """Return (headings list of (num, title, line_index), lines)."""
    lines = text.split("\n")
    heads = []
    for i, ln in enumerate(lines):
        m = HEADING_RE.match(ln)
        if m:
            heads.append((int(m.group(1)), m.group(2), i))
    return heads, lines


def section_text(lines, heads, idx):
    start = heads[idx][2] + 1
    end = heads[idx + 1][2] if idx + 1 < len(heads) else len(lines)
    return "\n".join(lines[start:end])


def strip_fences(text):
    out, fenced = [], []
    infence, buf = False, []
    for ln in text.split("\n"):
        if ln.strip().startswith("```"):
            if infence:
                fenced.append("\n".join(buf))
                buf = []
            infence = not infence
            continue
        (buf if infence else out).append(ln)
    return "\n".join(out), fenced


def looks_like_path(tok):
    t = re.sub(r"(:\d+(-\d+)?|#L?\d+.*)$", "", tok)
    if t.startswith("/") or not PATH_RE.match(t):
        return None
    segs = t.rstrip("/").split("/")
    last = segs[-1]
    if t.endswith("/") or re.search(r"\.[A-Za-z0-9]+$", last) or segs[0] in TOP_DIRS:
        return t
    return None


def path_problems(text, fs):
    probs = []
    for rx in ABS_BAD:
        m = rx.search(text)
        if m:
            probs.append("absolute home or Windows user path: %r" % m.group(0)[:40])
    prose, fenced = strip_fences(text)
    toks = TOKEN_RE.findall(prose)
    for blk in fenced:
        toks.extend(blk.replace("\n", " ").split())
    for tok in toks:
        if tok.startswith("NEW:"):
            p = tok[4:]
            parent = os.path.dirname(p.rstrip("/"))
            if fs.exists(p):
                probs.append("NEW: path already exists (a laptop record is in the tree, revise the hand-back): " + p)
            elif parent and not fs.exists(parent):
                probs.append("NEW: path has no existing parent directory: " + p)
            continue
        p = looks_like_path(tok)
        if p is None:
            continue
        if not fs.exists(p):
            probs.append("backticked path does not exist: " + p)
    seen, out = set(), []
    for p in probs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def check_text(text, fs, mutant_skip_numbers=False):
    """Return a list of (code, ok, detail). ok False means the document is refused."""
    res = []

    def add(code, ok, detail=""):
        res.append((code, ok, detail))

    first = text.split("\n")[0] if text else ""
    add("V-HO-FIRSTLINE", first == FIRST_LINE, "first line is %r" % first[:80])

    heads, lines = split_sections(text)
    titles = [(n, t) for n, t, _ in heads]
    want = list(enumerate(SECTIONS, 1))
    add("V-HO-SECTIONS", titles == want, "headings %s" % (titles,))
    sec = {}
    if titles == want:
        for i, (_, t, _) in enumerate(heads):
            sec[t] = section_text(lines, heads, i)

    kv, err = parse_inventory_line(text)
    inv = None
    if kv is None:
        add("V-HO-COUNT", False, err)
    else:
        inv = fs.inventory(kv["head"])
        if inv["problems"] or inv["head"] is None:
            add("V-HO-COUNT", False, "inventory not computable: %s" % "; ".join(inv["problems"]))
        else:
            real = parse_inventory_line(inventory_line(inv))[0]
            bad = [k for k in ("unknowns", "lp", "lp_ids", "owner_decisions", "changed_files")
                   if kv[k] != real[k]]
            if mutant_skip_numbers:
                bad = []
            add("V-HO-COUNT", not bad,
                "differs from the inventory: " + ", ".join("%s doc=%s inventory=%s" % (k, kv[k], real[k]) for k in bad)
                if bad else "INVENTORY line equals the inventory")
            # numbers counted in prose must equal the inventory too
            prose_bad = []
            if not mutant_skip_numbers:
                for n, c in re.findall(r"Phase (\d): (\d+) unknowns", text):
                    i = int(n) - 1
                    if not (0 <= i < 5) or inv["unknowns"][i] != int(c):
                        prose_bad.append("Phase %s: %s unknowns" % (n, c))
                for c in re.findall(r"(\d+) laptop-only items", text):
                    if int(c) != len(inv["lp_ids"]):
                        prose_bad.append("%s laptop-only items" % c)
                for c in re.findall(r"(\d+) Owner decisions", text):
                    if inv["owner_ids"] is None or int(c) != len(inv["owner_ids"]):
                        prose_bad.append("%s Owner decisions" % c)
                for c in re.findall(r"(\d+) files changed", text):
                    if int(c) != inv["changed_files"]:
                        prose_bad.append("%s files changed" % c)
            add("V-HO-COUNT-PROSE", not prose_bad, "prose counts differ: %s" % prose_bad if prose_bad else "prose counts equal the inventory")

    # laptop-only checklist
    lp_rows, lp_probs = [], []
    if "Laptop-only checklist" in sec:
        for ln in sec["Laptop-only checklist"].split("\n"):
            if not re.match(r"^\|\s*LP-\d{2}\s*\|", ln):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            lp_rows.append(cells)
        ids = [c[0] for c in lp_rows]
        if len(set(ids)) != len(ids):
            lp_probs.append("duplicate LP rows")
        if inv is not None and not inv["problems"]:
            if set(ids) != set(inv["lp_ids"]):
                lp_probs.append("LP set differs: missing %s extra %s" % (
                    sorted(set(inv["lp_ids"]) - set(ids)), sorted(set(ids) - set(inv["lp_ids"]))))
        for c in lp_rows:
            if len(c) < 6:
                lp_probs.append("%s: row has %d cells, need 6" % (c[0], len(c)))
                continue
            lid, status, value, proc, rec, fal = c[:6]
            if status != LP_STATUS:
                lp_probs.append("%s: status is %r" % (lid, status))
            if value != LP_VALUE:
                lp_probs.append("%s: laptop value slot is %r, must be %s" % (lid, value, LP_VALUE))
            ptr = None
            for tok in TOKEN_RE.findall(proc):
                m = re.match(r"^(.+?):(\d+)$", tok)
                if m:
                    ptr = (m.group(1), int(m.group(2)))
                    break
            if ptr is None:
                lp_probs.append("%s: procedure cell has no `path:line` pointer" % lid)
            elif not fs.exists(ptr[0]):
                lp_probs.append("%s: pointer path does not exist: %s" % (lid, ptr[0]))
            else:
                ln_text = fs.line(ptr[0], ptr[1])
                if ln_text is None or lid not in ln_text:
                    lp_probs.append("%s: line %d of %s does not mention it" % (lid, ptr[1], ptr[0]))
            if not fal:
                lp_probs.append("%s: empty falsifier cell" % lid)
            if not rec:
                lp_probs.append("%s: empty record cell" % lid)
    else:
        lp_probs.append("checklist section not readable")
    add("V-HO-LP", not lp_probs, "; ".join(lp_probs) if lp_probs else "%d LP rows equal the inventory set" % len(lp_rows))

    # forbidden claims in the owner summary (line 1 up to the second heading)
    if "Owner summary" in sec:
        owner = first + "\n" + sec["Owner summary"]
    else:
        owner = "\n".join(lines[:heads[1][2]]) if len(heads) > 1 else text
    flat = re.sub(r"\s+", " ", owner).lower()
    hits = [p for p in FORBIDDEN if p in flat]
    for m in re.finditer(re.escape(CONDITIONAL), flat):
        window = flat[max(0, m.start() - 200): m.end() + 200]
        if "unjudged" not in window:
            hits.append(CONDITIONAL)
            break
    add("V-HO-CLAIM", not hits, "forbidden claim in the owner summary: %s" % hits if hits else "no forbidden claim")

    pp = path_problems(text, fs)
    add("V-HO-PATH", not pp, "; ".join(pp) if pp else "every backticked path exists, none absolute")

    # exact next task
    nt_probs = []
    if "Exact next task" in sec:
        s = sec["Exact next task"]
        _, fences = strip_fences(s)
        if len(fences) != 1 or len([x for x in fences[0].split("\n") if x.strip()]) != 1:
            nt_probs.append("needs exactly one fenced block holding exactly one command line")
        ids_in = re.findall(r"LP-\d{2}", s)
        if not ids_in or ids_in[0] != NEXT_TASK:
            nt_probs.append("first LP id must be %s" % NEXT_TASK)
        for c in NEXT_COMPANIONS:
            if c not in s:
                nt_probs.append("companion %s not named" % c)
        if "NEW:" not in s:
            nt_probs.append("no NEW: record path")
        if "Falsifier:" not in s:
            nt_probs.append("no Falsifier: line")
    else:
        nt_probs.append("section not readable")
    add("V-HO-NEXT", not nt_probs, "; ".join(nt_probs) if nt_probs else "one task, one command, one record, one falsifier")
    return res


def cmd_check(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    res = check_text(text, RealFS())
    bad = 0
    for code, ok, detail in res:
        print("%s %s: %s" % ("PASS" if ok else "FAIL", code, detail))
        bad += 0 if ok else 1
    print("HANDOFF_CHECK=%s" % ("PASS" if bad == 0 else "FAIL %d" % bad))
    return 0 if bad == 0 else 1


def cmd_inventory(head):
    inv = inventory(head=head)
    for i, u in enumerate(inv["unknowns"], 1):
        print("# phase %d unknowns: %s" % (i, "UNREADABLE" if u is None else u))
    print("# lp ids: %s" % ",".join(inv["lp_ids"]))
    print("# owner decision ids: %s" % ("UNREADABLE" if inv["owner_ids"] is None else ",".join(map(str, inv["owner_ids"]))))
    for p in inv["problems"]:
        print("# PROBLEM: " + p)
    print(inventory_line(inv))
    return 1 if inv["problems"] else 0


# --------------------------------------------------------------------------- tree check (plan 06-03, F5)

PH_REL = ".planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back"
STATE_REL = ".planning/workstreams/perf-construction/STATE.md"
ALLOWED_EXACT = {STATE_REL, "vault/tower/candidates/perf_construction.md",
                 "vault/knowledge_base/candidates/perf-construction-20261123.md"}
HASHED = ["vault/benchmarks/ledger.json", "vault/config/resource-floors.json"]


def tree_violations(porcelain_lines):
    """Porcelain lines whose path is outside PH, STATE.md and the two candidate files."""
    bad = []
    for ln in porcelain_lines:
        if not ln.strip():
            continue
        path = ln[3:].split(" -> ")[-1].strip().strip('"')
        if path in ALLOWED_EXACT or path.startswith(PH_REL + "/"):
            continue
        bad.append(path)
    return bad


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def cmd_tree(gates_record):
    rows, bad = [], 0
    rc, out, err = _git(["status", "--porcelain", "--", "tools", "modules", "hooks", "vault/config"])
    ok = rc == 0 and not out.strip()
    rows.append(("tools_modules_hooks_vault_config_clean", ok, "porcelain empty" if ok else (out.strip() or err.strip())[:300]))
    rc, out, err = _git(["status", "--porcelain", "--untracked-files=all"])
    viol = tree_violations(out.split("\n")) if rc == 0 else ["git status failed"]
    rows.append(("whole_tree_only_allowed_paths", rc == 0 and not viol,
                 "dirty paths are all inside the phase directory or STATE.md" if not viol else "outside: %s" % viol[:10]))
    try:
        with open(gates_record, encoding="utf-8") as fh:
            gt = fh.read()
    except OSError as exc:
        gt = ""
        rows.append(("hash_record_readable", False, str(exc)))
    before = dict((m.group(1), m.group(2)) for m in re.finditer(r"^HASH_BEFORE (\S+) ([0-9a-f]{64})$", gt, re.M))
    for p in HASHED:
        now = _sha256(p)
        same = before.get(p) == now
        rows.append(("hash_" + os.path.basename(p), same, "sha256 %s %s" % (now, "SAME as HASH_BEFORE in the gate record" if same else "DIFFERS or not recorded")))
    for name, ok, detail in rows:
        print("TREE %s %s: %s" % (name, "PASS" if ok else "FAIL", detail))
        bad += 0 if ok else 1
    print("HANDOFF_TREE=%s" % ("PASS" if bad == 0 else "FAIL %d" % bad))
    return 0 if bad == 0 else 1


# --------------------------------------------------------------------------- selftest

class FakeFS:
    def __init__(self, files, inv):
        self.files = files      # path -> list of lines; directories are implied
        self._inv = inv

    def exists(self, rel):
        r = rel.rstrip("/")
        return r in self.files or any(f.startswith(r + "/") for f in self.files)

    def line(self, rel, n):
        ls = self.files.get(rel)
        return ls[n - 1] if ls is not None and 1 <= n <= len(ls) else None

    def inventory(self, head):
        return self._inv


def _synthetic():
    inv = {"unknowns": [4, 6, 6, 7, 7], "lp_ids": ["LP-01", "LP-02", "LP-05"], "owner_ids": [1, 2, 3],
           "changed_files": 42, "head": "abcdef012345", "problems": []}
    files = {
        "tools/a.py": ["x"],
        "phases/e1.md": ["LP-01 procedure", "LP-02 procedure", "LP-05 procedure"],
        "phases/3/records": ["x"],
    }
    return inv, FakeFS(files, inv)


def _good_doc(inv):
    rows = ["| LP | Status | Laptop value | Procedure (source) | Record to bring back | Falsifier |",
            "|----|--------|--------------|--------------------|----------------------|-----------|"]
    for n, lid in enumerate(inv["lp_ids"], 1):
        rows.append("| %s | %s | %s | `phases/e1.md:%d` | `NEW:phases/3/records/%s.txt` | a laptop header that says GEX44 |"
                    % (lid, LP_STATUS, LP_VALUE, n, lid))
    return "\n".join([
        FIRST_LINE,
        "# Hand-back",
        "## 1. Owner summary",
        "The benchmark cannot hide a failed sample. Nothing here was measured on the laptop, so every laptop item is UNJUDGED.",
        "## 2. Engineering handoff",
        "Owner is `tools/a.py`. Phase 3: see below.",
        "## 3. Laptop-only checklist",
        *rows,
        "## 4. Known unknowns",
        "Phase 1: 4 unknowns. Phase 2: 6 unknowns. Phase 3: 6 unknowns. 3 laptop-only items. 3 Owner decisions. 42 files changed.",
        "%s" % inventory_line(inv),
        "## 5. Exact next task",
        "LP-05 first, beside LP-07, LP-08 and LP-10.",
        "```",
        "python tools/a.py --root <laptop transcript root>",
        "```",
        "Record: `NEW:phases/3/records/LP-05-laptop-distribution.txt`",
        "Falsifier: a laptop header that says GEX44.",
        "",
    ])


def selftest():
    results = []

    def gate(code, ok, detail):
        results.append(ok)
        print("%s %s: %s" % ("PASS" if ok else "FAIL", code, detail))

    def codes(doc, fs, **kw):
        return {c: (ok, d) for c, ok, d in check_text(doc, fs, **kw)}

    inv, fs = _synthetic()
    good = _good_doc(inv)
    base = codes(good, fs)
    gate("V-HO-GOOD-PASSES", all(ok for ok, _ in base.values()),
         "the synthetic document passes every code: %s" % sorted(c for c, (ok, _) in base.items() if not ok))

    # V-HO-INVENTORY on the real files
    real = inventory()
    shape_ok = (len(real["unknowns"]) == 5 and all(isinstance(u, int) for u in real["unknowns"])
                and real["lp_ids"] and all(re.match(r"^LP-\d{2}$", x) for x in real["lp_ids"])
                and real["owner_ids"] and isinstance(real["changed_files"], int) and real["changed_files"] > 0
                and not real["problems"])
    gate("V-HO-INVENTORY", bool(shape_ok),
         "real inventory unknowns=%s lp=%d owner_decisions=%s changed_files=%s head=%s" % (
             real["unknowns"], len(real["lp_ids"]), len(real["owner_ids"] or []), real["changed_files"], real["head"]))
    # parser poles: empty list counts 0, entries counted, next key ends the block, absent is None
    fm0 = '---\nstatus: x\nunknowns: []\nhuman: []\n---\nbody'
    fm3 = '---\nunknowns:\n  - "a"\n  - "b"\n  - \'c\'\nhuman_verification: []\n---\n  - "not counted"\n'
    fmn = '---\nstatus: x\n---\nbody'
    gate("V-HO-UNKNOWNS-PARSER", (parse_unknowns(fm0), parse_unknowns(fm3), parse_unknowns(fmn), parse_unknowns("no frontmatter"))
         == (0, 3, None, None), "[] -> 0, three quoted entries -> 3 (later key and body not counted), absent key -> None")
    with tempfile.TemporaryDirectory(prefix="p6-hand-") as td:
        st = os.path.join(td, "STATE.md")
        with open(st, "w", encoding="utf-8") as fh:
            fh.write("OWNER DECISION NEEDED (1) x\nOWNER DECISION NEEDED (2) y\nOWNER DECISION NEEDED (2) again\n")
        miss = inventory(phs=td, state=st)
        gate("V-HO-INVENTORY-ABSENT-IS-NOT-ZERO",
             miss["unknowns"] == [None] * 5 and len(miss["problems"]) >= 5 and miss["owner_ids"] == [1, 2],
             "an empty phases dir yields None per phase and named problems, never 0; duplicate decision ids count once")

    # V-HO-SECTIONS
    lines = good.split("\n")
    ok_all, notes = True, []
    for t in SECTIONS:
        d = "\n".join(l for l in lines if not l.startswith("## ") or t not in l)
        refused = not codes(d, fs)["V-HO-SECTIONS"][0]
        ok_all &= refused
        notes.append("%s:%s" % (t.split()[0], "refused" if refused else "ACCEPTED"))
    swapped = good.replace("## 1. Owner summary", "## 1. TMP").replace("## 2. Engineering handoff", "## 2. Owner summary").replace("## 1. TMP", "## 1. Engineering handoff")
    refused = not codes(swapped, fs)["V-HO-SECTIONS"][0]
    ok_all &= refused
    gate("V-HO-SECTIONS", ok_all, "each missing heading and an order swap refused (%s, swap:%s)" % (",".join(notes), refused))

    # V-HO-FIRSTLINE
    bad_firsts = ["", "Creation speed on the laptop: unknown", "Creation speed on the laptop: UNKNOWN.", "# Hand-back\n" + FIRST_LINE,
                  "Creation speed on the laptop: FASTER"]
    ok_all = True
    for b in bad_firsts:
        d = b + "\n" + "\n".join(lines[1:])
        ok_all &= not codes(d, fs)["V-HO-FIRSTLINE"][0]
    gate("V-HO-FIRSTLINE", ok_all, "%d wrong first lines refused" % len(bad_firsts))

    # V-HO-COUNT: change each number; the mutant control must accept the same documents
    ok_all, accepted_by_mutant = True, True
    muts = [("unknowns=4,6,6,7,7", "unknowns=4,6,6,7,8"), (" lp=3 ", " lp=4 "), ("owner_decisions=3", "owner_decisions=4"),
            ("changed_files=42", "changed_files=43"), ("lp_ids=LP-01,LP-02,LP-05", "lp_ids=LP-01,LP-02,LP-06")]
    for a, b in muts:
        d = good.replace(a, b)
        refused = not codes(d, fs)["V-HO-COUNT"][0]
        mutant = codes(d, fs, mutant_skip_numbers=True)["V-HO-COUNT"][0]
        ok_all &= refused and d != good
        accepted_by_mutant &= mutant
    prose = [("Phase 1: 4 unknowns", "Phase 1: 5 unknowns"), ("3 laptop-only items", "4 laptop-only items"),
             ("3 Owner decisions", "4 Owner decisions"), ("42 files changed", "41 files changed")]
    for a, b in prose:
        d = good.replace(a, b)
        refused = not codes(d, fs)["V-HO-COUNT-PROSE"][0]
        ok_all &= refused and d != good
    gate("V-HO-COUNT", ok_all, "each INVENTORY field and each prose count changed by one is refused (F2)")
    gate("V-HO-COUNT-MUTANT-CONTROL", accepted_by_mutant,
         "with the number comparison disabled in memory the same wrong INVENTORY lines are accepted, so the comparison is what refuses")

    # V-HO-LP
    ok_all, notes = True, []
    cases = {
        "drop LP-02": "\n".join(l for l in lines if not l.startswith("| LP-02")),
        "add LP-99": good.replace("## 4. Known unknowns", "| LP-99 | %s | %s | `phases/e1.md:1` | r | f |\n## 4. Known unknowns" % (LP_STATUS, LP_VALUE)),
        "status changed": good.replace("| LP-01 | %s |" % LP_STATUS, "| LP-01 | PASSED |"),
        "number in laptop slot": good.replace("| LP-01 | %s | %s |" % (LP_STATUS, LP_VALUE), "| LP-01 | %s | 53089 MB |" % LP_STATUS),
        "pointer path missing": good.replace("`phases/e1.md:1`", "`phases/none.md:1`"),
        "pointer line wrong": good.replace("`phases/e1.md:2`", "`phases/e1.md:1`"),
        "no pointer": good.replace("`phases/e1.md:3`", "see the file"),
        "duplicate row": good.replace("## 4. Known unknowns", "| LP-01 | %s | %s | `phases/e1.md:1` | r | f |\n## 4. Known unknowns" % (LP_STATUS, LP_VALUE)),
    }
    for name, d in cases.items():
        refused = not codes(d, fs)["V-HO-LP"][0]
        ok_all &= refused and d != good
        notes.append("%s:%s" % (name, "refused" if refused else "ACCEPTED"))
    gate("V-HO-LP", ok_all, "; ".join(notes))

    # V-HO-CLAIM
    ok_all, notes = True, []
    for ph in FORBIDDEN + [CONDITIONAL]:
        d = good.replace("Nothing here was measured on the laptop, so every laptop item is UNJUDGED.",
                         ("It is %s." % ph) if ph != CONDITIONAL else "The p95 was " + ph + ", and there is a long unrelated sentence. " * 6 + "End.")
        refused = not codes(d, fs)["V-HO-CLAIM"][0]
        ok_all &= refused
        if not refused:
            notes.append("ACCEPTED:" + ph)
    # case and line-break variants
    d = good.replace("Nothing here was measured on the laptop,", "Creation is\nNOW FASTER on the Laptop,")
    ok_all &= not codes(d, fs)["V-HO-CLAIM"][0]
    # a forbidden phrase outside the owner summary is not an owner-summary claim (control for scope)
    d = good.replace("Owner is `tools/a.py`.", "Owner is `tools/a.py`; the phrase 'faster on the laptop' is quoted here as a refused claim.")
    scoped = codes(d, fs)["V-HO-CLAIM"][0]
    # the conditional phrase passes when UNJUDGED sits within 200 characters
    d2 = good.replace("Nothing here was measured on the laptop, so every laptop item is UNJUDGED.", "The timing is measured on the laptop only after the operator runs it, UNJUDGED until then.")
    cond_ok = codes(d2, fs)["V-HO-CLAIM"][0]
    gate("V-HO-CLAIM", ok_all and scoped and cond_ok,
         "%d forbidden phrases, a case and line-break variant refused (%s); scope control passes outside the owner summary; the conditional phrase passes with UNJUDGED nearby"
         % (len(FORBIDDEN) + 1, "none accepted" if not notes else notes))

    # V-HO-PATH
    ok_all, notes = True, []
    path_cases = {
        "missing path": good.replace("`tools/a.py`", "`tools/missing.py`"),
        "absolute home path": good.replace("Phase 3: see below.", "See /home/someone/x.py now."),
        "windows user path": good.replace("Phase 3: see below.", "See C:\\Users\\Someone\\x now."),
        "NEW path that exists": good.replace("NEW:phases/3/records/LP-05-laptop-distribution.txt", "NEW:tools/a.py"),
        "NEW path without parent": good.replace("NEW:phases/3/records/LP-05-laptop-distribution.txt", "NEW:nowhere/dir/x.txt"),
        "missing path in a command": good.replace("python tools/a.py --root", "python tools/gone.py --root"),
    }
    for name, d in path_cases.items():
        refused = not codes(d, fs)["V-HO-PATH"][0]
        ok_all &= refused and d != good
        notes.append("%s:%s" % (name, "refused" if refused else "ACCEPTED"))
    ratio = good.replace("Phase 3: see below.", "The suite reads 53/53 and `14/15` rows.")
    ok_all &= codes(ratio, fs)["V-HO-PATH"][0]
    gate("V-HO-PATH", ok_all, "; ".join(notes) + "; ratios such as 53/53 are not read as paths")

    # V-HO-NEXT
    ok_all, notes = True, []
    next_cases = {
        "companion dropped": good.replace("LP-10", "LP-09"),
        "two commands": good.replace("python tools/a.py --root <laptop transcript root>", "python tools/a.py\npython tools/a.py"),
        "wrong first task": good.replace("LP-05 first,", "LP-01 first,"),
        "no falsifier": good.replace("Falsifier:", "Note:"),
        "no record": good.replace("Record: `NEW:phases/3/records/LP-05-laptop-distribution.txt`", "Record: none"),
    }
    for name, d in next_cases.items():
        refused = not codes(d, fs)["V-HO-NEXT"][0]
        ok_all &= refused and d != good
        notes.append("%s:%s" % (name, "refused" if refused else "ACCEPTED"))
    gate("V-HO-NEXT", ok_all, "; ".join(notes))

    # V-HO-TREE-ALLOWED: the classifier behind `tree` can say no (F5)
    okl = [" M %s/HANDOFF.md" % PH_REL, "?? %s/records/x.txt" % PH_REL, " M %s" % STATE_REL,
           " M vault/tower/candidates/perf_construction.md"]
    badl = [" M tools/bench_all.py", "?? hooks/new.js", " M ROADMAP.md", " M .planning/ROADMAP.md",
            "R  a.txt -> modules/x.py", "?? vault/config/other.json"]
    allowed_ok = tree_violations(okl) == []
    each_refused = all(tree_violations([b]) for b in badl)
    gate("V-HO-TREE-ALLOWED", allowed_ok and each_refused,
         "%d allowed shapes pass; %d paths outside the allowlist each refused (tools, hooks, roadmap, rename into modules, vault/config)"
         % (len(okl), len(badl)))

    n, total = sum(1 for r in results if r), len(results)
    print("HANDOFF_SELFTEST=%d/%d" % (n, total))
    return 0 if n == total else 1


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a:
        print(__doc__.split("\n")[0])
        return 2
    if a[0] == "selftest":
        return selftest()
    if a[0] == "inventory":
        head = "HEAD"
        if "--head" in a:
            head = a[a.index("--head") + 1]
        return cmd_inventory(head)
    if a[0] == "check" and len(a) == 2:
        return cmd_check(a[1])
    if a[0] == "tree" and len(a) == 2:
        return cmd_tree(a[1])
    print("usage: inventory [--head REF] | check FILE | tree GATES_RECORD | selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
