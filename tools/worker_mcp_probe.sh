#!/usr/bin/env bash
# Worker MCP probe (spec vault/specs/gex44-mission-plane.md). Rule predeclared 2026-09-27:
# APPLY only if every no-MCP run succeeds with "OK" AND its median input+cache tokens are
# >= 5% below the default's; any default error -> UNJUDGED; otherwise KEEP.
set -u
OUT="$HOME/.claude/state/worker-mcp-probe.json"
WORK="$(mktemp -d)"
cd "$HOME/cavex" || exit 1
for i in 1 2 3; do
  timeout 180 claude -p "Reply with the single word OK." --output-format json \
    > "$WORK/default_$i.json" 2> "$WORK/default_$i.err"
  timeout 180 claude -p "Reply with the single word OK." --output-format json \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
    > "$WORK/nomcp_$i.json" 2> "$WORK/nomcp_$i.err"
done
python3 - "$WORK" "$OUT" <<'PY'
import json, statistics, sys, time
from pathlib import Path
work, out = Path(sys.argv[1]), Path(sys.argv[2])
def runs(tag):
    rows = []
    for i in (1, 2, 3):
        try:
            d = json.loads((work / f"{tag}_{i}.json").read_text())
        except Exception as e:
            err = (work / f"{tag}_{i}.err").read_text(errors="replace")[:300]
            rows.append({"ok": False, "why": f"unreadable: {e}; stderr={err}"}); continue
        u = d.get("usage") or {}
        tok = sum(int(u.get(k) or 0) for k in
                  ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        ok = (not d.get("is_error")) and str(d.get("result", "")).strip().strip(".").upper() == "OK"
        rows.append({"ok": ok, "tokens": tok, "is_error": d.get("is_error"),
                     "status": d.get("api_error_status"), "result": str(d.get("result"))[:80]})
    return rows
dflt, nomcp = runs("default"), runs("nomcp")
if not all(r["ok"] for r in dflt):
    verdict, why = "UNJUDGED", "a default run failed; nothing to compare against"
elif not all(r["ok"] for r in nomcp):
    verdict, why = "KEEP", "a no-MCP run failed"
else:
    md = statistics.median(r["tokens"] for r in dflt)
    mn = statistics.median(r["tokens"] for r in nomcp)
    saving = (md - mn) / md if md else 0.0
    verdict = "APPLY" if saving >= 0.05 else "KEEP"
    why = f"median default={md} no_mcp={mn} saving={saving:.1%} (threshold 5%)"
out.write_text(json.dumps({"verdict": verdict, "why": why, "measured_at": time.time(),
                           "rule": "APPLY iff all no-MCP runs OK and median saving >= 5%",
                           "default": dflt, "no_mcp": nomcp}, indent=2))
print(verdict, why)
PY
