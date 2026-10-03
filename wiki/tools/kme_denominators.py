"""Freeze the KME audit denominators from a kme_report.py JSON output.

command: python wiki/tools/kme_denominators.py <report_all.json> <out.json>

The report comes from:
  python wiki/tools/kme_token_audit.py --host local --out local.json <KobiiCraft/KME project dirs>
  python3 wiki/tools/kme_token_audit.py --host gex44 --expand --out gex44.json <a5/a7/b001/main projects roots>
  python wiki/tools/kme_report.py report_all.json local.json gex44.json
"""
import json
import sys

CLASSIFICATION = ("KME_PATH or KME_STRONG (share of tool calls touching KME >= 0.30, or user "
                  "mentions >= 2 with share >= 0.10); GEX44 a5/a7 env projects by path")
CAVEAT = ("API-equivalent ESTIMATE at official per-MTok prices (cache write 1.25x / 2x input by "
          "TTL); not the Owner's subscription meter")


def main(src, dst):
    rep = json.load(open(src, encoding="utf-8"))
    out = {}
    for host, h in rep["hosts"].items():
        t = h["tokens"]
        out["KME-L" if host == "local" else "KME-G"] = {
            "source": "wiki/tools/kme_token_audit.py + wiki/tools/kme_report.py (see module docstring)",
            "sessions_active": h["active_sessions"], "sessions_dead": h["dead_sessions"],
            "calls": t["calls"], "input": t["inp"], "cache_write": t["cw"],
            "cache_write_1h": t["cw1h"], "cache_write_5m": t["cw5m"], "cache_read": t["cr"],
            "output": t["out"], "usd_api_equivalent": round(h["cost_total"], 2),
            "cost_split": {k: round(v, 2) for k, v in h["cost"].items()},
            "compactions": h["compactions"], "calls_over_150k": h["calls_over_150k"],
            "max_ctx": h["max_ctx"], "classification": CLASSIFICATION, "caveat": CAVEAT,
        }
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: (v["calls"], v["cache_read"], v["usd_api_equivalent"]) for k, v in out.items()}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
