#!/usr/bin/env python
"""V-CUSTODY-* gates: safe-to-forget refuses when the session's OWN written paths are uncommitted in
another repo (plan ccp-s16 §16.1 S1). Hermetic: two throwaway git repos and a non-repo dir.

Measured 2026-10-03: session a4849588 sealed SAFE_TO_FORGET in an Orca-X worktree while its edit to
the Power Pack's tools/rollover.py was uncommitted; it sat orphaned for 3 days."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover as ro  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def repo(d: Path) -> Path:
    d.mkdir(parents=True)
    for args in (("init", "-q"), ("config", "user.email", "t@t"), ("config", "user.name", "t"),
                 ("commit", "-q", "--allow-empty", "-m", "root")):
        assert ro._git(d, *args)[0], args
    return d


def custody_missing(fo: dict) -> list[str]:
    comp = ro.completeness({"repo": {"state": "OK", "head": "h", "branch": "b", "dirty": []}, "foreign": fo})
    return [m for m in comp["missing"] if m.startswith("custody")]


def _iso(t: float) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def shell_gates(tmp: Path, home: Path, other: Path) -> None:
    """V-CUSTODY-SHELL-*: a file written through a shell, uncommitted in another repo, is held in custody; a file the
    command only read, or a peer changed after the command, is not (2026-11-22 write-channel audit)."""
    import json
    import os
    import time
    t0 = time.time() - 600
    written, read_only, peer_later, untimed = (other / "gen.html", other / "spec.md", other / "notes.txt",
                                               other / "untimed.css")
    for p in (written, read_only, peer_later, untimed):
        p.write_text("x\n", encoding="utf-8")
    os.utime(written, (t0 + 3, t0 + 3))            # changed while its command ran (t0 .. t0+5)
    os.utime(read_only, (t0 - 3600, t0 - 3600))    # named, but last changed an hour before: a read
    os.utime(peer_later, (t0 + 400, t0 + 400))     # named, changed long after the command: a peer's edit
    os.utime(untimed, (t0 + 3, t0 + 3))

    def use(i, cmd, start, end, tool="PowerShell"):
        u = {"type": "assistant", "cwd": str(home), "message": {"content": [
            {"type": "tool_use", "id": "t%d" % i, "name": tool, "input": {"command": cmd}}]}}
        r = {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t%d" % i, "content": ""}]}}
        if start is not None:
            u["timestamp"] = _iso(start)
        if end is not None:
            r["timestamp"] = _iso(end)
        return [u, r]
    rows = (use(1, "Set-Content -Path '%s' -Value x; Get-Content %s" % (written, read_only), t0, t0 + 5)
            + use(2, "cat %s" % peer_later.as_posix(), t0, t0 + 5, tool="Bash")
            + use(3, "Set-Content %s x" % untimed, None, t0 + 5))
    tp = tmp / "shell.jsonl"
    tp.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    got = {Path(p).name for p in ro.custody_writes(tp)}
    ok("V-CUSTODY-SHELL-WRITE-HELD", "gen.html" in got, str(got))
    ok("V-CUSTODY-SHELL-READ-NOT-HELD", "spec.md" not in got, str(got))
    ok("V-CUSTODY-SHELL-PEER-LATER-NOT-HELD", "notes.txt" not in got, str(got))
    ok("V-CUSTODY-SHELL-UNTIMED-NOT-HELD", "untimed.css" not in got, str(got))
    miss = custody_missing(ro.foreign_custody(ro.custody_writes(tp), str(home)))
    ok("V-CUSTODY-SHELL-REFUSES-SEAL", len(miss) == 1 and "gen.html" in miss[0] and "notes.txt" not in miss[0], str(miss))
    # path shapes the tokenizer must resolve (review LOW): MSYS drive, relative to cwd, quoted with spaces,
    # redirection target, PowerShell $env: and ~ expansion
    spaced = other / "my dir" / "page.css"
    spaced.parent.mkdir(exist_ok=True)
    spaced.write_text("x\n", encoding="utf-8")
    rel = other / "rel.txt"
    rel.write_text("x\n", encoding="utf-8")
    drive, rest = str(written.resolve()).split(":", 1)
    msys = "/%s%s" % (drive.lower(), rest.replace("\\", "/"))
    os.environ["V_CUSTODY_DIR"] = str(other)
    shapes = {
        "msys": (ro._shell_paths("cat %s" % msys, ""), written),
        "relative": (ro._shell_paths("Set-Content rel.txt x", str(other)), rel),
        "quoted-spaces": (ro._shell_paths("Set-Content -Path \"%s\" -Value x" % spaced, ""), spaced),
        "redirect": (ro._shell_paths("echo x >%s" % rel.as_posix(), ""), rel),
        "ps-env": (ro._shell_paths("Set-Content $env:V_CUSTODY_DIR/rel.txt x", ""), rel),
    }
    bad = {k: v for k, (v, want) in shapes.items()
           if os.path.normcase(os.path.normpath(str(want))) not in {os.path.normcase(p) for p in v}}
    ok("V-CUSTODY-SHELL-PATH-SHAPES", not bad, str(bad))
    caller = (Path(__file__).resolve().parent / "mission_capsule.py").read_text(encoding="utf-8")
    ok("V-CUSTODY-SHELL-WIRED", "ro.foreign_custody(ro.custody_writes(tp)" in caller
       and "foreign_custody(custody_writes(tp)" in (Path(ro.__file__).read_text(encoding="utf-8")))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="custody-"))
    home, other, loose = repo(tmp / "home"), repo(tmp / "other"), tmp / "loose"
    loose.mkdir()
    mine, peer, at_home = other / "mine.py", other / "peer.py", home / "a.py"
    for p in (mine, peer, at_home, loose / "note.txt"):
        p.write_text("x\n", encoding="utf-8")
    writes = [str(mine), str(at_home), str(loose / "note.txt")]

    fo = ro.foreign_custody(writes, str(home))
    dirty = [r["dirty"] for r in fo.get("repos", [])]
    ok("V-CUSTODY-OWN-FOREIGN-WRITE-FOUND", fo.get("state") == "OK" and dirty == [["mine.py"]], str(fo))
    ok("V-CUSTODY-PEER-DIRT-NOT-JUDGED", all("peer.py" not in d for d in dirty), str(dirty))
    ok("V-CUSTODY-HOME-REPO-NOT-JUDGED", all(r["root"] != str(home) for r in fo.get("repos", [])), str(fo))
    ok("V-CUSTODY-NON-REPO-COUNTED", fo.get("unchecked_non_repo") == 1, str(fo))
    miss = custody_missing(fo)
    ok("V-CUSTODY-REFUSES", len(miss) == 1 and "mine.py" in miss[0], str(miss))

    assert ro._git(other, "add", "mine.py")[0] and ro._git(other, "commit", "-q", "-m", "mine")[0]
    clean = ro.foreign_custody(writes, str(home))
    ok("V-CUSTODY-COMMITTED-PASSES", clean.get("repos") == [] and not custody_missing(clean), str(clean))

    ok("V-CUSTODY-UNKNOWN-REFUSES", custody_missing(ro._unknown("git status failed")) != [])
    legacy = ro.completeness({"repo": {"state": "OK", "head": "h", "branch": "b", "dirty": []}})
    ok("V-CUSTODY-LEGACY-CAPSULE-NOT-JUDGED", not [m for m in legacy["missing"] if m.startswith("custody")])

    shell_gates(tmp, home, other)
    print(f"CUSTODY_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
