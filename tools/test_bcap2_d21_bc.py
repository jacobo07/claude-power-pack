"""V-BCAP2-D21-BC gate (Phase 8 Workstreams B/C slice): reference_intel. Both poles per scenario, no network.
Drives D21-B05/B06 and V-D21-12/13/18. python3 tools/test_bcap2_d21_bc.py (exit 0 == PASS)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.cdicf import reference_intel as RI  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


# V-D21-12: missing token is UNKNOWN, an unevidenced value is dropped, not carried
t = RI.extract_tokens({"tokens": {"color": {"value": "#0a0a0a", "evidence": "OBSERVED"},
                                  "font": {"value": "Inter", "evidence": None},
                                  "radius": {"value": "8px", "evidence": "INFERRED"}}})
check("V-D21-12 pole: absent spacing is UNKNOWN with no value", t["spacing"] == {"value": None, "level": "UNKNOWN"})
check("V-D21-12 pole: font named without evidence is dropped to UNKNOWN", t["font"]["level"] == "UNKNOWN" and t["font"]["value"] is None)
check("V-D21-12 control: observed colour and inferred radius keep value and level",
      t["color"] == {"value": "#0a0a0a", "level": "OBSERVED"} and t["radius"]["level"] == "INFERRED")
check("V-D21-12 pole: empty reference yields all-UNKNOWN, no invented defaults",
      all(v["level"] == "UNKNOWN" and v["value"] is None for v in RI.extract_tokens({}).values()))

# V-D21-13: project contract wins
proj = {"color": "#111111", "font": None, "radius": "4px", "spacing": None, "size": None}
m = RI.merge_into_project(proj, t)
check("V-D21-13 pole: conflicting imported colour does not overwrite the project's", m["tokens"]["color"] == "#111111")
check("V-D21-13 pole: the conflict is reported, not silent", {"kind": "color", "kept": "#111111", "rejected": "#0a0a0a"} in m["conflicts"])
check("V-D21-13 control: an empty project slot may take an evidenced import, UNKNOWN stays None",
      RI.merge_into_project({k: None for k in RI.TOKEN_KINDS}, t)["tokens"]["color"] == "#0a0a0a"
      and RI.merge_into_project({k: None for k in RI.TOKEN_KINDS}, t)["tokens"]["font"] is None)
check("V-D21-13 control: identical value is not a conflict", not RI.merge_into_project({"radius": "8px"}, t)["conflicts"])

# D21-B06 brief
good = {"source": "ref-A hero", "transferable": ["type scale hierarchy"], "forbidden_copy": ["exact layout", "logo"],
        "differs_by": "product-specific proof strip", "test_plan": "render + contrast + responsive"}
check("D21-B06 control: complete brief passes", RI.validate_brief(good)[0])
for f in RI.BRIEF_FIELDS:
    b = dict(good); b.pop(f)
    check(f"D21-B06 pole: brief without {f} is refused", not RI.validate_brief(b)[0])
check("D21-B06 pole: empty forbidden_copy is refused", not RI.validate_brief({**good, "forbidden_copy": []})[0])
check("D21-B06 pole: result identical to source is refused", not RI.validate_brief({**good, "differs_by": good["source"]})[0])
check("D21-B06 pole: None brief is refused", not RI.validate_brief(None)[0])

# D21-B05 ranking
CAT = [
    {"id": "m1", "purpose": "pricing", "platform": "mobile", "sector": "fintech", "era": "2024", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "m2", "purpose": "pricing", "platform": "mobile", "sector": "fintech", "era": "2024", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "m3", "purpose": "pricing", "platform": "mobile", "sector": "health", "era": "2023", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "d1", "purpose": "pricing", "platform": "desktop", "sector": "fintech", "era": "2024", "source_rights": "OPEN_PERMISSIVE",
     "license_evidence": {"spdx": "MIT", "version": "1", "license_sha256": "h"}},
    {"id": "r1", "purpose": "pricing", "platform": "mobile", "sector": "retail", "era": "2022", "source_rights": "RESTRICTED"},
]
r = RI.rank({"purpose": "pricing", "platform": "mobile", "sector": "fintech", "need_code": True}, CAT)
ids = [p["id"] for p in r["picks"]]
check("D21-B05 control: best mobile+sector item ranks first", r["verdict"] == "RANKED" and ids[0] == "m1", str(r))
check("D21-B05 pole: desktop item never returned for a mobile query", "d1" not in ids)
check("D21-B05 pole: RESTRICTED source filtered when code is needed", "r1" not in ids)
check("D21-B05 pole: diversity guard drops the near-duplicate (same sector+era)", "m2" not in ids and "m3" in ids)
check("D21-B05 control: without need_code the restricted item may be a reference-only pick",
      "r1" in [p["id"] for p in RI.rank({"purpose": "pricing", "platform": "mobile", "sector": "retail"}, CAT)["picks"]])
a = RI.rank({"purpose": "kanban", "platform": "watch"}, CAT)
check("D21-B05 pole: no match ABSTAINs with a reason", a["verdict"] == "ABSTAIN" and a["picks"] == [] and a["reason"])
check("D21-B05 pole: purpose mismatch alone (platform match) falls under the floor and ABSTAINs",
      RI.rank({"purpose": "kanban", "platform": "mobile"}, CAT)["verdict"] == "ABSTAIN")
check("D21-B05 pole: empty catalog ABSTAINs", RI.rank({"purpose": "pricing", "platform": "mobile"}, [])["verdict"] == "ABSTAIN")

# V-D21-18: motion budget NONE
n = RI.rank({"purpose": "pricing", "platform": "mobile", "motion_budget": "NONE", "want_motion": True}, CAT)
check("V-D21-18 pole: motion budget NONE with a motion ask ABSTAINs, nothing proposed", n["verdict"] == "ABSTAIN" and not n["picks"])
check("V-D21-18 control: budget NONE without a motion ask still ranks normally",
      RI.rank({"purpose": "pricing", "platform": "mobile", "motion_budget": "NONE"}, CAT)["verdict"] == "RANKED")

# D21-C07: no unobserved fidelity claims
full = {c: True for c in RI.RENDER_CHECKS}
check("D21-C07 control: no fidelity claim needs no evidence", RI.fidelity_claims("Adapted hero with our own proof strip", {})[0])
check("D21-C07 pole: '1:1' claim with no evidence is refused", not RI.fidelity_claims("Delivers a 1:1 match of the reference", {})[0])
check("D21-C07 pole: absent check is unobserved, not passed", not RI.fidelity_claims("pixel-perfect", {**full, "fonts": None})[0])
check("D21-C07 pole: a failed check refuses and names it", any("a11y: failed" in r for r in RI.fidelity_claims("pixel-perfect", {**full, "a11y": False})[1]))
check("D21-C07 control: claim with all five checks observed true passes", RI.fidelity_claims("pixel-perfect clone of layout", full)[0])
check("D21-C07 pole: None claim text is not a claim", RI.fidelity_claims(None, None)[0])

# mutant drill: a permissive merge would overwrite the project; prove the check can fail
bad = {k: (v["value"] if v["value"] else None) for k, v in t.items()}
check("drill: a naive overwrite-merge would differ from the project value (the V-D21-13 check is live)", bad["color"] != proj["color"])

print(f"{'PASS' if not FAILS else 'FAIL'}: {len(FAILS)} failures")
sys.exit(1 if FAILS else 0)
