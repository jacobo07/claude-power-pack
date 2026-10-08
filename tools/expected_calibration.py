"""Calibrate the expected-completion estimator (E1): per-call context growth g and call-count error.

Deterministic, no model. Attribution is mission_spend's (`autopsy`, `mission_sessions`, `_attributed`);
this file only adds what `autopsy_transcript` does not keep: the per-call context SERIES, so a session
can be split where context drops > 30% (autocompact / compaction, spec audit A3) and g fitted per segment:
    g = 2 x (mean - first) / (n - 1)      (context grows linearly: ctx_i = F + g x i)
Subagent transcripts feed their own profile, never `top-level-worker`.

  expected_calibration.py --mission M [--since ISO] | --transcript PATH [--transcript PATH ...]  [--out F]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_spend as ms  # noqa: E402

DROP = 0.30
MIN_SEGMENT = 3


def series(path: Path) -> list[dict]:
    """[{ctx, ts, tok}] per assistant call, deduped by message id exactly as `autopsy_transcript`."""
    seen, out = set(), []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") if isinstance(r, dict) else None
            if not isinstance(m, dict):
                continue
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            out.append({"ctx": sum(int(u.get(k) or 0) for k in ms._UK[:3]),
                        "tok": sum(int(u.get(k) or 0) for k in ms._UK), "ts": r.get("timestamp") or ""})
    return out


def segments(calls: list[dict]) -> list[list[dict]]:
    segs, cur = [], []
    for c in calls:
        if cur and c["ctx"] < cur[-1]["ctx"] * (1 - DROP):
            segs.append(cur)
            cur = []
        cur.append(c)
    if cur:
        segs.append(cur)
    return segs


def fit(calls: list[dict]) -> dict:
    """Segment-wise g; segments shorter than MIN_SEGMENT are counted but not fitted (n=1 has no slope)."""
    rows, gw, gn = [], 0.0, 0
    for s in segments(calls):
        n, first = len(s), s[0]["ctx"]
        mean = sum(c["ctx"] for c in s) / n
        g = 2 * (mean - first) / (n - 1) if n >= MIN_SEGMENT else None
        rows.append({"calls": n, "first_ctx": first, "mean_ctx": round(mean), "g": None if g is None else round(g)})
        if g is not None:
            gw += g * n
            gn += n
    return {"calls": len(calls), "processed": sum(c["tok"] for c in calls),
            "first_ctx": calls[0]["ctx"] if calls else None,
            "mean_ctx": round(sum(c["ctx"] for c in calls) / len(calls)) if calls else None,
            "segments": rows, "g": round(gw / gn) if gn else None, "g_calls": gn}


def mission_files(rec: dict) -> list[tuple[str, Path, str]]:
    """[(kind, path, session)] for the mission's own transcripts, via mission_spend's attribution."""
    root = ms.projects_root()
    dirs: list[Path] = []
    for base in (rec.get("work_dir"), rec.get("cwd")):
        for d in (ms.mission_dirs(base, root) if base else []):
            if d not in dirs:
                dirs.append(d)
    ids, prefixes = ms.mission_sessions(rec)
    out = []
    for d in dirs:
        for p in sorted(d.rglob("*.jsonl")):
            if ms._attributed(p, d, ids, prefixes):
                rel = p.relative_to(d)
                out.append(("subagent" if "subagents" in rel.parts else "session", p, str(rel).replace("\\", "/")))
    return out


def spend_since(files, since_iso: str) -> dict:
    tot = after = 0
    for _k, p, _s in files:
        for c in series(p):
            tot += c["tok"]
            if c["ts"] >= since_iso:
                after += c["tok"]
    return {"total": tot, "at_or_after": after, "since": since_iso}


def agent_type(path: Path) -> str | None:
    meta = path.with_name(path.stem + ".meta.json")
    try:
        return json.loads(meta.read_text(encoding="utf-8-sig")).get("agentType")
    except (OSError, ValueError, AttributeError):
        return None


def profile_of(kind: str, path: Path) -> str | None:
    """A top-level session is `top-level-worker`; a subagent is its agentType, or None when unclassifiable
    (an unclassifiable subagent feeds NO profile: it must never leak into top-level-worker)."""
    return "top-level-worker" if kind == "session" else agent_type(path)


def profiles_from(sessions: list[dict], call_samples: list[tuple[int, int]]) -> dict:
    """{profile: {growth_per_call, calls_err?}} -- a profile with no fitted sample gets NO field."""
    by: dict[str, list[dict]] = {}
    for s in sessions:
        if s.get("profile") and s["g"] is not None:
            by.setdefault(s["profile"], []).append(s)
    out = {}
    for prof, ss in by.items():
        w = sum(s["g_calls"] for s in ss)
        g = round(sum(s["g"] * s["g_calls"] for s in ss) / w)
        out[prof] = {"growth_per_call": {
            "value": g, "n": len(ss), "basis": "measured:autopsy-segmented-fit",
            "provenance": "tools/expected_calibration.py: call-weighted mean of g = 2 x (mean - first) / (n - 1) "
                          f"per segment over {len(ss)} session(s), {w} calls"}}
    if call_samples and "top-level-worker" in out:
        errs = [(act - plan) / plan for plan, act in call_samples]
        out["top-level-worker"]["calls_err"] = {
            "value": round(max(0.0, max(errs)), 3), "n": len(call_samples), "basis": "measured:planned-vs-metered-calls",
            "provenance": "high edge of (actual - planned) / planned over completed packet units "
                          + ", ".join(f"{p} planned -> {a} metered" for p, a in call_samples)}
    return out


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="expected_calibration")
    ap.add_argument("--mission", action="append", default=[])
    ap.add_argument("--transcript", action="append", default=[])
    ap.add_argument("--call-sample", action="append", default=[], help="PLANNED:ACTUAL calls of a completed unit")
    ap.add_argument("--since")
    ap.add_argument("--out")
    ap.add_argument("--write-floors", help="merge the fitted fields into this route-floors.json")
    a = ap.parse_args(argv)
    res: dict = {"sessions": []}
    files = []
    for m in a.mission:
        files += mission_files(ms._load_mission(m))
    files += [("session", Path(t), Path(t).name) for t in a.transcript]
    for kind, p, rel in files:
        res["sessions"].append({"file": rel, "kind": kind, "profile": profile_of(kind, p), **fit(series(p))})
    if a.since and a.mission:
        res["spend_window"] = spend_since(files, a.since)
    samples = [tuple(int(x) for x in s.split(":")) for s in a.call_sample]
    res["profiles"] = profiles_from(res["sessions"], samples)
    if a.write_floors:
        fp = Path(a.write_floors)
        floors = json.loads(fp.read_text(encoding="utf-8-sig"))
        for prof, fields in res["profiles"].items():
            if prof in floors["profiles"]:
                floors["profiles"][prof].update(fields)
            else:
                res.setdefault("not_in_floor_table", []).append(prof)
        fp.write_text(json.dumps(floors, indent=2) + "\n", encoding="utf-8")
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
