"""ONE chain tick for N programmes (zero model).

    python tools/chain_registry.py tick [--registry PATH] [--dry-run]

registry.json: {"chains": [{"name", "chain": "path/to/chain.json", "enabled": true}]}
Each enabled chain gets one gsdx_chain.tick; a disabled registry entry or a parked chain.json arms nothing.
One chain failing (bad file, exception) is reported and never stops the others. Rows go to
~/.claude/state/chain-registry.jsonl. Kill switch: CPP_GSDX_CHAIN=off (honoured per tick by gsdx_chain).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsdx_chain as gc  # noqa: E402

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "vault" / "programs" / "chains.json"


def tick_all(registry_path: Path, dry_run: bool = False, **kw) -> list[dict]:
    reg = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    rows = []
    for e in reg["chains"]:
        name = e.get("name", e.get("chain"))
        if e.get("enabled") is False:
            rows.append({"name": name, "action": "parked", "why": "registry enabled=false"})
            continue
        try:
            row = gc.tick(Path(e["chain"]), dry_run=dry_run, **kw)
        except Exception as ex:  # noqa: BLE001 -- isolate one programme from the rest
            row = {"action": "error", "why": f"{type(ex).__name__}: {ex}"[:300]}
        rows.append({"name": name, **row})
    return rows


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "tick":
        print(__doc__)
        return 2
    path = Path(argv[argv.index("--registry") + 1]) if "--registry" in argv else DEFAULT_REGISTRY
    dry = "--dry-run" in argv
    rows = tick_all(path, dry_run=dry)
    if not dry:
        log = Path.home() / ".claude" / "state" / "chain-registry.jsonl"
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": time.time(), "rows": rows}) + "\n")
    print(json.dumps(rows))
    bad = [r for r in rows if r["action"] == "error" or (r["action"] == "arm" and not (r.get("armed") or {}).get("ok", True))]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
