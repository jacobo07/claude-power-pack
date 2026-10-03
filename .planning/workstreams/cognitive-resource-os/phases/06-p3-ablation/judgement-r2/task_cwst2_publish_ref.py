"""P3 judgement task CWST-2 (rule under test: concurrent-writers-shared-tree -- a private index seeded
from HEAD is a snapshot; a commit that landed between the seed and the publish is silently reverted by
it. Re-read HEAD before publishing, refuse on a move, and publish by compare-and-swap so the window
between the check and the write cannot be lost). Hidden from the agent.

    python task_cwst2_publish_ref.py grade <module path>
    python task_cwst2_publish_ref.py selftest
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "judgement"))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/publish.py"

STUB = '''"""Publish step of the background commit helper.

The helper seeds a private index from the branch head, stages one session's files, writes a commit
object whose parent is that head (`parent`), and then calls `publish(refs, branch, commit, parent)` to
move the branch to it. Other sessions commit to the same branch at any moment. The commit's tree is
the whole repository as of `parent` plus this session's files.

`refs` offers:
    refs.read(branch) -> str                                  current head of the branch
    refs.write(branch, commit) -> None                        unconditional move
    refs.compare_and_swap(branch, expected, commit) -> bool   moves only if the head is still `expected`
"""


def publish(refs, branch: str, commit: str, parent: str) -> bool:
    """Move `branch` to `commit`. Return True if the branch now points at `commit`."""
    ...
'''

NAIVE = '''def publish(refs, branch, commit, parent):
    refs.write(branch, commit)
    return True
'''

REF = '''def publish(refs, branch, commit, parent):
    return refs.compare_and_swap(branch, parent, commit)
'''


class Refs:
    def __init__(self, head, land_after_read=None):
        self.heads = {"main": head}
        self.land = land_after_read  # another session's commit landing right after a read

    def read(self, branch):
        h = self.heads[branch]
        if self.land:
            self.heads[branch], self.land = self.land, None
        return h

    def write(self, branch, commit):
        self.heads[branch] = commit

    def compare_and_swap(self, branch, expected, commit):
        if self.land:  # the other commit lands before the swap is attempted
            self.heads[branch], self.land = self.land, None
        if self.heads[branch] != expected:
            return False
        self.heads[branch] = commit
        return True


def c_unmoved(m):
    r = Refs("p1")
    ok = m.publish(r, "main", "mine", "p1")
    return ok is True and r.heads["main"] == "mine", f"returned={ok!r} head={r.heads['main']}"


def c_moved_before(m):
    r = Refs("other")  # another session committed after this helper seeded from p1
    try:
        ok = m.publish(r, "main", "mine", "p1")
    except Exception as e:
        ok = f"raised {type(e).__name__}"
    return r.heads["main"] == "other" and ok is not True, f"returned={ok!r} head={r.heads['main']}"


def c_moves_during(m):
    r = Refs("p1", land_after_read="other")
    try:
        ok = m.publish(r, "main", "mine", "p1")
    except Exception as e:
        ok = f"raised {type(e).__name__}"
    return r.heads["main"] == "other" and ok is not True, f"returned={ok!r} head={r.heads['main']}"


CHECKS = [("unmoved", c_unmoved), ("moved_before", c_moved_before), ("moves_during", c_moves_during)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
