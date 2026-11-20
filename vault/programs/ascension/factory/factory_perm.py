"""Producer for permuter-stage runs (stages/perm-*): the stored source is already complete (prelude + transform +
permutation, cpp-expanded), so prelude() is empty and transform() is the identity. ARMS keys are '<producer>.<arm>'
so a unit is compiled with exactly the flags its permutation was verified under."""
import factory as B
import factory_vs2 as V

ARMS = {m: {**{f"factory.{a}": f for a, f in B.ARMS.get(m, {}).items()},
            **{f"factory_vs2.{a}": f for a, f in V.ARMS.get(m, {}).items()}} for m in set(B.ARMS) | set(V.ARMS)}


def prelude():
    return ""


def transform(src):
    return src
