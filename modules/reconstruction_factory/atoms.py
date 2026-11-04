"""Typed predicate registry for claims (WROS-style atoms). A predicate is `candidate` until a consumer uses it; `register()` refuses a duplicate or a
predicate with no consumer or past the cap. A malformed payload is rejected at write. Field spec grammar:
  int | int>=0 | num | str | bool | false | dict | list | enum:a,b | ?<spec> (nullable)
`world` = the coordinates that change a truth (toolchain, recipe, artifact); an absent dimension is absent, never null-filled."""
import hashlib
import json


class Malformed(ValueError):
    pass


class Refused(Exception):
    pass


WORLD_DIMS = ("artifact_sha256", "compiler_profile", "tool_versions", "region_build", "population_snapshot_id")
CAP = 24
RF = "modules/reconstruction_factory/"


def _p(fields, consumers, when=None, doc=""):
    return {"version": 1, "status": "candidate", "fields": fields, "consumers": consumers, "when": when or {}, "doc": doc}


PREDICATES = {
    "compile_outcome": _p({"fn": "str", "compiles": "bool", "exact": "?bool", "pct": "?num"}, [RF + "claims.py::from_judge"], doc="one candidate compile + judge outcome"),
    "certificate": _p({"fn": "str", "verdict": "enum:CERTIFIED_EXACT,NOT_EXACT,DISAGREEMENT,UNDERDETERMINED_TOOLCHAIN,HELDOUT_NOT_RELEASED", "candidate_sha256": "?str"},
                      [RF + "claims.py::from_certificate"], doc="a certification verdict; only CERTIFIED_EXACT carries a candidate hash"),
    "control_outcome": _p({"control": "enum:pos,neg,noop", "refused": "bool"}, [RF + "certify.py::certify"], doc="a positive/negative control event"),
    "vtable": _p({"cls": "str", "grade": "enum:CANDIDATE,VTABLE", "kinds": "list", "slots": "int>=0"}, [RF + "om.py::build_registry"], doc="a recovered vtable and its support kinds"),
    "vptr_install": _p({"fn": "str", "cls": "str"}, [RF + "om.py::scan_installs"], doc="a function that installs a class's vptr"),
    "vcall_site": _p({"fn": "str", "slot": "int>=0"}, [RF + "om.py::scan_vcalls"], doc="a virtual call site through a vtable slot"),
    "field_access": _p({"fn": "str", "offset": "int>=0", "op": "str"}, [RF + "om.py::field_accesses"], doc="a this-call member access"),
    "twin_verdict": _p({"verdict": "enum:TWIN_CONFIRMED,TWIN_UNCERTAIN,TWIN_NONE", "matches": "list"}, [RF + "build_twin.py::twin"], doc="a Build Twin outcome"),
    "residual_class": _p({"fn": "str", "residual_class": "?str", "primary": "?str"}, [RF + "residual.py::residual"], doc="a residual classification"),
    "invalidation_event": _p({"reason": "enum:tool_version_changed,population_changed,counterexample,missing_dependency,scope_changed,direct_contradiction,instrument_failure",
                              "claims": "list"}, [RF + "claims.py::invalidate"], doc="bookkeeping: claims withdrawn and why"),
}
STRUCTURAL = ("invalidation_event",)
REASONS = PREDICATES["invalidation_event"]["fields"]["reason"][5:].split(",")


def contract(predicate):
    return PREDICATES.get(predicate)


def _check(spec, v, where):
    if spec.startswith("?"):
        if v is None:
            return
        spec = spec[1:]
    ok = ((spec == "bool" and isinstance(v, bool)) or (spec == "false" and v is False) or (spec == "str" and isinstance(v, str)) or
          (spec == "dict" and isinstance(v, dict)) or (spec == "list" and isinstance(v, list)) or
          (spec == "num" and isinstance(v, (int, float)) and not isinstance(v, bool)) or
          (spec.startswith("int") and isinstance(v, int) and not isinstance(v, bool) and (spec == "int" or v >= 0)) or
          (spec.startswith("enum:") and v in spec[5:].split(",")))
    if not ok:
        raise Malformed("%s: %r does not satisfy %s" % (where, v, spec))


def validate(predicate, payload):
    c = contract(predicate)
    if c is None:
        raise Malformed("no contract for predicate %r" % predicate)
    if not isinstance(payload, dict):
        raise Malformed("payload must be a dict")
    req = dict(c["fields"])
    for cond, extra in c["when"].items():
        k, val = cond.split("=")
        if str(payload.get(k)) == val:
            req.update(extra)
    for f, spec in req.items():
        if f not in payload:
            raise Malformed("%s: required field %r missing" % (predicate, f))
        _check(spec, payload[f], "%s.%s" % (predicate, f))
    extra = set(payload) - set(req)
    if extra:
        raise Malformed("%s: unknown field(s) %s" % (predicate, sorted(extra)))
    return payload


def world(**dims):
    bad = set(dims) - set(WORLD_DIMS)
    if bad:
        raise Malformed("unknown world dimension %s" % sorted(bad))
    return {k: dims[k] for k in sorted(dims) if dims[k] is not None}


def world_compatible(a, b):
    """Two worlds conflict only where both name a dimension and disagree."""
    return all(a[k] == b[k] for k in set(a) & set(b))


def _norm(v):
    if isinstance(v, float):
        return round(v, 12)
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in sorted(v.items())}
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


def semantic_key(subject, predicate, payload, world_):
    """sha256 of the canonical (subject, predicate, normalised value, world): the proposition, not the event."""
    return hashlib.sha256(json.dumps([subject, predicate, _norm(payload), world_], sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def register(name, contract_):
    if name in PREDICATES:
        raise Refused("predicate %r already exists" % name)
    if not contract_.get("consumers"):
        raise Refused("predicate %r has no consumer" % name)
    if len(PREDICATES) >= CAP:
        raise Refused("at most %d predicates" % CAP)
    PREDICATES[name] = _p(contract_.get("fields", {}), contract_["consumers"], contract_.get("when"), contract_.get("doc", ""))
    return PREDICATES[name]
