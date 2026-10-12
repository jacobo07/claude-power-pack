"""Carry of Read results that a later Read of the same file and range supersedes (dead by construction: the
newer copy is in the transcript). Tokens are apportioned like carry_by_kind.py (text carry by chars x rides).
Usage: python superseded_reads.py <stream.jsonl>
"""
import json, sys
from carry_by_kind import main as by_kind


def main(path: str) -> dict:
    base = by_kind(path)
    calls, seen, reads, results = 0, set(), {}, []
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        m = o.get("message") or {}
        content = m.get("content") if isinstance(m.get("content"), list) else []
        if o.get("type") == "assistant":
            if m.get("id") and m["id"] not in seen and m.get("usage"):
                seen.add(m["id"])
                calls += 1
            for b in content:
                if b.get("type") == "tool_use" and b.get("name") == "Read":
                    i = b.get("input", {})
                    reads[b.get("id")] = (str(i.get("file_path", "")).lower().replace("\\", "/"), i.get("offset"), i.get("limit"))
        elif o.get("type") == "user":
            for b in content:
                if b.get("type") == "tool_result" and b.get("tool_use_id") in reads:
                    c = b.get("content")
                    n = len(c) if isinstance(c, str) else sum(len(x.get("text", "")) for x in (c or []) if isinstance(x, dict))
                    results.append((calls, reads[b["tool_use_id"]], n))
    total_calls = base["calls"]
    dead_chars = 0
    for idx, (k, key, n) in enumerate(results):
        later = next((k2 for k2, key2, _ in results[idx + 1:] if key2[0] == key[0] and (key2[1:] == key[1:] or key2[1:] == (None, None))), None)
        if later is not None:
            dead_chars += n * (total_calls - later)  # rides from the superseding read onwards are dead
    read_chars = sum(n * (total_calls - k) for k, _, n in results) or 1
    read_tok = base["shares_of_processed"].get("result:Read", 0) * base["processed"]
    dead_tok = round(read_tok * dead_chars / read_chars)
    return {"reads": len(results), "distinct": len({r[1] for r in results}), "read_result_tok": round(read_tok),
            "superseded_tok": dead_tok, "superseded_share_of_processed": round(dead_tok / base["processed"], 3)}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=1))
