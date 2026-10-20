"""CLI for the pre-budget Owner router: JSON event on stdin, one JSON line on stdout. Run with python -I."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.provider_routing import owner_router  # noqa: E402


def main() -> int:
    try:
        ev = json.loads(sys.stdin.read() or "{}")
        res = owner_router.route(ev.get("prompt"), ev.get("session_id"), ev)
    except Exception as ex:  # noqa: BLE001 -- the hook treats any non-JSON/ERROR as fall-through
        print(json.dumps({"outcome": "ERROR", "error": repr(ex)}))
        return 0
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
