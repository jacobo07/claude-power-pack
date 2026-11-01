"""V-CTXW-* gates for tools/ctx_wait.py. Fixtures use real transcript shapes: one assistant line per content block, shared message.id + usage."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctx_wait as cw  # noqa: E402

PASS = FAIL = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate}: {ev}")


def line(mid: str, total: int, name: str | None, inp: dict | None = None) -> str:
    blk = {"type": "tool_use", "id": "t" + mid, "name": name, "input": inp} if name else {"type": "text", "text": "ok"}
    u = {"input_tokens": 3, "cache_read_input_tokens": total - 3, "cache_creation_input_tokens": 0, "output_tokens": 7}
    return json.dumps({"type": "assistant", "message": {"id": mid, "usage": u, "content": [blk]}})


def run(lines: list[str]) -> dict:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "s.jsonl"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return cw.classify(p)


def main() -> int:
    r = run([line("a", 1000, "Bash", {"command": "sleep 30 && tail out.log"}),
             line("b", 2000, "Monitor", {"x": 1}),
             line("c", 3000, "Bash", {"command": "ls"}),
             line("d", 4000, "Bash", {"command": "ls"}),
             line("e", 5000, "Edit", {"f": 1}),
             line("f", 6000, None)])
    bc = r["by_class"]
    check("V-CTXW-SLEEP", bc["WAIT_SLEEP"]["calls"] == 1 and bc["WAIT_SLEEP"]["processed"] == 1000, str(bc["WAIT_SLEEP"]))
    check("V-CTXW-NOTIFY", bc["WAIT_NOTIFY"]["calls"] == 1 and bc["WAIT_NOTIFY"]["processed"] == 2000, str(bc["WAIT_NOTIFY"]))
    check("V-CTXW-REASK", bc["WAIT_REASK"]["calls"] == 1 and bc["WAIT_REASK"]["processed"] == 4000, "second identical ls is the re-ask; the first is WORK")
    check("V-CTXW-WORK-CONTROL", bc["WORK"]["calls"] == 3, "first ls, Edit and a text-only turn stay WORK (a classifier that flags all would fail)")
    check("V-CTXW-CONSERVED", sum(v["processed"] for v in bc.values()) == r["processed"] == 21000, "class costs sum to the measured processed total")
    check("V-CTXW-SHARE", r["wait_calls"] == 3 and abs(r["wait_processed_share"] - 7000 / 21000) < 1e-3, f"share {r['wait_processed_share']}")
    sh = cw.shadow_admission(r)
    check("V-CTXW-SHADOW-FLAG", sh["shadow"] is True and sh["would_flag"] is True, sh["reason"])
    quiet = cw.shadow_admission(run([line("a", 1000, "Edit", {"f": 1}), line("b", 2000, "Edit", {"f": 2})]))
    check("V-CTXW-SHADOW-QUIET", quiet["would_flag"] is False, quiet["reason"])
    check("V-CTXW-UNMEASURED", cw.shadow_admission({})["would_flag"] is None, "no calls is UNMEASURED, not a clean zero")
    # mutation drill: a classifier that never recognises sleep must turn V-CTXW-SLEEP red
    orig = cw.SLEEP_RE
    cw.SLEEP_RE = __import__("re").compile(r"\Zx")
    try:
        m = run([line("a", 1000, "Bash", {"command": "sleep 30"})])["by_class"]["WAIT_SLEEP"]["calls"]
    finally:
        cw.SLEEP_RE = orig
    check("V-CTXW-MUTATION-RED", m == 0, "with the sleep pattern disabled the sleep call is no longer found, so the gate can fail")
    import ccr_pgo as pg
    with tempfile.TemporaryDirectory() as d:
        img = Path(d) / "i.txt"
        img.write_text("x" * 100, encoding="utf-8")
        base = pg.contract(None, "o", img, None)
        shad = pg.contract(None, "o", img, None, waiting=sh)
    check("V-CTXW-PGO-SHADOW", shad.get("waiting_shadow") == sh and shad["verdict"] == base["verdict"] == "ADMIT_UNFORECAST", "annotation present, verdict unchanged")
    check("V-CTXW-PGO-ABSENT", "waiting_shadow" not in base, "no waiting input: no annotation invented")
    print(f"CTXW_PASS={PASS}/{PASS + FAIL}  threshold=N/N")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
