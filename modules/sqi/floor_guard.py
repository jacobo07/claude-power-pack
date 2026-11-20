#!/usr/bin/env python3
"""SQI floor guard -- the DIFF-SCOPED non-weakening check (CPP-AGSK-001 pilot AGSK-C).

The weakening detectors beside this file read a CENSUS (counts and hashes of the authored tests
at two points in time). They cannot see a change that adds a suppression comment, an unfinished
stub, a skipped case, a raised-tolerance edit to a written constraint, or a new exception row,
because none of those move a census count. This module reads the CHANGE ITSELF: the unified diff
between a merge base and the working tree, plus untracked files.

Threat model adapted from addyosmani/agent-skills (MIT, (c) 2025 Addy Osmani, pin 8c99fa36,
skills/constraint-driven-development/references/floor-guard.md). Reimplemented in Python on
CPP's own vocabulary (`weakening_detectors._ASSERT_CALL_NAME`), not copied. Attribution:
vault/programs/bcap-2/agsk/NOTICE.md. Deliberate departures from upstream:

  * NET, not gross: a suppression/stub/skip/assertion that is removed and re-added in the same
    file (a move, a reflow) is not a new weakening. A rule is flagged only when the file's added
    count exceeds its removed count, so PRE-EXISTING debt never becomes a finding by being edited.
  * Assertion vocabulary is CPP's (V-gate `_ok(...)`, pytest.raises, assert_called...), and
    comment lines are never counted -- a word in a comment is not an assertion (SQI contract 1).
  * `TODO` alone is not an unfinished stub (too noisy to be a floor).
  * Exceptions are APPROVALS: a finding is waived only by an unexpired approval that names rule,
    path glob, owner, reason, approver and expiry. A partial approval waives nothing, and every
    waiver is reported (audit trail), never silent.

Exit codes: 0 clean, 1 at least one unwaived violation, 2 the guard could not run. A 2 is never a 0.
Tightening is silent; loosening is loud. Threshold direction is read from the words around the
number; an unreadable direction is reported on change, because staying quiet is the wrong default.

    python3 -m modules.sqi.floor_guard [--base REF] [--approvals approvals.json] [--json]
"""
from __future__ import annotations

import datetime as _dt
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

RULES = ("silenced-checker", "unfinished-work", "test-made-easier", "assertion-removed",
         "test-deleted", "rule-removed", "threshold-loosened", "new-exception")

SUPPRESSIONS = re.compile(
    r"@ts-ignore|@ts-nocheck|eslint-disable|biome-ignore|#\s*noqa|#\s*type:\s*ignore|"
    r"#\s*pragma:\s*no cover|#\s*pylint:\s*disable|istanbul ignore|nosemgrep|gitleaks:allow|"
    r"Stryker disable")
STUBS = re.compile(
    r"raise\s+NotImplementedError|throw new (?:Error|NotImplemented)\w*\(.*[Nn]ot implemented|"
    r"catch\s*(?:\(\w*\))?\s*\{\s*\}|except\b[^:\n]*:\s*pass\b|^\s*pass\s*#\s*stub")
SKIPS = re.compile(
    r"\.(?:skip|todo)\b|\bxit\(|\bxdescribe\(|@pytest\.mark\.skip|pytest\.skip\(|"
    r"@unittest\.skip|\bt\.Skip\(|@pytest\.mark\.xfail")
TEST_PATH = re.compile(
    r"(?:^|/)(?:tests?/|test_[^/]*\.py$|[^/]*_test\.py$|[^/]*\.(?:test|spec)\.[jt]sx?$)")
CONSTRAINT_FILE = re.compile(r"(?:^|/)CONSTRAINTS\.md$")
_EXC_ROW = re.compile(r"^\|\s*(?:W|E)\d+\s*\|")
_COMMENT = re.compile(r"^\s*(?:#|//|\*|/\*)")

_MIN_BEFORE = re.compile(r"(>=|>|≥|at least|minimum|\bmin\b|no less than|not fall|not drop)\s*$")
_MAX_BEFORE = re.compile(r"(<=|<|≤|at most|maximum|\bmax\b|no more than|under|below|not grow|not exceed)\s*$")
_MIN_AFTER = re.compile(r"^\s*\S*\s*(?:\|\s*)?(or more|or higher|must not fall|must not drop)")
_MAX_AFTER = re.compile(r"^\s*\S*\s*(?:\|\s*)?(or less|or lower|must not grow|must not exceed)")


def _assert_regex() -> re.Pattern:
    """CPP's own assertion idiom, reused from the weakening detectors (REUSE > BUILD)."""
    try:
        from modules.sqi import weakening_detectors as wd
        names = "|".join(sorted(re.escape(n) for n in wd._ASSERT_CALL_NAME))
        tails = "|".join(sorted(re.escape(n) for n in wd._ASSERT_CALL_TAIL))
    except Exception:  # noqa: BLE001 -- vocabulary unavailable: fall back to the defaults, never go blind
        names, tails = "_ok|_fail|_check|_assert|expect|should", "raises|warns|should|expect"
    return re.compile(
        rf"(?:^\s*assert\b|\bself\.assert\w*\(|\.assert_\w+\(|\b(?:{names})\(|\.(?:{tails})\b|\bassert\w*\()")


ASSERTION = _assert_regex()


@dataclass
class Finding:
    rule: str
    file: str
    text: str
    waived_by: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Line:
    file: str
    text: str


@dataclass
class ParsedDiff:
    added: list
    removed: list
    deleted: list
    new_files: list


def parse_diff(diff: str) -> ParsedDiff:
    """Walk a `--unified=0` diff. `---`/`+++` are headers only between a `diff` line and its first
    `@@`; inside a hunk every line is content (an added `++i` shows as `+++i`)."""
    added: list = []
    removed: list = []
    deleted: list = []
    new_files: list = []
    file = old = ""
    header = False
    for line in diff.split("\n"):
        if line.startswith("diff "):
            header = True
            file = old = ""
        elif line.startswith("@@"):
            header = False
        elif header:
            if line.startswith("--- "):
                old = re.sub(r"^[ab]/", "", line[4:])
            elif line.startswith("+++ "):
                new = re.sub(r"^[ab]/", "", line[4:])
                if new == "/dev/null":
                    file = old
                    deleted.append(old)
                else:
                    file = new
                    if old == "/dev/null":
                        new_files.append(new)
        elif line.startswith("+"):
            added.append(Line(file, line[1:]))
        elif line.startswith("-"):
            removed.append(Line(file, line[1:]))
    return ParsedDiff(added, removed, deleted, new_files)


def _rule_key(text: str):
    s = text.strip()
    if s.startswith("|"):
        cells = [c.strip() for c in s.split("|") if c.strip()]
        return cells[0] if cells else ""
    if re.match(r"^[-*] ", s):
        return s[2:].split(":")[0].strip()
    return None


def _thresholds(text: str) -> list:
    out = []
    for m in re.finditer(r"\d+(?:\.\d+)?", text):
        before = text[max(0, m.start() - 24):m.start()].lower()
        after = text[m.end():m.end() + 40].lower()
        if _MIN_BEFORE.search(before) or _MIN_AFTER.match(after):
            d = "min"
        elif _MAX_BEFORE.search(before) or _MAX_AFTER.match(after):
            d = "max"
        else:
            d = None
        out.append((float(m.group()), d))
    return out


def _loosened(before: str, after: str) -> bool:
    """True when a number moved in the loosening direction; unreadable direction + change = True."""
    b, a = _thresholds(before), _thresholds(after)
    for d in ("min", "max", None):
        bs = [n for n, x in b if x == d]
        as_ = [n for n, x in a if x == d]
        for i, bn in enumerate(bs):
            if i >= len(as_):
                return True           # a threshold with no counterpart after the edit was removed
            an = as_[i]
            if d == "min" and an < bn:
                return True
            if d == "max" and an > bn:
                return True
            if d is None and an != bn:
                return True
    return False


def _net(added: list, removed: list, rx: re.Pattern, skip_comments: bool = False) -> dict:
    """Per-file net count of lines matching rx (added minus removed) plus the added examples."""
    net: dict = {}
    for ln in added:
        if skip_comments and _COMMENT.match(ln.text):
            continue
        if rx.search(ln.text):
            n, ex = net.get(ln.file, (0, []))
            net[ln.file] = (n + 1, ex + [ln.text])
    for ln in removed:
        if skip_comments and _COMMENT.match(ln.text):
            continue
        if rx.search(ln.text):
            n, ex = net.get(ln.file, (0, []))
            net[ln.file] = (n - 1, ex)
    return net


def analyze(diff: str) -> list:
    """Pure: unified-diff text -> list[Finding]. No I/O, no waiver logic."""
    p = parse_diff(diff)
    out: list = []

    def flag(rule: str, file: str, text: str) -> None:
        out.append(Finding(rule, file, text.strip()[:120]))

    for rule, rx in (("silenced-checker", SUPPRESSIONS), ("unfinished-work", STUBS), ("test-made-easier", SKIPS)):
        for f, (n, ex) in _net(p.added, p.removed, rx).items():
            if n > 0:
                flag(rule, f, ex[0] if ex else "")
    # An assertion is the only thing in a test that can fail: net loss inside a surviving test file.
    for f, (n, _) in _net(p.added, p.removed, ASSERTION, skip_comments=True).items():
        if n < 0 and TEST_PATH.search(f) and f not in p.deleted:
            flag("assertion-removed", f, f"net {n} assertion line(s)")
    added_names = {Path(x).name for x in p.new_files}
    for f in p.deleted:
        if TEST_PATH.search(f) and Path(f).name not in added_names:
            flag("test-deleted", f, "file deleted")
    # Written constraints: a rule dropped or a number moved the loosening way; a new exception row.
    rem = [x for x in p.removed if CONSTRAINT_FILE.search(x.file) and _rule_key(x.text) is not None]
    add = [x for x in p.added if CONSTRAINT_FILE.search(x.file) and _rule_key(x.text) is not None]
    for ln in add:
        if _EXC_ROW.match(ln.text.strip()):
            flag("new-exception", ln.file, ln.text)
    for r in rem:
        a = next((x for x in add if _rule_key(x.text) == _rule_key(r.text)), None)
        if a is None:
            if not _EXC_ROW.match(r.text.strip()):    # dropping an exception tightens: silent
                flag("rule-removed", r.file, r.text)
        elif _loosened(r.text, a.text):
            flag("threshold-loosened", r.file, f"{r.text.strip()} -> {a.text.strip()}")
    return out


def _approval_valid(a: dict, today: _dt.date) -> bool:
    need = ("rule", "path", "owner", "reason", "approved_by", "expires")
    if not all(isinstance(a.get(k), str) and a.get(k).strip() for k in need):
        return False
    try:
        return _dt.date.fromisoformat(a["expires"]) >= today
    except ValueError:
        return False


def apply_approvals(findings: list, approvals: list, today: _dt.date | None = None) -> list:
    """Mark findings waived by a COMPLETE, UNEXPIRED approval. Partial/expired approvals waive nothing."""
    today = today or _dt.date.today()
    for f in findings:
        for a in approvals or []:
            if isinstance(a, dict) and _approval_valid(a, today) and a["rule"] == f.rule \
                    and fnmatch.fnmatch(f.file, a["path"]):
                f.waived_by = f"{a['approved_by']} (owner {a['owner']}, expires {a['expires']}): {a['reason']}"
                break
    return findings


def _git(args: list, cwd: Path, diff_exit: bool = False):
    try:
        # Explicit UTF-8: bare text=True decodes with the ANSI code page on Windows, and the
        # first non-cp1252 byte in a diff killed the reader -> "could not diff" on every real
        # repo (measured 2026-11-20, byte 0x90). An undecodable byte is replaced, never fatal.
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode == 0 or (diff_exit and r.returncode == 1):
        return r.stdout
    return None


def collect_diff(repo: Path, base: str = "HEAD"):
    """(diff_text, error). Tracked changes vs the merge base PLUS untracked files (git diff alone is
    blind to new files). Any git failure is an error, never an empty diff."""
    top = _git(["rev-parse", "--show-toplevel"], repo)
    if not top:
        return None, "not inside a git work tree"
    root = Path(top.strip())
    mb = _git(["merge-base", base, "HEAD"], root)
    if not mb:
        return None, f"no merge base against {base}"
    tracked = _git(["diff", "--unified=0", "--no-renames", mb.strip(), "--"], root)
    if tracked is None:
        return None, "could not diff against merge base"
    untracked = _git(["ls-files", "--others", "--exclude-standard"], root)
    if untracked is None:
        return None, "could not list untracked files"
    parts = [tracked]
    for f in filter(None, untracked.split("\n")):
        d = _untracked_as_diff(root, f)
        if d is None:
            return None, f"could not read untracked file {f}"
        parts.append(d)
    return "\n".join(parts), None


def _untracked_as_diff(root: Path, rel: str):
    """The `git diff --no-index /dev/null <f>` text for a new file, built in-process. One git
    process per untracked file cost >600 s on a 2,955-file tree (measured 2026-11-20) and timed
    out run_sqi. A binary file (NUL in its first 8 KiB, git's own test) contributes no lines."""
    try:
        data = (root / rel).read_bytes()
    except OSError:
        return None
    head = f"diff --git a/{rel} b/{rel}\nnew file mode 100644\n--- /dev/null\n+++ b/{rel}"
    if b"\0" in data[:8192]:
        return head + f"\nBinary files /dev/null and b/{rel} differ"
    lines = data.decode("utf-8", errors="replace").splitlines()
    if not lines:
        return head
    return head + f"\n@@ -0,0 +1,{len(lines)} @@\n" + "\n".join("+" + ln for ln in lines)


def run(repo: Path, base: str = "HEAD", approvals: list | None = None):
    """-> (exit_code, findings, error)."""
    diff, err = collect_diff(Path(repo), base)
    if err:
        return 2, [], err
    findings = apply_approvals(analyze(diff or ""), approvals or [])
    return (1 if any(f.waived_by is None for f in findings) else 0), findings, None


CLEAN, VIOLATIONS, UNASSESSED = "CLEAN", "VIOLATIONS", "UNASSESSED"


def report(repo: Path, base: str = "HEAD", approvals: list | None = None) -> dict:
    """REPORT-ONLY view for done paths (bcap2-activation slice B). Never raises and never decides
    an exit code: the caller prints it beside its verdict. A guard that could not run is
    UNASSESSED with its reason -- never CLEAN, because absence of a reading is not a clean diff."""
    try:
        code, findings, err = run(Path(repo), base, approvals)
    except Exception as e:  # noqa: BLE001 -- a crashed guard is UNASSESSED, reported, never silent
        return {"status": UNASSESSED, "base": base, "error": f"{type(e).__name__}: {e}",
                "violations": [], "waived": 0}
    if err:
        return {"status": UNASSESSED, "base": base, "error": err, "violations": [], "waived": 0}
    open_ = [dict(f.to_dict(), text=_redact(f.text)) for f in findings if f.waived_by is None]
    return {"status": VIOLATIONS if open_ else CLEAN, "base": base, "error": None,
            "violations": open_, "waived": len(findings) - len(open_)}


def report_line(r: dict) -> str:
    """One line, same shape for every consumer."""
    if r["status"] not in (CLEAN, VIOLATIONS):  # UNASSESSED / NOT_RUN: no reading, so no counts
        return f"floor-guard (report only, base {r['base']}): {r['status']} -- {r['error']}"
    rules = sorted({v["rule"] for v in r["violations"]})
    return (f"floor-guard (report only, base {r['base']}): {r['status']} "
            f"{len(r['violations'])} violation(s), {r['waived']} waived"
            + (f" [{', '.join(rules)}]" if rules else ""))


def _redact(s: str) -> str:
    try:
        from modules.secret_firewall.redactor import redact
        return redact(s)
    except Exception:  # noqa: BLE001 -- never print an unredacted line if the redactor is unavailable
        return "[text withheld: redactor unavailable]"


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Diff-scoped quality-floor non-weakening guard")
    ap.add_argument("--base", default="HEAD", help="merge-base ref (default HEAD = uncommitted work)")
    ap.add_argument("--approvals", help="JSON list of approvals (rule,path,owner,reason,approved_by,expires)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--repo", default=".")
    a = ap.parse_args(argv)
    approvals: list = []
    if a.approvals:
        try:
            approvals = json.loads(Path(a.approvals).read_text(encoding="utf-8"))
            if not isinstance(approvals, list):
                raise ValueError("approvals must be a JSON list")
        except (OSError, ValueError) as e:
            print(f"floor-guard: cannot read approvals: {e}", file=sys.stderr)
            return 2
    code, findings, err = run(Path(a.repo), a.base, approvals)
    if err:
        print(f"floor-guard: {err}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps([dict(f.to_dict(), text=_redact(f.text)) for f in findings], indent=1))
    else:
        for f in findings:
            tag = "WAIVED" if f.waived_by else "VIOLATION"
            print(f"{tag} {f.rule} {f.file}: {_redact(f.text)}" + (f"  [{f.waived_by}]" if f.waived_by else ""))
        print("floor-guard: clean" if not findings else f"floor-guard: {len(findings)} finding(s)")
    return code


if __name__ == "__main__":
    sys.exit(main())
