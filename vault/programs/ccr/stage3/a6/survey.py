"""WU-A6 survey: per projected session, was a CCR Work Unit declared at start (receipt `start.unit`), and what
did the first main-chain call carry (input + cache_read + cache_creation)? Joined to mission records by owner sid.
Content-free inputs only. Usage: python3 survey.py <pack> > sessions.json"""
import glob, json, sys
from pathlib import Path


def first_ctx(path: Path):
    for line in open(path, errors="replace"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        u = o.get("usage")
        if o.get("role") == "assistant" and isinstance(u, dict) and not o.get("sidechain"):
            return sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens",
                                                     "cache_creation_input_tokens")), o.get("model"), o.get("ts")
    return None, None, None


def main(pack: str) -> int:
    pack = Path(pack)
    owner = {}
    for m in json.loads((pack / "missions.json").read_text(encoding="utf-8")):
        for i, sid in enumerate(m.get("owners") or []):
            owner[sid] = {"mission": m["id"], "epoch_ix": i, "packet": m.get("packet"), "state": m.get("state"),
                          "created": m.get("created"), "token_estimate": m.get("token_estimate")}
    rows = []
    for f in glob.glob(str(pack / "receipts" / "*" / "*.jsonl")):
        for line in open(f, errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if o.get("ev") != "start":
                continue
            sid = o.get("sid")
            proj = pack / "sessions" / f"{sid}.jsonl"
            ctx, model, ts = first_ctx(proj) if proj.is_file() else (None, None, None)
            unit = o.get("unit")
            rows.append({"sid": sid, "ts": ts, "interactive": o.get("interactive"), "modes": o.get("modes"),
                         "unit": unit.get("cls") if isinstance(unit, dict) else unit,
                         "first_ctx": ctx, "model": model, **owner.get(sid, {})})
    rows.sort(key=lambda r: r["ts"] or "")
    json.dump(rows, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
