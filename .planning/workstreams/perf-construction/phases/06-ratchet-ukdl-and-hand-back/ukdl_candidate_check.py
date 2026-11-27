"""ukdl_candidate_check.py - phase-local shape checker for the append-only UKDL candidate file
(plan 06-02, PERF-06, D6-06). It judges SHAPE and POINTERS, never whether a rule is true.

  selftest                  drive each bad shape and a good one against the checker (footer UKDL_SELFTEST=k/n)
  check FILE                validate every candidate block of FILE (footer UKDL_CHECK=k/n)
  sweep [--wide] TERM [TERM ...]
                            ownership sweep: for each regex term, the files (names and count) among the three
                            aggregates and vault/knowledge_base/*.md that contain it; --wide adds
                            vault/knowledge_base recursively and skills/*/SKILL.md

Candidate block shape (a `### ID` heading then `- key: value` lines):
  kind, statement, evidence (path[:line|#section] separated by `;`), measured, plane, scope,
  ownership sweep, status.

Stdlib only. Registered nowhere. Never imported from tools/ or modules/ (D6-01).
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_root():
    d = HERE
    while True:
        if os.path.isdir(os.path.join(d, "vault", "knowledge_base")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("ukdl_candidate_check: no vault/knowledge_base above " + HERE)
        d = parent


ROOT = find_root()
os.chdir(ROOT)

AGGREGATES = ("vault/knowledge_base/ukdl-universal.md", "vault/knowledge_base/session_lessons.md",
              "vault/hard_rules/HARD_RULES.md")
PLANES = ("GEX44", "LAPTOP-ONLY", "REPO-STATIC", "SPEC")
SCOPES = ("#CROSS-PROJECT", "#PP-LOCAL")
STATUS = "CANDIDATE - NOT PROMOTED"
ID_RX = re.compile(r"^(HR|PR|T)-[A-Z0-9-]+-\d{3}$")
HOME_RX = re.compile(r"(/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\|[A-Za-z]:/Users/)")
BLOCK_RX = re.compile(r"^### (\S+)\s*$", re.M)


def parse_blocks(text):
    """[{id, fields, text, line}] for each `### ID` block; fields maps lowercase key -> value."""
    marks = list(BLOCK_RX.finditer(text))
    blocks = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end]
        fields = {}
        for fm in re.finditer(r"^- ([A-Za-z ]+):\s*(.*)$", body, re.M):
            fields.setdefault(fm.group(1).strip().lower(), fm.group(2).strip())
        blocks.append({"id": m.group(1), "fields": fields, "text": m.group(0) + body,
                       "line": text.count("\n", 0, m.start()) + 1})
    return blocks


def aggregate_text():
    out = []
    for rel in AGGREGATES:
        try:
            with open(rel, "r", encoding="utf-8", errors="replace") as fh:
                out.append(fh.read())
        except OSError:
            out.append("")
    return "\n".join(out)


def pointer_path(ptr):
    p = ptr.strip().strip("`")
    p = re.split(r"#", p, 1)[0]
    p = re.sub(r":\d+(-\d+)?$", "", p)
    return p


# --------------------------------------------------------------------------- the checks
def c_id(b, ctx):
    return [] if ID_RX.match(b["id"]) else ["id %r does not match ^(HR|PR|T)-[A-Z0-9-]+-\\d{3}$" % b["id"]]


def c_kind(b, ctx):
    kind = b["fields"].get("kind", "")
    prefix = b["id"].split("-", 1)[0]
    return [] if kind == prefix and prefix in ("HR", "PR", "T") else ["kind %r does not match id prefix %r" % (
        kind, prefix)]


def c_unique(b, ctx):
    return [] if ctx["ids"].count(b["id"]) == 1 else ["id %s occurs %d times in the file" % (
        b["id"], ctx["ids"].count(b["id"]))]


def c_collision(b, ctx):
    rx = re.compile(r"(?<![A-Z0-9-])" + re.escape(b["id"]) + r"(?![A-Z0-9-])")
    return ["id %s already occurs in an aggregate (collides)" % b["id"]] if rx.search(ctx["aggregates"]) else []


def c_statement(b, ctx):
    return [] if b["fields"].get("statement") else ["no statement"]


def c_evidence(b, ctx):
    raw = b["fields"].get("evidence", "")
    ptrs = [p for p in raw.split(";") if p.strip()]
    if not ptrs:
        return ["no evidence pointer"]
    bad = []
    for p in ptrs:
        path = pointer_path(p)
        if not path or os.path.isabs(path) or not os.path.exists(path):
            bad.append(path or p)
    return ["dangling evidence pointer: " + ", ".join(bad)] if bad else []


def c_measured(b, ctx):
    return [] if b["fields"].get("measured") else ["no measured cost"]


def c_plane(b, ctx):
    plane = b["fields"].get("plane", "").split(" ", 1)[0].strip(",;.")
    return [] if plane in PLANES else ["plane %r is not one of %s" % (plane, ", ".join(PLANES))]


def c_scope(b, ctx):
    return [] if b["fields"].get("scope", "").split(" ", 1)[0] in SCOPES else ["scope tag missing or not in %s" % (
        ", ".join(SCOPES),)]


def c_sweep(b, ctx):
    s = b["fields"].get("ownership sweep", "")
    return [] if s.startswith("NEW") or s.startswith("EXTEND_EXISTING_OWNER") else [
        "no ownership sweep result (must start NEW or EXTEND_EXISTING_OWNER)"]


def c_status(b, ctx):
    return [] if b["fields"].get("status") == STATUS else ["status is not exactly %r" % STATUS]


def c_home(b, ctx):
    return ["absolute home or Windows user path in the block"] if HOME_RX.search(b["text"]) else []


CHECKS = {"id": c_id, "kind": c_kind, "unique": c_unique, "collision": c_collision, "statement": c_statement,
          "evidence": c_evidence, "measured": c_measured, "plane": c_plane, "scope": c_scope, "sweep": c_sweep,
          "status": c_status, "home": c_home}


def validate(b, ctx):
    problems = []
    for name, fn in CHECKS.items():
        problems += ["%s: %s" % (name, p) for p in fn(b, ctx)]
    return problems


def make_ctx(blocks):
    return {"ids": [b["id"] for b in blocks], "aggregates": aggregate_text()}


# --------------------------------------------------------------------------- commands
def cmd_check(path):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    blocks = parse_blocks(text)
    ctx = make_ctx(blocks)
    ok = 0
    for b in blocks:
        probs = validate(b, ctx)
        ok += 0 if probs else 1
        print("%s %s line=%d%s" % ("PASS" if not probs else "FAIL", b["id"], b["line"],
                                    "" if not probs else " :: " + " | ".join(probs)))
    n = len(blocks)
    print("UKDL_CHECK=%d/%d" % (ok, n))
    return 0 if n >= 1 and ok == n else 1


def good_block(ident="PR-SELFTEST-FIXTURE-SHAPE-001", **over):
    f = {"kind": ident.split("-", 1)[0], "statement": "a fixture statement",
         "evidence": "vault/knowledge_base/ukdl-universal.md", "measured": "fixture: 1 of 2",
         "plane": "GEX44", "scope": "#PP-LOCAL", "ownership sweep": "NEW (fixture sweep, 0 files)",
         "status": STATUS}
    f.update(over)
    lines = ["### " + ident] + ["- %s: %s" % (k, v) for k, v in f.items() if v is not None]
    return "\n".join(lines) + "\n"


def run_one(text):
    blocks = parse_blocks(text)
    ctx = make_ctx(blocks)
    return validate(blocks[0], ctx), blocks, ctx


def selftest():
    n = ok = 0

    def gate(name, cond, detail):
        nonlocal n, ok
        n += 1
        ok += 1 if cond else 0
        print("  %s %s: %s" % ("PASS" if cond else "FAIL", name, detail))

    probs, _, _ = run_one(good_block())
    gate("V-UKDL-GOOD", probs == [], "a well-formed block has no problems %s" % probs)
    probs, _, _ = run_one(good_block(plane=None))
    gate("V-UKDL-NO-PLANE", any(p.startswith("plane:") for p in probs), "missing plane -> %s" % probs)
    real = None
    m = re.search(r"(?<![A-Z0-9-])((?:HR|PR|T)-[A-Z0-9-]+-\d{3})(?![A-Z0-9-])", aggregate_text())
    if m:
        real = m.group(1)
    probs, _, _ = run_one(good_block(real or "PR-NO-AGGREGATE-ID-READ-001"))
    gate("V-UKDL-ID-COLLISION", bool(real) and any(p.startswith("collision:") for p in probs),
         "id %s read from an aggregate at run time -> %s" % (real, [p for p in probs if p.startswith("collision")]))
    probs, _, _ = run_one(good_block(evidence="vault/knowledge_base/no-such-file-for-selftest.md:3"))
    gate("V-UKDL-DANGLING-POINTER", any(p.startswith("evidence:") and "dangling" in p for p in probs),
         "pointer to a missing file -> %s" % probs)
    probs, _, _ = run_one(good_block(**{"ownership sweep": None}))
    gate("V-UKDL-NO-SWEEP", any(p.startswith("sweep:") for p in probs), "no ownership sweep line -> %s" % probs)
    probs, _, _ = run_one(good_block(status="PROMOTED"))
    gate("V-UKDL-STATUS", any(p.startswith("status:") for p in probs), "a promoted status -> %s" % probs)
    probs, _, _ = run_one(good_block(statement="see " + "/home" + "/someone/notes.md"))
    gate("V-UKDL-HOME-PATH", any(p.startswith("home:") for p in probs), "an absolute home path -> %s" % probs)
    probs, _, _ = run_one(good_block(kind="T"))
    gate("V-UKDL-KIND", any(p.startswith("kind:") for p in probs), "kind T on a PR id -> %s" % probs)
    twice = good_block() + good_block()
    blocks = parse_blocks(twice)
    probs = validate(blocks[0], make_ctx(blocks))
    gate("V-UKDL-DUPLICATE-ID", any(p.startswith("unique:") for p in probs), "an id twice in one file -> %s" % probs)
    # mutant control: with the plane check disabled the missing-plane fixture is accepted
    saved = CHECKS["plane"]
    try:
        CHECKS["plane"] = lambda b, ctx: []
        probs, _, _ = run_one(good_block(plane=None))
    finally:
        CHECKS["plane"] = saved
    gate("V-UKDL-MUTANT-CONTROL", probs == [], "with the plane check disabled the missing-plane block is ACCEPTED "
         "(the gate depends on that check); restored")
    print("UKDL_SELFTEST=%d/%d" % (ok, n))
    return 0 if ok == n else 1


def cmd_sweep(terms):
    wide = bool(terms) and terms[0] == "--wide"
    terms = terms[1:] if wide else terms
    files = list(AGGREGATES) + sorted(glob.glob("vault/knowledge_base/*.md"))
    scope = "3 aggregates + vault/knowledge_base/*.md"
    if wide:
        files += sorted(glob.glob("vault/knowledge_base/**/*.md", recursive=True))
        files += sorted(glob.glob("vault/knowledge_base/**/*.txt", recursive=True))
        files += sorted(glob.glob("skills/*/SKILL.md"))
        scope += " + vault/knowledge_base/**/*.md,*.txt + skills/*/SKILL.md (--wide)"
    files = list(dict.fromkeys(files))
    print("SWEEP files=%d (%s)" % (len(files), scope))
    for t in terms:
        rx = re.compile(t, re.I)
        hits = []
        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    if rx.search(fh.read()):
                        hits.append(os.path.basename(f))
            except OSError:
                continue
        print("SWEEP term=%r files=%d %s" % (t, len(hits), ",".join(hits[:6])))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "selftest":
        return selftest()
    if len(argv) == 3 and argv[1] == "check":
        return cmd_check(argv[2])
    if len(argv) >= 3 and argv[1] == "sweep":
        return cmd_sweep(argv[2:])
    print(__doc__.split("\n")[0])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
