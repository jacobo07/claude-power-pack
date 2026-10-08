"""Deterministic entry-point matrix (A3b B0).

Scans the repo for the sites that can start model spend and prints, per entry
class: the files holding a launch site, whether any binding token appears in
those files, and whether the launch can be intercepted before it happens.

No model is involved. A class with no launch site found is reported ABSENT,
never silently skipped. Binding evidence is textual (a token in the same file);
it says "a binding is referenced", not "the binding is enforced" -- that second
claim is what the B3 canaries judge, so the column is named accordingly.

Usage: python tools/entry_matrix.py [--root DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_SUFFIXES = {".py", ".js", ".ps1", ".bat", ".cmd", ".vbs", ".sh", ".json", ".xml"}
SKIP_PARTS = {".git", "node_modules", "__pycache__", "vault", "_audit_cache", "evidence"}
SKIP_NAME = re.compile(r"(^|[\\/])(test_|tests[\\/]|fixtures[\\/])|_test\.|\.test\.")
SELF = Path(__file__).name   # the scanner's own patterns matched themselves (B0 flaw 1)

# Tokens meaning "this file talks to a budget binding".
BINDING = re.compile(
    r"admit_route|admit_subagent|goal[-_]spawn|goal[-_]renew|CPP_GOAL|session_budget"
    r"|session-budget|--max-budget-usd|loop_budget|mission_spend|envelope"
)
# Tokens meaning "an explicit ceiling is passed on the launch itself".
CEILING = re.compile(r"--max-budget-usd|--max-turns|max_turns|max-turns")

# class -> (launch regex, applicable-path regex, interceptable, why)
CLASSES = [
    ("claude --bg / -p (headless)",
     re.compile(r"""['"]claude(\.exe)?['"].*['"](--bg|-p|--print)['"]|claude(\.exe)?\s+(--bg|-p|--print)\b"""),
     re.compile(r"."), "yes",
     "launcher code runs before spawn; a pre-launch check is ours to add"),
    ("Agent/Task spawn",
     re.compile(r"""PreToolUse-Agent|matcher['"]?\s*[:=]\s*['"](Task\|Agent|Agent\|Task|Agent|Task)['"]|tool_name\s*[=!]==?\s*['"](Agent|Task)['"]"""),
     re.compile(r"."), "yes (host registration)",
     "PreToolUse on Agent fires pre-spawn; registering it in settings.json is an Owner step (HR-001)"),
    ("gsd_mission arm / relay",
     re.compile(r"def\s+(cmd_)?(arm|relay|launch|envelope|admit_route)\b|['\"](arm|relay)['\"]"),
     re.compile(r"gsd_mission|ralph|relay|mission"), "yes",
     "in-repo python; admit_route is the pre-launch hook point"),
    ("tranche_driver",
     re.compile(r"subprocess|Popen|claude"),
     re.compile(r"tranche_driver"), "yes",
     "in-repo python driver; check precedes each tranche launch"),
    ("scheduled tasks",
     re.compile(r"schtasks|Register-ScheduledTask|New-ScheduledTask|wscript|hidden_launch|CronCreate"),
     re.compile(r"."), "host",
     "the OS scheduler starts it; only the launched script can refuse, after start"),
    ("kclear / kresume",
     re.compile(r"kresume|kclear|--resume|rollover"),
     re.compile(r"kresume|kclear|rollover|courier"), "yes",
     "in-repo courier/launcher runs before the successor session starts"),
    ("GEX44 bridge",
     re.compile(r"gex44|ssh\s+.*claude|kobicraft_gex44"),
     re.compile(r"gex44"), "host",
     "runs on the remote host; local pre-launch cannot see the remote session"),
]


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        rel = p.relative_to(root)
        if p.name == SELF or SKIP_PARTS & set(rel.parts) or SKIP_NAME.search(str(rel)):
            continue
        yield p, rel


def code_lines(text: str, suffix: str):
    """(line number, line) for executable lines only: comments and Python docstrings name launch
    flags without launching anything, and counted them as sites (B0 flaw 3)."""
    in_doc = None
    for i, ln in enumerate(text.splitlines(), 1):
        s = ln.strip()
        if suffix == ".py":
            if in_doc:
                if in_doc in s:
                    in_doc = None
                continue
            q = next((d for d in ('"""', "'''") if s.startswith(d) or s.startswith(("r" + d, "f" + d))), None)
            if q:
                if s.count(q) == 1:
                    in_doc = q
                continue
            if s.startswith("#"):
                continue
        elif suffix in (".js", ".ps1") and s.startswith(("//", "/*", "*", "#", "<#")):
            continue
        yield i, ln


def scan(root: Path):
    rows = {name: [] for name, *_ in CLASSES}
    for p, rel in iter_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, launch, paths, _icpt, _why in CLASSES:
            if not paths.search(str(rel)):
                continue
            hits = [i for i, ln in code_lines(text, p.suffix.lower()) if launch.search(ln)]
            named = hits or [i for i, ln in enumerate(text.splitlines(), 1) if launch.search(ln)]
            if not named:
                continue
            # A launch named only in comments is kept, never dropped: the regex does not see argv-list
            # launches (`[exe, "-p", ...]`), so a file that only DESCRIBES its launch is usually a real
            # launcher the text scan cannot judge. Dropping it would turn "not matched" into "absent".
            rows[name].append({
                "file": str(rel).replace("\\", "/"),
                "lines": named[:3],
                "n": len(hits),
                "mention_only": not hits,
                "binding": bool(BINDING.search(text)),
                "ceiling": bool(CEILING.search(text)),
            })
    return rows


# A text scan cannot prove a launch is unbounded, only that no binding or ceiling reference appears
# in its file (B0 flaw 2). The label says what was observed.
UNSEEN_LABEL = "no binding/ceiling ref found"


def render(rows) -> str:
    out = ["# Entry-point matrix (A3b B0)", "",
           "Generated by `python tools/entry_matrix.py` -- deterministic, no model. `sites` counts code "
           "lines only; a file whose launch is named only in comments/docstrings is listed as `mention only` "
           "(the regex misses argv-list launches, so it is UNJUDGED, not absent). `binding ref` = a "
           "budget-binding name appears in the file (referenced, not proven enforced; B3 canaries judge "
           f"enforcement). `{UNSEEN_LABEL}` is what the text scan observed, not proof the launch is unbounded.",
           ""]
    for name, _l, _p, icpt, why in CLASSES:
        found = rows[name]
        out += [f"## {name}", f"- interceptable pre-launch: **{icpt}** -- {why}"]
        if not found:
            out += ["- launch sites: **ABSENT** (no match; absence of a match, not proof of absence)", ""]
            continue
        unbound = [r for r in found if not r["binding"] and not r["ceiling"]]
        mention = sum(1 for r in found if r["mention_only"])
        out += [f"- launch files: {len(found)} ({len(found) - mention} matched in code, {mention} mention only); "
                f"with neither binding ref nor ceiling: {len(unbound)}", "",
                "| file | sites | first lines | binding ref | ceiling | null today |",
                "|---|---|---|---|---|---|"]
        for r in sorted(found, key=lambda r: r["file"]):
            null = (UNSEEN_LABEL if not r["binding"] and not r["ceiling"]
                    else "ceiling only" if not r["binding"] else "UNJUDGED (read the code)")
            if r["mention_only"]:
                null = "mention only -- " + null
            out.append(f"| {r['file']} | {r['n']} | {','.join(map(str, r['lines']))} | "
                       f"{'yes' if r['binding'] else 'no'} | {'yes' if r['ceiling'] else 'no'} | {null} |")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    text = render(scan(Path(a.root)))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {a.out} ({len(text)} chars)")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
