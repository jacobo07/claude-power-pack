#!/usr/bin/env python3
"""Parity matrix: private engine mechanism -> public module/gate, status GREEN | GAP | NOT_PORTED, with the command that proves it. The data lives here; PARITY.json
and PARITY.md are generated from it (`python tools/rf_parity.py write`) and V-RF-PARITY fails if either file drifts from this source.
Private module names below are the engine's own file names (code only); no content of the private tree is read or copied."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "vault", "programs", "reconstruction-factory")
SUITE = "python tools/test_reconstruction_factory.py"

# private modules the spec's Shape list covers (a GREEN or GAP row each)
G = [
    ("exact certification (judge, certificate, independent vs corroborating evidence, UNDERDETERMINED_TOOLCHAIN, held-out refusal)", ["judge", "certify", "cert_cxx"], ["judge", "certify"],
     ["V-RF-JUDGE", "V-RF-CERT-POSITIVE", "V-RF-CERT-NEGATIVE", "V-RF-HELDOUT-REFUSE"], "GREEN", ""),
    ("fingerprint / causal diff / residual", ["fingerprint", "causal_diff", "residual", "diagnostics"], ["fingerprint", "causal_diff", "residual"],
     ["V-RF-FINGERPRINT", "V-RF-CAUSAL-DIFF", "V-RF-RESIDUAL"], "GREEN", ""),
    ("search / search_plan / permute", ["search", "search_c", "search_ops", "search_plan", "permute", "permute_cut"], ["search", "search_plan", "permute", "operators"],
     ["V-RF-SEARCH", "V-RF-SEARCH-BUDGET", "V-RF-PERMUTE", "V-RF-PLAN"], "GREEN", ""),
    ("Build Twin + toolchain discrimination", ["build_twin", "toolchain_sd"], ["build_twin"], ["V-RF-BUILD-TWIN"], "GREEN", ""),
    ("Object Model (tables, vptr installs, vcalls, support rule, prototype propagation, this-call fields)", ["om"], ["om"],
     ["V-RF-OM-REGISTRY", "V-RF-OM-PROPAGATE", "V-RF-OM-THISCALL", "V-RF-OM-VCALL"], "GREEN", ""),
    ("om_skeleton generator (class decls, method<->vslot)", ["om_skeleton"], ["om_skeleton"], ["V-RF-OM-DECLS", "V-RF-OM-VCALL"], "GREEN", ""),
    ("Method Graph + supercompiled macros", [], ["method_graph"], ["V-RF-METHOD-GRAPH"], "GREEN", ""),
    ("Strategy Genome", [], ["genome"], ["V-RF-GENOME"], "GREEN", ""),
    ("Negative Search Memory (sound refutations only)", [], ["nsm"], ["V-RF-NSM"], "GREEN", ""),
    ("atoms (typed predicates)", ["atoms", "g3_atoms"], ["atoms"], ["V-RF-ATOMS"], "GREEN", ""),
    ("claims (semantic-key store)", ["claims"], ["claims"], ["V-RF-CLAIMS"], "GREEN", ""),
    ("invalidation (header delta, compiler ground truth)", ["invalidation"], ["invalidation"], ["V-RF-INVALIDATION"], "GREEN", ""),
    ("maturity contract (executable rubric, frozen hash)", ["maturity"], ["maturity"], ["V-RF-MATURITY"], "GREEN", ""),
    ("CBR birth + construction return", ["cbr"], ["cbr"], ["V-RF-CBR"], "GREEN", ""),
    ("held-out law (seal, leak scan, one-way release bound to a solver freeze)", [], ["heldout"], ["V-RF-HELDOUT-REFUSE", "V-RF-HELDOUT-RELEASE"], "GREEN", ""),
    ("frontier projection (a function counts once)", ["frontier"], ["frontier"], ["V-RF-FRONTIER"], "GREEN", ""),
    ("provenance (language evidence from the object)", ["provenance_cxx"], ["provenance"], ["V-RF-PROVENANCE"], "GREEN", ""),
    ("synthetic corpus + manifest (recon.toml) + toolchain adapter gcc-ppc", ["fixtures", "toolchain"], ["manifest", "toolchain", "elf", "core", "gatekit"],
     ["V-RF-CORPUS-DETERMINISTIC"], "GREEN", ""),
    ("public gate (derived-content scanner)", [], [], [], "GREEN", "python tools/recon_public_gate.py && python tools/test_recon_public_gate.py --drills"),
    ("liveness: package declared, scanner lists no reconstruction_factory row", [], [], [], "GREEN", "python modules/liveness/reachability.py | grep -c reconstruction_factory   # 0"),
    ("m2c lift + objdiff adapters", ["m2c_proto"], [], [], "GAP", "external tools not installed on the build host; lift is fixture skeletons, so the adapters are unexercised"),
    ("mwcc toolchain adapter", [], ["toolchain"], [], "GAP", "adapter exists but no compiler binary may ship or be required; unexercised by any test"),
    ("public gate denylist of private names", [], [], [], "GAP", "gate carries SHA-256 hashed built-in floor; the Owner's full private list must be supplied as hashes (--deny-file / RECON_GATE_DENY)"),
    ("operator-reachable skeleton coverage", [], [], [], "GAP", "22 corpus functions have no skeleton reachable by operators from a lifted form"),
    ("Object Model: virtual-method return types", [], ["om_skeleton"], [], "GAP", "default to s32; no evidence channel for return type"),
    ("Object Model: field layout", [], ["om"], [], "GAP", "field layout comes from this-call evidence only (no allocation-site or ctor-store evidence)"),
]
# private modules that were not ported. Reasons are by group; the modules were classified by name and role in the spec, not by reading private code.
WAVE = ["g4_ab", "g4_atlas", "g4_cohort", "g4_domain", "g4_fresh", "g4_mine", "g4_ops", "g4_policy", "g4_reach", "g4_s6", "g4_solv", "asc_fresh", "shared_actuate", "shared_blockers",
        "shared_scope", "shared_types", "shared_types_sweep", "roots", "pop_collapse", "progress_cse", "motion_canary", "tomography", "microscope", "science"]
TARGET_COUNT = 21  # private-target bridge modules; names withheld (the public gate denylist matches some)
MODEL = ["llm_fix", "campaign", "farm", "projection", "compounding", "repair", "regime_router", "regimes", "roofline", "semantic_interrupt", "operator_coverage", "fastmatch",
         "compiler_causality", "fixed_point"]
NOT_PORTED = [
    ("private wave scripts (g4_*, ascension, sweeps, shared-blocker waves)", WAVE, "NOT_PORTED", "served one private wave; the spec lists them as out of scope"),
    ("private-target bridges (binary-format, donor, decompiler-import, title-specific tables; %d modules, names withheld because the public gate denylist matches some)" % TARGET_COUNT, [], "NOT_PORTED", "bound to the private binary/title; the general engine reads a manifest instead"),
    ("model-driven lane and campaign runners, regime routing, economics", MODEL, "NOT_PORTED", "need credentials/evidence from the private campaign; outside the spec's mechanism list"),
]
PUBLIC_ONLY = {"__init__"}


def build():
    rows = []
    for i, (mech, priv, pub, gates, st, note) in enumerate(G, 1):
        proof = note if st == "GREEN" and not gates else (SUITE if gates else "")
        rows.append({"id": "P%02d" % i, "mechanism": mech, "private_modules": priv, "public_modules": ["modules/reconstruction_factory/%s.py" % m for m in pub],
                     "gates": gates, "status": st, "reason": "" if st == "GREEN" else note, "proof": proof})
    for j, (mech, priv, st, why) in enumerate(NOT_PORTED, 1):
        rows.append({"id": "N%02d" % j, "mechanism": mech, "private_modules": sorted(priv), "public_modules": [], "gates": [], "status": st, "reason": why, "proof": ""})
    return {"schema": 1, "spec": "vault/specs/reconstruction-factory-general.md", "rows": rows,
            "counts": {s: sum(1 for r in rows if r["status"] == s) for s in ("GREEN", "GAP", "NOT_PORTED")}}


def render(doc):
    out = ["# Reconstruction Factory (general) - parity with the private engine", "",
           "Generated by `python tools/rf_parity.py write`; do not edit. GREEN = a public gate proves it on the synthetic corpus; GAP = ported or planned but not provable here (reason given); "
           "NOT_PORTED = deliberately absent (reason given).", "", "Counts: %s" % ", ".join("%s %d" % kv for kv in doc["counts"].items()), "",
           "| id | mechanism | status | gates / proof | reason |", "|---|---|---|---|---|"]
    for r in doc["rows"]:
        out.append("| %s | %s | %s | %s | %s |" % (r["id"], r["mechanism"], r["status"], ", ".join(r["gates"]) or r["proof"] or "-", r["reason"] or "-"))
    out += ["", "Maturity vector: `python modules/reconstruction_factory/maturity.py` (anchor 10 of every dimension is Owner acceptance and is absent by design).", ""]
    return "\n".join(out)


def files(doc=None):
    doc = doc or build()
    return {"PARITY.json": json.dumps(doc, indent=1, sort_keys=True) + "\n", "PARITY.md": render(doc)}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "write":
        for n, t in files().items():
            with open(os.path.join(OUT, n), "w", newline="\n") as fh:
                fh.write(t)
        print(build()["counts"])
    else:
        print("usage: rf_parity.py write")
