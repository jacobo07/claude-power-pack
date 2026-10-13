"""Ph1c deterministic-first gate (D28 WU-D1c): run a unit's `pre` commands before the chain arms a worker.

Packet front matter (optional, between `---` lines at the top):
    class: DETERMINISTIC | SEARCH | MODEL | OWNER_REQUIRED     (absent = MODEL, the old behaviour)
    pre_timeout_s: 600                                         (default 600, max 900)
    pre:
      - python tools/x.py
Zero model. gsdx_chain calls apply(); CPP_CHAIN_PRE=off is the kill switch.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CLASSES = {"DETERMINISTIC", "SEARCH", "MODEL", "OWNER_REQUIRED"}
USED_MODEL = "DETERMINISTIC_USED_MODEL"
_TYPED = re.compile(r"^[ \t>*_\-|]*(UNKNOWN|CONFLICT)\b", re.M)


def _unq(v: str) -> str:
    v = v.strip()
    return v[1:-1] if len(v) > 1 and v[0] == v[-1] and v[0] in "'\"" and v[0] not in v[1:-1] else v


def front_matter(path) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out, key = {}, None
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        m = re.match(r"^\s+-\s+(.*\S)\s*$", ln)
        if m and key == "pre":
            out["pre"].append(_unq(m.group(1)))
            continue
        m = re.match(r"^([A-Za-z_]+)\s*:\s*(.*?)\s*$", ln)
        if m:
            key, val = m.group(1), m.group(2)
            out[key] = [] if key == "pre" and not val else _unq(val)
    return out


def klass(fm: dict) -> str:
    c = str(fm.get("class", "MODEL")).upper()
    return c if c in CLASSES else "MODEL"


def timeout_s(fm: dict) -> int:
    try:
        return max(1, min(900, int(fm.get("pre_timeout_s", 600))))
    except ValueError:
        return 600


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_pre(cmds: list, cwd, timeout) -> dict:
    """Run each command in order; stop at the first non-zero rc (124 = timed out). Last 4 KB of output."""
    res, t0, rc, tail = [], time.time(), 0, ""
    for c in cmds:
        s = time.time()
        pr = subprocess.Popen(c, shell=True, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                              errors="replace", stdin=subprocess.DEVNULL)
        try:
            out, _ = pr.communicate(timeout=timeout)
            rc, tail = pr.returncode, (out or "")[-4096:]
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":   # shell=True: killing cmd alone leaves the child holding the pipe
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pr.pid)], capture_output=True)
            else:
                pr.kill()
            try:
                out, _ = pr.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                out = ""
            rc, tail = 124, ("timeout after %ss " % timeout) + (out or "")[-4000:]
        res.append({"cmd": c, "rc": rc, "seconds": round(time.time() - s, 2), "tail": tail})
        if rc != 0:
            break
    return {"rc": rc, "seconds": round(time.time() - t0, 2), "tail": tail, "steps": res}


def pre_path(packet) -> Path:
    return Path(str(packet) + ".pre.json")


def apply(chain: dict, row: dict, receipt_done, runner=run_pre) -> dict:
    """row is decide()'s `arm` row. Returns it unchanged (MODEL/no pre), or pre_failed / closed_deterministic,
    or the arm row annotated with `pre_json`. `receipt_done(unit) -> bool` is the receipt_judge reading."""
    unit = next(u for u in chain["units"] if u["id"] == row["unit"])
    packet = Path(unit["packet"])
    fm = front_matter(packet)
    cmds = fm.get("pre") or []
    if not fm or not isinstance(cmds, list):
        return row
    cls = klass(fm)
    if cmds:
        sha, pj = _sha(packet), pre_path(packet)
        rec = None
        try:
            rec = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if not rec or rec.get("sha") != sha:       # once per packet sha
            rec = {"sha": sha, **runner(cmds, unit.get("cwd") or chain["root"], timeout_s(fm))}
            pj.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        if rec.get("rc") != 0:
            return {"action": "pre_failed", "unit": unit["id"], "rc": rec["rc"], "pre_json": str(pj),
                    "why": str(rec.get("tail", ""))[-300:]}
        row = dict(row, pre_json=str(pj))
    if cls == "DETERMINISTIC" and receipt_done(unit):
        return {"action": "closed_deterministic", "unit": unit["id"], **({"pre_json": row["pre_json"]} if "pre_json" in row else {})}
    return row


def used_model(receipt_text: str, cls: str, model_calls: int) -> str | None:
    """DETERMINISTIC_USED_MODEL: a DETERMINISTIC unit that spent model calls without a typed UNKNOWN/CONFLICT line."""
    if cls == "DETERMINISTIC" and model_calls > 0 and not _TYPED.search(receipt_text):
        return USED_MODEL
    return None
