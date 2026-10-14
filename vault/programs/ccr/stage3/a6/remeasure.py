"""WU-A6 deterministic obligation: re-measure Stage 3 units' processed tokens from their GEX44 run files.
The same rule as drive.sh spent(): every run-<unit>*.jsonl of the unit, assistant lines, first usage per
message id, input + cache_read + cache_creation + output. No model is called.
Usage: python3 remeasure.py <data dir> <unit>...   -> one JSON object {unit: processed} on stdout."""
import glob
import json
import sys

K = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")


def spent(d: str, unit: str) -> int:
    seen, tot = set(), 0
    for f in sorted(glob.glob(f"{d}/run-{unit}*.jsonl")):
        for line in open(f, errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            m = (o.get("message") or {}) if isinstance(o, dict) else {}
            us = m.get("usage") if isinstance(m, dict) else None
            if o.get("type") == "assistant" and isinstance(us, dict) and m.get("id") not in seen:
                seen.add(m.get("id"))
                tot += sum(us.get(k, 0) or 0 for k in K)
    return tot


if __name__ == "__main__":
    print(json.dumps({u: spent(sys.argv[1], u) for u in sys.argv[2:]}))
