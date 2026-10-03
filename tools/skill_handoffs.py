#!/usr/bin/env python3
"""skill_handoffs.py -- measured handoffs for skill-capability pillars I, K, L, M (phase 8, D-01).

A MERGED or DEFERRED terminal is honest only if the owner receives something it can act on. This tool
measures, for each of the four pillars, the evidence its frozen owner needs, and renders it into
`vault/programs/skill-capability/handoffs/<P>.md`. Line 1 of every handoff is `[<P>] -> <owner>`, the owner
being a frozen owner string of that pillar, copied from the ledger's `frozen` block.

    python3 tools/skill_handoffs.py --check          # re-measure at HEAD + handoff contract, exit 0 iff all PASS
    python3 tools/skill_handoffs.py --write L        # measure at HEAD, write handoffs/L.md (the only writer)
    python3 tools/skill_handoffs.py --measure K      # print one measurement as JSON, writes nothing

Decisions (08-03-PLAN.md):
  DH-01  modules/capability_runtime/retirement.py is an adjacent, propose-only evaluator of capability
         contracts. It is cited by I and measured with `--json` only; `--record` writes and is never run.
  DH-02  I module candidates: reachability rows whose status is not REACHABLE and whose declared class is
         absent or DEPRECATED. Declared LIBRARY / SCHEDULED / PLANNED rows are counted by class, not listed.
  DH-03  K and M sweep every file ADDED (`--diff-filter=A`) between FROZEN_AT and the measured commit under
         modules/ and tools/. The range holds foreign commits, so the population is a superset of this
         program's files. It also holds this tool and its test, so neither may match a marker.
  DH-04  Markers (case-insensitive, fixed below). A positive control that stops hitting makes its sweep
         UNMEASURED, never PASS.
  DH-05  A handoff records the commit it measured. `--check` re-measures at HEAD and judges the CLAIMS
         (zero markers, controls hit), not bytes: the added-file population grows with later commits.
  DH-06  Owner items (laptop CO-12 row count, pointing the CE mission at a handoff, adjudicating a contrary
         audit claim) are owner-bundle lines written by plan 08-04, never checkpoints here.

Planes. Repository content is read from COMMITTED blobs at the measured commit (`git grep`, `git cat-file`,
`git diff`, `git archive`), never the working tree. I's reachability and retirement runs execute the
exported copy with HOME set to a fresh empty directory, so the live ~/.claude install is not read
(plan-check W1). K's CO-12 row count is the one host-state reading; it is labelled with its host.

Outcomes per claim part: PASS, FAIL (a marker hit, an absence contradicted), UNMEASURED (a dead control, an
empty population, a missing source), INCONCLUSIVE (git could not answer). A pillar takes the worst part, in
the order FAIL, INCONCLUSIVE, UNMEASURED, PASS.

Exit codes: 0 every pillar PASS; 1 anything else (a git failure included); 2 usage error.
Only `--write` writes, and only under the handoff directory.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
import skill_mirror_drift as smd  # noqa: E402

REPO = _THIS_DIR.parent
PROGRAM_DIR = "vault/programs/skill-capability/"
HANDOFF_DIR = PROGRAM_DIR + "handoffs/"
LEDGER_REL = PROGRAM_DIR + "ledger.json"
FROZEN_AT_REL = PROGRAM_DIR + "FROZEN_AT"
EVIDENCE_REL = PROGRAM_DIR + "evidence/"
CE_LEDGER_REL = "vault/programs/cognitive-economy/ledger.json"
PILLARS = ("I", "K", "L", "M")
SELF_CMD = "python3 tools/skill_handoffs.py"
RUN_TIMEOUT = 300
# Paths a measurement tool could write to in this checkout (reachability --baseline, retirement --record,
# the CE mission's files). Watched before and after I's runs; the rest of the tree is other sessions' business.
WATCH_PATHS = ("vault/capability_runtime", "vault/liveness", "vault/programs/cognitive-economy")

ORDER = ("FAIL", "INCONCLUSIVE", "UNMEASURED", "PASS")

# ------------------------------------------------------------------ markers (DH-04)

ROUTER_BASENAME = re.compile(r"rout(e|er|ing)", re.I)
ROUTER_LINE = re.compile(r"^\s*(def\s+route\(|class\s+\w*Router\b)", re.I)
M_DEF = re.compile(r"^\s*def\s+\w*(price|pricing|cost|usd)\w*\s*\(", re.I)
M_IMPORT = re.compile(r"^\s*(from|import)\s+pricing_source\b", re.I)
M_CONST = re.compile(r"^(?=[A-Z0-9_]*(PRICE|PRICING|COST|USD))[A-Z_][A-Z0-9_]*\s*(:[^=]*)?=(?!=)")
W_NAME = "signals" + ".jsonl"
W_OPEN = re.compile(r"(?:^|[^\w])open\(")
W_QUOTED = re.compile(r"""["']([^"'\n]*)["']""")
W_MODE = re.compile(r"[rwxabt+]+")
W_WRITE_CALL = re.compile(r"\.write_(text|bytes)\(|\b(appendFileSync|writeFileSync|appendFile|writeFile|"
                          r"createWriteStream)\(")
# L name search: built from fragments so this file never holds the searched literals itself.
L_PATH_RE = re.compile("(?i)context" + "[_-]?" + "compiler")
L_NAME_ERE = "class Context" + "Compiler|def compile_" + "context|context_" + "compiler"
L_CLAIM_PHRASE = "context " + "compiler"

K_CONTROLS = ("modules/cost_collapse/router.py", "modules/cognitive_os/router.py",
              "modules/knowledge_acquisition/routing.py")
M_CONTROL = "tools/usage_index.py"
M_CONTROL_KINDS = ("import", "def")
L_WRITER_CONTROLS = ("modules/cognitive_os/co_12_telemetry.py", "tools/test_agent_telemetry.py",
                     "tools/test_co12_signal_race.py")
L_CLAIM_CONTROL = "vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md"
L_CLAIM_FILES = (L_CLAIM_CONTROL, "vault/audits/frontier28/VERDICTS.md",
                 "vendor/genesis-suite/modules/genesis-batch-drafts/lib/genesis-batch-drafts.cjs")
APERTURE_DIRS = ("modules", "tools")
# Cost-model marker hits read and judged not to be a cost model. Keyed by (path, exact stripped line), so an
# edit to the line drops the exception and the hit is open again. An exception whose file is in the population
# but whose line no longer hits is STALE and makes the sweep UNMEASURED.
M_ADJUDICATED = (
    ("tools/skill_dedup_sweep.py", "def _line_cost(name, status, shape):",
     "pillar F listing arithmetic: the characters one listing line occupies (len(name) + overhead + N), an "
     "integer char count with no price, currency or rate"),
    ("tools/test_card_precision.py", "def write_unborn_pricing(repo: str) -> None:",
     "pillar A drill fixture: writes a pricing.py into a temporary repo as the subject the commit card judges; "
     "its domain is test data, not a cost model of this program"),
)


def router_hits(rel: str, text: str) -> list:
    """[(line, marker, text)] for the router marker; line 0 = the basename."""
    hits = []
    base = rel.rsplit("/", 1)[-1]
    if ROUTER_BASENAME.search(base):
        hits.append((0, "basename", base))
    for i, line in enumerate(text.splitlines(), 1):
        if ROUTER_LINE.match(line):
            hits.append((i, "def/class", line.strip()))
    return hits


def m_hits(text: str) -> list:
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if M_IMPORT.match(line):
            hits.append((i, "import", line.strip()))
        elif M_DEF.match(line):
            hits.append((i, "def", line.strip()))
        elif M_CONST.match(line):
            hits.append((i, "const", line.strip()))
    return hits


def is_writer_line(line: str) -> bool:
    """A line holding the CO-12 file name together with a write: an open() whose argument list carries a
    write/append/create mode string, or a write_text / write_bytes / fs write call."""
    if W_NAME not in line:
        return False
    for m in W_OPEN.finditer(line):
        for q in W_QUOTED.findall(line[m.end():]):
            if W_MODE.fullmatch(q) and set(q) & set("wax+"):
                return True
    return bool(W_WRITE_CALL.search(line))


# ------------------------------------------------------------------ git (through skill_mirror_drift)

def _rc1(why: str | None, verb: str) -> bool:
    """git_run folds rc 1 into a reason; for grep (no match) and merge-base (not an ancestor) rc 1 is an answer."""
    return str(why or "").startswith(f"git {verb} rc=1:")


# The one `git cat-file blob <sha>:<path>` failure that is an ANSWER: the commit does not hold the path. git says
# so with rc 128 and one of these two messages (the second when the path exists in the working tree).
ABSENT_BLOB = re.compile(r"^git cat-file rc=128: fatal: path '.*' (does not exist in|exists on disk, but not in) '")


def git_failed(why) -> bool:
    """True when a blob() reason is a git failure (a timeout, a killed or missing git, a lock, an invalid object, any
    other rc), so the caller reports INCONCLUSIVE. False for no reason and for an absent path, which is a measured
    absence (FAIL or UNMEASURED at the caller). smd.is_git_failure knows only vgm.batch_blobs reasons and is False
    for every git_run reason, so it cannot classify blob() (review WR-01)."""
    return bool(why) and not ABSENT_BLOB.match(str(why))


def blob(repo, sha, rel):
    """(text, None) or (None, reason). LF-normalized committed blob. Classify a reason with git_failed()."""
    out, why = smd.git_run(repo, "cat-file", "blob", f"{sha}:{rel}")
    if out is None:
        return None, why
    return smd.lf_bytes(out).decode("utf-8", "replace"), None


def grep(repo, sha, args, paths):
    """([(path, line, text)], None), ([], None) on no match, or (None, reason) on a git failure."""
    out, why = smd.git_run(repo, "grep", "-nI", "-z", *args, sha, "--", *paths)
    if out is None:
        return ([], None) if _rc1(why, "grep") else (None, why)
    rows = []
    for raw in smd.lf_bytes(out).decode("utf-8", "replace").splitlines():
        parts = raw.split("\0")
        if len(parts) < 3:
            continue
        path = parts[0][len(sha) + 1:] if parts[0].startswith(sha + ":") else parts[0]
        rows.append((path, int(parts[1]) if parts[1].isdigit() else 0, "\0".join(parts[2:])))
    return rows, None


def is_ancestor(repo, a, b):
    """(True/False, None) or (None, reason)."""
    out, why = smd.git_run(repo, "merge-base", "--is-ancestor", a, b)
    if out is not None:
        return True, None
    return (False, None) if _rc1(why, "merge-base") else (None, why)


def load_ctx(repo, sha):
    """Freeze pointer and frozen pillars as committed at `sha`. (ctx, None) or (None, (outcome, reason))."""
    text, why = blob(repo, sha, FROZEN_AT_REL)
    if text is None:
        if git_failed(why):
            return None, ("INCONCLUSIVE", f"git failed reading {FROZEN_AT_REL} at {sha[:8]}: {why}")
        return None, ("UNMEASURED", f"no freeze pointer {FROZEN_AT_REL} at {sha[:8]}: {why}")
    frozen, why = smd.resolve_commit(repo, text.strip())
    if frozen is None:
        return None, ("INCONCLUSIVE", f"freeze commit {text.strip()!r} not resolvable: {why}")
    led_text, why = blob(repo, sha, LEDGER_REL)
    if led_text is None:
        if git_failed(why):
            return None, ("INCONCLUSIVE", f"git failed reading {LEDGER_REL} at {sha[:8]}: {why}")
        return None, ("UNMEASURED", f"ledger not readable at {sha[:8]}: {why}")
    try:
        led = json.loads(led_text)
        pillars = {p["id"]: p for p in led["frozen"]["pillars"]}
    except (ValueError, KeyError, TypeError) as e:
        return None, ("UNMEASURED", f"ledger frozen block unreadable: {e}")
    return {"sha": sha, "frozen": frozen, "ledger": led, "pillars": pillars}, None


def owner_line_owner(pillar: dict) -> str:
    """The owner named on line 1: the first frozen owner that is a repo .py path, else the first owner."""
    owners = list(pillar.get("owner") or [])
    for o in owners:
        if o.endswith(".py") and not o.startswith("~"):
            return o
    return owners[0] if owners else ""


def added_files(repo, ctx):
    """(sorted added paths under modules/ and tools/ in FROZEN_AT..sha, None) or (None, reason)."""
    out, why = smd.git_run(repo, "diff", "--name-only", "-z", "--no-renames", "--diff-filter=A",
                           ctx["frozen"], ctx["sha"], "--", *APERTURE_DIRS)
    if out is None:
        return None, why
    return sorted(p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p), None


def aperture_cmd(ctx):
    return (f"git diff --name-only --diff-filter=A {ctx['frozen'][:8]} {ctx['sha'][:8]} -- "
            + " ".join(APERTURE_DIRS))


def worst(parts: dict) -> str:
    seen = {v[0] for v in parts.values()}
    for o in ORDER:
        if o in seen:
            return o
    return "PASS"


def _new(pillar_id, ctx, host):
    return {"pillar": pillar_id, "sha": ctx["sha"], "frozen": ctx["frozen"], "host": host,
            "parts": {}, "info": {}, "commands": [], "evidence": [], "aperture": [], "owner_do": [],
            "not_done": []}


def _sweep_added(repo, ctx, m, kind):
    """Shared K/M sweep over the added-file population. Returns (rows, None) or (None, reason)."""
    files, why = added_files(repo, ctx)
    if files is None:
        return None, why
    rows = []
    for rel in files:
        text, why = blob(repo, ctx["sha"], rel)
        if text is None:
            return None, why
        hits = router_hits(rel, text) if kind == "router" else m_hits(text)
        rows.append((rel, hits))
    return rows, None


def cell(s) -> str:
    """A markdown table cell: pipes escaped (GFM honours `\\|` inside code spans), newlines flattened."""
    return str(s).replace("|", "\\|").replace("\n", " ")


def _sweep_table(rows, label):
    out = [f"| added file | {label} hits | hit lines |", "|---|---|---|"]
    for rel, hits in rows:
        desc = "; ".join(f"{ln}:{mk}" for ln, mk, _ in hits) or "-"
        out.append(f"| {rel} | {len(hits)} | {desc} |")
    return out


# ------------------------------------------------------------------ L

def measure_L(repo, ctx, host):
    r = _new("L", ctx, host)
    sha, parts, cmds, ev = ctx["sha"], r["parts"], r["commands"], r["evidence"]
    # (a) tracked paths by name
    tracked, why = smd.tracked_paths(repo, sha)
    if tracked is None:
        parts["absence"] = ["INCONCLUSIVE", f"ls-tree failed: {why}"]
        return r
    path_hits = sorted(p for p in tracked if L_PATH_RE.search(p))
    cmds.append([f"git ls-tree -r --name-only {sha[:8]} | grep -icE '{L_PATH_RE.pattern[4:]}'",
                 f"{len(path_hits)} of {len(tracked)} tracked paths"])
    # (b) code identifiers
    code_hits, why = grep(repo, sha, ["-E", L_NAME_ERE], ["*.py", "*.js"])
    if code_hits is None:
        parts["absence"] = ["INCONCLUSIVE", f"git grep failed: {why}"]
        return r
    cmds.append([f"git grep -nIE '{L_NAME_ERE}' {sha[:8]} -- '*.py' '*.js'",
                 f"{len(code_hits)} lines" + (" (rc 1)" if not code_hits else "")])
    if path_hits or code_hits:
        parts["absence"] = ["FAIL", f"paths {path_hits[:3]} code {[(p, n) for p, n, _ in code_hits[:3]]}"]
    else:
        parts["absence"] = ["PASS", "0 tracked paths, 0 code lines"]
    # (c) name-search positive control + the contradicting claims, located by grep
    claims, why = grep(repo, sha, ["-i", "-F", L_CLAIM_PHRASE], list(L_CLAIM_FILES))
    if claims is None:
        parts["control"] = ["INCONCLUSIVE", f"git grep failed: {why}"]
        return r
    cmds.append([f"git grep -nIi -F '{L_CLAIM_PHRASE}' {sha[:8]} -- " + " ".join(L_CLAIM_FILES),
                 f"{len(claims)} lines"])
    claim_ctl = [c for c in claims if c[0] == L_CLAIM_CONTROL and "Context Compiler" in c[2]]
    r["info"]["claims"] = claims
    # (d) CO-12 writers at sha
    sig, why = grep(repo, sha, ["-F", W_NAME], ["*.py", "*.js"])
    if sig is None:
        parts["control"] = ["INCONCLUSIVE", f"git grep failed: {why}"]
        return r
    writers = [s for s in sig if is_writer_line(s[2])]
    cmds.append([f"git grep -nI -F '{W_NAME}' {sha[:8]} -- '*.py' '*.js'  (then the writer marker per line)",
                 f"{len(sig)} lines, {len(writers)} writer lines"])
    r["info"]["writers"] = writers
    dead = [c for c in L_WRITER_CONTROLS if not any(w[0] == c for w in writers)]
    if not claim_ctl:
        dead.insert(0, f"{L_CLAIM_CONTROL} ('Context Compiler')")
    parts["control"] = (["UNMEASURED", f"dead controls {dead}"] if dead else
                        ["PASS", f"name control {claim_ctl[0][0]}:{claim_ctl[0][1]}; "
                                 f"{len(L_WRITER_CONTROLS)} writer controls hit"])
    # (e) added writer lines since the freeze
    out, why = smd.git_run(repo, "diff", "-U0", "--no-color", "--no-ext-diff", "--no-renames", ctx["frozen"], sha,
                           "--", "*.py", "*.js")
    if out is None:
        parts["writer"] = ["INCONCLUSIVE", f"git diff failed: {why}"]
        return r
    added, cur, n_added = [], None, 0
    for line in smd.lf_bytes(out).decode("utf-8", "replace").splitlines():
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("+") and not line.startswith("+++"):
            n_added += 1
            if is_writer_line(line[1:]):
                added.append((cur, line[1:].strip()))
    cmds.append([f"git diff -U0 {ctx['frozen'][:8]} {sha[:8]} -- '*.py' '*.js'  (added lines, writer marker)",
                 f"{n_added} added lines, {len(added)} writer lines"])
    r["info"]["added_writers"] = added
    parts["writer"] = (["FAIL", f"added writer lines {added[:3]}"] if added else
                       ["PASS", f"0 of {n_added} added lines write {W_NAME}"])
    r["aperture"] = [
        f"Context Compiler: by name only (tracked paths matching `{L_PATH_RE.pattern}`, and the identifiers "
        f"`{L_NAME_ERE}` in *.py / *.js). An implementation under another name is not excluded.",
        f"CO-12 writers: lines naming `{W_NAME}` in *.py / *.js that also open it in a write, append or create "
        "mode, or call write_text / write_bytes / an fs write on it, on the same line. A writer that builds "
        "the path on one line and opens it on another is outside this marker; the three positive controls "
        "show the marker reaches the known writers.",
        f"Added lines: every `+` line of the diff from the freeze {ctx['frozen'][:8]} to the measured commit, "
        "in all *.py / *.js files. The range includes commits of other programs (a superset of this one's).",
    ]
    ev.append("### Contradicting claims (quoted for the Owner)")
    ev.append("")
    ev += [f"- `{p}:{n}`: {t.strip()}" for p, n, t in claims] or ["- none found"]
    ev.append("")
    ev.append(f"### CO-12 writers at {sha[:8]}")
    ev.append("")
    ev += ["| file:line | line |", "|---|---|"]
    ev += [f"| {p}:{n} | `{cell(t.strip())}` |" for p, n, t in writers]
    ev.append("")
    ev.append(f"Writer controls: {', '.join(L_WRITER_CONTROLS)}. The first is the owner's `record_signal`; "
              "the other two are tests that write a fixture file in a temporary state directory.")
    ev.append("")
    ev.append(f"### Writer lines added since the freeze: {len(added)}")
    ev += [""] + [f"- {p}: `{t}`" for p, t in added] if added else []
    r["owner_do"] = [
        "Cognitive-economy (owner of the Context Compiler question, CE ledger): treat the Context Compiler as "
        "ABSENT by name in this repository, as measured above, and decide whether to build it. This program "
        "defers it and builds none.",
        "The Owner adjudicates the contradicting audit line quoted above (it calls the capability "
        "EXISTS_AND_COMPLETE and names other components); plan 08-04 writes that as an `[L]` owner-bundle item.",
        "`modules/cognitive_os/co_12_telemetry.py`: `record_signal` stays the single writer of the CO-12 file. "
        "This program writes CO-12 rows only through it (`tools/skill_opportunity_signals.py`).",
    ]
    r["not_done"] = [
        "Did not build, stub or name a Context Compiler.",
        "Did not add a second writer of the CO-12 file, and did not run any CO-12 writer for this handoff.",
        "Did not edit `vault/programs/cognitive-economy/**` or the audit files it quotes.",
    ]
    return r


# ------------------------------------------------------------------ K

def _report_rows():
    """K's CO-12 row count through the producer's own consumer (`report`), never `sync`. Host state."""
    try:
        import skill_opportunity_signals as sos  # noqa: PLC0415
        from modules.cognitive_os import co_12_telemetry as co12  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001 -- an import failure is a reason, not a crash
        return {"state": "UNMEASURED", "reason": f"report not importable: {type(e).__name__}: {e}"}
    path = co12._default_state_dir() / W_NAME
    try:
        rep = sos.report()
    except Exception as e:  # noqa: BLE001
        return {"state": "UNMEASURED", "reason": f"report failed: {type(e).__name__}: {e}"}
    present = path.is_file()
    if not present or not rep.get("rows"):
        # Read the host, never infer it from the host name (review IN-03): the card ledger the producer syncs from.
        card = sos.card_state_dir() / "ledger.jsonl"
        try:
            card_present = card.is_file()
        except OSError as e:
            card_present = f"unreadable ({type(e).__name__})"
        why = "no card ledger on this host" if card_present is False else "no CO-12 opportunity rows on this host"
        return {"state": "UNMEASURED", "reason": f"{why} (card ledger present: {card_present}; CO-12 file present: "
                                                 f"{present}, rows {rep.get('rows', 0)})", "report": rep}
    return {"state": "MEASURED", "reason": f"rows {rep['rows']}", "report": rep}


def measure_K(repo, ctx, host):
    r = _new("K", ctx, host)
    sha, parts, cmds, ev = ctx["sha"], r["parts"], r["commands"], r["evidence"]
    rows, why = _sweep_added(repo, ctx, r, "router")
    if rows is None:
        for p in ("aperture", "router", "control"):
            parts[p] = ["INCONCLUSIVE", f"git failed: {why}"]
        return r
    cmds.append([aperture_cmd(ctx), f"{len(rows)} added files"])
    parts["aperture"] = (["PASS", f"{len(rows)} added files"] if rows else
                         ["UNMEASURED", "zero added files under modules/ and tools/"])
    n_hits = sum(len(h) for _, h in rows)
    cmds.append(["router marker over each added file (basename, then each line)", f"{n_hits} hits"])
    parts["router"] = (["FAIL", "; ".join(f"{rel}:{h[0][0]}:{h[0][1]}" for rel, h in rows if h)[:300]]
                       if n_hits else ["PASS", f"0 hits in {len(rows)} files"])
    ctl, dead = [], []
    for rel in K_CONTROLS:
        text, why = blob(repo, sha, rel)
        if text is None and git_failed(why):
            parts["control"] = ["INCONCLUSIVE", f"git failed: {why}"]
            break
        hits = [h for h in router_hits(rel, text or "") if h[0] > 0]
        (ctl if hits else dead).append((rel, hits))
    else:
        parts["control"] = (["UNMEASURED", f"dead controls {[d[0] for d in dead]}"] if dead else
                            ["PASS", "; ".join(f"{rel}:{h[0][0]}" for rel, h in ctl)])
    cmds.append(["router marker over the controls " + ", ".join(K_CONTROLS),
                 f"{len(ctl)} of {len(K_CONTROLS)} hit by content"])
    rep = _report_rows()
    r["info"]["rows"] = rep
    cmds.append(["python3 tools/skill_opportunity_signals.py report  (in-process report(); never sync)",
                 json.dumps(rep.get("report")) if rep.get("report") is not None else rep["reason"]])
    r["aperture"] = [
        f"Population: every file ADDED between the freeze {ctx['frozen'][:8]} and the measured commit under "
        "modules/ and tools/ (`--diff-filter=A`, endpoints compared). The range includes commits of other "
        "programs, so it is a superset of this program's files; a file added and removed inside the range "
        "is not in it.",
        "Router marker: a basename matching `rout(e|er|ing)`, or a line starting with `def route(` or "
        "`class <Name>Router` (case-insensitive). A router under another name or shape is outside it; the "
        "three controls show the marker reaches the repository's existing routers.",
        f"CO-12 row count: host state `{rep.get('state')}` read on {host}, not a committed blob.",
    ]
    ev += [f"### Router sweep at {sha[:8]}", ""] + _sweep_table(rows, "router")
    ev += ["", "### Router controls (must hit by content)", ""]
    ev += [f"- {rel}: " + ("; ".join(f"{ln}: `{t}`" for ln, _, t in hits) or "NO HIT") for rel, hits in ctl + dead]
    ev += ["", "### CO-12 opportunity rows", "",
           f"- state: {rep['state']}; {rep['reason']}",
           "- producer: `tools/skill_opportunity_signals.py` (kind `capability_opportunity`, capability "
           "`concurrent-writers-shared-tree`), which writes only through `record_signal`."]
    r["owner_do"] = [
        "ACV (`vault/specs/agent-capability-virtualization.md`, `modules/capability_runtime/agent_spec.py`): "
        "routing stays with you. Consume this program's opportunity rows from CO-12 (kind "
        "`capability_opportunity`, read with `python3 tools/skill_opportunity_signals.py report`).",
        "The row count on this host is UNMEASURED (reason above). The laptop count is an Owner item `[K]` "
        "written by plan 08-04.",
    ]
    r["not_done"] = [
        "Built no router: the sweep above found no router marker in any added file under modules/ or tools/.",
        "Did not run `sync` (it writes); only `report` was read.",
    ]
    return r


# ------------------------------------------------------------------ M

DELTA_LINE = re.compile(r"(?i)\bdelta [+-]\d|\bmoved\b.*[+-]\d|\blargest effect\b")
DENOM_HEAD = re.compile(r"--\s*(D-[A-Z0-9]+)\s+measurement")
M_DELTA_SOURCES = ("B-listing-floor.md", "E-contribution.md")
UNNAMED = "UNNAMED"


def measure_M(repo, ctx, host):
    r = _new("M", ctx, host)
    sha, parts, cmds, ev = ctx["sha"], r["parts"], r["commands"], r["evidence"]
    rows, why = _sweep_added(repo, ctx, r, "m")
    if rows is None:
        for p in ("aperture", "cost", "control", "denominator"):
            parts[p] = ["INCONCLUSIVE", f"git failed: {why}"]
        return r
    cmds.append([aperture_cmd(ctx), f"{len(rows)} added files"])
    parts["aperture"] = (["PASS", f"{len(rows)} added files"] if rows else
                         ["UNMEASURED", "zero added files under modules/ and tools/"])
    n_hits = sum(len(h) for _, h in rows)
    adj = {(rel, text): why for rel, text, why in M_ADJUDICATED}
    open_hits = [(rel, ln, k, t) for rel, h in rows for ln, k, t in h if (rel, t) not in adj]
    used = [(rel, ln, k, t, adj[(rel, t)]) for rel, h in rows for ln, k, t in h if (rel, t) in adj]
    pop = {rel for rel, _ in rows}
    stale = [(rel, text) for rel, text, _ in M_ADJUDICATED
             if rel in pop and not any(u[0] == rel and u[3] == text for u in used)]
    cmds.append(["cost-model marker over each added file (each line)",
                 f"{n_hits} hits: {len(open_hits)} open, {len(used)} adjudicated not a cost model"])
    if open_hits:
        parts["cost"] = ["FAIL", "; ".join(f"{rel}:{ln}:{k}" for rel, ln, k, _ in open_hits)[:300]]
    elif stale:
        parts["cost"] = ["UNMEASURED", f"stale adjudications (file in population, line no longer hits): {stale}"]
    else:
        parts["cost"] = ["PASS", f"0 open hits in {len(rows)} files ({len(used)} adjudicated)"]
    r["info"]["adjudicated"] = used
    text, why = blob(repo, sha, M_CONTROL)
    ctl = m_hits(text or "")
    kinds = {k for _, k, _ in ctl}
    missing = [k for k in M_CONTROL_KINDS if k not in kinds]
    if text is None and git_failed(why):
        parts["control"] = ["INCONCLUSIVE", f"git failed: {why}"]
    elif missing:
        parts["control"] = ["UNMEASURED", f"{M_CONTROL} lacks marker kinds {missing}"]
    else:
        parts["control"] = ["PASS", f"{M_CONTROL}: {len(ctl)} hits"]
    cmds.append([f"cost-model marker over the control {M_CONTROL}", f"{len(ctl)} hits, kinds {sorted(kinds)}"])
    # Every turn / token figure this program reported, with its denominator.
    savings = []
    for pid, st in sorted((ctx["ledger"].get("state") or {}).items()):
        for s in (st or {}).get("savings") or []:
            savings.append((pid, s))
    cmds.append([f"ledger state.<P>.savings[] at {sha[:8]} ({LEDGER_REL})", f"{len(savings)} entries"])
    deltas, unreadable, per_source = [], [], []
    for name in M_DELTA_SOURCES:
        t, why = blob(repo, sha, EVIDENCE_REL + name)
        if t is None:
            deltas.append((name, 0, f"UNREADABLE: {why}", "-"))
            unreadable.append((name, why))
            per_source.append(f"{name}: unreadable")
            continue
        m = DENOM_HEAD.search(t.splitlines()[0] if t else "")
        denom = m.group(1) if m else UNNAMED
        hit = [(name, i, line.strip(), denom) for i, line in enumerate(t.splitlines(), 1) if DELTA_LINE.search(line)]
        deltas += hit
        per_source.append(f"{name}: {len(hit)} delta line(s), denominator {denom} (from its line 1)")
    cmds.append(["delta lines of evidence/B-listing-floor.md and evidence/E-contribution.md (pattern "
                 f"`{DELTA_LINE.pattern}`; denominator from line 1)", f"{len(deltas)} lines"])
    r["info"]["savings"] = savings
    r["info"]["deltas"] = deltas
    # The frozen rule: deltas relative to a NAMED denominator. Judge it on every figure (review WR-03).
    no_denom = [p for p, s in savings if not str(s.get("denominator") or "").strip()]
    unnamed = [f"{n}:{i}" for n, i, _, d in deltas if d == UNNAMED]
    readable_lines = [x for x in deltas if x[1] > 0]
    if no_denom or unnamed:
        parts["denominator"] = ["FAIL", f"savings entries of pillars {no_denom} lack a denominator; delta lines "
                                        f"under an unnamed denominator {unnamed}"[:300]]
    elif any(git_failed(w) for _, w in unreadable):
        parts["denominator"] = ["INCONCLUSIVE", f"git failed: {unreadable}"[:300]]
    elif unreadable:
        parts["denominator"] = ["UNMEASURED", f"evidence not committed: {[n for n, _ in unreadable]}"]
    elif not readable_lines:
        parts["denominator"] = ["UNMEASURED", f"dead control: the delta pattern hits no line of {M_DELTA_SOURCES}"]
    else:
        parts["denominator"] = ["PASS", f"{len(savings)} savings entries and {len(readable_lines)} delta lines, each "
                                        "with a named denominator"]
    cmds.append(["denominator of every savings[] entry and every delta line", parts["denominator"][1]])
    r["aperture"] = [
        "Population: the same added-file set as K (modules/ and tools/, `--diff-filter=A`, freeze to the "
        "measured commit, a superset of this program's files).",
        "Cost-model marker: a line starting with `def <name containing price|pricing|cost|usd>(`, an import of "
        "`pricing_source`, or an UPPER_CASE constant containing PRICE|PRICING|COST|USD assigned at line "
        "start. A cost model under other names is outside it; the control shows the marker reaches the owner.",
        "Figures: read from the ledger's `savings[]` and the delta lines of the B and E evidence files, never "
        "by searching evidence for the word token.",
    ]
    ev += ["### Turn and token figures this program reported", "",
           "| pillar | what | value | unit | status | displacement | denominator |", "|---|---|---|---|---|---|---|"]
    ev += [f"| {p} | {cell(s.get('what'))} | {s.get('value')} | {s.get('unit')} | {s.get('status')} | "
           f"{s.get('displacement')} | {s.get('denominator')} |" for p, s in savings]
    ev += ["", "### Delta lines quoted from evidence (denominator from each file's line 1)", "",
           "| source | denominator | line |", "|---|---|---|"]
    ev += [f"| {n}:{i} | {d} | {cell(t)} |" for n, i, t, d in deltas]
    ev += ["", "Per source (measured above, not typed): " + "; ".join(per_source) + ".",
           "", f"### Cost-model sweep at {sha[:8]}", ""] + _sweep_table(rows, "cost-model")
    ev += ["", f"### Marker hits adjudicated not a cost model: {len(used)}", "",
           "Each is pinned in `M_ADJUDICATED` of tools/skill_handoffs.py by path and exact line; an edit to the "
           "line re-opens the hit. The Owner may disagree with a reason.", "",
           "| file:line | line | why it is not a cost model |", "|---|---|---|"]
    ev += [f"| {rel}:{ln} | `{cell(t)}` | {cell(why)} |" for rel, ln, _, t, why in used]
    ev += ["", f"### Control {M_CONTROL}", ""] + [f"- {ln}: {k}: `{t}`" for ln, k, t in ctl]
    r["owner_do"] = [
        "`tools/usage_index.py`: cost figures stay yours, from your windows. The figures above are turn and "
        "token deltas relative to a named denominator, upper bounds unless the status says realized; none is "
        "a cost.",
    ]
    r["not_done"] = [
        f"Owns no cost model: the sweep above found no open cost-model marker hit in any added file "
        f"({len(used)} hit(s) read and adjudicated not a cost model, listed above).",
        "Converted no token or turn figure to money.",
    ]
    return r


# ------------------------------------------------------------------ I

def _snapshot(root: Path) -> dict:
    out = {}
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            p = Path(dp) / f
            try:
                st = p.lstat()
            except OSError:
                continue
            out[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return out


def _porcelain(repo):
    out, why = smd.git_run(repo, "status", "--porcelain", "--", *WATCH_PATHS)
    return (out.decode("utf-8", "replace") if out is not None else None), why


def _extract(tar_bytes: bytes, dest: Path):
    """Extract an archive with the data filter; a member the filter refuses is skipped and counted."""
    members = skipped = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tf:
        for m in tf.getmembers():
            try:
                tf.extract(m, dest, filter="data")
                members += 1
            except (tarfile.FilterError, OSError):
                skipped += 1
    return members, skipped


def _run_json(script: Path, cwd: Path, home: Path):
    """(json, rc, None) or (None, rc, reason). rc 1 with valid JSON is a measurement."""
    if not script.is_file():
        return None, None, f"{script.relative_to(cwd).as_posix()} not in the export"
    # No bytecode cache: the export must read back byte-identical after the runs (the nowrite part).
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONDONTWRITEBYTECODE="1")
    try:
        p = subprocess.run([sys.executable, str(script), "--json"], cwd=str(cwd), env=env,
                           capture_output=True, timeout=RUN_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as e:
        return None, None, f"run failed: {e}"
    try:
        return json.loads(p.stdout.decode("utf-8", "replace")), p.returncode, None
    except ValueError:
        tail = p.stderr.decode("utf-8", "replace").strip().splitlines()
        return None, p.returncode, f"rc={p.returncode}, no JSON ({tail[-1] if tail else 'no stderr'})"


def _skill_candidates(repo, ctx):
    """(rows, labels, None) or (None, labels-or-None, reason). gex44 coverage plane rows with coverage `none`, minus
    skills invoked in window G. The coverage class is computed by pillar D's gate and rendered into
    D-coverage.md; D-live-gex44.json carries the skill list, so the two are cross-checked. A reason that starts
    with "git failed" is a git failure (INCONCLUSIVE at the caller); any other reason is UNMEASURED."""
    sha = ctx["sha"]
    srcs = ("D-live-gex44.json", "C-window-G.json", "D-coverage.md")
    got = {n: blob(repo, sha, EVIDENCE_REL + n) for n in srcs}
    failed = [f"{n}: {w}" for n, (_t, w) in got.items() if git_failed(w)]
    if failed:
        return None, None, f"git failed: {failed[0]}"
    missing = [f"{n}: {w}" for n, (t, w) in got.items() if t is None]
    if missing:
        return None, None, f"source missing: {missing[0]}"
    d_text, c_text, cov_text = (got[n][0] for n in srcs)
    try:
        d, c = json.loads(d_text), json.loads(c_text)
        live, host, node, at = list(d["skills"]), d["host"], d["node"], d["measured_at"]
        invoked = dict(c["skills"])
        window = (c["window"], c["start"], c["end"], c["host"], c["totals"]["files_scanned"])
    except (ValueError, KeyError, TypeError) as e:
        return None, None, f"missing key: {e}"
    rows, in_sec, header = {}, False, False
    for i, line in enumerate(cov_text.splitlines(), 1):
        if line.startswith("## "):
            in_sec = line.strip() == f"## Plane {host}"
            header = False
            continue
        if in_sec and line.startswith("| skill | coverage |"):
            header = True
            continue
        if in_sec and header and line.startswith("| ") and not line.startswith("|---"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) >= 4:
                rows[cells[0]] = (cells[1], cells[3], i)
    if not rows:
        return None, None, f"no `## Plane {host}` coverage table in D-coverage.md"
    if set(rows) != set(live):
        return None, None, (f"D-coverage.md plane {host} ({len(rows)}) and D-live-gex44.json ({len(live)}) "
                            "disagree on the skill set")
    none = sorted(s for s, v in rows.items() if v[0] == "none")
    cands = [(s, rows[s][1], rows[s][2]) for s in none if s not in invoked]
    labels = {"host": host, "node": node, "measured_at": at, "skills": len(live), "none": len(none),
              "invoked": sorted(invoked), "window": window}
    if not cands:
        return None, labels, "zero skill candidates"
    return cands, labels, None


def measure_I(repo, ctx, host):
    r = _new("I", ctx, host)
    sha, parts, cmds, ev = ctx["sha"], r["parts"], r["commands"], r["evidence"]
    before, why = _porcelain(repo)
    if before is None:
        for p in ("reachability", "retirement", "skills", "nowrite"):
            parts[p] = ["INCONCLUSIVE", f"git status failed: {why}"]
        return r
    tar, why = smd.git_run(repo, "archive", "--format=tar", sha)
    if tar is None:
        for p in ("reachability", "retirement", "nowrite"):
            parts[p] = ["INCONCLUSIVE", f"git archive failed: {why}"]
    else:
        with tempfile.TemporaryDirectory(prefix="skh-export-") as exp, \
                tempfile.TemporaryDirectory(prefix="skh-home-") as home:
            exp_p, home_p = Path(exp), Path(home)
            n_mem, n_skip = _extract(tar, exp_p)
            cmds.append([f"git archive --format=tar {sha[:8]}  (extracted to a temporary directory)",
                         f"{len(tar)} bytes, {n_mem} members, {n_skip} refused by the data filter"])
            snap0 = _snapshot(exp_p)
            reach, rc, why = _run_json(exp_p / "modules/liveness/reachability.py", exp_p, home_p)
            cmds.append(["HOME=<empty tmp> python3 modules/liveness/reachability.py --json  (cwd = export)",
                         f"rc={rc}" + (f", rows {len(reach.get('rows') or [])}, offenders "
                                       f"{len(reach.get('offenders') or [])}" if isinstance(reach, dict) else
                                       f", {why}")])
            ret, rc2, why2 = _run_json(exp_p / "modules/capability_runtime/retirement.py", exp_p, home_p)
            cmds.append(["HOME=<empty tmp> python3 modules/capability_runtime/retirement.py --json  "
                         "(cwd = export; never --record)",
                         f"rc={rc2}" + (f", verdicts {len(ret.get('verdicts') or [])}" if isinstance(ret, dict)
                                        else f", {why2}")])
            snap1 = _snapshot(exp_p)
            home_after = sorted(os.listdir(home_p))
        changed = sorted(k for k in set(snap0) | set(snap1) if snap0.get(k) != snap1.get(k))
        # reachability rows
        keys_ok = isinstance(reach, dict) and isinstance(reach.get("rows"), list) and reach["rows"] and all(
            {"unit", "status", "klass"} <= set(x) for x in reach["rows"])
        if not keys_ok:
            parts["reachability"] = ["UNMEASURED", why or "rows missing or keys differ from unit/status/klass"]
        else:
            rws, offs = reach["rows"], {o.get("unit") for o in reach.get("offenders") or []}
            by_status, by_class = {}, {}
            for x in rws:
                by_status[x["status"]] = by_status.get(x["status"], 0) + 1
                if x["status"] != "REACHABLE":
                    k = x["klass"] or "undeclared"
                    by_class[k] = by_class.get(k, 0) + 1
            cands = sorted((x for x in rws if x["status"] != "REACHABLE" and x["klass"] in (None, "DEPRECATED")),
                           key=lambda x: x["unit"])
            r["info"]["modules"] = {"rows": len(rws), "by_status": by_status, "by_class_unreachable": by_class,
                                    "offenders": len(offs), "candidates": len(cands), "passed": reach.get("passed")}
            parts["reachability"] = ["PASS", f"{len(rws)} rows parsed, {len(cands)} candidates"]
            ev += [f"### Module candidates (plane: committed export of {sha[:8]}, HOME empty)", "",
                   f"Rows {len(rws)}; by status " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items()))
                   + f"; gate offenders {len(offs)}; gate passed {reach.get('passed')}.",
                   "Not REACHABLE, counted by declared class (declared rows are alive by declaration and not "
                   "listed): " + ", ".join(f"{k} {v}" for k, v in sorted(by_class.items())) + ".",
                   f"Candidates (status not REACHABLE, class absent or DEPRECATED): {len(cands)}. "
                   "`gate offender` = no (the module is in the registry's standing debt `known_orphans`).", "",
                   "| module | status | class | gate offender | via | note |", "|---|---|---|---|---|---|"]
            ev += [f"| {x['unit']} | {x['status']} | {x['klass'] or '-'} | {'yes' if x['unit'] in offs else 'no'}"
                   f" | {cell(x.get('via') or '-')} | {cell(x.get('note') or '-')} |" for x in cands]
        if not (isinstance(ret, dict) and isinstance(ret.get("verdicts"), list) and ret["verdicts"]):
            parts["retirement"] = ["UNMEASURED", why2 or "no verdicts"]
        else:
            vs = ret["verdicts"]
            counts = {}
            for v in vs:
                counts[v.get("status")] = counts.get(v.get("status"), 0) + 1
            r["info"]["retirement"] = counts
            parts["retirement"] = ["PASS", f"{len(vs)} verdicts parsed"]
            ev += ["", "### Adjacent evaluator: modules/capability_runtime/retirement.py (DH-01)", "",
                   "Propose-only evaluator of the `retirement_condition` of capability contracts "
                   "(`vault/capability_runtime/contracts/*.json`). It enumerates contracts, not modules or skills, "
                   "and is not a frozen owner of I; its `liveness_reachability` probe reuses `reachability.gate`.",
                   f"Verdicts {len(vs)}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=str))
                   + f"; stale {len(ret.get('stale') or [])}.", "",
                   "| contract | status | evidence |", "|---|---|---|"]
            ev += [f"| {v.get('contract_id')} | {v.get('status')} | {cell(v.get('evidence') or '')} |"
                   for v in vs]
        after, why3 = _porcelain(repo)
        if after is None:
            parts["nowrite"] = ["INCONCLUSIVE", f"git status failed: {why3}"]
        elif after != before or changed or home_after:
            parts["nowrite"] = ["FAIL", f"porcelain moved {after != before}; export changed {changed[:3]}; "
                                        f"HOME holds {home_after[:3]}"]
        else:
            parts["nowrite"] = ["PASS", "watched paths, export tree and HOME unchanged"]
        cmds.append([f"git status --porcelain -- {' '.join(WATCH_PATHS)}  (before == after); export tree and "
                     "HOME compared", parts["nowrite"][1]])
    # skill candidates
    sk, labels, why = _skill_candidates(repo, ctx)
    if sk is None:
        parts["skills"] = ["INCONCLUSIVE" if why.startswith("git failed") else "UNMEASURED", why]
    else:
        parts["skills"] = ["PASS", f"{len(sk)} skill candidates"]
        w = labels["window"]
        r["info"]["skills"] = {"candidates": len(sk), "none": labels["none"], "skills": labels["skills"]}
        cmds.append([f"coverage none rows of evidence/D-coverage.md section '## Plane {labels['host']}' at {sha[:8]}, "
                     "cross-checked against evidence/D-live-gex44.json, minus evidence/C-window-G.json key skills",
                     f"{labels['skills']} skills, {labels['none']} none, {len(labels['invoked'])} invoked, "
                     f"{len(sk)} candidates"])
        ev += ["", f"### Skill candidates (host {labels['host']} / node {labels['node']}, coverage recorded "
                   f"{labels['measured_at']}; invocation window {w[0]} {w[1]}..{w[2]}, host {w[3]}, "
                   f"{w[4]} transcript files)", "",
               f"Coverage `none` on that host: {labels['none']} of {labels['skills']}. Invoked in the window "
               f"(excluded): {', '.join(labels['invoked'])}. Candidates: {len(sk)}. Another host or window can "
               "differ.", "",
               "| skill | criticality | D-coverage.md line |", "|---|---|---|"]
        ev += [f"| {s} | {c} | {i} |" for s, c, i in sk]
    ce_t, _ = blob(repo, sha, CE_LEDGER_REL)
    t_name = "unreadable"
    try:
        t = [p for p in json.loads(ce_t)["frozen"]["pillars"] if p["id"] == "T"][0]
        t_name = f"\"{t['name']}\", predicted {t['predicted']}"
    except Exception:  # noqa: BLE001 -- an unreadable CE ledger only changes the quoted name
        pass
    r["info"]["ce_T"] = t_name
    r["aperture"] = [
        "Modules: the reachability scanner's own population (packages under `modules/`), run on a `git archive` "
        "export of the measured commit with HOME set to an empty directory, so live ~/.claude seeds are not "
        "merged (plan-check W1). A host's live install adds seeds, so a module listed here can be reachable on "
        "that host; this list is the committed-blobs plane only.",
        "Skills: the coverage plane recorded on one host and the invocation window of pillar C on that host, "
        "both committed evidence. A skill invoked only outside the window, or on another host, is listed.",
    ]
    r["owner_do"] = [
        f"Cognitive-economy pillar T ({t_name}, owner `{CE_LEDGER_REL}`): take these lists as input to "
        "institutional GC. Re-measure before acting: both lists are measured at the commit above.",
        "`modules/liveness/reachability.py`: the module list is your own output on committed blobs; a candidate "
        "leaves it by being wired, declared in the registry, or deleted by its owner.",
        "A candidate is not a deletion verdict. This program deleted nothing.",
    ]
    r["not_done"] = [
        "Deleted, moved or deprecated nothing; declared nothing in `vault/liveness/reachability_registry.json`.",
        "Did not run `reachability.py --baseline` or `retirement.py --record` (both write).",
        "Did not edit `vault/programs/cognitive-economy/**`; the Owner points the CE mission at this file "
        "(an `[I]` owner-bundle item written by plan 08-04).",
    ]
    return r


MEASURES = {"I": measure_I, "K": measure_K, "L": measure_L, "M": measure_M}


def measure(repo, pillar, sha=None, host=None):
    """One pillar's measurement at `sha` (default HEAD). Never raises on a git failure."""
    host = host or platform.node()
    if sha is None:
        sha, why = smd.resolve_commit(repo, "HEAD")
        if sha is None:
            return {"pillar": pillar, "sha": None, "parts": {"git": ["INCONCLUSIVE",
                                                                      f"HEAD not resolvable: {why}"]}}
    ctx, bad = load_ctx(repo, sha)
    if ctx is None:
        return {"pillar": pillar, "sha": sha, "parts": {"ctx": list(bad)}}
    r = MEASURES[pillar](repo, ctx, host)
    r["ctx"] = ctx
    return r


# ------------------------------------------------------------------ render

def render(r) -> str:
    ctx, p = r["ctx"], r["pillar"]
    fp = ctx["pillars"][p]
    owner = owner_line_owner(fp)
    parts = " ".join(f"{k}={v[0]}" for k, v in r["parts"].items())
    L = [f"[{p}] -> {owner}", "",
         f"Handoff of skill-capability pillar [{p}] ({fp.get('name')}), predicted {fp.get('predicted')}.", "",
         "Frozen rule (ledger `frozen.pillars`):", "", f"> {fp.get('rule')}", "",
         "Frozen owners: " + ", ".join(f"`{o}`" for o in fp.get("owner") or []) + ".", "",
         f"- measured_at_commit: {r['sha']}",
         f"- freeze: {r['frozen']}",
         f"- host: {r['host']}",
         "- plane: committed blobs at measured_at_commit (git grep / cat-file / diff / archive), never the "
         "working tree" + ("; plus the host-state row count named below" if p == "K" else ""),
         f"- produced by: {SELF_CMD} --write {p}",
         f"- claim: {worst(r['parts'])} {parts}", "",
         "## Commands and observed output", "", "| command | observed |", "|---|---|"]
    L += [f"| `{cell(c)}` | {cell(o)} |" for c, o in r["commands"]]
    L += ["", "## Claim parts", "", "| part | outcome | reason |", "|---|---|---|"]
    L += [f"| {k} | {v[0]} | {cell(v[1])} |" for k, v in r["parts"].items()]
    L += ["", "## Aperture", ""] + [f"- {a}" for a in r["aperture"]]
    L += ["", "## Evidence", ""] + r["evidence"]
    L += ["", "## What the owner should do", ""] + [f"- {a}" for a in r["owner_do"]]
    L += ["", "## What this program did not do", ""] + [f"- {a}" for a in r["not_done"]]
    return "\n".join(L).rstrip("\n") + "\n"


def write_handoff(repo, p, text) -> Path:
    path = Path(repo) / HANDOFF_DIR / f"{p}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".md.tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)
    return path


# ------------------------------------------------------------------ contract

LINE1 = re.compile(r"^\[([A-Z])\] -> (\S.*)$")
MEASURED_AT = re.compile(r"^- measured_at_commit: ([0-9a-f]{40})$", re.M)


def contract(repo, p, head):
    """(outcome, reason) for handoffs/<P>.md at HEAD: committed and equal to the working copy (LF), line 1
    `[<P>] -> <frozen owner>`, `[<P>]` named, a frozen owner string verbatim, a commit after the freeze, and a
    measured commit in HEAD's history."""
    rel = HANDOFF_DIR + f"{p}.md"
    ctx, bad = load_ctx(repo, head)
    if ctx is None:
        return tuple(bad)
    owners = list(ctx["pillars"].get(p, {}).get("owner") or [])
    text, why = blob(repo, head, rel)
    if text is None:
        return ("INCONCLUSIVE", f"git failed: {why}") if git_failed(why) else ("FAIL", f"{rel} not committed")
    wt = Path(repo) / rel
    if not wt.is_file() or smd.lf_bytes(wt.read_bytes()).decode("utf-8", "replace") != text:
        return "FAIL", f"{rel} working copy differs from the committed blob"
    first = text.splitlines()[0] if text else ""
    m = LINE1.match(first)
    if not m or m.group(1) != p or m.group(2) not in owners:
        return "FAIL", f"line 1 {first[:80]!r} is not `[{p}] -> <one of {owners}>`"
    if f"[{p}]" not in text or not any(o in text for o in owners):
        return "FAIL", f"{rel} does not name [{p}] and a frozen owner"
    out, why = smd.git_run(repo, "log", "--format=%H", head, "--", rel)
    if out is None:
        return "INCONCLUSIVE", f"git log failed: {why}"
    landed = False
    for c in out.decode().split():
        anc, why = is_ancestor(repo, c, ctx["frozen"])
        if anc is None:
            return "INCONCLUSIVE", f"merge-base failed: {why}"
        if not anc:
            landed = True
            break
    if not landed:
        return "FAIL", f"{rel} has no commit after the freeze {ctx['frozen'][:8]}"
    mm = MEASURED_AT.search(text)
    if not mm:
        return "FAIL", f"{rel} records no measured_at_commit"
    anc, why = is_ancestor(repo, mm.group(1), head)
    if anc is None:
        return "INCONCLUSIVE", f"measured commit {mm.group(1)[:8]} not answerable: {why}"
    if not anc:
        return "FAIL", f"measured commit {mm.group(1)[:8]} is not in HEAD's history"
    return "PASS", f"line 1 `{first}`, landed, measured at {mm.group(1)[:8]}"


def judge(repo, pillars=PILLARS, contract_pillars=PILLARS):
    """{P: {part: [outcome, reason]}} at HEAD: re-measured claims plus the handoff contract."""
    head, why = smd.resolve_commit(repo, "HEAD")
    out = {}
    for p in pillars:
        if head is None:
            out[p] = {"git": ["INCONCLUSIVE", f"HEAD not resolvable: {why}"]}
            continue
        r = measure(repo, p, head)
        parts = dict(r["parts"])
        if p in contract_pillars:
            parts["contract"] = list(contract(repo, p, head))
        out[p] = parts
        out[p]["_info"] = r.get("info", {})
    return out


def fail_set(result) -> set:
    return {(p, k) for p, parts in result.items() for k, v in parts.items() if not k.startswith("_")
            and v[0] != "PASS"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", nargs="+", metavar="P")
    g.add_argument("--measure", metavar="P")
    ap.add_argument("--repo", default=str(REPO))
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    if a.measure or a.write:
        sel = [a.measure] if a.measure else a.write
        bad = [p for p in sel if p not in PILLARS]
        if bad:
            print(f"unknown pillar(s) {bad}; choose from {PILLARS}", file=sys.stderr)
            return 2
    if a.measure:
        r = measure(repo, a.measure)
        r.pop("ctx", None)
        print(json.dumps(r, indent=1, default=str))
        return 0 if worst(r["parts"]) == "PASS" else 1
    if a.write:
        rc = 0
        for p in a.write:
            r = measure(repo, p)
            if "ctx" not in r:
                print(f"HANDOFF_{p} {worst(r['parts'])} not written: {r['parts']}")
                rc = 1
                continue
            path = write_handoff(repo, p, render(r))
            o = worst(r["parts"])
            print(f"HANDOFF_{p} {o} written {path.relative_to(repo).as_posix()} measured_at {r['sha'][:8]}")
            rc = rc if o == "PASS" else 1
        return rc
    res = judge(repo)
    for p, parts in res.items():
        o = worst({k: v for k, v in parts.items() if not k.startswith("_")})
        detail = " ".join(f"{k}={v[0]}" for k, v in parts.items() if not k.startswith("_"))
        extra = ""
        rows = (parts.get("_info") or {}).get("rows")
        if rows:
            extra = f" rows={rows['state']}({rows['reason']})"
        bad = "; ".join(f"{k}: {v[1]}" for k, v in parts.items() if not k.startswith("_") and v[0] != "PASS")
        print(f"HANDOFF_{p} {o} {detail}{extra}" + (f" -- {bad}" if bad else ""))
    total = worst({p: [worst({k: v for k, v in parts.items() if not k.startswith('_')}), ""]
                   for p, parts in res.items()})
    print(f"SKILL_HANDOFFS {total} pillars={len(res)}")
    return 0 if total == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
