"""Work-unit packet compiler: a packet is DERIVED from the claims IR + product HEAD, never a second truth.

  wu_packet.py compile --claims IR.json --unit ID --repo PRODUCT_REPO --out PACKET.md
  wu_packet.py verify PACKET.md          # prints CURRENT (exit 0) or STALE (exit 3)

fingerprint = sha256( canonical JSON of {unit, its claims, the gates those claims reference}
                      + product repo `git rev-parse HEAD` + sha256 of the IR file ).
Changing a claim, the IR bytes or the product HEAD makes a packet STALE; an unknown unit is refused (exit 2).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

GIT_FALLBACK = r"C:\Program Files\Git\cmd\git.exe"
HARD_STOP_FACTOR = 3
PROGRESS_RULE = ("Every call must produce a NEW identity: new evidence, an artifact delta, a test transition, "
                 "a new failure signature, a closed acceptance item, or an `ADVANCED:` line (discriminator / "
                 "constraint / hypothesis / eliminated). Five consecutive calls with none: stop and report.")


class Refused(Exception):
    pass


def _git(repo: str, *args: str) -> str:
    exe = shutil.which("git") or GIT_FALLBACK
    p = subprocess.run([exe, "-C", repo, *args], capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed in {repo}: {p.stderr.strip()}")
    return p.stdout.strip()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(ir_path: Path, unit_id: str, repo: str) -> tuple[str, dict, list, list, str, str]:
    raw = ir_path.read_bytes()
    ir = json.loads(raw.decode("utf-8-sig"))
    unit = next((u for u in ir.get("units") or [] if u.get("id") == unit_id), None)
    if unit is None:
        raise Refused(f"unit {unit_id!r} not in {ir_path}")
    claims = [c for c in ir.get("claims") or [] if c.get("unit") == unit_id]
    gate_ids = sorted({g for c in claims for g in c.get("gates") or []})
    gates = [g for g in ir.get("gates") or [] if g.get("id") in gate_ids]
    head = _git(repo, "rev-parse", "HEAD")
    ir_sha = _sha(raw)
    body = json.dumps({"unit": unit, "claims": claims, "gates": gates}, sort_keys=True, separators=(",", ":"))
    return _sha((body + "\n" + head + "\n" + ir_sha).encode()), unit, claims, gates, head, ir_sha


def render(ir_path: Path, unit_id: str, repo: str) -> str:
    fp, unit, claims, gates, head, ir_sha = fingerprint(ir_path, unit_id, repo)
    est = int(unit.get("est_calls") or 0)
    res = int(unit.get("reserve_calls") or 0)
    L = ["---", f"fingerprint: {fp}", f"unit: {unit_id}", f"claims_ir: {ir_path.resolve()}",
         f"repo: {Path(repo).resolve()}", f"head: {head}", f"ir_sha256: {ir_sha}", "---", "",
         f"# Work-unit packet: {unit_id} - {unit.get('title', '')}", "",
         "Derived from the claims IR; if `wu_packet.py verify` says STALE, recompile, do not hand-edit.", "",
         "## Unit", "", "```json", json.dumps(unit, indent=2, sort_keys=True), "```", "", "## Claims", ""]
    L += [f"- {c['id']}: {c.get('title', '')} [gates: {', '.join(c.get('gates') or []) or '-'}]" for c in claims]
    L += ["", "## Gates", ""] + [f"- {g['id']}: {g.get('text', '')}" for g in gates]
    L += ["", "## Context", ""] + [f"- {p}" for p in unit.get("context") or []]
    L += ["", "## Acceptance", ""] + [f"- {a}" for a in unit.get("acceptance") or []]
    L += ["", "## Capabilities", ""] + [f"- {a}" for a in unit.get("capabilities") or []]
    L += ["", "## Budget", "", f"- est calls: {est}", f"- reserve calls: {res}",
          f"- hard stop: {HARD_STOP_FACTOR * est} calls", "", "## Progress rule", "", PROGRESS_RULE, ""]
    return "\n".join(L)


def _header(packet: Path) -> dict:
    hdr: dict = {}
    lines = packet.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise Refused(f"{packet} has no packet header")
    for ln in lines[1:]:
        if ln == "---":
            return hdr
        k, _, v = ln.partition(": ")
        hdr[k] = v
    raise Refused(f"{packet} header is not closed")


def verify(packet: Path) -> bool:
    h = _header(packet)
    fp = fingerprint(Path(h["claims_ir"]), h["unit"], h["repo"])[0]
    return fp == h.get("fingerprint")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="wu_packet")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile")
    c.add_argument("--claims", required=True)
    c.add_argument("--unit", required=True)
    c.add_argument("--repo", required=True)
    c.add_argument("--out", required=True)
    v = sub.add_parser("verify")
    v.add_argument("packet")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "compile":
            text = render(Path(args.claims), args.unit, args.repo)
            Path(args.out).write_text(text, encoding="utf-8", newline="\n")
            print(f"wrote {args.out}")
            return 0
        ok = verify(Path(args.packet))
    except (Refused, OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print("CURRENT" if ok else "STALE")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
