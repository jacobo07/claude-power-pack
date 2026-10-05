"""Pillar K resident-rent scan (read-only, deterministic, no model call).

For the N newest top-level transcripts under ~/.claude/projects (any project), sums every hook_additional_context
element by event and by leading marker, and counts real user prompts (user rows whose content is a string, not a
tool_result list). Rent of a recurring injection = chars per occurrence x occurrences: a per-prompt injection is paid
once per prompt, a SessionStart one once per session (plus once per /clear or resume).

    python k_rent_scan.py [--n 40] [--min-bytes 200000]

Prints one ROW line per (event, marker) and a TOTAL line; chars are characters of the injected text, the unit the
floor gate uses. Nothing is written.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"


def marker(text):
    """A stable producer label from the element's first non-blank line: a leading [Tag], else its first 4 words."""
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    m = re.match(r"^(\[[^\]]{1,40}\]|<[A-Z_]{3,30}>|-{2,}\s*[^-]{1,40}-{2,})", first)
    if m:
        return m.group(1)
    return " ".join(re.findall(r"[A-Za-z0-9_-]+", first)[:4]) or "<blank>"


def scan(path):
    per = defaultdict(lambda: [0, 0])   # (event, marker) -> [chars, occurrences]
    prompts = 0
    with open(path, "rb") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            if r.get("type") == "user" and isinstance((r.get("message") or {}).get("content"), str):
                prompts += 1
            a = r.get("attachment") or {}
            if a.get("type") != "hook_additional_context":
                continue
            content = a.get("content")
            for el in content if isinstance(content, list) else [content]:
                s = el if isinstance(el, str) else json.dumps(el)
                for part in re.split(r"\n(?=\[[A-Z][^\]]{1,40}\] )", s):   # composite hub output: one row per [Tag] section
                    k = (a.get("hookEvent"), marker(part))
                    per[k][0] += len(part)
                    per[k][1] += 1
    return prompts, per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--min-bytes", type=int, default=200000)
    args = ap.parse_args()
    files = [p for p in PROJECTS.glob("*/*.jsonl") if p.stat().st_size >= args.min_bytes]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    files = files[: args.n]
    agg = defaultdict(lambda: [0, 0, 0])   # chars, occurrences, sessions
    total_prompts = 0
    for p in files:
        prompts, per = scan(p)
        total_prompts += prompts
        for k, (c, o) in per.items():
            agg[k][0] += c
            agg[k][1] += o
            agg[k][2] += 1
    n = len(files)
    print(f"SCAN sessions={n} prompts={total_prompts} min_bytes={args.min_bytes}")
    grand = 0
    for (ev, mk), (c, o, s) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        grand += c
        print(f"ROW event={ev} marker={mk!r} chars_total={c} occurrences={o} sessions={s} "
              f"chars_per_occurrence={c // max(o, 1)} chars_per_session={c // max(n, 1)}")
    print(f"TOTAL hook_additional_context chars={grand} per_session={grand // max(n, 1)} "
          f"per_prompt={grand // max(total_prompts, 1)}")


if __name__ == "__main__":
    main()
