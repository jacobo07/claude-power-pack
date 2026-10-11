#!/usr/bin/env python3
"""CDC C1 gates: economic role per call (session_autopsy --roles).

3 golden mini-transcripts + one source mutant per role (the role's tag is renamed in an
in-memory copy of the module; the golden expectation must flip RED). Never touches the live file.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
SRC = (_HERE / "session_autopsy.py").read_text(encoding="utf-8")
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def load(src: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(_HERE / "session_autopsy.py")
    sys.modules[name] = mod
    sys.path.insert(0, str(_HERE))
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


class T:
    """Transcript builder: each assistant call = one message id with usage 100 in / 10 out."""
    def __init__(self):
        self.rows, self.n = [], 0

    def user(self, text):
        self.rows.append({"type": "user", "message": {"role": "user", "content": text}})
        return self

    def raw(self, row):
        self.rows.append(row)
        return self

    def call(self, name=None, inp=None, result="ok", err=False, text=""):
        self.n += 1
        mid, tid = f"m{self.n}", f"t{self.n}"
        blocks = ([{"type": "text", "text": text}] if text else [])
        if name:
            blocks.append({"type": "tool_use", "id": tid, "name": name, "input": inp or {}})
        self.rows.append({"type": "assistant", "requestId": f"r{self.n}", "message": {
            "id": mid, "model": "claude-opus-5-5", "role": "assistant", "content": blocks,
            "usage": {"input_tokens": 10, "cache_creation_input_tokens": 0,
                      "cache_read_input_tokens": 90, "output_tokens": 10}}})
        if name:
            self.rows.append({"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tid, "content": result, "is_error": err}]}})
        return self

    def write(self, path):
        Path(path).write_text("\n".join(json.dumps(r) for r in self.rows) + "\n", encoding="utf-8")


def bash(t, cmd, result="ok", err=False):
    return t.call("Bash", {"command": cmd}, result=result, err=err)


def golden1(p):
    t = T().user("Capsule: read capsule.md first")
    t.call("Read", {"file_path": "/r/a.py"})
    t.call("Read", {"file_path": "/r/a.py"})
    t.call("Read", {"file_path": "/r/capsule.md"})
    t.call("WebSearch", {"query": "x"})
    t.call("Write", {"file_path": "/r/.planning/x.md", "content": "plan"})
    t.call("Write", {"file_path": "/r/new.py", "content": "x=1"})
    t.call("Edit", {"file_path": "/r/a.py", "old_string": "a", "new_string": "b"})
    bash(t, "python -m pytest tools/test_a.py", result="1 failed, 2 passed")
    t.call("Edit", {"file_path": "/r/a.py", "old_string": "b", "new_string": "c"})
    bash(t, "python -m pytest -q tools/test_a.py", result="3 passed")
    bash(t, "git status")
    bash(t, "python render_status.py --status")
    bash(t, "ls /nonexistent", result="No such file", err=True)
    bash(t, "ls /nonexistent", result="No such file", err=True)
    t.write(p)


G1 = ["READ", "REREAD", "CONTEXT_FAULT", "RESEARCH", "PLAN", "NOVELTY", "IMPLEMENT", "PROOF",
      "REPAIR", "PROOF", "CONTROL", "STATUS", "unattributed", "RECOVERY"]


def golden2(p):
    T().user("go").call(text="x" * 700).call("Edit", {"file_path": "/r/a.py"}).call(text="y" * 700).write(p)


def golden3(p):
    t = T().user("go")
    t.call("Read", {"file_path": "/r/z.py"})
    t.raw({"type": "system", "subtype": "compact_boundary"})
    t.call("Read", {"file_path": "/r/z.py"})
    t.write(p)
    sub = Path(p).with_suffix("") / "subagents"
    sub.mkdir(parents=True)
    s = T().user("sub task")
    s.call("Read", {"file_path": "/r/q.py"})
    s.write(sub / "agent-1.jsonl")


def seq(mod, path):
    return [r["role"] for r in mod.classify_calls(mod._scan(Path(path), "main"))]


def run_all(mod):
    """Return the tuple of observable golden outputs for a module."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        golden1(d / "g1.jsonl")
        golden2(d / "g2.jsonl")
        golden3(d / "g3.jsonl")
        r3 = mod.roles(d / "g3.jsonl")
        return (seq(mod, d / "g1.jsonl"), seq(mod, d / "g2.jsonl"), seq(mod, d / "g3.jsonl"), r3,
                mod.roles(d / "g1.jsonl"))


def main():
    base = load(SRC, "sa_base")
    g1, g2, g3, r3, r1 = run_all(base)
    check("G1 roles", g1 == G1, str(g1))
    check("G2 plan-by-text only before edit", g2 == ["PLAN", "IMPLEMENT", "unattributed"], str(g2))
    check("G3 epoch resets reread", g3 == ["READ", "READ"], str(g3))
    check("G3 subagent included+tagged", r3["calls"] == 3 and r3["roles"]["READ"]["subagent_tokens"] == 110
          and r3["files"][1].startswith("sub:"), f"calls={r3['calls']}")
    check("unattributed reported", r1["unattributed_share"] is not None
          and abs(r1["unattributed_share"] - 110 / (110 * 14)) < 1e-9, f"{r1['unattributed_share']:.4f}")
    check("shares sum to 1", abs(sum(v["share"] for v in r1["roles"].values()) - 1) < 1e-9)
    tr = r1["transitions"]
    check("transitions", tr["new_file"] == 1 and tr["red_green"] == 1 and tr["commit"] == 0
          and tr["tokens_per_transition"] == r1["processed_tokens"] / tr["total"], str(tr))
    # commit + claim counted
    with tempfile.TemporaryDirectory() as d:
        t = T().user("go")
        bash(t, 'git commit -m "x"')
        t.call("PowerShell", {"command": "$g='C:\\Program Files\\Git\\cmd\\git.exe'; & $g commit -m y"})
        t.call(text="Status: DONE")
        t.write(Path(d) / "c.jsonl")
        tt = base.roles(Path(d) / "c.jsonl")["transitions"]
        check("commit and claim", tt["commit"] == 2 and tt["claim"] == 1, str(tt))
    # one mutant per role: rename the tag everywhere it is assigned; the goldens must go RED
    for role in base.ROLES:
        src = SRC.replace(f'found.add("{role}")', 'found.add("MUTANT")')
        if src == SRC:
            check(f"mutant {role}", False, "no assignment site found")
            continue
        try:
            m = load(src, f"sa_mut_{role}")
            out = run_all(m)
            flipped = out[0] != G1 or out[1] != ["PLAN", "IMPLEMENT", "unattributed"] or out[2] != ["READ", "READ"]
        except Exception as e:  # a crash is also a RED
            flipped = True
        check(f"mutant {role} flips RED", flipped)
    # epoch mutant
    m = load(SRC.replace("read_since.clear()", "pass"), "sa_mut_epoch")
    check("mutant epoch flips RED", run_all(m)[2] != ["READ", "READ"])
    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
