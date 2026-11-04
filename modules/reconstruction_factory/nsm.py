"""Negative Search Memory: what was tried and is KNOWN not to work, scoped to a WORLD (toolchain/recipe fingerprint) so a change of world makes
old negatives inapplicable instead of silently true. Soundness rule (learned the hard way: pruning on 'no gain' made a solvable function
unsolvable, because a beam may need a non-gaining step): only DETERMINISTIC facts refute.
  record(fn, cls, op, why, state=None)   why: NO_COMPILE_ALL (every site of op at text-state `state` fails to compile) | REFUTED (owner/mined) |
                                         SOLVED (veto: un-refutes op for fn/cls) | NO_GAIN / WORSE (advisory, never refutes)
  refuted_operator(fn, cls, op)          interface search_plan expects; a row with state=None applies everywhere, a stated row only via at(state)
  memo_not_found / known_not_found       whole-run memo: (fn, skeleton, config) searched to NOT_FOUND in this world; re-running cannot differ
Persistent as append-only JSONL when a path is given. Absence of memory is never a refutation."""
import json
import os

FAILS = ("NO_COMPILE_ALL", "REFUTED")


class NSM:
    def __init__(self, path=None, world="", state=None):
        self.path, self.world, self.state = path, world, state
        self.rows = []
        self._root = self
        if path and os.path.exists(path):
            with open(path) as fh:
                self.rows = [json.loads(l) for l in fh if l.strip()]

    def at(self, state):
        v = object.__new__(NSM)
        v.__dict__.update(self.__dict__)
        v.state, v._root = state, self._root
        return v

    def record(self, fn, cls, op, why, state=None):
        r = {"fn": fn, "cls": cls, "op": op, "why": why, "world": self.world, "state": state if state is not None else self.state}
        self._root.rows.append(r)
        if self.path:
            with open(self.path, "a") as fh:
                fh.write(json.dumps(r, sort_keys=True) + "\n")

    def _mine(self, fn, cls, op):
        return [r for r in self._root.rows if r["world"] == self.world and r["fn"] == fn and r["cls"] == cls and r["op"] == op
                and (r["state"] is None or r["state"] == self.state)]

    def refuted_operator(self, fn, cls, op):
        rs = self._mine(fn, cls, op)
        if any(r["why"] == "SOLVED" for r in rs):
            return False
        return any(r["why"] in FAILS for r in rs)

    def memo_not_found(self, fn, key, result):
        self.record(fn, "<run>", key, "RUN_NOT_FOUND")
        self._root.__dict__.setdefault("_memo", {})[(self.world, fn, key)] = result

    def known_not_found(self, fn, key):
        m = self._root.__dict__.get("_memo", {}).get((self.world, fn, key))
        if m is not None:
            return m
        for r in self._root.rows:                                  # reloaded from disk: the fact survives, the best-text does not
            if r["world"] == self.world and r["fn"] == fn and r["op"] == key and r["why"] == "RUN_NOT_FOUND":
                return {"status": "NOT_FOUND", "compiles": 0, "memo": True, "text": None, "path": []}
        return None

    def applicable(self):
        return [r for r in self._root.rows if r["world"] == self.world]
