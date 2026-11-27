"""ratchet_connect.py - phase-local connector from the perf-construction campaign to the real
Baseline Ratchet owner (modules/tower/ratchet.py, baselines.py, checks.py). Plan 06-02, PERF-06.

It drives the owner's OWN code against a SCRATCH generation root and never against
vault/tower/baselines. It does not reimplement any of the owner's rules: every refusal shown is a
RatchetRefusal raised by modules.tower.ratchet.

Subcommands (run with `python3 -I`, from anywhere inside the repo checkout):
  selftest                         drive the owner from both poles on a synthetic fixture
  locate FILE QUOTE                print the 1-indexed line locate_quote finds for QUOTE in FILE
  fill --entries FILE              derive evidence and origin lines from the cited records and write
                                   them into FILE (nothing is typed by hand)
  connect --entries FILE [--write-status]
                                   judge each proposed entry, promote the passing ones into a scratch
                                   root and verify the chain; prints the RATCHET_STATUS footer
  classify                         re-measure whether any existing family reaches this work

Stdlib plus the repo's own modules. Registered nowhere (D6-01). Every printed path is repo-relative.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def find_root():
    d = HERE
    while True:
        if os.path.isdir(os.path.join(d, "modules", "tower")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise SystemExit("ratchet_connect: no modules/tower above " + HERE)
        d = parent


ROOT = find_root()
os.chdir(ROOT)  # verify_origin opens origin paths relative to the working directory
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import checks as ck  # noqa: E402
from modules.tower import ratchet as rt  # noqa: E402

LIVE_BASELINES = os.path.realpath(os.path.join(ROOT, "vault", "tower", "baselines"))
SCRATCH_PREFIX = "p6-ratchet-"
SCRATCH_FAMILY = "perf_construction_scratch"
SCRATCH_AUTHORITY = "UNATTENDED scratch run, phase 06-02, not a live promotion"
LIVE_PATHS = ("vault/tower/baselines", "vault/tower/families")
LIVE_BLOCKED_REASONS = (
    "1. no family reaches this work: classify_prompt returns no family for the performance-measurement "
    "prompts (see CLASSIFY_NO_FAMILY), so a live entry would be unreachable (presence without reachability)",
    "2. a live promotion carries an Owner authority and this run has none (the scratch authority text is "
    "UNATTENDED and may not contain that word)",
    "3. the evidence is from one mission (one campaign, no second independent domain), the precedent for work "
    "with no family is a candidates file",
)
CLASSIFY_PROMPTS = (
    "the benchmark is slow, fix the p95 latency of the hook chain",
    "va lento al crear, mide cuanto tarda la construccion",
    "make the bench_all regression window host-state matched",
    "performance measurement metrology for session start",
)
CLASSIFY_CONTROL = "add a landing page website"


class ConnectRefusal(ValueError):
    """The script's own guard (scratch root or authority text); distinct from the owner's RatchetRefusal."""


def scrub(text, extra=()):
    for path, repl in list(extra) + [(ROOT, "."), (os.path.expanduser("~"), "~")]:
        if path and path not in ("/", ""):
            text = text.replace(path, repl)
    return text


def out(line=""):
    sys.stdout.write(scrub(line) + "\n")


# --------------------------------------------------------------------------- guards
def assert_scratch_root(path):
    """F1: refuse a root equal to or inside vault/tower/baselines (by realpath) before any write."""
    real = os.path.realpath(path)
    if real == LIVE_BASELINES or real.startswith(LIVE_BASELINES + os.sep):
        raise SystemExit(2)
    return real


def make_scratch():
    root = tempfile.mkdtemp(prefix=SCRATCH_PREFIX)
    assert_scratch_root(root)
    return root


def remove_scratch(root):
    real = os.path.realpath(root)
    tmp = os.path.realpath(tempfile.gettempdir())
    if real.startswith(tmp + os.sep) and os.path.basename(real).startswith(SCRATCH_PREFIX):
        shutil.rmtree(real, ignore_errors=True)
        return True
    return False


def check_authority(text):
    """Scratch mode: the authority text may never claim to be the Owner's (T-06-07)."""
    if not str(text or "").strip():
        raise ConnectRefusal("an authority text is required")
    if re.search(r"owner", str(text), re.I):
        raise ConnectRefusal("scratch authority may not contain the word Owner")
    return text


def promote_scratch(family, entries, reason, evidence, root, authority=SCRATCH_AUTHORITY):
    """Script guard first (root, authority), then the owner's own promote_with_evidence."""
    assert_scratch_root(root)
    check_authority(authority)
    return rt.promote_with_evidence(family, entries, reason, authority, evidence, root=root)


def live_tree_clean():
    r = subprocess.run(["git", "status", "--porcelain", "--", *LIVE_PATHS], capture_output=True, text=True,
                       cwd=ROOT)
    return r.returncode == 0 and r.stdout.strip() == "", r.stdout.strip()


# --------------------------------------------------------------------------- reading evidence from records
def _read(rel):
    path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def grab(spec):
    """(value, line) from the first match of spec['pattern'] in spec['file'], or (None, why)."""
    if not isinstance(spec, dict) or not spec.get("file") or not spec.get("pattern"):
        return None, "no source declared"
    text = _read(spec["file"])
    if text is None:
        return None, "file unreadable: %s" % spec["file"]
    m = re.search(spec["pattern"], text, re.S | re.M)
    if not m:
        return None, "pattern not found in %s" % spec["file"]
    value = m.group(1) if m.groups() else m.group(0)
    return value, text.count("\n", 0, m.start()) + 1


def derive_evidence(entry):
    """Evidence read from the cited records. Returns (evidence_dict, source_problems). A part that cannot
    be read stays absent so the owner's evidence_problems names it; nothing is invented (F4)."""
    src = entry.get("sources") or {}
    ev_in = entry.get("evidence") or {}
    problems, ev = [], {}
    imp_in = ev_in.get("improvement") or {}
    imp = {"run": str(imp_in.get("run") or ""), "measure": str(imp_in.get("measure") or "")}
    for part in ("before", "after"):
        val, why = grab(src.get(part))
        if val is None:
            problems.append("%s: %s" % (part, why))
        else:
            try:
                imp[part] = int(val)
            except ValueError:
                problems.append("%s: not an integer: %r" % (part, val))
    if "before" in imp or "after" in imp or imp["run"]:
        ev["improvement"] = imp
    negs = []
    for spec in src.get("negative_controls") or []:
        val, why = grab(spec)
        if val is None:
            problems.append("negative_control %s: %s" % (spec.get("name"), why))
            continue
        try:
            negs.append({"name": str(spec.get("name") or ""), "rc": int(val)})
        except ValueError:
            problems.append("negative_control %s: not an integer: %r" % (spec.get("name"), val))
    ev["negative_controls"] = negs
    reuse = {}
    rspec = src.get("reuse_run")
    if rspec:
        val, why = grab(rspec)
        if val is None:
            problems.append("reuse run: %s" % why)
        else:
            reuse["run"] = str(rspec.get("name") or "")
    pspec = src.get("reuse_pointer")
    if pspec:
        val, why = grab(pspec)
        if val is None:
            problems.append("reuse pointer: %s" % why)
        else:
            reuse["pointer"] = "%s:%d" % (pspec["file"], why)
    if reuse:
        ev["reuse"] = reuse
    return ev, problems


def short_problems(problems):
    names = []
    for p in problems:
        name = re.split(r"[ :(]", p, 1)[0]
        if name not in names:
            names.append(name)
    return names


def judge_entry(entry):
    """One proposed entry through the owner's own judges. Never mutates the entry."""
    res = {"id": entry.get("id", "?"), "origin": "?", "check": "?", "evidence": "?", "notes": []}
    o = entry.get("origin") or {}
    q = o.get("quote")
    if not o.get("file") or not q or not os.path.isfile(o["file"]):
        res["origin"] = "FILE_MISSING" if o.get("file") and not os.path.isfile(o["file"]) else "MALFORMED"
    elif bl.locate_quote(o["file"], q) == 0:
        res["origin"] = "QUOTE_MISSING"          # F3: never edited to fit
    else:
        res["origin"] = bl.verify_origin(entry)
    res["check"] = ck.evaluate(entry, ROOT).outcome
    ev, src_problems = derive_evidence(entry)
    res["derived"] = ev
    missing = []
    if src_problems:
        res["notes"].append("source: " + "; ".join(src_problems))
    if ev != (entry.get("evidence") or {}):
        missing.append("evidence_not_equal_to_records")
    owner_bad = rt.evidence_problems(ev)
    missing += [p.split(" needs")[0] for p in owner_bad]
    res["evidence"] = "ok" if not missing and not src_problems else "missing: " + ", ".join(
        missing + [p for p in short_problems(src_problems) if p not in missing])
    res["promotable"] = (res["origin"] == bl.VERIFIED and res["check"] == ck.PASS and res["evidence"] == "ok")
    return res


def owner_entry(entry):
    return {k: entry[k] for k in ("id", "requirement", "why", "origin", "class", "check")}


# --------------------------------------------------------------------------- selftest
class Gates:
    def __init__(self):
        self.n = 0
        self.ok = 0

    def gate(self, name, cond, detail=""):
        self.n += 1
        self.ok += 1 if cond else 0
        out("  %s %s: %s" % ("PASS" if cond else "FAIL", name, detail))
        return cond


def _refusal_text(fn):
    try:
        fn()
    except rt.RatchetRefusal as exc:
        return "RatchetRefusal: " + str(exc)
    except ConnectRefusal as exc:
        return "ConnectRefusal: " + str(exc)
    return None


def fixture_entry(ident, n):
    rel = "modules/tower/ratchet.py"
    quote = "Anti-downgrade for constitutive baselines"
    return {"id": ident, "requirement": "selftest fixture %d" % n,
            "why": "selftest fixture, not a campaign claim", "class": "C",
            "origin": {"file": rel, "line": bl.locate_quote(rel, quote), "quote": quote},
            "check": "file:" + rel}


def fixture_evidence(tag="A"):
    return {"improvement": {"run": "fixture-run-%s" % tag, "measure": "fixture gates passing", "before": 1,
                            "after": 2},
            "negative_controls": [{"name": "fixture-mutant", "rc": 1}],
            "reuse": {"run": "fixture-reuse-%s" % tag, "pointer": "selftest fixture"}}


def selftest():
    g = Gates()
    root = make_scratch()
    try:
        # Test 1 V-RAT-SCRATCH-ROOT
        inside = os.path.join(LIVE_BASELINES, "web_surface")
        codes = []
        for bad in (LIVE_BASELINES, inside):
            try:
                assert_scratch_root(bad)
                codes.append("accepted")
            except SystemExit as exc:
                codes.append(exc.code)
        link = os.path.join(root, "link-to-live")
        os.symlink(LIVE_BASELINES, link)
        try:
            assert_scratch_root(link)
            codes.append("accepted")
        except SystemExit as exc:
            codes.append(exc.code)
        fresh_ok = assert_scratch_root(root) == os.path.realpath(root)
        g.gate("V-RAT-SCRATCH-ROOT", codes == [2, 2, 2] and fresh_ok and os.path.basename(root).startswith(
            SCRATCH_PREFIX), "live root, a path inside it and a symlink to it exit %s; the fresh temp root %s" % (
            codes, "is accepted" if fresh_ok else "was refused"))
        # Test 2 V-RAT-B0
        e0 = fixture_entry("perf_construction_scratch-fixture-0", 0)
        p0 = promote_scratch(SCRATCH_FAMILY, [e0], "selftest B0", fixture_evidence("A"), root)
        doc = bl.load_generation(SCRATCH_FAMILY, 0, root)
        got = doc["entries"][0]
        res = ck.evaluate(got, ROOT)
        vo = bl.verify_origin(got)
        g.gate("V-RAT-B0", os.path.isfile(p0) and bl.generations(SCRATCH_FAMILY, root) == [0]
               and res.outcome == ck.PASS and vo == bl.VERIFIED and doc.get("promoted_by") == SCRATCH_AUTHORITY,
               "B0 written under the scratch root, read back, check %s, origin %s" % (res.outcome, vo))
        # Test 3 V-RAT-B1-CHAIN
        e1 = fixture_entry("perf_construction_scratch-fixture-1", 1)
        promote_scratch(SCRATCH_FAMILY, [e1], "selftest B1", fixture_evidence("B"), root)
        rep = rt.verify_chain(SCRATCH_FAMILY, root=root)
        b1 = bl.load_generation(SCRATCH_FAMILY, 1, root)
        g.gate("V-RAT-B1-CHAIN", rep.ok and rep.generations == [0, 1] and bool(b1.get("parent_sha256")),
               "verify_chain ok=%s generations=%s parent_sha256 anchored=%s" % (rep.ok, rep.generations,
                                                                                bool(b1.get("parent_sha256"))))
        before_gens = bl.generations(SCRATCH_FAMILY, root)
        # Test 4 V-RAT-REFUSE-NEG
        e2 = fixture_entry("perf_construction_scratch-fixture-2", 2)
        ev_empty = dict(fixture_evidence("C"), negative_controls=[])
        ev_rc0 = dict(fixture_evidence("C"), negative_controls=[{"name": "fixture-mutant", "rc": 0}])
        t_empty = _refusal_text(lambda: promote_scratch(SCRATCH_FAMILY, [e2], "x", ev_empty, root))
        t_rc0 = _refusal_text(lambda: promote_scratch(SCRATCH_FAMILY, [e2], "x", ev_rc0, root))
        g.gate("V-RAT-REFUSE-NEG", bool(t_empty and t_rc0 and t_empty.startswith("RatchetRefusal")
                                         and "negative_controls" in t_empty and "negative_controls" in t_rc0),
               "empty list -> %s | rc 0 -> %s" % (t_empty and t_empty[:70], t_rc0 and t_rc0[:70]))
        # Test 5 V-RAT-REFUSE-REUSE
        ev_same = fixture_evidence("C")
        ev_same["reuse"] = {"run": ev_same["improvement"]["run"], "pointer": "selftest fixture"}
        t_reuse = _refusal_text(lambda: promote_scratch(SCRATCH_FAMILY, [e2], "x", ev_same, root))
        g.gate("V-RAT-REFUSE-REUSE", bool(t_reuse and t_reuse.startswith("RatchetRefusal") and "reuse" in t_reuse),
               "reuse run equal to the improving run -> %s" % (t_reuse and t_reuse[:70]))
        # Test 6 V-RAT-REFUSE-AUTH
        t_auth = _refusal_text(lambda: rt.promote_with_evidence(SCRATCH_FAMILY, [e2], "x", "", fixture_evidence("C"),
                                                                root=root))
        t_owner = [_refusal_text(lambda a=a: promote_scratch(SCRATCH_FAMILY, [e2], "x", fixture_evidence("C"), root,
                                                             authority=a))
                   for a in ("Owner go-ahead", "the owner said so", "OWNER")]
        g.gate("V-RAT-REFUSE-AUTH", bool(t_auth and t_auth.startswith("RatchetRefusal") and "authority" in t_auth)
               and all(t and t.startswith("ConnectRefusal") for t in t_owner),
               "empty authority -> the owner's refusal; three authority texts naming the Owner -> the script's own guard")
        g.gate("V-RAT-REFUSALS-WROTE-NOTHING", bl.generations(SCRATCH_FAMILY, root) == before_gens,
               "generations before %s after %s" % (before_gens, bl.generations(SCRATCH_FAMILY, root)))
        # Test 7 V-RAT-TAMPER
        b0_path = os.path.join(root, SCRATCH_FAMILY, "B0.json")
        with open(b0_path, "rb") as fh:
            original = fh.read()
        with open(b0_path, "ab") as fh:
            fh.write(b" ")
        tampered = rt.verify_chain(SCRATCH_FAMILY, root=root)
        with open(b0_path, "wb") as fh:
            fh.write(original)
        restored = rt.verify_chain(SCRATCH_FAMILY, root=root)
        g.gate("V-RAT-TAMPER", (not tampered.ok) and tampered.tampered == [1] and restored.ok,
               "one appended byte to B0 -> tampered=%s ok=%s; restored bytes -> ok=%s" % (tampered.tampered,
                                                                                         tampered.ok, restored.ok))
        # Test 8 V-RAT-REGRESS
        fam2 = SCRATCH_FAMILY + "_regress"
        promote_scratch(fam2, [fixture_entry("perf_construction_scratch-fixture-9", 9)], "selftest", fixture_evidence("D"),
                        root)
        bl.write_generation(fam2, [], "drop an entry with no recorded change", root=root)
        rep2 = rt.verify_chain(fam2, root=root)
        g.gate("V-RAT-REGRESS", (not rep2.ok) and any(r["kind"] == rt.WITHDRAWN for r in rep2.regressions),
               "a B1 that drops a B0 entry with no recorded change -> regressions=%s" % rep2.regressions)
        # Mutant control: the refusal comes from the owner's rule, so disabling the rule must stop the refusal
        fam3 = SCRATCH_FAMILY + "_mutant"
        original_fn = rt.evidence_problems
        try:
            rt.evidence_problems = lambda ev: []
            t_mut = _refusal_text(lambda: promote_scratch(fam3, [fixture_entry("perf_construction_scratch-fixture-m", 7)],
                                                          "x", ev_empty, root))
        finally:
            rt.evidence_problems = original_fn
        t_back = _refusal_text(lambda: promote_scratch(fam3 + "b", [fixture_entry("perf_construction_scratch-fixture-m", 7)],
                                                       "x", ev_empty, root))
        g.gate("V-RAT-MUTANT-CONTROL", t_mut is None and bool(t_back and "negative_controls" in t_back),
               "with evidence_problems disabled the empty-control entry is ACCEPTED (the instrument can say no); "
               "restored it refuses again")
        # judge_entry from both poles (F3, F4)
        rec = os.path.join(root, "rec.txt")
        with open(rec, "w", encoding="utf-8") as fh:
            fh.write("SUITE_PASS=3/9\nSUITE_PASS=9/9\nmutant exit=1\nlater run ok\n")
        base = fixture_entry("perf_construction_scratch-judge", 3)
        base["sources"] = {"before": {"file": rec, "pattern": r"SUITE_PASS=(\d+)/9"},
                           "after": {"file": rec, "pattern": r"SUITE_PASS=9/(9)"},
                           "negative_controls": [{"name": "m", "file": rec, "pattern": r"mutant exit=(\d+)"}],
                           "reuse_run": {"name": "later", "file": rec, "pattern": r"later run ok"},
                           "reuse_pointer": {"file": rec, "pattern": r"later run ok"}}
        base["evidence"] = {"improvement": {"run": "r", "measure": "m"}}
        base["evidence"] = derive_evidence(base)[0]
        good = judge_entry(base)
        bad_q = json.loads(json.dumps(base))
        bad_q["origin"]["quote"] = "this sentence is not in the file at all"
        bad_rc = json.loads(json.dumps(base))
        bad_rc["sources"]["negative_controls"] = [{"name": "m", "file": rec, "pattern": r"(later run) ok"}]
        bad_src = json.loads(json.dumps(base))
        bad_src["sources"]["before"] = {"file": rec, "pattern": r"NOT_THERE=(\d+)"}
        j_q, j_rc, j_src = judge_entry(bad_q), judge_entry(bad_rc), judge_entry(bad_src)
        g.gate("V-RAT-JUDGE-POLES",
               good["promotable"] and (not j_q["promotable"]) and j_q["origin"] == "QUOTE_MISSING"
               and (not j_rc["promotable"]) and (not j_src["promotable"]) and "before" in j_src["evidence"],
               "good fixture promotable; missing quote -> %s; unreadable rc -> %s; unreadable before -> %s" % (
                   j_q["origin"], j_rc["evidence"], j_src["evidence"]))
    finally:
        removed = remove_scratch(root)
    clean, dirty = live_tree_clean()
    g.gate("V-RAT-LIVE-UNTOUCHED", clean and removed,
           "git status empty for vault/tower/baselines and vault/tower/families; scratch removed=%s" % removed)
    out("RATCHET_SELFTEST=%d/%d" % (g.ok, g.n))
    return 0 if g.ok == g.n else 1


# --------------------------------------------------------------------------- locate / fill / connect / classify
def cmd_locate(a):
    n = bl.locate_quote(a.file, a.quote)
    out("LOCATE %s line=%d" % (a.file, n))
    return 0 if n else 1


def load_entries(path):
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc, doc["entries"]


def save(path, doc):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def cmd_fill(a):
    doc, entries = load_entries(a.entries)
    for e in entries:
        o = e.get("origin") or {}
        if o.get("file") and o.get("quote") and os.path.isfile(o["file"]):
            n = bl.locate_quote(o["file"], o["quote"])
            if n:
                o["line"] = n
        ev, problems = derive_evidence(e)
        e["evidence"] = ev
        out("FILL %s origin_line=%s evidence_parts=%s source_problems=%d" % (
            e.get("id"), o.get("line"), sorted(ev), len(problems)))
        for p in problems:
            out("  source problem: " + p)
    save(a.entries, doc)
    return 0


def cmd_connect(a):
    doc, entries = load_entries(a.entries)
    if len(entries) > 5:
        out("connect: more than five entries proposed")
        return 2
    root = make_scratch()
    chain = None
    reached = 0
    try:
        judged = []
        for e in entries:
            r = judge_entry(e)
            judged.append((e, r))
            status = "PROMOTABLE_UNDER_OWNER_AUTHORITY" if r["promotable"] else "NOT_PROMOTABLE"
            out("ENTRY %s %s origin=%s check=%s evidence=%s" % (r["id"], status, r["origin"], r["check"],
                                                                r["evidence"]))
            for note in r["notes"]:
                out("  note: " + note)
            e["status_note"] = status if r["promotable"] else "NOT_PROMOTABLE: origin=%s check=%s evidence=%s" % (
                r["origin"], r["check"], r["evidence"])
        for e, r in judged:
            if not r["promotable"]:
                continue
            try:
                promote_scratch(SCRATCH_FAMILY, [owner_entry(e)], "scratch connection of %s" % e["id"],
                                r["derived"], root)
                reached += 1
            except rt.RatchetRefusal as exc:
                out("  OWNER REFUSED %s: %s" % (e["id"], exc))
                r["promotable"] = False
                e["status_note"] = "NOT_PROMOTABLE: owner refused: %s" % exc
        chain = rt.verify_chain(SCRATCH_FAMILY, root=root)
        gens = chain.generations
        a_ok = sum(1 for _, r in judged if r["promotable"])
        # every promoted generation must read back through the owner's own readers
        for n in gens:
            for ent in bl.load_generation(SCRATCH_FAMILY, n, root)["entries"]:
                if ck.evaluate(ent, ROOT).outcome != ck.PASS or bl.verify_origin(ent) != bl.VERIFIED:
                    out("  READBACK FAIL B%d %s" % (n, ent.get("id")))
                    chain.regressions.append({"generation": n, "id": ent.get("id"), "kind": "READBACK"})
        status = "CONNECTED_SCRATCH LIVE=BLOCKED" if reached else "NOT_CONNECTED"
        out("RATCHET_STATUS=%s generations=%d chain_ok=%s promotable=%d/%d" % (
            status, len(gens), chain.ok, a_ok, len(judged)))
        if reached:
            out("LIVE_BLOCKED reasons, in order:")
            for line in LIVE_BLOCKED_REASONS:
                out("  " + line)
        else:
            out("NOT_CONNECTED: the owner or the evidence rule refused every entry; an honest zero is a result")
    finally:
        remove_scratch(root)
    clean, dirty = live_tree_clean()
    out("LIVE_TREE_CLEAN=%s" % ("yes" if clean else "NO " + dirty))
    if a.write_status:
        save(a.entries, doc)
    if not clean:
        return 1
    return 0 if (chain is not None and chain.ok) else 1


def cmd_classify(a):
    from modules.tower.families import classify_prompt
    none = 0
    for p in CLASSIFY_PROMPTS:
        res = classify_prompt(p)
        none += 1 if not res else 0
        out("PROMPT %r -> %s" % (p, [f for f, _ in res]))
    ctl = classify_prompt(CLASSIFY_CONTROL)
    out("CONTROL %r -> %s" % (CLASSIFY_CONTROL, [f for f, _ in ctl]))
    out("CLASSIFY_NO_FAMILY=%d/4 CONTROL_REACHED=%s" % (none, ctl[0][0] if ctl else "none"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    p = sub.add_parser("locate")
    p.add_argument("file")
    p.add_argument("quote")
    p = sub.add_parser("fill")
    p.add_argument("--entries", required=True)
    p = sub.add_parser("connect")
    p.add_argument("--entries", required=True)
    p.add_argument("--write-status", action="store_true")
    sub.add_parser("classify")
    a = ap.parse_args(argv)
    return {"selftest": lambda: selftest(), "locate": lambda: cmd_locate(a), "fill": lambda: cmd_fill(a),
            "connect": lambda: cmd_connect(a), "classify": lambda: cmd_classify(a)}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
