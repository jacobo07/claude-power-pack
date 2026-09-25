"""Mutation drills for Lane R modules: swap a snippet, the named gates must FAIL, restore by sha256.

Usage: python tools/lane_r_mutate.py vault/knowledge_base/uwcp_assimilation/mutations/<module>.json
KILLED needs a named gate red AND a non-zero exit; a traceback with no named gate is CRASH, which
proves nothing. Mutates files on disk: run only on files no other writer holds.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\User\.claude\skills\claude-power-pack")
PY = sys.executable


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    results = []
    for m in spec["mutations"]:
        target = ROOT / m["file"]
        original = target.read_bytes()
        before = sha(target)
        text = original.decode("utf-8")
        if text.count(m["old"]) != 1:
            results.append((m["name"], "HARNESS_FAILED", f"snippet count={text.count(m['old'])}"))
            continue
        try:
            target.write_bytes(text.replace(m["old"], m["new"]).encode("utf-8"))
            p = subprocess.run([PY, spec["gate"]], cwd=ROOT, capture_output=True, text=True,
                               timeout=300, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
            out = p.stdout + p.stderr
            red = [g for g in m["expect_red"] if f"FAIL {g}" in out]
            crashed = "Traceback" in out and not red
            verdict = "KILLED" if red and p.returncode != 0 else ("CRASH" if crashed else "SURVIVED")
            results.append((m["name"], verdict, ",".join(red) or out[-300:]))
        finally:
            target.write_bytes(original)
            assert sha(target) == before, f"RESTORE FAILED for {target}"
    for name, verdict, detail in results:
        print(f"{verdict:14} {name}: {detail}")
    killed = sum(v == "KILLED" for _, v, _ in results)
    print(f"MUTANTS_KILLED={killed}/{len(results)}  (all restores sha256-verified)")
    return 0 if killed == len(results) else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1]))
