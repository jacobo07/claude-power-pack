#!/usr/bin/env python3
"""V-ICR2-* gates: the R2 evidence printer tools/ic_r2_evidence.py (incremental-cognition phase 6, plan 06-01).

    python3 tools/test_ic_r2_evidence.py           run every gate
    python3 tools/test_ic_r2_evidence.py --drill   mutation drill (each mutant must be killed)

A SKIP or an INCONCLUSIVE is printed and counted apart; it is never a PASS and is outside the n/m denominator.
Every expectation about the owner ledger is read here independently, with `git show`, never by calling the
helper's own readers.
"""
from __future__ import annotations

import atexit
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import ic_r2_evidence as ev  # noqa: E402
import test_incremental_cognition_program as icp  # noqa: E402

ce = icp.ce
SCRIPT = HERE / "ic_r2_evidence.py"
CE_LEDGER = "vault/programs/cognitive-economy/ledger.json"
SC_LEDGER = "vault/programs/skill-capability/ledger.json"
FREEZE = "fa9ae2ed"          # CE P0 freeze: holds the CE ledger, every pillar open
PRE_LEDGER = "1cabd117"      # its parent: the CE ledger does not exist yet
TMP_ROOT = Path(tempfile.mkdtemp(prefix="icr2-test-"))
_COUNTER = [0]
RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)
QUIET = [False]


def _cleanup() -> None:
    for dp, dns, fns in os.walk(TMP_ROOT):
        for n in dns + fns:
            with contextlib.suppress(OSError):
                os.chmod(os.path.join(dp, n), 0o700)
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


atexit.register(_cleanup)


def scratch(prefix: str = "t") -> Path:
    _COUNTER[0] += 1
    d = TMP_ROOT / f"{prefix}{_COUNTER[0]}"
    d.mkdir(parents=True)
    return d


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


# --------------------------------------------------------------------------- independent git readers
def git(*args, cwd=REPO) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def have_commit(spec: str) -> bool:
    return git("rev-parse", "--verify", "--quiet", spec + "^{commit}").returncode == 0


def head() -> str:
    return git("rev-parse", "HEAD").stdout.strip()


def ledger_at(spec: str, ref: str) -> dict | None:
    r = git("show", f"{spec}:{ref}")
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.lstrip("﻿"))


def program_ledger() -> dict:
    return json.loads((REPO / "vault/programs/incremental-cognition/ledger.json").read_text(encoding="utf-8"))


def predicted_by_owner(spec: str, ref: str, pillar: str):
    led = ledger_at(spec, ref)
    for p in (led or {}).get("frozen", {}).get("pillars", []):
        if p.get("id") == pillar:
            return p.get("predicted")
    return None


def run_main(argv):
    """In-process ev.main(argv) with stdout captured; returns (rc, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        try:
            rc = ev.main(list(argv))
        except SystemExit as exc:      # argparse refusing its own arguments is a refusal, never a crash
            rc = exc.code if isinstance(exc.code, int) else 2
    return rc, buf.getvalue()


def run_cli(args):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(REPO), capture_output=True, text=True,
                       timeout=300)
    return p.returncode, p.stdout, p.stderr


# --------------------------------------------------------------------------- gates: real repository
def g_tracer_real_head():
    sha8 = head()[:8]
    rc, out, err = run_cli(["--pillar", "J", "--commit", "HEAD"])
    want = [f"OPEN {CE_LEDGER}#{p} at {sha8}: no terminal" for p in ("D", "E", "I")]
    miss = [w for w in want if not any(x.startswith(w) for x in out.splitlines())]
    good = (rc == 1 and not miss and "ICR2_READY=NO" in out and '"kind": "owner_ledger"' not in out)
    return good, f"rc={rc} missing={miss} ready_no={'ICR2_READY=NO' in out} stderr={err.strip()[:80]!r}"


def g_real_freeze_pole():
    if not have_commit(FREEZE):
        return "SKIP", f"{FREEZE} is not in this clone"
    led = program_ledger()
    bad = []
    for pid in ("J", "M"):
        rc, out = run_main(["--pillar", pid, "--commit", FREEZE])
        pairs = led["frozen"]["consumes"][pid]
        lines = [x for x in out.splitlines() if x.startswith("OPEN ")]
        if rc != 1 or len(lines) != len(pairs) or '"kind": "owner_ledger"' in out:
            bad.append(f"{pid}: rc={rc} open_lines={len(lines)}/{len(pairs)}")
            continue
        for pair, line in zip(pairs, lines):
            pred = predicted_by_owner(FREEZE, pair["ledger"], pair["pillar"])
            if not (line.startswith(f"OPEN {pair['ledger']}#{pair['pillar']} at {FREEZE}:")
                    and line.endswith(f"(owner predicted {pred})")) or not pred:
                bad.append(f"{pid}: {line!r} vs predicted {pred!r}")
    return not bad, f"bad={bad}"


def g_real_unreadable_pole():
    if not have_commit(PRE_LEDGER):
        return "SKIP", f"{PRE_LEDGER} is not in this clone"
    rc, out = run_main(["--pillar", "J", "--commit", PRE_LEDGER])
    line = f"UNREADABLE {CE_LEDGER} at {PRE_LEDGER}"
    good = rc == 1 and any(x.startswith(line) for x in out.splitlines()) and '"kind": "owner_ledger"' not in out
    return good, f"rc={rc} unreadable_line={any(x.startswith(line) for x in out.splitlines())}"


def g_consumes_discovered():
    led = program_ledger()
    bad = []
    for pid, wanted in led["frozen"]["consumes"].items():
        want = [(w["ledger"], w["pillar"]) for w in wanted]
        if list(ev.consumed(led, pid)) != want:
            bad.append(pid)
    rc, out = run_main(["--pillar", "A"])
    good = not bad and rc == 2 and "ICR2_COULD_NOT_RUN" in out
    return good, f"mismatch={bad} pillar_A rc={rc}"


# --------------------------------------------------------------------------- scratch git
@contextlib.contextmanager
def bound_repo(path):
    """Rebind the CE verifier's REPO (read by ce._git at call time) to a scratch repository; restored in finally.
    This seam exists ONLY in the test: the helper never rebinds a REPO global."""
    saved = ce.REPO
    ce.REPO = Path(path)
    try:
        yield
    finally:
        ce.REPO = saved


PREDICTED = {"D": "MERGED_INTO_EXISTING_OWNER", "E": "DEFERRED_STRONGER_OWNER", "I": "MERGED_INTO_EXISTING_OWNER"}
CLOSED = {"D": "MERGED_INTO_EXISTING_OWNER", "E": "MERGED_INTO_EXISTING_OWNER",
          "I": "FALSIFIED_OR_REJECTED_BY_EVIDENCE"}
PAIRS = [(CE_LEDGER, p) for p in ("D", "E", "I")]
_SCRATCH: dict = {}


def ce_shaped_ledger(terminals: dict, note: str = "") -> str:
    return json.dumps({
        "program": "cognitive-economy", "note": note,
        "frozen": {"pillars": [{"id": p, "predicted": PREDICTED[p]} for p in ("D", "E", "I")]},
        "state": {p: {"terminal": terminals.get(p), "evidence": []} for p in ("D", "E", "I")}}, indent=1)


def scratch_repo() -> dict:
    """c1: D, E, I open; c3: D, E closed; c2 (HEAD of main): all closed; side: all closed, NOT an ancestor of HEAD."""
    if _SCRATCH:
        return _SCRATCH
    d = scratch("gitrepo")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")

    def g(*args):
        return subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True, env=env, check=True)

    def commit(terminals, msg):
        p = d / CE_LEDGER
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(ce_shaped_ledger(terminals, msg), encoding="utf-8")
        g("add", "--", CE_LEDGER)
        g("commit", "-q", "-m", msg)
        return g("rev-parse", "HEAD").stdout.strip()

    g("init", "-q", "-b", "main")
    c1 = commit({}, "c1 open")
    side_base = c1
    c3 = commit({"D": CLOSED["D"], "E": CLOSED["E"]}, "c3 partial")
    c2 = commit(CLOSED, "c2 closed")
    g("checkout", "-q", "-b", "side", side_base)
    side = commit(CLOSED, "side closed")
    g("checkout", "-q", "main")
    _SCRATCH.update(dir=d, c1=c1, c2=c2, c3=c3, side=side)
    return _SCRATCH


def parse_rows(out: str) -> list:
    lines = out.splitlines()
    if "ROWS" not in lines:
        return []
    start = lines.index("ROWS") + 1
    end = lines.index("]", start) + 1       # the JSON array ends at its own closing bracket; NEEDS lines follow it
    return json.loads("\n".join(lines[start:end]))


def scratch_main(spec: str, pid: str = "J"):
    s = scratch_repo()
    with bound_repo(s["dir"]):
        return run_main(["--pillar", pid, "--commit", spec])


def g_scratch_closed():
    s = scratch_repo()
    rc, out = scratch_main(s["c2"])
    rows = parse_rows(out)
    want = [{"kind": "owner_ledger", "ref": CE_LEDGER, "commit": s["c2"], "pillar": p, "terminal": CLOSED[p]}
            for p in ("D", "E", "I")]
    ready = [x for x in out.splitlines() if x.startswith("READY ")]
    last = out.strip().splitlines()[-1] if out.strip() else ""
    pos = (rc == 0 and rows == want and len(ready) == 3 and last == f"ICR2_READY=J commit={s['c2']}"
           and all(len(r["commit"]) == 40 for r in rows))
    rc1, out1 = scratch_main(s["c1"])
    opens = [x for x in out1.splitlines() if x.startswith("OPEN ")]
    neg = (rc1 == 1 and len(opens) == 3 and not parse_rows(out1) and '"kind"' not in out1
           and all(f"owner predicted {PREDICTED[p]}" in o for p, o in zip(("D", "E", "I"), opens)))
    return pos and neg, f"closed rc={rc} rows_ok={rows == want} ready={len(ready)} | open rc={rc1} open_lines={len(opens)}"


def g_partial_no_paste():
    s = scratch_repo()
    rc, out = scratch_main(s["c3"])
    lines = out.splitlines()
    ready = [x for x in lines if x.startswith("READY ")]
    opens = [x for x in lines if x.startswith("OPEN ")]
    good = (rc == 1 and len(ready) == 2 and len(opens) == 1 and opens[0].startswith(f"OPEN {CE_LEDGER}#I ")
            and '"kind"' not in out and "ROWS" not in lines and "open=['I']" in out)
    return good, f"rc={rc} ready={len(ready)} open={len(opens)} rows_printed={'ROWS' in lines}"


def g_unreachable():
    s = scratch_repo()
    rc, out = scratch_main(s["side"])
    lines = out.splitlines()
    unreach = [x for x in lines if x.startswith("UNREACHABLE ")]
    good = (rc == 1 and len(unreach) == 1 and unreach[0].startswith(f"UNREACHABLE {s['side'][:8]}")
            and '"kind"' not in out and not any(x.startswith("READY ") for x in lines))
    rc2, out2 = scratch_main(s["c2"])        # control: the same ledger content, on the HEAD line, is accepted
    return good and rc2 == 0, f"side rc={rc} unreachable_lines={len(unreach)} rows={'ROWS' in lines} | control rc={rc2}"


def synth_ledger(rows, pid="J"):
    return {"frozen": {"consumes": {pid: [{"ledger": r, "pillar": p} for r, p in PAIRS]}},
            "state": {pid: {"terminal": "MERGED_INTO_EXISTING_OWNER", "evidence": rows}}}


def g_roundtrip_r2():
    s = scratch_repo()
    rc, out = scratch_main(s["c2"])
    rows = parse_rows(out)
    with bound_repo(s["dir"]):
        owners = icp.OwnerLedgers()
        clean_ev = ev.roundtrip_problems("J", PAIRS, rows, owners)
        clean_icp = icp.check_consumed(synth_ledger(rows), owners)
        changed = [dict(rows[0], terminal="AUTHORIZATION_BOUND")] + rows[1:]
        removed = rows[:-1]
        old = [dict(rows[0], commit=s["c1"])] + rows[1:]
        bad = {}
        for name, alt in (("terminal-changed", changed), ("row-removed", removed), ("c1-sha", old)):
            mine = ev.roundtrip_problems("J", PAIRS, alt, owners)
            theirs = icp.check_consumed(synth_ledger(alt), owners)
            bad[name] = bool(mine) and all(x.startswith("R2 J:") for x in mine) and bool(theirs)
    good = rc == 0 and len(rows) == 3 and clean_ev == [] and clean_icp == [] and all(bad.values())
    return good, f"rc={rc} clean_ev={clean_ev} clean_icp={clean_icp} altered_refused={bad}"


def g_bad_commit():
    bad = {}
    for spec in ("zzzz", "0" * 40, "-x", ""):
        rc, out = run_main(["--pillar", "J", f"--commit={spec}"])
        bad[spec or "<empty>"] = rc == 2 and "ICR2_COULD_NOT_RUN" in out and "ICR2_READY" not in out
    s = scratch_repo()
    rc, _ = scratch_main(s["c2"])           # control: a real commit in the same plumbing is not refused
    return all(bad.values()) and rc == 0, f"refused={bad} control_rc={rc}"


def g_needs_derived():
    s = scratch_repo()
    led = program_ledger()
    rc, out = scratch_main(s["c2"])
    lines = out.splitlines()
    bad = []
    for pid in ("J", "M"):
        entry = next(p for p in led["frozen"]["pillars"] if p["id"] == pid)
        pred = entry["predicted"]
        kinds = ce.REQUIRED_KINDS[pred][0]
        got = ev.needs_lines(led, pid)
        for kind in kinds:
            hit = [x for x in got if x.startswith(f"NEEDS {pid} {pred}: {kind}")]
            if len(hit) != 1:
                bad.append(f"{pid}:{kind} lines={len(hit)}")
                continue
            if kind == "owner" and not all(o in hit[0] for o in entry["owner"]):
                bad.append(f"{pid}: owner line misses an owner")
            if kind == "handoff" and f"vault/programs/incremental-cognition/handoffs/{pid}.md" not in hit[0]:
                bad.append(f"{pid}: handoff line misses its path")
        if len(got) != len(kinds):
            bad.append(f"{pid}: {len(got)} lines for {len(kinds)} kinds")
    j_needs = [i for i, x in enumerate(lines) if x.startswith("NEEDS J ")]
    rows_end = max((i for i, x in enumerate(lines) if x.startswith("]")), default=-1)
    ready_at = next((i for i, x in enumerate(lines) if x.startswith("ICR2_READY=")), -1)
    if not (j_needs and rows_end < min(j_needs) and max(j_needs) < ready_at):
        bad.append("NEEDS lines are not between the rows and ICR2_READY")
    rc1, out1 = scratch_main(s["c1"])
    if "NEEDS" in out1:
        bad.append("NEEDS printed on a not-ready result")
    return rc == 0 and not bad, f"rc={rc} problems={bad}"


def g_seam_restored():
    s = scratch_repo()
    problems = []
    if ce.REPO != icp.REPO:
        problems.append("ce.REPO differs from icp.REPO after the scratch gates")
    with bound_repo(s["dir"]):
        inside = ce.REPO == Path(s["dir"])
    if not inside:
        problems.append("bound_repo did not rebind ce.REPO inside the block")
    try:
        with bound_repo(s["dir"]):
            raise RuntimeError("probe")
    except RuntimeError:
        pass
    if ce.REPO != icp.REPO:
        problems.append("ce.REPO not restored after an exception inside the block")
    src = (HERE / "ic_r2_evidence.py").read_text(encoding="utf-8")
    if "setattr" in src or ".REPO =" in src or "REPO=" in src.replace(" ", ""):
        problems.append("the helper rebinds a REPO global")
    return not problems, f"problems={problems}"


def snapshot() -> dict:
    return {
        "ledgers": {r: ce.lf_sha256(REPO / r) for r in (ce.LEDGER_REL, CE_LEDGER, SC_LEDGER)},
        "status": git("status", "--porcelain").stdout,
        "head": git("rev-parse", "HEAD").stdout,
        "refs": git("for-each-ref").stdout,
    }


def g_read_only():
    led = program_ledger()
    before = snapshot()
    ran = 0
    for spec in ("HEAD", FREEZE):
        if not have_commit(spec):
            continue
        for pid in led["frozen"]["consumes"]:
            run_main(["--pillar", pid, "--commit", spec])
            ran += 1
    after = snapshot()
    diff = [k for k in before if before[k] != after[k]]
    return ran >= len(led["frozen"]["consumes"]) and not diff, f"runs={ran} changed={diff}"


# --------------------------------------------------------------------------- plan 06-02: bundle lines and the J / M evidence file
BUNDLE_REL = "vault/programs/incremental-cognition/owner-bundle.md"
JM_REL = "vault/programs/incremental-cognition/evidence/JM-blocked.md"
SUMMARY_HEAD = "## Summary (every Owner item, phases 1-5)"
REQUIRED_JM = ("J",)
PER_PILLAR_CHECK = "python3 tools/test_incremental_cognition_program.py --pillar {p}"


def strip_summary(text: str) -> str:
    """The bundle with its summary section removed (header to the next `## `): the table repeats the command lines."""
    import re
    m = re.search(r"^" + re.escape(SUMMARY_HEAD) + r"[ \t]*$", text, re.M)
    if not m:
        return text
    end = text.find("\n## ", m.end())
    end = len(text) if end < 0 else end + 1
    return text[:m.start()] + text[end:]


def bundle_r2_problems(text: str, consumes: dict, required) -> tuple:
    """(problems, pillars found): every indented line running tools/ic_r2_evidence.py, parsed with the printer's own parser."""
    import re
    import shlex
    body = strip_summary(text).split("\n")
    problems, found = [], set()
    item = None
    items: dict = {}          # item tag -> indented lines under it
    for ln in body:
        m = re.match(r"^- \*\*\[([A-Z])\]\*\*", ln)
        if m:
            item = m.group(1)
            items.setdefault(item, [])
        elif re.match(r"^## ", ln):
            item = None
        elif item and re.match(r"^ {4,}\S", ln):
            items[item].append(ln.strip())
    for tag, lines in items.items():
        for line in lines:
            if "tools/ic_r2_evidence.py" not in line:
                continue
            if "<" in line or ">" in line:
                problems.append(f"placeholder in {line[:70]}")
                continue
            try:
                toks = shlex.split(line)
            except ValueError:
                problems.append(f"unsplittable: {line[:70]}")
                continue
            at = next((i for i, t in enumerate(toks) if t.endswith("tools/ic_r2_evidence.py")), None)
            if at is None:
                problems.append(f"not a run of the printer: {line[:70]}")
                continue
            err = io.StringIO()
            try:
                with contextlib.redirect_stderr(err):
                    args = ev.build_parser().parse_args(toks[at + 1:])
            except SystemExit:
                problems.append(f"unparsable ({(err.getvalue().strip().splitlines() or ['?'])[-1]}): {line[:70]}")
                continue
            if args.pillar not in consumes:
                problems.append(f"pillar {args.pillar} is not in frozen.consumes: {line[:70]}")
                continue
            if tag != args.pillar:
                problems.append(f"line for {args.pillar} is filed under [{tag}]: {line[:70]}")
                continue
            if PER_PILLAR_CHECK.format(p=args.pillar) not in lines:
                problems.append(f"item [{tag}] has no per-pillar check line")
                continue
            found.add(args.pillar)
    if found != set(required):
        problems.append(f"pillars with a printer line {sorted(found)} != required {sorted(required)}")
    return problems, found


def g_bundle_argv_parses():
    led = program_ledger()
    consumes = led["frozen"]["consumes"]
    text = (REPO / BUNDLE_REL).read_text(encoding="utf-8")
    problems, found = bundle_r2_problems(text, consumes, REQUIRED_JM)
    good = ("- **[J]** x\n\n    python3 tools/ic_r2_evidence.py --pillar J --commit HEAD\n"
            "    python3 tools/test_incremental_cognition_program.py --pillar J\n")
    controls = {
        "good J item accepted": bundle_r2_problems(good, consumes, ("J",))[0] == [],
        "unknown flag refused": bool(bundle_r2_problems(good.replace("--commit HEAD", "--no-such HEAD"), consumes, ("J",))[0]),
        "placeholder refused": bool(bundle_r2_problems(good.replace("HEAD", "<commit>"), consumes, ("J",))[0]),
        "pillar outside frozen.consumes refused": any("not in frozen.consumes" in x for x in bundle_r2_problems(
            good.replace("--pillar J --commit", "--pillar A --commit"), consumes, ("J",))[0]),
        "J line under [M] refused": any("filed under [M]" in x for x in
                                        bundle_r2_problems(good.replace("[J]", "[M]"), consumes, ("J",))[0]),
        "missing per-pillar check refused": any("no per-pillar check" in x for x in bundle_r2_problems(
            good.replace("test_incremental_cognition_program.py --pillar J", "true"), consumes, ("J",))[0]),
    }
    if not all(controls.values()):
        return False, f"controls failed: {[k for k, v in controls.items() if not v]}"
    return not problems, (f"printer lines for {sorted(found)} (required {list(REQUIRED_JM)}), problems={problems[:3]}, "
                          f"{len(controls)} controls report")


def jm_blocked_problems(text: str, led: dict, required) -> list:
    problems = []
    rules = {p["id"]: p for p in led["frozen"]["pillars"]}
    for pid in required:
        for pair in led["frozen"]["consumes"][pid]:
            if f"{pair['ledger']}#{pair['pillar']}" not in text:
                problems.append(f"{pid}: input {pair['ledger']}#{pair['pillar']} not named")
        if rules[pid]["rule"] not in text:
            problems.append(f"{pid}: frozen rule not quoted verbatim")
        if not any(x.startswith(f"ICR2_READY=NO pillar={pid} ") for x in text.splitlines()):
            problems.append(f"{pid}: no measured ICR2_READY=NO line")
    if "## Status: OPEN" not in text.splitlines():
        problems.append("no `## Status: OPEN` line")
    return problems


def g_jm_blocked_covers():
    led = program_ledger()
    path = REPO / JM_REL
    if not path.exists():
        return False, f"{JM_REL} does not exist"
    text = path.read_text(encoding="utf-8")
    consumes = led["frozen"]["consumes"]
    lead = REQUIRED_JM[0]
    first = f"{consumes[lead][0]['ledger']}#{consumes[lead][0]['pillar']}"
    rule = next(p for p in led["frozen"]["pillars"] if p["id"] == lead)["rule"]
    controls = {
        "a blanked input is reported": any("not named" in x for x in
                                           jm_blocked_problems(text.replace(first, "x#y"), led, REQUIRED_JM)),
        "a removed status line is reported": any("Status: OPEN" in x for x in
                                                 jm_blocked_problems(text.replace("## Status: OPEN", "## Status"), led, REQUIRED_JM)),
        "an unquoted rule is reported": any("frozen rule" in x for x in
                                            jm_blocked_problems(text.replace(rule, "x"), led, REQUIRED_JM)),
        "a missing measured line is reported": any("ICR2_READY=NO" in x for x in
                                                   jm_blocked_problems(text.replace("ICR2_READY=NO", "ICR2_READY_NO"), led, REQUIRED_JM)),
    }
    if not all(controls.values()):
        return False, f"controls failed: {[k for k, v in controls.items() if not v]}"
    problems = jm_blocked_problems(text, led, REQUIRED_JM)
    return not problems, f"{JM_REL} covers {list(REQUIRED_JM)}: problems={problems[:3]}, {len(controls)} controls report"


GATES = [
    ("V-ICR2-TRACER-REAL-HEAD", g_tracer_real_head),
    ("V-ICR2-REAL-FREEZE-POLE", g_real_freeze_pole),
    ("V-ICR2-REAL-UNREADABLE-POLE", g_real_unreadable_pole),
    ("V-ICR2-CONSUMES-DISCOVERED", g_consumes_discovered),
    ("V-ICR2-SCRATCH-CLOSED", g_scratch_closed),
    ("V-ICR2-PARTIAL-NO-PASTE", g_partial_no_paste),
    ("V-ICR2-UNREACHABLE", g_unreachable),
    ("V-ICR2-ROUNDTRIP-R2", g_roundtrip_r2),
    ("V-ICR2-BAD-COMMIT", g_bad_commit),
    ("V-ICR2-NEEDS-DERIVED", g_needs_derived),
    ("V-ICR2-SEAM-RESTORED", g_seam_restored),
    ("V-ICR2-READ-ONLY", g_read_only),
    ("V-ICR2-BUNDLE-ARGV-PARSES", g_bundle_argv_parses),
    ("V-ICR2-JM-BLOCKED-COVERS", g_jm_blocked_covers),
]


def summary_line() -> str:
    p = sum(1 for r in RESULTS if r[0] == "PASS")
    f = sum(1 for r in RESULTS if r[0] == "FAIL")
    s = sum(1 for r in RESULTS if r[0] == "SKIP")
    i = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"ICR2_PASS={p}/{p + f}  threshold={p + f}/{p + f}  skipped={s}  inconclusive={i}"


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    return 0 if counted and all(r[0] == "PASS" for r in counted) else 1


# --------------------------------------------------------------------------- mutation drill
GATE_FN = dict(GATES)
DRILL_GATES = [n for n, _ in GATES if n != "V-ICR2-TRACER-REAL-HEAD"]   # the subprocess tracer is excluded (patches cannot reach it)


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


def _patch(module, attr, value):
    saved = getattr(module, attr)
    setattr(module, attr, value)
    return lambda: setattr(module, attr, saved)


def _m_reachable_always():
    return _patch(icp.OwnerLedgers, "reachable", lambda self, sha: True)


def _m_ready_any():
    return _patch(ev, "ready_when", lambda flags: any(flags))


def _m_abbreviated_commit():
    return _patch(ev, "full_commit", lambda sha: sha[:8])


def _m_first_pair_only():
    orig = ev.consumed
    return _patch(ev, "consumed", lambda led, pid: orig(led, pid)[:1])


def _m_roundtrip_blind():
    return _patch(ev, "roundtrip_problems", lambda pid, wanted, rows, owners: [])


def _m_never_unreadable():
    orig = ev.predicted_at

    def mutant(sha, ref, pillar):
        got = orig(sha, ref, pillar)
        return None if got == ev.UNREADABLE else got
    return _patch(ev, "predicted_at", mutant)


MUTANTS = [
    ("M1 OwnerLedgers.reachable always True (a side-branch commit is accepted)", _m_reachable_always,
     ["V-ICR2-UNREACHABLE"]),
    ("M2 ready_when is any (a partly closed owner prints a row)", _m_ready_any, ["V-ICR2-PARTIAL-NO-PASTE"]),
    ("M3 full_commit abbreviates to 8 chars", _m_abbreviated_commit, ["V-ICR2-SCRATCH-CLOSED"]),
    ("M4 consumed returns only the first pair", _m_first_pair_only, ["V-ICR2-CONSUMES-DISCOVERED"]),
    ("M5 roundtrip_problems is always empty", _m_roundtrip_blind, ["V-ICR2-ROUNDTRIP-R2"]),
    ("M6 predicted_at never answers UNREADABLE", _m_never_unreadable, ["V-ICR2-REAL-UNREADABLE-POLE"]),
]


def run_drill() -> int:
    """Control first (all in-process gates green), each mutant applied and restored, then an unmutated rerun."""
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
