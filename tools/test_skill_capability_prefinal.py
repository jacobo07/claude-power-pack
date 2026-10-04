#!/usr/bin/env python
"""test_skill_capability_prefinal.py -- the D-03 pre-final check of PLAN-SKILL-CAPABILITY-PROGRAM.

    python3 tools/test_skill_capability_prefinal.py                   gex44 pre-final check
    python  tools/test_skill_capability_prefinal.py --closeout        pillar N's laptop gate
    python3 tools/test_skill_capability_prefinal.py --write-evidence  gex44 run + its record
    python3 tools/test_skill_capability_prefinal.py --selftest        drives every check red

Phase 9 (closeout) decision D-03 asks, on host gex44, for a check that runs `--pillar <P>`
for every pillar A..M and the wrapper's `--selftest`, prints which pillars are terminal,
and reports N as OPEN (expected), never as PASS. This file is that check. It is NOT the
program's done-gate: `python tools/test_skill_capability_program.py --final` is, and it
runs on the laptop only, because its clause R1 reads the settings file of the host it runs
on. This file never starts the wrapper with `--final` (its single subprocess entry point
refuses that argument) and never writes state.N.

Modes
  default (PF_MODE=gex44)
      V-PF-COMMITTED  the WHOLE working tree is clean, untracked files included, except the
                      hook-written stubs named in HOOK_STUB_PATHS (else INCONCLUSIVE, and the
                      wrapper subprocesses are skipped: they read the working tree, not HEAD,
                      and their gates execute hooks/, skills/, modules/ and more, so a scope of
                      tools/ + the program dir could not see what they run: 09-REVIEW WR-03).
      static checks on COMMITTED blobs (`git show HEAD:<path>`, never the working tree):
                      V-PF-L8 (CE check_ledger final, gates not re-run, must fail ONLY on
                      `L3 N: no terminal disposition`), V-PF-UKDL, V-PF-CBR, V-PF-DELTAS,
                      V-PF-CLOSEOUT-BUNDLE / -DECISIONS / -COMMANDS (format contracts of the
                      closeout artifacts 09-02 and 09-03 write), V-PF-LEDGER-INVARIANT (all
                      but state/reviews/deltas equal to the FROZEN_AT ledger, state.N
                      unchanged), V-PF-UKDL-UNTOUCHED (no commit since the freeze touched
                      vault/knowledge_base/ukdl-universal.md).
      V-PF-NO-FINAL   the real guard refuses `--final`.
      wrapper runs:   V-PF-SELFTEST, V-PF-STATUS (open == ["N"]), V-PF-PILLARS (A..M PASS),
                      V-PF-N-OPEN (`--pillar N` FAILS with exactly the L3 N clause; a PASS
                      on N turns this check red).
      V-PF-DIRTY-SET-STABLE  the dirty set (same whole-tree scope) did not move while the
                      wrapper ran.
  --closeout (PF_MODE=closeout)   the gate state.N cites on the laptop. V-PF-COMMITTED
      narrowed to the three code files it executes, the same static checks without the
      gex44-only V-PF-UKDL-UNTOUCHED, V-PF-LEDGER-INVARIANT with only its state.N clause
      relaxed (every other key, `retained` included, must still equal the FROZEN_AT ledger:
      09-REVIEW WR-01), V-PF-L8 expecting `[]` (state.N committed), and
      V-PF-GEX44-RECORD (the committed gex44 record says PF_VERDICT=PASS at a commit
      reachable from HEAD). It starts no wrapper subprocess and so cannot recurse into
      `--final`. V-PF-CLOSEOUT-DECISIONS reads STATE.md as of the commit that last touched
      LAPTOP-CLOSEOUT.md, so a decision line added to STATE.md later cannot turn it red.
  --write-evidence   runs the gex44 mode and writes
      vault/programs/skill-capability/evidence/pre-final-gex44.md; refuses on a host whose
      name does not contain "gex44".
  --selftest   every check is a pure function; each gets a green control and red mutants.
      Prints PF_SELFTEST=PASS|FAIL kills=K/N.

What it does not prove: anything about the laptop plane (R1, the live hooks, the push), or
that pillar N is done. A gex44 PASS means "every pillar except N is terminal and passes,
and the closeout artifacts have the agreed shape".

Verdict: any FAIL -> FAIL (exit 1); else any INCONCLUSIVE -> INCONCLUSIVE (exit 2); else
PASS (exit 0). INCONCLUSIVE is never PASS.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_skill_capability_program as scp  # noqa: E402  (rebinds the ce globals)

ce = scp.ce
REPO = ce.REPO
SELF_REL = "tools/test_skill_capability_prefinal.py"
WRAPPER_REL = "tools/test_skill_capability_program.py"
PROGRAM_DIR = "vault/programs/skill-capability/"
UKDL_REL = PROGRAM_DIR + "reviews/ukdl.md"
CBR_REL = PROGRAM_DIR + "reviews/cbr.md"
CLOSEOUT_REL = PROGRAM_DIR + "LAPTOP-CLOSEOUT.md"
BUNDLE_REL = PROGRAM_DIR + "owner-bundle.md"
RECORD_REL = PROGRAM_DIR + "evidence/pre-final-gex44.md"
STATE_REL = ".planning/workstreams/skill-capability/STATE.md"
UKDL_UNIVERSAL_REL = "vault/knowledge_base/ukdl-universal.md"
ALL = [chr(c) for c in range(ord("A"), ord("N") + 1)]
CLOSED = ALL[:-1]  # A..M; N is closed on the laptop
N_CLAUSE = "L3 N: no terminal disposition"
CLOSEOUT_ARGV = ["python", SELF_REL, "--closeout"]
CLOSEOUT_ARGV_TEXT = json.dumps(CLOSEOUT_ARGV)
CLOSEOUT_CODE = [SELF_REL, WRAPPER_REL, "tools/test_cognitive_economy_program.py"]
WRAPPER_TIMEOUT_S = 1900
DECISION_RE = re.compile(r"OWNER DECISION|\(decision\)")
PATH_SUFFIX = re.compile(r":\d+(-\d+)?$")
OPEN_LINE = "PF_OPEN=N (expected: state.N and --final are laptop-only)"
# Paths the session hooks write on their own (progress log, per-file doc stubs, GSD state). They are
# the only dirty paths V-PF-COMMITTED tolerates; each is matched exactly or, ending in "/", as a prefix.
# No pillar gate reads them. Anything else dirty, anywhere in the tree, makes the run INCONCLUSIVE.
HOOK_STUB_PATHS = ("vault/progress.md", ".gsd/", "docs/arch/", "docs/changelog/", "docs/constitution/", "docs/prd/")


class GitUnavailable(Exception):
    """git could not answer: the check that needed it is INCONCLUSIVE, never PASS."""


class Inconclusive(Exception):
    """A check could not decide (its input was unreadable)."""


# ---------------------------------------------------------------- committed reads

def _git_bytes(*args) -> subprocess.CompletedProcess:
    if not ce.GIT:
        raise GitUnavailable("git not found")
    try:
        return subprocess.run([ce.GIT, "-C", str(REPO), *args], capture_output=True)
    except OSError as exc:
        raise GitUnavailable(f"git could not start: {exc}") from exc


def head_sha() -> str:
    r = _git_bytes("rev-parse", "--verify", "HEAD^{commit}")
    if r.returncode != 0:
        raise GitUnavailable("HEAD does not resolve")
    return r.stdout.decode().strip()


def blob_at(rev: str, rel: str):
    """Bytes of `rev:rel` when it is a blob, None when the path is absent or not a file."""
    t = _git_bytes("cat-file", "-t", f"{rev}:{rel}")
    if t.returncode != 0:
        if _git_bytes("rev-parse", "--verify", f"{rev}^{{commit}}").returncode != 0:
            raise GitUnavailable(f"revision {rev} does not resolve")
        return None
    if t.stdout.decode().strip() != "blob":
        return None
    r = _git_bytes("cat-file", "blob", f"{rev}:{rel}")
    if r.returncode != 0:
        raise GitUnavailable(f"git cat-file blob {rev}:{rel} failed")
    return r.stdout


def text_at(rev: str, rel: str):
    b = blob_at(rev, rel)
    return None if b is None else b.decode("utf-8", errors="replace")


def _repo_rel(rel: str) -> bool:
    return bool(rel) and not rel.startswith("~") and not Path(rel).is_absolute()


class CommittedResolver(ce.Resolver):
    """ce.Resolver answering from HEAD blobs for repo-relative refs. `~`-prefixed or
    absolute refs (frozen owners on the host, e.g. ~/.claude/settings.json) go to the base
    class. Never runs a gate."""

    def __init__(self):
        self.head = head_sha()

    def path_exists(self, rel: str) -> bool:
        if not _repo_rel(rel):
            return super().path_exists(rel)
        rel = rel.rstrip("/")
        if _git_bytes("cat-file", "-e", f"{self.head}:{rel}").returncode == 0:
            return True
        return False

    def file_sha(self, rel: str):
        if not _repo_rel(rel):
            return super().file_sha(rel)
        b = blob_at(self.head, rel)
        return None if b is None else hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()

    def file_text(self, rel: str) -> str:
        if not _repo_rel(rel):
            return super().file_text(rel)
        return text_at(self.head, rel) or ""

    def frozen_sha(self):
        t = text_at(self.head, ce.FROZEN_AT_REL)
        return t.strip() if t else None

    def frozen_at_commit(self):
        sha = self.frozen_sha()
        if not sha:
            return None
        t = text_at(sha, ce.LEDGER_REL)
        if t is None:
            raise RuntimeError(f"FROZEN_AT names {sha!r} but git cannot show the ledger there")
        return json.loads(t)["frozen"]

    def run_gate(self, argv):
        raise RuntimeError("CommittedResolver never runs gates (static checks only)")


# ---------------------------------------------------------------- pure checks

def _strip_suffix(p: str) -> str:
    return PATH_SUFFIX.sub("", p.strip())


def _path_problems(paths, exists, where) -> list:
    out = []
    for raw in paths:
        p = _strip_suffix(raw)
        if not _repo_rel(p) or ".." in Path(p).parts:
            out.append(f"{where}: {raw!r} is not a repo-relative path")
        elif not exists(p):
            out.append(f"{where}: {p} does not exist at HEAD")
    return out


def judge_l8(failures, mode) -> list:
    """gex44 expects exactly [L3 N] (N open by design); closeout expects [] (state.N set)."""
    want = [N_CLAUSE] if mode == "gex44" else []
    if list(failures) == want:
        return []
    extra = [x for x in failures if x not in want]
    missing = [x for x in want if x not in failures]
    out = []
    if extra:
        out.append(f"check_ledger failures beyond the expected {want}: " + "; ".join(extra))
    if missing:
        out.append(f"expected {missing} absent (state.N written on gex44?)")
    return out or [f"check_ledger returned {failures}, expected {want}"]


def check_ukdl(text, exists) -> list:
    if text is None:
        return [f"{UKDL_REL} missing at HEAD"]
    lines = text.splitlines()
    heads = [(i, re.match(r"^## UKDL-SC-(\d{2}): (\S.*)$", ln)) for i, ln in enumerate(lines)
             if ln.startswith("## UKDL-SC")]
    out = [f"malformed heading line {i + 1}: {lines[i]!r}" for i, m in heads if not m]
    heads = [(i, m) for i, m in heads if m]
    nums = [int(m.group(1)) for _, m in heads]
    if nums != list(range(1, len(nums) + 1)):
        out.append(f"entries must be numbered 01.. with no gaps, got {[f'{n:02d}' for n in nums]}")
    if len(heads) < 6:
        out.append(f"{len(heads)} entries, at least 6 required")
    for k, (i, m) in enumerate(heads):
        end = next((j for j in range(i + 1, len(lines)) if re.match(r"^#{1,2} ", lines[j])), len(lines))
        body = lines[i + 1:end]
        tag = f"UKDL-SC-{m.group(1)}"
        for field in ("- Trap:", "- Rule:", "- Source:"):
            hits = [ln for ln in body if ln.startswith(field)]
            if not hits:
                out.append(f"{tag}: no line starting {field!r}")
            elif field != "- Source:" and not any(ln[len(field):].strip() for ln in hits):
                out.append(f"{tag}: {field!r} line is empty")
        for ln in (x for x in body if x.startswith("- Source:")):
            paths = re.findall(r"`([^`]+)`", ln)
            if not paths:
                out.append(f"{tag}: Source line holds no backticked path")
            out += _path_problems(paths, exists, f"{tag} Source")
    return out


def _cells(line):
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return None
    return [c.strip() for c in s[1:-1].split("|")]


def _plain(cell):
    c = cell.strip()
    return c[1:-1] if len(c) > 1 and c.startswith("`") and c.endswith("`") else c


CBR_HEADER = "| pillar | predicted | terminal | evidence (paths) | what surprised us |"


def check_cbr(text, ledger, exists) -> list:
    if text is None:
        return [f"{CBR_REL} missing at HEAD"]
    lines = text.splitlines()
    try:
        h = lines.index(CBR_HEADER)
    except ValueError:
        return [f"no header line exactly {CBR_HEADER!r}"]
    sep = lines[h + 1] if h + 1 < len(lines) else ""
    if not re.fullmatch(r"\|(\s*:?-+:?\s*\|){5}", sep.strip()):
        return [f"line after the header is not a 5-column separator: {sep!r}"]
    rows = []
    for ln in lines[h + 2:]:
        if not ln.strip().startswith("|"):
            break
        rows.append(ln)
    out = []
    if len(rows) != len(ALL):
        out.append(f"{len(rows)} rows, exactly {len(ALL)} (A..N) required")
    frozen = {p.get("id"): p.get("predicted") for p in (ledger.get("frozen") or {}).get("pillars", [])}
    state = ledger.get("state") or {}
    for k, ln in enumerate(rows):
        c = _cells(ln)
        if c is None or len(c) != 5:
            out.append(f"row {k + 1} does not have exactly 5 cells: {ln!r}")
            continue
        pid, pred, term, ev, surprise = c
        pid = _plain(pid)
        want_pid = ALL[k] if k < len(ALL) else "?"
        if pid != want_pid:
            out.append(f"row {k + 1}: pillar {pid!r}, expected {want_pid!r} (A..N in order)")
            continue
        if _plain(pred) != frozen.get(pid):
            out.append(f"{pid}: predicted {_plain(pred)!r} != frozen {frozen.get(pid)!r}")
        st = state.get(pid) or {}
        want_term = "open" if pid == "N" else st.get("terminal")
        if want_term is None:
            out.append(f"{pid}: state.{pid} has no terminal in the ledger")
        elif _plain(term) != want_term:
            out.append(f"{pid}: terminal {_plain(term)!r} != {want_term!r}")
        paths = re.findall(r"`([^`]+)`", ev)
        if not paths:
            out.append(f"{pid}: evidence cell holds no backticked path")
        out += _path_problems(paths, exists, f"{pid} evidence")
        if pid != "N":
            refs = {e.get("ref") for e in st.get("evidence") or [] if e.get("kind") in ce.FILE_KINDS}
            if not any(_strip_suffix(p) in refs for p in paths):
                out.append(f"{pid}: evidence cites no file ref of state.{pid} in the ledger")
        if not surprise.strip():
            out.append(f"{pid}: 'what surprised us' is empty")
    return out


def check_deltas(ledger, exists) -> list:
    d = ledger.get("deltas")
    if not isinstance(d, dict):
        return ["ledger.deltas is not an object"]
    out, named = [], set()
    for key in ("product", "intelligence"):
        lst = d.get(key)
        if not isinstance(lst, list) or not lst:
            out.append(f"deltas.{key} is empty or not a list")
            continue
        for i, e in enumerate(lst):
            where = f"deltas.{key}[{i}]"
            if not isinstance(e, dict):
                out.append(f"{where} is not an object")
                continue
            pid, change, ev = e.get("pillar"), e.get("change"), e.get("evidence")
            if pid not in ALL:
                out.append(f"{where}: pillar {pid!r} not in A..N")
            else:
                named.add(pid)
            if not isinstance(change, str) or not change.strip():
                out.append(f"{where}: change is empty")
            elif ce.DEFERRAL_PROSE.search(change):
                out.append(f"{where}: change defers in prose: {ce.DEFERRAL_PROSE.search(change).group(0)!r}")
            if not isinstance(ev, list) or not ev or not all(isinstance(p, str) for p in ev):
                out.append(f"{where}: evidence must be a non-empty list of paths")
            else:
                out += _path_problems(ev, exists, f"{where} evidence")
    missing = [p for p in CLOSED if p not in named]
    if missing:
        out.append(f"pillars named by no delta: {missing}")
    return out


def bundle_items(bundle_text) -> list:
    return [ln for ln in (bundle_text or "").splitlines() if re.match(r"^\[[A-N]\] ", ln)]


def check_bundle(bundle_text, closeout_text) -> list:
    if bundle_text is None:
        return [f"{BUNDLE_REL} missing at HEAD"]
    if closeout_text is None:
        return [f"{CLOSEOUT_REL} missing at HEAD"]
    b = bundle_items(bundle_text)
    if not b:
        return ["owner-bundle holds no [X] item line (dead detector)"]
    want = [f"{i}. {x}" for i, x in enumerate(b, 1)]
    got = [ln for ln in closeout_text.splitlines() if re.match(r"^\d+\. \[[A-N]\] ", ln)]
    if got == want:
        return []
    out = [f"{len(got)} numbered bundle lines, {len(want)} expected"] if len(got) != len(want) else []
    for i, (g, w) in enumerate(zip(got, want), 1):
        if g != w:
            out.append(f"line {i} differs from bundle item {i}: {g[:60]!r} vs {w[:60]!r}")
            break
    return out or ["numbered bundle lines differ from the owner-bundle"]


def decision_lines(state_text) -> list:
    return [ln for ln in (state_text or "").splitlines()
            if ln.startswith("- [") and DECISION_RE.search(ln)]


def check_decisions(state_text, closeout_text) -> list:
    if closeout_text is None:
        return [f"{CLOSEOUT_REL} missing at HEAD"]
    found = decision_lines(state_text)
    if not found:
        return ["STATE.md yields no decision line (dead detector)"]
    lines = closeout_text.splitlines()
    sections, cur = [], None
    for ln in lines:
        if ln.startswith("### Q"):
            cur = [ln]
            sections.append(cur)
        elif re.match(r"^#{1,3} ", ln):
            cur = None
        elif cur is not None:
            cur.append(ln)
    out = []
    for d in found:
        pre = d[2:82]
        sec = [s for s in sections if any(pre in x for x in s)]
        if not sec:
            out.append(f"no '### Q' section quotes the STATE decision {pre[:50]!r}")
            continue
        s = sec[0]
        for field in ("Options:", "Recorded pick:"):
            if not any(x.startswith(field) for x in s):
                out.append(f"section {s[0][:40]!r} has no line starting {field!r}")
    return out


def run_decisions(mode, closeout_text, state_at, last_doc_commit) -> list:
    """Amendment W-01: gex44 reads STATE.md at HEAD; closeout reads it as of the commit
    that last touched LAPTOP-CLOSEOUT.md, so a later STATE line cannot turn the gate red."""
    if closeout_text is None:
        return [f"{CLOSEOUT_REL} missing at HEAD"]
    rev = "HEAD" if mode == "gex44" else last_doc_commit
    if not rev:
        raise Inconclusive(f"no commit touches {CLOSEOUT_REL}")
    st = state_at(rev)
    if st is None:
        raise Inconclusive(f"STATE.md unreadable at {rev[:12]}")
    return check_decisions(st, closeout_text)


REQUIRED_COMMAND_TEXT = (
    "python tools/test_skill_capability_program.py --final",
    "CLOSE.md",
    "state.N",
    "mission/skill-capability-run",
)


def check_commands(closeout_text) -> list:
    if closeout_text is None:
        return [f"{CLOSEOUT_REL} missing at HEAD"]
    out = [f"does not contain {s!r}" for s in REQUIRED_COMMAND_TEXT if s not in closeout_text]
    m = re.search(r'\["python", "tools/[^"\]]+", "--closeout"\]', closeout_text)
    if not m:
        return out + [f"does not contain the gate argv {CLOSEOUT_ARGV_TEXT}"]
    argv = json.loads(m.group(0))
    why = ce.gate_argv_problem(argv)
    if why:
        out.append(f"gate argv {m.group(0)} refused by CE: {why}")
    if argv != CLOSEOUT_ARGV:
        out.append(f"gate argv {m.group(0)} is not {CLOSEOUT_ARGV_TEXT}")
    return out


def check_invariant(ledger, frozen_ledger, allow_state_n=False) -> list:
    """Every key but state/reviews/deltas equals its FROZEN_AT copy. state.N must also be
    unchanged unless `allow_state_n` (closeout mode, where state.N is the laptop's own write).
    Relaxing state.N never relaxes the rest: emptying `retained` would turn R1 green while
    deleting the very declaration R1 reads (09-REVIEW WR-01)."""
    out = []
    for k in sorted(set(ledger) | set(frozen_ledger)):
        if k in ("state", "reviews", "deltas"):
            continue
        if json.dumps(ledger.get(k), sort_keys=True) != json.dumps(frozen_ledger.get(k), sort_keys=True):
            out.append(f"ledger key {k!r} differs from its FROZEN_AT copy")
    n_now = (ledger.get("state") or {}).get("N")
    n_then = (frozen_ledger.get("state") or {}).get("N")
    if not allow_state_n and json.dumps(n_now, sort_keys=True) != json.dumps(n_then, sort_keys=True):
        out.append("state.N differs from its FROZEN_AT copy (state.N is laptop-only)")
    return out


def judge_untouched(log_text) -> list:
    shas = (log_text or "").split()
    return [f"{len(shas)} commit(s) since the freeze touch {UKDL_UNIVERSAL_REL}: {shas[:3]}"] if shas else []


def judge_record(text, reachable) -> list:
    if text is None:
        return [f"{RECORD_REL} missing at HEAD"]
    lines = [ln.rstrip() for ln in text.splitlines()]
    out = []
    if not any(re.fullmatch(r"host: gex44 \(hostname [^)]*gex44[^)]*\)", ln) for ln in lines):
        out.append("no line 'host: gex44 (hostname <...gex44...>)'")
    cm = [re.fullmatch(r"commit: ([0-9a-f]{40})", ln) for ln in lines]
    cm = [m.group(1) for m in cm if m]
    if not cm:
        out.append("no line 'commit: <40-hex>'")
    elif not reachable(cm[0]):
        out.append(f"recorded commit {cm[0][:12]} is not reachable from HEAD")
    if not any(ln.startswith("date: ") and len(ln) > 6 for ln in lines):
        out.append("no 'date:' line")
    if "command: python3 tools/test_skill_capability_prefinal.py --write-evidence" not in lines:
        out.append("no 'command:' line naming --write-evidence")
    if "PF_MODE=gex44" not in lines:
        out.append("no PF_MODE=gex44 line")
    if f"PF_TERMINAL={','.join(CLOSED)}" not in lines:
        out.append(f"no PF_TERMINAL={','.join(CLOSED)} line")
    if OPEN_LINE not in lines:
        out.append("no PF_OPEN=N (expected ...) line")
    if any("CEP_PILLAR_N=PASS" in ln for ln in lines):
        out.append("the record shows N reported PASS")
    last = next((ln for ln in reversed(lines) if ln.strip()), "")
    if last != "PF_VERDICT=PASS":
        out.append(f"record does not end in PF_VERDICT=PASS (last line {last!r})")
    return out


def dirty_paths(porcelain_text, own_outputs) -> list:
    out = []
    for ln in (porcelain_text or "").splitlines():
        if len(ln) < 4:
            continue
        p = ln[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        p = p.strip().strip('"')
        if p not in own_outputs:
            out.append(p)
    return out


def outside_hook_stubs(paths) -> list:
    """`paths` minus the HOOK_STUB_PATHS entries (exact, or prefix for a "/"-ending entry)."""
    return [p for p in paths
            if not any(p == s or (s.endswith("/") and p.startswith(s)) for s in HOOK_STUB_PATHS)]


def committed_scope_dirty(porcelain_text) -> list:
    """V-PF-COMMITTED's dirty set: every dirty or untracked path in the whole tree except
    the gex44 record (this file's own output) and the hook-written stubs."""
    return outside_hook_stubs(dirty_paths(porcelain_text, {RECORD_REL}))


def judge_stable(before, after) -> list:
    """The wrapper reads the working tree: if the dirty set moved while it ran, its
    verdicts describe a tree nobody can name (INCONCLUSIVE, never PASS)."""
    return [] if list(before) == list(after) else [f"dirty set moved during the run: {list(after)[:5]}"]


# ---------------------------------------------------------------- wrapper subprocess

def _wrapper_args_ok(args) -> list:
    """The only argument shapes the wrapper may be started with. `--final` (and every
    argparse abbreviation of it) is refused: --final and state.N are laptop-only."""
    args = [str(a) for a in args]
    for a in args:
        head = a.split("=", 1)[0]
        if len(head) >= 3 and "--final".startswith(head):
            raise ValueError(f"refused: {a!r} would start the wrapper's --final (laptop-only)")
    if args in (["--status"], ["--selftest"]) or (len(args) == 2 and args[0] == "--pillar" and args[1] in ALL):
        return args
    raise ValueError(f"refused: wrapper arguments {args} are not --status / --selftest / --pillar <A-N>")


def run_wrapper(args, timeout=WRAPPER_TIMEOUT_S):
    """The single subprocess entry point. (rc, stdout + stderr); a timeout is rc 124."""
    args = _wrapper_args_ok(args)
    try:
        r = subprocess.run([sys.executable, WRAPPER_REL, *args], cwd=str(REPO), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"
    return r.returncode, r.stdout + r.stderr


def _fail_lines(out):
    return [ln.strip()[len("FAIL "):] for ln in out.splitlines() if ln.strip().startswith("FAIL ")]


def judge_pillars(results) -> list:
    out = []
    for p in CLOSED:
        if p not in results:
            out.append(f"pillar {p}: no result")
            continue
        rc, txt = results[p]
        if rc != 0 or f"CEP_PILLAR_{p}=PASS" not in txt.splitlines():
            fl = _fail_lines(txt)
            out.append(f"pillar {p}: rc {rc}" + (f", {fl[0][:120]}" if fl else ""))
    return out


def judge_n_open(rc, out) -> list:
    lines = out.splitlines()
    if "CEP_PILLAR_N=PASS" in lines or rc == 0:
        return [f"N reported PASS (rc {rc}): state.N must stay open on gex44"]
    probs = []
    if rc != 1:
        probs.append(f"--pillar N rc {rc}, expected 1")
    if "CEP_PILLAR_N=FAIL" not in lines:
        probs.append("no CEP_PILLAR_N=FAIL line")
    fl = _fail_lines(out)
    if fl != [N_CLAUSE]:
        probs.append(f"N must fail on exactly {N_CLAUSE!r}, failed on {fl[:3]}")
    return probs


def judge_selftest(rc, out) -> list:
    if rc == 0 and "SCP_SELFTEST=PASS" in out.splitlines():
        return []
    return [f"wrapper --selftest rc {rc}" + ("" if "SCP_SELFTEST=PASS" in out else ", no SCP_SELFTEST=PASS")]


def parse_status(out):
    i, j = out.find("{"), out.rfind("}")
    if i < 0 or j < i:
        raise ValueError("no JSON object in --status output")
    return json.loads(out[i:j + 1])


def judge_status(rc, out) -> list:
    try:
        st = parse_status(out)
    except ValueError as exc:
        return [f"--status output unparseable: {exc}"]
    probs = []
    if rc != 0:
        probs.append(f"--status rc {rc}")
    if st.get("open") != ["N"]:
        probs.append(f"open {st.get('open')}, expected ['N']")
    if st.get("closed") != CLOSED:
        probs.append(f"closed {st.get('closed')}, expected A..M")
    if st.get("violations"):
        probs.append(f"violations {st.get('violations')[:3]}")
    return probs


# ---------------------------------------------------------------- report

class Report:
    def __init__(self, sink=None):
        self.rows = []
        self.sink = sink

    def line(self, s=""):
        print(s, flush=True)
        if self.sink is not None:
            self.sink.append(s)

    def add(self, name, status, detail):
        self.rows.append((name, status))
        if status == "ok":
            self.line(f"  ok   {name} ({detail})")
        else:
            self.line(f"  {status} {name}: {detail}")

    def judge(self, name, fn, ok_detail):
        """fn() -> list of failures. GitUnavailable / Inconclusive -> INCONCLUSIVE."""
        try:
            probs = fn()
        except (GitUnavailable, Inconclusive) as exc:
            self.add(name, "INCONCLUSIVE", str(exc))
            return None
        if probs:
            self.add(name, "FAIL", "; ".join(probs))
        else:
            self.add(name, "ok", ok_detail)
        return probs

    def finish(self):
        bad = [n for n, s in self.rows if s != "ok"]
        okc = sum(1 for _, s in self.rows if s == "ok")
        verdict = ("FAIL" if any(s == "FAIL" for _, s in self.rows)
                   else "INCONCLUSIVE" if bad else "PASS")
        self.line(f"PF_PASS={okc}/{len(self.rows)}")
        self.line(f"PF_FAILED={','.join(bad) if bad else '-'}")
        self.line(f"PF_VERDICT={verdict}")
        return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}[verdict]


def _porcelain(paths=()):
    """`git status --porcelain -uall`, limited to `paths` when given, else the whole tree."""
    r = _git_bytes("status", "--porcelain", "--untracked-files=all", "--", *paths)
    if r.returncode != 0:
        raise GitUnavailable("git status failed")
    return r.stdout.decode("utf-8", errors="replace")


def _static_checks(rep, mode, res):
    """The checks on committed blobs, common to both modes."""
    head = res.head
    try:
        led = json.loads(text_at(head, ce.LEDGER_REL) or "null")
    except json.JSONDecodeError as exc:
        led = None
        rep.line(f"  (ledger at HEAD is not JSON: {exc})")
    if not isinstance(led, dict):
        for n in ("V-PF-L8", "V-PF-CBR", "V-PF-DELTAS"):
            rep.add(n, "FAIL", f"{ce.LEDGER_REL} missing or unreadable at HEAD")
    else:
        rep.judge("V-PF-L8", lambda: judge_l8(ce.check_ledger(led, res, final=True, run_gates=False), mode),
                  f"check_ledger(final, gates not re-run) == {[N_CLAUSE] if mode == 'gex44' else []}")
    rep.judge("V-PF-UKDL", lambda: check_ukdl(text_at(head, UKDL_REL), res.path_exists),
              f"{UKDL_REL} entries, fields and sources hold")
    if isinstance(led, dict):
        rep.judge("V-PF-CBR", lambda: check_cbr(text_at(head, CBR_REL), led, res.path_exists),
                  "14 rows A..N match the ledger, evidence exists")
        rep.judge("V-PF-DELTAS", lambda: check_deltas(led, res.path_exists),
                  f"product {len((led.get('deltas') or {}).get('product') or [])}, "
                  f"intelligence {len((led.get('deltas') or {}).get('intelligence') or [])}, A..M named")
    closeout = text_at(head, CLOSEOUT_REL)
    rep.judge("V-PF-CLOSEOUT-BUNDLE", lambda: check_bundle(text_at(head, BUNDLE_REL), closeout),
              f"{len(bundle_items(text_at(head, BUNDLE_REL)))} owner-bundle lines numbered in order")

    def decisions():
        last = None
        if mode != "gex44":
            r = _git_bytes("log", "-1", "--format=%H", "HEAD", "--", CLOSEOUT_REL)
            if r.returncode != 0:
                raise Inconclusive(f"git log of {CLOSEOUT_REL} failed")
            last = r.stdout.decode().strip() or None
        return run_decisions(mode, closeout, lambda rev: text_at(rev, STATE_REL), last)
    rep.judge("V-PF-CLOSEOUT-DECISIONS", decisions,
              "every STATE decision line has a ### Q section with Options: and Recorded pick:")
    rep.judge("V-PF-CLOSEOUT-COMMANDS", lambda: check_commands(closeout),
              "--final, CLOSE.md, state.N, run branch and the --closeout gate argv present")
    return led


def _judge_invariant(rep, res, led, mode):
    """V-PF-LEDGER-INVARIANT in both modes; closeout relaxes only the state.N clause."""
    def invariant():
        fa = res.frozen_sha()
        if not fa:
            raise Inconclusive("FROZEN_AT missing at HEAD")
        t = text_at(fa, ce.LEDGER_REL)
        if t is None:
            raise Inconclusive(f"ledger unreadable at FROZEN_AT {fa[:12]}")
        if not isinstance(led, dict):
            return ["ledger unreadable at HEAD"]
        return check_invariant(led, json.loads(t), allow_state_n=(mode == "closeout"))
    rep.judge("V-PF-LEDGER-INVARIANT", invariant,
              "all keys but state/reviews/deltas" + (" (state.N is the laptop's write)" if mode == "closeout"
                                                     else " and state.N") + " equal the FROZEN_AT ledger")


def run_gex44(rep) -> int:
    rep.line("PF_MODE=gex44")
    try:
        res = CommittedResolver()
    except GitUnavailable as exc:
        rep.add("V-PF-COMMITTED", "INCONCLUSIVE", str(exc))
        return rep.finish()
    rep.line(f"PF_HEAD={res.head}")
    try:
        before = committed_scope_dirty(_porcelain())
        clean = not before
        rep.add("V-PF-COMMITTED", "ok" if clean else "INCONCLUSIVE",
                "whole working tree clean except the hook-written stubs" if clean
                else f"dirty paths {before[:5]}; the wrapper reads the working tree")
    except GitUnavailable as exc:
        before, clean = None, False
        rep.add("V-PF-COMMITTED", "INCONCLUSIVE", str(exc))

    led = _static_checks(rep, "gex44", res)
    _judge_invariant(rep, res, led, "gex44")

    def untouched():
        fa = res.frozen_sha()
        if not fa:
            raise Inconclusive("FROZEN_AT missing at HEAD")
        r = _git_bytes("log", "--format=%H", f"{fa}..HEAD", "--", UKDL_UNIVERSAL_REL)
        if r.returncode != 0:
            raise Inconclusive("git log failed")
        return judge_untouched(r.stdout.decode())
    rep.judge("V-PF-UKDL-UNTOUCHED", untouched, f"no commit since the freeze touches {UKDL_UNIVERSAL_REL}")

    def no_final():
        try:
            run_wrapper(["--final"])
        except ValueError:
            return []
        return ["run_wrapper(['--final']) did not refuse"]
    rep.judge("V-PF-NO-FINAL", no_final, "run_wrapper(['--final']) raised ValueError; no process started")

    terminal, open_line = "UNMEASURED", "PF_OPEN=UNMEASURED"
    if not clean:
        for n in ("V-PF-SELFTEST", "V-PF-STATUS", "V-PF-PILLARS", "V-PF-N-OPEN"):
            rep.add(n, "INCONCLUSIVE", "skipped: V-PF-COMMITTED is not clean")
    else:
        t0 = time.monotonic()
        rc, out = run_wrapper(["--selftest"])
        rep.judge("V-PF-SELFTEST", lambda: judge_selftest(rc, out),
                  f"SCP_SELFTEST=PASS rc 0, {time.monotonic() - t0:.1f}s")
        rc, out = run_wrapper(["--status"])
        rep.judge("V-PF-STATUS", lambda: judge_status(rc, out), "open ['N'], closed A..M, violations []")
        try:
            st = parse_status(out)
            terminal = ",".join(st.get("closed") or []) or "-"
            open_line = OPEN_LINE if st.get("open") == ["N"] else f"PF_OPEN={','.join(st.get('open') or [])} (UNEXPECTED)"
        except ValueError:
            pass
        results, t0 = {}, time.monotonic()
        for p in CLOSED:
            results[p] = run_wrapper(["--pillar", p])
        rep.judge("V-PF-PILLARS", lambda: judge_pillars(results),
                  f"--pillar A..M each rc 0 CEP_PILLAR_<P>=PASS, {time.monotonic() - t0:.1f}s")
        rc, out = run_wrapper(["--pillar", "N"])
        rep.judge("V-PF-N-OPEN", lambda: judge_n_open(rc, out),
                  f"--pillar N rc 1, CEP_PILLAR_N=FAIL on exactly {N_CLAUSE!r}")
        try:
            moved = judge_stable(before, committed_scope_dirty(_porcelain()))
            rep.add("V-PF-DIRTY-SET-STABLE", "INCONCLUSIVE" if moved else "ok",
                    "; ".join(moved) or "dirty set unchanged while the wrapper ran")
        except GitUnavailable as exc:
            rep.add("V-PF-DIRTY-SET-STABLE", "INCONCLUSIVE", str(exc))
    rep.line(f"PF_TERMINAL={terminal}")
    rep.line(open_line)
    return rep.finish()


def run_closeout(rep) -> int:
    rep.line("PF_MODE=closeout")
    try:
        res = CommittedResolver()
        rep.line(f"PF_HEAD={res.head}")
        dirty = dirty_paths(_porcelain(CLOSEOUT_CODE), set())
        rep.add("V-PF-COMMITTED", "ok" if not dirty else "INCONCLUSIVE",
                "the three executed code files are clean" if not dirty else f"dirty: {dirty}")
    except GitUnavailable as exc:
        rep.add("V-PF-COMMITTED", "INCONCLUSIVE", str(exc))
        return rep.finish()
    led = _static_checks(rep, "closeout", res)
    _judge_invariant(rep, res, led, "closeout")

    def reachable(sha):
        return _git_bytes("merge-base", "--is-ancestor", sha, res.head).returncode == 0
    rep.judge("V-PF-GEX44-RECORD", lambda: judge_record(text_at(res.head, RECORD_REL), reachable),
              f"{RECORD_REL} at HEAD: gex44, PF_VERDICT=PASS, commit reachable")
    return rep.finish()


def write_evidence() -> int:
    host = socket.gethostname()
    if "gex44" not in host:
        print(f"PF_WRITE_EVIDENCE=REFUSED hostname {host!r} does not contain 'gex44'")
        return 2
    try:
        head = head_sha()
    except GitUnavailable as exc:
        print(f"PF_WRITE_EVIDENCE=REFUSED {exc}")
        return 2
    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    buf = []
    rc = run_gex44(Report(sink=buf))
    text = "\n".join([
        "# Skill / Capability Program -- pre-final check on gex44 (D-03)",
        "",
        f"host: gex44 (hostname {host})",
        f"commit: {head}",
        f"date: {date}",
        "command: python3 tools/test_skill_capability_prefinal.py --write-evidence",
        "",
        *buf,
    ]) + "\n"
    (REPO / RECORD_REL).parent.mkdir(parents=True, exist_ok=True)
    (REPO / RECORD_REL).write_text(text, encoding="utf-8", newline="\n")
    print(f"PF_WRITE_EVIDENCE=WROTE {RECORD_REL} rc {rc}")
    return rc


# ---------------------------------------------------------------- selftest

def _fixture():
    led = {
        "schema": 1, "program": "sc",
        "frozen": {"pillars": [{"id": p, "predicted": "IMPLEMENTED_AND_VERIFIED", "owner": []} for p in ALL]},
        "state": {p: {"terminal": "IMPLEMENTED_AND_VERIFIED", "reason": "r",
                      "evidence": [{"kind": "gate", "argv": ["python", "tools/x.py"]},
                                   {"kind": "prg", "ref": f"ev/{p}.md", "sha256": "0" * 64}]}
                  for p in CLOSED},
        "retained": {"settings": {"file": "~/.claude/settings.json",
                                  "keys": [{"pointer": "/env/CLAUDE_DOCTRINE_CARDS", "value": "deny"}]}},
        "reviews": {"ukdl": {"file": "r/ukdl.md"}, "cbr": {"file": "r/cbr.md"}},
        "deltas": {"product": [{"pillar": p, "change": f"product change {p}", "evidence": [f"ev/{p}.md:3"]}
                               for p in CLOSED[:7]],
                   "intelligence": [{"pillar": p, "change": f"rule learned {p}", "evidence": [f"ev/{p}.md"]}
                                    for p in CLOSED[7:]]},
    }
    led["state"]["N"] = {"terminal": None, "evidence": [], "savings": []}
    frozen_led = copy.deepcopy(led)
    frozen_led["state"] = {p: {"terminal": None, "evidence": [], "savings": []} for p in ALL}
    frozen_led["reviews"] = {"ukdl": None, "cbr": None}
    frozen_led["deltas"] = {"product": [], "intelligence": []}
    exists_set = {f"ev/{p}.md" for p in ALL} | {"src/x.py", "src/y.md"}
    ukdl = "# UKDL candidates\n\n" + "\n".join(
        f"## UKDL-SC-{i:02d}: trap {i}\n- Trap: symptom {i}\n- Rule: do {i}\n- Source: `src/x.py:{i}-{i + 2}` and `src/y.md`\n"
        for i in range(1, 7))
    rows = []
    for p in ALL:
        term = "open" if p == "N" else "IMPLEMENTED_AND_VERIFIED"
        rows.append(f"| {p} | IMPLEMENTED_AND_VERIFIED | {term} | `ev/{p}.md` `src/x.py:4` | surprise {p} |")
    cbr = "# CBR\n\n" + CBR_HEADER + "\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n\nafter\n"
    bundle = "# Owner bundle\nOne line per item.\n\n[A] (host: laptop) do a\n[B] do b `x`\n[N] push it\n"
    state_lines = ["- [Run, epoch 2]: push refused by a hook. OWNER DECISION NEEDED -- push or fetch the run branch now",
                   "- [Phase 8, epoch 4]: IN-04 NOT fixed (decision): seven invalid frontmatters stay as they are"]
    state = "# STATE\n\n## Decisions\n" + "\n".join(state_lines) + "\n- [Phase 5]: ordinary note\n"
    q = "\n".join(f"### Q{i}: question {i}\nSource (STATE.md): \"{ln[2:82]}\"\nOptions: (a) x, (b) y\nRecorded pick: (a)\n"
                  for i, ln in enumerate(state_lines, 1))
    closeout = ("# Laptop closeout\n\nfetch `mission/skill-capability-run`\n\n## Owner bundle, in order\n"
                + "\n".join(f"{i}. {b}" for i, b in enumerate(bundle_items(bundle), 1))
                + "\n\n## Owner decisions\n" + q
                + "\n## Close pillar N (laptop)\n1. write state.N with gate "
                + CLOSEOUT_ARGV_TEXT + "\n2. `python tools/test_skill_capability_program.py --final`\n3. write CLOSE.md\n")
    record = "\n".join(["# rec", "host: gex44 (hostname kobicraft-gex44)", "commit: " + "a" * 40,
                        "date: 2026-10-04T00:00:00Z",
                        "command: python3 tools/test_skill_capability_prefinal.py --write-evidence", "",
                        "PF_MODE=gex44", "  ok   V-PF-PILLARS (x)", f"PF_TERMINAL={','.join(CLOSED)}", OPEN_LINE,
                        "PF_PASS=16/16", "PF_FAILED=-", "PF_VERDICT=PASS", ""])
    return dict(led=led, frozen_led=frozen_led, exists=exists_set.__contains__, ukdl=ukdl, cbr=cbr,
                bundle=bundle, state=state, state_lines=state_lines, closeout=closeout, record=record)


def selftest() -> bool:
    F = _fixture()
    ok, kills, total, greens = True, 0, 0, 0

    def green(name, probs):
        nonlocal ok, greens
        if probs:
            ok = False
            print(f"  FAIL V-PF-SELF-GREEN {name}: {probs[:2]}")
        else:
            greens += 1
            print(f"  ok   V-PF-SELF-GREEN {name}")

    def mutant(name, fn, expect=None):
        """Killed only when the check reports a problem; with `expect`, only when one of
        the problems names it (the clause under test, not some other clause, said no)."""
        nonlocal ok, kills, total
        total += 1
        try:
            probs = fn()
            killed = bool(probs)
        except (ValueError, Inconclusive) as exc:
            probs, killed = [f"raised {type(exc).__name__}: {exc}"], True
        if killed and expect is not None and not any(expect in x for x in probs):
            probs, killed = [f"red, but not on {expect!r}: {probs[:2]}"], False
        if killed:
            kills += 1
            print(f"  ok   V-PF-SELF-MUT {name} killed ({probs[0][:90]})")
        else:
            ok = False
            print(f"  FAIL V-PF-SELF-MUT {name} SURVIVED")

    def led_with(fn):
        led = copy.deepcopy(F["led"])
        fn(led)
        return led

    ex = F["exists"]
    # ---- green controls (one consistent fixture)
    green("L8 gex44", judge_l8([N_CLAUSE], "gex44"))
    green("L8 closeout", judge_l8([], "closeout"))
    green("UKDL", check_ukdl(F["ukdl"], ex))
    green("CBR", check_cbr(F["cbr"], F["led"], ex))
    green("DELTAS", check_deltas(F["led"], ex))
    green("BUNDLE", check_bundle(F["bundle"], F["closeout"]))
    green("DECISIONS", check_decisions(F["state"], F["closeout"]))
    green("COMMANDS", check_commands(F["closeout"]))
    green("INVARIANT", check_invariant(F["led"], F["frozen_led"]))
    green("UNTOUCHED", judge_untouched(""))
    green("RECORD", judge_record(F["record"], lambda s: True))
    green("COMMITTED own output only", dirty_paths(f"?? {RECORD_REL}\n", {RECORD_REL}))
    green("COMMITTED empty", dirty_paths("", {RECORD_REL}))
    # W-01: a decision line added to STATE.md in a LATER commit leaves closeout green
    later = F["state"] + "- [Phase 9, epoch 5]: OWNER DECISION NEEDED -- a brand new question added after the doc\n"
    state_at = {"HEAD": later, "c0": F["state"]}.get
    green("DECISIONS closeout reads STATE at the doc commit", run_decisions("closeout", F["closeout"], state_at, "c0"))

    # ---- L8
    mutant("L8 extra L8 failure (gex44)", lambda: judge_l8([N_CLAUSE, "L8 review ukdl: missing"], "gex44"))
    mutant("L8 state.N written on gex44", lambda: judge_l8([], "gex44"))
    mutant("L8 closeout with N open", lambda: judge_l8([N_CLAUSE], "closeout"))
    # ---- UKDL
    five = F["ukdl"].split("## UKDL-SC-06")[0]
    mutant("UKDL 5 entries", lambda: check_ukdl(five, ex))
    mutant("UKDL entry without Rule", lambda: check_ukdl(F["ukdl"].replace("- Rule: do 3\n", "", 1), ex))
    mutant("UKDL Source path absent", lambda: check_ukdl(F["ukdl"].replace("`src/y.md`", "`src/gone.md`", 1), ex))
    mutant("UKDL numbering gap", lambda: check_ukdl(F["ukdl"].replace("UKDL-SC-02:", "UKDL-SC-03:", 1)
                                                  .replace("UKDL-SC-03: trap 3", "UKDL-SC-04: trap 3", 1)
                                                  .replace("UKDL-SC-04: trap 4", "UKDL-SC-05: trap 4", 1)
                                                  .replace("UKDL-SC-05: trap 5", "UKDL-SC-06: trap 5", 1)
                                                  .replace("UKDL-SC-06: trap 6", "UKDL-SC-07: trap 6", 1), ex))
    # ---- CBR
    mutant("CBR terminal swapped", lambda: check_cbr(F["cbr"].replace(
        "| C | IMPLEMENTED_AND_VERIFIED | IMPLEMENTED_AND_VERIFIED", "| C | IMPLEMENTED_AND_VERIFIED | DEFERRED_STRONGER_OWNER"),
        F["led"], ex))
    mutant("CBR row M missing", lambda: check_cbr("\n".join(x for x in F["cbr"].splitlines() if not x.startswith("| M |")),
                                                F["led"], ex))
    mutant("CBR N row reads a terminal", lambda: check_cbr(F["cbr"].replace(
        "| N | IMPLEMENTED_AND_VERIFIED | open", "| N | IMPLEMENTED_AND_VERIFIED | IMPLEMENTED_AND_VERIFIED"), F["led"], ex))
    mutant("CBR A..M row with no ledger ref", lambda: check_cbr(F["cbr"].replace("| `ev/D.md` `src/x.py:4` |",
                                                                              "| `src/x.py:4` |"), F["led"], ex))
    # ---- DELTAS
    mutant("DELTAS evidence path absent", lambda: check_deltas(led_with(
        lambda l: l["deltas"]["product"][0].__setitem__("evidence", ["ev/gone.md"])), ex))
    mutant("DELTAS pillar D named nowhere", lambda: check_deltas(led_with(
        lambda l: l["deltas"]["product"].__setitem__(3, dict(l["deltas"]["product"][3], pillar="N"))), ex))
    mutant("DELTAS bare string entry", lambda: check_deltas(led_with(
        lambda l: l["deltas"]["product"].append("just text")), ex))
    mutant("DELTAS change says later", lambda: check_deltas(led_with(
        lambda l: l["deltas"]["intelligence"][0].__setitem__("change", "we will fix this later")), ex))
    mutant("DELTAS intelligence empty", lambda: check_deltas(led_with(
        lambda l: l["deltas"].__setitem__("intelligence", [])), ex))
    # ---- BUNDLE
    cl = F["closeout"]
    items = [f"{i}. {b}" for i, b in enumerate(bundle_items(F["bundle"]), 1)]
    mutant("BUNDLE two lines swapped", lambda: check_bundle(F["bundle"], cl.replace(items[0], "@@").replace(
        items[1], items[0].replace("1. ", "2. ", 1)).replace("@@", items[1].replace("2. ", "1. ", 1))))
    mutant("BUNDLE last line dropped", lambda: check_bundle(F["bundle"], cl.replace(items[-1] + "\n", "")))
    mutant("BUNDLE one character changed", lambda: check_bundle(F["bundle"], cl.replace("do b", "do c", 1)))
    mutant("BUNDLE extra numbered line", lambda: check_bundle(F["bundle"], cl.replace(
        items[-1], items[-1] + "\n4. [M] invented item")))
    # ---- DECISIONS
    pre0 = F["state_lines"][0][2:82]
    mutant("DECISIONS prefix missing", lambda: check_decisions(F["state"], cl.replace(pre0, "paraphrased", 1)))
    mutant("DECISIONS section without Recorded pick", lambda: check_decisions(
        F["state"], cl.replace("Recorded pick: (a)\n", "", 1)))
    mutant("DECISIONS dead detector (zero lines)", lambda: check_decisions("# STATE\n- [x]: nothing\n", cl))
    mutant("DECISIONS line at the doc commit missing from the doc", lambda: run_decisions(
        "closeout", cl.replace(pre0, "paraphrased", 1), state_at, "c0"))
    mutant("DECISIONS gex44 reads HEAD (later line uncovered)", lambda: run_decisions(
        "gex44", cl, state_at, "c0"))
    mutant("DECISIONS closeout with no doc commit", lambda: run_decisions("closeout", cl, state_at, None))
    # ---- COMMANDS
    mutant("COMMANDS --final line removed", lambda: check_commands(
        cl.replace("python tools/test_skill_capability_program.py --final", "run the gate")))
    mutant("COMMANDS argv names the done-gate", lambda: check_commands(
        cl.replace(CLOSEOUT_ARGV_TEXT, json.dumps(["python", WRAPPER_REL, "--closeout"]))))
    # ---- INVARIANT / UNTOUCHED / RECORD / COMMITTED
    mutant("INVARIANT retained mutated", lambda: check_invariant(led_with(
        lambda l: l["retained"]["settings"]["keys"].append({"pointer": "/x"})), F["frozen_led"]))
    mutant("INVARIANT state.N given a terminal", lambda: check_invariant(led_with(
        lambda l: l["state"]["N"].__setitem__("terminal", "IMPLEMENTED_AND_VERIFIED")), F["frozen_led"]))
    n_set = led_with(lambda l: l["state"]["N"].__setitem__("terminal", "IMPLEMENTED_AND_VERIFIED"))
    green("INVARIANT closeout with state.N written", check_invariant(n_set, F["frozen_led"], allow_state_n=True))
    mutant("INVARIANT closeout: retained emptied (WR-01)", lambda: check_invariant(led_with(
        lambda l: (l["state"]["N"].__setitem__("terminal", "IMPLEMENTED_AND_VERIFIED"),
                   l["retained"]["settings"].__setitem__("keys", []))), F["frozen_led"], allow_state_n=True),
           expect="'retained' differs")
    mutant("UNTOUCHED commit touches ukdl-universal", lambda: judge_untouched("b" * 40 + "\n"))
    mutant("RECORD PF_VERDICT=FAIL", lambda: judge_record(F["record"].replace("PF_VERDICT=PASS", "PF_VERDICT=FAIL"),
                                                          lambda s: True))
    mutant("RECORD commit unreachable", lambda: judge_record(F["record"], lambda s: False))
    mutant("COMMITTED ledger dirty", lambda: dirty_paths(f" M {PROGRAM_DIR}ledger.json\n", {RECORD_REL}))
    stubs = " M vault/progress.md\n?? .gsd/state.json\n?? docs/arch/tools__x.py.md\n?? docs/prd/tools__x.py.md\n"
    green("COMMITTED whole tree, hook stubs only", committed_scope_dirty(stubs + f"?? {RECORD_REL}\n"))
    mutant("COMMITTED a dirty hook outside tools/ (WR-03)", lambda: committed_scope_dirty(
        stubs + " M hooks/doctrine_cards.js\n"), expect="hooks/doctrine_cards.js")
    mutant("COMMITTED an untracked skill file (WR-03)", lambda: committed_scope_dirty(
        stubs + "?? skills/new-skill/SKILL.md\n"), expect="skills/new-skill/SKILL.md")
    mutant("COMMITTED a stub-looking path outside the list", lambda: committed_scope_dirty(
        " M docs/INSTALL.md\n"), expect="docs/INSTALL.md")
    green("DIRTY-SET-STABLE", judge_stable([], []))
    mutant("DIRTY-SET-STABLE a path turned dirty during the run",
           lambda: judge_stable([], [f"{PROGRAM_DIR}evidence/D-live-gex44.json"]))
    # ---- wrapper judges (fixture outputs, no subprocess)
    good = {p: (0, f"CEP_PILLAR_{p}=PASS\n") for p in CLOSED}
    green("PILLARS", judge_pillars(good))
    mutant("PILLARS C fails", lambda: judge_pillars(dict(good, C=(1, "  FAIL L5 C: gate rc 1\nCEP_PILLAR_C=FAIL\n"))))
    mutant("PILLARS one missing", lambda: judge_pillars({p: v for p, v in good.items() if p != "K"}))
    n_good = f"  FAIL {N_CLAUSE}\nCEP_PILLAR_N=FAIL\n"
    green("N-OPEN", judge_n_open(1, n_good))
    mutant("N-OPEN N reported PASS", lambda: judge_n_open(0, "CEP_PILLAR_N=PASS\n"))
    mutant("N-OPEN fails on L2 instead", lambda: judge_n_open(
        1, "  FAIL L2 frozen pre-registration differs from its copy at FROZEN_AT\nCEP_PILLAR_N=FAIL\n"))
    green("SELFTEST", judge_selftest(0, "...\nSCP_SELFTEST=PASS\n"))
    mutant("SELFTEST rc 1 no PASS", lambda: judge_selftest(1, "  FAIL x\nSCP_SELFTEST=FAIL\n"))
    st_good = json.dumps({"open": ["N"], "closed": CLOSED, "violations": []}, indent=1)
    green("STATUS", judge_status(0, st_good))
    mutant("STATUS open E and N", lambda: judge_status(0, json.dumps({"open": ["E", "N"], "closed": CLOSED[:4] + CLOSED[5:],
                                                                       "violations": []})))
    mutant("STATUS violations", lambda: judge_status(1, json.dumps({"open": ["N"], "closed": CLOSED,
                                                                    "violations": ["L4 C: x"]})))
    mutant("STATUS unparseable", lambda: judge_status(0, "Traceback (most recent call last):\n"))
    # ---- one red mutant per clause (09-REVIEW WR-04): each must be refused by ITS clause,
    # named by `expect`, so deleting that one clause leaves this mutant alive and the selftest red.
    rec = F["record"]
    yes = lambda s: True  # noqa: E731
    mutant("RECORD host line removed", lambda: judge_record(
        rec.replace("host: gex44 (hostname kobicraft-gex44)\n", ""), yes), expect="host: gex44")
    mutant("RECORD date line removed", lambda: judge_record(
        rec.replace("date: 2026-10-04T00:00:00Z\n", ""), yes), expect="'date:'")
    mutant("RECORD command line removed", lambda: judge_record(
        rec.replace("command: python3 tools/test_skill_capability_prefinal.py --write-evidence\n", ""), yes),
           expect="'command:'")
    mutant("RECORD PF_MODE line removed", lambda: judge_record(rec.replace("PF_MODE=gex44\n", ""), yes),
           expect="PF_MODE=gex44")
    mutant("RECORD PF_TERMINAL=A,B", lambda: judge_record(
        rec.replace(f"PF_TERMINAL={','.join(CLOSED)}", "PF_TERMINAL=A,B"), yes), expect="PF_TERMINAL=")
    mutant("RECORD PF_OPEN line removed", lambda: judge_record(rec.replace(OPEN_LINE + "\n", ""), yes),
           expect="PF_OPEN=N")
    mutant("RECORD shows CEP_PILLAR_N=PASS", lambda: judge_record(
        rec.replace("PF_MODE=gex44\n", "PF_MODE=gex44\nCEP_PILLAR_N=PASS\n"), yes), expect="N reported PASS")
    for needle, repl in (("CLOSE.md", "the close file"), ("state.N", "the N state"),
                         ("mission/skill-capability-run", "the run")):
        mutant(f"COMMANDS without {needle!r}", lambda n=needle, r=repl: check_commands(cl.replace(n, r)),
               expect=f"does not contain {needle!r}")
    mutant("COMMANDS argv escapes tools/ (refused by CE)", lambda: check_commands(
        cl.replace(CLOSEOUT_ARGV_TEXT, json.dumps(["python", "tools/../x.py", "--closeout"]))), expect="refused by CE")
    mutant("CBR predicted differs from frozen", lambda: check_cbr(F["cbr"].replace(
        "| F | IMPLEMENTED_AND_VERIFIED |", "| F | MERGED_INTO_EXISTING_OWNER |", 1), F["led"], ex), expect="!= frozen")
    mutant("CBR empty 'what surprised us'", lambda: check_cbr(F["cbr"].replace("surprise G |", " |", 1), F["led"], ex),
           expect="'what surprised us' is empty")
    mutant("CBR evidence cell without a backticked path", lambda: check_cbr(F["cbr"].replace(
        "| `ev/N.md` `src/x.py:4` |", "| ev/N.md |", 1), F["led"], ex), expect="holds no backticked path")
    mutant("UKDL entry without Trap", lambda: check_ukdl(F["ukdl"].replace("- Trap: symptom 2\n", "", 1), ex),
           expect="'- Trap:'")
    mutant("UKDL entry without Source", lambda: check_ukdl(F["ukdl"].replace(
        "- Source: `src/x.py:4-6` and `src/y.md`\n", "", 1), ex), expect="'- Source:'")
    mutant("DECISIONS section without Options", lambda: check_decisions(
        F["state"], cl.replace("Options: (a) x, (b) y\n", "", 1)), expect="'Options:'")
    mutant("STATUS closed short by one", lambda: judge_status(0, json.dumps(
        {"open": ["N"], "closed": CLOSED[:-1], "violations": []})), expect="closed ")
    mutant("N-OPEN rc 2 with the right fail line", lambda: judge_n_open(2, n_good), expect="expected 1")
    mutant("DELTAS pillar Z", lambda: check_deltas(led_with(
        lambda l: l["deltas"]["intelligence"].append({"pillar": "Z", "change": "rule z", "evidence": ["ev/A.md"]})),
        ex), expect="not in A..N")
    # ---- NO-FINAL: the refusal pole and the other pole (argument check only, no process)
    mutant("NO-FINAL --final refused", lambda: _wrapper_args_ok(["--final"]))
    mutant("NO-FINAL abbreviation --fin refused", lambda: _wrapper_args_ok(["--fin"]))
    try:
        green("NO-FINAL --status passes the argument check", [] if _wrapper_args_ok(["--status"]) == ["--status"]
              else ["--status not passed through"])
    except ValueError as exc:
        green("NO-FINAL --status passes the argument check", [str(exc)])

    good_all = ok and kills == total
    print(f"PF_SELFTEST_GREENS={greens}")
    print(f"PF_SELFTEST={'PASS' if good_all else 'FAIL'} kills={kills}/{total}")
    return good_all


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0], allow_abbrev=False)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--closeout", action="store_true")
    mode.add_argument("--write-evidence", action="store_true")
    mode.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if a.closeout:
        return run_closeout(Report())
    if a.write_evidence:
        return write_evidence()
    return run_gex44(Report())


if __name__ == "__main__":
    sys.exit(main())
