"""Patch evolve.py / test_autopilot.py / levers.json in DIR (argv[1]). Anchor-exact; refuses on any anchor miss."""
import json, pathlib, sys

D = pathlib.Path(sys.argv[1])


def sub(path, old, new):
    p = D / path
    raw = p.read_bytes(); crlf = b"\r\n" in raw
    s = raw.decode("utf-8").replace("\r\n", "\n")
    assert s.count(old) == 1, f"{path}: anchor x{s.count(old)}: {old[:60]!r}"
    s = s.replace(old, new)
    p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))


# ---- evolve.py: owner_resume may name the lever ("research:<id>")
sub("evolve.py", '''def selection_evidence(lever, graph) -> dict | None:''', '''def owner_lever(levers: dict, lane: str, ls: dict, product: str, want: str, family) -> dict | None:
    """The lever the Owner named in owner_resume="research:<id>", under the same admission as select: open, not retired
    by this lane, preconditions met, research kind, and of another family than the one the lane leaves. None refuses."""
    retired = set(ls.get("retired") or [])
    return next((x for x in levers.get(lane, []) if x.get("id") == want and x.get("status") == "open"
                 and x["id"] not in retired and _requires_met(x, product) and x.get("kind") != "repair"
                 and x.get("family") != family), None)


def selection_evidence(lever, graph) -> dict | None:''')
sub("evolve.py", '''    if ls.pop(OWNER_RESUME, None) == "research":
        ls["repair"] = {}
        lever = select(levers, lane, ls, product, graph, family_not=family)
        if lever is None:
            return {"action": "park", "why": f"Owner resume: no open lever of another family than {family} with its "
                                             "preconditions met"}''', '''    # 2026-11-14 (Owner "crea las capacidades directamente y pegalas a las misiones", session 423c9c50): the value may
    # name the lever, "research:<id>"; a new lever has no MethodGraph prior, so select alone would never reach it.
    ro = ls.pop(OWNER_RESUME, None)
    if ro == "research" or (isinstance(ro, str) and ro.startswith("research:")):
        ls["repair"] = {}
        want = ro.split(":", 1)[1] if ":" in ro else None
        lever = (owner_lever(levers, lane, ls, product, want, family) if want
                 else select(levers, lane, ls, product, graph, family_not=family))
        if lever is None:
            return {"action": "park", "why": (f"Owner resume: lever {want} is not open, is retired, is of family {family}, "
                                              "or lacks its preconditions" if want else
                                              f"Owner resume: no open lever of another family than {family} with its "
                                              "preconditions met")}''')

# ---- test_autopilot.py: gates + mutant
sub("test_autopilot.py", '''    check("V-EVO-OWNER-RESUME-SAME-FAMILY-PARKS", ls["status"] == "PARKED" and "Owner resume" in q)''',
    '''    check("V-EVO-OWNER-RESUME-SAME-FAMILY-PARKS", ls["status"] == "PARKED" and "Owner resume" in q)
    # owner_resume="research:<id>" (2026-11-14): the named lever wins over a higher-ranked one; a bad name parks
    LD = dict(LB, id="lev_d", cost=99)
    RESD = dict(RES, phases=[p.replace("lev_b", "lev_d") for p in RES["phases"]])
    ls, q = evo_run(evo_fresh([LA, LB, LD], {"lever": "lev_a", "owner_resume": "research:lev_d"}, (RESD,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-NAMED-LEVER", ls["status"] == "RUNNING" and ls.get("lever") == "lev_d"
          and ls.get("mode") == "RESEARCH" and "owner_resume" not in ls)
    ls, q = evo_run(evo_fresh([LA, LB, LC], {"lever": "lev_a", "owner_resume": "research:lev_c"}, (RES,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-NAMED-SAME-FAMILY-PARKS", ls["status"] == "PARKED" and "lev_c" in q)
    ls, q = evo_run(evo_fresh([LA, LB], {"lever": "lev_a", "owner_resume": "research:nope"}, (RES,)), ["NONE"])
    check("V-EVO-OWNER-RESUME-NAMED-UNKNOWN-PARKS", ls["status"] == "PARKED" and "nope" in q)''')
sub("test_autopilot.py", '''         "evo_owner_resume_ignored": _evo_mut(OWNER_RESUME="zzz_never_set"),''',
    '''         "evo_owner_resume_ignored": _evo_mut(OWNER_RESUME="zzz_never_set"),
         "evo_owner_lever_ignored": _evo_mut(owner_lever=lambda *a, **k: None),''')

# ---- levers.json: the missing capabilities as research levers
PROFILE = ("Its certificates land in an additive profile proposed in ONE phase line that states: an independent target oracle "
           "on the original DOL bytes; a frozen pilot committed before the draw; pre/post controls; A2 negatives; historical "
           "receipts byte-identical; separate counters. Its receipts file gets a receipt_registry.json entry.")
COMMON = ("New route code in a new generation (existing route tools stay frozen); a frozen pilot committed before the draw; "
          "an independent oracle on the original DOL; a gate with planted mutants; certification only through the unchanged "
          "certify.decide. " + PROFILE)
NEW = {
 "KSR": [
  {"id": "cnm_variant_search", "family": "SOURCE_SEARCH", "kind": "research",
   "blockers": ["NO_OPERATOR_FOR_CLASS", "CNM_CODEGEN"], "cost": 7, "status": "open",
   "requires": ["evidence/ascension/s41k/pivot_residual_s41k.md"],
   "what": ("Owner 2026-11-14 ('crea las capacidades directamente'): a deterministic source-variant search over "
            "codegen-equivalent C rewrites (operand order, temporaries, loop form, cast placement, declaration order) for the "
            "3,177 S41K 'other' COMPILES_NO_EXACT ids, extending the existing search.run/search_ops of S17 W1; each "
            "candidate is judged by objdiff 100 plus reloc_oracle CONSISTENT plus object sha, never by a permuter score. "
            + COMMON + " Rival hypotheses: (a) a bounded variant search makes a measurable share of the residual BINARY_EXACT; "
            "(b) the residual differences are register-allocation or scheduling effects no source variant reaches "
            "(pilot BINARY_EXACT stays 0).")},
  {"id": "tu_boundary_floatdup", "family": "TU_SEGMENTATION_V2", "kind": "research",
   "blockers": ["FLAGS_SPLIT_ARM", "TU_BOUNDARY_CONTROL"], "cost": 8, "status": "open",
   "requires": ["evidence/ascension/s41k/pivot_residual_s41k.md"],
   "what": ("Owner 2026-11-14: the second independent TU-boundary signal that is the registered reopen condition of "
            "FLAGS_SPLIT per-unit flags and of H-S41PX: duplicated float/double constants in .sdata2/.rodata mark a TU "
            "boundary (research row Q6), combined with the existing sbss signal only after each is validated alone on "
            "units of known boundaries (own positive control). " + COMMON + " Rival hypotheses: (a) the inferred units "
            "predict per-unit flags or pragmas that make FLAGS_SPLIT ids BINARY_EXACT; (b) float-constant duplication "
            "does not track TU boundaries in KSR (the control on known units fails).")},
  {"id": "whole_program_type_model", "family": "TYPE_MODEL_V2", "kind": "research",
   "blockers": ["NO_COMPILE_TYPES"], "cost": 10, "status": "open",
   "requires": ["evidence/ascension/s41k/pivot_residual_s41k.md"],
   "what": ("Owner 2026-11-14: a whole-program KSR type model, not a per-function repair: callee prototypes by majority "
            "over EVERY call site of the program, struct layouts unioned per global symbol across all functions, iterated "
            "to a fixpoint, emitted as per-function source declarations only (no canonical ctx/header write). Known "
            "evidence against: on Tennis P1, P1c, P1d and P1e (call-graph propagation) were REFUTED and type repair gave "
            "compile without match; so the pre-registered outcome is BINARY_EXACT, never compile. " + COMMON +
            " Rival hypotheses: (a) whole-program consistency makes a measurable share of NO_COMPILE ids BINARY_EXACT; "
            "(b) it moves them to COMPILES_NO_EXACT only (pilot BINARY_EXACT stays 0).")},
 ],
 "TENNIS": [
  {"id": "cnm_variant_search", "family": "SOURCE_SEARCH", "kind": "research",
   "blockers": ["NO_OPERATOR_FOR_CLASS", "CNM_CODEGEN"], "cost": 7, "status": "open", "requires": [],
   "what": ("Owner 2026-11-14 ('crea las capacidades directamente'): the KSR deterministic source-variant search applied "
            "to the 164 Tennis COMPILES_NO_MATCH ids (attacked 1-4 times, 0 certified); tools read-only from t1; each "
            "candidate is judged by objdiff 100 plus object sha, never by a permuter score; certification only through "
            "the unchanged Tennis certifier, no new profile. Rival hypotheses: (a) a bounded variant search makes a "
            "measurable share BINARY_EXACT; (b) the differences are register allocation no source variant reaches "
            "(pilot BINARY_EXACT stays 0).")},
 ],
}
p = D / "levers.json"
d = json.loads(p.read_text(encoding="utf-8"))
for lane, add in NEW.items():
    ids = {x["id"] for x in d[lane]}
    for x in add:
        assert x["id"] not in ids, f"{lane}.{x['id']} already exists"
        d[lane].append(x)
p.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("patched", D)
