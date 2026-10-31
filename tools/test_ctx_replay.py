"""V-REPLAY-* gates for tools/ctx_replay.py (fixtures are real transcript byte shapes: assistant usage + user text)."""
import json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctx_replay as rp

passes = fails = 0
def check(n, ok):
    global passes, fails
    passes += ok; fails += (not ok); print(("OK   " if ok else "FAIL ") + n)

def session(d, name, text, inputs, sub=False):
    p = Path(d) / ("subagents" if sub else "") / (name + ".jsonl"); p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
        for i, t in enumerate(inputs):
            f.write(json.dumps({"type": "assistant", "timestamp": "2026-10-30T10:00:%02d" % i,
                                "message": {"id": "m%s%d" % (name, i), "role": "assistant", "content": [{"type": "text", "text": "x"}],
                                            "usage": {"input_tokens": 1, "cache_read_input_tokens": t - 1, "cache_creation_input_tokens": 0, "output_tokens": 5}}}) + "\n")

check("V-REPLAY-PRIME-CLAMP", rp.prime([100, 50000], 20000) == 0 + 30000)          # clamp: a call smaller than delta goes to 0, never negative
check("V-REPLAY-PRIME-ZERO-DELTA", rp.prime([10, 20], 0) == 30)                     # control: delta 0 changes nothing
check("V-REPLAY-CLASSIFY", [rp.classify("run /kresume", 5, 1, False), rp.classify("KSR 01.1", 5, 1, False), rp.classify("x", 5, 1, True),
                            rp.classify("fix this bug", 5, 1, False), rp.classify("hi", 200, 1, False), rp.classify("hi", 3, 1, False),
                            rp.classify("hi", 20, 500000, False)] ==
      ["kresume_successor", "ksr_style", "mission_worker", "debugging", "long_repo", "sparse", "coherent_large_context"])
with tempfile.TemporaryDirectory() as d:
    session(d, "a", "please fix this bug", [100000, 100000, 100000])
    session(d, "w", "work", [100000, 100000], )
    session(d, "s", "sub", [100000, 100000], sub=True)
    doc = rp.replay(Path(d), "2026-10-30", "2026-10-31", 20000, {"w": "full"}, "test")
    c = doc["classes"]
    check("V-REPLAY-INTERACTIVE-SAVES", c["debugging"]["X"] == 300000 and c["debugging"]["X_prime"] == 240000 and c["debugging"]["saving_pct"] == 20.0)
    check("V-REPLAY-WORKER-UNTOUCHED", c["mission_worker"]["X"] == c["mission_worker"]["X_prime"] == 200000)
    check("V-REPLAY-SUBAGENT-UNTOUCHED", c["subagent"]["X"] == c["subagent"]["X_prime"] == 200000)
    check("V-REPLAY-TOTAL-AND-LABEL", doc["total"]["X"] == 700000 and doc["total"]["X_prime"] == 640000 and doc["label"].startswith("ESTIMATE")
          and c["debugging"]["quality"].startswith("UNKNOWN"))
print("REPLAY_PASS=%d/%d  threshold=N/N" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
