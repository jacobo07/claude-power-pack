"""CCR spend census (Stage 3 WU-A0): processed tokens per session, deterministic, content-free.

processed = input + cache_read + cache_creation + output, summed over assistant messages deduplicated by
message id. One message can appear on several lines (stream-json and raw transcripts write one line per
content block, a resumed run replays its history): each usage field takes the largest value seen for that
id, so a repeat books nothing twice and a partial streaming count never wins over the final one.
stream-json assistant lines carry the output count from before the reply streamed (A3: 341 summed over 32
messages, 33,009 in its `result` line), so a session's output is the larger of the per-message sum and the
sum of its `result` lines (one per invocation; input and cache fields agree exactly between the two).

Three line formats, detected per line, so one call can read a mix:
  pack projection   {"t": "assistant", "mid": ..., "usage": {...}}            session = file stem
  stream-json       {"type": "assistant", "session_id": ..., "message": {"id", "usage"}}
  raw transcript    {"type": "assistant", "sessionId": ..., "message": {"id", "usage"}}
A file with no assistant usage at all is UNKNOWN (None), never 0.

    python tools/ccr_spend_census.py measure <file>...            # one JSON row per session
    python tools/ccr_spend_census.py census --data <dir> [--table]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FIELDS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")
GEX44 = "Linux plane GEX44, host 2.1.296"
LAPTOP = "laptop projection"


def _assistant(d: dict) -> tuple[str | None, str | None, dict | None]:
    """(session id or None, message id or None, usage) of an assistant line, else (None, None, None)."""
    if d.get("t") == "assistant":
        return None, d.get("mid"), d.get("usage")
    if d.get("type") == "assistant" and isinstance(d.get("message"), dict):
        m = d["message"]
        return d.get("session_id") or d.get("sessionId"), m.get("id"), m.get("usage")
    return None, None, None


def measure(paths, session: str | None = None) -> dict[str, dict]:
    """{session: {processed, calls, files}} over `paths`. `session` forces one key for every line (a
    projection has no session id on its lines; its file stem is used otherwise)."""
    per: dict[str, dict] = {}
    for p in map(Path, paths):
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines()):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            if d.get("type") == "result" and isinstance(d.get("usage"), dict):
                s = per.setdefault(session or d.get("session_id") or p.stem, {"msgs": {}, "files": [], "res": 0})
                s["res"] += int(d["usage"].get("output_tokens") or 0)
                continue
            sid, mid, usage = _assistant(d)
            if not isinstance(usage, dict):
                continue
            key = session or sid or p.stem
            s = per.setdefault(key, {"msgs": {}, "files": [], "res": 0})
            if str(p) not in s["files"]:
                s["files"].append(str(p))
            mid = mid or f"{p}:{n}"                     # no id: the line is its own message
            m = s["msgs"].setdefault(mid, dict.fromkeys(FIELDS, 0))
            for f in FIELDS:
                m[f] = max(m[f], int(usage.get(f) or 0))
    out = {}
    for k, s in per.items():
        if not s["msgs"]:
            continue                                     # a result line alone is not a measurement
        msg_out = sum(m["output_tokens"] for m in s["msgs"].values())
        out[k] = {"processed": sum(sum(m.values()) for m in s["msgs"].values()) - msg_out + max(msg_out, s["res"]),
                  "calls": len(s["msgs"]), "files": s["files"], "output_from_result": s["res"] > msg_out}
    return out


def measure_one(paths, session: str) -> int | None:
    got = measure(paths, session).get(session)
    return got["processed"] if got else None


# --- The Stage 3 A0 census -----------------------------------------------------------------------------
STAGE2 = ("E1", "M1", "W1", "V1", "X1")


def _stage2_rows(pack: Path) -> list[dict]:
    rows = []
    for m in json.loads((pack / "missions.json").read_text(encoding="utf-8")):
        pk = (m.get("packet") or "").replace("\\", "/")
        if "/programs/ccr/stage2/WU-" not in pk:
            continue
        unit = pk.rsplit("WU-", 1)[1].removesuffix(".md")
        for sid in m.get("owners") or []:
            src = pack / "sessions" / f"{sid}.jsonl"
            rows.append({"row": f"Stage 2 {unit} ({m['id']})", "session": sid, "plane": LAPTOP,
                         "source": str(src),
                         "processed": measure_one([src], sid) if src.exists() else None})
    order = {u: i for i, u in enumerate(STAGE2)}
    return sorted(rows, key=lambda r: order.get(r["row"].split()[2], 99))


def _v1_rows(pack: Path) -> list[dict]:
    rows = []
    for src in sorted((pack / "v1").glob("*.jsonl")):
        sid = f"ext-ccr-v1-{src.stem.replace('stream-', '')}"
        rows.append({"row": f"V1 canary {src.stem}", "session": sid, "plane": LAPTOP, "source": str(src),
                     "processed": measure_one([src], sid)})
    rows.append({"row": "V1 canary r6-CCR (killed by host memory reaper, no stream)", "session": None,
                 "plane": LAPTOP, "source": None, "processed": None})
    return rows


def _gex44_rows(data: Path) -> list[dict]:
    """One row per Stage 3 session named in drive.log; every run file of that sid is read together (a
    resumed unit writes a second file that replays the first one's history)."""
    sids: dict[str, str] = {}
    for line in (data / "drive.log").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) > 3 and parts[1] == "start":
            sid = next((x[4:] for x in parts if x.startswith("sid=")), None)
            if sid:
                sids.setdefault(sid, parts[2])
    rows = []
    for sid, unit in sids.items():
        files = sorted(f for f in data.glob(f"run-{unit}*.jsonl") if sid in f.read_text(encoding="utf-8",
                                                                                          errors="replace"))
        got = measure(files).get(sid) if files else None
        rows.append({"row": f"Stage 3 {unit}", "session": sid, "plane": GEX44,
                     "source": ", ".join(str(f) for f in files) or None,
                     "processed": got["processed"] if got else None})
    return rows


def census(data: Path) -> dict:
    pack = data / "pack"
    rows = _stage2_rows(pack) + _v1_rows(pack) + _gex44_rows(data)
    known = [r["processed"] for r in rows if r["processed"] is not None]
    return {"rows": rows, "sum_known": sum(known), "unknown": [r["row"] for r in rows if r["processed"] is None]}


def table(c: dict) -> str:
    out = ["| row | session | plane | source | processed |", "|---|---|---|---|---:|"]
    for r in c["rows"]:
        p = "UNKNOWN" if r["processed"] is None else f"{r['processed']:,}"
        out.append(f"| {r['row']} | {r['session'] or '--'} | {r['plane']} | {r['source'] or '--'} | {p} |")
    out.append(f"| **sum (known rows)** | | | | **{c['sum_known']:,}** |")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    me = sub.add_parser("measure")
    me.add_argument("files", nargs="+")
    me.add_argument("--session")
    ce = sub.add_parser("census")
    ce.add_argument("--data", required=True)
    ce.add_argument("--table", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "measure":
        print(json.dumps(measure(a.files, a.session), sort_keys=True))
        return 0
    c = census(Path(a.data))
    print(table(c) if a.table else json.dumps(c, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
