"""Largest shell tool results of one epoch, ranked by carry (chars x rides), with the command that made them.

A result appended before call k rides calls k..N, so its carry is chars x (N - k + 1). Chars, not tokens: use it
to rank, and take token shares from carry_by_kind.py.
Usage: python shell_results.py <stream.jsonl> [top]
"""
import json, sys


def main(path: str, top: int = 12) -> dict:
    calls, seen, cmd_of, rows = 0, set(), {}, []
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("isSidechain"):
            continue
        m = o.get("message") or {}
        content = m.get("content") if isinstance(m.get("content"), list) else []
        if o.get("type") == "assistant":
            if m.get("id") and m["id"] not in seen and m.get("usage"):
                seen.add(m["id"])
                calls += 1
            for b in content:
                if b.get("type") == "tool_use" and b.get("name") in ("PowerShell", "Bash"):
                    cmd_of[b["id"]] = str((b.get("input") or {}).get("command", ""))
        for b in content:
            if b.get("type") == "tool_result" and b.get("tool_use_id") in cmd_of:
                c = b.get("content")
                text = c if isinstance(c, str) else "".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
                rows.append({"after_call": calls, "chars": len(text), "cmd": cmd_of[b["tool_use_id"]][:160],
                             "head": text[:120]})
    for r in rows:
        r["rides"] = max(calls - r["after_call"], 0)
        r["carry_chars"] = r["chars"] * r["rides"]
    total = sum(r["carry_chars"] for r in rows)
    rows.sort(key=lambda r: -r["carry_chars"])
    return {"calls": calls, "shell_results": len(rows), "carry_chars": total,
            "result_chars": sum(r["chars"] for r in rows), "top": rows[:top]}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 12), indent=1, ensure_ascii=False))
