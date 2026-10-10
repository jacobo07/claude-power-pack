#!/usr/bin/env python
"""Certified Completion Reducer (oic-v1 S5): a missing receipt file is not missing work.

A slim worker's receipt IS its final message ("WU-n STATUS: DONE / HEAD / PICKED / TEST ... exit n",
packet contract); the worker is also the only thing that writes <packet>-receipt.md. When it ends
cleanly but dies before (or forgets) writing the file, gsd_mission stops the mission with "no receipt"
(F1) and the verified work reads as HALTED: the dying worker was the sole owner of its own certification.

This reducer derives the unit's state from evidence ranked by strength:
  re-run gates (proof) > commits reachable from the work tree's HEAD > the worker's final message
and materializes the receipt OUTSIDE the worker's failure domain, marked `source: reconstructed`.

Verdicts:
  DONE_RECONSTRUCTED   final message says DONE, every reported TEST exited 0, every PICKED/HEAD commit is
                       reachable from the work tree HEAD, tracked tree clean (and, with --rerun, every
                       gate re-ran green). The receipt is written; exactly once (content-addressed).
  RECOVERY_REQUIRED    anything missing, red, unreachable, dirty or unparseable. Never DONE, never a
                       guess; the reason is returned so halt-continue renews with it.

Used by gsd_mission's slim_finished branch (behind CPP_OIC, default on) BEFORE the "no receipt" stop,
so a reconstructed receipt and a fault-capsule renewal can never both fire.

    python tools/completion_reducer.py judge --packet <WU-n.md> --worktree <dir> --result-file <final message>
    python tools/completion_reducer.py judge ... --rerun --write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

DONE, RECOVERY = "DONE_RECONSTRUCTED", "RECOVERY_REQUIRED"
_SHA = r"[0-9a-f]{7,40}"


def parse_final(text: str) -> dict:
    """The worker's final message, per the packet contract. Missing fields stay missing."""
    t = text or ""
    st = re.search(r"\bSTATUS:\s*([A-Z_]+)", t)
    head = re.search(rf"\bHEAD:?\s*({_SHA})\b", t)
    picked = re.search(r"\bPICKED:?\s*(.+)", t)
    tests = re.findall(r"\bTEST:?\s*(.+?)\s+(?:->\s*)?exit\s+(-?\d+)", t)
    return {"status": st.group(1) if st else None,
            "head": head.group(1) if head else None,
            "picked": re.findall(_SHA, picked.group(1)) if picked else [],
            "tests": [{"cmd": c.strip(" `"), "exit": int(e)} for c, e in tests]}


def _git(wt: str, *args: str) -> tuple[int, str]:
    git = "git"
    for c in (r"C:\Program Files\Git\cmd\git.exe",):
        if Path(c).exists():
            git = c
    p = subprocess.run([git, "-C", wt, *args], capture_output=True, text=True, timeout=60)
    return p.returncode, (p.stdout or "").strip()


def git_facts(wt: str, shas: list[str]) -> dict:
    rc, head = _git(wt, "rev-parse", "HEAD")
    if rc != 0:
        return {"ok": False, "why": "work tree unreadable"}
    unreachable = []
    for s in shas:
        rc_t, _ = _git(wt, "cat-file", "-e", f"{s}^{{commit}}")
        rc_a, _ = _git(wt, "merge-base", "--is-ancestor", s, head)
        if rc_t != 0 or rc_a != 0:
            unreachable.append(s)
    _, dirty = _git(wt, "status", "--porcelain", "--untracked-files=no")
    return {"ok": True, "head": head, "unreachable": unreachable, "dirty_tracked": bool(dirty)}


def rerun(wt: str, cmds: list[str], timeout_s: int = 600) -> list[dict]:
    out = []
    for c in cmds:
        try:
            p = subprocess.run(c, shell=True, cwd=wt, capture_output=True, text=True, timeout=timeout_s)
            out.append({"cmd": c, "exit": p.returncode, "tail": (p.stdout or "")[-300:]})
        except subprocess.TimeoutExpired:
            out.append({"cmd": c, "exit": None, "tail": f"timeout {timeout_s}s"})
    return out


def judge(packet: str, worktree: str, result_text: str, *, do_rerun: bool = False) -> dict:
    f = parse_final(result_text)
    why = []
    if f["status"] != "DONE":
        why.append(f"final message status {f['status']!r}, not DONE")
    if not f["tests"]:
        why.append("no TEST line with an exit code")
    red = [t["cmd"] for t in f["tests"] if t["exit"] != 0]
    if red:
        why.append(f"reported red: {red}")
    shas = list(dict.fromkeys([*f["picked"], *([f["head"]] if f["head"] else [])]))
    if not shas:
        why.append("no HEAD/PICKED commit named")
    g = git_facts(worktree, shas) if shas else {"ok": False, "why": "nothing to check"}
    if not g["ok"]:
        why.append(g["why"])
    else:
        if g["unreachable"]:
            why.append(f"commits not reachable from HEAD: {g['unreachable']}")
        if g["dirty_tracked"]:
            why.append("tracked files dirty in the work tree")
    reran = rerun(worktree, [t["cmd"] for t in f["tests"]]) if do_rerun and not why else []
    red2 = [r["cmd"] for r in reran if r["exit"] != 0]
    if red2:
        why.append(f"re-run red: {red2}")
    return {"verdict": RECOVERY if why else DONE, "why": why, "final": f, "git": g, "rerun": reran,
            "packet": packet, "worktree": worktree}


def receipt_text(v: dict, now: float | None = None) -> str:
    f, g = v["final"], v["git"]
    unit = Path(v["packet"]).stem
    gates = ("re-run green at reconstruction" if v["rerun"] else "worker-reported exit 0, not re-run")
    lines = [f"# {unit} receipt", "", "Status: DONE", "source: reconstructed (completion_reducer, oic-v1 S5)",
             f"reconstructed_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now or time.time()))}",
             f"work_tree_head: {g.get('head')}", f"commits: {', '.join(f['picked'] or [f['head']])}",
             f"gates: {gates}", ""]
    lines += [f"- `{t['cmd']}` exit {t['exit']}" for t in f["tests"]]
    lines += [f"- re-run `{r['cmd']}` exit {r['exit']}" for r in v["rerun"]]
    lines += ["", "Why reconstructed: the worker finished cleanly and its final message carries this receipt,",
              "but <packet>-receipt.md was never written; the supervisor materialized it from that message",
              "after checking every named commit is reachable and the tracked tree is clean."]
    return "\n".join(lines) + "\n"


def write_receipt(v: dict, now: float | None = None) -> dict:
    """Exactly once: an existing receipt is never overwritten; the same content twice is a no-op."""
    if v["verdict"] != DONE:
        return {"written": False, "why": "verdict is not DONE"}
    p = Path(v["packet"])
    r = p.with_name(p.stem + "-receipt.md")
    if r.exists():
        return {"written": False, "why": "receipt already present", "path": str(r)}
    body = receipt_text(v, now)
    tmp = r.with_suffix(".md.tmp")
    tmp.write_text(body, encoding="utf-8", newline="\n")
    tmp.replace(r)
    return {"written": True, "path": str(r), "sha256": hashlib.sha256(body.encode()).hexdigest()[:12]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="completion_reducer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    j = sub.add_parser("judge")
    j.add_argument("--packet", required=True)
    j.add_argument("--worktree", required=True)
    j.add_argument("--result-file", required=True)
    j.add_argument("--rerun", action="store_true")
    j.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    v = judge(a.packet, a.worktree, Path(a.result_file).read_text(encoding="utf-8"), do_rerun=a.rerun)
    if a.write:
        v["write"] = write_receipt(v)
    print(json.dumps(v, ensure_ascii=False, indent=1, default=str))
    return 0 if v["verdict"] == DONE else 10


if __name__ == "__main__":
    sys.exit(main())
