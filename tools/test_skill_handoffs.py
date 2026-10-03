#!/usr/bin/env python3
"""test_skill_handoffs.py -- drills for tools/skill_handoffs.py (phase 8 plan 03), both poles.

Each drill builds a temporary git repository: a freeze-like base commit holding copies of the positive-control
files and the program's evidence (taken from this checkout's HEAD blobs), a FROZEN_AT pointer, one clean added
tool, and I / K / L / M handoffs rendered by the tool itself. A drill clones that base, makes one change in a
commit, and compares the EXACT set of non-PASS `(pillar, part) -> outcome` results with the expected one.

Strings that would match a marker (a route definition, a pricing import, a CO-12 append, the searched name)
are built from fragments, so this file never matches the sweeps it drives (DH-03: it is in their aperture).

    python3 tools/test_skill_handoffs.py      # last line SKH_PASS=<p>/<n>, exit 0 iff all PASS
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
import skill_handoffs as skh  # noqa: E402
import skill_mirror_drift as smd  # noqa: E402
import verify_global_mirrors as vgm  # noqa: E402

REPO = skh.REPO
TOOL = "tools/skill_handoffs.py"
SELF = "tools/test_skill_handoffs.py"
COPIED = (list(skh.K_CONTROLS) + [skh.M_CONTROL] + list(skh.L_WRITER_CONTROLS) + list(skh.L_CLAIM_FILES)
          + [skh.LEDGER_REL] + [skh.EVIDENCE_REL + n for n in ("B-listing-floor.md", "E-contribution.md",
                                                               "D-coverage.md", "D-live-gex44.json",
                                                               "C-window-G.json")])
CLEAN_TOOL = "tools/clean_tool.py"
KLM = ("K", "L", "M")
I_BASE = {("I", "reachability"): "UNMEASURED", ("I", "retirement"): "UNMEASURED"}  # the base exports no scanner

results = []


def record(gate, ok, detail):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {gate} {detail}")


def g(repo, *args):
    p = subprocess.run([vgm._git_exe(), "-C", str(repo), *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout


def put(repo, rel, text):
    p = Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def commit(repo, msg, add=(), rm=()):
    if add:
        g(repo, "add", "--", *add)
    if rm:
        g(repo, "rm", "-q", "--", *rm)
    g(repo, "commit", "-q", "-m", msg)


def init(repo):
    g(repo, "init", "-q")
    for k, v in (("user.email", "drill@example.invalid"), ("user.name", "drill"), ("commit.gpgsign", "false"),
                 ("core.autocrlf", "false")):
        g(repo, "config", k, v)


def build_base(root: Path) -> Path:
    base = root / "base"
    base.mkdir()
    init(base)
    for rel in COPIED:
        text, why = skh.blob(REPO, "HEAD", rel)
        if text is None:
            raise RuntimeError(f"cannot copy {rel}: {why}")
        put(base, rel, text)
    commit(base, "freeze-like base", add=COPIED)
    frozen = g(base, "rev-parse", "HEAD").strip()
    put(base, skh.FROZEN_AT_REL, frozen + "\n")
    put(base, CLEAN_TOOL, "VALUE = 1\n")
    commit(base, "freeze pointer + one clean added tool", add=[skh.FROZEN_AT_REL, CLEAN_TOOL])
    for p in ("I",) + KLM:
        r = skh.measure(base, p)
        skh.write_handoff(base, p, skh.render(r))
    commit(base, "handoffs", add=[f"{skh.HANDOFF_DIR}{p}.md" for p in ("I",) + KLM])
    return base


def outcome_map(res) -> dict:
    return {(p, k): v[0] for p, parts in res.items() for k, v in parts.items()
            if not k.startswith("_") and v[0] != "PASS"}


def fmt(m) -> str:
    return "{" + ",".join(f"{p}:{k}={o}" for (p, k), o in sorted(m.items())) + "}"


def drill(root, base, name, mutate, expected, pillars=KLM, contract=KLM):
    d = root / name
    g(root, "clone", "-q", str(base), str(d))
    init_cfg = [("user.email", "drill@example.invalid"), ("user.name", "drill"), ("commit.gpgsign", "false")]
    for k, v in init_cfg:
        g(d, "config", k, v)
    if mutate:
        mutate(d)
    got = outcome_map(skh.judge(d, pillars, contract))
    record(f"V-SKH-{name}", got == expected, f"expected={fmt(expected)} observed={fmt(got)}")
    return got


# ------------------------------------------------------------------ mutations (fragments, never markers)

ROUTE_DEF = "de" + "f route(task):\n    return task\n"
SOURCE_IMPORT = "fr" + "om pricing" + "_source import current\n"
APPEND_LINE = "with open(d / \"" + "signals" + ".jsonl\", \"a\") as fh:\n    fh.write(row)\n"
NAMED_PATH = "modules/context" + "_compiler.py"


def add_file(rel, text):
    def m(d):
        put(d, rel, text)
        commit(d, f"add {rel}", add=[rel])
    return m


def remove(*rels):
    def m(d):
        commit(d, "remove " + " ".join(rels), rm=list(rels))
    return m


def edit_handoff(p, fn):
    def m(d):
        rel = f"{skh.HANDOFF_DIR}{p}.md"
        path = Path(d) / rel
        path.write_bytes(fn(path.read_text(encoding="utf-8")).encode("utf-8"))
        commit(d, f"edit {rel}", add=[rel])
    return m


def measured_at_off_history(p):
    """Point handoffs/<p>.md's measured_at_commit at a real commit that is not in HEAD's history."""
    def m(d):
        orphan = g(d, "commit-tree", "HEAD^{tree}", "-m", "orphan, never on HEAD's history").strip()
        edit_handoff(p, lambda t: skh.MEASURED_AT.sub(f"- measured_at_commit: {orphan}", t, count=1))(d)
    return m


def freeze_after_handoffs(d):
    """Move the freeze pointer to the commit that holds the handoffs, so no handoff commit lands after the freeze.
    One clean tool is added in the same commit so the K / M apertures stay non-empty."""
    put(d, skh.FROZEN_AT_REL, g(d, "rev-parse", "HEAD").strip() + "\n")
    put(d, "tools/clean_tool_two.py", "VALUE = 2\n")
    commit(d, "freeze pointer moved past the handoffs", add=[skh.FROZEN_AT_REL, "tools/clean_tool_two.py"])


def worktree_edit_handoff(p):
    def m(d):
        path = Path(d) / f"{skh.HANDOFF_DIR}{p}.md"
        path.write_bytes(path.read_bytes() + b"\nan uncommitted working-copy line\n")
    return m


def coverage_without_plane(d):
    rel = skh.EVIDENCE_REL + "D-coverage.md"
    path = Path(d) / rel
    t = path.read_text(encoding="utf-8")
    out = "".join(ln for ln in t.splitlines(True) if not ln.startswith("## Plane "))
    if out == t:
        raise RuntimeError("precondition: D-coverage.md holds no `## Plane` heading")
    path.write_bytes(out.encode("utf-8"))
    commit(d, "D-coverage.md without plane tables", add=[rel])


def evidence_header_unnamed(name):
    """Drop the `-- D-XXX measurement` denominator from line 1 of evidence/<name>."""
    def m(d):
        rel = skh.EVIDENCE_REL + name
        path = Path(d) / rel
        head, rest = path.read_text(encoding="utf-8").split("\n", 1)
        new = skh.DENOM_HEAD.sub("-- (no denominator)", head)
        if new == head:
            raise RuntimeError(f"precondition: line 1 of {name} names no denominator")
        path.write_bytes((new + "\n" + rest).encode("utf-8"))
        commit(d, f"{name} line 1 without a denominator", add=[rel])
    return m


def savings_without_denominator(d):
    import json  # noqa: PLC0415
    path = Path(d) / skh.LEDGER_REL
    led = json.loads(path.read_text(encoding="utf-8"))
    hit = [s for st in led["state"].values() for s in (st or {}).get("savings") or [] if "denominator" in s]
    if not hit:
        raise RuntimeError("precondition: no savings entry carries a denominator")
    hit[0].pop("denominator")
    path.write_bytes(json.dumps(led, indent=1).encode("utf-8"))
    commit(d, "one savings entry without its denominator", add=[skh.LEDGER_REL])


def deltas_without_lines(d):
    """Keep line 1 of each delta source (its denominator) and drop every line the delta pattern could hit."""
    rels = [skh.EVIDENCE_REL + n for n in skh.M_DELTA_SOURCES]
    for rel in rels:
        path = Path(d) / rel
        path.write_bytes((path.read_text(encoding="utf-8").split("\n", 1)[0] + "\n").encode("utf-8"))
    commit(d, "delta sources reduced to their headers", add=rels)


# A reachability scanner that answers well-formed rows and writes a file into the export it runs in.
WRITING_SCANNER = ("import json, pathlib\n"
                   "pathlib.Path('scanner_wrote_this.txt').write_text('x')\n"
                   "print(json.dumps({'rows': [{'unit': 'm', 'status': 'REACHABLE', 'klass': None}], "
                   "'offenders': [], 'passed': True}))\n")


def worktree_only(rel, text):
    def m(d):
        put(d, rel, text)       # never committed: the sweep reads committed blobs only
    return m


# ------------------------------------------------------------------ git failure vs absence (review WR-01)

GIT_TIMEOUT_REASON = "git cat-file failed: Command '['git']' timed out after 30 seconds"


def _probe_ctx(d, h):
    ctx, bad = skh.load_ctx(d, h)
    return "PASS" if ctx is not None else bad[0]


def _probe_part(p, part):
    def probe(d, h):
        return skh.measure(d, p, h)["parts"].get(part, ["MISSING"])[0]
    return probe


# (site, committed path whose blob read is broken, probe(repo, head) -> outcome, outcome when the path is ABSENT)
GIT_SITES = (
    ("CTX", skh.FROZEN_AT_REL, _probe_ctx, "UNMEASURED"),
    ("CONTRACT", skh.HANDOFF_DIR + "K.md", lambda d, h: skh.contract(d, "K", h)[0], "FAIL"),
    ("K-CONTROL", skh.K_CONTROLS[0], _probe_part("K", "control"), "UNMEASURED"),
    ("M-CONTROL", skh.M_CONTROL, _probe_part("M", "control"), "UNMEASURED"),
    ("I-SKILLS", skh.EVIDENCE_REL + "D-coverage.md", _probe_part("I", "skills"), "UNMEASURED"),
    ("M-DENOMINATOR", skh.EVIDENCE_REL + "B-listing-floor.md", _probe_part("M", "denominator"), "UNMEASURED"),
)


def _with_blob_timeout(target, fn):
    """Run fn() while every `git cat-file blob <sha>:<target>` through smd.git_run fails as a timeout does."""
    real = smd.git_run

    def git_run(repo, *args, **kw):
        if args[:2] == ("cat-file", "blob") and len(args) > 2 and str(args[2]).endswith(":" + target):
            return None, GIT_TIMEOUT_REASON
        return real(repo, *args, **kw)

    smd.git_run = git_run
    try:
        return fn()
    finally:
        smd.git_run = real


def git_failure_drills(root, base):
    """Per blob-reading site, both poles on one line: the blob read timing out is INCONCLUSIVE, and the same path
    absent from the commit is the measured-absence outcome (FAIL or UNMEASURED), never INCONCLUSIVE."""
    head = g(base, "rev-parse", "HEAD").strip()
    for site, target, probe, absent in GIT_SITES:
        timed = _with_blob_timeout(target, lambda: probe(base, head))
        d = root / f"absent-{site}"
        g(root, "clone", "-q", str(base), str(d))
        for k, v in (("user.email", "drill@example.invalid"), ("user.name", "drill"), ("commit.gpgsign", "false")):
            g(d, "config", k, v)
        commit(d, f"remove {target}", rm=[target])
        gone = probe(d, g(d, "rev-parse", "HEAD").strip())
        record(f"V-SKH-GIT-TIMEOUT-{site}", timed == "INCONCLUSIVE" and gone == absent,
               f"{target}: timeout -> {timed} (want INCONCLUSIVE); absent -> {gone} (want {absent})")
    # The classifier on reasons git itself produced (positive and negative controls).
    untracked = "tools/untracked_probe.py"
    put(base, untracked, "VALUE = 1\n")
    try:
        reasons = {
            "absent": (smd.git_run(base, "cat-file", "blob", f"{head}:tools/nope.py")[1], False),
            "on-disk-not-committed": (smd.git_run(base, "cat-file", "blob", f"HEAD:{untracked}")[1], False),
            "invalid-object": (smd.git_run(base, "cat-file", "blob", "deadbeef:tools/clean_tool.py")[1], True),
            "timeout": (GIT_TIMEOUT_REASON, True),
            "git-missing": ("git not found: [Errno 2] No such file or directory: 'git'", True),
            "none": (None, False),
        }
    finally:
        (Path(base) / untracked).unlink()
    bad = {k: why for k, (why, want) in reasons.items() if skh.git_failed(why) != want}
    record("V-SKH-GIT-FAILED-CLASSIFIER", not bad and all(w for k, (w, _) in reasons.items() if k != "none"),
           f"{len(reasons)} reasons, misclassified {bad}")


def rows_reason_reads_host(root):
    """K's row-count reason states the card ledger's presence as read from the host (review IN-03), under a HOME
    without and then with `~/.claude/state/doctrine-cards/ledger.jsonl`; never the host name."""
    saved = {k: os.environ.get(k) for k in ("HOME", "DOCTRINE_CARDS_STATE_DIR")}
    home = root / "rows-home"
    home.mkdir()
    got = {}
    try:
        os.environ["HOME"] = str(home)
        os.environ.pop("DOCTRINE_CARDS_STATE_DIR", None)
        got["absent"] = skh._report_rows()
        led = home / ".claude" / "state" / "doctrine-cards" / "ledger.jsonl"
        led.parent.mkdir(parents=True)
        led.write_text("", encoding="utf-8")
        got["present"] = skh._report_rows()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    ok = (got["absent"].get("state") == "UNMEASURED" and "card ledger present: False" in got["absent"]["reason"]
          and got["present"].get("state") == "UNMEASURED" and "card ledger present: True" in got["present"]["reason"])
    record("V-SKH-K-ROWS-CARD-LEDGER", ok, f"absent -> {got['absent'].get('reason')!r}; present -> "
                                           f"{got['present'].get('reason')!r}")


def main() -> int:
    t0 = time.monotonic()
    root = Path(tempfile.mkdtemp(prefix="skh-drills-"))
    try:
        base = build_base(root)
        adj_rel, adj_line, _ = skh.M_ADJUDICATED[0]
        drills = [
            ("BASELINE", None, {}),
            ("ROUTER-BASENAME", add_file("tools/x_router.py", "VALUE = 1\n"), {("K", "router"): "FAIL"}),
            ("ROUTER-DEF", add_file("tools/x_def.py", ROUTE_DEF), {("K", "router"): "FAIL"}),
            ("PRICING-IMPORT", add_file("tools/x_mod.py", SOURCE_IMPORT), {("M", "cost"): "FAIL"}),
            ("CO12-APPEND", add_file("tools/x_sig.py", APPEND_LINE), {("L", "writer"): "FAIL"}),
            ("NAMED-MODULE", add_file(NAMED_PATH, "VALUE = 1\n"), {("L", "absence"): "FAIL"}),
            ("ROUTER-CONTROLS-REMOVED", remove(*skh.K_CONTROLS), {("K", "control"): "UNMEASURED"}),
            ("COST-CONTROL-REMOVED", remove(skh.M_CONTROL), {("M", "control"): "UNMEASURED"}),
            ("WRITER-CONTROL-REMOVED", remove(skh.L_WRITER_CONTROLS[2]), {("L", "control"): "UNMEASURED"}),
            ("CLAIM-CONTROL-REMOVED", remove(skh.L_CLAIM_CONTROL), {("L", "control"): "UNMEASURED"}),
            ("ZERO-ADDED", remove(CLEAN_TOOL), {("K", "aperture"): "UNMEASURED", ("M", "aperture"): "UNMEASURED"}),
            ("CONTRACT-NON-OWNER", edit_handoff("K", lambda t: re.sub(r"^\[K\] -> \S+", "[K] -> tools/clean_tool.py",
                                                                        t, count=1)),
             {("K", "contract"): "FAIL"}),
            ("CONTRACT-NO-TAG", edit_handoff("M", lambda t: t.replace("[M]", "(M)")), {("M", "contract"): "FAIL"}),
            ("ADJUDICATED-ADMITTED", add_file(adj_rel, adj_line + "\n    return 1\n"), {}),
            ("ADJUDICATED-EDITED", add_file(adj_rel, adj_line.replace("):", ", extra):") + "\n    return 1\n"),
             {("M", "cost"): "FAIL"}),
            ("ADJUDICATED-STALE", add_file(adj_rel, "VALUE = 1\n"), {("M", "cost"): "UNMEASURED"}),
            ("WORKTREE-ONLY", worktree_only("tools/x_router.py", ROUTE_DEF), {}),
            ("CONTRACT-MEASURED-OFF-HISTORY", measured_at_off_history("K"), {("K", "contract"): "FAIL"}),
            ("CONTRACT-NOT-LANDED-AFTER-FREEZE", freeze_after_handoffs,
             {("K", "contract"): "FAIL", ("L", "contract"): "FAIL", ("M", "contract"): "FAIL"}),
            ("CONTRACT-WORKTREE-EDIT", worktree_edit_handoff("M"), {("M", "contract"): "FAIL"}),
            ("CONTRACT-L-NON-OWNER", edit_handoff("L", lambda t: re.sub(r"^\[L\] -> \S+", "[L] -> tools/clean_tool.py",
                                                                          t, count=1)),
             {("L", "contract"): "FAIL"}),
            ("M-DENOMINATOR-UNNAMED", evidence_header_unnamed("E-contribution.md"), {("M", "denominator"): "FAIL"}),
            ("M-SAVINGS-NO-DENOMINATOR", savings_without_denominator, {("M", "denominator"): "FAIL"}),
            ("M-DELTA-DEAD-CONTROL", deltas_without_lines, {("M", "denominator"): "UNMEASURED"}),
            # I has no sweep; its red branch: an export with neither scanner reads UNMEASURED, never PASS.
            ("I-NO-SCANNERS", None, I_BASE, ("I",), ("I",)),
            ("I-SKILLS-NO-PLANE", coverage_without_plane, {**I_BASE, ("I", "skills"): "UNMEASURED"},
             ("I",), ("I",)),
            ("I-NOWRITE-SCANNER-WRITES", add_file("modules/liveness/reachability.py", WRITING_SCANNER),
             {("I", "retirement"): "UNMEASURED", ("I", "nowrite"): "FAIL"}, ("I",), ("I",)),
            ("I-CONTRACT-NON-OWNER", edit_handoff("I", lambda t: re.sub(r"^\[I\] -> \S+", "[I] -> tools/clean_tool.py",
                                                                          t, count=1)),
             {**I_BASE, ("I", "contract"): "FAIL"}, ("I",), ("I",)),
        ]
        flipped = set()
        for name, mut, exp, *scope in drills:
            pillars, contract_p = scope if scope else (KLM, KLM)
            got = drill(root, base, name, mut, exp, pillars, contract_p)
            if got == exp:
                flipped |= set(exp)
        git_failure_drills(root, base)
        rows_reason_reads_host(root)
        need = {("K", "router"), ("K", "control"), ("K", "aperture"), ("M", "cost"), ("M", "control"),
                ("M", "aperture"), ("L", "writer"), ("L", "absence"), ("L", "control"), ("K", "contract"),
                ("M", "contract"), ("L", "contract"), ("I", "reachability"), ("I", "retirement"), ("I", "skills"),
                ("I", "nowrite"), ("I", "contract"), ("M", "denominator")}
        record("V-SKH-EVERY-PART-RED", need <= flipped, f"driven={len(flipped & need)}/{len(need)} "
                                                        f"missing={sorted(need - flipped)}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # git missing: the real CLI on this checkout, PATH emptied.
    env = dict(os.environ, PATH="/nonexistent")
    p = subprocess.run([sys.executable, str(REPO / TOOL), "--check"], capture_output=True, text=True, env=env,
                       timeout=600)
    out = p.stdout + p.stderr
    last = (p.stdout.strip().splitlines() or [""])[-1]
    record("V-SKH-GIT-MISSING", p.returncode == 1 and "INCONCLUSIVE" in out and "Traceback" not in out,
           f"rc={p.returncode} last={last!r}")
    # live: this checkout
    p = subprocess.run([sys.executable, str(REPO / TOOL), "--check"], capture_output=True, text=True, timeout=600)
    lines = p.stdout.strip().splitlines()
    record("V-SKH-LIVE", p.returncode == 0 and lines and lines[-1] == "SKILL_HANDOFFS PASS pillars=4",
           f"rc={p.returncode} " + " | ".join(lines))
    # DH-03: neither file enrols as a CO-12 adapter; control: the real adapter does.
    enrol = re.compile(r"^(KIND|CAPABILITY)\s*=", re.M)
    mine = {rel: len(enrol.findall((REPO / rel).read_text(encoding="utf-8"))) for rel in (TOOL, SELF)}
    ctl = len(enrol.findall((REPO / "tools/skill_opportunity_signals.py").read_text(encoding="utf-8")))
    record("V-SKH-NO-SELF-ENROL", not any(mine.values()) and ctl == 2, f"mine={mine} control={ctl}")
    # The sweeps over this tool and this test: zero hits on the working copies (the committed ones are in V-SKH-LIVE).
    hits = {}
    for rel in (TOOL, SELF):
        t = (REPO / rel).read_text(encoding="utf-8")
        hits[rel] = (len(skh.router_hits(rel, t)), len(skh.m_hits(t)),
                     sum(skh.is_writer_line(x) for x in t.splitlines()),
                     len(re.findall(skh.L_NAME_ERE, t)))
    record("V-SKH-SELF-CLEAN", all(v == (0, 0, 0, 0) for v in hits.values()),
           f"(router, cost, writer, name) {hits}")
    n, ok = len(results), sum(results)
    print(f"# wall={time.monotonic() - t0:.1f}s")
    print(f"SKH_PASS={ok}/{n}")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
