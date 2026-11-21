"""V-BCAP2-D21 gate (Phase 8, Workstream A): the 21 design-resource sources and the fail-closed rights gate.
Drives V-D21-01/02/03/04/05/06/07/09/10/24/25/31/36 from both poles on the REAL registry file. No network.
Scope: source identity + rights posture only. Capability denominators, catalog entries and browser-real checks are NOT here.
python3 tools/test_bcap2_d21.py (exit 0 == PASS)"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.cdicf import source_intake as SI  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


R = SI.load()
by = {s["id"]: s for s in R["sources"]}
cov = SI.coverage(R)
check("D21-A01 control: real registry has 21/21 sources, none malformed", cov["ok"] and cov["registered"] == 21, str(cov))
LIVE = {r["url"]: r for r in json.loads((ROOT / "vault/programs/bcap-2/design-resources/LIVE_READ.json").read_text(encoding="utf-8"))["rows"]}


def live_problems(sources, live):
    """live_verified is true only when every non-GitHub URL has a recorded HTTP 200 read with a title; false must stay false."""
    out = []
    for s in sources:
        web = [u for u in s["urls"] if "github.com" not in u]
        ev = bool(web) and all(live.get(u, {}).get("status") == 200 and live.get(u, {}).get("title") for u in web)
        if s["live_verified"] and not ev:
            out.append(s["id"])
    return out


check("D21 control: every source has a canonical URL", all(s["urls"] for s in R["sources"]))
check("V-D21-LIVE-VERIFIED: every live_verified source has recorded LIVE_READ evidence", not live_problems(R["sources"], LIVE), str(live_problems(R["sources"], LIVE)))
check("V-D21-LIVE-VERIFIED: all 21 sources are live_verified", sum(s["live_verified"] for s in R["sources"]) == 21)
_m = copy.deepcopy(R); _m["sources"][0]["urls"] = ["https://never-read.invalid/"]
check("V-D21-LIVE-VERIFIED pole: a live_verified claim with no LIVE_READ row is caught", live_problems(_m["sources"], LIVE) == ["D21-01"])
_s = copy.deepcopy(LIVE); _s[R["sources"][1]["urls"][0]]["status"] = 503
check("V-D21-LIVE-VERIFIED pole: a recorded non-200 read cannot back the claim", live_problems(R["sources"], _s) == ["D21-02"])
check("D21 control: all 6 slide groups present", {s["group"] for s in R["sources"]} == {1, 2, 3, 4, 5, 6})

# V-D21-01 / 31: missing or shrunk corpus fails and names the resource
short = copy.deepcopy(R); short["sources"] = [s for s in short["sources"] if s["id"] != "D21-16"]
c1 = SI.coverage(short)
check("V-D21-01 pole: 20/21 fails and names the missing resource", not c1["ok"] and c1["missing"] == ["D21-16"])
check("V-D21-31 pole: dropping many sources cannot pass (denominator pinned in code, not in data)",
      not SI.coverage({"sources": R["sources"][:5], "denominator_sources": 5})["ok"])
bad = copy.deepcopy(R); bad["sources"][0]["rights_status"] = "FREE_FOR_ALL"
check("D21 pole: an invented rights status makes the record malformed", SI.coverage(bad)["malformed"] == ["D21-01"])

# V-D21-02 / 03: count drift is surfaced, never asserted
check("V-D21-02 pole: screenshot 49 vs observed 52 is DRIFT", SI.count_drift(49, 52)[0] == "DRIFT")
check("V-D21-03 pole: Kinetics 153 vs 144 is DRIFT, 153 vs 162 is DRIFT", SI.count_drift(153, 144)[0] == "DRIFT" and SI.count_drift(153, 162)[0] == "DRIFT")
check("V-D21-02 pole: no observation is UNKNOWN, not MATCH", SI.count_drift(49, None)[0] == "UNKNOWN")
check("V-D21-03 control: an equal observed count is MATCH", SI.count_drift(49, 49)[0] == "MATCH")

# V-D21-11: the stale "Proprietary" claim is reconciled explicitly, not silently overwritten and not left standing
import json as _json
_pin = next(r for r in _json.load(open(ROOT / "vault/programs/bcap-2/design-resources/LICENSE_PINS.json"))["rows"] if r["id"] == "D21-05")
_readme = (ROOT / "modules/design-md/README.md").read_text(encoding="utf-8")
_line = next(l for l in _readme.splitlines() if l.startswith("- license:"))
check("V-D21-11 control: pin evidence for design.md is Apache-2.0", "Apache License" in (_pin["license_head"] or ""))
check("V-D21-11 pole: README licence line is not a bare 'Proprietary' claim", not _line.startswith("- license: Proprietary"))
check("V-D21-11 pole: README records DRIFT and keeps the old claim visible", "DRIFT" in _line and "Proprietary" in _line)
check("V-D21-11 pole: README cites the pinned sha and leaves the npm licence UNVERIFIED", _pin["pinned_sha"][:8] in _line and "UNVERIFIED" in _line)

# V-D21-04: inaccessible sources carry no invented terms
for sid in ("D21-03", "D21-08"):
    check(f"V-D21-04 pole: {sid} is UNKNOWN_ACCESS and admits no code", by[sid]["rights_status"] == "UNKNOWN_ACCESS" and not SI.admit_code(by[sid])[0])

# V-D21-05 / 07: unknown community licence declines copy
check("V-D21-05 pole: 21st.dev community item with unknown licence is refused", not SI.admit_code(by["D21-09"])[0])
check("V-D21-07 pole: Uiverse snippet without origin/permission is refused", not SI.admit_code(by["D21-18"])[0])
# V-D21-06: Aceternity Pro
check("V-D21-06 pole: Aceternity (RESTRICTED) is refused even with a permissive-looking evidence blob",
      not SI.admit_code(by["D21-11"], {"spdx": "MIT", "version": "1", "license_sha256": "x"})[0])
# V-D21-09: restricted source never executable-licence-free
check("V-D21-09 pole: every RESTRICTED/REFERENCE_ONLY/UNKNOWN source is refused with no evidence",
      all(not SI.admit_code(s)[0] for s in R["sources"] if s["rights_status"] in ("RESTRICTED", "REFERENCE_ONLY", "UNKNOWN", "UNKNOWN_ACCESS")))
check("V-D21-09 pole: MIXED without item evidence is refused", not SI.admit_code(by["D21-17"])[0])
# V-D21-10: README vs LICENSE
MIT_L = "Permission is hereby granted, free of charge, to any person obtaining a copy"
GPL_L = "GNU General Public License version 3"
ev = {"spdx": "MIT", "version": "1.2.0", "license_sha256": "ab" * 32}
ok_c, why_c = SI.admit_code(by["D21-10"], dict(ev, readme="License: MIT", license_text=MIT_L))
check("V-D21-10 control: item with evidence, agreeing README/LICENSE is admitted", ok_c, why_c)
check("V-D21-10 pole: README MIT but LICENSE GPL is LICENSE_CONFLICT",
      SI.admit_code(by["D21-10"], dict(ev, readme="License: MIT", license_text=GPL_L))[1].startswith("LICENSE_CONFLICT"))
check("V-D21-10 pole: non-permissive SPDX refused", not SI.admit_code(by["D21-10"], dict(ev, spdx="GPL"))[0])
check("V-D21-10 pole: evidence missing the licence hash refused", not SI.admit_code(by["D21-10"], {"spdx": "MIT", "version": "1"})[0])

# V-D21-24 / 25: asset licences are item- and version-aware
check("V-D21-25 pole: premium 3dicons item under the source's CC0 label is refused", not SI.asset_license_ok({"tier": "premium", "license": "CC0", "provenance": "p"})[0])
check("V-D21-24 pole: Kitbitz asset with third-party marks / no provenance refused",
      not SI.asset_license_ok({"tier": "free", "third_party_marks": True, "provenance": "p"})[0]
      and not SI.asset_license_ok({"tier": "free"})[0])
check("V-D21-25 control: v1 item with provenance and no third-party marks accepted", SI.asset_license_ok({"tier": "v1", "provenance": "p"})[0])

# V-D21-36: DONE with just 21 URLs
d = SI.done_check(R, 0)
check("V-D21-36 pole: 21 URLs and zero vetted entries is NOT done", not d["ok"] and d["reason"] == "zero vetted entries")
check("V-D21-36 control: full coverage plus a vetted entry passes the source-gate arithmetic", SI.done_check(R, 1)["ok"])

# honest scope + provenance of the registry itself
check("D21 scope: no source is marked live-verified or has a derived capability denominator (Workstream A03 is NOT done)",
      all(s["capability_denominator"].startswith("UNKNOWN") for s in R["sources"]))
check("D21-A06 pole: known conflicts recorded (Kinetics no licence, mapcn tiles, 3dicons split, DESIGN.md drift)",
      "licen" in by["D21-15"]["rights_note"].lower() and "CARTO" in by["D21-17"]["rights_note"]
      and "premium" in by["D21-21"]["rights_note"] and "Proprietary" in by["D21-05"]["rights_note"])

# V-D21-05 (A05 pinned-commit + licence evidence): the pin is data the rights gate consumes, not decoration
pinned = {s["id"]: s for s in R["sources"] if "license_pin" in s}
check("V-D21-05 control: 9 repos carry a pinned 40-hex sha, 7 with a licence hash",
      len(pinned) == 9 and all(len(p["license_pin"]["pinned_sha"]) == 40 for p in pinned.values())
      and sum(1 for p in pinned.values() if p["license_pin"]["license_sha256"]) == 7)


def _ev(s):
    p = s["license_pin"]
    return {"spdx": p["spdx"], "version": p["pinned_sha"], "license_sha256": p["license_sha256"]}


ok_ids = [i for i, s in pinned.items() if SI.admit_code(s, _ev(s))[0]]
check("V-D21-05 pole: pin-derived evidence admits exactly the 7 licensed repos", sorted(ok_ids) == sorted(i for i, s in pinned.items() if s["license_pin"]["license_sha256"]), str(ok_ids))
check("V-D21-05 pole: no-licence repos (motion-primitives, kinetics) stay refused even with a pinned sha",
      not SI.admit_code(by["D21-14"], _ev(by["D21-14"]))[0] and not SI.admit_code(by["D21-15"], _ev(by["D21-15"]))[0])
mut = copy.deepcopy(by["D21-10"]); mut["license_pin"]["license_sha256"] = None
check("V-D21-05 pole: seeded mutant (licence hash dropped) is refused", not SI.admit_code(mut, _ev(mut))[0])
check("V-D21-05 control: live_verified is backed by LIVE_READ, not by the licence pin", not live_problems(R["sources"], LIVE))

print(f"\n{'V-BCAP2-D21 PASS' if not FAILS else 'V-BCAP2-D21 FAIL: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
