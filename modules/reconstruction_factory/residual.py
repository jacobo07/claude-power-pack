"""Residual: names what is left when a candidate is not exact, in the mission's closed failure vocabulary. It is a description of the diff,
not a claim that the residual is irreducible."""
from .causal_diff import causal_diff

# diff class -> (residual class, retry hint)
MAP = {
    "ORDER": ("COMPILER_SHAPE_RESIDUAL", "schedule / expression-order operators"),
    "REG_ALLOC": ("COMPILER_SHAPE_RESIDUAL", "variable lifetime, temporaries, declaration order"),
    "CONST": ("UNIQUE_SEMANTIC_RESIDUAL", "constant or type width differs"),
    "RELOC": ("TYPE_LAYOUT_BLOCKED", "callee or data symbol differs; object-model / layout evidence needed"),
    "FRAME": ("TYPE_LAYOUT_BLOCKED", "locals layout / stack frame differs"),
    "OPCODE": ("METHOD_PLATEAU", "different operation selected; type or operator choice"),
    "MISSING": ("OBJECT_MODEL_BLOCKED", "target has instructions the candidate lacks (inlined or virtual path)"),
    "EXTRA": ("COMPILER_SHAPE_RESIDUAL", "candidate has instructions the target lacks"),
}


def residual(adapter, target, cand, symbols):
    d = causal_diff(adapter, target, cand, symbols)
    if not d["hunks"]:
        return {"residual_class": None, "classes": {}, "hunks": 0, "hint": None}
    cls = d["primary"]
    rc, hint = MAP[cls]
    return {"residual_class": rc, "primary": cls, "classes": d["classes"], "hunks": d["hunks"], "hint": hint}
