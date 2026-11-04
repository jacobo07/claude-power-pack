"""Method Graph: operators are nodes, observed successful orderings are edges, per residual class. It is learned from solved search paths and
read back as (a) a prior for search_plan and (b) supercompiled trajectories: an operator sequence seen in >= `min_count` solved paths becomes one
MACRO node that can be replayed as a single step (`expand`). Nothing here is hand-curated: an empty graph yields an empty prior."""
import collections
import json

from .operators import apply_all


class MethodGraph:
    def __init__(self):
        self.edges = collections.Counter()          # (cls, a, b) -> n   ("<start>" as a)
        self.node = collections.Counter()           # (cls, op) -> n solved
        self.paths = []                             # (cls, tuple(path)) of solved trajectories
        self.macros = {}

    def learn(self, cls, path, solved=True):
        if not solved or not path:
            return
        self.paths.append((cls, tuple(path)))
        prev = "<start>"
        for op in path:
            self.node[(cls, op)] += 1
            self.edges[(cls, prev, op)] += 1
            prev = op

    def prior(self, cls):
        """-> {op: weight in [0,1)} for search_plan(prior=...); weight grows with solved count, saturating."""
        return {op: n / (n + 1.0) for (c, op), n in self.node.items() if c == cls}

    def supercompile(self, min_count=2, max_len=4):
        """Every contiguous op sequence (len 2..max_len) present in >= min_count solved paths (each path counted once) -> macro."""
        cnt = collections.Counter()
        for _c, p in self.paths:
            seen = set()
            for L in range(2, max_len + 1):
                for i in range(len(p) - L + 1):
                    seen.add(p[i:i + L])
            cnt.update(seen)
        self.macros = {"+".join(s): list(s) for s, n in cnt.items() if n >= min_count}
        return self.macros

    def to_json(self):
        return json.dumps({"paths": [[c, list(p)] for c, p in self.paths]}, sort_keys=True)

    @classmethod
    def from_json(cls, s):
        g = cls()
        for c, p in json.loads(s)["paths"]:
            g.learn(c, p)
        return g


def expand(text, ops, extra=None, limit=64):
    """All texts reachable by applying `ops` in order, one site per step (a macro replay). Bounded by `limit` frontier size."""
    front = [text]
    for op in ops:
        nxt = []
        for t in front:
            nxt += [x for _n, x in apply_all(t, [op], extra)]
        front = list(dict.fromkeys(nxt))[:limit]
        if not front:
            return []
    return front
