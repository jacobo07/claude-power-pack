"""Context Rent census (ctx-rent-x W0): where the processed tokens go, by class, CCR generation and carried content.

Three read-only measurements over Claude Code transcripts (`~/.claude/projects/**/*.jsonl`), every figure labelled with
the PLANE it was read on (`--plane`, default: this host's hostname) because a number from another host's transcripts is
quoted evidence, never data this host can re-read.

  estate      per class (top-level / subagent / worker:<kind>) AND per loaded CCR generation: sessions, calls, processed
              input (input + cache_read + cache_creation, summed over calls), call-1 floor, floor rent = calls x floor.
              A session with no CCR `start` receipt is generation UNKNOWN, never "current".
  carriage    per class of content, the ESTIMATED tokens carried on an average call (floor from call 1 is measured, the rest
              is characters / 4 and is APPROX); `calibration` is estimate / actual input so the estimate can be judged.
  dead-rent   offline Belady upper bound: tokens of each tool_result carried on calls AFTER its last reference. A reference
              is a distinctive token (>= 10 chars, with a path/identifier shape) of the result that the assistant later
              wrote in text or a tool call. A result used without quoting is counted dead, so the figure is an UPPER BOUND.

A call is a unique assistant message.id carrying usage (the same definition as ctx-rent-obs/b2/w6_estate.py).
Usage: ctx_rent.py estate --since ISO --until ISO | diff A.json B.json | carriage FILE | dead-rent FILE [FILE ...]
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_release as cr  # noqa: E402

PROJECTS = Path.home() / ".claude" / "projects"
CHARS_PER_TOKEN = 4  # APPROX: the only conversion this module makes between characters and tokens
COMPACT_DROP = 0.4   # a call whose input falls by more than 40 % (and > 20K) is a compaction boundary
TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\:-]{10,}")
CLASSES = ("thinking", "assistant_text", "tool_use", "tool_result", "user_text", "attachment")


def _size(x) -> int:
    if x is None:
        return 0
    return len(x) if isinstance(x, str) else len(json.dumps(x, ensure_ascii=False))


def _text_of(x) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return "\n".join(_text_of(b.get("text") if "text" in b else b.get("content")) if isinstance(b, dict) else _text_of(b) for b in x)
    return "" if x is None else str(x)


def _distinct(text: str) -> set[str]:
    return {t for t in TOKEN_RE.findall(text) if any(c in t for c in "/\\._-:") or any(c.isdigit() for c in t)}


def _compacted(prev: int | None, tot: int) -> bool:
    return prev is not None and tot < prev * (1 - COMPACT_DROP) and prev - tot > 20000


def events(path: Path):
    """Ordered semantic events: ('call', mid, ts, input_total, output) and ('blk', class, chars, tool_use_id, text)."""
    seen: set[str] = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            t = e.get("type")
            if t == "attachment":
                yield ("blk", "attachment", _size(e.get("attachment")), None, "")
                continue
            msg = e.get("message")
            if t not in ("assistant", "user") or not isinstance(msg, dict):
                continue
            if t == "assistant":
                u, mid = msg.get("usage"), msg.get("id")
                if u and mid and mid not in seen:
                    seen.add(mid)
                    tot = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                    yield ("call", mid, e.get("timestamp") or "", tot, u.get("output_tokens") or 0)
            content = msg.get("content")
            if isinstance(content, str):
                yield ("blk", "assistant_text" if t == "assistant" else "user_text", len(content), None, content if t == "assistant" else "")
                continue
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "thinking":
                    yield ("blk", "thinking", len(b.get("thinking") or ""), None, "")
                elif bt == "text":
                    txt = b.get("text") or ""
                    yield ("blk", "assistant_text" if t == "assistant" else "user_text", len(txt), None, txt if t == "assistant" else "")
                elif bt == "tool_use":
                    inp = json.dumps(b.get("input"), ensure_ascii=False)
                    yield ("blk", "tool_use", len(inp), b.get("id"), inp)
                elif bt == "tool_result":
                    txt = _text_of(b.get("content"))
                    yield ("blk", "tool_result", len(txt), b.get("tool_use_id"), txt)


def carriage(path: Path) -> dict:
    """Per-class mean ESTIMATED tokens carried per call, plus the measured floor and the estimate/actual calibration."""
    run = dict.fromkeys(CLASSES, 0)
    calls, floor, prev, comp = [], None, None, 0
    for ev in events(path):
        if ev[0] == "blk":
            run[ev[1]] += ev[2]
            continue
        tot = ev[3]
        if floor is None:
            floor = tot
        if _compacted(prev, tot):
            run = dict.fromkeys(CLASSES, 0)  # compaction: the carried history is gone, the floor stays
            comp += 1
        prev = tot
        calls.append((tot, dict(run)))
    if not calls:
        return {"calls": 0}
    n = len(calls)
    mean = {c: round(sum(r[c] for _, r in calls) / n / CHARS_PER_TOKEN) for c in CLASSES}
    est = floor + sum(mean.values())
    act = round(sum(t for t, _ in calls) / n)
    return {"calls": n, "floor_measured": floor, "mean_actual_input": act, "mean_est_by_class_APPROX": mean,
            "mean_est_total_APPROX": est, "calibration_est_over_actual": round(est / act, 3) if act else None,
            "unattributed_APPROX": act - est, "compactions": comp}


def dead_rent(path: Path) -> dict:
    """Offline Belady upper bound on tool_result tokens carried after their last reference.

    Call k (0-based) carries every block that appeared before it. A result seen after call idx first rides on call idx+1
    (entry). A token the assistant writes after call idx is the output OF call idx: last_tok[token] = idx means 'call idx
    was still using it', so the result is dead on the calls strictly after the last such idx.
    """
    idx = -1
    results: dict[str, dict] = {}
    origin: dict[str, set[str]] = {}
    last_tok: dict[str, int] = {}
    boundaries: list[int] = []
    prev = None
    for ev in events(path):
        if ev[0] == "call":
            tot = ev[3]
            idx += 1
            if _compacted(prev, tot):
                boundaries.append(idx)
            prev = tot
            continue
        _, cls, chars, tid, text = ev
        if cls == "tool_use" and tid:
            origin[tid] = _distinct(text)
        if cls in ("assistant_text", "tool_use") and text:
            for tk in _distinct(text):
                last_tok[tk] = idx
        elif cls == "tool_result" and tid and chars:
            results[tid] = {"entry": idx + 1, "tokens": chars / CHARS_PER_TOKEN, "toks": _distinct(text[:20000]) - origin.get(tid, set())}
    total_calls = idx + 1
    if total_calls <= 0:
        return {"calls": 0}
    carried = dead = never = 0.0
    n_res = 0
    for r in results.values():
        end = next((b for b in boundaries if b > r["entry"]), total_calls)
        span = end - r["entry"]            # calls entry .. end-1 carry the result
        if span <= 0:
            continue
        n_res += 1
        refs = [last_tok[t] for t in r["toks"] if last_tok.get(t, -1) >= r["entry"]]
        last = min(max(refs), end - 1) if refs else None
        carried += r["tokens"] * span
        if last is None:
            dead += r["tokens"] * span
            never += r["tokens"] * span
        else:
            dead += r["tokens"] * (end - 1 - last)  # calls strictly after the last call that still used it
    return {"calls": total_calls, "tool_results": n_res, "result_rent_tokens_APPROX": round(carried),
            "dead_rent_tokens_UPPER_BOUND": round(dead), "dead_share_of_result_rent": round(dead / carried, 3) if carried else None,
            "never_referenced_rent_tokens": round(never), "compaction_boundaries": len(boundaries)}


def processed_input(path: Path) -> int:
    return sum(ev[3] for ev in events(path) if ev[0] == "call")


def generation_of(sid: str, receipt_dirs: list[Path], active: str | None) -> str:
    st = cr.last_start(receipt_dirs, sid) if receipt_dirs else None
    if st is None or "releaseId" not in st:
        return "UNKNOWN"
    if st["releaseId"] is None:
        return "DEV"
    if active is None:
        return str(st["releaseId"])
    return f"CURRENT:{st['releaseId']}" if st["releaseId"] == active else f"STALE:{st['releaseId']}"


def estate(projects: Path, since: str, until: str, receipt_dirs: list[Path], active: str | None, worker_kind: dict[str, str],
           plane: str) -> dict:
    lo = time.mktime(time.strptime(since[:10], "%Y-%m-%d")) - 86400
    agg: dict[str, dict] = {}
    n_files = 0
    for p in projects.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < lo:
                continue
        except OSError:
            continue
        floor, calls, processed = None, 0, 0
        for ev in events(p):
            if ev[0] != "call":
                continue
            if floor is None:
                floor = ev[3]
            if since <= ev[2] < until:
                calls += 1
                processed += ev[3]
        if not calls:
            continue
        n_files += 1
        sid = p.stem
        cls = "subagent" if "subagents" in p.parts else f"worker:{worker_kind[sid]}" if sid in worker_kind else "top-level"
        gen = "UNKNOWN" if cls == "subagent" else generation_of(sid, receipt_dirs, active)
        a = agg.setdefault(cls, {}).setdefault(gen, {"sessions": 0, "calls": 0, "processed": 0, "floor_rent": 0, "floor_sum": 0})
        a["sessions"] += 1
        a["calls"] += calls
        a["processed"] += processed
        a["floor_rent"] += calls * (floor or 0)
        a["floor_sum"] += floor or 0
    tot = {"sessions": 0, "calls": 0, "processed": 0, "floor_rent": 0}
    for gens in agg.values():
        for a in gens.values():
            a["mean_floor"] = round(a["floor_sum"] / a["sessions"])
            a["floor_share"] = round(a["floor_rent"] / a["processed"], 3) if a["processed"] else None
            for k in tot:
                tot[k] += a[k]
    return {"plane": plane, "since": since, "until": until, "active_release": active, "classes": agg, "total": tot,
            "files_read": n_files,
            "method": "calls = unique assistant message.id with usage inside the window; floor = call-1 input incl. cache; "
                      "floor_rent = calls x floor; generation from the newest CCR start receipt by sid, none = UNKNOWN"}


def diff(a: dict, b: dict) -> list[dict]:
    """Per (class, generation) delta of two estate documents of the SAME plane. Cells present on one side only are kept."""
    if a.get("plane") != b.get("plane"):
        raise SystemExit(f"refused: planes differ ({a.get('plane')} vs {b.get('plane')}); a cross-plane delta is not a measurement")
    keys = sorted({(c, g) for d in (a, b) for c, gs in d["classes"].items() for g in gs})
    rows = []
    for c, g in keys:
        x, y = a["classes"].get(c, {}).get(g), b["classes"].get(c, {}).get(g)
        pick = ("sessions", "calls", "processed", "mean_floor")
        row = {"class": c, "generation": g, "from": x and {k: x[k] for k in pick}, "to": y and {k: y[k] for k in pick}}
        if x and y:
            row["delta_processed"] = y["processed"] - x["processed"]
            row["delta_mean_floor"] = y["mean_floor"] - x["mean_floor"]
        rows.append(row)
    return rows


def class_of(p: Path, worker_kind: dict[str, str]) -> str:
    """Same Work Class rule as `estate`: subagent / worker:<kind> / top-level."""
    return "subagent" if "subagents" in p.parts else f"worker:{worker_kind[p.stem]}" if p.stem in worker_kind else "top-level"


def regret(files: list[Path], worker_kind: dict[str, str], min_calls: int = 10) -> dict:
    """ICC-08 Context Policy Regret = actual tool_result carriage minus the offline Belady bound, i.e. the dead rent,
    per Work Class. An UPPER BOUND (a result used without quoting counts dead). Transcripts under `min_calls` calls are
    listed as skipped, never averaged in: a 2-call smoke run has no policy to regret."""
    agg: dict[str, dict] = {}
    skipped = []
    for f in files:
        d, proc = dead_rent(f), processed_input(f)
        if d.get("calls", 0) < min_calls:
            skipped.append({"file": f.name, "calls": d.get("calls", 0)})
            continue
        a = agg.setdefault(class_of(f, worker_kind), {"sessions": 0, "calls": 0, "processed_input": 0,
                                                       "result_rent": 0, "regret_dead_rent_UPPER_BOUND": 0})
        a["sessions"] += 1
        a["calls"] += d["calls"]
        a["processed_input"] += proc
        a["result_rent"] += d["result_rent_tokens_APPROX"]
        a["regret_dead_rent_UPPER_BOUND"] += d["dead_rent_tokens_UPPER_BOUND"]
    for a in agg.values():
        a["regret_share_of_processed"] = round(a["regret_dead_rent_UPPER_BOUND"] / a["processed_input"], 3) if a["processed_input"] else None
        a["regret_share_of_result_rent"] = round(a["regret_dead_rent_UPPER_BOUND"] / a["result_rent"], 3) if a["result_rent"] else None
    return {"classes": agg, "skipped": skipped, "sessions_measured": sum(a["sessions"] for a in agg.values())}


def _worker_kinds() -> dict[str, str]:
    try:
        import gsd_mission as g
        out = {}
        for m in g.all_missions():
            o = m.get("owner")
            if isinstance(o, dict) and o.get("session_id"):
                out[o["session_id"]] = o.get("kind") or "full"
        return out
    except Exception as exc:  # noqa: BLE001 -- reported, not hidden: no registry means every worker reads as top-level
        print(f"warning: mission registry unreadable ({exc!r}); workers are counted as top-level", file=sys.stderr)
        return {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plane", default=socket.gethostname())
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estate")
    e.add_argument("--since", required=True)
    e.add_argument("--until", required=True)
    e.add_argument("--projects", type=Path, default=PROJECTS)
    e.add_argument("--root", type=Path, default=cr.DEFAULT_ROOT)
    e.add_argument("--receipts", type=Path, action="append", default=[])
    e.add_argument("--out", type=Path)
    d = sub.add_parser("diff")
    d.add_argument("a", type=Path)
    d.add_argument("b", type=Path)
    c = sub.add_parser("carriage")
    c.add_argument("file", type=Path)
    r = sub.add_parser("dead-rent")
    r.add_argument("files", type=Path, nargs="+")
    g = sub.add_parser("regret", help="dead rent (carriage minus Belady bound) per Work Class (ICC Phase 6)")
    g.add_argument("files", type=Path, nargs="+")
    g.add_argument("--min-calls", type=int, default=10)
    a = ap.parse_args(argv)
    if a.cmd == "regret":
        print(json.dumps({"plane": a.plane, **regret(a.files, _worker_kinds(), a.min_calls)}, indent=1))
        return 0
    if a.cmd == "estate":
        try:
            active = json.loads((a.root / "ACTIVE.json").read_text(encoding="utf-8")).get("release")
        except (OSError, ValueError):
            active = None
        doc = estate(a.projects, a.since, a.until, [a.root / "state" / "receipts", *a.receipts], active, _worker_kinds(), a.plane)
        if a.out:
            a.out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(doc, indent=1))
    elif a.cmd == "diff":
        print(json.dumps(diff(json.loads(a.a.read_text()), json.loads(a.b.read_text())), indent=1))
    elif a.cmd == "carriage":
        print(json.dumps({"plane": a.plane, "file": a.file.name, **carriage(a.file)}, indent=1))
    else:
        print(json.dumps([{"plane": a.plane, "file": f.name, "processed_input": processed_input(f), **dead_rent(f)} for f in a.files], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
